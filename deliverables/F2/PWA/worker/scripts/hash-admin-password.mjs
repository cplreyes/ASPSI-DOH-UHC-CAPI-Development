#!/usr/bin/env node
/**
 * Generate the value to paste into `wrangler secret put ADMIN_PASSWORD_HASH`.
 *
 * Usage:
 *   node scripts/hash-admin-password.mjs
 *   (you'll be prompted for the password; not echoed)
 *
 * Output format: <saltB64url>:<iterations>:<hashB64url>
 * Verifier in the Worker is in src/admin.ts (verifyAdminPassword).
 */
import { webcrypto } from 'node:crypto';
import readline from 'node:readline';

const ITERATIONS = 600_000;

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

function readPasswordSilently(prompt) {
  return new Promise((resolve) => {
    process.stdout.write(prompt);
    const stdin = process.stdin;
    stdin.setRawMode?.(true);
    stdin.resume();
    let buf = '';
    stdin.on('data', function onData(b) {
      const ch = b.toString('utf8');
      if (ch === '\r' || ch === '\n' || ch === '') {
        stdin.setRawMode?.(false);
        stdin.pause();
        stdin.removeListener('data', onData);
        process.stdout.write('\n');
        resolve(buf);
        return;
      }
      if (ch === '') {
        process.exit(130);
      }
      if (ch === '' || ch === '\b') {
        buf = buf.slice(0, -1);
        return;
      }
      buf += ch;
    });
  });
}

(async () => {
  const password = await readPasswordSilently('Admin password (not echoed): ');
  if (!password) {
    console.error('No password provided.');
    process.exit(1);
  }
  if (password.length < 12) {
    console.error('Password too short. Use at least 12 characters.');
    process.exit(1);
  }
  const salt = webcrypto.getRandomValues(new Uint8Array(16));
  const hash = await pbkdf2(password, salt, ITERATIONS);
  const stored = `${b64url(salt)}:${ITERATIONS}:${b64url(hash)}`;
  console.log('\nPaste this exact value when prompted by `wrangler secret put ADMIN_PASSWORD_HASH`:\n');
  console.log(stored);
})();
