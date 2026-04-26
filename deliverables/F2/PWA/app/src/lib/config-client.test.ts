import { describe, expect, it } from 'vitest';
import { getConfig } from './config-client';

describe('getConfig', () => {
  const baseDeps = {
    proxyUrl: 'https://worker.example.workers.dev',
    deviceToken: 'eyJabc.eyJdef.sigxyz',
  };

  it('hits /exec?action=config with Bearer header', async () => {
    let capturedUrl = '';
    let capturedAuth = '';
    const fetchImpl = async (url: string, init?: RequestInit) => {
      capturedUrl = url;
      capturedAuth = (init?.headers as Record<string, string> | undefined)?.['Authorization'] ?? '';
      return new Response(
        JSON.stringify({
          ok: true,
          data: {
            current_spec_version: '2026-04-17-m1',
            min_accepted_spec_version: '2026-04-17-m1',
            kill_switch: false,
            broadcast_message: '',
            spec_hash: 'abc',
          },
        }),
        { status: 200 },
      );
    };
    const r = await getConfig({ ...baseDeps, fetchImpl: fetchImpl as unknown as typeof fetch });
    expect(capturedUrl).toBe('https://worker.example.workers.dev/exec?action=config');
    expect(capturedAuth).toBe('Bearer eyJabc.eyJdef.sigxyz');
    expect(r.ok).toBe(true);
    if (r.ok) expect(r.config.current_spec_version).toBe('2026-04-17-m1');
  });

  it('returns transport error on network failure', async () => {
    const fetchImpl = async () => {
      throw new Error('offline');
    };
    const r = await getConfig({ ...baseDeps, fetchImpl: fetchImpl as unknown as typeof fetch });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.transport).toBe(true);
  });

  it('surfaces Worker auth error code (E_TOKEN_REVOKED) verbatim', async () => {
    const fetchImpl = async () =>
      new Response(
        JSON.stringify({ ok: false, error: { code: 'E_TOKEN_REVOKED', message: 'revoked' } }),
        { status: 401 },
      );
    const r = await getConfig({ ...baseDeps, fetchImpl: fetchImpl as unknown as typeof fetch });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error.code).toBe('E_TOKEN_REVOKED');
  });

  it('returns backend error envelope verbatim on 200 with ok:false', async () => {
    const fetchImpl = async () =>
      new Response(JSON.stringify({ ok: false, error: { code: 'E_INTERNAL', message: 'boom' } }), {
        status: 200,
      });
    const r = await getConfig({ ...baseDeps, fetchImpl: fetchImpl as unknown as typeof fetch });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error.code).toBe('E_INTERNAL');
  });

  it('returns transport error on HTTP 5xx without a parseable body', async () => {
    const fetchImpl = async () => new Response('err', { status: 500 });
    const r = await getConfig({ ...baseDeps, fetchImpl: fetchImpl as unknown as typeof fetch });
    expect(r.ok).toBe(false);
    if (!r.ok) {
      expect(r.transport).toBe(true);
      expect(r.error.code).toBe('E_HTTP_500');
    }
  });
});
