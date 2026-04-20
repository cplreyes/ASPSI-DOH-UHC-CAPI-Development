import { describe, it, expect } from 'vitest';
import { hmacSha256Hex, canonicalString } from './hmac';

// RFC 4231-style known-answer — verified against Node's crypto.
// secret='key', msg='The quick brown fox jumps over the lazy dog'
// expected: f7bc83f430538424b13298e6aa6fb143ef4d59a14946175997479dbc2d1a3cd8
const KNOWN = {
  secret: 'key',
  msg: 'The quick brown fox jumps over the lazy dog',
  expected: 'f7bc83f430538424b13298e6aa6fb143ef4d59a14946175997479dbc2d1a3cd8',
};

describe('hmacSha256Hex', () => {
  it('produces lowercase hex output for the RFC-style fixture', async () => {
    const result = await hmacSha256Hex(KNOWN.secret, KNOWN.msg);
    expect(result).toBe(KNOWN.expected);
  });

  it('returns different signatures for different messages', async () => {
    const a = await hmacSha256Hex('secret', 'a');
    const b = await hmacSha256Hex('secret', 'b');
    expect(a).not.toBe(b);
    expect(a).toMatch(/^[0-9a-f]{64}$/);
  });

  it('returns different signatures for different secrets', async () => {
    const a = await hmacSha256Hex('s1', 'msg');
    const b = await hmacSha256Hex('s2', 'msg');
    expect(a).not.toBe(b);
  });
});

describe('canonicalString', () => {
  it('joins method, action, ts, body with pipes', () => {
    expect(canonicalString('POST', 'submit', 1_700_000_000_000, '{"x":1}')).toBe(
      'POST|submit|1700000000000|{"x":1}',
    );
  });

  it('uppercases the method', () => {
    expect(canonicalString('post', 'x', 1, '')).toBe('POST|x|1|');
  });
});
