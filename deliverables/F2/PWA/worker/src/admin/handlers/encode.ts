/**
 * F2 Admin Portal — paper-encoder submit handler.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 4.2)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.13)
 *
 * The Operator transcribes paper surveys via the admin portal. Worker
 * stamps the encoder identity (username from JWT sub) and forwards to
 * the Apps Script `admin_encode_submit` RPC, which reuses the PWA submit
 * write path with `source_path='paper_encoded'` (Task 2.7).
 *
 * Validation here is intentionally light — the Apps Script handler
 * already runs the canonical payload validation. Worker rejects only
 * what we know is invalid before round-tripping (no values, no hcw_id,
 * no client_submission_id) so we don't spend an AS quota call on a
 * payload we'd reject anyway.
 */
import { jsonResponse } from '../../types';
import type { AppsScriptResponse } from '../apps-script-client';

export interface EncodeRequestBody {
  client_submission_id?: unknown;
  spec_version?: unknown;
  app_version?: unknown;
  submitted_at_client?: unknown;
  device_fingerprint?: unknown;
  values?: unknown;
  facility_id?: unknown;
}

export interface EncodeSuccess {
  submission_id: string;
  status: string;
  server_timestamp: string;
}

export interface EncodeActor {
  username: string;
}

export type EncodeAsCallable = (
  payload: Record<string, unknown>,
) => Promise<AppsScriptResponse<EncodeSuccess>>;

function errorJson(code: string, message: string, status: number): Response {
  return jsonResponse({ ok: false, error: { code, message } }, status);
}

export async function handleEncodeSubmit(
  hcwId: string,
  body: EncodeRequestBody,
  actor: EncodeActor,
  asCallable: EncodeAsCallable,
): Promise<Response> {
  if (!hcwId) return errorJson('E_VALIDATION', 'hcw_id path param required', 400);
  if (!body || typeof body !== 'object') {
    return errorJson('E_VALIDATION', 'request body must be a JSON object', 400);
  }
  if (typeof body.client_submission_id !== 'string' || body.client_submission_id.length === 0) {
    return errorJson('E_VALIDATION', 'client_submission_id required', 400);
  }
  if (typeof body.spec_version !== 'string' || body.spec_version.length === 0) {
    return errorJson('E_VALIDATION', 'spec_version required', 400);
  }
  if (body.values == null || typeof body.values !== 'object' || Array.isArray(body.values)) {
    return errorJson('E_VALIDATION', 'values must be a JSON object', 400);
  }
  if (!actor.username) {
    return errorJson('E_INTERNAL', 'actor username missing from RBAC context', 500);
  }

  const enriched: Record<string, unknown> = {
    client_submission_id: body.client_submission_id,
    hcw_id: hcwId,
    spec_version: body.spec_version,
    app_version: body.app_version ?? '',
    submitted_at_client: body.submitted_at_client ?? null,
    device_fingerprint: body.device_fingerprint ?? '',
    facility_id: body.facility_id ?? '',
    values: body.values,
    // The AS handler force-overrides these from ctx.actor_username + nowMs;
    // we send them defensively so a misconfigured AS (no actor in ctx)
    // still records the right encoder identity.
    encoded_by: actor.username,
  };

  const r = await asCallable(enriched);
  if (!r.ok || !r.data) {
    return errorJson(r.error?.code ?? 'E_BACKEND', r.error?.message ?? 'Apps Script unavailable', 502);
  }
  return jsonResponse(r.data, 200);
}
