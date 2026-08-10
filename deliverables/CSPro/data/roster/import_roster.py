#!/usr/bin/env python3
"""K4 — import ASPSI's fieldworker roster (xlsx or csv) into roster-source.csv.

The hub build (`supervisor-hub/build_hub_apps.py`) reads roster-source.csv as its
single source of truth for the login roster. When ASPSI delivers the real-names
roster spreadsheet, run this instead of hand-editing the CSV.

Usage:
    py import_roster.py <sheet.xlsx|sheet.csv> [--sheet NAME] \
        --map username=<col> password=<col> role=<col> operator_id=<col> \
              cluster=<col> supervisor_id=<col>

Column values in --map are the HEADER NAMES in ASPSI's sheet (case-insensitive).
Any target column missing from the map is filled from a same-named header if
present, else left blank (supervisor_id may legitimately be blank for supervisors).

Output: roster-source.csv in this folder (GITIGNORED — carries credentials).
The previous file is kept as roster-source.csv.bak.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET_COLS = ["username", "password", "role", "operator_id", "cluster", "supervisor_id"]
OUT = HERE / "roster-source.csv"


def read_rows(src: Path, sheet: str | None) -> tuple[list[str], list[list[str]]]:
    if src.suffix.lower() == ".csv":
        with src.open(encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.reader(fh))
        return [h.strip() for h in rows[0]], [[(v or "").strip() for v in r] for r in rows[1:]]
    import openpyxl
    wb = openpyxl.load_workbook(src, read_only=True, data_only=True)
    ws = wb[sheet] if sheet else wb.active
    it = ws.iter_rows(values_only=True)
    header = [str(v or "").strip() for v in next(it)]
    body = [[str(v if v is not None else "").strip() for v in r] for r in it]
    wb.close()
    return header, [r for r in body if any(r)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("--sheet", default=None)
    ap.add_argument("--map", nargs="*", default=[], metavar="target=source_header")
    args = ap.parse_args()

    header, body = read_rows(args.source, args.sheet)
    lower = {h.lower(): i for i, h in enumerate(header)}

    mapping: dict[str, str] = {}
    for pair in args.map:
        tgt, _, srccol = pair.partition("=")
        if tgt not in TARGET_COLS:
            sys.exit(f"unknown target column '{tgt}' (valid: {', '.join(TARGET_COLS)})")
        mapping[tgt] = srccol

    idx: dict[str, int | None] = {}
    for col in TARGET_COLS:
        src_header = mapping.get(col, col)
        idx[col] = lower.get(src_header.lower())
        if idx[col] is None and col in mapping:
            sys.exit(f"mapped header '{src_header}' for '{col}' not found in {args.source.name} "
                     f"(headers: {header})")

    out_rows = []
    for r in body:
        row = [(r[idx[c]] if idx[c] is not None and idx[c] < len(r) else "") for c in TARGET_COLS]
        if not row[0]:
            continue  # no username = not a roster row
        out_rows.append(row)

    missing_pw = [r[0] for r in out_rows if not r[1]]
    if missing_pw:
        sys.exit(f"rows without a password: {missing_pw} — refusing to write a broken roster")

    if OUT.exists():
        OUT.replace(OUT.with_suffix(".csv.bak"))
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(TARGET_COLS)
        w.writerows(out_rows)
    print(f"wrote {len(out_rows)} roster rows -> {OUT}")
    print("next: py ../../supervisor-hub/build_hub_apps.py  (regenerates UserRoster.dat)")


if __name__ == "__main__":
    main()
