/**
 * F2 Admin Portal - Files panel.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 3.7)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (sec 7.9)
 *
 * Lists non-deleted F2_FileMeta rows with size + uploader; lets Admins
 * upload via file picker (multipart), download (always-attachment), and
 * soft-delete. Allowlist + size cap mirror the worker; we re-validate
 * client-side to give immediate feedback before paying the round trip.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { adminFetch, type AdminFetchOptions, type ApiError } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { useRouter } from '../lib/pages-router';

const ALLOWED_MIME = new Set([
  'application/pdf',
  'application/zip',
  'application/octet-stream',
  'image/png',
  'image/jpeg',
  'image/gif',
]);

const MAX_FILE_BYTES = 100 * 1024 * 1024;

// #174: folder-name charset — MUST mirror the worker apps.ts FOLDER_NAME_RE
// and the AS AdminFiles.js validator. ASCII letters/digits/space/. _ -, no
// '..', length 1–128.
const FOLDER_NAME_RE = /^(?!.*\.\.)[A-Za-z0-9 _\-.]{1,128}$/;

interface FileRow {
  file_id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  uploaded_by: string;
  uploaded_at: string;
  description?: string;
  deleted_at?: string;
  // #174 folders: is_folder marks a virtual folder row; folder_path is the
  // container it lives in ('/' = root).
  is_folder?: boolean;
  folder_path?: string;
}

interface ListFilesData {
  files: FileRow[];
  total: number;
}

interface UploadResponse {
  file: FileRow;
}

export interface FilesProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
}

type ListState =
  | { kind: 'loading' }
  | { kind: 'loaded'; data: ListFilesData }
  | { kind: 'failed'; error: ApiError };

export function Files({ apiBaseUrl, fetchImpl }: FilesProps): JSX.Element {
  const { token, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();
  const [state, setState] = useState<ListState>({ kind: 'loading' });
  const [reloadTick, setReloadTick] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  // #315: id of the row whose download is in flight (authenticated blob fetch).
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // #174: current virtual-folder path. '' = root; '/<name>' = inside a folder.
  const [path, setPath] = useState('');
  const [folderForm, setFolderForm] = useState<string | null>(null); // null = closed
  const [folderError, setFolderError] = useState<string | null>(null);
  const [creatingFolder, setCreatingFolder] = useState(false);

  // #175: inline rename — at most one row editable at a time.
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');
  const [renaming, setRenaming] = useState(false);

  // DRY auth options — call sites grew from 3 to ~6 with rename + folders.
  const authOpts = useCallback((): AdminFetchOptions => ({
    ...(token ? { token } : {}),
    onUnauthorized: () => { clearAuth(); navigate('/admin/login'); },
    onPasswordChangeRequired: () => navigate('/admin/me/change-password'),
    ...(fetchImpl ? { fetchImpl } : {}),
  }), [token, clearAuth, navigate, fetchImpl]);

  useEffect(() => {
    let cancelled = false;
    setState({ kind: 'loading' });
    void (async () => {
      const qs = path ? `?path=${encodeURIComponent(path)}` : '';
      const r = await adminFetch<ListFilesData>(
        `${apiBaseUrl}/admin/api/dashboards/apps/files${qs}`,
        {},
        authOpts(),
      );
      if (cancelled) return;
      if (r.ok) setState({ kind: 'loaded', data: r.data });
      else setState({ kind: 'failed', error: r.error });
    })();
    return () => {
      cancelled = true;
    };
  }, [apiBaseUrl, reloadTick, path, authOpts]);

  async function handleUpload(file: File): Promise<void> {
    setUploadError(null);
    if (file.size > MAX_FILE_BYTES) {
      setUploadError(`File exceeds ${formatBytes(MAX_FILE_BYTES)} limit.`);
      return;
    }
    const mime = file.type || 'application/octet-stream';
    if (!ALLOWED_MIME.has(mime)) {
      setUploadError(`MIME type ${mime} not allowed. Allowed: PDF, ZIP, PNG, JPEG, GIF.`);
      return;
    }

    setUploading(true);
    try {
      const form = new FormData();
      form.append('file', file);
      // #174: land the file in the open folder (omit at root).
      if (path) form.append('path', path);
      const r = await adminFetch<UploadResponse>(
        `${apiBaseUrl}/admin/api/dashboards/apps/files`,
        { method: 'POST', body: form },
        authOpts(),
      );
      if (r.ok) {
        setReloadTick((n) => n + 1);
        if (fileInputRef.current) fileInputRef.current.value = '';
      } else {
        setUploadError(friendlyError(r.error, 'Upload failed.'));
      }
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(row: FileRow): Promise<void> {
    if (!window.confirm(`Delete ${row.filename}?`)) return;
    const r = await adminFetch<undefined>(
      `${apiBaseUrl}/admin/api/dashboards/apps/files/${encodeURIComponent(row.file_id)}`,
      { method: 'DELETE' },
      authOpts(),
    );
    if (r.ok) setReloadTick((n) => n + 1);
    else window.alert(friendlyError(r.error, 'Delete failed.'));
  }

  // #174: create a folder (flat 1-level — always at root).
  async function handleCreateFolder(e: React.FormEvent): Promise<void> {
    e.preventDefault();
    const name = (folderForm ?? '').trim();
    setFolderError(null);
    if (!name) {
      setFolderError('Folder name required.');
      return;
    }
    // Mirror the worker/AS FOLDER_NAME_RE so the user gets immediate feedback
    // instead of a generic server 400 (ASCII letters/digits/space/. _ -, no ..).
    if (!FOLDER_NAME_RE.test(name)) {
      setFolderError('Use letters, numbers, spaces, and . _ - only (no slashes or "..", max 128).');
      return;
    }
    setCreatingFolder(true);
    try {
      const r = await adminFetch<{ folder: FileRow }>(
        `${apiBaseUrl}/admin/api/dashboards/apps/files/folders`,
        { method: 'POST', body: JSON.stringify({ name }) },
        authOpts(),
      );
      if (r.ok) {
        setFolderForm(null);
        setReloadTick((n) => n + 1);
      } else {
        setFolderError(friendlyError(r.error, 'Create folder failed.'));
      }
    } finally {
      setCreatingFolder(false);
    }
  }

  // #175: inline rename.
  function startRename(row: FileRow): void {
    setEditingId(row.file_id);
    setEditValue(row.filename);
  }
  function cancelRename(): void {
    setEditingId(null);
    setEditValue('');
  }
  async function commitRename(row: FileRow): Promise<void> {
    const next = editValue.trim();
    if (!next || next === row.filename) {
      cancelRename();
      return;
    }
    setRenaming(true);
    try {
      const r = await adminFetch<{ file: FileRow }>(
        `${apiBaseUrl}/admin/api/dashboards/apps/files/${encodeURIComponent(row.file_id)}`,
        { method: 'PATCH', body: JSON.stringify({ filename: next }) },
        authOpts(),
      );
      if (r.ok) {
        cancelRename();
        setReloadTick((n) => n + 1);
      } else {
        window.alert(friendlyError(r.error, 'Rename failed.'));
      }
    } finally {
      setRenaming(false);
    }
  }

  function openFolder(row: FileRow): void {
    // The folder's child container path is '/' + its display name.
    cancelRename();
    setPath(`/${row.filename}`);
  }
  function goToRoot(): void {
    cancelRename();
    setPath('');
  }

  function downloadUrl(fileId: string): string {
    return `${apiBaseUrl}/admin/api/dashboards/apps/files/${encodeURIComponent(fileId)}`;
  }

  // #315: the file download MUST be an authenticated fetch, not a plain
  // <a href> navigation. The admin JWT lives in memory only and is sent
  // exclusively via the Authorization header; a bare anchor click carries no
  // header, so the worker rejected every download with 401 and the error JSON
  // ("access denied") was what got saved as the "file". Fetch the bytes with
  // the token, then trigger a client-side save from the resulting blob.
  async function handleDownload(row: FileRow): Promise<void> {
    setDownloadingId(row.file_id);
    try {
      const fetchFn = fetchImpl ?? fetch;
      let resp: Response;
      try {
        resp = await fetchFn(downloadUrl(row.file_id), {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
      } catch {
        window.alert('Network unavailable. Try the download again.');
        return;
      }
      if (resp.status === 401) {
        clearAuth();
        navigate('/admin/login');
        return;
      }
      if (!resp.ok) {
        // Error responses are JSON envelopes; a successful download is raw bytes.
        let message = `Download failed (HTTP ${resp.status}).`;
        try {
          const env = (await resp.json()) as { error?: { code?: string; message?: string } };
          if (env?.error?.code === 'E_PASSWORD_CHANGE_REQUIRED') {
            navigate('/admin/me/change-password');
            return;
          }
          if (env?.error?.message) message = env.error.message;
        } catch {
          // Non-JSON error body — keep the generic message.
        }
        window.alert(message);
        return;
      }
      const blob = await resp.blob();
      const objectUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = objectUrl;
      a.download = row.filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(objectUrl);
    } finally {
      setDownloadingId(null);
    }
  }

  const atRoot = path === '';

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-baseline justify-between">
        <h3 className="font-serif text-lg font-medium tracking-tight">Files</h3>
        <div className="flex items-baseline gap-4">
          {atRoot ? (
            <Button
              type="button"
              variant="tableAction"
              size="tableAction"
              onClick={() => {
                setFolderForm(folderForm === null ? '' : null);
                setFolderError(null);
              }}
              className="text-muted-foreground no-underline hover:text-foreground hover:no-underline"
            >
              {folderForm === null ? '+ New folder' : 'Cancel'}
            </Button>
          ) : null}
          <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
            PDF / ZIP / PNG / JPEG / GIF, up to {formatBytes(MAX_FILE_BYTES)}
          </p>
        </div>
      </div>

      <Breadcrumb path={path} onRoot={goToRoot} />

      {folderForm !== null ? (
        <FolderForm
          value={folderForm}
          creating={creatingFolder}
          error={folderError}
          onChange={setFolderForm}
          onSubmit={handleCreateFolder}
        />
      ) : null}

      <UploadRow
        uploading={uploading}
        error={uploadError}
        fileInputRef={fileInputRef}
        onPick={handleUpload}
      />

      {state.kind === 'loading' ? (
        <p className="text-sm text-muted-foreground">Loading...</p>
      ) : state.kind === 'failed' ? (
        <ErrorBanner error={state.error} />
      ) : state.data.files.length === 0 ? (
        <EmptyState atRoot={atRoot} />
      ) : (
        <FilesTable
          rows={state.data.files}
          onDownload={handleDownload}
          downloadingId={downloadingId}
          onDelete={handleDelete}
          onOpenFolder={openFolder}
          editingId={editingId}
          editValue={editValue}
          renaming={renaming}
          onStartRename={startRename}
          onRenameChange={setEditValue}
          onCommitRename={commitRename}
          onCancelRename={cancelRename}
        />
      )}
    </section>
  );
}

function Breadcrumb({ path, onRoot }: { path: string; onRoot: () => void }): JSX.Element {
  const inFolder = path !== '';
  const folderName = inFolder ? path.replace(/^\//, '') : '';
  return (
    <nav
      aria-label="Folder path"
      className="flex items-center gap-1 font-mono text-[10px] uppercase tracking-wider text-muted-foreground"
    >
      <button
        type="button"
        onClick={onRoot}
        disabled={!inFolder}
        className={
          inFolder
            ? 'underline decoration-hairline underline-offset-4 hover:decoration-foreground'
            : 'cursor-default'
        }
      >
        Files
      </button>
      {inFolder ? (
        <>
          <span aria-hidden="true">/</span>
          <span className="text-foreground">{folderName}</span>
        </>
      ) : null}
    </nav>
  );
}

function FolderForm({
  value,
  creating,
  error,
  onChange,
  onSubmit,
}: {
  value: string;
  creating: boolean;
  error: string | null;
  onChange: (v: string) => void;
  onSubmit: (e: React.FormEvent) => void | Promise<void>;
}): JSX.Element {
  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-2 border-l-2 border-hairline pl-4">
      <label className="flex flex-col gap-1">
        <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
          Folder name
        </span>
        <input
          type="text"
          autoFocus
          maxLength={128}
          value={value}
          disabled={creating}
          onChange={(e) => onChange(e.target.value)}
          className="border-b border-hairline bg-transparent px-1 py-0.5 font-mono text-xs"
          aria-label="New folder name"
        />
      </label>
      {error ? (
        <p role="alert" className="text-sm text-error">
          {error}
        </p>
      ) : null}
      <div className="flex gap-3">
        <Button
          type="submit"
          variant="outline"
          disabled={creating}
          className="border-foreground px-3 py-1 font-mono text-xs uppercase tracking-wider hover:bg-foreground hover:text-background disabled:opacity-50"
        >
          {creating ? 'Creating…' : 'Create'}
        </Button>
      </div>
    </form>
  );
}

// FX-009 (2026-05-03): keep this allowlist in sync with ALLOWED_MIME above
// and the worker's apps.ts ALLOWED_MIME. Browsers honor `accept` as a hint
// (filters the OS picker by default) so it doesn't replace server-side
// validation but does close the UX gap where users could pick anything.
const ACCEPT_ATTR =
  '.pdf,.zip,.png,.jpg,.jpeg,.gif,application/pdf,application/zip,image/png,image/jpeg,image/gif';

function UploadRow({
  uploading,
  error,
  fileInputRef,
  onPick,
}: {
  uploading: boolean;
  error: string | null;
  fileInputRef: React.MutableRefObject<HTMLInputElement | null>;
  onPick: (file: File) => void | Promise<void>;
}): JSX.Element {
  // FX-010 (2026-05-03): drag-and-drop support so admins can drop a file
  // onto the upload zone instead of clicking through the OS picker. The
  // existing click-to-pick path still works; drag-drop is additive.
  const [dragActive, setDragActive] = useState(false);
  const dragDepth = useRef(0);

  function handleDragEnter(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    e.stopPropagation();
    if (uploading) return;
    dragDepth.current += 1;
    setDragActive(true);
  }

  function handleDragLeave(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    e.stopPropagation();
    dragDepth.current -= 1;
    if (dragDepth.current <= 0) {
      dragDepth.current = 0;
      setDragActive(false);
    }
  }

  function handleDragOver(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    e.stopPropagation();
    if (!uploading) e.dataTransfer.dropEffect = 'copy';
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    e.stopPropagation();
    dragDepth.current = 0;
    setDragActive(false);
    if (uploading) return;
    const f = e.dataTransfer.files?.[0];
    if (f) void onPick(f);
  }

  return (
    <div
      className={
        'flex flex-col gap-2 border-l-2 pl-4 transition-colors ' +
        (dragActive ? 'border-signal bg-secondary/20' : 'border-hairline')
      }
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <div className="flex items-center gap-3">
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPT_ATTR}
          disabled={uploading}
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) void onPick(f);
          }}
          className="text-sm"
        />
        <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
          {uploading ? 'Uploading…' : dragActive ? 'Drop to upload' : 'Or drop a file here'}
        </span>
      </div>
      {error ? (
        <p role="alert" className="text-sm text-error">
          {error}
        </p>
      ) : null}
    </div>
  );
}

function FilesTable({
  rows,
  onDownload,
  downloadingId,
  onDelete,
  onOpenFolder,
  editingId,
  editValue,
  renaming,
  onStartRename,
  onRenameChange,
  onCommitRename,
  onCancelRename,
}: {
  rows: FileRow[];
  onDownload: (row: FileRow) => void | Promise<void>;
  downloadingId: string | null;
  onDelete: (row: FileRow) => void | Promise<void>;
  onOpenFolder: (row: FileRow) => void;
  editingId: string | null;
  editValue: string;
  renaming: boolean;
  onStartRename: (row: FileRow) => void;
  onRenameChange: (v: string) => void;
  onCommitRename: (row: FileRow) => void | Promise<void>;
  onCancelRename: () => void;
}): JSX.Element {
  // #174: folders render first (a directory-listing convention), then files.
  const folders = rows.filter((r) => r.is_folder);
  const files = rows.filter((r) => !r.is_folder);
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="border-b border-hairline text-left">
          <tr>
            <Th>Filename</Th>
            <Th>Type</Th>
            <Th>Size</Th>
            <Th>Uploaded by</Th>
            <Th>Uploaded</Th>
            <Th>{''}</Th>
          </tr>
        </thead>
        <tbody className="divide-y divide-hairline">
          {folders.map((r) => (
            <tr key={r.file_id} className="hover:bg-secondary/20">
              <Td>
                <button
                  type="button"
                  onClick={() => onOpenFolder(r)}
                  className="flex items-center gap-2 text-left hover:text-foreground"
                >
                  <span aria-hidden="true" className="font-mono text-muted-foreground">
                    [dir]
                  </span>
                  <span className="underline decoration-hairline underline-offset-4 hover:decoration-foreground">
                    {r.filename}
                  </span>
                </button>
              </Td>
              <Td mono>folder</Td>
              <Td mono>—</Td>
              <Td mono>{r.uploaded_by}</Td>
              <Td mono>{formatTs(r.uploaded_at)}</Td>
              <Td>{''}</Td>
            </tr>
          ))}
          {files.map((r) => (
            <tr key={r.file_id}>
              <Td>
                {editingId === r.file_id ? (
                  // #175: inline rename — Enter commits, Esc/blur cancels.
                  <input
                    autoFocus
                    type="text"
                    value={editValue}
                    disabled={renaming}
                    onChange={(e) => onRenameChange(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        void onCommitRename(r);
                      }
                      if (e.key === 'Escape') {
                        e.preventDefault();
                        onCancelRename();
                      }
                    }}
                    onBlur={() => {
                      // Click-away cancels, but the disable-on-commit transition
                      // also fires blur — don't cancel mid-PATCH (renaming=true).
                      if (!renaming) onCancelRename();
                    }}
                    className="w-full border-b border-hairline bg-transparent px-1 py-0.5 font-mono text-xs"
                    aria-label={`Rename ${r.filename}`}
                  />
                ) : (
                  <>
                    {/* #315: download goes through handleDownload (authenticated
                        blob fetch). A plain <a href> cannot send the in-memory
                        admin JWT, so the bare GET 401'd and the error JSON was
                        saved as the "file". This button is the action trigger. */}
                    <button
                      type="button"
                      onClick={() => void onDownload(r)}
                      disabled={downloadingId === r.file_id}
                      className="text-left underline decoration-hairline underline-offset-4 hover:decoration-foreground disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {r.filename}
                    </button>
                    {downloadingId === r.file_id ? (
                      <span className="ml-2 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                        Downloading…
                      </span>
                    ) : null}
                  </>
                )}
              </Td>
              <Td mono>{r.content_type}</Td>
              <Td mono>{formatBytes(r.size_bytes)}</Td>
              <Td mono>{r.uploaded_by}</Td>
              <Td mono>{formatTs(r.uploaded_at)}</Td>
              <Td>
                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant="tableAction"
                    size="tableAction"
                    disabled={editingId === r.file_id}
                    onClick={() => onStartRename(r)}
                    className="text-muted-foreground no-underline hover:text-foreground hover:no-underline disabled:opacity-40"
                  >
                    Rename
                  </Button>
                  <Button
                    type="button"
                    variant="tableAction"
                    size="tableAction"
                    onClick={() => void onDelete(r)}
                    className="text-muted-foreground no-underline hover:text-error hover:no-underline"
                  >
                    Delete
                  </Button>
                </div>
              </Td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function EmptyState({ atRoot }: { atRoot: boolean }): JSX.Element {
  return (
    <div className="border border-hairline bg-secondary/20 px-4 py-4">
      <p className="text-sm text-muted-foreground">
        {atRoot
          ? 'No files uploaded yet. Reference documents (PDF protocols, training packets, ZIP exports) live here. Uploads are streamed to R2 with the original filename preserved on download.'
          : 'This folder is empty. Drop a file above to add it here.'}
      </p>
    </div>
  );
}

function Th({ children }: { children?: React.ReactNode }): JSX.Element {
  return (
    <th className="px-3 py-2 font-mono text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
      {children}
    </th>
  );
}

function Td({
  children,
  mono = false,
}: {
  children?: React.ReactNode;
  mono?: boolean;
}): JSX.Element {
  return <td className={`px-3 py-2 align-top ${mono ? 'font-mono text-xs' : ''}`}>{children}</td>;
}

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  if (n < 1024 * 1024 * 1024) return `${(n / (1024 * 1024)).toFixed(1)} MB`;
  return `${(n / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

function formatTs(iso: string): string {
  if (!iso) return '-';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function friendlyError(err: ApiError, fallback: string): string {
  if (err.code === 'E_PERM_DENIED') return 'Your role lacks dash_apps. Contact an Administrator.';
  if (err.code === 'E_NETWORK') return 'Network unavailable. Try again.';
  if (err.code === 'E_BACKEND')
    return 'Backend unavailable - Apps Script staging may be unreachable.';
  if (err.code === 'E_NOT_CONFIGURED')
    return 'File storage is not configured for this environment. Files require R2 to be enabled.';
  if (err.code === 'E_CONFLICT') return err.message || 'A folder with that name already exists.';
  return err.message || fallback;
}

function ErrorBanner({ error }: { error: ApiError }): JSX.Element {
  return (
    <div role="alert" className="border-l-2 border-error bg-secondary/30 px-3 py-2">
      <p className="text-sm text-error">{friendlyError(error, 'Failed to load files.')}</p>
      {error.requestId ? (
        <p className="mt-1 font-mono text-xs text-muted-foreground">ref {error.requestId}</p>
      ) : null}
    </div>
  );
}
