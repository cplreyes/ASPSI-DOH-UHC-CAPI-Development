---
type: concept
tags: [cspro, dcf, value-sets, psgc, geography, conventions]
source_count: 1
---

# PSGC Value Sets

**PSGC** = Philippine Standard Geographic Code, the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/PSA|PSA]]'s authoritative geographic code list covering Region → Province → City/Municipality → Barangay. Every F-series CAPI instrument needs PSGC value sets for the geographic identification fields on the cover/FIELD_CONTROL block.

## Items affected

In F1's `FacilityHeadSurvey.dcf` (the template for F2/F3/F4):

- `REGION` — length 10, stores full PSGC (e.g. `1300000000` for NCR)
- `PROVINCE_HUC` — length 10, stores full PSGC; includes all 82 Prov + 33 HUCs + 2 specials (Isabela City "not a province", Special Geographic Area)
- `CITY_MUNICIPALITY` — length 10, stores full PSGC; includes 149 City (CC/ICC/HUC) + 1,493 Mun + 14 SubMun (Manila districts) + 2 specials
- `BARANGAY` — length 10, stores full PSGC; 42,010 barangays

F2/F3/F4 inherit the same four items; the PSA source + loader is shared so those instruments can reuse without re-fetching.

## Source — PSA 1Q 2026 publication (self-served)

As of **2026-04-20**, PSGC value sets are sourced directly from the PSA 1Q 2026 Publication Datafile (released 13 Apr 2026), not from ASPSI. The shift happened because PSGC is public PSA data — ASPSI had no proprietary input to add, and waiting on them was pure delay.

Pipeline:

| Artifact | Path | Purpose |
|---|---|---|
| Source xlsx | `deliverables/CSPro/F1/inputs/PSGC-1Q-2026-Publication-Datafile.xlsx` | PSA's published workbook |
| Parser | `deliverables/CSPro/F1/inputs/parse_psgc.py` | state-machine extractor; emits 4 CSVs |
| Region CSV | `deliverables/CSPro/F1/inputs/psgc_region.csv` | 18 rows |
| Province/HUC CSV | `deliverables/CSPro/F1/inputs/psgc_province_huc.csv` | 117 rows (82 Prov + 33 HUC + 2 Special) |
| City/Mun CSV | `deliverables/CSPro/F1/inputs/psgc_city_municipality.csv` | 1,658 rows (149 City + 1,493 Mun + 14 SubMun + 2 Special) |
| Barangay CSV | `deliverables/CSPro/F1/inputs/psgc_barangay.csv` | 42,010 rows |
| Loader | `deliverables/CSPro/cspro_helpers.load_psgc_value_set()` | reads a CSV into `value_set_options` tuples |
| Wiring | `F1/generate_dcf.py :: build_geographic_id()` | attaches all four value sets to the items |

## Parent chains (for cascading filters)

Each CSV carries the parent PSGC code(s) so CSPro PROC code can filter child dropdowns by the selected parent:

- `psgc_province_huc.csv` → `parent_region`
- `psgc_city_municipality.csv` → `parent_province_huc` + `parent_region`
- `psgc_barangay.csv` → `parent_city_municipality` + `parent_province_huc` + `parent_region`

**Cascading-filter logic is NOT yet implemented.** The DCF ships with all 42k barangays in one dropdown. Implementing per-parent filtering is a follow-on PROC task — the data is ready.

## Edge cases handled by the parser

- **HUCs** (33) live at province-level (PROVINCE_HUC) AND as their own city-level (CITY_MUNICIPALITY) container, since their barangays sit directly beneath them in PSA's hierarchy.
- **ICCs** (5) stay under their geographic province (CITY_MUNICIPALITY), following DOH convention.
- **Manila SubMuns** (14) are preserved as distinct CITY_MUNICIPALITY-level entries, faithful to PSA's hierarchy; barangays list the SubMun as parent.
- **Isabela City "Not a Province"** and **Special Geographic Area** (BARMM) are treated as PROVINCE_HUC-level + CITY_MUNICIPALITY-level specials so their child barangays chain correctly.

## F2 parallel

[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F2 Google Forms Track|F2 Google Forms Track]] takes a different UX approach: rather than shipping PSGC as drop-downs, the F2 design **absorbs geographic fields into a `FacilityMasterList` Sheet** that prefills facility-linked metadata via per-facility prefilled URLs. The underlying PSGC codes it populates with should come from the same PSA source / CSVs here — keep one source of truth.

## Memory

- `memory/project_aspsi_psgc_value_sets.md` — pivot from ASPSI-blocked → self-served; pipeline artifacts list.

## Related

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F-Series Value Set Conventions|F-Series Value Set Conventions]] — project-internal coding rules for NA codes + value-set shape.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Data Dictionary|CSPro Data Dictionary]] — how value sets attach to items in `.dcf`.
