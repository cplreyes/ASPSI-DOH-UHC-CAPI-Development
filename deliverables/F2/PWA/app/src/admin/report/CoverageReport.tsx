/**
 * F2 Admin Portal — Coverage report (spec F2-Coverage-Report-2026-07-17).
 *
 * Replaces the Sync Report: fieldwork progress vs facility targets, rolled up
 * by geography NAMES from the facility master (never ID prefixes). Count
 * definitions are byte-identical to the Facilities page — the server computes
 * both from the same SQL fragments. Dates are Manila calendar days (server
 * converts via mnlWindow — the To day is INCLUDED).
 *
 * Rows drill down: facility → Responses/HCWs pre-filtered by facility_id;
 * region/province → Facilities page pre-filtered. "(not in master)" surfaces
 * responses whose facility_id has no master row — an integrity signal.
 */
import { useEffect, useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
import { adminFetch, type ApiError } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { Link, useRouter } from '../lib/pages-router';
import { coverageCsv, coverageCsvFilename, type CoverageCsvRow } from './coverage-csv';

type Level = 'region' | 'province' | 'facility';

type CoverageRow = CoverageCsvRow;

interface CoverageData {
  level: Level;
  rows: CoverageRow[];
  totals: CoverageRow;
}

export interface CoverageReportProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
}

interface UiFilters {
  level: Level;
  from: string;
  to: string;
  archived: boolean;
}

const ORPHAN_KEY = '(not in master)';
const UNSPECIFIED_KEY = '(unspecified)';

function readFiltersFromUrl(): UiFilters {
  if (typeof window === 'undefined') {
    return { level: 'region', from: '', to: '', archived: false };
  }
  const p = new URLSearchParams(window.location.search);
  const lvlRaw = p.get('level');
  const lvl: Level = lvlRaw === 'province' || lvlRaw === 'facility' ? lvlRaw : 'region';
  return {
    level: lvl,
    from: p.get('from') ?? '',
    to: p.get('to') ?? '',
    archived: p.get('archived') === '1',
  };
}

/** Reflect filters into the URL (keeps ?tab= and unrelated params intact). */
function writeFiltersToUrl(f: UiFilters): void {
  if (typeof window === 'undefined') return;
  const p = new URLSearchParams(window.location.search);
  if (f.level !== 'region') p.set('level', f.level);
  else p.delete('level');
  if (f.from) p.set('from', f.from);
  else p.delete('from');
  if (f.to) p.set('to', f.to);
  else p.delete('to');
  if (f.archived) p.set('archived', '1');
  else p.delete('archived');
  const qs = p.toString();
  window.history.replaceState({}, '', `${window.location.pathname}${qs ? `?${qs}` : ''}`);
}

function buildApiQuery(f: UiFilters): string {
  const p = new URLSearchParams();
  p.set('level', f.level);
  if (f.from) p.set('from', f.from);
  if (f.to) p.set('to', f.to);
  if (f.archived) p.set('include_archived', 'true');
  return p.toString();
}

export function CoverageReport({ apiBaseUrl, fetchImpl }: CoverageReportProps): JSX.Element {
  const { token, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();
  const [filters, setFiltersState] = useState<UiFilters>(() => readFiltersFromUrl());
  const [state, setState] = useState<
    | { kind: 'loading' }
    | { kind: 'loaded'; data: CoverageData }
    | { kind: 'failed'; error: ApiError }
  >({ kind: 'loading' });

  const setFilters = (f: UiFilters) => {
    setFiltersState(f);
    writeFiltersToUrl(f);
  };

  const apiQuery = useMemo(() => buildApiQuery(filters), [filters]);

  useEffect(() => {
    let cancelled = false;
    setState({ kind: 'loading' });
    void (async () => {
      const r = await adminFetch<CoverageData>(
        `${apiBaseUrl}/admin/api/dashboards/report/coverage?${apiQuery}`,
        {},
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
      if (cancelled) return;
      if (r.ok) setState({ kind: 'loaded', data: r.data });
      else setState({ kind: 'failed', error: r.error });
    })();
    return () => {
      cancelled = true;
    };
  }, [apiQuery, apiBaseUrl, token, clearAuth, navigate, fetchImpl]);

  const onExport = () => {
    if (state.kind !== 'loaded') return;
    const csv = coverageCsv(state.data.rows, state.data.totals);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = coverageCsvFilename(state.data.level);
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-3 border-b border-hairline pb-3">
        <FilterDate label="From" value={filters.from} onChange={(v) => setFilters({ ...filters, from: v })} />
        <FilterDate label="To" value={filters.to} onChange={(v) => setFilters({ ...filters, to: v })} />
        <div className="flex items-center gap-2">
          <PillToggle active={filters.level === 'region'} testid="coverage-level-region" onClick={() => setFilters({ ...filters, level: 'region' })}>Region</PillToggle>
          <PillToggle active={filters.level === 'province'} testid="coverage-level-province" onClick={() => setFilters({ ...filters, level: 'province' })}>Province</PillToggle>
          <PillToggle active={filters.level === 'facility'} testid="coverage-level-facility" onClick={() => setFilters({ ...filters, level: 'facility' })}>Facility</PillToggle>
        </div>
        <label className="flex items-center gap-2 pb-1">
          <input
            type="checkbox"
            checked={filters.archived}
            onChange={(e) => setFilters({ ...filters, archived: e.target.checked })}
            data-testid="coverage-archived"
            className="h-4 w-4 accent-signal"
          />
          <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
            Show archived
          </span>
        </label>
        <div className="ml-auto">
          <Button
            type="button"
            variant="outline"
            onClick={onExport}
            disabled={state.kind !== 'loaded'}
            data-testid="coverage-export"
            className="h-9 border-hairline font-mono text-xs uppercase tracking-wider text-muted-foreground hover:bg-secondary/40 hover:text-ink disabled:opacity-50"
          >
            Export CSV
          </Button>
        </div>
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
            {state.data.totals.submitted} submitted · {state.data.totals.refusals} refusal
            {state.data.totals.refusals === 1 ? '' : 's'} ·{' '}
            {state.data.totals.target != null && state.data.totals.coverage_pct != null
              ? `${state.data.totals.coverage_pct}% of ${state.data.totals.target} target`
              : 'no targets set'}
          </p>
          <CoverageTable level={state.data.level} rows={state.data.rows} totals={state.data.totals} />
        </>
      ) : null}
    </div>
  );
}

function CoverageTable({
  level,
  rows,
  totals,
}: {
  level: Level;
  rows: CoverageRow[];
  totals: CoverageRow;
}): JSX.Element {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="border-b border-hairline text-left">
          <tr>
            <Th>{level.charAt(0).toUpperCase() + level.slice(1)}</Th>
            <Th>Facilities</Th>
            <Th>Links</Th>
            <Th>Target</Th>
            <Th>Started</Th>
            <Th>Submitted</Th>
            <Th>Refusals</Th>
            <Th>Coverage</Th>
            <Th>Paper</Th>
            <Th>Last activity</Th>
          </tr>
        </thead>
        <tbody className="divide-y divide-hairline">
          {rows.map((r) => (
            <CoverageRowTr key={r.key} level={level} r={r} />
          ))}
        </tbody>
        <tfoot>
          <tr className="border-t border-hairline" data-testid="coverage-totals">
            <Td mono strong>TOTAL</Td>
            <Td mono strong>{totals.facilities}</Td>
            <Td mono strong>{totals.links_active}</Td>
            <Td mono strong>{totals.target ?? '—'}</Td>
            <Td mono strong>{totals.started}</Td>
            <Td mono strong>{totals.submitted}</Td>
            <Td mono strong>{refusalCell(totals)}</Td>
            <Td mono strong>{totals.coverage_pct != null ? `${totals.coverage_pct}%` : '—'}</Td>
            <Td mono strong>{totals.paper_encoded}</Td>
            <Td mono strong>{formatTs(totals.last_activity)}</Td>
          </tr>
        </tfoot>
      </table>
      <aside className="mt-3 border-l-2 border-hairline pl-3">
        <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
          Targets come from the facility master (Facilities &rarr; Edit, or the CSV import&rsquo;s
          target_hcws column). Dates are Manila calendar days; the To day is included.
        </p>
      </aside>
    </div>
  );
}

function refusalCell(r: CoverageRow): string {
  return r.refusal_rate != null && r.refusals > 0
    ? `${r.refusals} (${r.refusal_rate}%)`
    : String(r.refusals);
}

function CoverageRowTr({ level, r }: { level: Level; r: CoverageRow }): JSX.Element {
  const orphan = r.key === ORPHAN_KEY;
  const unspecified = r.key === UNSPECIFIED_KEY;
  return (
    <tr className={orphan ? 'opacity-70' : undefined} data-testid={`coverage-row-${r.key}`}>
      <Td>
        <GeoCell level={level} r={r} orphan={orphan} plain={unspecified} />
      </Td>
      <Td mono>{r.facilities}</Td>
      <Td mono>{r.links_active}</Td>
      <Td mono>{r.target ?? '—'}</Td>
      <Td mono>
        {level === 'facility' && r.started > 0 ? (
          <Link
            to={`/admin/data?tab=hcws&facility_id=${encodeURIComponent(r.key)}&status=enrolled&q=sr-`}
            className="underline-offset-4 hover:underline"
            data-testid={`coverage-started-${r.key}`}
          >
            {r.started}
          </Link>
        ) : (
          r.started
        )}
      </Td>
      <Td mono>{r.submitted}</Td>
      <Td mono>{refusalCell(r)}</Td>
      <Td mono>
        {r.coverage_pct != null ? (
          <span className="flex items-center gap-2">
            <span>{r.coverage_pct}%</span>
            <span aria-hidden="true" className="h-1 w-16 shrink-0 bg-secondary/60">
              <span
                className="block h-1 bg-signal"
                style={{ width: `${Math.min(100, r.coverage_pct)}%` }}
              />
            </span>
          </span>
        ) : (
          '—'
        )}
      </Td>
      <Td mono>{r.paper_encoded}</Td>
      <Td mono>{formatTs(r.last_activity)}</Td>
    </tr>
  );
}

function GeoCell({
  level,
  r,
  orphan,
  plain,
}: {
  level: Level;
  r: CoverageRow;
  orphan: boolean;
  plain: boolean;
}): JSX.Element {
  if (orphan) {
    return (
      <span className="flex flex-wrap items-center gap-2">
        <span className="font-mono text-xs">{r.label}</span>
        <Link
          to="/admin/facilities"
          className="border border-warning px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-warning underline-offset-4 hover:underline"
        >
          add to master
        </Link>
      </span>
    );
  }
  if (plain) return <span className="font-mono text-xs text-muted-foreground">{r.label}</span>;
  if (level === 'facility') {
    return (
      <span className="flex flex-col">
        <Link
          to={`/admin/data?tab=responses&facility_id=${encodeURIComponent(r.key)}`}
          className="underline-offset-4 hover:underline"
          data-testid={`coverage-geo-${r.key}`}
        >
          {r.label}
        </Link>
        <span className="font-mono text-[10px] text-muted-foreground">{r.key}</span>
      </span>
    );
  }
  const param = level === 'region' ? 'region' : 'province';
  return (
    <Link
      to={`/admin/facilities?${param}=${encodeURIComponent(r.key)}`}
      className="underline-offset-4 hover:underline"
      data-testid={`coverage-geo-${r.key}`}
    >
      {r.label}
    </Link>
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
        className="border-0 border-b border-hairline bg-transparent py-1 font-mono text-sm outline-none focus:border-signal focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal"
      />
    </label>
  );
}

function PillToggle({ active, onClick, testid, children }: { active: boolean; onClick: () => void; testid: string; children: React.ReactNode }): JSX.Element {
  return (
    <Button
      type="button"
      variant="outline"
      onClick={onClick}
      data-testid={testid}
      className={
        active
          ? 'h-auto rounded-sm border-signal bg-signal-bg px-3 py-1 text-xs text-signal hover:bg-signal-bg'
          : 'h-auto rounded-sm border-hairline bg-transparent px-3 py-1 text-xs text-muted-foreground hover:bg-transparent hover:text-ink'
      }
    >
      {children}
    </Button>
  );
}

function Th({ children }: { children?: React.ReactNode }): JSX.Element {
  return (
    <th className="px-3 py-2 font-mono text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
      {children}
    </th>
  );
}

function Td({ children, mono = false, strong = false }: { children?: React.ReactNode; mono?: boolean; strong?: boolean }): JSX.Element {
  return (
    <td className={`px-3 py-2 align-top ${mono ? 'font-mono text-xs' : ''} ${strong ? 'font-medium text-ink' : ''}`}>
      {children}
    </td>
  );
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
      <p className="font-serif text-lg">No fieldwork activity in this window.</p>
      <p className="mt-1 text-sm text-muted-foreground">
        Widen the date range, or add facilities on the Facilities page to start tracking coverage.
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
            ? 'Backend unavailable. Try again shortly.'
            : error.code === 'E_NETWORK'
              ? 'Network unavailable. Reload to retry.'
              : (error.message ?? 'Failed to load the Coverage report.')}
      </p>
      {error.requestId ? (
        <p className="mt-1 font-mono text-xs text-muted-foreground">ref {error.requestId}</p>
      ) : null}
    </div>
  );
}
