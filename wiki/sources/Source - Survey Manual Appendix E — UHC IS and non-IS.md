---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/2026-05-06-survey-manual-bundle/2026-05-06_Appendix-E_UHC-IS-and-non-IS]]"
date_ingested: 2026-05-07
tags: [sample-frame, uhc-is, geography, ncr, barmm]
---

# Source — Survey Manual Appendix E (UHC IS and non-UHC IS Sites)

Geographic listing of the 120 study sites circulated by [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Juvy Chavez-Rocamora|Kidd]] alongside the [[Source - Survey Manual Working File (2026-05-06 Kidd)|Working File]] on 2026-05-06. ~358 lines.

## Document structure

A single HTML table grouped by administrative region (NCR, Region I–XIII, BARMM):
- **5 columns:** Region | UHC IS (3 sub-columns) | non-UHC IS (1 column)
- 2–4 rows per region with city/municipality/province entries

## Site count totals

- **UHC IS:** ~107 sites
- **non-UHC IS:** ~13 sites
- **Total: 120** — matches the Inception Report sample frame.

Per-region samples (illustrative):
- **NCR:** 15 UHC IS (Marikina, Pasig, Caloocan, Parañaque, Mandaluyong, Malabon, Valenzuela, City of Manila, Muntinlupa, San Juan, Navotas, Las Piñas, Taguig, Pasay, Quezon City) + 2 non-UHC IS (Makati, Pateros)
- **Region XI (Davao):** 8 UHC IS / 0 non-UHC IS
- **BARMM:** 2 UHC IS (Basilan, Maguindanao) + 3 non-UHC IS (Lanao del Sur, Tawi-Tawi, Cotabato City)

## Differences vs existing wiki sources

[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex B List of UHC Integration Sites|Annex B (UHC IS list)]] and [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex C List of Non UHC Integration Sites|Annex C (non-UHC IS list)]] from the Inception Report cover the same 107 + 13 sites. Appendix E is a **presentation variant** (regional rollup vs flat list); membership appears unchanged.

## What's missing for CAPI

> [!warning] Too thin for F1 facility master list
> Appendix E is **geography-only** — facility / city / municipality names with no:
> - Facility codes (DOH internal codes)
> - PSGC codes
> - Ownership (public / private / DOH-retained)
> - Facility type (RHU / hospital / level)
> - Coordinates / administrative nesting
> - Survey wave indicator (Year 1 vs Year 2)
>
> The F1 facility master list **cannot be sourced from Appendix E alone**. Use [[Source - Survey Manual Appendix D — Case ID Format + Facility Master|Appendix D]]'s facility master list (L151–L897, with PSGC codes + per-LGU counts) instead.

## Anomalies

- **5 empty rows in Region X** (lines 268–286) — HTML formatting artifact, not data.
- No footnotes, source citations, or revision dates.
- Uneven column fill (e.g., some regions have empty non-UHC IS cells).
- No distinction between province + city — peers in same column (Davao City vs Davao del Sur).

## Cross-references

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex B List of UHC Integration Sites|Source - Annex B List of UHC Integration Sites]] — flat-list predecessor.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex C List of Non UHC Integration Sites|Source - Annex C List of Non UHC Integration Sites]] — flat-list predecessor.
- [[Source - Survey Manual Appendix D — Case ID Format + Facility Master|Appendix D]] — has the facility master list with PSGC codes + counts (more useful for F1 facility master).
- [[Source - Survey Manual Appendix B — Sample Distribution|Appendix B]] — per-province sample-size distribution applies to these 120 sites.
