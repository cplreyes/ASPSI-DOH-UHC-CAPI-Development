import { describe, expect, it, vi } from 'vitest';
import { adminFetch } from './api-client';

function jsonResponse(body: unknown, status = 200, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...headers },
  });
}

describe('adminFetch', () => {
  // The Worker's login endpoint returns the success body directly (no
  // envelope) — `{ token, role, role_version, expires_at, password_must_change }`.
  // Error responses always use the `{ ok: false, error }` envelope.
  // adminFetch returns the raw body on success and an unpacked ApiError on failure.

  it('attaches Bearer token when provided', async () => {
    const fetchImpl = vi.fn(async (_url: string, init?: RequestInit) => {
      const headers = new Headers(init?.headers);
      expect(headers.get('Authorization')).toBe('Bearer abc.def.ghi');
      return jsonResponse({ hello: 'world' });
    }) as unknown as typeof fetch;
    const r = await adminFetch<{ hello: string }>('/x', {}, { token: 'abc.def.ghi', fetchImpl });
    expect(r.ok).toBe(true);
    if (r.ok) expect(r.data).toEqual({ hello: 'world' });
  });

  it('omits Authorization when no token', async () => {
    const fetchImpl = vi.fn(async (_url: string, init?: RequestInit) => {
      const headers = new Headers(init?.headers);
      expect(headers.has('Authorization')).toBe(false);
      return jsonResponse({});
    }) as unknown as typeof fetch;
    await adminFetch('/x', {}, { fetchImpl });
  });

  it('captures X-Request-Id from the response', async () => {
    const fetchImpl = vi.fn(async () =>
      jsonResponse({ token: 't' }, 200, { 'X-Request-Id': 'req-42' }),
    ) as unknown as typeof fetch;
    const r = await adminFetch('/x', {}, { fetchImpl });
    expect(r.ok).toBe(true);
    if (r.ok) expect(r.requestId).toBe('req-42');
  });

  it('triggers onUnauthorized on 401 and returns the typed error code', async () => {
    const fetchImpl = vi.fn(async () =>
      jsonResponse(
        { ok: false, error: { code: 'E_AUTH_INVALID', message: 'bad creds' } },
        401,
        { 'X-Request-Id': 'req-1' },
      ),
    ) as unknown as typeof fetch;
    const onUnauthorized = vi.fn();
    const r = await adminFetch('/x', {}, { fetchImpl, onUnauthorized });
    expect(onUnauthorized).toHaveBeenCalledOnce();
    expect(r.ok).toBe(false);
    if (!r.ok) {
      expect(r.error.code).toBe('E_AUTH_INVALID');
      expect(r.error.requestId).toBe('req-1');
      expect(r.error.status).toBe(401);
    }
  });

  it('does NOT trigger onUnauthorized on non-401 errors', async () => {
    const fetchImpl = vi.fn(async () =>
      jsonResponse({ ok: false, error: { code: 'E_BACKEND', message: 'AS down' } }, 502),
    ) as unknown as typeof fetch;
    const onUnauthorized = vi.fn();
    const r = await adminFetch('/x', {}, { fetchImpl, onUnauthorized });
    expect(onUnauthorized).not.toHaveBeenCalled();
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error.code).toBe('E_BACKEND');
  });

  it('maps fetch network rejection to E_NETWORK without throwing', async () => {
    const fetchImpl = vi.fn(async () => {
      throw new TypeError('Failed to fetch');
    }) as unknown as typeof fetch;
    const r = await adminFetch('/x', {}, { fetchImpl });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error.code).toBe('E_NETWORK');
  });

  it('handles 204 No Content responses (logout)', async () => {
    const fetchImpl = vi.fn(async () =>
      new Response(null, { status: 204, headers: { 'X-Request-Id': 'req-9' } }),
    ) as unknown as typeof fetch;
    const r = await adminFetch('/x', {}, { fetchImpl });
    expect(r.ok).toBe(true);
    if (r.ok) expect(r.requestId).toBe('req-9');
  });

  it('normalizes unknown error codes to E_UNKNOWN', async () => {
    const fetchImpl = vi.fn(async () =>
      jsonResponse({ ok: false, error: { code: 'NOT_IN_ENUM', message: 'huh' } }, 500),
    ) as unknown as typeof fetch;
    const r = await adminFetch('/x', {}, { fetchImpl });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error.code).toBe('E_UNKNOWN');
  });
});
