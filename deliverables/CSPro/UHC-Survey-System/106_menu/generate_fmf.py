"""generate_fmf.py — emit menu_app.fmf (welcome screen, all fields protected)."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from shared.form_layout_engine import next_row_position, emit_field_block, emit_text_block

DICT_NAME = "MENU_DICT"
FORM_ITEMS = [
    ("MENU_LOGIN_ID",   "TextBox", "Logged in as (RA ID):"),
    ("MENU_LOGIN_NAME", "TextBox", "Name:"),
    ("MENU_ROLE",       "TextBox", "Role:"),
    ("MENU_SUP_ID",     "TextBox", "Supervisor ID:"),
    ("APP_VERSION",     "TextBox", "App version:"),
]


def main():
    out = []
    out.append("[FormFile]\nVersion=CSPro 8.0\nName=MENU_FF\nLabel=Menu")
    out.append("DefaultTextFont=-013 0000 0000 0000 0700 0000 0000 0000 0000 0000 0000 0000 0000 Arial")
    out.append("FieldEntryFont=0018 0000 0000 0000 0600 0000 0000 0000 0000 0000 0000 0000 0000 Courier New")
    out.append("Type=SystemControlled\n  \n[Dictionaries]\nFile=.\\menu_app.dcf\n  ")
    out.append("[Form]\nName=FORM000\nLabel=Menu\nLevel=1\nSize=2200,500\n  ")
    for n, _, _ in FORM_ITEMS:
        out.append(f"Item={n}")
    out.append("  \n[EndForm]\n  ")
    prev_y = 0
    for n, ct, qt in FORM_ITEMS:
        pos = next_row_position(prev_y=prev_y, field_w=970)
        out.append(emit_field_block(n, DICT_NAME, pos.field, ct, form_index=0))
        out.append(emit_text_block(pos.text, qt))
        prev_y = pos.field.y
    (HERE / "menu_app.fmf").write_text("\n".join(out), encoding="utf-8")
    print("wrote menu_app.fmf")


if __name__ == "__main__":
    main()
