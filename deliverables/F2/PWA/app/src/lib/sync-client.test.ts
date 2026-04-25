import { describe, it, expect, vi, beforeEach } from 'vitest';
import { postBatchSubmit, type BatchSubmitItem } from './sync-client';

type FetchMock = ReturnType<typeof vi.fn<typeof fetch>>;

function mockJsonResponse(body: unknown, init?: { status?: number }): Response {
  return new Response(JSON.stringify(body), {
    status: init?.status ?? 200,
    headers: { 'Content-Type': 'application/json' },
  });
}

const baseDeps = {
  proxyUrl: 'https://worker.example.workers.dev',
  deviceToken: 'eyJabc.eyJdef.sigxyz',
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

  it('POSTs to /exec?action=batch-submit with Bearer header and the responses array as body', async () => {
    baseDeps.fetchImpl.mockResolvedValue(
      mockJsonResponse({
        ok: true,
        data: {
          results: [{ client_submission_id: 'csid-1', submission_id: 'srv-1', status: 'accepted' }],
        },
      }),
    );
    const result = await postBatchSubmit(items, baseDeps);
    expect(result.ok).toBe(true);
    expect(baseDeps.fetchImpl).toHaveBeenCalledTimes(1);
    const [url, init] = baseDeps.fetchImpl.mock.calls[0]!;
    expect(String(url)).toBe('https://worker.example.workers.dev/exec?action=batch-submit');
    expect((init as RequestInit).method).toBe('POST');
    const headers = (init as RequestInit).headers as Record<string, string>;
    expect(headers['Content-Type']).toBe('text/plain');
    expect(headers['Authorization']).toBe('Bearer eyJabc.eyJdef.sigxyz');
    const body = JSON.parse((init as RequestInit).body as string);
    expect(body.responses).toHaveLength(1);
    expect(body.responses[0].client_submission_id).toBe('csid-1');
  });

  it('returns the per-item results array from the backend envelope', async () => {
    baseDeps.fetchImpl.mockResolvedValue(
      mockJsonResponse({
        ok: true,
        data: {
          results: [{ client_submission_id: 'csid-1', submission_id: 'srv-1', status: 'accepted' }],
        },
      }),
    );
    const result = await postBatchSubmit(items, baseDeps);
    if (!result.ok) throw new Error('expected ok');
    expect(result.results[0]?.status).toBe('accepted');
  });

  it('returns {ok: false, error} when the backend envelope says ok=false', async () => {
    baseDeps.fetchImpl.mockResolvedValue(
      mockJsonResponse({ ok: false, error: { code: 'E_KILL_SWITCH', message: 'off' } }),
    );
    const result = await postBatchSubmit(items, baseDeps);
    expect(result.ok).toBe(false);
    if (result.ok) throw new Error('expected failure');
    expect(result.error.code).toBe('E_KILL_SWITCH');
    expect(result.transport).toBe(false);
  });

  it('returns {ok: false, transport: true, error} when fetch throws (network down)', async () => {
    baseDeps.fetchImpl.mockRejectedValue(new TypeError('Failed to fetch'));
    const result = await postBatchSubmit(items, baseDeps);
    expect(result.ok).toBe(false);
    if (result.ok) throw new Error('expected failure');
    expect(result.transport).toBe(true);
    expect(result.error.code).toBe('E_NETWORK');
  });

  it('surfaces Worker auth error code on 401 (E_TOKEN_REVOKED)', async () => {
    baseDeps.fetchImpl.mockResolvedValue(
      mockJsonResponse(
        { ok: false, error: { code: 'E_TOKEN_REVOKED', message: 'revoked' } },
        { status: 401 },
      ),
    );
    const result = await postBatchSubmit(items, baseDeps);
    expect(result.ok).toBe(false);
    if (result.ok) throw new Error('expected failure');
    expect(result.error.code).toBe('E_TOKEN_REVOKED');
  });

  it('returns {ok: false, transport: true} for HTTP 5xx', async () => {
    baseDeps.fetchImpl.mockResolvedValue(mockJsonResponse({}, { status: 503 }));
    const result = await postBatchSubmit(items, baseDeps);
    expect(result.ok).toBe(false);
    if (result.ok) throw new Error('expected failure');
    expect(result.transport).toBe(true);
  });
});
