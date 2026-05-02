/**
 * F2 Admin Portal - F2_DataSettings CRUD.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 3.3)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (sec 7.6)
 *
 * Each row schedules a recurring CSV break-out: every interval_minutes,
 * the worker's scheduled() handler asks AS for due settings, writes the
 * CSVs to R2 at output_path_template, and marks each row complete.
 *
 * F2_DataSettings columns (Migrations.js):
 *   setting_id, instrument, included_columns, interval_minutes,
 *   next_run_at, output_path_template, last_run_at, last_run_status,
 *   last_run_error, enabled, created_by, created_at
 */

function _settingsSheet() {
  var ss = getF2Spreadsheet();
  var sh = ss.getSheetByName('F2_DataSettings');
  if (!sh) throw new Error('F2_DataSettings sheet not found - run runAllMigrations() first');
  return sh;
}

function _readSettings() {
  var sh = _settingsSheet();
  var headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  var lastRow = sh.getLastRow();
  if (lastRow < 2) return { sh: sh, headers: headers, rows: [] };
  var data = sh.getRange(2, 1, lastRow - 1, headers.length).getValues();
  var rows = [];
  for (var i = 0; i < data.length; i++) {
    var obj = { _rowNumber: i + 2 };
    for (var j = 0; j < headers.length; j++) obj[headers[j]] = data[i][j];
    rows.push(obj);
  }
  return { sh: sh, headers: headers, rows: rows };
}

function _withSettingsLock(fn) {
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(30000)) {
    return { ok: false, error: { code: 'E_LOCK_TIMEOUT', message: 'busy, retry' } };
  }
  try {
    return fn();
  } finally {
    lock.releaseLock();
  }
}

function _stripInternal(row) {
  var clone = {};
  for (var k in row) {
    if (Object.prototype.hasOwnProperty.call(row, k) && k !== '_rowNumber') clone[k] = row[k];
  }
  return clone;
}

function _validateInterval(n) {
  // Cron fires every 5 minutes, so 5 is the floor; 1440 (24h) caps long
  // intervals so a stuck row can't sit "next_run_at = next year" by accident.
  return typeof n === 'number' && n >= 5 && n <= 1440 && n === Math.floor(n);
}

function _validateOutputTemplate(s) {
  // Template uses `{{date}}` and `{{setting_id}}` placeholders. Reject anything
  // with backslash or ".." path traversal, or a leading slash.
  if (typeof s !== 'string' || s.length === 0) return false;
  if (s.indexOf('\\') !== -1) return false;
  if (s.indexOf('..') !== -1) return false;
  if (s.charAt(0) === '/') return false;
  return true;
}

function adminSettingsList() {
  var data = _readSettings();
  var rows = data.rows.map(_stripInternal);
  rows.sort(function (a, b) {
    var ka = a.created_at || '';
    var kb = b.created_at || '';
    if (ka < kb) return 1;
    if (ka > kb) return -1;
    return 0;
  });
  return { ok: true, data: { settings: rows, total: rows.length } };
}

function adminSettingsCreate(payload) {
  if (!payload || typeof payload !== 'object') {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'payload required' } };
  }
  var instrument = String(payload.instrument || 'F2').trim();
  var interval = Number(payload.interval_minutes);
  var template = String(payload.output_path_template || '').trim();
  var includedCols = Array.isArray(payload.included_columns)
    ? payload.included_columns.slice()
    : [];
  var enabled = payload.enabled !== false;

  if (!_validateInterval(interval)) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'interval_minutes must be an integer 5-1440' } };
  }
  if (!_validateOutputTemplate(template)) {
    return {
      ok: false,
      error: {
        code: 'E_VALIDATION',
        message: 'output_path_template required (no leading slash, no backslash, no ..)',
      },
    };
  }

  return _withSettingsLock(function () {
    var data = _readSettings();
    var nowMs = Date.now();
    var nowIso = new Date(nowMs).toISOString();
    var nextRunIso = new Date(nowMs + interval * 60 * 1000).toISOString();
    var settingId = 's-' + Utilities.getUuid().slice(0, 8);
    var record = {
      setting_id: settingId,
      instrument: instrument,
      included_columns: JSON.stringify(includedCols),
      interval_minutes: interval,
      next_run_at: nextRunIso,
      output_path_template: template,
      last_run_at: '',
      last_run_status: '',
      last_run_error: '',
      enabled: enabled,
      created_by: payload.created_by || '',
      created_at: nowIso,
    };
    var row = data.headers.map(function (h) { return record[h] != null ? record[h] : ''; });
    data.sh.appendRow(row);
    return { ok: true, data: { setting: record } };
  });
}

function adminSettingsUpdate(payload) {
  if (!payload || !payload.setting_id) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'setting_id required' } };
  }
  var sid = String(payload.setting_id);

  return _withSettingsLock(function () {
    var data = _readSettings();
    for (var i = 0; i < data.rows.length; i++) {
      var r = data.rows[i];
      if (r.setting_id !== sid) continue;
      var updated = _stripInternal(r);
      if (payload.instrument !== undefined) updated.instrument = String(payload.instrument);
      if (payload.included_columns !== undefined) {
        if (!Array.isArray(payload.included_columns)) {
          return { ok: false, error: { code: 'E_VALIDATION', message: 'included_columns must be an array' } };
        }
        updated.included_columns = JSON.stringify(payload.included_columns);
      }
      if (payload.interval_minutes !== undefined) {
        var n = Number(payload.interval_minutes);
        if (!_validateInterval(n)) {
          return { ok: false, error: { code: 'E_VALIDATION', message: 'interval_minutes must be an integer 5-1440' } };
        }
        updated.interval_minutes = n;
      }
      if (payload.output_path_template !== undefined) {
        var t = String(payload.output_path_template);
        if (!_validateOutputTemplate(t)) {
          return {
            ok: false,
            error: {
              code: 'E_VALIDATION',
              message: 'output_path_template invalid (no leading slash, no backslash, no ..)',
            },
          };
        }
        updated.output_path_template = t;
      }
      if (payload.enabled !== undefined) updated.enabled = !!payload.enabled;
      var rowArr = data.headers.map(function (h) { return updated[h] != null ? updated[h] : ''; });
      data.sh.getRange(r._rowNumber, 1, 1, data.headers.length).setValues([rowArr]);
      return { ok: true, data: { setting: updated } };
    }
    return { ok: false, error: { code: 'E_NOT_FOUND', message: 'setting ' + sid + ' not found' } };
  });
}

function adminSettingsDelete(payload) {
  if (!payload || !payload.setting_id) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'setting_id required' } };
  }
  var sid = String(payload.setting_id);

  return _withSettingsLock(function () {
    var data = _readSettings();
    for (var i = 0; i < data.rows.length; i++) {
      var r = data.rows[i];
      if (r.setting_id !== sid) continue;
      data.sh.deleteRow(r._rowNumber);
      return { ok: true, data: { setting_id: sid } };
    }
    return { ok: false, error: { code: 'E_NOT_FOUND', message: 'setting ' + sid + ' not found' } };
  });
}

/**
 * Set next_run_at = now and clear last_run_status so the next cron tick
 * picks up this setting. Used by the "Run now" button in the UI.
 */
function adminSettingsRunNow(payload) {
  if (!payload || !payload.setting_id) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'setting_id required' } };
  }
  var sid = String(payload.setting_id);

  return _withSettingsLock(function () {
    var data = _readSettings();
    for (var i = 0; i < data.rows.length; i++) {
      var r = data.rows[i];
      if (r.setting_id !== sid) continue;
      if (r.last_run_status === 'running') {
        return { ok: false, error: { code: 'E_CONFLICT', message: 'already running' } };
      }
      var nowIso = new Date().toISOString();
      var updated = _stripInternal(r);
      updated.next_run_at = nowIso;
      updated.last_run_status = '';
      updated.last_run_error = '';
      var rowArr = data.headers.map(function (h) { return updated[h] != null ? updated[h] : ''; });
      data.sh.getRange(r._rowNumber, 1, 1, data.headers.length).setValues([rowArr]);
      return { ok: true, data: { setting: updated } };
    }
    return { ok: false, error: { code: 'E_NOT_FOUND', message: 'setting ' + sid + ' not found' } };
  });
}

if (typeof module !== 'undefined') {
  module.exports = {
    adminSettingsList: adminSettingsList,
    adminSettingsCreate: adminSettingsCreate,
    adminSettingsUpdate: adminSettingsUpdate,
    adminSettingsDelete: adminSettingsDelete,
    adminSettingsRunNow: adminSettingsRunNow,
    _validateInterval: _validateInterval,
    _validateOutputTemplate: _validateOutputTemplate,
  };
}
