import { describe, expect, it } from 'vitest';
import { getConfig } from './config-client';

describe('getConfig', () => {
  const baseDeps = {
    backendUrl: 'https://example.com/exec',
    hmacSecret: 'secret',
    hmacSign: async () => 'deadbeef',
    nowMs: () => 1_700_000_000_000,
  };

  it('returns parsed config on 200 ok envelope', async () => {
    const fetchImpl = async (url: string) => {
      expect(url).toContain('action=config');
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

  it('returns backend error envelope verbatim', async () => {
    const fetchImpl = async () =>
      new Response(JSON.stringify({ ok: false, error: { code: 'E_INTERNAL', message: 'boom' } }), {
        status: 200,
      });
    const r = await getConfig({ ...baseDeps, fetchImpl: fetchImpl as unknown as typeof fetch });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error.code).toBe('E_INTERNAL');
  });

  it('returns transport error on HTTP 5xx', async () => {
    const fetchImpl = async () => new Response('err', { status: 500 });
    const r = await getConfig({ ...baseDeps, fetchImpl: fetchImpl as unknown as typeof fetch });
    expect(r.ok).toBe(false);
    if (!r.ok) {
      expect(r.transport).toBe(true);
      expect(r.error.code).toBe('E_HTTP_500');
    }
  });
});
