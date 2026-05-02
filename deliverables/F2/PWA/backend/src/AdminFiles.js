/**
 * F2 Admin Portal — F2_FileMeta CRUD.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 3.1)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.9)
 *
 * R2 holds the file bytes. AS holds the metadata so the admin UI can
 * list/search without paying R2 list-quota per page render. Worker is
 * the only writer to both; AS sees only the metadata side.
 *
 * Soft delete: adminFilesDelete stamps deleted_at and the list RPC hides
 * those rows. The worker is responsible for purging R2 after the AS
 * delete confirms — AS remains the system of record either way.
 *
 * F2_FileMeta columns (Migrations.js):
 *   file_id, filename, content_type, size_bytes, uploaded_by,
 *   uploaded_at, description, deleted_at
 */

function _fileMetaSheet() {
  var ss = getF2Spreadsheet();
  var sh = ss.getSheetByName('F2_FileMeta');
  if (!sh) throw new Error('F2_FileMeta sheet not found — run runAllMigrations() first');
  return sh;
}

function _readFileRows() {
  var sh = _fileMetaSheet();
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

function _withFilesLock(fn) {
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

/**
 * Append a metadata row. Worker has already streamed the bytes to R2 at
 * key `files/<file_id>` and verified MIME + size before calling.
 *
 * Required: file_id, filename, content_type, size_bytes, uploaded_by.
 * Optional: description, uploaded_at (default now).
 *
 * Returns E_CONFLICT if file_id already exists (worker generated a UUID,
 * so collisions are effectively impossible — the guard is defensive).
 */
function adminFilesCreate(payload) {
  if (!payload || typeof payload !== 'object') {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'payload required' } };
  }
  if (!payload.file_id) return { ok: false, error: { code: 'E_VALIDATION', message: 'file_id required' } };
  if (!payload.filename) return { ok: false, error: { code: 'E_VALIDATION', message: 'filename required' } };
  if (!payload.content_type) return { ok: false, error: { code: 'E_VALIDATION', message: 'content_type required' } };
  if (typeof payload.size_bytes !== 'number' || payload.size_bytes < 0) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'size_bytes must be a non-negative number' } };
  }
  if (!payload.uploaded_by) return { ok: false, error: { code: 'E_VALIDATION', message: 'uploaded_by required' } };

  return _withFilesLock(function () {
    var data = _readFileRows();
    for (var i = 0; i < data.rows.length; i++) {
      if (data.rows[i].file_id === payload.file_id) {
        return { ok: false, error: { code: 'E_CONFLICT', message: 'file_id already exists' } };
      }
    }
    var nowIso = new Date().toISOString();
    var record = {
      file_id: payload.file_id,
      filename: payload.filename,
      content_type: payload.content_type,
      size_bytes: payload.size_bytes,
      uploaded_by: payload.uploaded_by,
      uploaded_at: payload.uploaded_at || nowIso,
      description: payload.description || '',
      deleted_at: '',
    };
    var row = data.headers.map(function (h) { return record[h] != null ? record[h] : ''; });
    data.sh.appendRow(row);
    return { ok: true, data: { file: record } };
  });
}

/**
 * List metadata for non-deleted files. Newest-first by uploaded_at.
 * Filters: q (substring across filename + description + uploaded_by).
 * No paging yet — F2_FileMeta is small (admin-uploaded reference docs);
 * if it grows past a few hundred rows we'll add limit/offset.
 */
function adminFilesList(filters) {
  filters = filters || {};
  var data = _readFileRows();
  var q = filters.q ? String(filters.q).toLowerCase() : null;
  var matched = [];
  for (var i = 0; i < data.rows.length; i++) {
    var r = data.rows[i];
    if (r.deleted_at) continue;
    if (q) {
      var hay = (
        String(r.filename || '') + ' ' +
        String(r.description || '') + ' ' +
        String(r.uploaded_by || '')
      ).toLowerCase();
      if (hay.indexOf(q) === -1) continue;
    }
    var clone = {};
    for (var k in r) {
      if (Object.prototype.hasOwnProperty.call(r, k) && k !== '_rowNumber') clone[k] = r[k];
    }
    matched.push(clone);
  }
  matched.sort(function (a, b) {
    var ka = a.uploaded_at || '';
    var kb = b.uploaded_at || '';
    if (ka < kb) return 1;
    if (ka > kb) return -1;
    return 0;
  });
  return { ok: true, data: { files: matched, total: matched.length } };
}

/**
 * Soft delete by stamping deleted_at. The R2 object purge is the
 * worker's responsibility once this confirms — keeps the metadata as
 * the system of record even if R2 is briefly inconsistent.
 *
 * Returns E_NOT_FOUND for unknown or already-deleted file_id.
 */
function adminFilesDelete(payload) {
  if (!payload || !payload.file_id) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'file_id required' } };
  }
  var fid = String(payload.file_id);

  return _withFilesLock(function () {
    var data = _readFileRows();
    for (var i = 0; i < data.rows.length; i++) {
      var r = data.rows[i];
      if (r.file_id !== fid) continue;
      if (r.deleted_at) {
        return { ok: false, error: { code: 'E_NOT_FOUND', message: 'file ' + fid + ' already deleted' } };
      }
      var deletedAtIdx = data.headers.indexOf('deleted_at');
      if (deletedAtIdx === -1) throw new Error('deleted_at column missing on F2_FileMeta');
      var nowIso = new Date().toISOString();
      data.sh.getRange(r._rowNumber, deletedAtIdx + 1).setValue(nowIso);
      return { ok: true, data: { file_id: fid, deleted_at: nowIso } };
    }
    return { ok: false, error: { code: 'E_NOT_FOUND', message: 'file ' + fid + ' not found' } };
  });
}

/**
 * Lookup by file_id including soft-deleted rows. Used by the worker's
 * download handler to resolve filename + content_type for the
 * Content-Disposition header without round-tripping a list call. Hidden
 * from the admin UI (which calls adminFilesList instead).
 */
function adminFilesGet(payload) {
  if (!payload || !payload.file_id) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'file_id required' } };
  }
  var fid = String(payload.file_id);
  var data = _readFileRows();
  for (var i = 0; i < data.rows.length; i++) {
    var r = data.rows[i];
    if (r.file_id !== fid) continue;
    var clone = {};
    for (var k in r) {
      if (Object.prototype.hasOwnProperty.call(r, k) && k !== '_rowNumber') clone[k] = r[k];
    }
    return { ok: true, data: { file: clone } };
  }
  return { ok: false, error: { code: 'E_NOT_FOUND', message: 'file ' + fid + ' not found' } };
}

if (typeof module !== 'undefined') {
  module.exports = {
    adminFilesCreate: adminFilesCreate,
    adminFilesList: adminFilesList,
    adminFilesDelete: adminFilesDelete,
    adminFilesGet: adminFilesGet,
  };
}
