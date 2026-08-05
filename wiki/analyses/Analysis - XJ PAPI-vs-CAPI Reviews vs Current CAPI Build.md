---
type: analysis
date_created: 2026-07-20
tags: [capi, survey-design, papi-vs-capi, doh-comments, parked-decision, interpretation]
---

# Analysis - XJ PAPI-vs-CAPI Reviews vs Current CAPI Build

> [!note] Interpretation, not an action list
> This page maps [[Xylee Javier (XJ)|XJ]]'s 2026-07 reviews
> ([[Source - PAPI vs CAPI Household Review (XJ 2026-07)|HH]] +
> [[Source - PAPI vs CAPI HCW Review (XJ 2026-07)|HCW]]) against what the current instruments do. It
> exists to make the **eventual consolidated DOH response** easy to assemble — **not** to reopen
> build work. The governing decision is unchanged: the comments are **PARKED**
> ([[Source - DOH June Questionnaire Comments (PARKED) 2026-06-19]]); Carl builds to the April-20
> baseline and answers only what resurfaces in SJREB/PSA/pre-testing. Per-item build claims below are
> **from project memory + the wiki**, not re-verified against code line-by-line — confirm before
> quoting any in a formal reply.

## The reframe

XJ reviewed **April screenshots without test-environment access**. So the comments sort into four
buckets, and only the last is potential work:

| Bucket | Meaning | Typical response |
|---|---|---|
| **A — Already built** | Feature exists in the live instrument; the April screenshot didn't show it | "Implemented; current screen attached" |
| **B — Deliberate design** | A real difference from PAPI, chosen on purpose | Document the rationale |
| **C — Evidence gap** | Real feature, unverifiable from screenshots | Supply a **skip/validation matrix + test login** |
| **D — Candidate change** | A genuine gap or improvement worth considering | ASPSI/DOH decide post-pretest |

The single highest-leverage action is **C**: one skip-pattern-matrix + programming-spec + test
account answers the recurring "no test access" ask across both instruments and most of the
"confirm the skip/validation is programmed" items.

## Bucket A — already built (screenshot lag)

- **Consent Form / per-case consent** — F2 shipped a per-case Consent gate (R6 #808); F1/F3/F4 carry
  consent/break-off handling. (see [[F2 Admin Portal]]; the case-start break-off → closing
  Result-of-Visit + off-form disposition pattern is documented in project reference notes)
- **Autosave + resume from last save** — F2 has IndexedDB autosave + resume in production; CSEntry
  partial-save resumes a case.
- **GPS lat/long capture** — captured (moved to end-of-flow, warm-radio); accuracy recorded.
  ([[GPS and Photo Capture]]; GPS moved to end-of-flow with a warm-radio read, 2026-07-16/19)
- **PSGC cascade** — the 12-digit key is geo-validated through Region → … → Barangay at field 1.
  ([[PSGC Value Sets]], [[Questionnaire Numbering Convention]]) XJ's "geo fields not observed" is a screenshot
  gap, though the *household-address* presentation (F4) is worth a current screenshot in the reply.
- **Exclusive-option blocking / checkbox integrity** — shipped as #830 (ascending-order + exclusivity)
  and F4 #832/#833 (checkbox-conversion ascending-order + exclusivity rules; the multi-select
  conversion is a shared generator path across F1/F3/F4).
- **Employment-type definitions (F2 Q2)** — surfaced via the #826 "\n"-rendered definitions.
- **Roster member identifier (F4 Q30–Q50)** — the household roster is a repeating record;
  member-name display was addressed in the roster rebuild (Section-N block-as-roster pilot).
  ([[Source - Annex F4 Household Survey Questionnaire]])
- **Navigation** — CSEntry provides built-in Next/Back/Go-To; the F2 PWA has section navigation.

## Bucket B — deliberate design (document the rationale)

- **12-digit QN vs 9-digit PAPI** — intentional cross-instrument respondent key (facility-9 +
  sequence-3), not an inconsistency. ([[Questionnaire Numbering Convention]])
- **Disposition "Withdraw Participation/Consent"** and its code set/order — a deliberate replacement;
  the response should state the rationale and the cross-instrument harmonization intent.
- **Visit-date YYYYMMDD** and **first/final-visit** recording model — a design choice; the reply
  should explain how callbacks map to the CAPI break-off/disposition model.
- **F2 is a different platform (PWA) than F1/F3/F4 (CSPro)** — by design; XJ actually rates the PWA the
  *better* interface. The rationale (self-administered, online/offline) is documentable.
- **Skip/filter instructions removed from the screen** — this is correct CAPI practice; XJ agrees
  ("no need for visible notes on skip rules, as long as… implemented accurately").

## Bucket C — evidence gaps (answer with a matrix + test access)

- "No access to the CAPI test environment" (both docs) → provide a **test login** + the deployed
  build.
- "Confirm skip patterns / applicability rules are programmed per PAPI" → a **skip-pattern matrix**
  keyed to question numbers (the project's `verify_questions.py` reachability output is a starting
  point).
- "Validation checks not demonstrated" → a **validation matrix** (range/consistency/required/
  exclusivity) per item.
- F2 "missing sections" (QN, ICF, Field Control, geo) and F2 Q6 "no screenshot" → current screenshots.

## Bucket D — candidate changes (ASPSI/DOH call, post-pretest)

Genuine gaps/improvements to weigh only if they resurface in review/pre-test — not build work now:

- **Other (specify) "specify" field** — both docs list dozens of items. Some already have `_OTHER_TXT`
  via the checkbox conversion; a per-item audit against the current DCFs would confirm which (if any)
  are truly missing. *This is the most concrete potential-work item and worth a targeted check before
  the response, but still gated by the parked decision.*
- **Cascading geo for F4 household address** — if the household-address field is a single entry rather
  than a cascade, that's a real UX/quality item.
- **Presentation** — repeated question text + missing section titles/intros on the CSPro instruments
  (F4 especially); grouping the Household Expenditure block and Q67 Hours/Minutes; input labels/units;
  red-asterisk legend; Q35-style date hints applied consistently.
- **Content** — Q103 missing option, Q29 Refuse option, Q11 option order, Q22 wording, Q199 range,
  Q18 income-bracket dropdown + auto-derivation, travel-duration >1-day limit, E1/E2 sub-headers,
  Q61/62/63 possible typo, Q98/Q113 missing instructions.

## Net

The reviews are **thorough and mostly answerable without rework** — a large share is Bucket A/B/C
(document + demonstrate), with a smaller Bucket-D tail that is ASPSI/DOH's to prioritize after
pre-testing. The parked posture holds; this page is the scaffolding for the single consolidated reply
when that time comes.

## Tracked as GitHub issues (2026-07-20)

Triaged one ticket per finding/question (parked; `from-doh-review-xj-2026-07` label): **149 child
issues** (#851–#999) under two tracking epics — **#849 (F2 HCW, 63)** and **#850 (F4 Household, 86)**.
Each ticket carries XJ's comment + the disposition bucket above + a one-line current-build status.
F1/F3 will get the same treatment when their XJ review docs are shared. The bucket-C "supply a
skip/validation matrix + test login" remains the single highest-leverage action across the set.

## Scheduled — post-pretest remediation (2026-07-20)

Carl scheduled the remediation for **after pretesting**: both epics are assigned to GitHub milestone **#7 "Post-pretest — DOH/XJ review remediation"** (due ~2026-07-31, ahead of D5/August training). The instruments stay **frozen through the pretest**; the pass executes the moment fieldwork ends, in order — (1) promote any finding that surfaced in the field from *candidate* → *confirmed*, (2) ship the bucket-C skip/validation matrix + test login, (3) decide + build the ~27 bucket-D candidates, (4) run the other-specify DCF audit, (5) assemble the consolidated DOH response. Progress-report deliverable: `deliverables/DOH-Reviews/2026-07-20_DOH-XJ-Review_Triage-Progress-Report.{html,pdf}` (formatted like the PCA-ARC briefs; carries the item table + triage + this schedule). This is consistent with the park decision — pretest is the gate Dr. Myra named ([[Source - DOH June Questionnaire Comments (PARKED) 2026-06-19]]).

## Related

- [[PAPI-to-CAPI Translation Review Criteria]] — the rubric these comments apply
- [[Source - PAPI vs CAPI Household Review (XJ 2026-07)]] · [[Source - PAPI vs CAPI HCW Review (XJ 2026-07)]]
- [[Source - DOH June Questionnaire Comments (PARKED) 2026-06-19]] · [[Source - Project Movement and Revised Timeline (Apr-Jun 2026)]]
