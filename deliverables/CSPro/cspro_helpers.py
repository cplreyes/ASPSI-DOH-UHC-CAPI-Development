"""
cspro_helpers.py — Shared helpers and value sets for CSPro 8.0 dictionary generators.

Extracted from F1/generate_dcf.py so F3 (Patient Survey) and F4 (Household Survey)
can reuse the same item-builder functions, value sets, and common record builders
without duplicating code.

Usage:
    from cspro_helpers import (
        YES_NO, YES_NO_DK, YES_NO_NA, UHC9_OPTIONS, FREQUENCY, WHY_DIFF_OPTIONS,
        SATISFACTION_5PT, ENUM_RESULT_OPTIONS,
        numeric, alpha, yes_no, yes_no_dk, yes_no_na, select_one, select_all,
        uhc9_item, record,
        build_field_control, build_geo_id,
        build_dictionary, write_dcf,
    )

Compatibility guarantee:
    The value sets and helper functions (lines 1–220 of F1/generate_dcf.py) are
    reproduced here byte-for-identically so that F1's refactored generator produces
    the same JSON output after switching to imports.  Do NOT modify the existing
    constants or helper bodies without also updating the F1 generator.
"""

import csv
import json
import re
from pathlib import Path

# ============================================================
# 1. VALUE SETS — reused across many items in multiple surveys
# ============================================================


def load_psgc_value_set(csv_path, code_col="code", name_col="name"):
    """Load a PSGC CSV (produced by F1/inputs/parse_psgc.py) into
    value_set_options tuples (label, code). Source: PSA 1Q 2026 publication.
    """
    options = []
    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            options.append((row[name_col], row[code_col]))
    return options




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

# UHC9 — 9-option pattern for all UHC Act implementation questions.
# Codes 1–9 are load-bearing for skip logic ("if in 5..9 then skip").
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

# NEW — used by F3 (Patient Survey) and F4 (Household Survey)
SATISFACTION_5PT = [
    ("Very Satisfied",                        "1"),
    ("Satisfied",                             "2"),
    ("Neither Satisfied nor Dissatisfied",    "3"),
    ("Dissatisfied",                          "4"),
    ("Very Dissatisfied",                     "5"),
    ("Not applicable",                        "9"),
]

# NEW — shared by all FIELD_CONTROL records (F1, F3, F4)
ENUM_RESULT_OPTIONS = [
    ("Completed",  "1"),
    ("Postponed",  "2"),
    ("Refused",    "3"),
    ("Incomplete", "4"),
]

# AAPOR Standard Definitions 10th ed. (2023) — Final Disposition Codes
# adapted for in-person CAPI health surveys. 3-digit numeric (zero-filled)
# maps AAPOR decimals to integers (×100). The "In Progress" (000) sentinel
# is ASPSI-internal — set at case start by FIELD_CONTROL.preproc, rewritten
# to the final code on the CLOSING form.
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

def _case_control_items(survey_code):
    """Five case-control items prepended to every FIELD_CONTROL record (F1/F3/F4).

    Captures case-start metadata: instrument identification, interviewer,
    start-timestamps, and initial AAPOR disposition. Populated by the
    FIELD_CONTROL.preproc handler in the instrument's .apc file — see the
    corresponding F*-Skip-Logic-and-Validations spec §2 for PROC snippets.

    Parameters
    ----------
    survey_code : str
        The instrument code string — one of "F1", "F3", "F4". Attached to
        the SURVEY_CODE item's value set as the sole allowed value so the
        DCF self-documents which instrument the dictionary belongs to.

    Returns
    -------
    list of dict
        [SURVEY_CODE, INTERVIEWER_ID, DATE_STARTED, TIME_STARTED,
         AAPOR_DISPOSITION]
    """
    return [
        alpha("SURVEY_CODE",        "Survey Instrument Code",              length=2),
        numeric("INTERVIEWER_ID",   "Interviewer ID",                      length=4,
                zero_fill=True),
        numeric("DATE_STARTED",     "Date Interview Started (YYYYMMDD)",   length=8),
        numeric("TIME_STARTED",     "Time Interview Started (HHMMSS)",     length=6),
        numeric("AAPOR_DISPOSITION", "AAPOR Disposition Code",             length=3,
                zero_fill=True, value_set_options=AAPOR_DISPOSITION_OPTIONS),
    ]


def build_field_control(survey_code, extra_items=None, date_label_entity="the Facility"):
    """Build a FIELD_CONTROL record (record type "A").

    Parameters
    ----------
    survey_code : str
        Instrument code ("F1", "F3", "F4") — prepended as SURVEY_CODE item.
    extra_items : list, optional
        Additional item dicts to append after the standard block.
        Use this when a survey needs fields not present in the base template.
    date_label_entity : str, optional
        Human-readable entity name used in the date-field labels.
        Defaults to "the Facility" (matching F1 semantics).
        Pass "the Patient" for F3, "the Household" for F4, etc.

    Standard items (in order):
        SURVEY_CODE, INTERVIEWER_ID, DATE_STARTED, TIME_STARTED, AAPOR_DISPOSITION,
        SURVEY_TEAM_LEADER_S_NAME, ENUMERATOR_S_NAME, FIELD_VALIDATED_BY,
        FIELD_EDITED_BY, DATE_FIRST_VISITED (length 8), DATE_FINAL_VISIT (length 8),
        TOTAL_NUMBER_OF_VISITS, ENUM_RESULT_FIRST_VISIT, ENUM_RESULT_FINAL_VISIT,
        CONSENT_GIVEN.
    """
    items = _case_control_items(survey_code) + [
        alpha("SURVEY_TEAM_LEADER_S_NAME", "Survey Team Leader's Name",   length=50),
        alpha("ENUMERATOR_S_NAME",         "Enumerator's Name",           length=50),
        alpha("FIELD_VALIDATED_BY",        "Field Validated by",          length=50),
        alpha("FIELD_EDITED_BY",           "Field Edited by",             length=50),
        numeric("DATE_FIRST_VISITED",
                f"Date First Visited {date_label_entity} (YYYYMMDD)", length=8),
        numeric("DATE_FINAL_VISIT",
                f"Date of Final Visit to {date_label_entity} (YYYYMMDD)", length=8),
        numeric("TOTAL_NUMBER_OF_VISITS",  "Total Number of Visits",      length=3),
        numeric("ENUM_RESULT_FIRST_VISIT", "Result of First Visit",       length=1,
                value_set_options=ENUM_RESULT_OPTIONS),
        numeric("ENUM_RESULT_FINAL_VISIT", "Result of Final Visit",       length=1,
                value_set_options=ENUM_RESULT_OPTIONS),
        numeric("CONSENT_GIVEN",           "Informed consent given",      length=1,
                value_set_options=YES_NO),
        # §15.E — language used for the interview (captured via getlanguage()
        # at case start; forward-compatible with the #145 language switcher).
        alpha("LANGUAGE_USED",             "Language used for the interview", length=20),
    ]
    if extra_items:
        items.extend(extra_items)
    return record("FIELD_CONTROL", "Field Control", "A", items)


def _gps_fields(prefix=""):
    """Six GPS-metadata items plus a capture-trigger button.

    The trigger item's onfocus handler (wired in the form's .app) calls
    `ReadGPSReading()` from shared/Capture-Helpers.apc and assigns the
    `gps(latitude)`, `gps(longitude)`, etc. results to the metadata items.

    Parameters
    ----------
    prefix : str
        Optional prefix so multiple GPS blocks coexist in one case.
        Examples: prefix="FACILITY_"  → FACILITY_GPS_LATITUDE, ...
                  prefix="P_HOME_"    → P_HOME_GPS_LATITUDE, ...

    Returns
    -------
    list of dict
        [LAT, LON, ALT, ACCURACY, SATELLITES, READTIME, CAPTURE_TRIGGER]
    """
    capture_vs = [("Capture GPS now", "1")]
    return [
        alpha(  f"{prefix}GPS_LATITUDE",   "GPS Latitude",   length=12),
        alpha(  f"{prefix}GPS_LONGITUDE",  "GPS Longitude",  length=12),
        alpha(  f"{prefix}GPS_ALTITUDE",   "GPS Altitude (m)", length=10),
        numeric(f"{prefix}GPS_ACCURACY",   "GPS Accuracy (m)", length=3),
        numeric(f"{prefix}GPS_SATELLITES", "GPS Satellites",   length=2),
        alpha(  f"{prefix}GPS_READTIME",   "GPS Read Time (UTC)", length=19),
        numeric(f"{prefix}CAPTURE_GPS",    "Capture GPS", length=1,
                value_set_options=capture_vs),
    ]


def _photo_block(prefix=""):
    """Verification-photo filename item + capture-trigger button.

    The .app's onfocus handler calls `TakeVerificationPhoto()` from
    shared/Capture-Helpers.apc, which launches the camera, resamples,
    and saves the JPG to tablet storage. The saved filename is assigned
    to the alpha item; CSWeb syncs the file itself via CSEntry's
    attachment mechanism (not as a dictionary binary item — that class
    is flagged experimental in CSPro 8.0 and avoided for MVP).

    Parameters
    ----------
    prefix : str
        Optional prefix. Default "" emits
        VERIFICATION_PHOTO_FILENAME + CAPTURE_VERIFICATION_PHOTO.

    Returns
    -------
    list of dict
        [FILENAME_ALPHA, CAPTURE_TRIGGER]
    """
    capture_vs = [("Take verification photo", "1")]
    return [
        alpha(f"{prefix}VERIFICATION_PHOTO_FILENAME",
              "Verification Photo Filename", length=120),
        numeric(f"{prefix}CAPTURE_VERIFICATION_PHOTO",
                "Take Verification Photo", length=1,
                value_set_options=capture_vs),
    ]


def _psgc_fields(prefix=""):
    """Return the four standard PSGC geographic code items.

    Items are length=10 numeric zero-filled, holding the full 10-digit PSA
    PSGC code. Value sets are deliberately NOT baked in — the four PSGC
    external lookup dictionaries (shared/psgc_*.dcf) + PSGC-Cascade.apc
    logic populate dynamic value sets at runtime via setvalueset().

    A one-entry generic placeholder value set is attached so CSPro Designer
    shows a label in the case tree (per CSPro 8.0 Users Guide p.188 best-
    practice #3 for cascading items).

    Parameters
    ----------
    prefix : str
        Optional prefix to disambiguate when two PSGC blocks live in the
        same record (e.g. facility vs patient-home). Names become
        {prefix}REGION, {prefix}PROVINCE_HUC, etc.

    Returns
    -------
    list of dict
        [REGION, PROVINCE_HUC, CITY_MUNICIPALITY, BARANGAY]
    """
    placeholder = [("(set at runtime)", "0" * 10)]
    return [
        numeric(f"{prefix}REGION",            "Region",               length=10, zero_fill=True, value_set_options=placeholder),
        numeric(f"{prefix}PROVINCE_HUC",      "Province / HUC",       length=10, zero_fill=True, value_set_options=placeholder),
        numeric(f"{prefix}CITY_MUNICIPALITY", "City / Municipality",  length=10, zero_fill=True, value_set_options=placeholder),
        numeric(f"{prefix}BARANGAY",          "Barangay",             length=10, zero_fill=True, value_set_options=placeholder),
    ]


def build_geo_id(mode, extra_items=None):
    """Build a geographic identification record.

    Parameters
    ----------
    mode : str
        One of:
        - "facility"             — CLASSIFICATION + PSGC + latitude/longitude.
                                   Record name: HEALTH_FACILITY_AND_GEOGRAPHIC_IDENTIFICATION
        - "facility_and_patient" — CLASSIFICATION + PSGC + facility name/address
                                   + patient home PSGC (P_ prefix).
                                   Record name: PATIENT_GEO_ID
        - "household"            — CLASSIFICATION + PSGC + HH_ADDRESS.
                                   Record name: HOUSEHOLD_GEO_ID
    extra_items : list, optional
        Additional item dicts appended after the mode-specific block.

    Returns
    -------
    dict
        A CSPro record dict (use directly in the records list of build_dictionary).
    """
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
        if extra_items:
            items.extend(extra_items)
        return record(
            "HEALTH_FACILITY_AND_GEOGRAPHIC_IDENTIFICATION",
            "Health Facility and Geographic Identification",
            "B", items,
        )

    elif mode == "facility_and_patient":
        patient_psgc = _psgc_fields(prefix="P_")
        for it in patient_psgc:
            it["labels"][0]["text"] = "Patient Home " + it["labels"][0]["text"]
        items = (
            [classification_item]
            + _psgc_fields()
            + [
                alpha("FACILITY_NAME",    "Facility Name",    length=100),
                alpha("FACILITY_ADDRESS", "Facility Address", length=200),
            ]
            + patient_psgc
        )
        if extra_items:
            items.extend(extra_items)
        return record("PATIENT_GEO_ID", "Patient Geographic Identification", "B", items)

    elif mode == "household":
        items = (
            [classification_item]
            + _psgc_fields()
            + [
                alpha("HH_ADDRESS", "Household Address", length=200),
            ]
        )
        if extra_items:
            items.extend(extra_items)
        return record("HOUSEHOLD_GEO_ID", "Household Geographic Identification", "B", items)

    else:
        raise ValueError(
            f"build_geo_id: unknown mode {mode!r}. "
            "Expected 'facility', 'facility_and_patient', or 'household'."
        )


# ============================================================
# 4. DICTIONARY ASSEMBLY
# ============================================================

def build_id_block():
    """12-digit decomposed case key (RR-PP-MMM-FF-CCC) — adopted Questionnaire
    Numbering Convention (2026-05-05), replacing the legacy single 6-digit
    QUESTIONNAIRE_NO. First 7 digits are the within-parent PSA PSGC codes, then
    a 2-digit facility number and a 3-digit per-facility / per-instrument case
    sequence. Five contiguous numeric ID items starting at position 2 (position
    1 is the recordType byte)."""
    specs = [
        ("REGION_CODE",            "Region Code (PSGC)",                           2),
        ("PROVINCE_HUC_CODE",      "Province / HUC Code (PSGC)",                   2),
        ("CITY_MUNICIPALITY_CODE", "City / Municipality Code (PSGC)",              3),
        ("FACILITY_NO",            "Facility Number (within municipality)",        2),
        ("CASE_SEQ",               "Case Sequence (per-facility, per-instrument)", 3),
    ]
    items, start = [], 2
    for name, label, length in specs:
        items.append({
            "name": name,
            "labels": [{"text": label}],
            "contentType": "numeric",
            "start": start,
            "length": length,
            "zeroFill": True,
        })
        start += length
    return items


def build_dictionary(dict_name, dict_label, records=None,
                     id_items=None, id_item_name=None, id_item_label=None,
                     id_length=None):
    """Assemble a complete CSPro 8.0 dictionary JSON structure.

    Parameters
    ----------
    dict_name : str
        Dictionary name (UPPER_SNAKE, e.g. "FACILITYHEADSURVEY_DICT").
    dict_label : str
        Human-readable dictionary label (e.g. "FacilityHeadSurvey").
    id_item_name : str
        Name of the level ID item (e.g. "QUESTIONNAIRE_NO").
    id_item_label : str
        Label for the level ID item (e.g. "Questionnaire No").
    id_length : int
        Numeric length of the level ID item (zero-filled, starts at position 2).
    records : list of dict
        List of record dicts produced by record() / build_field_control() /
        build_geo_id() / etc.

    Returns
    -------
    dict
        Full CSPro 8.0 dictionary object suitable for json.dumps.
    """
    level_name  = dict_name.replace("_DICT", "_LEVEL")
    level_label = dict_label + " Level"

    # Backward-compat: synthesize the single-item key from legacy params when
    # no decomposed id_items block is supplied.
    if id_items is None:
        id_items = [{
            "name":        id_item_name,
            "labels":      [{"text": id_item_label}],
            "contentType": "numeric",
            "start":       2,
            "length":      id_length,
            "zeroFill":    True,
        }]

    return {
        "software":          "CSPro",
        "version":           8.0,
        "fileType":          "dictionary",
        "name":              dict_name,
        "labels":            [{"text": dict_label}],
        "readOptimization":  True,
        "recordType":        {"start": 1, "length": 1},
        "defaults":          {"decimalMark": True, "zeroFill": False},
        "relativePositions": True,
        "levels": [
            {
                "name":   level_name,
                "labels": [{"text": level_label}],
                "ids": {"items": id_items},
                "records": records,
            }
        ],
    }


CSPRO_LABEL_MAX = 255  # CSPro hard limit on any label (item/value/value-set/record).


def _truncate_long_labels(node, max_len=CSPRO_LABEL_MAX):
    """Recursively cap every labels[].text at CSPro's max_len, truncating at a word
    boundary + '...'. CSPro rejects a dictionary outright if any label exceeds 255
    chars; long verbatim option/category descriptions from the questionnaire trip this.
    Returns the count truncated. The full text remains in the questionnaire source."""
    n = 0
    if isinstance(node, dict):
        labs = node.get("labels")
        if isinstance(labs, list):
            for lab in labs:
                t = lab.get("text")
                if isinstance(t, str) and len(t) > max_len:
                    cut = t[:max_len - 3]
                    sp = cut.rfind(" ")
                    if sp > max_len * 0.6:
                        cut = cut[:sp]
                    lab["text"] = cut.rstrip(" ,;:-") + "..."
                    n += 1
        for k, v in node.items():
            n += _truncate_long_labels(v, max_len)
    elif isinstance(node, list):
        for x in node:
            n += _truncate_long_labels(x, max_len)
    return n


def write_dcf(dictionary, out_path):
    """Write a CSPro dictionary to a .dcf file and print diagnostics.

    Parameters
    ----------
    dictionary : dict
        Full dictionary object returned by build_dictionary().
    out_path : str or Path
        Destination file path (will be created or overwritten).

    Diagnostics printed to stdout:
        Wrote <path>
          Records: <n>
          Items:   <n>  (sum across all records)
    """
    out_path = Path(out_path)
    n_truncated = _truncate_long_labels(dictionary)
    if n_truncated:
        print(f"  Capped {n_truncated} label(s) at {CSPRO_LABEL_MAX} chars (CSPro max)")
    out_path.write_text(json.dumps(dictionary, indent=2), encoding="utf-8")

    record_list = dictionary["levels"][0]["records"]
    record_count = len(record_list)
    item_count   = sum(len(r["items"]) for r in record_list)

    print(f"Wrote {out_path}")
    print(f"  Records: {record_count}")
    print(f"  Items:   {item_count}")


# ============================================================
# 5. MULTI-LANGUAGE POST-PROCESSING
# ============================================================

# Active languages are discovered at generate time: a language is included only
# if its translations/<file>.json exists. EN is the source (label text as
# authored). To add Filipino once ASPSI delivers it, drop `translations/fil.json`
# next to the generator and re-run — no code change.
TRANSLATION_LANGUAGES = [
    ("EN",  "English",    None),
    ("FIL", "Filipino",   "fil.json"),
    ("BCL", "Bikol",      "bcl.json"),
    ("BIS", "Bisaya",     "bis.json"),
    ("CEB", "Cebuano",    "ceb.json"),
    ("WAR", "Waray",      "war.json"),
    ("HIL", "Hiligaynon", "hil.json"),
]


def apply_translations(dictionary, translations_dir, languages=TRANSLATION_LANGUAGES):
    """Expand a single-language dictionary into a multi-language CSPro 8.0 dictionary.

    Walks every `labels` list and replaces its single English entry with one
    `{text, language}` entry per ACTIVE language. Translations are pulled from
    `translations_dir/<file>.json`, keyed by the English label text; any key
    missing from a map falls back to English. A language is active only if its
    map file exists (EN is always active and first), so new locales are drop-in.
    Mutates and returns `dictionary`; prints a per-language coverage summary.
    """
    translations_dir = Path(translations_dir)
    active, maps, skipped = [], {}, []
    for code, disp, fname in languages:
        if fname is None:
            active.append((code, disp))
        elif (translations_dir / fname).exists():
            maps[code] = json.loads((translations_dir / fname).read_text(encoding="utf-8"))
            active.append((code, disp))
        else:
            skipped.append(code)

    dictionary["languages"] = [{"name": c, "label": d} for c, d in active]
    counts = {c: [0, 0] for c in maps}   # code -> [matched, total]

    def expand(node):
        if isinstance(node, dict):
            labs = node.get("labels")
            if isinstance(labs, list) and labs and isinstance(labs[0], dict) and "text" in labs[0]:
                en_text = labs[0]["text"]
                new_labels = []
                for code, _disp in active:
                    if code in maps:
                        counts[code][1] += 1
                        tr = maps[code].get(en_text)
                        if tr is not None:
                            counts[code][0] += 1
                        else:
                            tr = en_text
                        new_labels.append({"text": tr, "language": code})
                    else:
                        new_labels.append({"text": en_text, "language": code})
                node["labels"] = new_labels
            for k, v in node.items():
                if k != "labels":
                    expand(v)
        elif isinstance(node, list):
            for it in node:
                expand(it)

    expand(dictionary)

    print(f"  Languages: {', '.join(c for c, _ in active)}"
          + (f"   (no map, skipped: {', '.join(skipped)})" if skipped else ""))
    for code in maps:
        matched, total = counts[code]
        pct = (100 * matched // total) if total else 0
        print(f"    {code}: {matched}/{total} labels translated ({pct}%)")
    return dictionary


# ---------------------------------------------------------------------------
# 'Other (specify)' enforcement — auto-derived from the dictionary
# ---------------------------------------------------------------------------
# An "Other (specify)" option that has a free-text companion item must require
# that text when the option is chosen. Two layouts occur in F3/F4:
#   * single-choice — a coded parent field <BASE> with an "Other (specify)" value
#     and a companion <BASE>_OTHER_TXT  -> require text when <BASE> = <other code>
#   * select-all    — option-flag fields <BASE>_O01.._Onn (each 1=Yes/2=No) with a
#     companion <BASE>_OTHER_TXT; one flag is the "Other (Specify)" option
#     -> require text when that flag = 1
# UHC9 dual-other (<BASE>_YES_OTHER_TXT / _NO_OTHER_TXT) is handled separately by
# the per-instrument uhc9_other_specify_procs(); we skip those here.
# Items whose trigger can't be resolved from the dictionary (e.g. a bare _SPECIFY
# conditional with no coded parent and no Other option flag) are returned in
# `skipped` for manual handling rather than guessed wrong.

_OTHER_LABEL_RE = re.compile(r"specif|\bothers?\b", re.IGNORECASE)


def _label_text(node):
    labs = node.get("labels") or [{}]
    return labs[0].get("text", "") or ""


def _other_value_code(item):
    """The 'Other (specify)' value code of a coded item, or None."""
    for vs in item.get("valueSets") or []:
        for val in vs.get("values") or []:
            if _OTHER_LABEL_RE.search(_label_text(val)):
                pairs = val.get("pairs") or [{}]
                code = pairs[0].get("value")
                if code is not None:
                    return code
    return None


def other_specify_procs(items):
    """Build 'Other (specify)' enforcement PROCs from a dcf items map
    ({name: item_dict}). Returns (procs: {field: proc_text}, mapping: [(txt,
    trigger_desc)], skipped: [names]). See module note above for the patterns."""
    procs, mapping, skipped = {}, [], []
    txt_items = sorted(
        n for n in items
        if (n.endswith("_OTHER_TXT") or n.endswith("_SPECIFY"))
        and not (n.endswith("_YES_OTHER_TXT") or n.endswith("_NO_OTHER_TXT"))
    )
    for n in txt_items:
        base = n[: -len("_OTHER_TXT")] if n.endswith("_OTHER_TXT") else n[: -len("_SPECIFY")]

        # (1) single-choice coded parent carrying an 'Other (specify)' value.
        #     Parent is usually <base>, sometimes <base>_TYPE, or a uniquely-named
        #     descriptive sibling <base>_SOURCE / _CATEGORY / etc. We only accept a
        #     descendant when it is the SOLE <base>_… coded field that actually has
        #     an 'Other' value (so panels / unrelated coded fields can't mis-match).
        cands = [base, base + "_TYPE"]
        desc = [k for k in sorted(items)
                if k.startswith(base + "_") and items[k].get("valueSets")
                and not re.search(r"_O?\d+$", k)
                and _other_value_code(items[k]) is not None]
        if len(desc) == 1:
            cands.append(desc[0])
        parent_name = code = None
        for cand in cands:
            it = items.get(cand)
            if it and it.get("valueSets"):
                c = _other_value_code(it)
                if c is not None:
                    parent_name, code = cand, c
                    break
        if parent_name is not None:
            lit = int(code) if str(code).lstrip("-").isdigit() else f'"{code}"'
            procs[n] = (
                f"PROC {n}\npostproc\n"
                f"  if {parent_name} = {lit} and length(strip({n})) = 0 then\n"
                f"    errmsg(\"'Other' was selected for {parent_name} but no text was entered. Please specify.\");\n"
                f"    reenter;\n  endif;"
            )
            mapping.append((n, f"single: {parent_name} = {lit}"))
            continue

        # (2) select-all option flags — <base>_O01.. (with 'O') or <base>_01..
        #     (without) — pick the flag whose label is the 'Other (Specify)' one.
        #     The label gate means panels with no 'Other' option stay unmatched.
        flag_re = re.compile(re.escape(base) + r"_O?\d+$")
        other_flag = next(
            (k for k in sorted(items)
             if flag_re.match(k) and _OTHER_LABEL_RE.search(_label_text(items[k]))),
            None,
        )
        if other_flag is not None:
            procs[n] = (
                f"PROC {n}\npostproc\n"
                f"  if {other_flag} = 1 and length(strip({n})) = 0 then\n"
                f"    errmsg(\"'Other (specify)' was selected for {base} but no text was entered. Please specify.\");\n"
                f"    reenter;\n  endif;"
            )
            mapping.append((n, f"select-all: {other_flag} = 1"))
            continue

        # (3) unresolved -> manual
        skipped.append(n)
    return procs, mapping, skipped
