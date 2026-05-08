"""generate_fmf.py — emit FacilityHeadSurvey.fmf in canonical CSPro 8.0 layout.

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
from shared.question_text_loader import load_question_texts


DICT_NAME = "FACILITYHEADSURVEY_DICT"
LEVEL_NAME  = "FACILITYHEADSURVEY_LEVEL"
LEVEL_LABEL = "FacilityHeadSurvey Level"
FF_NAME  = "FACILITYHEADSURVEY_FF"
FF_LABEL = "FacilityHeadSurvey"
DCF_PATH  = HERE / "FacilityHeadSurvey.dcf"
SPEC_PATH = HERE / "F1.spec.md"


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


def first_id_item(level):
    ids = level.get("ids", {})
    if isinstance(ids, dict):
        return ids.get("items", [{}])[0]
    if isinstance(ids, list) and ids:
        return ids[0]
    return {}


def main():
    if not DCF_PATH.exists():
        raise SystemExit(f"F1 DCF not found at {DCF_PATH} — run generate_dcf.py first")

    dcf = json.loads(DCF_PATH.read_text(encoding="utf-8"))
    qtexts = load_question_texts(SPEC_PATH) if SPEC_PATH.exists() else {}
    valuesets = {vs["name"]: vs for vs in dcf.get("valueSets", [])}

    level = dcf["levels"][0]
    id_item = first_id_item(level)

    # Build the form list. forms[i] = (form_name, form_label, group_name, items)
    # Group form_index_one_based = i+1 (1-indexed CSPro convention).
    forms = []
    if id_item:
        forms.append(("FORM000", "(Id Items)", "IDS0_FORM", [id_item]))
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
        parts.append(emit_group_open(group_name, form_label, form_index_one_based=form_index_1b))

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
            qt = qtexts.get(name) or item_label(item) or name
            parts.append(emit_text_block(pos.text, qt))
            prev_y = pos.field.y

        parts.append(emit_group_close())

    body = "".join(parts)
    (HERE / "FacilityHeadSurvey.fmf").write_text("﻿" + body, encoding="utf-8")
    item_total = sum(len(f[3]) for f in forms)
    print(f"wrote FacilityHeadSurvey.fmf ({len(forms)} forms, {item_total} items, BOM-prefixed)")


if __name__ == "__main__":
    main()
