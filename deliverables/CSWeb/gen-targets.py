#!/usr/bin/env python3
r"""Build targets.json — the per-EA-facility sample targets that the monitoring
surfaces divide completed cases by (Phase 2 coverage-vs-target).

Source: deliverables/CSPro/data/assignments/assignments-source.csv (tracked; no
credentials) — one row per EA-facility assignment with a `target_count`. Grouped by
(instrument, 9-digit facility code). Region/province are enriched from the DOH
facility masterlist (F1/facility_lookup.dat, gitignored) IF present, so the province
choropleth can shade even facilities that have zero synced cases yet; when absent,
the dashboard/map fall back to the case-derived province at runtime.

targets.json is a shippable artifact (like the generators): scp it to /opt/ next to
csweb-dashboard-gen.py / csweb-map-gen.py. It carries only facility-level targets +
public facility name/area — no credentials, no PII. Coverage numbers are meaningless
until ASPSI's real EA plan replaces the R6 fixture rows in assignments-source.csv;
this generator re-runs to pick that up (same file).

Usage:
  python gen-targets.py            # repo defaults -> data/assignments/targets.json
  python gen-targets.py --assignments <csv> --lookup <facility_lookup.dat> --out <json>
First built 2026-07-06 (Phase 2).
"""
import csv, json, argparse, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent                             # .../deliverables
ASSIGN = REPO / "CSPro" / "data" / "assignments" / "assignments-source.csv"
LOOKUP = REPO / "CSPro" / "F1" / "facility_lookup.dat"   # gitignored; enrich if present
OUT = REPO / "CSPro" / "data" / "assignments" / "targets.json"

# fixed-width layout of facility_lookup.dat (see data/facilities/build_facility_lookup.py)
LK = {"code": (0, 9), "region": (9, 49), "province": (49, 109), "name": (109, 229)}


def load_lookup(path):
    """code9 -> {region, province, name} from the DOH masterlist .dat, if present."""
    m = {}
    p = Path(path)
    if not p.exists():
        return m
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if len(line) < 9:
            continue
        code = line[LK["code"][0]:LK["code"][1]].strip()
        if not (code.isdigit() and len(code) == 9):
            continue
        m[code] = {
            "region":   line[LK["region"][0]:LK["region"][1]].strip(),
            "province": line[LK["province"][0]:LK["province"][1]].strip(),
            "name":     line[LK["name"][0]:LK["name"][1]].strip(),
        }
    return m


def build(assignments_path, lookup_path):
    lk = load_lookup(lookup_path)
    targets = {"f1": {}, "f3": {}, "f4": {}}
    n = 0
    with open(assignments_path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            code = (row.get("ea_facility_code") or "").strip()
            inst = (row.get("instrument") or "").strip().lower()
            if inst not in targets or not code:
                continue
            try:
                tgt = int(float(row.get("target_count") or 0))
            except ValueError:
                tgt = 0
            code = code.zfill(9)
            info = lk.get(code, {})
            rec = targets[inst].setdefault(code, {
                "name": info.get("name") or (row.get("ea_name") or "").strip(),
                "region": info.get("region", ""),
                "province": info.get("province", ""),
                "target": 0,
            })
            rec["target"] += tgt          # sum if a facility has multiple assignment rows
            n += 1
    return targets, n


def main():
    ap = argparse.ArgumentParser(description="Build targets.json for coverage-vs-target.")
    ap.add_argument("--assignments", default=str(ASSIGN))
    ap.add_argument("--lookup", default=str(LOOKUP), help="facility_lookup.dat (optional enrichment)")
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--plan-label", default="R6 fixture (placeholder)",
                    help="human name for this assignment plan, shown on the monitoring surfaces")
    # Provisional is the DEFAULT and --final must be typed deliberately. Coverage % divided by
    # a placeholder plan looks exactly like real coverage; the monitoring surfaces are the
    # evidentiary basis for the DOH timeline case, so a plan is a placeholder until a human
    # says otherwise — never the reverse.
    ap.add_argument("--final", action="store_true",
                    help="declare this ASPSI's real EA plan (removes the PROVISIONAL warning)")
    a = ap.parse_args()
    targets, n = build(a.assignments, a.lookup)
    facilities = {k: len(v) for k, v in targets.items()}
    payload = {
        "generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "plan": {
            "label": a.plan_label,
            "provisional": not a.final,
            "source": Path(a.assignments).name,
            "assignments": n,
            "facilities": facilities,
        },
        "targets": targets,
    }
    Path(a.out).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    enriched = any(r["province"] for inst in targets.values() for r in inst.values())
    print("wrote %s | rows=%d facilities: f1=%d f3=%d f4=%d | province-enriched=%s | plan=%s"
          % (a.out, n, facilities["f1"], facilities["f3"], facilities["f4"],
             "yes (facility_lookup.dat)" if enriched else "no (runtime case-derived)",
             "FINAL" if a.final else "PROVISIONAL — " + a.plan_label))


if __name__ == "__main__":
    main()
