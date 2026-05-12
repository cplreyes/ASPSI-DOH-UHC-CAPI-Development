"""generate_fmf.py — emit PatientSurvey.fmf in canonical CSPro 8.0 layout.

Parallel to 107_F1/generate_fmf.py + 110_F3_listing/generate_fmf.py — same
single-column auto-layout via shared.form_layout_engine, BOM-prefixed,
[Form] / [Level] / [Group] / [Field] / [Text] structure.

F3-specific form ordering:
  FORM000  — (Id Items)                        (5-item 12-digit case-ID block)
  FORM001  — Root record (PATIENTSURVEY_REC)   (CSPro hierarchy requirement)
  FORM002  — FIELD_CONTROL
  FORM003  — PATIENT_GEO_ID
  FORM004  — REC_FACILITY_CAPTURE              (GPS)
  FORM005  — REC_PATIENT_HOME_CAPTURE          (GPS)
  FORM006  — REC_CASE_VERIFICATION             (photo)
  FORM007  — A_INFORMED_CONSENT                (Q1-Q3)
  FORM008..FORM018 — B..L sections             (Q4-Q178)

Patient-pick screen — implemented via the FIELD_CONTROL.preproc handler in
generate_apc.py (commit 5), NOT as its own form. The handler runs at
case-open before any form opens, queries the listing app's PATIENTLISTING_DICT
EXTERNAL dictionary, prompts the operator with the eligible-patient list via
showlist(), and stamps the chosen patient's identifiers into the case header
+ ASSIGNED_F3_CASE_SEQ on the roster occurrence.

Structure:
  BOM + [FormFile] header
  [Dictionaries]
  [Form] x (1 + records.length)        — Item= refs only, no [Field]
  [Level]
  [Group] x (1 + records.length)       — wraps [Field]+[Text] per form
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from shared.form_layout_engine import (
    next_row_position, emit_field_block, emit_text_block, pick_capture_type,
    emit_level_block, emit_group_open, emit_group_close,
)


DICT_NAME   = "PATIENTSURVEY_DICT"
LEVEL_NAME  = "PATIENTSURVEY_LEVEL"
LEVEL_LABEL = "PatientSurvey Level"
FF_NAME     = "PATIENTSURVEY_FF"
FF_LABEL    = "PatientSurvey"
DCF_PATH    = HERE / "PatientSurvey.dcf"


def collect_items(record):
    for item in record.get("items", []):
        yield item
        for sub in item.get("subitems", []) or []:
            yield sub


def item_label(item):
    labels = item.get("labels") or []
    if labels and isinstance(labels[0], dict):
        return labels[0].get("text", "") or item.get("name", "")
    return item.get("label", item.get("name", ""))


def item_type(item):
    return item.get("contentType") or item.get("type", "numeric")


def all_id_items(level):
    """Return every ID-item dict for the level — supports both the
    multi-item case-ID block and the legacy single-item shape. CSPro 8.0
    accepts both."""
    ids = level.get("ids", {})
    if isinstance(ids, dict):
        return ids.get("items", []) or []
    if isinstance(ids, list):
        return ids
    return []


def main():
    if not DCF_PATH.exists():
        raise SystemExit(f"F3 DCF not found at {DCF_PATH} — run generate_dcf.py first")

    dcf = json.loads(DCF_PATH.read_text(encoding="utf-8"))
    valuesets = {vs["name"]: vs for vs in dcf.get("valueSets", [])}

    level = dcf["levels"][0]
    id_items = all_id_items(level)

    forms = []
    if id_items:
        forms.append(("FORM000", "(Id Items)", "IDS0_FORM", list(id_items)))
    for i, record in enumerate(level.get("records", [])):
        rec_items = list(collect_items(record))
        rec_label = item_label(record) or record["name"]
        rec_form_name  = f"FORM{i+1:03d}"
        rec_group_name = f"{record['name']}_FORM"
        forms.append((rec_form_name, rec_label, rec_group_name, rec_items))

    parts = []
    parts.append("[FormFile]\n")
    parts.append("Version=CSPro 8.0\n")
    parts.append(f"Name={FF_NAME}\n")
    parts.append(f"Label={FF_LABEL}\n")
    parts.append("DefaultTextFont=-013 0000 0000 0000 0700 0000 0000 0000 0000 0000 0000 0000 0000 Arial\n")
    parts.append("FieldEntryFont=0018 0000 0000 0000 0600 0000 0000 0000 0000 0000 0000 0000 0000 Courier New\n")
    parts.append("Type=SystemControlled\n")
    parts.append("  \n")
    parts.append("[Dictionaries]\n")
    parts.append(rf"File=.\{DCF_PATH.name}" + "\n")
    parts.append("  \n")

    # [Form] blocks
    for form_name, form_label, _group_name, items in forms:
        parts.append("[Form]\n")
        parts.append(f"Name={form_name}\n")
        parts.append(f"Label={form_label}\n")
        parts.append("Level=1\n")
        parts.append("Size=2700,3690\n")
        parts.append("  \n")
        for item in items:
            parts.append(f"Item={item['name']}\n")
        parts.append("  \n")
        parts.append("[EndForm]\n")
        parts.append("  \n")

    # [Level] + [Group] blocks
    parts.append(emit_level_block(LEVEL_NAME, LEVEL_LABEL))

    for form_index_zero_based, (_form_name, form_label, group_name, items) in enumerate(forms):
        form_index_1b = form_index_zero_based + 1
        # F3 has no occurring records (single patient per case); leave Max=1.
        # If a future spec change makes a record occurring (e.g., Q147/Q156
        # medication roster), read maximum from the source record here per
        # the 110_F3_listing pattern.
        max_occ = 1
        if form_index_zero_based > 0:
            src_rec = level.get("records", [])[form_index_zero_based - 1]
            occ = src_rec.get("occurrences", {})
            max_occ = occ.get("maximum", 1)
        parts.append(emit_group_open(group_name, form_label,
                                     form_index_one_based=form_index_1b,
                                     max_occurs=max_occ))

        prev_y = 0
        for item in items:
            name = item["name"]
            vs_ref = (item.get("valueSets") or [{}])[0] if item.get("valueSets") else None
            vs_name = (vs_ref or {}).get("name") if vs_ref else item.get("valueSet")
            vs_size = len(valuesets[vs_name].get("values", [])) if vs_name in valuesets else 0
            it_type = item_type(item)
            length = item.get("length", 0)
            ct = pick_capture_type(vs_size, it_type, length)
            field_w = 29 if ct == "RadioButton" else (970 if it_type == "alpha" else 200)
            pos = next_row_position(prev_y=prev_y, field_w=field_w)
            parts.append(emit_field_block(name, DICT_NAME, pos.field, ct, form_index=form_index_1b))
            qt = item_label(item) or name
            parts.append(emit_text_block(pos.text, qt))
            prev_y = pos.field.y

        parts.append(emit_group_close())

    body = "".join(parts)
    (HERE / "PatientSurvey.fmf").write_text("﻿" + body, encoding="utf-8")
    item_total = sum(len(f[3]) for f in forms)
    print(f"wrote PatientSurvey.fmf ({len(forms)} forms, {item_total} items, BOM-prefixed)")


if __name__ == "__main__":
    main()
