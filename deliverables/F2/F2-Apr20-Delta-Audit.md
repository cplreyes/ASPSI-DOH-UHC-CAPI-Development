---
title: F2 Apr 08 vs Apr 20 Delta Audit
instrument: F2
source_apr20: raw/Project-Deliverable-1_Apr20-submitted/Annex F2_Healthcare Worker Survey Questionnaire_UHC Year 2.pdf
source_apr08: raw/Project-Deliverable-1/Annex F2_Healthcare Worker Survey Questionnaire_UHC Year 2_April 08.pdf
date_created: 2026-04-21
status: phase-1-input-for-spec-rewrite
---

# F2 Apr 08 vs Apr 20 Delta Audit

Input for the F2 Apr 20 alignment work. Captures the per-section item counts, where the +11 items landed, and which gates / skip-logic shifts are implied.

## Item count by section

| Section | Topic | Apr 08 | Apr 20 | Δ | Apr 20 Q-range |
|---|---|---:|---:|---:|---|
| A | Healthcare Worker Profile | 11 | 11 | 0 | Q1–Q11 |
| B | UHC Awareness | 15 | 19 | **+4** | Q12–Q30 |
| C | YAKAP/Konsulta Package | 10 | 10 | 0 | Q31–Q40 |
| D | NBB and ZBB Awareness | 6 | 7 | **+1** | Q41–Q47 |
| E | Expanded Health Programs (BUCAS + GAMOT) | 6 | 8 | **+2** | Q48–Q55 |
| F | Outbound & Inbound Referrals and Satisfaction | 7 | 7 | 0 | Q56–Q62 |
| G | KAP on Professional Setting, Charging, and Reimbursement | 25 | 28 | **+3** | Q63–Q90 |
| H | Task Sharing | 5 | 5 | 0 | Q91–Q95 |
| I | Facility Support | 2 | 2 | 0 | Q96–Q97 |
| J | Job Satisfaction | 27 | 28 | **+1** | Q98–Q125 |
| | **TOTAL (numbered)** | **114** | **125** | **+11** | |
| | **TOTAL (actual items)** | **114** | **124** | **+10** | Apr 20 PDF omits Q108 — numbering jumps Q107 → Q109 in Section J (see "J. Job Satisfaction" below) |

## Where the +11 items landed

### B. UHC Awareness (+4) — four new UHC-implementation items

> **Correction (2026-04-21 revision):** an earlier draft of this audit attributed the +4 to an "expected change" matrix expansion. That was wrong — Apr 08 already had Q21 overview + Q22–Q26 per-domain expect-change items (6 items). The true +4 is **four new UHC-implementation items** inserted between Apr 08 Q20 and the expect-change battery.

Apr 20 adds four new `single + specify` items to the UHC-implementation battery (all use the same 8-option choice set as Apr 08 Q13, Q15, Q17, Q18, Q19, Q20):

- Apr 20 **Q21** — "Have the DOH licensing standards been implemented since the UHC Act was passed in 2019…" (**NEW**)
- Apr 20 **Q22** — "Have the PhilHealth accreditation requirements been implemented…" (**NEW**)
- Apr 20 **Q23** — "Have the service delivery protocols been implemented…" (**NEW**)
- Apr 20 **Q24** — "Have the primary care quality measures been implemented…" (**NEW**)

Apr 20 also **renames** Apr 08 Q20 "improved standards / quality guidelines" to "improved clinical practice guidelines" (same item, relabeled).

The expect-change battery is structurally unchanged — Apr 08 Q21 (overview) + Q22–Q26 (5 per-domain) maps 1:1 to Apr 20 Q25 (overview) + Q26–Q30 (5 per-domain), shifted by +4 from the new implementation inserts.

**Build impact:** 4 new UHC-implementation items to add to the spec, skip-logic graph, and validation inventory. Reporting queries that aggregated the Apr 08 implementation list must extend to include Q21–Q24 (DOH licensing, PhilHealth accreditation, service delivery protocols, primary care quality measures) per the Annex G licensing/accreditation track.

### D. NBB/ZBB Awareness (+1) — Q47 ZBB challenges

New: **Q47 "What challenges do you commonly encounter for patients covered by ZBB?"** (multi-select; no Apr 08 equivalent). Driven by [[Annex G Recommendations Matrix|Annex G #7]] — ZBB explicit coverage.

### E. Expanded Health Programs (+2) — BUCAS deeper dive

Apr 08 Section E was 6 items split into E1 BUCAS (Q43–Q45) and E2 GAMOT (Q46–Q48). Apr 20 Section E is 8 items (Q48–Q55) reorganized:

- **Q48** "Heard about BUCAS?" (was Apr 08 Q43)
- **Q49** "Do you have a BUCAS Center?" (was Apr 08 Q44)
- **Q50** "In your assessment, what are the main factors affecting the utilization of BUCAS in [this facility / this area]?" — **NEW**
- **Q51** "Do you feel BUCAS improves patient management efficiently?" — **NEW**
- **Q52** "In your opinion, BUCAS Centers have: [impact options]" (was Apr 08 Q45, reformatted)
- **Q53** "Heard about GAMOT?" (was Apr 08 Q46)
- **Q54** "Is your facility an accredited GAMOT provider?" (was Apr 08 Q47)
- **Q55** "In your assessment, what are the main factors affecting the utilization of the [GAMOT program]?" (was Apr 08 Q48, expanded label)

**Net additions:** Q50 (BUCAS utilization factors), Q51 (BUCAS efficacy opinion). Apr 08 Q48 GAMOT factors got re-phrased but is structurally the same as Apr 20 Q55.

### G. KAP on Professional Setting (+3) — NBB siblings to existing ZBB items

> **Confirmed (2026-04-21):** the +3 is **three new NBB-variant siblings** added to the existing ZBB-only items in Apr 08 Section G. Direct verbatim compare of the Apr 20 text pinned them exactly.

Apr 08 G: Q56–Q80 (25 items). Apr 20 G: Q63–Q90 (28 items).

Apr 08 had ZBB-only variants at Q62 (implications), Q67 (fee fairness 1–5 scale), and Q78 (balance billing experience). Apr 20 preserves each of those and **adds an NBB-variant sibling** immediately after each one:

- Apr 20 **Q70** — "Do you know the implications of the NBB policy for professional fee charging?" (**NEW**; NBB sibling to Q69 / Apr 08 Q62 ZBB)
- Apr 20 **Q76** — "On a scale of 1-5 with 5 as highest, how fair is your professional fee reimbursement compared to colleagues…who practice in facilities which are not NBB accredited?" (**NEW**; NBB sibling to Q75 / Apr 08 Q67 ZBB)
- Apr 20 **Q88** — "Have you experienced professional fee balance billing despite the insurance/NBB?" (**NEW**; NBB sibling to Q87 / Apr 08 Q78 ZBB)

**Build impact:** each new item carries a facility-type gate — NBB variants apply to "public hospitals, including those from DOH-retained hospitals" (DOH-retained respondents see **both** ZBB and NBB; public non-DOH see only NBB). This doubles the number of facility-type-gated splits in Section G from 3 (Apr 08: Q62, Q67, Q78) to 6 (Apr 20: Q69/Q70, Q75/Q76, Q87/Q88).

The `Q83–Q86 charge/waive/coping` battery (Apr 20) maps 1:1 to Apr 08 Q74–Q77 and is **not new** — the earlier draft of this audit misidentified these as the additions.

### J. Job Satisfaction — nominal +1, actual 0 (Q108 is a PDF numbering gap)

> **Confirmed (2026-04-21):** Apr 20 Section J **numbers** 28 slots (Q98–Q125) but **omits Q108** — the PDF jumps directly from Q107 to Q109. The actual item count is **27**, identical to Apr 08.

Apr 08 J: Q88–Q114 (27 items). Apr 20 J: Q98–Q125 numbered, 27 actual (Q108 absent).

Verbatim compare against the Apr 20 PDF:

- Apr 20 Q98–Q107 Grid #1 (agreement scale) → maps 1:1 to Apr 08 Q88–Q97 (10 items, unchanged)
- Apr 20 Q109–Q113 open/closed items → maps 1:1 to Apr 08 Q98–Q102 (5 items, unchanged)
- Apr 20 Q114–Q121 Grid #2 (frequency scale) → maps 1:1 to Apr 08 Q103–Q110 (8 items, unchanged; the burnout block)
- Apr 20 Q122 overtime frequency → Apr 08 Q111
- Apr 20 Q123 leaving consideration → Apr 08 Q112
- Apr 20 Q124 reason for leaving → Apr 08 Q113
- Apr 20 Q125 plans after leaving → Apr 08 Q114

**Net change in Section J content: zero.** The earlier Q99/Q100 split hypothesis was wrong — both Apr 08 (Q89/Q90) and Apr 20 (Q99/Q100) have the duplicated "All of my salary payments have arrived…" pair (Apr 20 adds "on time" vs "in the correct amount" suffixes; Apr 08 has the same two items with "on"/"in" fragments).

**Annex G #23 status:** the burnout block (Apr 20 Q116–Q121) was flagged for removal in Annex G but was retained in the Apr 20 submission. Decision gate for Dr. Claro pre-build remains open.

**Build impact:** the Q108 numbering gap must be preserved in the spec, skip-logic, validation, and Apps Script — there is no `Q108` anywhere. This is an editorial artifact of the Apr 20 PDF (an item was likely removed during revision without reflowing the numbers).

## Cross-cutting renumbering

Because the Apr 20 additions are front-loaded in Section B, every Q# from Section C onward is shifted:

| Apr 08 Q# range | Apr 20 Q# range | Offset |
|---|---|---|
| Q1–Q11 (A) | Q1–Q11 (A) | 0 |
| Q12–Q25 (B implementation list) | Q12–Q24 (B implementation list, Q25 now "which expect to change") | 0 to −1 |
| Q26 (B matrix) | Q25 + Q26–Q30 (split) | expanded to 5 |
| Q27–Q36 (C) | Q31–Q40 (C) | **+4** |
| Q37–Q42 (D) | Q41–Q47 (D) | **+4 to +5** |
| Q43–Q48 (E) | Q48–Q55 (E) | **+5 to +7** |
| Q49–Q55 (F) | Q56–Q62 (F) | **+7** |
| Q56–Q80 (G) | Q63–Q90 (G) | **+7 to +10** |
| Q81–Q85 (H) | Q91–Q95 (H) | **+10** |
| Q86–Q87 (I) | Q96–Q97 (I) | **+10** |
| Q88–Q114 (J) | Q98–Q125 (J) | **+10 to +11** |

## Section label updates (all driven by Annex G)

| Section | Apr 08 label | Apr 20 label |
|---|---|---|
| D | NBB and ZBB Awareness | Awareness on No Balance Billing (NBB) and Zero Balance Billing (ZBB) |
| E | Expanded Health Programs | Awareness on Expanded Health Programs (BUCAS and GAMOT) |
| G | KAP on Professional Setting, Charging, Reimbursement | Knowledge, Attitude, And Practices (KAP) on Professional Setting, Charging, And Reimbursement |

## Skip-logic impacts

Gates in Apr 08 F2-Skip-Logic.md referenced old Q#s. Known gates and their Apr 20 equivalents (+offset):

| Apr 08 gate | Apr 20 gate |
|---|---|
| Q7 Yes→Q8, No→Q9 (private practice filter) | **unchanged** — Q7/Q8/Q9 in Section A, not shifted |
| Role (Q5) gates Sections C/D/E1/E2/G | Q5 unchanged; gated sections shift to Apr 20 ranges |
| Q36 "since when" conditional on Q34=Yes | Q35 on Q34=Yes (**renumbered**) |
| Q43 BUCAS heard → Q44 | Q48 → Q49 |
| Q46 GAMOT heard → Q47 | Q53 → Q54 |
| Q114 overtime "Never" → skip Q122 | Q122 overtime → skip Q122 (or the actual overtime item — verify; the Apr 20 burnout block kept the same Q-range coincidentally) |
| Q123 "No" on leaving → end survey | **Q123 unchanged** — "Have you considered leaving this facility?" — No → END (skip Q124, Q125) |

## Downstream consumers requiring sync after F2-Spec.md rewrite

- `deliverables/F2/F2-Skip-Logic.md` — routing graph renumber
- `deliverables/F2/F2-Validation.md` — required-flag inventory renumber + new-item entries
- `deliverables/F2/F2-Cross-Field.md` — 20 POST rules; DISP-03 "114 items" reference
- `deliverables/F2/apps-script/Spec.gs` — hardcoded 114-item list
- `deliverables/F2/PWA/app/spec/F2-Spec.md` — shipped copy (mirror of root)
- `deliverables/F2/PWA/app/spec/README.md` — "114 items" reference
- `deliverables/F2/PWA/2026-04-17-design-spec.md` — §11.1 M6 row
- `deliverables/F2/PWA/2026-04-17-implementation-plan.md` — M6 row
- `deliverables/F2/PWA/2026-04-17-implementation-plan-M1-generator-plus-render.md` — 114 refs
- `deliverables/F2/PWA/2026-04-18-implementation-plan-M6-full-instrument.md` — 114 refs (multiple)
- `deliverables/F2/F2-Build-Handoff.md` — if it references the count
- `wiki/sources/Source - Annex F2 Healthcare Worker Survey Questionnaire.md` — "needs re-audit" line (retire)

## Notes

- Annex G #23 "reduce or remove burnout items" **not acted on** in Apr 20 — burnout block Q114–Q122 retained. Decision gate for Dr. Claro pre-build still open.
- Cover-block rewrite status unchanged — no longer a build gate per `feedback_f2_admin_model_self_admin_first.md` memory; the Apr 20 PDF still uses interviewer-style cover blocks, but the field-work model is self-admin-first.
- Verbatim-label rule applies to the rewrite: every Apr 20 label must match the PDF exactly (subject to CSPro 255-char trim for the CSPro encoder track, which is deferred anyway).
