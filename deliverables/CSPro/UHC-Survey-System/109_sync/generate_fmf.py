"""generate_fmf.py — emit sync_F1_app.fmf in canonical CSPro 8.0 layout.

The sync app's primary dict has one field (SYNC_STATUS). The form is minimal —
preproc fires sync + endlevel, so the user never lands on a field. CSPro still
requires the .fmf to be well-formed (level + IDs + record form).
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from shared.form_layout_engine import (
    next_row_position, emit_field_block, emit_text_block,
    emit_level_block, emit_group_open, emit_group_close,
)


DICT_NAME = "SYNC_DICT"

ID_ITEMS = [("SYNC_APP_ID", "TextBox", "Sync App ID")]

RECORD_ITEMS = [
    ("SYNC_STATUS", "TextBox", "Status:"),
]


def emit_form_block(name: str, label: str, items: list) -> str:
    out = ["[Form]", f"Name={name}", f"Label={label}", "Level=1", "Size=2200,500", "  "]
    for item_name, _, _ in items:
        out.append(f"Item={item_name}")
    out.append("  ")
    out.append("[EndForm]")
    out.append("  ")
    return "\n".join(out) + "\n"


def main():
    parts = []
    parts.append("[FormFile]\n")
    parts.append("Version=CSPro 8.0\n")
    parts.append("Name=SYNC_FF\n")
    parts.append("Label=SyncDictionary\n")
    parts.append("DefaultTextFont=-013 0000 0000 0000 0700 0000 0000 0000 0000 0000 0000 0000 0000 Arial\n")
    parts.append("FieldEntryFont=0018 0000 0000 0000 0600 0000 0000 0000 0000 0000 0000 0000 0000 Courier New\n")
    parts.append("Type=SystemControlled\n")
    parts.append("  \n")
    parts.append("[Dictionaries]\n")
    parts.append(r"File=.\sync_F1_app.dcf" + "\n")
    parts.append("  \n")

    parts.append(emit_form_block("FORM000", "(Id Items)",        ID_ITEMS))
    parts.append(emit_form_block("FORM001", "SyncDictionary Record", []))
    parts.append(emit_form_block("FORM002", "Sync",              RECORD_ITEMS))

    parts.append(emit_level_block("SYNC_LEVEL", "SyncDictionary Level"))

    parts.append(emit_group_open("IDS0_FORM", "(Id Items)", form_index_one_based=1))
    prev_y = 0
    for name, ct, qt in ID_ITEMS:
        pos = next_row_position(prev_y=prev_y, field_w=200)
        parts.append(emit_field_block(name, DICT_NAME, pos.field, ct, form_index=1))
        parts.append(emit_text_block(pos.text, qt))
        prev_y = pos.field.y
    parts.append(emit_group_close())

    parts.append(emit_group_open("SYNC_REC_FORM", "SyncDictionary Record", form_index_one_based=2))
    parts.append(emit_group_close())

    parts.append(emit_group_open("SYNC_REC_DATA", "Sync", form_index_one_based=3))
    prev_y = 0
    for name, ct, qt in RECORD_ITEMS:
        pos = next_row_position(prev_y=prev_y, field_w=970)
        parts.append(emit_field_block(name, DICT_NAME, pos.field, ct, form_index=3))
        parts.append(emit_text_block(pos.text, qt))
        prev_y = pos.field.y
    parts.append(emit_group_close())

    body = "".join(parts)
    (HERE / "sync_F1_app.fmf").write_text("﻿" + body, encoding="utf-8")
    print(f"wrote sync_F1_app.fmf ({body.count(chr(10))} lines, BOM-prefixed)")


if __name__ == "__main__":
    main()
