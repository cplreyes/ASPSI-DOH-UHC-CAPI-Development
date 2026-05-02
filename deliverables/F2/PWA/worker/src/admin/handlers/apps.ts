/**
 * F2 Admin Portal - Files dashboard handlers.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 3.2)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (sec 7.9)
 *
 * R2 holds the bytes; AS holds the metadata. Worker is the only writer
 * to both, so consistency is bounded by the order operations land:
 *
 *   Upload:   R2.put -> AS.adminFilesCreate     (orphaned R2 object on AS failure)
 *   Delete:   AS.adminFilesDelete -> R2.delete  (orphaned R2 object on R2 failure)
 *
 * Either failure mode leaves R2 bytes that AS doesn't track, never the
 * reverse - an admin who can't see a file in the UI can't mistakenly
 * believe it was distributed. A future sweep can reconcile R2 against
 * AS soft-deletes; out of scope for Sprint 3.
 *
 * MIME allowlist + size cap mirror spec sec 7.9 step 7. SVG / HTML / JS
 * are rejected to prevent XSS via Content-Type sniffing on download.
 */
import { jsonResponse } from '../../types';
import type { AppsScriptResponse } from '../apps-script-client';

export const ALLOWED_MIME = new Set([
  'application/pdf',
  'application/zip',
  'application/octet-stream',
  'image/png',
  'image/jpeg',
  'image/gif',
]);

export const MAX_FILE_BYTES = 100 * 1024 * 1024;

export interface FileMetaRow {
  file_id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  uploaded_by: string;
  uploaded_at: string;
  description?: string;
  deleted_at?: string;
}

export interface ListFilesData {
  files: FileMetaRow[];
  total: number;
}

export interface FilesListFilters {
  q?: string;
}

export type FilesListAsCallable = (
  filters: FilesListFilters,
) => Promise<AppsScriptResponse<ListFilesData>>;

export type FilesCreateAsCallable = (
  payload: Record<string, unknown>,
) => Promise<AppsScriptResponse<{ file: FileMetaRow }>>;

export type FilesGetAsCallable = (
  payload: { file_id: string },
) => Promise<AppsScriptResponse<{ file: FileMetaRow }>>;

export type FilesDeleteAsCallable = (
  payload: { file_id: string },
) => Promise<AppsScriptResponse<{ file_id: string; deleted_at: string }>>;

/**
 * Minimal R2 surface used by these handlers. Accepting an interface
 * (rather than the full R2Bucket type) makes the tests trivial - the
 * production wiring still passes env.F2_ADMIN_R2 which structurally
 * satisfies this.
 */
export interface FilesR2 {
  put(
    key: string,
    value: ReadableStream | ArrayBuffer | string,
    options?: { httpMetadata?: { contentType?: string; contentDisposition?: string } },
  ): Promise<unknown>;
  get(key: string): Promise<{
    body: ReadableStream;
    httpMetadata?: { contentType?: string; contentDisposition?: string };
  } | null>;
  delete(key: string): Promise<void>;
}

function errorJson(code: string, message: string, status: number): Response {
  return jsonResponse({ ok: false, error: { code, message } }, status);
}

function statusForAsError(code: string | undefined): number {
  if (code === 'E_VALIDATION') return 400;
  if (code === 'E_NOT_FOUND') return 404;
  if (code === 'E_CONFLICT') return 409;
  if (code === 'E_LOCK_TIMEOUT') return 503;
  return 502;
}

function r2Key(fileId: string): string {
  return `files/${fileId}`;
}

/**
 * Sanitize a filename for safe inclusion in a Content-Disposition header.
 * Strip control chars (U+0000-U+001F, U+007F), double quotes, and
 * backslashes - anything that would break Content-Disposition or enable
 * header injection. Falls back to "file" if entirely scrubbed away.
 */
function sanitizeFilename(name: string): string {
  let cleaned = '';
  for (let i = 0; i < name.length; i++) {
    const c = name.charCodeAt(i);
    // Skip control chars (0x00-0x1F), DEL (0x7F), double quote, backslash.
    if (c < 0x20 || c === 0x7F || c === 0x22 || c === 0x5C) continue;
    cleaned += name[i];
  }
  cleaned = cleaned.trim();
  return cleaned.length > 0 ? cleaned : 'file';
}

export async function handleListFiles(
  url: URL,
  asCallable: FilesListAsCallable,
): Promise<Response> {
  const filters: FilesListFilters = {};
  const q = url.searchParams.get('q');
  if (q) filters.q = q;
  const r = await asCallable(filters);
  if (!r.ok || !r.data) {
    return errorJson(
      r.error?.code ?? 'E_BACKEND',
      r.error?.message ?? 'Apps Script unavailable',
      statusForAsError(r.error?.code),
    );
  }
  return jsonResponse(r.data, 200);
}

/**
 * Multipart upload. Steps:
 *   1. Parse one `file` field from form data; reject non-multipart.
 *   2. Enforce size cap (413) + MIME allowlist (400).
 *   3. crypto.randomUUID for the file_id (R2 key derived from it).
 *   4. R2.put -> AS.adminFilesCreate. AS failure leaves R2 orphan; we
 *      attempt a best-effort R2.delete to clean up before surfacing 502.
 */
export async function handleUploadFile(
  req: Request,
  actor: { username: string },
  r2: FilesR2 | undefined,
  asCallable: FilesCreateAsCallable,
): Promise<Response> {
  // Staging environments without R2 enabled (and any other env where the
  // [[r2_buckets]] binding is omitted) leave env.F2_ADMIN_R2 undefined.
  // Returning a specific error code here is much clearer than the generic
  // "Backend unavailable" the frontend would otherwise show after the
  // worker crashed on r2.put.
  if (!r2) {
    return errorJson(
      'E_NOT_CONFIGURED',
      'File storage is not configured for this environment',
      503,
    );
  }
  const ct = req.headers.get('content-type') || '';
  if (!ct.toLowerCase().startsWith('multipart/form-data')) {
    return errorJson('E_VALIDATION', 'multipart/form-data body required', 400);
  }
  if (!actor.username) {
    return errorJson('E_INTERNAL', 'actor username missing from RBAC context', 500);
  }

  let form: FormData;
  try {
    form = await req.formData();
  } catch {
    return errorJson('E_VALIDATION', 'request body is not valid multipart/form-data', 400);
  }

  const fileEntry = form.get('file');
  // FormData.get() returns string | Blob | null in Workers types. We need
  // a Blob (File extends Blob in browsers; in Workers a multipart "file"
  // field is a Blob carrying name + type metadata).
  if (fileEntry === null || typeof fileEntry === 'string') {
    return errorJson('E_VALIDATION', '"file" form field required', 400);
  }
  const file = fileEntry as Blob & { name?: string };
  if (file.size > MAX_FILE_BYTES) {
    return errorJson('E_VALIDATION', `file exceeds ${MAX_FILE_BYTES} byte cap`, 413);
  }
  // Treat empty / unknown content type as the conservative octet-stream
  // (which is in the allowlist). Browsers usually send something; this
  // handles curl --data-binary without -H Content-Type.
  const mime = file.type || 'application/octet-stream';
  if (!ALLOWED_MIME.has(mime)) {
    return errorJson('E_VALIDATION', `MIME type ${mime} not allowed`, 400);
  }

  const description = typeof form.get('description') === 'string'
    ? (form.get('description') as string)
    : '';

  const fileId = crypto.randomUUID();
  const rawName = file.name ?? 'upload';
  const safeName = sanitizeFilename(rawName);
  const uploadedAt = new Date().toISOString();

  await r2.put(r2Key(fileId), file.stream(), {
    httpMetadata: {
      contentType: mime,
      contentDisposition: `attachment; filename="${safeName}"`,
    },
  });

  const r = await asCallable({
    file_id: fileId,
    filename: safeName,
    content_type: mime,
    size_bytes: file.size,
    uploaded_by: actor.username,
    uploaded_at: uploadedAt,
    description,
  });
  if (!r.ok || !r.data) {
    // Best-effort cleanup of the orphaned R2 object so the bucket
    // doesn't accumulate untracked bytes. Failure here is logged-only;
    // the user-facing error is still the AS failure.
    try {
      await r2.delete(r2Key(fileId));
    } catch {
      // swallow - the AS error is the actionable signal
    }
    return errorJson(
      r.error?.code ?? 'E_BACKEND',
      r.error?.message ?? 'Apps Script unavailable',
      statusForAsError(r.error?.code),
    );
  }

  return jsonResponse({ file: r.data.file }, 201);
}

/**
 * Streams the R2 object to the client. Always sets
 * `Content-Disposition: attachment` so browsers download rather than
 * render - defense in depth against MIME-sniff XSS, even though the
 * upload allowlist already blocks SVG / HTML.
 *
 * AS metadata is fetched first so the response can use the original
 * filename and the AS-recorded content_type. If the file was soft-
 * deleted, return 404 (the row exists but the user shouldn't see it).
 */
export async function handleDownloadFile(
  fileId: string,
  r2: FilesR2 | undefined,
  asCallable: FilesGetAsCallable,
): Promise<Response> {
  if (!r2) {
    return errorJson(
      'E_NOT_CONFIGURED',
      'File storage is not configured for this environment',
      503,
    );
  }
  if (!fileId) return errorJson('E_VALIDATION', 'file_id required', 400);

  const meta = await asCallable({ file_id: fileId });
  if (!meta.ok || !meta.data) {
    return errorJson(
      meta.error?.code ?? 'E_BACKEND',
      meta.error?.message ?? 'Apps Script unavailable',
      statusForAsError(meta.error?.code),
    );
  }
  if (meta.data.file.deleted_at) {
    return errorJson('E_NOT_FOUND', 'file deleted', 404);
  }

  const obj = await r2.get(r2Key(fileId));
  if (!obj) {
    return errorJson('E_NOT_FOUND', 'file bytes not found in storage', 404);
  }

  const safeName = sanitizeFilename(meta.data.file.filename);
  return new Response(obj.body, {
    status: 200,
    headers: {
      'Content-Type': meta.data.file.content_type || 'application/octet-stream',
      'Content-Disposition': `attachment; filename="${safeName}"`,
    },
  });
}

/**
 * Soft-delete via AS first, then best-effort R2 purge. AS being the
 * system of record means a partial failure leaves bytes in R2 but the
 * row marked deleted, which is the safe direction (UI hides the file
 * regardless of R2 state). 204 on success.
 */
export async function handleDeleteFile(
  fileId: string,
  r2: FilesR2 | undefined,
  asCallable: FilesDeleteAsCallable,
): Promise<Response> {
  if (!r2) {
    return errorJson(
      'E_NOT_CONFIGURED',
      'File storage is not configured for this environment',
      503,
    );
  }
  if (!fileId) return errorJson('E_VALIDATION', 'file_id required', 400);

  const r = await asCallable({ file_id: fileId });
  if (!r.ok) {
    return errorJson(
      r.error?.code ?? 'E_BACKEND',
      r.error?.message ?? 'Apps Script unavailable',
      statusForAsError(r.error?.code),
    );
  }
  try {
    await r2.delete(r2Key(fileId));
  } catch {
    // R2 purge failure leaves an orphaned object; the metadata is
    // already marked deleted so the UI is consistent. A future sweep
    // reconciles. We do not surface this to the user.
  }
  return new Response(null, { status: 204 });
}

// ===== Data Settings (Tasks 3.4, 3.5) =====================================

export interface SettingRow {
  setting_id: string;
  instrument: string;
  included_columns: string;
  interval_minutes: number;
  next_run_at: string;
  output_path_template: string;
  last_run_at?: string;
  last_run_status?: string;
  last_run_error?: string;
  enabled: boolean;
  created_by?: string;
  created_at?: string;
}

export interface ListSettingsData {
  settings: SettingRow[];
  total: number;
}

export type SettingsListAsCallable = () => Promise<AppsScriptResponse<ListSettingsData>>;

export type SettingsMutateAsCallable = (
  payload: Record<string, unknown>,
) => Promise<AppsScriptResponse<{ setting: SettingRow }>>;

export type SettingsDeleteAsCallable = (
  payload: { setting_id: string },
) => Promise<AppsScriptResponse<{ setting_id: string }>>;

export interface SettingMutationBody {
  instrument?: unknown;
  included_columns?: unknown;
  interval_minutes?: unknown;
  output_path_template?: unknown;
  enabled?: unknown;
}

const SETTING_ID_RE = /^[A-Za-z0-9_\-]{3,64}$/;

function parseSettingMutation(body: SettingMutationBody): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  if (body.instrument !== undefined) out.instrument = body.instrument;
  if (body.included_columns !== undefined) out.included_columns = body.included_columns;
  if (body.interval_minutes !== undefined) out.interval_minutes = body.interval_minutes;
  if (body.output_path_template !== undefined) out.output_path_template = body.output_path_template;
  if (body.enabled !== undefined) out.enabled = !!body.enabled;
  return out;
}

export async function handleListSettings(
  asCallable: SettingsListAsCallable,
): Promise<Response> {
  const r = await asCallable();
  if (!r.ok || !r.data) {
    return errorJson(
      r.error?.code ?? 'E_BACKEND',
      r.error?.message ?? 'Apps Script unavailable',
      statusForAsError(r.error?.code),
    );
  }
  return jsonResponse(r.data, 200);
}

export async function handleCreateSetting(
  body: SettingMutationBody,
  actor: { username: string },
  asCallable: SettingsMutateAsCallable,
): Promise<Response> {
  if (!actor.username) {
    return errorJson('E_INTERNAL', 'actor username missing from RBAC context', 500);
  }
  const payload = { ...parseSettingMutation(body), created_by: actor.username };
  const r = await asCallable(payload);
  if (!r.ok || !r.data) {
    return errorJson(
      r.error?.code ?? 'E_BACKEND',
      r.error?.message ?? 'Apps Script unavailable',
      statusForAsError(r.error?.code),
    );
  }
  return jsonResponse(r.data, 201);
}

export async function handleUpdateSetting(
  settingId: string,
  body: SettingMutationBody,
  asCallable: SettingsMutateAsCallable,
): Promise<Response> {
  if (!SETTING_ID_RE.test(settingId)) {
    return errorJson('E_VALIDATION', 'invalid setting_id path param', 400);
  }
  const payload = { setting_id: settingId, ...parseSettingMutation(body) };
  const r = await asCallable(payload);
  if (!r.ok || !r.data) {
    return errorJson(
      r.error?.code ?? 'E_BACKEND',
      r.error?.message ?? 'Apps Script unavailable',
      statusForAsError(r.error?.code),
    );
  }
  return jsonResponse(r.data, 200);
}

export async function handleDeleteSetting(
  settingId: string,
  asCallable: SettingsDeleteAsCallable,
): Promise<Response> {
  if (!SETTING_ID_RE.test(settingId)) {
    return errorJson('E_VALIDATION', 'invalid setting_id path param', 400);
  }
  const r = await asCallable({ setting_id: settingId });
  if (!r.ok) {
    return errorJson(
      r.error?.code ?? 'E_BACKEND',
      r.error?.message ?? 'Apps Script unavailable',
      statusForAsError(r.error?.code),
    );
  }
  return new Response(null, { status: 204 });
}

export async function handleRunNowSetting(
  settingId: string,
  asCallable: SettingsMutateAsCallable,
): Promise<Response> {
  if (!SETTING_ID_RE.test(settingId)) {
    return errorJson('E_VALIDATION', 'invalid setting_id path param', 400);
  }
  const r = await asCallable({ setting_id: settingId });
  if (!r.ok || !r.data) {
    return errorJson(
      r.error?.code ?? 'E_BACKEND',
      r.error?.message ?? 'Apps Script unavailable',
      statusForAsError(r.error?.code),
    );
  }
  return jsonResponse(r.data, 200);
}

// ===== Quota (Task 3.9) ===================================================

export interface QuotaKv {
  get(key: string): Promise<string | null>;
}

export interface QuotaData {
  date_utc: string;
  count: number;
  cap: number;
  percent: number;
}

/**
 * Default Apps Script daily URL fetch cap on a Google Workspace account.
 * The widget turns red at 80% of this in the UI.
 */
export const APPS_SCRIPT_DAILY_CAP = 20000;

function utcDateKey(now: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${now.getUTCFullYear()}-${pad(now.getUTCMonth() + 1)}-${pad(now.getUTCDate())}`;
}

/**
 * Read today's AS-call counter from KV at `as_quota:<YYYY-MM-DD>`. The
 * counter increment side is wired up in a follow-up commit (every
 * callAppsScript will bump it). Until then, this returns 0/cap which
 * is the correct empty-state.
 */
export async function handleGetQuota(kv: QuotaKv, now: Date = new Date()): Promise<Response> {
  const key = utcDateKey(now);
  const raw = await kv.get(`as_quota:${key}`);
  const count = raw ? Number(raw) || 0 : 0;
  const data: QuotaData = {
    date_utc: key,
    count,
    cap: APPS_SCRIPT_DAILY_CAP,
    percent: Math.min(100, Math.round((count / APPS_SCRIPT_DAILY_CAP) * 100)),
  };
  return jsonResponse(data, 200);
}
