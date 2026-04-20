---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Project-Deliverable-1_Apr20-submitted/Annex F4_Household Survey Questionnaire_UHC Year 2.pdf]]"
date_ingested: 2026-04-20
tags: [questionnaire, household, f4, survey-instrument, ingest-batch-apr20, community-survey]
---

# Source — Annex F4: Household Survey Questionnaire

Household Survey Questionnaire for [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/UHC Survey Year 2|UHC Survey Year 2]], **202 numbered items**. New for Year 2 — captures population-level UHC awareness and household expenditure. **Community survey** administered to household head or main decision-maker via **interval sampling starting from patient HH → neighbor HHs** (Annex G #6, #13).

**Version:** Apr 20 2026 Revised Inception Report submission (−33 KB vs Apr 08 — net trim despite new household-expenditure module). Supersedes Apr 08 baseline.

> [!info] Most material structural change across F-series
> F4 being a **community/household survey** (not a patient-centric follow-up) is the single biggest scope change in the Apr 20 submission. The original TOR required only Facility Head + HCW + Patient surveys; ASPSI added F4 as a community instrument to mitigate Year 1's patient-centric response bias. See [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex G DOH Recommendations Matrix|Annex G]] remarks #6 + #13.

## Structure

| Section | Topic | Key Data Collected |
|---|---|---|
| Field Control | Survey logistics | Team leader, enumerator, visit dates, result codes |
| Geographic ID | Household location | Region, province/HUC, city/municipality, barangay |
| **A. Introduction and Informed Consent Form Profile** | Consent process | Consent verification |
| **B. Respondent Profile** | Demographics | Name, age, sex, education, employment, income |
| **C. Household Roster and Characteristics** | Household composition | Household members roster (repeating record), demographics of each member |
| **D. Awareness on Universal Health Care (UHC)** | UHC knowledge | Awareness of UHC Act and provisions |
| **E. YAKAP/Konsulta Awareness** | PhilHealth program | Konsulta/YAKAP awareness and enrollment |
| **F. Bagong Urgent Care and Ambulatory Service (BUCAS) Awareness and Utilization** | Urgent care program | BUCAS awareness, utilization — named explicitly (Annex G #1) |
| **G. Access to Medicines** | Drug availability | GAMOT awareness, generic drug access |
| **H. PhilHealth Registration and Health Insurance** | Insurance coverage | PhilHealth membership, **category of member (registration type — Annex G #4)**, other insurance |
| **I. Primary Care Utilization** | Primary care access | Usual source of care, utilization patterns |
| **J. Household members' Health-Seeking Behavior and Outcomes** | Care decisions per member | **Regardless of recent facility visit** (Annex G #12): health-seeking, delay, forgone care |
| **K. Experiences and Satisfaction with Referrals** | Referral experience | Referral process, satisfaction |
| **L. No Balance Billing (NBB) Awareness and Utilization** | NBB | NBB awareness and utilization experience |
| **M. Zero Balance Billing (ZBB) Awareness and Utilization** | ZBB | ZBB awareness and utilization experience (Annex G #1, #7, #19) |
| **N. Household Expenditures** | Spending grid | **WHO household expenditures module** (Annex G #11): sub-tables A Food (last week), B Non-food/Non-health, E Health Products and Services (last 12 months) |
| **O. Sources of Funds for Health** | Health financing | Where money came from to pay for health (savings, borrowing, sold assets, donations, LGU) |
| **P. Financial Risk Protection: Incidence of Reduced/Delayed Care** | Distress financing + forgone care | Q197–199: delayed care, saw doctor but did not get treatment, willingness-to-pay for consultation |
| **Q. Anxiety about Household Finances** | Household finances | Q200–202: reduced spending on essentials, worry about paying for health needs, reasons |

## Skip Logic Notes

- Section C household roster: repeating record keyed by member line number; Section J loops over members for health-seeking items
- Section H PhilHealth: non-members skip member-only benefit items
- Sections L and M gated on awareness of NBB/ZBB programs
- Section N expenditure sub-tables each have their own "did you spend on this?" gate before amount
- Section P Q198 yes/no routing for willingness-to-pay follow-ups

## Changes from Apr 08 baseline

Driven by [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex G DOH Recommendations Matrix|Annex G remarks]]:

- **Community-survey framing confirmed** (Annex G #6 + #13): F4 structure firmly oriented to household-level data collection irrespective of facility visit. Interval sampling starts from patient HH.
- **Section F renamed and expanded**: "BUCAS Awareness" → "Bagong Urgent Care and Ambulatory Service (BUCAS) Awareness **and Utilization**" — utilization items added (Annex G #1).
- **Section H — PhilHealth registration type**: category-of-member (Direct/Indirect Contributor, Indigent/Sponsored/Lifetime/Senior/OFW/Dependent) added (Annex G #4).
- **Section J — health-seeking + delay + forgone care** at household level regardless of recent facility visit (Annex G #12).
- **Section L + M NBB/ZBB** explicit awareness + utilization experience (Annex G #1, #7, #19).
- **Section N — WHO household expenditures module** structure retained with sub-tables A (food weekly), B (non-food/non-health), E (health products/services, 12-month recall) (Annex G #11).
- **Section P — distress financing / forgone care for financial reasons** (Annex G #12).
- **Net item-count**: now 202 numbered items across 17 sections. Despite the –33 KB file-size drop, the schema did not shrink — PDF re-flow accounts for the size change.

## CAPI Development Notes

- Most complex instrument: 202 items across 17 sections.
- **Household roster** (Section C) requires repeating-record structure in CSPro — each household member gets a row.
- **Health-seeking behavior** (Section J) loops over household members.
- **Expenditure sub-tables** (N-A food weekly, N-B non-food, N-E health) need roster/grid data entry with item catalogs.
- Expenditure data enables computation of **catastrophic health expenditure (CHE)** using SDG 3.8.2 capacity-to-pay approach.
- **Sampling design** (Annex G #6): interval sampling of neighbor households starting from the patient's HH. Not a Labor Force Survey one-respondent-per-HH design in the strict sense — F4 respondent is household decision-maker.
- **PSGC value sets** for REGION / PROVINCE_HUC / CITY_MUNICIPALITY / BARANGAY — same inbound ASPSI dependency as F1.
- **DCF-generator impact**: F4 `generate_dcf.py` needs re-audit (previous build was 20 records / 460 items incl. 3 repeating against Apr 08; expect growth on Sections F, H, J, P).

## Cross-references

- Change-rationale map: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex G DOH Recommendations Matrix|Annex G DOH Recommendations Matrix]]
- Sibling instruments: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F1 Facility Head Survey Questionnaire|F1]], [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F2 Healthcare Worker Survey Questionnaire|F2]], [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3 Patient Survey Questionnaire|F3]]
- Programme concept: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/UHC Survey Year 2|UHC Survey Year 2]]

## Sources

- Part of [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Revised Inception Report|Revised Inception Report]] Apr 20 submission to [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/DOH-PMSMD|DOH-PMSMD]]
- Developed by [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/ASPSI|ASPSI]] consultant team
- Raw file: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Project-Deliverable-1_Apr20-submitted/Annex F4_Household Survey Questionnaire_UHC Year 2.pdf|F4 Apr 20 PDF]]
- Apr 08 baseline preserved at: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Project-Deliverable-1/Annex F4_Household Survey Questionnaire_UHC Year 2_Apr 08.pdf|F4 Apr 08 PDF]]
