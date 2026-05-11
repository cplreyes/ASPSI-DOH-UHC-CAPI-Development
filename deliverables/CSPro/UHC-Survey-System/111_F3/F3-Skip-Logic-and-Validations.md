---
type: spec
project: ASPSI-DOH-CAPI-CSPro-Development
deliverable: F3 Patient Survey — CAPI logic spec (post-rebuild)
date_created: 2026-05-12
status: draft
source_questionnaire: raw/Project-Deliverable-1_Apr20-submitted/Annex F3_Patient Survey Questionnaire_UHC Year 2.pdf
source_dcf: deliverables/CSPro/UHC-Survey-System/111_F3/PatientSurvey.dcf
predecessor: deliverables/.archive/pre-rebuild-2026-05-11/CSPro/F3/F3-Skip-Logic-and-Validations.md
tags: [cspro, capi, skip-logic, validations, f3, rebuild]
---

# F3 Patient Survey — Skip Logic and Validations Spec (Rebuild)

Source-of-truth for CSPro CAPI logic on `PatientSurvey.dcf` (rebuild, 18 records / 805 items). All Q-numbers refer to the **Apr 20 printed Annex F3** (Q1–Q178); dcf item names follow the `Q{n}_*` convention.

> **Successor doc** — supersedes the archived pre-rebuild logic spec at `deliverables/.archive/pre-rebuild-2026-05-11/CSPro/F3/F3-Skip-Logic-and-Validations.md`. The archived spec remains code reference for PROC patterns; this doc updates references to the post-rebuild item names and the retired `F3_FACILITY_ID` / `QUESTIONNAIRE_NO`.

## Rebuild deltas vs. the archived spec

| Topic | Pre-rebuild | Post-rebuild |
|---|---|---|
| Case ID | Single `QUESTIONNAIRE_NO` (6-digit) | 5-item 12-digit block (`REGION_CODE`, `PROVINCE_HUC_CODE`, `CITY_MUNICIPALITY_CODE`, `FACILITY_NO`, `CASE_SEQ`) via `build_id_block()` |
| F1 linkage | `F3_FACILITY_ID` (10-digit numeric extra in PATIENT_GEO_ID) | **Retired.** Linkage derives from the shared first 9 digits of the case-ID (RR+PP+MMM+FF) |
| FIELD_CONTROL | Hand-rolled | Shared `build_field_control(survey_code="F3", date_label_entity="the Patient")` + extras (`PATIENT_TYPE`, `PATIENT_LISTING_NO`) |
| PATIENT_GEO_ID | 12 items (including F3_FACILITY_ID) | 11 items (F3_FACILITY_ID dropped) |
| Record names | Archived used `_CARE` and `_REG` suffixes (e.g. `K_ACCESS_MEDICINES`, `D_PHILHEALTH_REG`, `H_INPATIENT_CARE`) | Trimmed: `K_MEDICINES`, `D_PHILHEALTH`, `H_INPATIENT`. `G_OUTPATIENT_CARE` kept (matches `Outpatient Care` section label exactly) |
| Listing app | Implicit (paper-log fallback) | Sibling **110_F3_listing** CSPro app issues 12-digit case-IDs; F3 consumes them at interview-start. Custom sync (supervisor → enumerator) per the project's sync-model split |

Everything else (item names, value sets, skip rules, validations) is preserved from the archived spec; the section-by-section item counts match exactly except for the −1 from F3_FACILITY_ID.

---

## 1. Sanity-check findings (carried over from archived spec)

These are the open generator-design questions identified during the Apr 20 ingest, all still applicable post-rebuild:

| # | Item | Issue | Disposition |
|---|---|---|---|
| 1 | **Q14 DISABILITY_TYPE** card-gated | Q14 is enumerator-only ("DO NOT READ ALOUD... record the type as indicated on the card"). Must only be answered when Q13 = "Yes (card was presented and verified)" | GATE rule §3 — no DCF change |
| 2 | **Q18 amount + bracket duality** | Captures both a free-entry numeric (`Q18_INCOME_AMOUNT`) AND a ticked bracket (`Q18_INCOME_BRACKET`). Hard consistency check: amount must fall in bracket | HARD consistency rule §3 |
| 3 | **Q31 IP_GROUP specify** | PDF says "A list will be provided to ensure accurate details" but none is included. Retain alpha until ASPSI provides codes | Flag for ASPSI; alpha as default |
| 4 | **Q147 / Q156 medication lists** | Both `alpha(length=240)`. Monitor during pilot — if patients routinely list >240 chars, convert to a roster record | Monitor |
| 5 | **Q150 travel time HH/MM** | Split into `Q150_TRAVEL_HH` + `Q150_TRAVEL_MM` (both length=2). MM ∈ [0, 59]; (HH=0 ∧ MM=0) allowed only if patient lives at pharmacy — warn | HARD range + SOFT sanity §3 |
| 6 | **Q169 skip-branch coverage** | Option 2 ("No, not planning") and 3 ("Not yet, planning") both skip to Q171; option 1 ("Yes") proceeds to Q170 then Q172. Q171 always jumps to Q172 (`<Proceed to Q172>` printed in PDF) | Skip-logic §2 Section L |
| 7 | **Q159 "Not applicable" → Q164** | Q159 option 5 routes to Q164 but Q164 is in Section L, Q159 in Section K — cross-section jump. Verify intent with ASPSI; default: honor source | Flag for ASPSI; honor source |
| 8 | **Q162 No → End of survey** | Hard terminator. Set `ENUM_RESULT_FINAL_VISIT` per Field Control codes and skip Section L body (Q163-Q171). Q172-Q178 still asked (those concern non-referral visits) | PROC §3 Section L |

---

## 2. Skip-logic table

### Section A — Introduction and Informed Consent

| Q | Condition | Skip to |
|---|---|---|
| Q1 IS_PATIENT | = Yes (1) | **Q4** (skip Q2, Q3) |
| — | `FIELD_CONTROL.CONSENT_GIVEN = No` | **Terminate interview**; set `ENUM_RESULT_FINAL_VISIT = Withdraw Participation/Consent` |

### Section B — Patient Profile

| Q | Condition | Skip to |
|---|---|---|
| Q11 PWD | = No | **Q15** (skip Q12, Q13, Q14) |
| Q12 PWD_SPECIFY | = No | **Q15** (skip Q13, Q14) |
| Q13 PWD_CARD | ≠ "Yes (card presented and verified)" (1) | **Q15** (skip Q14 — GATE rule, card-gated) |
| Q30 IP | = No | **Q32** (skip Q31) |
| Q33 DECISION_MAKER | = Yes (1) **or** "Companion is main DM" (3) | **Q35** (skip Q34) |

### Section C — UHC Awareness

| Q | Condition | Skip to |
|---|---|---|
| Q35 UHC_HEARD | = No | **Q38** (skip Q36, Q37) |

### Section D — PhilHealth Registration + Insurance

| Q | Condition | Skip to |
|---|---|---|
| Q38 PHILHEALTH_REG | = No (2) **or** DK (3) | **Q43** (skip Q39-Q42) |
| Q41 REG_DIFFICULTY | = No | **Q43** (skip Q42) |
| Q43 KNOWS_ASSIST | = No | **Q51** (skip Q44; Q45-Q50 also skipped — non-member per PDF) |
| Q45 CATEGORY | (any answer; non-member case) | **Q51** (per PDF "ASKED ONLY FOR PHILHEALTH MEMBERS. SKIP TO 51 FOR NON-MEMBERS"). PROC determines non-member via `Q38_PHILHEALTH_REG = 1` precondition |
| Q48 PREMIUM_PAY | = No (3) | **Q51** (skip Q49, Q50) |
| Q49 PREMIUM_DIFFICULT | = No | **Q51** (skip Q50) |
| Q51 OTHER_INSURANCE | = No | **Q53** (skip Q52) |

### Section E — Primary Care Utilization

| Q | Condition | Skip to |
|---|---|---|
| Q53 HAS_PCP | = No | **Q63** (skip Q54-Q62) |
| Q59 SCHED_COMM | Q59 contains "Teleconsultation" (2) | enables Q60 |
| Q60 SCHED_TELECON_OK | Q59 does NOT contain "Teleconsultation" | **Q61** (skip Q60 — GATE rule) |
| Q61 CONSULT_COMM | Q61 contains "Teleconsultation" (2) | enables Q62 |
| Q62 CONSULT_TELECON_OK | Q61 does NOT contain "Teleconsultation" | **Q63** (skip Q62 — GATE rule) |
| Q63 HAS_USUAL_FACILITY | = No | **Q65** (Q64 facility name unused); after Q65 → **Q71** (skip Q66-Q70) |
| Q66 SAME_AS_USUAL | = Yes | **Q68** (skip Q67) |
| Q74 KON_HEARD | = No | **Q83** (Section F — skip Q75-Q82) |
| Q77 KON_REGISTERED | = No (2) | **Q82** (skip Q78-Q81) |
| Q77 KON_REGISTERED | = "Never heard" (3) or DK (4) | **Q83** (Section F — skip Q78-Q82) |

### Section F — Health-Seeking Behavior

No internal skips. Q84 SERVICE_TYPE gates Section G (Outpatient/Primary care) vs Section H (Inpatient/Emergency).

| Q | Condition | Skip to |
|---|---|---|
| Q84 SERVICE_TYPE | = 1 (Outpatient) or 4 (Primary care consultation) | **Section G** (Q88), then Section I (Q116) |
| Q84 SERVICE_TYPE | = 2 (Inpatient) or 3 (Emergency) | **Section H** (Q105), then Section I (Q116) |
| Q84 SERVICE_TYPE | = 5 (Other) | **Section I** (Q116) — both Sections G and H skipped |

### Section G — Outpatient Care

| Q | Condition | Skip to |
|---|---|---|
| Q89 ADVISED_ADMIT | = No | **Q91** (skip Q90) |
| Q93 LABS | only "None" (17) selected | **Q95** (skip Q94 — no lab costs) |
| Q95 PRESCRIBED | = No | **Q97** (skip Q96) |
| Q99 BUCAS_HEARD | = No | **Q104** (skip Q100-Q103). Then Q104 → **Section I (Q116)** per PDF `<skip to Q116>` |
| Q102 BUCAS_ACCESSED | = No | **Q104** (skip Q103) |
| Q104 WITHOUT_BUCAS | (any answer) | **Q116** (Section I) — section G terminus |

### Section H — Inpatient Care

| Q | Condition | Skip to |
|---|---|---|
| Q108 MEDS_OUTSIDE | = No | **Q110** (skip Q109) |
| Q110 LAB_OUTSIDE | = No | **Q113** (skip Q111, Q112) |
| Q114 NO_PH | asked ONLY if `Q113_PAY_08 = No` (PhilHealth not used in Q113) | GATE rule, PROC-enforced |
| Q115 FINAL_CASH | (terminal) | **Q116** (Section I) |

### Section I — Financial Risk Protection

| Q | Condition | Skip to |
|---|---|---|
| Q116 NBB_HEARD | = No (2) or DK (3) | **Q119** (skip Q117, Q118) |
| Q119 ZBB_HEARD | = No (2) or DK (3) | **Q124** (skip Q120-Q123) |
| Q124 MAIFIP_HEARD | (any) IF `Q113_PAY_07 = Yes` (MAIFIP used at Q113) | **Q126** (skip Q125 — already informed via Q113) |
| Q124 MAIFIP_HEARD | = No (2) or DK (3) | **Q130** (skip Q125-Q129) |
| Q126 MAIFIP_AVAILED | = No | **Q129** (skip Q127, Q128) |
| Q127 MAIFIP_OOP | = No | **Q130** (skip Q128, Q129) |

### Section J — Satisfaction

| Q | Condition | Skip to |
|---|---|---|
| Q134 AMEN_ROOMS | `Q84_SERVICE_TYPE ≠ 2` (not Inpatient) | GATE — skip Q134 |
| Q135 SAT_OVERALL_TIME | `Q84_SERVICE_TYPE ≠ 2` (not Inpatient) | GATE — skip Q135 |

### Section K — Access to Medicines

| Q | Condition | Skip to |
|---|---|---|
| Q152 GAMOT_HEARD | = No | **Q158** (skip Q153-Q157) |
| Q155 GAMOT_GOT_MEDS | = No | **Q158** (skip Q156, Q157) |
| Q158 BRAND_GEN_KNOW | (any) | proceeds to Q159 regardless (Q159 has own "Don't know the difference" option) |
| Q159 BRAND_GEN_BOUGHT | = Branded (1) | **Q161** (skip Q160) |
| Q159 BRAND_GEN_BOUGHT | = Generic (2) | **Q160** (skip Q161 after Q160) |
| Q159 BRAND_GEN_BOUGHT | = Both (3) | ask Q160, then Q161 |
| Q159 BRAND_GEN_BOUGHT | = DK (4) or NA (5) | **Q162** (skip Q160, Q161) — see Open Question #7 above |

### Section L — Referrals

| Q | Condition | Skip to |
|---|---|---|
| Q162 REFERRED | = No | **Q172** (skip Q163-Q171; non-referral path) |
| Q169 VISITED | = Yes (1) | **Q170**, then **Q172** (skip Q171) |
| Q169 VISITED | = 2 ("No, not planning") or 3 ("Not yet, planning") | **Q171**, then **Q172** (`<Proceed to Q172>` per PDF) |
| Q172 PCP_REFERRAL | = No | **Q177** (skip Q173-Q176; non-PCP-referral path) |
| Q178 SAT_REFERRAL | (terminal) | **End of survey** — set `ENUM_RESULT_FINAL_VISIT` |

---

## 3. Cross-field validations

Classified **HARD** (block save / forced re-entry), **SOFT** (warn-and-confirm), **GATE** (display-only conditional rendering — already covered as skips above).

### HARD

| # | Rule | Implementation |
|---|---|---|
| H1 | `Q5_BIRTH_MONTH ∈ [1, 12]` | PROC range check |
| H2 | `Q5_BIRTH_YEAR ∈ [1900, current_year]` and `current_year - Q5_BIRTH_YEAR ≥ Q6_AGE - 1` and `≤ Q6_AGE + 1` (age consistency) | PROC |
| H3 | `Q6_AGE ∈ [0, 120]` | range |
| H4 | `Q18_INCOME_AMOUNT` must fall in the `Q18_INCOME_BRACKET` range | PROC consistency check |
| H5 | `Q19_HH_SIZE ≥ Q20_HH_CHILDREN + Q21_HH_SENIORS` (HH size covers all sub-groups) | PROC |
| H6 | `Q19_HH_SIZE ∈ [1, 30]`, `Q20`, `Q21 ∈ [0, Q19_HH_SIZE]` | range |
| H7 | `Q106_NIGHTS` and `Q106_DAYS` non-negative; `Q106_DAYS ≤ Q106_NIGHTS + 1` | PROC consistency |
| H8 | Payment-matrix totals: sum of `_AMT` items for Q92/Q94/Q96/Q107/Q109/Q112/Q113 = `Q97_FINAL_AMOUNT` (OPD) or `Q115_FINAL_CASH` (IPD) | PROC consistency (warn if >5% off — see SOFT) |
| H9 | `Q150_TRAVEL_MM ∈ [0, 59]` | range |
| H10 | At least one option selected for select-all items where the PDF marks a `*` required-set (Q36, Q37, Q42, Q50, Q52, Q70, Q73) | PROC `count(...) > 0` |

### SOFT

| # | Rule | Implementation |
|---|---|---|
| S1 | `Q6_AGE ≥ 18` — F3 should not enroll minors per Annex F3b sampling rules. Soft because relative interviews (Q1=No) allow proxy reporting; PROC warns "Patient age <18 — confirm relative-reporting allowed" | PROC warn |
| S2 | `Q150_TRAVEL_HH = 0 AND Q150_TRAVEL_MM = 0` — soft warn "Patient at pharmacy?" | PROC warn |
| S3 | Payment-matrix totals off by >5% from `Q97_FINAL_AMOUNT` / `Q115_FINAL_CASH` — soft warn | PROC warn |
| S4 | `Q14 DISABILITY_TYPE = 8 (Other)` without `Q14_DISABILITY_OTHER_TXT` filled — warn | PROC warn |
| S5 | All Other-specify items: if option `Other (specify)` selected, the corresponding `_OTHER_TXT` must be non-empty — warn at field exit | PROC warn |

### GATE (already covered as skips in §2)

- Q14 card-gated on Q13 = 1
- Q60 telecon-gated on Q59 containing 2
- Q62 telecon-gated on Q61 containing 2
- Q134, Q135 inpatient-gated on Q84 = 2
- Q114 PhilHealth-gated on Q113_PAY_08 = No
- Q124 MAIFIP-gated by Q113_PAY_07 (skip Q125 if availed via Q113)

---

## 4. CSPro PROC code templates

Paste-ready snippets keyed to the recurring patterns. The full APC lands in `generate_apc.py` (next commit).

### 4.1 Yes/No/DK skip pattern (Q38, Q116, Q119, Q124)

```cspro
PROC Q38_PHILHEALTH_REG
postproc
    if Q38_PHILHEALTH_REG in 2, 3 then
        skip to Q43_KNOWS_ASSIST;
    endif;
```

### 4.2 Select-all gate (Q59 → Q60 teleconsult)

```cspro
PROC Q60_SCHED_TELECON_OK
preproc
    if Q59_SCHED_COMM_O02 <> 1 then  // option 2 = Teleconsultation
        skip to Q61_CONSULT_COMM;
    endif;
```

### 4.3 Inpatient-gated amenity (Q134, Q135)

```cspro
PROC Q134_AMEN_ROOMS
preproc
    if Q84_SERVICE_TYPE <> 2 then  // 2 = Inpatient
        skip to Q136_STAFF_COURTESY;
    endif;
```

### 4.4 Q1 IS_PATIENT branching (skip Q2-Q3 if respondent IS the patient)

```cspro
PROC Q1_IS_PATIENT
postproc
    if Q1_IS_PATIENT = 1 then
        skip to Q4_NAME;
    endif;
```

### 4.5 Q33 decision-maker → Q35 skip

```cspro
PROC Q33_DECISION_MAKER
postproc
    if Q33_DECISION_MAKER in 1, 3 then
        skip to Q35_UHC_HEARD;
    endif;
```

### 4.6 Other-specify enforcement (any Q with `_OTHER_TXT` companion)

```cspro
PROC Q23_WATER_OTHER_TXT
preproc
    if Q23_WATER <> 4 then  // 4 = "Other (specify)"
        skip to Q24_FAUCET_OWN;
    endif;
postproc
    if Q23_WATER = 4 and strlen(strip(Q23_WATER_OTHER_TXT)) = 0 then
        errmsg("Please specify the 'Other' water source.");
        reenter;
    endif;
```

### 4.7 Age-vs-birth-year consistency

```cspro
PROC Q6_AGE
postproc
    numeric calc_age = SYSDATE("YYYY") - Q5_BIRTH_YEAR;
    if abs(calc_age - Q6_AGE) > 1 then
        errmsg("Age (%v) inconsistent with birth year %v (computed %v). Please re-check.",
               Q6_AGE, Q5_BIRTH_YEAR, calc_age);
        reenter;
    endif;
```

### 4.8 Q18 amount-in-bracket consistency

```cspro
PROC Q18_INCOME_BRACKET
postproc
    numeric lo, hi;
    if      Q18_INCOME_BRACKET = 1 then lo = 0;      hi = 39999;
    elseif  Q18_INCOME_BRACKET = 2 then lo = 40000;  hi = 59999;
    elseif  Q18_INCOME_BRACKET = 3 then lo = 60000;  hi = 99999;
    elseif  Q18_INCOME_BRACKET = 4 then lo = 100000; hi = 249999;
    elseif  Q18_INCOME_BRACKET = 5 then lo = 250000; hi = 499999;
    elseif  Q18_INCOME_BRACKET = 6 then lo = 500000; hi = 9999999;
    endif;
    if not (Q18_INCOME_AMOUNT >= lo and Q18_INCOME_AMOUNT <= hi) then
        errmsg("Income amount %v is outside bracket %v (%v-%v).",
               Q18_INCOME_AMOUNT, Q18_INCOME_BRACKET, lo, hi);
        reenter;
    endif;
```

### 4.9 Section H entry gate (Q84 = Inpatient/Emergency)

```cspro
PROC H_INPATIENT
preproc
    if not (Q84_SERVICE_TYPE in 2, 3) then
        skip to I_FINANCIAL_RISK;
    endif;
```

### 4.10 Section G entry gate (Q84 = Outpatient/Primary care)

```cspro
PROC G_OUTPATIENT_CARE
preproc
    if not (Q84_SERVICE_TYPE in 1, 4) then
        skip to H_INPATIENT;
    endif;
```

### 4.11 Q162 No → end-of-survey block

```cspro
PROC Q162_REFERRED
postproc
    if Q162_REFERRED = 2 then  // No referral
        skip to Q172_PCP_REFERRAL;  // skip Section L body, go to non-referral block
    endif;
```

### 4.12 Q169 three-way branch

```cspro
PROC Q169_VISITED
postproc
    if Q169_VISITED in 2, 3 then
        skip to Q171_WHY_NOT;     // not visiting / planning later
    endif;
    // Q169 = 1 (Yes) falls through to Q170, then Q172
```

### 4.13 Q104 BUCAS → Section I jump

```cspro
PROC Q104_WITHOUT_BUCAS
postproc
    skip to Q116_NBB_HEARD;   // Section G terminus
```

### 4.14 Case-start setup (FIELD_CONTROL.preproc — shared template)

```cspro
PROC FIELD_CONTROL
preproc
    SURVEY_CODE = "F3";
    DATE_STARTED = SYSDATE("YYYYMMDD");
    TIME_STARTED = SYSTIME("HHMMSS");
    AAPOR_DISPOSITION = 0;   // "000 — In Progress (initial)"
    // INTERVIEWER_ID and PATIENT_LISTING_NO populated from
    // the 110_F3_listing app's synced case record (see listing app spec
    // when written).
```

---

## 5. Open questions for ASPSI / next iteration

1. **Q31 IP_GROUP** — alpha vs coded list. Reaffirm with ASPSI whether a coded IP list will ship.
2. **Q159 = DK / NA cross-section jump** — confirm whether DK/NA on branded-vs-generic should skip Q160+Q161 and proceed to Q162, or remain in section.
3. **Q147 / Q156 medication lists** — bench-test to see if 240-char alpha is enough; if not, convert to a roster.
4. **Q114 PhilHealth-gated** — currently asked only "If PhilHealth was not availed in 113". Confirm the PROC reads `Q113_PAY_08 = No` (PhilHealth row in 13-source matrix) as the gate trigger.
5. **Section J inpatient gates** — Q134 and Q135 are PDF-tagged "for inpatients only". Confirm Q131-Q133 are asked of all patients (outpatient + inpatient) for amenity-only data.
6. **Case-ID issuance handshake** — when 110_F3_listing lands, document the exact item-name(s) it writes to the F3 case header so this spec can reference them.

These do **not** block the F3 build. Default behavior follows the printed source.

---

## 6. Implementation status

- [x] DCF generated and committed (805 items, 18 records).
- [x] Logic spec drafted (this file).
- [ ] APC (`generate_apc.py`) — implements §4 templates.
- [ ] FMF generated (`generate_fmf.py`) — form layout.
- [ ] ENT generated (`generate_ent.py`) — entry application metadata.
- [ ] Wired into `build_all.py` (add `("111", "F3", "111_F3", "PatientSurvey")` to `INSTRUMENTS`).
- [ ] Smoke test on tablet (F7 publish → .pen → CSEntry).

Tracked in the F3 portion of the broader UHC-build epic.
