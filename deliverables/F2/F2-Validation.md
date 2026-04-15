---
title: F2 Validation Inventory — Self-Administered
instrument: F2
version: draft-2026-04-15
depends_on: deliverables/F2/F2-Spec.md
target_platform: Google Forms
author: Carl Reyes
status: draft-for-review
---

# F2 Validation Inventory — Self-Administered

Per-question validation rules for the F2 Google Forms build. **Self-admin has no "interviewer override"** pattern — if the form rejects an answer, the respondent is stuck. Rules below are therefore deliberately loose at the field level and push most consistency checks into **POST** processing (`F2-Cross-Field.md`).

## Legend

| Field | Meaning |
|---|---|
| `item` | F2-Spec item code (`Q1`…`Q114`) |
| `req` | `Y` required · `N` optional · `C` conditional (required if prior-answer gate) |
| `gf_type` | Google Forms field type: `short-text` · `long-text` · `number` · `date` · `single` · `multi` · `grid-single` · `scale-1-5` |
| `rule` | Form-side validator (Forms native or regex) |
| `on_fail` | Error message shown to respondent |
| `post` | POST-processing check that runs on the response Sheet |

## Global conventions

- **Every question is skippable by default** (per cover-block rewrite Decision on Q1 information block) EXCEPT consent, facility-type confirm, role bucket confirm, and Q5 role. Those four are hard-required because downstream routing depends on them.
- **Numeric fields** use Forms' built-in "Number · Between" validator with generous ranges. A too-tight range on self-admin blocks submission — prefer loose + POST flag.
- **Regex on short-text** only where a structured value is expected (none in F2 body — no phone, no email beyond Google sign-in auto-capture).
- **"Other, specify" follow-ups** are standalone short-text fields triggered by the parent single/multi-select. Required only when parent = "Other".
- **Consent (Block 5)** is the single hard gate. Declining routes to thank-you; everything else is optional.

---

## Pre-survey fields (hidden / pre-filled from URL)

| item | source | rule | on_fail |
|---|---|---|---|
| `facility_id` | URL param (read-only display) | must match master-list ID | route to error page "invalid link — contact ASPSI" |
| `facility_type` | URL param → re-confirmed as visible single Q | one of `DOH-retained hospital` · `Public hospital (non-DOH-retained)` · `Private facility` · `RHU / Health center` · `Other public facility` | drop to default `Other public facility` + POST flag |
| `facility_has_bucas` | URL param → visible single Q | `Yes` · `No` | default `No` + POST flag |
| `facility_has_gamot` | URL param → visible single Q | `Yes` · `No` | default `No` + POST flag |
| `response_source` | URL param (hidden) | `self` · `staff_encoded` · `paper_mirror` | default `self` |

---

## Section A — Healthcare Worker Profile

| item | req | gf_type | rule | on_fail |
|---|---|---|---|---|
| Q1.last_name | N | short-text | max 50 chars | "Please keep under 50 characters" |
| Q1.first_name | N | short-text | max 50 chars | same |
| Q1.middle_initial | N | short-text | max 5 chars | same |
| Q2 | N | single | — | — |
| Q2.other_specify | C | short-text | required if Q2 = Other | "Please specify your employment type" |
| Q3 | N | single | — | — |
| **Q4** | N | **number** | integer · between 18 and 80 | "Please enter your age between 18 and 80" |
| **Q5** | **Y** | **single** | required | "Please select your role to continue" |
| Q5.other_specify | C | short-text | required if Q5 = Other | "Please specify your role" |
| Q6 | N | single | — | — |
| Q6.other_specify | C | short-text | required if Q6 = Others | — |
| Q7 | N | single | — | — |
| Q8 | C | single | shown only if Q7=Yes AND facility_type ∈ public-ish | — |
| Q9.years | N | number | integer · between 0 and 60 | "Enter years between 0 and 60" |
| Q9.months | N | number | integer · between 0 and 11 | "Enter months between 0 and 11" |
| Q10 | N | number | integer · between 1 and 7 | "Enter days per week between 1 and 7" |
| Q11 | N | number | integer · between 1 and 24 | "Enter hours per day between 1 and 24" |

**POST flags:** tenure vs age plausibility (Q9 years > Q4 − 15), full-time/part-time derivation from Q11, Q6 specialty set when Q5 ∉ doctor/dentist.

---

## Section B — UHC Awareness

| item | req | gf_type | rule |
|---|---|---|---|
| Q12 | N | single | — |
| Q13–Q20 | N | single + specify | "other, specify" short-text when "Yes, specify other reason" / "No, specify other reason" chosen |
| Q14 (equipment list) | C | long-text | shown only if Q13 = any Yes variant |
| Q16 (supplies list) | C | long-text | shown only if Q15 = any Yes variant |
| Q21 | N | multi + specify | Forms cannot require "at least 1" on multi-select — leave optional |
| Q21.other_specify | C | short-text | required if Q21 includes Other |
| Q22–Q26 | N | grid-single | 5 rows, 3 columns (Higher/Lower × I don't know variants per row) |

**POST flags:** none.

---

## Section C — YAKAP/Konsulta (role-gated BUCKET-CD)

| item | req | gf_type | rule |
|---|---|---|---|
| Q27 | N | single | — |
| Q28 | N | multi | — |
| Q29 | N | single | — |
| Q30 | N | single + specify | — |
| Q31 | C | date | shown only if Q30 = Yes; no range constraint |
| Q32 | C | single + specify | shown only if Q30 = Yes |
| Q32.other_specify | C | short-text | required if Q32 = Other |
| Q33 | C | multi + specify | shown only if Q30 = No |
| Q34 | N | single | — |
| Q35 | C | multi + specify | shown only if Q34 = Yes |
| Q36 | N | long-text | max 1000 chars |

---

## Section D — NBB/ZBB Awareness

| item | req | gf_type | rule |
|---|---|---|---|
| Q37 | N | single | — |
| Q38 | C | multi + specify | shown only if Q37 = Yes |
| Q39 | C | multi + specify | shown only if Q37 = Yes |
| Q40 | N | single | — |
| Q41 | C | multi + specify | shown only if Q40 = Yes |
| Q42 | C | multi + specify | shown only if Q40 = Yes |

---

## Section E1 — BUCAS (double-gated)

| item | req | gf_type | rule |
|---|---|---|---|
| Q43 | N | single | shown only if `facility_has_bucas=Yes` AND role ∈ BUCKET-CD |
| Q44 | C | single | shown only if Q43 = Yes |
| Q45 | C | multi + specify | shown only if Q44 = Yes |

---

## Section E2 — GAMOT (double-gated)

| item | req | gf_type | rule |
|---|---|---|---|
| Q46 | N | single | shown only if `facility_has_gamot=Yes` AND role ∈ BUCKET-CD ∪ BUCKET-PHARM |
| Q47 | C | single | shown only if Q46 = Yes |
| Q48 | C | multi + specify | shown only if Q47 = Yes |

---

## Section F — Referrals

| item | req | gf_type | rule |
|---|---|---|---|
| Q49 | N | multi + specify | — |
| Q50 | N | single + specify | — |
| Q51 | N | single | — |
| Q52 | N | single | — |
| Q53 | N | multi + specify | — |
| Q54 | N | single | — |
| Q55 | C | multi + specify | shown only if Q54 ∈ {Dissatisfied, Very Dissatisfied} |

---

## Section G — KAP on Fees (physician/dentist only, facility-type-split)

| item | req | gf_type | rule |
|---|---|---|---|
| Q56 | N | single | — |
| Q57 | C | single | shown only if Q56 = Yes |
| Q58 | C | long-text | shown only if Q57 = No |
| Q59 | N | single | — |
| Q60 | C | single | shown only if Q59 = Yes |
| Q61 | C | long-text | shown only if Q60 = No |
| Q62 (ZBB) | C | single | shown only if facility_type = DOH-retained |
| Q62.1 (NBB) | C | single | shown only if facility_type ∈ {DOH-retained, Public non-DOH-retained} |
| Q63 | C | long-text | shown only if Q62=Yes OR Q62.1=Yes |
| Q64 | N | single | — |
| Q65 | C | long-text | shown only if Q64 = No |
| Q66 | N | long-text | — |
| Q67 (ZBB scale) | C | scale-1-5 | shown only if facility_type = DOH-retained |
| Q67.1 (NBB scale) | C | scale-1-5 | shown only if facility_type ∈ {DOH-retained, Public non-DOH-retained} |
| Q68–Q72 | N | scale-1-5 | 5 standalone 1-5 single-choice questions (**not** a grid — Forms grids don't support section routing mid-grid) |
| Q73 | N | long-text | max 1000 chars |
| Q74–Q76 | N | grid-single | 3 rows × 5 columns (Never/Rarely/Sometimes/Often/Always) |
| Q77 | N | long-text | max 1000 chars |
| Q78 (ZBB) | C | single | shown only if facility_type = DOH-retained |
| Q78.1 (NBB) | C | single | shown only if facility_type ∈ {DOH-retained, Public non-DOH-retained} |
| Q79 | C | long-text | shown only if Q78=Yes OR Q78.1=Yes |
| Q80 | N | long-text | max 1000 chars |

**POST flags:** Q55 answered by non-doctor/dentist (drop), Q62/Q62.1 dual-answer from DOH-retained, Q67/Q67.1 variance.

---

## Section H — Task Sharing

| item | req | gf_type | rule |
|---|---|---|---|
| Q81 | N | single | — |
| Q82 | N | single + specify | — |
| Q83 | N | multi + specify | — |
| Q84 | N | single + specify | — |
| Q85 | N | single | — |

---

## Section I — Facility Support

| item | req | gf_type | rule |
|---|---|---|---|
| Q86 | N | single | — |
| Q87 | C | multi + specify | shown only if Q86 = No |

---

## Section J — Job Satisfaction

| item | req | gf_type | rule |
|---|---|---|---|
| Q88–Q97 | N | grid-single | 10 rows × 5 cols (Strongly Agree … Strongly Disagree) |
| Q98 | N | long-text | — |
| Q99 | N | multi + specify | — |
| Q100 | N | multi + specify | — |
| Q101 | N | multi | — |
| Q102 | N | multi + specify | — |
| **Q103** | N | **single** | **lifted out of Q103–Q110 grid** (per F2-Skip-Logic open item #3) — standalone single-choice so Q111 skip-if-Never can work |
| Q104–Q110 | N | grid-single | 7 rows × 5 cols (Always … Never) |
| Q111 | C | single | shown only if Q103 ≠ Never |
| **Q112** | **Y** | **single** | required — terminal branch driver |
| Q113 | C | multi + specify | shown only if Q112 ∈ {any Yes} |
| Q114 | C | multi + specify | shown only if Q112 ∈ {any Yes} |

---

## Hard-required questions (summary)

Four and only four questions hard-block submission:

1. **Consent confirmation** (Block 5, cover) — routes to thank-you if declined
2. **Facility type re-confirm** (pre-survey, drives SPLIT routing)
3. **Q5 role** (drives role-bucket routing)
4. **Q112 leaving** (drives terminal branch)

Everything else is optional at the field level. This is a deliberate anti-drop-off choice for a 114-item self-admin survey.

## Decisions baked in (flagged to ASPSI via F2-0 memo)

- Completion-time placeholder `[X minutes]` — will be filled from desk-test results.
- Raffle still applies — wording retained verbatim from PDF.
- "Skip any question" acceptable except the four above.
- Q1 name fields kept as optional (raffle eligibility) — remove if SJREB requires anonymization.

## What lives in `F2-Cross-Field.md` instead

Anything that requires looking at >1 field simultaneously:
- Tenure × age plausibility
- Q5 role × Q6 specialty consistency
- Q54 × role × Q55 audience filter
- Q62/Q62.1 and Q67/Q67.1 and Q78/Q78.1 dual-variant reconciliation
- Disposition derivation from timestamps + consent
- `response_source` × submitter identity consistency
- Q11 full-time/part-time derivation
