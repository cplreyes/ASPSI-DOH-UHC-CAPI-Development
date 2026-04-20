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

*Sections D–L, CSPro logic templates: see subsequent chunks.*
