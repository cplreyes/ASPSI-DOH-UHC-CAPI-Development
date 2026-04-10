---
type: source-summary
source: "[[raw/Project Deliverable 1/Annex F4_Household Survey Questionnaire_UHC Year 2_Apr 08.pdf]]"
date_ingested: 2026-04-09
tags: [questionnaire, household, f4, survey-instrument]
---

# Source — Annex F4: Household Survey Questionnaire

Household Survey Questionnaire for [[wiki/concepts/UHC Survey Year 2|UHC Survey Year 2]], 26 pages. New module for Year 2 — captures population-level UHC awareness and household expenditure. Face-to-face CAPI interview with household head or main decision-maker.

## Structure

| Section | Topic | Key Data Collected |
|---|---|---|
| Field Control | Survey logistics | Team leader, enumerator, visit dates, result codes |
| Geographic ID | Household location | Region, province, city, barangay |
| **A. Informed Consent** | Consent process | Consent verification |
| **B. Respondent Profile** | Demographics | Name, age, sex, education, employment, income |
| **C. Household Characteristics** | Household composition | Household members roster, demographics of each member |
| **D. UHC Awareness** | UHC knowledge | Awareness of UHC Act and provisions |
| **E. YAKAP/Konsulta Awareness** | PhilHealth program | Konsulta/YAKAP awareness and enrollment |
| **F. BUCAS Awareness** | Urgent care program | BUCAS awareness and utilization |
| **G. Access to Medicines** | Drug availability | GAMOT awareness, generic drug access |
| **H. PhilHealth Registration** | Insurance coverage | PhilHealth membership for all household members |
| **I. Primary Care Utilization** | Primary care access | Usual source of care, utilization patterns |
| **J. Health-Seeking Behavior** | Care decisions per member | Health-seeking behavior and outcomes for each household member |
| **K. Referrals** | Referral experience | Referral process, satisfaction |
| **L. NBB Awareness** | No Balance Billing | NBB awareness and utilization experience |
| **M. ZBB Awareness** | Zero Balance Billing | ZBB awareness and utilization experience |
| **N. Household Expenditures** | Spending data | Food (weekly), non-food/non-health, health products/services (12 months) |
| **O. Sources of Funds** | Health financing | Sources of funds for health expenditure |
| **P. Financial Risk Protection** | Reduced/delayed care | Incidence of forgone or delayed care due to cost |
| **Q. Financial Anxiety** | Household finances | Anxiety about ability to pay for health needs |

## CAPI Development Notes

- Most complex instrument: 26 pages, 17 sections.
- **Household roster** (Section C) requires repeating-record structure in CSPro — each household member gets a row.
- **Health-seeking behavior** (Section J) likely loops over household members.
- **Expenditure sections** (N) have sub-tables: food items (weekly), non-food items, health products/services (12-month recall). These need roster/grid data entry.
- Expenditure data enables computation of **catastrophic health expenditure (CHE)** using SDG 3.8.2 capacity-to-pay approach.
- Follows **Labor Force Survey (LFS) design** — one respondent per household.

## Sources

- Part of Deliverable 1 submitted to [[wiki/entities/DOH-PMSMD|DOH-PMSMD]]
- Developed by [[wiki/entities/ASPSI|ASPSI]] consultant team
