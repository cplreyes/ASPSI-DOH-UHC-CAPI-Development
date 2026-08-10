/**
 * Respondent-path handlers — behavior-parity port of backend/src/Handlers.js
 * (handleSubmit/handleBatchSubmit/handleConfig/handleFacilities) writing
 * csweb_f2 directly instead of the F2_Responses Sheet. Envelope + error codes
 * are IDENTICAL so the PWA's sync-client works unchanged.
 */
import { randomUUID } from 'node:crypto';
import type { Store, ResponseRow, DlqRow } from './store.js';

export type Envelope<T = unknown> =
  | { ok: true; data: T }
  | { ok: false; error: { code: string; message: string } };

const err = (code: string, message: string): Envelope => ({ ok: false, error: { code, message } });

const coordOrEmpty = (v: unknown): string => {
  if (v == null || v === '') return '';
  const n = Number(v);
  return Number.isFinite(n) ? String(n) : '';
};

// GPS capture outcome (Reports-tab audit P1-4 instrumentation). Whitelisted so
// a hostile/buggy client can't stuff arbitrary strings into the column; the
// paper-encode path never asks for GPS, so its rows default to not_requested.
const GPS_STATUSES = new Set([
  'granted',
  'denied',
  'timeout',
  'unavailable',
  'unsupported',
  'not_requested',
]);
const gpsStatusOrDefault = (raw: unknown, sourcePath: string): string => {
  const s = String(raw ?? '');
  if (GPS_STATUSES.has(s)) return s;
  return sourcePath === 'paper_encoded' ? 'not_requested' : '';
};

function buildResponseRow(
  payload: Record<string, unknown>,
  serverSubmissionId: string,
  nowIso: string,
): ResponseRow {
  const values = (payload.values ?? {}) as Record<string, unknown>;
  const sourcePath = String(payload.source_path ?? values.source_path ?? 'self_admin');
  return {
    submission_id: serverSubmissionId,
    client_submission_id: String(payload.client_submission_id),
    submitted_at_server: nowIso,
    submitted_at_client:
      payload.submitted_at_client != null ? new Date(payload.submitted_at_client as number).toISOString() : '',
    source: 'PWA',
    spec_version: String(payload.spec_version ?? ''),
    app_version: String(payload.app_version ?? ''),
    hcw_id: String(payload.hcw_id ?? ''),
    facility_id: String(payload.facility_id ?? ''),
    device_fingerprint: String(payload.device_fingerprint ?? ''),
    sync_attempt_count: payload.sync_attempt_count != null ? String(payload.sync_attempt_count) : '1',
    // #825: consent refusals are first-class rows.
    status: values.consent_given === 0 ? 'refusal' : 'stored',
    values_json: JSON.stringify(values),
    // Top-level wins over values (encoder path is explicit) — parity with AS.
    submission_lat: coordOrEmpty(payload.submission_lat != null ? payload.submission_lat : values.submission_lat),
    submission_lng: coordOrEmpty(payload.submission_lng != null ? payload.submission_lng : values.submission_lng),
    gps_status: gpsStatusOrDefault(
      payload.gps_status != null ? payload.gps_status : values.gps_status,
      sourcePath,
    ),
    source_path: sourcePath,
    encoded_by: String(payload.encoded_by ?? ''),
    encoded_at: payload.encoded_at ? new Date(payload.encoded_at as number | string).toISOString() : '',
    qn: String(payload.qn ?? values.qn ?? ''),
  };
}

export async function handleSubmit(payload: unknown, store: Store): Promise<Envelope> {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    return err('E_PAYLOAD_INVALID', 'Body must be a JSON object');
  }
  const p = payload as Record<string, unknown>;
  if (typeof p.client_submission_id !== 'string' || !p.client_submission_id) {
    return err('E_PAYLOAD_INVALID', 'Missing client_submission_id');
  }
  if (typeof p.spec_version !== 'string' || !p.spec_version) {
    return err('E_PAYLOAD_INVALID', 'Missing spec_version');
  }
  if (p.values == null) return err('E_PAYLOAD_INVALID', 'Missing values');

  const minSpec = await store.getConfig('min_accepted_spec_version');
  if (minSpec && (p.spec_version as string) < minSpec) {
    return err('E_SPEC_TOO_OLD', `spec_version ${p.spec_version} < ${minSpec}`);
  }
  const nowIso = new Date().toISOString();
  if (typeof p.values !== 'object' || Array.isArray(p.values)) {
    const dlqRow: DlqRow = {
      dlq_id: randomUUID(),
      received_at_server: nowIso,
      client_submission_id: String(p.client_submission_id),
      reason: 'values must be an object',
      payload_json: JSON.stringify(p),
    };
    await store.dlqAppend(dlqRow);
    return err('E_VALIDATION', 'values must be an object');
  }

  const existing = await store.findExisting(p.client_submission_id as string);
  if (existing) {
    return { ok: true, data: { submission_id: existing.submission_id, status: 'duplicate', server_timestamp: nowIso } };
  }

  const serverId = 'srv-' + randomUUID();
  const row = buildResponseRow(p, serverId, nowIso);
  const outcome = await store.insertResponse(row);
  if (outcome === 'duplicate') {
    // Lost a same-csid race to another request — the unique key makes this safe.
    const winner = await store.findExisting(row.client_submission_id);
    return {
      ok: true,
      data: { submission_id: winner?.submission_id ?? serverId, status: 'duplicate', server_timestamp: nowIso },
    };
  }
  // Forward-only case close-out (#825 refusal tag + its submitted counterpart):
  // once the response is in, the HCW row leaves 'enrolled' — which removes an
  // sr- case from the Facilities/Coverage "In progress" count and trips
  // /claim's already-completed gate for numbered slots. Never demotes
  // refusal/revoked. Branch on row.status: buildResponseRow already derived it
  // from consent_given, so response and HCW tags cannot disagree.
  if (row.status === 'refusal') {
    await store.tagRefusal(row.hcw_id);
  } else {
    await store.tagSubmitted(row.hcw_id);
  }
  return { ok: true, data: { submission_id: serverId, status: 'accepted', server_timestamp: row.submitted_at_server } };
}

export interface BatchResultItem {
  client_submission_id: string | null;
  submission_id?: string;
  status: 'accepted' | 'duplicate' | 'rejected';
  error?: { code: string; message: string };
}

export async function handleBatchSubmit(payload: unknown, store: Store): Promise<Envelope<{ results: BatchResultItem[] }>> {
  const p = payload as { responses?: unknown } | null;
  if (!p || !Array.isArray(p.responses)) {
    return err('E_PAYLOAD_INVALID', 'Body must be { responses: [] }') as Envelope<{ results: BatchResultItem[] }>;
  }
  if (p.responses.length > 50) {
    return err('E_BATCH_TOO_LARGE', 'Max 50 responses per batch') as Envelope<{ results: BatchResultItem[] }>;
  }
  const results: BatchResultItem[] = [];
  for (const item of p.responses) {
    const clientId =
      item && typeof item === 'object' && typeof (item as Record<string, unknown>).client_submission_id === 'string'
        ? ((item as Record<string, unknown>).client_submission_id as string)
        : null;
    const r = await handleSubmit(item, store);
    if (r.ok) {
      const d = r.data as { submission_id: string; status: 'accepted' | 'duplicate' };
      results.push({ client_submission_id: clientId, submission_id: d.submission_id, status: d.status });
    } else {
      results.push({ client_submission_id: clientId, status: 'rejected', error: r.error });
    }
  }
  return { ok: true, data: { results } };
}

const coerceConfigValue = (v: string): string | boolean => (v === 'true' ? true : v === 'false' ? false : v);

export async function handleConfig(store: Store): Promise<Envelope> {
  const pairs = await store.readAllConfig();
  const out: Record<string, string | boolean> = {};
  for (const [k, v] of pairs) out[k] = coerceConfigValue(v);
  return { ok: true, data: out };
}

export async function handleFacilities(store: Store): Promise<Envelope> {
  return { ok: true, data: { facilities: await store.readFacilities() } };
}
