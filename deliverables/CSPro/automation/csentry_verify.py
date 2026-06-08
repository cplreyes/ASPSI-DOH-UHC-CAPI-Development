#!/usr/bin/env python
r"""CSEntry compile-gate — the REAL verification of generated .ent.apc logic.

WHY THIS EXISTS (learned the hard way 2026-06-09):
  cspro_compile_driver.py drives CSPro DESIGNER (Ctrl+L / Ctrl+K) and reads
  "Compile Successful" from a screenshot. That is NOT trustworthy: Designer can
  report success while compiling a stale/empty in-memory app (it does not always
  reload the regenerated .ent.apc from disk). It masked 61 real syntax errors in
  F4 (a bad protect() call) for an entire session.

  CSEntry, by contrast, RECOMPILES the .ent.apc text on every launch and writes
  <base>.ent.err listing the errors when it fails. That file is ground truth.

WHAT THIS DOES — for each instrument:
  1. delete any stale <base>.ent.err
  2. kill CSEntry, launch it on <base>_desktest.pff (CSEntry auto-compiles)
  3. wait, then kill CSEntry
  4. PASS if no .err was written (logic compiled, entry started);
     FAIL if .err exists (print its contents — the file/line/message to fix)

Usage:  py csentry_verify.py [F1] [F3] [F4]      (no args = all three)
Exit code 0 = all pass, 1 = at least one failed.
"""
import subprocess
import sys
import time
from pathlib import Path

CSENTRY_EXE = r"C:\Program Files (x86)\CSPro 8.0\CSEntry.exe"
CSPRO_DIR = Path(__file__).resolve().parent.parent      # deliverables/CSPro
SPECS = {
    "F1": ("F1", "FacilityHeadSurvey"),
    "F3": ("F3", "PatientSurvey"),
    "F4": ("F4", "HouseholdSurvey"),
}
WAIT_S = 8


def _kill():
    subprocess.run(["taskkill", "/F", "/IM", "CSEntry.exe"], capture_output=True)
    time.sleep(1.0)


def verify(key):
    d, base = SPECS[key]
    inst = CSPRO_DIR / d
    pff = inst / f"{base}_desktest.pff"
    err = inst / f"{base}.ent.err"
    if not pff.exists():
        print(f"[{key}] SKIP — {pff.name} not found")
        return True
    try:
        err.unlink()
    except FileNotFoundError:
        pass
    _kill()
    subprocess.Popen([CSENTRY_EXE, str(pff.resolve())])
    time.sleep(WAIT_S)
    _kill()
    if err.exists():
        print(f"[{key}] FAIL — CSEntry reported compile errors:\n"
              f"---- {err.name} ----")
        print(err.read_text(encoding="utf-8", errors="replace").rstrip())
        print("--------")
        return False
    print(f"[{key}] PASS — .ent.apc compiles in CSEntry (entry started, no .ent.err)")
    return True


def main():
    keys = [a for a in sys.argv[1:] if a in SPECS] or list(SPECS)
    results = {k: verify(k) for k in keys}
    print("\n=== CSEntry compile-gate summary ===")
    for k, ok in results.items():
        print(f"  {k}: {'PASS' if ok else 'FAIL'}")
    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()
