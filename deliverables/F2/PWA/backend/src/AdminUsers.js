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
  var ss = getF2Spreadsheet();
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
  // password_hash is normally stripped from list responses to keep secrets
  // off the UI wire. The worker's login handler is the ONLY caller that
  // legitimately needs it (to verifyPassword). Setting include_password_hash
  // is HMAC-gated at the envelope layer (only the worker has the secret),
  // so this flag is safe to honor.
  var includeHash = filters.include_password_hash === true;
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
    matched.push(includeHash ? u : _stripPasswordHash(u));
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
    var ss = getF2Spreadsheet();
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
    var ss = getF2Spreadsheet();
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
  var actor = payload.actor_username ? String(payload.actor_username).trim() : '';

  // Self-delete guard — defense-in-depth (worker also blocks this). R2-#133.
  if (actor && u === actor) {
    return { ok: false, error: { code: 'E_CONFLICT', message: 'cannot delete your own account' } };
  }

  return _withDocLock(function () {
    var ss = getF2Spreadsheet();
    var sh = ss.getSheetByName('F2_Users');
    if (!sh) throw new Error('F2_Users sheet not found — run runAllMigrations() first');
    var found = _findUserRow(sh, u);
    if (!found.row) {
      return { ok: false, error: { code: 'E_NOT_FOUND', message: 'user ' + u + ' not found' } };
    }
    // Orphan-admin guard — refuse to delete the last Administrator. UAT R2
    // recovery incident (Sprint 004 Day 4): carl_admin was hard-deleted from
    // prod F2_Users with no guard, locking Carl out of the portal. R2-#133.
    if (String(found.row.role_name || '') === 'Administrator' && _countAdmins(sh) <= 1) {
      return { ok: false, error: { code: 'E_CONFLICT', message: 'cannot orphan the last Administrator' } };
    }
    sh.deleteRow(found.rowNumber);
    return { ok: true, data: { username: u } };
  });
}

/**
 * R2-#134 (E4-APRT-051): user-self password rotation.
 *
 * Distinct from `adminUsersUpdate` because the worker route that calls this
 * (`PATCH /admin/api/me/password`) is gated only on a valid JWT — no
 * dash_users perm — so a non-administrator can rotate their own password.
 * Worker has already verified the current password (PBKDF2) and pre-hashed
 * the new one. AS only persists the new hash + clears `password_must_change`.
 */
function adminUsersChangePassword(payload) {
  if (!payload || !payload.username || !payload.password_hash) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'username and password_hash required' } };
  }
  var u = String(payload.username).trim();

  return _withDocLock(function () {
    var ss = getF2Spreadsheet();
    var sh = ss.getSheetByName('F2_Users');
    if (!sh) throw new Error('F2_Users sheet not found — run runAllMigrations() first');
    var found = _findUserRow(sh, u);
    if (!found.row) {
      return { ok: false, error: { code: 'E_NOT_FOUND', message: 'user ' + u + ' not found' } };
    }
    var updated = {};
    for (var k in found.row) updated[k] = found.row[k];
    updated.password_hash = payload.password_hash;
    updated.password_must_change = false;
    var rowArr = found.headers.map(function (h) { return updated[h] != null ? updated[h] : ''; });
    sh.getRange(found.rowNumber, 1, 1, found.headers.length).setValues([rowArr]);
    return { ok: true, data: { username: u } };
  });
}

/**
 * R2-#66 (E4-APRT-048): write last_login_at on successful login.
 *
 * Called fire-and-forget from the Worker after JWT mint via ctx.waitUntil,
 * so the user response doesn't wait on this. Single-cell write — no
 * LockService needed (idempotent: a later login overwrites with a newer
 * timestamp). If the column is missing or the user vanished mid-flight,
 * silently no-op rather than fail the login flow.
 *
 * F2_Audit row is written separately by the Worker's auditFn pipeline;
 * this RPC handles only the cell write.
 */
function adminUsersTouchLastLogin(payload) {
  if (!payload || !payload.username) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'username required' } };
  }
  var u = String(payload.username).trim();
  var ts = payload.ts ? String(payload.ts) : new Date().toISOString();

  var ss = getF2Spreadsheet();
  var sh = ss.getSheetByName('F2_Users');
  if (!sh) return { ok: true, data: { username: u, written: false } };
  var headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  var llIdx = headers.indexOf('last_login_at');
  if (llIdx === -1) return { ok: true, data: { username: u, written: false } };
  var found = _findUserRow(sh, u);
  if (!found.row) return { ok: true, data: { username: u, written: false } };
  sh.getRange(found.rowNumber, llIdx + 1).setValue(ts);
  return { ok: true, data: { username: u, written: true, ts: ts } };
}

function _countAdmins(sh) {
  var headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  var roleIdx = headers.indexOf('role_name');
  if (roleIdx === -1) return 0;
  var lastRow = sh.getLastRow();
  if (lastRow < 2) return 0;
  var data = sh.getRange(2, 1, lastRow - 1, headers.length).getValues();
  var count = 0;
  for (var i = 0; i < data.length; i++) {
    if (data[i][roleIdx] === 'Administrator') count++;
  }
  return count;
}

/**
 * Bulk-create admin users (R2-#98). Worker has already PBKDF2-hashed
 * each password and validated structurally. AS iterates and calls
 * adminUsersCreate for each row, collecting per-row results so the
 * UI can render successes alongside rejection reasons.
 *
 * Payload: `{ rows: [{username, password_hash, role_name, ...}] }`
 * Returns: `{ ok: true, data: { results: [{username, status, error?}] } }`
 *
 * status: 'created' | 'rejected'. On rejection, `error` mirrors the
 * adminUsersCreate error shape so the UI can attribute the failure.
 */
function adminUsersBulkImport(payload) {
  if (!payload || !Array.isArray(payload.rows)) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'payload.rows must be an array' } };
  }
  if (payload.rows.length === 0) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'rows must not be empty' } };
  }
  if (payload.rows.length > 100) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'max 100 rows per bulk import' } };
  }
  var results = [];
  var createdCount = 0;
  var rejectedCount = 0;
  for (var i = 0; i < payload.rows.length; i++) {
    var row = payload.rows[i] || {};
    var r = adminUsersCreate(row);
    if (r.ok) {
      createdCount++;
      results.push({
        username: row.username || '',
        status: 'created',
      });
    } else {
      rejectedCount++;
      results.push({
        username: row.username || '',
        status: 'rejected',
        error: r.error || { code: 'E_INTERNAL', message: 'Unknown failure' },
      });
    }
  }
  return {
    ok: true,
    data: {
      results: results,
      total: payload.rows.length,
      created: createdCount,
      rejected: rejectedCount,
    },
  };
}

if (typeof module !== 'undefined') {
  module.exports = {
    adminUsersList: adminUsersList,
    adminRolesList: adminRolesList,
    adminUsersCreate: adminUsersCreate,
    adminUsersUpdate: adminUsersUpdate,
    adminUsersDelete: adminUsersDelete,
    adminUsersBulkImport: adminUsersBulkImport,
    _stripPasswordHash: _stripPasswordHash,
  };
}
