"""generate_ent.py — emit menu_app.ent + .qsf + .mgf."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from shared.ent_template import (
    canonical_logic_settings, canonical_properties, QSF_TEMPLATE, mgf_template,
)


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
    "logicSettings": canonical_logic_settings(),
    "properties":    canonical_properties(),
    "userSettings": [
        {"name": "csweb_url", "value": "PLACEHOLDER"},
        {"name": "expiration_days", "value": "30"},
    ],
}

(HERE / "menu_app.ent").write_text(json.dumps(ENT, indent=2), encoding="utf-8")
(HERE / "menu_app.ent.qsf").write_text(QSF_TEMPLATE, encoding="utf-8")
(HERE / "menu_app.ent.mgf").write_text(mgf_template("UHC Menu"), encoding="utf-8")
print("wrote menu_app.ent + .qsf + .mgf")
