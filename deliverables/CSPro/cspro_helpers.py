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
    """Load a PSGC CSV (produced by data/psgc/parse_psgc.py) into
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
#
# "Replaced" (2026-07-14) — the sampled unit was never interviewed, so a substitute is
# drawn to hold the sample size. Set by PROC BREAKOFF from the never-started codes
# (BREAKOFF 5/6/7 = refused at the door / not found / ineligible); the REASON stays on
# BREAKOFF, this only records the OUTCOME. Appended at the end of each list so existing
# codes keep their values — never renumber, it would orphan already-synced cases.
# The per-instrument code differs (F1=5, F3=7, F4=5) because each list has a different
# length, so cross-instrument queries must count BREAKOFF in 5,6,7 — that IS uniform.
REPLACED_CODE_F1 = "5"
REPLACED_CODE_F3 = "7"
REPLACED_CODE_F4 = "5"

ENUM_RESULT_OPTIONS_F1 = [          # F1 Facility Head
    ("Completed",  "1"),
    ("Postponed",  "2"),
    ("Refused",    "3"),
    ("Incomplete", "4"),
    ("Replaced",   REPLACED_CODE_F1),
]
ENUM_RESULT_OPTIONS_F3 = [          # F3 Patient
    ("Completed",                       "1"),
    ("Completed at the Hospital",       "2"),
    ("Postponed",                       "3"),
    ("Incomplete",                      "4"),
    ("Completed at Home",               "5"),
    ("Withdraw Participation/Consent",  "6"),
    ("Replaced",                        REPLACED_CODE_F3),
]
ENUM_RESULT_OPTIONS_F4 = [          # F4 Household
    ("Completed",                       "1"),
    ("Postponed",                       "2"),
    ("Incomplete",                      "3"),
    ("Withdraw Participation/Consent",  "4"),
    ("Replaced",                        REPLACED_CODE_F4),
]
ENUM_RESULT_OPTIONS = ENUM_RESULT_OPTIONS_F1   # default / back-compat

# Break-off / interview-status codes. IDENTICAL across F1/F3/F4 on purpose: this is the
# one field a cross-instrument query can rely on. Codes 1-4 are the original #515/#744
# break-off set (the interview STARTED and then stopped). Codes 5-7 were added 2026-07-14
# for the never-started outcomes — the case that ASPSI/SAAD calls a replacement.
#
# Per ASPSI (Marriz, 2026-07-14): every unit that cannot be interviewed is replaced by a
# substitute, so refused-at-the-door + not-found + ineligible are ALL replacements; the
# code distinguishes only WHY. "Postponed" (3) is deliberately NOT a replacement — that
# unit is revisited, not substituted, and counting it would overstate the rate and blunt
# the curbstoning signal (a high replacement rate per enumerator is the standard check).
BREAKOFF_OPTIONS = [
    ("Continue interview",           "1"),
    ("Respondent withdrew",          "2"),
    ("Postponed / reschedule",       "3"),
    ("Stop — other (incomplete)",    "4"),
    ("Not interviewed — refused",    "5"),
    ("Not interviewed — not found",  "6"),
    ("Not interviewed — ineligible", "7"),
]
BREAKOFF_REPLACED_CODES = ("5", "6", "7")

# NOTE (2026-07-14) — an AAPOR_DISPOSITION_OPTIONS constant lived here from 2026-04-22 until
# today. AAPOR (the survey-research disposition taxonomy) was never requested by ASPSI or DOH,
# is not their vocabulary, and was not on the April-20 paper Field Control form. The whole
# case-start block it belonged to (SURVEY_CODE, DATE_STARTED, TIME_STARTED, INTERVIEWER_ID,
# AAPOR_DISPOSITION, CONSENT_GIVEN) was removed from F1/F3/F4 on 2026-06-12; the constant was
# left behind as dead code and is now deleted with it. Do not reintroduce it.
#
# The real dispositions are the paper ones, defined above:
#   CASE_DISPOSITION            0 In progress · 1 Completed · 2 Partial/not completed
#   BREAKOFF                    BREAKOFF_OPTIONS  ("Interview status", 1-7, same in F1/F3/F4)
#   ENUM_RESULT_FIRST/FINAL_VISIT   ENUM_RESULT_OPTIONS_F1 / _F3 / _F4  ("Result of Visit")
#
# RESOLVED 2026-07-14 — this block previously recorded a known gap: no instrument had a
# doorstep-refusal or non-contact code, so a replaced/never-started unit left no trace and
# replacement counts could not be derived (which also removed the standard curbstoning check).
# ASPSI (Marriz) confirmed the SAAD convention: any unit that cannot be interviewed is marked
# as such up front and then replaced. BREAKOFF codes 5/6/7 now capture exactly that, the case
# is still created and still syncs, and:
#
#     replacements = count(BREAKOFF in 5, 6, 7)     — per facility / enumerator / supervisor
#
# Postponed (BREAKOFF 3) is excluded by design: revisited, not substituted.


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
        # #1037 (F1 Q163): detect the specify option ANYWHERE in the list, not just
        # last — paper option order can put an exclusive (e.g. "I don't know") after
        # "Other (specify)". Last-only detection silently dropped the _OTHER_TXT dict
        # item while the apc still emitted its PROC -> Publish "PROC invalid" error.
        with_other_txt = any("specify" in text.lower() for text, _ in options)
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
        # #1037 (F1 Q163): detect the specify option ANYWHERE in the list, not just
        # last — paper option order can put an exclusive (e.g. "I don't know") after
        # "Other (specify)". Last-only detection silently dropped the _OTHER_TXT dict
        # item while the apc still emitted its PROC -> Publish "PROC invalid" error.
        with_other_txt = any("specify" in text.lower() for text, _ in options)
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


def record(name, label, record_type, items, max_occurs=1, required=True, occ_labels=None):
    """occ_labels: optional list of per-occurrence label strings (1-based order) for a
    repeating record — emitted as occurrences.labels per the CSPro 8 JSON dictionary shape
    ([{occurrence, labels: [{text}]}], zDictO/DictRecord.cpp). Names the roster row stub +
    case-tree occurrences (first use: F4 Section N Option C food grid, 2026-07-03)."""
    occurrences = {"required": required, "maximum": max_occurs}
    if occ_labels:
        occurrences["labels"] = [
            {"occurrence": k, "labels": [{"text": t}]}
            for k, t in enumerate(occ_labels, start=1)
        ]
    return {
        "name": name,
        "labels": [{"text": label}],
        "recordType": record_type,
        "occurrences": occurrences,
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


def _date_fmt(mmddyyyy):
    """Prompt suffix for the two visit-date fields.

    #1132/#1174 (ASPSI 2026-08-06): the paper asks the enumerator for MMDDYYYY, the CAPI
    asked for YYYYMMDD. Opting an instrument in flips only the PROMPT — the value is
    converted back to YYYYMMDD in that instrument's date postproc, so STORAGE never
    changes and every downstream consumer (final<first check, MM/DD/YYYY echo, Supervisor
    App, cross-instrument parsers) is untouched.

    Opt-in per instrument ON PURPOSE, and it is not cosmetic: flipping this without also
    adding the conversion postproc would have enumerators typing MMDDYYYY into a field
    stored raw as YYYYMMDD, silently corrupting every date. Only flip it together with
    that PROC.

    ALSO re-key the translations whenever this suffix changes (#1099, 2026-08-12).
    apply_translations() below matches on the FULL English label text and falls back to
    English SILENTLY on a miss, so a relabel orphans every translations/<loc>.json key for
    the affected items and the row quietly reverts to English with no warning — F4's Waray
    visit-date labels sat broken this way for six days. Move the keys, copy the values
    verbatim, and never author translated text as part of a relabel.
    """
    return "MMDDYYYY" if mmddyyyy else "YYYYMMDD"


def build_field_control(survey_code, extra_items=None, date_label_entity="the Facility",
                        result_options=None, date_display=False, date_mmddyyyy=False):
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
                f"Date First Visited {date_label_entity} ({_date_fmt(date_mmddyyyy)})", length=8),
        # #1099 (F4 pretest): optional read-only MM/DD/YYYY echo under each date.
        # The STORED composition is always YYYYMMDD (Supervisor App + cross-instrument
        # parsers depend on it). Under #1132/#1174 the TYPED order may now differ from
        # the stored one — see date_mmddyyyy — which makes this echo the enumerator's
        # confirmation that their entry parsed correctly. Opt-in (date_display=True).
        *([alpha("DATE_FIRST_VISITED_DISP",
                 "Date First Visited (MM/DD/YYYY)", length=10)] if date_display else []),
        numeric("DATE_FINAL_VISIT",
                f"Date of Final Visit to {date_label_entity} ({_date_fmt(date_mmddyyyy)})", length=8),
        *([alpha("DATE_FINAL_VISIT_DISP",
                 "Date of Final Visit (MM/DD/YYYY)", length=10)] if date_display else []),
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


def _cap_text(t, max_len=CSPRO_LABEL_MAX):
    """The exact string _truncate_long_labels would store for `t`.

    Factored out so apply_translations can look a translation up under the capped key as
    well as the full one - the two must stay in step, or #1182 comes back.
    """
    if not isinstance(t, str) or len(t) <= max_len:
        return t
    cut = t[:max_len - 3]
    sp = cut.rfind(" ")
    if sp > max_len * 0.6:
        cut = cut[:sp]
    return cut.rstrip(" ,;:-") + "..."


def _truncate_long_labels(node, max_len=CSPRO_LABEL_MAX, hits=None):
    """Recursively cap every labels[].text at CSPro's max_len, truncating at a word
    boundary + '...'. CSPro rejects a dictionary outright if any label exceeds 255
    chars; long verbatim option/category descriptions from the questionnaire trip this.
    Returns a list of (language, original_length, truncated_text) for everything capped.

    This is a LAST-RESORT safety net, not a feature. A capped label is a real defect on
    two counts, which is why write_dcf now NAMES every label it cuts instead of printing
    a bare count (#1177, 2026-08-09 — the bare count is why the two below went unnoticed
    through several deployed builds):

      1. The enumerator reads a definition that stops mid-sentence.
      2. It silently breaks translation lookup. apply_translations() keys off the FULL
         English source text, but a translation map extracted from an already-truncated
         .dcf carries the TRUNCATED string as its key. Those never match, so the label
         falls back to English in precisely the languages that had a translation.
         F3 Q45 'Lifetime member' / 'Senior citizen' shipped English in FIL/HIL/ILO
         for exactly this reason.

    The fix for a capped label is always to shorten it AT SOURCE and re-key its
    translation entries — never to let this function silently absorb it."""
    if hits is None:
        hits = []
    if isinstance(node, dict):
        labs = node.get("labels")
        if isinstance(labs, list):
            for lab in labs:
                t = lab.get("text")
                if isinstance(t, str) and len(t) > max_len:
                    lab["text"] = _cap_text(t, max_len)
                    hits.append((lab.get("language", "?"), len(t), lab["text"]))
        for k, v in node.items():
            _truncate_long_labels(v, max_len, hits)
    elif isinstance(node, list):
        for x in node:
            _truncate_long_labels(x, max_len, hits)
    return hits


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
    capped = _truncate_long_labels(dictionary)
    if capped:
        # An EN cap and a translation cap are NOT the same severity, so report them apart
        # (#1177). EN is the authored source AND the key apply_translations() looks up:
        # capping it truncates the text *and* silently drops that label's translation in
        # every locale. Those are named individually - they are always a bug to fix at
        # source. A capped translation only truncates that one locale's display, so those
        # are summarised per language and belong in the next translation pass.
        en = [c for c in capped if c[0] == "EN"]
        other = [c for c in capped if c[0] != "EN"]
        if en:
            print(f"  !! {len(en)} ENGLISH label(s) exceed {CSPRO_LABEL_MAX} chars and were cut. "
                  f"Fix AT SOURCE - a capped EN label also breaks its translation lookup:")
            for _lang, orig_len, text in en:
                # ASCII-safe: build logs run on a cp1252 console and questionnaire text
                # carries non-breaking hyphens, curly quotes and other non-cp1252 chars.
                safe = text[:80].encode("ascii", "replace").decode("ascii")
                print(f"       {orig_len} chars -> {safe}...")
        if other:
            by_lang = {}
            for lang, _orig_len, _text in other:
                by_lang[lang] = by_lang.get(lang, 0) + 1
            summary = ", ".join(f"{k}:{v}" for k, v in sorted(by_lang.items()))
            print(f"  -- {len(other)} translated label(s) cut at {CSPRO_LABEL_MAX} chars "
                  f"({summary}) - for the next translation pass, display only")
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
    # 2026-08-03: seventh locale — the June-5 DOH-cleared papers exist in Ilocano
    # for all four instruments; seeded from translations-paper-extract (#see
    # deliverables/CSPro/translations-paper-extract/QA-REPORT.md).
    ("ILO", "Ilocano",    "ilo.json"),
]


def _value_pair_key(value):
    """Stable identity for a value-set value: its CODES, never its wording.

    Codes are the one thing an English relabel cannot move (the codebook/DDI
    discipline), so translation keys built on them survive every rewording.
    """
    parts = []
    for p in value.get("pairs", []) or []:
        if "range" in p:
            r = p["range"]
            parts.append(f"{r[0]}..{r[1]}")
        elif "value" in p:
            parts.append(str(p["value"]))
    if value.get("special"):
        parts.append(f"special={value['special']}")
    return ",".join(parts) if parts else "?"


def walk_labeled_nodes(dictionary):
    """Yield (key, node) for every labels-bearing node of a CSPro 8 dictionary.

    THE key contract of the name-scoped translation map format (2026-08-17):
    this one walker is shared by apply_translations(), the map migrator and the
    poisoned-key scanner, so a key can never mean different things in different
    tools. Key shapes:
        dict:<NAME> | level:<NAME> | record:<NAME> | item:<NAME>
        vs:<VALUE-SET-NAME> | val:<VALUE-SET-NAME>:<code[,code|lo..hi]>
    """
    def item_nodes(it):
        yield f"item:{it.get('name', '?')}", it
        for vs in it.get("valueSets", []) or []:
            yield f"vs:{vs.get('name', '?')}", vs
            for v in vs.get("values", []) or []:
                yield f"val:{vs.get('name', '?')}:{_value_pair_key(v)}", v

    yield f"dict:{dictionary.get('name', '?')}", dictionary
    for lvl in dictionary.get("levels", []) or []:
        yield f"level:{lvl.get('name', '?')}", lvl
        for it in (lvl.get("ids") or {}).get("items", []) or []:
            yield from item_nodes(it)
        for rec in lvl.get("records", []) or []:
            yield f"record:{rec.get('name', '?')}", rec
            for it in rec.get("items", []) or []:
                yield from item_nodes(it)


def apply_translations(dictionary, translations_dir, languages=TRANSLATION_LANGUAGES):
    """Expand a single-language dictionary into a multi-language CSPro 8.0 dictionary.

    2026-08-17 re-key: maps are NAME-SCOPED (see walk_labeled_nodes), no longer
    keyed on full English label text. The text keys silently orphaned a
    translation on every English edit (#1182/#1213 — about half the measured
    coverage gap), and a bare shared option key ("No" served 36 F1 value sets)
    could not express per-question option wording (the #1222 wall). A name-
    scoped key survives rewording, and every value-set option is independently
    addressable. A missing key still means English fallback, verbatim. The
    #1182 capped-key fallback is gone: name keys never hit the 255-char cap.
    Mutates and returns `dictionary`; prints a per-language coverage summary.
    """
    translations_dir = Path(translations_dir)
    active, maps, skipped = [], {}, []
    for code, disp, fname in languages:
        if fname is None:
            active.append((code, disp))
        elif (translations_dir / fname).exists():
            m = json.loads((translations_dir / fname).read_text(encoding="utf-8"))
            m.pop("_meta", None)
            legacy = [k for k in m if ":" not in k]
            if legacy:
                raise SystemExit(
                    f"{fname}: {len(legacy)} legacy text-format keys (e.g. {legacy[0]!r}). "
                    "Maps must be name-scoped — run data/translations-official/"
                    "migrate_maps_namekeys.py or restore the intended map.")
            maps[code] = m
            active.append((code, disp))
        else:
            skipped.append(code)

    dictionary["languages"] = [{"name": c, "label": d} for c, d in active]
    counts = {c: [0, 0] for c in maps}   # code -> [matched, total]

    seen = set()
    for key, node in walk_labeled_nodes(dictionary):
        seen.add(id(node))
        labs = node.get("labels")
        if not (isinstance(labs, list) and labs and isinstance(labs[0], dict)
                and "text" in labs[0]):
            continue
        en_text = labs[0]["text"]
        new_labels = []
        for code, _disp in active:
            if code in maps:
                counts[code][1] += 1
                tr = maps[code].get(key)
                if tr is not None:
                    counts[code][0] += 1
                else:
                    tr = en_text
                new_labels.append({"text": tr, "language": code})
            else:
                new_labels.append({"text": en_text, "language": code})
        node["labels"] = new_labels

    # Safety net: the walker must reach every labels node the old generic
    # recursion reached — a structural addition that slips past it would ship
    # silently English in all locales. A missed node is a hard error.
    def _find_missed(node):
        if isinstance(node, dict):
            labs = node.get("labels")
            if (isinstance(labs, list) and labs and isinstance(labs[0], dict)
                    and "text" in labs[0] and id(node) not in seen):
                yield node
            for k, v in node.items():
                if k != "labels":
                    yield from _find_missed(v)
        elif isinstance(node, list):
            for it in node:
                yield from _find_missed(it)

    missed = list(_find_missed(dictionary))
    if missed:
        names = [m.get("name", "?") for m in missed[:5]]
        raise SystemExit(
            f"walk_labeled_nodes missed {len(missed)} labels node(s): {names} — "
            "extend the walker (and re-run the migrator) before generating.")

    print(f"  Languages: {', '.join(c for c, _ in active)}"
          + (f"   (no map, skipped: {', '.join(skipped)})" if skipped else ""))
    for code in maps:
        matched, total = counts[code]
        pct = (100 * matched // total) if total else 0
        print(f"    {code}: {matched}/{total} labels translated ({pct}%)")
    return dictionary


# R2 (2026-07-03): runtime errmsg texts move out of the logic into numbered .mgf
# messages so they can be translated like question text. Numbers are permanent
# once assigned — see numberize_errmsgs() below.
ERRMSG_NUMBER_BASE = 1001

_ERRMSG_OPEN = re.compile(r'errmsg\s*\(\s*(?=")', re.IGNORECASE)


def _parse_literal_chain(text, i):
    """Parse a CSPro string-literal chain starting at text[i] == '"'.

    Handles line-wrapped messages written as `"part one " + "part two"`.
    Returns (folded_text, end_index, clean) where end_index is just past the
    last closing quote and clean=True only when the chain is the COMPLETE
    argument (next non-space char is ',' or ')'). A chain that continues with
    a non-literal term (`+ strip(X)` etc.) returns clean=False — converting it
    would corrupt the call, so the caller must leave it inline.
    """
    parts = []
    while True:
        j = text.find('"', i + 1)
        if j < 0:
            return None, i, False               # unterminated — leave untouched
        parts.append(text[i + 1:j])
        k = j + 1
        while k < len(text) and text[k] in " \t\r\n":
            k += 1
        if k < len(text) and text[k] == "+":
            k2 = k + 1
            while k2 < len(text) and text[k2] in " \t\r\n":
                k2 += 1
            if k2 < len(text) and text[k2] == '"':
                i = k2                          # `+ "more text"` — keep folding
                continue
            return "".join(parts), j + 1, False  # `+ <expr>` — runtime concat
        clean = k < len(text) and text[k] in ",)"
        return "".join(parts), j + 1, clean


def _mgf_safe_text(text):
    """Make one message text safe for the strict .mgf parser (Publish/CSPack).

    zMessageO/MessageFile.cpp ProcessMessageText(): a text that BEGINS with a
    quote character is parsed as a string literal, and any trailing text then
    fails with "No text can follow a string literal" (mid-text quotes in bare
    text are fine). Remedy: emit the whole text as ONE string literal in the
    other quote type — the parser strips the enclosing quotes, so the
    displayed message is unchanged. A leading-quote text that contains both
    quote types (or a backslash, an escape hazard inside literals) falls back
    to typographic quotes so no delimiter starts the line.
    """
    if not text.startswith(("'", '"')):
        return text
    if '"' not in text and "\\" not in text:
        return f'"{text}"'
    if "'" not in text and "\\" not in text:
        return f"'{text}'"
    return text.replace("'", "’").replace('"', "”")


def numberize_errmsgs(apc_text, instrument_dir, mgf_path, app_label,
                      languages=TRANSLATION_LANGUAGES, generated_by="generate_apc.py"):
    """Swap inline errmsg("...") literals for numbered messages + emit the .mgf.

    Rewrites every errmsg("<text>", ...) in the assembled .apc to
    errmsg(<number>, ...) — fill arguments and everything after the literal are
    untouched, and the displayed text is unchanged (the .ent files set
    showErrorMessageNumbers=false). Generator/fragment sources keep their
    readable inline English; only the assembled output is numbered.

    Numbering is STABLE across regenerations via <instrument>/messages-registry.json
    (machine-managed — do not hand-edit): a text keeps its number forever, new
    texts append at the next free number, and retired texts stay in the registry
    so their numbers are never reused. That makes the numbers safe to key
    translations on.

    The .mgf gets a `Language = EN` section with the exact texts, plus one
    section per drop-in translations/messages.<locale>.json (same convention as
    apply_translations: keyed by the English text; a missing key falls back to
    English so every language section stays complete).

    Line-wrapped messages written as adjacent literals (`"part one " + "part
    two"`) are folded into ONE message. Calls whose first argument is NOT a
    complete literal (runtime concat like `"EA " + strip(X)`) are left inline
    and reported — rewrite those to fill-style (`errmsg("EA %s ...", strip(X))`)
    at the source to make them numberable. A text containing { or } would be
    truncated by the .mgf comment syntax, so it is also left inline (none exist).
    """
    instrument_dir = Path(instrument_dir)
    registry_path = instrument_dir / "messages-registry.json"
    if registry_path.exists():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    else:
        registry = {
            "_note": ("Machine-managed by cspro_helpers.numberize_errmsgs() — do not "
                      "hand-edit. Maps each errmsg text to its permanent message "
                      "number; numbers are never reused or renumbered."),
            "next": ERRMSG_NUMBER_BASE,
            "messages": {},
        }
    messages = registry["messages"]

    live, skipped = [], []      # texts in this build (first-appearance order); inline leftovers
    out, pos, n_calls = [], 0, 0
    for m in _ERRMSG_OPEN.finditer(apc_text):
        if m.start() < pos:
            continue                            # inside a chain already consumed
        text, end, clean = _parse_literal_chain(apc_text, m.end())
        if text is None:
            continue
        n_calls += 1
        if not clean or "{" in text or "}" in text:
            # runtime concat (`+ <expr>`) would be corrupted by numbering;
            # braces are .mgf comment syntax and would truncate the message.
            if text not in skipped:
                skipped.append(text)
            continue
        if text not in messages:
            messages[text] = registry["next"]
            registry["next"] += 1
        if text not in live:
            live.append(text)
        out.append(apc_text[pos:m.start()])
        out.append(f"errmsg({messages[text]}")
        pos = end
    out.append(apc_text[pos:])
    new_text = "".join(out)

    registry_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n",
                             encoding="utf-8")

    # ---- emit the .mgf: EN section always; translated sections are drop-in ----
    live_numbered = sorted((messages[t], t) for t in live)
    lines = [
        f"{{ {app_label} runtime messages — generated by {generated_by}; do NOT hand-edit. }}",
        "{ Numbering is permanent via messages-registry.json. To add a locale, drop        }",
        "{ translations/messages.<locale>.json (English text -> translated text) next to  }",
        "{ the generator and re-run — same convention as the .dcf label translations.     }",
        "Language = EN",
    ]
    lines += [f"{num} {_mgf_safe_text(text)}" for num, text in live_numbered]

    coverage = []
    for code, _disp, fname in languages:
        if fname is None:
            continue
        map_path = instrument_dir / "translations" / f"messages.{fname}"
        if not map_path.exists():
            continue
        tr_map = json.loads(map_path.read_text(encoding="utf-8"))
        matched = sum(1 for _n, t in live_numbered if t in tr_map)
        coverage.append((code, matched, len(live_numbered)))
        lines += ["", f"Language = {code}"]
        lines += [f"{num} {_mgf_safe_text(tr_map.get(text, text))}" for num, text in live_numbered]

    mgf_path = Path(mgf_path)
    mgf_path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig", newline="\r\n")

    print(f"  errmsg -> .mgf: {n_calls - len(skipped)} of {n_calls} calls numbered "
          f"({len(live_numbered)} distinct texts) -> {mgf_path.name}")
    for code, matched, total in coverage:
        pct = (100 * matched // total) if total else 0
        print(f"    {code}: {matched}/{total} messages translated ({pct}%)")
    if skipped:
        print(f"    WARNING: {len(skipped)} text(s) left inline (runtime concat or braces): "
              + "; ".join(t[:60] for t in skipped[:3]))
    return new_text


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

def range_check_proc(field, lo, hi, hard=True, soft_over=None, allow_sentinels=False):
    """Numeric range check. HARD -> reenter; otherwise warn only. `soft_over`
    adds a second soft warning when field exceeds that value (spec 'warn if >N').

    allow_sentinels (#761/#793 missing-value standard): when True, the negative
    missing-value codes -98 ("I don't know") and -99 ("Refuse to answer") are
    exempt from the range check — used on money-amount fields so the enumerator
    can record them without the 0..max range hard-blocking entry (#743 fix)."""
    guard = "{field} <> -98 and {field} <> -99 and ".format(field=field) if allow_sentinels else ""
    lines = [f"PROC {field}", "postproc",
             f"  if {guard}({field} < {lo} or {field} > {hi}) then",
             f"    errmsg(\"{field} must be between {lo} and {hi} (or -98 don't-know / -99 refused).\");" if allow_sentinels
             else f"    errmsg(\"{field} must be between {lo} and {hi}.\");"]
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
