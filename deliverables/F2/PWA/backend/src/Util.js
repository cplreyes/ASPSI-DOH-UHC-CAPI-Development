function ok(data) {
  return { ok: true, data: data };
}

function fail(code, message) {
  return { ok: false, error: { code: code, message: message } };
}

function timingSafeEq(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string') return false;
  if (a.length !== b.length) return false;
  var diff = 0;
  for (var i = 0; i < a.length; i++) {
    diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return diff === 0;
}

function generateUuid() {
  var hex = '0123456789abcdef';
  var s = '';
  for (var i = 0; i < 36; i++) {
    if (i === 8 || i === 13 || i === 18 || i === 23) {
      s += '-';
    } else if (i === 14) {
      s += '4';
    } else if (i === 19) {
      s += hex[(Math.random() * 4) | 8];
    } else {
      s += hex[(Math.random() * 16) | 0];
    }
  }
  return s;
}

function nowMs() {
  return Date.now();
}

/**
 * Resolve the F2 backend Spreadsheet handle, regardless of whether the
 * Apps Script project is bound to the workbook (Extensions -> Apps
 * Script from inside Sheets) or standalone (script.google.com -> New
 * project, with a SPREADSHEET_ID Script Property).
 *
 * Bound projects: SpreadsheetApp.getActiveSpreadsheet() returns the
 * bound workbook. Standalone projects: it returns null, which historically
 * crashed every admin handler (Migrations, AdminUsers, AdminFiles, etc.)
 * with `Cannot read properties of null (reading 'getSheetByName')`.
 *
 * Try active first (cheap, no extra ScriptProperties read on hot paths),
 * fall back to openById from PROP_SPREADSHEET_ID. Throws a clear error
 * if neither path resolves so the failure mode is explicit instead of
 * a null-deref four call frames deep.
 */
function getF2Spreadsheet() {
  var ss = null;
  try {
    ss = SpreadsheetApp.getActiveSpreadsheet();
  } catch (e) {
    ss = null;
  }
  if (ss) return ss;
  var ssId = PropertiesService.getScriptProperties().getProperty('SPREADSHEET_ID');
  if (!ssId) {
    throw new Error('No active spreadsheet and SPREADSHEET_ID script property not set. Run setupBackend() or bind the script to a workbook.');
  }
  return SpreadsheetApp.openById(ssId);
}

if (typeof module !== 'undefined') {
  module.exports = {
    ok: ok,
    fail: fail,
    timingSafeEq: timingSafeEq,
    generateUuid: generateUuid,
    nowMs: nowMs,
    getF2Spreadsheet: getF2Spreadsheet,
  };
}
