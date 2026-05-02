/**
 * F2 Admin Portal - Scheduled CSV break-out builder.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 3.3)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (sec 7.6)
 *
 * Two RPC entry points:
 *   admin_settings_run_due()         - returns CSVs for every due/enabled
 *                                      F2_DataSettings row, marks them
 *                                      `running` so two cron ticks within
 *                                      a window can't double-process.
 *   admin_settings_mark_complete()   - records success/failure + advances
 *                                      next_run_at by interval_minutes.
 *
 * Worker drives the R2 write between the two; AS never sees R2.
 *
 * The pure helpers (column filtering, CSV escaping, output path
 * resolution) are exported via the standard CJS-export tail at the
 * bottom of this file so backend Vitest can require() them outside
 * an Apps Script runtime.
 */

function _renderOutputPath(template, ctx) {
  // Replace {{date}} and {{setting_id}} placeholders. Date is YYYY-MM-DD
  // in UTC; the worker key path needs to be deterministic across the
  // ~5min cron window so the same row processed twice would overwrite
  // (idempotent), not fork into two objects.
  var d = new Date(ctx.nowMs);
  var pad = function (n) { return String(n).padStart(2, '0'); };
  var ymd = d.getUTCFullYear() + '-' + pad(d.getUTCMonth() + 1) + '-' + pad(d.getUTCDate());
  return String(template)
    .replace(/\{\{date\}\}/g, ymd)
    .replace(/\{\{setting_id\}\}/g, String(ctx.setting_id));
}

function _csvEscape(value) {
  if (value == null) return '';
  var s = String(value);
  if (s.indexOf(',') >= 0 || s.indexOf('"') >= 0 || s.indexOf('\n') >= 0 || s.indexOf('\r') >= 0) {
    return '"' + s.replace(/"/g, '""') + '"';
  }
  return s;
}

function _buildCsv(columns, rows) {
  var out = columns.map(_csvEscape).join(',') + '\r\n';
  for (var i = 0; i < rows.length; i++) {
    var cells = [];
    for (var j = 0; j < columns.length; j++) {
      cells.push(_csvEscape(rows[i][columns[j]]));
    }
    out += cells.join(',') + '\r\n';
  }
  return out;
}

function _parseIncludedColumns(s, fallback) {
  if (!s) return fallback;
  try {
    var parsed = JSON.parse(s);
    if (Array.isArray(parsed) && parsed.length > 0) {
      return parsed.filter(function (c) { return typeof c === 'string'; });
    }
    return fallback;
  } catch (e) {
    return fallback;
  }
}

/**
 * Walk F2_DataSettings, pick rows where enabled AND next_run_at <= now
 * AND last_run_status != 'running', mark each running, build a CSV
 * from F2_Responses. Returns to the worker:
 *   { ran: [{setting_id, output_path, csv}], errors: [{setting_id, message}] }
 */
function adminSettingsRunDue() {
  var ss = getF2Spreadsheet();
  var settingsSh = ss.getSheetByName('F2_DataSettings');
  if (!settingsSh) {
    return { ok: false, error: { code: 'E_INTERNAL', message: 'F2_DataSettings missing' } };
  }
  var responsesSh = ss.getSheetByName('F2_Responses');
  if (!responsesSh) {
    return { ok: false, error: { code: 'E_INTERNAL', message: 'F2_Responses missing' } };
  }

  var lock = LockService.getScriptLock();
  if (!lock.tryLock(30000)) {
    return { ok: false, error: { code: 'E_LOCK_TIMEOUT', message: 'busy, retry' } };
  }
  try {
    var sHeaders = settingsSh.getRange(1, 1, 1, settingsSh.getLastColumn()).getValues()[0];
    var sLastRow = settingsSh.getLastRow();
    if (sLastRow < 2) return { ok: true, data: { ran: [], errors: [] } };
    var sData = settingsSh.getRange(2, 1, sLastRow - 1, sHeaders.length).getValues();

    var nowMs = Date.now();
    var nowIso = new Date(nowMs).toISOString();
    var due = [];
    for (var i = 0; i < sData.length; i++) {
      var row = {};
      for (var j = 0; j < sHeaders.length; j++) row[sHeaders[j]] = sData[i][j];
      if (!row.enabled) continue;
      if (row.last_run_status === 'running') continue;
      var nextRun = String(row.next_run_at || '');
      if (!nextRun || nextRun > nowIso) continue;
      due.push({ row: row, rowNumber: i + 2 });
    }

    if (due.length === 0) return { ok: true, data: { ran: [], errors: [] } };

    var statusIdx = sHeaders.indexOf('last_run_status');
    if (statusIdx === -1) {
      return { ok: false, error: { code: 'E_INTERNAL', message: 'last_run_status column missing' } };
    }
    for (var k = 0; k < due.length; k++) {
      settingsSh.getRange(due[k].rowNumber, statusIdx + 1).setValue('running');
    }

    var rHeaders = responsesSh.getRange(1, 1, 1, responsesSh.getLastColumn()).getValues()[0];
    var rLastRow = responsesSh.getLastRow();
    var responseRows = [];
    if (rLastRow >= 2) {
      var rData = responsesSh.getRange(2, 1, rLastRow - 1, rHeaders.length).getValues();
      for (var m = 0; m < rData.length; m++) {
        var rowObj = {};
        for (var n = 0; n < rHeaders.length; n++) rowObj[rHeaders[n]] = rData[m][n];
        responseRows.push(rowObj);
      }
    }

    var ran = [];
    var errors = [];
    for (var p = 0; p < due.length; p++) {
      var setting = due[p].row;
      try {
        var cols = _parseIncludedColumns(setting.included_columns, rHeaders);
        var csv = _buildCsv(cols, responseRows);
        var outPath = _renderOutputPath(setting.output_path_template, {
          nowMs: nowMs,
          setting_id: setting.setting_id,
        });
        ran.push({
          setting_id: setting.setting_id,
          output_path: outPath,
          csv: csv,
        });
      } catch (err) {
        errors.push({
          setting_id: setting.setting_id,
          message: err && err.message ? err.message : String(err),
        });
      }
    }
    return { ok: true, data: { ran: ran, errors: errors } };
  } finally {
    lock.releaseLock();
  }
}

/**
 * After the worker writes the CSV to R2, it calls this to record the
 * outcome and schedule the next run. status: 'success' | 'failed'.
 * On success, next_run_at = last_run_at + interval_minutes; on failure,
 * next_run_at advances the same so a poison row doesn't burn quota.
 */
function adminSettingsMarkComplete(payload) {
  if (!payload || !payload.setting_id) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'setting_id required' } };
  }
  var status = payload.status === 'failed' ? 'failed' : 'success';
  var sid = String(payload.setting_id);
  var errMsg = String(payload.error_message || '');

  var lock = LockService.getScriptLock();
  if (!lock.tryLock(30000)) {
    return { ok: false, error: { code: 'E_LOCK_TIMEOUT', message: 'busy, retry' } };
  }
  try {
    var ss = getF2Spreadsheet();
    var sh = ss.getSheetByName('F2_DataSettings');
    if (!sh) return { ok: false, error: { code: 'E_INTERNAL', message: 'F2_DataSettings missing' } };
    var headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
    var lastRow = sh.getLastRow();
    if (lastRow < 2) {
      return { ok: false, error: { code: 'E_NOT_FOUND', message: 'no settings rows' } };
    }
    var data = sh.getRange(2, 1, lastRow - 1, headers.length).getValues();
    for (var i = 0; i < data.length; i++) {
      var row = {};
      for (var j = 0; j < headers.length; j++) row[headers[j]] = data[i][j];
      if (row.setting_id !== sid) continue;
      var nowMs = Date.now();
      var nowIso = new Date(nowMs).toISOString();
      var interval = Number(row.interval_minutes) || 60;
      row.last_run_at = nowIso;
      row.last_run_status = status;
      row.last_run_error = status === 'failed' ? errMsg : '';
      row.next_run_at = new Date(nowMs + interval * 60 * 1000).toISOString();
      var rowArr = headers.map(function (h) { return row[h] != null ? row[h] : ''; });
      sh.getRange(i + 2, 1, 1, headers.length).setValues([rowArr]);
      return { ok: true, data: { setting_id: sid, last_run_status: status, next_run_at: row.next_run_at } };
    }
    return { ok: false, error: { code: 'E_NOT_FOUND', message: 'setting ' + sid + ' not found' } };
  } finally {
    lock.releaseLock();
  }
}

if (typeof module !== 'undefined') {
  module.exports = {
    adminSettingsRunDue: adminSettingsRunDue,
    adminSettingsMarkComplete: adminSettingsMarkComplete,
    _renderOutputPath: _renderOutputPath,
    _csvEscape: _csvEscape,
    _buildCsv: _buildCsv,
    _parseIncludedColumns: _parseIncludedColumns,
  };
}
