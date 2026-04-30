/**
 * Admin auth + admin endpoint handlers.
 * Spec §4.1, §7.3.
 */
import type { Env, JwtClaims, TokenAuditEntry } from './types';
import { errorResponse, jsonResponse } from './types';
import { mintJwt, verifyJwt } from './jwt';
import { renderAdminHtml } from './admin-html';

const enc = new TextEncoder();
const SESSION_COOKIE = 'f2_admin_session';
const SESSION_TTL_S = 60 * 60; // 1 hour
/** Sentinel `tablet_id` value used to mark an admin session JWT vs. a device JWT. */
const ADMIN_SESSION_TABLET_ID = '__admin_session__';

// ---------- Password hashing (PBKDF2-SHA256) ----------

// Cloudflare Workers caps `crypto.subtle.deriveBits` PBKDF2 iterations at 100,000;
// values above throw `NotSupportedError: iteration counts above 100000 are not supported`
// at runtime. NIST 2023 recommends 600k for SHA-256 — we accept 100k below that bar
// because (a) admin password is high-entropy + rate-limited at the Worker, and
// (b) anything higher silently soft-bricks `/admin/login`. Issue #35 tracked this.
export const MAX_PBKDF2_ITERS = 100_000;

function b64urlEncode(bytes: Uint8Array): string {
  let s = '';
  for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]!);
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function b64urlDecode(s: string): Uint8Array {
  const padded = s.replace(/-/g, '+').replace(/_/g, '/') + '==='.slice((s.length + 3) % 4);
  const bin = atob(padded);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

/** Constant-time byte comparison. */
function timingSafeEqual(a: Uint8Array, b: Uint8Array): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a[i]! ^ b[i]!;
  return diff === 0;
}

async function pbkdf2Derive(password: string, salt: Uint8Array, iterations: number): Promise<Uint8Array> {
  const baseKey = await crypto.subtle.importKey('raw', enc.encode(password), 'PBKDF2', false, ['deriveBits']);
  const bits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt, iterations, hash: 'SHA-256' },
    baseKey,
    256,
  );
  return new Uint8Array(bits);
}

/**
 * Verify a plaintext admin password against the stored hash.
 * Stored format: `<saltB64url>:<iterations>:<hashB64url>`.
 * Note: spec §7.3 says "bcrypt"; we use PBKDF2-SHA256 because it's native to Workers.
 *
 * Returns false (without throwing) for malformed hashes, iteration counts below
 * the 10k floor, or iteration counts above the Workers cap (`MAX_PBKDF2_ITERS`).
 * The Workers-cap check is a fail-fast guard: if a future operator generates a
 * hash with too-high iterations and ships it as the secret, login fails cleanly
 * rather than throwing `NotSupportedError` mid-request.
 */
export async function verifyAdminPassword(plaintext: string, storedHash: string): Promise<boolean> {
  const parts = storedHash.split(':');
  if (parts.length !== 3) return false;
  const [saltB64, iterStr, expectedB64] = parts as [string, string, string];
  const iterations = parseInt(iterStr, 10);
  if (!iterations || iterations < 10_000) return false;
  if (iterations > MAX_PBKDF2_ITERS) return false;
  const salt = b64urlDecode(saltB64);
  const expected = b64urlDecode(expectedB64);
  const actual = await pbkdf2Derive(plaintext, salt, iterations);
  return timingSafeEqual(actual, expected);
}

// ---------- Session cookie (signed with JWT_SIGNING_KEY) ----------
// Sessions reuse the device-JWT shape so verifyJwt can validate them. The marker
// claim `tablet_id === ADMIN_SESSION_TABLET_ID` distinguishes them from real device
// tokens, so a stolen device JWT cannot be used as an admin session.

async function mintSession(env: Env): Promise<string> {
  const nowS = Math.floor(Date.now() / 1000);
  const claims: JwtClaims = {
    jti: crypto.randomUUID(),
    tablet_id: ADMIN_SESSION_TABLET_ID,
    facility_id: 'admin',
    iat: nowS,
    exp: nowS + SESSION_TTL_S,
  };
  return mintJwt(claims, env.JWT_SIGNING_KEY);
}

async function verifySession(cookieHeader: string | null, env: Env): Promise<boolean> {
  if (!cookieHeader) return false;
  const cookies = Object.fromEntries(
    cookieHeader.split(';').map((c) => {
      const [k, ...rest] = c.trim().split('=');
      return [k!, rest.join('=')];
    }),
  );
  const token = cookies[SESSION_COOKIE];
  if (!token) return false;
  const result = await verifyJwt(token, env.JWT_SIGNING_KEY);
  if (!result.ok) return false;
  // Reject anything that's not specifically an admin session token.
  return result.claims.tablet_id === ADMIN_SESSION_TABLET_ID;
}

// ---------- Endpoint handlers ----------

export async function handleAdminLogin(req: Request, env: Env): Promise<Response> {
  const body = (await req.json().catch(() => ({}))) as { password?: string };
  const password = body.password ?? '';
  if (!password) return errorResponse('E_BAD_REQUEST', 'Missing password.', 400);

  const ok = await verifyAdminPassword(password, env.ADMIN_PASSWORD_HASH);
  if (!ok) return errorResponse('E_AUTH_FAILED', 'Invalid password.', 401);

  const sessionToken = await mintSession(env);
  return jsonResponse(
    { ok: true },
    200,
    {
      'Set-Cookie': `${SESSION_COOKIE}=${sessionToken}; HttpOnly; Secure; SameSite=Strict; Path=/admin; Max-Age=${SESSION_TTL_S}`,
    },
  );
}

export async function requireAdminSession(req: Request, env: Env): Promise<Response | null> {
  const ok = await verifySession(req.headers.get('Cookie'), env);
  if (!ok) return errorResponse('E_AUTH_REQUIRED', 'Admin session required. POST /admin/login first.', 401);
  return null;
}

export async function handleIssueToken(req: Request, env: Env): Promise<Response> {
  const guard = await requireAdminSession(req, env);
  if (guard) return guard;

  const body = (await req.json().catch(() => ({}))) as {
    facility_id?: string;
    tablet_label?: string;
    ttl_days?: number;
  };
  const facility_id = (body.facility_id ?? '').trim();
  const tablet_label = (body.tablet_label ?? '').trim();
  const ttl_days = body.ttl_days ?? 30; // spec §5: default 30 days

  if (!facility_id) return errorResponse('E_BAD_REQUEST', 'facility_id is required.', 400);
  if (!tablet_label) return errorResponse('E_BAD_REQUEST', 'tablet_label is required.', 400);
  if (ttl_days < 1 || ttl_days > 365)
    return errorResponse('E_BAD_REQUEST', 'ttl_days must be between 1 and 365.', 400);

  const nowS = Math.floor(Date.now() / 1000);
  const jti = crypto.randomUUID();
  const tablet_id = crypto.randomUUID();
  const exp = nowS + ttl_days * 86400;

  const claims: JwtClaims = { jti, tablet_id, facility_id, iat: nowS, exp };
  const token = await mintJwt(claims, env.JWT_SIGNING_KEY);

  const audit: TokenAuditEntry = {
    jti,
    tablet_id,
    tablet_label,
    facility_id,
    issued_at: nowS,
    exp,
  };
  await env.F2_AUTH.put(`token:${jti}`, JSON.stringify(audit), { expirationTtl: ttl_days * 86400 });

  return jsonResponse({ ok: true, token, claims, audit });
}

export async function handleRevokeToken(req: Request, env: Env): Promise<Response> {
  const guard = await requireAdminSession(req, env);
  if (guard) return guard;

  const body = (await req.json().catch(() => ({}))) as { jti?: string };
  const jti = (body.jti ?? '').trim();
  if (!jti) return errorResponse('E_BAD_REQUEST', 'jti is required.', 400);

  // Look up the audit entry to compute remaining TTL for the revocation marker.
  const auditRaw = await env.F2_AUTH.get(`token:${jti}`);
  if (!auditRaw) return errorResponse('E_NOT_FOUND', `No active token with jti=${jti}.`, 404);
  const audit = JSON.parse(auditRaw) as TokenAuditEntry;

  const nowS = Math.floor(Date.now() / 1000);
  const remainingTtl = Math.max(60, audit.exp - nowS); // at least 60s so KV doesn't drop instantly

  // Write revocation marker; expires when the original JWT would expire anyway.
  await env.F2_AUTH.put(`revoked:${jti}`, '1', { expirationTtl: remainingTtl });

  // Update audit entry with revoked_at.
  audit.revoked_at = nowS;
  await env.F2_AUTH.put(`token:${jti}`, JSON.stringify(audit), { expirationTtl: remainingTtl });

  return jsonResponse({ ok: true, jti, revoked_at: nowS });
}

export async function handleListTokens(req: Request, env: Env): Promise<Response> {
  const guard = await requireAdminSession(req, env);
  if (guard) return guard;

  const url = new URL(req.url);
  const filterFacility = url.searchParams.get('facility') ?? '';

  const list = await env.F2_AUTH.list({ prefix: 'token:' });
  const tokens: TokenAuditEntry[] = [];
  for (const key of list.keys) {
    const raw = await env.F2_AUTH.get(key.name);
    if (!raw) continue;
    const entry = JSON.parse(raw) as TokenAuditEntry;
    if (filterFacility && entry.facility_id !== filterFacility) continue;
    tokens.push(entry);
  }
  // Newest first.
  tokens.sort((a, b) => b.issued_at - a.issued_at);
  return jsonResponse({ ok: true, tokens });
}

export function handleAdminUi(): Response {
  return new Response(renderAdminHtml(), {
    status: 200,
    headers: { 'Content-Type': 'text/html; charset=utf-8' },
  });
}
