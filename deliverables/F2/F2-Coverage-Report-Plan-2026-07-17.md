# F2 Coverage Report — Implementation Plan

> **For agentic workers:** execute inline, task by task, tests before deploy.
> Steps use checkbox syntax for tracking. NO git commits (Carl handles git).

**Goal:** Replace the Sync Report with the Coverage report per
`F2-Coverage-Report-Spec-2026-07-17.md` (approved): targets on the facility
master, geo-name rollups with an orphan bucket, single-sourced counts,
Manila-day date windows portal-wide, facility_id drill-downs, CSV export.

**Architecture:** one shared rollup (`rollupCoverage` in `reports.ts`) fed by
per-facility aggregate rows from either store; MySQL reuses the SAME count
subqueries as `listFacilitiesOverview` via extracted fragment builders. Date
windows become half-open UTC intervals produced by one `mnlWindow()` helper
used by coverage AND the Responses/Audit/DLQ/Map endpoints.

**Tech stack:** existing — Hono + mysql2 server, React/TS/Vite admin app,
vitest both sides. No new dependencies.

## Global constraints

- No git commits or version bumps (release-notes workflow owns versions).
- Verde Manual styling; tokens only; data-testids on new controls.
- Counts definitions byte-identical to the Facilities page: submitted =
  `status <> 'refusal'`; refusals = `= 'refusal'`; started = `f2_hcws
  hcw_id LIKE 'sr-%' AND status='enrolled'`.
- DDL applied to prod BEFORE backend rebuild (overview SELECT gains
  `m.target_hcws`).
- `target_hcws`: INT UNSIGNED NULL; valid = integer 0–9999 or null; 0/null
  both render "—" and yield `coverage_pct: null`.
- MNL window: date `d` ⇒ UTC `[d 00:00−08:00, d+1 00:00−08:00)`; full-ISO
  params pass through (from inclusive, to exclusive).

---

### Task 1: `mnlWindow()` helper + tests

**Files:** Create `server/src/admin/mnl-window.ts`, `server/test/mnl-window.test.ts`.

```ts
const MNL_OFFSET_MS = 8 * 3_600_000;
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
export interface UtcWindow { fromUtc?: string; toUtcExcl?: string }
export function mnlWindow(from?: string, to?: string): UtcWindow {
  const out: UtcWindow = {};
  if (from) out.fromUtc = DATE_RE.test(from)
    ? new Date(Date.parse(`${from}T00:00:00Z`) - MNL_OFFSET_MS).toISOString() : from;
  if (to) out.toUtcExcl = DATE_RE.test(to)
    ? new Date(Date.parse(`${to}T00:00:00Z`) - MNL_OFFSET_MS + 86_400_000).toISOString() : to;
  return out;
}
```

- [ ] Tests: `2026-07-16` → from `2026-07-15T16:00:00.000Z`, toExcl
      `2026-07-16T16:00:00.000Z`; ISO passthrough; both empty → `{}`.

### Task 2: half-open windows in Responses / Audit / DLQ / Map

**Files:** `server/src/admin/routes.ts` (parseRespFilters, parseAuditFilters,
parseDlqFilters, map route), `server/src/admin/store.ts` (3 InMemory + 3 MySQL
list methods), `server/src/admin/reports.ts` (mapReport bound), tests.

- [ ] Filters' `from`/`to` are redefined as UTC ISO, `to` EXCLUSIVE (JSDoc on
      `RespFilters`). Route parsers run raw params through `mnlWindow()`.
- [ ] InMemory: `r.x > f.to` → `r.x >= f.to`. MySQL: `<= isoToDt(f.to)` →
      `< isoToDt(f.to)`. Map route converts params; `mapReport` uses `>= to`.
- [ ] Boundary test: submission `2026-07-16T16:01:00.000Z` (= 00:01 MNL 07-17):
      `to=2026-07-16` excludes it, `from=2026-07-17` includes it; submission
      `2026-07-16T13:19:19.000Z` included by `to=2026-07-16`.

### Task 3: DDL — `target_hcws`

**Files:** `server/ddl/f2_api_tables.sql`.

- [ ] Guarded ALTER (information_schema PREPARE/EXECUTE pattern, same as
      `archived`): `ALTER TABLE f2_facility_master ADD COLUMN target_hcws INT UNSIGNED NULL`.

### Task 4: `target_hcws` through the master stack (server)

**Files:** `server/src/facility-master.ts`, `server/src/admin/store.ts`,
`server/src/admin/routes.ts`, `server/src/store.ts` (FacilityRow),
`server/test/facility-master*.test.ts`, `server/test/facilities-overview.test.ts`.

- [ ] `FacilityMasterInput` += `target_hcws?: number | null`; validator:
      non-null ⇒ `Number.isInteger && 0 ≤ n ≤ 9999` else error
      `'target_hcws must be an integer between 0 and 9999'` (NaN fails).
- [ ] `FacilityRow` += `target_hcws?: number | null` (PWA readFacilities
      untouched). `FacilityMasterRecord`/`FacilityOverviewRow` carry
      `target_hcws: number | null`.
- [ ] InMemory + MySQL create/get/update/overview read+write the column
      (MySQL: INSERT column, dynamic SET, `mapDbFacilityMaster`, overview
      SELECT `m.target_hcws`).
- [ ] `facilityInputFrom` parses number|numeric-string|''|null →
      number|NaN|null (NaN → validator error, never silent). PATCH accepts
      `target_hcws`; import verdict `changes` detects it.
- [ ] Tests: validator range/NaN; create+patch roundtrip; import sets/updates
      target; overview row carries it.

### Task 5: `rollupCoverage()` + `coverageReport()` in both stores

**Files:** `server/src/admin/reports.ts`, `server/src/admin/store.ts`,
`server/test/coverage.test.ts` (new).

- [ ] `reports.ts`: `CoverageLevel`, `CoverageRow` (spec shape),
      `CoverageFacility` (per-facility aggregate: facility_id/name/region/
      province/archived/link_active/target_hcws/started/submitted/refusals/
      paper_encoded/last_activity), `CoverageOrphan`, and
      `rollupCoverage(level, facilities, orphans)` → `{ level, rows, totals }`:
      keys = region|province names (`'(unspecified)'` when blank) |
      facility_id; label = key except facility level → facility_name; orphan
      bucket `'(not in master)'` sorts last; target = sum of non-null targets,
      null when ALL null; refusal_rate = `round(refusals/(submitted+refusals)*1000)/10`
      or null at 0 total; coverage_pct = `round(submitted/target*100)` when
      target>0 else null; totals row key/label `'TOTAL'`.
- [ ] `store.ts`: extract the overview's response-counts + in-progress
      subqueries into builder consts shared with coverage (single source).
      `AdminStore.coverageReport(f)` on both stores: produce
      `CoverageFacility[]` (respecting `include_archived`, date window on the
      response aggregates; started undated) + orphans (responses LEFT JOIN
      master IS NULL, same window) → return `rollupCoverage(...)`.
      `link_active` = facility has ANY active slug.
- [ ] Tests: 3 levels incl. multi-facility province; orphan bucket; archived
      default-off + include; window boundaries; target math (null/0/sum);
      refusal-only row; **parity test: facility-level CoverageRow counts ===
      listFacilitiesOverview counts on the same fixture**.

### Task 6: route swap `/report/sync` → `/report/coverage`

**Files:** `server/src/admin/routes.ts`, `server/src/admin/reports.ts`,
`server/test/admin.test.ts`.

- [ ] Add `GET /dashboards/report/coverage` (gate `dash_report`; level/from/
      to/include_archived via `mnlWindow`); delete the sync route and
      `syncReport()` (+ its types); `readResponsesLite` stays (map/versioning).
- [ ] Replace sync tests with coverage-route tests (shape + RBAC).

### Task 7: frontend — `CoverageReport.tsx` + CSV export

**Files:** create `app/src/admin/report/CoverageReport.tsx`,
`app/src/admin/report/coverage-csv.ts`, `app/src/admin/report/CoverageReport.test.tsx`;
modify `ReportDashboard.tsx`; delete `SyncReport.tsx` + `SyncReport.test.tsx`;
update `admin.dashboards.a11y.test.tsx` mock.

- [ ] Tab key/label → `coverage` / "Coverage" (legacy `?tab=sync` falls back
      to the default tab = Coverage). Map tab untouched.
- [ ] CoverageReport: level pills + From/To dates + "Show archived" toggle
      (URL-synced: `level/from/to/archived`), hairline table with columns
      Geography · Facilities · Links · Target · Started · Submitted ·
      Refusals (count + small % when non-null) · Coverage % (value + inline
      hairline bar) · Paper · Last activity; totals row (mono,
      border-t); facility rows link Geography → `/admin/data?tab=responses&facility_id=`
      and Started → `/admin/data?tab=hcws&facility_id=…&status=enrolled&q=sr-`;
      region/province rows → `/admin/facilities?region=`/`?province=`;
      "(not in master)" row muted + warning chip → `/admin/facilities`;
      "—" for null target/coverage; Export CSV button (`coverage-export`)
      downloads `coverageCsv(rows, totals)` as
      `f2-coverage-<level>-<yyyymmdd>.csv` via Blob anchor.
- [ ] `coverage-csv.ts`: pure `coverageCsv(rows, totals): string` with
      RFC-quoting (mirror parse-csv quoting rules).
- [ ] Tests: renders columns + totals; pills/toggle change fetch query + URL;
      drill-down hrefs; null renders "—"; csv unit test (quoting, header,
      totals line); error banner on E_PERM_DENIED.

### Task 8: target field on Facilities surfaces

**Files:** `app/src/admin/facilities/{FacilityEditDialog,FacilityImportDialog,FacilitiesPage,parse-csv}.tsx|ts` + their tests.

- [ ] parse-csv: header may be the 7-col OR 8-col (`…,barangay,target_hcws`)
      template; row gains `target_hcws: string` ('' when 7-col); template
      download emits 8 columns.
- [ ] Import dialog: pass `target_hcws` through (raw string; server parses —
      NaN becomes a per-row error, never silently null).
- [ ] Edit dialog: "Target HCWs" numeric-inputMode field (`edit-target`),
      blank ⇒ null; sent on both POST and PATCH.
- [ ] FacilitiesPage: Target column (mono; "—" when null), OverviewRow type
      += target_hcws.
- [ ] Tests: 8-col + 7-col parse, wrong-header error; dialog sends
      target_hcws; page renders target.

### Task 9: Help page + nav copy

**Files:** `app/src/admin/help/HelpPage.tsx`, `app/src/admin/Layout.tsx`.

- [ ] Reports sub-tabs article: Sync Report row → Coverage row (columns,
      targets-from-master, "(not in master)" bucket, Facilities-parity note).
- [ ] Dashboard-guide gist for Reports mentions Coverage vs targets; glossary
      adds `target_hcws` / "coverage %". Layout nav description already says
      "Coverage" — verify, adjust if stale.

### Task 10: verify, deploy (DDL first), live-probe, record

- [ ] `tsc -b --force` + eslint + full vitest, server and app; app prod build
      (VITE_F2_PROXY_URL) with bundle checks.
- [ ] Apply the guarded ALTER on prod (scp ddl + docker exec mysql) BEFORE
      the backend rebuild; then `deploy_model_c_full.sh`.
- [ ] Probes (read-only, se_001): coverage all 3 levels (LPH-Bay row =
      3/1 with real names); `to=2026-07-16` now INCLUDES the 4 MNL-07-16
      submissions; `q=lph` still 200; legacy `/report/sync` → 404.
- [ ] Update spec status → DEPLOYED w/ numbers; update memory
      `project_aspsi_f2_reports_tab.md`; final report to Carl.

## Self-review

Spec coverage: decisions 1–6 map to Tasks 3–4 (targets), 5 (names/orphans/
single-source), 4+8 (CSV lane), 2 (dates portal-wide), 6–7 (route/tab swap),
7 (CSV export, drill-downs) ✔. No placeholders; types named consistently
(`CoverageRow`, `rollupCoverage`, `mnlWindow`, `target_hcws`) ✔. Facilities
page counts stay authoritative via shared fragments ✔.
