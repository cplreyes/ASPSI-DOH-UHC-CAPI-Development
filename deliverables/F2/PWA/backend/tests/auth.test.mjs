import { describe, it, expect } from 'vitest';
import crypto from 'node:crypto';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { verifyRequest, canonicalString } = require('../src/Auth.js');

const SECRET = 'test-secret-0123456789';
const nodeHmacHex = (key, data) =>
  crypto.createHmac('sha256', key).update(data).digest('hex');

function signed({ method = 'POST', action = 'submit', ts, body = '' }) {
  const canonical = `${method}|${action}|${ts}|${body}`;
  return {
    method,
    action,
    ts: String(ts),
    body,
    sig: nodeHmacHex(SECRET, canonical),
  };
}

describe('Auth.canonicalString', () => {
  it('joins method|action|ts|body with pipes', () => {
    expect(canonicalString('POST', 'submit', '1700000000000', '{"a":1}'))
      .toBe('POST|submit|1700000000000|{"a":1}');
  });
});

describe('Auth.verifyRequest', () => {
  const deps = { hmacSha256Hex: nodeHmacHex, nowMs: () => 1700000000000 };

  it('returns {ok: true} for a valid signature within skew', () => {
    const r = signed({ ts: 1700000000000, body: '{"x":1}' });
    expect(verifyRequest(r, SECRET, deps)).toEqual({ ok: true });
  });

  it('returns E_TS_SKEW when timestamp is >5 minutes old', () => {
    const r = signed({ ts: 1700000000000 - 6 * 60 * 1000 });
    expect(verifyRequest(r, SECRET, deps)).toEqual({
      ok: false,
      error: { code: 'E_TS_SKEW', message: 'Timestamp outside ±5 minute window' },
    });
  });

  it('returns E_TS_SKEW when timestamp is >5 minutes in the future', () => {
    const r = signed({ ts: 1700000000000 + 6 * 60 * 1000 });
    expect(verifyRequest(r, SECRET, deps).error.code).toBe('E_TS_SKEW');
  });

  it('returns E_TS_INVALID when ts is not an integer', () => {
    const r = signed({ ts: 1700000000000 });
    r.ts = 'nope';
    expect(verifyRequest(r, SECRET, deps).error.code).toBe('E_TS_INVALID');
  });

  it('returns E_SIG_INVALID when body is tampered', () => {
    const r = signed({ ts: 1700000000000, body: '{"x":1}' });
    r.body = '{"x":2}';
    expect(verifyRequest(r, SECRET, deps).error.code).toBe('E_SIG_INVALID');
  });

  it('returns E_SIG_INVALID when signature is missing', () => {
    const r = signed({ ts: 1700000000000 });
    r.sig = '';
    expect(verifyRequest(r, SECRET, deps).error.code).toBe('E_SIG_INVALID');
  });

  it('returns E_SIG_INVALID when secret does not match', () => {
    const r = signed({ ts: 1700000000000 });
    expect(verifyRequest(r, 'wrong-secret', deps).error.code).toBe('E_SIG_INVALID');
  });
});
