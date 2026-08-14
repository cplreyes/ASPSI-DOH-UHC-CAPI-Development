#!/usr/bin/env python3
r"""Per-question option labels for F1 - the fix for #1222 (Bikol "Dai" vs "Dae").

THE PROBLEM
-----------
cspro_helpers.apply_translations keys a value-set option on its BARE English text, and
cspro_helpers._value_set gives every option just that bare label. So `"No"` is ONE key
shared by all 36 yes/no value sets in F1, and the map physically cannot hold two different
translations for it.

The DOH-cleared June-5 Bikol questionnaire does not agree with itself across those
questions. Verified directly from official_translations.json, not from recollection:

    "Dae"  -> Q9, Q10, Q16, Q35, Q138, Q139, Q141, Q145, Q148, Q150   (10)
    "Dai"  -> Q13, Q37, Q51, Q54, Q55, Q56, Q59, Q61, Q77, Q81, Q88, Q89, Q90, Q93,
              Q97, Q101, Q102, Q107, Q108, Q109, Q112, Q116, Q118, Q135, Q136, Q157 (26)

The tester asked for a blanket change to "Dae" (#1222). Applied blanket it would fix 10
questions and break 26, so it is applied PER QUESTION instead. The inconsistency lives in
the approved questionnaire, not in the CAPI - flagged to ASPSI separately.

WHY A POST-PROCESSOR AND NOT A GENERATOR CHANGE
-----------------------------------------------
Teaching apply_translations about scoped keys would touch the file every instrument and
locale runs through, mid-review-round. This keeps the blast radius at one instrument and
one value set per entry, stays revertible, and follows the repo's existing idempotent
inject_*.py idiom. Run it after generate_dcf.py, before publishing.

Idempotent: it sets labels to a fixed target, so running it twice changes nothing the
second time. It only ever REPLACES the text of an existing label on an existing option -
never adds, removes or reorders options, so value codes cannot move.

    python inject_scoped_option_labels.py            # dry run
    python inject_scoped_option_labels.py --apply
"""
import argparse
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DCF = os.path.join(HERE, "FacilityHeadSurvey.dcf")

# item name -> english option -> { language code: cleared translation }
OVERRIDES = {
    item: {"No": {"BCL": "Dae"}}
    for item in (
        "Q9_UHC_HEARD",
        "Q10_HAS_PRIMARY_PKG",
        "Q16_HEALTH_PROMO_UNIT",
        "Q35_STAFFING_CHANGED",
        "Q138_ZBB_CURR",
        "Q139_ZBB_ALL_PATIENTS",
        "Q141_ALLOW_OOP_BASIC",
        "Q145_MALASAKIT_PROVIDED",
        "Q148_LGU_SUPPORT",
        "Q150_LGU_SATISFIED",
    )
}

# ---- #1229 / #1230: the Section C implementation-status options -------------------
#
# Same shared-key problem, opposite shape. 22 Section C questions carry these two options,
# and the build propagated **Q12's** wording to all of them - which is why the tablet
# disagrees with the paper form nearly everywhere.
#
# The cleared June-5 Bikol source actually says:
#   "Yes, ... not due to the UHC Act"  -> one wording on 20 questions; Q12 and Q17 differ
#   "No, ... plan to in the next 1-2 years" -> one wording on 19; Q12, Q17 and Q21 differ
#
# So the majority wording goes on the SHARED key in bcl.json (fixing 20 and 19 questions
# in one move, and matching what the tester asked for), and only the genuine exceptions
# are scoped here. Q17's "No" differs from Q12's by a trailing full stop; that is the
# cleared source's own artifact and is kept verbatim rather than tidied.
YES_OPT = "Yes, this has been implemented or improved recently, but not due to the UHC Act"
NO_OPT = "No, this has not been implemented yet, but we plan to in the next 1-2 years"

_SECTION_C_EXCEPTIONS = {
    "Q12_PCB_LICENSING": {
        YES_OPT: {"BCL": "Iyo, na implementar ini asin na-improve pero bako dahil sa UHC Act"},
        NO_OPT: {"BCL": "Dae pa ini naimplementar pero igwang plano sa mga masunod na 1-2 taon"},
    },
    "Q17_HPU_CREATED": {
        YES_OPT: {"BCL": "Iyo, na-implementar ini o na-improve pero bako dahil sa UHC Act"},
        NO_OPT: {"BCL": "Dae pa ini naimplementar pero igwang plano sa mga masunod na 1-2 taon."},
    },
    "Q21_NEW_DEPTS": {
        NO_OPT: {"BCL": "Dae pa ini naipatupad, pero igwang plano sa masunod na 1-2 taon"},
    },
}

for _item, _spec in _SECTION_C_EXCEPTIONS.items():
    OVERRIDES.setdefault(_item, {}).update(_spec)


def lab(node, code):
    for l in node.get("labels") or []:
        if l.get("language") == code:
            return l.get("text", "")
    return ""


def set_lab(node, code, text):
    for l in node.get("labels") or []:
        if l.get("language") == code:
            l["text"] = text
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    doc = json.loads(io.open(DCF, encoding="utf-8-sig").read())
    changes, hit_items = [], set()

    def visit(node):
        if isinstance(node, dict):
            nm = node.get("name")
            if nm in OVERRIDES and node.get("valueSets"):
                hit_items.add(nm)
                spec = OVERRIDES[nm]
                for vs in node["valueSets"]:
                    for v in vs.get("values") or []:
                        en = lab(v, "EN")
                        if en in spec:
                            for code, text in spec[en].items():
                                before = lab(v, code)
                                if before != text:
                                    changes.append((nm, en, code, before, text))
                                    if a.apply:
                                        set_lab(v, code, text)
            for k, val in node.items():
                visit(val)
        elif isinstance(node, list):
            for it in node:
                visit(it)

    visit(doc)
    missing = [nm for nm in OVERRIDES if nm not in hit_items]

    for nm, en, code, before, after in changes:
        print(f"  {nm:<28} [{code}] {en!r}: {before!r} -> {after!r}")
    print(f"\n{len(changes)} label(s) to change across {len(hit_items)}/{len(OVERRIDES)} items")
    if missing:
        # A renamed or removed item must be loud: silence would mean the fix quietly
        # stopped applying while still reporting success.
        print(f"  ! NOT FOUND in the dictionary: {', '.join(sorted(missing))}")

    if a.apply:
        if changes:
            # Match generate_dcf.py byte-for-byte in format: utf-8 with NO BOM and indent=2
            # (cspro_helpers writes `json.dumps(dictionary, indent=2)` as utf-8). Writing
            # utf-8-sig here added a BOM that made generate_qsf.py fail to parse the file.
            with io.open(DCF, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(doc, fh, indent=2)
            print(f"APPLIED -> {DCF}")
        else:
            print("nothing to do (already applied)")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
