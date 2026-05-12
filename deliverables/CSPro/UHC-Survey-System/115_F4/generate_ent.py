"""generate_ent.py — emit HouseholdSurvey.ent + .qsf + .mgf.

Parallel to 107_F1/generate_ent.py + 110_F3_listing/generate_ent.py +
111_F3/generate_ent.py — same canonical .ent shape, same QSF/MGF template,
same .userSettings placeholders spliced by env_loader at build time.

F4-specific addition: F4LISTING_DICT declared as a second dictionary entry
with type="external". This wires the (future) 113_F4_listing app's
F4Listing.dcf into F4's runtime so the FIELD_CONTROL.preproc handler can
call loadcase() / forcase() against the listing app's roster occurrences
to:

  1. Look up eligible households for the current barangay listing session
     (LISTING_NO unused-and-eligible-for-F4).
  2. Stamp F4_STATUS = 2 (in-progress) on the chosen roster row at
     case-open, F4_STATUS = 1 (completed) on case-save, and
     F4_STATUS = 3 (refused-at-F4) on documented refusal.

Per CSPro 8.0 Users Guide -> Dictionaries -> External Dictionaries: a
type="external" dict entry exposes the named records to the entry app's
logic via the standard dictionary symbol table (the dict name becomes a
reserved symbol you can pass to loadcase()/forcase()).

IMPORTANT — STUBBED DEPENDENCY:
The 113_F4_listing app does not yet exist (held over for the F4 listing
phase; see CLAUDE memo project_f4_rebuild_2026_05_12.md). To keep the F4
.ent buildable + the household-pick wiring in place for when the listing
app lands, we declare the EXTERNAL dictionary path as
'../113_F4_listing/F4Listing.dcf'. CSPro Designer's F7 publish step will
fail until the path resolves -- the smoke test pins the declaration so
the wiring stays correct; the runtime activation lands at the F4 listing
phase (task #7 in the F4 rebuild plan).

Documented in F4-Skip-Logic-and-Validations.md §5 (Open Questions); the
.apc household-pick PROC is stubbed in commit 9 of this F4 quartet build
to allow manual HH_LISTING_NO entry while 113_F4_listing is pending.
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
    "type": "entry", "name": "HOUSEHOLDSURVEY", "label": "HouseholdSurvey",
    "dictionaries": [
        {"type": "input", "path": "HouseholdSurvey.dcf", "parent": "HouseholdSurvey.fmf"},
        # F4LISTING_DICT — EXTERNAL dictionary for household-pick at case
        # open. See module docstring for the loadcase()/forcase() handshake
        # and the stubbed-until-113_F4_listing-lands caveat.
        {"type": "external", "path": "../113_F4_listing/F4Listing.dcf"},
    ],
    "forms": ["HouseholdSurvey.fmf"],
    "questionText": ["HouseholdSurvey.ent.qsf"],
    "code": [{"type": "main", "path": "HouseholdSurvey.ent.apc"}],
    "messages": ["HouseholdSurvey.ent.mgf"],
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
(HERE / "HouseholdSurvey.ent").write_text(
    json.dumps(ENT, indent=2), encoding="utf-8", newline="\n",
)
# .qsf and .mgf are CSPro Designer-owned (rewritten with CRLF on every save
# in Designer). Leave the initial generator-write as universal so subsequent
# Designer saves don't produce churn warnings on commit.
(HERE / "HouseholdSurvey.ent.qsf").write_text(QSF_TEMPLATE, encoding="utf-8")
(HERE / "HouseholdSurvey.ent.mgf").write_text(mgf_template("HouseholdSurvey"), encoding="utf-8")
print("wrote HouseholdSurvey.ent + .qsf + .mgf")
