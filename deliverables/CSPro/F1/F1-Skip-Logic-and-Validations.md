---
type: spec
project: ASPSI-DOH-CAPI-CSPro-Development
deliverable: F1 Facility Head Survey — CAPI logic spec
date_created: 2026-04-10
status: draft
source_questionnaire: raw/Project-Deliverable-1/Annex F1_Facility Head Survey Questionnaire_UHC Year 2_April 08.pdf
source_dcf: deliverables/CSPro/F1/FacilityHeadSurvey.dcf
tags: [cspro, capi, skip-logic, validations, f1]
---

# F1 Facility Head Survey — Skip Logic and Validations Spec

This spec is the source-of-truth for CSPro CAPI logic on `FacilityHeadSurvey.dcf`. It covers:

1. **Sanity-check findings** — discrepancies between the April 8 questionnaire and the v1 dcf.
2. **Skip-logic table** — every conditional jump extracted from the questionnaire.
3. **Cross-field validations** — logical impossibilities, range checks, and consistency rules.
4. **CSPro logic templates** — paste-ready snippets for the most common patterns.

> All Q-numbers refer to the **printed questionnaire** numbering (1–166), which is what the dcf items are named after (`Q{n}_*`).

---

## 1. Sanity-check findings (dcf vs questionnaire)

### A. Bugs to fix in `generate_dcf.py` before bench-test

| # | Item | Issue | Fix |
|---|---|---|---|
| 1 | **Q166 PD_NURSES** | dcf reuses the same `pd_options` list as Q165 (doctors), which includes "Clinical audits" and "Surgical audits". The printed Q166 list omits both audit options. | Build a separate `pd_nurse_options` without `Clinical audits` / `Surgical audits`. |
| 2 | **Secondary Data section MISSING ENTIRELY** | Pages 30–34 of the questionnaire (hospital census 6mo, patient load by month, full-time/part-time HCW rosters by cadre × employment type, YAKAP services availability, procurement vs charged prices, lab markup) are not represented in the dcf at all. | Add new records: `SEC_HOSP_CENSUS` (occurs 6, monthly), `SEC_HCW_ROSTER` (one record per cadre, multi-occurring), `SEC_YK_SERVICES` (15 yes/no items), `SEC_LAB_PRICES` (procurement + charged amount per service), `SEC_FT_LEFT` / `SEC_CONTRACT_NOT_RENEWED` numerics, `SEC_LAB_MARKUP` numeric. Decide unit (record-per-month vs flat) before re-generating. |
| 3 | **Q63 ACCRED_WAIT label/units mismatch** | Printed question: "How many **days** did you wait from application to approval?" Bucket labels in both source and dcf are in **months** ("Less than a month", "1-2 months", …). | Confirm with ASPSI which is correct; either rewrite labels to days (`<30`, `31–60`, `>60`) or keep months and edit the question stem. Source bug — flag in Apr 13 LSS meeting. |
| 4 | **Q31 EMR — `Not applicable` skip omitted** | Every other UHC9 question routes "Not applicable" → next-section skip; Q31 in source omits the skip on NA but dcf inherits it as a missing skip. | Add Q31 NA → Q35 skip in CAPI logic to be consistent. Mark in field manual. |
| 5 | **Informed consent block not captured** | Field Control captures questionnaire #/visit dates but not respondent name/position/email/mobile from the consent form, nor a consent-signed flag. | Add to `FIELD_CONTROL`: `CONSENT_GIVEN` (1=Yes, 2=No, refusal aborts interview), `RESP_NAME`, `RESP_POSITION`, `RESP_EMAIL`, `RESP_MOBILE`. |
| 6 | **Tenure pre-filter missing** | Inception Report restricts F1 respondents to facility heads with **≥6 months tenure**. No screening item exists. | Either add a screening Q before Section A or enforce in Q5 logic (months ≥ 6 → continue, else terminate with refusal code). |

### B. Cosmetic / acceptable as-is

- F1.txt has stray legacy prefixes like `Q40 52`, `Q43 64` — these are leftover from an older question-numbering scheme. Dcf correctly uses the printed 1–166 numbering. No action.
- Hospital-only / PCF-only flags inside Q121 options are not encoded as separate items in the dcf — they will be enforced via display logic (Section 3 below), which is the right approach.

---

## 2. Skip-logic table

Format: **Trigger → Destination (skip range)**. Where the source has multiple "No / NA / I don't know / no plans" branches all going to the same target, they are collapsed into a single row.

### Section C — UHC Implementation

| Q | Condition | Skip to |
|---|---|---|
| Q10 HAS_PRIMARY_PKG | = No (2) | Q12 (skip Q11) |
| Q13 PUBLIC_HEALTH_UNIT | = No (2) **or** NA | Q16 (skip Q14, Q15) |
| Q14 PHU_CREATED | ∈ {No-planned, No-no-plans, No-other, IDK, NA} (5–9) | Q16 (skip Q15) |
| Q16 HEALTH_PROMO_UNIT | = No **or** NA | Q19 (skip Q17, Q18) |
| Q17 HPU_CREATED | ∈ {5–9} | Q19 (skip Q18) |
| Q19 NEW_ROLES | ∈ {5–9} | Q21 (skip Q20) |
| Q21 NEW_DEPTS | ∈ {5–9} | Q23 (skip Q22) |
| Q23 NEW_BUILDINGS | ∈ {5–9} | Q25 (skip Q24) |
| Q25 NEW_ROOMS | ∈ {5–9} | Q27 (skip Q26) |
| Q27 INC_EQUIPMENT | ∈ {5–9} | Q29 (skip Q28) |
| Q29 INC_SUPPLIES | ∈ {5–9} | Q31 (skip Q30) |
| Q31 EMR_USE | ∈ {5–8} (and NA per Bug #4) | Q35 (skip Q32, Q33, Q34) |
| Q32 DATA_SUBMIT | = "No, not submitting" (4) | Q35 (skip Q33, Q34) |
| Q35 STAFFING_CHANGED | = No | Q37 (skip Q36) |
| Q37 REFERRAL_CHANGED | = No | Q39 (skip Q38) |

### Section D — YAKAP / Konsulta

| Q | Condition | Skip to |
|---|---|---|
| **Q51 YK_ACCRED** | = No | **Q79** (skip Q52–Q78; non-accredited path) |
| Q59 KNOW_PAY_FREQ | = No | Q61 (skip Q60) |
| Q61 TRANCHE_DELAY | = No | Q62 (skip Q61.1 reason text) |
| Q65 ACCRED_DIFFICULT | = "None of the above" only | Q75 (skip Q66–Q74) |
| Q66–Q74 | Each is gated on the corresponding option being selected in Q65 (not a jump skip — display-time gate; see §3) | — |
| Q77 ENROLL_CHALL | = No | Q85 (skip Q78) |
| **Q79–Q84** | Only entered if Q51 = No | — |
| Q80 INTEND_ACCRED | = "Yes, in process" / "Yes, not in process" (1, 2) | Q84 |
|  | = "No, decided not to" (3) | Q82 |
|  | = "No, tried and failed" (4) | Q83 |
|  | = "No, haven't thought about it" (5) | Q81 |
|  | = "I don't know" (6) | Q85 |
| Q89 COSTING_DONE | = No | Q91 (skip Q90) |
| Q90 COSTING_VIABLE | = Yes AND Q51 = Yes | Q91 |
|  | = No AND Q51 = No | Q92 |
|  | = I don't know | Q93 |
| Q93 CHARGE_ADDL_CAP | = No | Q95 (skip Q94) |
| Q95 RECEIVED_PAYMENTS | ∈ {Yes-all, Yes-some} | Q97 (skip Q96) |
| Q97 PAYMENT_CHALL | = No | Q99 (skip Q98) |
| Q99, Q100 | Only if Q51 = Yes; otherwise → Q101 | — |

### Section E — BUCAS / GAMOT

| Q | Condition | Skip to |
|---|---|---|
| **Q101 HEARD_BUCAS** | = No | **Q108** (skip Q102–Q107) |
| Q102 HAS_BUCAS | = Yes | Q104 (skip Q103) |
|  | = No | Q103 then Q108 (skip Q104–Q107) |
|  | = I don't know | Q108 |
| Q103 NO_BUCAS_REASON | (any answer) | Q108 |
| Q104–Q107 | Only entered if Q102 = Yes | — |
| Q107 BUCAS_DECONGEST | Only relevant if BUCAS center exists in area (Q102 = Yes) | — |
| **Q108 HEARD_GAMOT** | = No | **Q112** (skip Q109–Q111) |
| Q109 GAMOT_ACCRED | = Yes | Q111 (skip Q110) |
|  | = No | Q110 then Q112 (skip Q111) |
| Q110 NO_GAMOT_REASON | (any answer) | Q112 |
| Q112 STOCKOUT | = No | Q118 (skip Q113–Q117) |
| Q116 ADDR_STOCKOUT | Gated on Q108 = Yes AND Q109 = Yes | — |
|  | = No or "Did not experience" | Q118 (skip Q117) |
| Q117 ADDR_STOCKOUT_HOW | Gated on Q108 = Yes AND Q109 = Yes | — |

### Section F — DOH Licensing

| Q | Condition | Skip to |
|---|---|---|
| **Q118 DOH_LICENSED** | = No / Submitted-waiting / Don't know what licensing is (2, 3, 4) | **Q135** (skip Q119–Q134) |
| Q121 DOH_LIC_DIFFICULT | = "None of the above" only | Q135 (skip Q122–Q134) |
| Q122–Q134 | Each gated on corresponding option in Q121 | — |
| **Q132, Q133, Q134** | Hospital-only — gated on Q8 SERVICE_LEVEL ∈ {Level 1, 2, 3 Hospital} AND corresponding Q121 option | — |
| **Q130** | Primary-care-only — gated on Q8 = Primary Care Facility AND Q121 price-info option | — |

### Section G — Service Delivery

| Q | Condition | Skip to |
|---|---|---|
| Q135 NBB_CURR | = No | Q138 (skip Q136, Q137) |
| Q138 ZBB_CURR | = No | Q141 (skip Q139, Q140) |
| Q141 ALLOW_OOP_BASIC | = No | Q143 (skip Q142) |
| Q145 MALASAKIT_PROVIDED | = Yes | Q146 → Q148 (skip Q147) |
|  | = No | Q147 (skip Q146) |
| Q148 LGU_SUPPORT | = No | Q152 (skip Q149, Q150, Q151) |
| Q150 LGU_SATISFIED | = Yes | Q154 (skip Q151) |
| Q152 PHO_PROTOCOL_CLARITY | ∈ {Very Clear, Clear} | Q154 (skip Q153) — *implied; confirm with ASPSI* |
| Q161 REF_SATISFACTION | ∈ {Very Satisfied, Satisfied} | Q163 (skip Q162) |

### Section H — no skips

---

## 3. Validations

Categories: **HARD** = block save / reenter, **SOFT** = warn-and-confirm, **GATE** = display-only conditional rendering.

### 3.1 Field Control & Geographic ID

| Item | Rule | Severity |
|---|---|---|
| `DATE_FIRST_VISIT` | Must be a valid date; `20260101 ≤ d ≤ today + 1` | HARD |
| `DATE_FINAL_VISIT` | Must be a valid date; `≥ DATE_FIRST_VISIT`; `≤ today + 1` | HARD |
| `TOTAL_VISITS` | `≥ 1`; if `ENUM_RESULT = Completed`, must be `≥ 1` | HARD |
| `LATITUDE` | Numeric in `[4.5, 21.5]` (Philippine bounding box) | HARD |
| `LONGITUDE` | Numeric in `[116.5, 127.0]` (Philippine bounding box) | HARD |
| `CLASSIFICATION`, `REGION`, `PROVINCE_HUC`, `CITY_MUNICIPALITY`, `BARANGAY` | Required, non-blank | HARD |
| `ENUM_RESULT = Completed` | All Section A–H mandatory items present (no blanks) | HARD |

### 3.2 Section A — Facility Head Profile

| Item | Rule | Severity |
|---|---|---|
| `Q3_AGE` | `18 ≤ age ≤ 90` | HARD |
| `Q3_AGE > 75` | Warn ("Unusually old for an active facility head — confirm") | SOFT |
| `Q5_YEARS_AT_FACILITY` | `0 ≤ y ≤ 60` | HARD |
| `Q5_MONTHS_AT_FACILITY` | `0 ≤ m ≤ 11` | HARD |
| **Tenure ≥ 6 months** | `Q5_YEARS_AT_FACILITY * 12 + Q5_MONTHS_AT_FACILITY ≥ 6` (per IR eligibility) | HARD — terminate interview if violated |
| `Q5_YEARS_AT_FACILITY ≤ Q3_AGE − 18` | Can't have started working before age 18 | HARD |
| `Q6_YEARS_HEALTH` | `0 ≤ y ≤ 70` | HARD |
| `Q6_YEARS_HEALTH ≤ Q3_AGE − 18` | Same age-floor rule | HARD |
| **Tenure consistency** | `Q5_total ≤ Q6_total` (years at this facility cannot exceed total years in any health-related role) | HARD |
| `Q4_SEX` | Required, ∈ {1, 2} | HARD |
| `Q2_DESIGNATION = "Other"` | `Q2_DESIGNATION_OTHER_TXT` is required, non-blank | HARD |

### 3.3 Section B — Facility Profile

| Item | Rule | Severity |
|---|---|---|
| `Q7_OWNERSHIP` | Required | HARD |
| `Q8_SERVICE_LEVEL` | Required; drives Q121 / Q130 / Q132–134 gates | HARD |

### 3.4 Section C — UHC Implementation

| Item | Rule | Severity |
|---|---|---|
| Q11 enabled | Q10 = Yes | GATE |
| Q14, Q15 enabled | Q13 = Yes | GATE |
| Q15 enabled | Q14 ∈ {1–4} ("Yes" branches) | GATE |
| Q17, Q18 enabled | Q16 = Yes | GATE |
| Q18 enabled | Q17 ∈ {1–4} | GATE |
| Q20 enabled | Q19 ∈ {1–4} | GATE |
| Q22 enabled | Q21 ∈ {1–4} | GATE |
| Q24 enabled | Q23 ∈ {1–4} | GATE |
| Q26 enabled | Q25 ∈ {1–4} | GATE |
| Q28 enabled | Q27 ∈ {1–4} | GATE |
| Q30 enabled | Q29 ∈ {1–4} | GATE |
| Q33, Q34 enabled | Q32 ∈ {1, 2, 3} | GATE |
| Q36 enabled | Q35 = Yes | GATE |
| Q38 enabled | Q37 = Yes | GATE |
| Q49, Q50 select-all | Cannot combine "I don't know" with substantive options | HARD |
| Q49, Q50 select-all | Cannot combine "Other" without `_OTHER_TXT` filled | HARD |
| All `Q*_OTHER_TXT` | Required if "Other" option selected | HARD |
| All `Q*_YES_OTHER_TXT` | Required if main = 4 ("Yes, other reason") | HARD |
| All `Q*_NO_OTHER_TXT` | Required if main = 7 ("No, other reason") | HARD |

### 3.5 Section D — YAKAP / Konsulta

| Item | Rule | Severity |
|---|---|---|
| Q52–Q78 entered | Q51 = Yes | GATE |
| Q79–Q84 entered | Q51 = No | GATE |
| `Q52_YK_SINCE_YEAR` | `2019 ≤ year ≤ current_year` (UHC Act passed 2019) | HARD |
| `Q52_YK_SINCE_MONTH` | `1 ≤ m ≤ 12` | HARD |
| `Q52` not in future | `(year, month) ≤ (current_year, current_month)` | HARD |
| Q52 vs head's career | Accreditation date should be after head turned 18 — `current_year - Q52_YK_SINCE_YEAR ≤ Q3_AGE - 18` | SOFT |
| `Q57_CAPITATION_AMT` | `0 < amt ≤ 5000` (PHP) | HARD |
| `Q57_CAPITATION_AMT > 1700` | Warn ("Above PhilHealth max — confirm") | SOFT |
| Q60 enabled | Q59 = Yes | GATE |
| Q61 reason text | Q61 = Yes | GATE |
| **Q66–Q74 each** | Q65 has the corresponding option selected | GATE |
| Q78 enabled | Q77 = Yes | GATE |
| **Q80 routing** | See skip table; only one of Q81/Q82/Q83/Q84 should be answered per case | HARD |
| `Q86_ELIGIBLE_PATIENTS` | `0 ≤ n ≤ 1,000,000` | HARD |
| `Q87_REGISTERED_PATIENTS` | `0 ≤ n ≤ Q86_ELIGIBLE_PATIENTS` (registered cannot exceed eligible) | HARD |
| `Q87 / Q86 > 1.0` | Block with reentry | HARD |
| Q90 enabled | Q89 = Yes | GATE |
| `Q91_MIN_CAP_VALUE_ACC` | `0 < amt ≤ 50000`; warn if `> 5000` | HARD / SOFT |
| `Q92_MIN_CAP_VALUE_NONACC` | `0 < amt ≤ 50000`; warn if `> 5000` | HARD / SOFT |
| Q94 enabled | Q93 = Yes | GATE |
| Q96 enabled | Q95 ∈ {3, 4} (No options) | GATE |
| Q98 enabled | Q97 = Yes | GATE |
| Q99, Q100 enabled | Q51 = Yes | GATE |

### 3.6 Section E — BUCAS / GAMOT

| Item | Rule | Severity |
|---|---|---|
| Q102–Q107 enabled | Q101 = Yes | GATE |
| Q103 enabled | Q102 = No | GATE |
| Q104–Q107 enabled | Q102 = Yes | GATE |
| Q109–Q111 enabled | Q108 = Yes | GATE |
| Q110 enabled | Q109 = No | GATE |
| Q111 enabled | Q109 = Yes | GATE |
| Q113–Q117 enabled | Q112 = Yes | GATE |
| Q116, Q117 enabled | Q108 = Yes AND Q109 = Yes AND Q112 = Yes | GATE |
| `Q114_STOCKOUT_DURATION` vs `Q115_STOCKOUT_AVG` | If `Q114 = "More than 60 days"`, `Q115` should not be `"Less than a month"` (contradiction) | HARD |

### 3.7 Section F — DOH Licensing

| Item | Rule | Severity |
|---|---|---|
| Q119–Q134 enabled | Q118 = Yes (1) | GATE |
| Q122–Q134 enabled | Corresponding Q121 option selected | GATE |
| **Q132, Q133, Q134** enabled | Q8 ∈ {Level 1, 2, 3 Hospital} AND corresponding Q121 option | GATE |
| **Q130** enabled | Q8 = Primary Care Facility AND Q121 price-info option | GATE |
| Q121 hospital-only options selectable | Only if Q8 ∈ hospital levels | GATE |
| Q121 PCF-only option selectable | Only if Q8 = Primary Care Facility | GATE |

### 3.8 Section G — Service Delivery

| Item | Rule | Severity |
|---|---|---|
| Q136, Q137 enabled | Q135 = Yes | GATE |
| Q139, Q140 enabled | Q138 = Yes | GATE |
| Q142 enabled | Q141 = Yes | GATE |
| Q146 enabled | Q145 = Yes | GATE |
| Q147 enabled | Q145 = No | GATE |
| Q149–Q151 enabled | Q148 = Yes | GATE |
| Q151 enabled | Q150 = No | GATE |
| Q153 enabled | Q152 ∈ {Unclear, Very Unclear} | GATE |
| `Q154_NUM_REFERRED_OUT` | `0 ≤ n ≤ 100,000` (over 6 months); warn if `> 10,000` | HARD / SOFT |
| Q162 enabled | Q161 ∈ {Neither, Dissatisfied, Very Dissatisfied} | GATE |

### 3.9 Cross-section consistency

| Rule | Severity |
|---|---|
| If `Q118 = "I don't know what DOH licensing is"`, the Q65 option "DOH licensing requirements" should not be selected | SOFT (warn) |
| If `Q51 = Yes`, no answers should be present for Q79–Q84 | HARD |
| If `Q51 = No`, no answers should be present for Q52–Q78 | HARD |
| If `Q102 = No`, no answers in Q104–Q107 | HARD |
| If `Q109 = No`, no answers in Q111 | HARD |
| Secondary data — full-time staff who left ≤ total full-time staff count (when secondary data record is added per Bug #2) | HARD |

---

## 4. CSPro logic templates

Drop these into the corresponding `PROC` blocks in CSPro Designer. Item names match `generate_dcf.py`.

### 4.1 Helper: current date

```cspro
PROC GLOBAL
numeric currentYYYYMMDD;
numeric currentYear;
numeric currentMonth;

PROC FACILITYHEADSURVEY_FF       { application-level entry }
preproc
  currentYYYYMMDD = systemdate("YYYYMMDD");
  currentYear  = int(currentYYYYMMDD / 10000);
  currentMonth = int(currentYYYYMMDD / 100) % 100;
endpreproc
```

### 4.2 Eligibility gate at Q5/Q6 (terminate non-eligible respondents)

```cspro
PROC Q5_MONTHS_AT_FACILITY
postproc
  if (Q5_YEARS_AT_FACILITY * 12 + Q5_MONTHS_AT_FACILITY) < 6 then
    errmsg("Respondent must have ≥ 6 months in current position. End interview and code as Refused/Incomplete.");
    move to ENUM_RESULT;
  endif;

  if Q5_YEARS_AT_FACILITY > (Q3_AGE - 18) then
    errmsg("Years at facility (%d) exceeds working-age years available (%d). Reenter.",
           Q5_YEARS_AT_FACILITY, Q3_AGE - 18);
    reenter;
  endif;
```

### 4.3 Tenure consistency at Q6

```cspro
PROC Q6_MONTHS_HEALTH
postproc
  numeric tenureMos;
  numeric healthMos;
  tenureMos = Q5_YEARS_AT_FACILITY * 12 + Q5_MONTHS_AT_FACILITY;
  healthMos = Q6_YEARS_HEALTH * 12 + Q6_MONTHS_HEALTH;

  if healthMos < tenureMos then
    errmsg("Years in any health-related role (%d mos) cannot be less than years at this facility (%d mos).",
           healthMos, tenureMos);
    reenter;
  endif;

  if Q6_YEARS_HEALTH > (Q3_AGE - 18) then
    errmsg("Years in health (%d) exceeds working-age years available (%d).",
           Q6_YEARS_HEALTH, Q3_AGE - 18);
    reenter;
  endif;
```

### 4.4 Section C — generic UHC9 skip pattern (apply to Q11–Q48 sub-questions)

```cspro
{ Example: Q14 controls whether Q15 (PHU role) is asked. }
PROC Q14_PHU_CREATED
postproc
  if Q14_PHU_CREATED in 5:9 then    { 5..9 = all No / IDK / NA branches }
    skip to Q16_HEALTH_PROMO_UNIT;
  endif;
```

For dichotomous yes/no skips:

```cspro
PROC Q10_HAS_PRIMARY_PKG
postproc
  if Q10_HAS_PRIMARY_PKG = 2 then    { No }
    skip to Q12_PCB_LICENSING;
  endif;

PROC Q13_PUBLIC_HEALTH_UNIT
postproc
  if Q13_PUBLIC_HEALTH_UNIT in 2,9 then  { No or NA }
    skip to Q16_HEALTH_PROMO_UNIT;
  endif;
```

### 4.5 Section D — YAKAP master gate at Q51

```cspro
PROC Q51_YK_ACCRED
postproc
  if Q51_YK_ACCRED = 2 then  { Not accredited }
    skip to Q79_NOT_ACCRED_REASON;
  endif;
```

### 4.6 Q52 accreditation date validation

```cspro
PROC Q52_YK_SINCE_YEAR
postproc
  if Q52_YK_SINCE_YEAR < 2019 or Q52_YK_SINCE_YEAR > currentYear then
    errmsg("YAKAP accreditation year must be between 2019 and %d.", currentYear);
    reenter;
  endif;

PROC Q52_YK_SINCE_MONTH
postproc
  if Q52_YK_SINCE_MONTH < 1 or Q52_YK_SINCE_MONTH > 12 then
    errmsg("Month must be 1–12.");
    reenter;
  endif;
  if Q52_YK_SINCE_YEAR = currentYear and Q52_YK_SINCE_MONTH > currentMonth then
    errmsg("Accreditation date is in the future. Reenter.");
    reenter;
  endif;
```

### 4.7 Q86/Q87 consistency

```cspro
PROC Q87_REGISTERED_PATIENTS
postproc
  if Q87_REGISTERED_PATIENTS > Q86_ELIGIBLE_PATIENTS then
    errmsg("Registered patients (%d) cannot exceed eligible patients (%d).",
           Q87_REGISTERED_PATIENTS, Q86_ELIGIBLE_PATIENTS);
    reenter;
  endif;
```

### 4.8 Q57 capitation soft warning

```cspro
PROC Q57_CAPITATION_AMT
postproc
  if Q57_CAPITATION_AMT > 5000 then
    errmsg("Capitation %d PHP is implausibly high. Reenter or confirm.", Q57_CAPITATION_AMT);
    reenter;
  endif;
  if Q57_CAPITATION_AMT > 1700 then
    if not accept("Capitation %d exceeds the PHP 1,700 PhilHealth max. Confirm?", "Yes", "No") = 1 then
      reenter;
    endif;
  endif;
```

### 4.9 Section F — Q121 facility-type-aware gating

```cspro
PROC Q121_DOH_LIC_DIFFICULT
preproc
  { Hide hospital-only options for non-hospital facilities }
  if Q8_SERVICE_LEVEL = 1 then  { Primary Care Facility }
    setvalueset(Q121_DOH_LIC_DIFFICULT, vs_q121_pcf);
  else
    setvalueset(Q121_DOH_LIC_DIFFICULT, vs_q121_hospital);
  endif;
postproc
  { "None of the above" → skip the why-difficult cluster }
  if Q121_O14_NONE = 1 then
    skip to Q135_NBB_CURR;
  endif;
```

### 4.10 Generic "why-difficult" gate (Q66–Q74, Q122–Q134)

```cspro
PROC Q66_WHY_DIFF_66
preproc
  { Skip Q66 entirely if Q65 didn't flag this area }
  if Q65_O01_ABILITY_TO_CONDUCT_PRE = 0 then
    skip to next;
  endif;
```

### 4.11 Section G — Q150 → Q154 jump

```cspro
PROC Q150_LGU_SATISFIED
postproc
  if Q150_LGU_SATISFIED = 1 then  { Yes }
    skip to Q154_NUM_REFERRED_OUT;
  endif;
```

### 4.12 Section G — Q161 satisfaction skip

```cspro
PROC Q161_REF_SATISFACTION
postproc
  if Q161_REF_SATISFACTION in 1,2 then  { Very Satisfied / Satisfied }
    skip to Q163_HR_CHALL;     { Section H starts here }
  endif;
```

### 4.13 "Other (specify)" enforcement (apply to every `Q*_OTHER_TXT`)

```cspro
PROC Q11_OTHER_TXT
postproc
  if Q11_PRIMARY_PKG_STATUS = 5 and length(strip(Q11_OTHER_TXT)) = 0 then
    errmsg("'Other' was selected for Q11. Please specify.");
    reenter;
  endif;
```

For UHC9 items (`*_YES_OTHER_TXT` / `*_NO_OTHER_TXT`):

```cspro
PROC Q12_YES_OTHER_TXT
postproc
  if Q12_PCB_LICENSING = 4 and length(strip(Q12_YES_OTHER_TXT)) = 0 then
    errmsg("'Yes, other reason' was selected. Please specify.");
    reenter;
  endif;

PROC Q12_NO_OTHER_TXT
postproc
  if Q12_PCB_LICENSING = 7 and length(strip(Q12_NO_OTHER_TXT)) = 0 then
    errmsg("'No, other reason' was selected. Please specify.");
    reenter;
  endif;
```

### 4.14 Geographic ID lat/long bounds

```cspro
PROC LATITUDE
postproc
  numeric lat;
  lat = tonumber(LATITUDE);
  if lat = notappl or lat < 4.5 or lat > 21.5 then
    errmsg("Latitude must be a number between 4.5 and 21.5 (Philippines).");
    reenter;
  endif;

PROC LONGITUDE
postproc
  numeric lon;
  lon = tonumber(LONGITUDE);
  if lon = notappl or lon < 116.5 or lon > 127.0 then
    errmsg("Longitude must be a number between 116.5 and 127.0 (Philippines).");
    reenter;
  endif;
```

---

## 5. Open questions for the Apr 13 LSS meeting

1. **Q63 days vs months** — clarify whether "How many days did you wait" should have day buckets or month buckets.
2. **Secondary data section** — confirm structure: separate dcf records vs separate CSPro app vs paper-only collection.
3. **Eligibility termination** — should `<6 months tenure` exit the questionnaire entirely, or capture what data we have and code as Incomplete?
4. **Q31 NA-skip** — is the missing skip on "Not applicable" intentional?
5. **Q166 PD_NURSES options** — confirm whether nurses really should not have "Clinical audits" / "Surgical audits" in the choice list, or whether the printed questionnaire is missing them.
6. **Hospital-only Q121 options** — confirm whether the Q121 value set should dynamically change by facility type, or whether all options are shown and only enforcement happens via skip on Q132/Q133/Q134.

---

## 6. Implementation order (recommended)

1. **Fix dcf bugs #1, #4, #5, #6** in `generate_dcf.py`, regenerate `FacilityHeadSurvey.dcf`.
2. **Decide secondary data structure** (Bug #2), add records, regenerate.
3. **Open in CSPro Designer**, validate the dictionary loads cleanly.
4. **Build Form file** (`.fmf`) — one form per record A–H + secondary data.
5. **Add PROC code** in this order: Field Control validations → Section A eligibility → Section C generic UHC9 skips → Section D Q51 master gate → other section gates → Other-specify enforcements.
6. **Bench-test** with paper-walkthrough of 2–3 mock facility responses (one accredited hospital, one non-accredited PCF, one terminated-on-tenure case).
7. **Pretest readiness** — bundle as PFF for CSEntry Android distribution.

---

*This spec is generated from the April 8 Annex F1 PDF and the v1 dcf. Update both this file and `generate_dcf.py` whenever the questionnaire is revised.*
