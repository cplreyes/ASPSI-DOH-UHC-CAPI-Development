---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Project-Deliverable-1_Apr20-submitted/Annex F1_Facility Head Survey Questionnaire_UHC Year 2.pdf]]"
date_ingested: 2026-04-20
tags: [questionnaire, facility-head, f1, survey-instrument, ingest-batch-apr20]
---

# Source — Annex F1: Facility Head Survey Questionnaire

Facility Head Survey Questionnaire for [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/UHC Survey Year 2|UHC Survey Year 2]], **37 pages, 166 main-survey items** (up from ~126 in the Apr 08 baseline). Targets facility heads or authorized representatives (municipal/city health officers, chiefs of hospital, etc.) who have held their position for at least 6 months.

**Version:** Apr 20 2026 Revised Inception Report submission. Supersedes Apr 08 baseline.

## Structure

| Section | Topic | Key Data Collected |
|---|---|---|
| Field Control | Survey logistics | Team leader, enumerator, visit dates, result codes |
| Geographic ID | Facility location | UHC IS/non-UHC classification, region, province/HUC, city/municipality, barangay, lat/long |
| **A. Facility Head Profile** | Respondent demographics | Name, designation, age, sex, tenure at facility, years in health |
| **B. Facility Profile** | Facility characteristics | Ownership (public/private), service capacity level (PCF, L1–L3) |
| **C. UHC Implementation** | UHC awareness and changes | UHC awareness, primary care packages, DOH licensing, public health unit, HCPN participation, referral networks, health info systems, **EMR adoption + DOH IS/PhilHealth Dashboard submissions + decision-making utilization** (Q32–34, NEW) |
| **D. YAKAP/Konsulta Package** | PhilHealth program implementation | Accreditation status, Konsulta enrollment, benefits delivery, barriers |
| **E. Awareness on Expanded Health Programs (BUCAS and GAMOT)** | BUCAS + GAMOT awareness & implementation | Q101–107: BUCAS awareness/availability/implementation; Q108–117: GAMOT awareness/availability/implementation (RENAMED + expanded) |
| **F. DOH Licensing** | Licensing status and barriers | Licensing application status, barriers to compliance |
| **G. Service Delivery Process** | Healthcare service delivery | **4 subsections:** NBB (Q135–137), ZBB (Q138–140), LGU Support (Q148–153), Referral (Q154–162) |
| **H. Human Resources for Health** | Staffing | Staff counts, vacancies, turnover, training needs |
| **Secondary Data (Sections I–5)** | Facility records | Hospital census (6 months), patient load, staffing counts (full-time/part-time/contractual), other documents |

## Skip Logic Notes

- Q10 No → Q12
- Q13 No/NA → Q16
- Multiple additional skip destinations across Sections C, E, G driven by the new UHC-programme and ZBB/NBB branching
- Facility-type branches (RHU vs. hospital) still govern Sections B, G, H

## Changes from Apr 08 baseline

Driven by [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex G DOH Recommendations Matrix|Annex G remarks]]:

- **Q32–34 added** (Section C): DOH Information System / PhilHealth Dashboard submission, frequency, and which submitted reports are actually used for decision-making (12-option checklist incl. YAKAP/Konsulta utilization, NBB compliance, ZBB compliance). Direct response to **Annex G #3** (EMR-use-in-decision-making).
- **Q40–42**: Explicit separate items for NBB / ZBB / no-copayment implementation since UHC Act.
- **Section E renamed + expanded** to explicitly name **BUCAS and GAMOT** (Q101–117), responding to **Annex G #1** (include BUCAS / PuroKalusugan / ZBB questions).
- **Section G expanded** into four named subsections (NBB, ZBB, LGU Support, Referral) — responds to **Annex G #1 + #19 + #22**.
- **Sampling frame context** (affects F1 universe, not schema): 107 UHC IS + 17 non-UHC = 124 sites from NHFR covering public + private Level 1–3 hospitals and RHUs/health centers. See **Annex G #14, #17, #21**.
- **Net item-count growth**: ~126 → 166 main-survey items (+40).

## CAPI Development Notes

- 37-page paper questionnaire with 166 main-survey items plus sub-items and Secondary Data pages (pp. 33–37).
- Mix of single-select, multi-select ("select all that apply"), open-ended text, and numeric fields.
- Probing instructions embedded (e.g., "DO NOT READ OPTIONS OUT LOUD" guide questions).
- Secondary data section requires separate roster/grid input for staffing tables.
- Facility geographic identification includes GPS coordinates (latitude/longitude).
- **PSGC value sets** for REGION / PROVINCE_HUC / CITY_MUNICIPALITY / BARANGAY still inbound from ASPSI — see project memory on this open dependency.
- **DCF-generator impact**: `generate_dcf.py` needs re-audit against Apr 20 items. Previous build was 11 records / 655 items against Apr 08 source; item count will grow with the new Section C, E, G items.

## Cross-references

- Change-rationale map: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex G DOH Recommendations Matrix|Annex G DOH Recommendations Matrix]]
- Sibling instruments: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F2 Healthcare Worker Survey Questionnaire|F2]], [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3 Patient Survey Questionnaire|F3]], [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F4 Household Survey Questionnaire|F4]]
- Programme concept: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/UHC Survey Year 2|UHC Survey Year 2]]

## Sources

- Part of [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Revised Inception Report|Revised Inception Report]] Apr 20 submission to [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/DOH-PMSMD|DOH-PMSMD]]
- Developed by [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/ASPSI|ASPSI]] consultant team
- Raw file: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Project-Deliverable-1_Apr20-submitted/Annex F1_Facility Head Survey Questionnaire_UHC Year 2.pdf|F1 PDF]]
- Apr 08 baseline preserved at: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Project-Deliverable-1/Annex F1_Facility Head Survey Questionnaire_UHC Year 2_April 08.pdf|F1 Apr 08 PDF]]
