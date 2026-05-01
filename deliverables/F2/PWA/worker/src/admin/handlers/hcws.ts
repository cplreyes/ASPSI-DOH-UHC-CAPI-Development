/**
 * F2 Admin Portal — HCW token reissue handler.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 4.4 + 4.5)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.5)
 *
 * Issuance order is critical:
 *   1. Generate new_jti.
 *   2. CAS the F2_HCWs row prev_jti → new_jti via Apps Script.
 *   3. ONLY on AS success, mint the new HCW JWT with new_jti.
 *
 * If we minted first and then CAS failed, an attacker (or buggy admin
 * tab) holding two windows could double-issue with both tokens still
 * minted. Doing AS first means failed CAS attempts never produce a
 * usable token.
 *
 * Distinct from the existing M10-era handleIssueToken in src/admin.ts:
 * that path mints per-tablet JWTs gated on a session cookie. This is
 * gated on the new admin portal RBAC (dash_users) and rotates the jti
 * for an existing HCW.
 */
import { jsonResponse } from '../../types';
import { mintJwt } from '../../jwt';
import type { JwtClaims } from '../../types';
import type { AppsScriptResponse } from '../apps-script-client';

export interface ReissueRequestBody {
  prev_jti?: unknown;
  ttl_days?: unknown;
}

export interface ReissueAsCallable {
  (payload: { hcw_id: string; new_jti: string; prev_jti: string }): Promise<
    AppsScriptResponse<{
      hcw_id: string;
      facility_id: string;
      new_jti: string;
      old_jti: string;
      token_issued_at: string;
    }>
  >;
}

export interface ReissueKv {
  put(key: string, value: string, opts?: { expirationTtl?: number }): Promise<void>;
}

export interface ReissueSuccess {
  hcw_id: string;
  facility_id: string;
  old_jti: string;
  new_token: string;
  new_jti: string;
  expires_at: number;
  /** URL the HCW visits to enroll the new token. Frontend renders this as a QR. */
  enroll_url: string;
}

function errorJson(code: string, message: string, status: number): Response {
  return jsonResponse({ ok: false, error: { code, message } }, status);
}

function statusForAsError(code: string | undefined): number {
  if (code === 'E_VALIDATION') return 400;
  if (code === 'E_NOT_FOUND') return 404;
  if (code === 'E_CAS_FAILED') return 409;
  if (code === 'E_LOCK_TIMEOUT') return 503;
  return 502;
}

/**
 * @param hcwId         Path param
 * @param body          { prev_jti, ttl_days }
 * @param signingKey    JWT_SIGNING_KEY (HCW JWT uses the same key as admin per spec §6.3)
 * @param pwaOrigin     Public PWA origin (e.g. https://f2-pwa.pages.dev) — used to build enroll_url
 * @param asCallable    AS reissue RPC
 * @param kv            F2_AUTH KV — token audit entry
 */
export async function handleReissueToken(
  hcwId: string,
  body: ReissueRequestBody,
  signingKey: string,
  pwaOrigin: string,
  asCallable: ReissueAsCallable,
  kv: ReissueKv,
): Promise<Response> {
  if (!hcwId) return errorJson('E_VALIDATION', 'hcw_id required', 400);

  const prevJti = typeof body.prev_jti === 'string' ? body.prev_jti : '';
  const ttlDays = typeof body.ttl_days === 'number' && body.ttl_days >= 1 && body.ttl_days <= 365
    ? body.ttl_days
    : 30;

  const newJti = crypto.randomUUID();

  // Step 1: AS CAS rotation. Worker only mints if AS confirms.
  const asResp = await asCallable({ hcw_id: hcwId, new_jti: newJti, prev_jti: prevJti });
  if (!asResp.ok || !asResp.data) {
    return errorJson(
      asResp.error?.code ?? 'E_BACKEND',
      asResp.error?.message ?? 'Apps Script unavailable',
      statusForAsError(asResp.error?.code),
    );
  }

  // Step 2: Mint the new HCW JWT.
  const nowS = Math.floor(Date.now() / 1000);
  const exp = nowS + ttlDays * 86400;
  const claims: JwtClaims = {
    jti: newJti,
    tablet_id: crypto.randomUUID(),
    facility_id: asResp.data.facility_id || '',
    iat: nowS,
    exp,
  };
  const token = await mintJwt(claims, signingKey);

  // Step 3: KV audit entry (matches the M10 path's `token:<jti>` shape so
  // existing list/revoke endpoints in src/admin.ts continue to find it).
  const audit = {
    jti: newJti,
    tablet_id: claims.tablet_id,
    tablet_label: 'reissued for ' + hcwId,
    facility_id: asResp.data.facility_id || '',
    issued_at: nowS,
    exp,
  };
  await kv.put(`token:${newJti}`, JSON.stringify(audit), { expirationTtl: ttlDays * 86400 });

  // The PWA's enrollment screen accepts a token query param; HCW visits
  // /enroll?token=... on their device, scans the QR or pastes the token.
  const enrollUrl = `${pwaOrigin}/enroll?token=${encodeURIComponent(token)}`;

  const success: ReissueSuccess = {
    hcw_id: hcwId,
    facility_id: asResp.data.facility_id || '',
    old_jti: asResp.data.old_jti,
    new_token: token,
    new_jti: newJti,
    expires_at: exp,
    enroll_url: enrollUrl,
  };
  return jsonResponse(success, 200);
}
