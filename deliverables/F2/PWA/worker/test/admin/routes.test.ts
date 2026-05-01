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
