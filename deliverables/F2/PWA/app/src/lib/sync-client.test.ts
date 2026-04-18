import { describe, it, expect, vi, beforeEach } from 'vitest';
import { postBatchSubmit, type BatchSubmitItem } from './sync-client';

type FetchMock = ReturnType<typeof vi.fn<typeof fetch>>;

function mockJsonResponse(body: unknown, init?: { status?: number }): Response {
  return new Response(JSON.stringify(body), {
    status: init?.status ?? 200,
    headers: { 'Content-Type': 'application/json' },
  });
}

const fakeSign = async (secret: string, msg: string) => `sig(${secret}:${msg})`;

const baseDeps = {
  hmacSign: fakeSign,
  nowMs: () => 1_700_000_000_000,
  fetchImpl: null as unknown as FetchMock,
};

describe('postBatchSubmit', () => {
  const items: BatchSubmitItem[] = [
    {
      client_submission_id: 'csid-1',
      hcw_id: 'h1',
      facility_id: 'f1',
      spec_version: '2026-04-17-m1',
      app_version: '0.1.0',
      submitted_at_client: 1_699_999_999_000,
      device_fingerprint: 'fp',
      values: { Q2: 'Regular' },
    },
  ];

  beforeEach(() => {
    baseDeps.fetchImpl = vi.fn();
  });

  it('sends a signed POST with ts, sig, action, and body', async () => {
    baseDeps.fetchImpl.mockResolvedValue(
      mockJsonResponse({ ok: true, data: { results: [{ client_submission_id: 'csid-1', submission_id: 'srv-1', status: 'accepted' }] } }),
    );
    const result = await postBatchSubmit(items, {
      backendUrl: 'https://x/exec',
      hmacSecret: 'S',
      ...baseDeps,
    });
    expect(result.ok).toBe(true);
    expect(baseDeps.fetchImpl).toHaveBeenCalledTimes(1);
    const [url, init] = baseDeps.fetchImpl.mock.calls[0]!;
    expect(String(url)).toContain('action=batch-submit');
    expect(String(url)).toContain('ts=1700000000000');
    const sigParam = new URL(String(url)).searchParams.get('sig') ?? '';
    expect(sigParam).toMatch(/^sig\(S:POST\|batch-submit\|1700000000000\|/);
    expect((init as RequestInit).method).toBe('POST');
    expect((init as RequestInit).headers).toMatchObject({ 'Content-Type': 'application/json' });
    const body = JSON.parse((init as RequestInit).body as string);
    expect(body.responses).toHaveLength(1);
    expect(body.responses[0].client_submission_id).toBe('csid-1');
  });

  it('returns the per-item results array from the backend envelope', async () => {
    baseDeps.fetchImpl.mockResolvedValue(
      mockJsonResponse({
        ok: true,
        data: { results: [{ client_submission_id: 'csid-1', submission_id: 'srv-1', status: 'accepted' }] },
      }),
    );
    const result = await postBatchSubmit(items, {
      backendUrl: 'https://x/exec',
      hmacSecret: 'S',
      ...baseDeps,
    });
    if (!result.ok) throw new Error('expected ok');
    expect(result.results[0]?.status).toBe('accepted');
  });

  it('returns {ok: false, error} when the backend envelope says ok=false', async () => {
    baseDeps.fetchImpl.mockResolvedValue(
      mockJsonResponse({ ok: false, error: { code: 'E_KILL_SWITCH', message: 'off' } }),
    );
    const result = await postBatchSubmit(items, {
      backendUrl: 'https://x/exec',
      hmacSecret: 'S',
      ...baseDeps,
    });
    expect(result.ok).toBe(false);
    if (result.ok) throw new Error('expected failure');
    expect(result.error.code).toBe('E_KILL_SWITCH');
    expect(result.transport).toBe(false);
  });

  it('returns {ok: false, transport: true, error} when fetch throws (network down)', async () => {
    baseDeps.fetchImpl.mockRejectedValue(new TypeError('Failed to fetch'));
    const result = await postBatchSubmit(items, {
      backendUrl: 'https://x/exec',
      hmacSecret: 'S',
      ...baseDeps,
    });
    expect(result.ok).toBe(false);
    if (result.ok) throw new Error('expected failure');
    expect(result.transport).toBe(true);
    expect(result.error.code).toBe('E_NETWORK');
  });

  it('returns {ok: false, transport: true} for HTTP 5xx', async () => {
    baseDeps.fetchImpl.mockResolvedValue(mockJsonResponse({}, { status: 503 }));
    const result = await postBatchSubmit(items, {
      backendUrl: 'https://x/exec',
      hmacSecret: 'S',
      ...baseDeps,
    });
    expect(result.ok).toBe(false);
    if (result.ok) throw new Error('expected failure');
    expect(result.transport).toBe(true);
  });
});
