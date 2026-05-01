/**
 * F2 Admin Portal — F2_Users + F2_Roles read RPCs.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Tasks 1.10 + 3.x)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§5, §7.10–7.12)
 *
 * Read-only listings for the admin Users + Roles tabs. Mutations
 * (create / update / delete / bulk import / revoke sessions) live in
 * separate Sprint 3 tasks that wrap these in LockService. password_hash
 * is intentionally stripped from list output — the API never returns it.
 */

var ADMIN_USERS_SCAN_CAP = 50000;

function _readSheetAsObjects(sheetName) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(sheetName);
  if (!sh) throw new Error(sheetName + ' sheet not found — run runAllMigrations() first');
  var headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  var lastRow = sh.getLastRow();
  if (lastRow < 2) return { headers: headers, rows: [] };
  var data = sh.getRange(2, 1, Math.min(lastRow - 1, ADMIN_USERS_SCAN_CAP), headers.length).getValues();
  var rows = data.map(function (r) {
    var obj = {};
    for (var i = 0; i < headers.length; i++) obj[headers[i]] = r[i];
    return obj;
  });
  return { headers: headers, rows: rows };
}

function _stripPasswordHash(user) {
  var clone = {};
  for (var k in user) {
    if (Object.prototype.hasOwnProperty.call(user, k) && k !== 'password_hash') {
      clone[k] = user[k];
    }
  }
  // Surface a boolean rather than dropping the column entirely so the UI
  // can show "(set)" vs "(not set)" without leaking the hash.
  clone.has_password = !!user.password_hash;
  return clone;
}

function adminUsersList(filters) {
  filters = filters || {};
  var data = _readSheetAsObjects('F2_Users');
  var matched = [];
  var q = filters.q ? String(filters.q).toLowerCase() : null;
  for (var i = 0; i < data.rows.length; i++) {
    var u = data.rows[i];
    if (filters.role_name && u.role_name !== filters.role_name) continue;
    if (filters.username && u.username !== filters.username) continue;
    if (q) {
      var hay = (
        String(u.username || '') + ' ' +
        String(u.first_name || '') + ' ' +
        String(u.last_name || '') + ' ' +
        String(u.email || '')
      ).toLowerCase();
      if (hay.indexOf(q) === -1) continue;
    }
    matched.push(_stripPasswordHash(u));
  }
  // Newest first by created_at (ISO string compares correctly).
  matched.sort(function (a, b) {
    var ka = a.created_at || '';
    var kb = b.created_at || '';
    if (ka < kb) return 1;
    if (ka > kb) return -1;
    return 0;
  });
  return { ok: true, data: { users: matched, total: matched.length } };
}

function adminRolesList() {
  var data = _readSheetAsObjects('F2_Roles');
  // Sort built-in roles first (stable for the matrix), then alphabetical.
  var rows = data.rows.slice();
  rows.sort(function (a, b) {
    var ba = a.is_builtin ? 0 : 1;
    var bb = b.is_builtin ? 0 : 1;
    if (ba !== bb) return ba - bb;
    var na = String(a.name || '');
    var nb = String(b.name || '');
    if (na < nb) return -1;
    if (na > nb) return 1;
    return 0;
  });
  return { ok: true, data: { roles: rows, total: rows.length } };
}

if (typeof module !== 'undefined') {
  module.exports = {
    adminUsersList: adminUsersList,
    adminRolesList: adminRolesList,
    _stripPasswordHash: _stripPasswordHash,
  };
}
