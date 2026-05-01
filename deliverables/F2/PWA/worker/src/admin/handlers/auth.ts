/**
 * F2 Admin Portal — login handler.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 1.11)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.1, §10)
 *
 * Flow:
 *   1. Pre-check two-axis throttle. If exceeded → 429 E_AUTH_LOCKED + Retry-After.
 *   2. Fetch users via admin_users_list. Apps Script failure → 502 E_BACKEND.
 *   3. Find user; missing → 401 E_AUTH_INVALID (no counter increment — username
 *      enumeration is not a concern; throttle exists primarily to slow online
 *      brute force on a known-good account, and bumping for unknown users
 *      lets an attacker DoS legitimate users by spamming usernames).
 *   4. PBKDF2 verify; on fail → record on BOTH counters + 401 E_AUTH_INVALID.
 *   5. Fetch roles, find user.role; missing → 502 (data integrity, not auth).
 *   6. Mint admin JWT; reset per-user throttle (per-IP intentionally preserved).
 *   7. Return 200 with `{ token, role, role_version, expires_at, password_must_change }`.
 */
import type { Env } from '../../types';
import { jsonResponse } from '../../types';
import { mintAdminJwt, verifyAdminJwt, verifyPassword, type AdminJwtPayload } from '../auth';
import {
  checkLoginThrottle,
  recordFailedLogin,
  resetLoginThrottle,
  type ThrottleKv,
} from '../throttle';
import type { AppsScriptResponse } from '../apps-script-client';

const WINDOW_SECONDS = 15 * 60;
const JWT_TTL_SECONDS = 4 * 60 * 60;

export interface AdminUserRow {
  username: string;
  password_hash: string;
  password_must_change: boolean | string | number;
  role: string;
  active?: boolean | string;
}

export interface AdminRoleRow {
  name: string;
  version: number;
  [perm: string]: unknown;
}

export type UsersListFn = () => Promise<AppsScriptResponse<{ users: AdminUserRow[] }>>;
export type RolesListFn = () => Promise<AppsScriptResponse<{ roles: AdminRoleRow[] }>>;

interface LoginBody {
  username?: unknown;
  password?: unknown;
}

interface LoginSuccess {
  token: string;
  role: string;
  role_version: number;
  expires_at: number;
  password_must_change: boolean;
}

function errorJson(code: string, message: string, status: number, headers: Record<string, string> = {}): Response {
  return jsonResponse({ ok: false, error: { code, message } }, status, headers);
}

function retryAfterSeconds(): number {
  const now = Math.floor(Date.now() / 1000);
  const winStart = Math.floor(now / WINDOW_SECONDS) * WINDOW_SECONDS;
  return Math.max(1, winStart + WINDOW_SECONDS - now);
}

function isTruthy(v: unknown): boolean {
  if (typeof v === 'boolean') return v;
  if (typeof v === 'number') return v !== 0;
  if (typeof v === 'string') {
    const s = v.trim().toLowerCase();
    return s === 'true' || s === '1' || s === 'yes';
  }
  return false;
}

export async function handleLogin(
  body: LoginBody,
  ipHash: string,
  env: Pick<Env, 'JWT_SIGNING_KEY' | 'F2_AUTH'>,
  usersListFn: UsersListFn,
  rolesListFn: RolesListFn,
): Promise<Response> {
  const username = typeof body.username === 'string' ? body.username.trim() : '';
  const password = typeof body.password === 'string' ? body.password : '';
  if (!username || !password) {
    return errorJson('E_VALIDATION', 'username and password are required', 400);
  }

  const kv = env.F2_AUTH as unknown as ThrottleKv;

  const pre = await checkLoginThrottle(kv, username, ipHash);
  if (!pre.allowed) {
    const ra = retryAfterSeconds();
    return errorJson(
      'E_AUTH_LOCKED',
      `Too many login attempts. Try again in ${ra}s.`,
      429,
      { 'Retry-After': String(ra) },
    );
  }

  const usersResp = await usersListFn();
  if (!usersResp.ok || !usersResp.data) {
    return errorJson(
      'E_BACKEND',
      usersResp.error?.message || 'Apps Script unavailable',
      502,
    );
  }

  const user = usersResp.data.users.find(u => u.username === username);
  if (!user) {
    return errorJson('E_AUTH_INVALID', 'Invalid username or password', 401);
  }

  const ok = await verifyPassword(password, user.password_hash);
  if (!ok) {
    await recordFailedLogin(kv, username, ipHash);
    return errorJson('E_AUTH_INVALID', 'Invalid username or password', 401);
  }

  const rolesResp = await rolesListFn();
  if (!rolesResp.ok || !rolesResp.data) {
    return errorJson(
      'E_BACKEND',
      rolesResp.error?.message || 'Apps Script unavailable',
      502,
    );
  }

  const role = rolesResp.data.roles.find(r => r.name === user.role);
  if (!role) {
    return errorJson(
      'E_BACKEND',
      `Role "${user.role}" not found for user "${username}"`,
      502,
    );
  }

  const claims: Pick<AdminJwtPayload, 'sub' | 'role' | 'role_version'> = {
    sub: username,
    role: role.name,
    role_version: role.version,
  };
  const token = await mintAdminJwt(env.JWT_SIGNING_KEY, claims, { ttl: JWT_TTL_SECONDS });

  await resetLoginThrottle(kv, username);

  const expiresAt = Math.floor(Date.now() / 1000) + JWT_TTL_SECONDS;
  const success: LoginSuccess = {
    token,
    role: role.name,
    role_version: role.version,
    expires_at: expiresAt,
    password_must_change: isTruthy(user.password_must_change),
  };
  return jsonResponse(success, 200);
}

const BEARER_RE = /^Bearer (.+)$/;

export interface LogoutKv {
  put(key: string, value: string, opts?: { expirationTtl?: number }): Promise<void>;
}

/**
 * Revoke the bearer token by recording its jti in KV with a TTL that
 * outlives the JWT's own exp by 60 seconds (clock-skew buffer). The
 * RBAC middleware checks `revoked_jti:<jti>` on every request, so any
 * cached/copied token stops working immediately.
 *
 * Expired/invalid tokens get 401 — there's nothing meaningful to revoke
 * and the caller should clear their local state via the login redirect
 * the 401 already triggers.
 */
export async function handleLogout(
  req: Request,
  env: Pick<Env, 'JWT_SIGNING_KEY' | 'F2_AUTH'>,
): Promise<Response> {
  const auth = req.headers.get('Authorization') || '';
  const m = BEARER_RE.exec(auth);
  if (!m) return errorJson('E_AUTH_INVALID', 'Authorization header missing or malformed', 401);

  const v = await verifyAdminJwt(env.JWT_SIGNING_KEY, m[1]!);
  if (!v.ok) {
    const code = v.error === 'expired' ? 'E_AUTH_EXPIRED' : 'E_AUTH_INVALID';
    return errorJson(code, 'Token invalid or expired', 401);
  }

  const now = Math.floor(Date.now() / 1000);
  const ttl = Math.max(60, v.payload.exp - now + 60);
  const kv = env.F2_AUTH as unknown as LogoutKv;
  await kv.put(`revoked_jti:${v.payload.jti}`, '1', { expirationTtl: ttl });

  return new Response(null, { status: 204 });
}
