/**
 * F2 Admin Portal — F2_Roles mutations.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Tasks 3.21, 3.22)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§6.4.1, §8)
 *
 * Reads live in AdminUsers.js (adminRolesList). Mutations live here.
 * The crucial bit: every successful adminRolesUpdate auto-increments
 * the role's `version` so any JWT carrying the prior role_version
 * fails RBAC on the next request and the admin is forced to re-login —
 * the only way the portal can guarantee a perm change takes effect
 * mid-session without a server-side session-revocation broadcast.
 */

var ROLE_NAME_RE = /^[A-Za-z][A-Za-z0-9 _-]{0,63}$/;

var ROLE_PERM_KEYS = [
  'dash_data', 'dash_report', 'dash_apps', 'dash_users', 'dash_roles',
  'dict_self_admin_up', 'dict_self_admin_down',
  'dict_paper_encoded_up', 'dict_paper_encoded_down',
  'dict_capi_up', 'dict_capi_down',
];

function _withRolesLock(fn) {
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

function _findRoleRow(sh, name) {
  var headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  var nameIdx = headers.indexOf('name');
  if (nameIdx === -1) throw new Error('name column missing on F2_Roles');
  var lastRow = sh.getLastRow();
  if (lastRow < 2) return { headers: headers, rowNumber: -1, row: null, nameIdx: nameIdx };
  var data = sh.getRange(2, 1, lastRow - 1, headers.length).getValues();
  for (var i = 0; i < data.length; i++) {
    if (data[i][nameIdx] === name) {
      var obj = {};
      for (var j = 0; j < headers.length; j++) obj[headers[j]] = data[i][j];
      return { headers: headers, rowNumber: i + 2, row: obj, nameIdx: nameIdx };
    }
  }
  return { headers: headers, rowNumber: -1, row: null, nameIdx: nameIdx };
}

function _toBool(v) {
  if (typeof v === 'boolean') return v;
  if (typeof v === 'number') return v !== 0;
  if (typeof v === 'string') {
    var s = v.trim().toLowerCase();
    return s === 'true' || s === '1' || s === 'yes';
  }
  return false;
}

function adminRolesCreate(payload) {
  if (!payload || typeof payload !== 'object') {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'payload required' } };
  }
  var name = String(payload.name || '').trim();
  if (!ROLE_NAME_RE.test(name)) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'role name must start with a letter; up to 64 chars [A-Za-z0-9 _-]' } };
  }
  // At least one perm must be set; otherwise the role is useless.
  var anyPerm = false;
  for (var i = 0; i < ROLE_PERM_KEYS.length; i++) {
    if (_toBool(payload[ROLE_PERM_KEYS[i]])) { anyPerm = true; break; }
  }
  if (!anyPerm) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'at least one permission must be granted' } };
  }

  return _withRolesLock(function () {
    var ss = getF2Spreadsheet();
    var sh = ss.getSheetByName('F2_Roles');
    if (!sh) throw new Error('F2_Roles sheet not found — run runAllMigrations() first');
    var found = _findRoleRow(sh, name);
    if (found.row) {
      return { ok: false, error: { code: 'E_CONFLICT', message: 'role name already exists' } };
    }
    var nowIso = new Date().toISOString();
    var row = found.headers.map(function (h) {
      if (h === 'name') return name;
      if (h === 'is_builtin') return false;
      if (h === 'version') return 1;
      if (h === 'created_at') return nowIso;
      if (h === 'created_by') return payload.created_by || '';
      if (ROLE_PERM_KEYS.indexOf(h) !== -1) return _toBool(payload[h]);
      return '';
    });
    sh.appendRow(row);
    var rowObj = {};
    for (var k = 0; k < found.headers.length; k++) rowObj[found.headers[k]] = row[k];
    return { ok: true, data: { role: rowObj } };
  });
}

/**
 * Update the perm flags on an existing role. Auto-bumps `version` on
 * any successful change so JWTs minted under the prior version fail
 * RBAC (rbac.ts compares role_version claim against current cache /
 * AS read; mismatch → E_AUTH_EXPIRED).
 *
 * `name` is the PK and cannot be renamed (would break JWTs in flight
 * harder than a version bump). Built-in roles cannot be renamed but
 * CAN have perms updated — admins use this to tweak access without
 * the full rename ceremony.
 */
function adminRolesUpdate(payload) {
  if (!payload || !payload.name) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'name required' } };
  }
  var name = String(payload.name).trim();

  return _withRolesLock(function () {
    var ss = getF2Spreadsheet();
    var sh = ss.getSheetByName('F2_Roles');
    if (!sh) throw new Error('F2_Roles sheet not found — run runAllMigrations() first');
    var found = _findRoleRow(sh, name);
    if (!found.row) {
      return { ok: false, error: { code: 'E_NOT_FOUND', message: 'role ' + name + ' not found' } };
    }
    var updated = {};
    for (var k in found.row) updated[k] = found.row[k];
    var changed = false;
    for (var i = 0; i < ROLE_PERM_KEYS.length; i++) {
      var pk = ROLE_PERM_KEYS[i];
      if (payload[pk] !== undefined) {
        var newVal = _toBool(payload[pk]);
        if (newVal !== _toBool(updated[pk])) {
          updated[pk] = newVal;
          changed = true;
        }
      }
    }
    if (changed) {
      updated.version = (Number(updated.version) || 0) + 1;
    }
    var rowArr = found.headers.map(function (h) { return updated[h] != null ? updated[h] : ''; });
    sh.getRange(found.rowNumber, 1, 1, found.headers.length).setValues([rowArr]);
    return { ok: true, data: { role: updated, changed: changed } };
  });
}

function adminRolesDelete(payload) {
  if (!payload || !payload.name) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'name required' } };
  }
  var name = String(payload.name).trim();

  return _withRolesLock(function () {
    var ss = getF2Spreadsheet();
    var sh = ss.getSheetByName('F2_Roles');
    if (!sh) throw new Error('F2_Roles sheet not found — run runAllMigrations() first');
    var found = _findRoleRow(sh, name);
    if (!found.row) {
      return { ok: false, error: { code: 'E_NOT_FOUND', message: 'role ' + name + ' not found' } };
    }
    if (_toBool(found.row.is_builtin)) {
      return { ok: false, error: { code: 'E_VALIDATION', message: 'built-in roles cannot be deleted' } };
    }
    // Reject delete if any users still hold this role — would orphan them.
    var usersSh = ss.getSheetByName('F2_Users');
    if (usersSh && usersSh.getLastRow() > 1) {
      var uHeaders = usersSh.getRange(1, 1, 1, usersSh.getLastColumn()).getValues()[0];
      var roleColIdx = uHeaders.indexOf('role_name');
      if (roleColIdx !== -1) {
        var uData = usersSh.getRange(2, roleColIdx + 1, usersSh.getLastRow() - 1, 1).getValues();
        for (var i = 0; i < uData.length; i++) {
          if (uData[i][0] === name) {
            return { ok: false, error: { code: 'E_CONFLICT', message: 'role still assigned to one or more users' } };
          }
        }
      }
    }
    sh.deleteRow(found.rowNumber);
    return { ok: true, data: { name: name } };
  });
}

if (typeof module !== 'undefined') {
  module.exports = {
    adminRolesCreate: adminRolesCreate,
    adminRolesUpdate: adminRolesUpdate,
    adminRolesDelete: adminRolesDelete,
    ROLE_PERM_KEYS: ROLE_PERM_KEYS,
  };
}
