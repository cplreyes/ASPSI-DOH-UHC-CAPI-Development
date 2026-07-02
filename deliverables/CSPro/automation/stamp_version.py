#!/usr/bin/env python
r"""CSEntry build-version stamper (tester request 2026-07-02).

CSEntry has NO native app-version concept -- the .ent 'version' fields are file-format
versions, which is exactly why "Update Installed Applications" can't tell testers whether
their build is current. So versions live in ../versions.json (single source of truth) and
are stamped onto two surfaces that ride every CSWeb deploy:

  1. .pff [Run Information] Description  -> CSEntry's application-list entry + case-listing
     title (CSPro source: PFF.cpp APPDESCRIPTION = "Description"; Android shows it verbatim).
  2. generate_qsf.py build footer on the first cover question -> every bug screenshot
     identifies its build. The generator reads versions.json itself; this script just
     re-runs it after a bump so the two surfaces can never drift.

Usage:
  py stamp_version.py show               # versions + drift check (pff/qsf vs versions.json)
  py stamp_version.py stamp F1 F3 F4     # write pff Descriptions from versions.json as-is
  py stamp_version.py bump F3            # PATCH bump (bug-fix deploy), restamp pff, regen qsf
  py stamp_version.py bump F3 --minor    # MINOR bump (new/changed functionality)
  py stamp_version.py bump F3 --major    # MAJOR bump (UAT round close / breaking change)
  py stamp_version.py set F3 2.0.0       # explicit version, same restamp+regen

Policy: Semantic Versioning (MAJOR.MINOR.PATCH) — patch per bug-fix deploy, minor for new
functionality, major at UAT round close or a breaking change (e.g. data shape).
Exit 0 = ok / no drift; 1 = drift found (show) or an instrument failed.
"""
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # deliverables/CSPro
VERSIONS = ROOT / "versions.json"
PFF = {
    "F1": ROOT / "F1" / "FacilityHeadSurvey.pff",
    "F3": ROOT / "F3" / "PatientSurvey.pff",
    "F4": ROOT / "F4" / "HouseholdSurvey.pff",
}
QSF = {
    "F1": ROOT / "F1" / "FacilityHeadSurvey.ent.qsf",
    "F3": ROOT / "F3" / "PatientSurvey.ent.qsf",
    "F4": ROOT / "F4" / "HouseholdSurvey.ent.qsf",
}


def load():
    return json.loads(VERSIONS.read_text(encoding="utf-8"))


def description(v, key):
    return f"{v[key]['app']} ({key}) - v{v[key]['version']} ({v[key]['date']})"


def qsf_marker(v, key):
    # must match the BUILD_FOOTER string each generate_qsf.py emits
    return f"Build: {key} v{v[key]['version']} ({v[key]['date']})"


def stamp_pff(v, key):
    """Insert/replace Description= in [Run Information]. Preserves everything else byte-for-byte."""
    p = PFF[key]
    raw = p.read_text(encoding="utf-8-sig")          # CSPro writes pffs with a UTF-8 BOM
    bom = "﻿" if p.read_bytes()[:3] == b"\xef\xbb\xbf" else ""
    lines = raw.splitlines()
    out, in_runinfo, done = [], False, False
    for ln in lines:
        stripped = ln.strip()
        if stripped.startswith("["):
            # leaving [Run Information] without having seen a Description -> insert one
            if in_runinfo and not done:
                while out and not out[-1].strip():
                    out.pop()
                out += [f"Description={description(v, key)}", ""]
                done = True
            in_runinfo = stripped == "[Run Information]"
        elif in_runinfo and stripped.startswith("Description="):
            ln = f"Description={description(v, key)}"
            done = True
        out.append(ln)
    if not done:
        print(f"[{key}] ! no [Run Information] section in {p.name} -- not stamped")
        return False
    p.write_text(bom + "\n".join(out) + "\n", encoding="utf-8")
    print(f"[{key}] pff Description = {description(v, key)}")
    return True


def regen_qsf(key):
    """Re-run the instrument's qsf generator so the build footer picks up the new version."""
    r = subprocess.run([sys.executable, "generate_qsf.py"], cwd=ROOT / key,
                       capture_output=True, text=True)
    tail = (r.stdout or r.stderr).strip().splitlines()
    print(f"[{key}] {tail[-1] if tail else 'generate_qsf.py: no output'}")
    return r.returncode == 0


def show(v):
    drift = False
    for key in PFF:
        want_pff = f"Description={description(v, key)}"
        pff_ok = want_pff in PFF[key].read_text(encoding="utf-8-sig")
        qsf_ok = qsf_marker(v, key) in QSF[key].read_text(encoding="utf-8-sig")
        flag = "" if (pff_ok and qsf_ok) else "  <-- DRIFT" + ("" if pff_ok else " [pff]") + ("" if qsf_ok else " [qsf]")
        print(f"[{key}] v{v[key]['version']} ({v[key]['date']})  pff={'ok' if pff_ok else 'STALE'}  "
              f"qsf={'ok' if qsf_ok else 'STALE'}{flag}")
        drift = drift or not (pff_ok and qsf_ok)
    return not drift


def main():
    args = sys.argv[1:]
    if not args or args[0] not in ("show", "stamp", "bump", "set"):
        print(__doc__)
        sys.exit(1)
    cmd, rest = args[0], args[1:]
    v = load()

    if cmd == "show":
        sys.exit(0 if show(v) else 1)

    keys = [a.upper() for a in rest if a.upper() in PFF]
    if not keys:
        print("no instrument given (F1/F3/F4)")
        sys.exit(1)

    if cmd in ("bump", "set"):
        for key in keys:
            if cmd == "bump":
                major, minor, patch = (int(x) for x in v[key]["version"].split("."))
                if "--major" in rest:
                    v[key]["version"] = f"{major + 1}.0.0"
                elif "--minor" in rest:
                    v[key]["version"] = f"{major}.{minor + 1}.0"
                else:
                    v[key]["version"] = f"{major}.{minor}.{patch + 1}"
            else:
                explicit = [a for a in rest if a not in keys and a[0].isdigit()]
                if not explicit:
                    print("set needs a version, e.g.: set F3 2.0.0")
                    sys.exit(1)
                v[key]["version"] = explicit[0]
            v[key]["date"] = date.today().isoformat()
        VERSIONS.write_text(json.dumps(v, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    ok = True
    for key in keys:
        ok = stamp_pff(v, key) and ok
        if cmd in ("bump", "set"):
            ok = regen_qsf(key) and ok
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
