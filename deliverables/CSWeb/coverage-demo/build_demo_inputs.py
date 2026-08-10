#!/usr/bin/env python3
"""Build a REAL F1 targets.json (target = sampled facilities per province, from
facility_lookup.dat) + an ILLUSTRATIVE completed-count fixture, so csweb-map-gen.py
--sample renders the real coverage choropleth off-box. No prod, no MySQL."""
import json
from pathlib import Path

LOOKUP = Path(r"C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/F1/facility_lookup.dat")
WD = Path(r"C:/Users/analy/.claude/jobs/228d3e51/tmp/mapdemo")

# fixed-width layout (chars) — same as gen-targets.py LK
LK = {"code": (0, 9), "region": (9, 49), "province": (49, 109), "name": (109, 229)}

# count sampled facilities per province  ->  the REAL F1 denominator
prov_region = {}
prov_count = {}
for line in LOOKUP.read_text(encoding="utf-8", errors="replace").splitlines():
    if len(line) < 109:
        continue
    code = line[LK["code"][0]:LK["code"][1]].strip()
    if not (code.isdigit() and len(code) == 9):
        continue
    region = line[LK["region"][0]:LK["region"][1]].strip()
    prov = line[LK["province"][0]:LK["province"][1]].strip()
    if not prov:
        continue
    prov_count[prov] = prov_count.get(prov, 0) + 1
    prov_region.setdefault(prov, region)

# targets.json — one entry per province, keyed by province (coverage sums by norm(prov))
targets_f1 = {}
for prov, cnt in prov_count.items():
    targets_f1[prov] = {"name": prov, "region": prov_region.get(prov, ""), "province": prov, "target": cnt}

targets = {
    "generated": "2026-07-15 DEMO",
    "plan": {
        "label": "DEMO — F1 target = sampled facilities/province (REAL, facility_lookup.dat) · completed = ILLUSTRATIVE",
        "provisional": False,
        "source": "facility_lookup.dat (1,521 facilities)",
        "facilities": {"f1": len(targets_f1), "f3": 0, "f4": 0},
    },
    "targets": {"f1": targets_f1, "f3": {}, "f4": {}},
}
(WD / "targets-demo.json").write_text(json.dumps(targets, ensure_ascii=False, indent=1), encoding="utf-8")

# ILLUSTRATIVE completed counts -> deterministic spread across red/amber/green.
# ratio bucket chosen by sorted-province index so the map shows the full gradient.
ratios = [1.00, 0.62, 0.28, 0.88, 0.45, 0.10, 0.95, 0.72, 0.35, 0.00, 0.55, 0.80]
completed_f1 = {}
for i, prov in enumerate(sorted(prov_count)):
    r = ratios[i % len(ratios)]
    completed_f1[prov] = round(prov_count[prov] * r)

fixture = {"points": [], "completed_prov": {"f1": completed_f1, "f3": {}, "f4": {}}}
(WD / "fixture-demo.json").write_text(json.dumps(fixture, ensure_ascii=False, indent=1), encoding="utf-8")

# report
tot_fac = sum(prov_count.values())
tot_comp = sum(completed_f1.values())
print(f"provinces={len(prov_count)}  facilities(F1 targets)={tot_fac}  illustrative completed={tot_comp}")
print("top provinces (target / illustrative completed / pct):")
for prov in sorted(prov_count, key=lambda p: -prov_count[p])[:8]:
    t = prov_count[prov]; c = completed_f1[prov]
    print(f"  {prov:28s} {t:4d} / {c:4d}  = {round(100*c/t)}%")
