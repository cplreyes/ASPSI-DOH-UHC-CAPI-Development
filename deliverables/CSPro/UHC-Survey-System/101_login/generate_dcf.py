"""generate_dcf.py — emit login_app.dcf per login_app.spec.md.

Uses the real CSPro 8.0 JSON schema:
  - ids:    {"items": [...]}                     (not a flat list)
  - labels: [{"text": "..."}]                    (not a flat label string)
  - items:  contentType (not type)
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
    "name": "LOGIN_DICT",
    "labels": [{"text": "Login Dictionary"}],
    "valueSets": [
        {
            "name": "VS_ROLE_LABEL",
            "labels": [{"text": "Role"}],
            "values": [
                {"value": "1", "labels": [{"text": "Supervisor"}]},
                {"value": "2", "labels": [{"text": "Enumerator"}]},
                {"value": "3", "labels": [{"text": "Ops"}]},
            ],
        },
    ],
    "levels": [{
        "name": "LOGIN_LEVEL",
        "labels": [{"text": "Login Level"}],
        "ids": {
            "items": [
                _item("LOGIN_APP_ID", "Login App ID", "numeric", 4, zeroFill=True),
            ],
        },
        "records": [{
            "name": "LOGIN_REC",
            "labels": [{"text": "Login Record"}],
            "recordType": "",
            "required": True,
            "occurrences": 1,
            "items": [
                _item("LOGIN_RA_ID", "RA ID",      "numeric", 4, zeroFill=True),
                _item("LOGIN_PW",    "Password",   "alpha",   40),
                _item("LOGIN_ROLE",  "Role",       "numeric", 1, valueSets=[{"name": "VS_ROLE_LABEL"}]),
                _item("LOGIN_NAME",  "Name",       "alpha",   40),
                _item("APP_VERSION", "App Version","alpha",   16),
            ],
        }],
    }],
}

(HERE / "login_app.dcf").write_text(json.dumps(DCF, indent=2), encoding="utf-8")
print("wrote login_app.dcf (CSPro 8.0 schema)")
