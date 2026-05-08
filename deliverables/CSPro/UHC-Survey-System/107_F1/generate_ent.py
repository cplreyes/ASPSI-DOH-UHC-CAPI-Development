"""generate_ent.py — emit FacilityHeadSurvey.ent + .qsf + .mgf."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

ENT = {
    "software": "CSPro", "version": 8.0, "fileType": "application",
    "type": "entry", "name": "FACILITYHEADSURVEY", "label": "F1 Facility Head Survey",
    "dictionaries": [
        {"type": "input", "path": "FacilityHeadSurvey.dcf", "parent": "FacilityHeadSurvey.fmf"},
    ],
    "forms": ["FacilityHeadSurvey.fmf"],
    "questionText": ["FacilityHeadSurvey.ent.qsf"],
    "code": [{"type": "main", "path": "FacilityHeadSurvey.ent.apc"}],
    "messages": ["FacilityHeadSurvey.ent.mgf"],
    "logicSettings": {"version": 2.0, "caseSensitive": {"symbols": False}},
    "properties": {
        "askOperatorId": False, "autoAdvanceOnSelection": False,
        "caseTree": "mobileOnly", "centerForms": False,
        "createListing": False, "createLog": True, "decimalMark": "dot",
        "displayCodesAlongsideLabels": False,
        "notes": {"delete": "all"},
    },
    "userSettings": [
        {"name": "csweb_url", "value": "PLACEHOLDER"},
        {"name": "expiration_days", "value": "30"},
    ],
}

(HERE / "FacilityHeadSurvey.ent").write_text(json.dumps(ENT, indent=2), encoding="utf-8")
(HERE / "FacilityHeadSurvey.ent.qsf").write_text("[QSF]\nVersion=CSPro 8.0\n", encoding="utf-8")
(HERE / "FacilityHeadSurvey.ent.mgf").write_text("[MessageFile]\nVersion=CSPro 8.0\n", encoding="utf-8")
print("wrote FacilityHeadSurvey.ent + .qsf + .mgf")
