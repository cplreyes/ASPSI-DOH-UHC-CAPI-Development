#!/usr/bin/env python3
r"""Look up what the DEPLOYED CAPI shows vs what the CLEARED June-5 questionnaire says.

Built for counter-checking tester tickets: a ticket names an instrument, a question and a
locale, and this prints both sides so the claim can be judged on evidence instead of
recollection.

    python lookup.py --instrument F1 --q 27 --locale BCL
    python lookup.py --instrument F1 --locale BCL --english "No"     # every match
    python lookup.py --instrument F1 --locale BCL --item Q34_DATA_REPORTS_USED
    python lookup.py --instrument F3 --locale HIL --grep "kabalo"    # search cleared text
"""
import argparse
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
CSPRO = os.path.abspath(os.path.join(HERE, "..", ".."))
OFFICIAL = os.path.join(HERE, "official_translations.json")
BASE = {"F1": "FacilityHeadSurvey", "F3": "PatientSurvey", "F4": "HouseholdSurvey"}
LABEL_Q = re.compile(r"^\s*(\d{1,3}(?:\.\d)?)\s*[\.\)]")
NAME_Q = re.compile(r"^Q(\d{1,3})(?:_(\d))?_")


def qnum_of(name, en):
    m = LABEL_Q.match(en or "")
    if m:
        return m.group(1)
    m = NAME_Q.match(name or "")
    if m:
        return m.group(1) + ("." + m.group(2) if m.group(2) else "")
    return None


def load_dcf(inst):
    return json.loads(io.open(os.path.join(CSPRO, inst, BASE[inst] + ".dcf"),
                              encoding="utf-8-sig").read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instrument", required=True, choices=list(BASE))
    ap.add_argument("--locale", required=True)
    ap.add_argument("--q")
    ap.add_argument("--item")
    ap.add_argument("--english")
    ap.add_argument("--grep")
    a = ap.parse_args()

    lg = a.locale.upper()
    off = json.loads(io.open(OFFICIAL, encoding="utf-8").read()).get(a.instrument, {})

    if a.grep:
        rx = re.compile(a.grep, re.I)
        print(f"--- cleared {a.instrument}/{lg} strings matching {a.grep!r} ---")
        for qn, e in off.items():
            d = e.get(lg) or {}
            for label, txt in [("stem", d.get("stem", ""))] + \
                              [(f"opt{i}", t) for i, t in enumerate(d.get("options", []))]:
                if txt and rx.search(txt):
                    print(f"  Q{qn} {label}: {txt[:110]}")
        return

    dcf = load_dcf(a.instrument)
    shown = 0
    for lvl in dcf["levels"]:
        for rec in lvl.get("records", []):
            for it in rec.get("items", []):
                nm = it["name"]
                labs = {l.get("language") or "EN": l.get("text", "")
                        for l in it.get("labels", [])}
                en = labs.get("EN", "")
                qn = qnum_of(nm, en)
                if a.item and a.item.upper() not in nm.upper():
                    continue
                if a.q and qn != a.q:
                    continue
                oe = off.get(qn, {})
                o_stem = (oe.get(lg) or {}).get("stem", "")
                o_opts = (oe.get(lg) or {}).get("options", [])
                en_opts = (oe.get("EN") or {}).get("options", [])

                if not a.english:
                    shown += 1
                    print(f"\n=== {nm}  (question {qn})")
                    print(f"  EN      : {en[:150]}")
                    print(f"  CAPI {lg}: {labs.get(lg, '') [:150] or '(English fallback)'}")
                    print(f"  CLEARED : {o_stem[:150] or '(none)'}")

                for vs in it.get("valueSets", []) or []:
                    for val in vs.get("values", []) or []:
                        vl = {l.get("language") or "EN": l.get("text", "")
                              for l in val.get("labels", [])}
                        ven = vl.get("EN", "")
                        if a.english and ven.strip().lower() != a.english.strip().lower():
                            continue
                        cleared = ""
                        for i, e in enumerate(en_opts):
                            if e.strip().lower() == ven.strip().lower() and i < len(o_opts):
                                cleared = o_opts[i]
                                break
                        shown += 1
                        print(f"  [opt] {nm} Q{qn} | EN {ven[:52]!r}")
                        print(f"        CAPI {lg}: {vl.get(lg, '')[:80]!r}")
                        print(f"        CLEARED : {cleared[:80]!r}")
    if not shown:
        print("(no match)")


if __name__ == "__main__":
    main()
