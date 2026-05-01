/**
 * F2 Admin Portal — HCWs tab (Data dashboard).
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.18)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.14)
 *
 * Lookup table for healthcare workers tracked in F2_HCWs. Filters by
 * facility_id, status (enrolled / submitted / revoked), or substring
 * search across the row. Each row exposes "View" (link to filter
 * Responses by hcw_id) and "Encode" (jump to encoder for that HCW).
 *
 * The "Reissue token" row action lands with Sprint 4.4 once the
 * QR-issuing modal is built; perm gating (dash_users) plumbs through
 * then. Skipping it now keeps this commit a clean lookup-only tab.
 */
import { useEffect, useMemo, useState } from 'react';
import { adminFetch, type ApiError } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { Link, useRouter } from '../lib/pages-router';
import { ReissueTokenModal } from './ReissueTokenModal';

interface HcwRow {
  hcw_id: string;
  facility_id: string;
  facility_name: string;
  status: string;
  created_at: string;
  enrollment_token_jti?: string;
  token_revoked_at?: string;
}

interface ListHcwsData {
  rows: HcwRow[];
  total: number;
  has_more: boolean;
}

export interface HCWsTabProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
}

interface UiFilters {
  facility_id: string;
  status: string;
  q: string;
}

function readFiltersFromUrl(): UiFilters {
  if (typeof window === 'undefined') {
    return { facility_id: '', status: '', q: '' };
  }
  const p = new URLSearchParams(window.location.search);
  return {
    facility_id: p.get('facility_id') ?? '',
    status: p.get('status') ?? '',
    q: p.get('q') ?? '',
  };
}

function buildApiQuery(f: UiFilters): string {
  const p = new URLSearchParams();
  if (f.facility_id) p.set('facility_id', f.facility_id);
  if (f.status) p.set('status', f.status);
  if (f.q) p.set('q', f.q);
  p.set('limit', '200');
  return p.toString();
}

export function HCWsTab({ apiBaseUrl, fetchImpl }: HCWsTabProps): JSX.Element {
  const { token, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();
  const [filters, setFilters] = useState<UiFilters>(() => readFiltersFromUrl());
  const [state, setState] = useState<
    | { kind: 'loading' }
    | { kind: 'loaded'; data: ListHcwsData }
    | { kind: 'failed'; error: ApiError }
  >({ kind: 'loading' });

  const apiQuery = useMemo(() => buildApiQuery(filters), [filters]);
  const [reissueTarget, setReissueTarget] = useState<HcwRow | null>(null);

  useEffect(() => {
    let cancelled = false;
    setState({ kind: 'loading' });
    void (async () => {
      const r = await adminFetch<ListHcwsData>(
        `${apiBaseUrl}/admin/api/dashboards/data/hcws?${apiQuery}`,
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

  const togglePill = (value: string) => {
    setFilters((prev) => ({ ...prev, status: prev.status === value ? '' : value }));
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-3 border-b border-hairline pb-3">
        <FilterText label="Facility ID" value={filters.facility_id} onChange={(v) => setFilters({ ...filters, facility_id: v })} />
        <FilterText label="Search" value={filters.q} onChange={(v) => setFilters({ ...filters, q: v })} />
        <div className="flex items-center gap-2">
          <PillToggle active={filters.status === 'enrolled'} onClick={() => togglePill('enrolled')}>Enrolled</PillToggle>
          <PillToggle active={filters.status === 'submitted'} onClick={() => togglePill('submitted')}>Submitted</PillToggle>
          <PillToggle active={filters.status === 'revoked'} onClick={() => togglePill('revoked')}>Revoked</PillToggle>
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
            {state.data.total} HCW{state.data.total === 1 ? '' : 's'}
            {state.data.has_more ? ' (showing first 200)' : ''}
          </p>
          <HcwsTable rows={state.data.rows} onReissue={setReissueTarget} />
        </>
      ) : null}

      {reissueTarget ? (
        <ReissueTokenModal
          apiBaseUrl={apiBaseUrl}
          {...(fetchImpl ? { fetchImpl } : {})}
          hcwId={reissueTarget.hcw_id}
          {...(reissueTarget.facility_name ? { facilityName: reissueTarget.facility_name } : {})}
          {...(reissueTarget.enrollment_token_jti ? { prevJti: reissueTarget.enrollment_token_jti } : {})}
          onClose={() => setReissueTarget(null)}
        />
      ) : null}
    </div>
  );
}

function FilterText({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }): JSX.Element {
  return (
    <label className="flex flex-col gap-1">
      <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">{label}</span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="border-0 border-b border-hairline bg-transparent py-1 text-sm outline-none focus:border-signal"
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

function HcwsTable({ rows, onReissue }: { rows: HcwRow[]; onReissue: (r: HcwRow) => void }): JSX.Element {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="border-b border-hairline text-left">
          <tr>
            <Th>HCW</Th>
            <Th>Facility</Th>
            <Th>Status</Th>
            <Th>Created</Th>
            <Th aria-label="actions" />
          </tr>
        </thead>
        <tbody className="divide-y divide-hairline">
          {rows.map((r) => (
            <tr key={r.hcw_id}>
              <Td mono>{r.hcw_id}</Td>
              <Td>
                <span>{r.facility_name || r.facility_id}</span>
                {r.facility_name ? (
                  <span className="ml-2 font-mono text-[10px] text-muted-foreground">{r.facility_id}</span>
                ) : null}
              </Td>
              <Td>
                <StatusPill value={r.status} />
              </Td>
              <Td mono>{formatTs(r.created_at)}</Td>
              <Td>
                <div className="flex flex-wrap gap-3">
                  <Link
                    to={`/admin/data?tab=responses&q=${encodeURIComponent(r.hcw_id)}`}
                    className="font-mono text-xs uppercase tracking-wider text-muted-foreground underline-offset-4 hover:text-ink hover:underline"
                  >
                    View responses
                  </Link>
                  <Link
                    to={`/admin/encode/${encodeURIComponent(r.hcw_id)}`}
                    className="font-mono text-xs uppercase tracking-wider text-muted-foreground underline-offset-4 hover:text-ink hover:underline"
                  >
                    Encode
                  </Link>
                  <button
                    type="button"
                    onClick={() => onReissue(r)}
                    className="font-mono text-xs uppercase tracking-wider text-warning underline-offset-4 hover:underline"
                    title="Issue a new enrollment token (CAS-protected; admin only)"
                  >
                    Reissue
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

function Th({ children, ...rest }: { children?: React.ReactNode } & React.ThHTMLAttributes<HTMLTableCellElement>): JSX.Element {
  return (
    <th {...rest} className="px-3 py-2 font-mono text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
      {children}
    </th>
  );
}

function Td({ children, mono = false }: { children?: React.ReactNode; mono?: boolean }): JSX.Element {
  return <td className={`px-3 py-2 align-top ${mono ? 'font-mono text-xs' : ''}`}>{children}</td>;
}

function StatusPill({ value }: { value: string }): JSX.Element {
  const tone =
    value === 'revoked'
      ? 'border-error text-error'
      : value === 'submitted'
        ? 'border-signal text-signal'
        : 'border-hairline text-muted-foreground';
  return (
    <span className={`rounded-full border ${tone} px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider`}>
      {value || '—'}
    </span>
  );
}

function formatTs(iso: string): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function EmptyBanner(): JSX.Element {
  return (
    <div className="border border-hairline bg-secondary/20 px-4 py-6">
      <p className="font-serif text-lg">No healthcare workers match the current filters.</p>
      <p className="mt-1 text-sm text-muted-foreground">
        F2_HCWs populates from token issuance + the backfillHcws helper. If this is empty,
        run backfillHcws on the staging sheet (Task 2.8).
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
              : (error.message ?? 'Failed to load HCWs.')}
      </p>
      {error.requestId ? (
        <p className="mt-1 font-mono text-xs text-muted-foreground">ref {error.requestId}</p>
      ) : null}
    </div>
  );
}
