/**
 * F2 Admin Portal — audit log helper.
 *
 * Appends a row to F2_Audit with admin-context columns populated.
 * Pre-existing PWA-event columns are left null on admin rows; they coexist
 * in the same sheet keyed by event_type prefix (admin_* vs everything else).
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 1.3)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§5.2, §10.3)
 *
 * Caller passes a context object:
 *   {
 *     event_type:    'admin_login' | 'admin_logout' | 'admin_user_created' | ...
 *     actor_username: string,
 *     actor_jti:      string,
 *     actor_role:     string,
 *     event_resource: string | null,   // resource ID acted on (username, role,
 *                                       //   hcw_id, file_id, submission_id)
 *     payload:        object | null,    // structured details (serialized to JSON)
 *     client_ip_hash: string,           // sha256 of client IP
 *     request_id:     string            // UUID propagated from Worker edge
 *   }
 *
 * The helper assigns occurred_at_server itself (server-side timestamp).
 * For thread-safety, callers should wrap this in LockService.getDocumentLock()
 * via adminAuditWrite (see admin RPC dispatcher).
 */
function writeAuditRow(ctx) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName('F2_Audit');
  if (!sh) throw new Error('F2_Audit sheet not found');
  var headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  var row = headers.map(function (h) {
    if (h === 'event_type') return ctx.event_type || null;
    if (h === 'occurred_at_server') return new Date().toISOString();
    if (h === 'actor_username') return ctx.actor_username || null;
    if (h === 'actor_jti') return ctx.actor_jti || null;
    if (h === 'actor_role') return ctx.actor_role || null;
    if (h === 'event_resource') return ctx.event_resource || null;
    if (h === 'event_payload_json') return ctx.payload ? JSON.stringify(ctx.payload) : null;
    if (h === 'client_ip_hash') return ctx.client_ip_hash || null;
    if (h === 'request_id') return ctx.request_id || null;
    return null;
  });
  sh.appendRow(row);
}

/**
 * RPC entry point invoked from the admin doPost dispatcher (Task 1.5).
 * Wraps writeAuditRow in a document-level lock so concurrent admin events
 * (logins from multiple admins, simultaneous logout + role-change) can't
 * corrupt the F2_Audit sheet via interleaved appendRow calls.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 1.18)
 *
 * Returns `{ ok: true }` on success or throws E_LOCK_TIMEOUT on contention
 * (caller — Worker — fires this via waitUntil so a thrown error logs but
 * never fails the user-facing login/logout response).
 */
function adminAuditWrite(payload) {
  var lock = LockService.getDocumentLock();
  if (!lock.tryLock(30000)) {
    throw new Error('E_LOCK_TIMEOUT');
  }
  try {
    writeAuditRow(payload);
    return { ok: true };
  } finally {
    lock.releaseLock();
  }
}
