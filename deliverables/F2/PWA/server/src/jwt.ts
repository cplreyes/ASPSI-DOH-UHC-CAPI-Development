/**
 * HS256 JWT verify — faithful port of worker/src/jwt.ts so the SAME device
 * tokens (same JWT_SIGNING_KEY) verify identically on the box. Uses Node's
 * WebCrypto (globalThis.crypto.subtle), so the code matches the Worker's.
 * mintJwt is exported for tests and the future admin (P1b) reissue port.
 */

export interface JwtClaims {
  jti: string;
  tablet_id: string;
  facility_id: string;
  iat: number;
  exp: number;
  /** 12-digit Questionnaire Number; absent on pre-qn tokens. */
  qn?: string;
}

/**
 * Sentinel `tablet_id` for a Model-C facility QR token (design
 * F2-Model-C-Self-Register-2026-07-16): NOT bound to an HCW. Only `/self-register`
 * accepts a token carrying it, and the admin facility-token mint stamps it — so a
 * stray per-HCW device token or admin session can never spawn a self-registered case.
 */
export const SELF_REGISTER_TABLET_ID = '__self_register__';

import type { webcrypto } from 'node:crypto';

const enc = new TextEncoder();
const dec = new TextDecoder();
/** Field-tablet RTC drift tolerance for iat-in-the-future (matches the Worker). */
const CLOCK_SKEW_S = 300;

function b64urlEncode(input: string | Uint8Array): string {
  const bytes = typeof input === 'string' ? enc.encode(input) : input;
  return Buffer.from(bytes).toString('base64url');
}

function b64urlDecode(s: string): Uint8Array {
  return new Uint8Array(Buffer.from(s, 'base64url'));
}

async function importHmacKey(signingKeyB64url: string): Promise<webcrypto.CryptoKey> {
  const keyBytes = b64urlDecode(signingKeyB64url);
  return crypto.subtle.importKey('raw', keyBytes, { name: 'HMAC', hash: 'SHA-256' }, false, [
    'sign',
    'verify',
  ]);
}

/** Mint a JWT with the given claims. `iat`/`exp` must already be set. */
export async function mintJwt(claims: JwtClaims, signingKeyB64url: string): Promise<string> {
  const headerEnc = b64urlEncode(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const payloadEnc = b64urlEncode(JSON.stringify(claims));
  const signingInput = `${headerEnc}.${payloadEnc}`;
  const key = await importHmacKey(signingKeyB64url);
  const sig = await crypto.subtle.sign('HMAC', key, enc.encode(signingInput));
  return `${signingInput}.${b64urlEncode(new Uint8Array(sig))}`;
}

export type JwtVerifyResult =
  | { ok: true; claims: JwtClaims }
  | { ok: false; reason: 'malformed' | 'bad-signature' | 'expired' | 'iat-future' | 'missing-claim' };

/**
 * Verify a JWT and return its claims if valid.
 * Checks: signature, exp (>= now), iat (<= now + clock skew), required claims.
 * Does NOT check revocation — the caller does that against auth_revoked.
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

  const key = await importHmacKey(signingKeyB64url);
  const valid = await crypto.subtle.verify(
    'HMAC',
    key,
    b64urlDecode(sigEnc),
    enc.encode(`${headerEnc}.${payloadEnc}`),
  );
  if (!valid) return { ok: false, reason: 'bad-signature' };

  if (!claims.jti || !claims.tablet_id || !claims.facility_id || !claims.iat || !claims.exp) {
    return { ok: false, reason: 'missing-claim' };
  }

  const nowS = Math.floor(Date.now() / 1000);
  if (claims.exp < nowS) return { ok: false, reason: 'expired' };
  if (claims.iat > nowS + CLOCK_SKEW_S) return { ok: false, reason: 'iat-future' };

  return { ok: true, claims };
}
