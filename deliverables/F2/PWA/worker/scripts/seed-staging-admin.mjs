#!/usr/bin/env node
/**
 * Seed the staging Administrator role + first admin user, talking
 * directly to the staging Apps Script Web App via HMAC-signed envelopes.
 *
 * Usage:
 *   $env:APPS_SCRIPT_URL  = "https://script.google.com/macros/s/<id>/exec"
 *   $env:APPS_SCRIPT_HMAC = "<HMAC_SECRET from staging AS Script Properties>"
 *   node scripts/seed-staging-admin.mjs `
 *     --username carl-admin `
 *     --password "<chosen password, min 12 chars>" `
 *     --first-name Carl `
 *     --last-name Reyes `
 *     --email carlpatricklreyes@gmail.com
 *
 * What it does:
 *   1. PBKDF2-hashes the password (100k iters, SHA-256, 16-byte salt) -
 *      matches worker/src/admin/auth.ts exactly.
 *   2. POSTs admin_roles_create with name=Administrator + all perms = true.
 *      If the role already exists (E_CONFLICT), continues - this is idempotent.
 *   3. POSTs admin_users_create with the hashed password + Administrator role.
 *      If the user already exists (E_CONFLICT), prints the conflict and exits
 *      non-zero so re-runs against the same username are explicit.
 *
 * Why a custom Node script instead of the worker / portal:
 *   The portal's Users / Roles dashboards require a logged-in admin. There is
 *   no admin yet. This is the bootstrap. After it runs once, all subsequent
 *   admin creations go through the portal.
 *
 * Production cutover: re-run this with production APPS_SCRIPT_URL +
 * APPS_SCRIPT_HMAC after the production AS deployment includes the admin
 * dispatcher (Task 1.5). The script is environment-agnostic.
 */
import { webcrypto, createHmac } from 'node:crypto';

const PBKDF2_ITERATIONS = 100_000;

const ADMIN_PERMS = {
  dash_data: true,
  dash_report: true,
  dash_apps: true,
  dash_users: true,
  dash_roles: true,
  dict_self_admin_up: true,
  dict_self_admin_down: true,
  dict_paper_encoded_up: true,
  dict_paper_encoded_down: true,
  dict_capi_up: true,
  dict_capi_down: true,
};

function b64url(bytes) {
  return Buffer.from(bytes).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

async function pbkdf2(password, salt, iterations) {
  const baseKey = await webcrypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(password),
    'PBKDF2',
    false,
    ['deriveBits'],
  );
  const bits = await webcrypto.subtle.deriveBits(
    { name: 'PBKDF2', salt, iterations, hash: 'SHA-256' },
    baseKey,
    256,
  );
  return new Uint8Array(bits);
}

async function hashPassword(password) {
  const salt = webcrypto.getRandomValues(new Uint8Array(16));
  const hash = await pbkdf2(password, salt, PBKDF2_ITERATIONS);
  return `${b64url(salt)}:${PBKDF2_ITERATIONS}:${b64url(hash)}`;
}

// Mirror worker/src/admin/apps-script-client.ts stableJson exactly.
function stableJson(payload) {
  if (payload === null || payload === undefined) return 'null';
  if (typeof payload !== 'object' || Array.isArray(payload)) {
    return JSON.stringify(payload);
  }
  const keys = Object.keys(payload).sort();
  return JSON.stringify(payload, keys);
}

function signRequest(secret, action, ts, requestId, payload) {
  const canonical = `${action}.${ts}.${requestId}.${stableJson(payload)}`;
  return createHmac('sha256', secret).update(canonical).digest('hex');
}

async function callAppsScript(url, secret, action, payload) {
  const ts = Math.floor(Date.now() / 1000);
  const request_id = webcrypto.randomUUID();
  const hmac = signRequest(secret, action, ts, request_id, payload);
  const body = JSON.stringify({ action, ts, request_id, payload, hmac });
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
    redirect: 'follow',
  });
  const text = await r.text();
  let parsed;
  try { parsed = JSON.parse(text); }
  catch { return { ok: false, error: { code: 'E_BACKEND', message: `non-JSON: ${text.slice(0, 200)}` }, request_id }; }
  return { ...parsed, request_id };
}

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith('--')) continue;
    const key = a.slice(2);
    const val = argv[i + 1];
    if (val === undefined || val.startsWith('--')) {
      out[key] = true;
    } else {
      out[key] = val;
      i++;
    }
  }
  return out;
}

function fail(msg) {
  console.error(`\n[seed-staging-admin] ERROR: ${msg}\n`);
  process.exit(1);
}

(async () => {
  const url = process.env.APPS_SCRIPT_URL;
  const secret = process.env.APPS_SCRIPT_HMAC;
  if (!url) fail('APPS_SCRIPT_URL env var not set');
  if (!secret) fail('APPS_SCRIPT_HMAC env var not set');

  const args = parseArgs(process.argv.slice(2));
  const username = args.username;
  const password = args.password;
  const firstName = args['first-name'] || '';
  const lastName = args['last-name'] || '';
  const email = args.email || '';
  const phone = args.phone || '';

  if (!username) fail('--username required');
  if (!password || password === true) fail('--password required');
  if (typeof password !== 'string' || password.length < 12) {
    fail('--password must be a string of at least 12 characters');
  }
  if (!/^[A-Za-z0-9_]{3,32}$/.test(username)) {
    fail('--username must be 3-32 chars [A-Za-z0-9_] (matches USERNAME_RE in worker)');
  }

  console.log('[seed-staging-admin] hashing password (PBKDF2-SHA256, 100k iters)...');
  const password_hash = await hashPassword(password);

  console.log('[seed-staging-admin] ensuring Administrator role exists...');
  const roleResp = await callAppsScript(url, secret, 'admin_roles_create', {
    name: 'Administrator',
    ...ADMIN_PERMS,
    created_by: 'bootstrap',
  });
  if (roleResp.ok) {
    console.log(`  ok: created role Administrator (request_id ${roleResp.request_id})`);
  } else if (roleResp.error?.code === 'E_CONFLICT') {
    console.log('  ok: role Administrator already exists (idempotent)');
  } else {
    fail(`admin_roles_create failed: ${JSON.stringify(roleResp.error)} (request_id ${roleResp.request_id})`);
  }

  console.log(`[seed-staging-admin] creating user "${username}"...`);
  const userResp = await callAppsScript(url, secret, 'admin_users_create', {
    username,
    password_hash,
    role_name: 'Administrator',
    first_name: firstName,
    last_name: lastName,
    email,
    phone,
    password_must_change: false,
    created_by: 'bootstrap',
  });
  if (userResp.ok) {
    console.log(`  ok: user ${username} seeded (request_id ${userResp.request_id})`);
    console.log('\n[seed-staging-admin] DONE. Now smoke-test login:');
    console.log(`  curl.exe -i -X POST "<staging worker URL>/admin/api/login" \\`);
    console.log(`    -H "Content-Type: application/json" \\`);
    console.log(`    --data-raw '{"username":"${username}","password":"<your password>"}'`);
    console.log('\nExpect 200 with a JWT token in the response body.');
  } else {
    fail(`admin_users_create failed: ${JSON.stringify(userResp.error)} (request_id ${userResp.request_id})`);
  }
})();
