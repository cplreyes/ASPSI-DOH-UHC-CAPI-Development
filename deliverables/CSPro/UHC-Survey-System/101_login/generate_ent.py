"""generate_ent.py — emit login_app.ent + .ent.qsf + .ent.mgf."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from shared.ent_template import canonical_logic_settings, canonical_properties


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
    "logicSettings": canonical_logic_settings(),
    "properties":    canonical_properties(),
    "userSettings": [
        {"name": "csweb_url", "value": "PLACEHOLDER"},   # spliced by env_loader
        {"name": "expiration_days", "value": "30"},
    ],
}

(HERE / "login_app.ent").write_text(json.dumps(ENT, indent=2), encoding="utf-8")
(HERE / "login_app.ent.qsf").write_text("[QSF]\nVersion=CSPro 8.0\n", encoding="utf-8")
(HERE / "login_app.ent.mgf").write_text("[MessageFile]\nVersion=CSPro 8.0\n", encoding="utf-8")
print("wrote login_app.ent + .qsf + .mgf")
