# -*- coding: utf-8 -*-
"""#1102 round-close prep: inventory every noinput-gated field (the painted-but-
locked class) per instrument, with its trigger field and whether both live on
the same form (the DisplayTogether paint problem).

The "#1102 class" = gated *_OTHER_TXT fields that share a form with their
trigger — the tester-agreed round-close sweep target (option 3, 2026-08-10).
Rows marked * belong to the class. Run from either checkout:

    py deliverables/CSPro/automation/inventory_1102.py
"""
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]  # deliverables/CSPro
APPS = [("F1", "FacilityHeadSurvey"), ("F3", "PatientSurvey"), ("F4", "HouseholdSurvey")]

for key, app in APPS:
    apc = (BASE / key / f"{app}.ent.apc").read_text(encoding="utf-8", errors="replace")
    fmf = (BASE / key / f"{app}.fmf").read_text(encoding="utf-8", errors="replace")

    # form membership: fields hang off a form as Item=<FIELD> lines inside
    # [Form]...[EndForm] (NOT as Name= lines — Name= inside a form names the
    # form itself). Track the current form and map every Item= to it.
    form_of, form_label = {}, {}
    current_form = None
    for line in fmf.splitlines():
        line = line.strip()
        if line == "[Form]" or line == "[EndForm]":
            current_form = None
        elif line.startswith("Name=FORM"):
            current_form = line.split("=", 1)[1]
        elif line.startswith("Label=") and current_form and current_form not in form_label:
            form_label[current_form] = line.split("=", 1)[1]
        elif line.startswith("Item=") and current_form:
            form_of[line.split("=", 1)[1]] = current_form

    rows = []
    for m in re.finditer(r"PROC (\w+)\s*\n(?:preproc|onfocus)\s*\n(.*?)(?=\nPROC |\Z)", apc, re.S):
        field, body = m.group(1), m.group(2)
        head = body[:600]
        if "noinput" not in head:
            continue
        # trigger = first OTHER form-field referenced in the gate body; covers
        # both `if Q12 <> 3` and the checkbox idiom `pos("90", Q104_...) = 0`
        trigger = "?"
        for tok in re.findall(r"[A-Z][A-Z0-9_]{2,}", head):
            if tok != field and tok in form_of:
                trigger = tok
                break
        f1, f2 = form_of.get(field, "?"), form_of.get(trigger, "?")
        rows.append((field, trigger, f1, f2, "SAME-FORM" if f1 == f2 and f1 != "?" else ""))

    unmapped = sum(1 for r in rows if r[2] == "?")
    the_class = [r for r in rows if r[4] and r[0].endswith("_OTHER_TXT")]
    print(f"== {key}: {len(rows)} noinput-gated fields, "
          f"{sum(1 for r in rows if r[4])} on the same form as their trigger, "
          f"{unmapped} unmapped")
    print(f"   #1102 class (gated other-specify sharing its trigger's form): "
          f"{len(the_class)}")
    for r in rows:
        lbl = form_label.get(r[2], "")[:44]
        mark = "*" if r[4] and r[0].endswith("_OTHER_TXT") else " "
        print(f"  {mark}{r[0]:34} gate={r[1]:28} form={r[2]:8} trig-form={r[3]:8} {r[4]:9} {lbl}")
