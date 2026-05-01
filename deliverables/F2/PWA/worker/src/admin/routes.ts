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
import { callAppsScript } from './apps-script-client';

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

  return notFound(requestId);
}
