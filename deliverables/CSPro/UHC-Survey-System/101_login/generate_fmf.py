"""generate_fmf.py — emit login_app.fmf using shared form_layout_engine."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from shared.form_layout_engine import (
    next_row_position, emit_field_block, emit_text_block,
)


DICT_NAME = "LOGIN_DICT"

# (item_name, capture_type, q_text)
FORM_ITEMS = [
    ("LOGIN_RA_ID",  "TextBox",     "Enter your RA ID:"),
    ("LOGIN_PW",     "TextBox",     "Enter your password:"),
    ("LOGIN_NAME",   "TextBox",     "Name:"),
    ("LOGIN_ROLE",   "RadioButton", "Role:"),
    ("APP_VERSION",  "TextBox",     "App version:"),
]


def main():
    out = []
    out.append("[FormFile]")
    out.append("Version=CSPro 8.0")
    out.append("Name=LOGIN_FF")
    out.append("Label=Login")
    out.append("DefaultTextFont=-013 0000 0000 0000 0700 0000 0000 0000 0000 0000 0000 0000 0000 Arial")
    out.append("FieldEntryFont=0018 0000 0000 0000 0600 0000 0000 0000 0000 0000 0000 0000 0000 Courier New")
    out.append("Type=SystemControlled")
    out.append("  ")
    out.append("[Dictionaries]")
    out.append(r"File=.\login_app.dcf")
    out.append("  ")
    out.append("[Form]")
    out.append("Name=FORM000")
    out.append("Label=Login")
    out.append("Level=1")
    out.append("Size=2200,500")
    out.append("  ")
    for name, _ct, _qt in FORM_ITEMS:
        out.append(f"Item={name}")
    out.append("  ")
    out.append("[EndForm]")
    out.append("  ")

    # [Field] + [Text] blocks
    prev_y = 0
    for name, capture_type, q_text in FORM_ITEMS:
        pos = next_row_position(prev_y=prev_y, field_w=29 if capture_type == "RadioButton" else 970)
        out.append(emit_field_block(name, DICT_NAME, pos.field, capture_type, form_index=0))
        out.append(emit_text_block(pos.text, q_text))
        prev_y = pos.field.y

    (HERE / "login_app.fmf").write_text("\n".join(out), encoding="utf-8")
    print("wrote login_app.fmf")


if __name__ == "__main__":
    main()
