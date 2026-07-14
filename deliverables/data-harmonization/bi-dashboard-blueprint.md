---
type: deliverable
kind: bi-blueprint
audience: DOH-PMSMD · ADB · ASPSI data team + consulting team · analysts
prepared_by: Carl Patrick L. Reyes
date_drafted: 2026-06-03
status: draft-for-review
related_task: E4-INT-002
builds_on: [data-harmonization/codebook.md, data-harmonization/etl-spec.md]
tags: [integration, bi, looker, dashboard, harmonization, e4]
---

# UHC Year 2 — BI Dashboard Blueprint (Looker Studio over the unified store)

A buildable blueprint for the **#177** dashboard prototype over the harmonized analysis store. It defines the **data source**, a thin **semantic layer** (BigQuery views + calculated UHC metrics), the **page/chart inventory**, and the **build + governance** rules — so the live prototype is a wiring exercise once the ETL produces a (dry-run or real) `uhc_y2` dataset.

> **Grounding.** Data source = the `uhc_y2` BigQuery dataset from `etl-spec.md` (Load stage). Dimensions + canonical column names = `codebook.md` v0.2 (§1–§13). De-identified-only per the Data Privacy & Security Plan §3.3.
>
> **Tool:** Looker Studio (free, Google-native, connects directly to BigQuery — matches the F2 Google stack). Equally implementable in Metabase/Tableau; the semantic layer below is tool-agnostic SQL.

---

## 1. What this dashboard answers (the UHC monitoring questions)

The UHC Act monitoring lens, mapped to the four instruments:

| UHC pillar | Headline question | Primary source |
|---|---|---|
| **Financial protection** | What share of households face **catastrophic health expenditure**? OOP share? | F4 Section N (WHO method) |
| **Service coverage** | PhilHealth membership; YAKAP/Konsulta accreditation penetration; utilization | F1, F3, F4 |
| **Awareness / KAP** | NBB/ZBB awareness (facility) + experience (patient); UHC knowledge | F1, F2, F3 |
| **Quality / experience** | Patient satisfaction; referral-system function; HCW job satisfaction + retention | F1, F2, F3 |
| **System readiness** | Accreditation status, capitation viability, HR challenges | F1 |
| **Fieldwork integrity** | Coverage vs target, completion rate, data-quality flags, GPS spread | all four |

---

## 2. Data source + refresh

- **Source:** BigQuery dataset **`uhc_y2`** (de-identified by default — no name/contact/precise-GPS/photo; identifiers live only in the ETL linkage table and never reach BI).
- **Tables** (one per instrument, harmonized to the codebook canonical columns) + cross-instrument link keys:
  - `f1_facility`, `f2_hcw`, `f3_patient`, `f4_household`, `f4_member` (roster long-form), `f4_expenditure` (Section N long-form).
  - Shared keys: `facility_id` (codebook §2), PSGC `region/province/city/barangay` (§1), `survey_date` (§10), `disposition` (§12).
- **Refresh:** Looker Studio on BigQuery = live/extract; schedule the extract **nightly, after the ETL run** (`etl-spec.md` scheduling). Stamp each page with the ETL `run_date` from the lineage manifest.
- **Cross-instrument join key (updated 2026-06-04):** **§15.H is resolved** — F1/F3/F4 share the 12-digit case key's first **9-digit facility block** (`RR-PP-MMM-FF` = REGION+PROVINCE+CITY+FACILITY_NO), so facility↔patient↔household joins resolve directly (`F3_FACILITY_ID` retired; F4→F3 via `F4_PARENT_F3_CASE_SEQ`). **Only F2 stays gated on §15.G** (facility master list) — its `facility_id` is a placeholder and its 12-digit Respondent No is ETL-derived. So §5.6 caveats apply to the **F2↔facility** tiles only; the CAPI-to-CAPI linkage is live.

---

## 3. Semantic layer — BigQuery views + calculated metrics

Build these as **BigQuery views** in `uhc_y2` so the BI tool binds to stable, documented fields (not raw recodes). Definitions are sketches against the codebook columns; finalize field names from the ETL output.

### 3.1 Reporting dimensions (shared, from the codebook)
`region`, `province`, `city_municipality`, `barangay` (§1) · `facility_id`, `facility_type` ∈ {RHU, CHO, Hospital_L1/L2/L3} (§2) · `sex` (§3) · `age_band` (derived from §4: 0–17/18–34/35–49/50–64/65+) · `philhealth_status` (§8) · `survey_date` + `survey_month` (§10) · `disposition` (§12) · `instrument` ∈ {F1,F2,F3,F4}.

### 3.2 Calculated UHC metrics (the headline measures)
| Metric | Definition (sketch) | Source |
|---|---|---|
| **Catastrophic health expenditure (CHE) incidence** | `% households where total_oop_health / capacity_to_pay > 0.40` (WHO method; capacity-to-pay = non-food household expenditure) | F4 Section N **expenditure rosters** (converted 2026-07-03, F4 v1.1.0 — the old flat `Q161/Q175/Q184_*_PHP` columns are GONE): sum `_PURCHASED_PHP`+`_INKIND_PHP` over each roster's `_CONSUMED`=1 rows (exclude `-98`/`-99`); non-food capacity-to-pay = `N_NF1M/NF6M/NF12M_ROSTER` rows, OOP-health = `N_H12M/H6M/H1M_ROSTER` + Q158 restaurant. Crosswalk: codebook CHANGELOG v0.6 |
| **OOP share of health spending** | `sum(oop_health) / sum(total_health_spend)` | `f4_expenditure` |
| **PhilHealth coverage rate** | `% with philhealth_status = member` | `f3_patient`, `f4_member` (§8) |
| **YAKAP/Konsulta accreditation penetration** | `% facilities accredited` (by facility_type, region) | `f1_facility` (Q51/Q80 family) |
| **NBB awareness vs experience gap** | facility NBB-knowledge correct-rate (F1) − patient NBB-experienced-rate (F3) | F1 Q43 family, F3 |
| **Patient satisfaction index** | mean/Top-2-box on F3 satisfaction items | `f3_patient` |
| **HCW retention risk** | `% HCWs whose Q125 plan ≠ "stay/transfer-same-role"` (uses the R3-corrected Q125) | `f2_hcw` |
| **Completion rate** | `completed / cases started` from `case_disposition` (§12) | all instruments |
| ~~Response rate~~ | **NOT COMPUTABLE — do not ship.** A true response rate needs `completed / eligible contacted`, and no CAPI instrument records a non-contact; F3/F4 record no doorstep refusal; replaced units are never started and leave no row (§12 gap). Any "response rate" built from the data we hold would silently be a completion rate wearing the wrong label. Blocked on an ASPSI/DOH decision about the paper Field Control form. | — |

> Each metric is a **view column or a Looker Studio calculated field**; CHE is the one that warrants a materialized view (heavier logic, reused across pages).

---

## 4. Global controls (every page)

Date range (`survey_date`) · Region → Province → City (drill, PSGC cascade) · Facility type · Instrument (where multi) · Disposition (default = `completed`). Optional: ETL `run_date` selector for snapshot comparisons.

---

## 5. Pages

### 5.1 Fieldwork Coverage & Quality *(operations — the live-monitoring view)*
- **Scorecards:** total completed (by instrument), % of target, completion rate, On-Hold count, DLQ count (F2). (No response-rate scorecard — see §12: not computable from the instruments as built.)
- **Coverage map:** GPS points of completed cases by region/cluster (de-identified facility/household centroids only).
- **Timeline:** submissions/day by instrument (sync-health proxy).
- **Table:** completion by facility (expected vs landed) — mirrors the STL reconciliation routine.
- *Complements (doesn't replace) the CSWeb dashboard + F2 admin portal — this is the unified all-4-instrument view.*

### 5.2 F1 — Facility Head
- Facility profile (type, accreditation status) by region; YAKAP/Konsulta penetration bar.
- KAP: UHC/NBB/ZBB knowledge correct-rates; capitation viability; referral-system function.
- HR challenges (Q163 multi-select) top reasons; fees/charging practices.

### 5.3 F2 — Healthcare Worker
- HCW profile: discipline (§6), tenure band, public/private.
- UHC awareness + YAKAP/Konsulta attitudes (KAP battery).
- **Job satisfaction + retention risk** (Q125 future-plans breakdown) — by discipline, facility type.

### 5.4 F3 — Patient
- Patient profile (age band, sex, PhilHealth status); **outpatient vs inpatient** split.
- Health-seeking + utilization; NBB experience; **satisfaction index** by facility type/region.
- Patients linked to their F1 facility (accreditation × satisfaction cross-tab).

### 5.5 F4 — Household
- Household demographics (roster: size, dependency, PhilHealth membership coverage).
- Utilization + health-seeking.
- **Financial protection: CHE incidence + OOP share** — the headline UHC indicator, by region/facility catchment/income band.

### 5.6 Cross-instrument — UHC Indicator Synthesis
- Headline KPI strip: CHE incidence · PhilHealth coverage · accreditation penetration · NBB awareness · satisfaction.
- **Facility ↔ patient ↔ household** linkage views (keyed on `facility_id`): e.g. accredited-facility catchment vs CHE incidence; facility NBB-knowledge vs patient NBB-experience.
- ✅ **F1↔F3↔F4 linkage live** via the shared 9-digit facility block (§15.H resolved 2026-06-04, codebook v0.3). ⚠️ **F2↔facility tiles gated on §15.G** (master list) only — banner the F2 linkage, not the CAPI-to-CAPI joins.

---

## 6. Governance

- **De-identified only.** The BI service account reads the de-identified views; no access to the linkage table. No name/contact/precise-GPS/photo column is ever exposed (Privacy Plan §3.3). Map artefacts use area centroids, not household points.
- **Access:** Looker Studio shared to named DOH/ASPSI viewers; editor access to the data team only. If any tile could re-identify (small-cell counts), apply a **minimum cell-size suppression** (e.g. hide cells with n < 5).
- **Provenance:** every page footer shows ETL `run_date` + source = `uhc_y2`.

---

## 7. Build steps + what unblocks the live prototype

> **✅ Prototype delivered (2026-06-04, #177):** `uhc-y2-dashboard-prototype.html` — a **self-contained single-file** clickable dashboard (no server, no account, no external dependencies) implementing all six §5 pages with the §3.2 metrics over a deterministic synthetic `uhc_y2` sample. Looker Studio was **not** used (per decision) — the semantic layer is tool-agnostic, so the same §3 views drive Looker/Metabase/Tableau when the live store is ready. To go live, swap the in-file synthetic generator for the real BigQuery `uhc_y2` views (step 2).

1. **Now (buildable):** create the §3 BigQuery views against a **dry-run `uhc_y2`** (the ETL spec's synthetic-fixtures output) → wire the BI tool → lay out §5 pages with the §3 metrics. This produces a clickable prototype on synthetic data. *(Delivered as the HTML prototype above.)*
2. **On first synced data:** point the views at the real `uhc_y2`; validate the CHE logic against hand calcs.
3. **Before sharing externally:** confirm §15.H/§15.G (enables §5.6 linkage) + apply cell-suppression.

**Closes #177 once** the prototype is built on a (dry-run or real) store. The blueprint is the spec; it needs the ETL `etl/` package run at least once (etl-spec.md build-plan step) to populate `uhc_y2`.

## 8. Issue + cross-reference map
| This blueprint | Connects to |
|---|---|
| **#177** (E4-INT-002) Looker dashboard prototype | `etl-spec.md` (#176 — the `uhc_y2` source), `codebook.md` (#178 — dimensions + metrics), #204 (facility-id scheme for §5.6 linkage) |
| §15.H/§15.G dependency | codebook §15 open items (ASPSI) |
