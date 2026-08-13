/**
 * Numbered short-link claim helpers (design F2-Model-C-Numbered-Links-2026-07-16).
 *
 * A per-HCW link is `<origin>/e/<slug>?k=<secret>` where slug = `<CODE>-HCW-<NN>`
 * (a human label for one pre-provisioned QN slot) and secret is a 6-char Crockford
 * base32 string (~30 bits). Only an HMAC of the secret — keyed with the JWT signing
 * key — is stored, so a DB-only leak can't derive live secrets; verification is
 * constant-time.
 */
import { createHmac, randomBytes, timingSafeEqual } from 'node:crypto';

// Crockford base32, lower-cased, minus the ambiguous i/l/o/u → exactly 32 chars,
// so `byte % 32` is unbiased (256 is a multiple of 32).
const SECRET_ALPHABET = '0123456789abcdefghjkmnpqrstvwxyz';
const SECRET_LEN = 6;

/** `^[A-Z0-9]{2,12}$` — admin-chosen facility short-code (upper-cased). */
export const SHORT_CODE_RE = /^[A-Z0-9]{2,12}$/;
/** Full slug shape, case-insensitive: `<CODE>-HCW-<seq>`. */
export const SLUG_RE = /^[A-Z0-9]{2,12}-HCW-\d{1,4}$/;

/** `LPHBAY` + 19 → `LPHBAY-HCW-19` (seq zero-padded to 2, wider if needed). */
export function buildSlug(shortCode: string, seq: number): string {
  return `${shortCode.toUpperCase()}-HCW-${String(seq).padStart(2, '0')}`;
}

/** Normalise a slug from the URL path for lookup (codes are stored upper-cased). */
export function normalizeSlug(raw: string): string {
  return raw.trim().toUpperCase();
}

/** A fresh 6-char secret. Unbiased over a 32-char alphabet. */
export function generateSecret(): string {
  const bytes = randomBytes(SECRET_LEN);
  let out = '';
  for (let i = 0; i < SECRET_LEN; i++) out += SECRET_ALPHABET[bytes[i]! % 32];
  return out;
}

/** HMAC-SHA256(secret, signingKey) as hex. signingKey is the b64url JWT key. */
export function secretHmac(secret: string, signingKeyB64url: string): string {
  const key = Buffer.from(signingKeyB64url, 'base64url');
  return createHmac('sha256', key).update(secret.trim().toLowerCase()).digest('hex');
}

/** Constant-time check of a presented secret against the stored HMAC. */
export function verifySecret(secret: string, storedHmac: string, signingKeyB64url: string): boolean {
  if (!secret || !storedHmac) return false;
  const expected = Buffer.from(storedHmac, 'hex');
  const actual = Buffer.from(secretHmac(secret, signingKeyB64url), 'hex');
  if (expected.length !== actual.length || expected.length === 0) return false;
  return timingSafeEqual(expected, actual);
}
