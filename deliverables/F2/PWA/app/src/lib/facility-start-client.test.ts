/**
 * Facility slug link client (design F2-Facility-Slug-Links-2026-07-16):
 * URL parsing + resolve/self-register envelope handling.
 */
import { describe, expect, it, vi } from 'vitest';
import {
  parseFacilityUrl,
  resolveFacilitySlug,
  selfRegisterBySlug,
} from './facility-start-client';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

describe('parseFacilityUrl', () => {
  it('parses /f/<slug> (with or without a trailing slash), case-folded', () => {
    expect(parseFacilityUrl({ pathname: '/f/lphbay' })).toEqual({ slug: 'lphbay' });
    expect(parseFacilityUrl({ pathname: '/f/lphbay/' })).toEqual({ slug: 'lphbay' });
    expect(parseFacilityUrl({ pathname: '/f/LphBay' })).toEqual({ slug: 'lphbay' });
    expect(parseFacilityUrl({ pathname: '/f/rhu-daraga-2' })).toEqual({ slug: 'rhu-daraga-2' });
  });

  it('rejects non-facility paths, bad slugs, and the reserved resolver path', () => {
    expect(parseFacilityUrl({ pathname: '/' })).toBeNull();
    expect(parseFacilityUrl({ pathname: '/e/LPHBAY-HCW-19' })).toBeNull();
    expect(parseFacilityUrl({ pathname: '/f/' })).toBeNull();
    expect(parseFacilityUrl({ pathname: '/f/-bad' })).toBeNull();
    expect(parseFacilityUrl({ pathname: '/f/a/b' })).toBeNull();
    expect(parseFacilityUrl({ pathname: '/f/resolve' })).toBeNull();
  });
});

describe('resolveFacilitySlug', () => {
  it('returns the facility on ok:true and encodes the slug into the query', async () => {
    let captured = '';
    const fetchImpl = vi.fn(async (url: RequestInfo | URL) => {
      captured = String(url);
      return jsonResponse({ ok: true, facility_id: '040340210', facility_name: 'LPH-Bay' });
    }) as unknown as typeof fetch;
    const r = await resolveFacilitySlug({ proxyUrl: 'https://w.example', slug: 'lphbay', fetchImpl });
    expect(r).toEqual({ ok: true, facility_id: '040340210', facility_name: 'LPH-Bay' });
    expect(captured).toBe('https://w.example/f/resolve?slug=lphbay');
  });

  it('maps an HTTP 404 to a non-transport E_NOT_FOUND', async () => {
    const fetchImpl = vi.fn(async () =>
      jsonResponse({ ok: false, error: { code: 'E_NOT_FOUND', message: 'inactive' } }, 404),
    ) as unknown as typeof fetch;
    const r = await resolveFacilitySlug({ proxyUrl: 'https://w.example', slug: 'nope', fetchImpl });
    expect(r).toMatchObject({ ok: false, transport: false, error: { code: 'E_NOT_FOUND' } });
  });

  it('maps a thrown fetch to a transport E_NETWORK', async () => {
    const fetchImpl = vi.fn(async () => {
      throw new Error('offline');
    }) as unknown as typeof fetch;
    const r = await resolveFacilitySlug({ proxyUrl: 'https://w.example', slug: 'lphbay', fetchImpl });
    expect(r).toMatchObject({ ok: false, transport: true, error: { code: 'E_NETWORK' } });
  });
});

describe('selfRegisterBySlug', () => {
  it('POSTs {slug} and returns the token/qn payload', async () => {
    let capturedBody: unknown = null;
    const fetchImpl = vi.fn(async (_url: RequestInfo | URL, init?: RequestInit) => {
      capturedBody = JSON.parse(String(init?.body));
      return jsonResponse({
        ok: true,
        token: 'device.jwt',
        hcw_id: 'sr-1',
        qn: '040340210101',
        facility_id: '040340210',
        facility_name: 'LPH-Bay',
      });
    }) as unknown as typeof fetch;
    const r = await selfRegisterBySlug({ proxyUrl: 'https://w.example', slug: 'lphbay', fetchImpl });
    expect(capturedBody).toEqual({ slug: 'lphbay' });
    expect(r).toEqual({
      ok: true,
      token: 'device.jwt',
      hcw_id: 'sr-1',
      qn: '040340210101',
      facility_id: '040340210',
      facility_name: 'LPH-Bay',
    });
  });

  it('surfaces the kill-switch envelope (HTTP 200, ok:false) as its error code', async () => {
    const fetchImpl = vi.fn(async () =>
      jsonResponse({ ok: false, error: { code: 'E_KILL_SWITCH', message: 'paused' } }),
    ) as unknown as typeof fetch;
    const r = await selfRegisterBySlug({ proxyUrl: 'https://w.example', slug: 'lphbay', fetchImpl });
    expect(r).toMatchObject({ ok: false, transport: false, error: { code: 'E_KILL_SWITCH' } });
  });

  it('maps a thrown fetch to a transport E_NETWORK', async () => {
    const fetchImpl = vi.fn(async () => {
      throw new Error('offline');
    }) as unknown as typeof fetch;
    const r = await selfRegisterBySlug({ proxyUrl: 'https://w.example', slug: 'lphbay', fetchImpl });
    expect(r).toMatchObject({ ok: false, transport: true, error: { code: 'E_NETWORK' } });
  });
});
