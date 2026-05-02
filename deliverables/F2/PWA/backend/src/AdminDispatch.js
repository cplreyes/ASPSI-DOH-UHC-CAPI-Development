/**
 * F2 Admin Portal - Admin RPC dispatcher.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 1.5)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (sec 6.2)
 *
 * The legacy F2 PWA submit path verifies HMAC over the canonical string
 *   `${method}|${action}|${ts}|${body}`
 * with action/ts/sig as URL params and the JSON values in the body. That
 * shape predates RBAC and isn't structured enough for admin RPCs, which
 * need a request_id propagated through the trace and a payload-level
 * canonicalization that's stable under JSON key reordering.
 *
 * Admin RPCs use an envelope POSTed to the same /exec deployment:
 *   { action, ts, request_id, payload, hmac }
 * where hmac is hex(HMAC-SHA256(secret, `${action}.${ts}.${request_id}.${stableJson(payload)}`)).
 * The action MUST start with "admin_" so a dispatcher branch can pick the
 * envelope path off the legacy path without sniffing the body shape twice.
 *
 * Pure functions live here for backend Vitest. The Apps Script Code.js
 * branches into dispatchAdminAction() when the body parses as a signed
 * envelope; otherwise the legacy verifyRequest + dispatch path runs.
 */

var ADMIN_SKEW_MS = 5 * 60 * 1000;

/**
 * Canonical JSON serialization with stable top-level key ordering.
 * Mirrors the worker's stableJson exactly so HMAC verification round-
 * trips. One-level sort: nested objects/arrays use default ordering.
 *
 * Apps Script V8 supports JSON.stringify(value, replacer) where the
 * replacer is a string-array whitelist that also dictates key order.
 */
function _stableJson(payload) {
  if (payload === null || payload === undefined) return 'null';
  if (typeof payload !== 'object' || Array.isArray(payload)) {
    return JSON.stringify(payload);
  }
  var keys = Object.keys(payload).sort();
  return JSON.stringify(payload, keys);
}

function _canonicalAdminString(action, ts, requestId, payload) {
  return String(action) + '.' + String(ts) + '.' + String(requestId) + '.' + _stableJson(payload);
}

/**
 * Determine whether a parsed body is an admin envelope. Returns the
 * envelope on yes, null on no. Used by the doPost branch to pick a
 * verifier without mixing verification logic into routing.
 */
function _isAdminEnvelope(parsed) {
  if (!parsed || typeof parsed !== 'object') return null;
  if (typeof parsed.action !== 'string') return null;
  if (parsed.action.indexOf('admin_') !== 0) return null;
  if (typeof parsed.ts !== 'number' && typeof parsed.ts !== 'string') return null;
  if (typeof parsed.request_id !== 'string' || parsed.request_id.length === 0) return null;
  if (typeof parsed.hmac !== 'string' || parsed.hmac.length === 0) return null;
  return parsed;
}

function _hexEqualsConstantTime(a, b) {
  var as = String(a).toLowerCase();
  var bs = String(b).toLowerCase();
  if (as.length !== bs.length) return false;
  var diff = 0;
  for (var i = 0; i < as.length; i++) {
    diff |= as.charCodeAt(i) ^ bs.charCodeAt(i);
  }
  return diff === 0;
}

/**
 * Verify an admin envelope. Returns { ok: true } or { ok: false, error }.
 * Mirrors verifyRequest's error code style so the response shape is
 * uniform across legacy and admin paths.
 *
 * @param env       Parsed envelope { action, ts, request_id, payload, hmac }
 * @param secret    HMAC secret (mirrors worker's APPS_SCRIPT_HMAC)
 * @param deps      { hmacSha256Hex(secret, message) -> hex, nowMs() -> ms }
 */
function _verifyAdminEnvelope(env, secret, deps) {
  // ts is in seconds in the envelope (worker uses Math.floor(Date.now()/1000));
  // tolerate either seconds or milliseconds.
  var rawTs = env.ts;
  var tsNum = Number(rawTs);
  if (!isFinite(tsNum)) {
    return { ok: false, error: { code: 'E_TS_INVALID', message: 'ts must be a number' } };
  }
  var tsMs = tsNum < 1e12 ? tsNum * 1000 : tsNum;
  var now = deps.nowMs();
  if (Math.abs(now - tsMs) > ADMIN_SKEW_MS) {
    return { ok: false, error: { code: 'E_TS_SKEW', message: 'Timestamp outside +/-5 minute window' } };
  }

  var canonical = _canonicalAdminString(env.action, rawTs, env.request_id, env.payload);
  var expected = deps.hmacSha256Hex(secret, canonical);
  if (!_hexEqualsConstantTime(expected, env.hmac)) {
    return { ok: false, error: { code: 'E_SIG_INVALID', message: 'Signature mismatch' } };
  }
  return { ok: true };
}

/**
 * Build the action -> handler routing tables. Two tables because the
 * data/reports/encoder modules were authored to be unit-testable with
 * a mock ctx, while the user/role/file/setting/audit/hcw modules touch
 * SpreadsheetApp directly. Both shapes coexist; the dispatcher picks
 * the right call site per action.
 *
 * Exposed as a function (not a const) so registration order matches
 * the bundle ORDER and missing handlers fail loud at dispatch time
 * rather than at module load (which is hard to debug in Apps Script).
 */
function _adminHandlers() {
  return {
    // ctx-less handlers
    no_ctx: {
      admin_users_list: typeof adminUsersList !== 'undefined' ? adminUsersList : null,
      admin_users_create: typeof adminUsersCreate !== 'undefined' ? adminUsersCreate : null,
      admin_users_update: typeof adminUsersUpdate !== 'undefined' ? adminUsersUpdate : null,
      admin_users_delete: typeof adminUsersDelete !== 'undefined' ? adminUsersDelete : null,
      admin_roles_list: typeof adminRolesList !== 'undefined' ? adminRolesList : null,
      admin_roles_create: typeof adminRolesCreate !== 'undefined' ? adminRolesCreate : null,
      admin_roles_update: typeof adminRolesUpdate !== 'undefined' ? adminRolesUpdate : null,
      admin_roles_delete: typeof adminRolesDelete !== 'undefined' ? adminRolesDelete : null,
      admin_files_list: typeof adminFilesList !== 'undefined' ? adminFilesList : null,
      admin_files_create: typeof adminFilesCreate !== 'undefined' ? adminFilesCreate : null,
      admin_files_get: typeof adminFilesGet !== 'undefined' ? adminFilesGet : null,
      admin_files_delete: typeof adminFilesDelete !== 'undefined' ? adminFilesDelete : null,
      admin_settings_list: typeof adminSettingsList !== 'undefined' ? adminSettingsList : null,
      admin_settings_create: typeof adminSettingsCreate !== 'undefined' ? adminSettingsCreate : null,
      admin_settings_update: typeof adminSettingsUpdate !== 'undefined' ? adminSettingsUpdate : null,
      admin_settings_delete: typeof adminSettingsDelete !== 'undefined' ? adminSettingsDelete : null,
      admin_settings_run_now: typeof adminSettingsRunNow !== 'undefined' ? adminSettingsRunNow : null,
      admin_settings_run_due: typeof adminSettingsRunDue !== 'undefined' ? adminSettingsRunDue : null,
      admin_settings_mark_complete: typeof adminSettingsMarkComplete !== 'undefined' ? adminSettingsMarkComplete : null,
      admin_audit_write: typeof adminAuditWrite !== 'undefined' ? adminAuditWrite : null,
      admin_hcws_list: typeof adminHcwsList !== 'undefined' ? adminHcwsList : null,
      admin_hcws_create: typeof adminHcwsCreate !== 'undefined' ? adminHcwsCreate : null,
      admin_hcws_reissue_token: typeof adminHcwsReissueToken !== 'undefined' ? adminHcwsReissueToken : null,
    },
    // (payload, ctx) handlers
    needs_ctx: {
      admin_read_responses: typeof adminReadResponses !== 'undefined' ? adminReadResponses : null,
      admin_count_responses: typeof adminCountResponses !== 'undefined' ? adminCountResponses : null,
      admin_read_response_by_id: typeof adminReadResponseById !== 'undefined' ? adminReadResponseById : null,
      admin_read_audit: typeof adminReadAudit !== 'undefined' ? adminReadAudit : null,
      admin_read_dlq: typeof adminReadDlq !== 'undefined' ? adminReadDlq : null,
      admin_form_revisions: typeof adminFormRevisions !== 'undefined' ? adminFormRevisions : null,
      admin_sync_report: typeof adminSyncReport !== 'undefined' ? adminSyncReport : null,
      admin_map_report: typeof adminMapReport !== 'undefined' ? adminMapReport : null,
      admin_encode_submit: typeof adminEncodeSubmit !== 'undefined' ? adminEncodeSubmit : null,
    },
  };
}

/**
 * Pure dispatcher. Verifies the envelope HMAC and routes the action.
 * Caller (Code.js) provides the context (sheets, deps) and the secret.
 *
 * @param env       Parsed envelope (already JSON.parsed from the body)
 * @param secret    HMAC secret
 * @param ctx       Apps Script ctx (sheets/helpers) for ctx-needing actions
 * @param deps      { hmacSha256Hex, nowMs } so this is unit-testable
 * @param handlers  Optional override — defaults to _adminHandlers().
 */
function dispatchAdminAction(env, secret, ctx, deps, handlers) {
  var verify = _verifyAdminEnvelope(env, secret, deps);
  if (!verify.ok) return verify;

  var tables = handlers || _adminHandlers();
  var action = env.action;

  if (Object.prototype.hasOwnProperty.call(tables.no_ctx, action)) {
    var fn1 = tables.no_ctx[action];
    if (!fn1) {
      return { ok: false, error: { code: 'E_ACTION_UNKNOWN', message: 'admin handler ' + action + ' not loaded' } };
    }
    try {
      return fn1(env.payload || {});
    } catch (err) {
      return { ok: false, error: { code: 'E_INTERNAL', message: String(err && err.message ? err.message : err) } };
    }
  }
  if (Object.prototype.hasOwnProperty.call(tables.needs_ctx, action)) {
    var fn2 = tables.needs_ctx[action];
    if (!fn2) {
      return { ok: false, error: { code: 'E_ACTION_UNKNOWN', message: 'admin handler ' + action + ' not loaded' } };
    }
    try {
      return fn2(env.payload || {}, ctx);
    } catch (err) {
      return { ok: false, error: { code: 'E_INTERNAL', message: String(err && err.message ? err.message : err) } };
    }
  }
  return { ok: false, error: { code: 'E_ACTION_UNKNOWN', message: 'Unknown admin action: ' + action } };
}

if (typeof module !== 'undefined') {
  module.exports = {
    dispatchAdminAction: dispatchAdminAction,
    _stableJson: _stableJson,
    _canonicalAdminString: _canonicalAdminString,
    _isAdminEnvelope: _isAdminEnvelope,
    _verifyAdminEnvelope: _verifyAdminEnvelope,
    _hexEqualsConstantTime: _hexEqualsConstantTime,
  };
}
