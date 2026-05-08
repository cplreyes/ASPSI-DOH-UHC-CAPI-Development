"""generate_fmf.py — emit menu_app.fmf in canonical CSPro 8.0 layout."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from shared.form_layout_engine import (
    next_row_position, emit_field_block, emit_text_block,
    emit_level_block, emit_group_open, emit_group_close,
)


DICT_NAME = "MENU_DICT"

ID_ITEMS = [("MENU_APP_ID", "TextBox", "Menu App ID")]

RECORD_ITEMS = [
    ("MENU_LOGIN_ID",   "TextBox", "Logged in as (RA ID):"),
    ("MENU_LOGIN_NAME", "TextBox", "Name:"),
    ("MENU_ROLE",       "TextBox", "Role:"),
    ("MENU_SUP_ID",     "TextBox", "Supervisor ID:"),
    ("APP_VERSION",     "TextBox", "App version:"),
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
    parts.append("Name=MENU_FF\n")
    parts.append("Label=MenuDictionary\n")
    parts.append("DefaultTextFont=-013 0000 0000 0000 0700 0000 0000 0000 0000 0000 0000 0000 0000 Arial\n")
    parts.append("FieldEntryFont=0018 0000 0000 0000 0600 0000 0000 0000 0000 0000 0000 0000 0000 Courier New\n")
    parts.append("Type=SystemControlled\n")
    parts.append("  \n")
    parts.append("[Dictionaries]\n")
    parts.append(r"File=.\menu_app.dcf" + "\n")
    parts.append("  \n")

    parts.append(emit_form_block("FORM000", "(Id Items)",        ID_ITEMS))
    parts.append(emit_form_block("FORM001", "MenuDictionary Record", []))
    parts.append(emit_form_block("FORM002", "Menu",              RECORD_ITEMS))

    parts.append(emit_level_block("MENU_LEVEL", "MenuDictionary Level"))

    parts.append(emit_group_open("IDS0_FORM", "(Id Items)", form_index_one_based=1))
    prev_y = 0
    for name, ct, qt in ID_ITEMS:
        pos = next_row_position(prev_y=prev_y, field_w=200)
        parts.append(emit_field_block(name, DICT_NAME, pos.field, ct, form_index=1))
        parts.append(emit_text_block(pos.text, qt))
        prev_y = pos.field.y
    parts.append(emit_group_close())

    parts.append(emit_group_open("MENU_REC_FORM", "MenuDictionary Record", form_index_one_based=2))
    parts.append(emit_group_close())

    parts.append(emit_group_open("MENU_REC_DATA", "Menu", form_index_one_based=3))
    prev_y = 0
    for name, ct, qt in RECORD_ITEMS:
        pos = next_row_position(prev_y=prev_y, field_w=970)
        parts.append(emit_field_block(name, DICT_NAME, pos.field, ct, form_index=3))
        parts.append(emit_text_block(pos.text, qt))
        prev_y = pos.field.y
    parts.append(emit_group_close())

    body = "".join(parts)
    (HERE / "menu_app.fmf").write_text("﻿" + body, encoding="utf-8")
    print(f"wrote menu_app.fmf ({body.count(chr(10))} lines, BOM-prefixed)")


if __name__ == "__main__":
    main()
