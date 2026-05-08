"""generate_ent.py — emit login_app.ent + .ent.qsf + .ent.mgf."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

ENT = {
    "software": "CSPro", "version": 8.0, "fileType": "application",
    "type": "entry",
    "name": "LOGIN_APP", "label": "UHC Login",
    "dictionaries": [
        {"type": "input",    "path": "login_app.dcf", "parent": "login_app.fmf"},
        {"type": "external", "path": r"..\102_EXT_DIC\user_roster.dcf"},
    ],
    "forms": ["login_app.fmf"],
    "questionText": ["login_app.ent.qsf"],
    "code": [{"type": "main", "path": "login_app.ent.apc"}],
    "messages": ["login_app.ent.mgf"],
    "logicSettings": {"version": 2.0, "caseSensitive": {"symbols": False}},
    "properties": {
        "askOperatorId": False, "autoAdvanceOnSelection": False,
        "caseTree": "mobileOnly", "centerForms": False,
        "createListing": False, "createLog": False, "decimalMark": "dot",
        "displayCodesAlongsideLabels": False,
        "notes": {"delete": "all"},
    },
    "userSettings": [
        {"name": "csweb_url", "value": "PLACEHOLDER"},   # spliced by env_loader
        {"name": "expiration_days", "value": "30"},
    ],
}

(HERE / "login_app.ent").write_text(json.dumps(ENT, indent=2), encoding="utf-8")
(HERE / "login_app.ent.qsf").write_text("[QSF]\nVersion=CSPro 8.0\n", encoding="utf-8")
(HERE / "login_app.ent.mgf").write_text("[MessageFile]\nVersion=CSPro 8.0\n", encoding="utf-8")
print("wrote login_app.ent + .qsf + .mgf")
