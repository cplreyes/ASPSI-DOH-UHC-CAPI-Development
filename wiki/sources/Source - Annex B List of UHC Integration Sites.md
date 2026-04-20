---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Project-Deliverable-1_Apr20-submitted/Annex B_List of UHC IS as of Nov 25.pdf]]"
date_ingested: 2026-04-20
tags: [deliverable-1, inception-report, sampling-frame, uhc-integration-site, ingest-batch-apr20]
---

# Source — Annex B: List of UHC Integration Sites

3-page sampling-frame annex listing the **107 UHC Integration Sites** as of November 2025, paired with the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex C List of Non UHC Integration Sites|Annex C (13 non-UHC IS)]] to compose the 120-site Year 2 universe referenced in the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Revised Inception Report|Revised Inception Report]] Section V.C.

## Structure

Each row: **No. · Year of integration · Region · City/Province · Class (HUC/ICC/blank=province-or-component)**.

## Cohort distribution

| Integration year | Count | Running total |
|---|---|---|
| 2020 | 58 (rows 1–58) | 58 |
| 2022 | 13 (rows 59–71) | 71 |
| 2023 | 2 (rows 72–73) | 73 |
| 2024 | 28 (rows 74–101) | 101 |
| 2025 | 6 (rows 102–107) | 107 |

## Regional spread (Nov 2025 snapshot)

Covers all 17 Philippine regions (NCR, CAR, Regions I–XIII, BARMM). Regions with the deepest coverage: NCR (13 sites across multiple HUCs), Region XIII Caraga (6), Region X (6), Region III (5). BARMM represented by Basilan + Maguindanao.

## 2025-cohort additions (newest)

- NCR: Quezon City
- Region IV-A: Rizal
- Region V: Naga City
- Region VIII: Ormoc City
- Region IX: Zamboanga City

## Source provenance

Compiled from DOH Bureau of Local Health Systems Development (BLHSD) circulars:
- DOH Department Circular **No. 2024-0094** (13 March 2024) — LHS Maturity Levels 2023 Year-End Report
- DOH Department Circular **No. 2025-0125** (14 March 2025) — LHS Maturity Levels 2024 Annual Report

Combined with November 2025 BLHSD integration-report update (referenced by [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex C List of Non UHC Integration Sites|Annex C]]).

## Sampling-frame implications

- **F1 Facility Head Survey** draws from facilities within all 107 UHC IS (+13 non-UHC IS) per NHFR stratification.
- **F4 Household Survey** uses a subset: 4 UHC IS since 2020 + 4 non-UHC IS per island group × 4 island groups. Year-2020 eligibility filters this list to rows 1–58 for the UHC IS side of the F4 frame (Revised IR Table 4).
- **PSGC value-set request** to ASPSI (REGION/PROVINCE_HUC/CITY_MUNICIPALITY/BARANGAY) should align with the City/Province-Class distinctions used here — a plain string list is insufficient for the CAPI dropdowns; each site needs PSGC codes.

> [!warning] Annex G contradiction
> [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex G DOH Recommendations Matrix|Annex G]] remark #21 references **107 UHC IS + 17 non-UHC = 124 sites**. Annex B (107) + Annex C (13) = 120 is authoritative; treat Annex G's 124 figure as stale. See [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Revised Inception Report|Revised IR]] contradiction callout.

## Cross-references

- Companion: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex C List of Non UHC Integration Sites|Annex C (13 non-UHC IS)]]
- Parent: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Revised Inception Report|Revised Inception Report]] Section V.C
- Field-ops: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex D Replacement Protocol|Annex D]] (replacement rules when a site/facility becomes non-responsive)

## Sources

- Raw file: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Project-Deliverable-1_Apr20-submitted/Annex B_List of UHC IS as of Nov 25.pdf|Annex B PDF]]
- Upstream: DOH BLHSD circulars cited above
