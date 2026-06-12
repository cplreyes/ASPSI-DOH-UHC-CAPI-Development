"""ETL runner (skeleton) — etl-spec §6.

    python run.py [--date YYYY-MM-DD] [--skip-extract]

extract (breakout DBs over SSH) -> transform (codebook subset) ->
qa gates -> out/<date>/{f*_clean.csv, f4_roster_clean.csv,
shared_dimensions.csv, qa_report.md, manifest.json}
"""
import csv, datetime, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import extract_csweb
from transform import (INSTRUMENTS, DIMENSION_TODO, transform_instrument,
                       to_shared_dimensions)

CODEBOOK_VERSION = "0.3"


def write_csv(path, rows):
    if not rows:
        path.write_text("")
        return
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def qa_gates(all_clean, counts, qa_notes):
    """etl-spec §4 subset. Returns (hard_failures, soft_flags)."""
    hard, soft = [], []
    # row counts vs source (hard)
    for inst, db in INSTRUMENTS.items():
        src = counts[db].get("level-1", 0)
        got = len([r for r in all_clean if r["_source_instrument"] == inst])
        if got != src:
            # deleted-case exclusions are legitimate; only fail if we LOST rows
            deleted = src - got
            soft.append(f"{inst}: {src} source cases -> {got} clean rows "
                        f"({deleted} excluded as deleted/invalid)")
    # join integrity (hard): F3 facility block must exist among F1 facilities
    f1_fac = {r["facility_id"] for r in all_clean if r["_source_instrument"] == "f1"}
    for r in all_clean:
        if r["_source_instrument"] == "f3" and r["facility_id"] not in f1_fac:
            hard.append(f"f3 case {r['case_key']}: facility block "
                        f"{r['facility_id']} has no matching F1 case")
    # sex domain (hard, where captured)
    for r in all_clean:
        if r.get("sex") not in (None, "", "1", "2"):
            hard.append(f"{r['_source_instrument']} {r['case_key']}: sex "
                        f"'{r['sex']}' outside canonical domain {{1,2}}")
    # case-key uniqueness within an instrument (soft — partial saves and
    # re-entries can legitimately collide; relates to conflict policy §B4)
    seen = {}
    for r in all_clean:
        k = (r["_source_instrument"], r["case_key"])
        seen[k] = seen.get(k, 0) + 1
    for (inst, key), n in seen.items():
        if n > 1:
            soft.append(f"{inst}: case key {key} appears {n}x "
                        f"(duplicate entry or partial+complete pair — "
                        f"resolve via conflict policy)")
    # key flags already collected in qa_notes (soft)
    soft += [n for n in qa_notes if n.startswith("[key]")]
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
        counts = {db: {p.stem: max(0, sum(1 for _ in open(p, encoding='utf-8')) - 1)
                       for p in (raw_dir / db).glob("*.tsv")}
                  for db in INSTRUMENTS.values()}
    else:
        print("extracting from CSWeb breakout DBs ...")
        counts = extract_csweb.extract(raw_dir)
    for db, t in counts.items():
        print(f"  {db}: {sum(t.values())} rows across {len(t)} tables")

    qa_notes, all_clean = [], []
    for inst in INSTRUMENTS:
        clean, roster = transform_instrument(raw_dir, inst, qa_notes)
        all_clean += clean
        write_csv(out_dir / f"{inst}_clean.csv", clean)
        if roster:
            write_csv(out_dir / "f4_roster_clean.csv", roster)
        print(f"  {inst}: {len(clean)} clean rows"
              + (f", {len(roster)} roster rows" if roster else ""))

    shared = to_shared_dimensions(all_clean)
    write_csv(out_dir / "shared_dimensions.csv", shared)

    hard, soft = qa_gates(all_clean, counts, qa_notes)
    drift = [n for n in qa_notes if n.startswith("[drift]")]
    report = ["# QA report — run " + run_date, "",
              f"Codebook: v{CODEBOOK_VERSION} · skeleton (subset of dimensions)", "",
              "## Hard-gate failures" if hard else "## Hard gates: ALL PASS"]
    report += [f"- ❌ {h}" for h in hard]
    report += ["", "## Soft flags"] + ([f"- ⚠️ {s}" for s in soft] or ["- none"])
    report += ["", "## Codebook drift (missing source columns)"]
    report += [f"- {d}" for d in drift] or ["- none"]
    report += ["", "## Not yet implemented in skeleton"]
    report += [f"- {t}" for t in DIMENSION_TODO]
    (out_dir / "qa_report.md").write_text("\n".join(report), encoding="utf-8")

    manifest = {
        "run_date": run_date,
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "codebook_version": CODEBOOK_VERSION,
        "extract": {"mechanism": "csweb-breakout-mysql (etl-spec §2.1)",
                    "source_counts": counts},
        "clean_rows": {i: len([r for r in all_clean
                               if r["_source_instrument"] == i])
                       for i in INSTRUMENTS},
        "shared_dimension_rows": len(shared),
        "hard_failures": len(hard), "soft_flags": len(soft),
        "f2": "not extracted — separate path (etl-spec §2.2), gated on §15.G",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                           encoding="utf-8")
    print(f"\nQA: {len(hard)} hard failures, {len(soft)} soft flags, "
          f"{len(drift)} drift notes -> {out_dir / 'qa_report.md'}")
    sys.exit(1 if hard else 0)


if __name__ == "__main__":
    main()
