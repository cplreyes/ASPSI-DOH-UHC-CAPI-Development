/**
 * F2 Admin Portal — RBAC middleware + RoleVersionCache tests.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 1.12)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§6.4, §10)
 *
 * Stale role_version surfaces as E_AUTH_EXPIRED 401 (per spec — forces full
 * re-login when the role has been version-bumped via PATCH). Missing perm
 * surfaces as E_PERM_DENIED 403.
 */
import { describe, expect, it } from 'vitest';
import { mintAdminJwt } from '../../src/admin/auth';
import {
  RoleVersionCache,
  requirePerm,
  type Role,
} from '../../src/admin/rbac';

interface FakeKV {
  get(k: string): Promise<string | null>;
  put(k: string, v: string): Promise<void>;
  _store: Map<string, string>;
}
function makeKv(): FakeKV {
  const store = new Map<string, string>();
  return {
    async get(k) { return store.get(k) ?? null; },
    async put(k, v) { store.set(k, v); },
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

const KEY = fakeKey();

const ROLES: Role[] = [
  { name: 'Administrator', version: 1, manage_users: true, dash_data: true },
  { name: 'Standard User', version: 1, dash_data: true },
];

function reqWithToken(token: string): Request {
  return new Request('https://x/admin/api/x', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

describe('RoleVersionCache', () => {
  it('round-trips set/get', () => {
    const c = new RoleVersionCache();
    c.set(ROLES[0]!);
    expect(c.get('Administrator', 1)).toEqual(ROLES[0]);
  });

  it('treats different versions as separate entries', () => {
    const c = new RoleVersionCache();
    c.set({ name: 'X', version: 1, p: true });
    c.set({ name: 'X', version: 2, p: false });
    expect(c.get('X', 1)).toEqual({ name: 'X', version: 1, p: true });
    expect(c.get('X', 2)).toEqual({ name: 'X', version: 2, p: false });
  });

  it('returns undefined when entry missing', () => {
    const c = new RoleVersionCache();
    expect(c.get('Ghost', 1)).toBeUndefined();
  });

  it('treats entries beyond TTL as expired', () => {
    const c = new RoleVersionCache();
    c.set(ROLES[0]!);
    // Force expiry by mutating cachedAt directly.
    const internal = (c as unknown as { cache: Map<string, { role: Role; cachedAt: number }> }).cache;
    const entry = internal.get('Administrator:1')!;
    entry.cachedAt = Date.now() - (60 * 60 * 1000 + 1);
    expect(c.get('Administrator', 1)).toBeUndefined();
  });
});

describe('requirePerm', () => {
  it('allows when JWT carries a role with the required perm', async () => {
    const token = await mintAdminJwt(KEY, { sub: 'carl', role: 'Administrator', role_version: 1 });
    const r = await requirePerm(reqWithToken(token), 'manage_users', {
      secret: KEY,
      cache: new RoleVersionCache(),
      rolesListFn: async () => ({ ok: true, data: { roles: ROLES } }),
      kv: makeKv(),
    });
    expect(r.ok).toBe(true);
    expect(r.payload?.sub).toBe('carl');
  });

  it('rejects 403 E_PERM_DENIED when role lacks the perm', async () => {
    const token = await mintAdminJwt(KEY, { sub: 'sue', role: 'Standard User', role_version: 1 });
    const r = await requirePerm(reqWithToken(token), 'manage_users', {
      secret: KEY,
      cache: new RoleVersionCache(),
      rolesListFn: async () => ({ ok: true, data: { roles: ROLES } }),
      kv: makeKv(),
    });
    expect(r.ok).toBe(false);
    expect(r.status).toBe(403);
    expect(r.errorCode).toBe('E_PERM_DENIED');
  });

  it('rejects 401 E_AUTH_EXPIRED when role_version is stale', async () => {
    const token = await mintAdminJwt(KEY, { sub: 'carl', role: 'Administrator', role_version: 1 });
    const bumpedRoles: Role[] = [{ name: 'Administrator', version: 2, manage_users: true, dash_data: true }];
    const r = await requirePerm(reqWithToken(token), 'manage_users', {
      secret: KEY,
      cache: new RoleVersionCache(),
      rolesListFn: async () => ({ ok: true, data: { roles: bumpedRoles } }),
      kv: makeKv(),
    });
    expect(r.ok).toBe(false);
    expect(r.status).toBe(401);
    expect(r.errorCode).toBe('E_AUTH_EXPIRED');
  });

  it('rejects 401 E_AUTH_INVALID when Authorization header is missing or malformed', async () => {
    const noAuth = new Request('https://x/admin/api/x');
    const r = await requirePerm(noAuth, 'dash_data', {
      secret: KEY,
      cache: new RoleVersionCache(),
      rolesListFn: async () => ({ ok: true, data: { roles: ROLES } }),
      kv: makeKv(),
    });
    expect(r.status).toBe(401);
    expect(r.errorCode).toBe('E_AUTH_INVALID');

    const badAuth = new Request('https://x/admin/api/x', { headers: { Authorization: 'NotBearer xyz' } });
    const r2 = await requirePerm(badAuth, 'dash_data', {
      secret: KEY,
      cache: new RoleVersionCache(),
      rolesListFn: async () => ({ ok: true, data: { roles: ROLES } }),
      kv: makeKv(),
    });
    expect(r2.status).toBe(401);
    expect(r2.errorCode).toBe('E_AUTH_INVALID');
  });

  it('rejects 401 E_AUTH_EXPIRED on expired JWT', async () => {
    const token = await mintAdminJwt(KEY, { sub: 'carl', role: 'Administrator', role_version: 1 }, { ttl: -1 });
    const r = await requirePerm(reqWithToken(token), 'dash_data', {
      secret: KEY,
      cache: new RoleVersionCache(),
      rolesListFn: async () => ({ ok: true, data: { roles: ROLES } }),
      kv: makeKv(),
    });
    expect(r.status).toBe(401);
    expect(r.errorCode).toBe('E_AUTH_EXPIRED');
  });

  it('rejects 401 E_AUTH_EXPIRED when JWT.iat predates revoked_user timestamp (admin force-logout)', async () => {
    const token = await mintAdminJwt(KEY, { sub: 'alice', role: 'Administrator', role_version: 1 });
    // Decode the JWT iat so the revoke timestamp is provably AFTER mint.
    const parts = token.split('.');
    const padded = parts[1]!.replace(/-/g, '+').replace(/_/g, '/') + '==='.slice((parts[1]!.length + 3) % 4);
    const payload = JSON.parse(atob(padded)) as { iat: number };
    const kv = makeKv();
    kv._store.set(`revoked_user:alice`, String(payload.iat + 1));
    const r = await requirePerm(reqWithToken(token), 'dash_data', {
      secret: KEY,
      cache: new RoleVersionCache(),
      rolesListFn: async () => ({ ok: true, data: { roles: ROLES } }),
      kv,
    });
    expect(r.status).toBe(401);
    expect(r.errorCode).toBe('E_AUTH_EXPIRED');
  });

  it('allows tokens minted AFTER a revoked_user timestamp (admin reset → user re-logged in)', async () => {
    const token = await mintAdminJwt(KEY, { sub: 'alice', role: 'Administrator', role_version: 1 });
    const kv = makeKv();
    // Revoke timestamp from before the JWT was minted — JWT.iat will be > revokedAt.
    kv._store.set(`revoked_user:alice`, '1');
    const r = await requirePerm(reqWithToken(token), 'dash_data', {
      secret: KEY,
      cache: new RoleVersionCache(),
      rolesListFn: async () => ({ ok: true, data: { roles: ROLES } }),
      kv,
    });
    expect(r.ok).toBe(true);
  });

  it('rejects 401 E_AUTH_EXPIRED when JWT jti is in revoked_jti KV', async () => {
    const token = await mintAdminJwt(KEY, { sub: 'carl', role: 'Administrator', role_version: 1 });
    // Decode jti from the minted token (middle segment, base64url JSON).
    const parts = token.split('.');
    const padded = parts[1]!.replace(/-/g, '+').replace(/_/g, '/') + '==='.slice((parts[1]!.length + 3) % 4);
    const payload = JSON.parse(atob(padded)) as { jti: string };
    const kv = makeKv();
    kv._store.set(`revoked_jti:${payload.jti}`, '1');
    const r = await requirePerm(reqWithToken(token), 'dash_data', {
      secret: KEY,
      cache: new RoleVersionCache(),
      rolesListFn: async () => ({ ok: true, data: { roles: ROLES } }),
      kv,
    });
    expect(r.status).toBe(401);
    expect(r.errorCode).toBe('E_AUTH_EXPIRED');
  });

  it('returns 502 E_BACKEND when rolesListFn fails on cache miss', async () => {
    const token = await mintAdminJwt(KEY, { sub: 'carl', role: 'Administrator', role_version: 1 });
    const r = await requirePerm(reqWithToken(token), 'manage_users', {
      secret: KEY,
      cache: new RoleVersionCache(),
      rolesListFn: async () => ({ ok: false }),
      kv: makeKv(),
    });
    expect(r.status).toBe(502);
    expect(r.errorCode).toBe('E_BACKEND');
  });

  it('skips rolesListFn on cache hit', async () => {
    const cache = new RoleVersionCache();
    cache.set(ROLES[0]!);
    const token = await mintAdminJwt(KEY, { sub: 'carl', role: 'Administrator', role_version: 1 });
    let calls = 0;
    const r = await requirePerm(reqWithToken(token), 'manage_users', {
      secret: KEY,
      cache,
      rolesListFn: async () => { calls++; return { ok: true, data: { roles: ROLES } }; },
      kv: makeKv(),
    });
    expect(r.ok).toBe(true);
    expect(calls).toBe(0);
  });

  it('rejects 401 E_AUTH_EXPIRED when JWT role is missing entirely from current roles', async () => {
    const token = await mintAdminJwt(KEY, { sub: 'orphan', role: 'GhostRole', role_version: 1 });
    const r = await requirePerm(reqWithToken(token), 'dash_data', {
      secret: KEY,
      cache: new RoleVersionCache(),
      rolesListFn: async () => ({ ok: true, data: { roles: ROLES } }),
      kv: makeKv(),
    });
    expect(r.status).toBe(401);
    expect(r.errorCode).toBe('E_AUTH_EXPIRED');
  });
});
