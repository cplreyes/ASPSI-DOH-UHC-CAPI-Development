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
# 4. CASE-ID BLOCK — adopted 12-digit decomposed scheme
# ============================================================
#
# 5-item case identifier per the Questionnaire Numbering Convention
# (wiki/concepts/Questionnaire Numbering Convention.md, adopted 2026-05-05).
# Total width 12 digits, anchored to PSA 1Q 2026 PSGC.
#
#   RR  PP  MMM  FF  CCC
#   ^^  ^^  ^^^  ^^  ^^^
#   |   |   |    |   |__ Per-facility per-instrument case sequence
#   |   |   |    |______ ASPSI sampling-frame facility index in municipality
#   |   |   |___________ PSGC city/municipality slot (positions 5-7)
#   |   |_______________ PSGC province/HUC slot     (positions 3-4)
#   |___________________ PSGC region               (positions 1-2)
#
# All five items are non-NA — they are required identifying keys, not data
# fields, so the project-wide NA-at-highest-value convention (9/99/999) does
# not apply. Range bounds below match the concept page.

# Column positions in the data file. Record-type occupies column 1; case-ID
# block starts at column 2 and runs through column 13. Downstream records
# begin at column 14 (handled per-record by CSPro Designer based on the
# record's items, not pinned here).
_CASE_ID_START_COLUMN = 2

# Replacement-protocol partitioning of the CASE_SEQ range (per the concept
# page). Encoded as a constant so F1/F3/F4 PROC code and the F2 PWA case-ID
# issuer can reference the same numeric boundaries without duplicating magic
# numbers.
CASE_SEQ_ACTIVE_RANGE      = (1,   699)   # STL-allocated across enumerators
CASE_SEQ_REPLACEMENT_RANGE = (700, 899)   # Annex D replacement protocol
CASE_SEQ_REFUSED_RANGE     = (900, 999)   # Refused / forfeited (no data)


def build_id_block():
    """Return the 5-item case-ID block adopted under the 12-digit
    decomposed numbering scheme.

    The returned list slots into ``build_dictionary(id_items=...)`` for any
    F-series instrument. ``CASE_SEQ`` is scoped per-instrument per-facility,
    so F1 case 001 and F3 case 001 at the same facility do not collide —
    the dictionaries are separate. Cross-instrument linkage at the same
    facility falls out of the shared ``REGION_CODE + PROVINCE_HUC_CODE +
    CITY_MUNICIPALITY_CODE + FACILITY_NO`` prefix.

    Item attributes
    ---------------
    - All numeric, zero-fill, decimal=0 (no decimals).
    - Start positions are explicit (cols 2-3, 4-5, 6-8, 9-10, 11-13)
      because CSPro 8.0 requires absolute positions for ID items even
      when ``relativePositions: True`` is set at the dictionary level
      (that flag governs record items, not ID items).

    Returns
    -------
    list of dict
        Five item dicts in case-ID order: REGION_CODE, PROVINCE_HUC_CODE,
        CITY_MUNICIPALITY_CODE, FACILITY_NO, CASE_SEQ.
    """
    spec = [
        ("REGION_CODE",            "Region Code",            2),
        ("PROVINCE_HUC_CODE",      "Province / HUC Code",    2),
        ("CITY_MUNICIPALITY_CODE", "City / Municipality Code", 3),
        ("FACILITY_NO",            "Facility No",            2),
        ("CASE_SEQ",               "Case Sequence",          3),
    ]
    items = []
    col = _CASE_ID_START_COLUMN
    for name, label, length in spec:
        items.append({
            "name":        name,
            "labels":      [{"text": label}],
            "contentType": "numeric",
            "start":       col,
            "length":      length,
            "zeroFill":    True,
            "decimal":     0,
            "decimalChar": False,
        })
        col += length
    return items


def build_listing_id_block():
    """Return the 6-item listing-session ID block for the 110_F3_listing
    CSPro app.

    Distinct from the F-series 12-digit case-ID. A listing session is one
    facility-day; the case-ID block encodes facility (RR+PP+MMM+FF) plus
    the session date and a per-facility-day session sequence.

    Block layout (20 digits total starting at column 2):

        RR  PP  MMM  FF  YYYYMMDD  SSS
        ^^  ^^  ^^^  ^^  ^^^^^^^^  ^^^
        |   |   |    |       |     |__ LISTING_SESSION_SEQ
        |   |   |    |       |________ Date of listing session
        |   |   |    |________________ ASPSI facility index
        |   |   |_____________________ PSGC city/municipality slot
        |   |_________________________ PSGC province/HUC slot
        |_____________________________ PSGC region

    LISTING_SESSION_SEQ resets to 1 per facility-day; a second listing
    session at the same facility on the same date (e.g., AM vs PM crew)
    becomes session 2. The reset is enforced in the 101_login menu app
    when the operator starts a new session.

    Returns
    -------
    list of dict
        Six item dicts in session-ID order: REGION_CODE,
        PROVINCE_HUC_CODE, CITY_MUNICIPALITY_CODE, FACILITY_NO,
        LISTING_SESSION_DATE, LISTING_SESSION_SEQ.
    """
    spec = [
        ("REGION_CODE",            "Region Code",                      2),
        ("PROVINCE_HUC_CODE",      "Province / HUC Code",              2),
        ("CITY_MUNICIPALITY_CODE", "City / Municipality Code",         3),
        ("FACILITY_NO",            "Facility No",                      2),
        ("LISTING_SESSION_DATE",   "Listing Session Date (YYYYMMDD)",  8),
        ("LISTING_SESSION_SEQ",    "Listing Session Sequence (per facility-day)", 3),
    ]
    items = []
    col = _CASE_ID_START_COLUMN
    for name, label, length in spec:
        items.append({
            "name":        name,
            "labels":      [{"text": label}],
            "contentType": "numeric",
            "start":       col,
            "length":      length,
            "zeroFill":    True,
            "decimal":     0,
            "decimalChar": False,
        })
        col += length
    return items


# ============================================================
# 5. DICTIONARY ASSEMBLY
# ============================================================

def build_dictionary(dict_name, dict_label,
                     id_item_name=None, id_item_label=None, id_length=None,
                     records=None, id_items=None):
    """Assemble a complete CSPro 8.0 dictionary JSON structure.

    Two ID-item shapes are supported:

      - **New (preferred)**: pass ``id_items=`` as a fully-formed list of
        item dicts. Use ``build_id_block()`` for the adopted 5-item
        12-digit case ID. The keyword exists so F3/F4/PLF can adopt the
        same block without code duplication.

      - **Legacy single-item**: pass ``id_item_name``, ``id_item_label``,
        and ``id_length``. The dictionary is built with one zero-filled
        numeric ID item starting at column 2. Retained for backwards
        compatibility with any caller that has not yet migrated; new code
        should use ``id_items=``.

    Parameters
    ----------
    dict_name : str
        Dictionary name (UPPER_SNAKE, e.g. "FACILITYHEADSURVEY_DICT").
    dict_label : str
        Human-readable dictionary label (e.g. "FacilityHeadSurvey").
    id_item_name, id_item_label, id_length
        Legacy single-ID-item parameters. Mutually exclusive with ``id_items``.
    records : list of dict
        List of record dicts produced by record() / build_field_control() /
        build_geo_id() / etc.
    id_items : list of dict, optional
        New-shape ID-item block. Mutually exclusive with the three legacy
        parameters. Each dict must include name, labels, contentType,
        start, length, zeroFill.

    Returns
    -------
    dict
        Full CSPro 8.0 dictionary object suitable for json.dumps.
    """
    if records is None:
        records = []

    if id_items is not None:
        if id_item_name is not None or id_item_label is not None or id_length is not None:
            raise ValueError(
                "build_dictionary: pass either id_items= OR the legacy "
                "(id_item_name, id_item_label, id_length) triple, not both."
            )
        ids_items_block = id_items
    else:
        if id_item_name is None or id_item_label is None or id_length is None:
            raise ValueError(
                "build_dictionary: must pass id_items= or all of "
                "(id_item_name, id_item_label, id_length)."
            )
        ids_items_block = [{
            "name":        id_item_name,
            "labels":      [{"text": id_item_label}],
            "contentType": "numeric",
            "start":       2,
            "length":      id_length,
            "zeroFill":    True,
        }]

    level_name  = dict_name.replace("_DICT", "_LEVEL")
    level_label = dict_label + " Level"

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
                "ids": {
                    "items": ids_items_block,
                },
                "records": records,
            }
        ],
    }


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
    out_path.write_text(json.dumps(dictionary, indent=2), encoding="utf-8")

    record_list = dictionary["levels"][0]["records"]
    record_count = len(record_list)
    item_count   = sum(len(r["items"]) for r in record_list)

    print(f"Wrote {out_path}")
    print(f"  Records: {record_count}")
    print(f"  Items:   {item_count}")
