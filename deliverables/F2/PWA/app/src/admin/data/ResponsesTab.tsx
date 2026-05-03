/**
 * F2 Admin Portal — Responses tab (Data dashboard).
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.15)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.1)
 *
 * Reads filters from URL query params so the view is shareable; defaults
 * to last-24h when no `from` is specified. Fetches GET /admin/api/dashboards/
 * data/responses on mount and on filter change. Renders a hairline-divided
 * Verde Manual table — no card chrome, mono for IDs, monospace for ISO
 * timestamps, signal color reserved for the source-path pills.
 *
 * Virtualization is intentionally NOT wired here; F2_Responses caps at
 * ~30K rows, the API caps page size at 500, and the typical default-24h
 * filter returns < 200 rows — DOM weight stays well under what would
 * justify a react-window dep. Revisit if scale outgrows this.
 */
import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { adminFetch, type ApiError } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { Link, useRouter } from '../lib/pages-router';

interface ResponseRow {
  submission_id: string;
  client_submission_id: string;
  submitted_at_server: string;
  hcw_id: string;
  facility_id: string;
  status: string;
  source_path: string;
  encoded_by?: string;
}

interface ListResponsesData {
  rows: ResponseRow[];
  total: number;
  has_more: boolean;
}

export interface ResponsesTabProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
}

interface UiFilters {
  from: string; // YYYY-MM-DD or ''
  to: string; // YYYY-MM-DD or ''
  facility_id: string;
  source_path: string; // '' | 'self_admin' | 'paper_encoded' | 'capi'
  errors_only: boolean;
  q: string;
}

function defaultFromIso(): string {
  // Default to 24h ago, formatted as YYYY-MM-DD for the date input.
  const d = new Date(Date.now() - 24 * 60 * 60 * 1000);
  return d.toISOString().slice(0, 10);
}

function readFiltersFromUrl(): UiFilters {
  if (typeof window === 'undefined') {
    return {
      from: defaultFromIso(),
      to: '',
      facility_id: '',
      source_path: '',
      errors_only: false,
      q: '',
    };
  }
  const p = new URLSearchParams(window.location.search);
  return {
    from: p.get('from') ?? defaultFromIso(),
    to: p.get('to') ?? '',
    facility_id: p.get('facility_id') ?? '',
    source_path: p.get('source_path') ?? '',
    errors_only: p.get('errors_only') === '1',
    q: p.get('q') ?? '',
  };
}

function buildQuery(filters: UiFilters): string {
  const p = new URLSearchParams();
  // Preserve dashboard tab so refresh stays on Responses.
  p.set('tab', 'responses');
  if (filters.from) p.set('from', filters.from);
  if (filters.to) p.set('to', filters.to);
  if (filters.facility_id) p.set('facility_id', filters.facility_id);
  if (filters.source_path) p.set('source_path', filters.source_path);
  if (filters.errors_only) p.set('errors_only', '1');
  if (filters.q) p.set('q', filters.q);
  return p.toString();
}

function buildApiQuery(filters: UiFilters): string {
  const p = new URLSearchParams();
  if (filters.from) p.set('from', filters.from);
  if (filters.to) p.set('to', filters.to);
  if (filters.facility_id) p.set('facility_id', filters.facility_id);
  if (filters.source_path) p.set('source_path', filters.source_path);
  if (filters.errors_only) p.set('status', 'rejected');
  if (filters.q) p.set('q', filters.q);
  p.set('limit', '200');
  return p.toString();
}

export function ResponsesTab({ apiBaseUrl, fetchImpl }: ResponsesTabProps): JSX.Element {
  const { token, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();
  const [filters, setFilters] = useState<UiFilters>(() => readFiltersFromUrl());
  const [state, setState] = useState<
    | { kind: 'idle' }
    | { kind: 'loading' }
    | { kind: 'loaded'; data: ListResponsesData }
    | { kind: 'failed'; error: ApiError }
  >({ kind: 'idle' });

  const apiQuery = useMemo(() => buildApiQuery(filters), [filters]);
  const uiQuery = useMemo(() => buildQuery(filters), [filters]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const cur = window.location.search.replace(/^\?/, '');
    if (cur !== uiQuery) {
      window.history.replaceState({}, '', `${window.location.pathname}?${uiQuery}`);
    }
  }, [uiQuery]);

  useEffect(() => {
    let cancelled = false;
    setState({ kind: 'loading' });
    void (async () => {
      const r = await adminFetch<ListResponsesData>(
        `${apiBaseUrl}/admin/api/dashboards/data/responses?${apiQuery}`,
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
  }, [apiQuery, apiBaseUrl, token]);

  const onFilterSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setFilters({ ...filters });
  };

  const togglePill = <K extends keyof UiFilters>(key: K, value: UiFilters[K]) => {
    setFilters((prev) => ({ ...prev, [key]: prev[key] === value ? ('' as UiFilters[K]) : value }));
  };

  return (
    <div className="flex flex-col gap-4">
      <form
        onSubmit={onFilterSubmit}
        className="flex flex-wrap items-end gap-3 border-b border-hairline pb-3"
      >
        <FilterDate
          label="From"
          value={filters.from}
          onChange={(v) => setFilters({ ...filters, from: v })}
        />
        <FilterDate
          label="To"
          value={filters.to}
          onChange={(v) => setFilters({ ...filters, to: v })}
        />
        <FilterText
          label="Facility ID"
          value={filters.facility_id}
          onChange={(v) => setFilters({ ...filters, facility_id: v })}
        />
        <FilterText
          label="Search"
          value={filters.q}
          onChange={(v) => setFilters({ ...filters, q: v })}
        />
        <div className="flex items-center gap-2">
          <PillToggle
            active={filters.source_path === 'self_admin'}
            onClick={() => togglePill('source_path', 'self_admin')}
          >
            Self-admin
          </PillToggle>
          <PillToggle
            active={filters.source_path === 'paper_encoded'}
            onClick={() => togglePill('source_path', 'paper_encoded')}
          >
            Paper-encoded
          </PillToggle>
          <PillToggle
            active={filters.errors_only}
            onClick={() => setFilters({ ...filters, errors_only: !filters.errors_only })}
          >
            Errors only
          </PillToggle>
        </div>
      </form>

      {state.kind === 'loading' ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : state.kind === 'failed' ? (
        <ResponsesError error={state.error} />
      ) : state.kind === 'loaded' && state.data.rows.length === 0 ? (
        <ResponsesEmpty />
      ) : state.kind === 'loaded' ? (
        <>
          <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
            {state.data.total} response{state.data.total === 1 ? '' : 's'}
            {state.data.has_more ? ' (showing first 200 — refine filters to see more)' : ''}
          </p>
          <ResponsesTable rows={state.data.rows} />
        </>
      ) : null}
    </div>
  );
}

// FX-014 (2026-05-03): inputs derive `name` from the label so Chrome's
// "form field should have an id or name" issue panel stays clean and so
// browser autofill / password managers have something to key on.
function slugifyLabel(label: string): string {
  return (
    label
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '') || 'field'
  );
}

function FilterDate({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}): JSX.Element {
  const name = slugifyLabel(label);
  return (
    <label className="flex flex-col gap-1">
      <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      <input
        type="date"
        name={name}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="border-0 border-b border-hairline bg-transparent py-1 font-mono text-sm outline-none focus:border-signal"
      />
    </label>
  );
}

function FilterText({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}): JSX.Element {
  const name = slugifyLabel(label);
  return (
    <label className="flex flex-col gap-1">
      <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      <input
        type="text"
        name={name}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="border-0 border-b border-hairline bg-transparent py-1 text-sm outline-none focus:border-signal"
      />
    </label>
  );
}

function PillToggle({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}): JSX.Element {
  return (
    <button
      type="button"
      onClick={onClick}
      className={
        active
          ? 'rounded-full border border-signal bg-signal-bg px-3 py-1 text-xs text-signal'
          : 'rounded-full border border-hairline px-3 py-1 text-xs text-muted-foreground hover:text-ink'
      }
    >
      {children}
    </button>
  );
}

function ResponsesTable({ rows }: { rows: ResponseRow[] }): JSX.Element {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="border-b border-hairline text-left">
          <tr>
            <Th>Submitted</Th>
            <Th>HCW</Th>
            <Th>Facility</Th>
            <Th>Source</Th>
            <Th>Status</Th>
            <Th aria-label="actions" />
          </tr>
        </thead>
        <tbody className="divide-y divide-hairline">
          {rows.map((r) => (
            <tr key={r.submission_id}>
              <Td mono>{formatTs(r.submitted_at_server)}</Td>
              <Td mono>{r.hcw_id}</Td>
              <Td>{r.facility_id}</Td>
              <Td>
                <SourcePill value={r.source_path} />
              </Td>
              <Td>
                <StatusText value={r.status} />
              </Td>
              <Td>
                <Link
                  to={`/admin/data/responses/${encodeURIComponent(r.submission_id)}`}
                  className="font-mono text-xs uppercase tracking-wider text-muted-foreground underline-offset-4 hover:text-ink hover:underline"
                >
                  View
                </Link>
              </Td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Th({
  children,
  ...rest
}: { children?: React.ReactNode } & React.ThHTMLAttributes<HTMLTableCellElement>): JSX.Element {
  return (
    <th
      {...rest}
      className="px-3 py-2 font-mono text-[10px] font-medium uppercase tracking-wider text-muted-foreground"
    >
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

function SourcePill({ value }: { value: string }): JSX.Element {
  const label =
    value === 'self_admin'
      ? 'Self-admin'
      : value === 'paper_encoded'
        ? 'Paper'
        : value === 'capi'
          ? 'CAPI'
          : value || '—';
  return (
    <span className="rounded-full border border-hairline px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
      {label}
    </span>
  );
}

function StatusText({ value }: { value: string }): JSX.Element {
  if (value === 'rejected') return <span className="text-error">{value}</span>;
  return <span className="text-muted-foreground">{value}</span>;
}

function formatTs(iso: string): string {
  // Compact: YYYY-MM-DD HH:MM (local). Easy to scan; precise enough.
  if (!iso) return '';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function ResponsesEmpty(): JSX.Element {
  return (
    <div className="border border-hairline bg-secondary/20 px-4 py-6">
      <p className="font-serif text-lg">No responses match the current filters.</p>
      <p className="mt-1 text-sm text-muted-foreground">
        Widen the date range or clear filters to see all submissions.
      </p>
    </div>
  );
}

function ResponsesError({ error }: { error: ApiError }): JSX.Element {
  return (
    <div role="alert" className="border-l-2 border-error bg-secondary/30 px-3 py-2">
      <p className="text-sm text-error">
        {error.code === 'E_PERM_DENIED'
          ? 'Your role lacks dash_data. Contact an Administrator.'
          : error.code === 'E_BACKEND'
            ? 'Backend unavailable — Apps Script staging may not be reachable yet.'
            : error.code === 'E_NETWORK'
              ? 'Network unavailable. Reload to retry.'
              : (error.message ?? 'Failed to load responses.')}
      </p>
      {error.requestId ? (
        <p className="mt-1 font-mono text-xs text-muted-foreground">ref {error.requestId}</p>
      ) : null}
    </div>
  );
}
