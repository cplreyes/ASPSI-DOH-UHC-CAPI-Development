/**
 * F2 Admin Portal — schema migrations (additive only).
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 1.2)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§5)
 *
 * To run: open this Apps Script project in the editor, choose `runAllMigrations`,
 * click Run. Idempotent — safe to re-run; existing sheets/columns are skipped.
 */

/**
 * Create the 5 new admin sheets if they don't already exist.
 * Each is created with header row + frozen first row.
 */
function migrateAddAdminSheets() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var newSheets = [
    {
      name: 'F2_Users',
      headers: [
        'username', 'first_name', 'last_name', 'role_name', 'password_hash',
        'password_must_change', 'email', 'phone',
        'created_at', 'created_by', 'last_login_at'
      ]
    },
    {
      name: 'F2_Roles',
      headers: [
        'name', 'is_builtin', 'version',
        'dash_data', 'dash_report', 'dash_apps', 'dash_users', 'dash_roles',
        'dict_self_admin_up', 'dict_self_admin_down',
        'dict_paper_encoded_up', 'dict_paper_encoded_down',
        'dict_capi_up', 'dict_capi_down',
        'created_at', 'created_by'
      ]
    },
    {
      name: 'F2_HCWs',
      headers: [
        'hcw_id', 'facility_id', 'facility_name',
        'enrollment_token_jti', 'token_issued_at', 'token_revoked_at',
        'status', 'created_at'
      ]
    },
    {
      name: 'F2_FileMeta',
      headers: [
        'file_id', 'filename', 'content_type', 'size_bytes',
        'uploaded_by', 'uploaded_at', 'description', 'deleted_at'
      ]
    },
    {
      name: 'F2_DataSettings',
      headers: [
        'setting_id', 'instrument', 'included_columns',
        'interval_minutes', 'next_run_at', 'output_path_template',
        'last_run_at', 'last_run_status', 'last_run_error',
        'enabled', 'created_by', 'created_at'
      ]
    }
  ];
  var created = [];
  for (var i = 0; i < newSheets.length; i++) {
    var s = newSheets[i];
    if (ss.getSheetByName(s.name)) continue;
    var sheet = ss.insertSheet(s.name);
    sheet.getRange(1, 1, 1, s.headers.length).setValues([s.headers]).setFontWeight('bold');
    sheet.setFrozenRows(1);
    created.push(s.name);
  }
  return { created: created };
}

/**
 * Append the 5 new GPS + provenance columns to F2_Responses if missing.
 *   submission_lat, submission_lng, source_path, encoded_by, encoded_at
 */
function migrateExtendF2ResponsesColumns() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName('F2_Responses');
  if (!sh) throw new Error('F2_Responses sheet not found');
  var headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  var newCols = ['submission_lat', 'submission_lng', 'source_path', 'encoded_by', 'encoded_at'];
  var added = [];
  for (var i = 0; i < newCols.length; i++) {
    var col = newCols[i];
    if (headers.indexOf(col) !== -1) continue;
    sh.getRange(1, sh.getLastColumn() + 1).setValue(col).setFontWeight('bold');
    added.push(col);
  }
  return { added: added };
}

/**
 * Append the 7 new admin-context columns to F2_Audit if missing.
 *   actor_username, actor_jti, actor_role, event_resource,
 *   event_payload_json, client_ip_hash, request_id
 *
 * Pre-existing rows have these as null (no backfill required — admin context
 * is only meaningful for admin events, which are emitted post-migration).
 */
function migrateExtendF2AuditColumns() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName('F2_Audit');
  if (!sh) throw new Error('F2_Audit sheet not found');
  var headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  var newCols = [
    'actor_username', 'actor_jti', 'actor_role',
    'event_resource', 'event_payload_json',
    'client_ip_hash', 'request_id'
  ];
  var added = [];
  for (var i = 0; i < newCols.length; i++) {
    var col = newCols[i];
    if (headers.indexOf(col) !== -1) continue;
    sh.getRange(1, sh.getLastColumn() + 1).setValue(col).setFontWeight('bold');
    added.push(col);
  }
  return { added: added };
}

/**
 * Top-level orchestrator. Runs all three migrations and logs the result.
 * Run this once per environment (staging, then production at cutover).
 */
function runAllMigrations() {
  var r1 = migrateAddAdminSheets();
  var r2 = migrateExtendF2ResponsesColumns();
  var r3 = migrateExtendF2AuditColumns();
  var summary = {
    adminSheets: r1,
    responses: r2,
    audit: r3
  };
  console.log('Migrations complete: ' + JSON.stringify(summary));
  return summary;
}

/**
 * Backfill source_path = 'self_admin' on F2_Responses rows where the column
 * is empty. Idempotent — only touches rows whose source_path is currently
 * blank, so re-runs after the encoder write path (Task 4.2) starts populating
 * 'paper_encoded' values won't overwrite them.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.7)
 *
 * Run from the AS editor after migrations land. Returns {updated, skipped}.
 */
function backfillSourcePath() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName('F2_Responses');
  if (!sh) throw new Error('F2_Responses sheet not found');
  var headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  var sourcePathCol = headers.indexOf('source_path') + 1;
  if (sourcePathCol === 0) {
    throw new Error('source_path column missing — run migrateExtendF2ResponsesColumns first');
  }
  var lastRow = sh.getLastRow();
  if (lastRow < 2) return { updated: 0, skipped: 0 };
  var range = sh.getRange(2, sourcePathCol, lastRow - 1, 1);
  var values = range.getValues();
  var updated = 0;
  var skipped = 0;
  for (var i = 0; i < values.length; i++) {
    if (values[i][0] === '' || values[i][0] === null) {
      values[i][0] = 'self_admin';
      updated++;
    } else {
      skipped++;
    }
  }
  range.setValues(values);
  console.log('backfillSourcePath: updated=' + updated + ' skipped=' + skipped);
  return { updated: updated, skipped: skipped };
}
