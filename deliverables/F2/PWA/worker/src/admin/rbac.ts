/**
 * F2 Admin Portal — RBAC middleware + role perm cache.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 1.12)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§6.4, §10)
 *
 * Cache invariant: holds at most one entry per role name (the latest version
 * the worker has seen). Two layers of staleness defense:
 *
 * 1. Active eviction — every successful role mutation (POST/PATCH/DELETE on
 *    `/admin/api/dashboards/roles/...`) invalidates the entry for that name
 *    in routes.ts, so the next request for any user holding that role
 *    refetches authoritative data from F2_Roles.
 * 2. Per-request version validation — on every cache hit, requirePerm
 *    compares the cached role's version to the JWT's `role_version`. A JWT
 *    minted before a version bump (with `role_version=v1`) is rejected
 *    against a cached v2 entry with E_AUTH_EXPIRED, even if the active-
 *    eviction step somehow missed.
 * 3. TTL backstop — entries older than `TTL_MS` (5 min) are treated as
 *    expired regardless. Bounds worst-case staleness when neither active
 *    eviction nor a fresh-token request has happened recently.
 *
 * R2-#56 (E4-APRT-044): the prior shape keyed entries on `name:version`,
 * which meant a v1 JWT lookup hit the v1 cache entry directly without
 * triggering the version-mismatch detection — revoked perms persisted up
 * to 60 minutes. Reshaped to key-by-name + explicit version validation +
 * shorter TTL.
 */
import { verifyAdminJwt, type AdminJwtPayload } from './auth';

export interface Role {
  name: string;
  version: number;
  [perm: string]: unknown;
}

export class RoleVersionCache {
  private cache = new Map<string, { role: Role; cachedAt: number }>();
  private TTL_MS = 5 * 60 * 1000;

  /**
   * Returns the latest cached role for `name`, or undefined when absent or
   * past TTL. Caller is responsible for verifying the cached `role.version`
   * against the JWT's `role_version` — the cache itself never compares
   * versions, since that comparison is the security gate.
   */
  get(name: string): Role | undefined {
    const e = this.cache.get(name);
    if (!e) return undefined;
    if (Date.now() - e.cachedAt > this.TTL_MS) return undefined;
    return e.role;
  }

  /**
   * Overwrites the entry for `role.name` with the given role. Latest write
   * wins — version is stored on the entry but not in the key.
   */
  set(role: Role): void {
    this.cache.set(role.name, { role, cachedAt: Date.now() });
  }

  /**
   * Active eviction. Called by routes.ts after a successful role mutation
   * so the next request for any user holding `name` refetches authoritative
   * data from F2_Roles. Idempotent — no-op when the entry is absent.
   */
  invalidate(name: string): void {
    this.cache.delete(name);
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

  // R2-#57 (E4-APRT-045): a token issued to a user who owes a password
  // change is barred from every RBAC-gated route. The password-rotation
  // endpoint (`PATCH /admin/api/me/password`) bypasses this gate by design
  // — it does its own JWT verify and never calls requirePerm. Frontend
  // intercepts E_PASSWORD_CHANGE_REQUIRED on the api-client side and
  // redirects to /admin/me/change-password.
  if (payload.pwc === true) {
    return { ok: false, status: 403, errorCode: 'E_PASSWORD_CHANGE_REQUIRED' };
  }

  // R2-#56 (E4-APRT-044): per-request version validation. Cache hit only
  // when the cached version exactly matches the JWT — a stale JWT (lower
  // version than cache) gets caught here without an AS round-trip; a stale
  // cache (higher JWT version than cache) falls through to refetch. The
  // refetch path also catches the case where active-eviction missed (cache
  // and JWT both stale together): authoritative AS data wins, mismatch
  // rejected.
  const cached = opts.cache.get(payload.role);
  let role: Role | undefined;
  if (cached && cached.version === payload.role_version) {
    role = cached;
  } else {
    const rl = await opts.rolesListFn();
    if (!rl.ok || !rl.data) return { ok: false, status: 502, errorCode: 'E_BACKEND' };
    const found = rl.data.roles.find(r => r.name === payload.role);
    if (!found) {
      return { ok: false, status: 401, errorCode: 'E_AUTH_EXPIRED' };
    }
    // Always update the cache with the authoritative latest, even when the
    // JWT turns out to be stale — the next caller benefits from a fresh
    // entry instead of repeating the same AS round-trip.
    opts.cache.set(found);
    if (found.version !== payload.role_version) {
      return { ok: false, status: 401, errorCode: 'E_AUTH_EXPIRED' };
    }
    role = found;
  }

  if (!role[perm]) return { ok: false, status: 403, errorCode: 'E_PERM_DENIED' };
  return { ok: true, payload };
}
