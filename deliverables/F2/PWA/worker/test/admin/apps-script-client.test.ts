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
import { signRequest } from '../../src/admin/apps-script-client';

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
