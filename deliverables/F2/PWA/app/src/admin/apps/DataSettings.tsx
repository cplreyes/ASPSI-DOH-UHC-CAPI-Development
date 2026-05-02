/**
 * F2 Admin Portal - Data Settings panel.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 3.8)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (sec 7.6)
 *
 * Each row schedules a recurring CSV break-out: every interval_minutes
 * the worker's scheduled() handler asks AS for due rows, writes the
 * CSV to R2 at output_path_template, and marks the row complete which
 * advances next_run_at.
 *
 * Inline minimal CRUD - new row form at top, table with Run-now /
 * Edit / Delete actions per row. Edit reuses the new-row form
 * pre-filled. We keep this a single file rather than a separate
 * editor modal because the surface is small (5 fields) and the row
 * count is bounded (one per instrument, ~3 expected).
 */
import { useEffect, useState } from 'react';
import { adminFetch, type ApiError } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { useRouter } from '../lib/pages-router';

interface SettingRow {
  setting_id: string;
  instrument: string;
  included_columns: string;
  interval_minutes: number;
  next_run_at: string;
  output_path_template: string;
  last_run_at?: string;
  last_run_status?: string;
  last_run_error?: string;
  enabled: boolean;
  created_by?: string;
  created_at?: string;
}

interface ListSettingsData {
  settings: SettingRow[];
  total: number;
}

export interface DataSettingsProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
}

type ListState =
  | { kind: 'loading' }
  | { kind: 'loaded'; data: ListSettingsData }
  | { kind: 'failed'; error: ApiError };

interface FormState {
  setting_id?: string;
  instrument: string;
  interval_minutes: string;
  output_path_template: string;
  enabled: boolean;
}

const EMPTY_FORM: FormState = {
  instrument: 'F2',
  interval_minutes: '60',
  output_path_template: 'exports/{{date}}/{{setting_id}}.csv',
  enabled: true,
};

export function DataSettings({ apiBaseUrl, fetchImpl }: DataSettingsProps): JSX.Element {
  const { token, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();
  const [state, setState] = useState<ListState>({ kind: 'loading' });
  const [reloadTick, setReloadTick] = useState(0);
  const [form, setForm] = useState<FormState | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setState({ kind: 'loading' });
    void (async () => {
      const r = await adminFetch<ListSettingsData>(
        `${apiBaseUrl}/admin/api/dashboards/apps/data-settings`,
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

  function authOpts() {
    return {
      ...(token ? { token } : {}),
      onUnauthorized: () => {
        clearAuth();
        navigate('/admin/login');
      },
      ...(fetchImpl ? { fetchImpl } : {}),
    };
  }

  async function handleSubmit(e: React.FormEvent): Promise<void> {
    e.preventDefault();
    if (!form) return;
    setFormError(null);
    const interval = Number(form.interval_minutes);
    if (!Number.isInteger(interval) || interval < 5 || interval > 1440) {
      setFormError('Interval must be an integer between 5 and 1440 minutes.');
      return;
    }
    if (
      !form.output_path_template ||
      form.output_path_template.startsWith('/') ||
      form.output_path_template.includes('\\') ||
      form.output_path_template.includes('..')
    ) {
      setFormError(
        'Output path required (no leading slash, no backslash, no .. path traversal).',
      );
      return;
    }

    setSubmitting(true);
    try {
      const isEdit = !!form.setting_id;
      const url = isEdit
        ? `${apiBaseUrl}/admin/api/dashboards/apps/data-settings/${encodeURIComponent(form.setting_id!)}`
        : `${apiBaseUrl}/admin/api/dashboards/apps/data-settings`;
      const r = await adminFetch<{ setting: SettingRow }>(
        url,
        {
          method: isEdit ? 'PATCH' : 'POST',
          body: JSON.stringify({
            instrument: form.instrument,
            interval_minutes: interval,
            output_path_template: form.output_path_template,
            enabled: form.enabled,
          }),
        },
        authOpts(),
      );
      if (r.ok) {
        setForm(null);
        setReloadTick((n) => n + 1);
      } else {
        setFormError(friendlyError(r.error, isEdit ? 'Update failed.' : 'Create failed.'));
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(row: SettingRow): Promise<void> {
    if (!window.confirm(`Delete the ${row.instrument} setting ${row.setting_id}?`)) return;
    const r = await adminFetch<undefined>(
      `${apiBaseUrl}/admin/api/dashboards/apps/data-settings/${encodeURIComponent(row.setting_id)}`,
      { method: 'DELETE' },
      authOpts(),
    );
    if (r.ok) setReloadTick((n) => n + 1);
    else window.alert(friendlyError(r.error, 'Delete failed.'));
  }

  async function handleRunNow(row: SettingRow): Promise<void> {
    const r = await adminFetch<{ setting: SettingRow }>(
      `${apiBaseUrl}/admin/api/dashboards/apps/data-settings/${encodeURIComponent(row.setting_id)}/run-now`,
      { method: 'POST' },
      authOpts(),
    );
    if (r.ok) setReloadTick((n) => n + 1);
    else window.alert(friendlyError(r.error, 'Run-now failed.'));
  }

  function startEdit(row: SettingRow): void {
    setForm({
      setting_id: row.setting_id,
      instrument: row.instrument,
      interval_minutes: String(row.interval_minutes),
      output_path_template: row.output_path_template,
      enabled: !!row.enabled,
    });
    setFormError(null);
  }

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-baseline justify-between">
        <h3 className="font-serif text-lg font-medium tracking-tight">Data Settings</h3>
        <button
          type="button"
          onClick={() => {
            setForm(form ? null : { ...EMPTY_FORM });
            setFormError(null);
          }}
          className="font-mono text-xs uppercase tracking-wider text-muted-foreground hover:text-foreground"
        >
          {form ? 'Cancel' : '+ Add setting'}
        </button>
      </div>

      {form ? (
        <SettingForm
          form={form}
          setForm={setForm}
          submitting={submitting}
          formError={formError}
          onSubmit={handleSubmit}
        />
      ) : null}

      {state.kind === 'loading' ? (
        <p className="text-sm text-muted-foreground">Loading...</p>
      ) : state.kind === 'failed' ? (
        <ErrorBanner error={state.error} />
      ) : state.data.settings.length === 0 ? (
        <EmptyState />
      ) : (
        <SettingsTable
          rows={state.data.settings}
          onEdit={startEdit}
          onDelete={handleDelete}
          onRunNow={handleRunNow}
        />
      )}
    </section>
  );
}

function SettingForm({
  form,
  setForm,
  submitting,
  formError,
  onSubmit,
}: {
  form: FormState;
  setForm: React.Dispatch<React.SetStateAction<FormState | null>>;
  submitting: boolean;
  formError: string | null;
  onSubmit: (e: React.FormEvent) => Promise<void>;
}): JSX.Element {
  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-3 border-l-2 border-hairline pl-4">
      <FormRow label="Instrument">
        <input
          type="text"
          value={form.instrument}
          onChange={(e) => setForm({ ...form, instrument: e.target.value })}
          className="border-b border-hairline bg-transparent px-1 py-0.5 font-mono text-xs"
        />
      </FormRow>
      <FormRow label="Interval (minutes)">
        <input
          type="number"
          min={5}
          max={1440}
          value={form.interval_minutes}
          onChange={(e) => setForm({ ...form, interval_minutes: e.target.value })}
          className="border-b border-hairline bg-transparent px-1 py-0.5 font-mono text-xs"
        />
      </FormRow>
      <FormRow label="Output path template">
        <input
          type="text"
          value={form.output_path_template}
          onChange={(e) => setForm({ ...form, output_path_template: e.target.value })}
          className="w-full border-b border-hairline bg-transparent px-1 py-0.5 font-mono text-xs"
        />
      </FormRow>
      <FormRow label="Enabled">
        <input
          type="checkbox"
          checked={form.enabled}
          onChange={(e) => setForm({ ...form, enabled: e.target.checked })}
        />
      </FormRow>
      {formError ? (
        <p role="alert" className="text-sm text-error">
          {formError}
        </p>
      ) : null}
      <div className="flex gap-3">
        <button
          type="submit"
          disabled={submitting}
          className="border border-foreground px-3 py-1 font-mono text-xs uppercase tracking-wider hover:bg-foreground hover:text-background disabled:opacity-50"
        >
          {submitting ? 'Saving...' : form.setting_id ? 'Save' : 'Create'}
        </button>
      </div>
    </form>
  );
}

function FormRow({ label, children }: { label: string; children: React.ReactNode }): JSX.Element {
  return (
    <label className="flex flex-col gap-1">
      <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      {children}
    </label>
  );
}

function SettingsTable({
  rows,
  onEdit,
  onDelete,
  onRunNow,
}: {
  rows: SettingRow[];
  onEdit: (row: SettingRow) => void;
  onDelete: (row: SettingRow) => void | Promise<void>;
  onRunNow: (row: SettingRow) => void | Promise<void>;
}): JSX.Element {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="border-b border-hairline text-left">
          <tr>
            <Th>Setting</Th>
            <Th>Instrument</Th>
            <Th>Every</Th>
            <Th>Output path</Th>
            <Th>Last run</Th>
            <Th>Next run</Th>
            <Th>{''}</Th>
          </tr>
        </thead>
        <tbody className="divide-y divide-hairline">
          {rows.map((r) => (
            <tr key={r.setting_id} className={!r.enabled ? 'opacity-60' : ''}>
              <Td mono>
                {r.setting_id}
                {!r.enabled ? <span className="ml-1 text-muted-foreground">(off)</span> : null}
              </Td>
              <Td mono>{r.instrument}</Td>
              <Td mono>{r.interval_minutes}m</Td>
              <Td mono>{r.output_path_template}</Td>
              <Td mono>
                {r.last_run_status ? (
                  <span className={r.last_run_status === 'failed' ? 'text-error' : ''}>
                    {r.last_run_status} {formatTs(r.last_run_at || '')}
                  </span>
                ) : (
                  '-'
                )}
              </Td>
              <Td mono>{formatTs(r.next_run_at)}</Td>
              <Td>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => void onRunNow(r)}
                    className="font-mono text-xs uppercase tracking-wider text-muted-foreground hover:text-foreground"
                  >
                    Run now
                  </button>
                  <button
                    type="button"
                    onClick={() => onEdit(r)}
                    className="font-mono text-xs uppercase tracking-wider text-muted-foreground hover:text-foreground"
                  >
                    Edit
                  </button>
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
        No scheduled break-outs yet. Add one to export F2 responses to R2 on an
        interval (default 60 minutes). The output path supports{' '}
        <code className="font-mono text-xs">{'{{date}}'}</code> and{' '}
        <code className="font-mono text-xs">{'{{setting_id}}'}</code> placeholders.
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

function Td({ children, mono = false }: { children?: React.ReactNode; mono?: boolean }): JSX.Element {
  return <td className={`px-3 py-2 align-top ${mono ? 'font-mono text-xs' : ''}`}>{children}</td>;
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
  if (err.code === 'E_BACKEND') return 'Backend unavailable - Apps Script staging may be unreachable.';
  if (err.code === 'E_CONFLICT') return err.message || 'This setting is already running.';
  return err.message || fallback;
}

function ErrorBanner({ error }: { error: ApiError }): JSX.Element {
  return (
    <div role="alert" className="border-l-2 border-error bg-secondary/30 px-3 py-2">
      <p className="text-sm text-error">{friendlyError(error, 'Failed to load settings.')}</p>
      {error.requestId ? (
        <p className="mt-1 font-mono text-xs text-muted-foreground">ref {error.requestId}</p>
      ) : null}
    </div>
  );
}
