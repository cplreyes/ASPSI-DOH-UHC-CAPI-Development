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

# Result-of-visit disposition codes. Per-instrument — transcribed from the
# paper FIELD CONTROL block (2026-06-12). The consent/refusal outcome is now
# captured HERE (no separate "Informed consent given" field): F1 = "Refused";
# F3/F4 = "Withdraw Participation/Consent".
ENUM_RESULT_OPTIONS_F1 = [          # F1 Facility Head
    ("Completed",  "1"),
    ("Postponed",  "2"),
    ("Refused",    "3"),
    ("Incomplete", "4"),
]
ENUM_RESULT_OPTIONS_F3 = [          # F3 Patient
    ("Completed",                       "1"),
    ("Completed at the Hospital",       "2"),
    ("Postponed",                       "3"),
    ("Incomplete",                      "4"),
    ("Completed at Home",               "5"),
    ("Withdraw Participation/Consent",  "6"),
]
ENUM_RESULT_OPTIONS_F4 = [          # F4 Household
    ("Completed",                       "1"),
    ("Postponed",                       "2"),
    ("Incomplete",                      "3"),
    ("Withdraw Participation/Consent",  "4"),
]
ENUM_RESULT_OPTIONS = ENUM_RESULT_OPTIONS_F1   # default / back-compat

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


def image(name, label):
    """Binary Image dictionary item (CSPro 8.0 'Image' data type).

    Captured in logic via ITEM.takePhoto() + ITEM.resample(); the JPG BYTES are
    stored INSIDE the case, so they travel with the case during synchronization
    and are downloadable from CSWeb (Data tab -> PFF -> Data Viewer thumbnail).
    This is the supported path: loose Image.save("file.jpg") files are NOT synced
    by CSWeb (case sync moves record items, not app-folder files) — the reason
    R4 #713 saw "no picture retained by the system."

    Binary items carry no fixed-width length/position (they are stored out of the
    record) and CANNOT be placed on a form — drive capture from an on-form trigger
    field's logic, and EXCLUDE this item from the .fmf form-field list.
    """
    return {
        "name": name,
        "labels": [{"text": label}],
        "contentType": "image",
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


def checkbox_multiselect(prefix, label, options, with_other_txt=None):
    """TRUE CSPro 'Check Box' multi-select: ONE alpha field holding the ticked option
    codes concatenated left-to-right (CSEntry's Check Box capture writes each fixed-width
    code into the field as a box is checked). Renders as a single question + a tick-list
    on one screen (tick all that apply) — unlike select_all() which emits one Yes/No item
    per option (N individual radios). length = (#options) * (code width). Codes MUST be
    fixed width (CSPro slices the field by code width). The CheckBox capture type itself is
    applied by name in generate_fmf / optimize_capture_types. Returns [checkbox field]
    (+ an OTHER_TXT alpha when a 'specify' option is present)."""
    code_w = max(len(c) for _, c in options)
    item = {
        "name": prefix,
        "labels": [{"text": label}],
        "contentType": "alpha",
        "length": len(options) * code_w,
        "valueSets": [_value_set(prefix, label, options)],
    }
    items = [item]
    if with_other_txt is None:
        with_other_txt = bool(options) and "specify" in options[-1][0].lower()
    if with_other_txt:
        items.append(alpha(f"{prefix}_OTHER_TXT",
                           f"{label} — Other (specify) text", length=120))
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
    """Case-start operational metadata — NOW EMPTY (returns []).

    Per Carl 2026-06-12, the FIELD CONTROL section of each instrument should
    match the paper questionnaire exactly: just the team-leader/enumerator
    names, validated/edited-by, visit dates, result dispositions, and total
    visits. Everything previously prepended here was "unnecessary input data":
      - SURVEY_CODE        — the installed questionnaire identifies the instrument
      - INTERVIEWER_ID     — not in the paper FC (Enumerator's Name covers it)
      - DATE_STARTED /
        TIME_STARTED       — not in the paper FC (Date First/Final Visited covers it)
      - AAPOR_DISPOSITION  — not in the paper FC (Result-of-Visit codes cover it)
    Interview language is still recorded (LANGUAGE_USED, auto-set from
    getlanguage() in the QUESTIONNAIRE_NUMBER postproc — off-form, not input).

    `survey_code` retained for caller compatibility; emits nothing.
    """
    return []


def build_field_control(survey_code, extra_items=None, date_label_entity="the Facility",
                        result_options=None):
    """Build a FIELD_CONTROL record (record type "A").

    Parameters
    ----------
    survey_code : str
        Instrument code ("F1", "F3", "F4"). No longer emits a SURVEY_CODE
        item (removed 2026-06-12 — the per-instrument dictionary already
        identifies the instrument); retained for caller compatibility.
    extra_items : list, optional
        Additional item dicts to append after the standard block.
        Use this when a survey needs fields not present in the base template.
    date_label_entity : str, optional
        Human-readable entity name used in the date-field labels.
        Defaults to "the Facility" (matching F1 semantics).
        Pass "the Patient" for F3, "the Household" for F4, etc.

    Standard items (in order) — matches the paper FIELD CONTROL block:
        SURVEY_TEAM_LEADER_S_NAME, ENUMERATOR_S_NAME, FIELD_VALIDATED_BY,
        FIELD_EDITED_BY, DATE_FIRST_VISITED (length 8), DATE_FINAL_VISIT (length 8),
        TOTAL_NUMBER_OF_VISITS, ENUM_RESULT_FIRST_VISIT, ENUM_RESULT_FINAL_VISIT.
    Plus LANGUAGE_USED (off-form metadata, auto-set from getlanguage()).
    CONSENT_GIVEN was removed 2026-06-12 — consent outcome is now the Result
    disposition (Refused / Withdraw Participation/Consent), and the read-aloud
    consent script is off the CAPI (read from the printed sheet).

    result_options : list, optional
        Per-instrument Result-of-Visit value set. Defaults to the F1 codes.
    """
    results = result_options or ENUM_RESULT_OPTIONS
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
                value_set_options=results),
        numeric("ENUM_RESULT_FINAL_VISIT", "Result of Final Visit",       length=1,
                value_set_options=results),
        # §15.E — language used for the interview (captured via getlanguage()
        # in the QUESTIONNAIRE_NUMBER postproc; off-form, not enumerator input).
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
    # GPS is AUTO-FETCHED on focus now (2026-06-12) — no manual "Capture GPS"
    # trigger button. The coordinate + metadata fields are auto-populated and
    # protected (read-only) by the <prefix>GPS_LATITUDE onfocus PROC in the .apc.
    return [
        alpha(  f"{prefix}GPS_LATITUDE",   "GPS Latitude",   length=12),
        alpha(  f"{prefix}GPS_LONGITUDE",  "GPS Longitude",  length=12),
        alpha(  f"{prefix}GPS_ALTITUDE",   "GPS Altitude (m)", length=10),
        numeric(f"{prefix}GPS_ACCURACY",   "GPS Accuracy (m)", length=3),
        numeric(f"{prefix}GPS_SATELLITES", "GPS Satellites",   length=2),
        alpha(  f"{prefix}GPS_READTIME",   "GPS Read Time (UTC)", length=19),
    ]


def _photo_block(prefix=""):
    """Verification-photo capture block: binary Image item + filename label + trigger.

    The on-form trigger field (CAPTURE_VERIFICATION_PHOTO) drives capture from its
    onfocus handler via `TakeVerificationPhoto()` (shared/Capture-Helpers.apc), which
    launches the camera, resamples, and stores the JPG BYTES into the binary Image
    item VERIFICATION_PHOTO_IMAGE. Because the bytes live inside the case, they sync
    to CSWeb and are downloadable there (Data Viewer thumbnail).

    R4 #713 root cause: the previous design saved the photo to a LOOSE FILE on the
    tablet and stored only the filename string — loose files are not synced by CSWeb,
    so the image never reached the server. The binary Image item fixes that.

    Item roles:
    - VERIFICATION_PHOTO_IMAGE   binary Image, OFF-FORM (binary items can't be on a
                                 form) — holds the actual photo, syncs to CSWeb.
    - VERIFICATION_PHOTO_FILENAME alpha — human-readable label + the "already captured"
                                 sentinel the trigger's onfocus guards on.
    - CAPTURE_VERIFICATION_PHOTO  on-form numeric trigger whose onfocus fires capture.

    NB: the .fmf form-field list MUST exclude VERIFICATION_PHOTO_IMAGE (F3/F4
    generate_fmf use a {"exclude": [...]} spec; F1's static .fmf never references it),
    and verify_questions treats it as a KNOWN_OFFFORM item.

    Parameters
    ----------
    prefix : str
        Optional prefix. Default "" emits VERIFICATION_PHOTO_IMAGE +
        VERIFICATION_PHOTO_FILENAME + CAPTURE_VERIFICATION_PHOTO.

    Returns
    -------
    list of dict
        [IMAGE_BINARY, FILENAME_ALPHA, CAPTURE_TRIGGER]
    """
    capture_vs = [("Take verification photo", "1")]
    return [
        image(f"{prefix}VERIFICATION_PHOTO_IMAGE",
              "Verification Photo (binary; syncs to CSWeb)"),
        alpha(f"{prefix}VERIFICATION_PHOTO_FILENAME",
              "Verification Photo Filename", length=120),
        numeric(f"{prefix}CAPTURE_VERIFICATION_PHOTO",
                "Take Verification Photo", length=1,
                value_set_options=capture_vs),
    ]


def _psgc_fields(prefix="", facility_derived=False):
    """Return PSGC geographic code items.

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
    facility_derived : bool
        Single-number redesign (2026-06-10): when True the facility geo
        region/province/city are DERIVED from QUESTIONNAIRE_NUMBER (shown
        read-only as REGION_NAME/PROVINCE_NAME/CITY_NAME in FIELD_CONTROL),
        so only the BARANGAY picker is captured here (barangay isn't in the
        12-digit code). Default False keeps the full manual cascade — used by
        the F3 patient-home (P_) block, which is a separate location.

    Returns
    -------
    list of dict
        [BARANGAY] when facility_derived else [REGION, PROVINCE_HUC, CITY_MUNICIPALITY, BARANGAY]
    """
    placeholder = [("(set at runtime)", "0" * 10)]
    barangay = numeric(f"{prefix}BARANGAY", "Barangay", length=10, zero_fill=True, value_set_options=placeholder)
    if facility_derived:
        return [barangay]
    return [
        numeric(f"{prefix}REGION",            "Region",               length=10, zero_fill=True, value_set_options=placeholder),
        numeric(f"{prefix}PROVINCE_HUC",      "Province / HUC",       length=10, zero_fill=True, value_set_options=placeholder),
        numeric(f"{prefix}CITY_MUNICIPALITY", "City / Municipality",  length=10, zero_fill=True, value_set_options=placeholder),
        barangay,
    ]


def _facility_name_address(structured=False):
    """Facility name + address items.

    structured=False — the legacy single free-text address (one blob).
    structured=True (#784/#786, Option A) — a typed STREET line + two read-only
    derived fields: BARANGAY_NAME (from the BARANGAY picker) and the assembled
    FACILITY_ADDRESS ("Street, Barangay, Municipality"). The derive + assembly +
    protect() live in shared/PSGC-Cascade.apc PROC BARANGAY; CITY_NAME
    (municipality) is already populated there, so nothing is re-typed.
    """
    name = alpha("FACILITY_NAME", "Facility Name", length=100)
    if not structured:
        return [name, alpha("FACILITY_ADDRESS", "Facility Address", length=200)]
    return [
        name,
        alpha("FACILITY_STREET",  "Facility Address — Street Name / No.",            length=120),
        alpha("BARANGAY_NAME",    "Barangay (from PSGC)",                            length=80),
        alpha("FACILITY_ADDRESS", "Facility Address (Street, Barangay, Municipality)", length=200),
    ]


def build_geo_id(mode, extra_items=None, facility_derived=False, structured_address=False):
    """Build a geographic identification record.

    structured_address (#784/#786, Option A, 2026-06-25): when True the facility
    address is captured as a typed STREET line plus a read-only assembled
    FACILITY_ADDRESS ("Street, Barangay, Municipality"). Barangay + Municipality
    are NOT re-typed — BARANGAY_NAME is derived from the BARANGAY picker and
    CITY_NAME (municipality) already comes from the PSGC cascade in FIELD_CONTROL
    (shared/PSGC-Cascade.apc owns the lookup + the assembly). Only the FACILITY
    branches honour it; "household" is unaffected.

    facility_derived (2026-06-10 single-number redesign): when True the FACILITY
    PSGC region/province/city are derived from QUESTIONNAIRE_NUMBER and only the
    barangay picker is captured here. The F3 patient-home (P_) block is never
    affected — it stays a full manual cascade.

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
        # LATITUDE/LONGITUDE removed here 2026-06-12 — they were redundant
        # typed fields; F1's canonical GPS is the auto-fetched FACILITY_GPS_*
        # block (REC_FACILITY_CAPTURE), so no manual coordinates on the geo form.
        items = (
            [classification_item]
            + _psgc_fields(facility_derived=facility_derived)
            + _facility_name_address(structured_address)
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
            + _psgc_fields(facility_derived=facility_derived)
            + _facility_name_address(structured_address)
            + patient_psgc
        )
        if extra_items:
            items.extend(extra_items)
        return record("PATIENT_GEO_ID", "Patient Geographic Identification", "B", items)

    elif mode == "household":
        items = (
            [classification_item]
            + _psgc_fields(facility_derived=facility_derived)
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

def build_id_block(single_questionnaire_number=False):
    """Case key for the level-1 ID block.

    `single_questionnaire_number=False` (legacy, default): five contiguous numeric
    ID items (RR-PP-MMM-FF-CCC) per the 2026-05-05 Questionnaire Numbering
    Convention. Kept default so un-migrated instruments regenerate unchanged.

    `single_questionnaire_number=True` (redesign 2026-06-10, Carl): ONE 12-digit
    `QUESTIONNAIRE_NUMBER` id item. The enumerator types one number; the component
    codes are DERIVED from it in logic and live as non-id FIELD_CONTROL items (see
    `derived_geo_code_items()`), so every existing PROC reference to REGION_CODE
    etc. keeps working. Spec:
    deliverables/CSPro/2026-06-10-single-questionnaire-number-redesign.md.
    NB: only flip this WITH the matching .apc (QUESTIONNAIRE_NUMBER postproc) and
    .fmf (one-field key form) in the same regen, or the build breaks."""
    if single_questionnaire_number:
        return [{
            "name": "QUESTIONNAIRE_NUMBER",
            "labels": [{"text": "Questionnaire Number (12-digit: RR-PP-MMM-FF-CCC)"}],
            "contentType": "numeric",
            "start": 2,
            "length": 12,
            "zeroFill": True,
        }]
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


def derived_geo_code_items():
    """Component PSGC codes + read-only PSGC names, parsed from QUESTIONNAIRE_NUMBER
    at case start and stored as non-id FIELD_CONTROL items (single-number redesign,
    2026-06-10). The codes reuse the exact legacy id names so existing PROC refs
    (photo filename, skip gates) resolve unchanged; the names are filled read-only
    from the PSGC external dicts for on-screen confirmation."""
    return [
        numeric("REGION_CODE",            "Region Code (PSGC)",                           length=2,  zero_fill=True),
        numeric("PROVINCE_HUC_CODE",      "Province / HUC Code (PSGC)",                   length=2,  zero_fill=True),
        numeric("CITY_MUNICIPALITY_CODE", "City / Municipality Code (PSGC)",              length=3,  zero_fill=True),
        numeric("FACILITY_NO",            "Facility Number (within municipality)",        length=2,  zero_fill=True),
        numeric("CASE_SEQ",               "Case Sequence (per-facility, per-instrument)", length=3,  zero_fill=True),
        alpha("REGION_NAME",   "Region (from PSGC)",              length=80),
        alpha("PROVINCE_NAME", "Province / HUC (from PSGC)",      length=80),
        alpha("CITY_NAME",     "City / Municipality (from PSGC)", length=80),
    ]


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
# The real 'Other (specify)' marker: 'specif' immediately after an opening paren or a
# comma — 'Other (Specify)', 'Other, specify', 'Other disability (specify)'. This does
# NOT match 'specif' buried in a definition (e.g. Q45 'Indigent (i.e., ... as specified
# ...)') or a substantive 'Other health care provider', so the gate can't latch onto the
# wrong value (#400 Q40 + Q39/Q44/Q45).
_SPECIFY_OPTION_RE = re.compile(r"[(,]\s*specif", re.IGNORECASE)


def _label_text(node):
    labs = node.get("labels") or [{}]
    return labs[0].get("text", "") or ""


def _other_value_code(item):
    """The 'Other (specify)' value code of a coded item, or None. Prefer a value whose
    label carries the parenthetical/comma 'specify' marker; fall back to the loose match
    only when no such value exists (so legacy 'Others'-style options are unchanged)."""
    vals = [(val, _label_text(val)) for vs in (item.get("valueSets") or [])
            for val in (vs.get("values") or [])]
    for matcher in (_SPECIFY_OPTION_RE, _OTHER_LABEL_RE):
        for val, lbl in vals:
            if matcher.search(lbl):
                code = (val.get("pairs") or [{}])[0].get("value")
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
                f"PROC {n}\npreproc\n"
                f"  if {parent_name} <> {lit} then\n"
                f"    {n} = \"\";   {{ skip + clear: 'Other' not chosen -> field must not be enterable }}\n"
                f"    noinput;\n  endif;\n"
                f"postproc\n"
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
        group_flags = [k for k in sorted(items) if flag_re.match(k)]

        def _opt_text(k):
            lbl = _label_text(items[k])
            return lbl.rsplit("—", 1)[-1] if "—" in lbl else lbl

        # Prefer the flag whose OPTION text (after the em-dash) literally says
        # 'specify'. A substantive option that merely contains the word 'other'
        # ('Other facility visits', 'Referred by other specialist', 'Other
        # infection…') must NOT capture the gate — otherwise the real 'Other
        # (specify)' box never appears (#507/#513, + Q82/Q85/Q87/Q113/Q1142).
        # Fall back to the loose match for groups with no 'specify' option (e.g.
        # amount-matrix 'Other expenses' rows) so those are unchanged.
        other_flag = next(
            (k for k in group_flags if re.search(r"specif", _opt_text(k), re.I)), None)
        if other_flag is None:
            other_flag = next(
                (k for k in group_flags
                 if _OTHER_LABEL_RE.search(_label_text(items[k]))), None)
        if other_flag is not None:
            procs[n] = (
                f"PROC {n}\npreproc\n"
                f"  if {other_flag} <> 1 then\n"
                f"    {n} = \"\";   {{ skip + clear: 'Other (specify)' not ticked -> field must not be enterable }}\n"
                f"    noinput;\n  endif;\n"
                f"postproc\n"
                f"  if {other_flag} = 1 and length(strip({n})) = 0 then\n"
                f"    errmsg(\"'Other (specify)' was selected for {base} but no text was entered. Please specify.\");\n"
                f"    reenter;\n  endif;"
            )
            mapping.append((n, f"select-all: {other_flag} = 1"))
            continue

        # (3) unresolved -> manual
        skipped.append(n)
    return procs, mapping, skipped


# ---------------------------------------------------------------------------
# Select-all validation — auto-derived from the dictionary
# ---------------------------------------------------------------------------
# For every "select all that apply" group <BASE>_O01.._Onn (each flag 1=Yes/2=No)
# the spec marks two HARD rules (F3 §3.5-3.14, F4 equivalents):
#   * at least one option must be ticked when the group is reached;
#   * an exclusive option ("I don't know" / "None" / "There are no benefits" /
#     "No condition" / "Did not …") cannot be combined with any other option.
# Both checks are emitted on the group's LAST flag's postproc (fires once the
# whole group has been entered; a skipped group never reaches it). Expenditure /
# payment matrices (a flag with an <flag>_AMT sibling) are EXCLUDED — they carry
# separate amount/subtotal logic and zero selections can be valid there.

_EXCLUSIVE_LABEL_RE = re.compile(
    r"i don'?t know|none of|there are no|no condition|no benefit|did not|"
    r"\bnone\b|not applicable",
    re.IGNORECASE,
)


def _select_all_groups(items):
    """{base: [flag names sorted]} for genuine select-all option groups
    (>=2 yes/no flags, excluding expenditure/amount matrices)."""
    groups = {}
    flag_re = re.compile(r"^(?P<base>.+?)_O?\d+$")
    for n in sorted(items):
        m = flag_re.match(n)
        if not m or n.endswith("_AMT") or n.endswith("_TXT"):
            continue
        it = items[n]
        codes = {str(v.get("pairs", [{}])[0].get("value"))
                 for vs in it.get("valueSets") or [] for v in vs.get("values") or []}
        if not ({"1"} <= codes):           # must be a Yes/No-style flag (has code 1)
            continue
        base = m.group("base")
        if any((f"{n}_AMT") in items for n in [n]):  # this flag has an amount -> matrix
            continue
        groups.setdefault(base, []).append(n)
    # drop amount-matrix groups (any flag has an _AMT sibling) and singletons
    out = {}
    for base, flags in groups.items():
        if len(flags) < 2:
            continue
        if any(f"{f}_AMT" in items for f in flags):
            continue
        out[base] = sorted(flags)
    return out


# ---------------------------------------------------------------------------
# Exclusive-option detection — SOFT warning when an exclusive answer is combined
# ---------------------------------------------------------------------------
# An "exclusive" select-all option ('I don't know' / 'None of the above' / 'There
# are no benefits…' / 'Not applicable') is a standalone answer that should NOT be
# ticked together with substantive options. CSPro can hard-block this, but
# auto-detecting WHICH option is exclusive by label is imperfect — so we emit a
# SOFT warning (errmsg, no reenter): even a mis-detection only adds a confirm
# prompt, it never traps the enumerator. Detection matches the OPTION text (after
# the em-dash in the dcf label) as a near-whole phrase, so a shared question stem
# ('If none, why…') or a 'don't know how/what X' specific reason cannot false-match.

_EXCL_EXACT = {
    "i don't know", "i dont know", "don't know", "dont know", "none", "wala",
    "none of the above", "none of these", "none of the above options",
    "not applicable", "n/a", "na", "refused", "not sure", "unsure",
    "i am not sure", "prefer not to say", "prefer not to answer", "no answer",
}


def is_exclusive_option(label):
    """True when a select-all option label denotes an EXCLUSIVE / standalone answer."""
    opt = label.rsplit("—", 1)[-1]            # option text after the em-dash
    t = re.sub(r"\s+", " ", opt.lower()).strip().rstrip(".").strip()
    if t in _EXCL_EXACT:
        return True
    if t.startswith("there are no") or t.startswith("there is no"):
        return True
    if re.search(r"^no (benefits?\b|forms? of professional|available)", t):
        return True
    return False


def _exclusive_split(flags, items):
    """Partition a group's flags into (exclusive, substantive)."""
    excl = [f for f in flags if is_exclusive_option(_label_text(items[f]))]
    sub = [f for f in flags if f not in excl]
    return excl, sub


def _exclusivity_warning_lines(base, excl, sub):
    """CSPro statement lines (soft warning) for an exclusive-vs-substantive clash."""
    excl_or = " or ".join(f"{f} = 1" for f in excl)
    sub_or = " or ".join(f"{f} = 1" for f in sub)
    return [
        "  { exclusivity (soft warning): an exclusive option should be the only answer }",
        f"  if ({excl_or}) and ({sub_or}) then",
        f"    errmsg(\"{base}: an exclusive option (e.g. 'None' or 'Do not know') was ticked "
        f"together with other answers. Please review - an exclusive option should be the only choice.\");",
        "  endif;",
    ]


def select_all_exclusive_warning_procs(items):
    """Standalone soft-warning PROCs ({last_flag: proc_text}) for select-all groups
    that carry an exclusive option. For instruments WITHOUT the at-least-one check
    (F1); F3/F4 get the warning merged into select_all_validation_procs()."""
    out = {}
    for base, flags in sorted(_select_all_groups(items).items()):
        excl, sub = _exclusive_split(flags, items)
        if not (excl and sub):
            continue
        last = flags[-1]
        out[last] = "\n".join([f"PROC {last}", "postproc"] + _exclusivity_warning_lines(base, excl, sub))
    return out


def select_all_validation_procs(items):
    """'At least one option ticked' enforcement for every select-all group, PLUS a
    SOFT exclusivity warning when the group carries an exclusive option. Both emitted
    on the group's LAST flag postproc (fires once the group is entered; a skipped
    group never reaches it). Returns (procs: {last_flag: text}, bases: [base]).

    Exclusivity is a soft warning (errmsg, no reenter) — see is_exclusive_option():
    auto-detecting the exclusive option by label is imperfect, so we warn rather than
    hard-block, which stays safe even on a mis-detection. Specific groups could be
    upgraded to a hard reenter later from the spec's explicit exclusive codes."""
    procs, bases = {}, []
    for base, flags in sorted(_select_all_groups(items).items()):
        last = flags[-1]
        any_ticked = " or ".join(f"{f} = 1" for f in flags)
        lines = [
            f"PROC {last}", "postproc",
            f"  if not ({any_ticked}) then",
            f"    errmsg(\"Select at least one option for {base} before continuing.\");",
            "    reenter;", "  endif;",
        ]
        excl, sub = _exclusive_split(flags, items)
        if excl and sub:
            lines.extend(_exclusivity_warning_lines(base, excl, sub))
        procs[last] = "\n".join(lines)
        bases.append(base)
    return procs, bases


# ---------------------------------------------------------------------------
# Range + amount-required validations (spec §3.x per-item rules)
# ---------------------------------------------------------------------------

def range_check_proc(field, lo, hi, hard=True, soft_over=None):
    """Numeric range check. HARD -> reenter; otherwise warn only. `soft_over`
    adds a second soft warning when field exceeds that value (spec 'warn if >N')."""
    lines = [f"PROC {field}", "postproc",
             f"  if {field} < {lo} or {field} > {hi} then",
             f"    errmsg(\"{field} must be between {lo} and {hi}.\");"]
    if hard:
        lines.append("    reenter;")
    lines.append("  endif;")
    if soft_over is not None:
        lines += [f"  if {field} > {soft_over} then",
                  f"    errmsg(\"{field} = %d is unusually high — confirm.\", {field});",
                  "  endif;"]
    return "\n".join(lines)


def amount_required_procs(items):
    """Payment/expenditure matrices: for each `<FLAG>_AMT` whose `<FLAG>` is a
    Yes/No option, require a positive amount when the option is selected
    (spec 'for each *_PAY_NN = Yes, *_AMT > 0'). Auto-derived from the dcf."""
    procs = {}
    for n in sorted(items):
        if not n.endswith("_AMT"):
            continue
        flag = n[: -len("_AMT")]
        f = items.get(flag)
        if not f:
            continue
        codes = {str(v.get("pairs", [{}])[0].get("value"))
                 for vs in f.get("valueSets") or [] for v in vs.get("values") or []}
        if "1" not in codes:                       # flag must be a Yes(1)/No option
            continue
        # F3 #553 (retest fix): when the row's flag is NOT selected, auto-set the
        # amount to 0 and skip the field (noinput). Earlier we set it to `notappl`
        # (blank), but the _AMT fields render on a combined/DisplayTogether screen
        # where `noinput` is ignored, and a blank numeric trips CSEntry's built-in
        # range check ("Out of range! enter a valid value for <AMT>" — Marriz's
        # retest, Q107_PAY_03). 0 is in range, so it passes silently and is pre-filled
        # — the enumerator never has to type it. A No row is recorded as 0 (clean).
        procs[n] = (
            f"PROC {n}\npreproc\n"
            f"  if {flag} <> 1 then\n"
            f"    {n} = 0;   {{ #553: No-ticked row -> amount auto-set 0 (in range) + skip }}\n"
            f"    noinput;\n  endif;\n"
            f"postproc\n"
            f"  if {flag} = 1 and ({n} = 0 or {n} = notappl) then\n"
            f"    errmsg(\"'{flag}' was selected — enter its amount (must be greater than 0).\");\n"
            f"    reenter;\n  endif;"
        )
    return procs
