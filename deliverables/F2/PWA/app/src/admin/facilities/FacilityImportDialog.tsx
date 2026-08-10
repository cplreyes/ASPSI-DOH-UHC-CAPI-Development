/**
 * F2 Admin Portal — CSV import dialog (spec F2-Facility-Master-Mgmt-2026-07-16).
 *
 * Paste (or pick a file — same textarea) → Dry run → per-row verdict table +
 * summary → Apply. Apply is enabled only after a dry run of the CURRENT text;
 * editing the CSV re-arms the dry-run gate. Import never archives anything.
 */
import { useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { adminFetch, type ApiError } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { useRouter } from '../lib/pages-router';
import { FACILITY_CSV_HEADER_V2, parseFacilityCsv, type FacilityCsvRow } from './parse-csv';

interface Verdict {
  row: number;
  facility_id: string;
  action: 'create' | 'update' | 'unchanged' | 'error';
  changes?: string[];
  warnings: string[];
  errors: string[];
}

interface ImportResponse {
  ok: true;
  mode: 'dry_run' | 'apply';
  summary: { creates: number; updates: number; unchanged: number; errors: number; warnings: number };
  verdicts: Verdict[];
}

export interface FacilityImportDialogProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
  onApplied: () => void;
  onClose: () => void;
}

export function FacilityImportDialog({
  apiBaseUrl,
  fetchImpl,
  onApplied,
  onClose,
}: FacilityImportDialogProps): JSX.Element {
  const { token, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();
  const [text, setText] = useState('');
  const [parseError, setParseError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [dryRun, setDryRun] = useState<ImportResponse | null>(null);
  const [applied, setApplied] = useState<ImportResponse | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const post = async (mode: 'dry_run' | 'apply', rows: FacilityCsvRow[]) =>
    adminFetch<ImportResponse>(
      `${apiBaseUrl}/admin/api/facilities/import`,
      { method: 'POST', body: JSON.stringify({ mode, rows }) },
      {
        ...(token ? { token } : {}),
        onUnauthorized: () => {
          clearAuth();
          navigate('/admin/login');
        },
        onPasswordChangeRequired: () => navigate('/admin/me/change-password'),
        ...(fetchImpl ? { fetchImpl } : {}),
      },
    );

  const run = async (mode: 'dry_run' | 'apply') => {
    const parsed = parseFacilityCsv(text);
    if (parsed.error) {
      setParseError(parsed.error);
      setDryRun(null);
      return;
    }
    setParseError(null);
    setBusy(true);
    setError(null);
    const r = await post(mode, parsed.rows);
    setBusy(false);
    if (!r.ok) {
      setError(r.error);
      return;
    }
    if (mode === 'dry_run') setDryRun(r.data);
    else {
      setApplied(r.data);
      onApplied();
    }
  };

  const onText = (v: string) => {
    setText(v);
    setDryRun(null); // editing re-arms the dry-run gate
    setApplied(null);
    setParseError(null);
  };

  const onFile = (file: File | undefined) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => onText(String(reader.result ?? ''));
    reader.readAsText(file);
  };

  const template = `data:text/csv;charset=utf-8,${encodeURIComponent(FACILITY_CSV_HEADER_V2.join(',') + '\n')}`;

  const result = applied ?? dryRun;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Import facilities CSV"
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/70 px-4"
      onClick={(e) => {
        if (e.target === e.currentTarget && !busy) onClose();
      }}
    >
      <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto border border-hairline bg-paper p-6">
        <header className="border-b border-hairline pb-3">
          <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
            Facility master · batch import
          </p>
          <h3 className="mt-1 font-serif text-xl font-medium tracking-tight">Import facilities CSV</h3>
        </header>

        <div className="mt-4 flex flex-col gap-4">
          <p className="text-sm text-muted-foreground">
            Paste a wave file (or pick one) with the template header — the trailing{' '}
            <code>target_hcws</code> column is optional (7-column files stay valid and never touch
            existing targets). Dry run shows exactly what would change — nothing lands until you
            Apply. Imports never archive a facility.{' '}
            <a
              href={template}
              download="facility-master-template.csv"
              data-testid="import-template"
              className="underline underline-offset-4 hover:text-ink"
            >
              Download template
            </a>
          </p>

          <div className="flex flex-wrap items-center gap-3">
            <input
              ref={fileRef}
              type="file"
              accept=".csv,text/csv"
              data-testid="import-file"
              onChange={(e) => onFile(e.target.files?.[0])}
              className="text-xs text-muted-foreground"
            />
          </div>
          <textarea
            value={text}
            onChange={(e) => onText(e.target.value)}
            rows={8}
            placeholder={FACILITY_CSV_HEADER_V2.join(',')}
            data-testid="import-text"
            className="border border-hairline bg-transparent p-2 font-mono text-xs outline-none focus:border-signal"
          />

          {parseError ? (
            <p className="text-sm text-error" data-testid="import-parse-error">
              {parseError}
            </p>
          ) : null}
          {error ? (
            <div role="alert" className="border-l-2 border-error py-2 pl-3">
              <p className="text-sm text-error">{error.message ?? 'Import failed.'}</p>
            </div>
          ) : null}

          <div className="flex flex-wrap gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={() => void run('dry_run')}
              disabled={busy || !text.trim()}
              data-testid="import-dry-run"
              className="h-10 border-hairline hover:bg-secondary disabled:opacity-50"
            >
              {busy && !dryRun ? 'Checking…' : 'Dry run'}
            </Button>
            <Button
              type="button"
              onClick={() => void run('apply')}
              disabled={busy || !dryRun || !!applied}
              data-testid="import-apply"
              className="h-10"
            >
              {busy && dryRun ? 'Applying…' : 'Apply'}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={busy}
              className="h-10 border-hairline hover:bg-secondary disabled:opacity-50"
            >
              Close
            </Button>
          </div>

          {result ? (
            <div className="flex flex-col gap-2">
              <p
                className={`font-mono text-xs uppercase tracking-wider ${
                  applied ? 'text-signal' : 'text-muted-foreground'
                }`}
                data-testid="import-summary"
              >
                {applied ? 'Applied · ' : 'Dry run · '}
                {result.summary.creates} create · {result.summary.updates} update ·{' '}
                {result.summary.unchanged} unchanged · {result.summary.errors} error ·{' '}
                {result.summary.warnings} warning
              </p>
              <div className="max-h-64 overflow-auto border border-hairline" data-testid="import-verdicts">
                <table className="w-full text-xs">
                  <thead className="border-b border-hairline text-left">
                    <tr>
                      <Th>#</Th>
                      <Th>Facility ID</Th>
                      <Th>Action</Th>
                      <Th>Details</Th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-hairline">
                    {result.verdicts.map((v) => (
                      <tr key={v.row}>
                        <td className="px-2 py-1 font-mono">{v.row}</td>
                        <td className="px-2 py-1 font-mono">{v.facility_id || '—'}</td>
                        <td
                          className={`px-2 py-1 font-mono uppercase ${
                            v.action === 'error'
                              ? 'text-error'
                              : v.action === 'unchanged'
                                ? 'text-muted-foreground'
                                : 'text-signal'
                          }`}
                        >
                          {v.action}
                        </td>
                        <td className="px-2 py-1">
                          {v.errors.map((e) => (
                            <span key={e} className="block text-error">
                              {e}
                            </span>
                          ))}
                          {v.changes?.length ? (
                            <span className="block text-muted-foreground">
                              changes: {v.changes.join(', ')}
                            </span>
                          ) : null}
                          {v.warnings.map((w) => (
                            <span key={w} className="block text-warning">
                              {w}
                            </span>
                          ))}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function Th({ children }: { children?: React.ReactNode }): JSX.Element {
  return (
    <th className="px-2 py-1 font-mono text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
      {children}
    </th>
  );
}
