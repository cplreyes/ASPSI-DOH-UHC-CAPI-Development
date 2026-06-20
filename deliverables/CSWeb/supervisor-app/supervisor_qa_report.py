"""Supervisor-QA report — read CSV exports of F1/F3/F4 + the assignment lookup,
write one PII-light HTML report (coverage / partials / flags). Read-only.

Usage:
  python supervisor_qa_report.py --exports ./exports --assignments ./assignments.csv \
      --out ./supervisor-qa.html --cluster 01028 --today 20260621

Expects ./exports/F1.csv, F3.csv, F4.csv (any subset). Missing instruments are skipped.
Run tests: python -m pytest -q
"""
import argparse
import os
from case_model import load_cases
from assignment import load_assignments
from coverage import compute_coverage
from qa_rules import run_rules
from partials import list_partials
from report_html import render_report


def build_report(export_dir, assignments_csv, cluster, today):
    cases = []
    for inst in ("F1", "F3", "F4"):
        path = os.path.join(export_dir, f"{inst}.csv")
        if os.path.exists(path):
            cases.extend(load_cases(path, inst))
    assignments = load_assignments(assignments_csv) if os.path.exists(assignments_csv) else {}
    coverage = compute_coverage(cases, assignments)
    flags = run_rules(cases, today=today)
    partials = list_partials(cases)
    return render_report(coverage, partials, flags, cluster=cluster,
                         generated=f"{today} (cases: {len(cases)})")


def main():
    ap = argparse.ArgumentParser(description="Supervisor-QA report (read-only).")
    ap.add_argument("--exports", required=True, help="dir with F1.csv/F3.csv/F4.csv")
    ap.add_argument("--assignments", required=True, help="assignment/target CSV")
    ap.add_argument("--out", required=True, help="output HTML path")
    ap.add_argument("--cluster", default="(cluster)")
    ap.add_argument("--today", required=True, help="YYYYMMDD (stuck-partial reference)")
    args = ap.parse_args()
    html = build_report(args.exports, args.assignments, args.cluster, args.today)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
