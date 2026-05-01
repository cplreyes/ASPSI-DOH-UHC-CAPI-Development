/**
 * F2 Admin Portal — Users + Roles read handlers.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Tasks 3.14, 3.23)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.10–7.12)
 *
 * Read-only listings; mutations land in follow-up commits with their
 * AS counterparts (admin_users_create / update / delete / bulk_create
 * / revoke_sessions and admin_roles_create / update / delete).
 */
import { jsonResponse } from '../../types';
import { hashPassword } from '../auth';
import type { AppsScriptResponse } from '../apps-script-client';

export interface UserRow {
  username: string;
  first_name: string;
  last_name: string;
  role_name: string;
  email?: string;
  phone?: string;
  password_must_change?: boolean | string;
  has_password?: boolean;
  created_at?: string;
  created_by?: string;
  last_login_at?: string;
}

export interface ListUsersData {
  users: UserRow[];
  total: number;
}

export interface UsersListFilters {
  role_name?: string;
  username?: string;
  q?: string;
}

export type UsersListAsCallable = (filters: UsersListFilters) => Promise<AppsScriptResponse<ListUsersData>>;

export interface RoleRow {
  name: string;
  is_builtin?: boolean | string;
  version: number;
  created_at?: string;
  created_by?: string;
  [perm: string]: unknown;
}

export interface ListRolesData {
  roles: RoleRow[];
  total: number;
}

export type RolesListAsCallable = () => Promise<AppsScriptResponse<ListRolesData>>;

function errorJson(code: string, message: string, status: number): Response {
  return jsonResponse({ ok: false, error: { code, message } }, status);
}

function parseUsersFilters(params: URLSearchParams): UsersListFilters {
  const out: UsersListFilters = {};
  const role = params.get('role_name');
  const u = params.get('username');
  const q = params.get('q');
  if (role) out.role_name = role;
  if (u) out.username = u;
  if (q) out.q = q;
  return out;
}

export async function handleListUsers(
  url: URL,
  asCallable: UsersListAsCallable,
): Promise<Response> {
  const filters = parseUsersFilters(url.searchParams);
  const r = await asCallable(filters);
  if (!r.ok || !r.data) {
    return errorJson(
      r.error?.code ?? 'E_BACKEND',
      r.error?.message ?? 'Apps Script unavailable',
      502,
    );
  }
  return jsonResponse(r.data, 200);
}

export async function handleListRoles(asCallable: RolesListAsCallable): Promise<Response> {
  const r = await asCallable();
  if (!r.ok || !r.data) {
    return errorJson(
      r.error?.code ?? 'E_BACKEND',
      r.error?.message ?? 'Apps Script unavailable',
      502,
    );
  }
  return jsonResponse(r.data, 200);
}

// ----- Mutations (Tasks 3.11, 3.14) ---------------------------------------

const USERNAME_RE = /^[A-Za-z0-9_]{3,32}$/;

export interface CreateUserBody {
  username?: unknown;
  password?: unknown;
  first_name?: unknown;
  last_name?: unknown;
  role_name?: unknown;
  email?: unknown;
  phone?: unknown;
}

export interface UpdateUserBody {
  first_name?: unknown;
  last_name?: unknown;
  role_name?: unknown;
  email?: unknown;
  phone?: unknown;
  password?: unknown;            // optional reset
  password_must_change?: unknown; // optional toggle
}

export type CreateUserAsCallable = (
  payload: Record<string, unknown>,
) => Promise<AppsScriptResponse<{ user: UserRow }>>;

export type UpdateUserAsCallable = (
  payload: Record<string, unknown>,
) => Promise<AppsScriptResponse<{ user: UserRow }>>;

export type DeleteUserAsCallable = (
  payload: { username: string },
) => Promise<AppsScriptResponse<{ username: string }>>;

function statusForAsError(code: string | undefined): number {
  if (code === 'E_VALIDATION') return 400;
  if (code === 'E_NOT_FOUND') return 404;
  if (code === 'E_CONFLICT') return 409;
  if (code === 'E_LOCK_TIMEOUT') return 503;
  return 502;
}

export async function handleCreateUser(
  body: CreateUserBody,
  actor: { username: string },
  asCallable: CreateUserAsCallable,
): Promise<Response> {
  const u = typeof body.username === 'string' ? body.username.trim() : '';
  const password = typeof body.password === 'string' ? body.password : '';
  const role = typeof body.role_name === 'string' ? body.role_name.trim() : '';
  if (!USERNAME_RE.test(u)) {
    return errorJson('E_VALIDATION', 'username must be 3-32 chars [A-Za-z0-9_]', 400);
  }
  if (password.length < 8) {
    return errorJson('E_VALIDATION', 'password must be at least 8 characters', 400);
  }
  if (!role) {
    return errorJson('E_VALIDATION', 'role_name required', 400);
  }

  const password_hash = await hashPassword(password);
  const r = await asCallable({
    username: u,
    password_hash,
    role_name: role,
    first_name: typeof body.first_name === 'string' ? body.first_name.trim() : '',
    last_name: typeof body.last_name === 'string' ? body.last_name.trim() : '',
    email: typeof body.email === 'string' ? body.email.trim() : '',
    phone: typeof body.phone === 'string' ? body.phone.trim() : '',
    password_must_change: true,
    created_by: actor.username,
  });
  if (!r.ok || !r.data) {
    return errorJson(
      r.error?.code ?? 'E_BACKEND',
      r.error?.message ?? 'Apps Script unavailable',
      statusForAsError(r.error?.code),
    );
  }
  return jsonResponse(r.data, 200);
}

export async function handleUpdateUser(
  username: string,
  body: UpdateUserBody,
  asCallable: UpdateUserAsCallable,
): Promise<Response> {
  if (!USERNAME_RE.test(username)) {
    return errorJson('E_VALIDATION', 'invalid username path param', 400);
  }
  const payload: Record<string, unknown> = { username };
  if (typeof body.first_name === 'string') payload.first_name = body.first_name.trim();
  if (typeof body.last_name === 'string') payload.last_name = body.last_name.trim();
  if (typeof body.role_name === 'string') payload.role_name = body.role_name.trim();
  if (typeof body.email === 'string') payload.email = body.email.trim();
  if (typeof body.phone === 'string') payload.phone = body.phone.trim();
  if (typeof body.password_must_change === 'boolean') payload.password_must_change = body.password_must_change;
  if (typeof body.password === 'string' && body.password.length > 0) {
    if (body.password.length < 8) {
      return errorJson('E_VALIDATION', 'password must be at least 8 characters', 400);
    }
    payload.password_hash = await hashPassword(body.password);
    // Admin-initiated password reset forces the user to change it on next login.
    payload.password_must_change = true;
  }

  const r = await asCallable(payload);
  if (!r.ok || !r.data) {
    return errorJson(
      r.error?.code ?? 'E_BACKEND',
      r.error?.message ?? 'Apps Script unavailable',
      statusForAsError(r.error?.code),
    );
  }
  return jsonResponse(r.data, 200);
}

export async function handleDeleteUser(
  username: string,
  asCallable: DeleteUserAsCallable,
): Promise<Response> {
  if (!USERNAME_RE.test(username)) {
    return errorJson('E_VALIDATION', 'invalid username path param', 400);
  }
  const r = await asCallable({ username });
  if (!r.ok) {
    return errorJson(
      r.error?.code ?? 'E_BACKEND',
      r.error?.message ?? 'Apps Script unavailable',
      statusForAsError(r.error?.code),
    );
  }
  return new Response(null, { status: 204 });
}

// ----- Revoke sessions (Tasks 3.13, 3.16, 3.17) ---------------------------

export interface RevokeKv {
  put(key: string, value: string, opts?: { expirationTtl?: number }): Promise<void>;
}

/**
 * Force-logout every JWT held by `username`. Writes
 * `revoked_user:<username>` to KV with the current Unix timestamp; rbac
 * compares against JWT.iat so any token minted BEFORE the revocation
 * fails authentication on its next request. Tokens minted AFTER (e.g.
 * the user re-logs in following an admin-initiated password reset)
 * pass through normally.
 *
 * TTL: 24h. Long enough to cover the JWT TTL (4h per spec §6.3) plus
 * a generous buffer for clock skew, while still letting KV reclaim the
 * key automatically. If a longer lockout is needed, admin re-revokes.
 */
export async function handleRevokeSessions(
  username: string,
  kv: RevokeKv,
): Promise<Response> {
  if (!USERNAME_RE.test(username)) {
    return errorJson('E_VALIDATION', 'invalid username path param', 400);
  }
  const nowSec = Math.floor(Date.now() / 1000);
  await kv.put(`revoked_user:${username}`, String(nowSec), { expirationTtl: 24 * 3600 });
  return new Response(null, { status: 204 });
}

// ----- Roles mutations (Tasks 3.21, 3.22, 3.23) ---------------------------

const ROLE_NAME_RE = /^[A-Za-z][A-Za-z0-9 _-]{0,63}$/;

export interface RoleMutationBody {
  name?: unknown;
  dash_data?: unknown;
  dash_report?: unknown;
  dash_apps?: unknown;
  dash_users?: unknown;
  dash_roles?: unknown;
  dict_self_admin_up?: unknown;
  dict_self_admin_down?: unknown;
  dict_paper_encoded_up?: unknown;
  dict_paper_encoded_down?: unknown;
  dict_capi_up?: unknown;
  dict_capi_down?: unknown;
}

export type CreateRoleAsCallable = (
  payload: Record<string, unknown>,
) => Promise<AppsScriptResponse<{ role: RoleRow }>>;

export type UpdateRoleAsCallable = (
  payload: Record<string, unknown>,
) => Promise<AppsScriptResponse<{ role: RoleRow; changed: boolean }>>;

export type DeleteRoleAsCallable = (
  payload: { name: string },
) => Promise<AppsScriptResponse<{ name: string }>>;

const PERM_KEYS = [
  'dash_data', 'dash_report', 'dash_apps', 'dash_users', 'dash_roles',
  'dict_self_admin_up', 'dict_self_admin_down',
  'dict_paper_encoded_up', 'dict_paper_encoded_down',
  'dict_capi_up', 'dict_capi_down',
] as const;

function buildRolePayload(body: RoleMutationBody): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const k of PERM_KEYS) {
    const v = (body as Record<string, unknown>)[k];
    if (typeof v === 'boolean') out[k] = v;
  }
  return out;
}

export async function handleCreateRole(
  body: RoleMutationBody,
  actor: { username: string },
  asCallable: CreateRoleAsCallable,
): Promise<Response> {
  const name = typeof body.name === 'string' ? body.name.trim() : '';
  if (!ROLE_NAME_RE.test(name)) {
    return errorJson(
      'E_VALIDATION',
      'role name must start with a letter; up to 64 chars [A-Za-z0-9 _-]',
      400,
    );
  }
  const payload = { name, ...buildRolePayload(body), created_by: actor.username };
  const r = await asCallable(payload);
  if (!r.ok || !r.data) {
    return errorJson(
      r.error?.code ?? 'E_BACKEND',
      r.error?.message ?? 'Apps Script unavailable',
      statusForAsError(r.error?.code),
    );
  }
  return jsonResponse(r.data, 200);
}

export async function handleUpdateRole(
  name: string,
  body: RoleMutationBody,
  asCallable: UpdateRoleAsCallable,
): Promise<Response> {
  if (!ROLE_NAME_RE.test(name)) {
    return errorJson('E_VALIDATION', 'invalid role name path param', 400);
  }
  const payload = { name, ...buildRolePayload(body) };
  const r = await asCallable(payload);
  if (!r.ok || !r.data) {
    return errorJson(
      r.error?.code ?? 'E_BACKEND',
      r.error?.message ?? 'Apps Script unavailable',
      statusForAsError(r.error?.code),
    );
  }
  return jsonResponse(r.data, 200);
}

export async function handleDeleteRole(
  name: string,
  asCallable: DeleteRoleAsCallable,
): Promise<Response> {
  if (!ROLE_NAME_RE.test(name)) {
    return errorJson('E_VALIDATION', 'invalid role name path param', 400);
  }
  const r = await asCallable({ name });
  if (!r.ok) {
    return errorJson(
      r.error?.code ?? 'E_BACKEND',
      r.error?.message ?? 'Apps Script unavailable',
      statusForAsError(r.error?.code),
    );
  }
  return new Response(null, { status: 204 });
}
