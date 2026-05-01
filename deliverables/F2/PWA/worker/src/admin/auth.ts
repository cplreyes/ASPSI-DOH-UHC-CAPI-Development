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
