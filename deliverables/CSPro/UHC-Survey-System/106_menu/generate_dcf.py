"""generate_dcf.py — emit menu_app.dcf per menu_app.spec.md."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

DCF = {
    "software": "CSPro", "version": 8.0, "fileType": "dictionary",
    "name": "MENU_DICT", "label": "Menu Dictionary",
    "valueSets": [],
    "levels": [{
        "name": "MENU_LEVEL", "label": "Menu Level",
        "ids": [{"name": "MENU_APP_ID", "label": "Menu App ID", "type": "numeric", "length": 4, "zeroFill": True}],
        "records": [{
            "name": "MENU_REC", "label": "Menu Record",
            "recordType": "", "required": True,
            "items": [
                {"name": "MENU_LOGIN_ID",   "label": "Login ID",      "type": "numeric", "length": 4, "zeroFill": True},
                {"name": "MENU_LOGIN_NAME", "label": "Login Name",    "type": "alpha",   "length": 40},
                {"name": "MENU_ROLE",       "label": "Role",          "type": "numeric", "length": 1},
                {"name": "MENU_SUP_ID",     "label": "Supervisor ID", "type": "numeric", "length": 4, "zeroFill": True},
                {"name": "APP_VERSION",     "label": "App Version",   "type": "alpha",   "length": 16},
            ],
        }],
    }],
}

(HERE / "menu_app.dcf").write_text(json.dumps(DCF, indent=2), encoding="utf-8")
print("wrote menu_app.dcf")
