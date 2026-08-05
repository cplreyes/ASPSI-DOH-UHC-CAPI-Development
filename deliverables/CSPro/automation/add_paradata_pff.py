#!/usr/bin/env python3
r"""Add the missing `Paradata=` line to the F1/F3/F4 .pff [Files] sections (#840).

WHY THIS EXISTS
---------------
`cspro_compile_driver.py` writes `"paradata": {"collection": "all", ...}` into each
.ent, which turns paradata collection ON. But CSPro only writes the paradata log if
the .pff's [Files] section also says WHERE to put it:

    [Files]
    Application=.\FacilityHeadSurvey.ent
    InputData=.\FacilityHeadSurvey.csdb
    Paradata=.\FacilityHeadSurvey.cslog     <-- this line

Without it the .ent setting is INERT: nothing is ever logged. Verified on the itel
2026-07-17 - the five CSES tutorial apps each carry `Paradata=` in their .pff and each
has a .cslog; F1/F3/F4 have neither. So #840's premise ("the durations are on the
enumerators' devices") was false - no paradata has ever been collected for these
instruments, and the durations for interviews already conducted are unrecoverable.

This is a .pff-only change: no .dcf, no .fmf, no .apc. It is therefore NOT covered by
the pretest dictionary freeze, and it starts capturing durations from the next
interview onward (option C in #840). The durable reporting answer - an off-form
INTERVIEW_TIMING block whose DURATION_MIN rides the case sync into CSWeb - is option A
and still wants doing post-pretest.

NOTE: the .cslog stays ON THE DEVICE. It does not ride the `direction: put` case sync,
so retrieving it is a separate step (adb pull, or CSEntry's own paradata sync).

Safe across version bumps: automation/stamp_version.py's stamp_pff() only rewrites
`Description=` inside [Run Information] and preserves the rest byte-for-byte, so this
line will not be clobbered by a `bump`.

Idempotent - re-running is a no-op. Mirrors stamp_pff()'s BOM/newline handling.

Run:  py automation/add_paradata_pff.py [--check]
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PFF = {
    "F1": (ROOT / "F1" / "FacilityHeadSurvey.pff", "FacilityHeadSurvey"),
    "F3": (ROOT / "F3" / "PatientSurvey.pff", "PatientSurvey"),
    "F4": (ROOT / "F4" / "HouseholdSurvey.pff", "HouseholdSurvey"),
}


def patch(key, check_only=False):
    p, base = PFF[key]
    raw = p.read_text(encoding="utf-8-sig")       # CSPro writes pffs with a UTF-8 BOM
    bom = "﻿" if p.read_bytes()[:3] == b"\xef\xbb\xbf" else ""
    want = "Paradata=.\\%s.cslog" % base

    if any(ln.strip().lower().startswith("paradata=") for ln in raw.splitlines()):
        print("[%s] already has Paradata= - no change" % key)
        return False
    if check_only:
        print("[%s] MISSING Paradata= -> would add: %s" % (key, want))
        return True

    out, in_files, done = [], False, False
    for ln in raw.splitlines():
        stripped = ln.strip()
        if stripped.startswith("["):
            # leaving [Files] without having inserted -> insert before the next section
            if in_files and not done:
                while out and not out[-1].strip():
                    out.pop()
                out += [want, ""]
                done = True
            in_files = stripped == "[Files]"
        out.append(ln)
        # insert immediately after InputData= so the block reads Application/InputData/Paradata
        if in_files and not done and stripped.lower().startswith("inputdata="):
            out.append(want)
            done = True

    if in_files and not done:                      # [Files] was the last section
        out.append(want)
        done = True
    if not done:
        print("[%s] ! no [Files] section in %s - not patched" % (key, p.name))
        return False

    p.write_text(bom + "\n".join(out) + "\n", encoding="utf-8")
    print("[%s] added: %s" % (key, want))
    return True


if __name__ == "__main__":
    check = "--check" in sys.argv
    changed = [k for k in ("F1", "F3", "F4") if patch(k, check_only=check)]
    print("\n%s: %s" % ("would patch" if check else "patched", changed or "nothing"))
