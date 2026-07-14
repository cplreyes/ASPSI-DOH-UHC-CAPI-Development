---
project: UHC Survey Year 2 — CAPI Development
artifact: Shared Codebook (cross-instrument harmonization spec)
version: 0.8 (draft, 2026-07-14)
status: draft
owners: Carl Patrick L. Reyes (data programmer)
covers: F1 Facility Head, F2 Healthcare Worker (PWA), F3 Patient, F4 Household
---

# Shared Codebook — UHC Survey Year 2

**Purpose:** define canonical encodings for the small set of dimensions that cross instrument boundaries, plus the per-instrument source mappings the harmonization ETL applies to produce clean, joinable, analysis-ready output.

**Scope:** the 13 cross-instrument dimensions documented below. Everything else in each instrument is instrument-specific and stays in its native form.

**Source of truth:**
- F1 — `deliverables/CSPro/F1/FacilityHeadSurvey.dcf` + `deliverables/CSPro/F1/F1-Skip-Logic-and-Validations.md`
- F2 — `deliverables/F2/PWA/app/spec/F2-Spec.md` + `deliverables/F2/PWA/app/src/generated/items.ts`
- F3 — `deliverables/CSPro/F3/PatientSurvey.dcf` + `deliverables/CSPro/F3/F3-Skip-Logic-and-Validations.md`
- F4 — `deliverables/CSPro/F4/HouseholdSurvey.dcf` + `deliverables/CSPro/F4/F4-Skip-Logic-and-Validations.md`

**Audited 2026-04-25** against the live spec/dcf files. Per-instrument encodings reflect what's actually in the source today, not what the spec template suggests they should be.

---

## 0. Conventions

### 0.1 Canonical column naming in harmonized output

- **Per-instrument output**: `<instrument>_<questionId>` (e.g. `f1_q12`, `f2_q5`). Avoids cross-instrument collisions and keeps Q-numbers traceable to the printed questionnaire.
- **Shared dimensions**: short canonical names (`region_code`, `sex`, `age_years`, etc.) appear in all per-instrument outputs and in the cross-instrument `shared_dimensions.csv` join layer.
- **Instrument tag**: every harmonized row carries `_source_instrument` ∈ {`f1`, `f2`, `f3`, `f4`} so downstream concatenation is traceable.

### 0.2 Missing-value sentinels (Stata extended-missing)

| Concept | Stata code | Where it comes from |
|---|---|---|
| Skipped due to skip-logic (item hidden) | `.a` | CSPro `NOTAPPL`; PWA `undefined` (item filtered by `shouldShow`) |
| Refused | `.b` | CSPro `REFUSED`; **amount/continuous numeric fields: the value `-99` (#743)**; PWA: not currently captured (see open item §15) |
| Don't know | `.c` | Categorical: coded value `8` / `98` / `'I don't know'` (see per-dimension recodes); **amount/continuous numeric fields: the value `-98` (#743)** |
| Truly missing (data error) | `.` | Should be zero in clean output |

**Amount-field missing-value sentinels (#743, adopted 2026-06-23).** Continuous/amount numeric items (PHP amounts, etc.) cannot use a categorical `8`/`98`, so they carry **negative sentinels**: `-98` = Don't know → `.c`, `-99` = Refused → `.b`. Negatives are unambiguous (no real amount is < 0). The ETL must recode `-98`/`-99` on these fields to the Stata extended-missing codes above (and never sum them). F4 Section N expenditure piloted first (CSEntry device-test of typed-negative entry pending); fan-out to the remaining F4 amount fields (Q18 income, Q199 willingness-to-pay) + F1/F3 follows confirmation. **Retires** the prior in-range `99999999` "don't know" sentinel.

### 0.3 Output formats

The harmonization ETL emits, per instrument:
- `<instrument>_clean.csv` — UTF-8 CSV; missing as empty cell; categorical values as canonical labels (not codes)
- `<instrument>_clean.dta` — Stata 14 format with variable labels + value labels per the codebook
- `shared_dimensions.csv` — long-format table, one row per (instrument, respondent, dimension) for cross-instrument joins

---

## 1. Geographic identifiers (PSGC)

**Canonical encoding**

| Field | Type | Format |
|---|---|---|
| `region_code` | string | 2-digit PSA region code (e.g. `"05"` for Bicol) |
| `province_code` | string | 4-digit PSA province code (zero-padded; HUCs use the city code) |
| `city_mun_code` | string | 6-digit city/municipality code |
| `barangay_code` | string | 9-digit barangay code (PSGC standard) |

PSGC vintage: **PSA 2024 release — pinned and frozen for the engagement (§15.F resolved 2026-06-03).** All four instruments must consume the same vintage to avoid silent rollup drift.

**Per-instrument source mapping**

| Instrument | Source | Encoding | Recode rule |
|---|---|---|---|
| F1 | `REGION`, `PROVINCE_HUC`, `CITY_MUNICIPALITY`, `BARANGAY` (numeric, PSGC-cascaded via `PSGC-Cascade.apc`) | numeric, padded to canonical width | cast to string, left-pad with zeros to canonical width |
| F2 | **Not collected from respondent.** Geography is inherited from the chosen facility (`facility_id` → facility master list) | — | join on `facility_id` to populate geography |
| F3 | `P_REGION`, `P_PROVINCE_HUC`, `P_CITY_MUNICIPALITY`, `P_BARANGAY` (only for outpatient / home-visit cases; same PSGC cascade) | numeric, padded | cast to string + zero-pad |
| F4 | `REGION`, `PROVINCE_HUC`, `CITY_MUNICIPALITY`, `BARANGAY` (household location) | numeric, padded | cast to string + zero-pad |

**Alignment risk:** F1 / F3 / F4 all use the same `PSGC-Cascade.apc`, so within-CAPI alignment is automatic. **F2's geography is derived via the facility join** — if the F2 facility master list isn't synchronised with F1's facility list, geography rolls up wrong for HCWs. Mitigation: single facility master list, see §2.

---

## 2. Facility identifier

**Canonical encoding**

| Field | Type | Format |
|---|---|---|
| `facility_id` | string | Stable identifier from the facility master list |
| `facility_type` | string | One of: `RHU`, `CHO`, `Hospital_L1`, `Hospital_L2`, `Hospital_L3` |
| `facility_name` | string | Human-readable facility name |

The facility master list is the **single source** ASPSI must publish before fieldwork; all four instruments consume it. F2 already uses a placeholder list (replace with master list before production rollout).

**Per-instrument source mapping**

| Instrument | Source | Notes |
|---|---|---|
| F1 | **Case-key id-block** — `facility_id` = the first **9 digits** `REGION_CODE`+`PROVINCE_HUC_CODE`+`CITY_MUNICIPALITY_CODE`+`FACILITY_NO`. F1 = one row per facility head (`CASE_SEQ` = 001). | derive `facility_id` from the id-block; join to master list for type + name |
| F2 | `facility_id` (pre-filled from facility selection — **placeholder pending §15.G**), `facility_type`, `facility_name`; per-response `hcw_id` | 12-digit Respondent No is **derived at ETL** (decided 2026-06-04), not minted in-app — see §11. Gated on §15.G for the real facility block |
| F3 | **Case-key id-block** — facility is intrinsic to the F3 case key's first 9 digits (`F3_FACILITY_ID` **retired 2026-06-04**) | F3→F1 join on the shared 9 digits; join to master list for type + name |
| F4 | **Case-key id-block** (first 9 digits) + `F4_PARENT_F3_CASE_SEQ`(3) for the F4→F3 patient link | F4→F3 join on shared 9 digits + parent seq; join to master list |

**Case key (12-digit Respondent / Questionnaire Number) — adopted 2026-06-04.** All instruments now key on the decomposed 12-digit case key `RR-PP-MMM-FF-CCC` (5 ID items: `REGION_CODE`(2) · `PROVINCE_HUC_CODE`(2) · `CITY_MUNICIPALITY_CODE`(3) · `FACILITY_NO`(2) · `CASE_SEQ`(3)), per the adopted Questionnaire Numbering Convention. The first **9 digits are the facility**; the last 3 are the per-facility, per-instrument case sequence. This *supersedes* the earlier single 6-digit geography-free `QUESTIONNAIRE_NO` (§15.H). These are compact **within-parent** geographic codes — distinct from the full PSGC codes stored in the geographic data items (§1); both derive from the same PSA 2024 vintage.

**Alignment risk** (CRITICAL): every cross-instrument join keys off the **9-digit facility block**. F3→F1 and F4→F3 join on the shared first 9 digits (geography + facility number) — no separate facility-id field is needed (hence `F3_FACILITY_ID` was retired). **F2 remains the gap**: its `facility_id` is a placeholder until ASPSI publishes the master list (§15.G) mapping each facility to its `REGION_CODE`/`PROVINCE_HUC_CODE`/`CITY_MUNICIPALITY_CODE`/`FACILITY_NO` block. Until then, F2↔CAPI facility joins can't be verified.

---

## 3. Sex / sex at birth

**Canonical encoding**

| Code | Label |
|---|---|
| `1` | Male |
| `2` | Female |
| `.c` | Don't know (rare, F4 roster only) |

**Per-instrument source mapping**

| Instrument | Source | Current encoding | Recode |
|---|---|---|---|
| F1 | `Q4_SEX` | numeric `1` / `2` | passthrough |
| F2 | `Q3` | string `'Male'` / `'Female'` | `'Male' → 1`, `'Female' → 2` |
| F3 | `Q7_SEX` | numeric `1` / `2` | passthrough |
| F4 (respondent) | `Q3_SEX` | string with extra `'Other'` option | `'Male' → 1`, `'Female' → 2`, `'Other' → see §15` |
| F4 (roster) | `Q33_SEX` per member | numeric `1` / `2` | passthrough |

**Alignment risk** (CRITICAL — the textbook silent-failure case): four different shapes for the same concept. The ETL must apply the recode rules above; downstream code must not assume `sex == 'Male'` or `sex == 1` in the harmonized output — only the canonical codes should appear.

**Open item:** F4 respondent has an `'Other'` sex option that doesn't exist in F1/F2/F3. Decision needed (§15.A) — either map to a new canonical code `3`, or treat as `.c` don't-know, or carry as a separate `sex_other` flag. Affects analysis comparability.

---

## 4. Age

**Canonical encoding**

| Field | Type | Range |
|---|---|---|
| `age_years` | integer | 0–120 (truly missing → `.`; refused → `.b`; don't know → `.c`) |

**Per-instrument source mapping**

| Instrument | Source | Range | Recode |
|---|---|---|---|
| F1 | `Q3_AGE` | 18–90 | passthrough |
| F2 | `Q4` | 18–99 | passthrough |
| F3 | `Q6_AGE` | 0–120 | passthrough |
| F4 (respondent) | `Q2_1_AGE` (or derived from `Q2_BIRTH_YEAR`) | implicit ≥ 18 | passthrough; cross-check vs birth year |
| F4 (roster) | `Q32_AGE` per member | 0–120 | passthrough |

**Alignment risk:** range mismatch is intentional (F1 surveys facility heads who are working adults; F3/F4 include children). Don't force a single range. **Do** sanity-check at ETL time: F1 row with age < 18 or > 90 is a data error; F4 roster row with age > 120 is a data error.

---

## 5. Facility leadership role (F1 only)

> **Note**: this is its own dimension because F1 captures the facility head's *organizational* designation, not a clinical/healthcare role. F2 captures a different concept (HCW clinical discipline — see §6). F3/F4 capture employment status (see §7). They are NOT the same column with different encodings; they are three distinct dimensions.

**Canonical encoding (F1-scoped)**

| Code | Label |
|---|---|
| `01` | Rural / Urban Health Unit Head |
| `02` | Physician |
| `03` | Chief of Hospital |
| `04` | Medical Director |
| `05` | Hospital Administrator |
| `06` | Nurse |
| `07` | Municipal / City Health Officer |
| `08` | Medical Officer |
| `09` | Administrative Officer / Assistant |
| `10` | Midwife |
| `11` | Health Promotion / Nutrition Officer |

**Source**: F1 `Q2_FACILITY_ROLE` (numeric, length 2, zero-filled). Already in canonical shape — passthrough.

---

## 6. HCW clinical discipline (F2 only)

**Canonical encoding (F2-scoped)** — 16 string values from `Q5` value set, plus `Other (specify)` free text.

| Value | Notes |
|---|---|
| `Administrator`, `Physician/Doctor`, `Physician assistant`, `Nurse`, `Nursing assistant`, `Pharmacist/Dispenser`, `Midwife`, `Laboratory technician`, `Medical/ radiologic technologist`, `Health promotion officer`, `Nutrition action officer/ coordinator`, `Physical Therapist`, `Dentist`, `Dentist aide`, `Barangay Health Worker` | canonical strings, used as both label and code |
| `Other (specify)` | with companion free-text field `Q5_other` |

**Source**: F2 `Q5` (PWA single-select string enum) + `Q5_other` (specify text).

**Alignment risk**: F2 `Q5` and F1 `Q2_FACILITY_ROLE` partially overlap semantically (a Nurse appears in both lists) but the universes are different (F1 = facility head's role; F2 = any HCW's discipline). **Don't merge into one column.** Cross-instrument analysis joining F1 facility heads to F2 HCWs at the same facility uses `facility_id` as the join key, not role.

---

## 7. Employment status (F3, F4)

**Canonical encoding (F3 + F4)**

| Code | Label |
|---|---|
| `1` | Has permanent job / own business |
| `2` | Has short-term / seasonal / casual job |
| `3` | Worked different jobs day-to-day |
| `4` | Unemployed, looking |
| `5` | Unemployed, not looking |
| `6` | Studying |
| `7` | Retired |
| `8` | Don't know |
| `9` | Not applicable |

Plus an employment-class sub-question (private / government / self-employed / etc.) for codes `1`–`3`.

**Per-instrument source mapping**

| Instrument | Source | Notes |
|---|---|---|
| F3 | `Q16_EMPLOYMENT` (respondent) | per-respondent |
| F4 (respondent) | `Q12_EMPLOYMENT` | per-respondent |
| F4 (roster) | `Q41_EMPLOYMENT` per household member | per-member |

F3 and F4 already use identical codes — passthrough. F1 / F2 do not collect employment status; the column is `.a` (skipped / not applicable for instrument).

---

## 8. PhilHealth membership status

**Canonical encoding**

| Field | Codes | Notes |
|---|---|---|
| `philhealth_registered` | `1` Yes / `2` No / `8` Don't know | the gating question |
| `philhealth_member_category` | `01` Formal economy / `02` Informal economy / `03` Indigent / `04` Sponsored / `05` Lifetime member / `06` Senior citizen / `07` OFW / `08` Qualified dependent / `98` Don't know / `99` Other (specify) | only when registered = Yes |
| `philhealth_premium_paid` | `1` Yes / `2` No / `3` Don't pay premiums | only when registered = Yes |

**Per-instrument source mapping**

| Instrument | Source | Notes |
|---|---|---|
| F1 | not collected | `.a` skipped |
| F2 | not collected | `.a` skipped |
| F3 | `Q38_PHILHEALTH_REG`, `Q45_CATEGORY`, `Q48_PREMIUM_PAY` | passthrough |
| F4 (per member) | `Q45_PHILHEALTH_REG`, `Q46_MEMBER_CATEGORY`, `Q49_PREMIUM_PAY` | passthrough; per-member roster |

**Alignment**: F3 ↔ F4 are fully aligned. F1 / F2 don't collect this — that's intentional (F1 is facility-level, F2 is HCW-employment-context).

---

## 9. Informed consent

**Canonical encoding**

| Field | Codes | Notes |
|---|---|---|
| `consent_given` | `1` Yes / `2` No (refused / withdrew) | required for record retention |
| `consent_timestamp` | ISO 8601 datetime | when consent was recorded |

**Per-instrument source mapping**

| Instrument | Source | Notes |
|---|---|---|
| F1 | `CONSENT_GIVEN` (FIELD_CONTROL) | numeric `1` / `2`; if `2` → ENUM_RESULT = Refused, interview ends |
| F2 | not stored as a survey item — implicit click-through | refusal redirects out before any data is captured (see open item §15.B) |
| F3 | `CONSENT_GIVEN` (FIELD_CONTROL) ✓ verified 2026-04-25 | numeric `1` / `2`; same shape as F1 |
| F4 | `CONSENT_GIVEN` (FIELD_CONTROL) ✓ verified 2026-04-25 | numeric `1` / `2`; same shape as F1 |

**Alignment risk**: F1 / F3 / F4 all capture consent identically. **Only F2 PWA lacks an explicit consent field** — refusal in F2 means the user never reaches the form (no row created), so there's no audit trail of who declined.

**Open item §15.B (narrowed)**: should F2 add an explicit `consent_given` field for audit parity? Recommend yes — captures explicit refusal (instead of just "no row exists"), enables ethics-board audit symmetry, and is a small PWA change (a checkbox + a submission-payload field). F3 / F4 already aligned with F1.

---

## 10. Survey / submission date

**Canonical encoding**

| Field | Type | Format |
|---|---|---|
| `survey_started_at` | datetime (ISO 8601) | when interview/form started |
| `survey_submitted_at` | datetime (ISO 8601) | when interview/form ended (or final visit completed) |

**Per-instrument source mapping**

| Instrument | Source | Recode |
|---|---|---|
| F1 | `DATE_STARTED` (YYYYMMDD numeric) + `TIME_STARTED` (HHMMSS numeric) → `survey_started_at`; `DATE_FIRST_VISITED_THE_FACILITY` + `DATE_OF_FINAL_VISIT_TO_THE_FACILITY` for multi-visit; the final-visit date → `survey_submitted_at` | concatenate + parse to ISO; F1's multi-visit model means `survey_submitted_at` = final visit date |
| F2 | client-side timestamp at submit (PWA) + server-side receipt timestamp at Apps Script | use server-side receipt as `survey_submitted_at` for authoritative ordering |
| F3 | `DATE_STARTED` + `TIME_STARTED` (FIELD_CONTROL) ✓ verified 2026-04-25; multi-visit also supported via `DATE_FIRST_VISITED` + `DATE_FINAL_VISIT` | same recode as F1 |
| F4 | `DATE_STARTED` + `TIME_STARTED` (FIELD_CONTROL) ✓ verified 2026-04-25; multi-visit also supported via `DATE_FIRST_VISITED` + `DATE_FINAL_VISIT` | same recode as F1 |

**Alignment risk** (revised 2026-04-25): all three CAPI instruments (F1 / F3 / F4) support multi-visit interviews and capture both first-visit and final-visit dates. **Only F2 PWA is single-session** — its `survey_submitted_at` is one timestamp from the Apps Script receipt log. The asymmetry is intentional: a self-admin web form completed in one sitting doesn't need multi-visit semantics.

**Open item §15.C — RESOLVED 2026-04-25**: F3 and F4 dcfs both have `DATE_STARTED`, `TIME_STARTED`, `DATE_FIRST_VISITED`, and `DATE_FINAL_VISIT`. No new fields needed.

---

## 11. Interviewer ID / response source

**Canonical encoding**

| Field | Codes / format |
|---|---|
| `response_source` | `capi` (CSEntry-administered) / `pwa` (self-admin web) / `paper_encoded` (reserved for fallback) |
| `interviewer_id` | string (ASPSI enumerator roster ID; `null` for `pwa` rows) |
| `respondent_self_id` | string (PWA `hcw_id` from enrollment; `null` for `capi` rows) |

**Per-instrument source mapping**

| Instrument | Source | Notes |
|---|---|---|
| F1 | `INTERVIEWER_ID` (FIELD_CONTROL) | `response_source = 'capi'`; `respondent_self_id = null` |
| F2 | `hcw_id` (PWA enrollment, autoinjected into submitted payload) | `response_source = 'pwa'`; `interviewer_id = null` |
| F3 | `INTERVIEWER_ID` (FIELD_CONTROL) | `response_source = 'capi'` |
| F4 | `INTERVIEWER_ID` (FIELD_CONTROL) | `response_source = 'capi'` |

**Alignment**: clean — three concrete source-mode values cover all current and known-future cases.

**F2 12-digit Respondent Number — derived at ETL (decided 2026-06-04).** F2 is self-admin web (no paper questionnaire number to mint), and every response already carries `facility_id` + `hcw_id`. Rather than change the production PWA, the harmonization ETL composes the convention's 12-digit `RR-PP-MMM-FF-CCC` for each F2 row: **first 9 digits** = the `facility_id`'s id-block (`REGION_CODE`+`PROVINCE_HUC_CODE`+`CITY_MUNICIPALITY_CODE`+`FACILITY_NO`, looked up via the §15.G master list) + **`CASE_SEQ`(3)** = the HCW's stable per-facility roster index. Gated on §15.G for the real facility block — until ASPSI publishes the master list, F2 rows carry a placeholder `facility_id` and the derived composite is structurally valid but unverified. (This supersedes the adopted convention's Implementation Footprint item 5, which assumed in-app minting — the as-built F2 flow makes ETL derivation the cleaner, zero-risk path.)

---

## 12. Disposition / response status

> **Corrected 2026-07-14.** Earlier versions of this section (v0.2–v0.4) defined the canonical
> encoding as **AAPOR 3-digit codes** and stated that F1/F3/F4 carried an `AAPOR_DISPOSITION`
> item in `FIELD_CONTROL` — "✓ verified 2026-04-25". That was true when written and became
> false on **2026-06-12**, when the whole case-start block (`SURVEY_CODE`, `DATE_STARTED`,
> `TIME_STARTED`, `INTERVIEWER_ID`, `AAPOR_DISPOSITION`, `CONSENT_GIVEN`) was removed from all
> three instruments as **not on the April-20 paper Field Control form**. AAPOR was never
> requested by ASPSI or DOH and is not their vocabulary; it is not being reinstated here, and
> it has deliberately **not** been replaced with a different invented taxonomy.
>
> The canonical encoding below is now simply **what the instruments actually capture**.

**Canonical encoding** — the paper Field Control fields, verbatim.

`case_disposition` (from `FIELD_CONTROL.CASE_DISPOSITION`, numeric, length 1) — the only code
that is common to all three CAPI instruments and therefore the only safe cross-instrument key:

| Code | Label |
|---|---|
| `0` | In progress |
| `1` | Completed |
| `2` | Partial / not completed |

`result_of_visit` (from `FIELD_CONTROL.ENUM_RESULT_FIRST_VISIT` / `ENUM_RESULT_FINAL_VISIT`) —
**instrument-specific and NOT harmonised**, because the paper forms genuinely differ. Do not
recode across instruments without ASPSI sign-off:

| Instrument | Value set (verbatim) |
|---|---|
| F1 | `1` Completed · `2` Postponed · `3` Refused · `4` Incomplete · `5` **Replaced** |
| F3 | `1` Completed · `2` Completed at the Hospital · `3` Postponed · `4` Incomplete · `5` Completed at Home · `6` Withdraw Participation/Consent · `7` **Replaced** |
| F4 | `1` Completed · `2` Postponed · `3` Incomplete · `4` Withdraw Participation/Consent · `5` **Replaced** |

> `Replaced` (added 2026-07-14) is set by logic from `BREAKOFF` 5/6/7, never typed directly. Its code
> differs per instrument because the three lists have different lengths — so **count replacements on
> `BREAKOFF`, which is uniform across F1/F3/F4**, not on this column. See the Replacements block below.

**Per-instrument source mapping**

| Instrument | Source | Recode |
|---|---|---|
| F1 | `CASE_DISPOSITION` + `ENUM_RESULT_FIRST_VISIT` / `ENUM_RESULT_FINAL_VISIT` (FIELD_CONTROL) | passthrough |
| F2 | not captured as a survey item — derive at ETL from the joined distribution-list × submission-row state (rule below) | derive |
| F3 | `CASE_DISPOSITION` + `ENUM_RESULT_*` (FIELD_CONTROL) | passthrough |
| F4 | `CASE_DISPOSITION` + `ENUM_RESULT_*` (FIELD_CONTROL) | passthrough |

**F2 derivation rule** (F2 is self-administered; there is no enumerator and no visit):

| Observed state | `case_disposition` | Note |
|---|---|---|
| Submission row exists, `status='stored'` | `1` Completed | |
| Submission row exists, `status='refusal'` (consent declined, #825) | `2` Partial / not completed | F2 is the **only** instrument that records an explicit refusal |
| Draft exists, never submitted, last update <24h | `0` In progress | |
| Draft exists, last update ≥24h, or HCW enrolled with no draft | `2` Partial / not completed | cannot distinguish abandonment from non-contact — see the gap below |

### ✅ Replacements — RESOLVED 2026-07-14 (was a known gap)

This section previously recorded that response rates and replacement counts were **not derivable**:
no instrument had a non-contact code, F3/F4 had no doorstep-refusal code, and the field protocol was
understood to say *don't start a case* for a replaced unit — so a replaced unit left no trace.

**ASPSI (Marriz) corrected the protocol premise on 2026-07-14.** The SAAD convention is the opposite:
the enumerator **does** open a case for a unit that cannot be interviewed, marks it as such up front,
and a substitute is then drawn. Any unit that cannot be interviewed is replaced — the reason (refused
/ not found / ineligible) is recorded, but all of them are replacements.

`BREAKOFF` now carries that. It is the **same code list in F1, F3 and F4** — which is what makes a
cross-instrument query possible at all:

| `BREAKOFF` | Meaning | Interview started? | Replacement? |
|---|---|---|---|
| `1` | Continue interview | — | no |
| `2` | Respondent withdrew | yes | no |
| `3` | Postponed / reschedule | yes | **no** — revisited, not substituted |
| `4` | Stop — other (incomplete) | yes | no |
| `5` | Not interviewed — refused | **no** | **yes** |
| `6` | Not interviewed — not found | **no** | **yes** |
| `7` | Not interviewed — ineligible | **no** | **yes** |

```
replacements = count(BREAKOFF in 5, 6, 7)      -- per facility / enumerator / supervisor
```

Codes 5/6/7 route to the closing Result-of-Visit, set it to **Replaced**, set `CASE_DISPOSITION = 2`,
and end the case — so the case is created and **syncs**, which is the whole point. Count on `BREAKOFF`,
**not** on the Result-of-Visit code: `Replaced` is `5` in F1/F4 but `7` in F3, because the three Result
lists have different lengths. `BREAKOFF` is uniform.

**Curbstoning check (the reason this matters).** Replacement *share* per enumerator is now computable
and is surfaced in the Sync Dashboard's productivity panel. Use the share, never the raw count — a hard
catchment legitimately produces more replacements than an easy one. The dashboard flags ≥30% over ≥5
cases; below that denominator the rate is noise.

> [!warning] Applies to data collected AFTER the redeploy
> Codes 5/6/7 do not exist in any case collected before 2026-07-14. Historic R5/R6 cases will show
> zero replacements — that is *absence of the code*, not absence of replacements. Do not read a
> pre-redeploy zero as a real figure, and do not back-fill one.

**Response rate.** With refusal (5), non-contact (6) and ineligible (7) now distinguishable, a true
response rate becomes computable in principle (`completed ÷ eligible contacted`, excluding code 7 from
the denominator). It is **still not shippable today** — it needs post-redeploy field data first. Do not
manufacture a figure from pre-redeploy cases.

> [!note] Unused convention — a possible cross-check, not a source of truth
> `Field-Tablet-Sync-Configuration.md` documents a `CASE_SEQ` range convention (001–699 active /
> 700–899 replacement / 900–999 refused). It is **enforced nowhere** — no generator, no logic, no
> validation, no query references it, so nothing guarantees an enumerator follows it. `BREAKOFF` is the
> source of truth. If the range convention is ever enforced, the two counts should agree, and the
> disagreement would itself be a useful audit signal.

---

## 13. Language

**Canonical encoding**

| Field | Codes |
|---|---|
| `survey_language` | `en` / `fil` (extensible — ASPSI has more languages queued) |

**Per-instrument source mapping**

| Instrument | Source | Notes |
|---|---|---|
| F1 | not currently captured | implicit from CSPro form's `setlanguage()` call; **proposal: add `LANGUAGE_USED` to FIELD_CONTROL** (numeric `1`=en / `2`=fil; captured at submit via `getlanguage()`) |
| F2 | not currently captured as item | **Carl-owned change — to ship in F2 v1.2.0**: auto-inject `survey_language` from `useLocale()` value into the submission payload at submit time (single line addition to `App.handleSubmit`; backend response sheet adds the column) |
| F3 | not currently captured | same proposal as F1 |
| F4 | not currently captured | same proposal as F1 |

**Open item §15.E — PARTIALLY RESOLVED 2026-04-25**:
- **F2 implementation** is Carl-owned: ship `survey_language` capture as part of v1.2.0 (Round 3 batch). Field name: `survey_language` (string, values `'en'` / `'fil'`).
- **F1 / F3 / F4 implementation** still needs ASPSI sign-off — see ASPSI open items doc. Adding a field to FIELD_CONTROL is a small instrument-design change but should be confirmed with the instrument-design owner before Carl edits the dcfs.

---

## 14. Harmonization ETL — pseudocode sketch

```python
# Per instrument
def harmonize(instrument: str, raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df["_source_instrument"] = instrument

    # Apply per-dimension recodes (see §1–§13)
    df = recode_psgc(df, instrument)         # cast + zero-pad
    df = recode_facility(df, instrument)     # join to master list
    df = recode_sex(df, instrument)          # F2 string -> 1/2; F4 'Other' -> see §15.A
    df = recode_age(df, instrument)          # passthrough + range sanity check
    df = recode_role_dimensions(df, ...)     # split into 3 cols (§5/§6/§7)
    df = recode_philhealth(df, instrument)
    df = recode_consent(df, instrument)      # see §15.B for F2/F3/F4
    df = recode_dates(df, instrument)        # YYYYMMDD -> ISO 8601
    df = recode_response_source(df, instrument)
    df = recode_disposition(df, instrument)  # F2 derives from sync status (§15.D)
    df = recode_language(df, instrument)     # see §15.E

    # Stata extended-missing: NOTAPPL/REFUSED/DK/blank -> .a/.b/.c/.
    df = apply_missing_sentinels(df)

    # Column naming: prefix instrument
    df = df.rename(columns={c: f"{instrument}_{c}" for c in df.columns
                            if c not in CANONICAL_SHARED_COLS})
    return df

# Cross-instrument
def shared_dimensions_long(instruments: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """One row per (instrument, respondent_id, dimension)."""
    ...
```

The actual implementation lives in `deliverables/data-harmonization/etl/` (to be authored). Stata variable labels + value labels go in a paired `apply_stata_labels.do` (or built directly via pyreadstat).

---

## 15. Open items / decisions

### 15.0 Resolved 2026-04-25 (Carl-owned, no ASPSI input needed)

| # | Item | Resolution |
|---|---|---|
| **15.C** | Confirm F3/F4 explicit start/submit datetime fields | ✓ Verified — F3 and F4 dcfs both have `DATE_STARTED`, `TIME_STARTED`, `DATE_FIRST_VISITED`, `DATE_FINAL_VISIT`. Multi-visit semantics already supported. No new fields needed. |
| **15.D** | F2 disposition derivation strategy (was: "F2 AAPOR derivation strategy" — AAPOR dropped 2026-07-14, never an ASPSI requirement) | ✓ Defined ETL derivation rule over joined `(distribution_list × IndexedDB draft state × submission row)`. See §12 above for the full code-mapping table. Refusal capture deferred until §15.B is decided. |
| **15.E (F2 portion)** | F2 `survey_language` capture | ✓ Will ship as part of F2 v1.2.0 — `App.handleSubmit` auto-injects `useLocale()` value into submission payload; backend response sheet adds column. No ASPSI sign-off needed for F2's own field. |

### 15.1 Resolved 2026-06-03 (Carl build-decisions; ASPSI to confirm/ratify where noted)

| # | Item | Resolution |
|---|---|---|
| **15.A** | F4 `Q3_SEX` allows `'Other'` (F1/F2/F3 don't) | **Carry as a separate `sex_other` flag** — keep canonical `sex` to the shared domain; don't collapse 'Other' into the 3-code set. |
| **15.B** | F2 has no consent data field | **Add explicit `consent_given` to F2.** ✓ **Built 2026-06-03** (PR #362): `App.handleSubmit` injects `consent_given = 1` into the submission values (stored in `values_json` like `survey_language`; submitted ⟹ consent). ETL extracts to canonical `consent_given` (§9). No backend column — the response writer is header-mapped. |
| **15.E (F1/F3/F4)** | `LANGUAGE_USED` in FIELD_CONTROL | **Add `LANGUAGE_USED`** across the three CAPI instruments. ✓ **Built 2026-06-03**: added to the shared + F1-local `build_field_control`; written via `getlanguage()` in each instrument's `*_FF` preproc. Regenerated, pre-flight clean (the single fmf "orphan" is the logic-written field itself — no form placement needed). |
| **15.F** | PSGC vintage | **Pin PSA 2024** release and freeze for the engagement. |
| **15.H** | Case key ≡ facility linkage | **Superseded 2026-06-04 by the 12-digit decomposed case key** (`RR-PP-MMM-FF-CCC`; adopted Questionnaire Numbering Convention). `facility_id` = the case key's first 9 digits (geography + facility number) — *not* the old 6-digit geography-free `QUESTIONNAIRE_NO`. F1/F3/F4 dcfs rebuilt + re-registered in CSWeb 2026-06-04. ASPSI still confirms the facility↔id-block mapping against the published master list (§15.G). |

> **15.B and 15.E built 2026-06-03** (the field-adds). The rest are decisions of record that flow into the ETL/codebook.

### 15.2 Still pending — ASPSI to publish (held)

| # | Item | Decision needed | Owner |
|---|---|---|---|
| **15.G** | Facility master list publication | ASPSI publishes the single canonical list — the 6-digit `facility_id` source that §15.H assumes; F2 PWA must consume it (currently a placeholder). | ASPSI |
| **15.J** | OOP / financial-protection shared dimension | Add a cross-instrument out-of-pocket / catastrophic-health-expenditure dimension (F3 patient + F4 household). Source = the F3 `Q<n>_PAY_ROSTER` child tables (per case, sum `_PAY_AMT` over rows where `_PAY_SRC` = out-of-pocket code) + the **F4 Section N expenditure rosters** (converted 2026-07-03, CHANGELOG v0.6 — sum `_PURCHASED_PHP` + `_INKIND_PHP` over each roster's rows where `_CONSUMED` = 1, excluding the `-98`/`-99` DK/refused sentinels). Not yet in §1–§13. Added 2026-06-20 after the capi-multiselect roster fan-out (CHANGELOG v0.5). | Carl / analysis |

See `open-items-for-aspsi.md` for context.

---

## 16. Versioning

This codebook is **version 0.6** (see CHANGELOG) — drafted 2026-04-25 from current spec/dcf state. Subsequent revisions track:
- Each open item resolution (15.A–15.H)
- Each instrument spec change that touches a shared dimension (e.g. F1 sign-off may add or rename FIELD_CONTROL items)
- Each new instrument added to the engagement

Bump the `version` field at the top with every substantive change, and record the change in a CHANGELOG section appended below.

### CHANGELOG

| Version | Date | Change |
|---|---|---|
| 0.7 | 2026-07-14 | **§12 Disposition corrected — AAPOR removed.** v0.2–v0.6 defined the canonical disposition encoding as **AAPOR 3-digit codes** and recorded `AAPOR_DISPOSITION` (FIELD_CONTROL) as a live passthrough field in F1/F3/F4, "✓ verified 2026-04-25". That verification was correct on the day; the field was **removed from all three instruments on 2026-06-12** (together with the rest of the unrequested case-start block: `SURVEY_CODE`, `DATE_STARTED`, `TIME_STARTED`, `INTERVIEWER_ID`, `CONSENT_GIVEN`) as **not on the April-20 paper Field Control form**, and the codebook was never updated — so §12 documented a variable that does not exist. AAPOR was never an ASPSI or DOH requirement and is not their vocabulary; it has been dropped rather than reinstated, and deliberately **not** swapped for another invented taxonomy. §12 now documents only what the instruments actually capture: `CASE_DISPOSITION` (0/1/2) as the sole cross-instrument key, plus the **unharmonised, instrument-specific** Result-of-Visit value sets. **New, explicit gap recorded in §12:** no CAPI instrument has a non-contact code, F3/F4 have no doorstep-refusal code, and the field protocol tells enumerators not to start a case for a replaced unit — so true response rates and replacement counts are **not derivable**, which removes the standard curbstoning check. Closing that is an ASPSI/DOH decision on the paper form, not a code change. |
| 0.6 | 2026-07-03 | **F4 Section N expenditure matrices → Option-C rosters (LIVE, F4 v1.1.0 on CSWeb).** Every WHO/SHA recall block flattened from per-question flat triplets (`Q<n>_CONSUMED`/`_PURCHASED_PHP`/`_INKIND_PHP`) to fixed-occurrence **repeating-record rosters**; the flat `Q144_*`..`Q156_*` and `Q160_*`..`Q184_*` field names **no longer exist in the DCF**. Each roster row carries generic `N_<blk>_ITEM` (auto-filled with the paper item label, e.g. `"164. Telephone…"` — so the Q-number is preserved *in the stored label*), `N_<blk>_CONSUMED`, `N_<blk>_PURCHASED_PHP`, `N_<blk>_INKIND_PHP`. **Flat→roster occurrence crosswalk** (occurrence *k* ↔ retired `Q<n>`, position-based, `occ k = items_list[k-1]` in `generate_dcf.py`): `N_FOOD_ROSTER` (rec V) occ 1–13 ↔ Q144–Q156; `N_NF1M_ROSTER` (W, "last month") occ 1–8 ↔ Q160–Q167; `N_NF6M_ROSTER` (X, "6 months") occ 1–2 ↔ Q168–Q169; `N_NF12M_ROSTER` (Y, "12 months") occ 1–5 ↔ Q170–Q174; `N_H12M_ROSTER` (1) occ 1–2 ↔ Q175–Q176; `N_H6M_ROSTER` (3) occ 1–4 ↔ Q178–Q181; `N_H1M_ROSTER` (5) occ 1–2 ↔ Q183–Q184. **Still flat** (single columns, record P `N_HOUSEHOLD_EXPENDITURES`): `Q157_FOOD_SUBTOTAL_TOTAL_PHP`, `Q158_RESTAURANT_*`, `Q159_SMOKING_TOBACCO_*`; the health subtotals `Q177`/`Q182`/`Q185_*_TOTAL_PHP` are their own single-field records (letters 2/4/6), CAPI-computed over the adjacent roster (sum `_CONSUMED`=1 rows, exclude `-98`/`-99`). **Downstream impact** (same shape as the F3 v0.5 note): (a) column-discovery ETL (`etl/transform.py`, `extract_csweb.py`) is **UNAFFECTED** — the new roster child tables are dumped automatically; (b) **15.J OOP/CHE** now sums the F4 roster rows (see 15.J), not flat `Q<n>_*_PHP` columns (gone); (c) any analyst join to printed item numbers uses the crosswalk above (or reads the Q-number out of the stored `N_<blk>_ITEM` label). Source of truth = `deliverables/CSPro/F4/generate_dcf.py` / `generate_apc.py`. |
| 0.7 | 2026-07-06 | **F4 Q158/Q159 rosterized → `N_WKOTH_ROSTER` (fix #832/#833, F4 v1.3.0).** The last two flat Section N weekly singles moved out of record P `N_HOUSEHOLD_EXPENDITURES` into a new 2-row roster **`N_WKOTH_ROSTER`** (record type 7): `N_WKOTH_ITEM`/`_CONSUMED`/`_PURCHASED_PHP`/`_INKIND_PHP`, **occ 1 = restaurant** (retired `Q158_RESTAURANT_*`), **occ 2 = tobacco** (retired `Q159_SMOKING_TOBACCO_*`). Reason: on a flat DisplayTogether form CSEntry *displayed* typed amounts but did not *commit* them (tester #832/#833) — the roster grid commits, the flat form does not. **Record P now holds ONLY `Q157_FOOD_SUBTOTAL_TOTAL_PHP`.** Downstream: 15.J OOP/CHE also sums the N_WKOTH rows (`_PURCHASED_PHP`+`_INKIND_PHP` where `_CONSUMED`=1, excl `-98`/`-99`); the flat `Q158_*`/`Q159_*` columns are gone. Dict change → hub redeployed. Source of truth = `generate_dcf.py`/`generate_apc.py`. |
| 0.1 | 2026-04-25 | Initial draft. Covers F1 / F2 / F3 / F4. Identifies 8 open items. Aligned to current spec/dcf state. |
| 0.2 | 2026-04-25 | Corrections after deeper dcf grep: F3 + F4 dcfs DO have `CONSENT_GIVEN`, `AAPOR_DISPOSITION`, `DATE_STARTED`/`TIME_STARTED`, and `DATE_FIRST_VISITED`/`DATE_FINAL_VISIT` (initial v0.1 audit was overly pessimistic on these). 15.C closed. 15.D resolved with ETL derivation rule for F2 disposition. 15.E split into Carl-owned F2 portion (resolved — ships in v1.2.0) and ASPSI-owned F1/F3/F4 portion (pending). 15.B narrowed to F2 only (F3/F4 already capture consent). Open items shrunk from 8 to 6 (5 ASPSI-owned + 1 mixed Carl/ASPSI). Stakeholder-facing open-items doc created at `open-items-for-aspsi.md`. |
| 0.3 | 2026-06-04 | **12-digit case-key alignment.** Adopted the decomposed `RR-PP-MMM-FF-CCC` Questionnaire / Respondent Number (5 ID items) across F1/F3/F4 — dcfs rebuilt + re-registered in CSWeb. `facility_id` is now the case key's first 9 digits, *superseding* §15.H's 6-digit geography-free assumption. `F3_FACILITY_ID` retired; `F4_PARENT_F3_CASE_SEQ` added. §1 PSGC vintage pinned to PSA 2024 (§15.F). F2 case-ID issuer still gated on the facility master list (§15.G). |
| 0.5 | 2026-06-20 | **F3 cost-matrix → roster restructure (capi-multiselect fan-out).** The F3 out-of-pocket/payment matrices were converted from flat `Q<n>_PAY_##` + per-source `_AMT` fields to **CheckBox + repeating-record rosters**: Q92/Q94/Q96/Q97.1(`Q971`)/Q97.2(`Q972`)/Q98 (Sec G) + Q107/Q109/Q112/Q113 (Sec H). Each is now its own breakout child table `Q<n>_PAY_ROSTER` with `Q<n>_PAY_LINE` (occurrence), `Q<n>_PAY_SRC` (source code; `01` = out-of-pocket, etc.), `Q<n>_PAY_AMT` (peso amount). **Downstream impact:** (a) the shared-dimension ETL skeleton (`etl/transform.py`) is **UNAFFECTED** — it is column-discovery-based and never referenced the cost fields, and `extract_csweb.py` dumps *every* breakout table, so the new roster tables are captured automatically; (b) **FUTURE financial-protection / catastrophic-health-expenditure analysis** must derive per-case out-of-pocket by **summing `Q<n>_PAY_AMT` over the `Q<n>_PAY_ROSTER` rows where `Q<n>_PAY_SRC` = the out-of-pocket code(s)** — NOT by reading a flat `Q<n>_PAY_01_AMT` column (those are gone). This mirrors the in-instrument `q<n>_oop()` PROC GLOBAL helpers; **new open item 15.J: add an OOP / financial-protection shared dimension** (cross-instrument F3 patient + F4 household), currently absent from §1–§13, with the roster as its source shape; (c) **F4 cost matrices remain flat** — convert in a later round for symmetry. Skip routing fix logged: F3 Q89→Q90 (#688) inverted to correct routing (no codebook impact). |
| 0.4 | 2026-06-12 | **As-built drift audit from the first ETL dry-run** (skeleton at `etl/`, run against the 4 live desk-test cases in the CSWeb breakout DBs — see `etl/README.md` + etl-spec v0.2). Findings vs the rebuilt June dcfs: **(a) §10 stale** — `DATE_STARTED`/`TIME_STARTED` no longer exist; as-built capture is `DATE_FIRST_VISITED`/`DATE_FINAL_VISIT` (F1: `…_THE_FACILITY` names) + visit counts/results; **no time-of-day is captured** — `survey_started_at`/`survey_submitted_at` recodes are date-only. **(b) §11 stale** — `INTERVIEWER_ID` no longer exists; as-built has free-text `ENUMERATOR_S_NAME` (+ team-leader/validated-by/edited-by names). Codebook canon expects roster IDs → **new open item 15.I: restore an enumerator roster-ID item or redefine §11 to name-matching** (ASPSI/instrument decision). **(c) §9 partially stale** — no explicit `CONSENT_GIVEN` boolean in any CAPI instrument's `A_INFORMED_CONSENT` record (the v0.2 claim no longer holds post-rebuild); consent appears enforced by the consent-terminator flow (refusals never saved). Decide: re-add the explicit item (audit-trail parity, mirrors §15.B for F2) or codify implicit-consent-by-presence. **(d) §13/§15.E CAPI portion RESOLVED as-built** — `LANGUAGE_USED` exists in `FIELD_CONTROL` on F1/F3/F4. **(e) §1/§2 operational rule** — numeric-entered keys and PSGC items lose leading zeros in the store; the ETL zero-pads to canonical widths (12-digit key / 10-digit PSGC) before any join or slice (etl-spec §2.1 caveat 2). Extract mechanism decided: CSWeb breakout DBs (etl-spec v0.2 §2.1). |
