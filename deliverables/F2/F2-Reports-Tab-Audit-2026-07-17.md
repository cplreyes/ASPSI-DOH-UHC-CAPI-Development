# F2 Reports Tab — Audit & Target Analysis (2026-07-17)

**Status:** AUDIT — findings + target definition. No code changed.
**Scope:** Operate → Reports in the HCW Survey Console (Sync Report + Map Report),
its backend (`/admin/api/dashboards/report/sync|map`), and everything the tab
depends on. Verified against prod (read-only, via the admin API as `se_001`).
**Method:** code read of `app/src/admin/report/*` + `server/src/admin/reports.ts`
+ store projections; live probes of the prod endpoints; comparison against the
original design spec (§7.7/§7.8, 2026-05-01) and the current data model
(slug links / self-registration / refusals / facility master, all 2026-07-16).

---

## 1. What the Reports tab is today (as built)

Two sub-tabs, both gated `dash_report`, both computed in JS over a
`readResponsesLite()` projection (per-row: submission_id, hcw_id, facility_id,
submitted_at_server, spec_version, lat/lng — **no `status`**; MySQL scan
capped at 50 000 rows, no ORDER BY).

**Sync Report** (`SyncReport.tsx` → `reports.ts syncReport()`)
- Pivot of response counts by geography, keyed on **PSGC prefixes of
  `facility_id`**: region = first 2 digits, province = first 4, facility = all 9.
- Columns: geo key (raw code), Submitted, Expected, %, Last submission.
- **Expected / % are hard-stubbed `null`** ("until F2_SampleFrame ingest") —
  they have rendered as "—" since May and still do.
- Date From/To filters (raw ISO string compare, client-of-store side).
- Each geo key links to `/admin/data?tab=responses&q=<key>`.

**Map Report** (`MapReport.tsx` → `reports.ts mapReport()`)
- Leaflet + Carto Positron, PH bounds, Verde markers; popup → ResponseDetail.
- Markers = responses with non-null `submission_lat/lng`; "N without GPS"
  rendered as plain text (no drill-down — known v2.0.2 follow-up).
- Sidebar groups by facility-id **prefix** (raw "04"-style codes; the code
  comment itself flags "real region grouping needs a facility lookup").
- Region filter = 2-digit prefix text input. No clustering yet (deliberate,
  documented threshold ~500 markers).

**GPS capture** (PWA side, `lib/geolocation.ts` + `App.tsx`): requested once at
the submit tap — 5 s timeout, `enableHighAccuracy:false`, every failure
(decline / unsupported / timeout) collapses silently to null. Consent-decline
(refusal) submissions **never** request GPS, by design (#825).

## 2. Live state (prod probes, 2026-07-17)

| Probe | Result |
|---|---|
| Sync region | `04` → submitted **4** |
| Sync province | `0403` → 4 |
| Sync facility | `040340210` → 4 |
| Responses by status | stored **3** · refusal **1** · rejected 0 |
| Map | **0 markers**, 4 "without GPS" |
| `responses?q=…` (any value) | **HTTP 500** — every search |
| `hcws?q=…` | 200 OK (control) |
| Sync `to=2026-07-16` | totals **0** (all 4 responses ARE dated 07-16) |
| Responses `to=2026-07-16` | total **0** (same bug, SQL path) |

## 3. Findings, ranked

### P0-1 · Responses search is 500-broken in prod — and every Sync drill-down depends on it
Every `q=` value against `GET /dashboards/data/responses` returns
`Internal Server Error` (non-JSON). The HCWs endpoint's `q` works; the only
structural difference is `CAST(values_json AS CHAR)` inside the Responses
`LOWER(CONCAT_WS(…)) LIKE ?` clause (`server/src/admin/store.ts:1663`) — the
classic MySQL illegal-mix-of-collations trap (JSON cast yields a binary-collated
string). Consequences:
- **All Sync Report drill-down links** (region / province / facility) land on
  "Backend unavailable".
- **The SEARCH box on the Data → Responses tab is broken in prod.** It escaped
  CI because the server suite exercises the shared aggregation + InMemory store;
  the MySQL `LIKE` clause has no integration test.
Fix shape (when approved): normalize the JSON cast's collation (e.g.
`CONVERT(values_json USING utf8mb4)` / explicit `COLLATE`), or drop
`values_json` from the haystack — searching raw answer JSON from the ops search
box is arguably scope creep anyway. Add a MySQL-store regression test.

### P0-2 · "Submitted" counts refusals (and would count rejected)
`LiteResponseRow` carries no `status`, so the pivot counts **every row in
f2_responses**. Live proof: Sync says 4 "submitted" for LPH-Bay; the Facilities
page — deployed yesterday with agreed semantics — says Submitted 3 / Refusals 1.
Two tabs of the same console now disagree on the same number. A refusal is a
fieldwork *outcome*, not a completed questionnaire; coverage math built on this
column overstates progress and hides refusal patterns. Fix: project `status`
into the lite row; pivot Submitted = `status <> 'refusal'` (and exclude
`rejected`), add Refusals as its own column (see §5).

### P1-3 · Expected/% never wired — the report cannot answer its own question
The whole point of a coverage report is "are we on track?" — both value columns
have been "—" since May. The blocker used to be "no sample frame"; **that
excuse expired on 2026-07-16**: `f2_facility_master` is now portal-managed with
full CRUD + CSV import. What's still missing is one number per facility
(target HCW count / quota). Precedent: the F1 static dashboard got real
denominators via `facility_lookup.dat` on 2026-07-15; F3/F4 wait on ASPSI
quotas. Given the 2026-06-22 meeting positioned the monitoring dashboard as the
basis for the contract extension, this is the highest-value missing feature in
the tab. Fix shape: `target_hcws` column on the facility master (editable +
import column), pivot joins and rolls it up per level.

### P1-4 · Map Report is empty in practice — 0 of 4 submissions carried GPS
Structurally the pipeline works (capture → column → endpoint → marker), but the
one-shot 5 s silent-null capture at submit yielded nothing across the whole
pretest so far. Candidate causes, unverified: permission denied/dismissed at
the prompt, OS location off, or acquisition timeout; the code gives no way to
tell — every failure is an indistinguishable null. The refusal path also never
asks (correct), so refusals permanently inflate "without GPS". Decide the
map's future before rollout:
- **(a) Fix capture** — record a `gps_status` (granted/denied/timeout/unsupported)
  so the failure mode becomes measurable; consider prompting earlier (review
  screen) so the permission dialog isn't racing the submit moment.
- **(b) Pivot to facility-level mapping** — markers at facility locations sized
  by submitted count. Needs facility coordinates (not in the master today) or
  PSGC-area centroids; degrades gracefully to a choropleth like the CSWeb map.
- Or both. Respondent-point maps of health workers are also a privacy surface —
  facility-level may be the better ops answer anyway.

### P1-5 · Geo keys render as raw codes, not names
Rows read "04", "0403", "040340210" — operators must decode PSGC prefixes and
facility IDs by memory. The facility master now holds facility_name, region,
province (canonical PSGC names, byte-aligned with the CSWeb dashboards). Join
it: facility level shows names; region/province levels can label via the master
(or the shipped PH_REGIONS constant). The MapReport sidebar has the same issue
and its own TODO comment acknowledging it.

### P2-6 · Drill-down links are the wrong filter even once the 500 is fixed
`q=<geo key>` free-text-matches submission ids, device fingerprints, and the
entire `values_json` — `q=04` is noise by construction. Facility rows should
link with `facility_id=<id>` (exists today, used by the Facilities page
deep-links). Region/province rows have no expressible Responses filter at all —
either add a server-side facility-prefix filter or link region rows to the
Facilities page filtered by region.

### P2-7 · `To` date excludes its own day — portal-wide
Proven live on both paths (§2): `to=2026-07-16` returns 0 against four
responses submitted 2026-07-16. Reports compare `"…T13:19:19Z" > "2026-07-16"`
(string), the Data tab compares `<= '2026-07-16 00:00:00'` (SQL) — same
outcome. An operator filtering "up to yesterday" silently loses a full day.
Also lurking: dates are UTC, fieldwork is Manila (+8) — a "today" filter loses
the 08:00–24:00 MNL window. Fix: normalize `to` to end-of-day (or `< to+1d`)
in ONE shared place, and decide the display/filter timezone (MNL) explicitly.

### P2-8 · No funnel visibility (started vs submitted)
Self-registration made "in progress" a first-class state (`sr-` + enrolled).
The Facilities page counts it per facility; Reports can't aggregate it by
geo — yet "N started but haven't finished at facility X" is exactly the pacing
signal supervisors act on during a wave.

### P3 (noted, low)
- `no_gps_count` includes refusals, which can never have GPS — overstates the
  "missing GPS" signal.
- Rows with empty `submitted_at_server` bypass date filters (JS path).
- Error copy still says "Apps Script staging may not be reachable" — stale era.
- Unordered `LIMIT 50000` scan: fine at survey scale, but silent truncation
  with no banner if ever exceeded.
- Spec §7.7 promised a CSV export and a "last 7 days" default; neither shipped
  (the empty-default is arguably better — matches the Data tab's #296 decision).
- Spec §7.8's "X cases without GPS — view list" link was downgraded to plain
  text; needs a `no_gps` filter on the Responses API to ever exist.

## 4. As-designed vs as-built (spec §7.7/§7.8 deltas)

| Spec promise (2026-05-01) | Shipped |
|---|---|
| Expected from PSGC sample frame + % complete | Stub — always "—" |
| Cell hyperlinks to filtered Data | Present but `q=`-based and currently 500 |
| CSV export (top-right) | Missing |
| Last-7-days default window | Empty default (deliberate, fine) |
| Days since last submission | Timestamp instead (fine) |
| Marker clustering | Deferred, documented threshold |
| Sidebar regions → zoom to PSGC bbox | Prefix count list, no zoom |
| "Without GPS → view list" | Plain-text count, no filter exists |

## 5. What the Reports tab SHOULD be (target definition)

For a facility-based HCW survey, the ops report is a **coverage/pacing table
vs targets** plus a **disposition breakdown** — the same shape as DHS field
check tables and the CSWeb sync dashboard operators already know.

**Sync Report → "Coverage" (per region / province / facility row):**

| Column | Source | Today |
|---|---|---|
| Geo name (+ code) | facility master join | code only |
| Facilities w/ active link | f2_facility_slugs | — |
| Target HCWs | **new**: master `target_hcws` (import column + Edit field) | — |
| Started (in-progress) | `sr-` + enrolled, per facility → rollup | — |
| Submitted | responses `status<>'refusal'` (== Facilities page) | inflated |
| Refusals (+ rate) | `status='refusal'` | lumped in |
| Coverage % | submitted / target | stub |
| Paper-encoded share | `source_path` | — |
| Last activity | max(submitted_at) | ✔ |
| Drill-down | `facility_id=` link / region→Facilities page | broken `q=` |

Plus: totals row, CSV export of the pivot (stakeholder-ready; the break-out
export infra already exists), Manila-day date window handled correctly, and
one shared count implementation with the Facilities overview so the two tabs
can never disagree again.

**Map Report:** keep, but decide P1-4 first. Minimum viable honesty: measure
GPS failure modes before rollout; add the no-GPS drill-down; label markers/
sidebar with facility names. Facility-centroid aggregation is the robust
fallback that works with zero respondent GPS.

**Explicitly NOT this tab's job:** the ~190 PSA-committed tabulation tables
(SSRCS Form 1 §II-9) — analysis-stage outputs, not ops monitoring; and
spec-version drift (already lives in Apps & Settings → Versioning).

## 6. Recommended sequence

1. **P0 hotfix pair** — Responses `q` 500 (collation) + `status` in the lite
   projection so Submitted/Refusals split correctly. Small, self-contained,
   restores the Data tab search too.
2. **Targets + names** — `target_hcws` on the master (CRUD + import), master
   join for geo names, real Expected/% columns. Turns the tab into the
   monitoring dashboard the extension case leans on.
3. **Link + date hygiene** — facility_id-based drill-downs, end-of-day `to`,
   Manila-day semantics, CSV export.
4. **Map decision** — instrument GPS capture, then choose respondent-point
   fix vs facility-level pivot (or both).

Each step is independently shippable; 1 is a bugfix, 2–4 warrant a short spec
against this document.
