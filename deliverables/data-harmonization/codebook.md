---
project: UHC Survey Year 2 — CAPI Development
artifact: Shared Codebook (cross-instrument harmonization spec)
version: 0.1 (draft, 2026-04-25)
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
| Refused | `.b` | CSPro `REFUSED`; PWA: not currently captured (see open item §15) |
| Don't know | `.c` | Coded value `8` / `'I don't know'` / similar — see per-dimension recodes |
| Truly missing (data error) | `.` | Should be zero in clean output |

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

PSGC vintage: **PSA 2023Q4 (or whichever vintage ASPSI standardises on — see §15 open items).** All four instruments must consume the same vintage to avoid silent rollup drift.

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
| F1 | `QUESTIONNAIRE_NO` (in FIELD_CONTROL); facility identity is implicit since F1 = one row per facility | use `QUESTIONNAIRE_NO` as the canonical `facility_id` and join to master list for type + name |
| F2 | `facility_id`, `facility_type`, `facility_name` (pre-filled from facility selection) | already in the canonical shape |
| F3 | `F3_FACILITY_ID` (pre-filled; hard consistency check enforces region match against F1 `QUESTIONNAIRE_NO`) | join to master list for type + name |
| F4 | `HH_LISTING_NO` (tied to the listing facility); facility itself joined via the listing form output | join to master list |

**Alignment risk** (CRITICAL): every cross-instrument join keys off `facility_id`. If F1's `QUESTIONNAIRE_NO` schema differs from the facility master list's id schema, every join fails silently. **Mitigation**: F1's QUESTIONNAIRE_NO must equal the master list facility_id, enforced at instrument-design time, not ETL time.

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
| F3 | not found in F3 spec / dcf grep | gate is procedural; consent not captured as data field (see §15.B) |
| F4 | not found in F4 spec / dcf grep | gate is procedural; consent not captured as data field (see §15.B) |

**Alignment risk**: only F1 has an auditable consent record. Others treat consent as a precondition for the row to exist. For ethics-board audit purposes, this asymmetry is awkward.

**Open item §15.B**: should F2 / F3 / F4 add an explicit `consent_given` field? Recommend yes — adds one item, gives audit parity with F1, and lets analysts filter on consent without scanning external logs.

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
| F1 | `DATE_STARTED` (YYYYMMDD numeric) + `TIME_STARTED` (HHMMSS numeric) → `survey_started_at`; `DATE_OF_FINAL_VISIT_TO_THE_FACILITY` + visit time → `survey_submitted_at` | concatenate + parse to ISO; F1's multi-visit model means `survey_submitted_at` = final visit date |
| F2 | client-side timestamp at submit (PWA) + server-side receipt timestamp at Apps Script | use server-side receipt as `survey_submitted_at` for authoritative ordering |
| F3 | not found in F3 dcf grep — see §15.C | (assume backend submission log; needs verification) |
| F4 | not found in F4 dcf grep — see §15.C | (assume backend submission log; needs verification) |

**Alignment risk**: F1 uniquely supports multi-visit interviews (revisit a facility days later). F2 / F3 / F4 are single-session. Treat F1's `survey_submitted_at` as "final-visit date" semantically; treat F2 / F3 / F4's as "single-session submit date".

**Open item §15.C**: confirm F3 / F4 dcf actually has explicit start/submit datetime fields. The audit found no grep hits — may be implicit only.

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

---

## 12. Disposition / response status

**Canonical encoding** — AAPOR 3-digit codes:

| Code | Label |
|---|---|
| `000` | In progress |
| `110` | Complete |
| `120` | Partial / break-off |
| `210` | Refusal — respondent |
| `211` | Refusal — gatekeeper / household |
| `220` | Non-contact |
| `230` | Other eligible non-interview |
| `310` | Unknown eligibility — facility / household |
| `320` | Unknown eligibility — respondent |
| `410` | Not eligible |
| `450` | Other not eligible |

**Per-instrument source mapping**

| Instrument | Source | Recode |
|---|---|---|
| F1 | `AAPOR_DISPOSITION` (FIELD_CONTROL) | passthrough |
| F2 | not currently captured — only implicit `submitted` vs `pending_sync` (see §15.D) | derive from submission status: `synced` → `110`; `pending_sync` for >48h → `120`; abandoned draft → `220` |
| F3 | assumed `AAPOR_DISPOSITION`; verify in dcf | passthrough |
| F4 | assumed `AAPOR_DISPOSITION`; verify in dcf | passthrough |

**Open item §15.D**: F2 has no AAPOR field. Either add one (manual classifier in admin dashboard for non-completed submissions) or document the derivation rule the ETL applies.

---

## 13. Language

**Canonical encoding**

| Field | Codes |
|---|---|
| `survey_language` | `en` / `fil` (extensible — ASPSI has more languages queued) |

**Per-instrument source mapping**

| Instrument | Source | Notes |
|---|---|---|
| F1 | not currently captured | implicit from CSPro form's `setlanguage()` call; recommend adding `LANGUAGE_USED` to FIELD_CONTROL (§15.E) |
| F2 | not currently captured as item | available at runtime via `useLocale()`; auto-inject into submission payload as `survey_language` (§15.E) |
| F3 | not currently captured | same as F1 — recommend adding |
| F4 | not currently captured | same as F1 — recommend adding |

**Open item §15.E**: none of the four instruments currently store language as a survey item. Recommend adding `survey_language` to all four (F2: auto-inject from locale state; F1 / F3 / F4: capture from `getlanguage()` at submit). Without this, post-hoc language-stratified analysis is impossible.

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

## 15. Open items / decisions needed before fieldwork

These need answers before the harmonization ETL can be implemented end-to-end. None block instrument design today; all block production data delivery later.

| # | Item | Decision needed | Owner |
|---|---|---|---|
| **15.A** | F4 respondent `Q3_SEX` allows `'Other'`; F1/F2/F3 do not | Map `'Other'` → canonical code `3`, treat as `.c`, or carry as separate `sex_other` flag? | ASPSI (instrument design) |
| **15.B** | F2 / F3 / F4 don't capture consent as a data field | Add explicit `consent_given` to F2/F3/F4 for audit parity with F1? | ASPSI / ethics; recommend yes |
| **15.C** | F3 / F4 dcf may not have explicit start/submit datetime fields | Verify in dcf; if missing, add `DATE_STARTED` / `TIME_STARTED` / `DATE_SUBMITTED` to FIELD_CONTROL | Carl + ASPSI |
| **15.D** | F2 has no AAPOR disposition code | Add a manual classifier in F2 admin dashboard, or codify the ETL derivation rule (`synced` → `110`, etc.)? | Carl |
| **15.E** | None of the four instruments stores `survey_language` | Add to FIELD_CONTROL (CAPI) and submission payload (PWA)? | Carl + ASPSI |
| **15.F** | PSGC vintage to pin | Pick one PSA release (e.g. 2023Q4) and freeze for the engagement | ASPSI |
| **15.G** | Facility master list | ASPSI to publish single canonical list; F2 PWA must consume it (currently uses placeholder) | ASPSI |
| **15.H** | F1 `QUESTIONNAIRE_NO` ≡ master list `facility_id`? | Confirm F1's QUESTIONNAIRE_NO scheme matches the master list id scheme; otherwise F1↔F2/F3/F4 joins fail silently | Carl + ASPSI |

---

## 16. Versioning

This codebook is **version 0.1** — drafted 2026-04-25 from current spec/dcf state. Subsequent revisions track:
- Each open item resolution (15.A–15.H)
- Each instrument spec change that touches a shared dimension (e.g. F1 sign-off may add or rename FIELD_CONTROL items)
- Each new instrument added to the engagement

Bump the `version` field at the top with every substantive change, and record the change in a CHANGELOG section appended below.

### CHANGELOG

| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-04-25 | Initial draft. Covers F1 / F2 / F3 / F4. Identifies 8 open items. Aligned to current spec/dcf state. |
