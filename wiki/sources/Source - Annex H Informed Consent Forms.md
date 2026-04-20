---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Project-Deliverable-1_Apr20-submitted/Annex H_Informed Consent Forms_ UHC Year 2.pdf]]"
date_ingested: 2026-04-20
tags: [deliverable-1, inception-report, informed-consent, ethics, capi-intro, ingest-batch-apr20]
---

# Source — Annex H: Informed Consent Forms

10-page annex containing **four Informed Consent Forms (ICFs)** — one per survey instrument — required under the SJREB ethics clearance (see [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Revised Inception Report|Revised IR]] Section V.E Ethical Considerations). Each ICF follows a PART I (Information about the Study) + PART II (Certificate of Consent) structure.

## The four ICFs

| # | ICF | Instrument | Token / Incentive | Witness clause |
|---|---|---|---|---|
| 1 | Facility Head Survey Questionnaire | [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F1 Facility Head Survey Questionnaire\|F1]] | None | No |
| 2 | Healthcare Worker Survey Questionnaire | [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F2 Healthcare Worker Survey Questionnaire\|F2]] | **PhP 1,000 raffle** (chance, not guaranteed) | No (self-admin email return) |
| 3 | Inpatient and Outpatient Survey Questionnaire | [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3 Patient Survey Questionnaire\|F3]] | **PhP 100 token** (guaranteed) | Yes — witness clause if respondent can't sign |
| 4 | Household Survey Questionnaire | [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F4 Household Survey Questionnaire\|F4]] | **PhP 100 token** (guaranteed) | Yes — witness clause if respondent can't sign |

## Common PART I content (all four ICFs)

- **Introduction**: Data collector identifies as ASPSI staff; study funded by DOH.
- **Scope names**: UHC + YAKAP (Yaman ng Kalusugan Program) + NBB (No Balance Billing) + ZBB (Zero Balance Billing) + BUCAS (Bagong Urgent Care and Ambulatory Services) + GAMOT (Guaranteed and Accessible Medications for Outpatient Treatment). All programs named verbatim — this wording is authoritative and must match CAPI intro screens exactly.
- **Study aim**: "to generate evidence on the overall experience of [respondents / healthcare workers / general public] to support continuous monitoring, evaluation, and learning of the implementation of the UHC Act and its Implementing Rules and Regulations (IRR)."
- **Duration**: ~1 hour ("more or less than an hour").
- **Privacy**: names kept separate from answers, never shared with government or included in reports, secure storage.
- **Voluntary participation**: decline / stop at any time without penalty; no cost to participate.

## Administration protocol (printed on each ICF)

> This informed consent form must be obtained before conducting the interview. You are required to read this entire consent form aloud exactly as written. After reading this form to the respondent, you must complete and sign the verification consent form.

For F1, F3, F4 (interviewer-admin CAPI path): read aloud, verbatim. For F2 (self-admin Google Form): consent embedded in the form itself + email return of signed PART II.

## Contact points (identical across all four ICFs)

- **SJREB** — sjreb.doh@gmail.com / sjreb@doh.gov.ph (F4 variant) · +63 (02) 8651-7800 ×1328 · +63 936 992 5513
- **DOH** — Lindsley Jeremiah D. Villarante · ldvillarante@doh.gov.ph · +63 (02) 8651-7800 ×1432
- **ASPSI** — Paulyn Jean A. Claro · aspsiglobal@gmail.com · +63 917 819 6884

## Respondent signature fields

Per-ICF PART II fields:

| ICF | Signature fields |
|---|---|
| F1 | Name + Signature · Position, Office · Email · Mobile Number |
| F2 | Name + Signature · Email Address · Mobile Number + email-return instruction |
| F3 | Name + Signature · Address (No., Street, Barangay, Municipality/City, Province) · Tel/Mobile · **optional witness** (name + signature + address + phone) |
| F4 | Name + Signature · Mobile Number · **optional witness** (name + signature + phone) |

## CAPI implications

- **CAPI intro screens** for F1, F3, F4 should mirror PART I verbatim. This is not paraphraseable — the SJREB-approved text is authoritative, and deviation risks ethics-clearance rework. Consider rendering as a read-only "teleprompter" screen the enumerator reads from.
- **F2 Google Form** already hosts its consent at form-start; confirm wording matches Annex H verbatim (Q0 "I have read and understood the informed consent form and agree to participate" gate).
- **PART II capture**: F3 and F4 optionally capture witness-signature fields. The CSPro data dictionary should include `witness_name`, `witness_address`, `witness_phone` fields as **optional** for F3/F4 (not on F1). These are ancillary metadata, not analysis items — file them under a CONSENT record separate from the main substantive items.
- **Token/incentive tracking**: F3/F4 guarantee PhP 100; F2 runs a PhP 1,000 raffle. This may need a `token_given` flag (F3/F4) for finance reconciliation with the Reimbursables budget line.
- **Multi-language requirement**: Annex H is English-only. The [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Revised Inception Report|Revised IR]] commits to translating questionnaires to Filipino/Tagalog, Ilocano, Bicolano, Ilonggo, Waray, Bisaya, Cebuano — the ICFs will need parallel translations before fieldwork, also SJREB-approved.

## Cross-references

- Ethics governance: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/SJREB|SJREB]]
- Instruments: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F1 Facility Head Survey Questionnaire|F1]] · [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F2 Healthcare Worker Survey Questionnaire|F2]] · [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3 Patient Survey Questionnaire|F3]] · [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F4 Household Survey Questionnaire|F4]]
- Parent: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Revised Inception Report|Revised Inception Report]] Section V.E

## Sources

- Raw file: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Project-Deliverable-1_Apr20-submitted/Annex H_Informed Consent Forms_ UHC Year 2.pdf|Annex H PDF]]
- Authored by [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/ASPSI|ASPSI]] project team for SJREB review
