---
title: "Survey Monitoring Dashboard — Benchmark & Integration Plan"
category: deliverable
tags: [csweb, sync-report, map-report, monitoring, dashboard, e4-csweb, e8-monitoring]
created: 2026-07-06
status: draft-for-review
benchmark_target: "Google Data Studio 'Survey Monitoring Dashboard' (link shared 2026-07-06)"
integrates_into: [csweb-dashboard-gen.py (dashboard.html), csweb-map-gen.py (map.html)]
---

# Survey Monitoring Dashboard — Benchmark & Integration Plan

## 0. Access caveat (read first)

I could **not open the live Data Studio link** from here — the browser tooling wasn't
connected and Data Studio is a JavaScript/auth-gated app a plain fetch can't render. So the
benchmark below is against the **standard survey-monitoring dashboard capability set** — the
same one our own `bi-dashboard-blueprint.md §5.1 (Fieldwork Coverage & Quality)` already
targets — **not a panel-by-panel read of that specific report.** Send a screenshot / PDF
export (or share it to my account) and I'll tighten every row to its exact tiles. The
integration plan itself is grounded in what our Sync Report and Map Report actually do today,
so it holds regardless.

---

## 1. What we're integrating into — our current reporting surfaces

| # | Surface | File / where | Tech | Refresh | What it does today |
|---|---|---|---|---|---|
| 1 | **CSWeb native** Sync + Map Report | built-in CSWeb (patched) | PHP/Twig + Leaflet | on breakout | One row per questionnaire number; native map (ESRI, PH view). Group-by limited to ID items. |
| 2 | **Sync Report (Visualization)** | `csweb-dashboard-gen.py` → `/docs/dashboard.html` | static **Chart.js** (vendored), on-box | **2 min** cron | Filters (instrument · region · status · visit-date); **case-status doughnut** (Completed/Partial) per instrument; counts; reads breakout DBs + the 12 `csweb_reports` views (F1 by region/prov/city/facility/ownership/service-level/result; F3 by region/type/sex; F4 by region/prov). |
| 3 | **Map Report** | `csweb-map-gen.py` → `/docs/map.html` | static **Leaflet + markercluster** | **15 min** cron | Pin per case, colored by status; **F3 dual-point** (facility + patient-home); **spatial QA** (out-of-PH-bounds, duplicate-location, low-accuracy, displacement > 50 km, wrong-province PIP); **no-GPS-fix badge**; filter bar mirrors the dashboard. |
| 4 | **BI / indicator dashboard** | `uhc-y2-dashboard-prototype.html` + `bi-dashboard-blueprint.md` | separate track (harmonized `uhc_y2` store) | post-ETL | The **analysis** dashboard (CHE, PhilHealth coverage, satisfaction…). Different job from fieldwork monitoring — noted so we don't conflate. |

**Scope of this plan:** surfaces **2 (Sync Report viz) and 3 (Map Report)** — the live
fieldwork-monitoring layer Carl named. Not the BI/indicator dashboard (#4).

---

## 2. Benchmark — standard survey-monitoring capabilities vs. what we have

Rating: ✅ have it · 🟡 partial · ⛔ missing.

| # | Monitoring capability (what a survey-monitoring dashboard is for) | Sync Report (dashboard.html) | Map Report (map.html) |
|---|---|---|---|
| A | **Headline KPI strip** — total completed, today, % of target, response rate | 🟡 counts, no scorecard strip | — |
| B | **Coverage vs. target** — completed ÷ sample target, per area/facility | ⛔ counts only, **no target** | ⛔ points only, no coverage shading |
| C | **Completion table** — expected vs landed by area/facility (STL reconciliation) | 🟡 counts by area (views), **no expected column** | — |
| D | **Submissions over time** — daily/cumulative trend by instrument | ⛔ current snapshot only | — |
| E | **Response / disposition rates** — AAPOR-style completed/partial/refused/non-contact | 🟡 Completed/Partial doughnut; no full disposition | — |
| F | **Productivity** — cases per enumerator / team / day | ⛔ (needs `interviewer_id`) | ⛔ (no interviewer track) |
| G | **Geographic coverage** — map of cases + area shading (choropleth) | — | 🟡 **points yes**, choropleth **no** |
| H | **Data-quality / anomaly flags** — bad GPS, duplicates, outliers, stuck cases | 🟡 thin (status only) | ✅ strong (spatial QA v2/v3) |
| I | **Filters / geo drill** — instrument · region→prov→city · date · status | ✅ | ✅ (mirrors dashboard) |
| J | **"Last updated" / freshness stamp** | 🟡 add if missing | 🟡 |
| K | **De-identified + no new services** (our hard constraints) | ✅ | ✅ |

**Where we already match or beat a typical monitoring dashboard:** filters + geo drill (I),
data-quality flags on the map (H — most Data Studio dashboards don't do curbstoning/GPS-QA),
and the static/no-new-service, near-real-time (2-min) delivery (K).

**Where we're behind:** the **progress-tracking** half — coverage-vs-target (B), time trend
(D), completion table with an expected column (C), the KPI strip (A), and productivity (F).
That is exactly what a "survey monitoring" dashboard exists to show: *how far along are we,
are we on pace, and who/where is lagging.*

---

## 3. The gaps that matter — in priority order

1. **Coverage vs. target (B + C + G-choropleth)** — the #1 monitoring question, "how far
   along are we, and where are the gaps?" We show *counts*; a monitoring dashboard shows
   *counts ÷ target*. **Unblocker:** a target N per area/facility — which we already have the
   makings of in the **`deliverables/CSPro/data/assignments/` layer** (assignment plan) and the
   facilities master. Wire target N → % complete gauges + an expected-vs-landed table + map
   area-shading.
2. **Submissions over time (D)** — "are we on pace?" A daily/cumulative line by instrument,
   from the visit-date already in the breakout. **No new data needed.**
3. **KPI strip + disposition (A + E)** — headline scorecards + a full disposition breakdown
   (we have `CASE_DISPOSITION` / Result-of-Visit from #515/#561). **No new data needed.**
4. **Productivity by enumerator/team (F)** — "who's producing, who's stuck?" **Blocked on
   `interviewer_id`** being present + populated (flagged as an as-built drift gap in the Map
   spec §4). Confirm before scoping.

---

## 4. Integration plan (phased) — into `dashboard.html` + `map.html`

Everything stays within our proven constraints: **static generators on the box, Chart.js /
Leaflet vendored, ≤2-min cron, de-identified, no new service/port/DNS.**

### Phase 1 — "on-pace" view, no new data (fastest win) → `csweb-dashboard-gen.py`
Buildable today from the breakout DBs alone:
- **KPI scorecard strip** (A): total completed · completed today · Completed/Partial split ·
  no-GPS-fix count · last-updated stamp (J).
- **Submissions-over-time line** (D): daily + cumulative by instrument (Chart.js line), from
  `date_first_visited*`.
- **Disposition/result bars** (E): full Result-of-Visit breakdown (already a `csweb_reports`
  view for F1; add F3/F4) — moves us from Completed/Partial toward AAPOR-style rates.
- **Freshness stamp** (J) on both surfaces.
- *Effort: ~1 focused build; all data present.*

### Phase 2 — coverage vs. target (the real monitoring value) → both surfaces
Needs one input: **target N per facility/area** (the assignment/sample plan).
- Wire `data/assignments/` (+ facilities master) → a **targets table** (target N per
  facility/region).
- **Dashboard:** % complete gauges per area/instrument + an **expected-vs-landed table**
  (the STL reconciliation view) with a shortfall column, sortable.
- **Map:** add a **choropleth layer** shading each area by % coverage (we already ship
  `/docs/assets/ph-areas.json` region/province boundaries for the v3 QA — reuse it), toggle
  against the existing pin layer.
- *Effort: moderate; gated only on confirming the target source + granularity.*

### Phase 3 — productivity (gated) → `csweb-dashboard-gen.py`
- If `interviewer_id` is present + populated: cases per enumerator / team / day, a productivity
  leaderboard, and a "stalled since" flag.
- **First step is a data check**, not a build — confirm `interviewer_id` survives the round-trip
  (Map spec flags it as possibly absent). If absent, this waits on an instrument change (post-freeze).

### Cross-cutting
- Keep the **filter bar identical** across dashboard + map (already the design rule).
- **De-identification** holds (area shading + centroids, not household points; no PII).
- Land Phase-1/2 tiles so they mirror the benchmark's layout where it makes sense — tighten to
  its exact panels once I can see it.

---

## 5. What I need to proceed

| Need | For | From |
|---|---|---|
| **Screenshot / PDF export of the live Data Studio dashboard** | tighten the benchmark to its exact panels + match layout | Carl / ASPSI |
| **Target / sample plan** — target N per facility/area (or confirm `data/assignments/` is the source) | Phase 2 coverage-vs-target | ASPSI (sample design) |
| **Confirm `interviewer_id`** is captured + populated per instrument | Phase 3 productivity | data check (Carl) |
| Refresh cadence OK at 2-min dashboard / (bump map to 2-min?) | ops | Carl |

---

## 6. Recommendation

- **Do Phase 1 now** — it's a pure win (KPI strip, time-trend, disposition, freshness), no
  dependencies, and it already closes the most visible gaps vs. a standard monitoring dashboard.
- **Phase 2 next**, as soon as the target/sample plan is wired — this is the actual reason a
  "survey monitoring dashboard" exists (coverage vs. target + the coverage map), and we already
  have the assignment data layer and the boundary asset to build it.
- **Phase 3 gated** on the `interviewer_id` data check.
- Keep this on the **on-box static stack** (not a move to Data Studio) — it's faster (2-min,
  no BigQuery/ETL dependency), self-hosted on the CSWeb box, and already beats a typical
  Data Studio report on GPS/data-quality. The BI/indicator track (#4) remains the separate,
  post-ETL analysis surface.

*Benchmark against the standard capability set pending a live view of the shared dashboard;
plan grounded in the current `dashboard.html` / `map.html` build (2026-07-06).*
