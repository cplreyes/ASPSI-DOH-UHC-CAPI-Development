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
#
# RE-KEYED 2026-08-19 (Task 2.3, Aug-17 migration). Eight of these ten items were renumbered
# by the Aug-17 instrument; the old Apr-20 names below would have silently stopped matching
# (the script reports NOT FOUND rather than failing, so the overrides would just quietly
# stop applying). Mapped through instruments-aug17-extract/maps/F1-renames.csv:
#
#     Q9_UHC_HEARD             -> Q9_UHC_HEARD              (unchanged)
#     Q10_HAS_PRIMARY_PKG      -> Q10_HAS_PRIMARY_PKG       (unchanged)
#     Q16_HEALTH_PROMO_UNIT    -> Q13_HEALTH_PROMO_UNIT
#     Q35_STAFFING_CHANGED     -> Q24_STAFFING_CHANGED
#     Q138_ZBB_CURR            -> Q125_ZBB_CURR
#     Q139_ZBB_ALL_PATIENTS    -> Q126_ZBB_ALL_PATIENTS
#     Q141_ALLOW_OOP_BASIC     -> Q128_ALLOW_OOP_BASIC
#     Q145_MALASAKIT_PROVIDED  -> Q132_MALASAKIT_PROVIDED
#     Q148_LGU_SUPPORT         -> Q135_LGU_SUPPORT
#     Q150_LGU_SATISFIED       -> Q137_LGU_SATISFIED
#
# All ten verified present in the rebuilt dictionary, each carrying a BCL label slot on its
# EN "No" option. This override is still REQUIRED: the per-question values are NOT in
# translations/bcl.json - after the rebuild, Q9/Q10 read "Dai" there and the eight renamed
# items fall back to English "No" until Task 2.5 re-keys the locale files. Either way the
# cleared source says "Dae" for these ten, and only this map says so.
OVERRIDES = {
    item: {"No": {"BCL": "Dae"}}
    for item in (
        "Q9_UHC_HEARD",
        "Q10_HAS_PRIMARY_PKG",
        "Q13_HEALTH_PROMO_UNIT",
        "Q24_STAFFING_CHANGED",
        "Q125_ZBB_CURR",
        "Q126_ZBB_ALL_PATIENTS",
        "Q128_ALLOW_OOP_BASIC",
        "Q132_MALASAKIT_PROVIDED",
        "Q135_LGU_SUPPORT",
        "Q137_LGU_SATISFIED",
    )
}

# ---- #1229 / #1230: the Section C implementation-status options -- RETIRED 2026-08-19 ----
#
# These three per-question exceptions (Q12_PCB_LICENSING, Q17_HPU_CREATED, Q21_NEW_DEPTS)
# scoped two option labels out of the nine-option "UHC9" implementation-status set, because
# the build had propagated Q12's Bikol wording to all 22 Section C questions carrying it.
#
# The Aug-17 rebuild (Task 2.2) DELETED that structure. Section C is now a two-step battery:
# a plain Yes/No base plus a separate "<N>.1. If yes, was it a result of the UHC Act?" probe
# on a 6-option UHC_ATTRIB set whose option text is different wording entirely. Verified
# against the rebuilt FacilityHeadSurvey.dcf: the two English strings these exceptions keyed
# on --
#     "Yes, this has been implemented or improved recently, but not due to the UHC Act"
#     "No, this has not been implemented yet, but we plan to in the next 1-2 years"
# -- now occur ZERO times in the dictionary. There is nothing left to scope.
#
# The underlying problem is resolved rather than deferred: the 23 probes genuinely share ONE
# option set now, so one shared translation key is the CORRECT representation - which is what
# #1229/#1230 wanted and could not have while the wording was duplicated per question.


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
