/**
 * Shared types for the F2 PWA auth Worker.
 * See ../../../docs/superpowers/specs/2026-04-26-f2-pwa-auth-rearch-design.md
 */

export interface Env {
  /** PBKDF2-SHA256 password hash for the admin UI. Format: `<saltB64url>:<iterations>:<hashB64url>`. */
  ADMIN_PASSWORD_HASH: string;
  /** HMAC secret shared with the Apps Script backend. Mirrors PROP_HMAC_SECRET. */
  APPS_SCRIPT_HMAC: string;
  /** Apps Script /exec deployment URL. */
  APPS_SCRIPT_URL: string;
  /** Base64url-encoded random key (32 bytes) used to sign JWTs (HS256). */
  JWT_SIGNING_KEY: string;
  /** KV namespace for revocation list + token audit. */
  F2_AUTH: KVNamespace;
}

/** Claims embedded in every device JWT. */
export interface JwtClaims {
  /** Per-token identity (UUID v4). Used as the revocation lookup key. */
  jti: string;
  /** Stable identifier for the physical device (UUID v4). */
  tablet_id: string;
  /** Facility this token was issued for. Informational on the server. */
  facility_id: string;
  /** Issued-at, epoch seconds. */
  iat: number;
  /** Expiry, epoch seconds. */
  exp: number;
}

/** KV-stored audit metadata for an issued token. Key: `token:<jti>`. */
export interface TokenAuditEntry {
  jti: string;
  tablet_id: string;
  tablet_label: string;
  facility_id: string;
  issued_at: number;
  exp: number;
  revoked_at?: number;
}

/** Standard error response shape, matches the existing PWA expectation. */
export interface ErrorResponse {
  ok: false;
  error: { code: string; message: string };
}

/** Convenience helper: produce a JSON Response with the given status. */
export function jsonResponse(body: unknown, status = 200, extraHeaders: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...extraHeaders },
  });
}

export function errorResponse(code: string, message: string, status: number): Response {
  const body: ErrorResponse = { ok: false, error: { code, message } };
  return jsonResponse(body, status);
}
