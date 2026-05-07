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
import { useEffect, useRef, useState } from 'react';
import { adminFetch, type ApiError } from '../lib/api-client';
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

interface FileRow {
  file_id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  uploaded_by: string;
  uploaded_at: string;
  description?: string;
  deleted_at?: string;
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
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    let cancelled = false;
    setState({ kind: 'loading' });
    void (async () => {
      const r = await adminFetch<ListFilesData>(
        `${apiBaseUrl}/admin/api/dashboards/apps/files`,
        {},
        {
          ...(token ? { token } : {}),
          onUnauthorized: () => {
            clearAuth();
            navigate('/admin/login');
          },
          ...(fetchImpl ? { fetchImpl } : {}),
        },
      );
      if (cancelled) return;
      if (r.ok) setState({ kind: 'loaded', data: r.data });
      else setState({ kind: 'failed', error: r.error });
    })();
    return () => {
      cancelled = true;
    };
  }, [apiBaseUrl, token, reloadTick]);

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
    // UAT R2 #92: warn before stacking duplicates. The backend doesn't dedupe
    // by filename (file_id is a UUID), so without this guard two files with
    // the same name end up in the list and admins can't tell them apart.
    if (state.kind === 'loaded' && state.data.files.some((row) => row.filename === file.name)) {
      setUploadError(
        `A file named "${file.name}" already exists. Rename it and try again, or delete the existing one first.`,
      );
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    setUploading(true);
    try {
      const form = new FormData();
      form.append('file', file);
      const r = await adminFetch<UploadResponse>(
        `${apiBaseUrl}/admin/api/dashboards/apps/files`,
        { method: 'POST', body: form },
        {
          ...(token ? { token } : {}),
          onUnauthorized: () => {
            clearAuth();
            navigate('/admin/login');
          },
          ...(fetchImpl ? { fetchImpl } : {}),
        },
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
      {
        ...(token ? { token } : {}),
        onUnauthorized: () => {
          clearAuth();
          navigate('/admin/login');
        },
        ...(fetchImpl ? { fetchImpl } : {}),
      },
    );
    if (r.ok) setReloadTick((n) => n + 1);
    else window.alert(friendlyError(r.error, 'Delete failed.'));
  }

  function downloadUrl(fileId: string): string {
    return `${apiBaseUrl}/admin/api/dashboards/apps/files/${encodeURIComponent(fileId)}`;
  }

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-baseline justify-between">
        <h3 className="font-serif text-lg font-medium tracking-tight">Files</h3>
        <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
          PDF / ZIP / PNG / JPEG / GIF, up to {formatBytes(MAX_FILE_BYTES)}
        </p>
      </div>

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
        <EmptyState />
      ) : (
        <FilesTable rows={state.data.files} downloadUrl={downloadUrl} onDelete={handleDelete} />
      )}
    </section>
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
  downloadUrl,
  onDelete,
}: {
  rows: FileRow[];
  downloadUrl: (id: string) => string;
  onDelete: (row: FileRow) => void | Promise<void>;
}): JSX.Element {
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
          {rows.map((r) => (
            <tr key={r.file_id}>
              <Td>
                {/* FX-013 (2026-05-03): `download` attr is defense-in-depth; the
                    worker already sets Content-Disposition: attachment, but
                    listing `download` here makes the save-dialog deterministic
                    across browsers and surfaces the filename in the prompt. */}
                <a
                  href={downloadUrl(r.file_id)}
                  download={r.filename}
                  className="underline decoration-hairline underline-offset-4 hover:decoration-foreground"
                >
                  {r.filename}
                </a>
              </Td>
              <Td mono>{r.content_type}</Td>
              <Td mono>{formatBytes(r.size_bytes)}</Td>
              <Td mono>{r.uploaded_by}</Td>
              <Td mono>{formatTs(r.uploaded_at)}</Td>
              <Td>
                <div className="flex flex-wrap gap-3">
                  {/* UAT R2 #91: explicit Download action so admins don't
                      have to discover that the filename column is a download
                      link. The href + download attr below mirror the column
                      link so server semantics stay identical. */}
                  <a
                    href={downloadUrl(r.file_id)}
                    download={r.filename}
                    className="font-mono text-xs uppercase tracking-wider text-muted-foreground underline-offset-4 hover:text-ink hover:underline"
                  >
                    Download
                  </a>
                  <button
                    type="button"
                    onClick={() => void onDelete(r)}
                    className="font-mono text-xs uppercase tracking-wider text-muted-foreground hover:text-error"
                  >
                    Delete
                  </button>
                </div>
              </Td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function EmptyState(): JSX.Element {
  return (
    <div className="border border-hairline bg-secondary/20 px-4 py-4">
      <p className="text-sm text-muted-foreground">
        No files uploaded yet. Reference documents (PDF protocols, training packets, ZIP exports)
        live here. Uploads are streamed to R2 with the original filename preserved on download.
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
