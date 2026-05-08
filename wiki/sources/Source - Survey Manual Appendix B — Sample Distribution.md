---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/2026-05-06-survey-manual-bundle/2026-05-06_Appendix-B_Sample-Distribution]]"
date_ingested: 2026-05-07
tags: [sample-distribution, sampling, sample-size, case-id, capi]
---

# Source — Survey Manual Appendix B (Sample Distribution)

Three-table sample distribution annex circulated by [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Juvy Chavez-Rocamora|Kidd]] alongside the [[Source - Survey Manual Working File (2026-05-06 Kidd)|Working File]] on 2026-05-06. **The empirical reference for case-ID width verification.** ~5,483 lines of HTML-formatted tables.

## Document structure

- **Table 1** (L1–L1745) — Facility survey sample by study site × ownership classification. Columns: City/Rural Health Unit (gov), Hospital (gov), Hospital (private), All Facilities total + sample. **120 province/HUC rows + totals.**
- **Table 2** (L1749–L3988) — Hospital sample by level (1/2/3) × ownership (gov/private). Same 120 rows.
- **Table 3** (L3992–L5483) — Outpatient + Inpatient sample by province/HUC. Per-facility uniform: **45 outpatient, 30 inpatient** across all rows.

All tables are **province/HUC-level** aggregates — no municipality decomposition.

## Per-instrument sample totals

| Instrument | Total | Notes |
|---|---|---|
| F1 Facility Head | **1,521 sampled / 4,028 total facilities** | Table 1 final row |
| F3 Outpatient cases | **5,400** | Table 3 (45 × 120) |
| F3 Inpatient cases | **3,600** | Table 3 (30 × 120) |
| F2 HCW (private hospital sample) | ~298 | Table 2 (Level 2: 156, Level 3: 123, plus other tiers) |
| F4 Household | **NOT in this appendix** | Per [[Source - DOH Survey Protocol V2 (30 April)|Protocol V2]]: 2,672 (1,336 UHC IS + 1,336 non-IS) |

## Maximum per-province / per-HUC values (Table 1 — F1)

| Site | All-facility sample (largest values) |
|---|---|
| **BULACAN (Region III)** | **53** (highest per-province) |
| **QUEZON CITY HUC (NCR)** | **38** (highest HUC) |
| **NUEVA ECIJA (Region III)** | 35 |
| **CITY OF MANILA HUC (NCR)** | 26 |
| **PANGASINAN (Region I)** | ~33 |

Confirms the case-ID-width planning assumption: **max per-province F1 sample = 53 (Bulacan); max HUC = 38 (QC).**

## Maximum per-facility per-instrument (Table 3)

Uniform across all 120 rows: **45 outpatient, 30 inpatient** per facility. No per-LGU adaptive quotas — this is a centralized statistical design.

> [!info] Width verification for the 12-digit case-ID scheme
> Carl's [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Questionnaire Numbering Convention|Questionnaire Numbering Convention]] adopts `RR-PP-MMM-FF-CCC` with **FF=2 digits** and **CCC=3 digits**:
>
> - **FF=2 (max 99 facilities per LGU):** appendix shows max per-province = 53 (Bulacan); max HUC = 38 (QC). Per-mun is necessarily smaller. ✅ **Sufficient.**
> - **CCC=3 (max 999 cases per facility per instrument):** appendix shows uniform 45 outpatient / 30 inpatient / 1 facility-head / ≤53 HCW per facility. The active band (001–699) alone covers >10× the max observed quota; partition headroom is conservative. ✅ **Highly sufficient.**
>
> The [[Source - Survey Manual Working File (2026-05-06 Kidd)|Working File's variant]] uses `-CC-CCC` (respondent type 2 + sequence 2 within type) — also sufficient at 99 per type per facility, but loses the partition headroom for active/replacement/refused.

## Anomalies

- **Empty cells (zeros)** scattered (e.g., Apayao L71–L79 shows 0 private hospital total/sample) — intentional, not missing data.
- **Totals minor discrepancy:** Table 1 totals 1,374 sampled (Gov CHU 911 + Hospital 463) + 366 private = 1,740. Table 3 shows 1,521. Likely Table 1 counts unique facilities while Table 3 counts sampled-instances; reconcile if exact numbers matter for case-ID issuer.
- **Five empty rows** in Region X (HTML artifact, lines 268–286).
- **No footnotes / methodology / design-effect text** — pure table dump. Replacement-rate justification, design-effect assumptions, and non-response margin live in [[Source - DOH Survey Protocol V2 (30 April)|Protocol V2]] §Sampling Design instead.
- **Uniform 45/30 outpatient/inpatient per facility across all 120 rows** — indicates global design, not LGU-adaptive.

## Cross-references

- [[Source - DOH Survey Protocol V2 (30 April)|Protocol V2]] — sampling-design narrative + per-instrument design effects + replacement rates.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Questionnaire Numbering Convention|Questionnaire Numbering Convention]] — Carl's case-ID scheme; this appendix verifies the widths chosen.
- [[Source - Survey Manual Appendix E — UHC IS and non-IS|Appendix E]] — geographic listing of the 120 sites this distribution applies to.
- [[Source - Survey Manual Working File (2026-05-06 Kidd)|Survey Manual Working File]] — Working File §3.2 Sample Size cites this appendix for detail.
