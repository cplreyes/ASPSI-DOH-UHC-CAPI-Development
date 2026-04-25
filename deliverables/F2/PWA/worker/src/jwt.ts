/**
 * HS256 JWT mint + verify using the Web Crypto API.
 * Zero deps. Spec: §5 Token format.
 */
import type { JwtClaims } from './types';

const enc = new TextEncoder();
const dec = new TextDecoder();

/** ±5 minutes of clock skew tolerance for `iat` (spec §8.1). */
const CLOCK_SKEW_S = 300;

function b64urlEncode(bytes: Uint8Array | string): string {
  const buf = typeof bytes === 'string' ? enc.encode(bytes) : bytes;
  let str = '';
  for (let i = 0; i < buf.length; i++) str += String.fromCharCode(buf[i]!);
  return btoa(str).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function b64urlDecode(s: string): Uint8Array {
  const padded = s.replace(/-/g, '+').replace(/_/g, '/') + '==='.slice((s.length + 3) % 4);
  const bin = atob(padded);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

async function importHmacKey(rawB64url: string): Promise<CryptoKey> {
  const keyBytes = b64urlDecode(rawB64url);
  return crypto.subtle.importKey('raw', keyBytes, { name: 'HMAC', hash: 'SHA-256' }, false, [
    'sign',
    'verify',
  ]);
}

/** Mint a JWT with the given claims. The `iat` and `exp` must already be set on the claims object. */
export async function mintJwt(claims: JwtClaims, signingKeyB64url: string): Promise<string> {
  const header = { alg: 'HS256', typ: 'JWT' };
  const headerEnc = b64urlEncode(JSON.stringify(header));
  const payloadEnc = b64urlEncode(JSON.stringify(claims));
  const signingInput = `${headerEnc}.${payloadEnc}`;

  const key = await importHmacKey(signingKeyB64url);
  const sig = await crypto.subtle.sign('HMAC', key, enc.encode(signingInput));
  const sigEnc = b64urlEncode(new Uint8Array(sig));
  return `${signingInput}.${sigEnc}`;
}

export type JwtVerifyResult =
  | { ok: true; claims: JwtClaims }
  | { ok: false; reason: 'malformed' | 'bad-signature' | 'expired' | 'iat-future' | 'missing-claim' };

/**
 * Verify a JWT and return its claims if valid.
 * Checks: signature, exp (>= now), iat (<= now + clock skew), required claim presence.
 * Does NOT check revocation — the caller does that against KV.
 */
export async function verifyJwt(token: string, signingKeyB64url: string): Promise<JwtVerifyResult> {
  const parts = token.split('.');
  if (parts.length !== 3) return { ok: false, reason: 'malformed' };
  const [headerEnc, payloadEnc, sigEnc] = parts as [string, string, string];

  let claims: JwtClaims;
  try {
    const headerJson = JSON.parse(dec.decode(b64urlDecode(headerEnc))) as { alg?: string };
    if (headerJson.alg !== 'HS256') return { ok: false, reason: 'malformed' };
    claims = JSON.parse(dec.decode(b64urlDecode(payloadEnc))) as JwtClaims;
  } catch {
    return { ok: false, reason: 'malformed' };
  }

  // Verify signature.
  const key = await importHmacKey(signingKeyB64url);
  const valid = await crypto.subtle.verify(
    'HMAC',
    key,
    b64urlDecode(sigEnc),
    enc.encode(`${headerEnc}.${payloadEnc}`),
  );
  if (!valid) return { ok: false, reason: 'bad-signature' };

  // Required claims.
  if (!claims.jti || !claims.tablet_id || !claims.facility_id || !claims.iat || !claims.exp) {
    return { ok: false, reason: 'missing-claim' };
  }

  const nowS = Math.floor(Date.now() / 1000);
  if (claims.exp < nowS) return { ok: false, reason: 'expired' };
  // iat must not be more than CLOCK_SKEW_S in the future (field tablet RTC drift tolerance).
  if (claims.iat > nowS + CLOCK_SKEW_S) return { ok: false, reason: 'iat-future' };

  return { ok: true, claims };
}

/** Parse claims from a JWT WITHOUT verifying. For UI-side display only — never trust this server-side. */
export function parseClaimsUnsafe(token: string): JwtClaims | null {
  const parts = token.split('.');
  if (parts.length !== 3) return null;
  try {
    return JSON.parse(dec.decode(b64urlDecode(parts[1]!))) as JwtClaims;
  } catch {
    return null;
  }
}
