---
type: source-summary
source: "[[raw/Project Deliverable 1/Annex F3_Patient Survey Questionnaire_UHC Year 2_Apr 08.pdf]]"
date_ingested: 2026-04-09
tags: [questionnaire, patient, f3, survey-instrument]
---

# Source — Annex F3: Patient Survey Questionnaire

Patient Survey Questionnaire for [[wiki/concepts/UHC Survey Year 2|UHC Survey Year 2]], 23 pages. Face-to-face CAPI interview with outpatients and inpatients at sampled health facilities.

## Structure

| Section | Topic | Key Data Collected |
|---|---|---|
| Field Control | Survey logistics | Team leader, enumerator, visit dates, result codes |
| Geographic ID | Facility + patient location | Facility ID, patient address, barangay |
| **A. Informed Consent** | Consent process | Consent verification |
| **B. Patient Profile** | Demographics | Name, age, sex, education, employment, income |
| **C. UHC Awareness** | UHC knowledge | Awareness of UHC Act and key programs |
| **D. PhilHealth Registration** | Insurance status | PhilHealth membership, YAKAP/Konsulta enrollment, other insurance |
| **E. Primary Care Utilization** | Primary care access | Usual source of care, PCF utilization, barriers |
| **F. Health-Seeking Behavior** | Care decisions | Facility choice, reasons for visit, bypassing primary care |
| **G. Outpatient Care** | Outpatient experience | Services received, waiting time, costs, medicines |
| **H. Inpatient Care** | Inpatient experience | Admission details, length of stay, costs, billing |
| **I. Financial Risk Protection** | Health expenditure | OOP costs, distress financing, forgone care, catastrophic health expenditure |
| **J. Satisfaction** | Quality of care | Satisfaction with amenities, medical care, staff treatment |
| **K. Access to Medicines** | Drug availability | Generic drug access, medicine costs, pharmacy experience |
| **L. Referrals** | Referral experience | Referral process, satisfaction with referral system |

## Skip Logic Notes

- Outpatient vs. inpatient routing throughout (Sections G and H are mutually conditional).
- PhilHealth membership status affects routing in Sections D, I.
- Complex financial questions in Section I require careful validation (OOP amounts, income-relative thresholds).

## CAPI Development Notes

- 23 pages, longest face-to-face instrument alongside F4.
- Financial sections (I, N) need numeric validation with range checks and consistency checks (e.g., OOP ≤ total bill).
- Patient listing form (separate document) used to select respondents before this interview.
- Dual geographic identification: facility location AND patient home address.

## Sources

- Part of Deliverable 1 submitted to [[wiki/entities/DOH-PMSMD|DOH-PMSMD]]
- Developed by [[wiki/entities/ASPSI|ASPSI]] consultant team
