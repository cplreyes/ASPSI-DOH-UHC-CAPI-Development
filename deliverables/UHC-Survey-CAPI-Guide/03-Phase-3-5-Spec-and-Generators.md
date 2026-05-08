---
title: "03 — Phase 3-5: Spec, Generators, Corrections"
category: deliverable
tags: [capi, cspro, generators, skip-logic, validation, reformatting, uhc-y2]
last_updated: 2026-05-08
status: draft
---

# 03 — Phase 3-5: Spec, Generators, Corrections

This chapter covers the middle of the CAPI lifecycle for the UHC Survey Year 2 F-series instruments — the work that takes a frozen questionnaire (Phase 1) and a stable toolchain vocabulary (Phase 2) and turns them into a buildable, testable specification.

The boundary between these phases is the cheapest place in the lifecycle to find bugs. A typo in a markdown table costs one keystroke; the same typo discovered after Designer wiring costs a regen plus a layout rewire; the same typo discovered after enumerators have entered cases costs a `Reformat Data` cycle and a fieldwork-paused incident.

| Phase | Output | Question answered |
|---|---|---|
| Phase 3 | `.dcf` data dictionary, `psgc_*.dcf`/`psgc_*.dat` lookups, generator scripts, review workbooks | "Can the dictionary be regenerated from spec in one command?" |
| Phase 4 | `<F>-Skip-Logic-and-Validations.md` | "Does every conditional in the questionnaire have a documented skip and a validation tier?" |
| Phase 5 | Updated generators + closed bugs | "Has every Phase 4 finding either been fixed or explicitly deferred with a reason?" |

Cross-references in this chapter use Obsidian wikilinks. The canonical workflow template lives at [[2_Areas/IT-Standards/templates/CAPI-Development-Workflow]] and the F-Series naming and value-set conventions live at [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F-Series Value Set Conventions]].

---

## Phase 3 — Reproducible spec / dictionary generation

### 3.1 The "generator over hand-edit" rule

Questionnaires always change. The Apr 08 baseline of F1 had ~126 printed items; the Apr 20 DOH-submitted revision lifted the dcf to 11 records / 655 items; the Apr 21 GPS+photo capture pass took it to 12 records / 664 items. By the time the F-series settled it was F1 671 / F3 806 / F4 623. Each of those revisions was a re-run of `python generate_dcf.py`, not a manual pass through CSPro Designer.

The rule:

> **Every dictionary artifact that will rev — items, value sets, ID lengths, record types, FIELD_CONTROL composition — is produced by a script you can re-run, not maintained by hand. Hand-edits in CSPro Designer are reserved for form layout (the `.fmf`) and PROC code (the `.apc`) — never for the `.dcf`.**

Khurshid's GUI-driven workflow (paste-value-set-link in Designer, drag-drop on the form) is fine for one-off, low-rev-count instruments — say, a 50-item single-language pilot. For a 671-item F1 plus 806-item F3 plus 623-item F4, with a 7-dialect translation pipeline lurking at Phase 6, scripting wins three ways:

1. **Diffability.** A `git diff` over `generate_dcf.py` shows exactly which items changed; a `git diff` over a `.dcf` JSON blob is unreadable noise.
2. **Replayability.** Every fix in Phase 5 is a new commit on the generator. The dcf is a build artifact, regenerated deterministically from the script.
3. **Cross-instrument code reuse.** F3 and F4 share the same `cspro_helpers.py` module as F1. A bug fix in `select_all()` propagates to all three on next regen.

The trade-off — and there is one — is that anyone reading the project who only knows Designer needs a moment of orientation. The deliverable here is the generator, the regenerated dcf, **and** the explanatory markdown that lets a Designer-first reader skim the script and follow along.

### 3.2 The cspro_helpers.py pattern

`deliverables/CSPro/cspro_helpers.py` is the shared module imported by F1, F3, and F4 generators. Three responsibilities:

1. **Reusable value sets** as module constants.
2. **Item builder functions** that return CSPro 8.0 dictionary item dicts.
3. **Common record builders** for cross-instrument scaffolding (FIELD_CONTROL, GEO_ID, GPS, photo).

#### 3.2.1 Item builders

The base item builders cover the four CSPro item shapes that recur across the F-series. They all return a CSPro 8.0 JSON item dict ready for inclusion in a record's `items` list.

```python
def numeric(name, label, length=1, zero_fill=False, value_set_options=None):
    item = {
        "name": name,
        "labels": [{"text": label}],
        "contentType": "numeric",
        "length": length,
        "zeroFill": zero_fill,
    }
    if value_set_options:
        item["valueSets"] = [_value_set(name, label, value_set_options)]
    return item


def alpha(name, label, length=50):
    return {
        "name": name,
        "labels": [{"text": label}],
        "contentType": "alpha",
        "length": length,
    }
```

On top of these primitives are the convenience builders that bake in the recurring value-set patterns:

```python
def yes_no(name, label):
    return numeric(name, label, length=1, value_set_options=YES_NO)


def yes_no_dk(name, label):
    return numeric(name, label, length=1, value_set_options=YES_NO_DK)


def yes_no_na(name, label):
    return numeric(name, label, length=1, value_set_options=YES_NO_NA)


def select_one(name, label, options, length=2):
    return numeric(name, label, length=length,
                   zero_fill=(length > 1),
                   value_set_options=options)
```

The `select_all()` builder encapsulates the SELECT-ALL idiom — one dichotomous (Yes/No) item per option, plus an optional `_OTHER_TXT` alpha for "Other (specify)" capture:

```python
def select_all(prefix, label, options, with_other_txt=None):
    """SELECT-ALL idiom: one dichotomous item per option (1=selected, 2=not).
    If with_other_txt is True (or None and last option mentions 'specify'),
    appends an OTHER_TXT alpha for the free-text capture."""
    items = []
    for i, (text, _code) in enumerate(options):
        items.append(numeric(
            f"{prefix}_O{i+1:02d}",
            f"{label} — {text}",
            length=1,
            value_set_options=YES_NO,
        ))
    if with_other_txt is None:
        with_other_txt = bool(options) and "specify" in options[-1][0].lower()
    if with_other_txt:
        items.append(alpha(f"{prefix}_OTHER_TXT",
                           f"{label} — Other (specify) text",
                           length=120))
    return items
```

The `select_all()` function returns a *list* of items (not a single item), so generator code calls it with list extension:

```python
items.extend(select_all("Q121_DOH_LIC_DIFFICULT",
                        "121. Why was DOH licensing difficult?",
                        Q121_OPTIONS))
```

The project-specific composite `uhc9_item()` is the most opinionated builder — it knows about the 9-option UHC Act answer pattern and emits a triple (the main numeric + two specify-text alpha fields):

```python
def uhc9_item(name, label):
    """Standard UHC9 question. Emits 3 items: the main numeric (length 1,
    9-option value set) plus two free-text items for the 'Yes other'
    and 'No other' specify branches."""
    return [
        numeric(name, label, length=1, value_set_options=UHC9_OPTIONS),
        alpha(f"{name}_YES_OTHER_TXT",
              f"{label} — Yes, other (specify) text", length=120),
        alpha(f"{name}_NO_OTHER_TXT",
              f"{label} — No, other (specify) text", length=120),
    ]
```

A typical UHC9 question in `generate_dcf.py` is a single line:

```python
items.extend(uhc9_item("Q19_NEW_ROLES",
                       "19. Has the facility introduced new roles since UHC?"))
```

That one call expands to three dictionary items: `Q19_NEW_ROLES` (length-1 numeric with the 9-option value set), `Q19_NEW_ROLES_YES_OTHER_TXT` (length-120 alpha), `Q19_NEW_ROLES_NO_OTHER_TXT` (length-120 alpha).

#### 3.2.2 Value-set constants

Reusable value sets live as module-level lists of `(label, code)` tuples:

```python
YES_NO = [
    ("Yes", "1"),
    ("No",  "2"),
]

YES_NO_DK = [
    ("Yes",          "1"),
    ("No",           "2"),
    ("I don't know", "3"),
]

YES_NO_NA = [
    ("Yes",            "1"),
    ("No",             "2"),
    ("Not applicable", "9"),
]
```

Note `YES_NO_NA` codes "Not applicable" as `9`, not `3`. This is the **F-Series NA convention** documented in [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F-Series Value Set Conventions]]: when a value set includes "Not applicable" as an explicit pickable option, encode it as the **highest valid code at the item's field width**.

| Field width | NA code |
|---|---|
| length-1 numeric | `9` |
| length-2 numeric | `99` |
| length-3 numeric | `999` |

The reasoning: F-series instruments don't track "Missing" as a distinct concept (non-response is just a blank cell, which CSPro auto-maps to `notappl`), so the DHS reserved zone (7 = NA, 8 = DK, 9 = Missing) is dead weight here. "NA = highest code" matches the dominant existing pattern (5 of 7 F1 value sets used NA=9 before standardization), reads as the analyst-intuitive "least-likely answer at the top," and avoids field-width promotions.

Two warnings carried over from the conventions page:

- **Never** use CSPro's `notappl` special value as a value-set entry. CSPro reserves `notappl` for fields skipped during data entry — colliding with that breaks `if X = notappl` tests. The two concepts (skipped field vs enumerator-picked NA) must stay distinct.
- The squeeze case is allowed when substantive options exhaust the field width. F1's `UHC9_OPTIONS` has 7 substantive options + DK + NA filling all 9 length-1 codes. There is no Missing slot. This is intentional.

The other recurring constants:

```python
DICHOTOMOUS = YES_NO  # alias used in some older generator files

UHC9_OPTIONS = [
    ("Yes, this was implemented as a direct result of the UHC Act",                          "1"),
    ("Yes, this was pre-existing, but it has significantly improved due to the UHC Act",     "2"),
    ("Yes, this has been implemented or improved recently, but not due to the UHC Act",      "3"),
    ("Yes, other reason (specify)",                                                          "4"),
    ("No, this has not been implemented yet, but we plan to in the next 1-2 years",          "5"),
    ("No, and we have no plans to do this in the next 1-2 years",                            "6"),
    ("No, other reason (specify)",                                                           "7"),
    ("I don't know",                                                                         "8"),
    ("Not applicable",                                                                       "9"),
]

FREQUENCY = [
    ("Weekly",          "1"),
    ("Monthly",         "2"),
    ("Quarterly",       "3"),
    ("Semi-annually",   "4"),
    ("Annually",        "5"),
    ("Other (specify)", "6"),
]

SATISFACTION_5PT = [
    ("Very Satisfied",                        "1"),
    ("Satisfied",                             "2"),
    ("Neither Satisfied nor Dissatisfied",    "3"),
    ("Dissatisfied",                          "4"),
    ("Very Dissatisfied",                     "5"),
    ("Not applicable",                        "9"),
]

ENUM_RESULT_OPTIONS = [
    ("Completed",  "1"),
    ("Postponed",  "2"),
    ("Refused",    "3"),
    ("Incomplete", "4"),
]

AAPOR_DISPOSITION_OPTIONS = [
    ("000 — In Progress (initial)",                       "000"),
    ("110 — Complete interview",                          "110"),
    ("120 — Partial interview / break-off",               "120"),
    ("210 — Refusal — respondent",                        "210"),
    ("211 — Refusal — gatekeeper / household",            "211"),
    ("220 — Non-contact — respondent unavailable",        "220"),
    ("230 — Other eligible non-interview",                "230"),
    ("310 — Unknown eligibility — facility/household",    "310"),
    ("320 — Unknown eligibility — respondent",            "320"),
    ("410 — Not eligible — out of sample / ineligible",   "410"),
    ("450 — Not eligible — other",                        "450"),
]
```

The AAPOR codes are zero-filled length-3 numeric and use 3-digit integers — AAPOR's published decimal codes (1.10, 2.10, etc.) are multiplied by 100 to integerize. The `000 — In Progress` sentinel is ASPSI-internal — set at case start by `FIELD_CONTROL.preproc`, rewritten to the final code on the CLOSING form.

#### 3.2.3 The FIELD_CONTROL builder

`build_field_control()` produces the common case-control record (record type `A`) shared across F1, F3, and F4. It captures consent, eligibility, AAPOR disposition, interviewer/supervisor IDs, and visit dates — everything an analyst needs to reconstruct fieldwork posture for a case.

```python
def build_field_control(survey_code, extra_items=None,
                        date_label_entity="the Facility"):
    """Build a FIELD_CONTROL record (record type "A").

    Standard items (in order):
        SURVEY_CODE, INTERVIEWER_ID, DATE_STARTED, TIME_STARTED, AAPOR_DISPOSITION,
        SURVEY_TEAM_LEADER_S_NAME, ENUMERATOR_S_NAME, FIELD_VALIDATED_BY,
        FIELD_EDITED_BY, DATE_FIRST_VISITED (length 8), DATE_FINAL_VISIT (length 8),
        TOTAL_NUMBER_OF_VISITS, ENUM_RESULT_FIRST_VISIT, ENUM_RESULT_FINAL_VISIT,
        CONSENT_GIVEN.
    """
    items = _case_control_items(survey_code) + [
        alpha("SURVEY_TEAM_LEADER_S_NAME", "Survey Team Leader's Name", length=50),
        alpha("ENUMERATOR_S_NAME",         "Enumerator's Name",         length=50),
        alpha("FIELD_VALIDATED_BY",        "Field Validated by",        length=50),
        alpha("FIELD_EDITED_BY",           "Field Edited by",           length=50),
        numeric("DATE_FIRST_VISITED",
                f"Date First Visited {date_label_entity} (YYYYMMDD)", length=8),
        numeric("DATE_FINAL_VISIT",
                f"Date of Final Visit to {date_label_entity} (YYYYMMDD)", length=8),
        numeric("TOTAL_NUMBER_OF_VISITS",  "Total Number of Visits",   length=3),
        numeric("ENUM_RESULT_FIRST_VISIT", "Result of First Visit",    length=1,
                value_set_options=ENUM_RESULT_OPTIONS),
        numeric("ENUM_RESULT_FINAL_VISIT", "Result of Final Visit",    length=1,
                value_set_options=ENUM_RESULT_OPTIONS),
        numeric("CONSENT_GIVEN",           "Informed consent given",   length=1,
                value_set_options=YES_NO),
    ]
    if extra_items:
        items.extend(extra_items)
    return record("FIELD_CONTROL", "Field Control", "A", items)
```

The `_case_control_items()` private helper returns the five case-start metadata items prepended to every FIELD_CONTROL: `SURVEY_CODE` (alpha, length 2), `INTERVIEWER_ID`, `DATE_STARTED`, `TIME_STARTED`, `AAPOR_DISPOSITION`. These are populated by `FIELD_CONTROL.preproc` in the instrument's `.apc` file — see the per-instrument skip-logic spec §2 for PROC snippets.

The `date_label_entity` parameter is the cleanest example of why this is a generator and not a copy-paste: F1 calls `build_field_control("F1", date_label_entity="the Facility")`, F3 calls it with `"the Patient"`, F4 with `"the Household"`. The label string flows through to `"Date First Visited the Patient (YYYYMMDD)"` etc. without any text copy-edit.

#### 3.2.4 The GEO_ID builder

`build_geo_id(mode)` produces the geographic-identification record (record type `B`) and supports three modes:

| Mode | Used by | Items emitted |
|---|---|---|
| `"facility"` | F1 | CLASSIFICATION + 4 PSGC + FACILITY_NAME + FACILITY_ADDRESS + LATITUDE + LONGITUDE |
| `"facility_and_patient"` | F3 | CLASSIFICATION + 4 PSGC + FACILITY_NAME + FACILITY_ADDRESS + 4 patient-home PSGC (`P_` prefix) |
| `"household"` | F4 | CLASSIFICATION + 4 PSGC + HH_ADDRESS |

The function signature:

```python
def build_geo_id(mode, extra_items=None):
    classification_item = numeric("CLASSIFICATION", "Classification", length=1,
                                  value_set_options=[
                                      ("UHC IS",     "1"),
                                      ("Non-UHC IS", "2"),
                                  ])

    if mode == "facility":
        items = (
            [classification_item]
            + _psgc_fields()
            + [
                alpha("FACILITY_NAME",    "Facility Name",    length=100),
                alpha("FACILITY_ADDRESS", "Facility Address", length=200),
                alpha("LATITUDE",  "Latitude",  length=12),
                alpha("LONGITUDE", "Longitude", length=12),
            ]
        )
        # ... extend with extra_items, return record(...)

    elif mode == "facility_and_patient":
        patient_psgc = _psgc_fields(prefix="P_")
        for it in patient_psgc:
            it["labels"][0]["text"] = "Patient Home " + it["labels"][0]["text"]
        # ...

    elif mode == "household":
        # ...

    else:
        raise ValueError(
            f"build_geo_id: unknown mode {mode!r}. "
            "Expected 'facility', 'facility_and_patient', or 'household'."
        )
```

Three patterns to notice:

1. **Mode-specific record naming.** F1 emits `HEALTH_FACILITY_AND_GEOGRAPHIC_IDENTIFICATION`; F3 emits `PATIENT_GEO_ID`; F4 emits `HOUSEHOLD_GEO_ID`. The record name lives inside the builder, so callers don't have to remember it.
2. **Patient-home PSGC reuses `_psgc_fields()` with a `P_` prefix.** Same four items (`P_REGION`, `P_PROVINCE_HUC`, `P_CITY_MUNICIPALITY`, `P_BARANGAY`) but distinct from the facility PSGC items in the same record.
3. **Defensive `else` raises ValueError.** Typoing `"facilty"` (one missing `i`) explodes loudly at generator runtime instead of silently producing an empty record.

#### 3.2.5 PSGC cascade lookup binding

The four PSGC fields in `_psgc_fields()` deserve their own treatment because they're how the F-series handles the 1Q-2026 Philippine geography hierarchy (18 regions → 117 provinces → 1658 cities → 42010 barangays).

```python
def _psgc_fields(prefix=""):
    """Return the four standard PSGC geographic code items.

    Items are length=10 numeric zero-filled, holding the full 10-digit PSA
    PSGC code. Value sets are deliberately NOT baked in — the four PSGC
    external lookup dictionaries (shared/psgc_*.dcf) + PSGC-Cascade.apc
    logic populate dynamic value sets at runtime via setvalueset().

    A one-entry generic placeholder value set is attached so CSPro Designer
    shows a label in the case tree (per CSPro 8.0 Users Guide p.188 best-
    practice #3 for cascading items).
    """
    placeholder = [("(set at runtime)", "0" * 10)]
    return [
        numeric(f"{prefix}REGION",            "Region",
                length=10, zero_fill=True, value_set_options=placeholder),
        numeric(f"{prefix}PROVINCE_HUC",      "Province / HUC",
                length=10, zero_fill=True, value_set_options=placeholder),
        numeric(f"{prefix}CITY_MUNICIPALITY", "City / Municipality",
                length=10, zero_fill=True, value_set_options=placeholder),
        numeric(f"{prefix}BARANGAY",          "Barangay",
                length=10, zero_fill=True, value_set_options=placeholder),
    ]
```

The trick: each PSGC field is a length-10 numeric with a deliberately-empty placeholder value set. The real options come from the four PSGC external lookup dictionaries (`shared/psgc_region.dcf` etc.) loaded at runtime by `PSGC-Cascade.apc`, which calls `setvalueset()` after each `loadcase()` to populate the cascading dropdowns. See §3.6 below for the lookup-build script and the runtime PROC.

The placeholder value set isn't strictly required by CSPro 8.0 but CSPro Designer renders the case-tree better with one — the user-guide best practice for cascading items.

### 3.3 Naming convention

Q-numbers follow the printed questionnaire exactly. The convention is documented in the F1 generator header and propagates to F3 and F4:

| Item shape | Convention | Example |
|---|---|---|
| Single-item question | `Q{n}_{SHORT}` | `Q3_AGE`, `Q7_OWNERSHIP` |
| Single-item question with sub-fields | `Q{n}_{SHORT_PER_FIELD}` | `Q5_YEARS_AT_FACILITY`, `Q5_MONTHS_AT_FACILITY` |
| Select-all option | `Q{n}_O##_{SHORT}` (zero-padded option index) | `Q121_O01_BUDGET`, `Q121_O02_TIME` |
| Other-specify text | `Q{n}_OTHER_TXT` | `Q121_OTHER_TXT` |
| UHC9 specify branches | `Q{n}_YES_OTHER_TXT`, `Q{n}_NO_OTHER_TXT` | `Q19_NEW_ROLES_YES_OTHER_TXT` |
| Section letters in record names | `{LETTER}_{SECTION_SHORT_NAME}` | `A_FACILITY_HEAD_PROFILE`, `B_FACILITY_PROFILE`, `C_UHC_IMPLEMENTATION` |

All names are UPPER_SNAKE — no spaces, no hyphens, no lowercase. CSPro 8.0 accepts both cases but the F-series settled on upper for consistency with the imported PSA PSGC field names (`R_CODE`, `P_CODE`).

The Q-prefix is non-negotiable — it lets `F1-Skip-Logic-and-Validations.md` reference items by their printed-questionnaire number without ambiguity. A row that says "Q31 EMR_USE" in the spec maps unambiguously to `Q31_EMR_USE` in the dcf.

A note on record / level structure. CSPro External Dictionaries (used for PSGC lookups) have a single-level constraint — you cannot stack levels in an external lookup dcf the way you can in a primary survey dictionary. Khurshid covered this in the Login Application tutorial **(Khurshid 2022-03-27)**: external dictionaries are flat, single-level, and accessed by `loadcase()` rather than via the case tree. Our PSGC dictionaries respect this constraint — each is one level, one ID item, one record.

### 3.4 One-builder-function-per-section pattern

Each F-series section gets its own builder function in `generate_dcf.py`. The function creates one record, populates it with section items, returns it. This keeps records aligned with questionnaire sections and makes per-section changes review-friendly — a Section C bug fix shows up as a diff inside `build_section_c()`.

The skeleton (from F1 `generate_dcf.py`):

```python
def build_section_a():
    Q2_ROLES = [
        ("Rural / Urban Health Unit Head",      "1"),
        ("Physician",                           "2"),
        ("Chief of Hospital",                   "3"),
        ("Medical Director",                    "4"),
        ("Hospital Administrator",              "5"),
        ("Nurse",                               "6"),
        ("Municipal / City Health Officer",     "7"),
        ("Medical Officer",                     "8"),
        ("Administrative Officer / Assistant",  "9"),
        ("Midwife",                            "10"),
        ("Health Promotion / Nutrition Officer","11"),
    ]
    items = [
        # Respondent contact block — moved out of FIELD_CONTROL so it lives
        # with the facility-head profile it describes.
        alpha("RESP_NAME",     "Respondent name and signature", length=80),
        alpha("RESP_POSITION", "Respondent position / office",  length=80),
        alpha("RESP_EMAIL",    "Respondent email address",      length=60),
        alpha("RESP_MOBILE",   "Respondent mobile number",      length=20),

        alpha("Q1_NAME",
              "1. What is your name? (Last Name, First Name, Middle Initial, Ext)",
              length=80),
        select_one("Q2_FACILITY_ROLE",
                   "2. What is your official designation at this health facility?",
                   Q2_ROLES, length=2),
        numeric("Q3_AGE", "3. How old are you (in years), as of your last birthday?",
                length=2),
        numeric("Q4_SEX", "4. What is your sex assigned at birth?", length=1,
                value_set_options=[("Male", "1"), ("Female", "2")]),
        numeric("Q5_YEARS_AT_FACILITY",
                "5. In your current position, how many months/years have you "
                "worked at this health facility? Number of Years",
                length=2),
        numeric("Q5_MONTHS_AT_FACILITY",
                "5. In your current position, how many months/years have you "
                "worked at this health facility? Number of Months",
                length=2),
        numeric("Q6_YEARS_HEALTH",
                "6. How many years have you worked in health-related position? "
                "Number of Years",
                length=2),
        numeric("Q6_MONTHS_HEALTH",
                "6. How many years have you worked in health-related position? "
                "Number of Months",
                length=2),
    ]
    return record("A_FACILITY_HEAD_PROFILE", "A. Facility Head Profile", "2", items)
```

Three properties this layout enforces:

1. **Section-local value sets stay local.** `Q2_ROLES` is defined inside `build_section_a()` because no other section uses it. Reusable value sets (`YES_NO`, `UHC9_OPTIONS`) live at module scope or in `cspro_helpers.py`. The split keeps one-off vs reusable noise out of each other's diffs.
2. **The `record()` call at the bottom binds the section letter.** Section A is record-type `2` (FIELD_CONTROL is `1`), Section B is `3`, etc. — this maps to the dcf `recordType` field which CSEntry uses to disambiguate records on disk.
3. **The order of items inside the record matches the questionnaire's printed order.** Q1 first, then Q2..Q6. The respondent-contact block lives at the top because it's the consent header, not because of any technical reason. Order is the only thing CSPro Designer cares about for form-layout suggestions, so getting it right at generator time saves layout work in Phase 6.

Each F-series file has 8–14 such builders (one per major questionnaire section) plus a `main()` that assembles them:

```python
def main():
    records = [
        build_field_control(),
        build_geo_id("facility"),
        build_section_a(),
        build_section_b(),
        build_section_c(),
        build_section_d(),
        build_section_e(),
        build_section_f(),
        build_section_g(),
        build_section_h(),
        build_secondary_data_stubs(),
        build_facility_capture(),  # GPS + verification photo
    ]
    dictionary = build_dictionary(
        dict_name="FACILITYHEADSURVEY_DICT",
        dict_label="FacilityHeadSurvey",
        id_item_name="QUESTIONNAIRE_NO",
        id_item_label="Questionnaire No",
        id_length=6,
        records=records,
    )
    write_dcf(dictionary, Path(__file__).parent / "FacilityHeadSurvey.dcf")
```

### 3.5 Linked value sets: Designer's pink links vs the Python-module pattern

Khurshid's Linked Value Sets tutorial **(Khurshid 2023-09-12)** describes the GUI-driven approach: define the value set on one item (`EDUCATION_Q3` 1=Yes 2=No), copy it (Ctrl+C), navigate to the second item (`HEALTH_Q1`), paste-link (Ctrl+Alt+V). The linked value sets render in pink in Designer; editing one propagates to all linked items. Adding option `8 = Refused` to the source automatically appears on every linked item.

That's a clean, ergonomic answer to the "update Yes/No options in 50 places" problem, and it's the right answer if you're building in Designer.

The Python pattern in `cspro_helpers.py` achieves the same goal more reproducibly. Define once as a module constant:

```python
YES_NO = [
    ("Yes", "1"),
    ("No",  "2"),
]
```

Then reference it everywhere via the convenience builder:

```python
items.append(yes_no("Q10_HAS_PRIMARY_PKG",  "10. Does the facility have a primary package?"))
items.append(yes_no("Q13_PUBLIC_HEALTH_UNIT", "13. Is there a Public Health Unit?"))
items.append(yes_no("Q16_HEALTH_PROMO_UNIT",  "16. Is there a Health Promotion Unit?"))
# ... 50+ more callsites
```

If the codebook later changes "I don't know" to code 8 instead of 3, you edit one line in `cspro_helpers.py` (or you import a new value set: `YES_NO_REFUSED`), then re-run `python generate_dcf.py`. Every dictionary item updates atomically. Diff-friendly. No clicking through 50 items in Designer.

The trade-off: in Designer, you don't see the "linked value set" pink color. The links are virtual — they exist only in the Python module, not in the dcf JSON itself. The dcf has the value set inlined per item (because that's what CSPro 8.0 stores). Designer has no idea that 50 items share the same Python constant. That's fine — Designer never needs to know, because Designer never edits the dcf.

There is one Designer-specific case where the pink-link mechanic matters: hand-edits to the dcf during demo / scratch work. If you're building a 50-item demo dictionary by hand for a training session, paste-link is faster than re-typing options. For production F-series instruments, the Python pattern wins.

### 3.6 PSGC external lookups — `build_psgc_lookups.py`

`deliverables/CSPro/shared/build_psgc_lookups.py` builds four CSPro external lookup dictionaries (one per PSGC level) plus their fixed-width data files. The script reads CSVs prepared from the PSA 1Q 2026 publication.

#### 3.6.1 Inputs

```
F1/inputs/psgc_region.csv               (18 regions)
F1/inputs/psgc_province_huc.csv         (117 provinces + HUCs)
F1/inputs/psgc_city_municipality.csv    (1658 cities/municipalities)
F1/inputs/psgc_barangay.csv             (42010 barangays)
```

Each CSV has at minimum: `code` (10-digit PSGC), `name` (locality name), and (for non-region rows) `parent_*` (parent's PSGC code). The CSV-prep step lives in `F1/inputs/parse_psgc.py` (not detailed here) and is itself idempotent — run once after each PSA quarterly publication.

#### 3.6.2 Outputs

```
shared/psgc_region.dcf      + psgc_region.dat       (18 rows)
shared/psgc_province.dcf    + psgc_province.dat     (117 rows)
shared/psgc_city.dcf        + psgc_city.dat         (1658 rows)
shared/psgc_barangay.dcf    + psgc_barangay.dat     (42010 rows)
```

Each `.dcf` is a CSPro 8.0 single-level external dictionary. Each `.dat` is a fixed-width text file with one line per `(parent_code, child_code, child_name)` triple — line format `<parent(10)><child_code(10)><child_name(80 left-justified)>`.

#### 3.6.3 Why externalized?

Inlining the 42010-row barangay value set into the F-series dcf would bloat each instrument from ~1 MB to ~17 MB. CSPro Designer chokes on dictionaries that large; tablet sync time multiplies; the dcf becomes unreadable in any text editor.

External lookups solve this by letting the survey dcf carry a length-10 numeric placeholder for `BARANGAY` (etc.) and pulling the actual options at runtime via `loadcase()` keyed on the parent code. The barangay options for a single city/municipality are at most a few hundred — well under any UI threshold.

The shared-folder location (`shared/psgc_*.dcf`) is also load-bearing. F1, F3, and F4 all reference the same files. Republishing PSGC after a PSA boundary change is one re-run of `build_psgc_lookups.py`, and all three instruments inherit the new geography on next sync.

#### 3.6.4 Generation command

```bash
python deliverables/CSPro/shared/build_psgc_lookups.py
```

The script prints diagnostics:

```
PSGC regions: 18 rows
PSGC provinces: 117 rows
PSGC cities/municipalities: 1658 rows
PSGC barangays: 42010 rows
```

#### 3.6.5 Runtime: PSGC-Cascade.apc

`PSGC-Cascade.apc` is the runtime PROC that wires the four lookups into cascading dropdowns on the form. It uses `loadcase()` + `setvalueset()` per CSPro 8.0 patterns. Sketch:

```cspro
PROC REGION
onfocus
   { Load the Region lookup with parent code 0000000000 (root). }
   if loadcase(PSGC_REGION_DICT, "0000000000") then
      setvalueset(REGION, R_CODE, R_NAME);
   endif;
end;

PROC PROVINCE_HUC
onfocus
   { Load provinces under the selected REGION. }
   if loadcase(PSGC_PROVINCE_DICT, REGION) then
      setvalueset(PROVINCE_HUC, P_CODE, P_NAME);
   endif;
end;

PROC CITY_MUNICIPALITY
onfocus
   if loadcase(PSGC_CITY_DICT, PROVINCE_HUC) then
      setvalueset(CITY_MUNICIPALITY, C_CODE, C_NAME);
   endif;
end;

PROC BARANGAY
onfocus
   if loadcase(PSGC_BARANGAY_DICT, CITY_MUNICIPALITY) then
      setvalueset(BARANGAY, B_CODE, B_NAME);
   endif;
end;
```

Three things this enforces:

1. **Parent-child consistency by construction.** A child option list only contains children of the chosen parent — typing barangay code `099912001` under city `0712401` is unrepresentable, because `099912001` isn't in the loaded value set.
2. **No data duplication.** Each PSGC code appears once in `psgc_*.dat` and is referenced by foreign-key (`parent_code`) from the level below. The full 42010-row barangay table is a flat list, not a nested tree.
3. **Refresh on revisit.** Because the lookup is in `onfocus`, revisiting REGION re-fires the dropdown population — useful when an enumerator changes a parent value mid-case.

The `setvalueset()` mechanism Khurshid demonstrates **(Khurshid 2022-07-25)** for dynamic value sets is the same primitive used here, just with `loadcase()`-sourced arrays instead of in-PROC `array hh_name(50)` arrays.

### 3.7 Generator regeneration command

The full per-engagement regeneration recipe:

```bash
# Regenerate primary survey dictionaries
python deliverables/CSPro/F1/generate_dcf.py
python deliverables/CSPro/F3/generate_dcf.py
python deliverables/CSPro/F4/generate_dcf.py

# Regenerate PSGC external lookups (only if PSA published a new PSGC quarter)
python deliverables/CSPro/shared/build_psgc_lookups.py

# Regenerate review workbooks for non-technical sign-off
python deliverables/CSPro/export_dcf_to_xlsx.py --all
```

The `export_dcf_to_xlsx.py --all` script flattens each F-series dcf into a per-instrument Excel review workbook so non-technical reviewers (ASPSI questionnaire owners, DOH stakeholders, Juvy) can review the dictionary as a sortable spreadsheet rather than as JSON. The `--all` flag generates F1, F3, F4 in one shot.

Diagnostics from each generator print record and item counts so a regen visually confirms the dictionary shape:

```
Wrote .../FacilityHeadSurvey.dcf
  Records: 12
  Items:   671
```

If the count drops unexpectedly, the regen has lost something — usually a builder function got commented out or a `select_all()` returned empty. The print line is the cheapest health check.

### Phase 3 exit criteria

- [ ] `.dcf` opens cleanly in CSPro Designer (no parse errors, no orphan items).
- [ ] Item count matches the questionnaire question count, allowing for select-all expansion (each select-all option becomes one Yes/No item) and `_OTHER_TXT` companions.
- [ ] PSGC external lookup dictionaries regenerate cleanly, all four `.dcf` + `.dat` pairs land in `shared/`.
- [ ] Regeneration is one command per F-series instrument.
- [ ] The generator script and the regenerated artifacts are both committed (don't ship the generator without the artifact, or the artifact without the generator).
- [ ] Per-section builder functions match questionnaire section structure (one builder per major section).
- [ ] Review workbooks (`*-DCF-Review.xlsx`) regenerate from `export_dcf_to_xlsx.py --all`.
- [ ] `cspro_helpers.py` constants (value sets) match the F-Series Value Set Conventions (NA = highest code at field width).

---

## Phase 4 — Skip logic and validation spec (the cheap-bug-finding phase)

### 4.1 Why this phase is cheap and important

Walking the spec on paper before opening Designer surfaces dictionary bugs, ambiguous skips, and missing edits while the cost of fixing them is "edit a markdown line." After Designer wiring, the same fix is a regen-and-rewire loop:

| Fix surface | Bug discovered in Phase 4 | Bug discovered after Phase 6 wiring |
|---|---|---|
| Item rename | Edit one line in `generate_dcf.py`, regen | Edit generator, regen, re-open `.fmf` in Designer, drag-drop the renamed item back onto the form, re-test |
| Skip target wrong | Edit one cell in the markdown skip-logic table | Edit table, edit the corresponding `skip to` in `.apc`, regression-test the affected branch |
| Validation tier mistakenly HARD when it should be SOFT | Edit the table cell | Edit `.apc` PROC, find every test case that triggered the HARD path, redo |
| Missing "I don't know exclusivity" rule on a multi-select | Add a row to §4 cross-field rules | Add the row, plus implement the `.apc` exclusivity check, plus add a new test case |

The pattern: every Phase 4 fix is a single-line markdown edit. Every post-Phase-6 fix is a markdown edit *plus* generator change *plus* Designer rewire *plus* test regression. Spending two days on Phase 4 saves a week downstream.

The F-series demonstrated this in practice. F1's first walkthrough surfaced 6 dictionary bugs (the original Apr 10 bug list), F3 surfaced 14, F4 surfaced 13. Every one of those was an edit to either the printed questionnaire or the generator — no Designer or `.apc` work needed. Compare to F1 Bug #5 (informed-consent block missing from FIELD_CONTROL): caught early, fixed in `build_field_control()` with one PR; if it had been caught after wiring, the FIELD_CONTROL form layout would have needed redesign.

### 4.2 The Skip-Logic and Validations document structure

Each F-series instrument has a `<F>-Skip-Logic-and-Validations.md` document. The structure is:

| Section | Content |
|---|---|
| 1. Spec sanity-check findings | Every place the dcf disagrees with the printed questionnaire. F1 had 6, F3 14, F4 13. Each row has Status (OPEN / PARTIAL / CLOSED / CLOSED-BY-DESIGN) and Disposition. |
| 2. Skip-logic table | Every conditional jump. Format: **Trigger → Destination (skip range)**. Where multiple branches collapse to one target, they're merged. |
| 3. Validations | Three-tier classification — HARD, SOFT, GATE — with field-by-field rules. |
| 4. Cross-field consistency rules | Inter-item constraints (e.g. tenure ≤ age − 15; if Q51=No then Q52..Q78 blank). |
| 5. Paste-ready PROC code templates | One template per recurring pattern, ready to drop into `.apc`. |
| 6. Open questions | Unresolved questions for the next stakeholder meeting. |

A real fragment of F1's spec, showing the table format:

```markdown
### Section C — UHC Implementation

| Q | Condition | Skip to |
|---|---|---|
| Q10 HAS_PRIMARY_PKG | = No (2) | Q12 (skip Q11) |
| Q13 PUBLIC_HEALTH_UNIT | = No (2) **or** NA | Q16 (skip Q14, Q15) |
| Q14 PHU_CREATED | ∈ {No-planned, No-no-plans, No-other, IDK, NA} (5–9) | Q16 (skip Q15) |
| Q19 NEW_ROLES | ∈ {5–9} | Q21 (skip Q20) |
| Q31 EMR_USE | ∈ {5–8} (and NA per Bug #4) | Q35 (skip Q32, Q33, Q34) |
```

The columns are deliberately compact — Q-number + descriptor in column 1, the trigger condition in column 2, the destination plus the explicit skip range in column 3. The skip range matters: "skip Q11" tells the Phase 6 PROC author exactly which `skip to` target to write, and tells the Phase 7 tester which question to verify is bypassed.

The `(skip range)` notation also catches range-overlap bugs early. If two rows conflict ("Q10 No → skip Q11" and "Q11 condition → skip Q12") the spec author sees the conflict before opening `.apc`.

A real fragment of the validations table:

```markdown
### 3.2 Section A — Facility Head Profile

| Item | Rule | Severity |
|---|---|---|
| `Q3_AGE` | `18 ≤ age ≤ 90` | HARD |
| `Q3_AGE > 75` | Warn ("Unusually old for an active facility head — confirm") | SOFT |
| `Q5_YEARS_AT_FACILITY` | `0 ≤ y ≤ 60` | HARD |
| `Q5_MONTHS_AT_FACILITY` | `0 ≤ m ≤ 11` | HARD |
| **Tenure ≥ 6 months** | `Q5_YEARS * 12 + Q5_MONTHS ≥ 6` (per IR eligibility) | HARD |
| `Q5_YEARS_AT_FACILITY ≤ Q3_AGE − 18` | Can't have started working before age 18 | HARD |
| `Q6_YEARS_HEALTH ≤ Q3_AGE − 18` | Same age-floor rule | HARD |
| **Tenure consistency** | `Q5_total ≤ Q6_total` (years at this facility cannot exceed total years in any health-related role) | HARD |
```

Every row has a tier. No "we'll figure out the tier later" is allowed — tier is half the spec.

### 4.3 Three-tier validation: HARD / SOFT / GATE

Khurshid's Errmsg and Warning Function tutorial **(Khurshid 2022-06-26)** is the canonical reference for the HARD / SOFT distinction:

> "errmsg = HARD edit check; warning = SOFT edit check. The hard edit check does not allow the interviewer to move on until the inconsistency is fixed."

The F-series adds a third tier: GATE — display-conditional logic that doesn't block or warn, just hides items that don't apply.

| Tier | What it does | CSPro mechanism | UX |
|---|---|---|---|
| HARD | Block + force re-entry | `errmsg(...)` + `reenter` | Modal error; cursor doesn't advance until the value passes |
| SOFT | Warn but allow override | `accept(...)` or `warning(...)` | Confirm-or-override dialog; enumerator can confirm the unusual value and proceed |
| GATE | Display-conditional | `setProperty(..., "visible", ...)` in postproc / display condition | Item invisible when not applicable; no error, no warning, just hidden |

#### 4.3.1 HARD — block + force re-entry

For structurally impossible values: negative ages, gender outside the value set, dates in the future. Use `errmsg` followed by `reenter`:

```cspro
PROC AGE
  if AGE < 0 or AGE > 120 then
    errmsg("Age must be 0-120, you entered %d", AGE);
    reenter;
  endif;
```

The `%d` format specifier embeds the offending value in the message — Khurshid 2022-06-22 shows `%s` for strings, `%d` for integers, `%f` for decimals **(Khurshid 2022-06-22)**.

`reenter` is the CSPro statement that returns control to the field for re-entry. Without it, the cursor advances and the error becomes purely cosmetic.

For F-series item-level HARD checks, the recurring pattern looks like:

```cspro
PROC Q3_AGE
  if Q3_AGE < 18 or Q3_AGE > 90 then
    errmsg("Q3 Age must be between 18 and 90 (per facility head eligibility); you entered %d.", Q3_AGE);
    reenter;
  endif;
```

The 18–90 bound matches the Phase 4 spec table — Q3_AGE has HARD bounds [18, 90] per IR eligibility.

#### 4.3.2 SOFT — warn but allow override

For implausible-but-possible values: age > 110, age at first birth < 12, tenure unusually long. Use `accept(...)`:

```cspro
PROC AGE_AT_FIRST_BIRTH
  if AGE_AT_FIRST_BIRTH < 12 then
    if accept("Age at first birth is %d (unusually low). Confirm?", AGE_AT_FIRST_BIRTH) = 2 then
      reenter;
    endif;
  endif;
```

`accept(...)` returns `1` for the first option (default "Yes" / "Confirm") or `2` for the second ("No" / "Cancel"). When the enumerator picks "No," the `if ... = 2` branch fires `reenter` and forces re-entry. When they pick "Yes," control falls through and the value sticks.

Khurshid notes the partial-save resume semantics **(Khurshid 2022-06-26)**: HARD edits replay on every reopen until fixed; SOFT edits don't. So a partial-save case with a SOFT-warned value reopens cleanly, no re-prompt — the supervisor doesn't have to re-confirm every implausible age. HARD edits, by contrast, replay every time the case is reopened.

This semantics drives tier choice. Use SOFT when:

- The value is plausible enough that a real respondent might genuinely have it.
- Repeated re-prompts on resume would lead to enumerator fabrication ("just enter a normal value to make the warning stop").
- The override is the right answer for some real cases.

Use HARD when:

- The value is structurally impossible (negative numbers in a non-negative field).
- The value violates eligibility (tenure < 6 months at facility — the case shouldn't exist at all).
- Re-prompting on resume is desirable (the supervisor genuinely needs to re-see the inconsistency).

The F1 Q3_AGE rules show both tiers on the same field:

| Item | Rule | Severity |
|---|---|---|
| `Q3_AGE` | `18 ≤ age ≤ 90` | HARD |
| `Q3_AGE > 75` | Warn ("Unusually old for an active facility head — confirm") | SOFT |

The first rule is structural — anything outside [18, 90] is rejected outright. The second rule is plausibility — 75–90 is allowed but flagged for confirmation. The combined PROC:

```cspro
PROC Q3_AGE
  if Q3_AGE < 18 or Q3_AGE > 90 then
    errmsg("Q3 Age must be between 18 and 90; you entered %d.", Q3_AGE);
    reenter;
  endif;
  if Q3_AGE > 75 then
    if accept("Q3 Age %d is unusually old for an active facility head. Confirm?", Q3_AGE) = 2 then
      reenter;
    endif;
  endif;
```

#### 4.3.3 GATE — display-conditional

For items that don't apply to the current case path. The classic case: Section B (Hospital details) is shown only when the facility is hospital-classified.

```cspro
PROC FACILITY_TYPE
  postproc
  if FACILITY_TYPE in 1, 2, 3 then
    setProperty(SECTION_B_HOSPITAL_BLOCK, "visible", true);
  else
    setProperty(SECTION_B_HOSPITAL_BLOCK, "visible", false);
  endif;
```

The `postproc` keyword runs the block after the field's value is committed (vs `preproc` which runs before entry, or onfocus which runs each time the field gains focus). `setProperty(..., "visible", ...)` toggles the form item's visibility — it doesn't affect the dictionary, just the UI.

In the F-series, GATEs are widely used:

- F1 Q66–Q74 are gated on Q65 ("difficulties accreditation") option-by-option. Q66 is shown only if Q65_O01 = "Yes" (budget difficulty selected); Q67 only if Q65_O02 = "Yes"; etc.
- F1 Q132–Q134 are gated on Q8 SERVICE_LEVEL ∈ {Level 1, 2, 3 Hospital}. Primary-care facilities don't see them.
- F1 Q130 is gated on Q8 = Primary Care Facility.
- F1 Q116, Q117 are gated on Q108 = Yes AND Q109 = Yes (multi-condition).

GATE differs from skip in subtle ways:

| | Skip | GATE |
|---|---|---|
| Mechanism | `skip to` in `.apc` advances past the items | `setProperty("visible", false)` hides the items |
| Effect on dictionary | Skipped items become `notappl` | Hidden items still hold any prior value |
| Use case | Linear path advance based on a single trigger | Multi-condition show/hide; option-by-option reveal |
| Typical PROC location | `postproc` of the trigger field | `postproc` of any field whose change affects visibility |

Skip is the right answer when the route is linear — Q10 = No → skip to Q12 — and the reader of the case data should see the bypassed items as `notappl`. GATE is the right answer when items conditionally exist on top of a linear flow — show me Q66–Q74 only for the option(s) the enumerator picked.

### 4.4 Externalized error messages

Khurshid's Error Message Function tutorial **(Khurshid 2022-06-22)** introduces an important refinement over inline `errmsg` strings: move every message into the **Messages tab** of the logic editor, give it a number, and reference it by number.

> "Mark different languages in the file using word `language` with `=` sign followed by the language name. Please do not put space before and after the `=` sign — it will give you error."

The Messages tab pattern:

```
language=English
1001 Q3 Age must be 0-120, you entered %d.
1002 Q5 Tenure cannot exceed Q3 Age minus 18 years.
1003 Spouse age cannot be less than 16 years.
1004 Member %s is under 16; please check the age.

language=Filipino
1001 Ang Q3 Edad ay dapat 0-120, ikaw nag-enter ng %d.
1002 Ang Q5 Tagal ng tenure ay hindi maaaring lumampas sa Q3 Edad minus 18 taon.
1003 Ang edad ng asawa ay hindi maaaring kulang sa 16 taon.
1004 Ang miyembro %s ay below 16; suriin po ang edad.
```

Then in PROC:

```cspro
PROC Q3_AGE
  if Q3_AGE < 0 or Q3_AGE > 120 then
    errmsg(1001, Q3_AGE);  { Message 1001: "Q3 Age must be 0-120, you entered %d" }
    reenter;
  endif;
```

Three reasons this matters for the F-series:

#### 4.4.1 Translation

The UHC Survey Year 2 plan calls for 7 dialects (English plus 6 Philippine languages). Inline `errmsg("...")` strings would mean 7 copies of every PROC — one per language — and the codebase becomes unreadable. The Messages tab moves all 7 versions into one numbered table, switched by `setlanguage()` at runtime.

CSPro's `tr()` and `maketext()` wrappers **(Khurshid 2022-06-22)** let numeric message IDs be used in select / accept caption slots that demand alpha expressions:

```cspro
select(continue,
   tr(105),    { "Make correction in household head gender" }
   tr(106));   { "Make correction in spouse gender" }
errmsg(104);
```

Without the wrapper, the compiler complains "alpha expression expected." `tr()` and `maketext()` are interchangeable.

#### 4.4.2 Maintenance

Wording changes: typo in a message, awkward translation, ASPSI requests a softer phrasing. With inline strings, you grep for the typo, hit 30 callsites, and edit all of them — risky. With the Messages tab, you edit row 1001 in one place.

#### 4.4.3 Format specifier discipline

Inline strings tempt you to skip the `%s` / `%d` discipline. The Messages tab forces you to think about argument order:

```
1004 Member %s is under 16; please check the age.
```

In PROC:

```cspro
errmsg(1004, NAME);   { %s ← NAME }
```

Argument count and types must match the format specifiers exactly — fewer args than `%`s prints literal `%s`. Mixing `%s` with a numeric arg displays a garbled value.

For numeric:

```
1005 Member %d (age %d) failed eligibility.
```

In PROC:

```cspro
errmsg(1005, MEMBER_PID, MEMBER_AGE);
```

A numbering scheme that scales: reserve blocks of 100 IDs per section. F1 Section A errors live in 1001–1099, Section B in 1101–1199, etc. F3 starts at 3001, F4 at 4001, so cross-instrument message tables are mergeable without renumbering.

#### 4.4.4 Override system messages — `OnSystemMessage`

The same tutorial covers overriding CSPro's built-in system messages **(Khurshid 2022-06-22)**:

```cspro
function OnSystemMessage(numeric message_number)
   recode message_number;
      8889 => false;     { suppress system message 8889 "out of range" }
      else => true;      { let other system messages display }
   endrecode;

   if message_number = 8889 then
      errmsg(110);   { user-defined replacement: "Please enter a valid value" }
   endif;
end;
```

CSPro's default messages are technically correct but enumerator-unfriendly (e.g. "out of range" without saying which range). `OnSystemMessage` lets the project replace them with better wording. Use sparingly — suppressing the wrong message can mask genuine errors during desk testing. Open the messages reference file in the CSPro install folder to find the exact numbers worth overriding.

For F-series, plausible overrides include:

- 8889 ("out of range") → project-specific "Please enter a valid value within the printed range."
- Any "alpha required" / "numeric required" message → softer "Please enter <type>."

Don't override messages whose default phrasing is genuinely useful (date-format errors, etc.).

### 4.5 Cross-field validation

Cross-field rules — constraints that span multiple items — get their own subsection in the Skip-Logic spec because they don't fit the per-item table. F-series examples:

#### 4.5.1 Tenure ≤ age − 15 (or age − 18)

A facility head can't have started working before reaching working age. The F1 spec uses age − 18 (legal minimum employment age in the Philippines), F4 uses age − 15 for general work history.

```cspro
PROC Q5_YEARS_AT_FACILITY
  postproc
  if Q5_YEARS_AT_FACILITY > Q3_AGE - 18 then
    errmsg(1010, Q5_YEARS_AT_FACILITY, Q3_AGE);  { "Q5 tenure %d years exceeds Q3 age %d - 18." }
    reenter;
  endif;
```

The trigger lives in `postproc` of the dependent field (`Q5_YEARS_AT_FACILITY`), checked after the value is committed. If `Q3_AGE` is later edited to a smaller number, the rule fires again on that field's `postproc`:

```cspro
PROC Q3_AGE
  postproc
  if Q5_YEARS_AT_FACILITY > Q3_AGE - 18 then
    errmsg(1010, Q5_YEARS_AT_FACILITY, Q3_AGE);
    reenter;
  endif;
```

Either field's postproc enforces the joint constraint.

#### 4.5.2 If Q51 = No, Q52..Q78 must be blank

Section D's gate: if the facility didn't accredit YAKAP/Konsulta (Q51 = No), the entire Q52..Q78 sub-tree should be skipped. Phase 4 spec encodes this as a skip; Phase 6 PROC enforces it as a cleanup gate:

```cspro
PROC Q51_YK_ACCRED
  postproc
  if Q51_YK_ACCRED = 2 then  { No }
    skip to Q79_INTEND_ACCRED;
    { Cleanup: zero out any Q52..Q78 values that may have been entered before Q51 was answered. }
    Q52_FIRST_ACCRED_DATE = notappl;
    Q53_LATEST_ACCRED_DATE = notappl;
    { ... etc ... }
  endif;
```

Combining `skip to` (advance past the block) with explicit `= notappl` assignments (clear stale values) is the safe pattern. Without the assignments, edit-back behavior — enumerator answers Q53, then changes Q51 to No — would leave stale Q53 data.

For the analyst-side check (after fieldwork), a CSBatch consistency rule re-confirms: "if Q51 = 2 then Q52..Q78 must all be `notappl`."

#### 4.5.3 "I don't know" exclusivity in multi-select

Multi-select questions where one option is "I don't know" need to be exclusive — the enumerator can't pick "Budget" AND "Time" AND "I don't know" simultaneously, since the latter contradicts the former.

```cspro
PROC Q121_DOH_LIC_DIFFICULT_O09
  postproc  { Option 9: "I don't know" }
  if Q121_O09 = 1 then  { selected }
    if Q121_O01 = 1 or Q121_O02 = 1 or Q121_O03 = 1 or Q121_O04 = 1 or
       Q121_O05 = 1 or Q121_O06 = 1 or Q121_O07 = 1 or Q121_O08 = 1 then
      errmsg(1015);  { "I don't know is exclusive — uncheck other options first." }
      reenter;
    endif;
  endif;
```

The same pattern catches "None of the above" exclusivity:

```cspro
PROC Q121_O00_NONE
  postproc
  if Q121_O00_NONE = 1 then
    if Q121_O01 = 1 or Q121_O02 = 1 or ... then
      errmsg(1016);  { "None of the above is exclusive." }
      reenter;
    endif;
  endif;
```

#### 4.5.4 Date ordering

`DATE_FINAL_VISIT ≥ DATE_FIRST_VISITED`. Both length-8 YYYYMMDD numerics:

```cspro
PROC DATE_FINAL_VISIT
  postproc
  if DATE_FINAL_VISIT < DATE_FIRST_VISITED then
    errmsg(1020, DATE_FINAL_VISIT, DATE_FIRST_VISITED);
    reenter;
  endif;
```

#### 4.5.5 Sum of expenditure categories within ±5% of declared total income (F4)

F4 household budget reconciliation: each expenditure category sums to a total that should match (within tolerance) the declared monthly income.

```cspro
PROC TOTAL_EXPENDITURE
  postproc
  numeric category_sum;
  category_sum = EXP_FOOD + EXP_HOUSING + EXP_HEALTH + EXP_EDUCATION +
                 EXP_TRANSPORT + EXP_OTHER;
  if abs(category_sum - TOTAL_INCOME) / TOTAL_INCOME > 0.05 then
    if accept("Total expenditure (%f) differs from declared income (%f) by more than 5%%. Confirm?",
              category_sum, TOTAL_INCOME) = 2 then
      reenter;
    endif;
  endif;
```

This is SOFT, not HARD — household budgets legitimately don't always balance (savings, debt, in-kind, gifts), so the override matters.

### 4.6 Sentinel ID convention

Khurshid's Dynamic Value Set tutorial **(Khurshid 2022-07-25)** introduces a useful pattern for roster-augmenting questions: reserve member-IDs ≤60 for the printed roster, ≥61 for off-roster guardians added at runtime.

> "Because the maximum number we can enter in the sequence is 60, I am using guardian ID from 61 onwards. If the guardians are not household members, we can add them. In that case, the number will begin with 61 and is generated automatically based on the maximum available ID after 60."

The pattern lets the dynamic value set distinguish "in roster" from "freshly added":

```cspro
PROC GUARDIAN_LOOKUP
onfocus
  numeric next_id;
  next_id = max(GUARDIAN_PID where GUARDIAN_NAME is not empty) + 1;
  if next_id < 61 then
    next_id = 61;  { Floor — off-roster IDs start at 61 }
  endif;
  { ... build dynamic value set with guardian options + next_id sentinel ... }
end;
```

Anyone reading raw data later sees "GUARDIAN_PID = 63" and knows it's an off-roster guardian — the convention is encoded in the data itself.

For UHC Survey Year 2, the F4 household instrument is the most likely place this pattern applies. F4 has a household roster + a respondent-identification step where the chosen respondent might be an off-roster guardian (extended family, in-laws). Whether F4 needs the 60/61+ split depends on the printed F4 roster cap — if F4 caps at 30 members, the threshold becomes 30/31+. The pattern is the same; the cutoff number is questionnaire-specific.

The convention must be documented in the F4 codebook — "GUARDIAN_PID ≥ 31 = off-roster guardian, added at runtime." Otherwise an analyst reading raw data has no way to interpret the elevated IDs.

### 4.7 Open-questions discipline

Every spec ends with an "Open questions" section. These are unresolved questions that didn't block Phase 5 work but need stakeholder input before Phase 6 build can start. Routing them at this stage avoids the worst Phase 6 failure mode: the enumerator pretest catches an issue that the spec author already knew about.

Walk the current state:

- F1: Sub-bug list is now closed; remaining items are flagged in `generate_dcf.py` as `PENDING_DESIGN_*` constants (Q63 ACCRED_WAIT day-vs-month bucket mismatch routed to Juvy/Kidd; Q166 PD_NURSES list pending ASPSI sign-off; secondary-data structure pending Juvy/Kidd decision).
- F3: Q31 IP_GROUP open-question routed to Juvy. Several other rows open at the time of writing.
- F4: 3 questions to ASPSI, tracked in `F4-Skip-Logic-and-Validations.md` §6.

Don't list contents here — the per-instrument spec files are the source of truth. Just point to them: see `F1-Skip-Logic-and-Validations.md`, `F3-Skip-Logic-and-Validations.md`, `F4-Skip-Logic-and-Validations.md`.

The discipline: every open question has a named owner (Juvy, Kidd, ASPSI rep) and a target close date. Open questions older than 30 days get escalated. The point of the section is to prevent silent spec rot — questions accumulating in the spec-author's head with no commit on the answers.

### Phase 4 exit criteria

- [ ] Every conditional in the questionnaire is documented in §2 Skip-logic table with a Trigger / Destination / skip-range entry.
- [ ] Every validation has a tier (HARD / SOFT / GATE) — no "TBD tier" rows.
- [ ] Every recurring pattern has a paste-ready code template in §5.
- [ ] Cross-field rules are listed in §4 with their PROC location (which field's postproc enforces them).
- [ ] §1 sanity-check findings table has every spec / dcf / questionnaire mismatch, with Status and Disposition.
- [ ] §6 open-questions has named owners and target close dates.
- [ ] Externalized error message numbering scheme is established (e.g. 1001+ for F1, 3001+ for F3, 4001+ for F4).
- [ ] The spec is readable end-to-end as a paper walkthrough — a reviewer can follow it without opening the dcf.

---

## Phase 5 — Spec / dictionary corrections

Phase 5 is the loop that closes Phase 4. Every finding from §1 of the Skip-Logic spec gets either fixed or explicitly deferred. The mechanics differ depending on whether fieldwork has started.

### 5.1 Pre-fieldwork corrections (the easy case)

Before any enumerator has entered a real case, the dictionary is a build artifact — regenerating it costs nothing.

The recipe:

1. Apply each bug fix to the **generator** (`generate_dcf.py`), NOT to the `.dcf` directly.
   - Item rename: edit the `numeric()` / `alpha()` / `select_one()` call.
   - Item missing: add the call inside the right `build_section_*()` function.
   - Value-set wrong: edit the value-set list (module-level constant if shared, or section-local if not).
   - Length wrong: edit the `length=` argument.
   - PSGC structure changed: regenerate `psgc_*.dcf` via `python build_psgc_lookups.py`.

2. **Regenerate** v2 of the dcf:

```bash
python deliverables/CSPro/F1/generate_dcf.py
```

3. **Open in Designer** to verify item properties — length, decimals, value-set bindings, ID items, sub-items, value-set assignments. Designer's tree view is the cheapest visual check that the dcf is well-formed.

4. **Run Designer's dictionary lint** if available. CSPro 8.0 has a "Validate Dictionary" command in the Tools menu that flags structural issues (orphan value sets, items without labels, duplicate names).

5. **Update the spec.** Mark the corresponding §1 finding as CLOSED. Add a one-line disposition: "Fixed in `generate_dcf.py` — `Q5_YEARS_AT_FACILITY` length raised from 1 to 2."

The whole loop, end-to-end, is single-digit minutes for a single-bug fix. For a batch (10+ bugs) it's an hour. The point is that nothing in Phase 5 pre-fieldwork is destructive — the dcf is a build artifact and rebuilds are cheap.

### 5.2 Fieldwork-time corrections (the hard case)

Once enumerators have entered cases, the dictionary is no longer just a build artifact — it's the schema that on-disk data is aligned to. You cannot just regenerate.

Khurshid covers this in the Data Reformatting tutorial **(Khurshid 2023-09-21)**:

> "It is clear from this that when making structure changes while using the CSDB format, the data file remains unaffected, unlike the case with text file."

The CSDB / DAT split matters:

| Format | Behavior on length change | Behavior on item-add | Behavior on item-remove |
|---|---|---|---|
| `.csdb` | Self-adjusts; old cases remain readable | Old cases get the new item as blank | Old cases lose the dropped item's data |
| `.dat` | Mis-aligned; old cases unreadable | All cases need reformatting | All cases need reformatting |

**Decision: use `.csdb` for active fieldwork data.** Reserve `.dat` for archival / interchange where the schema is frozen. The F-series data files are `.csdb` for this reason.

But CSDB isn't immune. Major schema rewrites — item-remove, item-type-change, record-restructure — still need the Reformat Data tool.

#### 5.2.1 Khurshid's Reformat Data flow

The tool lives at **Tools → Reformat Data** in CSPro. The dialog has four file fields:

1. **Input dictionary** — the **backup** of the old dictionary (untouched, pre-change).
2. **Input data file** — the existing data file aligned to the old dictionary.
3. **Output dictionary** — the new modified dictionary.
4. **Output data file** — a new file path for the reformatted result.

Click **Reformat Data**. A summary report indicates rows reformatted.

Khurshid's gotcha **(Khurshid 2023-09-21)**:

> "In the first dictionary input box, enter the name of the dictionary that you backup before making any changes."

Without that backup, you cannot run reformat correctly. Always back up the dictionary before any structural change.

#### 5.2.2 The CRITICAL workflow rule

The order of operations matters and the bad path is silently destructive **(Khurshid 2023-09-21)**:

> "Through this exercise, we have reached the conclusion that it is important to reformat the text data first and then proceed with entering the data into the newly updated data file."

The correct workflow:

```
1. Backup the dictionary (copy FacilityHeadSurvey.dcf to FacilityHeadSurvey-v1.dcf-backup).
2. Modify the dictionary (regenerate via generate_dcf.py).
3. Run the Reformat Data tool with old/new dictionaries + old/new data files.
4. NOW you can enter new cases into the new data file.
```

The wrong workflow (data loss):

```
1. Modify the dictionary (no backup).
2. Insert new cases into the existing data file.
3. Try to run Reformat Data — old cases corrupt + cannot be recovered.
```

Treat Reformat Data as the first thing you run after any dictionary structural change.

#### 5.2.3 Paste-ready PFF for Reformat Data

CSPro's Reformat Data tool is also scriptable via a `.pff` (Project / Process File). For the F-series, the PFF would look like:

```
[Run Information]
Type=Reformat
Version=CSPro 8.0
AppName=ReformatF1
AppVersion=2.0

[Files]
InputDictionary=C:\survey\backup\FacilityHeadSurvey-v1.dcf
InputData=C:\survey\data\FacilityHeadSurvey.csdb
OutputDictionary=C:\survey\FacilityHeadSurvey.dcf
OutputData=C:\survey\data\FacilityHeadSurvey-v2.csdb

[Parameters]
ViewListing=Yes
```

Double-click the PFF (or run it via `cspro reformat.pff`) and the tool runs unattended. Useful when you need to reformat a batch of N tablets' data files — automate the per-tablet runs with a scripted PFF generator.

#### 5.2.4 SOP: fieldwork-time correction step-by-step

Codify the workflow as an SOP so any team member can run it under pressure:

1. **Freeze data ingest.** Stop sync from tablets. Pause CSWeb sync if running. Tell enumerators to pause new case entry. (You don't want races between the reformat run and incoming syncs.)
2. **Backup.** Copy the current `.dcf` to `<dcf>-v1-backup-YYYYMMDD.dcf`. Copy the current `.csdb` to `<csdb>-v1-backup-YYYYMMDD.csdb`. Verify both copies open.
3. **Apply the generator change.** Edit `generate_dcf.py`. Commit the change with a clear message that names the bug (e.g. "Fix #14: Q42 NBB length 1 → 2 to accommodate codes 10-15").
4. **Regenerate.** `python deliverables/CSPro/F1/generate_dcf.py` — verify the new `.dcf` opens in Designer. Confirm item count delta matches expectations.
5. **Run Reformat Data.** Either via the GUI (Tools → Reformat Data) or via the PFF above. Confirm the summary report shows the expected case count migrating.
6. **Verify a sample case.** Open the new `.csdb` in CSEntry; navigate to a sample case; confirm fields align correctly. Spot-check the changed item — does the migrated value look right?
7. **Distribute the new dcf + new csdb.** Push to all tablets. Wait for confirmation that every tablet is on the new schema before resuming sync.
8. **Resume data ingest.** Re-enable CSWeb sync. Tell enumerators to resume.
9. **Update the spec.** Mark the §1 finding CLOSED with a note: "Schema migrated via Reformat Data on YYYY-MM-DD; %N% cases migrated."

This is a heavy procedure. Run it at most weekly (e.g. only as a scheduled hot-fix window), not opportunistically. Multiple corrections should batch into one Reformat run.

### 5.3 Alternative — keep both old and new items, drop old from form

Khurshid's Data Reformatting tutorial **(Khurshid 2023-09-21)** offers a non-breaking alternative for additive schema changes:

> "Keep the old items (Q2, Q4) in the dictionary at their original positions and lengths, add new items (Q2_1, Q4_1) with the larger sizes, then remove only the old items from the form layout (not from the dictionary)."

The mechanics:

1. In the dictionary: copy `Q2` (original 35 chars) → paste after the last item → rename to `Q2_1` → resize to 45.
2. Same for any other item that needs evolution: `Q4` → `Q4_1` (3 chars).
3. Open the form in design view → delete `Q2` and `Q4` from the form layout (they remain in the dictionary at their original byte positions).
4. Drag-drop `Q2_1` and `Q4_1` from the dictionary onto the form, in the same visual positions where Q2 and Q4 used to be.

Result: existing cases keep their `Q2` / `Q4` values intact; new cases populate `Q2_1` / `Q4_1` (the originals stay empty for new cases). Analysis combines them with `coalesce(Q2, Q2_1)` style logic.

When this approach wins:

- The change is **additive** (rename, expand, add value to a value set, type-compatible).
- Fieldwork is already in progress and the Reformat Data downtime isn't acceptable.
- The data team can handle a "two columns, one logical field" pattern in analysis.

When it loses:

- The change is **removing** an item or **changing its type** — additive trick doesn't help.
- The instrument has a long-lived rev cycle; the dictionary accumulates `Q2_1`, `Q2_2`, `Q2_3`, etc. Mess in two reformats; chaos in five.
- Tabulation needs to know about both columns, requiring per-tab `coalesce()` logic.

For F-series UHC Y2, the additive trick is the right answer for any mid-fieldwork length expansion — e.g. discovering that `RESP_NAME` at length 80 truncates some Filipino names with multiple suffixes, and we need length 120. Add `RESP_NAME_1` at 120, drop `RESP_NAME` from the form, ship the patch. No reformat needed; existing data preserved.

For removals (e.g. ASPSI decides Q121 is unused and should be dropped), Reformat Data is the right answer. The clean schema beats two columns of chaff.

### 5.4 Decision tree: when to use which approach

```
                          A correction is needed.
                                    │
                ┌───────────────────┴───────────────────┐
                │                                       │
        Pre-fieldwork?                          Post-fieldwork?
                │                                       │
        Edit generate_dcf.py.                  Is the change additive
        Regenerate.                            (rename / expand / add)?
        Verify in Designer.                            │
        Update spec.                    ┌──────────────┴──────────────┐
                                        │                             │
                                       Yes                            No
                                        │                             │
                              Use the "keep both        Use Reformat Data tool.
                              items, drop from form"    Backup + run Reformat
                              alternative.              + verify + distribute.
                              Cheaper.                  Run as scheduled
                                                        downtime window.
```

A more compact heuristic:

| Stage | Type of change | Approach |
|---|---|---|
| Pre-fieldwork | Any | Regenerate |
| Post-fieldwork | Additive (rename / expand / add value) | Keep-both |
| Post-fieldwork | Breaking (remove / type-change / restructure) | Reformat Data |
| Post-fieldwork | Cosmetic (label change only, no structural impact) | Just edit, no migration |

The cosmetic case is worth calling out — relabeling an item's prompt text, fixing a typo in an option label, refining a value-set caption — none of these touch the data layout. Edit, regenerate, redistribute the dcf. CSEntry happily reads existing `.csdb` against the relabeled dcf.

### 5.5 Tracking — every fix gets a generator commit + spec markdown update

The bug list from Phase 4 is the audit trail. When a bug is fixed:

1. **Mark CLOSED in the spec.** Update §1's table row Status from `OPEN` / `PARTIAL` to `CLOSED` (or `CLOSED-BY-DESIGN` if the original framing was wrong).
2. **Link to the generator change.** In Disposition, name the function and the line: "Fixed in `build_section_a()`, `Q5_YEARS_AT_FACILITY` length raised from 1 to 2."
3. **Record the data migration step if any.** "Schema migrated via Reformat Data on 2026-04-30; 247 cases migrated cleanly."

The spec evolves into a closed-bug ledger. By the end of fieldwork, §1 should show CLOSED on every original finding plus any new ones surfaced during fieldwork.

A real example from F1 §1.A:

| # | Item | Status | Disposition |
|---|---|---|---|
| 4 | **Q31 EMR — `Not applicable` skip** | CLOSED | `Q31_NA_SKIPS = True`. Handled in CAPI `PROC Q31_EMR_USE` (§4.4 pattern) — NA routes to Q35 alongside the other UHC9 NA branches. |
| 5 | **Informed-consent block** | CLOSED | `CONSENT_GIVEN` added to `FIELD_CONTROL`; `RESP_NAME` / `RESP_POSITION` / `RESP_EMAIL` / `RESP_MOBILE` live at the top of `A_FACILITY_HEAD_PROFILE` (moved out of FIELD_CONTROL so they sit next to the facility-head profile they describe). Consent=No aborts the interview. |
| 6 | **Tenure ≥6 months pre-filter** | CLOSED-BY-DESIGN | Enforced in `PROC Q5_MONTHS_AT_FACILITY postproc` (§4.2), not as a separate screening item. Tenure below 6 months terminates and sets `ENUM_RESULT = Refused/Incomplete`. |

The pattern: every CLOSED row says exactly what changed and where. A future reader (or your future self in three months) can trace the disposition back to the generator code without spelunking.

For long-lived projects, this is the single most valuable artifact in the deliverables folder — more than the dcf, more than the PROC code. It's the record of every decision and every reversal.

### Phase 5 exit criteria

- [ ] Every Phase 4 finding has Status `CLOSED` / `CLOSED-BY-DESIGN` / `OPEN-with-named-owner`.
- [ ] Pre-fieldwork: regenerated dcf passes Designer's "Validate Dictionary" check.
- [ ] Pre-fieldwork: regenerated dcf opens cleanly in Designer (no parse errors).
- [ ] Post-fieldwork breaking changes: Reformat Data run, sample case verified, distribution complete.
- [ ] Post-fieldwork additive changes: form layout updated to point at the new items; old items remain in the dictionary at their original positions.
- [ ] Spec markdown §1 disposition column lists the generator function and item names that changed.
- [ ] No silent edits to the dcf — every change is traceable through `generate_dcf.py` (or, in the additive trick case, through the Designer form-layout edit log).
- [ ] If Reformat Data was run: the backup pre-change dcf and pre-change csdb are preserved as `<name>-v<N>-backup-YYYYMMDD.<ext>`.

---

## Cross-references

- [[2_Areas/IT-Standards/templates/CAPI-Development-Workflow]] — canonical workflow template; phases 3-5 are documented there as the mode-agnostic structure with CAPI-specific code.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F-Series Value Set Conventions]] — NA-coding convention.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/cspro_helpers]] — the shared module behind every F-series generator.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/F1/F1-Skip-Logic-and-Validations]] — the F1 spec.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/F3/F3-Skip-Logic-and-Validations]] — the F3 spec.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/F4/F4-Skip-Logic-and-Validations]] — the F4 spec.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/shared/build_psgc_lookups]] — PSGC external-lookup builder.

## Mentor citations

- **(Khurshid 2022-03-27)** — CSPro External Dictionary single-level constraint (Login Application tutorial).
- **(Khurshid 2022-06-22)** — Error Message Function: externalize messages with numbered IDs, format specifiers `%s` `%d` `%f`, `tr()` / `maketext()` for alpha-context wrappers, `OnSystemMessage` for system-message override.
- **(Khurshid 2022-06-26)** — Errmsg vs Warning: HARD vs SOFT distinction; `errmsg` + `reenter` blocks; partial-save resume semantics.
- **(Khurshid 2022-07-25)** — Dynamic Value Set: `setvalueset()` from runtime arrays; `seek(@(n+1), ...)` nth-occurrence; `count()` predicate aggregate; sentinel ID convention (60-cap with 61+ for off-roster guardians).
- **(Khurshid 2023-09-12)** — Linked Value Sets: GUI-driven Ctrl+Alt+V "Paste Value Set Link"; pink color in Designer; Remove Value Set Link.
- **(Khurshid 2023-09-21)** — Data Reformatting: CSDB resilience to length changes vs DAT mis-alignment; Tools → Reformat Data with old + new dictionaries; reformat-first-then-enter rule; alternative additive trick (keep both items, drop old from form).

---

## Next

[[04-Phase-6-Build-CAPI-App]]
