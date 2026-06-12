---
project: UHC Survey Year 2 — CAPI Development
artifact: Shared Codebook (cross-instrument harmonization spec)
version: 0.4 (draft, 2026-06-12)
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
| F2 | not currently captured as a survey item — derive from joined distribution-list × IndexedDB-state × submission-row data (see derivation rule below) | apply derivation rule at ETL time |
| F3 | `AAPOR_DISPOSITION` (FIELD_CONTROL) ✓ verified 2026-04-25 | passthrough |
| F4 | `AAPOR_DISPOSITION` (FIELD_CONTROL) ✓ verified 2026-04-25 | passthrough |

**Open item §15.D — RESOLVED 2026-04-25 (Carl-owned)**: ETL derivation rule for F2, applied at harmonization time over the joined `(distribution_list × submission_row)`:

| Observed state | AAPOR code | Label |
|---|---|---|
| Submission row exists, `status='synced'` | `110` | Complete |
| Submission row exists, never reached `synced` (stuck >48h in `pending_sync` or `retry_scheduled`) | `120` | Partial / break-off — sync issue, not respondent issue, but treated as partial for analytical conservatism |
| HCW in distribution list, draft exists in IndexedDB but never submitted, last update <24h | `000` | In progress |
| HCW in distribution list, draft exists, last update 24h–7d | `230` | Other eligible non-interview (likely abandoned but within return-window) |
| HCW in distribution list, draft exists, last update ≥7d | `220` | Non-contact / abandoned |
| HCW in distribution list, no draft, no submission | `220` | Non-contact (never opened the form) |
| Explicit refusal flag | `210` | Refusal — respondent (only available if §15.B is implemented; until then, refusals are indistinguishable from non-contact) |

The "draft last update" timestamp is observable from the F2 admin dashboard's IndexedDB-replicated state, which we'll need to expose in the response sheet (small Apps Script change to record `draft_last_updated_at` on each interim submission attempt — call it §15.D.1 if scoped as a follow-up).

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
| **15.D** | F2 AAPOR derivation strategy | ✓ Defined ETL derivation rule over joined `(distribution_list × IndexedDB draft state × submission row)`. See §12 above for the full code-mapping table. Refusal capture deferred until §15.B is decided. |
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

See `open-items-for-aspsi.md` for context.

---

## 16. Versioning

This codebook is **version 0.4** (see CHANGELOG) — drafted 2026-04-25 from current spec/dcf state. Subsequent revisions track:
- Each open item resolution (15.A–15.H)
- Each instrument spec change that touches a shared dimension (e.g. F1 sign-off may add or rename FIELD_CONTROL items)
- Each new instrument added to the engagement

Bump the `version` field at the top with every substantive change, and record the change in a CHANGELOG section appended below.

### CHANGELOG

| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-04-25 | Initial draft. Covers F1 / F2 / F3 / F4. Identifies 8 open items. Aligned to current spec/dcf state. |
| 0.2 | 2026-04-25 | Corrections after deeper dcf grep: F3 + F4 dcfs DO have `CONSENT_GIVEN`, `AAPOR_DISPOSITION`, `DATE_STARTED`/`TIME_STARTED`, and `DATE_FIRST_VISITED`/`DATE_FINAL_VISIT` (initial v0.1 audit was overly pessimistic on these). 15.C closed. 15.D resolved with ETL derivation rule for F2 disposition. 15.E split into Carl-owned F2 portion (resolved — ships in v1.2.0) and ASPSI-owned F1/F3/F4 portion (pending). 15.B narrowed to F2 only (F3/F4 already capture consent). Open items shrunk from 8 to 6 (5 ASPSI-owned + 1 mixed Carl/ASPSI). Stakeholder-facing open-items doc created at `open-items-for-aspsi.md`. |
| 0.3 | 2026-06-04 | **12-digit case-key alignment.** Adopted the decomposed `RR-PP-MMM-FF-CCC` Questionnaire / Respondent Number (5 ID items) across F1/F3/F4 — dcfs rebuilt + re-registered in CSWeb. `facility_id` is now the case key's first 9 digits, *superseding* §15.H's 6-digit geography-free assumption. `F3_FACILITY_ID` retired; `F4_PARENT_F3_CASE_SEQ` added. §1 PSGC vintage pinned to PSA 2024 (§15.F). F2 case-ID issuer still gated on the facility master list (§15.G). |
| 0.4 | 2026-06-12 | **As-built drift audit from the first ETL dry-run** (skeleton at `etl/`, run against the 4 live desk-test cases in the CSWeb breakout DBs — see `etl/README.md` + etl-spec v0.2). Findings vs the rebuilt June dcfs: **(a) §10 stale** — `DATE_STARTED`/`TIME_STARTED` no longer exist; as-built capture is `DATE_FIRST_VISITED`/`DATE_FINAL_VISIT` (F1: `…_THE_FACILITY` names) + visit counts/results; **no time-of-day is captured** — `survey_started_at`/`survey_submitted_at` recodes are date-only. **(b) §11 stale** — `INTERVIEWER_ID` no longer exists; as-built has free-text `ENUMERATOR_S_NAME` (+ team-leader/validated-by/edited-by names). Codebook canon expects roster IDs → **new open item 15.I: restore an enumerator roster-ID item or redefine §11 to name-matching** (ASPSI/instrument decision). **(c) §9 partially stale** — no explicit `CONSENT_GIVEN` boolean in any CAPI instrument's `A_INFORMED_CONSENT` record (the v0.2 claim no longer holds post-rebuild); consent appears enforced by the consent-terminator flow (refusals never saved). Decide: re-add the explicit item (audit-trail parity, mirrors §15.B for F2) or codify implicit-consent-by-presence. **(d) §13/§15.E CAPI portion RESOLVED as-built** — `LANGUAGE_USED` exists in `FIELD_CONTROL` on F1/F3/F4. **(e) §1/§2 operational rule** — numeric-entered keys and PSGC items lose leading zeros in the store; the ETL zero-pads to canonical widths (12-digit key / 10-digit PSGC) before any join or slice (etl-spec §2.1 caveat 2). Extract mechanism decided: CSWeb breakout DBs (etl-spec v0.2 §2.1). |
