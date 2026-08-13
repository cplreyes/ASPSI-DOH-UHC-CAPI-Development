"""ETL runner — builds the MASTER DATASET handed to ASPSI data processing.

    python run.py [--date YYYY-MM-DD] [--skip-extract]

extract (breakout DBs + csweb_f2 over SSH) -> transform (all questions, all
four instruments) -> QA gates -> out/<date>/

  f1_clean.csv f3_clean.csv f4_clean.csv f2_clean.csv   one row per case,
                                                        EVERY question column
  <inst>__<roster>.csv                                  repeating records
  shared_dimensions.csv                                 cross-instrument joins
  qa_report.md  manifest.json                           what came out, and what
                                                        ASPSI must know about it

Scope note (2026-07-13): tabulation moved to ASPSI; this dataset is the handoff.
Still open with them: the .dta/CSV question and who attaches the sampling
weights. Until they answer, we emit CSV (Stata reads it) and carry every design
variable through untouched.
"""
import csv, datetime, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import extract_csweb
from extract_csweb import ALL_DBS, F2_DB
from transform import (INSTRUMENTS, transform_instrument, transform_f2,
                       to_shared_dimensions, long_names, STATA_NAME_MAX)

CODEBOOK_VERSION = "0.6"      # bumped: full-variable extraction + F2 wired in


def write_csv(path, rows):
    """CSV with a stable column order: the union of every row's keys.

    Rows can differ in shape (an F2 spec change adds a key; a case-level table
    may be absent for a case), so DictWriter on rows[0] alone would silently
    drop columns. Union + restval keeps the file rectangular.
    """
    if not rows:
        path.write_text("")
        return []
    cols = []
    seen = set()
    for r in rows:
        for k in r:
            if k not in seen:
                seen.add(k)
                cols.append(k)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, restval="")
        w.writeheader()
        w.writerows(rows)
    return cols


def qa_gates(all_clean, counts, qa_notes):
    """etl-spec §4. Returns (hard_failures, soft_flags)."""
    hard, soft = [], []
    by_inst = {}
    for r in all_clean:
        by_inst.setdefault(r["_source_instrument"], []).append(r)

    # 1. row counts vs source (soft: deleted cases are legitimately excluded)
    for inst, db in INSTRUMENTS.items():
        src = counts.get(db, {}).get("level-1", 0)
        got = len(by_inst.get(inst, []))
        if got != src:
            soft.append(f"{inst}: {src} source cases -> {got} clean rows "
                        f"({src - got} excluded as deleted/invalid)")
    f2_src = counts.get(F2_DB, {}).get("f2_responses", 0)
    f2_got = len(by_inst.get("f2", []))
    if f2_src and f2_got != f2_src:
        hard.append(f"f2: {f2_src} submissions in the store -> {f2_got} clean "
                    f"rows — submissions were LOST in transform")

    # 2. an instrument that vanishes must never pass quietly. A missing
    #    instrument is indistinguishable from "everyone's cases were deleted"
    #    unless we look at the source: if the breakout has tables but no
    #    level-1 rows, the extract or the DB is broken, not the fieldwork.
    for inst, db in INSTRUMENTS.items():
        got = len(by_inst.get(inst, []))
        src_l1 = counts.get(db, {}).get("level-1", 0)
        if got == 0 and src_l1 == 0:
            hard.append(f"{inst}: the instrument is ABSENT from the dataset — "
                        f"no cases on the server ({db}.`level-1` is empty). "
                        f"Either none have been collected yet, or the breakout "
                        f"is mid-rebuild after a dictionary re-upload "
                        f"(etl-spec §2.1 caveat 1). Expected before fieldwork; "
                        f"a hard stop for a handoff — never ship a master "
                        f"dataset with an instrument missing.")
        elif got == 0 and src_l1 > 0:
            soft.append(f"{inst}: {src_l1} source cases but 0 clean rows — every "
                        f"case is flagged deleted on CSWeb (test-data cleanup?)")

    # 3. the dataset must actually contain the survey (the whole point)
    for inst, rows in by_inst.items():
        if not rows:
            continue
        n_cols = len(rows[0])
        if n_cols < 40:
            hard.append(f"{inst}: only {n_cols} columns — this looks like the "
                        f"old shared-dimension subset, not a master dataset")

    # 3. join integrity: an F3 case's facility block must exist among F1 cases
    f1_fac = {r["facility_id"] for r in by_inst.get("f1", [])}
    for r in by_inst.get("f3", []):
        if r["facility_id"] not in f1_fac:
            hard.append(f"f3 case {r['case_key']}: facility block "
                        f"{r['facility_id']} has no matching F1 case")

    # 4. F2 joins by qn; a blank key cannot join at all (soft — pre-QN rows are
    #    a known legacy class, and ASPSI needs to see how many there are)
    f2_nokey = [r for r in by_inst.get("f2", []) if not r["case_key"]]
    if f2_nokey:
        soft.append(f"f2: {len(f2_nokey)} of {f2_got} submissions have no qn "
                    f"(pre-QN enrollments) — they carry facility_id but cannot "
                    f"join to F1/F3/F4 on case_key")

    # 5. sex domain, where the harmonized dimension was captured
    for r in all_clean:
        s = r.get("sex")
        if r["_source_instrument"] != "f2" and s not in (None, "", "1", "2"):
            hard.append(f"{r['_source_instrument']} {r['case_key']}: sex "
                        f"'{s}' outside canonical domain {{1,2}}")

    # 6. case-key uniqueness within an instrument (soft: partial+complete pairs)
    seen = {}
    for r in all_clean:
        if not r["case_key"]:
            continue
        k = (r["_source_instrument"], r["case_key"])
        seen[k] = seen.get(k, 0) + 1
    for (inst, key), n in seen.items():
        if n > 1:
            soft.append(f"{inst}: case key {key} appears {n}x (duplicate entry "
                        f"or partial+complete pair — conflict policy §B4)")

    soft += [n for n in qa_notes if n.startswith(("[key]", "[roster]", "[f2]"))]
    return hard, soft


def main():
    args = sys.argv[1:]
    run_date = (args[args.index("--date") + 1] if "--date" in args
                else datetime.date.today().isoformat())
    base = Path(__file__).parent
    raw_dir = base / "raw" / run_date
    out_dir = base / "out" / run_date
    out_dir.mkdir(parents=True, exist_ok=True)

    if "--skip-extract" in args and raw_dir.exists():
        counts = {}
        for db in ALL_DBS:
            d = raw_dir / db
            if not d.exists():
                continue
            counts[db] = {p.stem: max(0, sum(1 for _ in open(p, encoding="utf-8",
                                                             errors="replace")) - 1)
                          for p in d.glob("*.tsv")}
    else:
        print("extracting F1/F3/F4 breakouts + csweb_f2 ...")
        counts = extract_csweb.extract(raw_dir)
    for db, t in counts.items():
        print(f"  {db}: {sum(t.values())} rows across {len(t)} tables")

    qa_notes, all_clean, widths, roster_counts = [], [], {}, {}

    for inst in INSTRUMENTS:
        clean, rosters = transform_instrument(raw_dir, inst, qa_notes)
        all_clean += clean
        cols = write_csv(out_dir / f"{inst}_clean.csv", clean)
        widths[inst] = len(cols)
        for tname, rows in rosters.items():
            if rows:
                write_csv(out_dir / f"{inst}__{tname}.csv", rows)
                roster_counts[f"{inst}.{tname}"] = len(rows)
        print(f"  {inst}: {len(clean)} cases x {len(cols)} columns"
              + (f"  + rosters {list(rosters)}" if rosters else ""))

    f2_clean = transform_f2(raw_dir, qa_notes)
    if f2_clean:
        all_clean += f2_clean
        cols = write_csv(out_dir / "f2_clean.csv", f2_clean)
        widths["f2"] = len(cols)
        print(f"  f2: {len(f2_clean)} submissions x {len(cols)} columns")

    shared = to_shared_dimensions(all_clean, qa_notes)
    write_csv(out_dir / "shared_dimensions.csv", shared)

    hard, soft = qa_gates(all_clean, counts, qa_notes)

    # names Stata cannot take — reported, never silently truncated
    over = {}
    for inst in list(INSTRUMENTS) + (["f2"] if f2_clean else []):
        rows = [r for r in all_clean if r["_source_instrument"] == inst]
        names = long_names(rows)
        if names:
            over[inst] = names

    report = [f"# QA report — run {run_date}", "",
              f"Codebook v{CODEBOOK_VERSION} · FULL-VARIABLE master dataset "
              f"(all four instruments)", "",
              "## Dataset shape", ""]
    report += [f"- **{i}** — {len([r for r in all_clean if r['_source_instrument'] == i])} "
               f"cases x {w} columns" for i, w in widths.items()]
    report += [f"- roster **{k}** — {v} rows" for k, v in roster_counts.items()]
    report += ["", "## Hard gates" if hard else "## Hard gates: ALL PASS"]
    report += [f"- FAIL {h}" for h in hard]
    report += ["", "## Soft flags"] + ([f"- {s}" for s in soft] or ["- none"])
    report += ["", f"## Variable names over Stata's {STATA_NAME_MAX}-char limit"]
    if over:
        report += ["", "Not truncated here: shortening can collide, and the "
                       "renaming rule is ASPSI's call once the handoff format "
                       "is agreed. Harmless for CSV; blocks .dta.", ""]
        for inst, names in over.items():
            report += [f"- **{inst}** ({len(names)}):"] + [f"    - `{n}`" for n in names]
    else:
        report += ["- none"]
    report += ["", "## Open with ASPSI",
               "- Handoff format: CSV (emitted now) or Stata `.dta`? "
               "Our Stata is 12 SE, so `.dta` must be format <=115.",
               "- Who attaches the sampling weights (facility / patient / "
               "household / HCW `wf`)? We carry the design variables through "
               "untouched; nobody has applied weights yet."]
    (out_dir / "qa_report.md").write_text("\n".join(report), encoding="utf-8")

    manifest = {
        "run_date": run_date,
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "codebook_version": CODEBOOK_VERSION,
        "purpose": "master dataset for ASPSI data processing (scope 2026-07-13)",
        "extract": {"mechanism": "csweb breakout MySQL + csweb_f2 (etl-spec §2.1/§2.2)",
                    "source_counts": counts},
        "instruments": {i: {"cases": len([r for r in all_clean
                                          if r["_source_instrument"] == i]),
                            "columns": w} for i, w in widths.items()},
        "rosters": roster_counts,
        "shared_dimension_rows": len(shared),
        "hard_failures": len(hard), "soft_flags": len(soft),
        "stata_long_names": {i: len(n) for i, n in over.items()},
        "weights_applied": False,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                           encoding="utf-8")
    print(f"\nQA: {len(hard)} hard failures, {len(soft)} soft flags "
          f"-> {out_dir / 'qa_report.md'}")
    sys.exit(1 if hard else 0)


if __name__ == "__main__":
    main()
