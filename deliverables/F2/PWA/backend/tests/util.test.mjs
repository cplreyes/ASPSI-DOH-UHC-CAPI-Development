import { describe, it, expect } from 'vitest';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { ok, fail, timingSafeEq, generateUuid, nowMs } = require('../src/Util.js');

describe('Util.ok / Util.fail', () => {
  it('ok returns {ok: true, data}', () => {
    expect(ok({ a: 1 })).toEqual({ ok: true, data: { a: 1 } });
  });

  it('fail returns {ok: false, error: {code, message}}', () => {
    expect(fail('E_X', 'nope')).toEqual({
      ok: false,
      error: { code: 'E_X', message: 'nope' },
    });
  });
});

describe('Util.timingSafeEq', () => {
  it('returns true for equal strings', () => {
    expect(timingSafeEq('abc', 'abc')).toBe(true);
  });
  it('returns false for different strings', () => {
    expect(timingSafeEq('abc', 'abd')).toBe(false);
  });
  it('returns false for different-length strings', () => {
    expect(timingSafeEq('abc', 'abcd')).toBe(false);
  });
  it('returns false when either input is not a string', () => {
    expect(timingSafeEq('abc', null)).toBe(false);
    expect(timingSafeEq(undefined, 'abc')).toBe(false);
  });
});

describe('Util.generateUuid', () => {
  it('returns a v4-looking UUID string', () => {
    const id = generateUuid();
    expect(id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
  });
  it('returns unique ids on repeated calls', () => {
    const a = generateUuid();
    const b = generateUuid();
    expect(a).not.toBe(b);
  });
});

describe('Util.nowMs', () => {
  it('returns a positive integer close to Date.now()', () => {
    const n = nowMs();
    expect(Number.isInteger(n)).toBe(true);
    expect(Math.abs(n - Date.now())).toBeLessThan(1000);
  });
});
