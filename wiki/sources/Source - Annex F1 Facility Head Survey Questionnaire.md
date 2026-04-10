---
type: source-summary
source: "[[raw/Project Deliverable 1/Annex F1_Facility Head Survey Questionnaire_UHC Year 2_April 08.pdf]]"
date_ingested: 2026-04-09
tags: [questionnaire, facility-head, f1, survey-instrument]
---

# Source — Annex F1: Facility Head Survey Questionnaire

Facility Head Survey Questionnaire for [[wiki/concepts/UHC Survey Year 2|UHC Survey Year 2]], 34 pages. Targets facility heads or authorized representatives (municipal/city health officers, chiefs of hospital, etc.) who have held their position for at least 6 months.

## Structure

| Section | Topic | Key Data Collected |
|---|---|---|
| Field Control | Survey logistics | Team leader, enumerator, visit dates, result codes |
| Geographic ID | Facility location | UHC IS/non-IS classification, region, province, city, barangay, lat/long |
| **A. Facility Head Profile** | Respondent demographics | Name, designation, age, sex, tenure at facility, years in health |
| **B. Facility Profile** | Facility characteristics | Ownership (public/private), service capacity level (PCF, L1–L3) |
| **C. UHC Implementation** | UHC awareness and changes | UHC awareness, primary care packages, DOH licensing, public health unit, HCPN participation, referral networks, health info systems, EMR adoption |
| **D. YAKAP/Konsulta Package** | PhilHealth program implementation | Accreditation status, Konsulta enrollment, benefits delivery, barriers |
| **E. Expanded Health Programs** | BUCAS and GAMOT awareness | Awareness, availability, implementation status, barriers |
| **F. DOH Licensing** | Licensing status and barriers | Licensing application status, barriers to compliance |
| **G. Service Delivery Process** | Healthcare service delivery | Services offered, costing, quality indicators, patient load management |
| **H. Human Resources for Health** | Staffing | Staff counts, vacancies, turnover, training needs |
| **Secondary Data** | Facility records | Hospital census (6 months), patient load, staffing counts (full-time/part-time/contractual) |

## Skip Logic Notes

- Q10 No → skip to Q12
- Q13 No/NA → skip to Q16
- Various conditional branches throughout based on facility type (RHU vs. hospital) and response patterns

## CAPI Development Notes

- 34-page paper questionnaire with ~126 questions plus sub-items.
- Mix of single-select, multi-select ("select all that apply"), open-ended text, and numeric fields.
- Probing instructions embedded (e.g., "DO NOT READ OPTIONS OUT LOUD" guide questions).
- Secondary data section (pages 30–34) may require separate roster/grid input for staffing tables.
- Facility geographic identification includes GPS coordinates (latitude/longitude).

## Sources

- Part of Deliverable 1 submitted to [[wiki/entities/DOH-PMSMD|DOH-PMSMD]]
- Developed by [[wiki/entities/ASPSI|ASPSI]] consultant team
