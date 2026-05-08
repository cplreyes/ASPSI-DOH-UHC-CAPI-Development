"""generate_fmf.py — emit login_app.fmf in canonical CSPro 8.0 layout.

Structure (matches legacy F1.fmf shape Designer accepts):
  BOM + [FormFile] + [Dictionaries]
  [Form] FORM000 (Id Items)        — only Item= refs, no fields
  [Form] FORM001 (LOGIN_REC wrap)  — empty, level wrapper
  [Form] FORM002 (LOGIN_REC data)  — with Item= refs for the 5 record items
  [Level] LOGIN_LEVEL
    [Group] IDS0_FORM    Form=1   — wraps the LOGIN_APP_ID [Field]+[Text]
    [Group] LOGIN_REC_FORM Form=2 — empty wrapper
    [Group] LOGIN_REC_DATA Form=3 — wraps the 5 record [Field]+[Text] blocks
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from shared.form_layout_engine import (
    next_row_position, emit_field_block, emit_text_block,
    emit_level_block, emit_group_open, emit_group_close,
)


DICT_NAME = "LOGIN_DICT"

# ID items go on FORM000 alone
ID_ITEMS = [("LOGIN_APP_ID", "TextBox", "Login App ID")]

# Record items go on FORM002 (FORM001 is the empty record wrapper)
RECORD_ITEMS = [
    ("LOGIN_RA_ID",  "TextBox",     "Enter your RA ID:"),
    ("LOGIN_PW",     "TextBox",     "Enter your password:"),
    ("LOGIN_NAME",   "TextBox",     "Name:"),
    ("LOGIN_ROLE",   "RadioButton", "Role:"),
    ("APP_VERSION",  "TextBox",     "App version:"),
]


def emit_form_block(name: str, label: str, items: list) -> str:
    """Emit a single [Form] section listing item names only."""
    out = [
        "[Form]",
        f"Name={name}",
        f"Label={label}",
        "Level=1",
        "Size=2200,500",
        "  ",
    ]
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
    parts.append("Name=LOGIN_FF\n")
    parts.append("Label=LoginDictionary\n")
    parts.append("DefaultTextFont=-013 0000 0000 0000 0700 0000 0000 0000 0000 0000 0000 0000 0000 Arial\n")
    parts.append("FieldEntryFont=0018 0000 0000 0000 0600 0000 0000 0000 0000 0000 0000 0000 0000 Courier New\n")
    parts.append("Type=SystemControlled\n")
    parts.append("  \n")
    parts.append("[Dictionaries]\n")
    parts.append(r"File=.\login_app.dcf" + "\n")
    parts.append("  \n")

    # Forms — one per logical group
    parts.append(emit_form_block("FORM000", "(Id Items)",     ID_ITEMS))
    parts.append(emit_form_block("FORM001", "LoginDictionary Record", []))
    parts.append(emit_form_block("FORM002", "Login",          RECORD_ITEMS))

    # Level + Groups
    parts.append(emit_level_block("LOGIN_LEVEL", "LoginDictionary Level"))

    # Group 1: ID items (Form=1 -> FORM000)
    parts.append(emit_group_open("IDS0_FORM", "(Id Items)", form_index_one_based=1))
    prev_y = 0
    for name, capture_type, q_text in ID_ITEMS:
        pos = next_row_position(prev_y=prev_y, field_w=200)
        parts.append(emit_field_block(name, DICT_NAME, pos.field, capture_type, form_index=1))
        parts.append(emit_text_block(pos.text, q_text))
        prev_y = pos.field.y
    parts.append(emit_group_close())

    # Group 2: empty record wrapper (Form=2 -> FORM001)
    parts.append(emit_group_open("LOGIN_REC_FORM", "LoginDictionary Record", form_index_one_based=2))
    parts.append(emit_group_close())

    # Group 3: the actual 5 record fields (Form=3 -> FORM002)
    parts.append(emit_group_open("LOGIN_REC_DATA", "Login", form_index_one_based=3))
    prev_y = 0
    for name, capture_type, q_text in RECORD_ITEMS:
        pos = next_row_position(prev_y=prev_y, field_w=29 if capture_type == "RadioButton" else 970)
        parts.append(emit_field_block(name, DICT_NAME, pos.field, capture_type, form_index=3))
        parts.append(emit_text_block(pos.text, q_text))
        prev_y = pos.field.y
    parts.append(emit_group_close())

    # Write with UTF-8 BOM
    body = "".join(parts)
    (HERE / "login_app.fmf").write_text("﻿" + body, encoding="utf-8")
    print(f"wrote login_app.fmf ({body.count(chr(10))} lines, BOM-prefixed)")


if __name__ == "__main__":
    main()
