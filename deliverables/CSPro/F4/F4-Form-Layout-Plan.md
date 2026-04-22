---
type: spec
project: ASPSI-DOH-CAPI-CSPro-Development
deliverable: F4 Household Survey — CAPI form-layout plan
date_created: 2026-04-21
status: draft
source_dcf: deliverables/CSPro/F4/HouseholdSurvey.dcf
source_spec: deliverables/CSPro/F4/F4-Skip-Logic-and-Validations.md
inherits: deliverables/CSPro/Form-Layout-Principles.md
tags: [cspro, capi, fmf, form-layout, f4, household]
---

# F4 Household Survey — Form-Layout Plan

**Scope:** section-by-section form inventory for `HouseholdSurvey.fmf`, mapping each DCF record to concrete CSEntry forms. Built on top of [[../Form-Layout-Principles]] — read that first.

**Source DCF:** 22 records / 618 items (Apr 21 build), covering 202 source questions, 17 sections (A–Q).
**Source spec:** [[F4-Skip-Logic-and-Validations]] for gates, skips, validations, and cross-section routing.

**Schema status (verified 2026-04-21):** `C_HOUSEHOLD_ROSTER` already emits `max_occurs=20` with `MEMBER_LINE_NO` as id-item (`generate_dcf.py:487`, `HouseholdSurvey.dcf:2836`). `J_HEALTH_SEEKING` is intentionally respondent-level (`max_occurs=1`) per the Apr 20 source rephrasing to singular "you/your household member" (`generate_dcf.py:984–989`). No schema patch needed — the plan below aligns with the emitted DCF.

**Key differences from F1 / F3:**
- Household-level roster: `C_HOUSEHOLD_ROSTER` enumerates all HH members; Section J (health-seeking) loops over them.
- `C_HH_PRIVATE_INS_GATE` is a separate non-repeating record for Q47 (HH-level private-insurance gate), isolated from the per-member loop.
- Sections H (PhilHealth) and J (health-seeking) are **respondent-level non-repeating** per the Apr 20 restructure — H applies to the respondent, J was refactored per ASPSI's "respondent-only" reading.
- One verification photo per case (`REC_CASE_VERIFICATION`, type Z). No patient-home GPS distinction — households are interviewed at one location.
- Bill-recall chain (Q140→Q141→Q141.1→Q142→Q143) in Section M is gated at the whole-section level by Q129 (in Section L).
- Section N is the WHO household-expenditure grid (~42 items), three-column pattern per item: `_CONSUMED` / `_PURCHASED_PHP` / `_INKIND_PHP`.

---

## 1. Record-to-form map (summary)

| # | Record (DCF) | Type / Occ | Form(s) | Notes |
|---|---|---|---|---|
| 1 | `HOUSEHOLDSURVEY_REC` | 1 | (container) | — |
| 2 | `FIELD_CONTROL` | A (1) | 1 form | Metadata, AAPOR, consent |
| 3 | `HOUSEHOLD_GEO_ID` | B (1) | 1 form | PSGC cascade |
| 4 | `REC_CASE_VERIFICATION` | Z (off-form) | Trigger on 1 form | GPS + photo |
| 5 | `A_INFORMED_CONSENT` | C (1) | 1 form | — |
| 6 | `B_RESPONDENT_PROFILE` | D (1) | 3 forms | Demographics + disability + income |
| 7 | `C_HOUSEHOLD_ROSTER` | E (rpt ≤ 20) | 1 roster form | One member per row; `MEMBER_LINE_NO` id-item |
| 8 | `C_HH_PRIVATE_INS_GATE` | F (1) | 1 form | Q47 HH-level gate |
| 9 | `D_UHC_AWARENESS` | G (1) | 2 forms | — |
| 10 | `E_YAKAP_KONSULTA` | H (1) | 2 forms | — |
| 11 | `F_BUCAS_AWARENESS` | (1) | 1 form | — |
| 12 | `G_ACCESS_MEDICINES` | I (1) | 2 forms | GAMOT |
| 13 | `H_PHILHEALTH_REG` | J (1, respondent) | 2 forms | Non-repeating per Apr 20 |
| 14 | `I_PRIMARY_CARE` | K (1) | 2 forms | — |
| 15 | `J_HEALTH_SEEKING` | L (1, respondent) | 1 form | Respondent-level per Apr 20 source rephrasing |
| 16 | `K_REFERRALS` | M (1) | 1 form | — |
| 17 | `L_NBB_AWARENESS` | N (1) | 1 form | Q129 lives here — gates Section M |
| 18 | `M_ZBB_MAIFIP_BILL` | O (1) | 3 forms | Bill-recall chain + ZBB/MAIFIP |
| 19 | `N_HOUSEHOLD_EXPENDITURES` | P (1) | 6 forms | WHO grid, ~42 items × 3-col pattern |
| 20 | `O_SOURCES_OF_FUNDS` | Q (1) | 1 form | — |
| 21 | `P_FINANCIAL_RISK` | R (1) | 2 forms | Distress-financing |
| 22 | `Q_FINANCIAL_ANXIETY` | S (1) | 1 form | Q199 WTP + Q202 worry reasons |
| — | Closing disposition | — | 1 form | — |

**Total: ~35 forms** (Section N expenditure grid is the single largest driver).

---

## 2. Form-by-form plan — key forms

### Form 1 — `FC_METADATA` (FIELD_CONTROL)

Same shape as F1/F3 Form 1. Consent = No → jump to closing.

### Form 2 — `FC_GEO` (PSGC cascade)

Standard PSGC cascade via `shared/PSGC-Cascade.apc`. No F1-linkage needed (F4 is HH-sampled, not facility-sampled).

### Form 3 — `FC_CAPTURE` (GPS + verification photo)

Single capture form. One trigger each for GPS and photo. Photo filename pattern: `case-{QUESTIONNAIRE_NO}-verification.jpg`.

### Form 4 — `A_CONSENT` (Section A — Informed Consent)

Respondent name, witness name/address/tel, consent signed date. Contents live in `FIELD_CONTROL` via `build_field_control()`; Form 4 surfaces them for signature step.

### Forms 5–7 — Section B (Respondent Profile, Q1–Q18)

| Form | Label | Q range | Content |
|---|---|---|---|
| 5 | `B1_DEMOGRAPHICS` | Q1–Q14 | Name, Q2 birth month/year + Q2.1 age (HARD consistency), sex, civil, education, employment |
| 6 | `B2_DISABILITY` | (within B) | Disability identity |
| 7 | `B3_INCOME_HH` | Q15–Q18 | IP group (alpha), Q19 HH size (drives roster-count check), Q18 amount↔bracket HARD |

### Form 8 — `C_ROSTER` (Household roster — REPEATING)

One row per household member, grid columns:

| Col | Field | Notes |
|---|---|---|
| 1 | `MEMBER_LINE_NO` | Auto-increment, id-item |
| 2 | `MEMBER_NAME` | Single-line |
| 3 | Age | Numpad |
| 4 | Sex | Radio (M/F) compressed |
| 5 | Relationship to respondent | Dropdown |
| 6 | Education level | Dropdown (compact codes) |
| 7 | Employment | Dropdown |
| … | Q30–Q46, Q48–Q50 per member | per-member insurance, work, etc. |

**Form rule:** roster scrolls alone (Principles §1.3, §8). Add/remove row controls pinned at top.
**Validation:** `count(C_HOUSEHOLD_ROSTER) = Q19_HH_SIZE_TOTAL` HARD, enforced in roster `postproc`.

### Form 9 — `C_GATE` (Q47 HH private-insurance gate)

Single form, single radio. Q47 HH-level answer.

### Forms 10–11 — Section D (UHC Awareness)

Two forms, split by topic.

### Forms 12–13 — Section E (YAKAP / Konsulta)

Two forms. Similar skip-tree to F1 Section D but HH-scoped.

### Form 14 — `F_BUCAS` (Section F — BUCAS Awareness)

Single form.

### Forms 15–16 — Section G (Access to Medicines, GAMOT)

Two forms; Q-specific med-list handling similar to F3 Section K.

### Forms 17–18 — Section H (PhilHealth Registration, respondent-level)

Two forms. Non-repeating — applies to respondent only.

### Forms 19–20 — Section I (Primary Care)

Two forms.

### Form 21 — `J_HEALTH_SEEKING` (Section J — respondent-level)

Single form, respondent-only per the Apr 20 source rephrasing. Q101 checkup frequency, Q102 visit reason select-all, Q103 care-type select-all, Q104 preventive Y/N, Q105 forgone-care gate, Q106 why-not select-all (Q105 = Yes only), Q107 other-actions select-all. Q105 = No → skip Q106 (intra-form gate).

### Form 22 — `K_REFERRALS` (Section K)

Single form.

### Form 23 — `L_NBB_AWARENESS` (Section L — includes Q129 gate for Section M)

Q129 = No → skip Forms 24–26 (Section M). Form-level jump.

### Forms 24–26 — Section M (ZBB / MAIFIP / Bill-recall chain)

| Form | Label | Content |
|---|---|---|
| 24 | `M1_ZBB_MAIFIP` | ZBB + MAIFIP awareness/experience |
| 25 | `M2_BILL_RECALL_1` | Q140 recall breakdown → Q141 bill items + Q141.1 no-receipt amt (intra-form gate) |
| 26 | `M3_BILL_RECALL_2` | Q142 recall payment → Q143 how paid (intra-form gate) |

**Bill-recall chain rules:** Q140 = No → Q141/Q141.1 disabled. Q142 = No → Q143 disabled. All intra-form gating.

### Forms 27–32 — Section N (Household Expenditures — WHO grid)

42 expenditure items × 3-column pattern = ~126 fields; well beyond a single form. Split by WHO panel grouping (food / housing / utilities / health / education / other):

| Form | Label | Panel | Items |
|---|---|---|---|
| 27 | `N1_FOOD` | Food & beverage | ~10 items |
| 28 | `N2_HOUSING` | Housing & utilities | ~6 items |
| 29 | `N3_TRANSPORT` | Transport & comms | ~6 items |
| 30 | `N4_HEALTH` | Health-related | ~8 items |
| 31 | `N5_EDUC_OTHER` | Education + other | ~8 items |
| 32 | `N6_SUBTOTALS` | Q157 / Q177 / Q182 / Q185 auto-subtotals | Read-only, computed in `postproc` |

**Grid layout per item (rows):** `_CONSUMED` radio (Y/N) | `_PURCHASED_PHP` numpad | `_INKIND_PHP` numpad — three controls on one row, two-column layout (label left, controls right). Gate: `_CONSUMED = No` → both PHP fields = 0 (HARD, enforced in field `postproc`).

**Row budget per N-form:** keep item count ≤ 10 per form to stay within the no-scroll ceiling even with 3-column layout.

### Form 33 — `O_FUNDS` (Section O)

Single form.

### Forms 34–35 — Section P (Financial Risk, distress-financing)

Two forms split by distress-financing subsection.

### Form 36 — `Q_ANXIETY` (Section Q — Financial Anxiety)

Q199 WTP amount, Q202 worry-reasons select-all (3 options + `_OTHER_TXT`).

### Form 37 — `CLOSING`

AAPOR disposition, notes, submit.

---

## 3. Form order (tab order)

```
1   FC_METADATA
2   FC_GEO
3   FC_CAPTURE
4   A_CONSENT
5–7 B1, B2, B3 (Respondent profile)
8   C_ROSTER (repeating — scrolls alone)
9   C_GATE (Q47 HH-level)
10–11  D1, D2 (UHC Awareness)
12–13  E1, E2 (YAKAP/Konsulta)
14     F_BUCAS
15–16  G1, G2 (GAMOT)
17–18  H1, H2 (PhilHealth, respondent-level)
19–20  I1, I2 (Primary care)
21     J (Health-seeking — respondent-level)
22     K (Referrals)
23     L_NBB_AWARENESS (incl. Q129 → Section M gate)
24–26  M1, M2, M3 (ZBB/MAIFIP/Bill-recall)
27–32  N1–N6 (Expenditure grid + subtotals)
33     O (Sources of funds)
34–35  P1, P2 (Financial risk)
36     Q (Financial anxiety)
37     CLOSING
```

**Form-level skips:**
- Consent = No (Form 1) → Form 37.
- Q129 = No (Form 23) → skip Forms 24–26, proceed to Form 27.

All other skips are intra-form GATE logic.

---

## 4. Dependencies / open items

| Item | Blocks | Owner | Notes |
|---|---|---|---|
| Q15 IP_GROUP coded list decision | Form 7 | ASPSI | Default: keep alpha |
| Q202 worry-reasons option count | Form 36 | Verify source | Currently 3 options + `_OTHER_TXT` |

---

## 5. Next steps

1. Lay out Forms 1–7 first (FC + Geo + Capture + Consent + Respondent profile). Stable.
2. Build Form 8 roster (first repeating-record form across all instruments) — exercise the Principles §8 roster pattern; reuse for any future F1 secondary-data rosters.
3. Build Sections M and N — these are F4's hardest layout challenges (bill-recall chain + WHO grid).
4. QA against [[F4-Skip-Logic-and-Validations]] §3–§4 before Designer sign-off.

---

**See also:** [[../Form-Layout-Principles]], [[F4-Skip-Logic-and-Validations]], [[../F1/F1-Form-Layout-Plan]], [[../F3/F3-Form-Layout-Plan]].
