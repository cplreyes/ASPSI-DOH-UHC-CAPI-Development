---
title: "Goal Prompt — Survey Monitoring Dashboard Integration"
category: deliverable
tags: [csweb, sync-report, map-report, monitoring, dashboard, goal-prompt, e4-csweb, e8-monitoring]
created: 2026-07-06
executes: Survey-Monitoring-Dashboard-Benchmark-and-Integration-Plan.md
status: ready-to-run
---

# Goal Prompt — Survey Monitoring Dashboard Integration

*A self-contained execution prompt. Hand this to a fresh session/agent (or use it yourself
next sprint) to build the monitoring layer into our two static CSWeb reporting surfaces. It
carries all the context an executor needs without this conversation's history.*

---

## MISSION

Upgrade the ASPSI-DOH UHC CAPI fieldwork-monitoring surfaces so they answer the three
questions a "survey monitoring dashboard" exists to answer — **how far along are we, are we on
pace, and who/where is lagging** — while staying on our proven **static, on-box, no-new-service**
stack. Do it in the phase order below; Phase 1 has zero dependencies and ships first.

The plan being executed is
`deliverables/CSWeb/Survey-Monitoring-Dashboard-Benchmark-and-Integration-Plan.md` — **read it
first.** This prompt is the build spec derived from it.

---

## THE TWO SURFACES YOU ARE EDITING

| Surface | Generator (edit this) | Output (on the box) | Refresh |
|---|---|---|---|
| **Sync Report (Visualization)** | `deliverables/CSWeb/csweb-dashboard-gen.py` | `/opt/app/lamp/www/docs/dashboard.html` → `https://csweb.asiansocial.org/docs/dashboard.html` | 2-min flock cron |
| **Map Report** | `deliverables/CSWeb/csweb-map-gen.py` | `/opt/app/lamp/www/docs/map.html` → `.../docs/map.html` | 2-min flock cron |

Both are **Python generators that run ON the CSWeb box** — they shell out via
`docker compose exec` to MySQL, read the breakout DBs, and write a single self-contained HTML
file with **vendored** Chart.js / Leaflet (no CDN). There is **no separate service, port, or DNS** —
the existing site serves the file. Keep it that way.

### Data sources (already wired in the generators — reuse, don't re-invent)
- **Breakout DBs:** `csweb_f1_breakout`, `csweb_f3_breakout`, `csweb_f4_breakout` — one
  labeled row per non-deleted case (geo / facility / ownership / result / patient-type / sex /
  `date_first_visited*` / partial-save status).
- **`csweb_reports` views** — 12 SQL views (e.g. `facility_names`, per-instrument by-area
  rollups). New aggregate needs → prefer a view in `gen-report-views.py` over ad-hoc SQL.
- **`STATUS`** expression (already defined in both files): Completed (fully saved) vs Partial
  (`partial_save_mode` set).
- **GPS** (map only): dedicated capture tables keyed on `level-1-id`
  (`rec_facility_capture.facility_gps_*`, F3 `rec_patient_home_capture.p_home_gps_*`,
  F4 `household_geo_id`). Area joins are **by NAME** (geo codes are survey-internal, not PSGC).
- **Boundary asset** (map only): `/opt/app/lamp/www/docs/assets/ph-areas.json` (built by
  `gen-ph-boundaries.py`) — already loaded for the v3 wrong-area QA. **Reuse it for the
  choropleth** in Phase 2.

---

## HARD CONSTRAINTS (do not violate)

1. **Static on-box only.** No new service/port/DNS, no BigQuery/ETL dependency, no live server
   process. A generator writes one HTML file; cron re-runs it. (This is the deliberate call vs.
   moving to Data Studio — do not "upgrade" to a hosted BI tool.)
2. **Vendored libs, no CDN.** Chart.js / Leaflet / markercluster are served from `/docs/assets/`.
   Any new lib must be vendored the same way. No `<script src="https://…">`.
3. **De-identified.** Aggregates, area shading, facility centroids — **never household-level PII**
   on a shared surface. Choropleths shade areas; they do not plot homes.
4. **Generator-first.** Edit the `.py` generators (and `gen-report-views.py` for new SQL views).
   **Never hand-edit the generated `dashboard.html` / `map.html`** — cron overwrites them in 2 min.
5. **Filter bar stays identical** across dashboard + map (existing design rule: Instrument ·
   Region→Prov→City · Visit-date · Status). New filters get added to *both*.
6. **No git operations.** Leave changes in the working tree; Carl handles git manually. Do not
   commit, push, branch, or add versioning commentary.
7. **Box execution reality — build a local sample path.** The generators can only fully run on
   the box (they need `docker compose exec` MySQL). To develop/verify tiles without box access,
   add a `--sample <fixture.json>` (or `--demo`) mode that feeds canned rows through the same
   render functions, and check the produced HTML locally in a browser. Do NOT claim a tile works
   until it has rendered against either the box data or a representative fixture. On-box
   verification against real synced cases is the final gate (may be Carl's step).

---

## PHASE 1 — "on-pace" view (no new data) → `csweb-dashboard-gen.py`

Everything here is buildable **today** from the breakout DBs alone. Ship this first.

**Build:**
1. **KPI scorecard strip** at the top of the dashboard: total completed · completed today ·
   Completed/Partial split · no-GPS-fix count (mirror the map's badge) · **last-updated stamp**.
   Scorecards recompute client-side under the existing filters, same as the charts.
2. **Submissions-over-time line** (Chart.js line): daily + cumulative counts by instrument, from
   `date_first_visited*`. Respects the Visit-date and Instrument filters.
3. **Disposition / Result-of-Visit bars**: full breakdown (not just Completed/Partial). F1
   already has a Result-of-Visit view; **add the equivalent for F3/F4** (via `gen-report-views.py`
   if a view is cleaner). Moves us toward AAPOR-style rates.
4. **Freshness stamp** ("Data as of <cron time>") on **both** dashboard and map.

**Acceptance:** on a filtered view, the KPI strip, the time-trend line, and the disposition bars
all recompute consistently with the existing doughnut/bar charts; numbers reconcile with the
current per-instrument counts; no CDN calls; file still self-contained; renders under `--sample`.

---

## PHASE 2 — coverage vs. target (the real monitoring value) → BOTH surfaces

Needs one input, **which we already have**: `deliverables/CSPro/data/assignments/assignments-source.csv`
carries a **`target_count`** column per `ea_facility_code` + `instrument` (cols:
`ea_facility_code, enumerator_id, instrument, target_count, ea_name, cluster`). That is the
target-N source. Confirm granularity with Carl (facility-level vs rolled to province) before
building, and confirm whether ASPSI's real EA plan has replaced the R6 fixture rows yet.

**Build:**
1. **Targets table**: read `assignments-source.csv` (+ facilities master for names) → target N per
   facility / area / instrument. Ship the target table onto the box alongside the generators
   (a small CSV or a generated `csweb_reports` view), so the on-box generator can join
   completed-count ÷ target.
2. **Dashboard:** % complete gauges per area/instrument + an **expected-vs-landed table** (STL
   reconciliation) with a shortfall column, sortable, filter-aware.
3. **Map:** add a **choropleth layer** shading each area by % coverage — reuse
   `/docs/assets/ph-areas.json` (already loaded for v3 QA), toggle against the existing pin layer.
   Shade by area only (de-identified).

**Acceptance:** coverage % = completed ÷ target per area reconciles against the Phase-1 counts;
shortfall column sums correctly; choropleth toggles cleanly with the pin layer and respects
filters; missing/zero-target areas render as "no target" not divide-by-zero.

---

## PHASE 3 — enumerator productivity (GATED — data check before build) → `csweb-dashboard-gen.py`

**Do the data check first, not the build.** Confirm whether an interviewer/enumerator identifier
actually **survives the CSEntry → sync → breakout round-trip** into the breakout DB case rows.
(`assignments-source.csv` has `enumerator_id`, but that is the *assignment plan*, not proof the
*synced case* carries who collected it. The Map spec flags this as a possible as-built gap.)

- **If present + populated:** build cases-per-enumerator / team / day, a productivity
  leaderboard, and a "stalled since" flag. Keep it team/enumerator-ID level (no personal names on
  the shared surface unless Carl approves).
- **If absent:** stop and report — this needs an instrument change, which is **post-freeze**
  (the pretest freeze stands; data-integrity exceptions only). Do not force it.

**Acceptance:** either a working productivity panel backed by a real per-case identifier, or a
clear written finding that the identifier is absent + what instrument change would be needed.

---

## INPUTS TO CONFIRM WITH CARL BEFORE / DURING

| Need | Blocks | Ask |
|---|---|---|
| Screenshot / PDF of the live Data Studio "Survey Monitoring Dashboard" | tightening tiles to match its exact layout (nice-to-have, not a blocker) | Carl / ASPSI |
| `target_count` granularity (facility vs province) + whether ASPSI's real EA plan has replaced the R6 fixture | Phase 2 | Carl |
| Does a per-case interviewer/enumerator ID exist in the breakout DBs? | Phase 3 | data check (Carl / on-box query) |
| Map refresh already at 2-min? (confirm parity with dashboard) | ops | Carl |

---

## DEPLOY MECHANICS (on-box, no git)

The generators live in the repo but **run on the CSWeb box** at `/opt/`:
- Deploy = `scp` the edited generator to `/opt/` (Carl's step or an agreed deploy path); cron
  already runs it every 2 min (flock-guarded). No service restart.
- The dashboard cron: `*/2 * * * * flock -n /tmp/csweb-dashboard.lock bash -c "cd /opt/app && python3 /opt/csweb-dashboard-gen.py" >> /var/log/csweb-dashboard.log 2>&1` (map is the sibling).
- **Verify after deploy** by loading the live URL and checking the freshness stamp advanced +
  the new tiles render against real synced cases. That on-box verification is the real gate.

---

## READ FIRST (grounding docs, all in-repo)

1. `deliverables/CSWeb/Survey-Monitoring-Dashboard-Benchmark-and-Integration-Plan.md` — the plan
   this executes (benchmark matrix + phase rationale).
2. `deliverables/CSWeb/csweb-dashboard-gen.py` + `csweb-map-gen.py` — the code you're extending
   (read the module docstrings — they document the whole data model + cron + vendored libs).
3. `deliverables/CSWeb/CSWeb-Sync-Report-and-Case-Breakout-Setup.md` — breakout DBs, the 12
   `csweb_reports` views, on-box patches, cron.
4. `deliverables/CSWeb/CSWeb-Map-Report-Spec.md` — map v1/v2/v3 features + spatial QA + the
   `ph-areas.json` boundary reuse + the `interviewer_id` gap note.
5. `deliverables/CSPro/data/assignments/README.md` + `assignments-source.csv` — the Phase-2
   target-N source.
6. `deliverables/CSWeb/bi-dashboard-blueprint.md` — the SEPARATE post-ETL BI/indicator track
   (CHE, coverage, satisfaction). **Not** this task — read only to avoid conflating the two;
   don't build indicator analytics into the fieldwork monitor.

---

## DEFINITION OF DONE

- **Phase 1** shipped into `csweb-dashboard-gen.py`: KPI strip + submissions-over-time +
  disposition bars + freshness stamp on both surfaces; renders under `--sample` and (verified by
  Carl) on-box; self-contained, no CDN, filter-aware.
- **Phase 2** shipped into both generators once the target source is confirmed: coverage gauges +
  expected-vs-landed table + map choropleth; numbers reconcile; de-identified.
- **Phase 3** either shipped (if the per-case ID exists) or a clear written finding that it's
  blocked on a post-freeze instrument change.
- Filter bar identical across both surfaces; no new service/port/DNS; vendored libs only.
- No git operations performed. Changes left in the working tree for Carl.
- `log.md` entry written (what shipped, which phase, deploy status); memory updated only if a
  standing fact changed (e.g. a new `csweb_reports` view, or the interviewer_id finding).

---

*Derived 2026-07-06 from the benchmark & integration plan; grounded in the live
`csweb-dashboard-gen.py` / `csweb-map-gen.py` build.*
