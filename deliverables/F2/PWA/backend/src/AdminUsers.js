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

// ----- Mutations (LockService-wrapped) ------------------------------------

var USERNAME_RE = /^[A-Za-z0-9_]{3,32}$/;
var NAME_RE = /^[A-Za-z][A-Za-z\-' ]*$/;

function _withDocLock(fn) {
  var lock = LockService.getDocumentLock();
  if (!lock.tryLock(30000)) {
    return { ok: false, error: { code: 'E_LOCK_TIMEOUT', message: 'busy, retry' } };
  }
  try {
    return fn();
  } finally {
    lock.releaseLock();
  }
}

function _findUserRow(sh, username) {
  var headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  var unameIdx = headers.indexOf('username');
  if (unameIdx === -1) throw new Error('username column missing');
  var lastRow = sh.getLastRow();
  if (lastRow < 2) return { headers: headers, rowNumber: -1, row: null };
  var data = sh.getRange(2, 1, lastRow - 1, headers.length).getValues();
  for (var i = 0; i < data.length; i++) {
    if (data[i][unameIdx] === username) {
      var obj = {};
      for (var j = 0; j < headers.length; j++) obj[headers[j]] = data[i][j];
      return { headers: headers, rowNumber: i + 2, row: obj };
    }
  }
  return { headers: headers, rowNumber: -1, row: null };
}

/**
 * Append a new user row. Worker has already PBKDF2-hashed the password
 * (spec §7.10 step 4) and set password_must_change=true; AS just persists.
 *
 * Returns E_CONFLICT on duplicate username, E_VALIDATION on shape errors.
 */
function adminUsersCreate(payload) {
  if (!payload || typeof payload !== 'object') {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'payload required' } };
  }
  var u = String(payload.username || '').trim();
  if (!USERNAME_RE.test(u)) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'username must be 3-32 chars [A-Za-z0-9_]' } };
  }
  if (!payload.password_hash) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'password_hash required (worker should pre-hash)' } };
  }
  if (!payload.role_name) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'role_name required' } };
  }
  if (payload.first_name && !NAME_RE.test(String(payload.first_name))) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'first_name must be letters' } };
  }
  if (payload.last_name && !NAME_RE.test(String(payload.last_name))) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'last_name must be letters' } };
  }

  return _withDocLock(function () {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sh = ss.getSheetByName('F2_Users');
    if (!sh) throw new Error('F2_Users sheet not found — run runAllMigrations() first');
    var found = _findUserRow(sh, u);
    if (found.row) {
      return { ok: false, error: { code: 'E_CONFLICT', message: 'username already exists' } };
    }
    var nowIso = new Date().toISOString();
    var row = found.headers.map(function (h) {
      if (h === 'username') return u;
      if (h === 'first_name') return payload.first_name || '';
      if (h === 'last_name') return payload.last_name || '';
      if (h === 'role_name') return payload.role_name;
      if (h === 'password_hash') return payload.password_hash;
      if (h === 'password_must_change') return payload.password_must_change != null ? payload.password_must_change : true;
      if (h === 'email') return payload.email || '';
      if (h === 'phone') return payload.phone || '';
      if (h === 'created_at') return nowIso;
      if (h === 'created_by') return payload.created_by || '';
      if (h === 'last_login_at') return '';
      return '';
    });
    sh.appendRow(row);
    return { ok: true, data: { user: _stripPasswordHash({
      username: u,
      first_name: payload.first_name || '',
      last_name: payload.last_name || '',
      role_name: payload.role_name,
      email: payload.email || '',
      phone: payload.phone || '',
      password_must_change: payload.password_must_change != null ? payload.password_must_change : true,
      password_hash: payload.password_hash,
      created_at: nowIso,
      created_by: payload.created_by || '',
      last_login_at: '',
    }) } };
  });
}

/**
 * Update an existing user. Mutable fields: first_name, last_name,
 * role_name, email, phone, password_hash (only if worker pre-hashed),
 * password_must_change. username is the PK and cannot change.
 */
function adminUsersUpdate(payload) {
  if (!payload || typeof payload !== 'object' || !payload.username) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'username required' } };
  }
  var u = String(payload.username).trim();

  return _withDocLock(function () {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sh = ss.getSheetByName('F2_Users');
    if (!sh) throw new Error('F2_Users sheet not found — run runAllMigrations() first');
    var found = _findUserRow(sh, u);
    if (!found.row) {
      return { ok: false, error: { code: 'E_NOT_FOUND', message: 'user ' + u + ' not found' } };
    }
    var mutable = ['first_name', 'last_name', 'role_name', 'email', 'phone', 'password_hash', 'password_must_change'];
    var updated = {};
    for (var k in found.row) updated[k] = found.row[k];
    for (var i = 0; i < mutable.length; i++) {
      var key = mutable[i];
      if (payload[key] !== undefined) updated[key] = payload[key];
    }
    var rowArr = found.headers.map(function (h) { return updated[h] != null ? updated[h] : ''; });
    sh.getRange(found.rowNumber, 1, 1, found.headers.length).setValues([rowArr]);
    return { ok: true, data: { user: _stripPasswordHash(updated) } };
  });
}

function adminUsersDelete(payload) {
  if (!payload || !payload.username) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'username required' } };
  }
  var u = String(payload.username).trim();

  return _withDocLock(function () {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sh = ss.getSheetByName('F2_Users');
    if (!sh) throw new Error('F2_Users sheet not found — run runAllMigrations() first');
    var found = _findUserRow(sh, u);
    if (!found.row) {
      return { ok: false, error: { code: 'E_NOT_FOUND', message: 'user ' + u + ' not found' } };
    }
    sh.deleteRow(found.rowNumber);
    return { ok: true, data: { username: u } };
  });
}

if (typeof module !== 'undefined') {
  module.exports = {
    adminUsersList: adminUsersList,
    adminRolesList: adminRolesList,
    adminUsersCreate: adminUsersCreate,
    adminUsersUpdate: adminUsersUpdate,
    adminUsersDelete: adminUsersDelete,
    _stripPasswordHash: _stripPasswordHash,
  };
}
