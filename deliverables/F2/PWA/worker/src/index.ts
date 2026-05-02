/**
 * F2 PWA auth Worker - entry point.
 * Spec: ../../../docs/superpowers/specs/2026-04-26-f2-pwa-auth-rearch-design.md
 *
 * Routes (see spec §7.3):
 *   Public:
 *     POST   /exec               - proxy tablet traffic (JWT-auth, HMAC-forwards)
 *     GET    /exec               - same, for read-only handlers
 *     POST   /verify-token       - PWA enrollment validates a pasted token
 *   Admin (password-gated, HttpOnly session cookie):
 *     POST   /admin/login        - establish session
 *     POST   /admin/issue-token  - mint a new device JWT
 *     POST   /admin/revoke       - revoke an existing JWT by jti
 *     GET    /admin/list         - list active tokens (?facility=... filter)
 *     GET    /admin/             - admin UI (static HTML)
 *
 * CORS: public routes accept cross-origin requests from the PWA (which lives on
 * Cloudflare Pages, a different origin). The Authorization header makes the request
 * "non-simple", so OPTIONS preflight is handled here. Admin routes are same-origin
 * (admin UI is served from this Worker), so they don't need CORS.
 */
import type { Env } from './types';
import { errorResponse } from './types';
import { handleExec } from './exec';
import { handleVerifyToken } from './verify';
import {
  handleAdminLogin,
  handleAdminUi,
  handleIssueToken,
  handleListTokens,
  handleRevokeToken,
} from './admin';
import { adminRouter } from './admin/routes';
import { runDueSettings, depsFromEnv } from './admin/cron';

const PUBLIC_ROUTES = new Set(['/exec', '/verify-token']);

const CORS_HEADERS: Record<string, string> = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Authorization, Content-Type',
  'Access-Control-Max-Age': '86400',
};

function withCors(resp: Response): Response {
  const headers = new Headers(resp.headers);
  for (const [k, v] of Object.entries(CORS_HEADERS)) headers.set(k, v);
  return new Response(resp.body, { status: resp.status, statusText: resp.statusText, headers });
}

export default {
  async fetch(req: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(req.url);
    const path = url.pathname.replace(/\/+$/, '') || '/';
    const method = req.method.toUpperCase();
    const isPublic = PUBLIC_ROUTES.has(path);

    // F2 Admin Portal routes (/admin/api/*) — handled by adminRouter.
    // Returns null for non-admin paths so we fall through to the legacy
    // router below. Same-origin (PWA frontend served from this Worker),
    // no CORS wrap needed.
    const adminResp = await adminRouter(req, env, ctx);
    if (adminResp) return adminResp;

    // CORS preflight for public routes only.
    if (method === 'OPTIONS' && isPublic) {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    let resp: Response;
    try {
      // Public endpoints.
      if (path === '/exec' && (method === 'POST' || method === 'GET')) {
        resp = await handleExec(req, env);
      } else if (path === '/verify-token' && method === 'POST') {
        resp = await handleVerifyToken(req, env);
      }
      // Admin endpoints (same-origin, no CORS).
      else if (path === '/admin/login' && method === 'POST') {
        resp = await handleAdminLogin(req, env);
      } else if (path === '/admin/issue-token' && method === 'POST') {
        resp = await handleIssueToken(req, env);
      } else if (path === '/admin/revoke' && method === 'POST') {
        resp = await handleRevokeToken(req, env);
      } else if (path === '/admin/list' && method === 'GET') {
        resp = await handleListTokens(req, env);
      } else if ((path === '/admin' || path === '/admin/') && method === 'GET') {
        resp = handleAdminUi();
      } else {
        resp = errorResponse('E_NOT_FOUND', `No route for ${method} ${path}`, 404);
      }
    } catch (err) {
      console.error('[f2-pwa-worker] unhandled', err);
      resp = errorResponse('E_INTERNAL', 'Internal Worker error.', 500);
    }

    // Add CORS headers to public-route responses (admin routes are same-origin).
    return isPublic ? withCors(resp) : resp;
  },

  /**
   * Cron trigger: every 5 minutes (wrangler.toml [triggers].crons).
   * Drives the F2_DataSettings break-out CSV exports. Failures are
   * logged but never thrown - a stuck cron tick mustn't poison the
   * Worker isolate.
   */
  async scheduled(_event: ScheduledEvent, env: Env, ctx: ExecutionContext): Promise<void> {
    ctx.waitUntil(
      runDueSettings(depsFromEnv(env)).catch((err) => {
        console.error('[scheduled] runDueSettings threw', err);
      }),
    );
  },
} satisfies ExportedHandler<Env>;
