import { describe, expect, it, vi } from 'vitest';
import { getFacilities } from './facilities-client';

const sampleEnvelope = {
  ok: true,
  data: {
    facilities: [
      {
        facility_id: 'F-001',
        facility_name: 'Manila General',
        facility_type: 'Hospital',
        region: 'NCR',
        province: 'Metro Manila',
        city_mun: 'Manila',
        barangay: 'Ermita',
      },
    ],
  },
};

function buildDeps(fetchImpl: typeof fetch) {
  return {
    proxyUrl: 'https://worker.example.workers.dev',
    deviceToken: 'eyJabc.eyJdef.sigxyz',
    fetchImpl,
  };
}

describe('getFacilities', () => {
  it('hits /exec?action=facilities with Bearer header', async () => {
    const fetchImpl = vi.fn(async (url: string, init?: RequestInit) => {
      expect(url).toBe('https://worker.example.workers.dev/exec?action=facilities');
      const auth = (init?.headers as Record<string, string> | undefined)?.['Authorization'] ?? '';
      expect(auth).toBe('Bearer eyJabc.eyJdef.sigxyz');
      return new Response(JSON.stringify(sampleEnvelope), { status: 200 });
    });
    await getFacilities(buildDeps(fetchImpl as unknown as typeof fetch));
    expect(fetchImpl).toHaveBeenCalled();
  });

  it('returns the facilities array on a 200 ok envelope', async () => {
    const fetchImpl = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(sampleEnvelope), { status: 200 }));
    const out = await getFacilities(buildDeps(fetchImpl));
    expect(out).toEqual({ ok: true, facilities: sampleEnvelope.data.facilities });
  });

  it('returns transport error on network failure', async () => {
    const fetchImpl = vi.fn().mockRejectedValue(new Error('boom'));
    const out = await getFacilities(buildDeps(fetchImpl));
    expect(out).toEqual({
      ok: false,
      transport: true,
      error: { code: 'E_NETWORK', message: 'boom' },
    });
  });

  it('surfaces Worker auth error code on 401', async () => {
    const fetchImpl = vi
      .fn()
      .mockResolvedValue(
        new Response(
          JSON.stringify({ ok: false, error: { code: 'E_TOKEN_EXPIRED', message: 'expired' } }),
          { status: 401 },
        ),
      );
    const out = await getFacilities(buildDeps(fetchImpl));
    expect(out).toMatchObject({
      ok: false,
      transport: true,
      error: { code: 'E_TOKEN_EXPIRED' },
    });
  });

  it('returns transport error on non-2xx without parseable body', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(new Response('nope', { status: 500 }));
    const out = await getFacilities(buildDeps(fetchImpl));
    expect(out).toMatchObject({ ok: false, transport: true, error: { code: 'E_HTTP_500' } });
  });

  it('returns logical error on ok=false envelope', async () => {
    const fetchImpl = vi
      .fn()
      .mockResolvedValue(
        new Response(
          JSON.stringify({ ok: false, error: { code: 'E_KILL_SWITCH', message: 'down' } }),
          { status: 200 },
        ),
      );
    const out = await getFacilities(buildDeps(fetchImpl));
    expect(out).toEqual({
      ok: false,
      transport: false,
      error: { code: 'E_KILL_SWITCH', message: 'down' },
    });
  });
});
