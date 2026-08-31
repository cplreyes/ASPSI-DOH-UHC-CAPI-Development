#!/usr/bin/env python3
r"""Generate a static, FILTERABLE Map Report from the CSWeb breakout DBs and
write it to the CSWeb docs site. Spatial sibling of csweb-dashboard-gen.py.
Runs ON the box (host python3 + docker compose exec to MySQL). No new service —
served by the existing site at https://csweb.asiansocial.org/docs/map.html.

v1: one marker per case at its captured GPS point, colored by Case Status,
marker-clustered, same filter bar as the dashboard (Instrument / Region /
Status / Visit-date range). No-fix cases counted in a badge, not plotted;
out-of-PH-bounds coords dropped as bad and tallied separately.

v2: F3 dual points (facility + patient-home as toggleable layers + connector),
plus QA flags — low accuracy (acc>50 m or sat<4; sat<=0 treated as unreported)
and duplicate location (identical per-respondent coords across cases).

v3 (2026-06-21) — displacement / wrong-area QA:
  TIER A (self-referential, no external data):
   * far-home: F3 patient-home > A_HOME_KM from its own facility point.
   * facility-cluster outlier: a facility point > CLUSTER_KM from the centroid
     of >=CLUSTER_MIN cases sharing the same facility code (wrong-location signal).
  TIER B (centroid distance): point > its DECLARED province's own radius from
     that province's centroid (province match by name; region fallback).
  TIER C (point-in-polygon): point positively falls inside a DIFFERENT province
     than declared (robust to lowres border imprecision — only asserts on a
     positive containment elsewhere). Reads /docs/assets/ph-areas.json (built by
     gen-ph-boundaries.py; faeldon 2011 lowres). Unmatched province names log +
     fall back to region level; missing asset => Tier B/C skipped gracefully.

GPS lives in dedicated breakout tables keyed on level-1-id: F1/F3
rec_facility_capture.facility_gps_*, F3 rec_patient_home_capture.p_home_gps_*,
F4 household_geo_id.latitude/longitude + hh_gps_*. Coords are varchar(12) ->
cast to decimal. questionnaire_number drops its leading zero -> LPAD(...,12,'0').
Geo CODES are survey-internal (not PSGC) so area joins are by NAME.

Refresh cron (tightened 2026-06-26, was */15): */2 * * * * flock -n /tmp/csweb-map.lock bash -c "cd /opt/app && python3 /opt/csweb-map-gen.py" >> /var/log/csweb-map.log 2>&1
Vendored libs (no CDN JS): /docs/assets/{leaflet.css,leaflet.js,MarkerCluster*.css,leaflet.markercluster.js}.
First built 2026-06-21 (v1); v2 + v3 same day.
"""
import subprocess, json, datetime, html, math, re, argparse
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import portal_shell as PS
from collections import defaultdict

# Phase 2 (2026-07-06): province coverage choropleth (completed ÷ target). Adds a
# --sample mode (off-box: q() returns nothing, coverage comes from the fixture) so
# the choropleth can be built/verified without MySQL. On-box Leaflet render = Carl's gate.
_ap = argparse.ArgumentParser(description="Generate the CSWeb Map Report.")
_ap.add_argument("--sample", help="off-box dev: JSON fixture (points/completed_prov) instead of MySQL")
_ap.add_argument("--targets", default="/opt/targets.json", help="targets.json for the coverage choropleth")
_ap.add_argument("--areas", default="/opt/app/lamp/www/docs/assets/ph-areas.json")
# Portal docroot since Slice 3 (2026-08-09) — see csweb-dashboard-gen.py OUT.
_ap.add_argument("--out", default="/opt/app/capi-www/projects/uhc-y2/monitoring/map/index.html")
_ap.add_argument("--facility-coords", default="/opt/facility_coords.csv",
                 help="geocoded facility coordinates CSV (code9 -> lat/lon + confidence)")
_ap.add_argument("--manual-coords", default="/opt/app/lamp/www/docs/data/facility_coords_manual.csv",
                 help="RA-entered facility coordinates + awaiting-list municipality labels; web-writable "
                      "(coords.php edits it from the map UI), read here each run")
ARGS = _ap.parse_args()
SAMPLE = json.load(open(ARGS.sample, encoding="utf-8")) if ARGS.sample else None

ENV = "/opt/app/.env"
COMPOSE_DIR = "/opt/app"
OUT = ARGS.out
AREAS_PATH = ARGS.areas
TARGETS_PATH = ARGS.targets

# PH coordinate sanity bounds (drops garbage pins; counted as "bad")
LAT_MIN, LAT_MAX = 4.5, 21.5
LON_MIN, LON_MAX = 116.0, 127.0

# QA thresholds
ACC_MAX = 50.0    # m; above = low accuracy
SAT_MIN = 4       # satellites; below = low accuracy (sat<=0 = unreported)
DUP_DP = 5        # coord rounding for duplicate-location (~1.1 m)
A_HOME_KM = 50.0  # F3 patient-home vs its facility
CLUSTER_KM = 5.0  # facility point vs same-facility cluster centroid
CLUSTER_MIN = 3   # cases needed at a facility to judge an outlier

STATUS = ("CASE WHEN c.partial_save_mode IS NULL OR c.partial_save_mode=''"
          " THEN 'Completed' ELSE 'Partial' END")
QN = "LPAD(l.`questionnaire_number`,12,'0')"
CODE9 = "LEFT(LPAD(l.`questionnaire_number`,12,'0'),9)"
# enumerator attribution (mirrors csweb-dashboard-gen.py): the typed FIELD_CONTROL name plus
# the STABLE key — the CSWeb login that UPLOADED the case, via cases.last_modified_revision =
# cspro_sync_history.revision (direction 'put'). revision is that table's PK, so the join is
# 1:1 (no row fan-out). Lets the Map Report filter to one enumerator, same as the dashboard.
ENUM = "COALESCE(NULLIF(fc.enumerator_s_name,''),'(unassigned)')"
SYNCUSER = "COALESCE(NULLIF(sh.username,''),'(unknown)')"
SYNC_JOIN = (" LEFT JOIN csweb_uhc_y2.cspro_sync_history sh"
             " ON sh.revision = c.last_modified_revision AND sh.direction = 'put'")

# cols: qnum, lat, lon, region, prov, status, facility, date, accuracy, satellites, enumerator, syncuser
COLS = ["qnum", "lat", "lon", "region", "prov", "status", "facility", "date", "acc", "sat", "enumerator", "syncuser"]


def src_q(db, gps_tbl, lat_c, lon_c, acc_c, sat_c, date_c):
    # SYNC_JOIN is concatenated INSIDE the parens BEFORE the % so the whole string formats as one
    # unit — `%` binds tighter than `+`, so "..."+SYNC_JOIN % (...) would try (and fail) to format
    # SYNC_JOIN, which has no placeholders. ENUM/SYNCUSER carry no %s either; passed as args.
    return (
        ("SELECT %s, g.%s, g.%s,"
         " COALESCE(NULLIF(fc.region_name,''),'(unknown)'),"
         " COALESCE(NULLIF(fc.province_name,''),'(unknown)'),"
         " %s, COALESCE(fn.name,'(unlabeled)'),"
         " COALESCE(CAST(fc.%s AS CHAR),''), g.%s, g.%s, %s, %s"
         " FROM `%s`.`level-1` l"
         " JOIN `%s`.cases c ON c.id=l.`case-id` AND c.deleted=0"
         " LEFT JOIN `%s`.%s g ON g.`level-1-id`=l.`level-1-id`"
         " LEFT JOIN `%s`.field_control fc ON fc.`level-1-id`=l.`level-1-id`"
         " LEFT JOIN csweb_reports.facility_names fn ON fn.code9=%s"
         + SYNC_JOIN)
        % (QN, lat_c, lon_c, STATUS, date_c, acc_c, sat_c, ENUM, SYNCUSER,
           db, db, db, gps_tbl, db, CODE9)
    )


SOURCES = [
    ("f1", "facility", True,
     src_q("csweb_f1_breakout", "rec_facility_capture",
           "facility_gps_latitude", "facility_gps_longitude",
           "facility_gps_accuracy", "facility_gps_satellites",
           "date_first_visited_the_facility")),
    ("f3", "facility", True,
     src_q("csweb_f3_breakout", "rec_facility_capture",
           "facility_gps_latitude", "facility_gps_longitude",
           "facility_gps_accuracy", "facility_gps_satellites",
           "date_first_visited")),
    ("f3", "home", False,
     src_q("csweb_f3_breakout", "rec_patient_home_capture",
           "p_home_gps_latitude", "p_home_gps_longitude",
           "p_home_gps_accuracy", "p_home_gps_satellites",
           "date_first_visited")),
    ("f4", "household", True,
     src_q("csweb_f4_breakout", "household_geo_id",
           "latitude", "longitude",
           "hh_gps_accuracy", "hh_gps_satellites",
           "date_first_visited")),
]
DUP_LAYERS = {"home", "household"}


def rootpw():
    with open(ENV) as f:
        for line in f:
            if line.startswith("MYSQL_ROOT_PASSWORD"):
                return line.split("=", 1)[1].strip()
    raise SystemExit("MYSQL_ROOT_PASSWORD not found in " + ENV)


def q(sql):
    if SAMPLE is not None:          # off-box: no MySQL; data comes from the fixture
        return []
    r = subprocess.run(
        ["docker", "compose", "exec", "-T", "database", "mysql", "-uroot",
         "-p" + rootpw(), "--batch", "-N", "-e", sql],
        cwd=COMPOSE_DIR, capture_output=True, text=True)
    return [ln.split("\t") for ln in r.stdout.splitlines() if ln.strip()]


def load_targets(path):
    """(targets, plan). No `plan` block (pre-provenance targets.json) => PROVISIONAL.
    Same fail-safe as the dashboard: a shaded province looks equally authoritative
    whether the denominator is ASPSI's EA plan or a leftover fixture."""
    try:
        obj = json.load(open(path, encoding="utf-8"))
    except Exception:
        return {}, {}
    plan = obj.get("plan") or {"label": "unlabelled targets.json", "provisional": True}
    plan.setdefault("provisional", True)
    return obj.get("targets", {}), plan


def fnum(s):
    if s is None or s in ("", "\\N", "NULL"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def norm(s):
    return " ".join(sorted(re.sub(r"[^a-z0-9 ]", " ", (s or "").lower()).split()))


# ---- region label harmonization ----
# The case data (CSWeb sync) and the facility masterlist (targets.json) spell regions
# differently — sync emits "Region IV-A (CALABARZON)", targets emits "REGION 4-A". Left raw,
# the same region shows TWICE in the filter and the exact-match filter splits the point layer
# from the facility layer. canon_region() maps any spelling (Roman/Arabic, named/acronym) to one
# canonical label so each region appears once and the filter selects both layers. The named
# labels are also the form ph-areas.json keys on (via token-sorted norm()), so the point
# area-QA fallback keeps resolving region centroids.
_ROMAN = [("xiii", "13"), ("xii", "12"), ("xi", "11"), ("viii", "8"), ("vii", "7"),
          ("vi", "6"), ("iv", "4"), ("ix", "9"), ("iii", "3"), ("ii", "2"),
          ("v", "5"), ("x", "10"), ("i", "1")]
REGION_LABELS = {
    "1": "Region I (Ilocos Region)", "2": "Region II (Cagayan Valley)",
    "3": "Region III (Central Luzon)", "4A": "Region IV-A (CALABARZON)",
    "4B": "Region IV-B (MIMAROPA)", "5": "Region V (Bicol Region)",
    "6": "Region VI (Western Visayas)", "7": "Region VII (Central Visayas)",
    "8": "Region VIII (Eastern Visayas)", "9": "Region IX (Zamboanga Peninsula)",
    "10": "Region X (Northern Mindanao)", "11": "Region XI (Davao Region)",
    "12": "Region XII (SOCCSKSARGEN)", "13": "Region XIII (Caraga)",
    "NCR": "NCR", "CAR": "CAR", "BARMM": "BARMM", "NIR": "NIR",
}


def _region_code(s):
    if not s:
        return ""
    low = " " + re.sub(r"[^a-z0-9]+", " ", s.lower()).strip() + " "
    if "national capital" in low or " ncr " in low:
        return "NCR"
    if "cordillera" in low or " car " in low:
        return "CAR"
    if "bangsamoro" in low or " barmm " in low or " armm " in low or "muslim mindanao" in low:
        return "BARMM"
    if "negros island" in low or " nir " in low:
        return "NIR"
    if "calabarzon" in low:
        return "4A"
    if "mimaropa" in low:
        return "4B"
    m = re.search(r" region\s+0*([0-9]{1,2})\s*([ab])?\b", low) or re.search(r"\b0*([0-9]{1,2})\s*([ab])?\b", low)
    if m:
        return m.group(1) + (m.group(2).upper() if m.group(2) else "")
    for rom, ar in _ROMAN:
        m = re.search(r"\b" + rom + r"\s*([ab])?\b", low)
        if m:
            return ar + (m.group(1).upper() if m.group(1) else "")
    return ""


def canon_region(s):
    """Canonical region label for any spelling; falls back to the raw string if unrecognized."""
    return REGION_LABELS.get(_region_code(s), (s or "").strip())


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    p = math.pi / 180
    dlat = (lat2 - lat1) * p
    dlon = (lon2 - lon1) * p
    x = math.sin(dlat / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


def pip_area(lat, lon, area):
    """ray-cast point-in-polygon over an area's polys (rings = [[lat,lon],...]);
    even-odd across rings handles holes."""
    for poly in area["polys"]:
        c = False
        for ring in poly:
            n = len(ring)
            j = n - 1
            for i in range(n):
                yi, xi = ring[i][0], ring[i][1]
                yj, xj = ring[j][0], ring[j][1]
                if ((yi > lat) != (yj > lat)) and \
                   (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi):
                    c = not c
                j = i
        if c:
            return True
    return False


# ---- pull point rows ----
points = []
regions = set()
nofix = {}
bad = {}
totals = {}
for inst, layer, primary, sql in SOURCES:
    try:
        rows = [dict(zip(COLS, r)) for r in q(sql)]
    except Exception:
        rows = []
    if primary:
        totals[inst] = len(rows)
        nofix.setdefault(inst, 0)
        bad.setdefault(inst, 0)
    for rec in rows:
        lat, lon = fnum(rec["lat"]), fnum(rec["lon"])
        if lat is None or lon is None:
            if primary:
                nofix[inst] += 1
            continue
        if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
            if primary:
                bad[inst] += 1
            continue
        acc, sat = fnum(rec["acc"]), fnum(rec["sat"])
        if sat is not None and sat <= 0:   # 0 sats = unreported, not a poor fix
            sat = None
        low = (acc is not None and acc > ACC_MAX) or (sat is not None and sat < SAT_MIN)
        points.append({
            "inst": inst, "layer": layer,
            "lat": round(lat, 6), "lon": round(lon, 6),
            "region": canon_region(rec["region"]), "prov": rec["prov"], "status": rec["status"],
            "facility": rec["facility"], "qnum": rec["qnum"],
            "enumerator": rec.get("enumerator", ""), "syncuser": rec.get("syncuser", ""),
            "date": rec["date"] if rec["date"] and rec["date"] != "\\N" else "",
            "acc": None if acc is None else round(acc, 1),
            "sat": None if sat is None else int(sat),
            "qaLow": bool(low), "qaDup": False,
            "qaFarHome": False, "qaClusterOut": False,
            "qaFarCentroid": False, "qaOutArea": False,
            "homeKm": None, "clusterKm": None, "provKm": None, "inArea": None,
        })
        regions.add(canon_region(rec["region"]))

# ---- duplicate location (per-respondent layers only) ----
keymap = {}
for p in points:
    if p["layer"] in DUP_LAYERS:
        keymap.setdefault((round(p["lat"], DUP_DP), round(p["lon"], DUP_DP)), set()).add(p["qnum"])
for p in points:
    if p["layer"] in DUP_LAYERS and len(keymap.get((round(p["lat"], DUP_DP), round(p["lon"], DUP_DP)), ())) > 1:
        p["qaDup"] = True

# ---- Tier A: F3 facility<->home displacement ----
pairs = defaultdict(dict)
for p in points:
    if p["inst"] == "f3":
        pairs[p["qnum"]][p["layer"]] = p
for o in pairs.values():
    f, h = o.get("facility"), o.get("home")
    if f and h:
        d = haversine(f["lat"], f["lon"], h["lat"], h["lon"])
        h["homeKm"] = round(d, 1)
        if d > A_HOME_KM:
            h["qaFarHome"] = True

# ---- Tier A: facility-cluster outlier ----
clusters = defaultdict(list)
for p in points:
    if p["layer"] == "facility":
        clusters[p["qnum"][:9]].append(p)
for pts in clusters.values():
    if len(pts) >= CLUSTER_MIN:
        clat = sum(x["lat"] for x in pts) / len(pts)
        clon = sum(x["lon"] for x in pts) / len(pts)
        for x in pts:
            d = haversine(x["lat"], x["lon"], clat, clon)
            x["clusterKm"] = round(d, 1)
            if d > CLUSTER_KM:
                x["qaClusterOut"] = True

# ---- Tier B/C: declared-area distance + wrong-area containment ----
try:
    AREAS = json.load(open(AREAS_PATH))
except Exception:
    AREAS = {"regions": {}, "provinces": {}}
PROV = AREAS.get("provinces", {})
REG = AREAS.get("regions", {})
unmatched = set()
for p in points:
    pkey, rkey = norm(p["prov"]), norm(p["region"])
    declared = PROV.get(pkey)
    pool, dkey = PROV, pkey
    if not declared:
        if p["prov"] and p["prov"] != "(unknown)" and pkey not in PROV:
            unmatched.add(p["prov"])
        declared = REG.get(rkey)
        pool, dkey = REG, rkey
    if not declared:
        continue
    d = haversine(p["lat"], p["lon"], declared["centroid"][0], declared["centroid"][1])
    p["provKm"] = round(d, 1)
    if d > declared["radius_km"]:
        p["qaFarCentroid"] = True
    cont = None
    for a in pool.values():
        if pip_area(p["lat"], p["lon"], a):
            cont = a
            break
    if cont and norm(cont["name"]) != dkey:
        p["qaOutArea"] = True
        p["inArea"] = cont["name"]

# ---- Phase 2: province coverage (completed ÷ target) for the choropleth ----
targets, plan = load_targets(TARGETS_PATH)
_COMP_SQL = {
    inst: ("SELECT COALESCE(NULLIF(fc.province_name,''),'(unknown)'), COUNT(*)"
           " FROM csweb_%s_breakout.`level-1` l"
           " JOIN csweb_%s_breakout.cases c ON c.id=l.`case-id` AND c.deleted=0"
           " LEFT JOIN csweb_%s_breakout.field_control fc ON fc.`level-1-id`=l.`level-1-id`"
           " WHERE (c.partial_save_mode IS NULL OR c.partial_save_mode='') GROUP BY 1"
           % (inst, inst, inst))
    for inst in ("f1", "f3", "f4")
}
completed_prov = {"f1": {}, "f3": {}, "f4": {}}
if SAMPLE is not None:
    for inst, d in (SAMPLE.get("completed_prov") or {}).items():
        completed_prov[inst] = {k: int(v) for k, v in d.items()}
else:
    for inst, sql in _COMP_SQL.items():
        try:
            for prov, cnt in q(sql):
                completed_prov[inst][prov] = int(cnt)
        except Exception:
            pass
coverage = {"f1": {}, "f3": {}, "f4": {}}
for inst in ("f1", "f3", "f4"):
    for code, t in (targets.get(inst) or {}).items():      # targets by province
        prov = (t.get("province") or "").strip()
        if not prov:
            continue
        rec = coverage[inst].setdefault(norm(prov), {"name": prov, "target": 0, "completed": 0})
        rec["target"] += int(t.get("target") or 0)
    for prov, cnt in completed_prov[inst].items():          # completed by province
        if not prov or prov == "(unknown)":
            continue
        rec = coverage[inst].setdefault(norm(prov), {"name": prov, "target": 0, "completed": 0})
        rec["completed"] += cnt
# ship polygons only for the provinces we actually shade (present in ph-areas.json)
_shade = set(k for inst in coverage.values() for k in inst)
prov_polys = {k: {"name": PROV[k]["name"], "polys": PROV[k]["polys"]} for k in _shade if k in PROV}
has_coverage = bool(targets)

# ---- UHC facilities layer (Option A, 2026-07-27): every planned facility as a pin —
# VISITED = its real captured GPS (centroid of that facility's facility-layer points);
# PENDING = its declared province/region centroid from ph-areas.json (APPROXIMATE, flagged
# as such in the popup). Masterlist = union of code9s in targets.json (the coverage plan) +
# any code9 that already has a facility point (visited-but-unplanned). NO new SQL — assembled
# from `points` + `targets` + `AREAS` already loaded above. Facilities without any location
# (pending + province/region unmatched in ph-areas.json) are counted, not plotted.
fac_pts = defaultdict(list)
for _p in points:
    if _p["layer"] == "facility":
        fac_pts[_p["qnum"][:9]].append(_p)
fac_src = {}
for _inst in ("f1", "f3", "f4"):
    for _code, _t in (targets.get(_inst) or {}).items():
        _m = fac_src.setdefault(_code, {"name": "", "region": "", "prov": "", "insts": set(), "target": 0})
        _m["name"] = _m["name"] or (_t.get("name") or "")
        _m["region"] = _m["region"] or (_t.get("region") or "")
        _m["prov"] = _m["prov"] or (_t.get("province") or "")
        _m["insts"].add(_inst)
        _m["target"] += int(_t.get("target") or 0)
for _code9, _pts in fac_pts.items():
    _m = fac_src.setdefault(_code9, {"name": "", "region": "", "prov": "", "insts": set(), "target": 0})
    if not _m["name"]:
        _m["name"] = next((x["facility"] for x in _pts if x["facility"] and x["facility"] != "(unlabeled)"), "")
    if not _m["region"]:
        _m["region"] = next((x["region"] for x in _pts if x["region"] and x["region"] != "(unknown)"), "")
    if not _m["prov"]:
        _m["prov"] = next((x["prov"] for x in _pts if x["prov"] and x["prov"] != "(unknown)"), "")
    _m["insts"] |= {x["inst"] for x in _pts}
# Exact facility coordinates — code9 -> (lat, lon, source). source is "doh" (DOH National
# Health Facility Registry, official coordinates — authoritative) or "geocoded" (OpenStreetMap
# facility match, ~the building). Placement ladder per facility: captured on-site GPS (ground
# truth) > DOH-registry exact > OSM-geocoded exact. Facilities with no exact fix are NOT
# scattered at a province centroid (Carl 2026-07-28: exact pins only, no centroids) — they are
# counted as "awaiting exact location" and their real GPS lands on the first field visit.
import csv as _csv
GEO_COORDS = {}
try:
    with open(ARGS.facility_coords, encoding="utf-8", newline="") as _gf:
        for _r in _csv.DictReader(_gf):
            if _r.get("confidence") == "high" and _r.get("lat") and _r.get("lon"):
                _srcv = (_r.get("source") or "geocoded").strip().lower()
                GEO_COORDS[_r["code9"]] = (round(float(_r["lat"]), 6), round(float(_r["lon"]), 6),
                                           "doh" if _srcv == "doh" else "geocoded")
except Exception:
    GEO_COORDS = {}

# Manual (RA-entered) coordinates + municipality labels for the awaiting list. This file is the
# RA fill-in template: one row per facility (code9,facility_name,municipality,province,region,
# lat,lon,note). A row with a valid lat/lon becomes a MANUAL pin (ranks just below on-site GPS —
# a human deliberately placed it); every row's municipality feeds the "awaiting exact location"
# list (targets.json has no municipality). Never auto-regenerated, so RA edits persist.
MANUAL_COORDS, MANUAL_MUNI = {}, {}
try:
    with open(ARGS.manual_coords, encoding="utf-8-sig", newline="") as _mf:
        for _r in _csv.DictReader(_mf):
            _c = (_r.get("code9") or "").strip()
            if not _c:
                continue
            if _r.get("municipality"):
                MANUAL_MUNI[_c] = _r["municipality"].strip()
            _la, _lo = (_r.get("lat") or "").strip(), (_r.get("lon") or "").strip()
            if _la and _lo:
                try:
                    _laf, _lof = float(_la), float(_lo)
                    if LAT_MIN <= _laf <= LAT_MAX and LON_MIN <= _lof <= LON_MAX:
                        MANUAL_COORDS[_c] = (round(_laf, 6), round(_lof, 6))
                except ValueError:
                    pass
except FileNotFoundError:
    pass

facilities = []
awaiting = []
fac_meta = {"total": 0, "visited": 0, "manual": 0, "doh": 0, "geocoded": 0, "pending": 0, "noloc": 0}
for _code9, _m in sorted(fac_src.items()):
    _fp = fac_pts.get(_code9, [])
    _done = len(_fp) > 0
    fac_meta["total"] += 1
    fac_meta["visited" if _done else "pending"] += 1
    if _done:
        _lat = round(sum(x["lat"] for x in _fp) / len(_fp), 6)
        _lon = round(sum(x["lon"] for x in _fp) / len(_fp), 6)
        _placed = "gps"
    elif _code9 in MANUAL_COORDS:
        _lat, _lon = MANUAL_COORDS[_code9]
        _placed = "manual"
        fac_meta["manual"] += 1
    elif _code9 in GEO_COORDS:
        _lat, _lon, _placed = GEO_COORDS[_code9]
        fac_meta[_placed] += 1                    # "doh" or "geocoded"
    else:
        fac_meta["noloc"] += 1                    # no exact fix — not plotted (no centroid)
        awaiting.append({
            "code9": _code9, "name": _m["name"] or "(unlabeled facility)",
            "muni": MANUAL_MUNI.get(_code9, ""),
            "region": canon_region(_m["region"]) or "(unknown)", "prov": _m["prov"] or "(unknown)",
            "insts": sorted(_m["insts"]),
        })
        continue
    facilities.append({
        "code9": _code9, "name": _m["name"] or "(unlabeled facility)",
        "region": canon_region(_m["region"]) or "(unknown)", "prov": _m["prov"] or "(unknown)",
        "insts": sorted(_m["insts"]), "target": _m["target"],
        "lat": _lat, "lon": _lon, "placed": _placed, "done": _done,
        "nCases": len(_fp), "nCompleted": sum(1 for x in _fp if x["status"] == "Completed"),
    })
awaiting.sort(key=lambda a: (a["region"], a["prov"], a["muni"], a["name"]))
for _f in facilities:                       # make pending-facility regions selectable in the filter
    if _f["region"] and _f["region"] != "(unknown)":
        regions.add(_f["region"])
for _a in awaiting:                          # awaiting facilities' regions belong in the filter too
    if _a["region"] and _a["region"] != "(unknown)":
        regions.add(_a["region"])

# ---- visit-date bounds ----
_valid = [p["date"] for p in points
          if p["date"].isdigit() and len(p["date"]) == 8 and p["date"] != "00000000"]
_iso = lambda d: d[:4] + "-" + d[4:6] + "-" + d[6:8]
date_min = _iso(min(_valid)) if _valid else ""
date_max = _iso(max(_valid)) if _valid else ""

payload_obj = {
    "points": points, "regions": sorted(regions),
    "nofix": nofix, "bad": bad, "totals": totals,
    "thresh": {"acc": ACC_MAX, "sat": SAT_MIN, "home": A_HOME_KM, "cluster": CLUSTER_KM},
    "dateMin": date_min, "dateMax": date_max,
    "coverage": coverage, "provPolys": prov_polys, "hasCoverage": has_coverage, "plan": plan,
    "facilities": facilities, "facMeta": fac_meta, "awaiting": awaiting,
    "generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
}
payload = html.escape(json.dumps(payload_obj), quote=False)

FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'%3E"
           "%3Crect width='40' height='40' rx='8' fill='%23006b3f'/%3E"
           "%3Cpath d='M20 9l9 5v12l-9 5-9-5V14z' fill='%23e5b23b'/%3E%3C/svg%3E")

TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta name="robots" content="noindex" />
<link rel="icon" href="__FAVICON__" />
<title>UHC Survey Year 2 — Map Report</title>
<link rel="stylesheet" href="/docs/assets/leaflet.css" />
<link rel="stylesheet" href="/docs/assets/MarkerCluster.css" />
<link rel="stylesheet" href="/docs/assets/MarkerCluster.Default.css" />
<script src="/docs/assets/leaflet.js"></script>
<script src="/docs/assets/leaflet.markercluster.js"></script>
<style>
  :root{--g:#006b3f;--gd:#004d2c;--gold:#e5b23b;--red:#d32f2f;--ink:#1c2b25;--muted:#5b6b63;--line:#dfe7e2;--bg:#f4f7f5;--card:#fff}
  *{box-sizing:border-box}html,body{margin:0;height:100%}
  body{font:15px/1.5 system-ui,Segoe UI,Roboto,sans-serif;color:var(--ink);background:var(--bg);display:flex;flex-direction:column}
  header{background:var(--g);color:#fff;padding:14px 24px}
  header h1{margin:0;font-size:20px;letter-spacing:-.01em}
  header .s{opacity:.85;font-size:13px;margin-top:3px}
  .filters{display:flex;flex-wrap:wrap;gap:12px 14px;align-items:end;background:var(--card);border-bottom:1px solid var(--line);padding:10px 20px}
  .filters .f{display:flex;flex-direction:column;gap:3px}
  .filters label{font-size:11px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
  .filters select,.filters input{font:14px system-ui;padding:6px 9px;border:1px solid var(--line);border-radius:8px;background:#fff;min-width:148px}
  .filters .reset{margin-left:auto;align-self:end;font:13px system-ui;padding:8px 14px;border:1px solid var(--line);border-radius:8px;background:#fff;cursor:pointer}
  .filters .reset:hover{background:var(--bg)}
  .layers{display:flex;gap:14px;align-items:center;padding:7px 20px;background:#eef3f0;border-bottom:1px solid var(--line);font-size:13px;flex-wrap:wrap}
  .layers label{display:inline-flex;gap:6px;align-items:center;cursor:pointer;font-weight:600;color:var(--ink)}
  .bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:8px 20px;background:var(--bg);border-bottom:1px solid var(--line);font-size:13px}
  .chip{background:#fff;border:1px solid var(--line);border-radius:20px;padding:4px 12px;font-weight:600}
  .chip b{color:var(--g)}
  .badge{background:#fffaf0;border:1px solid var(--gold);border-radius:20px;padding:4px 12px;color:#6b5418}
  .badge.warn{background:#fdecea;border-color:var(--red);color:#9b1c14}
  .legend{margin-left:auto;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
  .legend span{display:inline-flex;align-items:center;gap:6px}
  .sw{width:13px;height:13px;display:inline-block;border:2px solid #fff;box-shadow:0 0 0 1px rgba(0,0,0,.3)}
  .sw.dot{border-radius:50%}.sw.dia{border-radius:2px;transform:rotate(45deg)}
  .sw.flag{border-radius:50%;background:#bbb;box-shadow:0 0 0 1px #fff,0 0 0 3px var(--red)}
  #map{flex:1;min-height:300px}
  html:fullscreen,html:-webkit-full-screen{width:100%;height:100%;overflow:hidden}
  html:fullscreen body,html:-webkit-full-screen body{height:100%}
  .leaflet-control-fs a{display:flex;align-items:center;justify-content:center;font-size:0}
  .leaflet-control-fs svg{stroke:#333;width:16px;height:16px}
  .leaflet-control-loc a{display:flex;align-items:center;justify-content:center;font-size:0}
  .leaflet-control-loc svg{stroke:#333;width:18px;height:18px}
  .leaflet-control-loc a.on svg{stroke:#1a73e8}
  .leaflet-control-loc a.busy{opacity:.55;pointer-events:none}
  .myloc{display:block;width:16px;height:16px;border-radius:50%;background:#1a73e8;border:3px solid #fff;
    box-shadow:0 0 0 1px rgba(0,0,0,.3),0 0 10px 2px rgba(26,115,232,.55)}
  .dist{color:#1a73e8;font-weight:700}
  .lp b{color:var(--gd)}.lp .k{color:var(--muted);font-size:12px}.lp .qa{color:var(--red);font-weight:600}
  footer{padding:8px 20px;color:var(--muted);font-size:12px;background:var(--card);border-top:1px solid var(--line)}
  footer a{color:var(--g)}
  #cFac a{color:var(--g);font-weight:600;text-decoration:underline;cursor:pointer}
  .awdim{position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:1200;display:none;align-items:center;justify-content:center}
  .awbox{background:#fff;width:min(720px,94vw);max-height:86vh;display:flex;flex-direction:column;border-radius:10px;box-shadow:0 10px 40px rgba(0,0,0,.3);overflow:hidden}
  .awhead{display:flex;gap:10px;align-items:center;padding:12px 16px;border-bottom:1px solid var(--line);background:var(--bg)}
  .awhead b{color:var(--gd)} .awhead .awn{color:var(--muted);font-size:13px;font-weight:600}
  .awhead #awClose{margin-left:auto;border:1px solid var(--line);background:#fff;border-radius:6px;width:30px;height:30px;cursor:pointer;font-size:15px;line-height:1}
  .awtools{display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding:8px 16px;border-bottom:1px solid var(--line)}
  .awbtn{display:inline-flex;align-items:center;gap:5px;border:1px solid var(--line);background:#fff;border-radius:6px;padding:6px 10px;cursor:pointer;font-size:12.5px;font-weight:600;color:var(--gd)}
  .awbtn:hover{background:var(--bg)}
  .awtools #awSearch{margin-left:auto;padding:6px 10px;border:1px solid var(--line);border-radius:6px;font-size:13px;width:220px;max-width:44vw}
  .awstatus{padding:0 16px;font-size:12.5px;color:var(--muted);min-height:0;transition:padding .1s}
  .awstatus:not(:empty){padding:8px 16px}
  .awstatus.ok{color:#046a38;font-weight:600} .awstatus.err{color:var(--red);font-weight:600}
  .awlist{overflow:auto;padding:6px 0}
  .awgrp{padding:8px 16px 2px;font-weight:700;color:var(--gd);font-size:13px;position:sticky;top:0;background:#fff;border-bottom:1px solid var(--line)}
  .awrow{display:grid;grid-template-columns:1fr auto;gap:8px 10px;align-items:center;padding:7px 16px;border-bottom:1px solid #f0f2f0;font-size:13px}
  .awrow .nm{font-weight:600;color:var(--ink)} .awrow .mu{color:var(--muted);font-size:12px}
  .awentry{display:flex;gap:5px;align-items:center}
  .awentry input{width:78px;padding:5px 7px;border:1px solid var(--line);border-radius:6px;font-size:12.5px}
  .awentry input:focus{outline:none;border-color:var(--g)}
  .awentry .awsave{border:1px solid var(--g);background:var(--g);color:#fff;border-radius:6px;padding:5px 10px;cursor:pointer;font-size:12.5px;font-weight:600}
  .awentry .awsave:disabled{opacity:.5;cursor:default}
  .awfoot{padding:8px 16px;border-top:1px solid var(--line);color:var(--muted);font-size:11.5px;background:var(--bg)}
  .awfoot a{color:var(--g)}
</style>
</head>
<body>
<header><h1>UHC Survey Year 2 — Map Report</h1><div class="s">Synced CAPI cases plotted by captured GPS · F1 / F3 / F4 · with field-QA flags</div></header>
<div class="filters">
  <div class="f"><label for="fInst">Instrument</label><select id="fInst"></select></div>
  <div class="f"><label for="fRegion">Region</label><select id="fRegion"></select></div>
  <div class="f"><label for="fEnum">Enumerator</label><select id="fEnum"></select></div>
  <div class="f"><label for="fStatus">Status</label><select id="fStatus"></select></div>
  <div class="f"><label for="fQa">Data quality</label><select id="fQa"></select></div>
  <div class="f"><label for="fFrom">Visit from</label><input type="date" id="fFrom" /></div>
  <div class="f"><label for="fTo">Visit to</label><input type="date" id="fTo" /></div>
  <button class="reset" id="fReset" type="button">Reset</button>
</div>
<div class="layers">
  <span style="color:var(--muted);font-weight:600;text-transform:uppercase;font-size:11px;letter-spacing:.04em">Layers</span>
  <label><input type="checkbox" id="lPrimary" checked /> Facility / Household</label>
  <label><input type="checkbox" id="lHome" checked /> F3 patient home</label>
  <label><input type="checkbox" id="lConn" /> Connect F3 pairs</label>
  <label><input type="checkbox" id="lCoverage" /> Coverage % (choropleth)</label>
  <label><input type="checkbox" id="lFac" /> UHC facilities</label>
  <select id="fFacSt" title="Facility status" style="font:13px system-ui;padding:4px 8px;border:1px solid var(--line);border-radius:7px;background:#fff"></select>
</div>
<div class="bar">
  <span class="chip">Data as of <b id="fresh"></b></span>
  <span class="chip">Plotted: <b id="cPlotted">0</b></span>
  <span class="badge" id="cNofix"></span>
  <span class="badge" id="cBad" style="display:none"></span>
  <span class="badge warn" id="cLow" style="display:none"></span>
  <span class="badge warn" id="cDup" style="display:none"></span>
  <span class="badge warn" id="cDisp" style="display:none"></span>
  <span class="badge warn" id="cArea" style="display:none"></span>
  <span class="badge" id="covLegend" style="display:none">Coverage: <i class="sw" style="background:#d32f2f"></i>&lt;40% <i class="sw" style="background:#e5b23b"></i>40–79% <i class="sw" style="background:#006b3f"></i>&ge;80%</span>
  <span class="badge" id="covPlan" style="display:none;background:#fdf3d7;border-color:#e5b23b;color:#6b5200;font-weight:700"></span>
  <span class="chip" id="cFac" style="display:none"></span>
  <span class="legend">
    <span><i class="sw dot" style="background:#006b3f"></i>Completed</span>
    <span><i class="sw dot" style="background:#e5b23b"></i>Partial</span>
    <span><i class="sw dot" style="background:#9aa7a0"></i>Facility/HH</span>
    <span><i class="sw dia" style="background:#9aa7a0"></i>Patient home</span>
    <span><i class="sw flag"></i>QA flag</span>
    <span><i class="sw" style="border-radius:2px;background:#046a38"></i>Facility · on-site GPS</span>
    <span><i class="sw" style="border-radius:2px;background:#8e44ad"></i>Facility · manual</span>
    <span><i class="sw" style="border-radius:2px;background:#2563a8"></i>Facility · DOH registry</span>
    <span><i class="sw" style="border-radius:2px;background:#d08b2c"></i>Facility · geocoded</span>
  </span>
</div>
<div id="map"></div>
<div class="awdim" id="awDim">
  <div class="awbox">
    <div class="awhead">
      <b>Facilities awaiting exact location</b> <span class="awn" id="awN"></span>
      <button id="awClose" title="Close">✕</button>
    </div>
    <div class="awtools">
      <button class="awbtn" id="awDl" title="Download the fill-in CSV template">⬇ Template</button>
      <label class="awbtn" title="Import a filled CSV to place pins">⬆ Import CSV<input type="file" id="awUp" accept=".csv,text/csv" hidden></label>
      <input id="awSearch" placeholder="search name / municipality / province…">
    </div>
    <div class="awstatus" id="awStatus"></div>
    <div class="awlist" id="awList"></div>
    <div class="awfoot">Type a facility's <b>lat / lon</b> and Save — or download the template, fill it, and Import. Saved coordinates become violet pins within ~2 minutes. (Get coordinates by right-clicking the spot in Google Maps → the lat, lon at the top.)</div>
  </div>
</div>
<footer>Generated <span id="gen"></span> · auto-refreshes ~every 2 min · tiles © OpenStreetMap contributors · QA: low accuracy (&gt;<span id="tAcc"></span> m / &lt;<span id="tSat"></span> sat), duplicate respondent location, displacement (home &gt;<span id="tHome"></span> km from facility / facility off its cluster), wrong area (outside declared province) · admin areas © faeldon PH JSON maps (2011) · the UHC-facilities layer plots each facility at its exact location — on-site GPS where visited, else DOH National Health Facility Registry coordinates, else an OpenStreetMap geocode; facilities without an exact fix are not pinned (their GPS is captured on the first visit) · see also the <a href="/projects/uhc-y2/monitoring/">Sync Dashboard</a>.</footer>
<script type="application/json" id="map-data">__PAYLOAD__</script>
<script>
const P = JSON.parse(document.getElementById('map-data').textContent);
document.getElementById('gen').textContent = P.generated;
document.getElementById('fresh').textContent = P.generated;
document.getElementById('tAcc').textContent = P.thresh.acc;
document.getElementById('tSat').textContent = P.thresh.sat;
document.getElementById('tHome').textContent = P.thresh.home;
const NAMES = {f1:'F1 · Facility Head', f3:'F3 · Patient', f4:'F4 · Household'};
const LAYER = {facility:'Facility', home:'Patient home', household:'Household'};
const COLOR = {Completed:'#006b3f', Partial:'#e5b23b'};
const isFlag = p => p.qaLow||p.qaDup||p.qaFarHome||p.qaClusterOut||p.qaFarCentroid||p.qaOutArea;
const isDisp = p => p.qaFarHome||p.qaClusterOut;
const isArea = p => p.qaFarCentroid||p.qaOutArea;

const instSel=document.getElementById('fInst'), regSel=document.getElementById('fRegion'),
      enumSel=document.getElementById('fEnum'),
      statSel=document.getElementById('fStatus'), qaSel=document.getElementById('fQa'),
      fromInp=document.getElementById('fFrom'), toInp=document.getElementById('fTo'),
      lPrimary=document.getElementById('lPrimary'), lHome=document.getElementById('lHome'),
      lConn=document.getElementById('lConn'), lCoverage=document.getElementById('lCoverage'),
      lFac=document.getElementById('lFac'), facStSel=document.getElementById('fFacSt');
[['ALL','All instruments'],['f1','F1 · Facility Head'],['f3','F3 · Patient'],['f4','F4 · Household']]
  .forEach(([v,t])=>instSel.add(new Option(t,v)));
regSel.add(new Option('All regions','ALL')); P.regions.forEach(r=>regSel.add(new Option(r,r)));
[['ALL','All statuses'],['Completed','Completed'],['Partial','Partial']].forEach(([v,t])=>statSel.add(new Option(t,v)));
[['ALL','All points'],['flag','Flagged (any)'],['low','Low accuracy'],['dup','Duplicate location'],
 ['disp','Displacement'],['area','Wrong area']].forEach(([v,t])=>qaSel.add(new Option(t,v)));
[['ALL','All facilities'],['visited','Visited'],['pending','Pending']].forEach(([v,t])=>facStSel.add(new Option(t,v)));
// Enumerator filter — keyed on the CSWeb upload login (syncuser), typed-name fallback; same
// key scheme as the dashboard so a person reads identically on both surfaces.
function enumKeyOf(p){ return (p.syncuser&&p.syncuser!=='(unknown)') ? 'u:'+p.syncuser
                     : (p.enumerator&&p.enumerator!=='(unassigned)') ? 'n:'+p.enumerator : ''; }
enumSel.add(new Option('All enumerators','ALL'));
(function(){
  const em=new Map();
  P.points.forEach(p=>{ const key=enumKeyOf(p); if(!key) return;
    let o=em.get(key); if(!o){o={key,login:(p.syncuser&&p.syncuser!=='(unknown)')?p.syncuser:null,names:{}}; em.set(key,o);}
    if(p.enumerator&&p.enumerator!=='(unassigned)') o.names[p.enumerator]=(o.names[p.enumerator]||0)+1;
  });
  const lbl=o=>{const nm=Object.keys(o.names).sort((a,b)=>o.names[b]-o.names[a])[0]||(o.login?'(no name)':'(unknown)'); return o.login?(nm+' · '+o.login):nm;};
  [...em.values()].map(o=>[o.key,lbl(o)]).sort((a,b)=>a[1].toLowerCase()<b[1].toLowerCase()?-1:1).forEach(([v,t])=>enumSel.add(new Option(t,v)));
})();
if(P.dateMin){fromInp.min=P.dateMin;toInp.min=P.dateMin;}
if(P.dateMax){fromInp.max=P.dateMax;toInp.max=P.dateMax;}

const map = L.map('map');
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  {maxZoom:19, attribution:'© OpenStreetMap'}).addTo(map);

// ---- full-screen control (native Fullscreen API — Leaflet is vendored, so no plugin/CDN) ----
const FS_ENTER='<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3M3 16v3a2 2 0 0 0 2 2h3m8 0h3a2 2 0 0 0 2-2v-3"/></svg>';
const FS_EXIT ='<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3M3 16h3a2 2 0 0 1 2 2v3m8 0v-3a2 2 0 0 1 2-2h3"/></svg>';
let fsLink=null;
// fullscreen the whole page (not just #map) so overlays like the awaiting-list panel — which are
// siblings of #map — still render; a fullscreened #map would hide them behind its backdrop.
const fsEl=document.documentElement;
function fsActive(){return document.fullscreenElement||document.webkitFullscreenElement;}
function toggleFs(){
  if(!fsActive()){ (fsEl.requestFullscreen||fsEl.webkitRequestFullscreen||function(){}).call(fsEl); }
  else { (document.exitFullscreen||document.webkitExitFullscreen||function(){}).call(document); }
}
L.Control.Fullscreen=L.Control.extend({options:{position:'topleft'},
  onAdd:function(){
    const c=L.DomUtil.create('div','leaflet-bar leaflet-control leaflet-control-fs');
    const a=L.DomUtil.create('a','',c); a.href='#'; a.role='button';
    a.title='Full screen'; a.innerHTML=FS_ENTER; fsLink=a;
    L.DomEvent.on(a,'click',L.DomEvent.stop).on(a,'click',toggleFs);
    return c;
  }});
map.addControl(new L.Control.Fullscreen());
['fullscreenchange','webkitfullscreenchange'].forEach(function(ev){
  document.addEventListener(ev,function(){
    const on=!!fsActive();
    if(fsLink){ fsLink.innerHTML=on?FS_EXIT:FS_ENTER; fsLink.title=on?'Exit full screen':'Full screen'; }
    setTimeout(function(){map.invalidateSize();},120);   // let the container resize settle
  });
});

// ---- "awaiting exact location" list panel (opened from the facilities count) ----
const awDim=document.getElementById('awDim'), awListEl=document.getElementById('awList'),
      awN=document.getElementById('awN'), awSearch=document.getElementById('awSearch');
function awMatch(a,q){ if(!q) return true;
  return (a.name||'').toLowerCase().indexOf(q)>=0 || (a.muni||'').toLowerCase().indexOf(q)>=0
      || (a.prov||'').toLowerCase().indexOf(q)>=0 || (a.code9||'').indexOf(q)>=0; }
function renderAwaiting(){
  const all=P.awaiting||[], q=awSearch.value.trim().toLowerCase();
  const list=all.filter(a=>awMatch(a,q));
  awN.textContent=q?(list.length+' of '+all.length):(all.length+' facilities');
  let html='', curr=null;
  list.forEach(a=>{
    if(a.region!==curr){ curr=a.region; html+='<div class="awgrp">'+esc(curr)+'</div>'; }
    html+='<div class="awrow" data-code="'+esc(a.code9)+'">'
      +'<div><div class="nm">'+esc(a.name)+'</div><div class="mu">'
      +esc([a.muni,a.prov].filter(Boolean).join(', '))+' · '+esc(a.code9)+'</div></div>'
      +'<div class="awentry"><input class="awlat" placeholder="lat" inputmode="decimal">'
      +'<input class="awlon" placeholder="lon" inputmode="decimal">'
      +'<button class="awsave" type="button">Save</button></div></div>';
  });
  awListEl.innerHTML=html||'<div class="awrow"><div class="mu">No matches.</div></div>';
}
function openAwaiting(){ renderAwaiting(); awDim.style.display='flex'; awSearch.focus(); }
function closeAwaiting(){ awDim.style.display='none'; }
document.getElementById('awClose').onclick=closeAwaiting;
awDim.onclick=function(e){ if(e.target===awDim) closeAwaiting(); };
awSearch.oninput=renderAwaiting;
document.addEventListener('keydown',function(e){ if(e.key==='Escape'&&awDim.style.display==='flex') closeAwaiting(); });

// ---- coordinate intake: enter lat/lon inline, or download/import the CSV, -> coords.php ----
// ABSOLUTE on purpose: the map is served from /projects/uhc-y2/monitoring/map/ (capi nginx, static)
// since the 2026-08-09 console unification, but coords.php lives on the lamp Apache at /docs/.
// A relative 'coords.php' resolved to a static 404 and surfaced as 'Network error' (#1314).
const COORDS_EP='/docs/coords.php';
function asJson(r){ const ct=r.headers.get('content-type')||'';
  if(ct.indexOf('json')>=0) return r.json();   // coords.php always answers JSON, even on 400/500 (keeps its error text)
  throw new Error(r.ok?'Unexpected reply — sign in again (reload the page)'
    :'HTTP '+r.status+(r.status===401||r.status===403?' — sign in again (reload the page)':'')); }
function netErr(e){ return (e&&/^HTTP /.test(e.message))?e.message:'Network error — is the site reachable?'; }
function awStatus(msg,ok){ const s=document.getElementById('awStatus'); if(!s) return;
  s.textContent=msg||''; s.className='awstatus'+(ok===true?' ok':ok===false?' err':''); }
function downloadTemplate(){
  const cols=['code9','facility_name','municipality','province','region','lat','lon','note'];
  const q=v=>{ v=(v==null?'':''+v); return /[",\n]/.test(v)?'"'+v.replace(/"/g,'""')+'"':v; };
  const lines=[cols.join(',')];
  (P.awaiting||[]).forEach(a=>lines.push([a.code9,a.name,a.muni,a.prov,a.region,'','',''].map(q).join(',')));
  const blob=new Blob(['﻿'+lines.join('\r\n')],{type:'text/csv;charset=utf-8'});
  const url=URL.createObjectURL(blob), a=document.createElement('a');
  a.href=url; a.download='facility_coords_manual.csv'; document.body.appendChild(a); a.click();
  a.remove(); URL.revokeObjectURL(url);
}
function optimisticPin(u){                 // show a violet pin now; the 2-min cron makes it permanent
  const aw=(P.awaiting||[]).find(a=>a.code9===u.code9)||{};
  (P.facilities||[]).push({code9:u.code9, name:u.name||aw.name||u.code9,
    region:aw.region||'(unknown)', prov:aw.prov||'(unknown)', insts:aw.insts||[], target:0,
    lat:+u.lat, lon:+u.lon, placed:'manual', done:false, nCases:0, nCompleted:0});
  P.awaiting=(P.awaiting||[]).filter(a=>a.code9!==u.code9);
  if(P.facMeta){ P.facMeta.manual=(P.facMeta.manual||0)+1; P.facMeta.noloc=Math.max(0,(P.facMeta.noloc||0)-1); }
}
function afterSave(res){
  (res.updated||[]).forEach(optimisticPin);
  render(); renderAwaiting();
  const n=res.updatedCount||0, sk=(res.skipped||[]);
  let msg=n+' coordinate'+(n===1?'':'s')+' saved';
  if(sk.length) msg+=', '+sk.length+' skipped ('+esc(sk[0].reason||'invalid')+')';
  if(n) msg+=' · pins appear within ~2 min';
  awStatus(msg, n>0);
}
function saveRow(code,lat,lon,btn){
  awStatus('Saving…'); if(btn) btn.disabled=true;
  fetch(COORDS_EP,{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({code9:code,lat:lat,lon:lon})})
    .then(asJson).then(res=>{ if(btn) btn.disabled=false;
      if(res.ok) afterSave(res); else awStatus(res.error||'Save failed',false); })
    .catch(function(e){ if(btn) btn.disabled=false; awStatus(netErr(e),false); });
}
function importCsv(file){
  awStatus('Importing '+file.name+'…');
  const fd=new FormData(); fd.append('csv',file,file.name);
  fetch(COORDS_EP,{method:'POST',body:fd}).then(asJson)
    .then(res=>{ if(res.ok) afterSave(res); else awStatus(res.error||'Import failed',false); })
    .catch(function(e){ awStatus(netErr(e),false); });
}
document.getElementById('awDl').onclick=downloadTemplate;
document.getElementById('awUp').onchange=function(e){ const f=e.target.files[0]; if(f) importCsv(f); e.target.value=''; };
awListEl.addEventListener('click',function(e){
  const b=e.target.closest('.awsave'); if(!b) return;
  const row=b.closest('.awrow'); if(!row) return;
  const code=row.getAttribute('data-code');
  const lat=row.querySelector('.awlat').value.trim(), lon=row.querySelector('.awlon').value.trim();
  if(!lat||!lon){ awStatus('Enter both lat and lon for that facility.',false); return; }
  saveRow(code,lat,lon,b);
});
awListEl.addEventListener('keydown',function(e){
  if(e.key==='Enter' && (e.target.classList.contains('awlat')||e.target.classList.contains('awlon'))){
    const row=e.target.closest('.awrow'); if(row){ e.preventDefault(); row.querySelector('.awsave').click(); }
  }
});

// ---- current-location (device geolocation) + straight-line distance to facilities ----
// Works on any device with an HTTPS page (this site) and the user's permission. Auto-requested
// ONCE on load so the DEFAULT map view centres on the device (Carl 2026-07-28); if permission is
// denied/unavailable it fails SILENTLY and the data-bounds view stays as the fallback. A manual
// tap on the crosshair control re-requests it (and DOES surface an error if that fails). While
// active, a blue dot tracks the device; each facility popup then shows its straight-line km from
// you (Google-Maps style), and the facilities counter names the nearest one. Straight-line
// (haversine), not road distance — a planning aid.
const LOC_ICON='<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="3.5"/><line x1="12" y1="1.5" x2="12" y2="5"/><line x1="12" y1="19" x2="12" y2="22.5"/><line x1="1.5" y1="12" x2="5" y2="12"/><line x1="19" y1="12" x2="22.5" y2="12"/></svg>';
let locWatch=null, locMarker=null, locCircle=null, myLoc=null, locLink=null, locFirst=false, locSilent=false, shownFacilities=[];
function haversineKm(a,b){ const R=6371, r=Math.PI/180;
  const dLa=(b[0]-a[0])*r, dLo=(b[1]-a[1])*r, la1=a[0]*r, la2=b[0]*r;
  const h=Math.sin(dLa/2)**2 + Math.cos(la1)*Math.cos(la2)*Math.sin(dLo/2)**2;
  return R*2*Math.asin(Math.sqrt(h)); }
function fmtKm(km){ return km<1 ? Math.round(km*1000)+' m' : km.toFixed(km<10?1:0)+' km'; }
function nearestFacility(){ if(!myLoc) return null;
  const pool=shownFacilities.length?shownFacilities:(P.facilities||[]);
  let best=null,bd=Infinity;
  pool.forEach(function(f){ const d=haversineKm(myLoc,[f.lat,f.lon]); if(d<bd){bd=d;best=f;} });
  return best?{f:best,km:bd}:null; }
const locIcon=L.divIcon({className:'',iconSize:[16,16],iconAnchor:[8,8],popupAnchor:[0,-8],html:'<span class="myloc"></span>'});
function onLoc(pos){
  const la=pos.coords.latitude, lo=pos.coords.longitude, acc=pos.coords.accuracy||0;
  myLoc=[la,lo];
  if(locLink){ locLink.classList.remove('busy'); locLink.classList.add('on'); }
  if(!locMarker){
    locCircle=L.circle(myLoc,{radius:acc,color:'#1a73e8',weight:1,fillColor:'#1a73e8',fillOpacity:.12,interactive:false}).addTo(map);
    locMarker=L.marker(myLoc,{icon:locIcon,zIndexOffset:1000}).addTo(map);
    locMarker.bindPopup(function(){ const nf=nearestFacility();
      return '<div class="lp"><b>Your location</b><br><span class="k">accuracy ±'+Math.round(acc)+' m</span>'
        +(nf?('<br>Nearest facility:<br>'+esc(nf.f.name)+'<br><span class="dist">'+fmtKm(nf.km)+' away</span>'):'')+'</div>'; });
  } else { locMarker.setLatLng(myLoc); locCircle.setLatLng(myLoc).setRadius(acc); }
  if(!locFirst){ locFirst=true; map.setView(myLoc, Math.max(map.getZoom(),13)); locMarker.openPopup(); }
  render(true);  // refresh the "nearest facility" readout WITHOUT refitting the view off the device
}
function onLocErr(e){
  if(locLink){ locLink.classList.remove('busy','on'); }
  const silent = locSilent;
  stopLoc();
  if(silent) return;  // auto-locate on load: stay quiet, keep the default data-bounds view
  const why = e && e.code===1 ? 'permission was denied' : (e && e.code===3 ? 'it timed out' : 'it is unavailable');
  alert('Could not get your location — '+why+'.\nOn a phone/tablet, allow location access for this site and make sure GPS is on.');
}
function startLoc(silent){
  locSilent=!!silent;
  if(!('geolocation' in navigator)){ if(!locSilent) alert('This device/browser does not support location.'); return; }
  if(locLink) locLink.classList.add('busy');
  locFirst=false;
  locWatch=navigator.geolocation.watchPosition(onLoc,onLocErr,{enableHighAccuracy:true,maximumAge:10000,timeout:20000});
}
function stopLoc(){
  if(locWatch!=null){ navigator.geolocation.clearWatch(locWatch); locWatch=null; }
  if(locMarker){ map.removeLayer(locMarker); map.removeLayer(locCircle); locMarker=null; locCircle=null; }
  myLoc=null; locFirst=false; locSilent=false;
  if(locLink) locLink.classList.remove('on','busy');
  render();
}
function toggleLoc(){ if(locWatch!=null||myLoc) stopLoc(); else startLoc(); }
L.Control.Locate=L.Control.extend({options:{position:'topleft'},
  onAdd:function(){
    const c=L.DomUtil.create('div','leaflet-bar leaflet-control leaflet-control-loc');
    const a=L.DomUtil.create('a','',c); a.href='#'; a.role='button';
    a.title='Show my location'; a.innerHTML=LOC_ICON; locLink=a;
    L.DomEvent.on(a,'click',L.DomEvent.stop).on(a,'click',toggleLoc);
    return c;
  }});
map.addControl(new L.Control.Locate());
const cluster = L.markerClusterGroup({chunkedLoading:true, maxClusterRadius:45});
const lines = L.layerGroup();
const covLayer = L.layerGroup();
// Facility layer: one individual pin per facility, NOT clustered — now that facilities carry
// exact coordinates (on-site GPS / DOH registry / geocoded), each sits at its real location, so
// pooling them into count bubbles would hide exactly what the layer is meant to show.
const facLayer = L.layerGroup();
map.addLayer(facLayer); map.addLayer(covLayer); map.addLayer(cluster); map.addLayer(lines);
const PH = [12.5, 122.0];
// --- Phase 2: province coverage choropleth ---
function covColorMap(pct){ return pct==null?'#9aa7a0':(pct>=80?'#006b3f':(pct>=40?'#e5b23b':'#d32f2f')); }
function covForProv(key){
  const inst=instSel.value, insts = inst==='ALL'?['f1','f3','f4']:[inst];
  let t=0,c=0,any=false;
  insts.forEach(k=>{ const r=(P.coverage[k]||{})[key]; if(r){any=true; t+=r.target||0; c+=r.completed||0;} });
  return any?{t,c,pct:(t>0?Math.round(100*c/t):null)}:null;
}
function renderChoropleth(){
  covLayer.clearLayers();
  const on = lCoverage && lCoverage.checked && P.hasCoverage;
  document.getElementById('covLegend').style.display = on?'':'none';
  // A shaded province reads as fact. Say so when the denominator is a placeholder.
  const _pl=P.plan||{}, _cp=document.getElementById('covPlan');
  if(on && _pl.provisional!==false){
    _cp.textContent='PROVISIONAL PLAN ('+(_pl.label||'unlabelled')+') — shading is not real coverage';
    _cp.style.display='';
  } else { _cp.style.display='none'; }
  if(!on) return;
  Object.keys(P.provPolys||{}).forEach(key=>{
    const cov=covForProv(key); if(!cov) return;
    const color=covColorMap(cov.pct), nm=P.provPolys[key].name||key;
    (P.provPolys[key].polys||[]).forEach(poly=>{
      const pg=L.polygon(poly,{color:'#374151',weight:1,fillColor:color,fillOpacity:.45});
      pg.bindPopup('<div class="lp"><b>'+esc(nm)+'</b><br>'+cov.c+' / '+cov.t+' completed'+(cov.pct==null?' (no target)':' ('+cov.pct+'%)')+'</div>');
      covLayer.addLayer(pg);
    });
  });
}

function icon(p){
  const c = COLOR[p.status] || '#5b6b63';
  const ring = isFlag(p) ? '0 0 0 1px #fff,0 0 0 3px #d32f2f' : '0 0 0 1px rgba(0,0,0,.35)';
  const shape = p.layer==='home' ? 'border-radius:2px;transform:rotate(45deg)' : 'border-radius:50%';
  const html='<span style="display:block;width:13px;height:13px;background:'+c+';border:2px solid #fff;box-shadow:'+ring+';'+shape+'"></span>';
  return L.divIcon({className:'', html, iconSize:[15,15], iconAnchor:[7,7], popupAnchor:[0,-7]});
}
function esc(s){const d=document.createElement('div'); d.textContent=(s==null?'':s); return d.innerHTML;}
function popup(p){
  const d = p.date && p.date.length===8 ? p.date.slice(0,4)+'-'+p.date.slice(4,6)+'-'+p.date.slice(6,8) : '—';
  let qa='';
  if(p.qaLow) qa+='<div class="qa">⚠ Low GPS accuracy</div>';
  if(p.qaDup) qa+='<div class="qa">⚠ Duplicate location (possible curbstoning)</div>';
  if(p.qaFarHome) qa+='<div class="qa">⚠ Home '+esc(p.homeKm)+' km from facility</div>';
  if(p.qaClusterOut) qa+='<div class="qa">⚠ Facility point '+esc(p.clusterKm)+' km off its cluster</div>';
  if(p.qaOutArea) qa+='<div class="qa">⚠ Coordinates in '+esc(p.inArea)+', declared '+esc(p.prov)+'</div>';
  else if(p.qaFarCentroid) qa+='<div class="qa">⚠ '+esc(p.provKm)+' km from declared '+esc(p.prov)+'</div>';
  const who = (p.syncuser&&p.syncuser!=='(unknown)')
      ? ((p.enumerator&&p.enumerator!=='(unassigned)')?esc(p.enumerator)+' · ':'')+esc(p.syncuser)
      : (p.enumerator&&p.enumerator!=='(unassigned)'?esc(p.enumerator):'—');
  return '<div class="lp"><b>'+esc(p.facility)+'</b><br>'
    +'<span class="k">'+esc(NAMES[p.inst])+' · '+esc(LAYER[p.layer])+'</span><br>'
    +'Q#: '+esc(p.qnum)+'<br>Status: '+esc(p.status)+'<br>'
    +'Enumerator: '+who+'<br>'
    +'Declared: '+esc(p.prov)+'<br>Visited: '+d+'<br>'
    +'GPS: '+(p.acc==null?'—':esc(p.acc)+' m')+(p.sat==null?'':', '+esc(p.sat)+' sat')+qa+'</div>';
}
function chip(id,n,label){const e=document.getElementById(id); if(n>0){e.style.display='';e.textContent='⚠ '+n+' '+label;}else{e.style.display='none';}}
// ---- UHC facilities layer: a distinct square pin per facility. Colour = location source,
// an authority gradient: green = on-site GPS (ground truth) · blue = DOH NHFR registry (exact,
// official) · amber = OSM-geocoded (exact-ish, verify on site). No centroid pins. ----
function facIcon(f){
  var bg,bd='2px solid #fff',sh='0 0 0 1px rgba(0,0,0,.35)';
  if(f.placed==='gps'){ bg='#046a38'; }         // on-site GPS — ground truth
  else if(f.placed==='manual'){ bg='#8e44ad'; } // RA-entered (hand-verified)
  else if(f.placed==='doh'){ bg='#2563a8'; }    // DOH National Health Facility Registry
  else { bg='#d08b2c'; }                         // OSM-geocoded
  return L.divIcon({className:'',iconSize:[14,14],iconAnchor:[7,7],popupAnchor:[0,-7],
    html:'<span style="display:block;width:12px;height:12px;background:'+bg+';border:'+bd+';box-shadow:'+sh+';border-radius:2px"></span>'});
}
function facPopup(f){
  const insts=f.insts.map(k=>k.toUpperCase()).join(' / ');
  const stat=f.done?('Visited — '+f.nCases+' case'+(f.nCases===1?'':'s')+(f.nCompleted?(', '+f.nCompleted+' completed'):'')):'Pending — not yet visited';
  const loc=f.placed==='gps' ? 'Exact — captured on site'
    : f.placed==='manual' ? 'Exact — manually entered (RA-verified)'
    : f.placed==='doh' ? 'Exact — DOH National Health Facility Registry (official coordinates)'
    : 'Exact-ish — geocoded from OpenStreetMap (facility match); verify against site GPS';
  const dist = myLoc ? ('<br><span class="dist">'+fmtKm(haversineKm(myLoc,[f.lat,f.lon]))+' from your location</span>') : '';
  return '<div class="lp"><b>'+esc(f.name)+'</b><br>'
    +'<span class="k">UHC facility · '+esc(insts)+'</span><br>'
    +'Code: '+esc(f.code9)+'<br>Status: '+esc(stat)+'<br>'
    +'Declared: '+esc(f.prov)+'<br>Location: '+loc+dist+'</div>';
}
function renderFacilities(inst,region){
  facLayer.clearLayers();
  if(!(lFac&&lFac.checked)) return [];
  const fs=facStSel.value;
  const shownF=(P.facilities||[]).filter(f=>{
    if(inst!=='ALL' && f.insts.indexOf(inst)<0) return false;
    if(region!=='ALL' && f.region!==region) return false;
    if(fs==='visited' && !f.done) return false;
    if(fs==='pending' && f.done) return false;
    return true;
  });
  // function-bound popup so the "km from your location" line recomputes each time it opens
  shownF.forEach(f=>facLayer.addLayer(L.marker([f.lat,f.lon],{icon:facIcon(f)}).bindPopup(()=>facPopup(f))));
  shownFacilities=shownF;                      // for the nearest-facility readout
  return shownF;
}
function render(keepView){
  const inst=instSel.value, region=regSel.value, status=statSel.value, qa=qaSel.value, enumK=enumSel.value;
  const fromY=fromInp.value?fromInp.value.replace(/-/g,''):'';
  const toY=toInp.value?toInp.value.replace(/-/g,''):'';
  const pass=p=>{
    if(inst!=='ALL' && p.inst!==inst) return false;
    if(p.layer==='home' ? !lHome.checked : !lPrimary.checked) return false;
    if(region!=='ALL' && p.region!==region) return false;
    if(enumK!=='ALL' && enumKeyOf(p)!==enumK) return false;
    if(status!=='ALL' && p.status!==status) return false;
    if(qa==='low' && !p.qaLow) return false;
    if(qa==='dup' && !p.qaDup) return false;
    if(qa==='disp' && !isDisp(p)) return false;
    if(qa==='area' && !isArea(p)) return false;
    if(qa==='flag' && !isFlag(p)) return false;
    if(fromY||toY){const d=p.date; if(!(d&&d.length===8)) return false; if(fromY&&d<fromY) return false; if(toY&&d>toY) return false;}
    return true;
  };
  cluster.clearLayers(); lines.clearLayers();
  const shown = P.points.filter(pass);
  cluster.addLayers(shown.map(p=>L.marker([p.lat,p.lon],{icon:icon(p)}).bindPopup(popup(p))));
  if(lConn.checked){
    const by={};
    shown.forEach(p=>{ if(p.inst==='f3'){ (by[p.qnum]=by[p.qnum]||{})[p.layer]=p; } });
    Object.values(by).forEach(o=>{ if(o.facility&&o.home){
      lines.addLayer(L.polyline([[o.facility.lat,o.facility.lon],[o.home.lat,o.home.lon]],
        {color:'#5b6b63',weight:1.5,opacity:.6,dashArray:'4,4'})); }});
  }
  document.getElementById('cPlotted').textContent = shown.length;
  const insts = inst==='ALL' ? ['f1','f3','f4'] : [inst];
  const nf = insts.reduce((s,k)=>s+(P.nofix[k]||0),0);
  const bd = insts.reduce((s,k)=>s+(P.bad[k]||0),0);
  document.getElementById('cNofix').textContent = nf+' case'+(nf===1?'':'s')+' not plotted (no GPS fix)';
  const bdEl=document.getElementById('cBad');
  if(bd>0){bdEl.style.display='';bdEl.textContent=bd+' bad coordinate'+(bd===1?'':'s')+' dropped';}else{bdEl.style.display='none';}
  chip('cLow', shown.filter(p=>p.qaLow).length, 'low accuracy');
  chip('cDup', shown.filter(p=>p.qaDup).length, 'duplicate location');
  chip('cDisp', shown.filter(isDisp).length, 'displacement');
  chip('cArea', shown.filter(isArea).length, 'wrong area');
  renderChoropleth();
  const shownF = renderFacilities(inst, region);
  const cFac=document.getElementById('cFac');
  if(lFac.checked){
    const v=shownF.filter(f=>f.placed==='gps').length,
          m=shownF.filter(f=>f.placed==='manual').length,
          d=shownF.filter(f=>f.placed==='doh').length,
          g=shownF.filter(f=>f.placed==='geocoded').length,
          noloc=(P.facMeta&&P.facMeta.noloc)||0;
    const parts=[v+' on-site']; if(m) parts.push(m+' manual'); parts.push(d+' DOH', g+' geocoded');
    const nf = myLoc ? nearestFacility() : null;
    cFac.style.display=''; cFac.innerHTML='Facilities: <b>'+shownF.length+'</b> pinned ('+parts.join(', ')+')'
      +(nf?(' · <span class="dist">nearest: '+esc(nf.f.name)+' ('+fmtKm(nf.km)+')</span>'):'')
      +(noloc?(' · <a href="#" id="awLink">'+noloc+' awaiting exact location</a>'):'');
    const al=document.getElementById('awLink'); if(al) al.onclick=function(e){e.preventDefault();openAwaiting();};
  } else { cFac.style.display='none'; }
  // keepView: the geolocation path (onLoc) calls render() only to refresh the nearest-facility
  // readout while it owns the viewport (centred on / tracking the device) — skip the data-bounds
  // refit so we don't snap the map off the device. Filter changes call render() with no arg and
  // still refit to the visible data as before.
  if(keepView) return;
  let bb = shown.length ? cluster.getBounds() : null;
  if(shownF.length){ const fb=L.latLngBounds(shownF.map(f=>[f.lat,f.lon])); bb = bb ? bb.extend(fb) : fb; }
  if(bb && bb.isValid()){ map.fitBounds(bb.pad(0.2)); } else { map.setView(PH,6); }
}
[instSel,regSel,enumSel,statSel,qaSel,fromInp,toInp,facStSel].forEach(el=>el.onchange=render);
[lPrimary,lHome,lConn,lCoverage,lFac].forEach(el=>el.onchange=render);
document.getElementById('fReset').onclick=()=>{instSel.value='ALL';regSel.value='ALL';enumSel.value='ALL';statSel.value='ALL';qaSel.value='ALL';fromInp.value='';toInp.value='';lPrimary.checked=true;lHome.checked=true;lConn.checked=false;lCoverage.checked=false;lFac.checked=false;facStSel.value='ALL';render();};
render();
// Default the map view to the device's current location (Carl 2026-07-28): auto-request geolocation
// once on load. On success onLoc() re-centres the map on the device (zoom >=13) and starts tracking;
// on denial/timeout/no-support it fails silently (see startLoc/onLocErr) and the data-bounds
// fitBounds view set by render() above remains as the fallback.
if('geolocation' in navigator) startLoc(true);
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Unified portal shell (2026-07-25). The map renders inside the same
# sidebar / topbar / footer chrome as capi.asiansocial.org (shared
# portal_shell). A full-bleed canvas lets the Leaflet map fill the viewport.
# Leaflet CSS/JS, the payload script and all map JS are untouched.
# ---------------------------------------------------------------------------
_DESC = ("Synced CAPI cases plotted by captured GPS \u2014 F1/F3/F4 with field-QA "
         "flags and a coverage choropleth, ASPSI \u00d7 DOH UHC Survey Year 2.")

_MAP_CHROME_RULES = (
    "*{box-sizing:border-box}html,body{margin:0;height:100%}",
    "body{font:15px/1.5 system-ui,Segoe UI,Roboto,sans-serif;color:var(--ink);background:var(--bg);display:flex;flex-direction:column}",
    "header{background:var(--g);color:#fff;padding:14px 24px}",
    "header h1{margin:0;font-size:20px;letter-spacing:-.01em}",
    "header .s{opacity:.85;font-size:13px;margin-top:3px}",
    "footer{padding:8px 20px;color:var(--muted);font-size:12px;background:var(--card);border-top:1px solid var(--line)}",
    "footer a{color:var(--g)}",
)

_LEAFLET_HEAD = ('<link rel="stylesheet" href="/docs/assets/leaflet.css" />\n'
                 '<link rel="stylesheet" href="/docs/assets/MarkerCluster.css" />\n'
                 '<link rel="stylesheet" href="/docs/assets/MarkerCluster.Default.css" />\n'
                 '<script src="/docs/assets/leaflet.js"></script>\n'
                 '<script src="/docs/assets/leaflet.markercluster.js"></script>')


def _shellify_map(t):
    head_part, _, body_part = t.partition("<body>\n")
    _, _, after_header = body_part.partition("</header>\n")
    controls_and_map, _, rest2 = after_header.partition("<footer>")
    footer_inner, _, scripts = rest2.partition("</footer>")
    css = head_part.split("<style>", 1)[1].split("</style>", 1)[0]
    for rule in _MAP_CHROME_RULES:
        css = css.replace(rule, "")
    base = PS.PORTAL_ORIGIN
    crumbs = [("UHC Survey Year 2", PS.P + "/"),
              ("Monitoring", PS.P + "/monitoring/"),
              ("Map", None)]
    # No lock pill -- see csweb-dashboard-gen.py; the identity chip covers it.
    seg = ('<div class="tb-seg"><a href="/projects/uhc-y2/monitoring/">Sync Dashboard</a>'
           '<a class="on" href="/projects/uhc-y2/monitoring/map/">Map</a></div>')
    tb_right = seg
    head_html = PS.head("UHC Survey Year 2 \u2014 Map Report", _DESC, extra_css=css)
    head_html = head_html.replace("</head>", _LEAFLET_HEAD + "\n</head>")
    opened = (head_html + '\n<body>\n<div class="app">\n'
              + PS.sidebar(PS.P + "/monitoring/", base)
              + '\n<div class="main">\n<div class="topbar"><div class="crumbs">'
              + PS.crumbs_html(crumbs, base) + '</div><div class="tb-right">' + tb_right + PS.SIGNOUT_CHIP
              + '</div></div>\n<div class="canvas bleed">\n')
    closed = ('<footer class="page-foot">' + footer_inner + '</footer>\n'
              '</div>\n</div>\n</div>\n')
    out = opened + controls_and_map + closed + PS.SIGNOUT_JS + PS.PERM_DIM_JS + scripts
    out = out.replace("#006b3f", "#046a38").replace("#004d2c", "#04331d")
    return out


TEMPLATE = _shellify_map(TEMPLATE)

out_html = TEMPLATE.replace("__PAYLOAD__", payload).replace("__FAVICON__", FAVICON)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(out_html)
cnt = lambda k: sum(1 for p in points if p[k])
print("wrote %s (%d bytes); points=%d home=%d | QA low=%d dup=%d farHome=%d clusterOut=%d farCentroid=%d outArea=%d | areas=%s unmatched=%s"
      % (OUT, len(out_html), len(points), sum(1 for p in points if p["layer"] == "home"),
         cnt("qaLow"), cnt("qaDup"), cnt("qaFarHome"), cnt("qaClusterOut"),
         cnt("qaFarCentroid"), cnt("qaOutArea"),
         "%dR/%dP" % (len(REG), len(PROV)), sorted(unmatched)))
print("facilities: total=%d visited=%d manual=%d doh=%d geocoded=%d noloc=%d | plotted=%d (gps=%d manual=%d doh=%d geocoded=%d) awaiting=%d"
      % (fac_meta["total"], fac_meta["visited"], fac_meta["manual"], fac_meta["doh"], fac_meta["geocoded"],
         fac_meta["noloc"], len(facilities),
         sum(1 for f in facilities if f["placed"] == "gps"),
         sum(1 for f in facilities if f["placed"] == "manual"),
         sum(1 for f in facilities if f["placed"] == "doh"),
         sum(1 for f in facilities if f["placed"] == "geocoded"), len(awaiting)))
