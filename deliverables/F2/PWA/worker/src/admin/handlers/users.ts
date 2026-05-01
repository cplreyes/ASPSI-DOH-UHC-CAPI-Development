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
