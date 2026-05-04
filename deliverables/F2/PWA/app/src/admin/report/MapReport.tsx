/**
 * F2 Admin Portal — Map Report (Leaflet + OpenStreetMap).
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.22)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.8)
 *
 * Switched 2026-05-04 from hand-rolled SVG to Leaflet + OSM tiles per
 * ASPSI directive. OSM chosen over Google Maps because:
 *   - Zero ongoing cost (no API key, no $200/mo credit billing surface)
 *   - Cleaner privacy posture for a health-survey ops console
 *   - No vendor lock-in (tile provider is one-line swap)
 *   - Bundle weight comparable to Google's loader for our use case
 * Verde Manual aesthetic preserved via a CSS `filter: grayscale(0.4)
 * saturate(0.7)` overlay on the tile layer — gives the map an ink-paper
 * tone that doesn't fight the rest of the portal's hairline aesthetic.
 *
 * Sidebar shows per-region submission counts. Clicking a marker opens a
 * Popup with hcw_id + facility_id + submitted_at + "View full case" link
 * to ResponseDetail.
 *
 * Marker clustering is NOT yet implemented — current ≤100-marker
 * production scale renders cleanly without it. When the dataset crosses
 * ~500 markers, wire `leaflet.markercluster` (already in package.json) by
 * wrapping the marker layer in a MarkerClusterGroup. Until then, the
 * cluster overhead isn't worth the bundle bytes.
 */
import { useEffect, useMemo, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
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

// Philippine bounding box, tight — covers the archipelago from the Sulu
// Sea up to Batanes without padding into Taiwan / Hong Kong / SCS chrome
// that doesn't matter for ASPSI fieldwork. MapContainer fitBounds() uses
// this on initial load; user pan/zoom is unconstrained after that.
const PH_BOUNDS: L.LatLngBoundsExpression = [
  [5.0, 117.0],
  [19.5, 126.5],
];

// Custom Verde-themed marker — signal-green dot with a contrasting ring
// stack. Sized 18px so it stands out clearly against Carto Positron's
// already-paper-toned tile palette (the previous 12px got lost). Built
// once at module load; reused across all markers (Leaflet's `divIcon` is
// HTML-based, no separate sprite/asset to manage).
const VERDE_MARKER_ICON = L.divIcon({
  className: 'verde-marker',
  html: '<span class="verde-marker__dot" aria-hidden="true"></span>',
  iconSize: [22, 22],
  iconAnchor: [11, 11],
  popupAnchor: [0, -11],
});

// (No "West Philippine Sea" overlay needed — Carto Positron's tiles render
// "West Philippine Sea" natively at the demo zoom level inside PH's EEZ.
// At very-zoomed-out views Carto falls back to the multilingual SCS stack,
// which is acceptable for the rare case the user zooms beyond PH bounds.)

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

function MapPlot({ markers, onHover }: {
  markers: Marker[];
  hovered: Marker | null;
  onHover: (m: Marker | null) => void;
}): JSX.Element {
  return (
    <div className="verde-leaflet-wrap border border-hairline bg-paper">
      <MapContainer
        bounds={PH_BOUNDS}
        scrollWheelZoom
        className="aspect-[3/4] w-full"
        attributionControl
      >
        {/* Carto Positron tiles — same OSM data, but Carto's stylesheet
            uses `name:en` when available so labels render in English
            (default OSM tiles served Hong Kong as 香港 etc.). Already in
            a soft grayscale tone, so the `.verde-leaflet-wrap` CSS filter
            is reduced to a light contrast nudge instead of full grayscale.
            Free, no API key, used in production by many admin/ops consoles
            (Linear, Stripe-adjacent, many gov dashboards). */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          subdomains={['a', 'b', 'c', 'd']}
          maxZoom={19}
        />
        {markers.map((m) => (
          <Marker
            key={m.submission_id}
            position={[m.lat, m.lng]}
            icon={VERDE_MARKER_ICON}
            eventHandlers={{
              click: () => onHover(m),
              popupclose: () => onHover(null),
            }}
          >
            <Popup>
              <div className="flex flex-col gap-1 font-mono text-xs">
                <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
                  Submission
                </p>
                <p className="text-sm">{m.hcw_id}</p>
                <p className="text-muted-foreground">{m.facility_id}</p>
                <p className="text-muted-foreground">
                  {formatTs(m.submitted_at)} · {m.lat.toFixed(3)}, {m.lng.toFixed(3)}
                </p>
                <Link
                  to={`/admin/data/responses/${encodeURIComponent(m.submission_id)}`}
                  className="mt-1 self-start text-[10px] uppercase tracking-wider text-signal underline-offset-4 hover:underline"
                >
                  View full case →
                </Link>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
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
