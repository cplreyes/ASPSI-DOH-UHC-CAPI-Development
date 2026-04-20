---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Project-Deliverable-1_Apr20-submitted/Annex A_Data to be Collected and Sources_UHC Year 2.pdf]]"
date_ingested: 2026-04-20
tags: [deliverable-1, inception-report, data-mapping, catastrophic-health-expenditure, facility-records, ingest-batch-apr20]
---

# Source — Annex A: Data to be Collected and Sources

6-page matrix + methodological supplement accompanying the Apr 20 2026 Revised Inception Report. Two sections:

1. **Data-to-sources crosswalk** — maps each "Data to be Collected" concept to its Primary source (which F-instrument) and Secondary source (facility records / PhilHealth databases / program docs).
2. **Catastrophic Health Expenditure (CHE) methodology** — two-approach comparison (Budget Share vs. Capacity-to-pay) driving F3/F4 financial-risk analysis.
3. **Secondary Data requested from Health Facilities** — facility-records template covering Patient Load, Human Resources, YAKAP/Konsulta Package Services + Pricing.

## Data-to-sources crosswalk (Section 1)

| Data to be Collected | Primary | Secondary |
|---|---|---|
| Awareness and understanding of UHC | Patients, household heads, **community survey** | Facility records |
| PhilHealth registration/enrollment, benefits, reasons for not enrolling, issues | Patients, household heads, community survey | — |
| Awareness/understanding of **YAKAP/Konsulta, ZBB, BUCAS, GAMOT** + access | Patients, household heads, community survey | Facility records |
| YAKAP/Konsulta registration and enrollment | Patients, household heads, community survey | Facility records |
| Reasons for enrolling / not enrolling to YAKAP/Konsulta | Health facility heads, healthcare workers | Patients, household heads, community survey |
| Change in service delivery process under UHC | Health facility heads, healthcare workers | Program/project docs, reports, MOAs, ordinances |
| Level of satisfaction with quality of care | Health facility heads, healthcare workers | — |
| LGU support in UHC implementation | Health facility heads, healthcare workers | — |
| Facility enablers/barriers implementing HCPNs + full UHC benefits | Health facility heads, healthcare workers | Facility records |
| Adequacy of human resources enablers + constraints | Health facility heads, healthcare workers | — |
| Effect of progressive PhilHealth benefits 2024–2025 on financial risk protection, service delivery, beneficiary experience | Patients, household heads, health facility heads, healthcare workers | PhilHealth evaluation reports, YAKAP/Konsulta DB, M&E reports |
| YAKAP/Konsulta + ZBB + BUCAS + GAMOT utilization, accreditation, capitation payment status | Patients, household heads, health facility heads, healthcare workers | — |
| Barriers on availing YAKAP/Konsulta + ZBB + BUCAS + GAMOT benefits | Patients, household heads | — |
| Satisfaction level on YAKAP/Konsulta + ZBB + BUCAS + GAMOT | Patients, household heads | — |

### Primary-source implications for F-series

- **Community survey** appears as a Primary source column in nearly every row. This is the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F4 Household Survey Questionnaire|F4 community/household survey]] — reinforces [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex G DOH Recommendations Matrix|Annex G #6 + #13]] scope addition.
- **"Facility records" as Secondary source** = F1 Secondary Data section (pages 33–37 of the Apr 20 F1 PDF).
- **Every F-instrument shows up** in at least one Primary row, confirming all four are load-bearing.

## Catastrophic Health Expenditure methodology (Section 2)

Reference: **Nguyen et al., 2023**. Two primary CHE approaches:

| | Budget Share Approach | Capacity-to-pay Approach |
|---|---|---|
| **Definition** | OOP payments exceed defined proportion of total household income or expenditure | OOP payments exceed defined proportion of household's capacity to pay (available HH expenditure **after basic needs**) |
| **Numerator** | OOP payments | OOP payments |
| **Denominator** | Total household expenditure OR total household income | **Sub-method 1:** Total HH expenditure minus actual food spending. **Sub-method 2:** Total HH expenditure minus standard subsistence food spending. **Sub-method 3:** Total HH expenditure minus standard subsistence spending on food, rent, and utilities |
| **Standard thresholds** | 10% and 25% | 25% and 40% (sub-1); 40% (sub-2); 40% (sub-3) |

**Implication for F3/F4:** Section I (F3) and Section N (F4) must capture OOP payments + household expenditure in a form that supports **both** approaches — numerator items (OOP) and denominator components (total HH expenditure, food spending, subsistence baselines). The F4 N-A food-items table + N-E health-products table directly feed the Capacity-to-pay denominator.

## Secondary Data Requested from Health Facilities (Section 3)

This is the **F1 Secondary Data template** — the tables appended to the F1 CAPI instrument for facility-records extraction.

### 1. Patient Load

- Outpatients — average per day, last 6 months
- Inpatients — average per day, last 6 months

### 2. Human Resources

**2a. Full-time + part-time staff by role** (16 roles: Doctors, Midwives, Nurses, Nurses-RHC, Pharmacists/Technicians, Technologists med/radiology/respiratory, Laboratory technicians, Health promotion officers, Nutritionists, Physiotherapy officers, Nursing assistants, Dentists, Dental Aides, Data encoders, Other)
- Per role: Full-time counts by status (Regular / Probationary / Project-based / Casual) + Part-time count
- Per role: Number of staff to fulfill minimum requirements

**2b.** Full-time staff who left the facility in past 6 months
**2c.** Contractual healthcare workers not renewed

### 3. YAKAP/Konsulta Package Services

**3a. Availability checklist** — 14 services: CBC with platelet count, Urinalysis, Fecalysis, Sputum Microscopy, Fecal Occult Blood, Pap smear, Lipid profile, FBS, OGTT, ECG, Chest X-Ray, Creatinine, HbA1c, Abdominal ultrasound. Each: Yes/No.

**3b. Diagnostics pricing** — for the 14 services: Procurement Cost + Standard Price Charged to Patients (in PHP).

**3c. Consultation + room-and-board pricing** — Physician consultation (general practitioner + specialist), Private room and board per night, Shared room and board per night. Procurement Cost + Standard Price Charged to Patients.

**3d.** Standard markup for all laboratory services? Yes/No + amount.

## Implications for CSPro / CAPI development

- **F1 Secondary Data record** must accommodate Section 3 above: `build_secondary_data_stubs()` in F1 `generate_dcf.py` currently creates stubs — these should be expanded to capture the explicit 14-service × 2-price grid and the 16-role × 4-status staffing matrix (repeating record or explicit columns).
- **Apr 20 Annex A is authoritative** for what Secondary Data fields F1 must collect — supersedes whatever the Apr 08 generator currently stubs.
- **F3 + F4 CHE computation**: analysis layer, not CAPI schema. But the CAPI must capture denominator components (HH expenditure sub-tables) to enable CHE calculation downstream.
- No new Primary-instrument items land from Annex A — it's a data-mapping document, not a new question source. Item-level additions come from [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex G DOH Recommendations Matrix|Annex G]].

## Cross-references

- Primary-instrument sources: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F1 Facility Head Survey Questionnaire|F1]], [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F2 Healthcare Worker Survey Questionnaire|F2]], [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3 Patient Survey Questionnaire|F3]], [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F4 Household Survey Questionnaire|F4]]
- Change-rationale map: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex G DOH Recommendations Matrix|Annex G]]
- Programme concept: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/UHC Survey Year 2|UHC Survey Year 2]]
- Sibling annex (indicator mapping): Annex E — Suggested Indicators (pending ingest in Step 6)

## Sources

- Part of [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Revised Inception Report|Revised Inception Report]] Apr 20 submission to [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/DOH-PMSMD|DOH-PMSMD]]
- Authored by [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/ASPSI|ASPSI]] project team
- Raw file: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Project-Deliverable-1_Apr20-submitted/Annex A_Data to be Collected and Sources_UHC Year 2.pdf|Annex A PDF]]
