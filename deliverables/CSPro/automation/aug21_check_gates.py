#!/usr/bin/env python3
"""Count the Aug-21 printed-gate help notes per item across every qsf language.

    python automation/aug21_check_gates.py F4 Q117_SPECIALIST_FOLLOWUP \
        Q118_SAT_REFERRAL_PROCESS Q131_NBB_OOP Q135_ZBB_OOP

Exit 1 if any named item carries fewer gate notes than the qsf declares languages.

WHAT COUNTS AS A GATE NOTE
--------------------------
A gate is a BRACKETED directive on the blue Instruction line - the shape the paper
prints ("[Ask only if they went to a DOH-retained hospital]") and the shape the
cleared translations keep ("[Itanong lamang kung sila ay pumunta sa ...]"). So the
counter matches `<p class="instruction">[` and never the English words inside: a
translated gate must still pass. Matching the whole instruction paragraph instead
would false-GREEN on Q118, whose READ-ONE note is a second instruction paragraph
that would cover for a missing gate.
"""
import io
import re
import sys
from pathlib import Path

QSF = {"F1": "F1/FacilityHeadSurvey.ent.qsf", "F3": "F3/PatientSurvey.ent.qsf",
       "F4": "F4/HouseholdSurvey.ent.qsf"}

_ITEM = re.compile(r"^  - name: ", re.M)          # one qsf question block per item
_INSTRUCTION = '<p class="instruction">'
_GATE = _INSTRUCTION + "["


def item_block(text, name):
    """The qsf question block for `name`, ending at the NEXT item (not a fixed window)."""
    start = text.find(f".{name}\n")
    if start < 0:
        raise SystemExit(f"aug21_check_gates: no qsf question block for {name}")
    nxt = _ITEM.search(text, start)
    return text[start:nxt.start() if nxt else len(text)]


def main(inst, items):
    path = Path(__file__).resolve().parent.parent / QSF[inst]
    text = io.open(path, encoding="utf-8").read()
    nlang = len(re.findall(r"^  - name: \w+\n    label: ", text, re.M))
    bad = 0
    for name in items:
        blk = item_block(text, name)
        n = blk.count(_GATE)
        total = blk.count(_INSTRUCTION)
        print(f"{name}: {n} gate notes across {nlang} languages "
              f"({total} instruction paragraphs)")
        if n < nlang:
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2:]))
