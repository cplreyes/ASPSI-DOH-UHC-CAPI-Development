/**
 * F2 Admin Portal — login throttle tests.
 *
 * Two-axis throttle: per-username (10 attempts / 15 min) + per-IP (50 / 15 min).
 * Per-username is the correctness control; per-IP is the spam shield.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 1.9)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§5.10, §10.1)
 */
import { describe, expect, it } from 'vitest';
import { checkLoginThrottle, recordFailedLogin, resetLoginThrottle } from '../../src/admin/throttle';

interface FakeKV {
  get(k: string): Promise<string | null>;
  put(k: string, v: string, opts?: { expirationTtl?: number }): Promise<void>;
  delete(k: string): Promise<void>;
  _store: Map<string, string>;
  _puts: Array<{ key: string; value: string; ttl?: number }>;
}

function makeKv(): FakeKV {
  const store = new Map<string, string>();
  const puts: Array<{ key: string; value: string; ttl?: number }> = [];
  return {
    async get(k) { return store.get(k) ?? null; },
    async put(k, v, opts) { store.set(k, v); puts.push({ key: k, value: v, ttl: opts?.expirationTtl }); },
    async delete(k) { store.delete(k); },
    _store: store,
    _puts: puts,
  };
}

describe('login throttle', () => {
  it('allows the first attempt for a fresh user/ip', async () => {
    const kv = makeKv();
    const r = await checkLoginThrottle(kv, 'alice', 'iphash-1');
    expect(r.allowed).toBe(true);
  });

  it('locks per-username after 10 fails in window', async () => {
    const kv = makeKv();
    for (let i = 0; i < 10; i++) await recordFailedLogin(kv, 'alice', 'iphash-1');
    const r = await checkLoginThrottle(kv, 'alice', 'different-ip');
    expect(r.allowed).toBe(false);
    expect(r.reason).toBe('username');
  });

  it('does NOT lock per-username at 9 fails', async () => {
    const kv = makeKv();
    for (let i = 0; i < 9; i++) await recordFailedLogin(kv, 'alice', 'iphash-1');
    const r = await checkLoginThrottle(kv, 'alice', 'iphash-1');
    expect(r.allowed).toBe(true);
  });

  it('locks per-IP after 50 fails across users', async () => {
    const kv = makeKv();
    for (let i = 0; i < 50; i++) await recordFailedLogin(kv, `user${i}`, 'shared-ip');
    const r = await checkLoginThrottle(kv, 'newuser', 'shared-ip');
    expect(r.allowed).toBe(false);
    expect(r.reason).toBe('ip');
  });

  it('allows another username on a different IP after one IP is locked', async () => {
    const kv = makeKv();
    for (let i = 0; i < 50; i++) await recordFailedLogin(kv, `user${i}`, 'bad-ip');
    const r = await checkLoginThrottle(kv, 'newuser', 'good-ip');
    expect(r.allowed).toBe(true);
  });

  it('resets per-username after success', async () => {
    const kv = makeKv();
    for (let i = 0; i < 5; i++) await recordFailedLogin(kv, 'alice', 'iphash-1');
    await resetLoginThrottle(kv, 'alice');
    const r = await checkLoginThrottle(kv, 'alice', 'iphash-1');
    expect(r.allowed).toBe(true);
  });

  it('records both per-username and per-IP counters on failed login', async () => {
    const kv = makeKv();
    await recordFailedLogin(kv, 'alice', 'iphash-1');
    expect(kv._puts.length).toBe(2);
    const keys = kv._puts.map(p => p.key);
    expect(keys.some(k => k.includes('user:alice'))).toBe(true);
    expect(keys.some(k => k.includes('ip:iphash-1'))).toBe(true);
  });

  it('sets expirationTtl matching the window length', async () => {
    const kv = makeKv();
    await recordFailedLogin(kv, 'alice', 'iphash-1');
    expect(kv._puts.every(p => p.ttl === 15 * 60)).toBe(true);
  });
});
