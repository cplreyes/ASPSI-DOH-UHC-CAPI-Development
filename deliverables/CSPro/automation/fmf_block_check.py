#!/usr/bin/env python
r"""Static [Block] invariant checker for a CSPro .fmf — catches the malformations that make
CSPro Designer SILENTLY CRASH on open (clean exit, no error). Per [Group], the rule learned
from Designer-authored saves is: blocks are listed in field order and every block's
  Position == start_field_index + prior_block_count
(Position indexes the group's item list, where each prior block occupies one slot).

Blocks do NOT have to tile the group contiguously: unblocked fields between blocks are
legal and render as their own screens (F4 Section N does this — 38 food/expense triplet
blocks with 4 standalone subtotal fields interleaved; Designer opens and publishes it
fine). Since start_field_index is only recoverable FROM Position (start = Position - k),
the checkable invariant is: derived starts are in order, non-overlapping, and in bounds:
  start(k) = Position(k) - k;  start(k) >= start(k-1) + Length(k-1);  start(k)+Length(k) <= n_fields

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
        prev_end = 0                            # first field index available to the next block
        for k, (bn, pos, ln) in enumerate(blocks):
            if pos is None or ln is None:
                problems.append(f"[{gname}] {bn}: missing Position/Length")
                continue
            start = pos - k                     # Position = start_field_index + k prior blocks
            if start < prev_end:
                problems.append(f"[{gname}] {bn}: Position={pos} -> start field {start} "
                                f"overlaps/precedes previous block (fields < {prev_end} taken)")
            if start + ln > len(fields):
                problems.append(f"[{gname}] {bn}: Position={pos} Length={ln} -> fields "
                                f"{start}..{start + ln - 1} exceed group's {len(fields)} fields")
            prev_end = max(prev_end, start + ln)

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
