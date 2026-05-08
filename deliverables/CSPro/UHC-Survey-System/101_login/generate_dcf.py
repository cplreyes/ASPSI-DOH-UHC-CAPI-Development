"""generate_dcf.py — emit login_app.dcf using shared cspro_helpers.

Uses the canonical CSPro 8.0 schema produced by build_dictionary().
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared"))

from cspro_helpers import (
    numeric, alpha, select_one, record, build_dictionary, write_dcf,
)


ROLE_OPTIONS = [
    ("Supervisor", "1"),
    ("Enumerator", "2"),
    ("Ops",        "3"),
]


login_rec = record(
    name="LOGIN_REC", label="Login Record", record_type="",
    items=[
        numeric("LOGIN_RA_ID", "RA ID",      length=4, zero_fill=True),
        alpha  ("LOGIN_PW",    "Password",   length=40),
        select_one("LOGIN_ROLE", "Role",      ROLE_OPTIONS, length=1),
        alpha  ("LOGIN_NAME",  "Name",       length=40),
        alpha  ("APP_VERSION", "App Version",length=16),
    ],
)

dictionary = build_dictionary(
    dict_name="LOGIN_DICT",
    dict_label="LoginDictionary",
    id_item_name="LOGIN_APP_ID",
    id_item_label="Login App ID",
    id_length=4,
    records=[login_rec],
)

write_dcf(dictionary, HERE / "login_app.dcf")
