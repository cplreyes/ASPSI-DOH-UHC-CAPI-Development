---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/XJ-PAPI-vs-CAPI-Reviews-2026-07/PAPI-vs-CAPI-HH-XJ-review]] — Google Drive `1B598jCvifKkH1FsBIgUTictPjNUO5ASf`, `1_PAPI vs CAPI_HH_XJ review.docx`, owner xyleej@gmail.com (Xylee \"XJ\" Javier), modified 2026-07-13"
date_ingested: 2026-07-20
tags: [capi, survey-design, doh-comments, parked-decision, f4-household, papi-vs-capi, xj-review]
---

# Source - PAPI vs CAPI Household Review (XJ 2026-07)

DOH reviewer **Xylee "XJ" Javier**'s side-by-side **PAPI-vs-CAPI comparison of the Household (F4)
instrument** — a screenshot-driven `.docx` walking the paper questionnaire against the CAPI screens
section by section. Downloaded from Carl's shared Drive folder and ingested 2026-07-20.

> [!important] This is the previously-missing F4 comment matrix
> The [[Source - DOH June Questionnaire Comments (PARKED) 2026-06-19|June parked-comments source]]
> recorded that **no F4 comment matrix existed yet** — Myra: *"I did not see the comments for the
> household survey… Pahabol in a separate document."* **This document is that pahabol.** It arrives
> under the **same parked posture**: XJ is the same reviewer, this is the same DOH/PSA review track,
> and Myra's 2026-06-12 ruling still governs — the **April 20 build is the accepted baseline**, these
> comments are **deferred to what surfaces in SJREB review · PSA review · pre-testing**, and there is
> **no instruction to Carl** to implement them now. (File is numbered "1_" in a set of four —
> HH = 1, HCW = 4; F1/F3 numbered docs were not in the shared folder.)

## Nature of the comments

Almost all are **clarification requests and observations from screenshots**, not approved change
orders. Two structural facts shape them: (1) XJ has **no access to the CAPI test environment**, so
skip logic and validations can't be verified — hence the recurring ask for a **skip-pattern matrix /
programming specs / test access**; (2) the screenshots reviewed are the **April submission** set, so
many "not observed" items are already built in the current instrument (see the analysis page).

## What XJ raises (F4)

**System behaviour (clarifications):** navigation controls, autosave on interruption, resume of
incomplete interviews from last save, session timeout handling — one question each. Field Control
appears at the end: can it be accessed/updated mid-interview for callbacks?

**Disposition + visits:** justify "Refused" → "Withdraw Participation/Consent" (April change);
harmonize disposition codes and their order across F1/F2/F4 (Completed, Postponed, Refused,
Incomplete); explain the visit-date format change (PAPI M-D-Y vs CAPI YYYYMMDD); the manual allows up
to **three callbacks in the Visit Sheet** but CAPI records only first + final visit — how are
intermediate visits documented?

**Questionnaire Number:** **9-digit in PAPI vs 12-digit in CAPI** — flagged as inconsistent. (The
12-digit key is the deliberate cross-instrument design — see [[Questionnaire Numbering Convention]].)

**Geographic identification:** the geo section looks incomplete — only Classification + Barangay
visible, Region/Province/City and lat-long "not observed"; wants a **cascading geo selection**
(Region → Province/HUC → City/Municipality → Barangay) to narrow the barangay list and reduce
mis-selection; asks the status of the previously-promised **geocodes** and how GPS lat/long is
captured/recorded/validated. (See [[PSGC Value Sets]] — CAPI does gate the 12-digit key through a
PSGC cascade; GPS is captured at end-of-flow, [[GPS and Photo Capture]].)

**Presentation:** question text appears **displayed twice**; section titles/intros missing or out of
order (~16 sampled screens); recommends showing question text once and keeping PAPI section
titles/instructions in sequence.

**Automate enumerator notes (the recurring theme):** manual notes that should be system logic are
still on screen — Q1 "Ask all questions… unless a skip rule applies", Q15 external-list note + open
text (suggest dropdown), Q18 income-bracket note ("tick"→"select", derive bracket from amount,
dropdown not shown), Q45.1/45.2/78/117/118 filter phrasing embedded in question text, Q57/Q69–73
address-based eligibility. Contextualize retained notes for CAPI; some "Select all that apply" notes
missing.

**Validation checks to watch:** exclusive-option blocking (can't pick None/RA/NA/DK alongside a real
option or "Other"); prevent simultaneous exclusive selections; catch single-answer items that allow
multi and vice versa. **Travel-duration limit:** Year-1 SurveyCTO capped 1440 min; Year-2 should allow
>1 day for GIDA households.

**Other (specify) missing "specify" field** — a long item list (Q5, 10, 11, 17, 23, 38, 45.2, 46,
52–53, 55–56, 58–59, 61, 65–66, 70–71, 74, 77–80, 82, 85, 88, 91–94, 101–103, 106–107, 109–111, 113,
121, 127–128, 133–134, 137, 141, 143, 194, 199).

**Item-level:** Q11 option order; Q22 wording (house vs household); Q29 no Refuse option; Q103 missing
"No, I haven't accessed any form of medical care"; Q199 amount range not shown.

**Household roster (Q30–Q50):** clarify the member-level loop workflow and member-linkage controls;
only Q48 seems to show the member name/roster line — is a member identifier shown throughout?
Auto-populate already-collected respondent info in the roster. (CAPI F4 uses the `C_HOUSEHOLD_ROSTER`
repeating record — see [[Source - Annex F4 Household Survey Questionnaire]]; the Section-N amount
matrix was also rebuilt as a block-as-roster pilot.)

**Q67 travel time:** HH:MM split into separate Hours/Minutes — combine into one duration? repeated
question text. **Household Expenditure:** heavy item/question-text repetition — group per item.
**Q186–Q194:** section intro/overarching question not observed — items read as standalone Yes/No.

## Cross-references

- Same reviewer + posture: [[Source - DOH June Questionnaire Comments (PARKED) 2026-06-19]]
- Companion instrument review: [[Source - PAPI vs CAPI HCW Review (XJ 2026-07)]]
- Shared review criteria across both: [[PAPI-to-CAPI Translation Review Criteria]]
- Build-status mapping (interpretation): [[Analysis - XJ PAPI-vs-CAPI Reviews vs Current CAPI Build]]
- Instrument baseline: [[Source - Annex F4 Household Survey Questionnaire]]
- Timeline/posture context: [[Source - Project Movement and Revised Timeline (Apr-Jun 2026)]]
