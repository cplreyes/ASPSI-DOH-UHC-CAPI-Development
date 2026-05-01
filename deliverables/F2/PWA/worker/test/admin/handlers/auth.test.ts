/**
 * F2 Admin Portal — handleLogin tests.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 1.11)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.1, §10)
 *
 * Covers: throttle gate (E_AUTH_LOCKED 429 with Retry-After), unknown user
 * (E_AUTH_INVALID 401), wrong password (E_AUTH_INVALID 401 + counter
 * increments), success (200 + token + role + password_must_change), backend
 * failure passthrough (E_BACKEND 502), and per-user reset on success.
 */
import { describe, expect, it } from 'vitest';
import { handleLogin } from '../../../src/admin/handlers/auth';
import { hashPassword, verifyAdminJwt } from '../../../src/admin/auth';
import { recordFailedLogin } from '../../../src/admin/throttle';

interface FakeKV {
  get(k: string): Promise<string | null>;
  put(k: string, v: string, opts?: { expirationTtl?: number }): Promise<void>;
  delete(k: string): Promise<void>;
  _store: Map<string, string>;
  _puts: Array<{ key: string; value: string; ttl?: number }>;
}

function makeKv(): FakeKV {
  const store = new Map<string, string>();
  const puts: Array<{ key: string; value: string; ttl?: number }> = [];
  return {
    async get(k) { return store.get(k) ?? null; },
    async put(k, v, opts) { store.set(k, v); puts.push({ key: k, value: v, ttl: opts?.expirationTtl }); },
    async delete(k) { store.delete(k); },
    _store: store,
    _puts: puts,
  };
}

function fakeKey(): string {
  const bytes = new Uint8Array(32);
  for (let i = 0; i < bytes.length; i++) bytes[i] = i;
  let s = '';
  for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]!);
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

async function makeUser(username: string, password: string, role = 'Administrator', mustChange: boolean | string = false) {
  return {
    username,
    password_hash: await hashPassword(password),
    password_must_change: mustChange,
    role,
  };
}

const ROLES = [
  { name: 'Administrator', version: 1, manage_users: true, dash_data: true },
  { name: 'Standard User', version: 1, dash_data: true },
];

const KEY = fakeKey();

describe('handleLogin', () => {
  it('returns 400 on missing username or password', async () => {
    const kv = makeKv();
    const env = { JWT_SIGNING_KEY: KEY, F2_AUTH: kv as unknown as KVNamespace };
    const r = await handleLogin(
      { username: 'alice' },
      'iphash-1',
      env,
      async () => ({ ok: true, data: { users: [] } }),
      async () => ({ ok: true, data: { roles: ROLES } }),
    );
    expect(r.status).toBe(400);
  });

  it('returns 401 E_AUTH_INVALID on unknown user', async () => {
    const kv = makeKv();
    const env = { JWT_SIGNING_KEY: KEY, F2_AUTH: kv as unknown as KVNamespace };
    const r = await handleLogin(
      { username: 'nobody', password: 'x' },
      'iphash-1',
      env,
      async () => ({ ok: true, data: { users: [] } }),
      async () => ({ ok: true, data: { roles: ROLES } }),
    );
    expect(r.status).toBe(401);
    const body = await r.json() as { error: { code: string } };
    expect(body.error.code).toBe('E_AUTH_INVALID');
  });

  it('returns 401 on wrong password and increments both throttle counters', async () => {
    const kv = makeKv();
    const user = await makeUser('alice', 'CorrectPw1');
    const env = { JWT_SIGNING_KEY: KEY, F2_AUTH: kv as unknown as KVNamespace };
    const r = await handleLogin(
      { username: 'alice', password: 'WrongPw1' },
      'iphash-1',
      env,
      async () => ({ ok: true, data: { users: [user] } }),
      async () => ({ ok: true, data: { roles: ROLES } }),
    );
    expect(r.status).toBe(401);
    const body = await r.json() as { error: { code: string } };
    expect(body.error.code).toBe('E_AUTH_INVALID');
    expect(kv._puts.length).toBe(2);
    const keys = kv._puts.map(p => p.key);
    expect(keys.some(k => k.includes('user:alice'))).toBe(true);
    expect(keys.some(k => k.includes('ip:iphash-1'))).toBe(true);
  });

  it('returns 200 with token + role on correct credentials', async () => {
    const kv = makeKv();
    const user = await makeUser('alice', 'CorrectPw1', 'Administrator', false);
    const env = { JWT_SIGNING_KEY: KEY, F2_AUTH: kv as unknown as KVNamespace };
    const before = Math.floor(Date.now() / 1000);
    const r = await handleLogin(
      { username: 'alice', password: 'CorrectPw1' },
      'iphash-1',
      env,
      async () => ({ ok: true, data: { users: [user] } }),
      async () => ({ ok: true, data: { roles: ROLES } }),
    );
    expect(r.status).toBe(200);
    const body = await r.json() as {
      token: string;
      role: string;
      role_version: number;
      expires_at: number;
      password_must_change: boolean;
    };
    expect(body.token).toMatch(/.+\..+\..+/);
    expect(body.role).toBe('Administrator');
    expect(body.role_version).toBe(1);
    expect(body.password_must_change).toBe(false);
    expect(body.expires_at).toBeGreaterThan(before);

    // Token verifies and carries the expected claims.
    const v = await verifyAdminJwt(KEY, body.token);
    expect(v.ok).toBe(true);
    if (v.ok) {
      expect(v.payload.sub).toBe('alice');
      expect(v.payload.role).toBe('Administrator');
      expect(v.payload.role_version).toBe(1);
    }
  });

  it('echoes password_must_change=true for newly-created accounts', async () => {
    const kv = makeKv();
    const user = await makeUser('newbie', 'TempPw123', 'Standard User', true);
    const env = { JWT_SIGNING_KEY: KEY, F2_AUTH: kv as unknown as KVNamespace };
    const r = await handleLogin(
      { username: 'newbie', password: 'TempPw123' },
      'iphash-1',
      env,
      async () => ({ ok: true, data: { users: [user] } }),
      async () => ({ ok: true, data: { roles: ROLES } }),
    );
    expect(r.status).toBe(200);
    const body = await r.json() as { password_must_change: boolean };
    expect(body.password_must_change).toBe(true);
  });

  it('returns 429 E_AUTH_LOCKED with Retry-After when per-user throttle exceeded', async () => {
    const kv = makeKv();
    for (let i = 0; i < 10; i++) await recordFailedLogin(kv, 'alice', 'iphash-1');
    const user = await makeUser('alice', 'CorrectPw1');
    const env = { JWT_SIGNING_KEY: KEY, F2_AUTH: kv as unknown as KVNamespace };
    const r = await handleLogin(
      { username: 'alice', password: 'CorrectPw1' },
      'iphash-1',
      env,
      async () => ({ ok: true, data: { users: [user] } }),
      async () => ({ ok: true, data: { roles: ROLES } }),
    );
    expect(r.status).toBe(429);
    const body = await r.json() as { error: { code: string } };
    expect(body.error.code).toBe('E_AUTH_LOCKED');
    const ra = r.headers.get('Retry-After');
    expect(ra).not.toBeNull();
    expect(Number(ra)).toBeGreaterThan(0);
    expect(Number(ra)).toBeLessThanOrEqual(15 * 60);
  });

  it('returns 502 E_BACKEND when users list fails', async () => {
    const kv = makeKv();
    const env = { JWT_SIGNING_KEY: KEY, F2_AUTH: kv as unknown as KVNamespace };
    const r = await handleLogin(
      { username: 'alice', password: 'x' },
      'iphash-1',
      env,
      async () => ({ ok: false, error: { code: 'E_BACKEND', message: 'AS down' } }),
      async () => ({ ok: true, data: { roles: ROLES } }),
    );
    expect(r.status).toBe(502);
    const body = await r.json() as { error: { code: string } };
    expect(body.error.code).toBe('E_BACKEND');
  });

  it('returns 502 when role for user is missing in roles list (data integrity)', async () => {
    const kv = makeKv();
    const user = await makeUser('alice', 'CorrectPw1', 'GhostRole');
    const env = { JWT_SIGNING_KEY: KEY, F2_AUTH: kv as unknown as KVNamespace };
    const r = await handleLogin(
      { username: 'alice', password: 'CorrectPw1' },
      'iphash-1',
      env,
      async () => ({ ok: true, data: { users: [user] } }),
      async () => ({ ok: true, data: { roles: ROLES } }),
    );
    expect(r.status).toBe(502);
  });

  it('resets per-user throttle on successful login but leaves per-IP intact', async () => {
    const kv = makeKv();
    for (let i = 0; i < 5; i++) await recordFailedLogin(kv, 'alice', 'iphash-1');
    const user = await makeUser('alice', 'CorrectPw1');
    const env = { JWT_SIGNING_KEY: KEY, F2_AUTH: kv as unknown as KVNamespace };
    const r = await handleLogin(
      { username: 'alice', password: 'CorrectPw1' },
      'iphash-1',
      env,
      async () => ({ ok: true, data: { users: [user] } }),
      async () => ({ ok: true, data: { roles: ROLES } }),
    );
    expect(r.status).toBe(200);
    const winStart = Math.floor(Date.now() / 1000 / (15 * 60)) * (15 * 60);
    expect(kv._store.has(`throttle:login:user:alice:${winStart}`)).toBe(false);
    expect(kv._store.has(`throttle:login:ip:iphash-1:${winStart}`)).toBe(true);
  });
});
