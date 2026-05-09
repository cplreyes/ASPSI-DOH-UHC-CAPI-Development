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
import { describe, expect, it, vi } from 'vitest';
import {
  handleLogin,
  handleLogout,
  handleChangeMyPassword,
  type AuthAuditCtx,
  type ChangeMyPasswordAsCallable,
  type LastLoginFn,
} from '../../../src/admin/handlers/auth';
import { hashPassword, mintAdminJwt, verifyAdminJwt } from '../../../src/admin/auth';
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

  it('fires auditFn with admin_login context on success and skips it on failures', async () => {
    const kv = makeKv();
    const env = { JWT_SIGNING_KEY: KEY, F2_AUTH: kv as unknown as KVNamespace };
    const user = await makeUser('alice', 'CorrectPw1', 'Administrator', false);
    const auditFn = vi.fn<(ctx: AuthAuditCtx) => void>();

    // Success → auditFn called once with admin_login context.
    const ok = await handleLogin(
      { username: 'alice', password: 'CorrectPw1' },
      'iphash-1',
      env,
      async () => ({ ok: true, data: { users: [user] } }),
      async () => ({ ok: true, data: { roles: ROLES } }),
      auditFn,
    );
    expect(ok.status).toBe(200);
    expect(auditFn).toHaveBeenCalledTimes(1);
    const ctx = auditFn.mock.calls[0]![0]!;
    expect(ctx.event_type).toBe('admin_login');
    expect(ctx.actor_username).toBe('alice');
    expect(ctx.actor_role).toBe('Administrator');
    expect(ctx.client_ip_hash).toBe('iphash-1');
    expect(ctx.actor_jti).toMatch(/^[0-9a-f-]{36}$/);

    // Failure (wrong password) → auditFn not called.
    auditFn.mockClear();
    const bad = await handleLogin(
      { username: 'alice', password: 'WrongPw1' },
      'iphash-1',
      env,
      async () => ({ ok: true, data: { users: [user] } }),
      async () => ({ ok: true, data: { roles: ROLES } }),
      auditFn,
    );
    expect(bad.status).toBe(401);
    expect(auditFn).not.toHaveBeenCalled();
  });

  it('stamps pwc claim on JWT when user.password_must_change is true (R2-#57)', async () => {
    // Server-enforce password rotation. A token issued to a user under
    // password_must_change carries pwc:true, which requirePerm reads to
    // reject every gated route until the rotation endpoint clears it.
    const kv = makeKv();
    const env = { JWT_SIGNING_KEY: KEY, F2_AUTH: kv as unknown as KVNamespace };
    const user = await makeUser('newbie', 'TempPw123', 'Standard User', true);
    const r = await handleLogin(
      { username: 'newbie', password: 'TempPw123' },
      'iphash-1',
      env,
      async () => ({ ok: true, data: { users: [user] } }),
      async () => ({ ok: true, data: { roles: ROLES } }),
    );
    expect(r.status).toBe(200);
    const body = (await r.json()) as { token: string };
    const v = await verifyAdminJwt(KEY, body.token);
    expect(v.ok).toBe(true);
    if (v.ok) {
      expect(v.payload.pwc).toBe(true);
    }
  });

  it('omits pwc claim when user.password_must_change is false (R2-#57)', async () => {
    const kv = makeKv();
    const env = { JWT_SIGNING_KEY: KEY, F2_AUTH: kv as unknown as KVNamespace };
    const user = await makeUser('alice', 'CorrectPw1', 'Administrator', false);
    const r = await handleLogin(
      { username: 'alice', password: 'CorrectPw1' },
      'iphash-1',
      env,
      async () => ({ ok: true, data: { users: [user] } }),
      async () => ({ ok: true, data: { roles: ROLES } }),
    );
    expect(r.status).toBe(200);
    const body = (await r.json()) as { token: string };
    const v = await verifyAdminJwt(KEY, body.token);
    expect(v.ok).toBe(true);
    if (v.ok) {
      // Optional claim should be absent on regular tokens.
      expect(v.payload.pwc).toBeUndefined();
    }
  });

  it('fires lastLoginFn with username on success and skips it on failures (R2-#66)', async () => {
    const kv = makeKv();
    const env = { JWT_SIGNING_KEY: KEY, F2_AUTH: kv as unknown as KVNamespace };
    const user = await makeUser('alice', 'CorrectPw1', 'Administrator', false);
    const lastLoginFn = vi.fn<LastLoginFn>();

    // Success → lastLoginFn called once with the username.
    const ok = await handleLogin(
      { username: 'alice', password: 'CorrectPw1' },
      'iphash-1',
      env,
      async () => ({ ok: true, data: { users: [user] } }),
      async () => ({ ok: true, data: { roles: ROLES } }),
      undefined,
      lastLoginFn,
    );
    expect(ok.status).toBe(200);
    expect(lastLoginFn).toHaveBeenCalledTimes(1);
    expect(lastLoginFn).toHaveBeenCalledWith('alice');

    // Failure (wrong password) → lastLoginFn not called.
    lastLoginFn.mockClear();
    const bad = await handleLogin(
      { username: 'alice', password: 'WrongPw1' },
      'iphash-1',
      env,
      async () => ({ ok: true, data: { users: [user] } }),
      async () => ({ ok: true, data: { roles: ROLES } }),
      undefined,
      lastLoginFn,
    );
    expect(bad.status).toBe(401);
    expect(lastLoginFn).not.toHaveBeenCalled();
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

describe('handleLogout', () => {
  it('returns 401 E_AUTH_INVALID when Authorization header is missing', async () => {
    const kv = makeKv();
    const env = { JWT_SIGNING_KEY: KEY, F2_AUTH: kv as unknown as KVNamespace };
    const req = new Request('https://x/admin/api/logout', { method: 'POST' });
    const r = await handleLogout(req, 'iphash-test', env);
    expect(r.status).toBe(401);
    const body = await r.json() as { error: { code: string } };
    expect(body.error.code).toBe('E_AUTH_INVALID');
  });

  it('returns 401 E_AUTH_INVALID on malformed Authorization header', async () => {
    const kv = makeKv();
    const env = { JWT_SIGNING_KEY: KEY, F2_AUTH: kv as unknown as KVNamespace };
    const req = new Request('https://x/admin/api/logout', {
      method: 'POST',
      headers: { Authorization: 'Token xyz' },
    });
    const r = await handleLogout(req, 'iphash-test', env);
    expect(r.status).toBe(401);
    const body = await r.json() as { error: { code: string } };
    expect(body.error.code).toBe('E_AUTH_INVALID');
  });

  it('returns 401 E_AUTH_INVALID on bad signature', async () => {
    const kv = makeKv();
    const env = { JWT_SIGNING_KEY: KEY, F2_AUTH: kv as unknown as KVNamespace };
    const tok = await mintAdminJwt(KEY, { sub: 'alice', role: 'Administrator', role_version: 1 });
    const tampered = tok.slice(0, -2) + 'xx';
    const req = new Request('https://x/admin/api/logout', {
      method: 'POST',
      headers: { Authorization: `Bearer ${tampered}` },
    });
    const r = await handleLogout(req, 'iphash-test', env);
    expect(r.status).toBe(401);
  });

  it('returns 401 E_AUTH_EXPIRED for already-expired token (no revocation needed)', async () => {
    const kv = makeKv();
    const env = { JWT_SIGNING_KEY: KEY, F2_AUTH: kv as unknown as KVNamespace };
    const tok = await mintAdminJwt(KEY, { sub: 'alice', role: 'Administrator', role_version: 1 }, { ttl: -1 });
    const req = new Request('https://x/admin/api/logout', {
      method: 'POST',
      headers: { Authorization: `Bearer ${tok}` },
    });
    const r = await handleLogout(req, 'iphash-test', env);
    expect(r.status).toBe(401);
    const body = await r.json() as { error: { code: string } };
    expect(body.error.code).toBe('E_AUTH_EXPIRED');
    expect(kv._puts.length).toBe(0);
  });

  it('returns 204 and writes revoked_jti to KV with TTL = exp - now + 60 buffer', async () => {
    const kv = makeKv();
    const env = { JWT_SIGNING_KEY: KEY, F2_AUTH: kv as unknown as KVNamespace };
    const tok = await mintAdminJwt(KEY, { sub: 'alice', role: 'Administrator', role_version: 1 }, { ttl: 4 * 3600 });
    const req = new Request('https://x/admin/api/logout', {
      method: 'POST',
      headers: { Authorization: `Bearer ${tok}` },
    });
    const r = await handleLogout(req, 'iphash-test', env);
    expect(r.status).toBe(204);

    // Decode the jti and assert KV write.
    const parts = tok.split('.');
    const padded = parts[1]!.replace(/-/g, '+').replace(/_/g, '/') + '==='.slice((parts[1]!.length + 3) % 4);
    const payload = JSON.parse(atob(padded)) as { jti: string; exp: number };
    expect(kv._puts.length).toBe(1);
    expect(kv._puts[0]!.key).toBe(`revoked_jti:${payload.jti}`);
    expect(kv._puts[0]!.value).toBe('1');

    const now = Math.floor(Date.now() / 1000);
    const expectedTtl = payload.exp - now + 60;
    const actualTtl = kv._puts[0]!.ttl!;
    expect(actualTtl).toBeGreaterThanOrEqual(expectedTtl - 5);
    expect(actualTtl).toBeLessThanOrEqual(expectedTtl + 5);
  });

  it('fires auditFn with admin_logout context on success and skips it on failures', async () => {
    const kv = makeKv();
    const env = { JWT_SIGNING_KEY: KEY, F2_AUTH: kv as unknown as KVNamespace };
    const auditFn = vi.fn<(ctx: AuthAuditCtx) => void>();

    // Success → auditFn fires with admin_logout context.
    const tok = await mintAdminJwt(KEY, { sub: 'alice', role: 'Administrator', role_version: 1 });
    const okReq = new Request('https://x/admin/api/logout', {
      method: 'POST',
      headers: { Authorization: `Bearer ${tok}` },
    });
    const ok = await handleLogout(okReq, 'iphash-7', env, auditFn);
    expect(ok.status).toBe(204);
    expect(auditFn).toHaveBeenCalledTimes(1);
    const ctx = auditFn.mock.calls[0]![0]!;
    expect(ctx.event_type).toBe('admin_logout');
    expect(ctx.actor_username).toBe('alice');
    expect(ctx.actor_role).toBe('Administrator');
    expect(ctx.client_ip_hash).toBe('iphash-7');
    expect(ctx.actor_jti).toMatch(/^[0-9a-f-]{36}$/);

    // Failure (no Authorization header) → auditFn not called.
    auditFn.mockClear();
    const noAuth = new Request('https://x/admin/api/logout', { method: 'POST' });
    const bad = await handleLogout(noAuth, 'iphash-7', env, auditFn);
    expect(bad.status).toBe(401);
    expect(auditFn).not.toHaveBeenCalled();
  });

  it('revoked token then fails RBAC check (integration-style)', async () => {
    // Verifies the round-trip: logout writes the same key shape rbac.ts reads.
    const kv = makeKv();
    const env = { JWT_SIGNING_KEY: KEY, F2_AUTH: kv as unknown as KVNamespace };
    const tok = await mintAdminJwt(KEY, { sub: 'alice', role: 'Administrator', role_version: 1 });
    const req = new Request('https://x/admin/api/logout', {
      method: 'POST',
      headers: { Authorization: `Bearer ${tok}` },
    });
    await handleLogout(req, 'iphash-test', env);

    const parts = tok.split('.');
    const padded = parts[1]!.replace(/-/g, '+').replace(/_/g, '/') + '==='.slice((parts[1]!.length + 3) % 4);
    const payload = JSON.parse(atob(padded)) as { jti: string };
    expect(await kv.get(`revoked_jti:${payload.jti}`)).toBe('1');

    // JWT itself still verifies (sig OK, not expired) — revocation lives in KV.
    const v = await verifyAdminJwt(KEY, tok);
    expect(v.ok).toBe(true);
  });
});

describe('handleChangeMyPassword — R2-#134', () => {
  async function makeReq(token: string, body: Record<string, unknown>): Promise<Request> {
    return new Request('https://x/admin/api/me/password', {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  }

  it('returns 401 E_AUTH_INVALID without Authorization header', async () => {
    const kv = makeKv();
    const env = { JWT_SIGNING_KEY: KEY, F2_AUTH: kv as unknown as KVNamespace };
    const req = new Request('https://x/admin/api/me/password', {
      method: 'PATCH',
      body: JSON.stringify({ current_password: 'a', new_password: 'b' }),
    });
    const r = await handleChangeMyPassword(
      req,
      env,
      async () => ({ ok: true, data: { users: [] } }),
      async () => ({ ok: true, data: { roles: ROLES } }),
      async () => ({ ok: true, data: { username: '' } }),
    );
    expect(r.status).toBe(401);
  });

  it('returns 400 E_VALIDATION on missing fields', async () => {
    const kv = makeKv();
    const env = { JWT_SIGNING_KEY: KEY, F2_AUTH: kv as unknown as KVNamespace };
    const tok = await mintAdminJwt(KEY, { sub: 'alice', role: 'Administrator', role_version: 1 });
    const req = await makeReq(tok, {});
    const r = await handleChangeMyPassword(
      req,
      env,
      async () => ({ ok: true, data: { users: [] } }),
      async () => ({ ok: true, data: { roles: ROLES } }),
      async () => ({ ok: true, data: { username: '' } }),
    );
    expect(r.status).toBe(400);
    const body = (await r.json()) as { error: { code: string } };
    expect(body.error.code).toBe('E_VALIDATION');
  });

  it('returns 400 E_VALIDATION when new_password < 8 characters', async () => {
    const kv = makeKv();
    const env = { JWT_SIGNING_KEY: KEY, F2_AUTH: kv as unknown as KVNamespace };
    const tok = await mintAdminJwt(KEY, { sub: 'alice', role: 'Administrator', role_version: 1 });
    const req = await makeReq(tok, { current_password: 'CorrectPw1', new_password: 'short' });
    const r = await handleChangeMyPassword(
      req,
      env,
      async () => ({ ok: true, data: { users: [] } }),
      async () => ({ ok: true, data: { roles: ROLES } }),
      async () => ({ ok: true, data: { username: '' } }),
    );
    expect(r.status).toBe(400);
  });

  it('returns 400 E_VALIDATION when new_password equals current_password', async () => {
    const kv = makeKv();
    const env = { JWT_SIGNING_KEY: KEY, F2_AUTH: kv as unknown as KVNamespace };
    const tok = await mintAdminJwt(KEY, { sub: 'alice', role: 'Administrator', role_version: 1 });
    const req = await makeReq(tok, { current_password: 'SamePw1234', new_password: 'SamePw1234' });
    const r = await handleChangeMyPassword(
      req,
      env,
      async () => ({ ok: true, data: { users: [] } }),
      async () => ({ ok: true, data: { roles: ROLES } }),
      async () => ({ ok: true, data: { username: '' } }),
    );
    expect(r.status).toBe(400);
  });

  it('returns 401 E_AUTH_INVALID when current_password is wrong', async () => {
    const kv = makeKv();
    const env = { JWT_SIGNING_KEY: KEY, F2_AUTH: kv as unknown as KVNamespace };
    const user = await makeUser('alice', 'CorrectPw1', 'Administrator', false);
    const tok = await mintAdminJwt(KEY, { sub: 'alice', role: 'Administrator', role_version: 1 });
    const req = await makeReq(tok, { current_password: 'WrongPw1', new_password: 'NewSafePw1' });
    const r = await handleChangeMyPassword(
      req,
      env,
      async () => ({ ok: true, data: { users: [user] } }),
      async () => ({ ok: true, data: { roles: ROLES } }),
      async () => ({ ok: true, data: { username: 'alice' } }),
    );
    expect(r.status).toBe(401);
    const body = (await r.json()) as { error: { code: string } };
    expect(body.error.code).toBe('E_AUTH_INVALID');
  });

  it('returns 200 + fresh JWT with password_must_change=false on happy path', async () => {
    const kv = makeKv();
    const env = { JWT_SIGNING_KEY: KEY, F2_AUTH: kv as unknown as KVNamespace };
    const user = await makeUser('alice', 'CorrectPw1', 'Administrator', true);
    const tok = await mintAdminJwt(KEY, { sub: 'alice', role: 'Administrator', role_version: 1 });
    const asCall = vi.fn<ChangeMyPasswordAsCallable>().mockResolvedValue({
      ok: true,
      data: { username: 'alice' },
    });
    const req = await makeReq(tok, { current_password: 'CorrectPw1', new_password: 'BrandNewPw1' });
    const r = await handleChangeMyPassword(
      req,
      env,
      async () => ({ ok: true, data: { users: [user] } }),
      async () => ({ ok: true, data: { roles: ROLES } }),
      asCall,
    );
    expect(r.status).toBe(200);
    const body = (await r.json()) as {
      token: string;
      role: string;
      role_version: number;
      password_must_change: boolean;
    };
    expect(body.password_must_change).toBe(false);
    expect(body.role).toBe('Administrator');
    expect(body.role_version).toBe(1);
    expect(body.token).toMatch(/.+\..+\..+/);

    // AS RPC was called with the freshly-hashed new password (not equal to
    // the input), and with the actor's username from the JWT.
    expect(asCall).toHaveBeenCalledOnce();
    const arg = asCall.mock.calls[0]![0]!;
    expect(arg.username).toBe('alice');
    expect(arg.password_hash).not.toBe('BrandNewPw1');
    expect(arg.password_hash.length).toBeGreaterThan(20);

    // Fresh token verifies and the new sub/role/role_version match.
    // R2-#57: the freshly-minted JWT must NOT carry pwc:true even though
    // the user originally had password_must_change=true — that's the
    // whole point of the rotation flow.
    const v = await verifyAdminJwt(KEY, body.token);
    expect(v.ok).toBe(true);
    if (v.ok) {
      expect(v.payload.sub).toBe('alice');
      expect(v.payload.role).toBe('Administrator');
      expect(v.payload.pwc).toBeUndefined();
    }
  });

  it('fires auditFn with admin_password_change context on success', async () => {
    const kv = makeKv();
    const env = { JWT_SIGNING_KEY: KEY, F2_AUTH: kv as unknown as KVNamespace };
    const user = await makeUser('alice', 'CorrectPw1', 'Administrator', true);
    const tok = await mintAdminJwt(KEY, { sub: 'alice', role: 'Administrator', role_version: 1 });
    const auditFn = vi.fn<(ctx: AuthAuditCtx) => void>();
    const req = await makeReq(tok, { current_password: 'CorrectPw1', new_password: 'BrandNewPw1' });
    await handleChangeMyPassword(
      req,
      env,
      async () => ({ ok: true, data: { users: [user] } }),
      async () => ({ ok: true, data: { roles: ROLES } }),
      async () => ({ ok: true, data: { username: 'alice' } }),
      auditFn,
      'iphash-9',
    );
    expect(auditFn).toHaveBeenCalledTimes(1);
    const ctx = auditFn.mock.calls[0]![0]!;
    expect(ctx.event_type).toBe('admin_password_change');
    expect(ctx.actor_username).toBe('alice');
    expect(ctx.client_ip_hash).toBe('iphash-9');
  });
});
