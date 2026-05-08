"""generate_dcf.py — emit menu_app.dcf per menu_app.spec.md.

Uses the real CSPro 8.0 JSON schema (see 101_login/generate_dcf.py for the
canonical pattern reference).
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _item(name, label_text, content_type, length, **kwargs):
    item = {
        "name": name,
        "labels": [{"text": label_text}],
        "contentType": content_type,
        "length": length,
    }
    item.update(kwargs)
    return item


DCF = {
    "software": "CSPro", "version": 8.0, "fileType": "dictionary",
    "name": "MENU_DICT",
    "labels": [{"text": "Menu Dictionary"}],
    "valueSets": [],
    "levels": [{
        "name": "MENU_LEVEL",
        "labels": [{"text": "Menu Level"}],
        "ids": {
            "items": [
                _item("MENU_APP_ID", "Menu App ID", "numeric", 4, zeroFill=True),
            ],
        },
        "records": [{
            "name": "MENU_REC",
            "labels": [{"text": "Menu Record"}],
            "recordType": "",
            "required": True,
            "occurrences": 1,
            "items": [
                _item("MENU_LOGIN_ID",   "Login ID",      "numeric", 4, zeroFill=True),
                _item("MENU_LOGIN_NAME", "Login Name",    "alpha",   40),
                _item("MENU_ROLE",       "Role",          "numeric", 1),
                _item("MENU_SUP_ID",     "Supervisor ID", "numeric", 4, zeroFill=True),
                _item("APP_VERSION",     "App Version",   "alpha",   16),
            ],
        }],
    }],
}

(HERE / "menu_app.dcf").write_text(json.dumps(DCF, indent=2), encoding="utf-8")
print("wrote menu_app.dcf (CSPro 8.0 schema)")
