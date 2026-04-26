/**
 * /exec — proxy handler for tablet traffic.
 * Spec §4.3 (interview submission flow), §6 (error handling).
 */
import type { Env } from './types';
import { errorResponse } from './types';
import { verifyJwt } from './jwt';
import { signAppsScriptRequest } from './hmac';

const APPS_SCRIPT_QUOTA_PATTERNS = [
  // Apps Script returns these strings when daily quota is exceeded.
  'Service invoked too many times',
  'Quota exceeded',
  'Exceeded maximum execution time',
];

export async function handleExec(req: Request, env: Env): Promise<Response> {
  // 1. Bearer token extraction.
  const authHeader = req.headers.get('Authorization') ?? '';
  if (!authHeader.startsWith('Bearer ')) {
    return errorResponse('E_BAD_REQUEST', 'Missing or malformed Authorization header.', 400);
  }
  const token = authHeader.slice('Bearer '.length).trim();

  // 2. JWT signature + exp + iat checks.
  const verifyResult = await verifyJwt(token, env.JWT_SIGNING_KEY);
  if (!verifyResult.ok) {
    const code =
      verifyResult.reason === 'expired'
        ? 'E_TOKEN_EXPIRED'
        : verifyResult.reason === 'iat-future'
          ? 'E_TOKEN_INVALID'
          : verifyResult.reason === 'bad-signature'
            ? 'E_TOKEN_INVALID'
            : 'E_TOKEN_INVALID';
    const message =
      verifyResult.reason === 'expired'
        ? 'Tablet token expired. Re-enrol with a new token from ops.'
        : 'Tablet authorisation invalid. Contact ASPSI ops.';
    return errorResponse(code, message, 401);
  }

  // Reject admin session tokens presented as device tokens (they share the same
  // signing key but are scoped to /admin/* via the cookie path; defence in depth).
  if (verifyResult.claims.tablet_id === '__admin_session__') {
    return errorResponse('E_TOKEN_INVALID', 'Admin session is not a valid device token.', 401);
  }

  // 3. KV revocation check.
  const revoked = await env.F2_AUTH.get(`revoked:${verifyResult.claims.jti}`);
  if (revoked) {
    return errorResponse(
      'E_TOKEN_REVOKED',
      'Tablet revoked by ops. Contact them for a new token.',
      401,
    );
  }

  // 4. Forward to Apps Script with HMAC.
  const url = new URL(req.url);
  const action = url.searchParams.get('action') ?? '';
  if (!action) return errorResponse('E_BAD_REQUEST', 'action query parameter is required.', 400);

  // Apps Script Auth.js verifies ts as integer milliseconds within ±5 minutes of nowMs().
  // The canonical string uses the EXACT string of ts as the URL query, so we stringify once.
  const tsMs = Date.now().toString();
  const method = req.method.toUpperCase();
  const body = method === 'GET' || method === 'HEAD' ? '' : await req.text();

  const sig = await signAppsScriptRequest(env.APPS_SCRIPT_HMAC, method, action, tsMs, body);

  const targetUrl = new URL(env.APPS_SCRIPT_URL);
  targetUrl.searchParams.set('action', action);
  targetUrl.searchParams.set('ts', tsMs);
  targetUrl.searchParams.set('sig', sig);

  const upstreamReq = new Request(targetUrl.toString(), {
    method,
    headers: { 'Content-Type': 'text/plain' }, // matches existing PWA preflight-free pattern
    body: method === 'GET' || method === 'HEAD' ? undefined : body,
  });

  let upstreamResp: Response;
  try {
    upstreamResp = await fetch(upstreamReq);
  } catch (err) {
    return errorResponse('E_BACKEND_UNREACHABLE', `Apps Script unreachable: ${(err as Error).message}`, 502);
  }

  // 5. Apps Script quota detection (spec §6 Failure-1).
  // Apps Script returns 200 OK with a quota error body in some cases, or 429/500 with HTML in others.
  // We read the body, scan for known quota strings, and translate to E_BACKEND_BUSY.
  const upstreamBody = await upstreamResp.text();
  const looksLikeQuota = APPS_SCRIPT_QUOTA_PATTERNS.some((p) => upstreamBody.includes(p));
  if (looksLikeQuota || upstreamResp.status === 429) {
    return errorResponse(
      'E_BACKEND_BUSY',
      'Backend at capacity. The PWA should pause sync and retry in 1h.',
      503,
    );
  }

  // 6. Pass-through.
  return new Response(upstreamBody, {
    status: upstreamResp.status,
    headers: { 'Content-Type': upstreamResp.headers.get('Content-Type') ?? 'application/json' },
  });
}
