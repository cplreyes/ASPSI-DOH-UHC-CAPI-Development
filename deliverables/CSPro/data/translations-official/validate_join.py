#!/usr/bin/env python3
r"""Validate the question-number join itself, per question.

Everything downstream assumes CAPI question N and cleared question N are the same
question. F3 disproves that: the CAPI's Q107 is "Which of the following did you use to pay
for the total bill for confinement?" while the cleared June-5 Q107 is "How much was the
total bill for your confinement?" - the numbering diverges between the two documents.
Joining on the number alone then attaches a neighbouring question's translation.

Both sides carry ENGLISH, so the join is checkable: compare the CAPI's English label with
the cleared English stem for the same number. High agreement = the join is sound for that
question. Low = the number means different things in the two documents, and NOTHING from
that question may be applied.

    python validate_join.py                 # summary per instrument
    python validate_join.py --list F3       # every mismatch
    python validate_join.py --json ok.json  # question numbers safe to join
"""
import argparse
import difflib
import io
import json
import os
import re
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
CSPRO = os.path.abspath(os.path.join(HERE, "..", ".."))
OFFICIAL = os.path.join(HERE, "official_translations.json")
BASE = OrderedDict([("F1", "FacilityHeadSurvey"), ("F3", "PatientSurvey"),
                    ("F4", "HouseholdSurvey")])
LABEL_Q = re.compile(r"^\s*(\d{1,3}(?:\.\d)?)\s*[\.\)]")
NAME_Q = re.compile(r"^Q(\d{1,3})(?:_(\d))?_")
NOT_A_QUESTION = re.compile(r"(_OTHER_TXT|_SPECIFY|_TXT)$")
THRESHOLD = 0.55


# The cleared stem routinely carries the enumerator directive and routing notes that the
# CAPI keeps in a separate instruction paragraph. Those are not part of the question, and
# leaving them in drags a perfectly sound join below any sensible threshold - F3 Q9 scored
# 50% purely because cleared appends "It is fine if not comfortable answering. READ
# OPTIONS OUT LOUD...". Strip them before comparing.
_TAIL = re.compile(
    r"(READ\s+OPTIONS?|DO\s+NOT\s+READ|SELECT\s+ALL|SELECT\s+ONE|ENUMERATOR\s+INSTRUCTION"
    r"|INTERVIEWER|ASKED\s+ONLY|IF\s+MORE\s+THAN|PLEASE\s+COUNT|IT\s+IS\s+FINE"
    r"|THE\s+DECISION-?MAKER\s+IS|<).*$", re.I | re.S)


def canon(s):
    s = re.sub(r"^\s*\d{1,3}(?:\.\d)?\s*[\.\)]\s*", "", s or "")
    s = _TAIL.sub(" ", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def agreement(capi_en, cleared_en):
    """Containment-aware: the CAPI label is often a clean prefix of the cleared cell."""
    a, b = canon(capi_en), canon(cleared_en)
    if not a or not b:
        return 0.0
    if a == b or a.startswith(b) or b.startswith(a) or a in b or b in a:
        return 1.0
    n = min(len(a), len(b))
    return difflib.SequenceMatcher(None, a[:n], b[:n]).ratio()


def qnum_of(name, en):
    m = LABEL_Q.match(en or "")
    if m:
        return m.group(1)
    m = NAME_Q.match(name or "")
    return (m.group(1) + ("." + m.group(2) if m.group(2) else "")) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list")
    ap.add_argument("--json")
    a = ap.parse_args()

    official = json.loads(io.open(OFFICIAL, encoding="utf-8").read())
    out = {}
    for inst, base in BASE.items():
        dcf = json.loads(io.open(os.path.join(CSPRO, inst, base + ".dcf"),
                                 encoding="utf-8-sig").read())
        off = official.get(inst, {})
        best = {}
        for lvl in dcf["levels"]:
            for rec in lvl.get("records", []):
                for it in rec.get("items", []):
                    nm = it["name"]
                    if NOT_A_QUESTION.search(nm):
                        continue
                    en = next((l.get("text", "") for l in it.get("labels", [])
                               if (l.get("language") or "EN") == "EN"), "")
                    qn = qnum_of(nm, en)
                    if not qn or qn not in off:
                        continue
                    oe = canon((off[qn].get("EN") or {}).get("stem", ""))
                    if not oe:
                        continue
                    r = agreement(en, (off[qn].get('EN') or {}).get('stem',''))
                    if qn not in best or r > best[qn][0]:
                        best[qn] = (r, nm, en, (off[qn].get("EN") or {}).get("stem", ""))

        good = {q for q, v in best.items() if v[0] >= THRESHOLD}
        bad = {q: v for q, v in best.items() if v[0] < THRESHOLD}
        out[inst] = sorted(good, key=lambda x: float(x))
        print(f"[{inst}] joined questions {len(best)}  "
              f"| join VALID {len(good)}  | join BROKEN {len(bad)}"
              f"  ({100.0 * len(good) / len(best) if best else 0:.0f}% sound)")

        if a.list == inst:
            print(f"\n  --- {inst}: numbers meaning different things in the two documents ---")
            for q, (r, nm, en, oen) in sorted(bad.items(), key=lambda kv: float(kv[0])):
                print(f"\n  Q{q}  agreement {r:.0%}   ({nm})")
                print(f"     CAPI    : {en[:100]}")
                print(f"     CLEARED : {oen[:100]}")

    if a.json:
        with io.open(a.json, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=1)
        print(f"\nWrote {a.json}")


if __name__ == "__main__":
    main()
