# Single 12-digit Questionnaire Number — Case-Key + Geo Redesign (F1/F3/F4)

**Date:** 2026-06-10 · **Author decision:** Carl (architecture locked via in-chat go/no-go)
**Status:** specced, NOT yet applied. Foundation note left in `cspro_helpers.build_id_block`.
**Why:** (1) replaces the broken `FACILITY_LOOKUP` auto-fill that infinite-loops Android CSEntry
(Blocker 1); (2) removes the redundant double-entry of geo (case-key codes + body PSGC cascade);
(3) the geo-cascade removal is also the leading candidate fix for the survey-body SIGSEGV (Blocker 2).
See [[project_aspsi_f1_android_csentry_blockers]].

## Locked architecture (Carl, 2026-06-10)
1. **Scope = key + body geo.** ONE 12-digit number is the only place region/province/city/facility are
   entered. Region/province/city shown read-only (names) for confirmation; the redundant body
   Region→Province→City cascade is removed.
2. **Barangay = keep one picker**, cascade-filtered by the city derived from the number (barangay is
   NOT in the 12-digit facility code, so it still needs capture).
3. **Validation = validate + show names.** Each of region/province/city codes must resolve in the PSGC
   external dicts; hard-error (reenter) on an unknown code; display the PSGC names read-only.

Digit layout (unchanged): `RR(2) PP(2) MMM(3) FF(2) CCC(3)` = 12.

## DCF changes
**Shared (`cspro_helpers.py`):**
- `build_id_block()` → return a single item: `QUESTIONNAIRE_NUMBER` numeric, `start:2 length:12 zeroFill`.
- New `derived_geo_code_items()` → non-id items for FIELD_CONTROL: `REGION_CODE`(2) `PROVINCE_HUC_CODE`(2)
  `CITY_MUNICIPALITY_CODE`(3) `FACILITY_NO`(2) `CASE_SEQ`(3) [same names as old ids → all existing PROC
  refs keep working] + `REGION_NAME`/`PROVINCE_NAME`/`CITY_NAME` alpha(80) read-only display.
- `_psgc_fields(prefix="", facility_derived=False)` → add the flag. When `facility_derived=True` (the
  FACILITY geo only) return **`[BARANGAY]` only**. Default (patient-home P_ in F3) keeps the full
  `[REGION, PROVINCE_HUC, CITY_MUNICIPALITY, BARANGAY]` cascade — **F3 patient-home stays manual**.
- `build_field_control(...)` (shared, F3/F4) → append `derived_geo_code_items()` after the standard block.
- `build_geo_id("facility")` and `("facility_and_patient")` → pass `facility_derived=True` to the
  facility `_psgc_fields()` call (NOT the `P_` one).

**F1 (`F1/generate_dcf.py`) — most custom:**
- Inline id block (currently 5 items, lines ~1094-1107) → single `QUESTIONNAIRE_NUMBER` (or call
  `build_id_block()`).
- F1's own `build_field_control()` (line ~84) → append `derived_geo_code_items()`.

**F3/F4:** confirm they call shared `build_id_block` + `build_field_control` + `build_geo_id`; if so the
shared edits cover them. F4 = `build_geo_id("household")` (facility_derived=True). F3 =
`("facility_and_patient")` (facility derived, patient-home manual).

## APC changes (per instrument; F1 first)
- **REMOVE** the `PROC CASE_SEQ` FACILITY_LOOKUP auto-fill block (Blocker 1). Also remove
  `facility_lookup.dcf` from `cspro_compile_driver._ent_json` and stop bundling it.
- **REMOVE** the `PROC REGION / PROVINCE_HUC / CITY_MUNICIPALITY` onfocus cascade procs (geo now derived).
- **ADD** `PROC QUESTIONNAIRE_NUMBER` postproc:
  - parse: `REGION_CODE = int(QUESTIONNAIRE_NUMBER / 10^10)`, `PROVINCE_HUC_CODE = int(/10^8)%100`,
    `CITY_MUNICIPALITY_CODE = int(/10^5)%1000`, `FACILITY_NO = int(/10^3)%100`, `CASE_SEQ = %1000`.
  - validate each against PSGC via `loadcase(PSGC_REGION_DICT, REGION_CODE)` etc. (province filtered to
    region, city to province). On miss → `errmsg(...)` + `reenter`.
  - set `REGION_NAME/PROVINCE_NAME/CITY_NAME = strip(R_NAME/P_NAME/C_NAME)` from the loaded PSGC cases.
  - **CSPro nuance to VERIFY on CSEntry:** an id-field postproc writing FIELD_CONTROL items may hit the
    "record at a lower level" rule (cf. the LANGUAGE_USED finding). Fallback: do the parse/validate/name
    work in `PROC SURVEY_CODE preproc` (proven to write FIELD_CONTROL), and keep only the `reenter` guard
    on QUESTIONNAIRE_NUMBER. Decide by reading `<app>.ent.err`.
- **KEEP** `PROC BARANGAY` onfocus → `FillBarangayValueSet(CITY_MUNICIPALITY_CODE)` (was
  `CITY_MUNICIPALITY`; now the derived code).
- Photo-filename proc already uses `REGION_CODE…CASE_SEQ` → still valid (now derived items).

## FMF / forms
- **Case-key form (FORM000):** one field — `QUESTIONNAIRE_NUMBER`. F1 builds this via
  `F1/inject_case_key.py` (static fmf) → update it to emit one field, not five. F3/F4 via
  `generate_fmf.py` auto-layout → one id field.
- **Geo form:** show `REGION_NAME/PROVINCE_NAME/CITY_NAME` as read-only (Protected) text + `BARANGAY`
  dropdown. F1 static fmf needs hand-built block; F3/F4 generator auto-lays.

## Verification plan (per instrument, F1 pilot first)
1. `preflight_validate.py` ALL CLEAN.
2. `automation/csentry_verify.py F1` → CSEntry compile gate PASS, no `.ent.err`.
3. Emulator (AVD `capi_tablet`): app **starts clean** (Blocker 1 fixed — no FACILITY_LOOKUP loop).
4. Add a case, type a real 12-digit number (e.g. `010280001001`); confirm parse + PSGC names +
   barangay cascade; **confirm it enters the survey body without SIGSEGV (Blocker 2 check).**
5. Walk to consent=No (fast saveable case) → save → CSEntry Synchronize → verify the case lands in the
   CSWeb store (`setest`, read-only SSH/DB) → sync down. Closes Stage-2 #13/#14 for F1.
6. Replicate to F3 (patient-home cascade stays) and F4.

## Open risks
- Blocker 2 (body SIGSEGV) may NOT be the cascade — if it persists after this redesign, bisect the
  remaining body procs (SURVEY_CODE preproc, GPS/photo capture) on the emulator.
- F1's static fmf + `inject_case_key.py` is the fiddliest piece; budget CSEntry reconcile iterations.
