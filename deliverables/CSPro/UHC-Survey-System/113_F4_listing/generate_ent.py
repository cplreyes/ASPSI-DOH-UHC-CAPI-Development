"""generate_ent.py — emit F4Listing.ent + .qsf + .mgf.

Parallel to 107_F1/generate_ent.py + 110_F3_listing/generate_ent.py +
111_F3/generate_ent.py + 115_F4/generate_ent.py — same canonical .ent
shape, same QSF/MGF template, same .userSettings placeholders spliced
by env_loader at build time.

The F4 listing app is a self-contained entry app — its output is the
F4LISTING_DICT case file (one per barangay-day session). It does NOT
declare any EXTERNAL dictionary references; the consumer (115_F4) is
the one declaring F4LISTING_DICT as EXTERNAL.

Per CSPro 8.0 Users Guide -> Dictionaries -> External Dictionaries: a
type="external" dict entry exposes the named records to the entry app's
logic via the standard dictionary symbol table (the dict name becomes a
reserved symbol you can pass to loadcase()/forcase()).
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
    "type": "entry", "name": "F4LISTING", "label": "F4Listing",
    "dictionaries": [
        {"type": "input", "path": "F4Listing.dcf", "parent": "F4Listing.fmf"},
    ],
    "forms": ["F4Listing.fmf"],
    "questionText": ["F4Listing.ent.qsf"],
    "code": [{"type": "main", "path": "F4Listing.ent.apc"}],
    "messages": ["F4Listing.ent.mgf"],
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
(HERE / "F4Listing.ent").write_text(
    json.dumps(ENT, indent=2), encoding="utf-8", newline="\n",
)
# .qsf and .mgf are CSPro Designer-owned (rewritten with CRLF on every save
# in Designer). Leave the initial generator-write as universal so subsequent
# Designer saves don't produce churn warnings on commit.
(HERE / "F4Listing.ent.qsf").write_text(QSF_TEMPLATE, encoding="utf-8")
(HERE / "F4Listing.ent.mgf").write_text(mgf_template("F4Listing"), encoding="utf-8")
print("wrote F4Listing.ent + .qsf + .mgf")
