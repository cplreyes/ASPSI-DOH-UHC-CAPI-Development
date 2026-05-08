"""generate_dcf.py — emit menu_app.dcf using shared cspro_helpers."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared"))

from cspro_helpers import numeric, alpha, record, build_dictionary, write_dcf


menu_rec = record(
    name="MENU_REC", label="Menu Record", record_type="M",
    items=[
        numeric("MENU_LOGIN_ID",   "Login ID",      length=4, zero_fill=True),
        alpha  ("MENU_LOGIN_NAME", "Login Name",    length=40),
        numeric("MENU_ROLE",       "Role",          length=1),
        numeric("MENU_SUP_ID",     "Supervisor ID", length=4, zero_fill=True),
        alpha  ("APP_VERSION",     "App Version",   length=16),
    ],
)

dictionary = build_dictionary(
    dict_name="MENU_DICT",
    dict_label="MenuDictionary",
    id_item_name="MENU_APP_ID",
    id_item_label="Menu App ID",
    id_length=4,
    records=[menu_rec],
)

write_dcf(dictionary, HERE / "menu_app.dcf")
