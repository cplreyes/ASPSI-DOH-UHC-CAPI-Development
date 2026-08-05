---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/XJ-PAPI-vs-CAPI-Reviews-2026-07/PAPI-vs-CAPI-HCW-XJ-review]] — Google Drive `1FnA30wsQ6A6BiIhg4cD68spFIoUDp6n3`, `4_PAPI vs CAPI_HCW_XJ review.docx`, owner xyleej@gmail.com (Xylee \"XJ\" Javier), modified 2026-07-13"
date_ingested: 2026-07-20
tags: [capi, survey-design, doh-comments, parked-decision, f2-hcw, papi-vs-capi, xj-review, pwa]
---

# Source - PAPI vs CAPI HCW Review (XJ 2026-07)

DOH reviewer **Xylee "XJ" Javier**'s side-by-side **PAPI-vs-CAPI comparison of the Healthcare Worker
(F2) instrument** — the PWA. A screenshot-driven `.docx`, companion to the
[[Source - PAPI vs CAPI Household Review (XJ 2026-07)|Household review]] (numbered "4_" in the same
set). Downloaded from Carl's shared Drive folder and ingested 2026-07-20.

> [!important] Same parked posture
> This rides the same DOH/PSA review track as the
> [[Source - DOH June Questionnaire Comments (PARKED) 2026-06-19|June parked comments]] — Myra's
> 2026-06-12 ruling governs: **April-baseline accepted; deferred to SJREB/PSA/pre-test; no
> instruction to Carl.** As with the HH review, XJ has **no CAPI test-environment access** and is
> reviewing the **April screenshot** set, so many "not observed" items are already in the live build.

## The distinctive HCW thread: it's a different interface

Unlike F1/F3/F4 (CSPro/CSEntry), **F2 is the PWA** — so XJ opens by noting the HCW CAPI "appears to
use a different interface," asks for the rationale for different platforms across instruments, and —
notably — judges the HCW interface the **more polished one**: it has section headers, progress
indicators, streamlined questions, and **no repeated question text** (the very defect he flags on the
CSPro instruments). His recommendation is to make the others *consistent with F2*, not the reverse.
(This is the [[F2 Admin Portal|PWA]] vs CSPro-CAPI design split, by design.)

## What XJ raises (F2)

**Missing sections in the screenshots:** Questionnaire Number, Informed Consent Form, Field Control,
and Health Facility & Geographic Identification are "not observed" — clarify how implemented in CAPI;
and whether the **offline** version matches the online interface or resembles PAPI. (The per-case
Consent gate shipped in F2 R6; enrolment carries the facility/QN — see [[F2 Admin Portal]].)

**System behaviour (clarifications):** navigation controls, autosave on interruption, resume of an
incomplete questionnaire from last save, session timeout — one question each. (F2 has IndexedDB
autosave + resume in production.)

**Required-field legend:** the red asterisk (*) has no legend — add a note if it marks required fields.

**Skip-pattern matrix / test environment:** same recurring ask as HH — provide a skip matrix,
programming specs, or test access; confirm applicability rules match PAPI. Specific routing items:
- **Q38:** can "Not a physician/dentist" be auto-determined from role in Q5? implement as a condition.
- **E1/E2:** BUCAS / GAMOT sub-headers not shown.
- **Q61/62/63:** possible "proceed to Q63" typo (Q62?); who answers Q62 given Q61's skip?
- **Q69/70/71:** do "yes" in Q69 and Q70 get a separate Q71 input field as in PAPI?

**Validation checks to watch:** exclusive-option blocking; prevent simultaneous exclusive selections;
catch single-vs-multi mismatches. (Exclusivity fixes shipped as #830/#832 on the CSPro side; F2 has
its own.)

**Notes / instructions:** Q35 date design (Year required, Month/Day optional) is **praised as an
improvement** — apply consistently; missing instruction before **Q98** (up to Q107) and **Q113** (up
to Q120); a "None" option added in CAPI; **employment-type definitions** from PAPI not shown — surface
via help text/tooltips (this is the #826 "\n"-rendered Q2 definitions work — see
[[F2 Admin Portal]]). "Select one answer only" not observed — confirm enforced by the interface.
**Q6** has no CAPI screenshot.

**Other (specify) missing "specify" field** — item list: Q2, 5–6, 13, 15, 17–25, 34, 36–37, 39,
42–43, 45–47, 50, 52, 55–57, 60, 62, 92–94, 109–110, 112, 123–124.

**Input labels for numeric+units:** add "Year(s)"/"Day(s)"/"Hour(s)" input labels as in Q9; Q10
(days) and Q11 (hours) lack them.

## Cross-references

- Same reviewer + posture: [[Source - DOH June Questionnaire Comments (PARKED) 2026-06-19]]
- Companion instrument review: [[Source - PAPI vs CAPI Household Review (XJ 2026-07)]]
- Shared review criteria across both: [[PAPI-to-CAPI Translation Review Criteria]]
- Build-status mapping (interpretation): [[Analysis - XJ PAPI-vs-CAPI Reviews vs Current CAPI Build]]
- Instrument baseline: [[Source - Annex F2 Healthcare Worker Survey Questionnaire]]
- Prior HCW review track: [[Source - HCW CAPI Comments Matrix (Myra answers 2026-05-21)]]
