# CSWeb Map Report — Spec

**Status:** v1 + v2 + v3 BUILT (2026-06-21) · **Author:** Carl (with Claude) · **Created:** 2026-06-21

> **Build note (2026-06-21):** v1 (pin map), v2 (F3 dual-point + low-accuracy /
> duplicate-location QA), and v3 (displacement + wrong-area QA) all shipped to
> `/docs/map.html` via `csweb-map-gen.py` (15-min cron). Open decisions resolved:
> OSM tiles (7.1), v1→v2→v3 (7.2), QA thresholds accuracy > 50 m / < 4 sat (7.3).
>
> **Field correction (v2):** the breakout stores `satellites = 0` on every record
> (test devices/emulator don't populate `gps(satellites)`), so the generator
> treats `sat ≤ 0` as *unreported* — otherwise every point false-flags as
> low-accuracy. Accuracy (10–20 m in test data) is the reliable signal.
>
> **v3 — full A+B+C (Carl's call).** Geo CODES in the breakout are
> survey-internal, **not PSGC** (Ilocos Norte = region 1/prov 2/citymun 800), so
> area joins are **by NAME** (region names word-reordered → sorted-token key;
> province names exact). Boundaries from `gen-ph-boundaries.py` →
> `/docs/assets/ph-areas.json` (faeldon PH JSON maps **2011 lowres**: 17 regions,
> 80 provinces; Batanes + Camiguin null-geometry → region fallback). The 15-min
> cron reads this static asset; re-run the prep only if the source/vintage
> changes. **Tier C asserts wrong-area only on positive containment in a
> *different* province** (robust to lowres border imprecision). Pure-Python
> ray-cast PIP (shapely not on the box). Tiers: A self-referential
> (home > 50 km from facility; facility > 5 km off its ≥3-case cluster centroid),
> B point beyond declared province's own radius from its centroid, C PIP. Test
> data demonstrates it: cases coded Ilocos Norte but captured in Laguna →
> 20/20 wrong-area (445.9 km, contained in Laguna), 4 cluster outliers.
>
> Backlog left open: city/municipality-level checks (city_name unreliable in
> current data), newer PSGC vintage if recent-split provinces appear.
**Sibling of:** the static Sync Dashboard (`csweb-dashboard-gen.py` →
`/docs/dashboard.html`). This is the **spatial** counterpart.

---

## 1. Goal

A static, filterable map of every synced CAPI case plotted at its captured GPS
point — answering the questions the dashboard can't: *where* is fieldwork
happening, *where* are the gaps, and *do the coordinates look trustworthy*.
Served by the existing CSWeb site (no new service), auto-refreshed on the same
cron as the dashboard.

Live target: `https://csweb.asiansocial.org/docs/map.html`

---

## 2. Data foundation (CONFIRMED 2026-06-21, on the box)

All three instruments capture **real device GPS**, auto-fetched once on focus
then protected (read-only). Coordinates **are flowing into the breakout DBs** in
dedicated relational tables keyed on `level-1-id` — the same join shape the
dashboard already uses. No case-blob decoding needed.

| Instrument | Point(s) | Breakout table | Lat / Lon columns |
|---|---|---|---|
| **F1** | Facility | `csweb_f1_breakout.rec_facility_capture` | `facility_gps_latitude`, `facility_gps_longitude` |
| **F3** | **Facility + Patient home** (two points) | `csweb_f3_breakout.rec_facility_capture` / `rec_patient_home_capture` | `facility_gps_*` / `p_home_gps_*` |
| **F4** | Household | `csweb_f4_breakout.household_geo_id` | `latitude`, `longitude` |

Each GPS record also carries `*_accuracy`, `*_altitude`, `*_satellites`,
`*_readtime` (UTC) — available for the QA layer.

**Storage gotchas:**
- Coordinates are **`varchar(12)`** → cast to decimal for plotting:
  `CAST(NULLIF(facility_gps_latitude,'') AS DECIMAL(10,6))`.
- **Desktop entry has no GPS radio** → ~1 blank per instrument observed in
  current test data (F1 3/4, F3 7/8, F4 4/5). The map MUST count and surface
  these "no-fix" cases rather than silently dropping them.
- Live sample coordinates verified, e.g. F1 facility `14.167793, 121.243788`
  (Rizal/Laguna test cluster — plausible PH points).

---

## 3. Architecture (reuse the dashboard's pattern)

A **new sibling generator** `csweb-map-gen.py`, NOT an extension of the
dashboard gen (different rendering lib, different per-row shape). It:

1. Runs ON the box (host `python3` + `docker compose exec` to MySQL), same as
   `csweb-dashboard-gen.py`.
2. Emits one **point row per case-per-layer** with `[lat, lon, instrument,
   layer, region, status, facility, qnum, date, accuracy]`.
3. Embeds the rows as XSS-safe JSON in `<script type="application/json"
   id="map-data">` + `JSON.parse(...)` — the exact pattern hardened in the
   dashboard (html.escape, `quote=False`).
4. Renders with **Leaflet** (vendored locally at `/docs/assets/`, like
   `chart.umd.min.js`) + **Leaflet.markercluster** for clustering.
5. Writes `/opt/app/lamp/www/docs/map.html`.
6. Cron: `*/15 * * * *` alongside the dashboard.

**Base tiles:** OpenStreetMap public tiles (browser fetches them; fine for
online use). → *Open decision 7.1 if offline/self-hosted tiles are required.*

**Filtering** is client-side (same as dashboard): the filter bar recomputes
which markers render, no server round-trip.

---

## 4. Features

### v1 — Pin map (mirrors the dashboard; fastest path)

- **One marker per case**, plotted at its GPS point, **marker-clustered** at low
  zoom (counts per cluster).
- **Color by Case Status** — Completed vs Partial (reuse the dashboard's
  `partial_save_mode` → status logic verbatim).
- **Filter bar identical to the dashboard:** Instrument · Region · Status ·
  Visit-From · Visit-To · Reset. Same labels, same behavior — consistency is the
  point.
- **Popup per pin:** instrument, full facility label (from
  `csweb_reports.facility_names`), questionnaire number, status, visit date,
  GPS accuracy (m).
- **"No GPS fix" counter** — a visible badge: *N cases not plotted (desktop /
  no fix)*, so the map never reads as more-complete than it is.
- **Auto-fit bounds** to the filtered set; legend for status colors.

### v2 — Field-supervision value (the part that earns its keep)

- **F3 dual-point layers** — Facility vs Patient-home as two toggleable layers
  (different marker shapes), optionally a connector line. Shows patient
  catchment — a view nothing else in the stack provides.
- **Spatial QA / curbstoning flags:**
  - Pins whose coordinates fall **outside PH bounds** (lat 4.5–21.5,
    lon 116–127) → flagged as bad/garbage.
  - **Identical / near-identical coordinate clusters** across distinct cases →
    possible desk-fabrication signal.
  - **Low-accuracy pins** (e.g. `accuracy > 50 m` or `satellites < 4`) styled
    distinctly.
  - This dovetails with the spec'd **Supervisor App** review layer
    (reads `CASE_DISPOSITION`); the map is the geographic complement.
- **Distance-from-expected check** *(stretch)* — flag a pin sitting far from its
  facility's expected admin area, using the PSGC codes already in
  `field_control`.

### Out of scope (v1/v2)

- Choropleth shading (we have points; revisit only if point coverage proves too
  sparse).
- Coverage-vs-target shading (needs the sample plan / target N per area — not
  yet wired).
- Interviewer track/day overlays — `INTERVIEWER_ID` is an as-built drift gap
  (may be absent); confirm before scoping.

---

## 5. Data model / SQL sketch

One UNION-ed query per instrument producing point rows (non-deleted cases only):

```sql
-- F4 example (household)
SELECT
  'f4' AS instrument, 'household' AS layer,
  CAST(NULLIF(g.latitude,'')  AS DECIMAL(10,6)) AS lat,
  CAST(NULLIF(g.longitude,'') AS DECIMAL(10,6)) AS lon,
  COALESCE(NULLIF(fc.region_name,''),'(unknown)') AS region,
  CASE WHEN c.partial_save_mode IS NULL OR c.partial_save_mode=''
       THEN 'Completed' ELSE 'Partial' END AS status,
  l.`questionnaire_number` AS qnum,
  COALESCE(CAST(fc.date_first_visited AS CHAR),'') AS date,
  CAST(NULLIF(g.hh_gps_accuracy,'') AS DECIMAL(8,1)) AS accuracy
FROM csweb_f4_breakout.`level-1` l
JOIN csweb_f4_breakout.cases c ON c.id=l.`case-id` AND c.deleted=0
LEFT JOIN csweb_f4_breakout.household_geo_id g ON g.`level-1-id`=l.`level-1-id`
LEFT JOIN csweb_f4_breakout.field_control fc ON fc.`level-1-id`=l.`level-1-id`;
```

- Rows with NULL lat/lon after cast → counted into the **no-fix badge**, not
  emitted as markers.
- F3 emits **two** rows per case (facility + patient-home layers).
- Facility label join → `csweb_reports.facility_names` (same as dashboard).
- The exact `field_control` date column differs per instrument
  (`date_first_visited` vs `date_first_visited_the_facility`) — mirror what the
  dashboard gen already resolved.

---

## 6. Edge cases & guardrails

- **varchar coords** → always cast + `NULLIF('')` guard.
- **PH-bounds validation** drops garbage coordinates from the plot but counts
  them in a "bad coordinate" tally (QA signal, not silent loss).
- **No-fix transparency** — desktop/blank cases surfaced as a badge.
- **XSS** — JSON-in-`<script type=application/json>` + `JSON.parse`, no string
  interpolation into HTML (hardened pattern from the dashboard).
- **Survives breakout redeploys** — reads breakout tables by name + the separate
  `csweb_reports` DB; no schema coupling beyond column names.
- **No new ports/services/DNS** — static file on the existing site.

## 7. Open decisions

1. **Base tiles** — OSM public tiles (online, zero-setup) vs self-hosted tiles
   (offline-capable, heavier). Recommend OSM for v1.
2. **v1 scope line** — ship v1 alone first, or fold F3 dual-point in
   immediately? Recommend v1 first (proves the data path), v2 next.
3. **QA thresholds** — confirm accuracy/satellite cutoffs for "low-quality"
   styling (proposed: `accuracy > 50 m` or `satellites < 4`).

## 8. Definition of done (v1)

- `csweb-map-gen.py` in `deliverables/CSWeb/`, deployed to `/opt/`, on the
  15-min cron.
- `map.html` live, pins render, clustering works, filter bar matches the
  dashboard, popups + status legend + no-fix badge present.
- Leaflet + markercluster vendored under `/docs/assets/` (no CDN JS).
- Browser-verified (chrome-devtools): marker counts reconcile to the DB,
  filters recompute, console clean.
- Linked from `help.html` (like the dashboard) and cross-linked map ↔ dashboard.
- `log.md` entry; this spec marked Built.
