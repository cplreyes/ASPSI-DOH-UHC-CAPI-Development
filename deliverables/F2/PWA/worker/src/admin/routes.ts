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
  handleVersion,
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
  type FormRevisionsData,
} from './handlers/data';
import {
  handleReissueToken,
  type ReissueRequestBody,
} from './handlers/hcws';
import {
  handleListUsers,
  handleListRoles,
  handleCreateUser,
  handleUpdateUser,
  handleDeleteUser,
  handleRevokeSessions,
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
import {
  handleListFiles,
  handleUploadFile,
  handleDownloadFile,
  handleDeleteFile,
  handleListSettings,
  handleCreateSetting,
  handleUpdateSetting,
  handleDeleteSetting,
  handleRunNowSetting,
  handleGetQuota,
  type FileMetaRow,
  type FilesListFilters,
  type ListFilesData,
  type ListSettingsData,
  type SettingRow,
  type SettingMutationBody,
} from './handlers/apps';
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
const HCWS_REISSUE_RE = /^\/admin\/api\/hcws\/([A-Za-z0-9_\-]+)\/reissue-token\/?$/;
const REPORT_SYNC_RE = /^\/admin\/api\/dashboards\/report\/sync\/?$/;
const REPORT_MAP_RE = /^\/admin\/api\/dashboards\/report\/map\/?$/;
const APPS_VERSION_RE = /^\/admin\/api\/dashboards\/apps\/version\/?$/;
const USERS_LIST_RE = /^\/admin\/api\/dashboards\/users\/?$/;
const USERS_BY_NAME_RE = /^\/admin\/api\/dashboards\/users\/([A-Za-z0-9_]{3,32})\/?$/;
const USERS_REVOKE_RE = /^\/admin\/api\/dashboards\/users\/([A-Za-z0-9_]{3,32})\/revoke-sessions\/?$/;
const ROLES_LIST_RE = /^\/admin\/api\/dashboards\/roles\/?$/;
const ROLES_BY_NAME_RE = /^\/admin\/api\/dashboards\/roles\/([A-Za-z][A-Za-z0-9 _\-]{0,63})\/?$/;
const FILES_LIST_RE = /^\/admin\/api\/dashboards\/apps\/files\/?$/;
const FILES_BY_ID_RE = /^\/admin\/api\/dashboards\/apps\/files\/([A-Za-z0-9_\-]+)\/?$/;
const SETTINGS_LIST_RE = /^\/admin\/api\/dashboards\/apps\/data-settings\/?$/;
const SETTINGS_BY_ID_RE = /^\/admin\/api\/dashboards\/apps\/data-settings\/([A-Za-z0-9_\-]+)\/?$/;
const SETTINGS_RUN_NOW_RE = /^\/admin\/api\/dashboards\/apps\/data-settings\/([A-Za-z0-9_\-]+)\/run-now\/?$/;
const APPS_QUOTA_RE = /^\/admin\/api\/dashboards\/apps\/quota\/?$/;

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
        env.F2_AUTH,
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
        env.F2_AUTH,
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
    const loginUsername = typeof (body as { username?: unknown }).username === 'string'
      ? (body as { username: string }).username.trim()
      : '';
    const usersList = () =>
      callAppsScript<{ users: AdminUserRow[] }>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_users_list',
        // include_password_hash is HMAC-gated at the AS dispatcher; only the
        // worker (sole HMAC holder) can ask for the hash. Filter by username
        // so we don't transfer the whole user table over the wire on each
        // login attempt.
        { include_password_hash: true, username: loginUsername },
        requestId,
        env.F2_AUTH,
      );
    const rolesList = () =>
      callAppsScript<{ roles: AdminRoleRow[] }>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_roles_list',
        {},
        requestId,
        env.F2_AUTH,
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
        env.F2_AUTH,
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
        env.F2_AUTH,
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
        env.F2_AUTH,
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
        env.F2_AUTH,
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
        env.F2_AUTH,
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
        env.F2_AUTH,
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
        env.F2_AUTH,
      );
    const r = await handleSyncReport(url, asCall);
    return withRequestId(r, requestId);
  }

  if (req.method === 'GET' && FILES_LIST_RE.test(url.pathname)) {
    const auth = await requirePerm(req, 'dash_apps', buildRbacOpts(env, requestId));
    if (!auth.ok) {
      return withRequestId(rbacFailureResponse(auth.status, auth.errorCode), requestId);
    }
    const asCall = (filters: FilesListFilters) =>
      callAppsScript<ListFilesData>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_files_list',
        filters as unknown as Record<string, unknown>,
        requestId,
        env.F2_AUTH,
      );
    const r = await handleListFiles(url, asCall);
    return withRequestId(r, requestId);
  }

  if (req.method === 'POST' && FILES_LIST_RE.test(url.pathname)) {
    const auth = await requirePerm(req, 'dash_apps', buildRbacOpts(env, requestId));
    if (!auth.ok) {
      return withRequestId(rbacFailureResponse(auth.status, auth.errorCode), requestId);
    }
    const asCall = (payload: Record<string, unknown>) =>
      callAppsScript<{ file: FileMetaRow }>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_files_create',
        payload,
        requestId,
        env.F2_AUTH,
      );
    const r = await handleUploadFile(req, { username: auth.payload!.sub }, env.F2_ADMIN_R2, asCall);
    return withRequestId(r, requestId);
  }

  const fileByIdMatch = FILES_BY_ID_RE.exec(url.pathname);
  if (fileByIdMatch && (req.method === 'GET' || req.method === 'DELETE')) {
    const auth = await requirePerm(req, 'dash_apps', buildRbacOpts(env, requestId));
    if (!auth.ok) {
      return withRequestId(rbacFailureResponse(auth.status, auth.errorCode), requestId);
    }
    const fileId = decodeURIComponent(fileByIdMatch[1]!);
    if (req.method === 'GET') {
      const asCall = (payload: { file_id: string }) =>
        callAppsScript<{ file: FileMetaRow }>(
          env.APPS_SCRIPT_URL,
          env.APPS_SCRIPT_HMAC,
          'admin_files_get',
          payload,
          requestId,
          env.F2_AUTH,
        );
      const r = await handleDownloadFile(fileId, env.F2_ADMIN_R2, asCall);
      return withRequestId(r, requestId);
    }
    const asCall = (payload: { file_id: string }) =>
      callAppsScript<{ file_id: string; deleted_at: string }>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_files_delete',
        payload,
        requestId,
        env.F2_AUTH,
      );
    const r = await handleDeleteFile(fileId, env.F2_ADMIN_R2, asCall);
    return withRequestId(r, requestId);
  }

  if (req.method === 'GET' && APPS_QUOTA_RE.test(url.pathname)) {
    const auth = await requirePerm(req, 'dash_apps', buildRbacOpts(env, requestId));
    if (!auth.ok) {
      return withRequestId(rbacFailureResponse(auth.status, auth.errorCode), requestId);
    }
    const r = await handleGetQuota(env.F2_AUTH);
    return withRequestId(r, requestId);
  }

  // Run-now must come before generic by-id so the path is matched
  // specifically. Path: /admin/api/dashboards/apps/data-settings/:id/run-now
  const runNowMatch = SETTINGS_RUN_NOW_RE.exec(url.pathname);
  if (req.method === 'POST' && runNowMatch) {
    const auth = await requirePerm(req, 'dash_apps', buildRbacOpts(env, requestId));
    if (!auth.ok) {
      return withRequestId(rbacFailureResponse(auth.status, auth.errorCode), requestId);
    }
    const sid = decodeURIComponent(runNowMatch[1]!);
    const asCall = (payload: Record<string, unknown>) =>
      callAppsScript<{ setting: SettingRow }>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_settings_run_now',
        payload,
        requestId,
        env.F2_AUTH,
      );
    const r = await handleRunNowSetting(sid, asCall);
    return withRequestId(r, requestId);
  }

  if (req.method === 'GET' && SETTINGS_LIST_RE.test(url.pathname)) {
    const auth = await requirePerm(req, 'dash_apps', buildRbacOpts(env, requestId));
    if (!auth.ok) {
      return withRequestId(rbacFailureResponse(auth.status, auth.errorCode), requestId);
    }
    const asCall = () =>
      callAppsScript<ListSettingsData>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_settings_list',
        {},
        requestId,
        env.F2_AUTH,
      );
    const r = await handleListSettings(asCall);
    return withRequestId(r, requestId);
  }

  if (req.method === 'POST' && SETTINGS_LIST_RE.test(url.pathname)) {
    const auth = await requirePerm(req, 'dash_apps', buildRbacOpts(env, requestId));
    if (!auth.ok) {
      return withRequestId(rbacFailureResponse(auth.status, auth.errorCode), requestId);
    }
    const body = (await req.json().catch(() => ({}))) as SettingMutationBody;
    const asCall = (payload: Record<string, unknown>) =>
      callAppsScript<{ setting: SettingRow }>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_settings_create',
        payload,
        requestId,
        env.F2_AUTH,
      );
    const r = await handleCreateSetting(body, { username: auth.payload!.sub }, asCall);
    return withRequestId(r, requestId);
  }

  const settingByIdMatch = SETTINGS_BY_ID_RE.exec(url.pathname);
  if (settingByIdMatch && (req.method === 'PATCH' || req.method === 'DELETE')) {
    const auth = await requirePerm(req, 'dash_apps', buildRbacOpts(env, requestId));
    if (!auth.ok) {
      return withRequestId(rbacFailureResponse(auth.status, auth.errorCode), requestId);
    }
    const sid = decodeURIComponent(settingByIdMatch[1]!);
    if (req.method === 'PATCH') {
      const body = (await req.json().catch(() => ({}))) as SettingMutationBody;
      const asCall = (payload: Record<string, unknown>) =>
        callAppsScript<{ setting: SettingRow }>(
          env.APPS_SCRIPT_URL,
          env.APPS_SCRIPT_HMAC,
          'admin_settings_update',
          payload,
          requestId,
          env.F2_AUTH,
        );
      const r = await handleUpdateSetting(sid, body, asCall);
      return withRequestId(r, requestId);
    }
    const asCall = (payload: { setting_id: string }) =>
      callAppsScript<{ setting_id: string }>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_settings_delete',
        payload,
        requestId,
        env.F2_AUTH,
      );
    const r = await handleDeleteSetting(sid, asCall);
    return withRequestId(r, requestId);
  }

  if (req.method === 'GET' && APPS_VERSION_RE.test(url.pathname)) {
    const auth = await requirePerm(req, 'dash_apps', buildRbacOpts(env, requestId));
    if (!auth.ok) {
      return withRequestId(rbacFailureResponse(auth.status, auth.errorCode), requestId);
    }
    const asCall = () =>
      callAppsScript<FormRevisionsData>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_form_revisions',
        {},
        requestId,
        env.F2_AUTH,
      );
    // Pull versioning from worker env (fallback strings if unset).
    const versionEnv = env as unknown as {
      PWA_VERSION?: string;
      PWA_BUILD_SHA?: string;
      WORKER_VERSION?: string;
    };
    const r = await handleVersion(versionEnv, asCall);
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
        env.F2_AUTH,
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
        env.F2_AUTH,
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
        env.F2_AUTH,
      );
    const r = await handleCreateUser(body, { username: auth.payload!.sub }, asCall);
    return withRequestId(r, requestId);
  }

  const userRevokeMatch = USERS_REVOKE_RE.exec(url.pathname);
  if (req.method === 'POST' && userRevokeMatch) {
    const auth = await requirePerm(req, 'dash_users', buildRbacOpts(env, requestId));
    if (!auth.ok) {
      return withRequestId(rbacFailureResponse(auth.status, auth.errorCode), requestId);
    }
    const targetUser = userRevokeMatch[1]!;
    const r = await handleRevokeSessions(targetUser, env.F2_AUTH);
    // Fire-and-forget audit row noting who revoked whom.
    auditFn({
      event_type: 'admin_revoke_sessions',
      actor_username: auth.payload!.sub,
      actor_jti: auth.payload!.jti,
      actor_role: auth.payload!.role,
      client_ip_hash: ipHash,
      event_resource: targetUser,
    });
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
          env.F2_AUTH,
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
        env.F2_AUTH,
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
        env.F2_AUTH,
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
        env.F2_AUTH,
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
          env.F2_AUTH,
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
        env.F2_AUTH,
      );
    const r = await handleDeleteRole(name, asCall);
    return withRequestId(r, requestId);
  }

  const reissueMatch = HCWS_REISSUE_RE.exec(url.pathname);
  if (req.method === 'POST' && reissueMatch) {
    const auth = await requirePerm(req, 'dash_users', buildRbacOpts(env, requestId));
    if (!auth.ok) {
      return withRequestId(rbacFailureResponse(auth.status, auth.errorCode), requestId);
    }
    const hcwId = decodeURIComponent(reissueMatch[1]!);
    const body = (await req.json().catch(() => ({}))) as ReissueRequestBody;
    const asCall = (payload: { hcw_id: string; new_jti: string; prev_jti: string }) =>
      callAppsScript<{
        hcw_id: string;
        facility_id: string;
        new_jti: string;
        old_jti: string;
        token_issued_at: string;
      }>(
        env.APPS_SCRIPT_URL,
        env.APPS_SCRIPT_HMAC,
        'admin_hcws_reissue_token',
        payload as unknown as Record<string, unknown>,
        requestId,
        env.F2_AUTH,
      );
    // Origin of the PWA — request comes from the admin browser, which is
    // same-origin with the PWA in production. Falls back to a sensible
    // default if Origin is missing (curl, etc).
    const pwaOrigin = req.headers.get('Origin') ?? 'https://f2-pwa.pages.dev';
    const r = await handleReissueToken(hcwId, body, env.JWT_SIGNING_KEY, pwaOrigin, asCall, env.F2_AUTH);
    auditFn({
      event_type: 'admin_hcws_reissue_token',
      actor_username: auth.payload!.sub,
      actor_jti: auth.payload!.jti,
      actor_role: auth.payload!.role,
      client_ip_hash: ipHash,
      event_resource: hcwId,
    });
    return withRequestId(r, requestId);
  }

  return notFound(requestId);
}
