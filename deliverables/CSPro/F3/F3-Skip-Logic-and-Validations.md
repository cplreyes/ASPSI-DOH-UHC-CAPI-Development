---
type: spec
project: ASPSI-DOH-CAPI-CSPro-Development
deliverable: F3 Patient Survey — CAPI logic spec
date_created: 2026-04-21
status: draft
source_questionnaire: raw/Project-Deliverable-1_Apr20-submitted/Annex F3_Patient Survey Questionnaire_UHC Year 2.pdf
source_dcf: deliverables/CSPro/F3/PatientSurvey.dcf
tags: [cspro, capi, skip-logic, validations, f3]
---

# F3 Patient Survey — Skip Logic and Validations Spec

Source-of-truth for CSPro CAPI logic on `PatientSurvey.dcf`. Covers:

1. **Sanity-check findings** — discrepancies between the Apr 20 questionnaire and the current dcf (15 records / 818 items).
2. **Skip-logic table** — every conditional jump extracted from the questionnaire.
3. **Cross-field validations** — HARD (block save), SOFT (warn-and-confirm), GATE (display-only conditional rendering).
4. **CSPro logic templates** — paste-ready snippets for common patterns (final chunk).

All Q-numbers refer to the **Apr 20 printed questionnaire** (1–178); dcf item names follow the `Q{n}_*` convention.

---

## 1. Sanity-check findings (dcf vs Apr 20 questionnaire)

### A. Items to flag for generator fix before CAPI build

| # | Item | Issue | Fix |
|---|---|---|---|
| 1 | **Q14 DISABILITY_TYPE** — card-gated only | Source makes Q14 an enumerator-only item ("DO NOT READ ALOUD... record the type as indicated on the card"). Must only be answered when Q13 = "Yes (card was presented and verified)"; other Q13 answers should leave Q14 blank. | Spec as GATE rule in §3; no dcf change. |
| 2 | **Q18 amount + bracket duality** | Source captures both a free-entry numeric ("Approximate amount") AND the ticked bracket. The dcf stores both (`Q18_INCOME_AMOUNT`, `Q18_INCOME_BRACKET`) — correct — but needs a hard consistency check: amount must fall in bracket. | Spec as HARD consistency rule in §3. |
| 3 | **Q31 IP_GROUP specify** | Source says "A list will be provided to ensure accurate details" but none is included in Annex F3 — dcf currently uses a free-text alpha. Confirm with ASPSI whether a coded IP list will ship; if not, retain alpha. | Flag for ASPSI; keep alpha as default. |
| 4 | **Q147 / Q156 medication lists** | Both captured as single `alpha(length=240)`. If field reports indicate patients routinely list >240 chars of meds, consider converting to a roster record. Not a blocker for bench test. | Monitor during pilot. |
| 5 | **Q150 travel time HH/MM** | Dcf splits into `Q150_TRAVEL_HH` + `Q150_TRAVEL_MM` (both length=2). Needs a joint-sanity rule: MM ∈ [0, 59], and (HH=0 ∧ MM=0) is allowed only if patient lives at pharmacy — warn. | Spec as HARD range + SOFT sanity in §3. |
| 6 | **Q169 skip-branch coverage** | Source shows Q169 options 2 ("No, not planning") and 3 ("Not yet, planning") both skip to Q171; option 1 ("Yes") proceeds to Q170 then Q172. Q171 also has `<Proceed to Q172>` printed next to the stem — means Q171 is entered only from Q169 ∈ {2,3}, and after Q171 always jumps to Q172 regardless of Q170 having been skipped. | Spec as skip-logic in §3 under Section L. |
| 7 | **Q159 "Not applicable" → Q164** | Q159 option 5 "Not applicable" routes to Q164 — but Q164 lives in Section L (referrals) and Q159 is in Section K (medicines). That jumps out of a section. Verify with ASPSI this is intentional and not a typo for Q162. | Flag for ASPSI; default: honor source as printed. |
| 8 | **Q162 No → End of survey** | Hard terminator. Must set `ENUM_RESULT` to "Completed" (or "Completed at Hospital/Home" per Field Control codes) and prevent Sections L-tail from being entered. Handle in CSPro PROC. | Spec in §3 under Section L. |

### B. Cosmetic / acceptable as-is

- Informed-consent block (respondent name/signature, witness name, address, tel) lives in the shared `FIELD_CONTROL` record via `build_field_control()` — no Section-A dcf duplicate needed.
- Q45 member-category labels carry the full verbatim DOH definitions (paragraph-length) — intentional per the verbatim-labels rule; renders correctly in CSEntry.
- Q23 `Dug well` has no own/share sub-question (only piped/faucet paths do) — matches source.
- The dcf includes several long select-all lists (Q148 20 options, Q164 23 options) — these render fine on tablets in CSEntry 8.0.

---

## 2. Skip-logic table (Sections A–C)

Format: **Trigger → Destination (skip range)**. Multiple "No / IDK / Not applicable" branches converging on the same target are collapsed into one row.

### Section A — Introduction and Informed Consent

| Q | Condition | Skip to |
|---|---|---|
| Q1 IS_PATIENT | = Yes (1) | **Q4** (skip Q2, Q3; respondent IS the patient, no relationship or co-residence questions needed) |
| — | `FIELD_CONTROL.CONSENT_GIVEN = No` | **Terminate interview** with `ENUM_RESULT = Withdraw Participation/Consent` |

### Section B — Patient Profile

| Q | Condition | Skip to |
|---|---|---|
| Q11 PWD | = No | **Q15** (skip Q12, Q13, Q14) |
| Q12 PWD_SPECIFY | = No | **Q15** (skip Q13, Q14) |
| Q30 IP | = No | **Q32** (skip Q31) |
| Q33 DECISION_MAKER | = Yes (1) **or** "Companion is main DM" (3) | **Q35** (skip Q34) |

### Section C — UHC Awareness

| Q | Condition | Skip to |
|---|---|---|
| Q35 UHC_HEARD | = No | **Q38** (skip Q36, Q37) |

---

## 3. Validations (Sections A–C)

### 3.1 Field Control & Geographic ID

| Item | Rule | Severity |
|---|---|---|
| `DATE_FIRST_VISIT` | Valid date; `20260101 ≤ d ≤ today + 1` | HARD |
| `DATE_FINAL_VISIT` | Valid date; `≥ DATE_FIRST_VISIT`; `≤ today + 1` | HARD |
| `TOTAL_VISITS` | `≥ 1` when `ENUM_RESULT_FIRST_VISIT` or `ENUM_RESULT_FINAL_VISIT = Completed` | HARD |
| `LATITUDE` (facility + patient home) | Numeric in `[4.5, 21.5]` (Philippine bounding box) when provided | HARD |
| `LONGITUDE` (facility + patient home) | Numeric in `[116.5, 127.0]` (Philippine bounding box) when provided | HARD |
| `CLASSIFICATION`, `REGION`, `PROVINCE_HUC`, `CITY_MUNICIPALITY`, `BARANGAY` | Required, non-blank; must exist in the loaded PSGC value sets | HARD |
| `P_REGION`, `P_PROVINCE_HUC`, `P_CITY_MUNICIPALITY`, `P_BARANGAY` | Required when `PATIENT_TYPE = Outpatient` or home-visit interview; exist in PSGC value sets | HARD |
| Child PSGC parent consistency | `PROVINCE_HUC` must be under the selected `REGION`; `CITY_MUNICIPALITY` under `PROVINCE_HUC`; `BARANGAY` under `CITY_MUNICIPALITY` (apply same check to `P_*` family) | HARD — enforce via cascading dropdown in PROC |
| `PATIENT_TYPE` | Required, ∈ {Outpatient, Inpatient}; drives Section G vs Section H gating | HARD |
| `PATIENT_LISTING_NO` | Required, 4-digit zero-filled; must match a row in the F3b patient listing export | HARD |
| `CONSENT_GIVEN` | Required; if = No → terminate with `ENUM_RESULT = Withdraw Participation/Consent` | HARD |
| `ENUM_RESULT_FIRST_VISIT = Completed` / `Completed at Hospital` / `Completed at Home` | All Section A–L mandatory items must be non-blank | HARD |

### 3.2 Section A — Introduction and Informed Consent

| Item | Rule | Severity |
|---|---|---|
| Q2 enabled | `Q1_IS_PATIENT = No` (2) | GATE |
| Q3 enabled | `Q1_IS_PATIENT = No` (2) | GATE |
| `Q2_RELATIONSHIP = 19` (Other) | `Q2_RELATIONSHIP_OTHER_TXT` required, non-blank | HARD |
| `Q2_RELATIONSHIP = 20` (Refuse) | Accept; no other-text required | — |
| `Q3_SAME_HOUSE` | Required when Q1 = No | HARD |

### 3.3 Section B — Patient Profile

**Demographics**

| Item | Rule | Severity |
|---|---|---|
| `Q4_NAME` | Required; non-blank; ≤120 chars | HARD |
| `Q5_BIRTH_MONTH` | Integer 1–12 | HARD |
| `Q5_BIRTH_YEAR` | Integer; `1900 ≤ y ≤ current_year` | HARD |
| `Q6_AGE` | `0 ≤ age ≤ 120` | HARD |
| Q5/Q6 age-vs-birth consistency | `abs((current_year − Q5_BIRTH_YEAR) − Q6_AGE) ≤ 1` (allow ±1 for not-yet-birthday) | HARD |
| `Q7_SEX` | Required, ∈ {1, 2} | HARD |
| Q8 LGBTQIA | Required, ∈ {1–5} | HARD |
| Q9 enabled | `Q8_LGBTQIA = Yes` (1) | GATE |
| `Q9_GROUP = 8` (Other) | `Q9_GROUP_OTHER_TXT` required | HARD |
| `Q10_CIVIL_STATUS` | Required, ∈ {1–8} | HARD |

**PWD block**

| Item | Rule | Severity |
|---|---|---|
| Q12 enabled | `Q11_PWD = Yes` | GATE |
| Q13 enabled | `Q11_PWD = Yes` **and** `Q12_PWD_SPECIFY = Yes` | GATE |
| Q14 enabled | `Q13_PWD_CARD = 1` (card presented and verified) | GATE |
| `Q14_DISABILITY_TYPE = 8` (Other) | `Q14_DISABILITY_OTHER_TXT` required | HARD |

**Education, employment, income**

| Item | Rule | Severity |
|---|---|---|
| `Q15_EDUCATION` | Required; if = 11 (Other), `Q15_EDUCATION_OTHER_TXT` required | HARD |
| `Q16_EMPLOYMENT` | Required, ∈ {1–9} | HARD |
| `Q17_INCOME_SOURCE` | Required, ∈ {01–09, 99} | HARD |
| `Q17` employment-consistency | If `Q16_EMPLOYMENT = 4 or 5` (unemployed) → `Q17_INCOME_SOURCE ∈ {06, 07, 08, 09, 99}` (no paid-work income source) | SOFT |
| `Q18_INCOME_AMOUNT` | Numeric; `0 ≤ amt ≤ 99,999,999`; units = PHP/month | HARD |
| `Q18_INCOME_BRACKET` | Required; bracket must contain `Q18_INCOME_AMOUNT` (see table) | HARD |

Bracket-vs-amount table (for Q18 consistency check):

| Bracket | Amount range (PHP/month) |
|---|---|
| 1 — Under 40,000     | `0 ≤ amt < 40,000` |
| 2 — 40,000–59,999    | `40,000 ≤ amt ≤ 59,999` |
| 3 — 60,000–99,999    | `60,000 ≤ amt ≤ 99,999` |
| 4 — 100,000–249,999  | `100,000 ≤ amt ≤ 249,999` |
| 5 — 250,000–499,999  | `250,000 ≤ amt ≤ 499,999` |
| 6 — 500,000 and over | `amt ≥ 500,000` |

**Household composition**

| Item | Rule | Severity |
|---|---|---|
| `Q19_HH_SIZE`     | `1 ≤ size ≤ 30` (SOFT > 15) | HARD + SOFT |
| `Q20_HH_CHILDREN` | `0 ≤ children ≤ Q19_HH_SIZE` | HARD |
| `Q21_HH_SENIORS`  | `0 ≤ seniors ≤ Q19_HH_SIZE` | HARD |
| Q20 + Q21 ≤ Q19   | `Q20_HH_CHILDREN + Q21_HH_SENIORS ≤ Q19_HH_SIZE` (working-age adults = rest) | HARD |

**Utilities and assets**

| Item | Rule | Severity |
|---|---|---|
| `Q22_ELECTRICITY`, `Q26_REFRIGERATOR`, `Q27_TELEVISION`, `Q28_WASHER` | Required, ∈ {1, 2} | HARD |
| Q22 = No + Q26/Q27/Q28 = Yes | Warn: "Household without electricity reports powered appliance" | SOFT |
| `Q23_WATER` | Required, ∈ {1–4}; if = 4 (Other), `Q23_WATER_OTHER_TXT` required | HARD |
| Q24 enabled | `Q23_WATER = 1` (Faucet inside the house) | GATE |
| Q25 enabled | `Q23_WATER = 2` (Tubed/piped well) | GATE |

**Social classification**

| Item | Rule | Severity |
|---|---|---|
| `Q29_SEC_CLASS` | Required, ∈ {1–4} | HARD |
| Q29 vs Q18 sanity | If `Q29 = 1` (Class A/B) and `Q18_INCOME_BRACKET ∈ {1, 2}` (< 60k) → Warn | SOFT |
|                   | If `Q29 = 3` (Class D/E) and `Q18_INCOME_BRACKET ≥ 4` (≥ 100k) → Warn | SOFT |
| Q31 enabled | `Q30_IP = Yes` | GATE |
| `Q31_IP_GROUP` | Required when Q31 enabled; non-blank | HARD |
| `Q32_4PS` | Required, ∈ {1, 2} | HARD |

**Decision-maker**

| Item | Rule | Severity |
|---|---|---|
| `Q33_DECISION_MAKER` | Required, ∈ {1, 2, 3} | HARD |
| Q34 enabled | `Q33_DECISION_MAKER = 2` (No) | GATE |
| `Q34_WHO_DECIDES = 11` (Other) | `Q34_WHO_DECIDES_OTHER_TXT` required | HARD |

### 3.4 Section C — UHC Awareness

| Item | Rule | Severity |
|---|---|---|
| `Q35_UHC_HEARD` | Required, ∈ {1, 2} | HARD |
| Q36 enabled | `Q35_UHC_HEARD = Yes` | GATE |
| Q37 enabled | `Q35_UHC_HEARD = Yes` | GATE |
| `Q36_UHC_SOURCE` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q36_UHC_SOURCE` "I don't know" (7) | Cannot be combined with any other option | HARD |
| `Q36_UHC_SOURCE` "Other" (8) | `Q36_UHC_SOURCE_OTHER_TXT` required | HARD |
| `Q37_UHC_UNDERSTAND` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q37_UHC_UNDERSTAND` "I don't know" (5) | Cannot be combined with any other option | HARD |
| `Q37_UHC_UNDERSTAND` "Other" (6) | `Q37_UHC_UNDERSTAND_OTHER_TXT` required | HARD |

---

## 2. Skip-logic table (Sections D–F)

### Section D — PhilHealth Registration and Health Insurance

| Q | Condition | Skip to |
|---|---|---|
| Q38 PHILHEALTH_REG | = No (2) **or** "I don't know" (3) | **Q43** (skip Q39–Q42; non-members still asked whether they know where to seek help) |
| Q41 REG_DIFFICULTY | = No | **Q43** (skip Q42 — no difficulty → no reason-for-difficulty) |
| Q43 KNOWS_ASSIST | = No | **Q45** (skip Q44 — patient doesn't know where to go, no point asking) |
| — | `Q38_PHILHEALTH_REG ≠ Yes` | **Q51** after Q45 (non-members skip Q46–Q50: benefits/packages/premiums) |
| Q48 PREMIUM_PAY | = "No, I do not pay premiums" (3) | **Q51** (skip Q49, Q50) |
| Q49 PREMIUM_DIFFICULT | = No | **Q51** (skip Q50) |
| Q51 OTHER_INSURANCE | = No | **Q53** (skip Q52) |

### Section E — Primary Care Utilization

| Q | Condition | Skip to |
|---|---|---|
| Q53 HAS_PCP | = No | **Q63** (skip Q54–Q62 — no PCP, no PCP-specific questions) |
| Q59 SCHED_COMM | "Teleconsultation" (2) NOT ticked | Q60 disabled (teleconsult-success gate) |
| Q61 CONSULT_COMM | "Teleconsultation" (2) NOT ticked | Q62 disabled (teleconsult-success gate) |
| Q63 HAS_USUAL_FACILITY | = No | **Q65** (skip Q64 — no usual facility → no name to record) |
| Q63 HAS_USUAL_FACILITY | = Yes | **Q66** (skip Q65 — usual facility present → no reason-for-none question) |
| Q66 SAME_AS_USUAL | = Yes | **Q68** (skip Q67 — this IS the usual facility, so no why-different reason) |
| Q74 KON_HEARD | = No | **Q83** (skip Q75–Q82 — never heard of YAKAP/Konsulta; all remaining E block out) |
| Q77 KON_REGISTERED | = No (2) | **Q82** (skip Q78–Q81 — not registered → jump to reasons-not-registered) |
| Q77 KON_REGISTERED | = "I've never heard of it" (3) **or** "I don't know" (4) | **Q83** (skip Q78–Q82 entirely — exit Section E) |

### Section F — Health-Seeking Behavior

No explicit skip rules in Section F. Q84 `SERVICE_TYPE` is advisory for Section G vs. Section H routing, but **the authoritative routing signal is `FIELD_CONTROL.PATIENT_TYPE`** (see §3.7 cross-field rules).

---

## 3. Validations (Sections D–F)

### 3.5 Section D — PhilHealth Registration and Health Insurance

**Registration gates**

| Item | Rule | Severity |
|---|---|---|
| `Q38_PHILHEALTH_REG` | Required, ∈ {1, 2, 3} | HARD |
| Q39 enabled | `Q38_PHILHEALTH_REG = Yes` (1) | GATE |
| Q40 enabled | `Q38_PHILHEALTH_REG = Yes` (1) | GATE |
| Q41 enabled | `Q38_PHILHEALTH_REG = Yes` (1) | GATE |
| Q42 enabled | `Q38_PHILHEALTH_REG = Yes` **and** `Q41_REG_DIFFICULTY = Yes` | GATE |
| Q44 enabled | `Q43_KNOWS_ASSIST = Yes` | GATE |
| `Q39_HOW_FIND_OUT = 10` (Other) | `Q39_HOW_FIND_OUT_OTHER_TXT` required | HARD |
| `Q40_WHO_ASSISTED = 10` (Other) | `Q40_WHO_ASSISTED_OTHER_TXT` required | HARD |
| `Q44_WHERE_ASSIST = 10` (Other) | `Q44_WHERE_ASSIST_OTHER_TXT` required | HARD |
| `Q42_DIFFICULTY` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q42_DIFFICULTY` "I don't know" (7) | Cannot be combined with any other option | HARD |
| `Q42_DIFFICULTY = 8` (Other) | `Q42_DIFFICULTY_OTHER_TXT` required | HARD |

**Member category, benefits, packages**

| Item | Rule | Severity |
|---|---|---|
| Q45 enabled | `Q38_PHILHEALTH_REG = Yes` (non-members skip to Q51) | GATE |
| `Q45_CATEGORY` | Required when enabled, ∈ {01–08, 98, 99} | HARD |
| `Q45_CATEGORY = 99` (Other) | `Q45_CATEGORY_OTHER_TXT` required | HARD |
| Q46 enabled | `Q38_PHILHEALTH_REG = Yes` | GATE |
| `Q46_BENEFITS` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q46_BENEFITS` "There are no benefits" (4) | Cannot be combined with any other option | HARD |
| `Q46_BENEFITS` "I don't know" (5) | Cannot be combined with any other option | HARD |
| `Q46_BENEFITS = 6` (Other) | `Q46_BENEFITS_OTHER_TXT` required | HARD |
| Q45 = 06 (Senior citizen) | Check patient `Q6_AGE ≥ 60` | SOFT (warn if mismatched) |
| Q47 roster — Q47_PHYSICIAN_CHECKUP / Q47_DIAGNOSTIC_TESTS / Q47_HOSPITAL_CONF / Q47_OUTPATIENT_DRUGS | Each item required, ∈ {1, 2}, when Q46 enabled | HARD |

**Premiums**

| Item | Rule | Severity |
|---|---|---|
| Q48 enabled | `Q38_PHILHEALTH_REG = Yes` | GATE |
| `Q48_PREMIUM_PAY` | Required when enabled, ∈ {1, 2, 3} | HARD |
| Q49 enabled | `Q48_PREMIUM_PAY ∈ {1, 2}` (actually pays) | GATE |
| Q50 enabled | `Q48_PREMIUM_PAY ∈ {1, 2}` **and** `Q49_PREMIUM_DIFFICULT = Yes` | GATE |
| `Q50_DIFFICULTY_PAYING` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q50_DIFFICULTY_PAYING` "I don't know" (6) | Cannot be combined with any other option | HARD |
| `Q50_DIFFICULTY_PAYING = 7` (Other) | `Q50_DIFFICULTY_PAYING_OTHER_TXT` required | HARD |

**Other insurance**

| Item | Rule | Severity |
|---|---|---|
| `Q51_OTHER_INSURANCE` | Required, ∈ {1, 2} | HARD |
| Q52 enabled | `Q51_OTHER_INSURANCE = Yes` | GATE |
| `Q52_PLANS` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q52_PLANS` "I don't know" (6) | Cannot be combined with any other option | HARD |
| `Q52_PLANS = 7` (Others) | `Q52_PLANS_OTHER_TXT` required | HARD |

### 3.6 Section E — Primary Care Utilization

**Primary care provider block (Q53–Q62)**

| Item | Rule | Severity |
|---|---|---|
| `Q53_HAS_PCP` | Required, ∈ {1, 2} | HARD |
| Q54–Q62 enabled | `Q53_HAS_PCP = Yes` | GATE |
| `Q54_PCP_TYPE` | Required when enabled, ∈ {1–5} | HARD |
| `Q54_PCP_TYPE = 4` (Other) | `Q54_PCP_TYPE_OTHER_TXT` required | HARD |
| `Q55_LOC_CONVENIENT` / `Q56_HOURS_CONVENIENT` / `Q57_WAIT_CONVENIENT` | Required when enabled, ∈ {1, 2} | HARD |
| `Q58_WAIT_DAYS` | `0 ≤ days ≤ 365` | HARD |
| `Q58_WAIT_MINUTES` | `0 ≤ minutes ≤ 1440` (24 h cap) | HARD |
| Q58 pair sanity | `Q58_WAIT_DAYS + Q58_WAIT_MINUTES > 0` (at least one non-zero when enabled) | SOFT |
| `Q59_SCHED_COMM` select-all | ≥ 1 option ticked when enabled | HARD |
| Q60 enabled | `Q59_SCHED_COMM` includes "Teleconsultation" (2) | GATE |
| `Q60_SCHED_TELECON_OK` | Required when enabled, ∈ {1, 2} | HARD |
| `Q61_CONSULT_COMM` select-all | ≥ 1 option ticked when enabled | HARD |
| Q62 enabled | `Q61_CONSULT_COMM` includes "Teleconsultation" (2) | GATE |
| `Q62_CONSULT_TELECON_OK` | Required when enabled, ∈ {1, 2} | HARD |

**Usual vs. current facility (Q63–Q73)**

| Item | Rule | Severity |
|---|---|---|
| `Q63_HAS_USUAL_FACILITY` | Required, ∈ {1, 2} | HARD |
| Q64 enabled | `Q63_HAS_USUAL_FACILITY = Yes` | GATE |
| `Q64_FACILITY_NAME` | Required when enabled, non-blank | HARD |
| Q65 enabled | `Q63_HAS_USUAL_FACILITY = No` | GATE |
| `Q65_WHY_NO_USUAL` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q65_WHY_NO_USUAL` "I don't know" (6) | Cannot be combined with any other option | HARD |
| `Q65_WHY_NO_USUAL = 7` (Other) | `Q65_WHY_NO_USUAL_OTHER_TXT` required | HARD |
| Q66 enabled | `Q63_HAS_USUAL_FACILITY = Yes` | GATE |
| `Q66_SAME_AS_USUAL` | Required when enabled, ∈ {1, 2} | HARD |
| Q67 enabled | `Q63_HAS_USUAL_FACILITY = Yes` **and** `Q66_SAME_AS_USUAL = No` | GATE |
| `Q67_WHY_THIS_FACILITY` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q67_WHY_THIS_FACILITY = 8` (Other) | `Q67_WHY_THIS_OTHER_TXT` required | HARD |
| Q68 enabled | `Q63_HAS_USUAL_FACILITY = Yes` | GATE |
| `Q68_USUAL_FAC_TYPE` | Required when enabled, ∈ {1–9} | HARD |
| `Q68_USUAL_FAC_TYPE = 9` (Other) | `Q68_USUAL_FAC_TYPE_OTHER_TXT` required | HARD |
| Q69/Q70 enabled | `Q63_HAS_USUAL_FACILITY = Yes` | GATE |
| `Q69_USUAL_TRAVEL_HH` | `0 ≤ HH ≤ 24` | HARD |
| `Q69_USUAL_TRAVEL_MM` | `0 ≤ MM ≤ 59` | HARD |
| `Q69` pair sanity | `Q69_USUAL_TRAVEL_HH + Q69_USUAL_TRAVEL_MM > 0` (warn if both zero) | SOFT |
| `Q70_USUAL_TRANSPORT` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q70_USUAL_TRANSPORT = 12` (Other) | `Q70_USUAL_TRANSPORT_OTHER_TXT` required | HARD |
| `Q71_NEAREST_TYPE` | Required, ∈ {1–8} | HARD |
| `Q71_NEAREST_TYPE = 7` (I don't know) | `Q72`, `Q73` may be skipped (IDK → no travel estimate); warn if answered anyway | SOFT |
| `Q71_NEAREST_TYPE = 8` (Other) | `Q71_NEAREST_TYPE_OTHER_TXT` required | HARD |
| `Q72_NEAREST_TRAVEL_HH` | `0 ≤ HH ≤ 24` | HARD |
| `Q72_NEAREST_TRAVEL_MM` | `0 ≤ MM ≤ 59` | HARD |
| `Q73_NEAREST_TRANSPORT` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q73_NEAREST_TRANSPORT = 12` (Other) | `Q73_NEAREST_TRANSPORT_OTHER_TXT` required | HARD |

**YAKAP/Konsulta block (Q74–Q82)**

| Item | Rule | Severity |
|---|---|---|
| `Q74_KON_HEARD` | Required, ∈ {1, 2} | HARD |
| Q75–Q82 enabled | `Q74_KON_HEARD = Yes` | GATE |
| `Q75_KON_SOURCE` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q75_KON_SOURCE` "I don't know" (7) | Cannot be combined with any other option | HARD |
| `Q75_KON_SOURCE = 8` (Other) | `Q75_KON_SOURCE_OTHER_TXT` required | HARD |
| `Q76_KON_UNDERSTAND` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q76_KON_UNDERSTAND` "There are no benefits" (5) | Cannot be combined with any other option | HARD |
| `Q76_KON_UNDERSTAND` "I don't know" (6) | Cannot be combined with any other option | HARD |
| `Q76_KON_UNDERSTAND = 7` (Other) | `Q76_KON_UNDERSTAND_OTHER_TXT` required | HARD |
| `Q77_KON_REGISTERED` | Required when enabled, ∈ {1, 2, 3, 4} | HARD |
| Q78 enabled | `Q77_KON_REGISTERED = Yes` (1) | GATE |
| Q79 enabled | `Q77_KON_REGISTERED = Yes` (1) | GATE |
| Q80 enabled | `Q77_KON_REGISTERED = Yes` (1) | GATE |
| Q81 enabled | `Q77_KON_REGISTERED = Yes` (1) **and** `Q79_KON_HAD_APPT = Yes` | GATE |
| `Q78_KON_WHEN_REG` | Required when enabled, ∈ {1–4} | HARD |
| `Q78_KON_WHEN_REG` vs. age | Warn if `Q78 ∈ {3, 4}` and Q6 age suggests YAKAP/Konsulta did not yet exist at that time (configurable by ASPSI) | SOFT |
| Q82 enabled | `Q77_KON_REGISTERED = No` (2) | GATE |
| `Q82_KON_WHY_NOT_REG` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q82_KON_WHY_NOT_REG` "I don't know" (10) | Cannot be combined with any other option | HARD |
| `Q82_KON_WHY_NOT_REG = 11` (Other) | `Q82_KON_WHY_NOT_REG_OTHER_TXT` required | HARD |

### 3.7 Section F — Health-Seeking Behavior

| Item | Rule | Severity |
|---|---|---|
| `Q83_VISIT_REASON` | Required, ∈ {1–8} | HARD |
| `Q83_VISIT_REASON = 8` (Other) | `Q83_VISIT_REASON_OTHER_TXT` required | HARD |
| `Q84_SERVICE_TYPE` | Required, ∈ {1–5} | HARD |
| `Q84_SERVICE_TYPE = 5` (Other) | `Q84_SERVICE_TYPE_OTHER_TXT` required | HARD |
| Q84 vs. `FIELD_CONTROL.PATIENT_TYPE` | `PATIENT_TYPE` is authoritative for Section G vs H routing. If `Q84 = 1 (Outpatient)` but `PATIENT_TYPE = Inpatient` (or vice versa), warn enumerator to verify | SOFT |
| `Q85_CONDITIONS` select-all | ≥ 1 option ticked | HARD |
| `Q85_CONDITIONS` "No condition - Regular check-up only" (19) | Cannot be combined with any other option | HARD |
| `Q85_CONDITIONS = 20` (Other) | `Q85_CONDITIONS_OTHER_TXT` required | HARD |
| Q85 vs. Q83 | If `Q83 = 4` (general check-up) → expect `Q85 = 19` (No condition); if conflicting, warn | SOFT |
| `Q86_VISIT_EVENTS` select-all | ≥ 1 option ticked (a visit must have SOMETHING happen) | HARD |
| `Q87_OTHER_ACTIONS` select-all | ≥ 1 option ticked | HARD |
| `Q87_OTHER_ACTIONS` "Did not seek other forms of care" (6) | Cannot be combined with any other option | HARD |
| `Q87_OTHER_ACTIONS = 7` (Other) | `Q87_OTHER_ACTIONS_OTHER_TXT` required | HARD |

**Cross-section routing signal** (carries into Chunks 3 & 4):

| Signal | Consequence |
|---|---|
| `FIELD_CONTROL.PATIENT_TYPE = Outpatient` | Section G (Q88–Q104) asked; Section H (Q105–Q115) skipped |
| `FIELD_CONTROL.PATIENT_TYPE = Inpatient`  | Section H (Q105–Q115) asked; Section G (Q88–Q104) skipped |
| `FIELD_CONTROL.PATIENT_TYPE` missing      | HARD block — cannot advance past Section F until set |

---

## 2. Skip-logic table (Sections G–I)

**Routing preamble.** `FIELD_CONTROL.PATIENT_TYPE` is the authoritative routing signal:

- `PATIENT_TYPE = Outpatient` → enter Section G (Q88–Q104); skip Section H (Q105–Q115) entirely.
- `PATIENT_TYPE = Inpatient`  → skip Section G (Q88–Q104); enter Section H (Q105–Q115).
- Section I (Q116–Q130) is asked **for both** patient types after the applicable G or H has completed.

### Section G — Outpatient Care

| Q | Condition | Skip to |
|---|---|---|
| — | `PATIENT_TYPE ≠ Outpatient` | **Section I** (skip entire G record) |
| Q89 ADVISED_ADMIT | = Yes | Q91 (Q90 is the "why not confined" reasons — only meaningful when Q89 = No; see §3.8 sanity rule) |
| Q93 LABS | "None" (17) ticked | **Q95** (skip Q94 lab-cost matrix) |
| Q95 PRESCRIBED | = No | **Q97** (skip Q96 meds-cost matrix) |
| Q99 BUCAS_HEARD | = No | **Q115 as printed** — source prints `<proceed to Q115>` which crosses out of Section G into Section H. See sanity finding #9; default behaviour: **skip to end of Section G** (i.e., skip Q100–Q104) |
| Q99 / Q100–Q103 enumerator gate | Respondent's area has no BUCAS center | Skip Q99–Q103 entirely (enumerator judgment per source note) |
| Q102 BUCAS_ACCESSED | = No | **Q104** (skip Q103) |

### Section H — Inpatient Care

| Q | Condition | Skip to |
|---|---|---|
| — | `PATIENT_TYPE ≠ Inpatient` | **Section I** (skip entire H record) |
| Q108 MEDS_OUTSIDE | = No | **Q110** (skip Q109 meds-outside-cost matrix) |
| Q110 LAB_OUTSIDE | = No | **Q113** (skip Q111, Q112) |
| Q113 PhilHealth line (`Q113_PAY_08`) | = Yes (PhilHealth already availed) | **Q114.1** (skip Q114 — why-not-availed question moot) |

### Section I — Financial Risk Protection

| Q | Condition | Skip to |
|---|---|---|
| Q116 NBB_HEARD | = No (2) **or** "I don't know" (3) | **Q119** (skip Q117, Q118) |
| Q119 ZBB_HEARD | = No (2) **or** "I don't know" (3) | **Q124** (skip Q120, Q121, Q122, Q123) |
| Q119 ZBB_HEARD | = Yes **and** `PATIENT_TYPE ≠ Inpatient` | **Q124** (Q122/Q123 presume a confinement context) |
| Q124 MAIFIP_HEARD | = No (2) **or** "I don't know" (3) | **Q130** (skip Q125–Q129) |
| — | `Q113_PAY_07` (Q113 MAIFIP row, inpatients only) = Yes | **Q125** still asked; **Q124 auto-set to Yes** per source note ("SKIP IF ANSWERED MAIFIP IN Q113" — interpreted as: don't re-ask awareness when they already availed it) |
| Q126 MAIFIP_AVAILED | = No | **Q129** (skip Q127, Q128) |
| Q127 MAIFIP_OOP | = No | **Q130** (skip Q128, Q129) |
| Q128 MAIFIP_OOP_ITEMS | (after completion) | **Q130** (skip Q129 — reached only via Q127 = Yes path) |

---

## 3. Validations (Sections G–I)

### 3.8 Sanity extensions (carries additional findings for chunks 3–4)

| # | Item | Issue | Fix |
|---|---|---|---|
| 9 | **Q99 No → Q115** | Source prints `<proceed to Q115>` but Q115 is in Section H; for an outpatient, Q115 is unreachable. Likely typo for "end of Section G". | Default: treat as end-of-Section-G (skip Q100–Q104). Flag to ASPSI for confirmation. |
| 10 | **Q90 asked regardless of Q89** | Source prints no skip between Q89 and Q90; but Q90 asks "reasons why you were NOT confined" — only meaningful when Q89 = No. | Soft-warn when `Q89_ADVISED_ADMIT = No` **and** Q90 has ticked options other than option 6 ("No need/regular check-up only"). |
| 11 | **Q99–Q103 BUCAS enumerator gate** | Source note: "Q99 to Q103 are applicable only to respondents in areas with BUCAS center. Otherwise, skip." No dcf field captures the enumerator judgment. | Add PROC-level `BUCAS_AREA_FLAG` (not in dcf) or rely on enumerator leaving Q99 blank. Simplest: if Q99 blank, treat Q100–Q103 as skipped. |
| 12 | **Q94 per-test cost matrix is aggregate** | Source says "To be asked for each lab test ticked in Q93"; dcf captures Q94 once in aggregate across all labs. | Acknowledged deviation — fieldable only if per-test roster is added. For Apr 20 bench test, aggregate is acceptable; flag for pilot. |
| 13 | **Q124 MAIFIP awareness implied by Q113** | Source note "SKIP IF ANSWERED MAIFIP IN Q113". If patient already availed MAIFIP (Q113_PAY_07 = Yes), re-asking "have you heard of MAIFIP" is redundant. | Auto-set `Q124_MAIFIP_HEARD = Yes` and hide Q124 when `Q113_PAY_07 = Yes`; proceed directly to Q125. |
| 14 | **Section H cost-matrix lengths** | Q107/Q109/Q112/Q113 amount fields use `length=9` (max 999,999,999 pesos). Inpatient stays with long confinement may approach this — monitor during pilot. | Monitor; no action. |

### 3.9 Section G — Outpatient Care

**Routing and visit reason**

| Item | Rule | Severity |
|---|---|---|
| Section G enabled | `FIELD_CONTROL.PATIENT_TYPE = Outpatient` | GATE |
| `Q88_WHY_VISIT` | Required, ∈ {1–8} | HARD |
| `Q88_WHY_VISIT = 8` (Other) | `Q88_WHY_VISIT_OTHER_TXT` required | HARD |
| `Q89_ADVISED_ADMIT` | Required, ∈ {1, 2} | HARD |
| `Q89_ADVISED_ADMIT = Yes` + in facility for outpatient | Warn enumerator: "Patient was advised to be admitted but is receiving outpatient care — verify" | SOFT |
| `Q90_NOT_CONFINED` select-all | When Q89 = No: ≥ 1 option ticked | HARD |
| `Q90_NOT_CONFINED = 7` (Other) | `Q90_NOT_CONFINED_OTHER_TXT` required | HARD |
| `Q91_USUAL_OUTPATIENT` | Required, ∈ {1, 2} | HARD |

**Consultation and lab costs (Q92–Q94)**

| Item | Rule | Severity |
|---|---|---|
| Q92 payment-source matrix | For each `Q92_PAY_{code} = Yes`, `Q92_PAY_{code}_AMT` required `> 0` (pesos); for `= No`, `_AMT` must be 0 or blank | HARD |
| Q92 mutual exclusivity | `Q92_PAY_03` ("Free/no cost") = Yes cannot coexist with any Q92_PAY_01/02/07 (Out-of-pocket/Donation/In kind) | SOFT (allow override) |
| Q92 total sanity | Sum of Q92_*_AMT > 0 if Q92_PAY_03 ≠ Yes; warn if Q92 total implausibly low/high for facility tier | SOFT |
| `Q93_LABS` select-all | ≥ 1 option ticked | HARD |
| `Q93_LABS = 16` (Other, specify) | `Q93_LABS_OTHER_TXT` required | HARD |
| `Q93_LABS = 17` (None) | Cannot be combined with any other lab option; gates Q94 off | HARD |
| Q94 payment-source matrix enabled | `Q93_LABS ≠ {17}` (at least one lab ticked) | GATE |
| Q94 amount rules | Same as Q92 pattern | HARD |

**Meds cost and final payment (Q95–Q97.2)**

| Item | Rule | Severity |
|---|---|---|
| `Q95_PRESCRIBED` | Required, ∈ {1, 2} | HARD |
| Q96 payment-source matrix enabled | `Q95_PRESCRIBED = Yes` | GATE |
| Q96 amount rules | Same as Q92 pattern | HARD |
| `Q97_FINAL_AMOUNT` | `0 ≤ amt ≤ 99,999,999` | HARD |
| Q97 vs. Q92/Q94/Q96 | `Q97_FINAL_AMOUNT` should be ≈ sum of all Out-of-pocket (`_PAY_01`) lines across Q92/Q94/Q96 ± 10%; warn otherwise | SOFT |
| Q97.1 select matrix (`Q971_{1-4}`) | For each ticked, `_AMT > 0`; sum of Q971 amounts must also appear in Q97_FINAL_AMOUNT | HARD + SOFT |
| `Q971_4 = Yes` (Other expenses) | `Q971_OTHER_TXT` required | HARD |
| Q97.2 select matrix (`Q972_{1-6}`) | For each ticked, `_AMT > 0`; NOT summed into Q97 (these are out-of-bill) | HARD |
| `Q972_6 = Yes` (Other expenses) | `Q972_OTHER_TXT` required | HARD |

**Payment sources (Q98) — 15-row matrix**

| Item | Rule | Severity |
|---|---|---|
| Q98 matrix | ≥ 1 `Q98_PAY_*` = Yes (patient must have paid somehow) | HARD |
| Q98 per-row | For each `Q98_PAY_{code} = Yes`, `Q98_PAY_{code}_AMT > 0` | HARD |
| `Q98_PAY_06 = Yes` (Other gov donation) | `Q98_OTHER_DONATION_TXT` required | HARD |
| `Q98_PAY_15 = Yes` (Other) | `Q98_OTHER_TXT` required | HARD |
| Q98 total vs. Q97 | Sum of Q98_*_AMT should ≈ `Q97_FINAL_AMOUNT + Q972 non-OOP amounts`; warn if wildly different | SOFT |

**BUCAS block (Q99–Q104)**

| Item | Rule | Severity |
|---|---|---|
| `Q99_BUCAS_HEARD` | Required when enumerator judges area has BUCAS (see sanity #11); else may be blank | HARD (conditional) |
| Q100–Q103 enabled | `Q99_BUCAS_HEARD = Yes` | GATE |
| `Q100_BUCAS_SOURCE` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q100_BUCAS_SOURCE` "I don't know" (7) | Cannot be combined with any other option | HARD |
| `Q100_BUCAS_SOURCE = 8` (Other) | `Q100_BUCAS_SOURCE_OTHER_TXT` required | HARD |
| `Q101_BUCAS_UNDERSTAND` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q101_BUCAS_UNDERSTAND = 5` (Other) | `Q101_BUCAS_UNDERSTAND_OTHER_TXT` required | HARD |
| `Q102_BUCAS_ACCESSED` | Required when Q99 = Yes, ∈ {1, 2} | HARD |
| Q103 enabled | `Q102_BUCAS_ACCESSED = Yes` | GATE |
| `Q103_BUCAS_SERVICES` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q103_BUCAS_SERVICES` "I don't know" (6) | Cannot be combined with any other option | HARD |
| `Q103_BUCAS_SERVICES = 7` (Other) | `Q103_BUCAS_SERVICES_OTHER_TXT` required | HARD |
| `Q104_WITHOUT_BUCAS` | Required when Q99 = Yes, ∈ {1–6} | HARD |
| `Q104_WITHOUT_BUCAS = 6` (Others) | `Q104_WITHOUT_BUCAS_OTHER_TXT` required | HARD |

### 3.10 Section H — Inpatient Care

**Reason and duration**

| Item | Rule | Severity |
|---|---|---|
| Section H enabled | `FIELD_CONTROL.PATIENT_TYPE = Inpatient` | GATE |
| `Q105_REASON` | Required, ∈ {1–5} | HARD |
| `Q105_REASON = 5` (Other) | `Q105_REASON_OTHER_TXT` required | HARD |
| `Q106_NIGHTS` | `0 ≤ nights ≤ 365` (warn if > 90) | HARD + SOFT |
| `Q106_DAYS`   | `0 ≤ days ≤ 365`   (warn if > 90) | HARD + SOFT |
| Q106 pair sanity | `Q106_NIGHTS + Q106_DAYS ≥ 1` (at least one full day of stay) | HARD |
| Q106 vs. visit dates | `abs((DATE_FINAL_VISIT − DATE_FIRST_VISIT) − Q106_DAYS) ≤ 1` | SOFT |

**Total bill and outside-facility costs**

| Item | Rule | Severity |
|---|---|---|
| Q107 matrix | ≥ 1 `Q107_PAY_*` = Yes | HARD |
| Q107 per-row | For each `Q107_PAY_{code} = Yes`, `Q107_PAY_{code}_AMT > 0` | HARD |
| `Q107_PAY_10 = Yes` (Other) | `Q107_PAY_OTHER_TXT` required | HARD |
| `Q108_MEDS_OUTSIDE` | Required, ∈ {1, 2} | HARD |
| Q109 matrix enabled | `Q108_MEDS_OUTSIDE = Yes` | GATE |
| Q109 per-row | Same pattern as Q107 | HARD |
| `Q109_PAY_09 = Yes` (Other) | `Q109_PAY_OTHER_TXT` required | HARD |
| `Q110_LAB_OUTSIDE` | Required, ∈ {1, 2} | HARD |
| Q111, Q112 enabled | `Q110_LAB_OUTSIDE = Yes` | GATE |
| `Q111_SERVICES_OUTSIDE` | Required when enabled, non-blank | HARD |
| Q112 matrix enabled | `Q110_LAB_OUTSIDE = Yes` | GATE |
| Q112 per-row | Same pattern as Q107 | HARD |
| `Q112_PAY_09 = Yes` (Other) | `Q112_PAY_OTHER_TXT` required | HARD |

**Payment sources (Q113) — 13-row matrix**

| Item | Rule | Severity |
|---|---|---|
| Q113 matrix | ≥ 1 `Q113_PAY_*` = Yes | HARD |
| Q113 per-row | For each `Q113_PAY_{code} = Yes`, `Q113_PAY_{code}_AMT > 0` | HARD |
| `Q113_PAY_13 = Yes` (Other) | `Q113_PAY_OTHER_TXT` required | HARD |
| Q113 total vs. Q107 | Sum of Q113_*_AMT ≈ sum of Q107 OOP + PhilHealth/HMO/etc. rows; warn if off by > 10% | SOFT |

**Why-no-PhilHealth and other-bill items (Q114, Q114.1, Q114.2)**

| Item | Rule | Severity |
|---|---|---|
| Q114 enabled | `Q113_PAY_08 ≠ Yes` (PhilHealth not availed) | GATE |
| `Q114_NO_PH` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q114_NO_PH = 7` (Other) | `Q114_NO_PH_OTHER_TXT` required | HARD |
| Q114.1 matrix (`Q1141_{1-6}`) | For each ticked, `_AMT > 0`; amount included in Q107 totals | HARD |
| `Q1141_6 = Yes` (Other) | `Q1141_OTHER_TXT` required | HARD |
| Q114.2 matrix (`Q1142_{1-7}`) | For each ticked, `_AMT > 0`; amounts are out-of-bill, NOT in Q107 | HARD |
| `Q1142_7 = Yes` (Other) | `Q1142_OTHER_TXT` required | HARD |
| `Q115_FINAL_CASH` | `0 ≤ amt ≤ 999,999,999`; should ≈ Q107 OOP row (`Q107_PAY_01_AMT`) ± 10% | HARD + SOFT |

### 3.11 Section I — Financial Risk Protection

**NBB (Q116–Q118)**

| Item | Rule | Severity |
|---|---|---|
| `Q116_NBB_HEARD` | Required, ∈ {1, 2, 3} | HARD |
| Q117, Q118 enabled | `Q116_NBB_HEARD = Yes` | GATE |
| `Q117_NBB_SOURCE` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q117_NBB_SOURCE` "I don't know" (7) | Cannot be combined with any other option | HARD |
| `Q117_NBB_SOURCE = 8` (Other) | `Q117_NBB_SOURCE_OTHER_TXT` required | HARD |
| `Q118_NBB_UNDERSTAND` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q118_NBB_UNDERSTAND` "I don't know" (8) | Cannot be combined with any other option | HARD |
| `Q118_NBB_UNDERSTAND = 9` (Other) | `Q118_NBB_UNDERSTAND_OTHER_TXT` required | HARD |

**ZBB (Q119–Q123)**

| Item | Rule | Severity |
|---|---|---|
| `Q119_ZBB_HEARD` | Required, ∈ {1, 2, 3} | HARD |
| Q120–Q123 enabled | `Q119_ZBB_HEARD = Yes` | GATE |
| `Q120_ZBB_SOURCE` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q120_ZBB_SOURCE` "I don't know" (7) | Cannot be combined with any other option | HARD |
| `Q120_ZBB_SOURCE = 8` (Other) | `Q120_ZBB_SOURCE_OTHER_TXT` required | HARD |
| `Q121_ZBB_UNDERSTAND` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q121_ZBB_UNDERSTAND` "I don't know" (8) | Cannot be combined with any other option | HARD |
| `Q121_ZBB_UNDERSTAND = 9` (Other) | `Q121_ZBB_UNDERSTAND_OTHER_TXT` required | HARD |
| Q122 enabled | `Q119_ZBB_HEARD = Yes` **and** `PATIENT_TYPE = Inpatient` | GATE |
| `Q122_ZBB_INFORMED` | Required when enabled, ∈ {1, 2} | HARD |
| Q123 enabled | `Q119_ZBB_HEARD = Yes` **and** `PATIENT_TYPE = Inpatient` | GATE |
| `Q123_ZBB_EXTENT` | Required when enabled, ∈ {1–4} | HARD |

**MAIFIP (Q124–Q129)**

| Item | Rule | Severity |
|---|---|---|
| Q124 auto-set | If `Q113_PAY_07 = Yes` (MAIFIP already availed), set `Q124_MAIFIP_HEARD = Yes` and skip display | GATE (auto) |
| `Q124_MAIFIP_HEARD` | Required, ∈ {1, 2, 3} | HARD |
| Q125–Q129 enabled | `Q124_MAIFIP_HEARD = Yes` **or** `Q113_PAY_07 = Yes` | GATE |
| `Q125_MAIFIP_SOURCE` select-all | ≥ 1 option ticked when enabled | HARD |
| `Q125_MAIFIP_SOURCE` "I don't know" (7) | Cannot be combined with any other option | HARD |
| `Q125_MAIFIP_SOURCE = 8` (Other) | `Q125_MAIFIP_SOURCE_OTHER_TXT` required | HARD |
| `Q126_MAIFIP_AVAILED` | Required when enabled, ∈ {1, 2}; must = Yes if `Q113_PAY_07 = Yes` | HARD |
| Q127 enabled | `Q126_MAIFIP_AVAILED = Yes` | GATE |
| `Q127_MAIFIP_OOP` | Required when enabled, ∈ {1, 2} | HARD |
| Q128 enabled | `Q126_MAIFIP_AVAILED = Yes` **and** `Q127_MAIFIP_OOP = Yes` | GATE |
| `Q128_MAIFIP_OOP_ITEMS` select-all | ≥ 1 option ticked when enabled | HARD |
| Q129 enabled | `Q126_MAIFIP_AVAILED = No` | GATE |
| `Q129_WHY_NO_MAIFIP` select-all | ≥ 1 option ticked when enabled; ∈ {1–4} | HARD |

**Reduced spending (Q130)**

| Item | Rule | Severity |
|---|---|---|
| `Q130_REDUCED_SPEND` | Required (asked for all patients), ∈ {1–4} | HARD |
| Q130 = Yes vs. Q98/Q113 | If patient reports reduced-spending but all Q98/Q113 amounts are in free/covered rows (no OOP), warn | SOFT |

---

*Sections J–L, CSPro logic templates: see final chunk.*
