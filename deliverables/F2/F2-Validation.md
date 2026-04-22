---
title: F2 Validation Inventory — Self-Administered
instrument: F2
version: draft-2026-04-21-apr20
depends_on: deliverables/F2/F2-Spec.md (Apr 20 rev)
supersedes: draft-2026-04-15 (April 8 PDF)
target_platform: Google Forms
author: Carl Reyes
status: draft-for-review-apr20
---

# F2 Validation Inventory — Self-Administered

Per-question validation rules for the F2 Google Forms build. **Self-admin has no "interviewer override"** pattern — if the form rejects an answer, the respondent is stuck. Rules below are therefore deliberately loose at the field level and push most consistency checks into **POST** processing (`F2-Cross-Field.md`).

Sourced from the **April 20, 2026 PDF** (124 actual items, numbered Q1–Q125 with Q108 as a PDF numbering gap). Supersedes the April 8 PDF (114 items) draft.

## Legend

| Field | Meaning |
|---|---|
| `item` | F2-Spec item code (Apr 20: Q1…Q125, Q108 omitted) |
| `req` | `Y` required · `N` optional · `C` conditional (required if prior-answer gate) |
| `gf_type` | Google Forms field type: `short-text` · `long-text` · `number` · `date` · `single` · `multi` · `grid-single` · `scale-1-5` |
| `rule` | Form-side validator (Forms native or regex) |
| `on_fail` | Error message shown to respondent |
| `post` | POST-processing check that runs on the response Sheet |

## Global conventions

- **Every question is skippable by default** (per cover-block Decision on Q1 information block) EXCEPT consent, facility-type confirm, role bucket confirm, and Q5 role. Those four are hard-required because downstream routing depends on them.
- **Numeric fields** use Forms' built-in "Number · Between" validator with generous ranges. A too-tight range on self-admin blocks submission — prefer loose + POST flag.
- **Regex on short-text** only where a structured value is expected (none in F2 body — no phone, no email beyond Google sign-in auto-capture).
- **"Other, specify" follow-ups** are standalone short-text fields triggered by the parent single/multi-select. Required only when parent = "Other".
- **Consent (Block 5)** is the single hard gate. Declining routes to thank-you; everything else is optional.
- **Q108 gap** — Apr 20 PDF skips Q108 (editorial artifact). Builder must *not* emit a Q108 field. Flagged to ASPSI for confirmation.

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

## Section A — Healthcare Worker Profile (Q1–Q11)

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

## Section B — UHC Awareness (Q12–Q30)

Apr 20 expanded the implementation battery by **4 new items** (Q21–Q24) — DOH licensing, PhilHealth accreditation, service delivery protocols, primary-care quality measures. Q25 adds a multi-select filter in front of the expect-change sub-battery Q26–Q30.

| item | req | gf_type | rule |
|---|---|---|---|
| Q12 | N | single | — (drives SEC-B1 gate) |
| Q13–Q20 | N | single + specify | "UHC-impl set" 8-option choice set; "Yes, specify other reason" / "No, specify other reason" triggers short-text |
| Q14 (equipment list) | C | long-text | shown only if Q13 = any Yes variant |
| Q16 (supplies list) | C | long-text | shown only if Q15 = any Yes variant |
| **Q21–Q24** | N | single + specify | **NEW in Apr 20** — same "UHC-impl set" choice set as Q13–Q20 |
| Q25 | N | multi + specify | filter — "which of the following do you expect to change"; Forms cannot require "at least 1" on multi-select — leave optional |
| Q25.other_specify | C | short-text | required if Q25 includes Other |
| Q26–Q30 | N | grid-single | 5 rows (access, financial risk, quality, responsiveness, equity) × 3 cols (Higher/Lower/I don't know) — always shown (see POST flag on Q25 integrity) |

**POST flags:** Q25 integrity — if Q25 includes a given domain but Q26–Q30 answer is blank/"I don't know", flag for review (forms cannot gate grid rows on multi-select).

---

## Section C — YAKAP/Konsulta (role-gated BUCKET-CD) (Q31–Q40)

| item | req | gf_type | rule |
|---|---|---|---|
| Q31 | N | single | — (drives SEC-C1 gate) |
| Q32 | N | multi | — |
| Q33 | N | single | — |
| Q34 | N | single + specify | — (drives SEC-C3 accreditation gate) |
| Q35 | C | date | shown only if Q34 = Yes; no range constraint |
| Q36 | C | single + specify | shown only if Q34 = Yes; all answers route to SEC-D1 (skip C-tail — Apr 20 skip-logic fix) |
| Q36.other_specify | C | short-text | required if Q36 = Other |
| Q37 | C | multi + specify | shown only if Q34 = No / Don't know / Other |
| Q38 | N | single | — (drives SEC-C6 consider gate) |
| Q39 | C | multi + specify | shown only if Q38 = Yes |
| Q40 | N | long-text | max 1000 chars — shown only if Q38 = No |

---

## Section D — NBB/ZBB Awareness (Q41–Q47)

Apr 20 adds **Q47** (ZBB challenges multi-select) at the tail of the ZBB branch.

| item | req | gf_type | rule |
|---|---|---|---|
| Q41 | N | single | — (drives SEC-D1 gate) |
| Q42 | C | multi + specify | shown only if Q41 = Yes |
| Q43 | C | multi + specify | shown only if Q41 = Yes |
| Q44 | N | single | — (drives SEC-D3 gate) |
| Q45 | C | multi + specify | shown only if Q44 = Yes |
| Q46 | C | multi + specify | shown only if Q44 = Yes |
| **Q47** | C | **multi + specify** | **NEW in Apr 20** — ZBB challenges; shown only if Q44 = Yes |

---

## Section E1 — BUCAS (double-gated) (Q48–Q52)

Apr 20 adds **Q50** (BUCAS utilization factors) and **Q51** (BUCAS efficacy opinion) inside the post-Q49 sub-branch.

| item | req | gf_type | rule |
|---|---|---|---|
| Q48 | N | single | shown only if `facility_has_bucas=Yes` AND role ∈ BUCKET-CD |
| Q49 | C | single | shown only if Q48 = Yes |
| **Q50** | C | **multi + specify** | **NEW in Apr 20** — BUCAS utilization factors; shown only if Q49 = Yes |
| **Q51** | C | **scale-1-5** | **NEW in Apr 20** — BUCAS efficacy opinion (Not at all effective … Very effective); shown only if Q49 = Yes |
| Q52 | C | multi + specify | shown only if Q49 = Yes |

---

## Section E2 — GAMOT (double-gated) (Q53–Q55)

| item | req | gf_type | rule |
|---|---|---|---|
| Q53 | N | single | shown only if `facility_has_gamot=Yes` AND role ∈ BUCKET-CD ∪ BUCKET-PHARM |
| Q54 | C | single | shown only if Q53 = Yes |
| Q55 | C | multi + specify | shown only if Q54 = Yes |

---

## Section F — Referrals (Q56–Q62)

| item | req | gf_type | rule |
|---|---|---|---|
| Q56 | N | multi + specify | — |
| Q57 | N | single + specify | — |
| Q58 | N | single | — |
| Q59 | N | single | — |
| Q60 | N | multi + specify | — |
| Q61 | N | single | — (drives SEC-F2 gate) |
| Q62 | C | multi + specify | shown only if Q61 ∈ {Dissatisfied, Very Dissatisfied} |

---

## Section G — KAP on Fees (physician/dentist only, facility-type-split) (Q63–Q90)

Apr 20 adds **three** NBB siblings to existing ZBB-only items: **Q70** (NBB implications, paired with Q69 ZBB), **Q76** (NBB fairness scale, paired with Q75 ZBB), **Q88** (NBB balance billing gate, paired with Q87 ZBB).

Visibility matrix for the ZBB/NBB triples:

| ZBB item | NBB sibling | Visible for DOH-retained? | Visible for Public non-DOH? | Visible for other? |
|---|---|---|---|---|
| Q69 | Q70 | both | Q70 only | neither |
| Q75 | Q76 | both | Q76 only | neither |
| Q87 | Q88 | both | Q88 only | neither |

| item | req | gf_type | rule |
|---|---|---|---|
| Q63 | N | single | — (drives SEC-G1 gate) |
| Q64 | C | single | shown only if Q63 = Yes |
| Q65 | C | long-text | shown only if Q64 = No |
| Q66 | N | single | — (drives SEC-G2 gate) |
| Q67 | C | single | shown only if Q66 = Yes |
| Q68 | C | long-text | shown only if Q67 = No |
| Q69 (ZBB) | C | single | shown only if facility_type = DOH-retained |
| **Q70 (NBB)** | C | **single** | **NEW in Apr 20** — shown only if facility_type ∈ {DOH-retained, Public non-DOH-retained} |
| Q71 | C | long-text | shown only if Q69=Yes OR Q70=Yes |
| Q72 | N | single | — (drives SEC-G-Q72 gate) |
| Q73 | C | long-text | shown only if Q72 = No |
| Q74 | N | long-text | — |
| Q75 (ZBB scale) | C | scale-1-5 | shown only if facility_type = DOH-retained |
| **Q76 (NBB scale)** | C | **scale-1-5** | **NEW in Apr 20** — shown only if facility_type ∈ {DOH-retained, Public non-DOH-retained} |
| Q77–Q81 | N | scale-1-5 | 5 standalone 1-5 single-choice questions (**not** a grid — Forms grids don't support section routing mid-grid) |
| Q82 | N | long-text | max 1000 chars |
| Q83–Q85 | N | grid-single | 3 rows × 5 columns (Never/Rarely/Sometimes/Often/Always) |
| Q86 | N | long-text | max 1000 chars |
| Q87 (ZBB) | C | single | shown only if facility_type = DOH-retained |
| **Q88 (NBB)** | C | **single** | **NEW in Apr 20** — shown only if facility_type ∈ {DOH-retained, Public non-DOH-retained} |
| Q89 | C | multi + specify | shown only if Q87=Yes OR Q88=Yes |
| Q90 | N | long-text | max 1000 chars |

**POST flags:** Q62 answered by non-doctor/dentist (drop), Q69/Q70 dual-answer from DOH-retained, Q75/Q76 variance, Q87/Q88 dual-answer from DOH-retained.

---

## Section H — Task Sharing (Q91–Q95)

| item | req | gf_type | rule |
|---|---|---|---|
| Q91 | N | single | — |
| Q92 | N | single + specify | — |
| Q93 | N | multi + specify | — |
| Q94 | N | single + specify | — |
| Q95 | N | single | — |

---

## Section I — Facility Support (Q96–Q97)

| item | req | gf_type | rule |
|---|---|---|---|
| Q96 | N | single | — (drives SEC-I1 gate) |
| Q97 | C | multi + specify | shown only if Q96 = No |

---

## Section J — Job Satisfaction (Q98–Q125, Q108 omitted)

> **Q108 is a PDF numbering gap** — no item exists at that slot in the Apr 20 PDF. The builder must skip from Q107 to Q109 without emitting a Q108 field. Flagged to ASPSI under open item #7.

| item | req | gf_type | rule |
|---|---|---|---|
| Q98–Q107 | N | grid-single | 10 rows × 5 cols (Strongly Agree … Strongly Disagree) |
| Q109 | N | long-text | — |
| Q110 | N | multi + specify | — |
| Q111 | N | multi + specify | — |
| Q112 | N | multi | — |
| Q113 | N | multi + specify | — |
| **Q114** | N | **single** | **lifted out of Q114–Q121 grid** (per F2-Skip-Logic open item #4) — standalone single-choice so Q122 skip-if-Never can work |
| Q115–Q121 | N | grid-single | 7 rows × 5 cols (Always … Never) |
| Q122 | C | single | shown only if Q114 ≠ Never |
| **Q123** | **Y** | **single** | required — terminal branch driver |
| Q124 | C | multi + specify | shown only if Q123 ∈ {any Yes} |
| Q125 | C | multi + specify | shown only if Q123 ∈ {any Yes} |

---

## Hard-required questions (summary)

Four and only four questions hard-block submission:

1. **Consent confirmation** (Block 5, cover) — routes to thank-you if declined
2. **Facility type re-confirm** (pre-survey, drives SPLIT routing)
3. **Q5 role** (drives role-bucket routing)
4. **Q123 leaving** (drives terminal branch)

Everything else is optional at the field level. This is a deliberate anti-drop-off choice for a 124-item self-admin survey.

## Decisions baked in (flagged to ASPSI via F2-0 memo)

- Completion-time placeholder `[X minutes]` — will be filled from desk-test results (Apr 20 may extend vs. Apr 08 given +10 items).
- Raffle still applies — wording retained verbatim from PDF.
- "Skip any question" acceptable except the four above.
- Q1 name fields kept as optional (raffle eligibility) — remove if SJREB requires anonymization.
- Q108 numbering gap — builder omits the slot; POST checks never read a Q108 column.

## New-item summary (Apr 08 → Apr 20 validation delta)

| Apr 20 item | Section | Type | Required? | Gate |
|---|---|---|---|---|
| Q21 | B | single + specify | N | — |
| Q22 | B | single + specify | N | — |
| Q23 | B | single + specify | N | — |
| Q24 | B | single + specify | N | — |
| Q47 | D | multi + specify | C | Q44 = Yes |
| Q50 | E1 | multi + specify | C | Q49 = Yes (+ facility_has_bucas + BUCKET-CD upstream) |
| Q51 | E1 | scale-1-5 | C | Q49 = Yes (+ facility_has_bucas + BUCKET-CD upstream) |
| Q70 | G | single | C | facility_type ∈ {DOH-retained, Public non-DOH} |
| Q76 | G | scale-1-5 | C | facility_type ∈ {DOH-retained, Public non-DOH} |
| Q88 | G | single | C | facility_type ∈ {DOH-retained, Public non-DOH} |

Ten new items total. All optional at the field level; all gated upstream. None are hard-required.

## What lives in `F2-Cross-Field.md` instead

Anything that requires looking at >1 field simultaneously:

- Tenure × age plausibility
- Q5 role × Q6 specialty consistency
- Q25 multi-select × Q26–Q30 grid-row integrity (Apr 20 new check)
- Q61 × role × Q62 audience filter
- Q69/Q70, Q75/Q76, Q87/Q88 ZBB/NBB dual-variant reconciliation (Apr 20 triple-pair check — was a single pair per section in Apr 08)
- Disposition derivation from timestamps + consent
- `response_source` × submitter identity consistency
- Q11 full-time/part-time derivation
- Q108 column-presence guard (must never appear in response Sheet)
