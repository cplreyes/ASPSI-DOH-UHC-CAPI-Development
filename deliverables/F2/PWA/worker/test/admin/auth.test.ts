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

import { mintAdminJwt, verifyAdminJwt } from '../../src/admin/auth';

// JWT signing key in the existing Worker is base64url-encoded raw 32 bytes.
// For tests we generate a fresh key per run.
function fakeKey(): string {
  const bytes = new Uint8Array(32);
  for (let i = 0; i < bytes.length; i++) bytes[i] = i;
  // base64url-encode without padding
  let s = '';
  for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]!);
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

describe('mintAdminJwt / verifyAdminJwt', () => {
  const KEY = fakeKey();

  it('round-trips a valid token', async () => {
    const tok = await mintAdminJwt(KEY, { sub: 'carl', role: 'Administrator', role_version: 1 });
    const v = await verifyAdminJwt(KEY, tok);
    expect(v.ok).toBe(true);
    if (v.ok) {
      expect(v.payload.sub).toBe('carl');
      expect(v.payload.role).toBe('Administrator');
      expect(v.payload.role_version).toBe(1);
      expect(v.payload.aud).toBe('admin');
      expect(v.payload.iss).toBe('f2-pwa-worker');
      expect(typeof v.payload.jti).toBe('string');
      expect(v.payload.jti.length).toBeGreaterThan(0);
    }
  });

  it('rejects a tampered token', async () => {
    const tok = await mintAdminJwt(KEY, { sub: 'carl', role: 'Administrator', role_version: 1 });
    const tampered = tok.slice(0, -2) + 'xx';
    const v = await verifyAdminJwt(KEY, tampered);
    expect(v.ok).toBe(false);
  });

  it('rejects an expired token', async () => {
    const tok = await mintAdminJwt(KEY, { sub: 'carl', role: 'Administrator', role_version: 1 }, { ttl: -1 });
    const v = await verifyAdminJwt(KEY, tok);
    expect(v.ok).toBe(false);
    if (!v.ok) expect(v.error).toBe('expired');
  });

  it('rejects a token signed with a different key', async () => {
    const tok = await mintAdminJwt(KEY, { sub: 'carl', role: 'Administrator', role_version: 1 });
    const otherKey = fakeKey().slice(0, -1) + 'A'; // tweak last char
    const v = await verifyAdminJwt(otherKey, tok);
    expect(v.ok).toBe(false);
  });

  it('rejects a token with wrong aud (HCW JWT misused as admin)', async () => {
    // Construct a token with aud=hcw and verify it fails admin verification.
    const enc = new TextEncoder();
    const header = { alg: 'HS256', typ: 'JWT' };
    const payload = { iss: 'f2-pwa-worker', aud: 'hcw', sub: 'x', role: 'r', role_version: 1, iat: 1, exp: Date.now()/1000 + 60, jti: 'j' };
    function b64url(b: Uint8Array | string): string {
      const buf = typeof b === 'string' ? enc.encode(b) : b;
      let s = ''; for (let i = 0; i < buf.length; i++) s += String.fromCharCode(buf[i]!);
      return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    }
    const headerEnc = b64url(JSON.stringify(header));
    const payloadEnc = b64url(JSON.stringify(payload));
    const signingInput = `${headerEnc}.${payloadEnc}`;
    function unb64url(s: string): Uint8Array {
      const padded = s.replace(/-/g, '+').replace(/_/g, '/') + '==='.slice((s.length + 3) % 4);
      const bin = atob(padded);
      const out = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
      return out;
    }
    const key = await crypto.subtle.importKey('raw', unb64url(KEY), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
    const sig = await crypto.subtle.sign('HMAC', key, enc.encode(signingInput));
    let sigStr = ''; const sigBytes = new Uint8Array(sig);
    for (let i = 0; i < sigBytes.length; i++) sigStr += String.fromCharCode(sigBytes[i]!);
    const tok = `${signingInput}.${btoa(sigStr).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')}`;
    const v = await verifyAdminJwt(KEY, tok);
    expect(v.ok).toBe(false);
    if (!v.ok) expect(v.error).toBe('wrongaud');
  });

  it('rejects malformed tokens', async () => {
    expect((await verifyAdminJwt(KEY, 'not.a.jwt.token.has.too.many.dots')).ok).toBe(false);
    expect((await verifyAdminJwt(KEY, 'one-segment-only')).ok).toBe(false);
    expect((await verifyAdminJwt(KEY, '')).ok).toBe(false);
  });
});
