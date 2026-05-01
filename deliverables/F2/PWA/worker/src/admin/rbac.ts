/**
 * F2 Admin Portal — RBAC middleware + role-version-keyed perm cache.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 1.12)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§6.4, §10)
 *
 * Cache key is `name:version` so a role PATCH (which bumps F2_Roles.version)
 * naturally invalidates stale entries: a JWT minted under v1 won't match a
 * v2 cache entry, the lookup misses, and the fresh roles list is fetched.
 * Tokens minted before the bump fail with E_AUTH_EXPIRED — clients re-login
 * and get a token with the new role_version. TTL is a backstop in case AS
 * pushes a role-version update we haven't seen via cache invalidation.
 */
import { verifyAdminJwt, type AdminJwtPayload } from './auth';

export interface Role {
  name: string;
  version: number;
  [perm: string]: unknown;
}

export class RoleVersionCache {
  private cache = new Map<string, { role: Role; cachedAt: number }>();
  private TTL_MS = 60 * 60 * 1000;

  private key(name: string, version: number): string {
    return `${name}:${version}`;
  }

  get(name: string, version: number): Role | undefined {
    const e = this.cache.get(this.key(name, version));
    if (!e) return undefined;
    if (Date.now() - e.cachedAt > this.TTL_MS) return undefined;
    return e.role;
  }

  set(role: Role): void {
    this.cache.set(this.key(role.name, role.version), { role, cachedAt: Date.now() });
  }
}

export interface RbacKv {
  get(key: string): Promise<string | null>;
}

export interface RolesListResp {
  ok: boolean;
  data?: { roles: Role[] };
  error?: { code: string; message: string };
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
 * Verify the bearer token, check revocation, resolve role+version, and
 * confirm the requested perm is set on the role. Returns one of:
 *   - { ok: true, payload }                                      — proceed
 *   - { ok: false, status: 401, errorCode: 'E_AUTH_INVALID' }    — no/bad header
 *   - { ok: false, status: 401, errorCode: 'E_AUTH_EXPIRED' }    — bad sig / expired / revoked / stale role_version
 *   - { ok: false, status: 403, errorCode: 'E_PERM_DENIED' }     — role lacks perm
 *   - { ok: false, status: 502, errorCode: 'E_BACKEND' }         — Apps Script unreachable
 */
export async function requirePerm(req: Request, perm: string, opts: RbacOpts): Promise<RbacResult> {
  const auth = req.headers.get('Authorization') || '';
  const m = BEARER_RE.exec(auth);
  if (!m) return { ok: false, status: 401, errorCode: 'E_AUTH_INVALID' };

  const token = m[1]!;
  const v = await verifyAdminJwt(opts.secret, token);
  if (!v.ok) return { ok: false, status: 401, errorCode: 'E_AUTH_EXPIRED' };

  const payload = v.payload;
  // Per-token revocation (logout, /admin/api/logout from this user).
  const revokedJti = await opts.kv.get(`revoked_jti:${payload.jti}`);
  if (revokedJti) return { ok: false, status: 401, errorCode: 'E_AUTH_EXPIRED' };
  // Per-user revocation (admin-initiated revoke-sessions; force-logout
  // every JWT held by `payload.sub` regardless of jti). Issued_at vs
  // revoked-at comparison: a token minted AFTER the revoke timestamp
  // is allowed through (admin issued a fresh password reset, user
  // logged in again, the new JWT predates revocation).
  const revokedUser = await opts.kv.get(`revoked_user:${payload.sub}`);
  if (revokedUser) {
    const revokedAt = Number(revokedUser);
    if (Number.isFinite(revokedAt) && payload.iat < revokedAt) {
      return { ok: false, status: 401, errorCode: 'E_AUTH_EXPIRED' };
    }
  }

  let role = opts.cache.get(payload.role, payload.role_version);
  if (!role) {
    const rl = await opts.rolesListFn();
    if (!rl.ok || !rl.data) return { ok: false, status: 502, errorCode: 'E_BACKEND' };
    const found = rl.data.roles.find(r => r.name === payload.role);
    if (!found || found.version !== payload.role_version) {
      return { ok: false, status: 401, errorCode: 'E_AUTH_EXPIRED' };
    }
    opts.cache.set(found);
    role = found;
  }

  if (!role[perm]) return { ok: false, status: 403, errorCode: 'E_PERM_DENIED' };
  return { ok: true, payload };
}
