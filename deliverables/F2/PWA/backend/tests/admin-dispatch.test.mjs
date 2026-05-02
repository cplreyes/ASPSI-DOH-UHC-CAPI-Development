import { describe, it, expect } from 'vitest';
import { createHmac } from 'node:crypto';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const Dispatch = require('../src/AdminDispatch.js');

const SECRET = 'test-hmac-secret';

function nodeHmacHex(secret, message) {
  return createHmac('sha256', secret).update(message).digest('hex');
}

function signEnvelope({ action, ts, request_id, payload }) {
  const canonical = Dispatch._canonicalAdminString(action, ts, request_id, payload);
  return nodeHmacHex(SECRET, canonical);
}

function envelope(overrides = {}) {
  const ts = overrides.ts ?? Math.floor(1700000000000 / 1000);
  const action = overrides.action ?? 'admin_users_list';
  const request_id = overrides.request_id ?? 'req-uuid-1';
  const payload = overrides.payload ?? {};
  const e = { action, ts, request_id, payload };
  e.hmac = overrides.hmac ?? signEnvelope(e);
  return e;
}

describe('_stableJson', () => {
  it('serializes scalars and null/undefined as-is', () => {
    expect(Dispatch._stableJson(null)).toBe('null');
    expect(Dispatch._stableJson(undefined)).toBe('null');
    expect(Dispatch._stableJson(42)).toBe('42');
    expect(Dispatch._stableJson('hi')).toBe('"hi"');
    expect(Dispatch._stableJson(true)).toBe('true');
  });

  it('serializes arrays without sorting their elements', () => {
    expect(Dispatch._stableJson([3, 1, 2])).toBe('[3,1,2]');
  });

  it('sorts top-level object keys alphabetically', () => {
    const out = Dispatch._stableJson({ z: 1, a: 2, m: 3 });
    expect(out).toBe('{"a":2,"m":3,"z":1}');
  });

  it('produces identical output for equivalent objects with different key order (HMAC stability)', () => {
    const a = Dispatch._stableJson({ username: 'alice', role: 'admin' });
    const b = Dispatch._stableJson({ role: 'admin', username: 'alice' });
    expect(a).toBe(b);
  });
});

describe('_isAdminEnvelope', () => {
  it('returns the envelope when shape and admin_ prefix match', () => {
    const e = envelope();
    expect(Dispatch._isAdminEnvelope(e)).toBe(e);
  });

  it('returns null when action lacks admin_ prefix', () => {
    expect(Dispatch._isAdminEnvelope({ action: 'submit', ts: 1, request_id: 'r', hmac: 'x' })).toBeNull();
  });

  it('returns null on non-objects', () => {
    expect(Dispatch._isAdminEnvelope(null)).toBeNull();
    expect(Dispatch._isAdminEnvelope('a string')).toBeNull();
  });

  it('returns null when required fields are missing', () => {
    expect(Dispatch._isAdminEnvelope({ action: 'admin_x' })).toBeNull();
    expect(Dispatch._isAdminEnvelope({ action: 'admin_x', ts: 1, request_id: '' , hmac: 'h' })).toBeNull();
    expect(Dispatch._isAdminEnvelope({ action: 'admin_x', ts: 1, request_id: 'r', hmac: '' })).toBeNull();
  });
});

describe('_verifyAdminEnvelope', () => {
  const deps = { hmacSha256Hex: nodeHmacHex, nowMs: () => 1700000000000 };

  it('accepts a freshly-signed envelope', () => {
    const e = envelope();
    expect(Dispatch._verifyAdminEnvelope(e, SECRET, deps)).toEqual({ ok: true });
  });

  it('rejects a stale ts (more than 5 minutes off)', () => {
    const e = envelope({ ts: Math.floor(1700000000000 / 1000) - 600 });
    const r = Dispatch._verifyAdminEnvelope(e, SECRET, deps);
    expect(r.ok).toBe(false);
    expect(r.error.code).toBe('E_TS_SKEW');
  });

  it('rejects ms-based ts that is also stale', () => {
    const e = envelope({ ts: 1700000000000 - 600000 });
    e.hmac = signEnvelope(e); // re-sign so only ts skew remains
    const r = Dispatch._verifyAdminEnvelope(e, SECRET, deps);
    expect(r.error.code).toBe('E_TS_SKEW');
  });

  it('accepts ms-based ts within window', () => {
    const e = envelope({ ts: 1700000000000 });
    e.hmac = signEnvelope(e);
    const r = Dispatch._verifyAdminEnvelope(e, SECRET, deps);
    expect(r.ok).toBe(true);
  });

  it('rejects E_TS_INVALID when ts is non-numeric', () => {
    const e = envelope({ ts: 'not-a-number' });
    const r = Dispatch._verifyAdminEnvelope(e, SECRET, deps);
    expect(r.error.code).toBe('E_TS_INVALID');
  });

  it('rejects E_SIG_INVALID when hmac is wrong', () => {
    const e = envelope({ hmac: 'a'.repeat(64) });
    const r = Dispatch._verifyAdminEnvelope(e, SECRET, deps);
    expect(r.error.code).toBe('E_SIG_INVALID');
  });

  it('rejects E_SIG_INVALID when payload was tampered after signing', () => {
    const e = envelope({ payload: { username: 'alice' } });
    // Mutate payload AFTER signing — verifier recomputes canonical and rejects.
    e.payload = { username: 'mallory' };
    const r = Dispatch._verifyAdminEnvelope(e, SECRET, deps);
    expect(r.error.code).toBe('E_SIG_INVALID');
  });

  it('verifies regardless of payload key order (stableJson sort)', () => {
    // Sign with one key order, transmit with the other.
    const signed = envelope({ payload: { z: 1, a: 2 } });
    signed.payload = { a: 2, z: 1 };
    const r = Dispatch._verifyAdminEnvelope(signed, SECRET, deps);
    expect(r.ok).toBe(true);
  });

  it('rejects with the wrong secret', () => {
    const e = envelope();
    const r = Dispatch._verifyAdminEnvelope(e, 'wrong-secret', deps);
    expect(r.error.code).toBe('E_SIG_INVALID');
  });
});

describe('dispatchAdminAction', () => {
  const deps = { hmacSha256Hex: nodeHmacHex, nowMs: () => 1700000000000 };

  function buildHandlers({ noCtx = {}, needsCtx = {} } = {}) {
    return { no_ctx: noCtx, needs_ctx: needsCtx };
  }

  it('routes a no-ctx action and returns its result', () => {
    const handlers = buildHandlers({
      noCtx: {
        admin_users_list: (payload) => ({ ok: true, data: { users: [], filters: payload } }),
      },
    });
    const e = envelope({ action: 'admin_users_list', payload: { role_name: 'Administrator' } });
    const r = Dispatch.dispatchAdminAction(e, SECRET, null, deps, handlers);
    expect(r.ok).toBe(true);
    expect(r.data.filters.role_name).toBe('Administrator');
  });

  it('routes a needs-ctx action and passes ctx through', () => {
    let receivedCtx;
    const handlers = buildHandlers({
      needsCtx: {
        admin_read_responses: (payload, ctx) => {
          receivedCtx = ctx;
          return { ok: true, data: { rows: [], filters: payload } };
        },
      },
    });
    const fakeCtx = { sentinel: 'ctx-passed-through' };
    const e = envelope({ action: 'admin_read_responses', payload: { facility_id: 'F-001' } });
    const r = Dispatch.dispatchAdminAction(e, SECRET, fakeCtx, deps, handlers);
    expect(r.ok).toBe(true);
    expect(receivedCtx.sentinel).toBe('ctx-passed-through');
  });

  it('returns E_ACTION_UNKNOWN for unmapped actions', () => {
    const handlers = buildHandlers({ noCtx: {} });
    const e = envelope({ action: 'admin_does_not_exist' });
    const r = Dispatch.dispatchAdminAction(e, SECRET, null, deps, handlers);
    expect(r.error.code).toBe('E_ACTION_UNKNOWN');
  });

  it('returns E_ACTION_UNKNOWN when handler is registered but null (not bundled)', () => {
    const handlers = buildHandlers({ noCtx: { admin_users_list: null } });
    const e = envelope({ action: 'admin_users_list' });
    const r = Dispatch.dispatchAdminAction(e, SECRET, null, deps, handlers);
    expect(r.error.code).toBe('E_ACTION_UNKNOWN');
  });

  it('refuses to dispatch when HMAC verification fails', () => {
    const handlers = buildHandlers({
      noCtx: { admin_users_list: () => ({ ok: true, data: 'should-not-reach' }) },
    });
    const e = envelope({ action: 'admin_users_list', hmac: 'a'.repeat(64) });
    const r = Dispatch.dispatchAdminAction(e, SECRET, null, deps, handlers);
    expect(r.error.code).toBe('E_SIG_INVALID');
  });

  it('catches handler exceptions and returns E_INTERNAL', () => {
    const handlers = buildHandlers({
      noCtx: {
        admin_users_list: () => { throw new Error('handler exploded'); },
      },
    });
    const e = envelope({ action: 'admin_users_list' });
    const r = Dispatch.dispatchAdminAction(e, SECRET, null, deps, handlers);
    expect(r.error.code).toBe('E_INTERNAL');
    expect(r.error.message).toContain('handler exploded');
  });

  it('passes empty payload when envelope payload is null/missing', () => {
    let received;
    const handlers = buildHandlers({
      noCtx: {
        admin_settings_list: (payload) => {
          received = payload;
          return { ok: true, data: { settings: [] } };
        },
      },
    });
    const e = envelope({ action: 'admin_settings_list', payload: null });
    const r = Dispatch.dispatchAdminAction(e, SECRET, null, deps, handlers);
    expect(r.ok).toBe(true);
    expect(received).toEqual({});
  });
});
