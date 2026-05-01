/**
 * F2 Admin Portal — request dispatcher.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 1.14)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7)
 *
 * Returns null for non-/admin/api/ paths so index.ts can fall through to
 * the legacy router. All admin responses carry an X-Request-Id header
 * propagated end-to-end through Apps Script for cross-system trace.
 */
import type { Env } from '../types';
import {
  handleLogin,
  handleLogout,
  type AdminUserRow,
  type AdminRoleRow,
  type AuthAuditCtx,
} from './handlers/auth';
import {
  handleEncodeSubmit,
  type EncodeRequestBody,
  type EncodeSuccess,
} from './handlers/encode';
import {
  handleListResponses,
  handleGetResponseById,
  handleListAudit,
  handleListDlq,
  handleListHcws,
  handleSyncReport,
  handleMapReport,
  type ListFilters,
  type ListResponsesData,
  type ResponseRow,
  type AuditFilters,
  type ListAuditData,
  type DlqFilters,
  type ListDlqData,
  type HcwFilters,
  type ListHcwsData,
  type SyncReportFilters,
  type SyncReportData,
  type MapReportFilters,
  type MapReportData,
} from './handlers/data';
import {
  handleListUsers,
  handleListRoles,
  handleCreateUser,
  handleUpdateUser,
  handleDeleteUser,
  handleCreateRole,
  handleUpdateRole,
  handleDeleteRole,
  type UsersListFilters,
  type ListUsersData,
  type ListRolesData,
  type CreateUserBody,
  type UpdateUserBody,
  type UserRow,
  type RoleMutationBody,
  type RoleRow,
} from './handlers/users';
import { callAppsScript } from './apps-script-client';
import { RoleVersionCache, requirePerm, type Role, type RolesListResp, type RbacOpts } from './rbac';

/**
 * Module-level role cache shared across all RBAC-protected requests in
 * this Worker isolate. TTL is 60 minutes per the cache class default;
 * a role PATCH bumps F2_Roles.version which naturally invalidates stale
 * entries (key is `name:version`, see rbac.ts).
 */
const roleCache = new RoleVersionCache();

const ENCODE_RE = /^\/admin\/api\/encode\/([A-Za-z0-9_\-]+)\/?$/;
const RESPONSES_LIST_RE = /^\/admin\/api\/dashboards\/data\/responses\/?$/;
const RESPONSES_BY_ID_RE = /^\/admin\/api\/dashboards\/data\/responses\/([A-Za-z0-9_\-]+)\/?$/;
const AUDIT_LIST_RE = /^\/admin\/api\/dashboards\/data\/audit\/?$/;
const DLQ_LIST_RE = /^\/admin\/api\/dashboards\/data\/dlq\/?$/;
const HCWS_LIST_RE = /^\/admin\/api\/dashboards\/data\/hcws\/?$/;
const REPORT_SYNC_RE = /^\/admin\/api\/dashboards\/report\/sync\/?$/;
const REPORT_MAP_RE = /^\/admin\/api\/dashboards\/report\/map\/?$/;
const USERS_LIST_RE = /^\/admin\/api\/dashboards\/users\/?$/;
const USERS_BY_NAME_RE = /^\/admin\/api\/dashboards\/users\/([A-Za-z0-9_]{3,32})\/?$/;
const ROLES_LIST_RE = /^\/admin\/api\/dashboards\/roles\/?$/;
const ROLES_BY_NAME_RE = /^\/admin\/api\/dashboards\/roles\/([A-Za-z][A-Za-z0-9 _\-]{0,63})\/?$/;

/**
 * Build RbacOpts that's stable for one request. Most rbac-protected handlers
 * share the same cache/secret/kv triple; only the perm string varies.
 */
function buildRbacOpts(env: Env, requestId: string): RbacOpts {
  return {
    secret: env.JWT_SIGNING_KEY,
    cache: roleCache,
    kv: env.F2_AUTH,
    rolesListFn: () =>
      callAppsScript<{ roles: Role[] }>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_roles_list',
        {},
        requestId,
      ).then((r): RolesListResp =>
        r.ok && r.data ? { ok: true, data: { roles: r.data.roles } } : { ok: false },
      ),
  };
}

function rbacFailureResponse(status: number | undefined, errorCode: string | undefined): Response {
  return new Response(
    JSON.stringify({ ok: false, error: { code: errorCode, message: 'access denied' } }),
    { status: status ?? 401, headers: { 'Content-Type': 'application/json' } },
  );
}

const enc = new TextEncoder();

async function sha256Hex(s: string): Promise<string> {
  const buf = await crypto.subtle.digest('SHA-256', enc.encode(s));
  let hex = '';
  const view = new Uint8Array(buf);
  for (let i = 0; i < view.length; i++) hex += view[i]!.toString(16).padStart(2, '0');
  return hex;
}

function withRequestId(resp: Response, requestId: string): Response {
  const headers = new Headers(resp.headers);
  headers.set('X-Request-Id', requestId);
  return new Response(resp.body, { status: resp.status, statusText: resp.statusText, headers });
}

function notFound(requestId: string): Response {
  return new Response(
    JSON.stringify({ ok: false, error: { code: 'E_NOT_FOUND', message: 'route not found' } }),
    {
      status: 404,
      headers: { 'Content-Type': 'application/json', 'X-Request-Id': requestId },
    },
  );
}

/**
 * Build a fire-and-forget audit dispatcher. The handler invokes the returned
 * function synchronously on success (login / logout), but the actual AS RPC
 * runs via `ctx.waitUntil` so it cannot delay or fail the user response.
 * If `ctx` is unavailable (test environments without an ExecutionContext),
 * the function is a no-op, keeping handler unit tests independent of the
 * audit pipeline.
 */
function buildAuditDispatcher(
  env: Env,
  requestId: string,
  ctx?: ExecutionContext,
): (auditCtx: AuthAuditCtx) => void {
  return (auditCtx) => {
    if (!ctx) return;
    const payload = { ...auditCtx, request_id: requestId };
    ctx.waitUntil(
      callAppsScript(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_audit_write',
        payload,
        requestId,
      ).catch(() => undefined),
    );
  };
}

/**
 * Returns the response for an /admin/api/ request, or null when the path
 * isn't an admin-portal route (so the caller can fall through to legacy).
 *
 * `ctx` carries waitUntil for fire-and-forget audit writes (Task 1.18). If
 * absent, audit writes are silently skipped — handlers still succeed.
 */
export async function adminRouter(req: Request, env: Env, ctx?: ExecutionContext): Promise<Response | null> {
  const url = new URL(req.url);
  if (!url.pathname.startsWith('/admin/api/')) return null;

  const ipHash = await sha256Hex(req.headers.get('cf-connecting-ip') || '');
  const requestId = crypto.randomUUID();
  const auditFn = buildAuditDispatcher(env, requestId, ctx);

  if (req.method === 'POST' && url.pathname === '/admin/api/login') {
    const body = await req.json().catch(() => ({}));
    const usersList = () =>
      callAppsScript<{ users: AdminUserRow[] }>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_users_list',
        {},
        requestId,
      );
    const rolesList = () =>
      callAppsScript<{ roles: AdminRoleRow[] }>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_roles_list',
        {},
        requestId,
      );
    const r = await handleLogin(body as Record<string, unknown>, ipHash, env, usersList, rolesList, auditFn);
    return withRequestId(r, requestId);
  }

  if (req.method === 'POST' && url.pathname === '/admin/api/logout') {
    const r = await handleLogout(req, ipHash, env, auditFn);
    return withRequestId(r, requestId);
  }

  const encodeMatch = ENCODE_RE.exec(url.pathname);
  if (req.method === 'POST' && encodeMatch) {
    const hcwId = decodeURIComponent(encodeMatch[1]!);
    const auth = await requirePerm(req, 'dict_paper_encoded_up', buildRbacOpts(env, requestId));
    if (!auth.ok) {
      return withRequestId(rbacFailureResponse(auth.status, auth.errorCode), requestId);
    }
    const body = (await req.json().catch(() => ({}))) as EncodeRequestBody;
    const asCall = (payload: Record<string, unknown>) =>
      callAppsScript<EncodeSuccess>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_encode_submit',
        payload,
        requestId,
      );
    const r = await handleEncodeSubmit(
      hcwId,
      body,
      { username: auth.payload!.sub },
      asCall,
    );
    return withRequestId(r, requestId);
  }

  if (req.method === 'GET' && RESPONSES_LIST_RE.test(url.pathname)) {
    const auth = await requirePerm(req, 'dash_data', buildRbacOpts(env, requestId));
    if (!auth.ok) {
      return withRequestId(rbacFailureResponse(auth.status, auth.errorCode), requestId);
    }
    const asCall = (filters: ListFilters) =>
      callAppsScript<ListResponsesData>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_read_responses',
        filters as unknown as Record<string, unknown>,
        requestId,
      );
    const r = await handleListResponses(url, asCall);
    return withRequestId(r, requestId);
  }

  const responseByIdMatch = RESPONSES_BY_ID_RE.exec(url.pathname);
  if (req.method === 'GET' && responseByIdMatch) {
    const id = decodeURIComponent(responseByIdMatch[1]!);
    const auth = await requirePerm(req, 'dash_data', buildRbacOpts(env, requestId));
    if (!auth.ok) {
      return withRequestId(rbacFailureResponse(auth.status, auth.errorCode), requestId);
    }
    const asCall = (payload: { id: string }) =>
      callAppsScript<ResponseRow>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_read_response_by_id',
        payload,
        requestId,
      );
    const r = await handleGetResponseById(id, asCall);
    return withRequestId(r, requestId);
  }

  if (req.method === 'GET' && AUDIT_LIST_RE.test(url.pathname)) {
    const auth = await requirePerm(req, 'dash_data', buildRbacOpts(env, requestId));
    if (!auth.ok) {
      return withRequestId(rbacFailureResponse(auth.status, auth.errorCode), requestId);
    }
    const asCall = (filters: AuditFilters) =>
      callAppsScript<ListAuditData>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_read_audit',
        filters as unknown as Record<string, unknown>,
        requestId,
      );
    const r = await handleListAudit(url, asCall);
    return withRequestId(r, requestId);
  }

  if (req.method === 'GET' && DLQ_LIST_RE.test(url.pathname)) {
    const auth = await requirePerm(req, 'dash_data', buildRbacOpts(env, requestId));
    if (!auth.ok) {
      return withRequestId(rbacFailureResponse(auth.status, auth.errorCode), requestId);
    }
    const asCall = (filters: DlqFilters) =>
      callAppsScript<ListDlqData>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_read_dlq',
        filters as unknown as Record<string, unknown>,
        requestId,
      );
    const r = await handleListDlq(url, asCall);
    return withRequestId(r, requestId);
  }

  if (req.method === 'GET' && HCWS_LIST_RE.test(url.pathname)) {
    const auth = await requirePerm(req, 'dash_data', buildRbacOpts(env, requestId));
    if (!auth.ok) {
      return withRequestId(rbacFailureResponse(auth.status, auth.errorCode), requestId);
    }
    const asCall = (filters: HcwFilters) =>
      callAppsScript<ListHcwsData>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_hcws_list',
        filters as unknown as Record<string, unknown>,
        requestId,
      );
    const r = await handleListHcws(url, asCall);
    return withRequestId(r, requestId);
  }

  if (req.method === 'GET' && REPORT_SYNC_RE.test(url.pathname)) {
    const auth = await requirePerm(req, 'dash_report', buildRbacOpts(env, requestId));
    if (!auth.ok) {
      return withRequestId(rbacFailureResponse(auth.status, auth.errorCode), requestId);
    }
    const asCall = (filters: SyncReportFilters) =>
      callAppsScript<SyncReportData>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_sync_report',
        filters as unknown as Record<string, unknown>,
        requestId,
      );
    const r = await handleSyncReport(url, asCall);
    return withRequestId(r, requestId);
  }

  if (req.method === 'GET' && REPORT_MAP_RE.test(url.pathname)) {
    const auth = await requirePerm(req, 'dash_report', buildRbacOpts(env, requestId));
    if (!auth.ok) {
      return withRequestId(rbacFailureResponse(auth.status, auth.errorCode), requestId);
    }
    const asCall = (filters: MapReportFilters) =>
      callAppsScript<MapReportData>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_map_report',
        filters as unknown as Record<string, unknown>,
        requestId,
      );
    const r = await handleMapReport(url, asCall);
    return withRequestId(r, requestId);
  }

  if (req.method === 'GET' && USERS_LIST_RE.test(url.pathname)) {
    const auth = await requirePerm(req, 'dash_users', buildRbacOpts(env, requestId));
    if (!auth.ok) {
      return withRequestId(rbacFailureResponse(auth.status, auth.errorCode), requestId);
    }
    const asCall = (filters: UsersListFilters) =>
      callAppsScript<ListUsersData>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_users_list',
        filters as unknown as Record<string, unknown>,
        requestId,
      );
    const r = await handleListUsers(url, asCall);
    return withRequestId(r, requestId);
  }

  if (req.method === 'POST' && USERS_LIST_RE.test(url.pathname)) {
    const auth = await requirePerm(req, 'dash_users', buildRbacOpts(env, requestId));
    if (!auth.ok) {
      return withRequestId(rbacFailureResponse(auth.status, auth.errorCode), requestId);
    }
    const body = (await req.json().catch(() => ({}))) as CreateUserBody;
    const asCall = (payload: Record<string, unknown>) =>
      callAppsScript<{ user: UserRow }>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_users_create',
        payload,
        requestId,
      );
    const r = await handleCreateUser(body, { username: auth.payload!.sub }, asCall);
    return withRequestId(r, requestId);
  }

  const userByNameMatch = USERS_BY_NAME_RE.exec(url.pathname);
  if (userByNameMatch && (req.method === 'PATCH' || req.method === 'DELETE')) {
    const auth = await requirePerm(req, 'dash_users', buildRbacOpts(env, requestId));
    if (!auth.ok) {
      return withRequestId(rbacFailureResponse(auth.status, auth.errorCode), requestId);
    }
    const username = userByNameMatch[1]!;
    if (req.method === 'PATCH') {
      const body = (await req.json().catch(() => ({}))) as UpdateUserBody;
      const asCall = (payload: Record<string, unknown>) =>
        callAppsScript<{ user: UserRow }>(
          env.APPS_SCRIPT_URL,
          env.APPS_SCRIPT_HMAC,
          'admin_users_update',
          payload,
          requestId,
        );
      const r = await handleUpdateUser(username, body, asCall);
      return withRequestId(r, requestId);
    }
    // DELETE
    const asCall = (payload: { username: string }) =>
      callAppsScript<{ username: string }>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_users_delete',
        payload,
        requestId,
      );
    const r = await handleDeleteUser(username, asCall);
    return withRequestId(r, requestId);
  }

  if (req.method === 'GET' && ROLES_LIST_RE.test(url.pathname)) {
    const auth = await requirePerm(req, 'dash_roles', buildRbacOpts(env, requestId));
    if (!auth.ok) {
      return withRequestId(rbacFailureResponse(auth.status, auth.errorCode), requestId);
    }
    const asCall = () =>
      callAppsScript<ListRolesData>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_roles_list',
        {},
        requestId,
      );
    const r = await handleListRoles(asCall);
    return withRequestId(r, requestId);
  }

  if (req.method === 'POST' && ROLES_LIST_RE.test(url.pathname)) {
    const auth = await requirePerm(req, 'dash_roles', buildRbacOpts(env, requestId));
    if (!auth.ok) {
      return withRequestId(rbacFailureResponse(auth.status, auth.errorCode), requestId);
    }
    const body = (await req.json().catch(() => ({}))) as RoleMutationBody;
    const asCall = (payload: Record<string, unknown>) =>
      callAppsScript<{ role: RoleRow }>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_roles_create',
        payload,
        requestId,
      );
    const r = await handleCreateRole(body, { username: auth.payload!.sub }, asCall);
    return withRequestId(r, requestId);
  }

  const roleByNameMatch = ROLES_BY_NAME_RE.exec(url.pathname);
  if (roleByNameMatch && (req.method === 'PATCH' || req.method === 'DELETE')) {
    const auth = await requirePerm(req, 'dash_roles', buildRbacOpts(env, requestId));
    if (!auth.ok) {
      return withRequestId(rbacFailureResponse(auth.status, auth.errorCode), requestId);
    }
    const name = decodeURIComponent(roleByNameMatch[1]!);
    if (req.method === 'PATCH') {
      const body = (await req.json().catch(() => ({}))) as RoleMutationBody;
      const asCall = (payload: Record<string, unknown>) =>
        callAppsScript<{ role: RoleRow; changed: boolean }>(
          env.APPS_SCRIPT_URL,
          env.APPS_SCRIPT_HMAC,
          'admin_roles_update',
          payload,
          requestId,
        );
      const r = await handleUpdateRole(name, body, asCall);
      return withRequestId(r, requestId);
    }
    // DELETE
    const asCall = (payload: { name: string }) =>
      callAppsScript<{ name: string }>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_roles_delete',
        payload,
        requestId,
      );
    const r = await handleDeleteRole(name, asCall);
    return withRequestId(r, requestId);
  }

  return notFound(requestId);
}
