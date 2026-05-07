# F3/F4 Data Dictionary Generator Design

**Date:** 2026-04-16
**Scope:** Build CSPro 8.0 data dictionary generators for F3 (Patient Survey) and F4 (Household Survey) following the F1 pattern.
**Source PDFs:** April 8, 2026 versions (confirmed current).

---

## Architecture: Shared module extraction (Approach A)

Extract F1's reusable helpers into a shared module. Each instrument gets its own generator that imports from the shared module and only contains instrument-specific section builders.

### File structure

```
deliverables/CSPro/
├── cspro_helpers.py              — Shared helpers + value sets + FIELD_CONTROL/GEO_ID
├── F1/
│   ├── generate_dcf.py           — Refactored: imports cspro_helpers, keeps F1 section builders
│   ├── FacilityHeadSurvey.dcf
│   └── inputs/F1_clean.txt
├── F3/
│   ├── generate_dcf.py           — F3 section builders (A-L), imports cspro_helpers
│   ├── PatientSurvey.dcf         — Generated output
│   └── inputs/F3_clean.txt       — Text extraction from Apr 8 PDF
└── F4/
    ├── generate_dcf.py           — F4 section builders (A-Q), imports cspro_helpers
    ├── HouseholdSurvey.dcf       — Generated output
    └── inputs/F4_clean.txt       — Text extraction from Apr 8 PDF
```

---

## Shared module: `cspro_helpers.py`

### Helpers moved from F1

- `_value_set(name_prefix, label, options)` — CSPro value set object builder
- `numeric(name, label, length, zero_fill, value_set_options)` — numeric item
- `alpha(name, label, length)` — alpha item
- `yes_no(name, label)` — 1=Yes/2=No shorthand
- `yes_no_dk(name, label)` — Yes/No/I don't know
- `yes_no_na(name, label)` — Yes/No/Not applicable
- `select_one(name, label, options, length)` — single-select with value set
- `select_all(prefix, label, options, with_other_txt)` — dichotomous expansion (one item per option, 1=selected/2=not)
- `uhc9_item(name, label)` — standard 9-option UHC response + two Other-specify text fields
- `record(name, label, record_type, items, max_occurs, required)` — record wrapper

### Shared value sets

- `YES_NO`, `YES_NO_DK`, `YES_NO_NA`
- `UHC9_OPTIONS`
- `DICHOTOMOUS` (alias for YES_NO in select-all context)
- `FREQUENCY`
- `WHY_DIFF_OPTIONS`

### Parameterized common record builders

**`build_field_control(extra_items=None)`**

Shared structure: team leader, enumerator, field validated by, field edited by, date first visit, date final visit, total visits, enum result first visit, enum result final visit, consent given. The `extra_items` parameter lets each instrument inject additional cover fields (e.g., patient listing reference for F3, household listing reference for F4).

**`build_geo_id(mode, extra_items=None)`**

Three modes:
- `"facility"` — F1: region, province, city/municipality, barangay, facility-level fields
- `"facility_and_patient"` — F3: facility geo + patient home address fields
- `"household"` — F4: household-level geo (no facility)

PSGC fields (region, province, city/municipality, barangay) are common to all modes. Extra items can be appended per instrument.

---

## F3 Patient Survey dictionary

**Source:** Annex F3, April 8, 2026. 23 pages, 12 sections (A-L). Face-to-face CAPI, single respondent per case.

### Record layout

| Record | Section | Type | Max Occurs | Notes |
|---|---|---|---|---|
| FIELD_CONTROL | Cover | A | 1 | Shared + patient listing ref |
| PATIENT_GEO_ID | Geo ID | B | 1 | Dual: facility + patient home |
| A_INFORMED_CONSENT | A | C | 1 | Consent gate |
| B_PATIENT_PROFILE | B | D | 1 | Demographics |
| C_UHC_AWARENESS | C | E | 1 | UHC knowledge, UHC9 items |
| D_PHILHEALTH_REG | D | F | 1 | PhilHealth, YAKAP/Konsulta |
| E_PRIMARY_CARE | E | G | 1 | PCF utilization, barriers |
| F_HEALTH_SEEKING | F | H | 1 | Facility choice, bypassing |
| G_OUTPATIENT_CARE | G | I | 1 | Conditional on outpatient |
| H_INPATIENT_CARE | H | J | 1 | Conditional on inpatient |
| I_FINANCIAL_RISK | I | K | 1 | OOP, distress financing, CHE |
| J_SATISFACTION | J | L | 1 | Satisfaction ratings |
| K_ACCESS_MEDICINES | K | M | 1 | Drug access, pharmacy |
| L_REFERRALS | L | N | 1 | Referral process |

**14 records, all single-occurrence.** Structurally similar to F1.

### F3 design notes

- Sections G/H are mutually conditional (outpatient vs inpatient). Both records exist in the DCF; routing is PROC-level, not dictionary structure. An outpatient/inpatient flag captured early (Section F or FIELD_CONTROL) enables the skip.
- UHC9 items in Section C reuse `uhc9_item()` from shared helpers.
- Section I (Financial Risk Protection) has the heaviest validation needs (OOP amounts, income-relative thresholds) — noted for future skip logic spec, not in scope for DCF-only.

---

## F4 Household Survey dictionary

**Source:** Annex F4, April 8, 2026. 26 pages, 17 sections (A-Q). Face-to-face CAPI, one respondent (HH head/decision-maker) per case. New instrument for Year 2.

### Record layout

| Record | Section | Type | Max Occurs | Notes |
|---|---|---|---|---|
| FIELD_CONTROL | Cover | A | 1 | Shared + HH listing ref |
| HOUSEHOLD_GEO_ID | Geo ID | B | 1 | Household-only geo |
| A_INFORMED_CONSENT | A | C | 1 | Consent gate |
| B_RESPONDENT_PROFILE | B | D | 1 | HH head demographics |
| C_HOUSEHOLD_ROSTER | C | E | **20** | Repeating: name, age, sex, relationship, education, employment per member |
| D_UHC_AWARENESS | D | F | 1 | UHC knowledge |
| E_YAKAP_KONSULTA | E | G | 1 | YAKAP/Konsulta awareness |
| F_BUCAS_AWARENESS | F | H | 1 | BUCAS awareness |
| G_ACCESS_MEDICINES | G | I | 1 | GAMOT, generic drugs |
| H_PHILHEALTH_REG | H | J | **20** | Repeating: PhilHealth per HH member |
| I_PRIMARY_CARE | I | K | 1 | Usual source of care |
| J_HEALTH_SEEKING | J | L | **20** | Repeating: health-seeking per HH member |
| K_REFERRALS | K | M | 1 | Referral experience |
| L_NBB_AWARENESS | L | N | 1 | No Balance Billing |
| M_ZBB_AWARENESS | M | O | 1 | Zero Balance Billing |
| N_HOUSEHOLD_EXPENDITURES | N | P | 1 | Food/non-food/health sub-item grids (flat) |
| O_SOURCES_OF_FUNDS | O | Q | 1 | Health financing sources |
| P_FINANCIAL_RISK | P | R | 1 | Forgone/delayed care |
| Q_FINANCIAL_ANXIETY | Q | S | 1 | Health payment anxiety |

**19 records total. 3 repeating (max_occurs=20), 16 flat.**

### F4 design notes

- **Repeating records (C, H, J):** CSPro links via record occurrence. Each repeating record includes a `MEMBER_LINE_NO` item for cross-reference to the roster.
- **Section N (Expenditures):** Sub-tables (food weekly, non-food, health 12-month) modeled as flat item batteries within a single record (e.g., `Q_N01_RICE`, `Q_N02_BREAD`), not repeating records. Same approach F1 used for YAKAP service availability lists.
- **Sections L and M (NBB/ZBB):** Separate records despite similar structure, matching the questionnaire's separation.

---

## F1 refactor scope

Minimal, mechanical, and verified:

1. Create `cspro_helpers.py` with extracted helpers, value sets, and common builders.
2. Replace moved code in F1's `generate_dcf.py` with imports from `cspro_helpers`.
3. F1's `PENDING_DESIGN_*` constants, section builders, and `build_dictionary()` stay untouched.
4. **Regenerate `FacilityHeadSurvey.dcf` and diff against current version — must be identical.** Any byte-level difference means the refactor has a bug.

---

## Conventions (carried from F1)

- **Naming:** `Q{n}_{SHORT}` for items, `Q{n}_O##_{SHORT}` for select-all options, `_OTHER_TXT` for specify fields.
- **NA coding:** Highest valid code at field width (9/99/999). Never use CSPro `notappl` in value sets.
- **Verbatim labels:** Question text from the PDF as-is in DCF labels. 255-char CSPro limit may force trims — document any in generator comments.
- **Generator is source of truth:** All edits go through the generator script, never hand-edit the `.dcf`.

---

## Out of scope (future sprints)

- Skip logic and validation specs for F3/F4
- PROC code / form files (`.fmf`)
- F2 CSPro dictionary (deferred — Google Forms track is primary)
- PSGC value sets (blocked on ASPSI providing code lists)
- Multi-language support

---

## Build order

1. Extract shared helpers → `cspro_helpers.py`
2. Refactor F1 → import from shared module → identity-diff check
3. Text-extract F3 PDF → `F3_clean.txt`
4. Build F3 generator → emit `PatientSurvey.dcf`
5. Text-extract F4 PDF → `F4_clean.txt`
6. Build F4 generator → emit `HouseholdSurvey.dcf`
