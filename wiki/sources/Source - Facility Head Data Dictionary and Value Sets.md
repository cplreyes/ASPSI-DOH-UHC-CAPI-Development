---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Sample Data/Facility Head Survey Data Dictionary and Value Sets.xlsx]]"
date_ingested: 2026-04-09
tags: [data-dictionary, value-sets, cspro, f1, facility-head]
---

# Source — Facility Head Survey Data Dictionary and Value Sets

Excel workbook containing the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro|CSPro]] data dictionary structure and value set definitions for the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F1 Facility Head Survey Questionnaire|Facility Head Survey (F1)]]. This is a working/sample dictionary — likely an early draft or reference for building the actual CSPro .dcf file.

## Sheet 1: Dictionary Names and Labels

Defines the hierarchical CSPro dictionary structure:

| Level | Element | Example |
|---|---|---|
| **Dictionary** | `FACILITYHEADSURVEY_LEVEL` | Top-level dictionary |
| **ID Items** | `_IDS0` → `FACILITYHEADSURVEY_ID` | Case identifier |
| **Record** | `FACILITYHEADSURVEY_REC` | Single flat record |
| **Groups** | Sections A–H | Match questionnaire sections |
| **Items** | Individual variables | ~115 items |

### Section Mapping

| Group Name | Section |
|---|---|
| `FIELD_CONTROL` | Field Control (team, dates, results) |
| `HEALTH_FACILITY_AND_GEOGRPAHIC_IDENTIFICATION` | Geographic ID |
| `A_FACILITY_HEAD_PROFILE` | A. Facility Head Profile (Q1–Q6) |
| `B_FACILITY_PROFILE` | B. Facility Profile (Q7–Q8) |
| `C_UNIVERSAL_HEALTHCARE_UHC_IMPLEMENTATION` | C. UHC Implementation (Q9–Q29) |
| `D_YAKAP_KONSULTA_PACKAGE` | D. YAKAP/Konsulta (Q30–Q64) |
| `E_AWARENESS_ON_EXPANDED_HEALTH_PROGRAMS` | E. BUCAS and GAMOT (Q65–Q99) |
| `F_DOH_LICENSING` | F. DOH Licensing (Q100–Q104) |
| `G_SERVICE_DELIVERY_PROCESS` | G. Service Delivery (Q105–Q122) |
| `H_HUMAN_RESOURCES_FOR_HEALTH` | H. Human Resources (Q123–Q126) |

### Naming Convention

Variables follow the pattern: `Q{number}_{DESCRIPTION}` (e.g., `Q9_HEARD_UHC`, `Q10_IMPLEMENT_PRIMARY_CARE_PACKAGE`). Sub-items use suffixes like `_YES_SPECIFY`, `_NO_SPECIFY`.

## Sheet 2: Value Sets

Defines coded response options for each variable. ~303 rows covering all categorical questions.

Examples:
- `CLASSIFICATION_VS1`: UHC IS = 1, Non-UHC IS = 2
- `Q2_FACILITY_ROLE_VS1`: 11 role options (Rural Health Unit Head = 1, ... Health Promotion Officer = 11)
- `Q4_SEX_VS1`: Male = 1, Female = 2

## CAPI Development Notes

- This dictionary uses a **flat single-record** structure — no repeating records or rosters for the main F1 questionnaire.
- The secondary data section (hospital census, staffing tables) is not represented in this dictionary — may need separate records or a roster approach.
- Variable naming is clean and systematic — good foundation for the CSPro .dcf file.
- Value sets need validation against the latest questionnaire revision (April 8 version) to ensure alignment.

## Sources

- Sample/draft data dictionary for [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/UHC Survey Year 2|UHC Survey Year 2]]
- Created by [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/ASPSI|ASPSI]] data team
