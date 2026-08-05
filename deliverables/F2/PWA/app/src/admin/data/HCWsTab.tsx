/**
 * F2 Admin Portal — HCWs tab (Data dashboard).
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.18)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.14)
 *
 * Lookup table for healthcare workers tracked in F2_HCWs. Filter bar
 * (2026-07-17): created-date range, facility dropdown by name, status
 * pills (enrolled / submitted / refusal / revoked), substring search,
 * Clear filters; filters live in the URL so views stay shareable. Each
 * row exposes "View" (link to filter Responses by hcw_id) and "Encode"
 * (jump to encoder for that HCW).
 *
 * The "Reissue token" row action lands with Sprint 4.4 once the
 * QR-issuing modal is built; perm gating (dash_users) plumbs through
 * then. Skipping it now keeps this commit a clean lookup-only tab.
 */
import { useEffect, useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
import { adminFetch, type ApiError } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { Link, useRouter } from '../lib/pages-router';
import { CreateHCWModal } from './CreateHCWModal';
import { ReissueTokenModal } from './ReissueTokenModal';
import { FacilityLinksModal } from './FacilityLinksModal';
import {
  ClearFiltersButton,
  FilterDate,
  FilterSelect,
  FilterText,
  PillToggle,
} from './filter-controls';
import { useFacilityOptions, useFacilitySelectOptions } from './filter-hooks';

interface HcwRow {
  hcw_id: string;
  facility_id: string;
  /** 12-digit Questionnaire Number; '' / absent for pre-qn rows. */
  qn?: string;
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
  from: string; // YYYY-MM-DD or '' — created_at window
  to: string;
  facility_id: string;
  status: string;
  q: string;
}

function readFiltersFromUrl(): UiFilters {
  if (typeof window === 'undefined') {
    return { from: '', to: '', facility_id: '', status: '', q: '' };
  }
  const p = new URLSearchParams(window.location.search);
  return {
    from: p.get('from') ?? '',
    to: p.get('to') ?? '',
    facility_id: p.get('facility_id') ?? '',
    status: p.get('status') ?? '',
    q: p.get('q') ?? '',
  };
}

function buildQuery(f: UiFilters): string {
  const p = new URLSearchParams();
  // Preserve dashboard tab so refresh stays on HCWs.
  p.set('tab', 'hcws');
  if (f.from) p.set('from', f.from);
  if (f.to) p.set('to', f.to);
  if (f.facility_id) p.set('facility_id', f.facility_id);
  if (f.status) p.set('status', f.status);
  if (f.q) p.set('q', f.q);
  return p.toString();
}

function buildApiQuery(f: UiFilters): string {
  const p = new URLSearchParams();
  if (f.from) p.set('from', f.from);
  if (f.to) p.set('to', f.to);
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
  const uiQuery = useMemo(() => buildQuery(filters), [filters]);
  const facilityOptions = useFacilityOptions(apiBaseUrl, token, fetchImpl);
  const facilitySelectOptions = useFacilitySelectOptions(facilityOptions, filters.facility_id);
  const [reissueTarget, setReissueTarget] = useState<HcwRow | null>(null);
  // R2-#58: Create HCW modal state.
  const [createOpen, setCreateOpen] = useState(false);
  // Model C — facility numbered-links generator modal state (legacy).
  // Facility slug links moved to the Facilities page (spec F2-Facilities-Page-2026-07-16).
  const [linksOpen, setLinksOpen] = useState(false);
  const [reloadTick, setReloadTick] = useState(0);

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
          onPasswordChangeRequired: () => navigate("/admin/me/change-password"),
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
  }, [apiQuery, apiBaseUrl, token, reloadTick, clearAuth, navigate, fetchImpl]);

  // Shareable URLs: write the active filters back (same idiom as Responses).
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const cur = window.location.search.replace(/^\?/, '');
    if (cur !== uiQuery) {
      window.history.replaceState({}, '', `${window.location.pathname}?${uiQuery}`);
    }
  }, [uiQuery]);

  const togglePill = (value: string) => {
    setFilters((prev) => ({ ...prev, status: prev.status === value ? '' : value }));
  };

  const anyFilterActive =
    filters.from !== '' ||
    filters.to !== '' ||
    filters.facility_id !== '' ||
    filters.status !== '' ||
    filters.q !== '';

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end justify-between gap-3 border-b border-hairline pb-3">
        <div className="flex flex-wrap items-end gap-3">
          <FilterDate label="From" value={filters.from} onChange={(v) => setFilters({ ...filters, from: v })} />
          <FilterDate label="To" value={filters.to} onChange={(v) => setFilters({ ...filters, to: v })} />
          <FilterSelect
            label="Facility"
            value={filters.facility_id}
            options={facilitySelectOptions}
            onChange={(v) => setFilters({ ...filters, facility_id: v })}
          />
          <FilterText label="Search" value={filters.q} onChange={(v) => setFilters({ ...filters, q: v })} />
          <div className="flex items-center gap-2">
            <PillToggle active={filters.status === 'enrolled'} onClick={() => togglePill('enrolled')}>Enrolled</PillToggle>
            <PillToggle active={filters.status === 'submitted'} onClick={() => togglePill('submitted')}>Submitted</PillToggle>
            <PillToggle active={filters.status === 'refusal'} onClick={() => togglePill('refusal')}>Refusal</PillToggle>
            <PillToggle active={filters.status === 'revoked'} onClick={() => togglePill('revoked')}>Revoked</PillToggle>
          </div>
          {anyFilterActive ? (
            <ClearFiltersButton
              onClick={() => setFilters({ from: '', to: '', facility_id: '', status: '', q: '' })}
            />
          ) : null}
        </div>
        <div className="flex flex-wrap gap-3">
          <Button
            type="button"
            variant="outline"
            onClick={() => setLinksOpen(true)}
            className="h-10 border-hairline hover:bg-secondary"
            title="Legacy: one numbered self-register link per HCW slot at a facility"
          >
            Numbered links (legacy)
          </Button>
          <Button type="button" onClick={() => setCreateOpen(true)} className="h-10">
            + Create HCW
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
            {state.data.total} HCW{state.data.total === 1 ? '' : 's'}
            {state.data.has_more ? ' (showing first 200)' : ''}
          </p>
          <HcwsTable rows={state.data.rows} onReissue={setReissueTarget} />
        </>
      ) : null}

      {createOpen ? (
        <CreateHCWModal
          apiBaseUrl={apiBaseUrl}
          {...(fetchImpl ? { fetchImpl } : {})}
          onClose={() => setCreateOpen(false)}
          onCreated={() => setReloadTick((n) => n + 1)}
        />
      ) : null}

      {linksOpen ? (
        <FacilityLinksModal
          apiBaseUrl={apiBaseUrl}
          {...(fetchImpl ? { fetchImpl } : {})}
          {...(filters.facility_id ? { defaultFacilityId: filters.facility_id } : {})}
          onClose={() => setLinksOpen(false)}
        />
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

function HcwsTable({ rows, onReissue }: { rows: HcwRow[]; onReissue: (r: HcwRow) => void }): JSX.Element {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="border-b border-hairline text-left">
          <tr>
            <Th>HCW</Th>
            <Th>QN</Th>
            <Th>Facility</Th>
            <Th>Status</Th>
            <Th>Created</Th>
            <Th>
              <span className="sr-only">Row actions</span>
            </Th>
          </tr>
        </thead>
        <tbody className="divide-y divide-hairline">
          {rows.map((r) => (
            <tr key={r.hcw_id}>
              <Td mono>{r.hcw_id}</Td>
              <Td mono>{r.qn || '—'}</Td>
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
                  <Button
                    type="button"
                    variant="tableAction"
                    size="tableAction"
                    onClick={() => onReissue(r)}
                    className="text-warning"
                    title="Issue a new enrollment token (CAS-protected; admin only)"
                  >
                    Reissue
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
      : value === 'refusal'
        ? 'border-warning text-warning'
        : value === 'submitted'
          ? 'border-signal text-signal'
          : 'border-hairline text-muted-foreground';
  return (
    <span className={`rounded-sm border ${tone} px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider`}>
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
