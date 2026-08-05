/**
 * F2 Admin Portal auth — faithful port of worker/src/admin/auth.ts to Node.
 *
 * PBKDF2 password hash format is IDENTICAL (`<saltB64url>:<iters>:<hashB64url>`,
 * 100k iterations, SHA-256, 32-byte salt) so existing admin password hashes
 * migrate as-is at P4. Admin JWTs keep the same claims (aud='admin',
 * role_version, optional pwc) and default issuer so sessions minted by the
 * Worker verify here and vice-versa during cutover.
 */
import type { webcrypto } from 'node:crypto';

const enc = new TextEncoder();
const dec = new TextDecoder();

export const PBKDF2_ITERATIONS = 100_000;
const PBKDF2_FLOOR = 10_000;
const PBKDF2_CEIL = 100_000;
const HASH_LEN_BITS = 256;
const SALT_LEN = 32;

function b64urlEncode(bytes: Uint8Array): string {
  return Buffer.from(bytes).toString('base64url');
}

function b64urlDecode(s: string): Uint8Array {
  return new Uint8Array(Buffer.from(s, 'base64url'));
}

function timingSafeEqual(a: Uint8Array, b: Uint8Array): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a[i]! ^ b[i]!;
  return diff === 0;
}

async function pbkdf2(password: string, salt: Uint8Array, iters: number): Promise<Uint8Array> {
  const baseKey = await crypto.subtle.importKey('raw', enc.encode(password), 'PBKDF2', false, ['deriveBits']);
  const bits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt, iterations: iters, hash: 'SHA-256' },
    baseKey,
    HASH_LEN_BITS,
  );
  return new Uint8Array(bits);
}

/** Hash a plaintext password. Returns `<saltB64url>:<iters>:<hashB64url>`. */
export async function hashPassword(password: string): Promise<string> {
  const salt = crypto.getRandomValues(new Uint8Array(SALT_LEN));
  const hash = await pbkdf2(password, salt, PBKDF2_ITERATIONS);
  return `${b64urlEncode(salt)}:${PBKDF2_ITERATIONS}:${b64urlEncode(hash)}`;
}

/**
 * Lazy-cached dummy hash used to timing-equalize verifyPassword when the
 * username doesn't exist (username-enumeration defense — Worker parity).
 */
let dummyHashCache: string | null = null;
export async function getDummyPasswordHash(): Promise<string> {
  if (dummyHashCache) return dummyHashCache;
  const salt = new Uint8Array(SALT_LEN); // all zeros, intentional
  const probe = '__F2_PWA_ADMIN_DUMMY_HASH_PROBE_v1__';
  const hash = await pbkdf2(probe, salt, PBKDF2_ITERATIONS);
  dummyHashCache = `${b64urlEncode(salt)}:${PBKDF2_ITERATIONS}:${b64urlEncode(hash)}`;
  return dummyHashCache;
}

/** Verify a plaintext password against a stored hash. Never throws. */
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
// Admin JWT — mint + verify (spec §6.3; identical to the Worker's)
// ---------------------------------------------------------------------------

export interface AdminJwtPayload {
  iss: string;
  aud: 'admin';
  sub: string;
  role: string;
  role_version: number;
  iat: number;
  exp: number;
  jti: string;
  /** Present + true when the user owes a password rotation (R2-#57). */
  pwc?: boolean;
}

export interface MintAdminJwtOpts {
  /** Time-to-live in seconds. Default 4h per spec §6.3. */
  ttl?: number;
  /** Issuer claim. Default matches the Worker so tokens interop at cutover. */
  iss?: string;
}

async function importJwtKey(rawB64url: string): Promise<webcrypto.CryptoKey> {
  return crypto.subtle.importKey(
    'raw',
    b64urlDecode(rawB64url),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign', 'verify'],
  );
}

export async function mintAdminJwt(
  signingKeyB64url: string,
  claims: Pick<AdminJwtPayload, 'sub' | 'role' | 'role_version'> & { pwc?: boolean },
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
    ...(claims.pwc ? { pwc: true } : {}),
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

/** Verify signature + aud + exp. Revocation is the caller's job (auth_kv). */
export async function verifyAdminJwt(signingKeyB64url: string, token: string): Promise<AdminJwtVerifyResult> {
  if (!token) return { ok: false, error: 'malformed' };
  const parts = token.split('.');
  if (parts.length !== 3) return { ok: false, error: 'malformed' };
  const [headerEnc, payloadEnc, sigEnc] = parts as [string, string, string];
  let payload: AdminJwtPayload;
  try {
    const headerJson = JSON.parse(dec.decode(b64urlDecode(headerEnc))) as { alg?: string };
    if (headerJson.alg !== 'HS256') return { ok: false, error: 'malformed' };
    payload = JSON.parse(dec.decode(b64urlDecode(payloadEnc))) as AdminJwtPayload;
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

// ---------------------------------------------------------------------------
// Permission projection (FX-002 #324) — advisory perm map for nav gating.
// ---------------------------------------------------------------------------

export const PERM_KEYS = [
  'dash_data', 'dash_report', 'dash_apps', 'dash_users', 'dash_roles',
  'dict_self_admin_up', 'dict_self_admin_down',
  'dict_paper_encoded_up', 'dict_paper_encoded_down',
  'dict_capi_up', 'dict_capi_down',
] as const;

export type PermKey = (typeof PERM_KEYS)[number];
export type PermissionSet = Record<string, boolean>;

export function projectPermissions(role: Record<string, unknown>): PermissionSet {
  const out: PermissionSet = {};
  for (const k of PERM_KEYS) out[k] = !!role[k];
  return out;
}
