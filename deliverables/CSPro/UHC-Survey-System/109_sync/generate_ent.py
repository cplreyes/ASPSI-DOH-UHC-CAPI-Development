"""generate_ent.py — emit sync_F1_app.ent + .qsf + .mgf.

The .ent declares F1's primary dictionary as an external dictionary so
syncdata(PUT, FACILITYHEADSURVEY_DICT) inside the .apc resolves correctly.

Bootstrap note: this app is ONLY launched from menu_app's "Sync data to
server" choice, which appears after the user has at least navigated through
F1 once — so F1.csdb exists by the time sync_F1_app starts. If the user picks
Sync before any F1 case, CSPro will fail at startup on the missing external
data file; that's the documented degenerate case and is fine to surface as
an error.
"""
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
    "type": "entry", "name": "SYNC_F1_APP", "label": "UHC Sync F1",
    "dictionaries": [
        {"type": "input",    "path": "sync_F1_app.dcf", "parent": "sync_F1_app.fmf"},
        {"type": "external", "path": r"..\107_F1\FacilityHeadSurvey.dcf"},
    ],
    "forms": ["sync_F1_app.fmf"],
    "questionText": ["sync_F1_app.ent.qsf"],
    "code": [{"type": "main", "path": "sync_F1_app.ent.apc"}],
    "messages": ["sync_F1_app.ent.mgf"],
    "logicSettings": canonical_logic_settings(),
    "properties":    canonical_properties(),
    "userSettings": [
        {"name": "csweb_url", "value": "PLACEHOLDER"},
        {"name": "expiration_days", "value": "30"},
    ],
}

(HERE / "sync_F1_app.ent").write_text(json.dumps(ENT, indent=2), encoding="utf-8")
(HERE / "sync_F1_app.ent.qsf").write_text(QSF_TEMPLATE, encoding="utf-8")
(HERE / "sync_F1_app.ent.mgf").write_text(mgf_template("UHC Sync F1"), encoding="utf-8")
print("wrote sync_F1_app.ent + .qsf + .mgf")
