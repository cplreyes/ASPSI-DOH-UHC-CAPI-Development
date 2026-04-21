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
| Builder | `deliverables/CSPro/shared/build_psgc_lookups.py` | emits 4 external lookup dicts + fixed-width .dat files |
| External dicts | `deliverables/CSPro/shared/psgc_{region,province,city,barangay}.{dcf,dat}` | the 4 lookup dictionaries CSEntry reads via `loadcase()` |
| Cascade logic | `deliverables/CSPro/shared/PSGC-Cascade.apc` | 4 public `Fill*ValueSet` functions invoked from each form's `onfocus` events |
| Helper | `deliverables/CSPro/cspro_helpers._psgc_fields(prefix="")` | emits the 4 main-dict numeric items (length=10, placeholder VS) |
| Wiring | `F1/F3/F4 generate_dcf.py` via `build_geo_id(mode)` | attaches the placeholder value set; runtime cascade fills the real options |

## Architecture — External Lookup + Cascade

The four PSGC levels (18 regions / 117 provinces-HUCs / 1,658 cities-municipalities / 42,010 barangays) are **not baked into the main F1/F3/F4 dictionaries**. They live in four **external lookup dictionaries** under `deliverables/CSPro/shared/`. The main-dict PSGC items carry only a 1-entry generic placeholder value set (per CSPro 8.0 Users Guide p.188 best-practice #3 for cascading items).

At runtime, `PSGC-Cascade.apc` uses `loadcase()` to pull the relevant parent's children from the external dict and `setvalueset()` to replace the placeholder VS on the target item. Each handler fires in `onfocus` (not `preproc`, per Users Guide p.188 Logic Tip #4) so reverse-navigation re-populates the value set.

The design mirrors the **Popstan Census CAPI reference app** (`3_Resources/Tools-and-Software/CSPro/Examples 8.0/1 - Data Entry/CAPI Census/`) — the US Census Bureau's canonical demonstration of external-lookup geographic hierarchies.

### Why externalize?

| Concern | Before (baked VS) | After (external lookup) |
|---|---|---|
| F1 `.dcf` size | 17.2 MB | ~0.9 MB |
| F3 `.dcf` size | ~33 MB (doubled: facility + patient home) | ~1.0 MB |
| F4 `.dcf` size | ~17 MB | ~0.8 MB |
| PSGC duplication | 3× (once per F-series form) | 1× (single `shared/` source of truth) |
| Review xlsx Value Sets rows | 46k–90k | 2k–2.6k |
| Cascading dropdowns | infeasible | first-class via `setvalueset()` |
| Tablet UX | 42k-barangay single dropdown | filtered to parent-city's ~25 avg barangays |

### Parent-code schema

Each external dict is keyed by a 10-digit parent code in its single ID item. Regions have no real parent, so the builder uses the sentinel `0000000000`.

| Dict | ID item | Record | Children items | Max occurs |
|---|---|---|---|---|
| `PSGC_REGION_DICT` | `R_PARENT_CODE` | `PSGC_REGION_REC` | `R_CODE` (num 10), `R_NAME` (alpha 80) | 20 |
| `PSGC_PROVINCE_DICT` | `P_PARENT_REGION` | `PSGC_PROVINCE_REC` | `P_CODE`, `P_NAME` | 30 |
| `PSGC_CITY_DICT` | `C_PARENT_PROVINCE` | `PSGC_CITY_REC` | `C_CODE`, `C_NAME` | 60 |
| `PSGC_BARANGAY_DICT` | `B_PARENT_CITY` | `PSGC_BARANGAY_REC` | `B_CODE`, `B_NAME` | 2000 |

### Cascade handlers

`PSGC-Cascade.apc` exposes four public functions. Each form's `.app` file wires them from the corresponding main-dict item's `onfocus`:

```
PROC REGION            onfocus  FillRegionValueSet(REGION);
PROC PROVINCE_HUC      onfocus  FillProvinceValueSet(PROVINCE_HUC, REGION);
PROC CITY_MUNICIPALITY onfocus  FillCityValueSet(CITY_MUNICIPALITY, PROVINCE_HUC);
PROC BARANGAY          onfocus  FillBarangayValueSet(BARANGAY, CITY_MUNICIPALITY);
```

F3's patient-home block (`P_REGION`, `P_PROVINCE_HUC`, `P_CITY_MUNICIPALITY`, `P_BARANGAY`) wires the same functions against those items.

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
