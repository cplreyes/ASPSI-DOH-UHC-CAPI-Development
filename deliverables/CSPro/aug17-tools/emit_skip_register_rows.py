#!/usr/bin/env python3
r"""
Aug-17 migration: emit one aug17-approved-divergences.md register row per
UNREGISTERED SKIP_DIFF divergence, citing the Tier-2 matrix row that
verified it.

Task 3.4 R15 item 4. SKIP_DIFF stays a BLOCKING Tier-1 category forever --
the paper's skip cell is hand-written prose ("IF No GOTO <proceed to Q9>")
and the build's is its own JS visible-if predicate notation
("visible-if: v.Q7 === 'Yes'"); there is no shared normalized form, so a
string-equality Tier-1 comparison always disagrees even when the underlying
routing LOGIC matches (see aug17_diff.py / the Tier-2 matrix's own "Tier-1
structural note"). Rather than weaken the Tier-1 comparison (which would
also hide a REAL routing regression), each SKIP_DIFF finding is satisfied
individually by a register row -- but only when a human (Task 3.4's Tier-2
matrix pass) actually read the build's predicate against the paper's note
and a covering test, and recorded PASS. This tool automates the bookkeeping
of turning that verification into a citation-bearing register row; it never
invents or waives coverage that the matrix doesn't already assert.

Matching: a matrix row "covers" qnum N if its Rule + Expected-behavior text
contains an explicit "QN" token, OR a "Qa-Qb"/"Qa–Qb" dash range whose
integer span includes N (both column texts are searched, since the matrix
consistently names the CONDITION item -- e.g. "Shown only when Q41=Yes" --
even on a row whose own subject is a different, later item). Only rows
whose Status cell is exactly "PASS" count as verified coverage.

One row per SKIP_DIFF divergence; every emitted row's rationale names its
covering matrix row verbatim. A qnum with NO PASS-status matrix coverage is
reported separately under "No matrix coverage found" -- never silently
skipped, never given a row.

Usage:
    python emit_skip_register_rows.py F2 [--apply]

Dry-run (report only, no writes) is the default, matching
rejoin_translations.py's CLI conventions.
"""
from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path

from aug17_diff import DEFAULT_DATA_DIR, parse_register_rows, _norm_key

SCRIPT_DIR = Path(__file__).resolve().parent

_FINDING_LINE_RE = re.compile(
    r'^-\s+\*\*(?P<status>REGISTERED|UNREGISTERED)\*\*\s+\[(?P<qnum>[^\]]+)\]\s+'
    r'paper skip="(?P<paper>[^"]*)"\s+\|\s+build\s+\((?P<item>[^)]+)\)\s+skip="(?P<build>[^"]*)"'
)

_QNUM_TOKEN_RE = re.compile(r"\bQ(\d+[a-z]?(?:\.\d+)?)\b")
_QNUM_RANGE_RE = re.compile(r"\bQ(\d+)\s*[–‒\-]\s*Q?(\d+)\b")


def parse_skip_diff_findings(diff_md_text: str) -> list:
    """Extract every SKIP_DIFF finding from an aug17_diff.py report. Returns
    list of dicts: {qnum, registered (bool), paper, build, item}."""
    i = diff_md_text.find("## SKIP_DIFF")
    if i == -1:
        return []
    j = diff_md_text.find("\n## ", i + 1)
    block = diff_md_text[i:] if j == -1 else diff_md_text[i:j]
    out = []
    for line in block.split("\n"):
        m = _FINDING_LINE_RE.match(line.strip())
        if not m:
            continue
        out.append({
            "qnum": m.group("qnum"),
            "registered": m.group("status") == "REGISTERED",
            "paper": m.group("paper"),
            "build": m.group("build"),
            "item": m.group("item"),
        })
    return out


def _extract_qnums(text: str) -> set:
    """Every explicit 'Qn' token in `text`, plus every integer in a
    'Qa-Qb'/'Qa–Qb' dash range (range endpoints must be plain
    integers -- a decimal/lettered qnum is never a range endpoint in this
    document's own convention, e.g. the separate 'Q13.1–Q24.1' row names
    its members individually in the Covering-test column instead)."""
    out = {m.group(1) for m in _QNUM_TOKEN_RE.finditer(text)}
    for m in _QNUM_RANGE_RE.finditer(text):
        lo, hi = int(m.group(1)), int(m.group(2))
        if lo <= hi:
            out.update(str(n) for n in range(lo, hi + 1))
    return out


def parse_matrix_rows(matrix_md_text: str) -> list:
    """Parse every '| Rule | Expected behavior | Covering test | Status |'
    table row (skips header/divider rows and prose). Returns list of dicts:
    {rule, expected, test, status, qnums (set)}."""
    rows = []
    for line in matrix_md_text.split("\n"):
        line = line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 4:
            continue
        if cells[0].lower() == "rule":
            continue
        if set(cells[0]) <= {"-", ":"}:
            continue
        rule, expected, test, status = cells
        qnums = _extract_qnums(rule) | _extract_qnums(expected)
        rows.append({"rule": rule, "expected": expected, "test": test,
                      "status": status, "qnums": qnums})
    return rows


def build_coverage_index(matrix_rows: list) -> dict:
    """qnum -> list[matrix_row], PASS-status rows only."""
    idx: dict = {}
    for row in matrix_rows:
        # Some rows carry a parenthetical qualifier after the verdict word
        # itself (e.g. "PASS (predicate identical across Q92-Q95, ...)") --
        # still a verified PASS, just annotated. Only an exact non-PASS
        # verdict (FAIL, or anything else) excludes a row from coverage.
        if not row["status"].startswith("PASS"):
            continue
        for q in row["qnums"]:
            idx.setdefault(q, []).append(row)
    return idx


def pick_covering_row(qnum: str, candidates: list) -> dict:
    """Prefer a row whose OWN Rule cell names this exact qnum (the row is
    'about' this item) over one that only mentions it as a condition
    variable inside another item's Expected-behavior text."""
    for row in candidates:
        if qnum in _extract_qnums(row["rule"]):
            return row
    return candidates[0]


def already_registered_qnums(register_text: str, inst: str) -> set:
    """qnums that already have SOME register row for this instrument (any
    class) -- used to avoid emitting a duplicate row for a qnum the
    register already covers under a different class."""
    out = set()
    for r in parse_register_rows(register_text):
        if r.inst != inst:
            continue
        key = _norm_key(r.qnum_item)
        if key:
            out.add(key)
    return out


def _sanitize_cell(text: str) -> str:
    """aug17_diff.parse_register_rows splits a row on every raw "|" with no
    escape-awareness (`cells = line.split("|")`, then requires exactly 6) --
    a backslash-escaped `\\|` is NOT respected and silently corrupts the row
    into a >6-cell line that the parser then discards outright (a real
    finding, e.g. Q89's `isYes(v['Q87']) || isYes(v['Q88'])`, would go
    unregistered without any error). Replace a JS `||` (OR) with the word
    "OR", and any other stray literal pipe with a Unicode broken-bar
    look-alike, rather than relying on an escape the parser doesn't honor."""
    return text.replace("||", " OR ").replace("|", "¦")


def format_register_row(inst: str, qnum: str, finding: dict, matrix_row: dict, today: str) -> str:
    paper = finding["paper"] or "(no printed skip note -- this item is the destination of an earlier item's printed goto, not its source)"
    build = finding["build"] or f"(no visible-if declared -- {finding['item']} is the SOURCE of a forward routing decision; the destination item(s) carry the visible-if instead)"
    rationale = (
        f"Paper prose skip note vs build JS visible-if predicate -- notation differs, routing logic "
        f"verified identical by Tier-2 matrix row \"{matrix_row['rule']}\" ({matrix_row['expected']}), "
        f"covering test(s) {matrix_row['test']}. Emitted by emit_skip_register_rows.py from a VERIFIED "
        f"(Status=PASS) matrix row, per Task 3.4 R15. [scope: SKIP_DIFF] {today}."
    )
    paper = _sanitize_cell(paper)
    build = _sanitize_cell(build)
    rationale = _sanitize_cell(rationale)
    return f"| {inst} | Q{qnum} | capi-adaptation | {paper} | {build} | {rationale} |"


_EMITTED_ROW_SIGNATURE = "Emitted by emit_skip_register_rows.py from a VERIFIED"
_SCOPE_MARKER = "[scope: SKIP_DIFF]"


def migrate_add_scope_marker(register_text: str, inst: str) -> tuple:
    """R20 (rev-3-4 review finding): retrofit pass for rows this tool
    emitted BEFORE the scope marker existed (the real case: 64 F2 rows).
    Controller-sanctioned exception -- a logged, deterministic in-place
    annotation of rows the tool itself emitted, identified unambiguously
    by this tool's own distinctive rationale signature text
    (`_EMITTED_ROW_SIGNATURE`). NEVER touches a hand-authored row or a row
    from any other tool/task -- the signature string only ever appears in
    a row this function itself wrote. Idempotent: a row that already
    carries the marker is left untouched (migrated count excludes it).
    Returns (new_text, migrated_count)."""
    out_lines = []
    migrated = 0
    for line in register_text.split("\n"):
        stripped = line.strip()
        if (stripped.startswith("|") and f"| {inst} |" in line
                and _EMITTED_ROW_SIGNATURE in line and _SCOPE_MARKER not in line):
            # Insert the marker right before the signature sentence, inside
            # the same (last) rationale cell -- a single, deterministic
            # insertion point, never touching any other cell's content.
            line = line.replace(_EMITTED_ROW_SIGNATURE, f"{_SCOPE_MARKER} {_EMITTED_ROW_SIGNATURE}")
            migrated += 1
        out_lines.append(line)
    return "\n".join(out_lines), migrated


def main():
    ap = argparse.ArgumentParser(description="Emit register rows for VERIFIED SKIP_DIFF divergences (Task 3.4 R15)")
    ap.add_argument("instrument", choices=["F1", "F2", "F3", "F4"])
    ap.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    ap.add_argument("--apply", action="store_true", help="append to the register file (default: dry-run report only)")
    ap.add_argument("--migrate-scope", action="store_true",
                     help="R20: retrofit [scope: SKIP_DIFF] onto this tool's own "
                          "already-emitted rows for --instrument (dry-run unless --apply)")
    args = ap.parse_args()

    data_dir = args.data_dir.resolve()
    register_path = data_dir / "aug17-approved-divergences.md"

    if args.migrate_scope:
        register_text = register_path.read_text(encoding="utf-8") if register_path.exists() else ""
        new_text, migrated = migrate_add_scope_marker(register_text, args.instrument)
        print(f"{args.instrument}: {migrated} row(s) to annotate with {_SCOPE_MARKER}.")
        if args.apply:
            register_path.write_text(new_text, encoding="utf-8", newline="")
            print(f"  applied -> {register_path}")
        else:
            print("  DRY RUN -- no file written. Pass --apply to write.")
        return

    diff_path = data_dir / "reports" / f"{args.instrument}-diff.md"
    matrix_path = data_dir / "reports" / f"{args.instrument}-tier2-matrix.md"

    diff_text = diff_path.read_text(encoding="utf-8")
    matrix_text = matrix_path.read_text(encoding="utf-8")
    register_text = register_path.read_text(encoding="utf-8") if register_path.exists() else ""

    findings = parse_skip_diff_findings(diff_text)
    matrix_rows = parse_matrix_rows(matrix_text)
    coverage = build_coverage_index(matrix_rows)
    already = already_registered_qnums(register_text, args.instrument)

    today = datetime.now(timezone.utc).date().isoformat()
    emitted, skipped_already, uncovered = [], [], []

    for f in findings:
        if f["registered"]:
            continue  # already has a register row from an earlier task
        qnum = f["qnum"]
        key = _norm_key(qnum)
        if key in already:
            skipped_already.append(qnum)
            continue
        candidates = coverage.get(qnum)
        if not candidates:
            uncovered.append(qnum)
            continue
        row = pick_covering_row(qnum, candidates)
        emitted.append((qnum, format_register_row(args.instrument, qnum, f, row, today)))

    print(f"{args.instrument}: {len(findings)} SKIP_DIFF findings "
          f"({sum(1 for f in findings if f['registered'])} already registered).")
    print(f"  {len(emitted)} new register row(s) to emit (matrix-covered, unregistered).")
    if skipped_already:
        print(f"  {len(skipped_already)} already covered by an existing register row under another class: {skipped_already}")
    if uncovered:
        print(f"  {len(uncovered)} with NO PASS-status matrix coverage found -- NOT registered, needs hand review: {uncovered}")

    if args.apply and emitted:
        with open(register_path, "a", encoding="utf-8", newline="") as fh:
            for _qnum, line in emitted:
                fh.write(line + "\n")
        print(f"  appended {len(emitted)} row(s) to {register_path}")
    elif emitted:
        print("  DRY RUN -- no rows written. Pass --apply to append. Preview:")
        for qnum, line in emitted[:5]:
            print(f"    {line[:160]}...")
        if len(emitted) > 5:
            print(f"    ... and {len(emitted) - 5} more")


if __name__ == "__main__":
    main()
