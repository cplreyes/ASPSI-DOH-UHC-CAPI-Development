# F3/F4 Data Dictionary Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build CSPro 8.0 data dictionary generators for F3 (Patient Survey) and F4 (Household Survey) by extracting shared helpers from F1 and creating instrument-specific generators.

**Architecture:** Extract reusable helpers, value sets, and common record builders from F1's `generate_dcf.py` into a shared `cspro_helpers.py` module. Each instrument gets its own generator that imports from the shared module and only contains instrument-specific section builders. F1 is refactored to import from the shared module with a mandatory identity-diff check.

**Tech Stack:** Python 3.x, CSPro 8.0 JSON dictionary format, PyMuPDF (fitz) for PDF text extraction.

---

## File Structure

| Action | Path | Purpose |
|--------|------|---------|
| Create | `deliverables/CSPro/cspro_helpers.py` | Shared helpers, value sets, common record builders |
| Modify | `deliverables/CSPro/F1/generate_dcf.py` | Replace moved code with imports from cspro_helpers |
| Create | `deliverables/CSPro/F3/inputs/F3_clean.txt` | Text extraction from F3 PDF |
| Create | `deliverables/CSPro/F3/generate_dcf.py` | F3 section builders (A-L), imports cspro_helpers |
| Create | `deliverables/CSPro/F4/inputs/F4_clean.txt` | Text extraction from F4 PDF |
| Create | `deliverables/CSPro/F4/generate_dcf.py` | F4 section builders (A-Q), imports cspro_helpers |
| Unchanged | `deliverables/CSPro/F1/FacilityHeadSurvey.dcf` | Must remain byte-identical after refactor |

All paths are relative to `analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/`.

---

### Task 1: Create `cspro_helpers.py` — shared helpers and value sets

**Files:**
- Create: `deliverables/CSPro/cspro_helpers.py`

- [ ] **Step 1: Create the shared helpers module**

This file extracts all reusable code from F1's `generate_dcf.py` lines 42-258. The helpers, value sets, and common record builders are moved here verbatim. `build_field_control` and `build_geographic_id` gain parameters for per-instrument customization.

```python
"""
cspro_helpers.py — Shared helpers for CSPro 8.0 data dictionary generators.

Extracted from F1/generate_dcf.py. All F-series generators import from here.
"""

import json
from pathlib import Path

# ============================================================
# 1. SHARED VALUE SETS
# ============================================================

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
    ("Weekly",         "1"),
    ("Monthly",        "2"),
    ("Quarterly",      "3"),
    ("Semi-annually",  "4"),
    ("Annually",       "5"),
    ("Other (specify)","6"),
]

WHY_DIFF_OPTIONS = [
    ("Not enough budget / too expensive",  "1"),
    ("Time-consuming",                     "2"),
    ("Limited human resources",            "3"),
    ("Legal processes",                    "4"),
    ("Compiling documentary requirements", "5"),
    ("Stringent standards",                "6"),
    ("Lack of training",                   "7"),
    ("Lack of space",                      "8"),
    ("Other (specify)",                    "9"),
]

SATISFACTION_5PT = [
    ("Very Satisfied",                    "1"),
    ("Satisfied",                         "2"),
    ("Neither Satisfied nor Dissatisfied","3"),
    ("Dissatisfied",                      "4"),
    ("Very Dissatisfied",                 "5"),
    ("Not applicable",                    "9"),
]


# ============================================================
# 2. HELPER FUNCTIONS — emit CSPro 8.0 dictionary objects
# ============================================================

def _value_set(name_prefix, label, options):
    return {
        "name": f"{name_prefix}_VS1",
        "labels": [{"text": label}],
        "values": [
            {"labels": [{"text": text}], "pairs": [{"value": code}]}
            for text, code in options
        ],
    }

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

def record(name, label, record_type, items, max_occurs=1, required=True):
    return {
        "name": name,
        "labels": [{"text": label}],
        "recordType": record_type,
        "occurrences": {"required": required, "maximum": max_occurs},
        "items": items,
    }


# ============================================================
# 3. COMMON RECORD BUILDERS
# ============================================================

ENUM_RESULT_OPTIONS = [
    ("Completed",  "1"),
    ("Postponed",  "2"),
    ("Refused",    "3"),
    ("Incomplete", "4"),
]

def build_field_control(extra_items=None, date_label_entity="the Facility"):
    """Build the FIELD_CONTROL record.

    Args:
        extra_items: List of additional items to append (e.g., patient listing
                     reference for F3, HH listing reference for F4).
        date_label_entity: Entity name for date labels. F1 uses "the Facility",
                          F3 uses "the Patient", F4 uses "the Household".
    """
    items = [
        alpha("SURVEY_TEAM_LEADER_S_NAME",      "Survey Team Leader's Name",                    length=50),
        alpha("ENUMERATOR_S_NAME",              "Enumerator's Name",                            length=50),
        alpha("FIELD_VALIDATED_BY",             "Field Validated by",                           length=50),
        alpha("FIELD_EDITED_BY",                "Field Edited by",                              length=50),
        numeric("DATE_FIRST_VISITED",
                f"Date First Visited {date_label_entity} (YYYYMMDD)", length=8),
        numeric("DATE_FINAL_VISIT",
                f"Date of Final Visit to {date_label_entity} (YYYYMMDD)", length=8),
        numeric("TOTAL_NUMBER_OF_VISITS",       "Total Number of Visits",                       length=3),
        numeric("ENUM_RESULT_FIRST_VISIT",      "Result of First Visit",                        length=1,
                value_set_options=ENUM_RESULT_OPTIONS),
        numeric("ENUM_RESULT_FINAL_VISIT",      "Result of Final Visit",                        length=1,
                value_set_options=ENUM_RESULT_OPTIONS),
        numeric("CONSENT_GIVEN",                "Informed consent given",                       length=1,
                value_set_options=YES_NO),
    ]
    if extra_items:
        items.extend(extra_items)
    return record("FIELD_CONTROL", "Field Control", "A", items)


def _psgc_fields():
    """Common PSGC geographic fields shared by all instruments."""
    return [
        numeric("REGION",            "Region",              length=2, zero_fill=True),
        numeric("PROVINCE_HUC",      "Province / HUC",      length=3, zero_fill=True),
        numeric("CITY_MUNICIPALITY", "City / Municipality",  length=4, zero_fill=True),
        numeric("BARANGAY",          "Barangay",            length=4, zero_fill=True),
    ]


def build_geo_id(mode="facility", extra_items=None):
    """Build geographic identification record.

    Args:
        mode: One of "facility", "facility_and_patient", "household".
        extra_items: Additional items to append.
    """
    if mode == "facility":
        items = [
            numeric("CLASSIFICATION", "Classification", length=1, value_set_options=[
                ("UHC IS",     "1"),
                ("Non-UHC IS", "2"),
            ]),
            *_psgc_fields(),
            alpha("LATITUDE",   "Latitude",  length=12),
            alpha("LONGITUDE",  "Longitude", length=12),
        ]
        rec_name = "HEALTH_FACILITY_AND_GEOGRAPHIC_IDENTIFICATION"
        rec_label = "Health Facility and Geographic Identification"

    elif mode == "facility_and_patient":
        items = [
            numeric("CLASSIFICATION", "Classification", length=1, value_set_options=[
                ("UHC IS",     "1"),
                ("Non-UHC IS", "2"),
            ]),
            # Facility geo
            *_psgc_fields(),
            alpha("FACILITY_NAME",    "Name of Health Facility",   length=120),
            alpha("FACILITY_ADDRESS", "Address of Health Facility", length=120),
            # Patient home address
            numeric("P_REGION",            "Patient Home Region",              length=2, zero_fill=True),
            numeric("P_PROVINCE_HUC",      "Patient Home Province / HUC",      length=3, zero_fill=True),
            numeric("P_CITY_MUNICIPALITY", "Patient Home City / Municipality",  length=4, zero_fill=True),
            numeric("P_BARANGAY",          "Patient Home Barangay",            length=4, zero_fill=True),
        ]
        rec_name = "PATIENT_GEO_ID"
        rec_label = "Patient Geographic Identification"

    elif mode == "household":
        items = [
            numeric("CLASSIFICATION", "Classification", length=1, value_set_options=[
                ("UHC IS",     "1"),
                ("Non-UHC IS", "2"),
            ]),
            *_psgc_fields(),
            alpha("HH_ADDRESS", "Household Address", length=120),
        ]
        rec_name = "HOUSEHOLD_GEO_ID"
        rec_label = "Household Geographic Identification"

    else:
        raise ValueError(f"Unknown geo mode: {mode}")

    if extra_items:
        items.extend(extra_items)
    return record(rec_name, rec_label, "B", items)


def build_dictionary(dict_name, dict_label, id_item_name, id_item_label,
                     id_length, records):
    """Assemble a complete CSPro 8.0 dictionary.

    Args:
        dict_name: Dictionary name (e.g., "PATIENTSURVEY_DICT").
        dict_label: Human-readable label (e.g., "PatientSurvey").
        id_item_name: Name of the ID item (e.g., "QUESTIONNAIRE_NO").
        id_item_label: Label for the ID item.
        id_length: Length of the ID field.
        records: List of record dicts from record().
    """
    return {
        "software": "CSPro",
        "version": 8.0,
        "fileType": "dictionary",
        "name": dict_name,
        "labels": [{"text": dict_label}],
        "readOptimization": True,
        "recordType": {"start": 1, "length": 1},
        "defaults": {"decimalMark": True, "zeroFill": False},
        "relativePositions": True,
        "levels": [
            {
                "name": f"{dict_name.replace('_DICT', '_LEVEL')}",
                "labels": [{"text": f"{dict_label} Level"}],
                "ids": {
                    "items": [
                        {
                            "name": id_item_name,
                            "labels": [{"text": id_item_label}],
                            "contentType": "numeric",
                            "start": 2,
                            "length": id_length,
                            "zeroFill": True,
                        }
                    ]
                },
                "records": records,
            }
        ],
    }


def write_dcf(dictionary, out_path):
    """Write dictionary to .dcf file and print diagnostics."""
    Path(out_path).write_text(json.dumps(dictionary, indent=2), encoding="utf-8")
    record_count = len(dictionary["levels"][0]["records"])
    item_count = sum(len(r["items"]) for r in dictionary["levels"][0]["records"])
    print(f"Wrote {out_path}")
    print(f"  Records: {record_count}")
    print(f"  Items:   {item_count}")
```

- [ ] **Step 2: Verify module loads**

Run: `cd deliverables/CSPro && python -c "import cspro_helpers; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add deliverables/CSPro/cspro_helpers.py
git commit -m "feat: extract shared CSPro helpers module from F1 generator"
```

---

### Task 2: Refactor F1 generator to import from shared module

**Files:**
- Modify: `deliverables/CSPro/F1/generate_dcf.py`
- Unchanged: `deliverables/CSPro/F1/FacilityHeadSurvey.dcf` (identity-diff gate)

The refactored F1 generator keeps ALL of its section builders, PENDING_DESIGN constants, and `build_dictionary()` intact. Only the helpers and value sets are replaced with imports.

**CRITICAL:** F1's `build_field_control()` and `build_geographic_id()` use specific item names (e.g., `DATE_FIRST_VISITED_THE_FACILITY` not `DATE_FIRST_VISITED`) that differ from the parameterized shared versions. F1 MUST keep its own local `build_field_control()` and `build_geographic_id()` to preserve byte-identical output. Only the generic helpers (`_value_set`, `numeric`, `alpha`, `yes_no`, `yes_no_dk`, `yes_no_na`, `select_one`, `select_all`, `uhc9_item`, `record`) and value set constants are imported.

- [ ] **Step 1: Refactor F1 generator — replace helpers with imports**

Replace lines 1-221 (imports, constants, helpers, record function) of `deliverables/CSPro/F1/generate_dcf.py` with:

```python
"""
generate_dcf.py — F1 Facility Head Survey CSPro Data Dictionary generator.

Emits FacilityHeadSurvey.dcf in CSPro 8.0 JSON dictionary format from the
April 8 2026 Annex F1 questionnaire.

Authority sources (in priority order):
  1. raw/Project-Deliverable-1/Annex F1...Questionnaire...Apr 08.pdf  (printed)
  2. deliverables/CSPro/F1/inputs/F1_clean.txt                         (text extract)
  3. deliverables/CSPro/F1/F1-Skip-Logic-and-Validations.md            (logic spec)
  4. raw/CSPro-Data-Dictionary/FacilityHeadSurvey.dcf                  (Carl's manual
     scaffold — authoritative for FIELD_CONTROL, GEO_ID, Q1-Q8 item names + value
     set labels; this generator extends it for Q9-Q166 + secondary data.)

Naming convention: Q{n}_DESCRIPTOR in UPPER_SNAKE. Item names for Q9-Q166
follow F1-Skip-Logic-and-Validations.md so the validation-rule references
in that doc keep working without rename churn.

PENDING items: 6 questions still need ASPSI design decisions. They are
flagged with `TODO: PENDING DESIGN` constants near the top of this file and
emit working defaults so the dictionary loads cleanly in Designer. Hot-swap
the constants once decisions land.

Routing note (corrected 2026-04-15): these 6 items were originally expected
to be decided at the Apr 13 LSS meeting. After reading the actual Apr 13
meeting minutes, the routing was recognized as a category error — LSS scope
is process/tasking/communication, not technical questionnaire-logic
decisions. The 6 items need a narrowly-scoped technical design review with
Dr. Paunlagui (Survey Manager). Constants were renamed from the old
PENDING_LSS_* prefix to PENDING_DESIGN_* to reflect the correct forum.

Run:
    python generate_dcf.py        # writes FacilityHeadSurvey.dcf next to this file
"""

import json
import sys
from pathlib import Path

# Import shared helpers
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cspro_helpers import (
    YES_NO, YES_NO_DK, YES_NO_NA, UHC9_OPTIONS, FREQUENCY, WHY_DIFF_OPTIONS,
    _value_set, numeric, alpha, yes_no, yes_no_dk, yes_no_na,
    select_one, select_all, uhc9_item, record,
)
```

Keep everything from line 96 onward (`# 2. PENDING DESIGN DECISIONS`) through end of file UNCHANGED, except:
- Remove the duplicate definitions of `YES_NO`, `YES_NO_DK`, `YES_NO_NA`, `UHC9_OPTIONS`, `FREQUENCY`, `WHY_DIFF_OPTIONS` (lines 43-94)
- Remove the duplicate helper function definitions: `_value_set`, `numeric`, `alpha`, `yes_no`, `yes_no_dk`, `yes_no_na`, `select_one`, `select_all`, `uhc9_item`, `record` (lines 136-220)
- Keep `build_field_control()` (lines 227-258) — uses F1-specific item names
- Keep `build_geographic_id()` (lines 261-283) — uses F1-specific structure
- Keep ALL section builders and `build_dictionary()` and `main()` exactly as-is

- [ ] **Step 2: Regenerate F1 DCF and run identity-diff check**

```bash
cd deliverables/CSPro/F1
# Save a copy of the current DCF
cp FacilityHeadSurvey.dcf FacilityHeadSurvey.dcf.bak
# Regenerate
python generate_dcf.py
# Diff — must produce zero output
diff FacilityHeadSurvey.dcf FacilityHeadSurvey.dcf.bak
```

Expected: No output from `diff` (files are identical). If any difference appears, the refactor has a bug — fix before proceeding.

- [ ] **Step 3: Clean up backup and commit**

```bash
rm FacilityHeadSurvey.dcf.bak
git add deliverables/CSPro/F1/generate_dcf.py
git commit -m "refactor: F1 generator imports shared helpers from cspro_helpers"
```

---

### Task 3: Extract F3 and F4 PDF text

**Files:**
- Create: `deliverables/CSPro/F3/inputs/F3_clean.txt`
- Create: `deliverables/CSPro/F4/inputs/F4_clean.txt`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p deliverables/CSPro/F3/inputs
mkdir -p deliverables/CSPro/F4/inputs
```

- [ ] **Step 2: Extract F3 PDF text using PyMuPDF**

```python
import sys
import fitz  # PyMuPDF

pdf_path = r"raw/Project-Deliverable-1/Annex F3_Patient Survey Questionnaire_UHC Year 2_Apr 08.pdf"
out_path = r"deliverables/CSPro/F3/inputs/F3_clean.txt"

doc = fitz.open(pdf_path)
with open(out_path, "w", encoding="utf-8") as f:
    for page in doc:
        f.write(page.get_text())
        f.write("\n---PAGE BREAK---\n")
doc.close()
print(f"Wrote {out_path}")
```

Run from the project root: `python extract_f3.py` (or inline with `python -c "..."`)

- [ ] **Step 3: Extract F4 PDF text using PyMuPDF**

```python
import sys
import fitz  # PyMuPDF

pdf_path = r"raw/Project-Deliverable-1/Annex F4_Household Survey Questionnaire_UHC Year 2_Apr 08.pdf"
out_path = r"deliverables/CSPro/F4/inputs/F4_clean.txt"

doc = fitz.open(pdf_path)
with open(out_path, "w", encoding="utf-8") as f:
    for page in doc:
        f.write(page.get_text())
        f.write("\n---PAGE BREAK---\n")
doc.close()
print(f"Wrote {out_path}")
```

- [ ] **Step 4: Verify extractions have content**

```bash
wc -l deliverables/CSPro/F3/inputs/F3_clean.txt
wc -l deliverables/CSPro/F4/inputs/F4_clean.txt
```

Expected: F3 ~4000+ lines, F4 ~3900+ lines.

- [ ] **Step 5: Commit**

```bash
git add deliverables/CSPro/F3/inputs/F3_clean.txt deliverables/CSPro/F4/inputs/F4_clean.txt
git commit -m "feat: extract F3 and F4 questionnaire text from Apr 8 PDFs"
```

---

### Task 4: Build F3 Patient Survey generator

**Files:**
- Create: `deliverables/CSPro/F3/generate_dcf.py`

This is the largest task. The F3 generator covers 14 records (all single-occurrence) across 12 sections (A-L) with ~170 questions. Each section is a separate function.

- [ ] **Step 1: Create F3 generator — imports and section builders A-D**

```python
"""
generate_dcf.py — F3 Patient Survey CSPro Data Dictionary generator.

Emits PatientSurvey.dcf in CSPro 8.0 JSON dictionary format from the
April 8 2026 Annex F3 questionnaire.

Run:
    python generate_dcf.py        # writes PatientSurvey.dcf next to this file
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cspro_helpers import (
    YES_NO, YES_NO_DK, YES_NO_NA, UHC9_OPTIONS, SATISFACTION_5PT,
    numeric, alpha, yes_no, yes_no_dk, yes_no_na,
    select_one, select_all, uhc9_item, record,
    build_field_control, build_geo_id, build_dictionary, write_dcf,
)


# ============================================================
# FIELD CONTROL — shared + patient type extra
# ============================================================

def build_f3_field_control():
    extra = [
        numeric("PATIENT_TYPE", "Type of Patient", length=1,
                value_set_options=[("Outpatient", "1"), ("Inpatient", "2")]),
        numeric("PATIENT_LISTING_NO", "Patient Listing Reference Number", length=4, zero_fill=True),
    ]
    return build_field_control(extra_items=extra, date_label_entity="the Patient")


# ============================================================
# GEO ID — facility + patient home
# ============================================================

def build_f3_geo_id():
    return build_geo_id(mode="facility_and_patient")


# ============================================================
# Section A. Informed Consent (Q1)
# ============================================================

def build_section_a():
    items = [
        yes_no("Q1_CONSENT", "1. Do you voluntarily agree to participate in this survey?"),
    ]
    return record("A_INFORMED_CONSENT", "A. Informed Consent", "C", items)


# ============================================================
# Section B. Patient Profile (Q2-Q10)
# ============================================================

def build_section_b():
    Q2_RELATIONSHIP = [
        ("Patient him/herself",          "1"),
        ("Spouse",                       "2"),
        ("Son/Daughter",                 "3"),
        ("Parent",                       "4"),
        ("Sibling",                      "5"),
        ("Other relative",               "6"),
        ("Non-relative (e.g., neighbor)","7"),
    ]
    Q5_CIVIL_STATUS = [
        ("Single",    "1"),
        ("Married",   "2"),
        ("Widowed",   "3"),
        ("Separated", "4"),
        ("Divorced",  "5"),
    ]
    Q6_EDUCATION = [
        ("No formal education",          "01"),
        ("Elementary (incomplete)",       "02"),
        ("Elementary (complete)",         "03"),
        ("High School (incomplete)",      "04"),
        ("High School (complete)",        "05"),
        ("Vocational / Technical",        "06"),
        ("College (incomplete)",          "07"),
        ("College (complete)",            "08"),
        ("Post-graduate",                 "09"),
        ("I don't know",                  "99"),
    ]
    Q7_EMPLOYMENT = [
        ("Employed (full-time)",  "1"),
        ("Employed (part-time)",  "2"),
        ("Self-employed",         "3"),
        ("Unemployed",            "4"),
        ("Retired",               "5"),
        ("Student",               "6"),
        ("Homemaker",             "7"),
        ("Other (specify)",       "8"),
    ]
    Q9_INDIGENOUS = [
        ("Yes",          "1"),
        ("No",           "2"),
        ("I don't know", "3"),
    ]
    items = [
        select_one("Q2_RELATIONSHIP", "2. What is the relationship of the respondent to the patient?",
                   Q2_RELATIONSHIP, length=1),
        alpha("Q3_NAME", "3. What is the name of the patient? (Last Name, First Name, Middle Initial)", length=80),
        numeric("Q4_AGE", "4. How old are you (in years), as of your last birthday?", length=3),
        numeric("Q4_SEX", "4b. What is your sex assigned at birth?", length=1,
                value_set_options=[("Male", "1"), ("Female", "2")]),
        select_one("Q5_CIVIL_STATUS", "5. What is your civil status?", Q5_CIVIL_STATUS, length=1),
        select_one("Q6_EDUCATION", "6. What is your highest educational attainment?", Q6_EDUCATION, length=2),
        select_one("Q7_EMPLOYMENT", "7. What is your current employment status?", Q7_EMPLOYMENT, length=1),
        alpha("Q7_OTHER_TXT", "7. Employment — Other (specify) text", length=120),
        numeric("Q8_HH_SIZE", "8. How many members are there in your household, including yourself?", length=2),
        select_one("Q9_INDIGENOUS", "9. Do you identify as a member of an indigenous group?", Q9_INDIGENOUS, length=1),
        alpha("Q9_INDIGENOUS_TXT", "9a. If yes, please specify the name of the indigenous group.", length=80),
        yes_no("Q10_PWD", "10. Are you a person with disability (PWD)?"),
    ]
    return record("B_PATIENT_PROFILE", "B. Patient Profile", "D", items)
```

- [ ] **Step 2: Add F3 sections C-D (UHC Awareness, PhilHealth Registration)**

Append to the same file:

```python
# ============================================================
# Section C. UHC Awareness (Q11-Q24)
# ============================================================

def build_section_c():
    Q12_SOURCE = [
        ("News",                "1"),
        ("Legislation",         "2"),
        ("Social Media",        "3"),
        ("Friends / Family",    "4"),
        ("Health center/facility","5"),
        ("LGU/Barangay",        "6"),
        ("I don't know",        "7"),
        ("Other (specify)",     "8"),
    ]
    Q14_UNDERSTANDING = [
        ("Free healthcare for all Filipinos",                       "1"),
        ("Government provides financial assistance for health",     "2"),
        ("All Filipinos are automatically enrolled in PhilHealth",  "3"),
        ("Primary care provider for every Filipino",                "4"),
        ("Access to quality healthcare for everyone",               "5"),
        ("I don't know",                                            "6"),
        ("Other (specify)",                                         "7"),
    ]
    items = [
        yes_no_dk("Q11_UHC_HEARD", "11. Have you heard about Universal Health Care (UHC) prior to this survey?"),
        *select_all("Q12_UHC_SOURCE", "12. What are your sources of information about UHC?", Q12_SOURCE),
        yes_no_dk("Q13_UHC_LAW_AWARE", "13. Are you aware that UHC is a law?"),
        *select_all("Q14_UHC_UNDERSTAND", "14. What is your understanding about UHC?", Q14_UNDERSTANDING),
    ]
    # Q15-Q24: UHC9 items for various UHC benefits awareness
    uhc9_labels = [
        ("Q15_AUTO_PHILHEALTH", "15. Automatic PhilHealth coverage for all Filipinos"),
        ("Q16_FREE_CONSULT",    "16. Free primary care consultations"),
        ("Q17_FREE_LABS",       "17. Free laboratory and diagnostic services"),
        ("Q18_FREE_MEDS",       "18. Free medicines"),
        ("Q19_NBB",             "19. No Balance Billing (NBB) for inpatient services in government hospitals"),
        ("Q20_ZBB",             "20. Zero Balance Billing (ZBB) in DOH-retained hospitals"),
        ("Q21_REFERRAL",        "21. Referral system to connect patients to appropriate services"),
        ("Q22_KONSULTA",        "22. YAKAP/Konsulta primary care benefit package"),
        ("Q23_MEDS_ACCESS",     "23. Better access to essential medicines"),
        ("Q24_HCW_DEPLOYMENT",  "24. Increased deployment of healthcare workers to underserved areas"),
    ]
    for name, label in uhc9_labels:
        items.extend(uhc9_item(name, label))
    return record("C_UHC_AWARENESS", "C. UHC Awareness", "E", items)


# ============================================================
# Section D. PhilHealth Registration (Q25-Q40)
# ============================================================

def build_section_d():
    Q25_PHILHEALTH_STATUS = [
        ("Member (direct contributor)",  "1"),
        ("Dependent",                    "2"),
        ("Indigent / sponsored member",  "3"),
        ("Senior citizen",               "4"),
        ("Not a member",                 "5"),
        ("I don't know",                 "6"),
    ]
    Q26_MEMBER_TYPE = [
        ("Employed (private sector)",      "01"),
        ("Employed (government)",          "02"),
        ("Self-employed / Informal sector","03"),
        ("Voluntary / Individual paying",  "04"),
        ("Overseas Filipino Worker (OFW)", "05"),
        ("Sponsored (LGU/National Gov't)", "06"),
        ("Indigent",                       "07"),
        ("Senior citizen",                 "08"),
        ("Lifetime member",                "09"),
        ("I don't know",                   "99"),
    ]
    Q27_REG_DIFFICULTY = [
        ("Yes",          "1"),
        ("No",           "2"),
    ]
    Q28_DIFFICULTY_REASONS = [
        ("Unclear process",                              "1"),
        ("Took a long time",                             "2"),
        ("Did not know where to ask for help",           "3"),
        ("Had to travel a long way",                     "4"),
        ("No valid ID",                                  "5"),
        ("Did not know the required documents to register","6"),
        ("I don't know",                                  "7"),
        ("Other (specify)",                               "8"),
    ]
    Q30_PREMIUM_PAYMENT = [
        ("Yes, I pay directly",    "1"),
        ("Yes, my employer pays",  "2"),
        ("No, I do not pay premiums","3"),
    ]
    Q32_DIFFICULTY_PAYING = [
        ("Cannot afford the premium",                     "1"),
        ("Payment options are inconvenient",              "2"),
        ("No time to pay",                                "3"),
        ("Don't see value in paying",                     "4"),
        ("System of PhilHealth is unreliable/usually down","5"),
        ("I don't know",                                   "6"),
        ("Other (specify)",                                "7"),
    ]
    Q33_YAKAP_AWARE = [
        ("Yes",          "1"),
        ("No",           "2"),
        ("I don't know", "3"),
    ]
    Q35_KONSULTA_SOURCE = [
        ("News",                 "1"),
        ("Legislation",          "2"),
        ("Social Media",         "3"),
        ("Friends / Family",     "4"),
        ("Health center/facility","5"),
        ("PhilHealth",           "6"),
        ("LGU/Barangay",        "7"),
        ("BHW",                  "8"),
        ("I don't know",         "9"),
        ("Other (specify)",     "10"),
    ]
    items = [
        select_one("Q25_PHILHEALTH_STATUS", "25. What is your PhilHealth membership status?",
                   Q25_PHILHEALTH_STATUS, length=1),
        select_one("Q26_MEMBER_TYPE", "26. What type of PhilHealth member are you?",
                   Q26_MEMBER_TYPE, length=2),
        yes_no("Q27_REG_DIFFICULTY", "27. Did you have any difficulties in the registration process?"),
        *select_all("Q28_DIFFICULTY", "28. What did you find difficult about the process?", Q28_DIFFICULTY_REASONS),
        yes_no("Q29_KNOWS_ASSIST", "29. Would you know where to go to seek assistance in registration?"),
        select_one("Q30_PREMIUM_PAY", "30. Do you pay PhilHealth premiums every month?",
                   Q30_PREMIUM_PAYMENT, length=1),
        yes_no("Q31_PREMIUM_DIFFICULT", "31. Do you find it difficult to pay the PhilHealth premiums?"),
        *select_all("Q32_DIFF_PAYING", "32. Why did you find it difficult?", Q32_DIFFICULTY_PAYING),
        select_one("Q33_YAKAP_AWARE", "33. Have you heard about YAKAP/Konsulta?",
                   Q33_YAKAP_AWARE, length=1),
        yes_no("Q34_KONSULTA_ENROLLED", "34. Are you enrolled in a Konsulta provider?"),
        *select_all("Q35_KONSULTA_SOURCE", "35. What are your sources of information about Konsulta?",
                    Q35_KONSULTA_SOURCE),
        yes_no_dk("Q36_KONSULTA_USED", "36. Have you used any Konsulta services in the past 12 months?"),
        yes_no("Q37_KONSULTA_SATISFIED", "37. Were you satisfied with the Konsulta services?"),
        yes_no_dk("Q38_PRIVATE_INS", "38. Do you have private health insurance or HMO?"),
        alpha("Q39_PRIVATE_INS_NAME", "39. Name of private insurance/HMO provider", length=80),
        yes_no_dk("Q40_GSIS_SSS", "40. Are you a member of GSIS/SSS/Pag-IBIG?"),
    ]
    return record("D_PHILHEALTH_REG", "D. PhilHealth Registration", "F", items)
```

- [ ] **Step 3: Add F3 sections E-F (Primary Care, Health-Seeking)**

```python
# ============================================================
# Section E. Primary Care Utilization (Q41-Q55)
# ============================================================

def build_section_e():
    Q42_FACILITY_TYPE = [
        ("YAKAP/Konsulta or primary care provider",         "01"),
        ("Barangay Health Center",                          "02"),
        ("Rural Health Unit / Health Center",                "03"),
        ("Public Hospital",                                 "04"),
        ("Private Hospital",                                "05"),
        ("Private Clinic",                                  "06"),
        ("Traditional Healer or Manghihilot/Albularyo",     "07"),
        ("I don't know",                                    "08"),
        ("Other (specify)",                                 "09"),
    ]
    Q43_WHY_NOT = [
        ("I don't get sick",              "1"),
        ("I recently moved into the area","2"),
        ("It's expensive",                "3"),
        ("I can treat myself",            "4"),
        ("I don't know where to go",      "5"),
        ("I don't know",                  "6"),
        ("Other (specify)",               "7"),
    ]
    Q44_TRANSPORT = [
        ("Walk",                                 "01"),
        ("Bike",                                 "02"),
        ("Public Bus",                           "03"),
        ("Jeepney",                              "04"),
        ("Tricycle",                             "05"),
        ("Car (including private taxi/cab)",      "06"),
        ("Motorcycle",                           "07"),
        ("Boat",                                 "08"),
        ("Taxi",                                 "09"),
        ("Pedicab",                              "10"),
        ("E-bike",                               "11"),
        ("Other (specify)",                      "12"),
    ]
    items = [
        yes_no_dk("Q41_HAS_USUAL_FACILITY",
                  "41. In the past 12 months, do you have a clinic or health center that you usually go to?"),
        alpha("Q41_FACILITY_NAME", "41a. What is the name of the facility?", length=120),
        select_one("Q42_FACILITY_TYPE", "42. What is the type of facility that you usually go to?",
                   Q42_FACILITY_TYPE, length=2),
        *select_all("Q43_WHY_NOT", "43. Why do you not have a usual clinic/health center?", Q43_WHY_NOT),
        *select_all("Q44_TRANSPORT", "44. What mode/s of transportation do you use when travelling to the nearest primary care facility?",
                    Q44_TRANSPORT),
        numeric("Q45_TRAVEL_TIME", "45. How long does it take you to travel to the nearest primary care facility? (minutes)",
                length=3),
        numeric("Q46_TRAVEL_COST", "46. How much does it cost to travel to this facility? (PHP, one-way)",
                length=5),
        yes_no("Q47_KNOWS_BOOKING", "47. Do you know how to book an appointment at a primary care facility?"),
        select_one("Q48_PHONE_ADVICE", "48. Can you get advice quickly over the phone when the facility is open?",
                   [("Yes","1"),("No","2"),("I haven't tried","3"),("I don't know","4")], length=1),
        select_one("Q49_AFTER_HOURS", "49. Is there a phone number you can call when the facility is closed?",
                   [("Yes","1"),("No","2"),("I haven't tried","3"),("I don't know","4")], length=1),
        select_one("Q50_LEAVE_WORK", "50. Do you have to take a leave from work or school to visit?",
                   [("Yes","1"),("No","2"),("I haven't tried","3"),("I don't know","4"),("Not applicable","9")], length=1),
    ]
    return record("E_PRIMARY_CARE", "E. Primary Care Utilization", "G", items)


# ============================================================
# Section F. Health-Seeking Behavior (Q51-Q60)
# ============================================================

def build_section_f():
    Q51_WHY_VISIT = [
        ("This facility is more accessible than my usual facility", "01"),
        ("Needed a service/specialist not available at my usual facility", "02"),
        ("Recommended by friends/family", "03"),
        ("Wanted to try another facility than my usual", "04"),
        ("Prefer this facility than my usual", "05"),
        ("This was referred to me by my usual facility", "06"),
        ("Usual facility is closed for today", "07"),
        ("The doctor I trust transferred in this facility", "08"),
        ("Other (specify)", "09"),
    ]
    Q52_REASON_VISIT = [
        ("Consultation for new health problem",           "1"),
        ("Follow-up on ongoing health problem",           "2"),
        ("For tests/diagnostics only",                    "3"),
        ("For a general check-up",                        "4"),
        ("To get a health certificate/administrative reason","5"),
        ("For immunizations/vaccinations",                "6"),
        ("My doctor transferred to this facility",        "7"),
        ("Other (specify)",                               "8"),
    ]
    Q53_CARE_TYPE = [
        ("Outpatient care",            "1"),
        ("Inpatient care",             "2"),
        ("Emergency care",             "3"),
        ("Primary care consultation",  "4"),
        ("Other (specify)",            "5"),
    ]
    Q55_ACTIONS = [
        ("Visited other healthcare facility",   "1"),
        ("Sought alternative care",             "2"),
        ("Sought telemedicine",                 "3"),
        ("Used home care",                      "4"),
        ("Bought medicine from a pharmacy",     "5"),
        ("Did not seek other forms of care",    "6"),
        ("Other (specify)",                     "7"),
    ]
    items = [
        yes_no("Q51_USUAL_FACILITY", "51. Is this the facility you usually go to for general health concerns?"),
        *select_all("Q51A_WHY_DIFF", "51a. Why did you go to this facility?", Q51_WHY_VISIT),
        *select_all("Q52_REASON_VISIT", "52. What best describes why you will visit a health facility?", Q52_REASON_VISIT),
        *select_all("Q53_CARE_TYPE", "53. Have you accessed any of the following forms of care in the last 6 months?", Q53_CARE_TYPE),
        yes_no("Q54_PREVENTIVE", "54. Have you ever consulted a physician for preventative reasons?"),
        yes_no("Q55_FORGONE", "55. In the last 6 months, have you had a medical problem and chosen NOT to see a healthcare provider?"),
        *select_all("Q56_FORGONE_WHY", "56. Why not?", [
            ("Not sick enough","1"),("It's too expensive","2"),
            ("Could not take time off work","3"),("Could not get an appointment soon enough","4"),
            ("No transportation available","5"),("Afraid to know my illness","6"),
            ("I don't know","7"),("Other (specify)","8"),
        ]),
        *select_all("Q57_ACTIONS", "57. Did you do any other actions to improve your health?", Q55_ACTIONS),
    ]
    return record("F_HEALTH_SEEKING", "F. Health-Seeking Behavior", "H", items)
```

- [ ] **Step 4: Add F3 sections G-H (Outpatient Care, Inpatient Care)**

```python
# ============================================================
# Section G. Outpatient Care (Q58-Q78)
# ============================================================

def build_section_g():
    Q58_SERVICES = [
        ("Consultation with a doctor",          "01"),
        ("Vaccination / immunization",          "02"),
        ("Dental care",                         "03"),
        ("Eye care / vision check",             "04"),
        ("Mental health consultation",          "05"),
        ("Prenatal / postnatal care",           "06"),
        ("Family planning",                     "07"),
        ("Laboratory / diagnostic test",        "08"),
        ("Physical therapy / rehabilitation",   "09"),
        ("Other (specify)",                     "10"),
    ]
    # Q61 Lab tests (select-all, 17 options from PDF)
    Q61_LABS = [
        ("Complete blood count (CBC)",   "01"),
        ("Urinalysis",                   "02"),
        ("Fecalysis / Stool exam",       "03"),
        ("Blood chemistry",              "04"),
        ("Lipid profile",                "05"),
        ("Blood sugar / glucose test",   "06"),
        ("Thyroid function test",        "07"),
        ("X-ray",                        "08"),
        ("Ultrasound",                   "09"),
        ("ECG / EKG",                    "10"),
        ("Drug test",                    "11"),
        ("Pap smear",                    "12"),
        ("Mammogram",                    "13"),
        ("CT Scan",                      "14"),
        ("MRI",                          "15"),
        ("COVID-19 test",                "16"),
        ("Other (specify)",              "17"),
    ]
    # Q65 payment sources (15 options from PDF Q98)
    Q65_PAYMENT = [
        ("Own income / household income","01"),
        ("PhilHealth",                   "02"),
        ("Private insurance / HMO",      "03"),
        ("Loan",                         "04"),
        ("Sale of assets",               "05"),
        ("Donations from charities/NGOs","06"),
        ("Donations from LGUs",          "07"),
        ("National Gov't Agencies",      "08"),
        ("Paid by someone else",         "09"),
        ("Savings / pension",            "10"),
        ("Remittance",                   "11"),
        ("Borrowing from relatives",     "12"),
        ("Borrowing from institutions",  "13"),
        ("Government assistance",        "14"),
        ("Other (specify)",              "15"),
    ]
    items = [
        numeric("Q58_OUTPATIENT_VISITS", "58. How many outpatient visits in the last 6 months?", length=2),
        *select_all("Q59_SERVICES", "59. What services did you receive during your most recent outpatient visit?", Q58_SERVICES),
        yes_no("Q60_LABS", "60. Did you have any laboratory or diagnostic tests?"),
        *select_all("Q61_LAB_TYPES", "61. Which laboratory tests?", Q61_LABS),
        numeric("Q62_LAB_COST", "62. How much did you pay for lab tests? (PHP)", length=7),
        numeric("Q63_CONSULT_COST", "63. How much was the consultation fee? (PHP)", length=7),
        numeric("Q64_MEDS_COST", "64. How much did you spend on medicines? (PHP)", length=7),
        numeric("Q65_TOTAL_OOP", "65. Total out-of-pocket spending for outpatient visit (PHP)", length=8),
        # Payment sources: each has Yes/No + Amount
        *[item for name_code in Q65_PAYMENT for item in [
            yes_no(f"Q66_PAY_O{int(name_code[1]):02d}", f"66. Payment source: {name_code[0]}"),
            numeric(f"Q66_PAY_O{int(name_code[1]):02d}_AMT", f"66. Amount from {name_code[0]} (PHP)", length=8),
        ]],
        yes_no("Q67_PHILHEALTH_USED", "67. Did you use PhilHealth for this visit?"),
        yes_no("Q68_SATISFIED_OOP", "68. Were you satisfied with the amount you paid?"),
    ]
    return record("G_OUTPATIENT_CARE", "G. Outpatient Care", "I", items)


# ============================================================
# Section H. Inpatient Care (Q69-Q86)
# ============================================================

def build_section_h():
    Q69_REASON = [
        ("Illness / medical condition",    "1"),
        ("Surgery / procedure",            "2"),
        ("Childbirth / delivery",          "3"),
        ("Injury / accident",              "4"),
        ("Mental health",                  "5"),
        ("Other (specify)",                "6"),
    ]
    Q72_PAYMENT = [
        ("Own income / household income","01"),
        ("PhilHealth",                   "02"),
        ("Private insurance / HMO",      "03"),
        ("Loan",                         "04"),
        ("Sale of assets",               "05"),
        ("Donations from charities/NGOs","06"),
        ("Donations from LGUs",          "07"),
        ("National Gov't Agencies",      "08"),
        ("Paid by someone else",         "09"),
        ("Savings / pension",            "10"),
        ("Remittance",                   "11"),
        ("Borrowing from relatives",     "12"),
        ("Borrowing from institutions",  "13"),
        ("Other (specify)",              "14"),
    ]
    items = [
        numeric("Q69_INPATIENT_STAYS", "69. How many times were you admitted as an inpatient in the last 6 months?", length=2),
        *select_all("Q70_REASON", "70. What was the primary reason for the most recent admission?", Q69_REASON),
        numeric("Q71_NIGHTS", "71. How many nights were you admitted?", length=3),
        numeric("Q72_TOTAL_BILL", "72. Total hospital bill (PHP)", length=8),
        numeric("Q73_OOP", "73. Total out-of-pocket amount paid (PHP)", length=8),
        # Payment sources: each has Yes/No + Amount
        *[item for name_code in Q72_PAYMENT for item in [
            yes_no(f"Q74_PAY_O{int(name_code[1]):02d}", f"74. Payment source: {name_code[0]}"),
            numeric(f"Q74_PAY_O{int(name_code[1]):02d}_AMT", f"74. Amount from {name_code[0]} (PHP)", length=8),
        ]],
        yes_no("Q75_PHILHEALTH_USED", "75. Did you use PhilHealth for this admission?"),
        numeric("Q76_PHILHEALTH_COVERED", "76. How much did PhilHealth cover? (PHP)", length=8),
        yes_no("Q77_NBB_APPLIED", "77. Was No Balance Billing applied?"),
        yes_no("Q78_SATISFIED_OOP", "78. Were you satisfied with the amount you paid?"),
    ]
    return record("H_INPATIENT_CARE", "H. Inpatient Care", "J", items)
```

- [ ] **Step 5: Add F3 sections I-J (Financial Risk, Satisfaction)**

```python
# ============================================================
# Section I. Financial Risk Protection (Q79-Q88)
# ============================================================

def build_section_i():
    Q79_INCOME_BRACKET = [
        ("Below PHP 10,957 (poor)",           "1"),
        ("PHP 10,957 - PHP 21,914 (low income)","2"),
        ("PHP 21,914 - PHP 43,828 (lower middle)","3"),
        ("PHP 43,828 - PHP 76,669 (middle)",    "4"),
        ("PHP 76,669 - PHP 131,484 (upper middle)","5"),
        ("PHP 131,484 - PHP 219,140 (upper income)","6"),
        ("Above PHP 219,140 (rich)",            "7"),
        ("Refused to answer",                   "8"),
        ("I don't know",                        "9"),
    ]
    items = [
        select_one("Q79_INCOME", "79. What is your estimated average monthly household income?",
                   Q79_INCOME_BRACKET, length=1),
        yes_no("Q80_DELAYED_CARE", "80. Have you delayed seeking care for financial reasons in the last 6 months?"),
        yes_no("Q81_REDUCED_SPEND", "81. Have you reduced spending on basic needs because of health expenditures?"),
        yes_no("Q82_BORROWED", "82. Have you borrowed money to pay for health expenses?"),
        yes_no("Q83_SOLD_ASSETS", "83. Have you sold assets to pay for health expenses?"),
        numeric("Q84_HEALTH_SPEND_PCT",
                "84. What percentage of household income was spent on health in the last 12 months?",
                length=3),
        yes_no("Q85_CATASTROPHIC", "85. Did health spending exceed 10% of household income?"),
        yes_no("Q86_IMPOVERISHED", "86. Did health spending push your household below the poverty line?"),
        yes_no("Q87_FORGONE_MEDS", "87. Have you foregone buying prescribed medicines for financial reasons?"),
        yes_no("Q88_FORGONE_FOLLOWUP", "88. Have you skipped follow-up visits for financial reasons?"),
    ]
    return record("I_FINANCIAL_RISK", "I. Financial Risk Protection", "K", items)


# ============================================================
# Section J. Patient Satisfaction (Q89-Q100)
# ============================================================

def build_section_j():
    FREQUENCY_4PT = [
        ("Always",    "1"),
        ("Usually",   "2"),
        ("Sometimes", "3"),
        ("Never",     "4"),
    ]
    items = [
        # Satisfaction items (5-point scale)
        select_one("Q89_SAT_WAIT_TIME", "89. Satisfaction with waiting time", SATISFACTION_5PT, length=1),
        select_one("Q90_SAT_CONSULT_TIME", "90. Satisfaction with consultation time", SATISFACTION_5PT, length=1),
        select_one("Q91_SAT_EXPLANATION", "91. Satisfaction with explanation of condition/treatment", SATISFACTION_5PT, length=1),
        select_one("Q92_SAT_RESPECT", "92. Satisfaction with how you were treated/respected", SATISFACTION_5PT, length=1),
        select_one("Q93_SAT_PRIVACY", "93. Satisfaction with privacy during consultation", SATISFACTION_5PT, length=1),
        select_one("Q94_SAT_CLEANLINESS", "94. Satisfaction with cleanliness of the facility", SATISFACTION_5PT, length=1),
        select_one("Q95_SAT_OVERALL", "95. Overall satisfaction with the health facility", SATISFACTION_5PT, length=1),
        # Frequency items (4-point scale)
        select_one("Q96_FREQ_LISTEN", "96. How often does the provider listen carefully?", FREQUENCY_4PT, length=1),
        select_one("Q97_FREQ_EXPLAIN", "97. How often does the provider explain things clearly?", FREQUENCY_4PT, length=1),
        select_one("Q98_FREQ_RESPECT", "98. How often does the provider show respect?", FREQUENCY_4PT, length=1),
        select_one("Q99_FREQ_TIME", "99. How often does the provider spend enough time?", FREQUENCY_4PT, length=1),
        select_one("Q100_RECOMMEND", "100. Would you recommend this facility to family/friends?",
                   [("Yes, definitely","1"),("Yes, probably","2"),("No","3"),("I don't know","4")], length=1),
    ]
    return record("J_SATISFACTION", "J. Patient Satisfaction", "L", items)
```

- [ ] **Step 6: Add F3 sections K-L (Access to Medicines, Referrals)**

```python
# ============================================================
# Section K. Access to Medicines (Q101-Q110)
# ============================================================

def build_section_k():
    Q101_WHERE = [
        ("Government health facility pharmacy",    "1"),
        ("Private pharmacy / drugstore",           "2"),
        ("Online pharmacy",                        "3"),
        ("Botika ng Barangay",                     "4"),
        ("Botika ng Bayan",                        "5"),
        ("Other (specify)",                        "6"),
    ]
    Q103_BARRIER = [
        ("Medicine not available",          "1"),
        ("Too expensive",                   "2"),
        ("Pharmacy too far",                "3"),
        ("Don't know where to buy",         "4"),
        ("No prescription",                 "5"),
        ("I don't know",                    "6"),
        ("Other (specify)",                 "7"),
    ]
    items = [
        yes_no("Q101_PRESCRIBED_MEDS", "101. Were you prescribed any medicines during your visit?"),
        *select_all("Q102_WHERE_BUY", "102. Where did you get your medicines?", Q101_WHERE),
        yes_no("Q103_ALL_OBTAINED", "103. Were you able to get all prescribed medicines?"),
        *select_all("Q104_BARRIER", "104. Why were you unable to get all prescribed medicines?", Q103_BARRIER),
        yes_no_dk("Q105_GENERIC_AWARE", "105. Are you aware of the Generics Act / generic medicines?"),
        yes_no("Q106_GENERIC_PREFER", "106. Do you prefer generic medicines?"),
        yes_no("Q107_GAMOT_AWARE", "107. Have you heard of GAMOT (DOH medicine access program)?"),
        yes_no("Q108_GAMOT_USED", "108. Have you used GAMOT?"),
        numeric("Q109_MEDS_OOP", "109. Total out-of-pocket spending on medicines in the last month (PHP)", length=7),
        yes_no("Q110_MEDS_SATISFIED", "110. Are you satisfied with your access to medicines?"),
    ]
    return record("K_ACCESS_MEDICINES", "K. Access to Medicines", "M", items)


# ============================================================
# Section L. Referrals (Q111-Q120)
# ============================================================

def build_section_l():
    Q112_TYPE = [
        ("Outpatient care",   "01"),
        ("Emergency care",    "02"),
        ("Inpatient care",    "03"),
        ("Dental care",       "04"),
        ("Other facility",    "05"),
        ("Special therapy",   "06"),
        ("Alternative care",  "07"),
        ("Medical mission",   "08"),
        ("Home healthcare",   "09"),
        ("Telemedicine",      "10"),
        ("None of the above", "11"),
        ("Other (specify)",   "12"),
    ]
    Q113_REFERRAL_METHOD = [
        ("Physical referral slip",                        "1"),
        ("E-referral",                                    "2"),
        ("Phone call from referring to receiving facility","3"),
        ("I don't know",                                  "4"),
        ("Other (specify)",                               "5"),
    ]
    Q114_VISIT_STATUS = [
        ("Yes",                          "1"),
        ("No, I'm not planning to",      "2"),
        ("Not yet, but I'm planning to", "3"),
    ]
    Q115_WHY_NOT = [
        ("Facility is too far",              "1"),
        ("Do not trust the referred facility","2"),
        ("No time",                          "3"),
        ("Worried about additional costs",   "4"),
        ("Not needed",                       "5"),
        ("Don't know how to get to facility","6"),
        ("Other (specify)",                  "7"),
    ]
    items = [
        yes_no("Q111_REFERRED", "111. In the past 6 months, did a healthcare worker refer you to another facility?"),
        *select_all("Q112_TYPE", "112. What type of care was the referral for?", Q112_TYPE),
        select_one("Q113_METHOD", "113. How did they refer you?", Q113_REFERRAL_METHOD, length=1),
        select_one("Q114_VISITED", "114. Did you visit another facility after the referral?",
                   Q114_VISIT_STATUS, length=1),
        *select_all("Q115_WHY_NOT", "115. Why are you not planning to visit?", Q115_WHY_NOT),
        yes_no("Q116_DISCUSSED_OPTIONS", "116. Did they discuss different places you could go?"),
        yes_no("Q117_HELPED_APPT", "117. Did they help you make the appointment?"),
        yes_no("Q118_WROTE_INFO", "118. Did they write down information for the specialist?"),
        yes_no("Q119_FOLLOWUP", "119. Did they follow up with you about the visit?"),
        select_one("Q120_SAT_REFERRAL", "120. Overall satisfaction with the referral process",
                   SATISFACTION_5PT, length=1),
    ]
    return record("L_REFERRALS", "L. Referrals", "N", items)
```

- [ ] **Step 7: Add F3 dictionary assembly and main()**

```python
# ============================================================
# ASSEMBLE THE DICTIONARY
# ============================================================

def build_f3_dictionary():
    records = [
        record("PATIENTSURVEY_REC", "PatientSurvey Record", "1", []),
        build_f3_field_control(),
        build_f3_geo_id(),
        build_section_a(),
        build_section_b(),
        build_section_c(),
        build_section_d(),
        build_section_e(),
        build_section_f(),
        build_section_g(),
        build_section_h(),
        build_section_i(),
        build_section_j(),
        build_section_k(),
        build_section_l(),
    ]
    return build_dictionary(
        dict_name="PATIENTSURVEY_DICT",
        dict_label="PatientSurvey",
        id_item_name="QUESTIONNAIRE_NO",
        id_item_label="Questionnaire No",
        id_length=6,
        records=records,
    )


def main():
    out_path = Path(__file__).parent / "PatientSurvey.dcf"
    write_dcf(build_f3_dictionary(), out_path)


if __name__ == "__main__":
    main()
```

- [ ] **Step 8: Run F3 generator and verify output**

```bash
cd deliverables/CSPro/F3
python generate_dcf.py
```

Expected output:
```
Wrote deliverables/CSPro/F3/PatientSurvey.dcf
  Records: 15
  Items:   <count>
```

Verify the .dcf loads:
```bash
python -c "import json; d=json.load(open('PatientSurvey.dcf')); print('Valid JSON, records:', len(d['levels'][0]['records']))"
```

- [ ] **Step 9: Commit F3 generator**

```bash
git add deliverables/CSPro/F3/generate_dcf.py deliverables/CSPro/F3/PatientSurvey.dcf
git commit -m "feat: F3 Patient Survey data dictionary generator (14 records, sections A-L)"
```

---

### Task 5: Build F4 Household Survey generator

**Files:**
- Create: `deliverables/CSPro/F4/generate_dcf.py`

F4 has 19 records total. Three are repeating (max_occurs=20): C (Household Roster), H (PhilHealth per member), J (Health-Seeking per member). Section N (Expenditures) uses flat item batteries with multiple reference periods.

- [ ] **Step 1: Create F4 generator — imports, field control, geo, sections A-C**

```python
"""
generate_dcf.py — F4 Household Survey CSPro Data Dictionary generator.

Emits HouseholdSurvey.dcf in CSPro 8.0 JSON dictionary format from the
April 8 2026 Annex F4 questionnaire.

Run:
    python generate_dcf.py        # writes HouseholdSurvey.dcf next to this file
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cspro_helpers import (
    YES_NO, YES_NO_DK, YES_NO_NA,
    numeric, alpha, yes_no, yes_no_dk, yes_no_na,
    select_one, select_all, record,
    build_field_control, build_geo_id, build_dictionary, write_dcf,
)


# ============================================================
# FIELD CONTROL — shared + HH listing ref
# ============================================================

def build_f4_field_control():
    extra = [
        numeric("HH_LISTING_NO", "Household Listing Reference Number", length=4, zero_fill=True),
    ]
    return build_field_control(extra_items=extra, date_label_entity="the Household")


# ============================================================
# GEO ID — household mode
# ============================================================

def build_f4_geo_id():
    return build_geo_id(mode="household")


# ============================================================
# Section A. Informed Consent (Q1)
# ============================================================

def build_section_a():
    items = [
        yes_no("Q1_CONSENT", "1. Do you voluntarily agree to participate in this survey?"),
    ]
    return record("A_INFORMED_CONSENT", "A. Informed Consent", "C", items)


# ============================================================
# Section B. Respondent Profile (Q2-Q29)
# ============================================================

def build_section_b():
    Q5_CIVIL_STATUS = [
        ("Single",    "1"),
        ("Married",   "2"),
        ("Widowed",   "3"),
        ("Separated", "4"),
        ("Divorced",  "5"),
    ]
    Q6_EDUCATION = [
        ("No formal education",      "01"),
        ("Elementary (incomplete)",   "02"),
        ("Elementary (complete)",     "03"),
        ("High School (incomplete)",  "04"),
        ("High School (complete)",    "05"),
        ("Vocational / Technical",    "06"),
        ("College (incomplete)",      "07"),
        ("College (complete)",        "08"),
        ("Post-graduate",             "09"),
        ("I don't know",              "99"),
    ]
    Q7_EMPLOYMENT = [
        ("Employed (full-time)",  "1"),
        ("Employed (part-time)",  "2"),
        ("Self-employed",         "3"),
        ("Unemployed",            "4"),
        ("Retired",               "5"),
        ("Student",               "6"),
        ("Homemaker",             "7"),
        ("Other (specify)",       "8"),
    ]
    Q9_INCOME = [
        ("Below PHP 10,957 (poor)",              "1"),
        ("PHP 10,957 - PHP 21,914 (low income)", "2"),
        ("PHP 21,914 - PHP 43,828 (lower middle)","3"),
        ("PHP 43,828 - PHP 76,669 (middle)",      "4"),
        ("PHP 76,669 - PHP 131,484 (upper middle)","5"),
        ("PHP 131,484 - PHP 219,140 (upper income)","6"),
        ("Above PHP 219,140 (rich)",               "7"),
        ("Refused to answer",                      "8"),
        ("I don't know",                           "9"),
    ]
    items = [
        alpha("Q2_NAME", "2. What is the name of the respondent? (Last Name, First Name, MI)", length=80),
        numeric("Q3_AGE", "3. How old are you (in years), as of your last birthday?", length=3),
        numeric("Q4_SEX", "4. What is your sex assigned at birth?", length=1,
                value_set_options=[("Male", "1"), ("Female", "2")]),
        select_one("Q5_CIVIL_STATUS", "5. What is your civil status?", Q5_CIVIL_STATUS, length=1),
        select_one("Q6_EDUCATION", "6. What is your highest educational attainment?", Q6_EDUCATION, length=2),
        select_one("Q7_EMPLOYMENT", "7. What is your current employment status?", Q7_EMPLOYMENT, length=1),
        alpha("Q7_OTHER_TXT", "7. Employment — Other (specify) text", length=120),
        numeric("Q8_HH_SIZE", "8. How many members are there in your household?", length=2),
        select_one("Q9_INCOME", "9. Estimated average monthly household income", Q9_INCOME, length=1),
        yes_no_dk("Q10_INDIGENOUS", "10. Do you identify as a member of an indigenous group?"),
        alpha("Q10_INDIGENOUS_TXT", "10a. Name of indigenous group", length=80),
        yes_no("Q11_PWD", "11. Are you a person with disability (PWD)?"),
    ]
    return record("B_RESPONDENT_PROFILE", "B. Respondent Profile", "D", items)


# ============================================================
# Section C. Household Roster (Q30-Q50) — REPEATING, max_occurs=20
# Sub-tables C1-C5 flattened into single repeating record
# ============================================================

def build_section_c():
    Q34_RELATIONSHIP = [
        ("Head",              "01"),
        ("Spouse",            "02"),
        ("Son/Daughter",      "03"),
        ("Son-in-law/Daughter-in-law","04"),
        ("Grandchild",        "05"),
        ("Parent",            "06"),
        ("Brother/Sister",    "07"),
        ("Other relative",    "08"),
        ("Non-relative",      "09"),
    ]
    Q36_DISABILITY = [
        ("None",           "1"),
        ("Visual",         "2"),
        ("Hearing",        "3"),
        ("Physical",       "4"),
        ("Intellectual",   "5"),
        ("Psychosocial",   "6"),
        ("Multiple",       "7"),
        ("Other (specify)","8"),
    ]
    Q39_CIVIL = [
        ("Single",    "1"),
        ("Married",   "2"),
        ("Widowed",   "3"),
        ("Separated", "4"),
        ("Divorced",  "5"),
        ("Not applicable (below 15)","9"),
    ]
    Q40_EDUCATION = [
        ("No formal education",      "01"),
        ("Elementary (incomplete)",   "02"),
        ("Elementary (complete)",     "03"),
        ("High School (incomplete)",  "04"),
        ("High School (complete)",    "05"),
        ("Vocational / Technical",    "06"),
        ("College (incomplete)",      "07"),
        ("College (complete)",        "08"),
        ("Post-graduate",             "09"),
        ("Not applicable (below 5)",  "98"),
        ("I don't know",              "99"),
    ]
    Q41_EMPLOYMENT = [
        ("Employed (full-time)",  "1"),
        ("Employed (part-time)",  "2"),
        ("Self-employed",         "3"),
        ("Unemployed",            "4"),
        ("Retired",               "5"),
        ("Student",               "6"),
        ("Homemaker",             "7"),
        ("Not applicable",        "8"),
        ("Other (specify)",       "9"),
    ]
    Q45_PHILHEALTH_STATUS = [
        ("Member (direct contributor)",  "1"),
        ("Dependent",                    "2"),
        ("Indigent / sponsored member",  "3"),
        ("Senior citizen",               "4"),
        ("Not a member",                 "5"),
        ("I don't know",                 "6"),
    ]
    Q46_MEMBER_TYPE = [
        ("Employed (private sector)",      "01"),
        ("Employed (government)",          "02"),
        ("Self-employed / Informal sector","03"),
        ("Voluntary / Individual paying",  "04"),
        ("Overseas Filipino Worker (OFW)", "05"),
        ("Sponsored (LGU/National Gov't)", "06"),
        ("Indigent",                       "07"),
        ("Senior citizen",                 "08"),
        ("Lifetime member",                "09"),
        ("I don't know",                   "99"),
    ]
    items = [
        numeric("MEMBER_LINE_NO", "Household Member Line Number", length=2, zero_fill=True),
        # C1: Basic demographic
        alpha("Q30_NAME", "30. Name of household member", length=80),
        numeric("Q31_PRESENT", "31. Is this member present or away?", length=1,
                value_set_options=[("Present","1"),("Away","2")]),
        numeric("Q32_AGE", "32. Age (years)", length=3),
        numeric("Q33_SEX", "33. Sex assigned at birth", length=1,
                value_set_options=[("Male","1"),("Female","2")]),
        select_one("Q34_RELATIONSHIP", "34. Relationship to household head", Q34_RELATIONSHIP, length=2),
        # C2: Disability
        yes_no("Q35_HAS_DISABILITY", "35. Does this member have a disability?"),
        select_one("Q36_DISABILITY_TYPE", "36. Type of disability", Q36_DISABILITY, length=1),
        alpha("Q36_OTHER_TXT", "36. Disability — Other (specify) text", length=80),
        yes_no("Q37_DISABILITY_ID", "37. Does this member have a PWD ID?"),
        yes_no("Q38_DISABILITY_BENEFITS", "38. Does this member receive any disability benefits?"),
        # C3: Civil status, education, employment
        select_one("Q39_CIVIL_STATUS", "39. Civil status", Q39_CIVIL, length=1),
        select_one("Q40_EDUCATION", "40. Highest educational attainment", Q40_EDUCATION, length=2),
        select_one("Q41_EMPLOYMENT", "41. Current employment status", Q41_EMPLOYMENT, length=1),
        alpha("Q41_OTHER_TXT", "41. Employment — Other (specify) text", length=80),
        # C4: Social insurance coverage
        yes_no_dk("Q42_GSIS", "42. Is this member covered by GSIS?"),
        yes_no_dk("Q43_SSS", "43. Is this member covered by SSS?"),
        yes_no_dk("Q44_PAGIBIG", "44. Is this member covered by Pag-IBIG?"),
        # C5: PhilHealth and insurance
        select_one("Q45_PHILHEALTH", "45. PhilHealth membership status", Q45_PHILHEALTH_STATUS, length=1),
        select_one("Q46_PH_TYPE", "46. Type of PhilHealth membership", Q46_MEMBER_TYPE, length=2),
        yes_no_dk("Q47_PH_ACTIVE", "47. Is PhilHealth membership currently active?"),
        yes_no_dk("Q48_PH_ID", "48. Does this member have a PhilHealth ID?"),
        yes_no_dk("Q49_PRIVATE_INS", "49. Does this member have private health insurance/HMO?"),
        alpha("Q50_PRIVATE_INS_NAME", "50. Name of private insurance provider", length=80),
    ]
    return record("C_HOUSEHOLD_ROSTER", "C. Household Roster", "E", items, max_occurs=20)
```

- [ ] **Step 2: Add F4 sections D-G (UHC, YAKAP, BUCAS, Medicines)**

```python
# ============================================================
# Section D. UHC Awareness (Q51-Q60)
# ============================================================

def build_section_d():
    Q52_SOURCE = [
        ("News",                "1"),
        ("Legislation",         "2"),
        ("Social Media",        "3"),
        ("Friends / Family",    "4"),
        ("Health center/facility","5"),
        ("LGU/Barangay",        "6"),
        ("I don't know",        "7"),
        ("Other (specify)",     "8"),
    ]
    Q54_UNDERSTANDING = [
        ("Free healthcare for all Filipinos",                       "1"),
        ("Government provides financial assistance for health",     "2"),
        ("All Filipinos are automatically enrolled in PhilHealth",  "3"),
        ("Primary care provider for every Filipino",                "4"),
        ("Access to quality healthcare for everyone",               "5"),
        ("I don't know",                                            "6"),
        ("Other (specify)",                                         "7"),
    ]
    items = [
        yes_no_dk("Q51_UHC_HEARD", "51. Have you heard about Universal Health Care (UHC)?"),
        *select_all("Q52_UHC_SOURCE", "52. Sources of information about UHC", Q52_SOURCE),
        yes_no_dk("Q53_UHC_LAW_AWARE", "53. Are you aware that UHC is a law?"),
        *select_all("Q54_UHC_UNDERSTAND", "54. What is your understanding about UHC?", Q54_UNDERSTANDING),
    ]
    return record("D_UHC_AWARENESS", "D. UHC Awareness", "F", items)


# ============================================================
# Section E. YAKAP/Konsulta Awareness (Q61-Q68)
# ============================================================

def build_section_e():
    Q62_SOURCE = [
        ("News",                 "01"),
        ("Legislation",          "02"),
        ("Social Media",         "03"),
        ("Friends / Family",     "04"),
        ("Health center/facility","05"),
        ("PhilHealth",           "06"),
        ("LGU/Barangay",        "07"),
        ("BHW",                  "08"),
        ("I don't know",         "09"),
        ("Other (specify)",     "10"),
    ]
    items = [
        yes_no_dk("Q61_YAKAP_HEARD", "61. Have you heard about YAKAP/Konsulta?"),
        *select_all("Q62_YAKAP_SOURCE", "62. Sources of information about YAKAP/Konsulta", Q62_SOURCE),
        yes_no_dk("Q63_KONSULTA_ENROLLED", "63. Are you or any HH member enrolled in a Konsulta provider?"),
        yes_no_dk("Q64_KONSULTA_USED", "64. Have you used any Konsulta services in the past 12 months?"),
        yes_no("Q65_KONSULTA_SATISFIED", "65. Were you satisfied with the Konsulta services?"),
    ]
    return record("E_YAKAP_KONSULTA", "E. YAKAP/Konsulta Awareness", "G", items)


# ============================================================
# Section F. BUCAS Awareness (Q69-Q72)
# ============================================================

def build_section_f():
    items = [
        yes_no_dk("Q69_BUCAS_HEARD", "69. Have you heard about BUCAS?"),
        yes_no("Q70_BUCAS_ENROLLED", "70. Are you or any HH member enrolled in BUCAS?"),
        yes_no("Q71_BUCAS_USED", "71. Have you used any BUCAS services?"),
        yes_no("Q72_BUCAS_SATISFIED", "72. Were you satisfied with the BUCAS services?"),
    ]
    return record("F_BUCAS_AWARENESS", "F. BUCAS Awareness", "H", items)


# ============================================================
# Section G. Access to Medicines (Q73-Q78)
# ============================================================

def build_section_g():
    items = [
        yes_no_dk("Q73_GAMOT_HEARD", "73. Have you heard of GAMOT (DOH medicine access program)?"),
        yes_no("Q74_GAMOT_USED", "74. Have you used GAMOT?"),
        yes_no_dk("Q75_GENERIC_AWARE", "75. Are you aware of the Generics Act / generic medicines?"),
        yes_no("Q76_GENERIC_PREFER", "76. Do you prefer generic over branded medicines?"),
        yes_no("Q77_MEDS_ACCESSIBLE", "77. Do you find medicines accessible and affordable?"),
        yes_no("Q78_BOTIKA_AWARE", "78. Are you aware of Botika ng Barangay / Botika ng Bayan?"),
    ]
    return record("G_ACCESS_MEDICINES", "G. Access to Medicines", "I", items)
```

- [ ] **Step 3: Add F4 sections H-J (PhilHealth per member, Primary Care, Health-Seeking)**

```python
# ============================================================
# Section H. PhilHealth Registration (Q79-Q88) — REPEATING per member
# ============================================================

def build_section_h():
    Q79_REG_SOURCE = [
        ("PhilHealth representative","01"),
        ("No one / self-registered", "02"),
        ("LGU",                      "03"),
        ("Barangay Health Worker",   "04"),
        ("Primary care provider",    "05"),
        ("Friends / Family",         "06"),
        ("Other health care provider","07"),
        ("Health center/facility",   "08"),
        ("Employer",                 "09"),
        ("Other (specify)",          "10"),
    ]
    Q82_DIFFICULTY_REASONS = [
        ("Unclear process",                                 "1"),
        ("Took a long time",                                "2"),
        ("Did not know where to ask for help",              "3"),
        ("Had to travel a long way",                        "4"),
        ("No valid ID",                                     "5"),
        ("Did not know the required documents to register", "6"),
        ("I don't know",                                    "7"),
        ("Other (specify)",                                 "8"),
    ]
    Q85_BENEFITS = [
        ("No balance billing for basic ward accommodation","1"),
        ("Subsidized inpatient services",                  "2"),
        ("Subsidized outpatient services",                 "3"),
        ("There are no benefits to being a member",        "4"),
        ("I don't know",                                   "5"),
        ("Other (specify)",                                "6"),
    ]
    Q86_PREMIUM_PAY = [
        ("Yes, I pay directly",     "1"),
        ("Yes, my employer pays",   "2"),
        ("No, I do not pay premiums","3"),
    ]
    Q88_DIFF_PAYING = [
        ("Cannot afford the premium",                     "1"),
        ("Payment options are inconvenient",              "2"),
        ("No time to pay",                                "3"),
        ("Don't see value in paying",                     "4"),
        ("System of PhilHealth is unreliable/usually down","5"),
        ("I don't know",                                   "6"),
        ("Other (specify)",                                "7"),
    ]
    items = [
        numeric("MEMBER_LINE_NO", "Household Member Line Number", length=2, zero_fill=True),
        select_one("Q79_REG_SOURCE", "79. How did you find out about how to register to PhilHealth?",
                   Q79_REG_SOURCE, length=2),
        alpha("Q79_OTHER_TXT", "79. Registration source — Other (specify) text", length=80),
        select_one("Q80_ASSIST", "80. Who assisted you in the registration process?",
                   Q79_REG_SOURCE, length=2),
        alpha("Q80_OTHER_TXT", "80. Registration assistant — Other (specify) text", length=80),
        yes_no("Q81_REG_DIFFICULTY", "81. Did you have any difficulties in the registration process?"),
        *select_all("Q82_DIFFICULTY", "82. What did you find difficult?", Q82_DIFFICULTY_REASONS),
        yes_no("Q83_KNOWS_ASSIST", "83. Would you know where to seek assistance?"),
        alpha("Q84_WHERE_ASSIST", "84. Where would you go to seek assistance?", length=120),
        *select_all("Q85_BENEFITS", "85. What are some benefits of being a PhilHealth member?", Q85_BENEFITS),
        select_one("Q86_PREMIUM_PAY", "86. Do you pay PhilHealth premiums every month?", Q86_PREMIUM_PAY, length=1),
        yes_no("Q87_PREMIUM_DIFFICULT", "87. Do you find it difficult to pay premiums?"),
        *select_all("Q88_DIFF_PAYING", "88. Why did you find it difficult?", Q88_DIFF_PAYING),
    ]
    return record("H_PHILHEALTH_REG", "H. PhilHealth Registration", "J", items, max_occurs=20)


# ============================================================
# Section I. Primary Care Utilization (Q89-Q100)
# ============================================================

def build_section_i():
    Q92_FACILITY_TYPE = [
        ("YAKAP/Konsulta or primary care provider",     "01"),
        ("Barangay Health Center",                      "02"),
        ("Rural Health Unit / Health Center",            "03"),
        ("Public Hospital",                             "04"),
        ("Private Hospital",                            "05"),
        ("Private Clinic",                              "06"),
        ("Traditional Healer or Manghihilot/Albularyo", "07"),
        ("I don't know",                                "08"),
        ("Other (specify)",                             "09"),
    ]
    Q93_WHY_NOT = [
        ("I don't get sick",              "1"),
        ("I recently moved into the area","2"),
        ("It's expensive",                "3"),
        ("I can treat myself",            "4"),
        ("I don't know where to go",      "5"),
        ("I don't know",                  "6"),
        ("Other (specify)",               "7"),
    ]
    Q94_TRANSPORT = [
        ("Walk",                                "01"),
        ("Bike",                                "02"),
        ("Public Bus",                          "03"),
        ("Jeepney",                             "04"),
        ("Tricycle",                            "05"),
        ("Car (including private taxi/cab)",     "06"),
        ("Motorcycle",                          "07"),
        ("Boat",                                "08"),
        ("Taxi",                                "09"),
        ("Pedicab",                             "10"),
        ("E-bike",                              "11"),
        ("Other (specify)",                     "12"),
    ]
    items = [
        yes_no_dk("Q89_HAS_USUAL_FACILITY",
                  "89. In the past 12 months, do you have a clinic or health center that you usually go to?"),
        alpha("Q89A_FACILITY_NAME", "89a. What is the name of the facility?", length=120),
        yes_no("Q90_IS_USUAL", "90. Is this the facility you usually go to for general health concerns?"),
        *select_all("Q91_WHY_DIFF", "91. Why did you go to this facility?", [
            ("More accessible than usual facility","1"),("Needed specialist not available","2"),
            ("Recommended by friends/family","3"),("Wanted to try another facility","4"),
            ("Prefer this facility","5"),("Referred by usual facility","6"),
            ("Usual facility closed","7"),("Doctor transferred here","8"),("Other (specify)","9"),
        ]),
        select_one("Q92_FACILITY_TYPE", "92. Type of facility usually visited", Q92_FACILITY_TYPE, length=2),
        *select_all("Q93_WHY_NOT", "93. Why do you not have a usual facility?", Q93_WHY_NOT),
        *select_all("Q94_TRANSPORT", "94. Transportation modes to nearest primary care facility", Q94_TRANSPORT),
        numeric("Q95_TRAVEL_TIME", "95. Travel time to nearest primary care facility (minutes)", length=3),
        numeric("Q96_TRAVEL_COST", "96. Travel cost to facility (PHP, one-way)", length=5),
        yes_no("Q97_KNOWS_BOOKING", "97. Do you know how to book an appointment?"),
        select_one("Q98_PHONE_ADVICE", "98. Can you get advice over the phone when facility is open?",
                   [("Yes","1"),("No","2"),("I haven't tried","3"),("I don't know","4")], length=1),
        select_one("Q99_AFTER_HOURS", "99. Is there a phone number to call when facility is closed?",
                   [("Yes","1"),("No","2"),("I haven't tried","3"),("I don't know","4")], length=1),
        select_one("Q100_LEAVE_WORK", "100. Do you have to take leave to visit?",
                   [("Yes","1"),("No","2"),("I haven't tried","3"),("I don't know","4"),("Not applicable","9")], length=1),
    ]
    return record("I_PRIMARY_CARE", "I. Primary Care Utilization", "K", items)


# ============================================================
# Section J. Health-Seeking Behavior (Q101-Q107) — REPEATING per member
# ============================================================

def build_section_j():
    Q101_CHECKUP_FREQ = [
        ("More than once a year",          "1"),
        ("Every year",                     "2"),
        ("Every 2-3 years",               "3"),
        ("Every 4-5 years",               "4"),
        ("No set time; once or twice ever","5"),
        ("Never; only when sick",          "6"),
        ("Other (specify)",                "7"),
    ]
    Q102_VISIT_REASON = [
        ("Consultation for new health problem",  "1"),
        ("Follow-up ongoing health problem",     "2"),
        ("For tests/diagnostics only",           "3"),
        ("For a general check-up",               "4"),
        ("Health certificate/administrative",     "5"),
        ("Immunizations/vaccinations",            "6"),
        ("Doctor transferred to this facility",   "7"),
        ("Other (specify)",                       "8"),
    ]
    Q103_CARE_TYPE = [
        ("Outpatient care",           "1"),
        ("Inpatient care",            "2"),
        ("Emergency care",            "3"),
        ("Primary care consultation", "4"),
        ("Other (specify)",           "5"),
    ]
    Q106_FORGONE_WHY = [
        ("Not sick enough",                     "1"),
        ("It's too expensive",                  "2"),
        ("Could not take time off work",        "3"),
        ("Could not get appointment soon enough","4"),
        ("No transportation available",         "5"),
        ("Afraid to know my illness",           "6"),
        ("I don't know",                        "7"),
        ("Other (specify)",                     "8"),
    ]
    Q107_ACTIONS = [
        ("Visited other healthcare facility",  "1"),
        ("Sought alternative care",            "2"),
        ("Sought telemedicine",                "3"),
        ("Used home care",                     "4"),
        ("Bought medicine from a pharmacy",    "5"),
        ("Did not seek other forms of care",   "6"),
        ("Other (specify)",                    "7"),
    ]
    items = [
        numeric("MEMBER_LINE_NO", "Household Member Line Number", length=2, zero_fill=True),
        select_one("Q101_CHECKUP_FREQ", "101. How often do you have a general check-up?",
                   Q101_CHECKUP_FREQ, length=1),
        *select_all("Q102_VISIT_REASON", "102. Why would you visit a health facility?", Q102_VISIT_REASON),
        *select_all("Q103_CARE_TYPE", "103. Forms of care accessed in the last 6 months", Q103_CARE_TYPE),
        yes_no("Q104_PREVENTIVE", "104. Have you consulted a physician for preventative reasons?"),
        yes_no("Q105_FORGONE", "105. In the last 6 months, had a medical problem and chose NOT to see a provider?"),
        *select_all("Q106_FORGONE_WHY", "106. Why not?", Q106_FORGONE_WHY),
        *select_all("Q107_ACTIONS", "107. Other actions taken to improve health?", Q107_ACTIONS),
    ]
    return record("J_HEALTH_SEEKING", "J. Health-Seeking Behavior", "L", items, max_occurs=20)
```

- [ ] **Step 4: Add F4 sections K-M (Referrals, NBB, ZBB)**

```python
# ============================================================
# Section K. Referrals (Q108-Q125)
# ============================================================

def build_section_k():
    Q109_TYPE = [
        ("Outpatient care",   "01"),
        ("Emergency care",    "02"),
        ("Inpatient care",    "03"),
        ("Dental care",       "04"),
        ("Other facility",    "05"),
        ("Special therapy",   "06"),
        ("Alternative care",  "07"),
        ("Medical mission",   "08"),
        ("Home healthcare",   "09"),
        ("Telemedicine",      "10"),
        ("None of the above", "11"),
        ("Other (specify)",   "12"),
    ]
    Q110_SPECIALIST = [
        ("No specialty",          "01"),("Anesthesia",            "02"),
        ("Dermatology",           "03"),("Emergency Medicine",    "04"),
        ("Family Medicine",       "05"),("General Surgery",       "06"),
        ("Internal Medicine",     "07"),("Neurology",             "08"),
        ("Nuclear Medicine",      "09"),("Obstetrics and Gynecology","10"),
        ("Occupational Medicine", "11"),("Ophthalmology",         "12"),
        ("Orthopedics",           "13"),("Otorhinolaryngology (ENT)","14"),
        ("Pathology",             "15"),("Pediatrics",            "16"),
        ("Physical and Rehabilitation Medicine","17"),("Psychiatry","18"),
        ("Public health",         "19"),("Radiology",             "20"),
        ("Research",              "21"),("I don't know",          "22"),
        ("Other (specify)",       "23"),
    ]
    Q111_METHOD = [
        ("Physical referral slip",  "1"),
        ("E-referral",              "2"),
        ("Phone call",              "3"),
        ("I don't know",            "4"),
        ("Other (specify)",         "5"),
    ]
    Q112_VISIT = [
        ("Yes",                          "1"),
        ("No, I'm not planning to",      "2"),
        ("Not yet, but I'm planning to", "3"),
    ]
    Q113_WHY_NOT = [
        ("Facility is too far",              "1"),
        ("Do not trust the referred facility","2"),
        ("No time",                          "3"),
        ("Worried about additional costs",   "4"),
        ("Not needed",                       "5"),
        ("Don't know how to get to facility","6"),
        ("Other (specify)",                  "7"),
    ]
    Q121_WHY_HOSPITAL = [
        ("Referred by other specialist",       "1"),
        ("Nearest facility to house",          "2"),
        ("Facility is usual source of care",   "3"),
        ("Only place for certain test",        "4"),
        ("Referred by BHW/nurse/midwife",      "5"),
        ("Referred by family / friends",       "6"),
        ("Offers subsidized/free services",    "7"),
        ("I don't know",                       "8"),
        ("Other (specify)",                    "9"),
    ]
    SATISFACTION_5PT = [
        ("Very Satisfied",                    "1"),
        ("Satisfied",                         "2"),
        ("Neither Satisfied nor Dissatisfied","3"),
        ("Dissatisfied",                      "4"),
        ("Very Dissatisfied",                 "5"),
        ("Not applicable",                    "9"),
    ]
    items = [
        yes_no("Q108_REFERRED", "108. Were you referred to another facility in the past 6 months?"),
        *select_all("Q109_TYPE", "109. What type of care was the referral for?", Q109_TYPE),
        select_one("Q110_SPECIALIST", "110. What kind of specialist was recommended?", Q110_SPECIALIST, length=2),
        alpha("Q110_OTHER_TXT", "110. Specialist — Other (specify) text", length=80),
        select_one("Q111_METHOD", "111. How did they refer you?", Q111_METHOD, length=1),
        alpha("Q111_OTHER_TXT", "111. Referral method — Other (specify) text", length=80),
        select_one("Q112_VISITED", "112. Did you visit another facility after the referral?", Q112_VISIT, length=1),
        *select_all("Q113_WHY_NOT", "113. Why are you not planning to visit?", Q113_WHY_NOT),
        yes_no("Q114_DISCUSSED", "114. Did they discuss different places you could go?"),
        yes_no("Q115_HELPED_APPT", "115. Did they help you make the appointment?"),
        yes_no("Q116_WROTE_INFO", "116. Did they write down information for the specialist?"),
        yes_no("Q117_FOLLOWUP", "117. Did they follow up with you about what happened?"),
        select_one("Q118_SAT_REFERRAL", "118. Satisfaction with the referral process", SATISFACTION_5PT, length=1),
        yes_no("Q119_WAS_REFERRAL", "119. Was the visit a referral from your primary care facility?"),
        yes_no_dk("Q120_PCP_KNOWS", "120. Does your primary care provider know about the visit?"),
        *select_all("Q121_WHY_HOSPITAL", "121. Why did you decide to visit a hospital?", Q121_WHY_HOSPITAL),
        yes_no("Q122_PCP_DISCUSSED", "122. Did your PCP discuss different places to go?"),
        yes_no("Q123_PCP_HELPED_APPT", "123. Did your PCP help make the appointment?"),
        yes_no("Q124_PCP_WROTE_INFO", "124. Did your PCP write down information for the specialist?"),
        select_one("Q125_SAT_REFERRAL2", "125. Overall satisfaction with referral experience", SATISFACTION_5PT, length=1),
    ]
    return record("K_REFERRALS", "K. Referrals", "M", items)


# ============================================================
# Section L. NBB Awareness (Q126-Q131)
# ============================================================

def build_section_l():
    Q127_SOURCE = [
        ("News",                "1"),
        ("Legislation",         "2"),
        ("Social Media",        "3"),
        ("Friends / Family",    "4"),
        ("Health center/facility","5"),
        ("LGU/Barangay",        "6"),
        ("I don't know",        "7"),
        ("Other (specify)",     "8"),
    ]
    Q128_UNDERSTANDING = [
        ("Patient does not pay any hospital bill",          "1"),
        ("PhilHealth will cover cost of treatment",         "2"),
        ("Medicine and service are already included",       "3"),
        ("No cash payment required upon discharge",         "4"),
        ("Applies only to certain patients or hospitals",   "5"),
        ("Bills settled between hospital and PhilHealth",   "6"),
        ("Patients should not be charged extra fees",       "7"),
        ("I don't know",                                    "8"),
        ("Other (specify)",                                 "9"),
    ]
    Q130_HOSPITAL_TYPE = [
        ("Public",                "1"),
        ("DOH-retained hospital", "2"),
        ("Private",               "3"),
    ]
    items = [
        yes_no_dk("Q126_NBB_HEARD", "126. Have you heard of the No Balance Billing (NBB)?"),
        *select_all("Q127_NBB_SOURCE", "127. Sources of information about NBB", Q127_SOURCE),
        *select_all("Q128_NBB_UNDERSTAND", "128. What is your understanding about NBB?", Q128_UNDERSTANDING),
        yes_no_dk("Q129_CONFINED", "129. Were you or a HH member confined in a hospital in the past 6 months?"),
        select_one("Q130_HOSPITAL_TYPE", "130. For the most recent hospitalization, what type of hospital?",
                   Q130_HOSPITAL_TYPE, length=1),
        yes_no_dk("Q131_NBB_OOP", "131. During hospitalization in a DOH-retained hospital, did you pay OOP that should have been covered under NBB?"),
    ]
    return record("L_NBB_AWARENESS", "L. NBB Awareness", "N", items)


# ============================================================
# Section M. ZBB Awareness (Q132-Q136)
# ============================================================

def build_section_m():
    Q133_SOURCE = [
        ("News",                "1"),
        ("Legislation",         "2"),
        ("Social Media",        "3"),
        ("Friends / Family",    "4"),
        ("Health center/facility","5"),
        ("LGU/Barangay",        "6"),
        ("I don't know",        "7"),
        ("Other (specify)",     "8"),
    ]
    Q134_UNDERSTANDING = [
        ("Patient does not pay any hospital bill",          "1"),
        ("PhilHealth will cover cost of treatment",         "2"),
        ("Medicine and service are already included",       "3"),
        ("No cash payment required upon discharge",         "4"),
        ("Applies only to certain patients or hospitals",   "5"),
        ("Bills settled between hospital and PhilHealth",   "6"),
        ("Patients should not be charged extra fees",       "7"),
        ("I don't know",                                    "8"),
        ("Other (specify)",                                 "9"),
    ]
    Q136_MOST_EXPENSIVE = [
        ("Medicine",          "1"),
        ("Laboratory Tests",  "2"),
        ("Medical Supplies",  "3"),
        ("Doctor's Fee",      "4"),
    ]
    items = [
        yes_no_dk("Q132_ZBB_HEARD", "132. Have you heard of the Zero Balance Billing (ZBB)?"),
        *select_all("Q133_ZBB_SOURCE", "133. Sources of information about ZBB", Q133_SOURCE),
        *select_all("Q134_ZBB_UNDERSTAND", "134. What is your understanding about ZBB?", Q134_UNDERSTANDING),
        yes_no_dk("Q135_ZBB_OOP", "135. During hospitalization in a DOH-retained hospital, did you pay OOP that should have been covered under ZBB?"),
        select_one("Q136_MOST_EXPENSIVE", "136. From your most recent visit, which charge was most expensive?",
                   Q136_MOST_EXPENSIVE, length=1),
        numeric("Q137_FINAL_AMOUNT", "137. Final amount paid in cash at the hospital cashier upon discharge (PHP)", length=8),
        yes_no("Q138_RECALL_BREAKDOWN", "138. Do you recall the breakdown of the bill?"),
        *select_all("Q139_BILL_ITEMS", "139. Which items were included in the bill?", [
            ("Rooms","1"),("Doctor's Fee","2"),("Diagnostic or laboratory procedure","3"),
            ("Medical equipment or supplies","4"),("Medicines or drugs","5"),
            ("Non-medical expenses","6"),("Other expenses","7"),
        ]),
        numeric("Q139A_NO_RECEIPT_AMT", "139a. Amount charged for services with no receipts (PHP)", length=8),
        yes_no("Q140_RECALL_PAYMENT", "140. Do you recall how you paid for your bill?"),
        *select_all("Q141_HOW_PAID", "141. How did you pay?", [
            ("Own income/household income","01"),("PhilHealth","02"),
            ("Private insurance/HMO","03"),("Loan","04"),("Sale of assets","05"),
            ("Donations from charities/NGOs","06"),("Donations from LGUs","07"),
            ("National Government Agencies","08"),("Paid by someone else","09"),
            ("Other (specify)","10"),
        ]),
    ]
    return record("M_ZBB_AWARENESS", "M. ZBB Awareness", "O", items)
```

- [ ] **Step 5: Add F4 section N (Household Expenditures) — flat item batteries**

```python
# ============================================================
# Section N. Household Expenditures (Q142-Q180)
# Flat item batteries: each item has consumed (Y/N), purchased_amt, in_kind_amt
# Reference periods vary: weekly, monthly, 6-month, 12-month
# ============================================================

def _expenditure_item(prefix, label):
    """Three items per expenditure line: consumed Y/N, purchased amount, in-kind value."""
    return [
        yes_no(f"{prefix}_CONSUMED", f"{label} — Consumed?"),
        numeric(f"{prefix}_PURCHASED", f"{label} — Amount purchased (PHP)", length=8),
        numeric(f"{prefix}_INKIND", f"{label} — Estimated in-kind value (PHP)", length=8),
    ]

def build_section_n():
    items = []

    # A. Food Items (last WEEK) — Q142-Q155
    food_items = [
        ("Q142_CEREALS",     "142. Cereals (rice, flour, noodles, corn)"),
        ("Q143_PULSES",      "143. Pulses, roots, tubers, plantains, nuts"),
        ("Q144_VEGETABLES",  "144. Vegetables"),
        ("Q145_FRUITS",      "145. Fruits"),
        ("Q146_FISH",        "146. Fish and other seafoods"),
        ("Q147_MEAT",        "147. Any kind of meat and offal"),
        ("Q148_EGGS",        "148. Eggs"),
        ("Q149_MILK",        "149. Milk and milk products"),
        ("Q150_FATS",        "150. Butter, lard, oils and fats"),
        ("Q151_CONDIMENTS",  "151. Condiments, spices, and ready-made meals"),
        ("Q152_BEVERAGES",   "152. Water and non-alcoholic beverages"),
        ("Q153_ALCOHOL",     "153. Alcoholic beverages"),
        ("Q155_RESTAURANT",  "155. Meals and snacks from restaurants"),
    ]
    for prefix, label in food_items:
        items.extend(_expenditure_item(prefix, label))

    # B. Non-food (last WEEK) — Q156
    items.extend(_expenditure_item("Q156_TOBACCO", "156. Smoking and tobacco products"))

    # Non-food (last MONTH) — Q157-Q163
    monthly_nonfood = [
        ("Q157_PERSONAL_CARE", "157. Personal care products"),
        ("Q158_HOUSEHOLD",     "158. Household cleaning and maintenance"),
        ("Q159_TRANSPORT",     "159. Passenger transportation"),
        ("Q160_TELECOM",       "160. Phone, mobile, WiFi, cable TV"),
        ("Q161_RECREATION",    "161. Recreational, cultural, sporting"),
        ("Q162_POSTAL",        "162. Postal services"),
        ("Q163_HOUSING",       "163. Housing (actual/estimated rent)"),
    ]
    for prefix, label in monthly_nonfood:
        items.extend(_expenditure_item(prefix, label))

    # Non-food (last 6 MONTHS) — Q164-Q165
    items.extend(_expenditure_item("Q164_RECREATION_6M", "164. Recreational devices (6-month)"))
    items.extend(_expenditure_item("Q165_CLOTHING",      "165. Clothing, footwear, textiles"))

    # Non-food (last 12 MONTHS) — Q166-Q170
    annual_nonfood = [
        ("Q166_EDUCATION",     "166. Educational services"),
        ("Q167_ACCOMMODATION", "167. Accommodation services"),
        ("Q168_GARDEN_PETS",   "168. Garden and personal pets"),
        ("Q169_HEALTH_INS",    "169. Health insurance"),
        ("Q170_OTHER_INS",     "170. Other insurance"),
    ]
    for prefix, label in annual_nonfood:
        items.extend(_expenditure_item(prefix, label))

    # E. Health Products and Services (last 12 MONTHS) — Q171-Q173
    items.extend(_expenditure_item("Q171_INPATIENT",   "171. Inpatient care services"))
    items.extend(_expenditure_item("Q172_EMERGENCY",   "172. Emergency transportation"))

    # Health (last 6 MONTHS) — Q174-Q178
    health_6m = [
        ("Q174_PREVENTIVE",   "174. Preventive services (immunization)"),
        ("Q175_DIAGNOSTIC",   "175. Diagnostic and laboratory tests"),
        ("Q176_ASSISTIVE",    "176. Assistive health products (vision, hearing, mobility)"),
        ("Q177_MEDICAL_PROD", "177. Medical products (antigen tests, masks)"),
    ]
    for prefix, label in health_6m:
        items.extend(_expenditure_item(prefix, label))

    # Health (last MONTH) — Q179-Q180
    items.extend(_expenditure_item("Q179_MEDICINES",  "179. Medicines, vaccines, pharmaceuticals"))
    items.extend(_expenditure_item("Q180_OUTPATIENT", "180. Outpatient medical and dental services"))

    return record("N_HOUSEHOLD_EXPENDITURES", "N. Household Expenditures", "P", items)
```

- [ ] **Step 6: Add F4 sections O-Q (Sources of Funds, Financial Risk, Anxiety)**

```python
# ============================================================
# Section O. Sources of Funds for Health (Q182-Q192)
# ============================================================

def build_section_o():
    Q191_INCOME_PCT = [
        ("None",          "1"),
        ("Less than 1%",  "2"),
        ("1-3%",          "3"),
        ("4-6%",          "4"),
        ("More than 6%",  "5"),
        ("Don't know",    "6"),
    ]
    Q192_FOREGONE_CARE = [
        ("Doctor/consultation visit",        "1"),
        ("Medicines or treatments",          "2"),
        ("Laboratory tests / diagnostics",   "3"),
        ("Hospital admission / inpatient care","4"),
        ("Preventive care",                  "5"),
        ("Dental care",                      "6"),
        ("Other (specify)",                  "7"),
        ("We do not forego care",            "8"),
    ]
    items = [
        yes_no("Q182_CURRENT_INCOME", "182. Current income of any household members"),
        yes_no("Q183_SAVINGS",        "183. Savings, pension"),
        yes_no("Q184_SOLD_ASSETS",    "184. Selling of household's assets or goods"),
        yes_no("Q185_BORROW_FAMILY",  "185. Borrowing from friends or relatives"),
        yes_no("Q186_BORROW_INST",    "186. Borrowing from institutions"),
        yes_no("Q187_REMITTANCE",     "187. Remittance or money gift"),
        yes_no("Q188_GOVT_ASSIST",    "188. Government assistance (DSWD, local)"),
        yes_no("Q189_LGU_DONATION",   "189. Donation from LGUs"),
        yes_no("Q190_OTHER_SOURCE",   "190. Other source"),
        alpha("Q190_OTHER_TXT",       "190. Other source — specify", length=120),
        select_one("Q191_INCOME_PCT", "191. Portion of income willing to set aside for health care",
                   Q191_INCOME_PCT, length=1),
        *select_all("Q192_FOREGONE", "192. What kind of care do you usually forego for financial reasons?",
                    Q192_FOREGONE_CARE),
    ]
    return record("O_SOURCES_OF_FUNDS", "O. Sources of Funds for Health", "Q", items)


# ============================================================
# Section P. Financial Risk Protection (Q193-Q195)
# ============================================================

def build_section_p():
    Q195_WTP = [
        ("Php 0 - Php 249",        "1"),
        ("Php 250 - Php 499",      "2"),
        ("Php 500 - Php 999",      "3"),
        ("Php 1,000 - Php 1,249",  "4"),
        ("Php 1,250 - Php 1,499",  "5"),
        ("Php 1,500 - Php 1,749",  "6"),
        ("Php 1,750 - Php 1,999",  "7"),
        ("Php 2,000 and above",    "8"),
        ("Other (specify)",         "9"),
    ]
    items = [
        yes_no("Q193_DELAYED_CARE", "193. Delayed seeking care for financial reasons in the last 6 months?"),
        yes_no("Q194_NOT_FOLLOWED", "194. Seen a doctor and not fully followed advice for financial reasons?"),
        select_one("Q195_WTP_CONSULT", "195. Highest amount willing to pay for a consultation", Q195_WTP, length=1),
        alpha("Q195_OTHER_TXT", "195. WTP — Other (specify) text", length=80),
    ]
    return record("P_FINANCIAL_RISK", "P. Financial Risk Protection", "R", items)


# ============================================================
# Section Q. Anxiety about Household Finances (Q196-Q198)
# ============================================================

def build_section_q():
    Q196_REDUCED = [
        ("Yes",              "1"),
        ("No",               "2"),
        ("Don't know",       "3"),
        ("Refused to answer","4"),
    ]
    Q197_WORRIED = [
        ("Very worried",      "1"),
        ("Somewhat worried",  "2"),
        ("Not too worried",   "3"),
        ("Not worried at all","4"),
    ]
    Q198_REASONS = [
        ("Loss of income",                                   "1"),
        ("Healthcare costs related to COVID-19",              "2"),
        ("Healthcare costs NOT related to COVID-19",          "3"),
    ]
    items = [
        select_one("Q196_REDUCED_SPEND", "196. Had to reduce spending on needs because of health expenditure?",
                   Q196_REDUCED, length=1),
        select_one("Q197_WORRIED", "197. How worried are you about household finances in the next month?",
                   Q197_WORRIED, length=1),
        *select_all("Q198_WORRY_REASONS", "198. Reasons for worry about finances", Q198_REASONS, with_other_txt=False),
    ]
    return record("Q_FINANCIAL_ANXIETY", "Q. Financial Anxiety", "S", items)
```

- [ ] **Step 7: Add F4 dictionary assembly and main()**

```python
# ============================================================
# ASSEMBLE THE DICTIONARY
# ============================================================

def build_f4_dictionary():
    records = [
        record("HOUSEHOLDSURVEY_REC", "HouseholdSurvey Record", "1", []),
        build_f4_field_control(),
        build_f4_geo_id(),
        build_section_a(),
        build_section_b(),
        build_section_c(),   # Repeating: max_occurs=20
        build_section_d(),
        build_section_e(),
        build_section_f(),
        build_section_g(),
        build_section_h(),   # Repeating: max_occurs=20
        build_section_i(),
        build_section_j(),   # Repeating: max_occurs=20
        build_section_k(),
        build_section_l(),
        build_section_m(),
        build_section_n(),
        build_section_o(),
        build_section_p(),
        build_section_q(),
    ]
    return build_dictionary(
        dict_name="HOUSEHOLDSURVEY_DICT",
        dict_label="HouseholdSurvey",
        id_item_name="QUESTIONNAIRE_NO",
        id_item_label="Questionnaire No",
        id_length=6,
        records=records,
    )


def main():
    out_path = Path(__file__).parent / "HouseholdSurvey.dcf"
    write_dcf(build_f4_dictionary(), out_path)


if __name__ == "__main__":
    main()
```

- [ ] **Step 8: Run F4 generator and verify output**

```bash
cd deliverables/CSPro/F4
python generate_dcf.py
```

Expected output:
```
Wrote deliverables/CSPro/F4/HouseholdSurvey.dcf
  Records: 20
  Items:   <count>
```

Verify:
```bash
python -c "import json; d=json.load(open('HouseholdSurvey.dcf')); recs=d['levels'][0]['records']; print('Valid JSON, records:', len(recs)); repeating=[r['name'] for r in recs if r['occurrences']['maximum']>1]; print('Repeating:', repeating)"
```

Expected: `Repeating: ['C_HOUSEHOLD_ROSTER', 'H_PHILHEALTH_REG', 'J_HEALTH_SEEKING']`

- [ ] **Step 9: Commit F4 generator**

```bash
git add deliverables/CSPro/F4/generate_dcf.py deliverables/CSPro/F4/HouseholdSurvey.dcf
git commit -m "feat: F4 Household Survey data dictionary generator (19 records, sections A-Q, 3 repeating)"
```

---

### Task 6: Final verification and cross-check

**Files:**
- All generated .dcf files

- [ ] **Step 1: Regenerate all three DCFs and verify they load as valid JSON**

```bash
cd deliverables/CSPro
python F1/generate_dcf.py
python F3/generate_dcf.py
python F4/generate_dcf.py
```

- [ ] **Step 2: Print summary statistics**

```bash
python -c "
import json
for name in ['F1/FacilityHeadSurvey.dcf', 'F3/PatientSurvey.dcf', 'F4/HouseholdSurvey.dcf']:
    d = json.load(open(name))
    recs = d['levels'][0]['records']
    items = sum(len(r['items']) for r in recs)
    repeating = [r['name'] for r in recs if r['occurrences']['maximum'] > 1]
    print(f'{name}: {len(recs)} records, {items} items, repeating={repeating}')
"
```

- [ ] **Step 3: Verify F1 identity-diff one last time**

```bash
cd deliverables/CSPro/F1
cp FacilityHeadSurvey.dcf FacilityHeadSurvey.dcf.bak
python generate_dcf.py
diff FacilityHeadSurvey.dcf FacilityHeadSurvey.dcf.bak && echo "PASS: identical" || echo "FAIL: files differ"
rm FacilityHeadSurvey.dcf.bak
```

- [ ] **Step 4: Commit any final changes**

```bash
git add -A deliverables/CSPro/
git commit -m "chore: regenerate all F-series DCFs, verify cross-instrument consistency"
```
