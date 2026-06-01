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
 *   uploaded_at, description, deleted_at, folder_path, is_folder
 *
 * Folders (E4-APRT-046 / #174): R2 is flat key-value, so folders are
 * virtual. A folder is a F2_FileMeta row with is_folder=true; its display
 * name is `filename` and it LIVES at root (folder_path='/'), so it appears
 * in the root listing. Its children carry folder_path='/<name>'. Flat,
 * 1-level model: folders are only created at root. folder_path on any row
 * is the path of the *container* it lives in; root is '/'.
 */

var ALLOWED_FILE_EXTENSIONS = ['pdf', 'zip', 'png', 'jpg', 'jpeg', 'gif'];
// Mirrors the worker's ALLOWED_MIME (apps.ts). Keep in sync by hand.
// Rename (#175) re-checks this; octet-stream uploads normally still carry
// one of these extensions because the upload picker filters to them.

function _extensionOf(name) {
  var s = String(name || '');
  var dot = s.lastIndexOf('.');
  if (dot === -1 || dot === s.length - 1) return '';
  return s.slice(dot + 1).toLowerCase();
}

function _validateFileExtension(name) {
  var ext = _extensionOf(name);
  if (!ext) return false;
  for (var i = 0; i < ALLOWED_FILE_EXTENSIONS.length; i++) {
    if (ALLOWED_FILE_EXTENSIONS[i] === ext) return true;
  }
  return false;
}

// Sheets reads a blank cell as '' — coalesce legacy/blank folder_path to
// root so pre-migration files stay visible at the root listing.
function _coalesceFolderPath(v) {
  var s = String(v == null ? '' : v);
  return s.length ? s : '/';
}

// A folder row stores boolean true in is_folder; Sheets may surface it as
// the boolean true or the string 'true' depending on how it was written.
function _isFolderRow(v) {
  return v === true || v === 'true';
}

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
      // #174: which folder the file lands in. Defaults to root. If the
      // folder_path/is_folder columns aren't present yet (migration not run),
      // headers.map below silently drops these — harmless degradation.
      folder_path: payload.folder_path || '/',
      is_folder: false,
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
  // #174: scope to one folder. No path (or '/') = root view, which shows
  // root-level files AND every folder row (folders live at root). A path
  // like '/protocols' shows that folder's children only.
  var pathFilter = filters.path ? String(filters.path) : null;
  if (pathFilter === '/') pathFilter = null;
  var matched = [];
  for (var i = 0; i < data.rows.length; i++) {
    var r = data.rows[i];
    if (r.deleted_at) continue;
    var fp = _coalesceFolderPath(r.folder_path);
    if (pathFilter) {
      if (fp !== pathFilter) continue;
    } else if (fp !== '/') {
      continue; // root view: skip items nested inside a folder
    }
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

/**
 * Rename a file's display name (#175 / E4-APRT-047). Only `filename`
 * changes; file_id (the R2 key) is immutable, so download links never
 * break. The new name is re-validated against the extension allowlist —
 * the bytes and content_type are untouched, but keeping the display name
 * within the allowlist preserves the upload invariant.
 *
 * Folder rows cannot be renamed through this path (it would orphan their
 * children's folder_path); E_VALIDATION if is_folder. Returns the updated
 * row, or E_NOT_FOUND for unknown/soft-deleted file_id.
 */
function adminFilesRename(payload) {
  if (!payload || !payload.file_id) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'file_id required' } };
  }
  if (!payload.new_name || typeof payload.new_name !== 'string') {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'new_name required' } };
  }
  var fid = String(payload.file_id);
  var newName = String(payload.new_name).trim();
  if (newName.length === 0) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'new_name cannot be blank' } };
  }
  if (newName.indexOf('/') !== -1 || newName.indexOf('\\') !== -1 || newName.indexOf('..') !== -1) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'new_name cannot contain path separators or ..' } };
  }
  if (!_validateFileExtension(newName)) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'new_name extension not allowed (pdf, zip, png, jpg, jpeg, gif)' } };
  }

  return _withFilesLock(function () {
    var data = _readFileRows();
    var filenameIdx = data.headers.indexOf('filename');
    if (filenameIdx === -1) throw new Error('filename column missing on F2_FileMeta');
    for (var i = 0; i < data.rows.length; i++) {
      var r = data.rows[i];
      if (r.file_id !== fid) continue;
      if (r.deleted_at) {
        return { ok: false, error: { code: 'E_NOT_FOUND', message: 'file ' + fid + ' not found' } };
      }
      if (_isFolderRow(r.is_folder)) {
        return { ok: false, error: { code: 'E_VALIDATION', message: 'folders cannot be renamed' } };
      }
      data.sh.getRange(r._rowNumber, filenameIdx + 1).setValue(newName);
      var clone = {};
      for (var k in r) {
        if (Object.prototype.hasOwnProperty.call(r, k) && k !== '_rowNumber') clone[k] = r[k];
      }
      clone.filename = newName;
      return { ok: true, data: { file: clone } };
    }
    return { ok: false, error: { code: 'E_NOT_FOUND', message: 'file ' + fid + ' not found' } };
  });
}

/**
 * Create a virtual folder at root (#174 / E4-APRT-046). Flat, 1-level:
 * the folder row lives at root (folder_path='/') so it shows in the root
 * listing; its children carry folder_path='/<name>'. E_CONFLICT if a
 * non-deleted folder of the same name already exists at root.
 *
 * E_NOT_CONFIGURED if the folder columns are absent — makes a missed
 * migration loud instead of silently dropping the folder flag.
 */
function adminFilesCreateFolder(payload) {
  if (!payload || typeof payload !== 'object') {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'payload required' } };
  }
  var name = String(payload.name || '').trim();
  if (name.length === 0) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'folder name required' } };
  }
  if (name.indexOf('/') !== -1 || name.indexOf('\\') !== -1 || name.indexOf('..') !== -1) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'folder name cannot contain slashes or ..' } };
  }
  if (name.length > 128) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'folder name too long (max 128)' } };
  }

  return _withFilesLock(function () {
    var data = _readFileRows();
    if (data.headers.indexOf('folder_path') === -1 || data.headers.indexOf('is_folder') === -1) {
      return { ok: false, error: { code: 'E_NOT_CONFIGURED', message: 'run migrateExtendF2FileMetaColumns first' } };
    }
    // Duplicate guard: a non-deleted folder row of this name already at root.
    for (var i = 0; i < data.rows.length; i++) {
      var r = data.rows[i];
      if (r.deleted_at) continue;
      if (_isFolderRow(r.is_folder) && String(r.filename) === name) {
        return { ok: false, error: { code: 'E_CONFLICT', message: 'folder already exists' } };
      }
    }
    var nowIso = new Date().toISOString();
    var record = {
      file_id: generateUuid(),
      filename: name,
      content_type: 'application/x-directory',
      size_bytes: 0,
      uploaded_by: payload.created_by || '',
      uploaded_at: nowIso,
      description: '',
      deleted_at: '',
      folder_path: '/', // the folder lives at root; its children use '/' + name
      is_folder: true,
    };
    var row = data.headers.map(function (h) { return record[h] != null ? record[h] : ''; });
    data.sh.appendRow(row);
    return { ok: true, data: { folder: record } };
  });
}

if (typeof module !== 'undefined') {
  module.exports = {
    adminFilesCreate: adminFilesCreate,
    adminFilesList: adminFilesList,
    adminFilesDelete: adminFilesDelete,
    adminFilesGet: adminFilesGet,
    adminFilesRename: adminFilesRename,
    adminFilesCreateFolder: adminFilesCreateFolder,
    _extensionOf: _extensionOf,
    _validateFileExtension: _validateFileExtension,
    _coalesceFolderPath: _coalesceFolderPath,
    _isFolderRow: _isFolderRow,
  };
}
