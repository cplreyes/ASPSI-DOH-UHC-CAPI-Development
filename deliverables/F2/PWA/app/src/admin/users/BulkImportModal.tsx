/**
 * F2 Admin Portal — Users bulk import (R2-#98).
 *
 * UAT R2 tester reported: "Bulk Import not visible." Pre-fix the Users
 * dashboard had no bulk path — only the single-user editor. This modal
 * adds CSV upload + client-side preview (valid vs rejected rows) +
 * confirm + per-row results matching the U.A2 spec ("preview UI shows
 * valid rows + rejection reasons for invalid; confirm only valid rows
 * import").
 *
 * CSV format (first row = headers):
 *   username,password,role_name,first_name,last_name,email,phone
 * Required: username, password, role_name. Optional: first_name,
 * last_name, email, phone.
 */
import { useState } from 'react';
import { adminFetch } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { useRouter } from '../lib/pages-router';

interface ParsedRow {
  rowIndex: number; // 1-based, excluding header
  username: string;
  password: string;
  role_name: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
}

interface ValidationError {
  rowIndex: number;
  message: string;
}

interface ImportResultRow {
  username: string;
  status: 'created' | 'rejected';
  error?: { code: string; message: string };
}

interface ImportResult {
  results: ImportResultRow[];
  total: number;
  created: number;
  rejected: number;
}

const REQUIRED_HEADERS = ['username', 'password', 'role_name'] as const;
const OPTIONAL_HEADERS = ['first_name', 'last_name', 'email', 'phone'] as const;
const USERNAME_RE = /^[A-Za-z0-9_]{3,32}$/;

interface BulkImportModalProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
  onClose: () => void;
  onImported: () => void;
}

export function BulkImportModal({
  apiBaseUrl,
  fetchImpl,
  onClose,
  onImported,
}: BulkImportModalProps): JSX.Element {
  const { token, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();
  const [phase, setPhase] = useState<'upload' | 'preview' | 'submitting' | 'done'>('upload');
  const [parsedRows, setParsedRows] = useState<ParsedRow[]>([]);
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
  const [parseError, setParseError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);

  const handleFile = async (file: File) => {
    setParseError(null);
    setValidationErrors([]);
    setParsedRows([]);
    let text: string;
    try {
      text = await file.text();
    } catch (e) {
      setParseError(`Failed to read file: ${(e as Error).message}`);
      return;
    }
    const { rows, errors, parseError: pe } = parseCsv(text);
    if (pe) {
      setParseError(pe);
      return;
    }
    setParsedRows(rows);
    setValidationErrors(errors);
    setPhase('preview');
  };

  const validRows = parsedRows.filter(
    (r) => !validationErrors.some((e) => e.rowIndex === r.rowIndex),
  );

  const handleSubmit = async () => {
    if (validRows.length === 0) {
      setSubmitError('No valid rows to import.');
      return;
    }
    setPhase('submitting');
    setSubmitError(null);
    const r = await adminFetch<ImportResult>(
      `${apiBaseUrl}/admin/api/dashboards/users/bulk-import`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rows: validRows }),
      },
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
      setImportResult(r.data);
      setPhase('done');
      if (r.data.created > 0) onImported();
    } else {
      setSubmitError(`Import failed: ${r.error.message ?? r.error.code}`);
      setPhase('preview');
    }
  };

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4"
      role="dialog"
      aria-modal="true"
      aria-label="Bulk import users"
    >
      <div className="w-full max-w-3xl border border-hairline bg-background p-6 shadow-lg">
        <div className="flex items-start justify-between border-b border-hairline pb-3">
          <div>
            <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
              Users
            </p>
            <h3 className="mt-1 font-serif text-xl font-medium tracking-tight">Bulk import</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="font-mono text-xs uppercase tracking-wider text-muted-foreground underline-offset-4 hover:text-ink hover:underline"
          >
            Close
          </button>
        </div>

        {phase === 'upload' ? (
          <div className="flex flex-col gap-4 pt-4">
            <p className="text-sm text-muted-foreground">
              CSV with headers: <code className="font-mono text-xs">username,password,role_name</code>{' '}
              (required) and{' '}
              <code className="font-mono text-xs">first_name,last_name,email,phone</code> (optional).
              Max 100 rows. All imported users get{' '}
              <code className="font-mono text-xs">password_must_change=true</code> — they're forced to
              rotate the password on first login.
            </p>
            <label className="flex flex-col gap-1">
              <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
                CSV file
              </span>
              <input
                type="file"
                accept=".csv,text/csv"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) void handleFile(f);
                }}
                className="text-sm"
                aria-label="CSV file"
              />
            </label>
            {parseError ? (
              <p role="alert" className="border-l-2 border-error bg-secondary/30 px-3 py-2 text-sm text-error">
                {parseError}
              </p>
            ) : null}
          </div>
        ) : phase === 'preview' ? (
          <div className="flex flex-col gap-4 pt-4">
            <div className="grid grid-cols-3 gap-3 border border-hairline p-3 text-sm">
              <Stat label="Total rows" value={parsedRows.length} />
              <Stat label="Valid" value={validRows.length} tone="ok" />
              <Stat label="Rejected" value={validationErrors.length} tone="err" />
            </div>

            {validationErrors.length > 0 ? (
              <details className="border border-hairline">
                <summary className="cursor-pointer px-3 py-2 font-mono text-xs uppercase tracking-wider text-error">
                  {validationErrors.length} rejected row{validationErrors.length === 1 ? '' : 's'} — click to expand
                </summary>
                <ul className="border-t border-hairline px-3 py-2 text-xs">
                  {validationErrors.map((e, i) => (
                    <li key={i} className="font-mono">
                      Row {e.rowIndex}: {e.message}
                    </li>
                  ))}
                </ul>
              </details>
            ) : null}

            {validRows.length > 0 ? (
              <details className="border border-hairline" open>
                <summary className="cursor-pointer px-3 py-2 font-mono text-xs uppercase tracking-wider text-primary">
                  {validRows.length} valid row{validRows.length === 1 ? '' : 's'} ready to import
                </summary>
                <div className="overflow-x-auto border-t border-hairline">
                  <table className="w-full text-xs">
                    <thead className="border-b border-hairline text-left">
                      <tr>
                        <Th>#</Th>
                        <Th>Username</Th>
                        <Th>Role</Th>
                        <Th>Name</Th>
                        <Th>Email</Th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-hairline">
                      {validRows.slice(0, 50).map((r) => (
                        <tr key={r.rowIndex}>
                          <Td>{r.rowIndex}</Td>
                          <Td mono>{r.username}</Td>
                          <Td mono>{r.role_name}</Td>
                          <Td>
                            {[r.first_name, r.last_name].filter(Boolean).join(' ') || '—'}
                          </Td>
                          <Td>{r.email || '—'}</Td>
                        </tr>
                      ))}
                      {validRows.length > 50 ? (
                        <tr>
                          <Td>…</Td>
                          <Td mono>(+{validRows.length - 50} more not shown)</Td>
                          <Td />
                          <Td />
                          <Td />
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </details>
            ) : null}

            {submitError ? (
              <p role="alert" className="border-l-2 border-error bg-secondary/30 px-3 py-2 text-sm text-error">
                {submitError}
              </p>
            ) : null}

            <div className="flex justify-end gap-3 border-t border-hairline pt-3">
              <button
                type="button"
                onClick={() => setPhase('upload')}
                className="font-mono text-xs uppercase tracking-wider text-muted-foreground underline-offset-4 hover:text-ink hover:underline"
              >
                Back
              </button>
              <button
                type="button"
                disabled={validRows.length === 0}
                onClick={() => void handleSubmit()}
                className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                Import {validRows.length} row{validRows.length === 1 ? '' : 's'}
              </button>
            </div>
          </div>
        ) : phase === 'submitting' ? (
          <p className="pt-6 text-sm text-muted-foreground">Importing… please wait.</p>
        ) : phase === 'done' && importResult ? (
          <div className="flex flex-col gap-4 pt-4">
            <div className="grid grid-cols-3 gap-3 border border-hairline p-3 text-sm">
              <Stat label="Total submitted" value={importResult.total} />
              <Stat label="Created" value={importResult.created} tone="ok" />
              <Stat label="Rejected" value={importResult.rejected} tone="err" />
            </div>
            {importResult.rejected > 0 ? (
              <details open className="border border-hairline">
                <summary className="cursor-pointer px-3 py-2 font-mono text-xs uppercase tracking-wider text-error">
                  Rejected rows
                </summary>
                <ul className="border-t border-hairline px-3 py-2 text-xs">
                  {importResult.results
                    .filter((r) => r.status === 'rejected')
                    .map((r, i) => (
                      <li key={i} className="font-mono">
                        {r.username}: {r.error?.message ?? r.error?.code ?? 'unknown'}
                      </li>
                    ))}
                </ul>
              </details>
            ) : null}
            <div className="flex justify-end border-t border-hairline pt-3">
              <button
                type="button"
                onClick={onClose}
                className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90"
              >
                Done
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: number; tone?: 'ok' | 'err' }): JSX.Element {
  const color =
    tone === 'ok'
      ? 'text-primary'
      : tone === 'err'
        ? 'text-error'
        : 'text-foreground';
  return (
    <div className="flex flex-col">
      <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      <span className={`mt-1 font-serif text-2xl ${color}`}>{value}</span>
    </div>
  );
}

function Th({ children }: { children?: React.ReactNode }): JSX.Element {
  return (
    <th className="px-2 py-1.5 font-mono text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
      {children}
    </th>
  );
}

function Td({ children, mono = false }: { children?: React.ReactNode; mono?: boolean }): JSX.Element {
  return <td className={`px-2 py-1.5 align-top ${mono ? 'font-mono text-xs' : ''}`}>{children}</td>;
}

/**
 * Parse a CSV string. Supports double-quoted fields (with embedded commas
 * + escaped double-quotes via `""`) and CRLF or LF line endings. Returns
 * parsed rows + per-row validation errors so the caller can render a
 * preview before submitting.
 *
 * The R2-#98 spec is "preview UI shows valid rows + rejection reasons
 * for invalid", so the parser should NOT throw on a per-row error — it
 * should collect them and let the UI surface them in the preview.
 */
export function parseCsv(text: string): {
  rows: ParsedRow[];
  errors: ValidationError[];
  parseError: string | null;
} {
  const lines = splitCsvLines(text);
  if (lines.length === 0) {
    return { rows: [], errors: [], parseError: 'CSV file is empty' };
  }
  const headers = parseCsvLine(lines[0]!).map((h) => h.trim().toLowerCase());
  for (const required of REQUIRED_HEADERS) {
    if (!headers.includes(required)) {
      return {
        rows: [],
        errors: [],
        parseError: `Missing required header: ${required}`,
      };
    }
  }
  const headerIdx: Record<string, number> = {};
  headers.forEach((h, i) => {
    headerIdx[h] = i;
  });

  const rows: ParsedRow[] = [];
  const errors: ValidationError[] = [];

  for (let i = 1; i < lines.length; i++) {
    const raw = lines[i]!;
    if (raw.trim().length === 0) continue;
    const fields = parseCsvLine(raw);
    const rowIndex = i; // 1-based excl header
    const get = (key: string) => {
      const idx = headerIdx[key];
      return idx === undefined ? '' : (fields[idx] ?? '').trim();
    };
    const row: ParsedRow = {
      rowIndex,
      username: get('username'),
      password: get('password'),
      role_name: get('role_name'),
    };
    for (const opt of OPTIONAL_HEADERS) {
      const v = get(opt);
      if (v) row[opt] = v;
    }

    if (!USERNAME_RE.test(row.username)) {
      errors.push({
        rowIndex,
        message: `username "${row.username}" must be 3-32 chars [A-Za-z0-9_]`,
      });
    }
    if (row.password.length < 8) {
      errors.push({
        rowIndex,
        message: 'password must be at least 8 characters',
      });
    }
    if (!row.role_name) {
      errors.push({ rowIndex, message: 'role_name required' });
    }
    rows.push(row);
  }

  return { rows, errors, parseError: null };
}

function splitCsvLines(text: string): string[] {
  // Preserve quoted newlines: count quotes, only split when quote-balanced.
  const out: string[] = [];
  let buf = '';
  let inQuote = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (ch === '"') {
      // toggle (but skip-pair if escaped "")
      if (inQuote && text[i + 1] === '"') {
        buf += '""';
        i++;
        continue;
      }
      inQuote = !inQuote;
      buf += ch;
      continue;
    }
    if ((ch === '\n' || ch === '\r') && !inQuote) {
      // CRLF: skip following \n
      if (ch === '\r' && text[i + 1] === '\n') i++;
      out.push(buf);
      buf = '';
      continue;
    }
    buf += ch;
  }
  if (buf.length > 0) out.push(buf);
  return out;
}

function parseCsvLine(line: string): string[] {
  const out: string[] = [];
  let buf = '';
  let inQuote = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuote && line[i + 1] === '"') {
        buf += '"';
        i++;
        continue;
      }
      inQuote = !inQuote;
      continue;
    }
    if (ch === ',' && !inQuote) {
      out.push(buf);
      buf = '';
      continue;
    }
    buf += ch;
  }
  out.push(buf);
  return out;
}
