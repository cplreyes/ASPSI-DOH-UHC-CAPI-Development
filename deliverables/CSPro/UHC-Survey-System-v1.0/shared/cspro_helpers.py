"""cspro_helpers.py — CSPro 8.0 dictionary writer primitives.

Item builders, the record / value-set wrappers, the shared FIELD_CONTROL
builder, and the dictionary assembler for the UHC Survey System v1.0
generators.

v1.0 difference from the predecessor build: ``build_dictionary()`` takes a
LIST of ID items — the 12-digit RR-PP-MMM-FF-CCC block from ``case_id`` —
rather than a single ``QUESTIONNAIRE_NO`` id item.
"""

from __future__ import annotations

import json
from pathlib import Path

from .value_sets import (
    YES_NO, YES_NO_DK, YES_NO_NA, UHC9_OPTIONS,
    ENUM_RESULT_OPTIONS, AAPOR_DISPOSITION_OPTIONS,
)


# ============================================================
# 1. ITEM + VALUE-SET PRIMITIVES
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
    """Single-choice numeric item. Default width 2 (zero-filled); pass
    length=1 for value sets with <= 9 codes."""
    return numeric(name, label, length=length,
                   zero_fill=(length > 1),
                   value_set_options=options)


def select_all(prefix, label, options, with_other_txt=None):
    """SELECT-ALL idiom: one dichotomous item per option (1=selected, 2=not).

    If ``with_other_txt`` is True (or None and the last option mentions
    "specify"), appends an ``{prefix}_OTHER_TXT`` alpha for the free text.
    """
    items = []
    for i, (text, _code) in enumerate(options):
        items.append(numeric(
            f"{prefix}_O{i + 1:02d}",
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
    9-option value set) plus two free-text items for the "Yes, other" and
    "No, other" specify branches."""
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
# 2. SHARED FIELD_CONTROL BUILDER
# ============================================================

def _case_control_items(survey_code):
    """Five case-start metadata items prepended to every FIELD_CONTROL record
    (F1/F3/F4). Populated by the instrument's FIELD_CONTROL.preproc handler in
    phase 4 (.apc). ``survey_code`` is one of "F1", "F3", "F4"."""
    return [
        alpha("SURVEY_CODE",          "Survey Instrument Code",            length=2),
        numeric("INTERVIEWER_ID",     "Interviewer ID",                    length=4,
                zero_fill=True),
        numeric("DATE_STARTED",       "Date Interview Started (YYYYMMDD)", length=8),
        numeric("TIME_STARTED",       "Time Interview Started (HHMMSS)",   length=6),
        numeric("AAPOR_DISPOSITION",  "AAPOR Disposition Code",            length=3,
                zero_fill=True, value_set_options=AAPOR_DISPOSITION_OPTIONS),
    ]


def build_field_control(survey_code, extra_items=None, date_label_entity="the Facility"):
    """Build a FIELD_CONTROL record (record type "A").

    Standard items, in order: SURVEY_CODE, INTERVIEWER_ID, DATE_STARTED,
    TIME_STARTED, AAPOR_DISPOSITION, SURVEY_TEAM_LEADER_S_NAME,
    ENUMERATOR_S_NAME, FIELD_VALIDATED_BY, FIELD_EDITED_BY,
    DATE_FIRST_VISITED, DATE_FINAL_VISIT, TOTAL_NUMBER_OF_VISITS,
    ENUM_RESULT_FIRST_VISIT, ENUM_RESULT_FINAL_VISIT, CONSENT_GIVEN.
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


# ============================================================
# 3. DICTIONARY ASSEMBLY
# ============================================================

def build_dictionary(dict_name, dict_label, id_items, records):
    """Assemble a complete CSPro 8.0 dictionary JSON structure.

    Parameters
    ----------
    dict_name : str
        Dictionary name, UPPER_SNAKE (e.g. "FACILITYHEADSURVEY_DICT").
    dict_label : str
        Human-readable dictionary label (e.g. "FacilityHeadSurvey").
    id_items : list of dict
        Ordered list of level ID items — the RR-PP-MMM-FF-CCC block from
        ``case_id.build_id_block()``. ``start`` positions are assigned here:
        the record-type char occupies position 1; IDs follow contiguously.
    records : list of dict
        Record dicts produced by ``record()`` / ``build_field_control()`` etc.
    """
    level_name = dict_name.replace("_DICT", "_LEVEL")
    level_label = dict_label + " Level"

    pos = 2  # position 1 is the 1-char record type
    for it in id_items:
        it["start"] = pos
        pos += it["length"]

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
                "name":    level_name,
                "labels":  [{"text": level_label}],
                "ids":     {"items": id_items},
                "records": records,
            }
        ],
    }


def write_dcf(dictionary, out_path):
    """Write a CSPro dictionary to ``out_path`` and print diagnostics.
    Returns ``(record_count, item_count)``."""
    out_path = Path(out_path)
    out_path.write_text(json.dumps(dictionary, indent=2), encoding="utf-8")

    level = dictionary["levels"][0]
    id_list = level["ids"]["items"]
    record_list = level["records"]
    record_count = len(record_list)
    item_count = sum(len(r["items"]) for r in record_list)

    print(f"Wrote {out_path}")
    print(f"  ID items: {len(id_list)}  ({sum(i['length'] for i in id_list)} digits)")
    print(f"  Records:  {record_count}")
    print(f"  Items:    {item_count}")
    return record_count, item_count
