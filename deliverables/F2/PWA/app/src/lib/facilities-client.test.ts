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
    backendUrl: 'https://script.example/exec',
    hmacSecret: 'secret',
    hmacSign: vi.fn().mockResolvedValue('SIGNATURE'),
    nowMs: () => 1_700_000_000_000,
    fetchImpl,
  };
}

describe('getFacilities', () => {
  it('signs the request with GET|facilities|<ts>|', async () => {
    const fetchImpl = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(sampleEnvelope), { status: 200 }));
    const deps = buildDeps(fetchImpl);
    await getFacilities(deps);
    expect(deps.hmacSign).toHaveBeenCalledWith('secret', 'GET|facilities|1700000000000|');
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

  it('returns transport error on non-2xx', async () => {
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
