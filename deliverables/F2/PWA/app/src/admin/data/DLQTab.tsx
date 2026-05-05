/**
 * F2 Admin Portal — DLQ tab (Data dashboard).
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.17)
 *
 * Dead-letter queue surfaces submission attempts that AS rejected as
 * malformed (per Handlers.js the dlq is appended when payload.values
 * isn't an object, etc). Operations folks scan this tab to spot
 * client-side bugs or schema drift between PWA bundles.
 */
import { useEffect, useMemo, useState } from 'react';
import { adminFetch, type ApiError } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { useRouter } from '../lib/pages-router';

interface DlqRow {
  dlq_id: string;
  received_at_server: string;
  client_submission_id: string;
  reason: string;
  payload_json: string;
}

interface ListDlqData {
  rows: DlqRow[];
  total: number;
  has_more: boolean;
}

export interface DLQTabProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
}

interface UiFilters {
  from: string;
  to: string;
  q: string;
}

function defaultFromIso(): string {
  return new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
}

function readFiltersFromUrl(): UiFilters {
  if (typeof window === 'undefined') {
    return { from: defaultFromIso(), to: '', q: '' };
  }
  const p = new URLSearchParams(window.location.search);
  return {
    from: p.get('from') ?? defaultFromIso(),
    to: p.get('to') ?? '',
    q: p.get('q') ?? '',
  };
}

function buildApiQuery(f: UiFilters): string {
  const p = new URLSearchParams();
  if (f.from) p.set('from', f.from);
  if (f.to) p.set('to', f.to);
  if (f.q) p.set('q', f.q);
  p.set('limit', '200');
  return p.toString();
}

export function DLQTab({ apiBaseUrl, fetchImpl }: DLQTabProps): JSX.Element {
  const { token, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();
  const [filters, setFilters] = useState<UiFilters>(() => readFiltersFromUrl());
  const [state, setState] = useState<
    | { kind: 'loading' }
    | { kind: 'loaded'; data: ListDlqData }
    | { kind: 'failed'; error: ApiError }
  >({ kind: 'loading' });

  const apiQuery = useMemo(() => buildApiQuery(filters), [filters]);

  useEffect(() => {
    let cancelled = false;
    setState({ kind: 'loading' });
    void (async () => {
      const r = await adminFetch<ListDlqData>(
        `${apiBaseUrl}/admin/api/dashboards/data/dlq?${apiQuery}`,
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

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-3 border-b border-hairline pb-3">
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
          label="Search"
          value={filters.q}
          onChange={(v) => setFilters({ ...filters, q: v })}
        />
      </div>

      {state.kind === 'loading' ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : state.kind === 'failed' ? (
        <ErrorBanner error={state.error} />
      ) : state.kind === 'loaded' && state.data.rows.length === 0 ? (
        <EmptyBanner />
      ) : state.kind === 'loaded' ? (
        <>
          <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
            {state.data.total} dead-letter row{state.data.total === 1 ? '' : 's'}
            {state.data.has_more ? ' (showing first 200)' : ''}
          </p>
          <DlqTable rows={state.data.rows} />
        </>
      ) : null}
    </div>
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
  return (
    <label className="flex flex-col gap-1">
      <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      <input
        type="date"
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
  return (
    <label className="flex flex-col gap-1">
      <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="border-0 border-b border-hairline bg-transparent py-1 text-sm outline-none focus:border-signal"
      />
    </label>
  );
}

function DlqTable({ rows }: { rows: DlqRow[] }): JSX.Element {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="border-b border-hairline text-left">
          <tr>
            <Th>Received</Th>
            <Th>Client ID</Th>
            <Th>Reason</Th>
            <Th>Payload</Th>
          </tr>
        </thead>
        <tbody className="divide-y divide-hairline">
          {rows.map((r) => (
            <tr key={r.dlq_id}>
              <Td mono>{formatTs(r.received_at_server)}</Td>
              <Td mono>{r.client_submission_id}</Td>
              <Td>
                <span className="text-error">{r.reason}</span>
              </Td>
              <Td>
                <code className="block max-w-md truncate font-mono text-xs text-muted-foreground">
                  {r.payload_json}
                </code>
              </Td>
            </tr>
          ))}
        </tbody>
      </table>
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

function formatTs(iso: string): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function EmptyBanner(): JSX.Element {
  return (
    <div className="border border-hairline bg-secondary/20 px-4 py-6">
      <p className="font-serif text-lg">No dead-letter rows in this window.</p>
      <p className="mt-1 text-sm text-muted-foreground">
        That&rsquo;s good — every PWA submission accepted by the server made it to F2_Responses.
      </p>
    </div>
  );
}

function ErrorBanner({ error }: { error: ApiError }): JSX.Element {
  return (
    <div role="alert" className="border-l-2 border-error bg-secondary/30 px-3 py-2">
      <p className="text-sm text-error">
        {error.code === 'E_PERM_DENIED'
          ? 'Your role lacks dash_data. Contact an Administrator.'
          : error.code === 'E_BACKEND'
            ? 'Backend unavailable — Apps Script staging may not be reachable yet.'
            : error.code === 'E_NETWORK'
              ? 'Network unavailable. Reload to retry.'
              : (error.message ?? 'Failed to load DLQ.')}
      </p>
      {error.requestId ? (
        <p className="mt-1 font-mono text-xs text-muted-foreground">ref {error.requestId}</p>
      ) : null}
    </div>
  );
}
