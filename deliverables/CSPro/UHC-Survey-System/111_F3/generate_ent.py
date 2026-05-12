"""generate_ent.py — emit PatientSurvey.ent + .qsf + .mgf.

Parallel to 107_F1/generate_ent.py + 110_F3_listing/generate_ent.py — same
canonical .ent shape, same QSF/MGF template, same .userSettings placeholders
spliced by env_loader at build time.

F3-specific addition: PATIENTLISTING_DICT declared as a second dictionary
entry with type="external". This wires the 110_F3_listing app's
PatientListing.dcf into F3's runtime so the FIELD_CONTROL.preproc handler
(see generate_apc.py, commit 5) can call loadcase() / forcase() against
the listing app's roster occurrences to:

  1. Look up eligible patients for the current facility-day
     (LISTING_TAG=1 AND F3_STATUS=0 — pending-and-eligible-for-F3).
  2. Stamp F3_STATUS = 2 (in-progress) on the chosen roster row at
     case-open, F3_STATUS = 1 (completed) on case-save, and
     F3_STATUS = 3 (refused-at-F3) on documented refusal.
  3. Stamp ASSIGNED_F3_CASE_SEQ on the roster row with the CASE_SEQ
     allocated to the new F3 case, so the listing app's replacement-
     protocol cycle engine can see which roster slots have been
     consumed.

Per CSPro 8.0 Users Guide -> Dictionaries -> External Dictionaries: a
type="external" dict entry exposes the named records to the entry app's
logic via the standard dictionary symbol table (the dict name becomes a
reserved symbol you can pass to loadcase()/forcase()). The DCF file lives
in the sibling 110_F3_listing/ folder; the relative path here is resolved
by Designer at F7 publish time. The compiled .pen bundles a snapshot of
the external dict's structure; runtime data still reads from the tablet's
local .csdb path (set via setfile()/the SYNC.md sync flow that lands the
listing .csdb on the same tablet).
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
    "type": "entry", "name": "PATIENTSURVEY", "label": "PatientSurvey",
    "dictionaries": [
        {"type": "input", "path": "PatientSurvey.dcf", "parent": "PatientSurvey.fmf"},
        # PATIENTLISTING_DICT — EXTERNAL dictionary for patient-pick at case
        # open. See module docstring for the loadcase()/forcase() handshake.
        {"type": "external", "path": "../110_F3_listing/PatientListing.dcf"},
    ],
    "forms": ["PatientSurvey.fmf"],
    "questionText": ["PatientSurvey.ent.qsf"],
    "code": [{"type": "main", "path": "PatientSurvey.ent.apc"}],
    "messages": ["PatientSurvey.ent.mgf"],
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
(HERE / "PatientSurvey.ent").write_text(
    json.dumps(ENT, indent=2), encoding="utf-8", newline="\n",
)
# .qsf and .mgf are CSPro Designer-owned (rewritten with CRLF on every save
# in Designer). Leave the initial generator-write as universal so subsequent
# Designer saves don't produce churn warnings on commit.
(HERE / "PatientSurvey.ent.qsf").write_text(QSF_TEMPLATE, encoding="utf-8")
(HERE / "PatientSurvey.ent.mgf").write_text(mgf_template("PatientSurvey"), encoding="utf-8")
print("wrote PatientSurvey.ent + .qsf + .mgf")
