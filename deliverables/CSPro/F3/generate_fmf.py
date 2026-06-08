"""
generate_fmf.py - F3 Patient Survey CSPro Form File generator.

Emits PatientSurvey.generated.fmf - a COMPLETE, bindable CSPro 8.0 form file for
PatientSurvey.dcf. Mirrors the 32-form plan in F3-Form-Layout-Plan.md
(FIELD_CONTROL -> Geo -> capture triggers -> sections A-L -> closing).

FULL-STRUCTURE generation (2026-06-08): in addition to the visual [Form] blocks
(item membership + tab order), this now emits the logical structure CSPro requires
to open the file as a bound application without stripping items:
  [Level] -> one [Group] per form (Form=N, Max=1) -> [Field] + [Text] per item.
Auto-layout mirrors the working F1 .fmf: label at x=50, field at x=350, rows every
30px; DataCaptureType=RadioButton for value-set (coded) items, TextBox otherwise
(UseUnicodeTextBox=Yes for alpha). The id-items form and the level-1 container form
are emitted as EMPTY groups (exactly as F1 does) -- id items live in the dict id block.

This makes the file open + compile in Designer with no [Level]/[Group] warnings,
so the compile can be driven headlessly. Visual polish (split oversized sections,
capture-trigger buttons, roster grids) remains optional Designer refinement.

Run:
    python generate_fmf.py        # writes PatientSurvey.generated.fmf next to this file
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from generate_dcf import build_f3_dictionary
from cspro_helpers import _truncate_long_labels


DICT_LABEL = "PatientSurvey"
FF_NAME = "PATIENTSURVEY_FF"
DCF_REL_PATH = r".\PatientSurvey.dcf"

DEFAULT_FONT = (
    "DefaultTextFont=-013 0000 0000 0000 0700 0000 0000 0000 "
    "0000 0000 0000 0000 0000 Arial"
)
ENTRY_FONT = (
    "FieldEntryFont=0018 0000 0000 0000 0600 0000 0000 0000 "
    "0000 0000 0000 0000 0000 Courier New"
)

# --- Auto-layout geometry (mirrors the working F1 .fmf) ---
ROW_H = 30          # vertical pitch between fields
TOP_Y = 27          # first field's top
LABEL_X = 50
LABEL_X2 = 330
FIELD_X = 350
FIELD_TEXTBOX_X2 = 760
FIELD_RADIO_X2 = 365   # radio fields are narrow; options expand below
FIELD_H = 20
TEXT_H = 16
FORM_W = 806


FIELD_CONTROL_CASE_START = {
    "SURVEY_CODE", "INTERVIEWER_ID", "DATE_STARTED", "TIME_STARTED",
    "AAPOR_DISPOSITION", "PATIENT_TYPE", "PATIENT_LISTING_NO", "CONSENT_GIVEN",
    "LANGUAGE_USED",
}
FIELD_CONTROL_CASE_END = {
    "SURVEY_TEAM_LEADER_S_NAME", "ENUMERATOR_S_NAME",
    "FIELD_VALIDATED_BY", "FIELD_EDITED_BY",
    "DATE_FIRST_VISITED", "DATE_FINAL_VISIT", "TOTAL_NUMBER_OF_VISITS",
    "ENUM_RESULT_FIRST_VISIT", "ENUM_RESULT_FINAL_VISIT",
}


FORM_PLAN = [
    ("FC Metadata - case start",
     [("FIELD_CONTROL", {"names": FIELD_CONTROL_CASE_START})]),
    ("FC Geographic ID + F1 linkage",
     [("PATIENT_GEO_ID", None)]),
    ("FC Facility GPS Capture",
     [("REC_FACILITY_CAPTURE", None)]),
    ("FC Patient Home GPS + Verification Photo",
     [("REC_PATIENT_HOME_CAPTURE", None),
      ("REC_CASE_VERIFICATION", None)]),
    ("A. Informed Consent (Q1 gate)",
     [("A_INFORMED_CONSENT", None)]),
    ("B. Patient Profile",
     [("B_PATIENT_PROFILE", None)]),
    ("C. UHC Awareness",
     [("C_UHC_AWARENESS", None)]),
    ("D. PhilHealth Registration",
     [("D_PHILHEALTH_REG", None)]),
    ("E. Primary Care + YAKAP/Konsulta",
     [("E_PRIMARY_CARE", None)]),
    ("F. Health-Seeking",
     [("F_HEALTH_SEEKING", None)]),
    ("G. Outpatient Care",
     [("G_OUTPATIENT_CARE", None)]),
    ("H. Inpatient Care",
     [("H_INPATIENT_CARE", None)]),
    ("I. Financial Risk",
     [("I_FINANCIAL_RISK", None)]),
    ("J. Satisfaction",
     [("J_SATISFACTION", None)]),
    ("K. Access to Medicines",
     [("K_ACCESS_MEDICINES", None)]),
    ("L. Referrals",
     [("L_REFERRALS", None)]),
    ("Closing - case end",
     [("FIELD_CONTROL", {"names": FIELD_CONTROL_CASE_END})]),
]


def _filter_items(items, spec):
    """Apply a filter_spec to a record's item list; preserves source order."""
    if spec is None:
        return list(items)
    if "names" in spec:
        keep = set(spec["names"])
        return [it for it in items if it["name"] in keep]
    if "exclude" in spec:
        skip = set(spec["exclude"])
        return [it for it in items if it["name"] not in skip]
    raise ValueError(f"Unknown filter_spec keys: {spec!r}")


def _group_symbol(primary_record, used):
    """A unique, valid CSPro symbol for a form's [Group]; '_FORM' suffix avoids
    colliding with the dictionary record of the same name (F1 convention)."""
    base = re.sub(r"[^A-Za-z0-9]+", "_", primary_record).strip("_").upper() + "_FORM"
    if not base[0].isalpha():
        base = "F_" + base
    sym, i = base, 2
    while sym in used:
        sym = f"{base}_{i}"
        i += 1
    used.add(sym)
    return sym


def _form_height(n_items):
    return max(300, TOP_Y + n_items * ROW_H + 40)


def _emit_form(lines, form_num, label, item_names, height):
    lines.append("[Form]")
    lines.append(f"Name=FORM{form_num:03d}")
    lines.append(f"Label={label}")
    lines.append("Level=1")
    lines.append(f"Size={FORM_W},{height}")
    lines.append("  ")
    for name in item_names:
        lines.append(f"Item={name}")
    lines.append("  ")
    lines.append("[EndForm]")
    lines.append("  ")


def _emit_group(lines, group_sym, label, form_one_based, item_objs, dict_name):
    lines.append("[Group]")
    lines.append("Required=Yes")
    lines.append(f"Name={group_sym}")
    lines.append(f"Label={label}")
    lines.append(f"Form={form_one_based}")
    lines.append("Max=1")
    if not item_objs:
        lines.append("[EndGroup]")
        lines.append("  ")
        return
    lines.append("  ")
    for i, it in enumerate(item_objs):
        y = TOP_Y + i * ROW_H
        coded = bool(it.get("valueSets"))
        is_alpha = it.get("contentType") == "alpha"
        field_x2 = FIELD_RADIO_X2 if coded else FIELD_TEXTBOX_X2
        capture = "RadioButton" if coded else "TextBox"
        text = (it["labels"][0]["text"] if it.get("labels") else it["name"]).replace("\n", " ").replace("\r", " ")
        # [Field]
        lines.append("[Field]")
        lines.append(f"Name={it['name']}")
        lines.append(f"Position={FIELD_X},{y},{field_x2},{y + FIELD_H}")
        lines.append(f"Item={it['name']},{dict_name}")
        if not coded and is_alpha:
            lines.append("UseUnicodeTextBox=Yes")
        lines.append(f"DataCaptureType={capture}")
        lines.append(f"Form={form_one_based}")
        lines.append("  ")
        # [Text]
        lines.append("[Text]")
        lines.append(f"Position={LABEL_X},{y + 3},{LABEL_X2},{y + 3 + TEXT_H}")
        lines.append(f"Text={text}")
        lines.append(" ")
        lines.append("  ")
    lines.append("[EndGroup]")
    lines.append("  ")


def build_fmf():
    dictionary = build_f3_dictionary()
    _truncate_long_labels(dictionary)  # match the .dcf's 255-char label cap (CSPro max)
    dict_name = dictionary.get("name", "PATIENTSURVEY_DICT")
    level = dictionary["levels"][0]
    level_name = level.get("name", "PATIENTSURVEY_LEVEL")
    records_by_name = {r["name"]: r for r in level["records"]}
    id_item_names = [it["name"] for it in level["ids"]["items"]]
    container_rec = next((r["name"] for r in level["records"] if r.get("recordType") == "1"), "PATIENTSURVEY_REC")

    referenced = {rec for _, parts in FORM_PLAN for rec, _ in parts}
    missing = referenced - set(records_by_name)
    if missing:
        raise RuntimeError(f"FORM_PLAN references missing records: {sorted(missing)}")

    record_items_consumed = {name: set() for name in records_by_name}
    used_group_syms = set()

    # forms: list of dicts {num, label, group_sym, form_item_names, group_item_objs}
    forms = []
    # FORM000 - id items: EMPTY form + EMPTY group (mirrors F1). Id items live in
    # the dict ID block and are auto-associated; listing them as form Items makes
    # CSPro report "Item ... not found in any [Group] block" and strip them.
    _ = id_item_names  # intentionally not placed on the form
    forms.append({"num": 0, "label": "(Id Items)", "group_sym": "IDS0_FORM",
                  "form_item_names": [], "group_item_objs": []})
    used_group_syms.add("IDS0_FORM")
    # FORM001 - level-1 container record (empty group)
    forms.append({"num": 1, "label": "PatientSurvey Record",
                  "group_sym": _group_symbol(container_rec, used_group_syms),
                  "form_item_names": [], "group_item_objs": []})
    # FORM002.. - planned forms
    for idx, (label, parts) in enumerate(FORM_PLAN, start=2):
        objs = []
        for rec_name, spec in parts:
            for it in _filter_items(records_by_name[rec_name]["items"], spec):
                record_items_consumed[rec_name].add(it["name"])
                objs.append(it)
        primary = parts[0][0]
        forms.append({"num": idx, "label": label,
                      "group_sym": _group_symbol(primary, used_group_syms),
                      "form_item_names": [it["name"] for it in objs],
                      "group_item_objs": objs})

    lines = []
    lines.append("[FormFile]")
    lines.append("Version=CSPro 8.0")
    lines.append(f"Name={FF_NAME}")
    lines.append(f"Label={DICT_LABEL}")
    lines.append(DEFAULT_FONT)
    lines.append(ENTRY_FONT)
    lines.append("Type=SystemControlled")
    lines.append("  ")
    lines.append("[Dictionaries]")
    lines.append(f"File={DCF_REL_PATH}")
    lines.append("  ")

    # Visual [Form] blocks
    for f in forms:
        _emit_form(lines, f["num"], f["label"], f["form_item_names"],
                   _form_height(len(f["group_item_objs"])))

    # Logical structure: one [Level], one [Group] per form
    lines.append("[Level]")
    lines.append(f"Name={level_name}")
    lines.append(f"Label={DICT_LABEL} Level")
    lines.append("  ")
    for f in forms:
        _emit_group(lines, f["group_sym"], f["label"], f["num"] + 1,
                    f["group_item_objs"], dict_name)

    # Orphan check
    orphans = []
    for rec_name, rec in records_by_name.items():
        if rec["recordType"] == "1":
            continue
        placed = record_items_consumed[rec_name]
        for it in rec["items"]:
            if it["name"] not in placed:
                orphans.append(f"{rec_name}.{it['name']}")
    if orphans:
        sys.stderr.write(f"WARNING: {len(orphans)} items not placed on any form:\n")
        for o in orphans:
            sys.stderr.write(f"  {o}\n")

    return "\r\n".join(lines) + "\r\n", len(orphans)


def main():
    out_path = Path(__file__).parent / "PatientSurvey.generated.fmf"
    fmf_text, orphan_count = build_fmf()
    out_path.write_text(fmf_text, encoding="utf-8")
    sys.stderr.write(f"Wrote {out_path} ({orphan_count} orphan items)\n")


if __name__ == "__main__":
    main()
