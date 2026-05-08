"""generate_fmf.py — emit FacilityHeadSurvey.fmf with full [Field]+[Text] blocks.

Reads:
  - FacilityHeadSurvey.dcf (canonical data dict, 671 items / 12 records)
  - F1.spec.md (verbatim question text per item, extracted from legacy hand-laid FMF)

Emits a complete .fmf with:
  - [Form] blocks for every record (one form per record; Designer can split later)
  - [Field] blocks for every item, with computed positions and capture types
  - [Text] blocks for every item, with verbatim question text
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from shared.form_layout_engine import (
    next_row_position, emit_field_block, emit_text_block, pick_capture_type,
)
from shared.question_text_loader import load_question_texts


DICT_NAME = "FACILITYHEADSURVEY_DICT"
DCF_PATH  = HERE / "FacilityHeadSurvey.dcf"
SPEC_PATH = HERE / "F1.spec.md"


def collect_items(record):
    """Yield every leaf item, including subitems if present."""
    for item in record.get("items", []):
        yield item
        for sub in item.get("subitems", []) or []:
            yield sub


def item_label(item: dict) -> str:
    """Get the first label text for an item. CSPro 8.0 stores labels as
    an array of {text: ..., language: ...} objects."""
    labels = item.get("labels") or []
    if labels and isinstance(labels[0], dict):
        return labels[0].get("text", "") or item.get("name", "")
    return item.get("label", item.get("name", ""))


def item_type(item: dict) -> str:
    """CSPro 8.0 uses contentType (alpha/numeric); some older shapes use type."""
    return item.get("contentType") or item.get("type", "numeric")


def first_id_item(level: dict) -> dict:
    """CSPro 8.0 wraps ids in {'items': [...]}; older shape was a list directly."""
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

    out = []
    out.append("[FormFile]")
    out.append("Version=CSPro 8.0")
    out.append("Name=FACILITYHEADSURVEY_FF")
    out.append("Label=FacilityHeadSurvey")
    out.append("DefaultTextFont=-013 0000 0000 0000 0700 0000 0000 0000 0000 0000 0000 0000 0000 Arial")
    out.append("FieldEntryFont=0018 0000 0000 0000 0600 0000 0000 0000 0000 0000 0000 0000 0000 Courier New")
    out.append("Type=SystemControlled")
    out.append("  ")
    out.append("[Dictionaries]")
    out.append(r"File=.\FacilityHeadSurvey.dcf")
    out.append("  ")

    # Walk the DCF: one form per record. ID record is "FORM000".
    forms = []
    level = dcf["levels"][0]
    id_item = first_id_item(level)
    if id_item:
        forms.append(("FORM000", "(Id Items)", [id_item]))
    for i, record in enumerate(level.get("records", []), start=1):
        record_items = list(collect_items(record))
        if not record_items:
            continue   # skip empty records (FACILITYHEADSURVEY_REC has 0 items)
        record_label = item_label(record) or record["name"]
        forms.append((f"FORM{i:03d}", record_label, record_items))

    # Form blocks
    for form_index, (form_name, form_label, items) in enumerate(forms):
        out.append("[Form]")
        out.append(f"Name={form_name}")
        out.append(f"Label={form_label}")
        out.append("Level=1")
        out.append("Size=2700,3690")
        out.append("  ")
        for item in items:
            out.append(f"Item={item['name']}")
        out.append("  ")
        out.append("[EndForm]")
        out.append("  ")

    # Field + Text blocks for every item across every form
    valuesets = {vs["name"]: vs for vs in dcf.get("valueSets", [])}
    for form_index, (form_name, form_label, items) in enumerate(forms):
        prev_y = 0
        for item in items:
            name = item["name"]
            # value set name lives in different shapes across CSPro 8.0 schemas
            vs_ref = (item.get("valueSets") or [{}])[0] if item.get("valueSets") else None
            vs_name = (vs_ref or {}).get("name") if vs_ref else item.get("valueSet")
            vs_size = len(valuesets[vs_name].get("values", [])) if vs_name in valuesets else 0
            it_type = item_type(item)
            length = item.get("length", 0)
            ct = pick_capture_type(vs_size, it_type, length)
            field_w = 29 if ct == "RadioButton" else (970 if it_type == "alpha" else 200)
            pos = next_row_position(prev_y=prev_y, field_w=field_w)
            out.append(emit_field_block(name, DICT_NAME, pos.field, ct, form_index=form_index))
            qt = qtexts.get(name) or item_label(item) or name
            out.append(emit_text_block(pos.text, qt))
            prev_y = pos.field.y

    (HERE / "FacilityHeadSurvey.fmf").write_text("\n".join(out), encoding="utf-8")
    print(f"wrote FacilityHeadSurvey.fmf ({len(forms)} forms, {sum(len(f[2]) for f in forms)} items)")


if __name__ == "__main__":
    main()
