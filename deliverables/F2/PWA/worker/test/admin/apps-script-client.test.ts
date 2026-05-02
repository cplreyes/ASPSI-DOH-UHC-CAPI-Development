/**
 * F2 Admin Portal — Apps Script HMAC client tests.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 1.4)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§6.2)
 *
 * Canonical string for admin RPCs: `${action}.${ts}.${request_id}.${stable_json_payload}`
 * Distinct from PWA submit HMAC (`METHOD|action|ts|body`) — see src/hmac.ts.
 */
import { describe, expect, it } from 'vitest';
import { signRequest, bumpAdminQuota, type QuotaKv } from '../../src/admin/apps-script-client';

describe('signRequest', () => {
  it('produces deterministic HMAC over action.ts.request_id.payload', async () => {
    const sig1 = await signRequest('test-secret', 'admin_users_list', 1700000000, 'req-1', { foo: 'bar' });
    const sig2 = await signRequest('test-secret', 'admin_users_list', 1700000000, 'req-1', { foo: 'bar' });
    expect(sig1).toEqual(sig2);
    expect(sig1).toMatch(/^[a-f0-9]{64}$/);
  });

  it('changes when payload differs', async () => {
    const a = await signRequest('s', 'a', 1, 'r', { x: 1 });
    const b = await signRequest('s', 'a', 1, 'r', { x: 2 });
    expect(a).not.toEqual(b);
  });

  it('changes when secret differs', async () => {
    const a = await signRequest('s1', 'a', 1, 'r', { x: 1 });
    const b = await signRequest('s2', 'a', 1, 'r', { x: 1 });
    expect(a).not.toEqual(b);
  });

  it('changes when request_id differs', async () => {
    const a = await signRequest('s', 'a', 1, 'r1', { x: 1 });
    const b = await signRequest('s', 'a', 1, 'r2', { x: 1 });
    expect(a).not.toEqual(b);
  });

  it('handles empty payload object', async () => {
    const sig = await signRequest('s', 'admin_ping', 1700000000, 'req-1', {});
    expect(sig).toMatch(/^[a-f0-9]{64}$/);
  });

  it('produces canonical key order regardless of input order', async () => {
    const a = await signRequest('s', 'a', 1, 'r', { x: 1, y: 2 });
    const b = await signRequest('s', 'a', 1, 'r', { y: 2, x: 1 });
    expect(a).toEqual(b);
  });
});

describe('bumpAdminQuota', () => {
  function makeKv(initial: Record<string, string> = {}): {
    kv: QuotaKv;
    store: Record<string, string>;
    putCalls: Array<{ key: string; value: string; ttl?: number }>;
  } {
    const store: Record<string, string> = { ...initial };
    const putCalls: Array<{ key: string; value: string; ttl?: number }> = [];
    const kv: QuotaKv = {
      get: async (key) => (key in store ? store[key]! : null),
      put: async (key, value, opts) => {
        store[key] = value;
        putCalls.push({ key, value, ...(opts?.expirationTtl ? { ttl: opts.expirationTtl } : {}) });
      },
    };
    return { kv, store, putCalls };
  }

  it('writes 1 to as_quota:<UTC-date> when key is missing', async () => {
    const { kv, store, putCalls } = makeKv();
    await bumpAdminQuota(kv, new Date(Date.UTC(2026, 4, 2, 12)));
    expect(store['as_quota:2026-05-02']).toBe('1');
    expect(putCalls[0]?.ttl).toBe(7 * 86400);
  });

  it('increments existing counter', async () => {
    const { kv, store } = makeKv({ 'as_quota:2026-05-02': '42' });
    await bumpAdminQuota(kv, new Date(Date.UTC(2026, 4, 2, 12)));
    expect(store['as_quota:2026-05-02']).toBe('43');
  });

  it('treats non-numeric value as 0 (resets)', async () => {
    const { kv, store } = makeKv({ 'as_quota:2026-05-02': 'corrupt' });
    await bumpAdminQuota(kv, new Date(Date.UTC(2026, 4, 2, 12)));
    expect(store['as_quota:2026-05-02']).toBe('1');
  });

  it('uses UTC date — 03:00 UTC after midnight goes into the new day bucket', async () => {
    const { kv, store } = makeKv();
    await bumpAdminQuota(kv, new Date(Date.UTC(2026, 4, 3, 3, 0)));
    expect(store['as_quota:2026-05-03']).toBe('1');
    expect(store['as_quota:2026-05-02']).toBeUndefined();
  });

  it('swallows KV errors (counter is observability, not load-bearing)', async () => {
    const broken: QuotaKv = {
      get: async () => { throw new Error('KV down'); },
      put: async () => undefined,
    };
    await expect(bumpAdminQuota(broken)).resolves.toBeUndefined();
  });
});
