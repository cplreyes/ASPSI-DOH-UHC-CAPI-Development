/**
 * F2 Admin Portal — per-user PBKDF2 password hash + verify, plus admin JWT
 * mint/verify with role_version claim.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Tasks 1.7, 1.8)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§5.4, §6.3, §10.1)
 *
 * Iteration count: 100,000. Cloudflare Workers caps `crypto.subtle.deriveBits`
 * PBKDF2 iterations at 100k; values above throw NotSupportedError at runtime
 * (Issue #35; already discovered in src/admin.ts for the M10-era admin path).
 * The original spec §10.1 called for 600k via Web Crypto subtle — the spec is
 * wrong about Workers' deriveBits capabilities. The runtime constraint wins;
 * the spec note has been corrected via this implementation.
 */

const enc = new TextEncoder();

const PBKDF2_ITERATIONS = 100_000;
const PBKDF2_FLOOR = 10_000;
const PBKDF2_CEIL = 100_000;
const HASH_LEN_BITS = 256;
const SALT_LEN = 32;

// ---------------------------------------------------------------------------
// Encoding helpers (base64url, no padding)
// ---------------------------------------------------------------------------

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

function timingSafeEqual(a: Uint8Array, b: Uint8Array): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a[i]! ^ b[i]!;
  return diff === 0;
}

// ---------------------------------------------------------------------------
// PBKDF2 — password hash + verify
// ---------------------------------------------------------------------------

async function pbkdf2(password: string, salt: Uint8Array, iters: number): Promise<Uint8Array> {
  const baseKey = await crypto.subtle.importKey('raw', enc.encode(password), 'PBKDF2', false, ['deriveBits']);
  const bits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt, iterations: iters, hash: 'SHA-256' },
    baseKey,
    HASH_LEN_BITS,
  );
  return new Uint8Array(bits);
}

/**
 * Hash a plaintext password. Returns `<saltB64url>:<iters>:<hashB64url>`.
 * Iterations are fixed at PBKDF2_ITERATIONS (100k, Workers cap).
 */
export async function hashPassword(password: string): Promise<string> {
  const salt = crypto.getRandomValues(new Uint8Array(SALT_LEN));
  const hash = await pbkdf2(password, salt, PBKDF2_ITERATIONS);
  return `${b64urlEncode(salt)}:${PBKDF2_ITERATIONS}:${b64urlEncode(hash)}`;
}

/**
 * Verify a plaintext password against a stored hash. Returns false (without
 * throwing) for malformed hashes or out-of-range iteration counts.
 *
 * The PBKDF2_CEIL check is a fail-fast guard: if a stored hash claims
 * iterations above the Workers runtime cap, login fails cleanly here rather
 * than throwing NotSupportedError mid-request.
 */
export async function verifyPassword(password: string, stored: string): Promise<boolean> {
  const parts = stored.split(':');
  if (parts.length !== 3) return false;
  const [saltB64, iterStr, hashB64] = parts as [string, string, string];
  const iters = parseInt(iterStr, 10);
  if (!Number.isFinite(iters) || iters < PBKDF2_FLOOR) return false;
  if (iters > PBKDF2_CEIL) return false;
  let salt: Uint8Array;
  let expected: Uint8Array;
  try {
    salt = b64urlDecode(saltB64);
    expected = b64urlDecode(hashB64);
  } catch {
    return false;
  }
  const computed = await pbkdf2(password, salt, iters);
  return timingSafeEqual(computed, expected);
}

// ---------------------------------------------------------------------------
// Admin JWT — mint + verify
// ---------------------------------------------------------------------------

/**
 * Admin JWT payload shape per spec §6.3.
 *
 * Distinct from the existing HCW JWT (`tablet_id` + `facility_id` claims)
 * via the `aud` claim. Both share the JWT_SIGNING_KEY but verify routines
 * check `aud` to prevent cross-use (HCW token rejected by admin verifier
 * and vice-versa).
 */
export interface AdminJwtPayload {
  iss: string;
  aud: 'admin';
  sub: string;
  role: string;
  role_version: number;
  iat: number;
  exp: number;
  jti: string;
}

export interface MintAdminJwtOpts {
  /** Time-to-live in seconds. Default 4 * 3600 (4 hours per spec §6.3). */
  ttl?: number;
  /** Issuer claim. Default 'f2-pwa-worker'. */
  iss?: string;
}

async function importJwtKey(rawB64url: string): Promise<CryptoKey> {
  return crypto.subtle.importKey(
    'raw',
    b64urlDecode(rawB64url),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign', 'verify'],
  );
}

/**
 * Mint an admin JWT. The signing key is the existing JWT_SIGNING_KEY
 * (base64url-encoded raw bytes; same as HCW JWT minting).
 */
export async function mintAdminJwt(
  signingKeyB64url: string,
  claims: Pick<AdminJwtPayload, 'sub' | 'role' | 'role_version'>,
  opts: MintAdminJwtOpts = {},
): Promise<string> {
  const ttl = opts.ttl ?? 4 * 60 * 60;
  const iat = Math.floor(Date.now() / 1000);
  const payload: AdminJwtPayload = {
    iss: opts.iss ?? 'f2-pwa-worker',
    aud: 'admin',
    sub: claims.sub,
    role: claims.role,
    role_version: claims.role_version,
    iat,
    exp: iat + ttl,
    jti: crypto.randomUUID(),
  };
  const header = { alg: 'HS256', typ: 'JWT' };
  const encJson = (o: object) => b64urlEncode(enc.encode(JSON.stringify(o)));
  const signingInput = `${encJson(header)}.${encJson(payload)}`;
  const key = await importJwtKey(signingKeyB64url);
  const sig = await crypto.subtle.sign('HMAC', key, enc.encode(signingInput));
  return `${signingInput}.${b64urlEncode(new Uint8Array(sig))}`;
}

export type AdminJwtVerifyResult =
  | { ok: true; payload: AdminJwtPayload }
  | { ok: false; error: 'malformed' | 'badsig' | 'expired' | 'wrongaud' };

/**
 * Verify an admin JWT. Checks signature, aud=='admin', and exp > now.
 * Does NOT check revocation — caller does that against KV (revoked_jti / revoked_user).
 */
export async function verifyAdminJwt(signingKeyB64url: string, token: string): Promise<AdminJwtVerifyResult> {
  if (!token) return { ok: false, error: 'malformed' };
  const parts = token.split('.');
  if (parts.length !== 3) return { ok: false, error: 'malformed' };
  const [headerEnc, payloadEnc, sigEnc] = parts as [string, string, string];
  let payload: AdminJwtPayload;
  try {
    const headerJson = JSON.parse(new TextDecoder().decode(b64urlDecode(headerEnc))) as { alg?: string };
    if (headerJson.alg !== 'HS256') return { ok: false, error: 'malformed' };
    payload = JSON.parse(new TextDecoder().decode(b64urlDecode(payloadEnc))) as AdminJwtPayload;
  } catch {
    return { ok: false, error: 'malformed' };
  }
  let sigBytes: Uint8Array;
  try {
    sigBytes = b64urlDecode(sigEnc);
  } catch {
    return { ok: false, error: 'malformed' };
  }
  const key = await importJwtKey(signingKeyB64url);
  const valid = await crypto.subtle.verify('HMAC', key, sigBytes, enc.encode(`${headerEnc}.${payloadEnc}`));
  if (!valid) return { ok: false, error: 'badsig' };
  if (payload.aud !== 'admin') return { ok: false, error: 'wrongaud' };
  if (Math.floor(Date.now() / 1000) >= payload.exp) return { ok: false, error: 'expired' };
  return { ok: true, payload };
}
