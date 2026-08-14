/**
 * #847: encoder-path HCW ID validation.
 *
 * An encoder pasted an enrollment token into the HCW ID field and the
 * submission stored normally — caught only by eye in the Admin Portal
 * (recovered via the #846 void action). The two formats don't overlap, so
 * reject token-shaped (and generally malformed) values at entry, before
 * anything reaches the backend. `adminEncodeSubmit` (backend/src/
 * AdminEncoder.js) carries the same check server-side as the belt.
 */

/** Real HCW IDs are short slugs: hcw-001, LBRHU1-HCW-03. */
const HCW_ID_RE = /^[A-Za-z0-9][A-Za-z0-9_-]{0,39}$/;

/** Enrollment tokens are JWTs — three base64url segments joined by dots. */
const JWT_RE = /^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/;

/** Bare long-hex secrets (any future non-JWT token shape). */
const LONG_HEX_RE = /^[a-f0-9]{32,}$/i;

export type HcwIdValidation = { ok: true } | { ok: false; reason: 'token' | 'format' };

export function validateHcwId(raw: string): HcwIdValidation {
  const value = raw.trim();
  // Token/link pastes get the specific message — that's the observed
  // failure mode. URLs and query fragments (the /e/<CODE>?k=… link) count.
  if (
    JWT_RE.test(value) ||
    LONG_HEX_RE.test(value) ||
    value.includes('://') ||
    value.includes('?') ||
    value.includes('=') ||
    value.includes('/')
  ) {
    return { ok: false, reason: 'token' };
  }
  if (!HCW_ID_RE.test(value)) {
    return { ok: false, reason: 'format' };
  }
  return { ok: true };
}
