---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Project-Deliverable-1_Apr20-submitted/Annex I_Dummy Tables_ UHC Year 2.pdf]]"
date_ingested: 2026-04-20
tags: [deliverable-1, inception-report, dummy-tables, analysis-plan, tabulation-spec, ingest-batch-apr20]
---

# Source — Annex I: Dummy Tables

29-page tabulation-specification annex: **51 dummy tables** across four instrument-blocks showing the exact cross-tabulations and frequency breakdowns the final UHC Year 2 report must populate. Header note: "as of March 06, 2026" — pre-dates the Apr 20 submission by ~6 weeks, flagging that this annex may trail the Apr 20 questionnaire revisions.

## Block structure (table prefix = instrument)

| Prefix | Instrument | Table count | Coverage |
|---|---|---|---|
| **A** | [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F1 Facility Head Survey Questionnaire\|F1 Facility Head]] | **14** (A1–A14) | Demographics, service-capacity, UHC awareness, YAKAP/Konsulta compliance, BUCAS reasons, referral methods, HR challenges, prof-dev forms |
| **B** | [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F2 Healthcare Worker Survey Questionnaire\|F2 HCW]] | **10** (B1–B10) | IS distribution, role × employment status, expected work changes, YAKAP/NBB/ZBB awareness, BUCAS utilization factors, job satisfaction, burnout, intention-to-leave |
| **C** | [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3 Patient Survey Questionnaire\|F3 Patient]] | **18** (C1–C18) | UHC + PhilHealth awareness, info-source + benefit-knowledge for each of UHC/YAKAP/BUCAS/GAMOT/NBB/ZBB, PhilHealth registration, primary-care-provider, OOP payments |
| **D** | [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F4 Household Survey Questionnaire\|F4 Household]] | **9** (D1–D9) | HH awareness of UHC/YAKAP/BUCAS/GAMOT/NBB/ZBB, payment sources, visit reasons, OOP payments |

## F1 (A-series) tables

| # | Title (abbrev.) |
|---|---|
| A1 | Respondents by role in the health facility (11 roles) |
| A2 | Respondents by age group (18-24, 25-44, 45-59, 60+) |
| A3 | Respondents by sex at birth (F/M) |
| A4 | Facilities by service capacity level (PCF, L1, L2, L3) |
| A5 | UHC awareness × facility level (Yes/No) |
| A6 | UHC-led changes at the facility (primary care package) |
| A7 | YAKAP/Konsulta accreditation requirements reported as difficult |
| A8 | Compliance challenges with YAKAP/Konsulta accreditation |
| A9 | Reasons for not having a BUCAS center |
| A10 | Outbound referral methods |
| A11 | Outbound referral form types |
| A12 | HR challenges |
| A13 | Professional-development forms for doctors |
| A14 | Professional-development forms for nurses |

## F2 (B-series) tables

| # | Title (abbrev.) |
|---|---|
| B1 | HCWs by UHC integration site |
| B2 | HCWs by role × employment status |
| B3 | Expected changes in personal work as HCW |
| B4 | YAKAP/Konsulta awareness (% aware) |
| B5 | NBB + ZBB awareness |
| B6 | NBB + ZBB information sources |
| B7 | BUCAS center utilization factors |
| B8 | Job satisfaction rating summary |
| B9 | Work burnout experiences summary |
| B10 | Reasons for intention to leave |

## F3 (C-series) tables

| # | Title (abbrev.) |
|---|---|
| C1 | Awareness of UHC + PhilHealth program/packages |
| C2 | Info sources on UHC |
| C3 | Knowledge of UHC benefits |
| C4 | Info sources on YAKAP/Konsulta |
| C5 | Knowledge of YAKAP/Konsulta benefits |
| C6 | Info sources on BUCAS |
| C7 | Knowledge of BUCAS benefits |
| C8 | Info sources on GAMOT |
| C9 | Knowledge of GAMOT benefits |
| C10 | Info sources on NBB |
| C11 | Knowledge of NBB benefits |
| C12 | Info sources on ZBB |
| C13 | Knowledge of ZBB benefits |
| C14 | PhilHealth-registered patients |
| C15 | Patients with a primary care provider |
| C16 | Communication modes with primary care provider |
| C17 | Patients' usual health facility by facility type |
| C18 | Average OOP payments on health services |

## F4 (D-series) tables

| # | Title (abbrev.) |
|---|---|
| D1 | UHC awareness among household population |
| D2 | YAKAP/Konsulta awareness |
| D3 | BUCAS center awareness |
| D4 | GAMOT package awareness |
| D5 | NBB awareness |
| D6 | ZBB awareness |
| D7 | Payment sources for medical expenses |
| D8 | Reasons for visiting a health facility |
| D9 | Average OOP payments |

## Analysis-plan implications

- **All tables are frequency / cross-tab style** (n, %) — no regression, no weighting machinery shown here. Weighting implementation is downstream (per [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex D Replacement Protocol|Annex D]] + IR Section V.D).
- **Mirror coverage F3 ↔ F4**: per-program info-source + benefit-knowledge pairs appear for all 6 programs (UHC, YAKAP/Konsulta, BUCAS, GAMOT, NBB, ZBB). Confirms Apr 20 parallel-item design in F3 Sections A–F and F4 Sections A/E/F.
- **OOP averages (C18, D9)**: require numeric OOP items in F3 Section I and F4 Section N — the CHE denominator components from [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex A Data to be Collected and Sources|Annex A]] Section 2 feed these.
- **F2 burnout table (B9)** — retained in the dummy-table plan despite [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex G DOH Recommendations Matrix|Annex G]] #23 ("reduce or possibly remove"). Treat B9 as an indicator that burnout remains expected in the output set; do NOT drop burnout items from the F2 build without a coordinated Annex-I revision.

## CAPI implications

- **Data-dictionary completeness check**: every column and row labeled in Annex I must have a corresponding CAPI item populating it. Missing items → empty dummy tables.
- **Value-set alignment**: dummy-table row labels (e.g., A1's 11 roles, A4's 4 facility levels, A2's age groups 18-24/25-44/45-59/60+) are the **authoritative value-set specifications** for analysis — the CAPI data dictionaries should produce answers that map cleanly into these bins. Check for range-code drift.
- **Cross-instrument labels** (e.g., B2's role × employment-status matrix) match the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex A Data to be Collected and Sources|Annex A]] Section 3 HR matrix (16 roles × 4 FT statuses). Keep these aligned: if Annex A expands to 16 roles and Annex I's A1 shows 11, there's a downstream crosswalk to maintain.

> [!warning] Annex I pre-dates the Apr 20 questionnaires
> The Mar 06 2026 header means Annex I was drafted against an earlier questionnaire state. Items added in the Apr 20 revision ([[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex G DOH Recommendations Matrix|Annex G]]-driven: BUCAS utilization in F4, 4Ps in F3, DOH IS submissions in F1, etc.) may not have dummy tables yet. Expect an Annex I revision in a later deliverable cycle.

## Cross-references

- Indicators driving each table: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex E Suggested Indicators|Annex E]]
- Source items: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F1 Facility Head Survey Questionnaire|F1]] · [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F2 Healthcare Worker Survey Questionnaire|F2]] · [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3 Patient Survey Questionnaire|F3]] · [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F4 Household Survey Questionnaire|F4]]
- Data-source crosswalk: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex A Data to be Collected and Sources|Annex A]]
- Parent: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Revised Inception Report|Revised Inception Report]]

## Sources

- Raw file: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Project-Deliverable-1_Apr20-submitted/Annex I_Dummy Tables_ UHC Year 2.pdf|Annex I PDF]]
- Authored by [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/ASPSI|ASPSI]] project team
