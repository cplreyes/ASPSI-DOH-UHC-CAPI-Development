/**
 * HMAC compat tests.
 * Must match `deliverables/F2/PWA/backend/src/Auth.js` canonicalString format
 * AND produce the same hex output as Node `crypto.createHmac('sha256', ...)`.
 */
import { describe, expect, it } from 'vitest';
import { createHmac } from 'node:crypto';
import { signAppsScriptRequest } from '../src/hmac';

const SECRET = 'da6ee90c57f00b0b0b98587867c72b1fff7b458609d4df45383197d2a2a5a0b3';

function nodeReferenceHex(method: string, action: string, ts: string, body: string): string {
  const canonical = `${method}|${action}|${ts}|${body}`;
  return createHmac('sha256', SECRET).update(canonical).digest('hex');
}

describe('hmac: byte-for-byte compat with Apps Script Auth.js', () => {
  it('matches Node crypto for POST batch-submit', async () => {
    const ts = '1700000000000';
    const body = JSON.stringify({ responses: [{ client_submission_id: 'csid-1' }] });
    const ours = await signAppsScriptRequest(SECRET, 'POST', 'batch-submit', ts, body);
    const reference = nodeReferenceHex('POST', 'batch-submit', ts, body);
    expect(ours).toBe(reference);
  });

  it('matches Node crypto for GET config (empty body)', async () => {
    const ts = '1700000000000';
    const ours = await signAppsScriptRequest(SECRET, 'GET', 'config', ts, '');
    const reference = nodeReferenceHex('GET', 'config', ts, '');
    expect(ours).toBe(reference);
  });

  it('matches Node crypto for GET facilities', async () => {
    const ts = '1700000000000';
    const ours = await signAppsScriptRequest(SECRET, 'GET', 'facilities', ts, '');
    const reference = nodeReferenceHex('GET', 'facilities', ts, '');
    expect(ours).toBe(reference);
  });

  it('produces lowercase hex (Auth.js compares case-insensitively but normalises lower)', async () => {
    const sig = await signAppsScriptRequest(SECRET, 'POST', 'submit', '1', '');
    expect(sig).toBe(sig.toLowerCase());
    expect(sig).toMatch(/^[a-f0-9]{64}$/);
  });
});
