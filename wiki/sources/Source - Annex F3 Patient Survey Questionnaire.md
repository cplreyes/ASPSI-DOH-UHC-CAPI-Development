---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Project-Deliverable-1_Apr20-submitted/Annex F3_Patient Survey Questionnaire_UHC Year 2.pdf]]"
date_ingested: 2026-04-20
tags: [questionnaire, patient, f3, survey-instrument, ingest-batch-apr20]
---

# Source — Annex F3: Patient Survey Questionnaire

Patient Survey Questionnaire for [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/UHC Survey Year 2|UHC Survey Year 2]], **178 numbered items**. Face-to-face CAPI interview with **inpatients and outpatients** at sampled health facilities (Annex G #15 expanded scope beyond outpatient-only).

**Version:** Apr 20 2026 Revised Inception Report submission (+36 KB vs Apr 08). Supersedes Apr 08 baseline.

## Structure

| Section | Topic | Key Data Collected |
|---|---|---|
| Field Control | Survey logistics | Team leader, enumerator, visit dates, result codes |
| Geographic ID | Facility + patient location | Facility ID, patient address, barangay |
| **A. Introduction and Informed Consent** | Consent process | Consent verification, respondent relationship (self / companion) |
| **B. Patient Profile** | Demographics | Name, age, sex, education, employment, income, **4Ps / Pantawid household beneficiary status (Q32)**, household decision-maker |
| **C. Awareness on Universal Health Care (UHC)** | UHC knowledge | Awareness of UHC Act and key programs |
| **D. PhilHealth Registration and Health Insurance** | Insurance status | PhilHealth membership, **category of member (Q45 — Formal/Informal/Indigent/Sponsored/Lifetime/Senior/OFW/Dependent) = PhilHealth registration type**, other insurance, YAKAP/Konsulta enrollment |
| **E. Primary Care Utilization** | Primary care access | Usual source of care, PCF utilization, barriers |
| **F. Patient's Health-Seeking Behavior** | Care decisions | Facility choice, reasons for visit, **bypassing primary care** (Annex G #22) |
| **G. Outpatient Care** | Outpatient experience | Services received, waiting time, costs, medicines, OOP lines |
| **H. Inpatient Care** | Inpatient experience | Admission details, length of stay, costs, billing, **NHTS/CCT/4Ps Requirement** markers |
| **I. Financial Risk Protection** | Health expenditure | OOP costs, distress financing, forgone care, catastrophic health expenditure, **payments for medicines purchased outside facility (Q109), services outside facility (Q112)** |
| **J. Satisfaction on Amenities and Medical Care** | Quality of care | Satisfaction with amenities, medical care, staff treatment |
| **K. Access to Medicines** | Drug availability | Generic vs branded, pharmacy access, GAMOT knowledge + utilization (Q152–161) |
| **L. Experiences and Satisfaction on Referrals** | Referral experience | Referral process, follow-through, satisfaction (Q162–178) |

## Skip Logic Notes

- Outpatient vs. inpatient routing (Sections G and H are mutually conditional; F3 now covers BOTH per Annex G #15)
- PhilHealth membership status affects routing in Sections D, I (Q45 skip to Q51 for non-members)
- Q30 "Other, No" on NHTS membership → skip Q31
- Q33 patient-is-decision-maker → skip Q34 (who-decides roster)
- Complex financial questions in Section I require careful validation (OOP amounts, income-relative thresholds)

## Changes from Apr 08 baseline

Driven by [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex G DOH Recommendations Matrix|Annex G remarks]]:

- **Q32 added**: 4Ps household beneficiary status — direct response to **Annex G #11** (CCT/4Ps membership question).
- **Q45 PhilHealth member category** explicit (Formal/Informal/Indigent/Sponsored/Lifetime/Senior/OFW/Dependent) — direct response to **Annex G #4** (type of PhilHealth registration).
- **Expanded OOP lines** in Section I: medicines purchased outside hospital (Q108–109), services outside hospital (Q110–112), and take-home medicines treatment — direct response to **Annex G #10**.
- **F3 respondent universe**: now inpatient + outpatient (was outpatient-only in spirit per TOR) — **Annex G #15**.
- **Private clinics within hospital premises**: included in patient-exit sampling — **Annex G #15** (affects F3 sampling, not schema).
- **BUCAS / PuroKalusugan / ZBB coverage** woven through Sections C, E, G (**Annex G #1**).
- **Section L expanded**: Q162–178 cover referral follow-through (did you visit, did PCP follow up, did they write for specialist, rating of experience).
- **Net item-count growth**: ~126 → 178 items (+52).

## CAPI Development Notes

- Longest face-to-face instrument; dual-mode (outpatient + inpatient) routing makes skip logic complex.
- Financial section (I) needs numeric validation with range checks and consistency checks (e.g., OOP ≤ total bill, outside-facility payments reconcile with Q108/Q110 "did you pay outside?" gates).
- Patient listing form (**F3b, separate document**) used to select respondents before this interview.
- Dual geographic identification: facility location AND patient home address.
- **PSGC value sets** for REGION / PROVINCE_HUC / CITY_MUNICIPALITY / BARANGAY are **self-served + wired** from the PSA 1Q 2026 Publication (shared with F1 via `F1/inputs/`) — see [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/PSGC Value Sets|PSGC Value Sets]]. No longer an ASPSI-inbound dependency.
- **DCF-generator status**: Apr 20 rewrite complete across all sections A–L (2026-04-21, landed in 8 per-chunk commits). Current build: **15 records / 818 items** (up from 15 records / 387 items on the Apr 08 baseline). Skip logic targets (Q10 No→Q12, Q145 Never→Q152, Q152 No→Q158, Q158 No→Q162, Q162 No→end, Q169 2/3→Q171, Q172 No→Q177, etc.) left for the logic-pass phase.

## Cross-references

- Change-rationale map: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex G DOH Recommendations Matrix|Annex G DOH Recommendations Matrix]]
- Paired listing protocol: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Patient Listing Form|F3b Patient Listing Protocol]]
- Sibling instruments: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F1 Facility Head Survey Questionnaire|F1]], [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F2 Healthcare Worker Survey Questionnaire|F2]], [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F4 Household Survey Questionnaire|F4]]
- Programme concept: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/UHC Survey Year 2|UHC Survey Year 2]]

## Sources

- Part of [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Revised Inception Report|Revised Inception Report]] Apr 20 submission to [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/DOH-PMSMD|DOH-PMSMD]]
- Developed by [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/ASPSI|ASPSI]] consultant team
- Raw file: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Project-Deliverable-1_Apr20-submitted/Annex F3_Patient Survey Questionnaire_UHC Year 2.pdf|F3 Apr 20 PDF]]
- Apr 08 baseline preserved at: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Project-Deliverable-1/Annex F3_Patient Survey Questionnaire_UHC Year 2_Apr 08.pdf|F3 Apr 08 PDF]]
