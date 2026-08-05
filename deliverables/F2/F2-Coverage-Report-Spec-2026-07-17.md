# F2 Admin — Coverage Report (Sync Report redesign)

**Status:** **DEPLOYED to prod 2026-07-17** (uhc-hcw.asiansocial.org) — Coverage
live at all 3 levels with real geo names (verified: LPH-Bay 3 submitted /
1 refusal / 25% rate; Manila-day `to=2026-07-16` now returns all 4 responses,
was 0; legacy /report/sync 404s; q-search regression clean). `target_hcws`
column applied BEFORE the backend rebuild; targets all null until ASPSI quotas
land.
**Verified:** 132/132 server tests (+15 incl. overview-parity), 595/595 app
tests (+9 net), clean tsc/eslint both sides, production build checks OK.
**Plan:** `F2-Coverage-Report-Plan-2026-07-17.md` (executed same day).
**Owner:** Carl.
**Basis:** `F2-Reports-Tab-Audit-2026-07-17.md` §5–6 (approved direction:
"Start with the P0 hotfix, then spec the coverage redesign").
**Prereq shipped:** the P0 hotfix (2026-07-17) — Responses/Audit/DLQ `q` search
collation fix + Submitted/Refusals split in the current Sync Report.
**Builds on:** `F2-Facility-Master-Mgmt-Spec-2026-07-16.md` (facility master
CRUD + CSV import — this spec adds one column to that lane).

## Premise

The Sync Report answers "how many rows"; fieldwork monitoring needs "are we on
track, where, and where is it stalling". The facility master (portal-managed
since 2026-07-16) finally provides the frame; the missing piece is one target
number per facility. This spec turns the Sync Report into a **Coverage**
report: per-geography progress vs targets, with the same count definitions as
the Facilities page, real geography names, working drill-downs, Manila-day
date semantics, and CSV export. The Map Report is untouched (its GPS decision
is a separate item, audit P1-4).

## Decisions (locked unless Carl objects)

1. **Targets live on the facility master** — `target_hcws INT UNSIGNED NULL`
   — not a separate quota table. One number per facility, managed through the
   exact CRUD + CSV lane that already exists. NULL = "no target yet" (renders
   "—", contributes nothing to rollup targets); 0 is treated the same as NULL
   for coverage math (no division by zero, renders "—").
2. **Geography comes from the master, not from ID prefixes.** Rollup keys are
   the master's `region` / `province` **names** (canonical PSGC strings).
   Responses whose `facility_id` is missing from the master roll into a
   visible **"(not in master)"** bucket row — an integrity signal, never
   silently dropped.
3. **Count semantics are single-sourced.** Submitted = `status<>'refusal'`,
   Refusals = `='refusal'`, Started = `f2_hcws hcw_id LIKE 'sr-%' AND
   status='enrolled'` — the SAME aggregation subqueries the Facilities
   overview uses, extracted into one shared implementation so the two surfaces
   cannot drift.
4. **Archived facilities are excluded by default** (rows AND denominators);
   a "Show archived" toggle includes them. Parity with the Facilities page.
5. **Manila-day date windows, fixed once, portal-wide.** A shared helper
   converts a `YYYY-MM-DD` from/to pair into a UTC half-open window
   [from 00:00 MNL, to+1d 00:00 MNL). The Coverage endpoint uses it, and the
   existing Responses / Audit / DLQ list endpoints are switched to it in the
   same change (closes audit P2-7: `to=` currently excludes its own day).
6. **Old endpoint replaced.** `GET /dashboards/report/sync` is superseded by
   `GET /dashboards/report/coverage`; the portal is the API's only client, so
   the sync route + `syncReport()` + `SyncReport.tsx` are removed, not kept in
   parallel. Tab label becomes **Coverage**.

## Data model (additive, idempotent DDL)

```sql
-- Guarded ALTER, same information_schema pattern as `archived`:
ALTER TABLE f2_facility_master ADD COLUMN target_hcws INT UNSIGNED NULL;
```

- **Edit dialog:** numeric "Target HCWs" field (optional; integer 0–9999;
  blank = NULL). Frozen semantics otherwise unchanged.
- **CSV import:** header gains an optional 8th column `target_hcws`.
  Both the 7-column and 8-column headers validate (backward compatible — old
  wave files keep working). Non-integer / negative values are per-row errors;
  blank = NULL. Template download emits the 8-column header.
- **Facilities page list:** shows Target next to the counts (plain text).

## Backend

### `GET /admin/api/dashboards/report/coverage` (gate: `dash_report`)

Query: `level=region|province|facility` (default region), `from`, `to`
(Manila dates), `include_archived=true` (default false).

Row shape (per geo key at the level):

```ts
interface CoverageRow {
  key: string;            // region name | province name | facility_id
  label: string;          // same as key, except facility level: facility_name
  facilities: number;     // facilities in this bucket (1 at facility level)
  links_active: number;   // facilities with an ACTIVE /f/ slug
  target: number | null;  // SUM(target_hcws); null when no facility has one
  started: number;        // sr- + enrolled (in-progress self-registrations)
  submitted: number;      // status<>'refusal'  ← same def as Facilities page
  refusals: number;
  refusal_rate: number | null;   // refusals/(submitted+refusals), 1dp %; null when 0 total
  coverage_pct: number | null;   // submitted/target, whole %; null when target null/0
  paper_encoded: number;         // source_path='paper_encoded' subset of submitted
  last_activity: string;         // max(submitted_at_server) incl. refusals, ISO
}
```

Response: `{ level, rows: CoverageRow[], totals: CoverageRow /* key='TOTAL' */ }`.
Rows sorted by key asc; the "(not in master)" bucket (if any) sorts last.

### Store

New `AdminStore.coverageReport(level, filters)` on both stores:
- **MySQL:** `f2_facility_master` LEFT JOIN the response-count subquery
  (submitted/refusals/paper_encoded/last_activity per facility_id) LEFT JOIN
  the in-progress subquery LEFT JOIN the deduped-active-slug subquery —
  **the same three subqueries `listFacilitiesOverview` uses, extracted to
  shared SQL fragment constants** — then grouped by the level key in SQL.
  Orphan responses found via `f2_responses LEFT JOIN master … WHERE m.facility_id
  IS NULL` aggregate into the "(not in master)" row.
- **InMemory:** same logic over the in-memory maps (shared helper where
  practical); behavior-parity tested.

`syncReport()` is deleted with the old route. `readResponsesLite` stays —
`mapReport()` and `formRevisions()` (Versioning panel) still consume it,
unchanged.

### Shared date-window helper

`server/src/dates.ts`: `mnlWindow(from?: string, to?: string): { fromUtc?: string; toUtcExcl?: string }`
(+08:00, half-open). Adopted by: coverage, listResponses, listAudit, listDlq
(both stores — SQL `>= ? AND < ?`, InMemory string compare on ISO). Existing
behavior "empty timestamp bypasses the filter" is preserved.

## Frontend

`CoverageReport.tsx` replaces `SyncReport.tsx`; ReportDashboard tab renamed
**Coverage** (tooltip: "Fieldwork progress vs facility targets by region /
province / facility"). Verde Manual table, testids `coverage-*`.

- Level pills (Region / Province / Facility), From/To date inputs (Manila),
  "Show archived" toggle.
- Columns: Geography · Facilities · Active links · Target · Started ·
  Submitted · Refusals (+rate) · Coverage % · Paper · Last activity.
  Facility level: Geography cell = facility name + mono facility_id.
  Null target/coverage render "—". Coverage % also renders a thin inline bar
  (hairline track, signal fill) — no chart library.
- **Totals row** pinned at the bottom (mono, hairline-topped).
- **Drill-downs:** facility rows → `/admin/data?tab=responses&facility_id=<id>`
  (Started count → HCWs tab, same params as the Facilities page counts);
  region/province rows → `/admin/facilities?region=<name>` /
  `…?province=<name>`. No more free-text `q=` links.
- **Export CSV** button (top-right, per original spec §7.7): client-side CSV
  of the loaded rows + totals, filename
  `f2-coverage-<level>-<yyyymmdd>.csv`. No new dependency (hand-rolled
  serializer mirroring `parse-csv.ts` quoting).
- "(not in master)" row renders muted with a warning chip linking to the
  Facilities page ("add this facility to the master").
- Empty state: "No fieldwork activity in this window." Error states per the
  standard adminFetch codes.

## Help page (ships with implementation)

Reports section of the Operator Guide rewritten: Coverage columns explained,
"targets come from the facility master — set them per facility or via CSV
import", the "(not in master)" bucket, and the Facilities↔Coverage count
equivalence. Glossary gains `target_hcws` / "coverage %".

## Testing

- **Server:** target validation (blank/0/negative/non-int; 8-col and 7-col
  import headers); coverage rollups at all three levels incl. multi-facility
  provinces; orphan bucket; archived default-off + toggle; refusal_rate /
  coverage_pct math incl. null target and 0-total edges; MNL date window
  boundaries (submission at 2026-07-16T16:01Z = 00:01 MNL 07-17 lands in the
  07-17 window, not 07-16); **parity test asserting a facility-level coverage
  row equals the Facilities-overview counts for the same fixture**; Data-tab
  endpoints honor the new inclusive `to`; RBAC (dash_report).
- **App:** render + level switching + URL sync; drill-down hrefs; totals row;
  CSV content snapshot; "—" rendering; archived toggle; a11y pass; ResponsesTab
  regression for the now-inclusive date filters.
- Suites green, tsc/eslint clean, prod build checks, DDL-first deploy (new
  column is read by the overview → apply ALTER before backend rebuild, same
  as `archived`).

## Out of scope

- Map Report changes / GPS instrumentation (audit P1-4 — separate decision).
- Time-series pacing chart (submissions per day) — candidate follow-up once
  Coverage lands.
- Per-enumerator productivity, PSA tabulation tables (analysis-stage).
- Sourcing the actual target numbers (ASPSI's quotas land whenever they land —
  the column is nullable and the report degrades to today's behavior).

## Rollout

1. DDL (guarded ALTER) to prod first.
2. Backend + frontend in one deploy (standing UAT autodeploy).
3. Targets entered when ASPSI provides quotas; until then Coverage % shows "—"
   but Started/Submitted/Refusals/names/links work immediately.
