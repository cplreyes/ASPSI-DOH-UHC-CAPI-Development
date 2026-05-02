/**
 * F2 Admin Portal — fetch wrapper.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.14)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§6.4, §11)
 *
 * Centralizes Authorization header attachment, JSON envelope parsing, and
 * 401 → logout side-effect. Intentionally token-and-onUnauthorized-as-deps
 * (not reading from a global) so it stays trivially unit-testable; the
 * useAdminFetch hook in the React layer binds the current AdminAuth state.
 */

export type ErrorCode =
  | 'E_VALIDATION'
  | 'E_AUTH_INVALID'
  | 'E_AUTH_LOCKED'
  | 'E_AUTH_EXPIRED'
  | 'E_PERM_DENIED'
  | 'E_BACKEND'
  | 'E_NOT_FOUND'
  | 'E_CONFLICT'
  | 'E_CAS_FAILED'
  | 'E_LOCK_TIMEOUT'
  | 'E_NETWORK'
  | 'E_UNKNOWN';

export interface ApiError {
  code: ErrorCode;
  message: string;
  status?: number;
  requestId?: string;
}

export type ApiResult<T> =
  | { ok: true; data: T; requestId?: string }
  | { ok: false; error: ApiError };

export interface AdminFetchOptions {
  token?: string | null;
  onUnauthorized?: () => void;
  fetchImpl?: typeof fetch;
}

interface ErrorEnvelope {
  ok: false;
  error: { code: string; message: string };
}

/**
 * Make an authenticated request to the admin API. The path should be the
 * full URL (caller composes proxyUrl + endpoint). Returns a discriminated
 * union — never throws on HTTP errors. Network failures map to E_NETWORK.
 */
export async function adminFetch<T = unknown>(
  url: string,
  init: RequestInit = {},
  opts: AdminFetchOptions = {},
): Promise<ApiResult<T>> {
  const fetchImpl = opts.fetchImpl ?? fetch;
  const headers = new Headers(init.headers);
  if (opts.token) headers.set('Authorization', `Bearer ${opts.token}`);
  // Default to JSON for string bodies. NEVER set Content-Type when the body
  // is FormData / Blob / URLSearchParams - the browser/runtime auto-sets the
  // correct multipart boundary or form-encoded type, and overriding it
  // strips the boundary and breaks the upload (Files panel surfaced this:
  // worker rejected with "multipart/form-data body required").
  const bodyIsFormDataLike =
    typeof FormData !== 'undefined' && init.body instanceof FormData ||
    typeof Blob !== 'undefined' && init.body instanceof Blob ||
    typeof URLSearchParams !== 'undefined' && init.body instanceof URLSearchParams;
  if (init.body && !bodyIsFormDataLike && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  let resp: Response;
  try {
    resp = await fetchImpl(url, { ...init, headers });
  } catch (err) {
    return {
      ok: false,
      error: {
        code: 'E_NETWORK',
        message: err instanceof Error ? err.message : 'Network unavailable',
      },
    };
  }

  const requestIdHeader = resp.headers.get('X-Request-Id');
  const reqIdSpread = requestIdHeader ? { requestId: requestIdHeader } : {};

  // 401 always triggers the logout side-effect — the JWT is dead and the
  // caller cannot recover. The route layer redirects to /admin/login.
  if (resp.status === 401) {
    opts.onUnauthorized?.();
  }

  if (resp.status === 204) {
    return { ok: true, data: undefined as T, ...reqIdSpread };
  }

  let body: unknown;
  try {
    body = await resp.json();
  } catch {
    return {
      ok: false,
      error: {
        code: 'E_BACKEND',
        message: `Invalid JSON response (HTTP ${resp.status})`,
        status: resp.status,
        ...reqIdSpread,
      },
    };
  }

  if (!resp.ok || isErrorEnvelope(body)) {
    const env = body as ErrorEnvelope;
    return {
      ok: false,
      error: {
        code: normalizeErrorCode(env?.error?.code),
        message: env?.error?.message ?? `Request failed (HTTP ${resp.status})`,
        status: resp.status,
        ...reqIdSpread,
      },
    };
  }

  return { ok: true, data: body as T, ...reqIdSpread };
}

function isErrorEnvelope(body: unknown): body is ErrorEnvelope {
  return (
    typeof body === 'object' &&
    body !== null &&
    'ok' in body &&
    (body as { ok: unknown }).ok === false
  );
}

function normalizeErrorCode(code: unknown): ErrorCode {
  const known: ErrorCode[] = [
    'E_VALIDATION',
    'E_AUTH_INVALID',
    'E_AUTH_LOCKED',
    'E_AUTH_EXPIRED',
    'E_PERM_DENIED',
    'E_BACKEND',
    'E_NOT_FOUND',
    'E_CONFLICT',
    'E_CAS_FAILED',
    'E_LOCK_TIMEOUT',
    'E_NETWORK',
  ];
  if (typeof code === 'string' && (known as string[]).includes(code)) {
    return code as ErrorCode;
  }
  return 'E_UNKNOWN';
}
