/**
 * F2 Admin Portal — Data dashboard handlers.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.2)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.1, §7.2)
 *
 * Thin wrappers around the AS read RPCs (Task 2.1). Parses URL query
 * params into the AS filter shape, forwards via callAppsScript, maps
 * AS errors to HTTP status codes (E_NOT_FOUND → 404, anything else → 502).
 */
import { jsonResponse } from '../../types';
import type { AppsScriptResponse } from '../apps-script-client';

export interface ResponseRow {
  submission_id: string;
  client_submission_id: string;
  submitted_at_server: string;
  submitted_at_client: string | number;
  source: string;
  spec_version: string;
  app_version: string;
  hcw_id: string;
  facility_id: string;
  device_fingerprint: string;
  sync_attempt_count: string;
  status: string;
  values_json: string;
  submission_lat: number | string;
  submission_lng: number | string;
  source_path: string;
  encoded_by: string;
  encoded_at: string;
}

export interface ListResponsesData {
  rows: ResponseRow[];
  total: number;
  has_more: boolean;
}

export interface ListFilters {
  from?: string;
  to?: string;
  facility_id?: string;
  status?: string;
  source_path?: string;
  q?: string;
  limit?: number;
  offset?: number;
}

export type ListResponsesAsCallable = (
  filters: ListFilters,
) => Promise<AppsScriptResponse<ListResponsesData>>;

export type GetResponseByIdAsCallable = (
  payload: { id: string },
) => Promise<AppsScriptResponse<ResponseRow>>;

function errorJson(code: string, message: string, status: number): Response {
  return jsonResponse({ ok: false, error: { code, message } }, status);
}

function parseFilters(params: URLSearchParams): ListFilters {
  const out: ListFilters = {};
  const from = params.get('from');
  const to = params.get('to');
  const facility = params.get('facility_id');
  const status = params.get('status');
  const sp = params.get('source_path');
  const q = params.get('q');
  const limit = params.get('limit');
  const offset = params.get('offset');
  if (from) out.from = from;
  if (to) out.to = to;
  if (facility) out.facility_id = facility;
  if (status) out.status = status;
  if (sp) out.source_path = sp;
  if (q) out.q = q;
  if (limit && /^\d+$/.test(limit)) out.limit = Number(limit);
  if (offset && /^\d+$/.test(offset)) out.offset = Number(offset);
  return out;
}

export async function handleListResponses(
  url: URL,
  asCallable: ListResponsesAsCallable,
): Promise<Response> {
  const filters = parseFilters(url.searchParams);
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

export async function handleGetResponseById(
  id: string,
  asCallable: GetResponseByIdAsCallable,
): Promise<Response> {
  if (!id) return errorJson('E_VALIDATION', 'submission id required', 400);
  const r = await asCallable({ id });
  if (!r.ok || !r.data) {
    if (r.error?.code === 'E_NOT_FOUND') {
      return errorJson('E_NOT_FOUND', r.error.message, 404);
    }
    return errorJson(
      r.error?.code ?? 'E_BACKEND',
      r.error?.message ?? 'Apps Script unavailable',
      502,
    );
  }
  return jsonResponse(r.data, 200);
}

// Re-exported for the routes layer to compose ListFilters from request params.
export { parseFilters as _parseFilters };
