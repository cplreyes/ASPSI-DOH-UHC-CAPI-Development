---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Project-Deliverable-1_Apr20-submitted/Annex E_Suggested Indicators for UHC Year 2.pdf]]"
date_ingested: 2026-04-20
tags: [deliverable-1, inception-report, indicators, item-mapping, doh-review, ingest-batch-apr20]
---

# Source — Annex E: Suggested UHC Survey Year 2 Indicators

24-page matrix mapping **104 suggested indicators** to 8 High-Level Research Questions (HLRQs), with consolidated DOH-unit remarks (RETAIN / AMEND / OMIT verdicts) and the **Year 2 Source item** (the actual question wording landed in F1/F2/F3/F4). Acts as the indicator-level counterpart to [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex A Data to be Collected and Sources|Annex A]] (data-to-sources crosswalk) and the review-level counterpart to [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex G DOH Recommendations Matrix|Annex G]] (paragraph-level DOH recommendations).

## Structure

Five columns per row:

| Column | Content |
|---|---|
| # | Indicator row number (1–104) |
| **High-Level Research Question** | The parent HLRQ (8 total) |
| **Indicator** | Indicator title + reference code (e.g., 7.A, 7.B, 7.C, 7.D, 7.F, 8.C) |
| **Consolidated Remarks from DOH units** | Per-indicator review notes from OAAED, HFDB, HPB, HPDPB + RETAIN/AMEND/OMIT verdict |
| **Year 2 Source** | Actual question wording, bracket-tagged by instrument: `[PATIENT]`, `[HH]`, `[FACILITY]`, `[HCW]`, `SECONDARY DATA TO BE REQUESTED FROM HEALTH FACILITIES`, or `-` (omitted) |

## 8 High-Level Research Questions (with row ranges)

| # | HLRQ | Indicator rows | Primary instrument(s) |
|---|---|---|---|
| 1 | To what extent is the general population aware of UHC, including the full range of benefits it entitles them to and how to access them? | 1–11 | PATIENT, HH |
| 2 | Do Filipinos (esp. indigent/otherwise vulnerable population) complete the registration process (primarily through PhilHealth) successfully to enroll in UHC? | 12–17 | PATIENT, HH |
| 3 | How do patients engage with health care facilities and health care providers under UHC? | 18–20 | PATIENT |
| 4 | Is the UHC rollout associated with improved health-care access, quality, and financial risk protection for Filipino population? | 21–36 | PATIENT, HH |
| 5 | Are patients satisfied with the quality of care they receive under UHC? | 37–51 | PATIENT |
| 6 | To what extent are facilities able to serve patients' needs under UHC? | 52–55 | FACILITY |
| 7 | What are the main barriers facilities face in implementing HCPNs and the full range of benefits under UHC? | 56–68 | FACILITY |
| 8 | What human-resource constraints do HCWs face in implementing UHC? | 69–104 | FACILITY, HCW |

## DOH-unit review verdicts (vocabulary)

- **RETAIN** — keep the indicator as is
- **AMEND** — modify wording/scope (most common verdict; frequent drivers: "Konsulta → YAKAP rename", "shift recall to registered evidence")
- **OMIT** — drop the indicator (often because it's a PhilHealth internal concern, not UHC public awareness)

Reviewing units mentioned in the matrix: **OAAED** (Office of the Assistant Secretary for Affiliated Entities and Development), **HFDB** (Health Facility Development Bureau), **HPB** (Health Promotion Bureau), **HPDPB** (Health Policy Development and Planning Bureau).

## Item-mapping value for CAPI

Each indicator's **Year 2 Source** column is the authoritative link between "indicator #N" (analysis layer) and "CAPI item Qn" (data-collection layer). This is the crosswalk that lets Annex I [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex I Dummy Tables|Dummy Tables]] populate from the CSPro export.

**Bracket-tag convention** seen in the matrix:
- `[PATIENT]` → F3 items
- `[HH]` → F4 items
- `[FACILITY]` → F1 items (primary or Secondary Data)
- `[HCW]` → F2 items
- `SECONDARY DATA TO BE REQUESTED FROM HEALTH FACILITIES` → F1 Secondary Data record (Annex A Section 3)
- `-` → indicator omitted per DOH verdict; no CAPI item

## Representative examples

| Ind. # | Indicator (abbrev.) | Verdict | Year 2 Source |
|---|---|---|---|
| 1 | % population who have heard about UHC | OAAED AMEND | [PATIENT] + [HH] "Have you heard about UHC prior to this survey?" |
| 9 | % patients who have heard of YAKAP/Konsulta provider | OAAED RETAIN, HFDB AMEND | [PATIENT] + [HH] "Have you heard of the term YAKAP/Konsulta provider?" |
| 14 | % eligible indirect contributors registered as such | OAAED OMIT | `-` (PhilHealth concern) |
| 97 | % primary-care facilities with >7-day essential-medicine stock-outs last quarter | — | [FACILITY] stock-out questions |
| 101 | % facilities submitting routine data to DOH IS / PhilHealth Dashboard | — | SECONDARY DATA TO BE REQUESTED + [FACILITY] Q135-type items ([[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex G DOH Recommendations Matrix\|Annex G]] #3) |
| 104 | Average TAT for PhilHealth claim reimbursements | — | [FACILITY] capitation tranches question |

## Cross-instrument linkage

Many indicators specify **dual-source capture** (both [PATIENT] and [HH]) — this is the parallel-item design already reflected in [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3 Patient Survey Questionnaire|F3]] and [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F4 Household Survey Questionnaire|F4]] Sections A/B/C/D/E/F (UHC awareness / PhilHealth / YAKAP/Konsulta / BUCAS / GAMOT / NBB / ZBB).

## CAPI/analysis implications

- **Data-dictionary coverage check:** for every RETAIN or AMEND verdict, the corresponding CAPI item MUST exist in the named F-instrument. Treat Annex E as the completeness-audit input for the DCF generators.
- **Omitted indicators (`-` in Year 2 Source):** do NOT appear in any questionnaire. Don't add them back without DOH approval.
- **Secondary Data items:** the `SECONDARY DATA TO BE REQUESTED FROM HEALTH FACILITIES` bracket-tag in Annex E maps to [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex A Data to be Collected and Sources|Annex A]] Section 3 — the F1 Secondary Data record must carry these columns.
- **Dummy-table drivers:** [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex I Dummy Tables|Annex I]] tables are computed from the Year-2-Source items named here; a missing item → a blank dummy table.

## Cross-references

- Data-to-sources crosswalk: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex A Data to be Collected and Sources|Annex A]]
- Paragraph-level review: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex G DOH Recommendations Matrix|Annex G]]
- Questionnaires receiving the items: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F1 Facility Head Survey Questionnaire|F1]] · [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F2 Healthcare Worker Survey Questionnaire|F2]] · [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3 Patient Survey Questionnaire|F3]] · [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F4 Household Survey Questionnaire|F4]]
- Analysis output: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex I Dummy Tables|Annex I (Dummy Tables)]]
- Parent: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Revised Inception Report|Revised Inception Report]]

## Sources

- Raw file: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Project-Deliverable-1_Apr20-submitted/Annex E_Suggested Indicators for UHC Year 2.pdf|Annex E PDF]]
- Authored by [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/ASPSI|ASPSI]] project team with consolidated comments from DOH units (OAAED, HFDB, HPB, HPDPB)
