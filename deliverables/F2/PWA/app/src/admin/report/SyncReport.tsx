/**
 * F2 Admin Portal — Sync Report.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.21)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.7)
 *
 * Pivot table of submissions by geography level (region / province /
 * facility). Default region-level, last 7 days. Each row links to the
 * Data dashboard pre-filtered (free-text q on the geo key) so admins
 * can drill from a low-pacing region straight to the rows.
 *
 * "Expected" / "% complete" columns surface as null until F2_SampleFrame
 * is ingested — backend stub returns null and frontend shows "—".
 */
import { useEffect, useMemo, useState } from 'react';
import { adminFetch, type ApiError } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { Link, useRouter } from '../lib/pages-router';

type Level = 'region' | 'province' | 'facility';

interface PivotRow {
  key: string;
  submitted: number;
  expected: number | null;
  percent_complete: number | null;
  last_submitted_at: string;
}

interface SyncReportData {
  level: Level;
  pivot: PivotRow[];
  totals: { submitted: number; expected: number | null; keys: number };
}

export interface SyncReportProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
}

interface UiFilters {
  level: Level;
  from: string;
  to: string;
}

function defaultFromIso(): string {
  return new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
}

function readFiltersFromUrl(): UiFilters {
  if (typeof window === 'undefined') {
    return { level: 'region', from: defaultFromIso(), to: '' };
  }
  const p = new URLSearchParams(window.location.search);
  const lvlRaw = p.get('level');
  const lvl: Level = lvlRaw === 'province' || lvlRaw === 'facility' ? lvlRaw : 'region';
  return {
    level: lvl,
    from: p.get('from') ?? defaultFromIso(),
    to: p.get('to') ?? '',
  };
}

function buildApiQuery(f: UiFilters): string {
  const p = new URLSearchParams();
  p.set('level', f.level);
  if (f.from) p.set('from', f.from);
  if (f.to) p.set('to', f.to);
  return p.toString();
}

export function SyncReport({ apiBaseUrl, fetchImpl }: SyncReportProps): JSX.Element {
  const { token, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();
  const [filters, setFilters] = useState<UiFilters>(() => readFiltersFromUrl());
  const [state, setState] = useState<
    | { kind: 'loading' }
    | { kind: 'loaded'; data: SyncReportData }
    | { kind: 'failed'; error: ApiError }
  >({ kind: 'loading' });

  const apiQuery = useMemo(() => buildApiQuery(filters), [filters]);

  useEffect(() => {
    let cancelled = false;
    setState({ kind: 'loading' });
    void (async () => {
      const r = await adminFetch<SyncReportData>(
        `${apiBaseUrl}/admin/api/dashboards/report/sync?${apiQuery}`,
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

  const setLevel = (level: Level) => setFilters({ ...filters, level });

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-3 border-b border-hairline pb-3">
        <FilterDate label="From" value={filters.from} onChange={(v) => setFilters({ ...filters, from: v })} />
        <FilterDate label="To" value={filters.to} onChange={(v) => setFilters({ ...filters, to: v })} />
        <div className="flex items-center gap-2">
          <PillToggle active={filters.level === 'region'} onClick={() => setLevel('region')}>Region</PillToggle>
          <PillToggle active={filters.level === 'province'} onClick={() => setLevel('province')}>Province</PillToggle>
          <PillToggle active={filters.level === 'facility'} onClick={() => setLevel('facility')}>Facility</PillToggle>
        </div>
      </div>

      {state.kind === 'loading' ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : state.kind === 'failed' ? (
        <ErrorBanner error={state.error} />
      ) : state.kind === 'loaded' && state.data.pivot.length === 0 ? (
        <EmptyBanner />
      ) : state.kind === 'loaded' ? (
        <>
          <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
            {state.data.totals.submitted} submission{state.data.totals.submitted === 1 ? '' : 's'}
            {' across '}{state.data.totals.keys} {state.data.level === 'region' ? 'region' : state.data.level}{state.data.totals.keys === 1 ? '' : 's'}
          </p>
          <PivotTable level={state.data.level} rows={state.data.pivot} />
        </>
      ) : null}
    </div>
  );
}

function FilterDate({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }): JSX.Element {
  return (
    <label className="flex flex-col gap-1">
      <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">{label}</span>
      <input
        type="date"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="border-0 border-b border-hairline bg-transparent py-1 font-mono text-sm outline-none focus:border-signal"
      />
    </label>
  );
}

function PillToggle({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }): JSX.Element {
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

function PivotTable({ level, rows }: { level: Level; rows: PivotRow[] }): JSX.Element {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="border-b border-hairline text-left">
          <tr>
            <Th>{level.charAt(0).toUpperCase() + level.slice(1)}</Th>
            <Th>Submitted</Th>
            <Th>Expected</Th>
            <Th>%</Th>
            <Th>Last submission</Th>
          </tr>
        </thead>
        <tbody className="divide-y divide-hairline">
          {rows.map((r) => (
            <tr key={r.key}>
              <Td mono>
                <Link
                  to={`/admin/data?tab=responses&q=${encodeURIComponent(r.key)}`}
                  className="underline-offset-4 hover:underline"
                >
                  {r.key}
                </Link>
              </Td>
              <Td mono>{r.submitted}</Td>
              <Td mono>{r.expected ?? '—'}</Td>
              <Td mono>{r.percent_complete != null ? `${r.percent_complete}%` : '—'}</Td>
              <Td mono>{formatTs(r.last_submitted_at)}</Td>
            </tr>
          ))}
        </tbody>
      </table>
      <aside className="mt-3 border-l-2 border-hairline pl-3">
        <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
          Expected counts surface as &mdash; until the F2_SampleFrame ingest lands.
        </p>
      </aside>
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
  if (!iso) return '—';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function EmptyBanner(): JSX.Element {
  return (
    <div className="border border-hairline bg-secondary/20 px-4 py-6">
      <p className="font-serif text-lg">No submissions in this window.</p>
      <p className="mt-1 text-sm text-muted-foreground">
        Widen the date range or check the Data tab to verify submissions are reaching F2_Responses.
      </p>
    </div>
  );
}

function ErrorBanner({ error }: { error: ApiError }): JSX.Element {
  return (
    <div role="alert" className="border-l-2 border-error bg-secondary/30 px-3 py-2">
      <p className="text-sm text-error">
        {error.code === 'E_PERM_DENIED'
          ? 'Your role lacks dash_report. Contact an Administrator.'
          : error.code === 'E_BACKEND'
            ? 'Backend unavailable — Apps Script staging may not be reachable yet.'
            : error.code === 'E_NETWORK'
              ? 'Network unavailable. Reload to retry.'
              : (error.message ?? 'Failed to load Sync Report.')}
      </p>
      {error.requestId ? (
        <p className="mt-1 font-mono text-xs text-muted-foreground">ref {error.requestId}</p>
      ) : null}
    </div>
  );
}
