/**
 * Report aggregations — behavior-parity ports of backend/src/AdminReports.js
 * (adminSyncReport / adminMapReport) and AdminData.js (adminFormRevisions),
 * computed over LiteResponseRow projections so both stores share ONE
 * implementation. Shapes match worker/src/admin/handlers/data.ts exactly.
 */
import type { LiteResponseRow } from './store.js';

// ---------------------------------------------------------------------------
// Coverage report (spec F2-Coverage-Report-2026-07-17) — replaces the Sync
// Report. Geography comes from the facility master (names, not ID prefixes);
// count definitions are byte-identical to the Facilities page; targets roll up
// from f2_facility_master.target_hcws. Both stores hand per-facility aggregate
// rows to ONE shared rollup so their results can never drift.
// ---------------------------------------------------------------------------

export type CoverageLevel = 'region' | 'province' | 'facility';

export interface CoverageRow {
  key: string; // region/province name | facility_id | '(not in master)' | 'TOTAL'
  label: string; // facility level: facility_name; otherwise = key
  facilities: number;
  links_active: number;
  target: number | null; // sum of non-null targets; null when none set
  started: number; // sr- + enrolled (in-progress self-registrations)
  submitted: number; // status <> 'refusal' — Facilities-page definition
  refusals: number;
  refusal_rate: number | null; // refusals/(submitted+refusals), 1 dp %; null at 0 total
  coverage_pct: number | null; // submitted/target, whole %; null when target null/0
  paper_encoded: number; // paper-encoded subset of submitted
  last_activity: string; // max(submitted_at_server) incl. refusals, ISO
}

export interface CoverageReportData {
  level: CoverageLevel;
  rows: CoverageRow[];
  totals: CoverageRow; // key/label 'TOTAL'
}

/** Per-facility aggregate a store hands to the shared rollup. */
export interface CoverageFacility {
  facility_id: string;
  facility_name: string;
  region: string;
  province: string;
  link_active: boolean;
  target_hcws: number | null;
  started: number;
  submitted: number;
  refusals: number;
  paper_encoded: number;
  last_activity: string;
}

/** Responses whose facility_id has no master row — surfaced, never dropped. */
export interface CoverageOrphan {
  facility_id: string;
  submitted: number;
  refusals: number;
  paper_encoded: number;
  last_activity: string;
}

export const COVERAGE_ORPHAN_KEY = '(not in master)';
const UNSPECIFIED_KEY = '(unspecified)';

function blankRow(key: string, label: string): CoverageRow {
  return {
    key,
    label,
    facilities: 0,
    links_active: 0,
    target: null,
    started: 0,
    submitted: 0,
    refusals: 0,
    refusal_rate: null,
    coverage_pct: null,
    paper_encoded: 0,
    last_activity: '',
  };
}

function finishRates(r: CoverageRow): void {
  const outcomes = r.submitted + r.refusals;
  r.refusal_rate = outcomes > 0 ? Math.round((r.refusals / outcomes) * 1000) / 10 : null;
  r.coverage_pct =
    r.target != null && r.target > 0 ? Math.round((r.submitted / r.target) * 100) : null;
}

export function rollupCoverage(
  level: CoverageLevel,
  facilities: CoverageFacility[],
  orphans: CoverageOrphan[],
): CoverageReportData {
  const byKey = new Map<string, CoverageRow>();
  const keyOf = (f: CoverageFacility): string =>
    level === 'facility'
      ? f.facility_id
      : level === 'province'
        ? f.province || UNSPECIFIED_KEY
        : f.region || UNSPECIFIED_KEY;

  for (const f of facilities) {
    const key = keyOf(f);
    let row = byKey.get(key);
    if (!row) {
      row = blankRow(key, level === 'facility' ? f.facility_name || f.facility_id : key);
      byKey.set(key, row);
    }
    row.facilities++;
    if (f.link_active) row.links_active++;
    if (f.target_hcws != null) row.target = (row.target ?? 0) + f.target_hcws;
    row.started += f.started;
    row.submitted += f.submitted;
    row.refusals += f.refusals;
    row.paper_encoded += f.paper_encoded;
    if (f.last_activity > row.last_activity) row.last_activity = f.last_activity;
  }

  const rows = [...byKey.values()];
  rows.sort((a, b) => (a.key < b.key ? -1 : a.key > b.key ? 1 : 0));

  if (orphans.length > 0) {
    const orphanRow = blankRow(COVERAGE_ORPHAN_KEY, COVERAGE_ORPHAN_KEY);
    for (const o of orphans) {
      orphanRow.submitted += o.submitted;
      orphanRow.refusals += o.refusals;
      orphanRow.paper_encoded += o.paper_encoded;
      if (o.last_activity > orphanRow.last_activity) orphanRow.last_activity = o.last_activity;
    }
    rows.push(orphanRow); // always sorts last
  }

  const totals = blankRow('TOTAL', 'TOTAL');
  for (const r of rows) {
    finishRates(r);
    totals.facilities += r.facilities;
    totals.links_active += r.links_active;
    if (r.target != null) totals.target = (totals.target ?? 0) + r.target;
    totals.started += r.started;
    totals.submitted += r.submitted;
    totals.refusals += r.refusals;
    totals.paper_encoded += r.paper_encoded;
    if (r.last_activity > totals.last_activity) totals.last_activity = r.last_activity;
  }
  finishRates(totals);

  return { level, rows, totals };
}

export interface MapMarker {
  submission_id: string;
  hcw_id: string;
  facility_id: string;
  lat: number;
  lng: number;
  submitted_at: string;
}

export interface MapReportData {
  markers: MapMarker[];
  no_gps_count: number;
  /** Why the no-GPS rows lack coordinates (audit P1-4 instrumentation):
   *  denied | timeout | unavailable | unsupported | not_requested | unknown
   *  ('unknown' = legacy rows ingested before gps_status existed). */
  no_gps_breakdown: Record<string, number>;
}

export function mapReport(
  rows: LiteResponseRow[],
  filters: { from?: string; to?: string; region_id?: string; province_id?: string },
): MapReportData {
  const markers: MapMarker[] = [];
  let noGps = 0;
  const breakdown: Record<string, number> = {};
  for (const row of rows) {
    // Refusals never request geolocation (#825 — consent was declined), so they
    // can't be "missing" GPS; counting them inflated no_gps_count (audit P3).
    if (row.status === 'refusal') continue;
    if (filters.from && row.submitted_at_server && row.submitted_at_server < filters.from) continue;
    // `to` is an EXCLUSIVE UTC upper bound (mnlWindow half-open semantics).
    if (filters.to && row.submitted_at_server && row.submitted_at_server >= filters.to) continue;
    if (filters.region_id && row.facility_id && row.facility_id.slice(0, 2) !== filters.region_id) continue;
    if (filters.province_id && row.facility_id && row.facility_id.slice(0, 4) !== filters.province_id) continue;
    const lat = row.submission_lat;
    const lng = row.submission_lng;
    const hasGps = lat != null && lng != null && Number.isFinite(lat) && Number.isFinite(lng);
    if (!hasGps) {
      noGps++;
      const why = row.gps_status || 'unknown';
      breakdown[why] = (breakdown[why] ?? 0) + 1;
      continue;
    }
    markers.push({
      submission_id: row.submission_id,
      hcw_id: row.hcw_id,
      facility_id: row.facility_id,
      lat,
      lng,
      submitted_at: row.submitted_at_server,
    });
  }
  return { markers, no_gps_count: noGps, no_gps_breakdown: breakdown };
}

export interface FormRevision {
  spec_version: string;
  count: number;
  last_seen_at: string;
}

export interface FormRevisionsData {
  revisions: FormRevision[];
  total: number;
}

export function formRevisions(rows: LiteResponseRow[]): FormRevisionsData {
  const byVersion = new Map<string, FormRevision>();
  for (const row of rows) {
    const v = row.spec_version || '(unknown)';
    let entry = byVersion.get(v);
    if (!entry) {
      entry = { spec_version: v, count: 0, last_seen_at: '' };
      byVersion.set(v, entry);
    }
    entry.count++;
    const ts = row.submitted_at_server || '';
    if (ts > entry.last_seen_at) entry.last_seen_at = ts;
  }
  const revisions = [...byVersion.values()];
  revisions.sort((a, b) => (a.spec_version < b.spec_version ? 1 : a.spec_version > b.spec_version ? -1 : 0));
  return { revisions, total: revisions.reduce((n, r) => n + r.count, 0) };
}
