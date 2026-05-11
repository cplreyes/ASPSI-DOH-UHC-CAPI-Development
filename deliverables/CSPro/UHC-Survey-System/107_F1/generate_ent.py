"""generate_ent.py — emit FacilityHeadSurvey.ent + .qsf + .mgf."""
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
    "type": "entry", "name": "FACILITYHEADSURVEY", "label": "FacilityHeadSurvey",
    "dictionaries": [
        {"type": "input", "path": "FacilityHeadSurvey.dcf", "parent": "FacilityHeadSurvey.fmf"},
    ],
    "forms": ["FacilityHeadSurvey.fmf"],
    "questionText": ["FacilityHeadSurvey.ent.qsf"],
    "code": [{"type": "main", "path": "FacilityHeadSurvey.ent.apc"}],
    "messages": ["FacilityHeadSurvey.ent.mgf"],
    "logicSettings": canonical_logic_settings(),
    "properties":    canonical_properties(),
    "userSettings": [
        {"name": "csweb_url", "value": "PLACEHOLDER"},
        {"name": "expiration_days", "value": "30"},
    ],
}

# Write .ent with explicit LF newlines so the gitattributes pin (text eol=lf)
# does not have to fight Python's universal-newline translation on Windows.
# CSPro 8.0 reads JSON .ent files line-ending-agnostically.
(HERE / "FacilityHeadSurvey.ent").write_text(
    json.dumps(ENT, indent=2), encoding="utf-8", newline="\n",
)
# .qsf and .mgf are CSPro Designer-owned (rewritten with CRLF on every save
# in Designer). Leave the initial generator-write as universal so subsequent
# Designer saves don't produce churn warnings on commit.
(HERE / "FacilityHeadSurvey.ent.qsf").write_text(QSF_TEMPLATE, encoding="utf-8")
(HERE / "FacilityHeadSurvey.ent.mgf").write_text(mgf_template("FacilityHeadSurvey"), encoding="utf-8")
print("wrote FacilityHeadSurvey.ent + .qsf + .mgf")
