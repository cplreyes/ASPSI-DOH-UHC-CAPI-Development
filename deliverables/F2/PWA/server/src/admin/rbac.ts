/**
 * F2 Admin Portal — RBAC middleware + role perm cache (port of
 * worker/src/admin/rbac.ts). Semantics identical: bearer verify →
 * revocation (auth_kv replaces CF KV) → pwc gate → cached-role version
 * validation with authoritative refetch on mismatch → perm flag check.
 */
import { verifyAdminJwt, type AdminJwtPayload } from './auth.js';

export type Role = { name: string; version: number } & Record<string, unknown>;

export class RoleVersionCache {
  private cache = new Map<string, { role: Role; cachedAt: number }>();
  private TTL_MS = 5 * 60 * 1000;

  get(name: string): Role | undefined {
    const e = this.cache.get(name);
    if (!e) return undefined;
    if (Date.now() - e.cachedAt > this.TTL_MS) return undefined;
    return e.role;
  }

  set(role: Role): void {
    this.cache.set(role.name, { role, cachedAt: Date.now() });
  }

  invalidate(name: string): void {
    this.cache.delete(name);
  }
}

export interface RbacKv {
  kvGet(key: string): Promise<string | null>;
}

export interface RolesListResp {
  ok: boolean;
  data?: { roles: Role[] };
}

export interface RbacOpts {
  secret: string;
  cache: RoleVersionCache;
  rolesListFn: () => Promise<RolesListResp>;
  kv: RbacKv;
}

export interface RbacResult {
  ok: boolean;
  status?: number;
  errorCode?: string;
  payload?: AdminJwtPayload;
}

const BEARER_RE = /^Bearer (.+)$/;

/**
 * Returns { ok: true, payload } or a 401/403/502 failure — status + code
 * mapping identical to the Worker (E_AUTH_INVALID / E_AUTH_EXPIRED /
 * E_PASSWORD_CHANGE_REQUIRED / E_PERM_DENIED / E_BACKEND).
 */
export async function requirePerm(
  authHeader: string | undefined,
  perm: string,
  opts: RbacOpts,
): Promise<RbacResult> {
  const m = BEARER_RE.exec(authHeader || '');
  if (!m) return { ok: false, status: 401, errorCode: 'E_AUTH_INVALID' };

  const token = m[1]!;
  const v = await verifyAdminJwt(opts.secret, token);
  if (!v.ok) return { ok: false, status: 401, errorCode: 'E_AUTH_EXPIRED' };

  const payload = v.payload;
  const revokedJti = await opts.kv.kvGet(`revoked_jti:${payload.jti}`);
  if (revokedJti) return { ok: false, status: 401, errorCode: 'E_AUTH_EXPIRED' };
  const revokedUser = await opts.kv.kvGet(`revoked_user:${payload.sub}`);
  if (revokedUser) {
    const revokedAt = Number(revokedUser);
    if (Number.isFinite(revokedAt) && payload.iat < revokedAt) {
      return { ok: false, status: 401, errorCode: 'E_AUTH_EXPIRED' };
    }
  }

  // R2-#57: password-change owed → every RBAC-gated route is barred; only
  // PATCH /admin/api/me/password (which never calls requirePerm) works.
  if (payload.pwc === true) {
    return { ok: false, status: 403, errorCode: 'E_PASSWORD_CHANGE_REQUIRED' };
  }

  // R2-#56: per-request version validation with authoritative refetch.
  const cached = opts.cache.get(payload.role);
  let role: Role | undefined;
  if (cached && cached.version === payload.role_version) {
    role = cached;
  } else {
    const rl = await opts.rolesListFn();
    if (!rl.ok || !rl.data) return { ok: false, status: 502, errorCode: 'E_BACKEND' };
    const found = rl.data.roles.find((r) => r.name === payload.role);
    if (!found) {
      return { ok: false, status: 401, errorCode: 'E_AUTH_EXPIRED' };
    }
    opts.cache.set(found);
    if (found.version !== payload.role_version) {
      return { ok: false, status: 401, errorCode: 'E_AUTH_EXPIRED' };
    }
    role = found;
  }

  if (!role[perm]) return { ok: false, status: 403, errorCode: 'E_PERM_DENIED' };
  return { ok: true, payload };
}
