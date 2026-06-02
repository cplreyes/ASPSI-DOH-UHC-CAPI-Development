/**
 * AdminFiles — rename (#175) + virtual folders (#174) + path-scoped list.
 *
 * AdminFiles.js touches Apps Script globals directly (getF2Spreadsheet,
 * LockService, generateUuid) rather than an injected ctx, so we install a
 * faithful in-memory F2_FileMeta sheet on globalThis before requiring the
 * module. The mock backs a 2D array (row 0 = headers) and implements just the
 * Range/Sheet surface AdminFiles uses: getRange(r,c[,nr,nc]).getValues(),
 * getLastColumn/getLastRow, getRange(r,c).setValue, appendRow.
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);

// ---- In-memory Sheet mock --------------------------------------------------

class FakeSheet {
  constructor(headers, rows = []) {
    this.data = [headers.slice(), ...rows.map((r) => r.slice())];
  }
  getLastColumn() {
    return this.data[0].length;
  }
  getLastRow() {
    return this.data.length;
  }
  getRange(row, col, numRows, numCols) {
    const self = this;
    return {
      getValues() {
        const nr = numRows == null ? 1 : numRows;
        const nc = numCols == null ? 1 : numCols;
        const out = [];
        for (let r = 0; r < nr; r++) {
          const srcRow = self.data[row - 1 + r] || [];
          const slice = [];
          for (let c = 0; c < nc; c++) slice.push(srcRow[col - 1 + c]);
          out.push(slice);
        }
        return out;
      },
      setValue(v) {
        while (self.data.length < row) self.data.push([]);
        const target = self.data[row - 1];
        while (target.length < col) target.push('');
        target[col - 1] = v;
        return this;
      },
      setFontWeight() {
        return this;
      },
    };
  }
  appendRow(arr) {
    this.data.push(arr.slice());
  }
}

const FILE_META_HEADERS = [
  'file_id', 'filename', 'content_type', 'size_bytes',
  'uploaded_by', 'uploaded_at', 'description', 'deleted_at',
  'folder_path', 'is_folder',
];

let currentSheet;

globalThis.getF2Spreadsheet = () => ({
  getSheetByName: (name) => (name === 'F2_FileMeta' ? currentSheet : null),
});
globalThis.LockService = {
  getScriptLock: () => ({ tryLock: () => true, releaseLock: () => {} }),
};
let uuidCounter = 0;
globalThis.generateUuid = () => `uuid-${++uuidCounter}`;

const AdminFiles = require('../src/AdminFiles.js');

/** Build a file/folder row in header order. */
function row(overrides) {
  const base = {
    file_id: 'f-x', filename: 'x.pdf', content_type: 'application/pdf',
    size_bytes: 10, uploaded_by: 'kidd_admin', uploaded_at: '2026-05-01T00:00:00Z',
    description: '', deleted_at: '', folder_path: '/', is_folder: false,
  };
  const merged = { ...base, ...overrides };
  return FILE_META_HEADERS.map((h) => merged[h]);
}

beforeEach(() => {
  uuidCounter = 0;
  currentSheet = new FakeSheet(FILE_META_HEADERS);
});

// ---- Pure helpers ----------------------------------------------------------

describe('AdminFiles pure helpers', () => {
  it('_extensionOf lowercases and handles missing/trailing dots', () => {
    expect(AdminFiles._extensionOf('a.PDF')).toBe('pdf');
    expect(AdminFiles._extensionOf('noext')).toBe('');
    expect(AdminFiles._extensionOf('trailing.')).toBe('');
    expect(AdminFiles._extensionOf('a.b.zip')).toBe('zip');
  });

  it('_validateFileExtension allows only the upload allowlist', () => {
    for (const ok of ['x.pdf', 'x.zip', 'x.png', 'x.jpg', 'x.jpeg', 'x.gif']) {
      expect(AdminFiles._validateFileExtension(ok)).toBe(true);
    }
    for (const bad of ['x.exe', 'x.svg', 'x.html', 'noext']) {
      expect(AdminFiles._validateFileExtension(bad)).toBe(false);
    }
  });

  it('_coalesceFolderPath treats blank/null as root', () => {
    expect(AdminFiles._coalesceFolderPath('')).toBe('/');
    expect(AdminFiles._coalesceFolderPath(null)).toBe('/');
    expect(AdminFiles._coalesceFolderPath(undefined)).toBe('/');
    expect(AdminFiles._coalesceFolderPath('/docs')).toBe('/docs');
  });

  it('_isFolderRow accepts boolean true and string "true"', () => {
    expect(AdminFiles._isFolderRow(true)).toBe(true);
    expect(AdminFiles._isFolderRow('true')).toBe(true);
    expect(AdminFiles._isFolderRow(false)).toBe(false);
    expect(AdminFiles._isFolderRow('')).toBe(false);
  });
});

// ---- adminFilesRename (#175) -----------------------------------------------

describe('adminFilesRename', () => {
  it('renames the filename, keeps file_id, returns the updated row', () => {
    currentSheet = new FakeSheet(FILE_META_HEADERS, [row({ file_id: 'f-1', filename: 'old.pdf' })]);
    const res = AdminFiles.adminFilesRename({ file_id: 'f-1', new_name: 'new.pdf' });
    expect(res.ok).toBe(true);
    expect(res.data.file.filename).toBe('new.pdf');
    expect(res.data.file.file_id).toBe('f-1');
    // The sheet cell was actually updated.
    expect(currentSheet.data[1][FILE_META_HEADERS.indexOf('filename')]).toBe('new.pdf');
  });

  it('rejects a blank new_name', () => {
    currentSheet = new FakeSheet(FILE_META_HEADERS, [row({ file_id: 'f-1' })]);
    const res = AdminFiles.adminFilesRename({ file_id: 'f-1', new_name: '   ' });
    expect(res.ok).toBe(false);
    expect(res.error.code).toBe('E_VALIDATION');
  });

  it('rejects path separators in new_name', () => {
    currentSheet = new FakeSheet(FILE_META_HEADERS, [row({ file_id: 'f-1' })]);
    expect(AdminFiles.adminFilesRename({ file_id: 'f-1', new_name: 'a/b.pdf' }).error.code).toBe('E_VALIDATION');
    expect(AdminFiles.adminFilesRename({ file_id: 'f-1', new_name: '..\\evil.pdf' }).error.code).toBe('E_VALIDATION');
  });

  it('rejects a disallowed extension', () => {
    currentSheet = new FakeSheet(FILE_META_HEADERS, [row({ file_id: 'f-1' })]);
    const res = AdminFiles.adminFilesRename({ file_id: 'f-1', new_name: 'payload.exe' });
    expect(res.ok).toBe(false);
    expect(res.error.code).toBe('E_VALIDATION');
  });

  it('refuses to rename a folder row', () => {
    currentSheet = new FakeSheet(FILE_META_HEADERS, [
      row({ file_id: 'd-1', filename: 'protocols', is_folder: true, content_type: 'application/x-directory' }),
    ]);
    const res = AdminFiles.adminFilesRename({ file_id: 'd-1', new_name: 'renamed.pdf' });
    expect(res.ok).toBe(false);
    expect(res.error.code).toBe('E_VALIDATION');
  });

  it('returns E_NOT_FOUND for unknown or soft-deleted file_id', () => {
    currentSheet = new FakeSheet(FILE_META_HEADERS, [
      row({ file_id: 'f-1', deleted_at: '2026-05-02T00:00:00Z' }),
    ]);
    expect(AdminFiles.adminFilesRename({ file_id: 'f-1', new_name: 'a.pdf' }).error.code).toBe('E_NOT_FOUND');
    expect(AdminFiles.adminFilesRename({ file_id: 'nope', new_name: 'a.pdf' }).error.code).toBe('E_NOT_FOUND');
  });
});

// ---- adminFilesCreateFolder (#174) -----------------------------------------

describe('adminFilesCreateFolder', () => {
  it('creates a folder row at root with is_folder=true', () => {
    const res = AdminFiles.adminFilesCreateFolder({ name: 'protocols', created_by: 'kidd_admin' });
    expect(res.ok).toBe(true);
    expect(res.data.folder.is_folder).toBe(true);
    expect(res.data.folder.folder_path).toBe('/');
    expect(res.data.folder.filename).toBe('protocols');
    expect(res.data.folder.uploaded_by).toBe('kidd_admin');
    // Appended to the sheet.
    expect(currentSheet.getLastRow()).toBe(2);
  });

  it('rejects a duplicate non-deleted folder name (E_CONFLICT)', () => {
    currentSheet = new FakeSheet(FILE_META_HEADERS, [
      row({ file_id: 'd-1', filename: 'protocols', is_folder: true }),
    ]);
    const res = AdminFiles.adminFilesCreateFolder({ name: 'protocols', created_by: 'kidd_admin' });
    expect(res.ok).toBe(false);
    expect(res.error.code).toBe('E_CONFLICT');
  });

  it('allows reusing the name of a soft-deleted folder', () => {
    currentSheet = new FakeSheet(FILE_META_HEADERS, [
      row({ file_id: 'd-1', filename: 'protocols', is_folder: true, deleted_at: '2026-05-02T00:00:00Z' }),
    ]);
    expect(AdminFiles.adminFilesCreateFolder({ name: 'protocols', created_by: 'x' }).ok).toBe(true);
  });

  it('rejects slashes, .. and over-long names', () => {
    expect(AdminFiles.adminFilesCreateFolder({ name: 'a/b' }).error.code).toBe('E_VALIDATION');
    expect(AdminFiles.adminFilesCreateFolder({ name: '..' }).error.code).toBe('E_VALIDATION');
    expect(AdminFiles.adminFilesCreateFolder({ name: '' }).error.code).toBe('E_VALIDATION');
    expect(AdminFiles.adminFilesCreateFolder({ name: 'x'.repeat(129) }).error.code).toBe('E_VALIDATION');
  });

  it('rejects non-ASCII / special-char names that the worker upload-path regex would later reject', () => {
    // Closes the create-vs-upload asymmetry: a folder the worker could never
    // accept an upload-path for must not be creatable in the first place.
    for (const bad of ['Niño', 'café', 'Q&A', 'Forms(2026)', '#tag', 'a\tb']) {
      expect(AdminFiles.adminFilesCreateFolder({ name: bad, created_by: 'x' }).error.code).toBe('E_VALIDATION');
    }
  });

  it('accepts ASCII names with spaces, dots, dashes, underscores', () => {
    expect(AdminFiles.adminFilesCreateFolder({ name: 'Field Ops v2.1_draft-A', created_by: 'x' }).ok).toBe(true);
  });

  it('returns E_NOT_CONFIGURED when the folder columns are absent', () => {
    // Pre-migration sheet: no folder_path / is_folder columns.
    currentSheet = new FakeSheet(FILE_META_HEADERS.slice(0, 8));
    const res = AdminFiles.adminFilesCreateFolder({ name: 'protocols', created_by: 'x' });
    expect(res.ok).toBe(false);
    expect(res.error.code).toBe('E_NOT_CONFIGURED');
  });
});

// ---- adminFilesList path scoping (#174) ------------------------------------

describe('adminFilesList path scoping', () => {
  beforeEach(() => {
    currentSheet = new FakeSheet(FILE_META_HEADERS, [
      row({ file_id: 'root-1', filename: 'rootdoc.pdf', folder_path: '/' }),
      row({ file_id: 'd-1', filename: 'protocols', is_folder: true, folder_path: '/' }),
      row({ file_id: 'in-1', filename: 'inner.pdf', folder_path: '/protocols' }),
      row({ file_id: 'legacy-1', filename: 'legacy.pdf', folder_path: '' }), // pre-migration blank
    ]);
  });

  it('root view shows root files + folders + coalesced-legacy, hides nested', () => {
    const res = AdminFiles.adminFilesList({});
    const ids = res.data.files.map((f) => f.file_id);
    expect(ids).toContain('root-1');
    expect(ids).toContain('d-1'); // folder lives at root
    expect(ids).toContain('legacy-1'); // blank folder_path coalesces to root
    expect(ids).not.toContain('in-1'); // nested, hidden at root
  });

  it("path='/protocols' shows only that folder's children", () => {
    const res = AdminFiles.adminFilesList({ path: '/protocols' });
    const ids = res.data.files.map((f) => f.file_id);
    expect(ids).toEqual(['in-1']);
  });

  it("path='/' is treated as root", () => {
    const res = AdminFiles.adminFilesList({ path: '/' });
    const ids = res.data.files.map((f) => f.file_id);
    expect(ids).toContain('root-1');
    expect(ids).not.toContain('in-1');
  });
});

// ---- adminFilesCreate folder defaults --------------------------------------

describe('adminFilesCreate folder defaults', () => {
  it('defaults folder_path to root and is_folder to false', () => {
    const res = AdminFiles.adminFilesCreate({
      file_id: 'f-1', filename: 'a.pdf', content_type: 'application/pdf',
      size_bytes: 5, uploaded_by: 'kidd_admin',
    });
    expect(res.ok).toBe(true);
    expect(res.data.file.folder_path).toBe('/');
    expect(res.data.file.is_folder).toBe(false);
  });

  it('honors an explicit valid folder_path', () => {
    const res = AdminFiles.adminFilesCreate({
      file_id: 'f-2', filename: 'b.pdf', content_type: 'application/pdf',
      size_bytes: 5, uploaded_by: 'kidd_admin', folder_path: '/protocols',
    });
    expect(res.data.file.folder_path).toBe('/protocols');
  });

  it('coerces a malformed folder_path to root (defense-in-depth)', () => {
    const res = AdminFiles.adminFilesCreate({
      file_id: 'f-3', filename: 'c.pdf', content_type: 'application/pdf',
      size_bytes: 5, uploaded_by: 'kidd_admin', folder_path: '/../etc',
    });
    expect(res.data.file.folder_path).toBe('/');
  });
});
