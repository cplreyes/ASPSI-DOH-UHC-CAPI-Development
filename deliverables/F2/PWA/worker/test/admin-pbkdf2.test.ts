/**
 * verifyAdminPassword tests — Issue #35.
 *
 * Cloudflare Workers caps `crypto.subtle.deriveBits` PBKDF2 iterations at 100,000;
 * values above throw NotSupportedError at runtime. The verifier is built to fail
 * fast (return false, not throw) when a stored hash claims iterations above
 * `MAX_PBKDF2_ITERS`, so a misconfigured secret degrades to "login denied"
 * instead of "Internal Worker error".
 *
 * Note: Node's webcrypto in vitest does NOT enforce the 100k cap — it'll happily
 * deriveBits at 600k. So we can't test "Workers throws on 600k" directly; instead
 * we test the verifier's stored-iterations ceiling check, which makes the cap a
 * test-enforced contract regardless of runtime.
 */
import { describe, expect, it } from 'vitest';
import { webcrypto } from 'node:crypto';
import { verifyAdminPassword, MAX_PBKDF2_ITERS } from '../src/admin';

function b64url(bytes: Uint8Array): string {
  return Buffer.from(bytes)
    .toString('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

async function makeHash(password: string, iterations: number): Promise<string> {
  const salt = webcrypto.getRandomValues(new Uint8Array(16));
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
  return `${b64url(salt)}:${iterations}:${b64url(new Uint8Array(bits))}`;
}

describe('verifyAdminPassword — Issue #35 PBKDF2 cap', () => {
  it('verifies a 100k-iter hash for the correct password', async () => {
    const stored = await makeHash('correct-password-123', 100_000);
    expect(await verifyAdminPassword('correct-password-123', stored)).toBe(true);
  });

  it('rejects the wrong password against a 100k-iter hash', async () => {
    const stored = await makeHash('correct-password-123', 100_000);
    expect(await verifyAdminPassword('wrong-password', stored)).toBe(false);
  });

  it('rejects a hash with iterations above MAX_PBKDF2_ITERS without throwing', async () => {
    // Generate a 600k hash with Node crypto (which has no cap), then prove the
    // verifier refuses to attempt deriveBits against it (Workers would throw).
    const stored = await makeHash('correct-password-123', 600_000);
    expect(MAX_PBKDF2_ITERS).toBe(100_000);
    expect(await verifyAdminPassword('correct-password-123', stored)).toBe(false);
  });

  it('rejects iterations below the 10k floor', async () => {
    const stored = await makeHash('correct-password-123', 9_999);
    expect(await verifyAdminPassword('correct-password-123', stored)).toBe(false);
  });

  it('rejects malformed hash strings', async () => {
    expect(await verifyAdminPassword('any', 'no-colons')).toBe(false);
    expect(await verifyAdminPassword('any', 'a:b')).toBe(false);
    expect(await verifyAdminPassword('any', 'a:notanumber:c')).toBe(false);
    expect(await verifyAdminPassword('any', '')).toBe(false);
  });

  it('rejects iterations of 0 (parseInt edge case)', async () => {
    expect(await verifyAdminPassword('any', 'salt:0:hash')).toBe(false);
  });
});
