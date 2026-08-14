/**
 * F2 Admin Portal — Facilities page (Operate → Facilities).
 *
 * Spec: deliverables/F2/F2-Facilities-Page-Spec-2026-07-16.md (Approach A)
 * Diagram: deliverables/F2/F2-Facilities-Page-Design-2026-07-16.png
 *
 * READ-ONLY facility master list + per-facility /f/<slug> link management +
 * live counts (submitted · refusals · in-progress). One composite fetch
 * (GET /admin/api/facilities, limit=500); all writes go through the existing
 * facility-slugs upsert via FacilityLinkDialog / the row toggle.
 *
 * Filter state lives in the URL (shareable, #296: no implicit defaults).
 * Select options are captured from an UNFILTERED load only, so narrowing a
 * filter never shrinks the option lists.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
import { adminFetch, type ApiError } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { Link, useRouter } from '../lib/pages-router';
import { FacilityLinkDialog } from './FacilityLinkDialog';
import { FacilityEditDialog } from './FacilityEditDialog';
import { FacilityImportDialog } from './FacilityImportDialog';

export interface OverviewRow {
  facility_id: string;
  facility_name: string;
  facility_type: string;
  region: string;
  province: string;
  city_mun: string;
  archived: boolean;
  target_hcws: number | null; // spec F2-Coverage-Report-2026-07-17
  slug: string;
  active: boolean | null;
  url: string;
  submitted: number;
  refusals: number;
  in_progress: number;
}

interface ListData {
  rows: OverviewRow[];
  total: number;
  has_more: boolean;
}

export interface FacilitiesPageProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
}

interface UiFilters {
  q: string;
  region: string;
  province: string;
  facility_type: string;
  no_link: boolean;
  archived: boolean; // show archived rows (spec F2-Facility-Master-Mgmt)
}

function readFiltersFromUrl(): UiFilters {
  if (typeof window === 'undefined') {
    return { q: '', region: '', province: '', facility_type: '', no_link: false, archived: false };
  }
  const p = new URLSearchParams(window.location.search);
  return {
    q: p.get('q') ?? '',
    region: p.get('region') ?? '',
    province: p.get('province') ?? '',
    facility_type: p.get('facility_type') ?? '',
    no_link: p.get('no_link') === '1',
    archived: p.get('archived') === '1',
  };
}

function buildUiQuery(f: UiFilters): string {
  const p = new URLSearchParams();
  if (f.q) p.set('q', f.q);
  if (f.region) p.set('region', f.region);
  if (f.province) p.set('province', f.province);
  if (f.facility_type) p.set('facility_type', f.facility_type);
  if (f.no_link) p.set('no_link', '1');
  if (f.archived) p.set('archived', '1');
  return p.toString();
}

function buildApiQuery(f: UiFilters): string {
  const p = new URLSearchParams();
  if (f.q) p.set('q', f.q);
  if (f.region) p.set('region', f.region);
  if (f.province) p.set('province', f.province);
  if (f.facility_type) p.set('facility_type', f.facility_type);
  if (f.no_link) p.set('has_link', 'false');
  if (f.archived) p.set('include_archived', 'true');
  p.set('limit', '500');
  return p.toString();
}

const noFiltersActive = (f: UiFilters): boolean =>
  !f.q && !f.region && !f.province && !f.facility_type && !f.no_link && !f.archived;

interface SelectOptions {
  regions: string[];
  provinces: string[];
  types: string[];
}

type DialogTarget =
  | { kind: 'create'; row: OverviewRow }
  | { kind: 'view'; row: OverviewRow };

type EditTarget = { mode: 'create' } | { mode: 'edit'; row: OverviewRow };

export function FacilitiesPage({ apiBaseUrl, fetchImpl }: FacilitiesPageProps): JSX.Element {
  const { token, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();
  const [filters, setFilters] = useState<UiFilters>(() => readFiltersFromUrl());
  const [state, setState] = useState<
    | { kind: 'loading' }
    | { kind: 'loaded'; data: ListData }
    | { kind: 'failed'; error: ApiError }
  >({ kind: 'loading' });
  const [options, setOptions] = useState<SelectOptions | null>(null);
  const [dialog, setDialog] = useState<DialogTarget | null>(null);
  const [editTarget, setEditTarget] = useState<EditTarget | null>(null);
  const [importOpen, setImportOpen] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);
  const [reloadTick, setReloadTick] = useState(0);

  const apiQuery = useMemo(() => buildApiQuery(filters), [filters]);

  const fetchOpts = useCallback(
    () => ({
      ...(token ? { token } : {}),
      onUnauthorized: () => {
        clearAuth();
        navigate('/admin/login');
      },
      onPasswordChangeRequired: () => navigate('/admin/me/change-password'),
      ...(fetchImpl ? { fetchImpl } : {}),
    }),
    [token, clearAuth, navigate, fetchImpl],
  );

  useEffect(() => {
    let cancelled = false;
    setState({ kind: 'loading' });
    void (async () => {
      const r = await adminFetch<ListData>(
        `${apiBaseUrl}/admin/api/facilities?${apiQuery}`,
        { method: 'GET' },
        fetchOpts(),
      );
      if (cancelled) return;
      if (!r.ok) {
        setState({ kind: 'failed', error: r.error });
        return;
      }
      setState({ kind: 'loaded', data: r.data });
      // Capture select options from an UNFILTERED load only (spec: options
      // never depend on the current filter).
      if (noFiltersActive(filters)) {
        const uniq = (vals: string[]) => [...new Set(vals.filter(Boolean))].sort();
        setOptions({
          regions: uniq(r.data.rows.map((x) => x.region)),
          provinces: uniq(r.data.rows.map((x) => x.province)),
          types: uniq(r.data.rows.map((x) => x.facility_type)),
        });
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [apiBaseUrl, apiQuery, fetchOpts, reloadTick]);

  const applyFilters = (next: UiFilters) => {
    setFilters(next);
    const qs = buildUiQuery(next);
    navigate(`/admin/facilities${qs ? `?${qs}` : ''}`);
  };

  const reload = () => setReloadTick((n) => n + 1);

  const takenSlugs = useMemo(() => {
    if (state.kind !== 'loaded') return new Map<string, { facility_id: string; facility_name: string }>();
    return new Map(
      state.data.rows
        .filter((r) => r.slug)
        .map((r) => [r.slug, { facility_id: r.facility_id, facility_name: r.facility_name }]),
    );
  }, [state]);

  const knownProvinces = useMemo(() => {
    if (state.kind !== 'loaded') return [] as string[];
    return [...new Set(state.data.rows.map((r) => r.province).filter(Boolean))].sort();
  }, [state]);

  const archiveToggle = async (row: OverviewRow) => {
    const verb = row.archived ? 'Unarchive' : 'Archive';
    const liveLink =
      !row.archived && row.slug && row.active
        ? ` Its public link /f/${row.slug} stays LIVE until you deactivate it on this row.`
        : '';
    if (!window.confirm(`${verb} ${row.facility_name}?${liveLink}`)) return;
    await adminFetch(
      `${apiBaseUrl}/admin/api/facilities/${encodeURIComponent(row.facility_id)}`,
      { method: 'PATCH', body: JSON.stringify({ archived: !row.archived }) },
      fetchOpts(),
    );
    reload();
  };

  const toggle = async (row: OverviewRow) => {
    await adminFetch(
      `${apiBaseUrl}/admin/api/facility-slugs`,
      {
        method: 'POST',
        body: JSON.stringify({
          slug: row.slug,
          facility_id: row.facility_id,
          facility_name: row.facility_name,
          active: !row.active,
        }),
      },
      fetchOpts(),
    );
    reload();
  };

  const copy = async (key: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(key);
      setTimeout(() => setCopied(null), 2000);
    } catch {
      window.alert('Copy failed — select and copy manually.');
    }
  };

  return (
    <section className="flex flex-col gap-4 py-8">
      <header className="flex flex-wrap items-end justify-between gap-3 border-b border-hairline pb-4">
        <div>
          <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">Section</p>
          <h2 className="font-serif text-2xl font-medium tracking-tight">Facilities</h2>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button
            type="button"
            variant="outline"
            onClick={() => setImportOpen(true)}
            data-testid="facilities-import"
            className="h-10 border-hairline hover:bg-secondary"
            title="Batch import a facility wave CSV (dry-run first)"
          >
            Import CSV
          </Button>
          <Button
            type="button"
            onClick={() => setEditTarget({ mode: 'create' })}
            data-testid="facilities-add"
            className="h-10"
          >
            + Add facility
          </Button>
        </div>
      </header>

      <div className="flex flex-wrap items-end gap-4">
        <label className="flex flex-col gap-1">
          <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
            Search
          </span>
          <input
            type="text"
            value={filters.q}
            onChange={(e) => applyFilters({ ...filters, q: e.target.value })}
            placeholder="Name or facility ID…"
            data-testid="facilities-search"
            className="border-0 border-b border-hairline bg-transparent py-1 text-sm outline-none focus:border-signal"
          />
        </label>
        <FilterSelect
          label="Region"
          testid="facilities-region"
          value={filters.region}
          options={options?.regions ?? []}
          onChange={(v) => applyFilters({ ...filters, region: v })}
        />
        <FilterSelect
          label="Province"
          testid="facilities-province"
          value={filters.province}
          options={options?.provinces ?? []}
          onChange={(v) => applyFilters({ ...filters, province: v })}
        />
        <FilterSelect
          label="Type"
          testid="facilities-type"
          value={filters.facility_type}
          options={options?.types ?? []}
          onChange={(v) => applyFilters({ ...filters, facility_type: v })}
        />
        <Button
          type="button"
          variant={filters.no_link ? 'default' : 'outline'}
          onClick={() => applyFilters({ ...filters, no_link: !filters.no_link })}
          data-testid="facilities-no-link"
          className={filters.no_link ? 'h-9' : 'h-9 border-hairline hover:bg-secondary'}
        >
          No link yet
        </Button>
        <Button
          type="button"
          variant={filters.archived ? 'default' : 'outline'}
          onClick={() => applyFilters({ ...filters, archived: !filters.archived })}
          data-testid="facilities-archived"
          className={filters.archived ? 'h-9' : 'h-9 border-hairline hover:bg-secondary'}
        >
          Show archived
        </Button>
      </div>

      {state.kind === 'loading' ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : state.kind === 'failed' ? (
        <div role="alert" className="border-l-2 border-error py-2 pl-3">
          <p className="text-sm text-error">{messageFor(state.error)}</p>
          <div className="mt-2">
            <Button
              type="button"
              variant="outline"
              onClick={reload}
              className="h-9 border-hairline px-3 text-xs hover:bg-secondary"
            >
              Retry
            </Button>
          </div>
        </div>
      ) : (
        <>
          <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
            {state.data.total} facilities
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-hairline text-left">
                <tr>
                  <Th>Facility</Th>
                  <Th>Link</Th>
                  <Th>Status</Th>
                  <Th>Target</Th>
                  <Th>Submitted</Th>
                  <Th>Refusals</Th>
                  <Th>In progress</Th>
                  <Th>
                    <span className="sr-only">Actions</span>
                  </Th>
                </tr>
              </thead>
              <tbody className="divide-y divide-hairline">
                {state.data.rows.map((r) => (
                  <tr
                    key={r.facility_id}
                    data-testid={`facility-row-${r.facility_id}`}
                    className={r.archived ? 'opacity-60' : ''}
                  >
                    <td className="px-3 py-2 align-top">
                      <span className="block text-sm">
                        {r.facility_name}
                        {r.archived ? (
                          <span className="ml-2 inline-flex items-center border border-dashed border-hairline px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
                            Archived
                          </span>
                        ) : null}
                      </span>
                      <span className="block font-mono text-[10px] text-muted-foreground">
                        {r.facility_id} · {r.province}
                      </span>
                    </td>
                    <td className="px-3 py-2 align-top font-mono text-xs">
                      {r.slug ? (
                        `/f/${r.slug}`
                      ) : (
                        <span className="italic text-muted-foreground">— no link yet</span>
                      )}
                    </td>
                    <td className="px-3 py-2 align-top">
                      <StatusChip active={r.active} />
                    </td>
                    <td
                      className="px-3 py-2 align-top font-mono text-xs"
                      data-testid={`facility-target-${r.facility_id}`}
                    >
                      {r.target_hcws ?? '—'}
                    </td>
                    <td className="px-3 py-2 align-top font-mono text-xs">
                      <CountCell
                        value={r.submitted}
                        to={`/admin/data?tab=responses&facility_id=${r.facility_id}`}
                        testid={`facility-submitted-${r.facility_id}`}
                      />
                    </td>
                    <td className="px-3 py-2 align-top font-mono text-xs">
                      <CountCell
                        value={r.refusals}
                        to={`/admin/data?tab=responses&facility_id=${r.facility_id}&status=refusal`}
                        testid={`facility-refusals-${r.facility_id}`}
                      />
                    </td>
                    <td className="px-3 py-2 align-top font-mono text-xs">
                      <CountCell
                        value={r.in_progress}
                        to={`/admin/data?tab=hcws&facility_id=${r.facility_id}&status=enrolled&q=sr-`}
                        testid={`facility-inprogress-${r.facility_id}`}
                      />
                    </td>
                    <td className="px-3 py-2 align-top">
                      <div className="flex flex-wrap gap-2">
                        {r.slug ? (
                          <>
                            <Button
                              type="button"
                              variant="tableAction"
                              size="tableAction"
                              data-testid={`facility-qr-${r.facility_id}`}
                              onClick={() => setDialog({ kind: 'view', row: r })}
                            >
                              QR
                            </Button>
                            <Button
                              type="button"
                              variant="tableAction"
                              size="tableAction"
                              data-testid={`facility-copy-${r.facility_id}`}
                              onClick={() => void copy(r.facility_id, r.url)}
                            >
                              {copied === r.facility_id ? 'Copied' : 'Copy'}
                            </Button>
                            <Button
                              type="button"
                              variant="tableAction"
                              size="tableAction"
                              data-testid={`facility-toggle-${r.facility_id}`}
                              onClick={() => void toggle(r)}
                            >
                              {r.active ? 'Deactivate' : 'Activate'}
                            </Button>
                          </>
                        ) : (
                          <Button
                            type="button"
                            variant="tableAction"
                            size="tableAction"
                            data-testid={`facility-create-${r.facility_id}`}
                            onClick={() => setDialog({ kind: 'create', row: r })}
                          >
                            + Create link
                          </Button>
                        )}
                        <Button
                          type="button"
                          variant="tableAction"
                          size="tableAction"
                          data-testid={`facility-edit-${r.facility_id}`}
                          onClick={() => setEditTarget({ mode: 'edit', row: r })}
                        >
                          Edit
                        </Button>
                        <Button
                          type="button"
                          variant="tableAction"
                          size="tableAction"
                          data-testid={`facility-archive-${r.facility_id}`}
                          onClick={() => void archiveToggle(r)}
                        >
                          {r.archived ? 'Unarchive' : 'Archive'}
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-muted-foreground">
            Facility IDs are permanent once created; facilities are archived, never deleted.
          </p>
        </>
      )}

      {editTarget ? (
        <FacilityEditDialog
          apiBaseUrl={apiBaseUrl}
          {...(fetchImpl ? { fetchImpl } : {})}
          mode={editTarget.mode}
          initial={editTarget.mode === 'edit' ? editTarget.row : {}}
          knownProvinces={knownProvinces}
          onSaved={reload}
          onClose={() => setEditTarget(null)}
        />
      ) : null}

      {importOpen ? (
        <FacilityImportDialog
          apiBaseUrl={apiBaseUrl}
          {...(fetchImpl ? { fetchImpl } : {})}
          onApplied={reload}
          onClose={() => setImportOpen(false)}
        />
      ) : null}

      {dialog ? (
        <FacilityLinkDialog
          apiBaseUrl={apiBaseUrl}
          {...(fetchImpl ? { fetchImpl } : {})}
          facility={{
            facility_id: dialog.row.facility_id,
            facility_name: dialog.row.facility_name,
          }}
          existing={
            dialog.kind === 'view'
              ? { slug: dialog.row.slug, active: dialog.row.active === true, url: dialog.row.url }
              : null
          }
          takenSlugs={takenSlugs}
          onSaved={reload}
          onClose={() => setDialog(null)}
        />
      ) : null}
    </section>
  );
}

function FilterSelect({
  label,
  testid,
  value,
  options,
  onChange,
}: {
  label: string;
  testid: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
}): JSX.Element {
  return (
    <label className="flex flex-col gap-1">
      <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        data-testid={testid}
        className="border-0 border-b border-hairline bg-transparent py-1 text-sm outline-none focus:border-signal"
      >
        <option value="">All</option>
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </label>
  );
}

/** Counts deep-link into the Data tabs when non-zero; zero stays plain text. */
function CountCell({ value, to, testid }: { value: number; to: string; testid: string }): JSX.Element {
  if (value <= 0) return <span>{value}</span>;
  return (
    <Link
      to={to}
      data-testid={testid}
      className="underline underline-offset-4 hover:text-ink"
    >
      {value}
    </Link>
  );
}

function StatusChip({ active }: { active: boolean | null }): JSX.Element {
  if (active === null) return <span className="text-xs text-muted-foreground">—</span>;
  return active ? (
    <span className="inline-flex items-center border border-signal bg-signal/10 px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-signal">
      Active
    </span>
  ) : (
    <span className="inline-flex items-center border border-dashed border-hairline px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
      Off
    </span>
  );
}

function Th({ children }: { children?: React.ReactNode }): JSX.Element {
  return (
    <th className="px-3 py-2 font-mono text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
      {children}
    </th>
  );
}

function messageFor(error: ApiError): string {
  if (error.code === 'E_PERM_DENIED') return 'Your role lacks dash_users.';
  if (error.code === 'E_NETWORK') return 'Network unavailable. Retry when reconnected.';
  if (error.code === 'E_BACKEND') return 'Backend unavailable. Try again shortly.';
  return error.message ?? 'Could not load facilities.';
}
