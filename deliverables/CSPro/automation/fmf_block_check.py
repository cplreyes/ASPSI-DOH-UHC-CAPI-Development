#!/usr/bin/env python
r"""Static [Block] invariant checker for a CSPro .fmf — catches the malformations that make
CSPro Designer SILENTLY CRASH on open (clean exit, no error). Per [Group], the rule learned
from Designer-authored saves is: blocks are listed in field order, every block's
  Position == (sum of Lengths of prior blocks in the group) + (count of prior blocks)
i.e. Position = start_field_index + prior_block_count, and the blocks must tile the group's
fields contiguously with no gaps/overlaps when blocks are used.

Usage:  py fmf_block_check.py <path-to.fmf> [<path2.fmf> ...]
Exit 0 = clean, 1 = problems found.
"""
import sys
from pathlib import Path


def check(fmf_path):
    text = Path(fmf_path).read_text(encoding="utf-8-sig")
    lines = text.replace("\r\n", "\n").split("\n")
    sec = None
    gname = None
    fields = []          # field names, in order, in the current group
    blocks = []          # [name, position, length] per [Block], in order
    problems = []

    def validate():
        if not blocks:
            return
        cum = 0
        for k, (bn, pos, ln) in enumerate(blocks):
            exp = cum + k                       # start_index (cum) + prior-block count (k)
            if pos != exp:
                problems.append(f"[{gname}] {bn}: Position={pos} expected {exp} "
                                f"(start {cum} + {k} prior blocks)")
            cum += (ln or 0)
        if cum != len(fields):
            problems.append(f"[{gname}] blocks tile {cum} fields but group has "
                            f"{len(fields)} (gap/overlap)")

    for raw in lines:
        s = raw.strip()
        if s == "[Group]":
            validate(); sec = "G"; gname = None; fields = []; blocks = []
        elif s == "[EndGroup]":
            validate(); sec = None; gname = None; fields = []; blocks = []
        elif s == "[Field]":
            sec = "F"
        elif s == "[Block]":
            sec = "B"; blocks.append([None, None, None])
        elif s.startswith("[") and s.endswith("]"):
            sec = s                              # [Form], [Text], [Level], etc.
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
    validate()
    return problems


def main():
    paths = [a for a in sys.argv[1:] if not a.startswith("-")] or []
    bad = 0
    for p in paths:
        probs = check(p)
        tag = Path(p).name
        if probs:
            bad = 1
            print(f"[FAIL] {tag}: {len(probs)} block problem(s)")
            for x in probs[:25]:
                print("   ", x)
        else:
            print(f"[ OK ] {tag}: block invariant holds")
    sys.exit(bad)


if __name__ == "__main__":
    main()
