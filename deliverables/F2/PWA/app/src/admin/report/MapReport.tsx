/**
 * F2 Admin Portal — Map Report.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.22)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.8)
 *
 * Hand-rolled SVG plot of submission lat/lng over a Philippine bounding
 * box. Avoiding Leaflet keeps the bundle lean and matches Verde Manual:
 * a sparse data plot with hairline rules and signal-color markers, not
 * a colorful tile-based GIS map. The spec calls for clustering at zoom
 * <12 to handle 13K markers; that's a future concern when the dataset
 * grows — for now (≤ a few hundred markers) the SVG renders fine.
 *
 * Sidebar shows per-region submission counts. Clicking a region marker
 * opens a tooltip with hcw_id + facility_id + submitted_at; clicking
 * again navigates to /admin/data/responses/:id (the detail page).
 */
import { useEffect, useMemo, useState } from 'react';
import { adminFetch, type ApiError } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { Link, useRouter } from '../lib/pages-router';

interface Marker {
  submission_id: string;
  hcw_id: string;
  facility_id: string;
  lat: number;
  lng: number;
  submitted_at: string;
}

interface MapReportData {
  markers: Marker[];
  no_gps_count: number;
}

export interface MapReportProps {
  apiBaseUrl: string;
  fetchImpl?: typeof fetch;
}

interface UiFilters {
  from: string;
  to: string;
  region_id: string;
}

// Philippine bounding box, generously padded.
const LNG_MIN = 116.5;
const LNG_MAX = 127.0;
const LAT_MIN = 4.5;
const LAT_MAX = 21.5;
const SVG_WIDTH = 600;
const SVG_HEIGHT = 800;

function project(lat: number, lng: number): { x: number; y: number } {
  const x = ((lng - LNG_MIN) / (LNG_MAX - LNG_MIN)) * SVG_WIDTH;
  const y = SVG_HEIGHT - ((lat - LAT_MIN) / (LAT_MAX - LAT_MIN)) * SVG_HEIGHT;
  return { x, y };
}

function defaultFromIso(): string {
  return new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
}

function readFiltersFromUrl(): UiFilters {
  if (typeof window === 'undefined') {
    return { from: defaultFromIso(), to: '', region_id: '' };
  }
  const p = new URLSearchParams(window.location.search);
  return {
    from: p.get('from') ?? defaultFromIso(),
    to: p.get('to') ?? '',
    region_id: p.get('region_id') ?? '',
  };
}

function buildApiQuery(f: UiFilters): string {
  const p = new URLSearchParams();
  if (f.from) p.set('from', f.from);
  if (f.to) p.set('to', f.to);
  if (f.region_id) p.set('region_id', f.region_id);
  return p.toString();
}

export function MapReport({ apiBaseUrl, fetchImpl }: MapReportProps): JSX.Element {
  const { token, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();
  const [filters, setFilters] = useState<UiFilters>(() => readFiltersFromUrl());
  const [state, setState] = useState<
    | { kind: 'loading' }
    | { kind: 'loaded'; data: MapReportData }
    | { kind: 'failed'; error: ApiError }
  >({ kind: 'loading' });
  const [hovered, setHovered] = useState<Marker | null>(null);

  const apiQuery = useMemo(() => buildApiQuery(filters), [filters]);

  useEffect(() => {
    let cancelled = false;
    setState({ kind: 'loading' });
    void (async () => {
      const r = await adminFetch<MapReportData>(
        `${apiBaseUrl}/admin/api/dashboards/report/map?${apiQuery}`,
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

  // Group markers by region (2-char facility prefix) for the sidebar.
  const regionCounts = useMemo(() => {
    if (state.kind !== 'loaded') return new Map<string, number>();
    const m = new Map<string, number>();
    for (const marker of state.data.markers) {
      const key = String(marker.facility_id).slice(0, 2) || '—';
      m.set(key, (m.get(key) ?? 0) + 1);
    }
    return m;
  }, [state]);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-3 border-b border-hairline pb-3">
        <FilterDate label="From" value={filters.from} onChange={(v) => setFilters({ ...filters, from: v })} />
        <FilterDate label="To" value={filters.to} onChange={(v) => setFilters({ ...filters, to: v })} />
        <FilterText label="Region" value={filters.region_id} onChange={(v) => setFilters({ ...filters, region_id: v })} placeholder="e.g. 05" />
      </div>

      {state.kind === 'loading' ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : state.kind === 'failed' ? (
        <ErrorBanner error={state.error} />
      ) : state.kind === 'loaded' ? (
        <div className="flex flex-col gap-4 lg:flex-row">
          <div className="flex-1">
            <MapPlot
              markers={state.data.markers}
              hovered={hovered}
              onHover={setHovered}
            />
            <p className="mt-2 font-mono text-xs uppercase tracking-wider text-muted-foreground">
              {state.data.markers.length} marker{state.data.markers.length === 1 ? '' : 's'}
              {state.data.no_gps_count > 0 ? (
                <>
                  {' · '}
                  <Link
                    to={`/admin/data?tab=responses&q=submission_lat`}
                    className="text-error underline-offset-4 hover:underline"
                  >
                    {state.data.no_gps_count} without GPS
                  </Link>
                </>
              ) : null}
            </p>
          </div>
          <aside className="lg:w-64">
            <h3 className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
              By region
            </h3>
            {regionCounts.size === 0 ? (
              <p className="mt-2 text-sm text-muted-foreground">No GPS-tagged submissions yet.</p>
            ) : (
              <ul className="mt-2 divide-y divide-hairline border-y border-hairline">
                {Array.from(regionCounts.entries())
                  .sort((a, b) => b[1] - a[1])
                  .map(([region, count]) => (
                    <li key={region} className="flex items-center justify-between py-2 text-sm">
                      <button
                        type="button"
                        onClick={() => setFilters({ ...filters, region_id: region })}
                        className="font-mono text-xs underline-offset-4 hover:underline"
                      >
                        {region}
                      </button>
                      <span className="font-mono text-xs text-muted-foreground">{count}</span>
                    </li>
                  ))}
              </ul>
            )}
            {hovered ? (
              <HoveredCard marker={hovered} onClear={() => setHovered(null)} />
            ) : null}
          </aside>
        </div>
      ) : null}
    </div>
  );
}

function MapPlot({ markers, hovered, onHover }: {
  markers: Marker[];
  hovered: Marker | null;
  onHover: (m: Marker | null) => void;
}): JSX.Element {
  return (
    <div className="border border-hairline bg-paper">
      <svg
        viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
        className="aspect-[3/4] w-full"
        role="img"
        aria-label="Submission locations across the Philippines"
      >
        {/* Hairline grid (5° lat/lng). Provides geographic context without tiles. */}
        {[5, 10, 15, 20].map((lat) => {
          const { y } = project(lat, LNG_MIN);
          return (
            <g key={`lat-${lat}`}>
              <line x1={0} y1={y} x2={SVG_WIDTH} y2={y} stroke="hsl(var(--border))" strokeWidth={0.5} strokeDasharray="2 4" />
              <text x={4} y={y - 2} className="fill-muted-foreground" fontSize={9} fontFamily="ui-monospace, monospace">
                {lat}°N
              </text>
            </g>
          );
        })}
        {[118, 121, 124, 127].map((lng) => {
          const { x } = project(LAT_MIN, lng);
          return (
            <g key={`lng-${lng}`}>
              <line x1={x} y1={0} x2={x} y2={SVG_HEIGHT} stroke="hsl(var(--border))" strokeWidth={0.5} strokeDasharray="2 4" />
              <text x={x + 2} y={SVG_HEIGHT - 4} className="fill-muted-foreground" fontSize={9} fontFamily="ui-monospace, monospace">
                {lng}°E
              </text>
            </g>
          );
        })}
        {/* Marker plot — signal color circles, hairline stroke. */}
        {markers.map((m) => {
          const { x, y } = project(m.lat, m.lng);
          const isHovered = hovered?.submission_id === m.submission_id;
          return (
            <circle
              key={m.submission_id}
              cx={x}
              cy={y}
              r={isHovered ? 6 : 3}
              className={isHovered ? 'fill-signal stroke-ink' : 'fill-signal/70 stroke-signal'}
              strokeWidth={1}
              onMouseEnter={() => onHover(m)}
              onMouseLeave={() => onHover(null)}
              onFocus={() => onHover(m)}
              onBlur={() => onHover(null)}
              style={{ cursor: 'pointer' }}
              tabIndex={0}
            >
              <title>
                {m.hcw_id} · {m.facility_id}
              </title>
            </circle>
          );
        })}
      </svg>
    </div>
  );
}

function HoveredCard({ marker, onClear }: { marker: Marker; onClear: () => void }): JSX.Element {
  return (
    <div className="mt-3 border border-hairline bg-secondary/20 p-3 text-sm">
      <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">Marker</p>
      <p className="mt-1 font-mono text-xs">{marker.hcw_id}</p>
      <p className="font-mono text-xs text-muted-foreground">{marker.facility_id}</p>
      <p className="mt-2 font-mono text-xs text-muted-foreground">
        {formatTs(marker.submitted_at)} · {marker.lat.toFixed(3)}, {marker.lng.toFixed(3)}
      </p>
      <div className="mt-2 flex flex-wrap gap-3">
        <Link
          to={`/admin/data/responses/${encodeURIComponent(marker.submission_id)}`}
          className="font-mono text-xs uppercase tracking-wider text-muted-foreground underline-offset-4 hover:text-ink hover:underline"
        >
          View full case
        </Link>
        <button
          type="button"
          onClick={onClear}
          className="font-mono text-xs uppercase tracking-wider text-muted-foreground hover:text-ink"
        >
          Dismiss
        </button>
      </div>
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

function FilterText({ label, value, onChange, placeholder }: { label: string; value: string; onChange: (v: string) => void; placeholder?: string }): JSX.Element {
  return (
    <label className="flex flex-col gap-1">
      <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">{label}</span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="border-0 border-b border-hairline bg-transparent py-1 font-mono text-sm outline-none focus:border-signal"
      />
    </label>
  );
}

function formatTs(iso: string): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
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
              : (error.message ?? 'Failed to load Map Report.')}
      </p>
      {error.requestId ? (
        <p className="mt-1 font-mono text-xs text-muted-foreground">ref {error.requestId}</p>
      ) : null}
    </div>
  );
}
