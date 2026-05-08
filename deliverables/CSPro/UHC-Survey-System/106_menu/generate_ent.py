"""generate_ent.py — emit menu_app.ent + .qsf + .mgf."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

ENT = {
    "software": "CSPro", "version": 8.0, "fileType": "application",
    "type": "entry", "name": "MENU_APP", "label": "UHC Menu",
    "dictionaries": [
        {"type": "input",    "path": "menu_app.dcf", "parent": "menu_app.fmf"},
        {"type": "external", "path": r"..\102_EXT_DIC\user_roster.dcf"},
    ],
    "forms": ["menu_app.fmf"],
    "questionText": ["menu_app.ent.qsf"],
    "code": [{"type": "main", "path": "menu_app.ent.apc"}],
    "messages": ["menu_app.ent.mgf"],
    "logicSettings": {"version": 2.0, "caseSensitive": {"symbols": False}},
    "properties": {
        "askOperatorId": False, "autoAdvanceOnSelection": False,
        "caseTree": "mobileOnly", "centerForms": False,
        "createListing": False, "createLog": False, "decimalMark": "dot",
        "displayCodesAlongsideLabels": False,
        "notes": {"delete": "all"},
    },
    "userSettings": [
        {"name": "csweb_url", "value": "PLACEHOLDER"},
        {"name": "expiration_days", "value": "30"},
    ],
}

(HERE / "menu_app.ent").write_text(json.dumps(ENT, indent=2), encoding="utf-8")
(HERE / "menu_app.ent.qsf").write_text("[QSF]\nVersion=CSPro 8.0\n", encoding="utf-8")
(HERE / "menu_app.ent.mgf").write_text("[MessageFile]\nVersion=CSPro 8.0\n", encoding="utf-8")
print("wrote menu_app.ent + .qsf + .mgf")
