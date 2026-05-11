---
type: spec
project: ASPSI-DOH-CAPI-CSPro-Development
deliverable: F3 Patient Survey — CAPI form-layout plan
date_created: 2026-04-21
status: draft
source_dcf: deliverables/CSPro/F3/PatientSurvey.dcf
source_spec: deliverables/CSPro/F3/F3-Skip-Logic-and-Validations.md
inherits: deliverables/CSPro/Form-Layout-Principles.md
tags: [cspro, capi, fmf, form-layout, f3]
---

# F3 Patient Survey — Form-Layout Plan

**Scope:** section-by-section form inventory for `PatientSurvey.fmf`, mapping each DCF record to concrete CSEntry forms. Built on top of [[../Form-Layout-Principles]] — read that first.

**Source DCF:** 18 records / 835 items (Apr 21 build), covering 178 source questions.
**Source spec:** [[F3-Skip-Logic-and-Validations]] for gates, skips, validations, and cross-section routing.

**Key differences from F1:**
- Two separate GPS capture records: facility (`REC_FACILITY_CAPTURE`, type Z) and patient home (`REC_PATIENT_HOME_CAPTURE`, type Y). Distinct because a patient may be interviewed at home after being identified at a facility.
- Verification photo is its own record (`REC_CASE_VERIFICATION`, type X) — one photo per case.
- `F3_FACILITY_ID` links the patient case back to the F1 facility record (MVP analytical linkage).
- Q1 IS_PATIENT gate determines whether relationship/co-residence questions apply (Q2, Q3).
- Q162 is a hard terminator (end-of-survey trigger).

---

## 1. Record-to-form map (summary)

| # | Record (DCF) | Type | Form(s) | Notes |
|---|---|---|---|---|
| 1 | `PATIENTSURVEY_REC` | 1 | (container; no form) | — |
| 2 | `FIELD_CONTROL` | A (1 occ) | 1 form | Metadata, AAPOR, consent |
| 3 | Geo ID fields (incl. `F3_FACILITY_ID`) | — | 1 form | PSGC cascade + F1 linkage |
| 4 | `REC_FACILITY_CAPTURE` | Z (off-form) | Triggers on 1 form | Facility GPS |
| 5 | `REC_PATIENT_HOME_CAPTURE` | Y (off-form) | Triggers on same or new form | Patient home GPS |
| 6 | `REC_CASE_VERIFICATION` | X (off-form) | Trigger on capture form | One photo/case |
| 7 | `A_INFORMED_CONSENT` | C (1 occ) | 1 form | Respondent/patient/witness, Q1 gate |
| 8 | `B_PATIENT_PROFILE` | D (1 occ) | 3 forms | Demographics + disability + income |
| 9 | `C_UHC_AWARENESS` | E (1 occ) | 2 forms | — |
| 10 | `D_PHILHEALTH_REG` | F (1 occ) | 2 forms | Registration + membership category |
| 11 | `E_PRIMARY_CARE` | G (1 occ) | 3 forms | PCP + YAKAP/Konsulta |
| 12 | `F_HEALTH_SEEKING` | H (1 occ) | 2 forms | — |
| 13 | `G_OUTPATIENT_CARE` | I (1 occ) | 3 forms | Payment-source matrix (Q92 et al.) drives split |
| 14 | `H_INPATIENT_CARE` | J (1 occ) | 3 forms | Payment-source matrix (Q107 et al.) drives split |
| 15 | `I_FINANCIAL_RISK` | K (1 occ) | 3 forms | NBB + ZBB + MAIFIP + distress |
| 16 | `J_SATISFACTION` | L (1 occ) | 1 form | — |
| 17 | `K_ACCESS_MEDICINES` | M (1 occ) | 2 forms | Q147/Q156 med lists, Q150 travel time |
| 18 | `L_REFERRALS` | N (1 occ) | 2 forms | Q162 terminator, Q169 routing |
| — | Closing disposition | — | 1 form | — |

**Total: ~30 forms.**

---

## 2. Form-by-form plan

### Form 1 — `FC_METADATA` (FIELD_CONTROL)

Case ID, survey code, interviewer ID, date/time, AAPOR disposition, consent gate. Same shape as F1 Form 1. Consent = No → jump to closing.

### Form 2 — `FC_GEO` (Geographic ID + F1 linkage)

| Row | Field | Control | Notes |
|---|---|---|---|
| 1–4 | Region → Province → City/Mun → Barangay | Cascade dropdowns | Via `shared/PSGC-Cascade.apc` |
| 5 | `F3_FACILITY_ID` | Numpad (10 digit, zero-fill) | Links back to F1 case; shown as "Sampled facility ID" |
| 6 | `FACILITY_NAME` | Single-line text (prefill if facility known) | — |
| 7 | `PATIENT_HOME_ADDRESS` | Multi-line text (3 rows) | Distinct from facility address |

**Row cost:** 9 · **Budget fit:** ✅

### Form 3 — `FC_CAPTURE_FACILITY` (facility GPS)

One form dedicated to facility GPS. Trigger calls `ReadGPSReading()` with `FACILITY_` prefix. GPS status display shows lat/long/accuracy from `REC_FACILITY_CAPTURE`.

**Row cost:** 5

### Form 4 — `FC_CAPTURE_HOME` (patient home GPS + verification photo)

Bundled because both capture events happen at the interview location (patient home). Photo filename pattern: `case-{QUESTIONNAIRE_NO}-verification.jpg`.

| Row | Field | Control | Notes |
|---|---|---|---|
| 1 | Label "Capture patient home GPS" | Section label | — |
| 2 | `P_HOME_GPS_TRIGGER` | Button | `onfocus` → `ReadGPSReading()` with `P_HOME_` prefix |
| 3 | `P_HOME_GPS_STATUS` | Read-only | — |
| 4 | Label "Take verification photo" | Section label | — |
| 5 | `PHOTO_TRIGGER` | Button | `onfocus` → `TakeVerificationPhoto()` |
| 6 | `PHOTO_STATUS` | Read-only | — |

**Row cost:** 6 · **Helpers:** `shared/Capture-Helpers.apc`

### Form 5 — `A_CONSENT` (Section A — Informed Consent + Q1 gate)

| Row | Field | Control | Notes |
|---|---|---|---|
| 1 | `Q1_IS_PATIENT` | Radio, horizontal (Y/N) | **Gate:** Yes → skip Forms 6–7 of Section A proxies (Q2, Q3 not asked); No → proceed |
| 2 | `Q2_RELATIONSHIP` | Dropdown | Gated on Q1 = No |
| 3 | `Q3_CO_RESIDENT` | Radio, horizontal | Gated on Q1 = No |
| 4 | Informed-consent script | Section label + text | — |
| 5 | `RESP_NAME` / `PATIENT_NAME` / `WITNESS_NAME` | 3 text fields | Witness only if required |
| 6 | `CONSENT_SIGNED_DATE` | DatePicker | — |

**Row cost:** ~8 · Consent fields overlap with `FIELD_CONTROL`'s consent but capture respondent/witness identity here per the Apr 20 questionnaire.

### Forms 6–8 — Section B (Patient Profile, Q4–Q18)

| Form | Label | Q range | Content |
|---|---|---|---|
| 6 | `B1_DEMOGRAPHICS` | Q4–Q12 | Age, sex, civil status, education, employment |
| 7 | `B2_DISABILITY` | Q13–Q14 | Disability + Q14 card-gated (Q14 only when Q13 = "Yes, card verified") |
| 8 | `B3_INCOME_HH` | Q15–Q18 | IP group, HH size, income amount **and** bracket (consistency check in `postproc`) |

### Forms 9–10 — Section C (UHC Awareness)

Split by topic; small sections stay on one form where they fit the budget.

### Forms 11–12 — Section D (PhilHealth Registration, Q31–Q45+)

Q45 member-category labels are paragraph-length — give the label control enough vertical space; keep 2–3 such options per form maximum (they'll burst the row budget otherwise). Split by registration status + category.

### Forms 13–15 — Section E (Primary Care + YAKAP/Konsulta)

Three forms because YAKAP/Konsulta carries its own skip-tree similar to F1 Section D.

### Forms 16–17 — Section F (Health-Seeking)

Two forms; one on the primary care seek path, one on referrals path.

### Forms 18–20 — Section G (Outpatient Care, Q92 payment-source matrix)

Q92/Q94/Q96/Q98 each explode into `_PAY_{code}` + `_PAY_{code}_AMT` pairs. These payment-source matrices are dense — dedicate one form to each matrix.

| Form | Label | Content |
|---|---|---|
| 18 | `G1_OUTPATIENT_EVENT` | Outpatient encounter details |
| 19 | `G2_OUTPATIENT_PAYMENTS` | Q92 + Q94 payment-source matrix (one matrix per form if budget tight) |
| 20 | `G3_OUTPATIENT_EXPERIENCE` | Q96 + Q98 + follow-up |

### Forms 21–23 — Section H (Inpatient Care, Q107/Q109/Q112/Q113 payment matrices)

Same split logic as Section G. Inpatient has more payment rows, so two-form matrix split is likely.

### Forms 24–26 — Section I (Financial Risk — NBB + ZBB + MAIFIP + distress)

Mirrors F1 Section G structure (NBB/ZBB/MAIFIP named subsections) but patient-side. Three forms keep each subsection on its own form.

### Form 27 — `J_SATISFACTION` (Section J)

Single form. Satisfaction items are short-form Likert — high row budget utilization with compact labels is fine.

### Forms 28–29 — Section K (Access to Medicines, GAMOT)

| Form | Label | Content |
|---|---|---|
| 28 | `K1_GAMOT_ACCESS` | Q147 med list (alpha 240) + Q148 challenge select-all (20 options, compact) |
| 29 | `K2_GAMOT_TRAVEL` | Q150 travel HH/MM split, Q156 second med list, Q159 NA → Q164 jump |

**Q148 / Q164 long select-all lists:** checkbox list renders fine on tablet but the form will scroll if > 16 rows. Each list gets its own form if needed.

### Forms 30–31 — Section L (Referrals, Q162 terminator + Q169 routing)

| Form | Label | Content |
|---|---|---|
| 30 | `L1_REFERRAL_EXPERIENCE` | Q160–Q168; **Q162 = No → jump to Form 32 (closing)** with `ENUM_RESULT = Completed` |
| 31 | `L2_FOLLOWUP` | Q169 routing: Yes → Q170 → Q172; No/Not-planning → Q171 → Q172 |

### Form 32 — `CLOSING`

AAPOR final disposition, interviewer notes, time ended, submit. Same as F1.

---

## 3. Form order (tab order)

```
1  FC_METADATA
2  FC_GEO (includes F3_FACILITY_ID linkage)
3  FC_CAPTURE_FACILITY
4  FC_CAPTURE_HOME (incl. verification photo)
5  A_CONSENT (Q1 gate)
6  B1_DEMOGRAPHICS
7  B2_DISABILITY (Q13/Q14 card gate)
8  B3_INCOME_HH (Q18 amount↔bracket HARD check)
9–10   C1, C2 (UHC Awareness)
11–12  D1, D2 (PhilHealth)
13–15  E1, E2, E3 (Primary care + YAKAP/Konsulta)
16–17  F1, F2 (Health-seeking)
18–20  G1, G2, G3 (Outpatient)
21–23  H1, H2, H3 (Inpatient)
24–26  I1, I2, I3 (NBB/ZBB/MAIFIP/distress)
27     J (Satisfaction)
28–29  K1, K2 (GAMOT)
30–31  L1, L2 (Referrals; Q162 terminator on Form 30)
32     CLOSING
```

**Form-level skips:**
- Consent = No (Form 1) → Form 32.
- Q1 = Yes (Form 5) → skip Q2, Q3 at field level (stay on Form 5).
- Q162 = No (Form 30) → set `ENUM_RESULT = Completed`, skip Form 31 → Form 32.
- Q159 = Not applicable (Form 29) → jump to Form 30 (Q164 start; per source).

All other skips are intra-form GATE logic.

---

## 4. Dependencies / open items

| Item | Blocks | Owner | Notes |
|---|---|---|---|
| Q31 IP_GROUP coded list decision | Form 8 (B3) | ASPSI | Default: keep alpha |
| Q159 → Q164 cross-section jump verified intentional | Form 29 → Form 30 | ASPSI | Honor source as printed until confirmed |
| Q147/Q156 med list length monitoring | Forms 28, 29 | Pilot | Convert to roster only if field reports 240-char overflow |

---

## 5. Next steps

1. Lay out Forms 1–8 first (FC + Geo + Capture ×2 + Consent + Patient Profile). Stable and inherits F1 patterns.
2. Build Section G/H payment-matrix forms (18–23) — one `_PAY_{code}` + `_PAY_{code}_AMT` pattern reused everywhere.
3. Build Section L terminator logic (Q162) — exercises form-level skip to CLOSING once; reuse for F4.
4. QA against [[F3-Skip-Logic-and-Validations]] §3–§4 before Designer sign-off.

---

**See also:** [[../Form-Layout-Principles]], [[F3-Skip-Logic-and-Validations]], [[../F1/F1-Form-Layout-Plan]], [[../F4/F4-Form-Layout-Plan]].
