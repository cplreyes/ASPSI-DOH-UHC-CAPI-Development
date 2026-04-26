/**
 * /verify-token — public endpoint used by the PWA enrollment screen.
 * Spec §4.2 step 2.
 *
 * No admin auth: verifying the token IS the auth. We return claims so the PWA can
 * filter the facility/enumerator picker locally before storing the token.
 */
import type { Env } from './types';
import { errorResponse, jsonResponse } from './types';
import { verifyJwt } from './jwt';

export async function handleVerifyToken(req: Request, env: Env): Promise<Response> {
  const body = (await req.json().catch(() => ({}))) as { token?: string };
  const token = (body.token ?? '').trim();
  if (!token) return errorResponse('E_BAD_REQUEST', 'token is required.', 400);

  const result = await verifyJwt(token, env.JWT_SIGNING_KEY);
  if (!result.ok) {
    return errorResponse('E_TOKEN_INVALID', `Token rejected (${result.reason}).`, 401);
  }

  // Reject admin session tokens — they sign with the same key but are not device tokens.
  if (result.claims.tablet_id === '__admin_session__') {
    return errorResponse('E_TOKEN_INVALID', 'Not a device token.', 401);
  }

  // Also check revocation, otherwise a revoked token would still validate at enrollment time.
  const revoked = await env.F2_AUTH.get(`revoked:${result.claims.jti}`);
  if (revoked) return errorResponse('E_TOKEN_REVOKED', 'Token has been revoked.', 401);

  return jsonResponse({
    ok: true,
    claims: {
      facility_id: result.claims.facility_id,
      exp: result.claims.exp,
      tablet_id: result.claims.tablet_id,
    },
  });
}
