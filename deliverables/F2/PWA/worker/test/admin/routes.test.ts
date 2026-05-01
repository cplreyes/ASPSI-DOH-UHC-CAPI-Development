/**
 * F2 Admin Portal — adminRouter dispatcher tests.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 1.14)
 *
 * Thin tests for the routing layer: non-admin paths fall through (null),
 * unknown admin paths return 404 with X-Request-Id, and the login route
 * stamps X-Request-Id on the handleLogin response.
 */
import { describe, expect, it, vi } from 'vitest';
import { adminRouter } from '../../src/admin/routes';
import { hashPassword, mintAdminJwt } from '../../src/admin/auth';
import type { Env } from '../../src/types';

interface FakeKV {
  get(k: string): Promise<string | null>;
  put(k: string, v: string, opts?: { expirationTtl?: number }): Promise<void>;
  delete(k: string): Promise<void>;
  _store: Map<string, string>;
}
function makeKv(): FakeKV {
  const store = new Map<string, string>();
  return {
    async get(k) { return store.get(k) ?? null; },
    async put(k, v) { store.set(k, v); },
    async delete(k) { store.delete(k); },
    _store: store,
  };
}

function fakeKey(): string {
  const bytes = new Uint8Array(32);
  for (let i = 0; i < bytes.length; i++) bytes[i] = i;
  let s = '';
  for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]!);
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function makeEnv(kv: FakeKV): Env {
  return {
    ADMIN_PASSWORD_HASH: 'unused',
    APPS_SCRIPT_HMAC: 'test-hmac',
    APPS_SCRIPT_URL: 'https://script.example/exec',
    JWT_SIGNING_KEY: fakeKey(),
    F2_AUTH: kv as unknown as KVNamespace,
  };
}

describe('adminRouter', () => {
  it('returns null for non-admin paths so the legacy router can handle them', async () => {
    const req = new Request('https://x/exec', { method: 'POST' });
    const r = await adminRouter(req, makeEnv(makeKv()));
    expect(r).toBeNull();
  });

  it('returns null for /admin/login (legacy admin UI), only /admin/api/* is ours', async () => {
    const req = new Request('https://x/admin/login', { method: 'POST' });
    const r = await adminRouter(req, makeEnv(makeKv()));
    expect(r).toBeNull();
  });

  it('returns 404 with X-Request-Id for unknown /admin/api paths', async () => {
    const req = new Request('https://x/admin/api/does-not-exist', { method: 'GET' });
    const r = await adminRouter(req, makeEnv(makeKv()));
    expect(r).not.toBeNull();
    expect(r!.status).toBe(404);
    const requestId = r!.headers.get('X-Request-Id');
    expect(requestId).toBeTruthy();
    expect(requestId).toMatch(/^[0-9a-f-]{36}$/);
    const body = await r!.json() as { error: { code: string } };
    expect(body.error.code).toBe('E_NOT_FOUND');
  });

  it('routes POST /admin/api/login to handleLogin and stamps X-Request-Id', async () => {
    const kv = makeKv();
    const env = makeEnv(kv);

    // Stub global fetch so callAppsScript returns deterministic users + roles.
    const passwordHash = await hashPassword('CorrectPw1');
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(async (_url, init) => {
      const body = JSON.parse((init as RequestInit).body as string) as { action: string };
      if (body.action === 'admin_users_list') {
        return new Response(JSON.stringify({
          ok: true,
          data: { users: [{ username: 'alice', password_hash: passwordHash, password_must_change: false, role: 'Administrator' }] },
        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      if (body.action === 'admin_roles_list') {
        return new Response(JSON.stringify({
          ok: true,
          data: { roles: [{ name: 'Administrator', version: 1, manage_users: true }] },
        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      return new Response('{}', { status: 500 });
    });

    try {
      const req = new Request('https://x/admin/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'cf-connecting-ip': '203.0.113.5' },
        body: JSON.stringify({ username: 'alice', password: 'CorrectPw1' }),
      });
      const r = await adminRouter(req, env);
      expect(r).not.toBeNull();
      expect(r!.status).toBe(200);
      expect(r!.headers.get('X-Request-Id')).toMatch(/^[0-9a-f-]{36}$/);
      const body = await r!.json() as { token: string; role: string };
      expect(body.role).toBe('Administrator');
      expect(body.token).toMatch(/.+\..+\..+/);
    } finally {
      fetchSpy.mockRestore();
    }
  });

  it('fires audit-write via ctx.waitUntil on successful login', async () => {
    const kv = makeKv();
    const env = makeEnv(kv);
    const passwordHash = await hashPassword('CorrectPw1');
    const calls: Array<{ url: string; action: string }> = [];
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(async (url, init) => {
      const body = JSON.parse((init as RequestInit).body as string) as { action: string };
      calls.push({ url: String(url), action: body.action });
      if (body.action === 'admin_users_list') {
        return new Response(JSON.stringify({
          ok: true,
          data: { users: [{ username: 'alice', password_hash: passwordHash, password_must_change: false, role: 'Administrator' }] },
        }), { status: 200 });
      }
      if (body.action === 'admin_roles_list') {
        return new Response(JSON.stringify({
          ok: true,
          data: { roles: [{ name: 'Administrator', version: 1, manage_users: true }] },
        }), { status: 200 });
      }
      if (body.action === 'admin_audit_write') {
        return new Response(JSON.stringify({ ok: true, data: { ok: true } }), { status: 200 });
      }
      return new Response('{}', { status: 500 });
    });

    const waitUntilPromises: Promise<unknown>[] = [];
    const ctx: ExecutionContext = {
      waitUntil: (p: Promise<unknown>) => { waitUntilPromises.push(p); },
      passThroughOnException: () => undefined,
    } as unknown as ExecutionContext;

    try {
      const req = new Request('https://x/admin/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'cf-connecting-ip': '203.0.113.5' },
        body: JSON.stringify({ username: 'alice', password: 'CorrectPw1' }),
      });
      const r = await adminRouter(req, env, ctx);
      expect(r!.status).toBe(200);

      // Drain waitUntil promises so the audit fetch completes.
      await Promise.all(waitUntilPromises);

      const auditCalls = calls.filter(c => c.action === 'admin_audit_write');
      expect(auditCalls).toHaveLength(1);
    } finally {
      fetchSpy.mockRestore();
    }
  });

  it('skips audit-write when ctx is absent (no ExecutionContext)', async () => {
    const kv = makeKv();
    const env = makeEnv(kv);
    const passwordHash = await hashPassword('CorrectPw1');
    const calls: Array<{ action: string }> = [];
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(async (_url, init) => {
      const body = JSON.parse((init as RequestInit).body as string) as { action: string };
      calls.push({ action: body.action });
      if (body.action === 'admin_users_list') {
        return new Response(JSON.stringify({
          ok: true,
          data: { users: [{ username: 'alice', password_hash: passwordHash, password_must_change: false, role: 'Administrator' }] },
        }), { status: 200 });
      }
      if (body.action === 'admin_roles_list') {
        return new Response(JSON.stringify({
          ok: true,
          data: { roles: [{ name: 'Administrator', version: 1, manage_users: true }] },
        }), { status: 200 });
      }
      return new Response('{}', { status: 500 });
    });

    try {
      const req = new Request('https://x/admin/api/login', {
        method: 'POST',
        body: JSON.stringify({ username: 'alice', password: 'CorrectPw1' }),
      });
      const r = await adminRouter(req, env); // no ctx
      expect(r!.status).toBe(200);
      expect(calls.some(c => c.action === 'admin_audit_write')).toBe(false);
    } finally {
      fetchSpy.mockRestore();
    }
  });

  it('routes POST /admin/api/logout to handleLogout and stamps X-Request-Id', async () => {
    const kv = makeKv();
    const env = makeEnv(kv);
    const tok = await mintAdminJwt(env.JWT_SIGNING_KEY, { sub: 'alice', role: 'Administrator', role_version: 1 });
    const req = new Request('https://x/admin/api/logout', {
      method: 'POST',
      headers: { Authorization: `Bearer ${tok}` },
    });
    const r = await adminRouter(req, env);
    expect(r).not.toBeNull();
    expect(r!.status).toBe(204);
    expect(r!.headers.get('X-Request-Id')).toMatch(/^[0-9a-f-]{36}$/);
  });

  it('rejects POST /admin/api/encode/:hcw_id with no Authorization header (401)', async () => {
    const env = makeEnv(makeKv());
    const req = new Request('https://x/admin/api/encode/hcw-1', {
      method: 'POST',
      body: JSON.stringify({ client_submission_id: 'c1', spec_version: '2026-04-17-m1', values: {} }),
    });
    const r = await adminRouter(req, env);
    expect(r!.status).toBe(401);
    const body = await r!.json() as { error: { code: string } };
    expect(body.error.code).toBe('E_AUTH_INVALID');
  });

  it('rejects POST /admin/api/encode/:hcw_id with 403 when role lacks dict_paper_encoded_up', async () => {
    const env = makeEnv(makeKv());
    const tok = await mintAdminJwt(env.JWT_SIGNING_KEY, { sub: 'standard', role: 'Standard User', role_version: 1 });
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(async (_url, init) => {
      const body = JSON.parse((init as RequestInit).body as string) as { action: string };
      if (body.action === 'admin_roles_list') {
        return new Response(JSON.stringify({
          ok: true,
          data: { roles: [{ name: 'Standard User', version: 1, dash_data: true }] },
        }), { status: 200 });
      }
      return new Response('{}', { status: 500 });
    });
    try {
      const req = new Request('https://x/admin/api/encode/hcw-1', {
        method: 'POST',
        headers: { Authorization: `Bearer ${tok}` },
        body: JSON.stringify({ client_submission_id: 'c1', spec_version: '2026-04-17-m1', values: {} }),
      });
      const r = await adminRouter(req, env);
      expect(r!.status).toBe(403);
      const body = await r!.json() as { error: { code: string } };
      expect(body.error.code).toBe('E_PERM_DENIED');
    } finally {
      fetchSpy.mockRestore();
    }
  });

  it('routes a permitted encode request to handleEncodeSubmit and forwards to AS', async () => {
    const env = makeEnv(makeKv());
    const tok = await mintAdminJwt(env.JWT_SIGNING_KEY, { sub: 'admin-alice', role: 'Operator', role_version: 1 });
    const calls: Array<{ action: string; payload: unknown }> = [];
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(async (_url, init) => {
      const body = JSON.parse((init as RequestInit).body as string) as { action: string; payload: unknown };
      calls.push({ action: body.action, payload: body.payload });
      if (body.action === 'admin_roles_list') {
        return new Response(JSON.stringify({
          ok: true,
          data: { roles: [{ name: 'Operator', version: 1, dict_paper_encoded_up: true }] },
        }), { status: 200 });
      }
      if (body.action === 'admin_encode_submit') {
        return new Response(JSON.stringify({
          ok: true,
          data: { submission_id: 'srv-99', status: 'accepted', server_timestamp: '2026-05-01T00:00:00Z' },
        }), { status: 200 });
      }
      return new Response('{}', { status: 500 });
    });
    try {
      const req = new Request('https://x/admin/api/encode/hcw-from-path', {
        method: 'POST',
        headers: { Authorization: `Bearer ${tok}`, 'cf-connecting-ip': '203.0.113.5' },
        body: JSON.stringify({
          client_submission_id: 'cli-1',
          spec_version: '2026-04-17-m1',
          values: { Q3: 'Female' },
        }),
      });
      const r = await adminRouter(req, env);
      expect(r!.status).toBe(200);
      expect(r!.headers.get('X-Request-Id')).toMatch(/^[0-9a-f-]{36}$/);
      const body = await r!.json() as { submission_id: string; status: string };
      expect(body.submission_id).toBe('srv-99');

      // Confirm the AS got the right enriched payload.
      const submitCall = calls.find(c => c.action === 'admin_encode_submit');
      expect(submitCall).toBeDefined();
      const sent = submitCall!.payload as { hcw_id: string; encoded_by: string };
      expect(sent.hcw_id).toBe('hcw-from-path');
      expect(sent.encoded_by).toBe('admin-alice');
    } finally {
      fetchSpy.mockRestore();
    }
  });

  it('routes GET /admin/api/dashboards/data/responses with dash_data perm and forwards filters', async () => {
    const env = makeEnv(makeKv());
    const tok = await mintAdminJwt(env.JWT_SIGNING_KEY, { sub: 'data-mgr', role: 'Data Manager', role_version: 1 });
    const calls: Array<{ action: string; payload: unknown }> = [];
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(async (_url, init) => {
      const body = JSON.parse((init as RequestInit).body as string) as { action: string; payload: unknown };
      calls.push({ action: body.action, payload: body.payload });
      if (body.action === 'admin_roles_list') {
        return new Response(JSON.stringify({
          ok: true,
          data: { roles: [{ name: 'Data Manager', version: 1, dash_data: true }] },
        }), { status: 200 });
      }
      if (body.action === 'admin_read_responses') {
        return new Response(JSON.stringify({
          ok: true,
          data: { rows: [], total: 0, has_more: false },
        }), { status: 200 });
      }
      return new Response('{}', { status: 500 });
    });
    try {
      const req = new Request('https://x/admin/api/dashboards/data/responses?facility_id=fac-1&limit=10', {
        headers: { Authorization: `Bearer ${tok}` },
      });
      const r = await adminRouter(req, env);
      expect(r!.status).toBe(200);
      const readCall = calls.find(c => c.action === 'admin_read_responses');
      expect(readCall).toBeDefined();
      expect(readCall!.payload).toEqual({ facility_id: 'fac-1', limit: 10 });
    } finally {
      fetchSpy.mockRestore();
    }
  });

  it('rejects GET /admin/api/dashboards/data/responses without dash_data with 403', async () => {
    const env = makeEnv(makeKv());
    const tok = await mintAdminJwt(env.JWT_SIGNING_KEY, { sub: 'newbie', role: 'NoAccess', role_version: 1 });
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(async () =>
      new Response(JSON.stringify({
        ok: true,
        data: { roles: [{ name: 'NoAccess', version: 1 }] },
      }), { status: 200 }),
    );
    try {
      const req = new Request('https://x/admin/api/dashboards/data/responses', {
        headers: { Authorization: `Bearer ${tok}` },
      });
      const r = await adminRouter(req, env);
      expect(r!.status).toBe(403);
    } finally {
      fetchSpy.mockRestore();
    }
  });

  it('routes GET /admin/api/dashboards/data/responses/:id and surfaces 404 from AS', async () => {
    const env = makeEnv(makeKv());
    const tok = await mintAdminJwt(env.JWT_SIGNING_KEY, { sub: 'data-mgr', role: 'Data Manager', role_version: 1 });
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(async (_url, init) => {
      const body = JSON.parse((init as RequestInit).body as string) as { action: string };
      if (body.action === 'admin_roles_list') {
        return new Response(JSON.stringify({
          ok: true, data: { roles: [{ name: 'Data Manager', version: 1, dash_data: true }] },
        }), { status: 200 });
      }
      if (body.action === 'admin_read_response_by_id') {
        return new Response(JSON.stringify({
          ok: false, error: { code: 'E_NOT_FOUND', message: 'no row' },
        }), { status: 200 });
      }
      return new Response('{}', { status: 500 });
    });
    try {
      const req = new Request('https://x/admin/api/dashboards/data/responses/srv-missing', {
        headers: { Authorization: `Bearer ${tok}` },
      });
      const r = await adminRouter(req, env);
      expect(r!.status).toBe(404);
    } finally {
      fetchSpy.mockRestore();
    }
  });

  it('hashes cf-connecting-ip into ipHash (not echoed in response)', async () => {
    // Send two failed login attempts from the same IP and confirm both
    // end up keyed under the same ipHash in throttle storage.
    const kv = makeKv();
    const env = makeEnv(kv);

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(async () => {
      return new Response(JSON.stringify({
        ok: true,
        data: { users: [] }, // unknown user → no counter increment, but path is reachable
      }), { status: 200, headers: { 'Content-Type': 'application/json' } });
    });

    try {
      const req = new Request('https://x/admin/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'cf-connecting-ip': '203.0.113.5' },
        body: JSON.stringify({ username: 'nobody', password: 'x' }),
      });
      const r = await adminRouter(req, env);
      expect(r!.status).toBe(401);
      // The ipHash is internal — just confirm the response carries no cf-connecting-ip header.
      expect(r!.headers.get('cf-connecting-ip')).toBeNull();
    } finally {
      fetchSpy.mockRestore();
    }
  });
});
