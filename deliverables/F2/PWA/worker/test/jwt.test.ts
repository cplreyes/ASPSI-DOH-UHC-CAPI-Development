/**
 * Unit tests for JWT mint + verify.
 * Spec §8.1.
 *
 * Run: npm test
 *
 * Note: vitest in node uses globalThis.crypto.subtle natively (Node 19+).
 * If running under older Node, install `@cloudflare/vitest-pool-workers` and
 * switch the test pool to Workers; the tests themselves remain the same.
 */
import { describe, expect, it } from 'vitest';
import { mintJwt, verifyJwt, parseClaimsUnsafe } from '../src/jwt';
import type { JwtClaims } from '../src/types';

// 32-byte base64url key, deterministic for tests.
const TEST_KEY = 'YWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWE';

function makeClaims(overrides: Partial<JwtClaims> = {}): JwtClaims {
  const nowS = Math.floor(Date.now() / 1000);
  return {
    jti: 'test-jti-1',
    tablet_id: 'tablet-uuid-1',
    facility_id: 'F-001',
    iat: nowS,
    exp: nowS + 3600,
    ...overrides,
  };
}

describe('jwt: mint + verify', () => {
  it('mints a token that verifies cleanly', async () => {
    const claims = makeClaims();
    const token = await mintJwt(claims, TEST_KEY);
    expect(token.split('.').length).toBe(3);
    const result = await verifyJwt(token, TEST_KEY);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.claims.jti).toBe(claims.jti);
      expect(result.claims.facility_id).toBe('F-001');
    }
  });

  it('rejects a tampered payload', async () => {
    const token = await mintJwt(makeClaims(), TEST_KEY);
    const [h, _p, s] = token.split('.');
    // Swap in a payload claiming a different facility, keep original signature.
    const tamperedPayload = btoa(JSON.stringify(makeClaims({ facility_id: 'F-666' })))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=+$/, '');
    const tampered = `${h}.${tamperedPayload}.${s}`;
    const result = await verifyJwt(tampered, TEST_KEY);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toBe('bad-signature');
  });

  it('rejects an expired token', async () => {
    const nowS = Math.floor(Date.now() / 1000);
    const expired = await mintJwt(makeClaims({ iat: nowS - 7200, exp: nowS - 3600 }), TEST_KEY);
    const result = await verifyJwt(expired, TEST_KEY);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toBe('expired');
  });

  it('tolerates ±5 minutes of iat clock skew (field tablet RTC drift)', async () => {
    // iat 4 minutes in the future is acceptable.
    const nowS = Math.floor(Date.now() / 1000);
    const skewedFuture = await mintJwt(makeClaims({ iat: nowS + 240, exp: nowS + 3600 }), TEST_KEY);
    const result = await verifyJwt(skewedFuture, TEST_KEY);
    expect(result.ok).toBe(true);
  });

  it('rejects iat too far in the future (>5 minutes)', async () => {
    const nowS = Math.floor(Date.now() / 1000);
    const tooFarFuture = await mintJwt(makeClaims({ iat: nowS + 600, exp: nowS + 3600 }), TEST_KEY);
    const result = await verifyJwt(tooFarFuture, TEST_KEY);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toBe('iat-future');
  });

  it('rejects malformed tokens', async () => {
    const result = await verifyJwt('not.a.jwt.token', TEST_KEY);
    expect(result.ok).toBe(false);
  });

  it('parseClaimsUnsafe returns claims without verifying', () => {
    const claims = makeClaims();
    return mintJwt(claims, TEST_KEY).then((token) => {
      const parsed = parseClaimsUnsafe(token);
      expect(parsed?.facility_id).toBe('F-001');
    });
  });

  it('replay: same token verifies repeatedly within TTL (design property, not a bug)', async () => {
    const token = await mintJwt(makeClaims(), TEST_KEY);
    const r1 = await verifyJwt(token, TEST_KEY);
    const r2 = await verifyJwt(token, TEST_KEY);
    expect(r1.ok).toBe(true);
    expect(r2.ok).toBe(true);
    // Replay protection is delegated to Apps Script's client_submission_id dedup.
    // See spec §8.1 and §13.
  });
});
