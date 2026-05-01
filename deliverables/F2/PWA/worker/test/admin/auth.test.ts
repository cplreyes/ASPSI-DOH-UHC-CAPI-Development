/**
 * F2 Admin Portal — auth tests (PBKDF2 + JWT).
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Tasks 1.7, 1.8)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§5.4, §6.3, §10.1)
 *
 * Iteration count: 100,000 (Cloudflare Workers runtime cap; Workers throws
 * NotSupportedError for deriveBits iterations above 100k). Spec originally
 * called for 600k via Web Crypto; this is a documented runtime constraint
 * already discovered in the existing src/admin.ts (Issue #35).
 */
import { describe, expect, it } from 'vitest';
import { hashPassword, verifyPassword } from '../../src/admin/auth';

describe('hashPassword / verifyPassword', () => {
  it('produces a hash of the documented format saltB64url:iters:hashB64url with iters=100000', async () => {
    const h = await hashPassword('PasSwOrD7!');
    const parts = h.split(':');
    expect(parts).toHaveLength(3);
    expect(Number(parts[1])).toBe(100000);
    expect(parts[0]).toMatch(/^[A-Za-z0-9_-]+$/);
    expect(parts[2]).toMatch(/^[A-Za-z0-9_-]+$/);
  });

  it('verifies a correct password', async () => {
    const h = await hashPassword('correct');
    expect(await verifyPassword('correct', h)).toBe(true);
  });

  it('rejects a wrong password', async () => {
    const h = await hashPassword('correct');
    expect(await verifyPassword('wrong', h)).toBe(false);
  });

  it('rejects a malformed hash without throwing', async () => {
    expect(await verifyPassword('x', 'not-a-hash')).toBe(false);
    expect(await verifyPassword('x', 'a:b')).toBe(false);
    expect(await verifyPassword('x', '')).toBe(false);
  });

  it('rejects a hash claiming below the 10k floor without throwing', async () => {
    // Fabricated hash with iters=1 — verifier should reject without attempting derive.
    expect(await verifyPassword('x', 'AAAA:1:AAAA')).toBe(false);
  });

  it('rejects a hash claiming above Workers 100k cap without throwing', async () => {
    // Fabricated hash with iters=600000 — verifier rejects (would soft-brick at runtime).
    expect(await verifyPassword('x', 'AAAA:600000:AAAA')).toBe(false);
  });

  it('produces a different hash for the same password (different salts)', async () => {
    const h1 = await hashPassword('same-pw');
    const h2 = await hashPassword('same-pw');
    expect(h1).not.toEqual(h2);
    expect(await verifyPassword('same-pw', h1)).toBe(true);
    expect(await verifyPassword('same-pw', h2)).toBe(true);
  });
});
