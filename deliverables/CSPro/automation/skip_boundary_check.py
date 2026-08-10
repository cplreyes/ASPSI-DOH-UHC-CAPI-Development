#!/usr/bin/env python
r"""Static skip-boundary checker — validates the SHIPPED .fmf screen plan against
the SHIPPED .ent.apc skip logic (R3, 2026-07-03).

On a DisplayTogether ([Block]) screen CSEntry renders EVERY member field
regardless of skip/noinput logic (verified on-device, UAT R4 — GH #371/#372).
The generators encode this rule when DERIVING plans (F3/F4 derive_block_plan,
F1 inject_blocks.py), but nothing re-checked the artifacts that actually ship.
This gate closes that gap, independently of how the .fmf was produced:

  1. a `skip to` TARGET field must START its screen (nothing skipped over may
     already be rendered on the target's screen);
  2. a `skip to` SOURCE field must END its screen (nothing it can skip over
     may share the screen);
  3. a noinput-gated field (other-specify etc.) must be ALONE on its screen
     (the gate can only suppress a whole screen, not one member of it).

Field->block mapping uses the Designer-verified Position formula
(start_field_index = Position - prior_block_count; see fmf_block_check.py).

Usage:  py skip_boundary_check.py            # all three instruments
        py skip_boundary_check.py F4         # one instrument
Exit 0 = clean, 1 = violations found.
"""
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
TARGETS = {
    "F1": (BASE / "F1" / "FacilityHeadSurvey.ent.apc", BASE / "F1" / "FacilityHeadSurvey.fmf"),
    "F3": (BASE / "F3" / "PatientSurvey.ent.apc", BASE / "F3" / "PatientSurvey.fmf"),
    "F4": (BASE / "F4" / "HouseholdSurvey.ent.apc", BASE / "F4" / "HouseholdSurvey.fmf"),
}

# Documented, deliberate exceptions — reported as [WAIVED], never as failures.
# (block_name, field_name): the break-off flow (#515/#561) PRE-FILLS the
# Result-of-Visit and skips to it as the LAST member of the hand-made visit-record
# screen, so the enumerator records the visit row + final result together when
# closing out a broken-off case. Designed behavior, identical on F1/F3/F4, live
# through UAT R4/R5 with no tester reports. Remove this waiver if the break-off
# landing is ever redesigned to a standalone result screen.
KNOWN_WAIVERS = {
    ("VISIT_RECORD_BLOCK", "ENUM_RESULT_FINAL_VISIT"),
}


def parse_apc(apc_path):
    """-> (skip_sources, skip_targets, noinput_gated) — same semantics as the
    generators' parse_apc (F3/F4 generate_fmf.py, F1 inject_blocks.py)."""
    txt = apc_path.read_text(encoding="utf-8")
    txt = re.sub(r"\{[^{}]*\}", " ", txt)
    sources, targets, gated = set(), set(), set()
    procs = re.split(r"(?m)^PROC\s+([A-Z0-9_]+)\s*$", txt)
    for name, body in zip(procs[1::2], procs[2::2]):
        if re.search(r"\bskip\s+to\b", body):
            sources.add(name)
        if re.search(r"\bnoinput\b", body):
            gated.add(name)
    targets.update(re.findall(r"\bskip\s+to\s+([A-Z0-9_]+)", txt))
    return sources, targets, gated


def parse_fmf_groups(fmf_path):
    """-> [(group_name, [field...], [(block_name, start, length)...])] per [Group]."""
    lines = fmf_path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").split("\n")
    groups, sec, gname, fields, blocks = [], None, None, [], []

    def flush():
        if gname and blocks:
            resolved = [(bn, pos - k, ln) for k, (bn, pos, ln) in enumerate(blocks)]
            groups.append((gname, list(fields), resolved))

    for raw in lines:
        s = raw.strip()
        if s == "[Group]":
            flush(); sec = "G"; gname = None; fields = []; blocks = []
        elif s == "[EndGroup]":
            flush(); sec = None; gname = None; fields = []; blocks = []
        elif s == "[Field]":
            sec = "F"
        elif s == "[Block]":
            sec = "B"; blocks.append([None, None, None])
        elif s.startswith("[") and s.endswith("]"):
            sec = s
        elif sec == "G" and s.startswith("Name=") and gname is None:
            gname = s[5:]
        elif sec == "F" and s.startswith("Name="):
            fields.append(s[5:])
        elif sec == "B":
            if s.startswith("Name="):
                blocks[-1][0] = s[5:]
            elif s.startswith("Position=") and "," not in s:
                blocks[-1][1] = int(s.split("=", 1)[1])
            elif s.startswith("Length="):
                blocks[-1][2] = int(s.split("=", 1)[1])
    flush()
    return groups


def check(inst, apc_path, fmf_path):
    sources, targets, gated = parse_apc(apc_path)
    problems, waived = [], []
    for gname, fields, blocks in parse_fmf_groups(fmf_path):
        for bn, start, length in blocks:
            members = fields[start:start + length]
            for i, f in enumerate(members):
                sink = waived if (bn, f) in KNOWN_WAIVERS else problems
                if f in targets and i != 0:
                    sink.append(f"[{gname}] {bn}: skip TARGET {f} at member {i + 1}/{length} "
                                f"(must START its screen)")
                if f in sources and i != length - 1:
                    sink.append(f"[{gname}] {bn}: skip SOURCE {f} at member {i + 1}/{length} "
                                f"(must END its screen)")
                if f in gated and length > 1:
                    sink.append(f"[{gname}] {bn}: noinput-gated {f} shares a {length}-field "
                                f"screen (must be alone)")
    return problems, waived


def main():
    keys = [a for a in sys.argv[1:] if a in TARGETS] or list(TARGETS)
    bad = 0
    for k in keys:
        apc, fmf = TARGETS[k]
        if not apc.exists() or not fmf.exists():
            print(f"[SKIP] {k}: missing apc or fmf")
            continue
        probs, waived = check(k, apc, fmf)
        if probs:
            bad = 1
            print(f"[FAIL] {k}: {len(probs)} skip-boundary violation(s)")
            for p in probs[:30]:
                print("   ", p)
        else:
            print(f"[ OK ] {k}: no skip target/source/noinput-gate inside a shared screen"
                  + (f" ({len(waived)} known waiver(s))" if waived else ""))
        for w in waived:
            print(f"    [WAIVED] {w}")
    sys.exit(bad)


if __name__ == "__main__":
    main()
