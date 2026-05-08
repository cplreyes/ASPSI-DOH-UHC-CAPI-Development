"""generate_dcf.py — emit login_app.dcf per login_app.spec.md."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

DCF = {
    "software": "CSPro", "version": 8.0, "fileType": "dictionary",
    "name": "LOGIN_DICT", "label": "Login Dictionary",
    "valueSets": [
        {
            "name": "VS_ROLE_LABEL", "label": "Role",
            "values": [
                {"value": "1", "label": "Supervisor"},
                {"value": "2", "label": "Enumerator"},
                {"value": "3", "label": "Ops"},
            ],
        },
    ],
    "levels": [{
        "name": "LOGIN_LEVEL", "label": "Login Level",
        "ids": [{
            "name": "LOGIN_APP_ID", "label": "Login App ID",
            "type": "numeric", "length": 4, "zeroFill": True,
        }],
        "records": [{
            "name": "LOGIN_REC", "label": "Login Record",
            "recordType": "", "required": True,
            "items": [
                {"name": "LOGIN_RA_ID", "label": "RA ID",      "type": "numeric", "length": 4,  "zeroFill": True},
                {"name": "LOGIN_PW",    "label": "Password",   "type": "alpha",   "length": 40},
                {"name": "LOGIN_ROLE",  "label": "Role",       "type": "numeric", "length": 1, "valueSet": "VS_ROLE_LABEL"},
                {"name": "LOGIN_NAME",  "label": "Name",       "type": "alpha",   "length": 40},
                {"name": "APP_VERSION", "label": "App Version","type": "alpha",   "length": 16},
            ],
        }],
    }],
}

(HERE / "login_app.dcf").write_text(json.dumps(DCF, indent=2), encoding="utf-8")
print("wrote login_app.dcf")
