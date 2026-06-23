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

Refresh cron: */15 * * * * cd /opt/app && python3 /opt/csweb-map-gen.py >> /var/log/csweb-map.log 2>&1
Vendored libs (no CDN JS): /docs/assets/{leaflet.css,leaflet.js,MarkerCluster*.css,leaflet.markercluster.js}.
First built 2026-06-21 (v1); v2 + v3 same day.
"""
import subprocess, json, datetime, html, math, re
from collections import defaultdict

ENV = "/opt/app/.env"
COMPOSE_DIR = "/opt/app"
OUT = "/opt/app/lamp/www/docs/map.html"
AREAS_PATH = "/opt/app/lamp/www/docs/assets/ph-areas.json"

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

# cols: qnum, lat, lon, region, prov, status, facility, date, accuracy, satellites
COLS = ["qnum", "lat", "lon", "region", "prov", "status", "facility", "date", "acc", "sat"]


def src_q(db, gps_tbl, lat_c, lon_c, acc_c, sat_c, date_c):
    return (
        "SELECT %s, g.%s, g.%s,"
        " COALESCE(NULLIF(fc.region_name,''),'(unknown)'),"
        " COALESCE(NULLIF(fc.province_name,''),'(unknown)'),"
        " %s, COALESCE(fn.name,'(unlabeled)'),"
        " COALESCE(CAST(fc.%s AS CHAR),''), g.%s, g.%s"
        " FROM `%s`.`level-1` l"
        " JOIN `%s`.cases c ON c.id=l.`case-id` AND c.deleted=0"
        " LEFT JOIN `%s`.%s g ON g.`level-1-id`=l.`level-1-id`"
        " LEFT JOIN `%s`.field_control fc ON fc.`level-1-id`=l.`level-1-id`"
        " LEFT JOIN csweb_reports.facility_names fn ON fn.code9=%s"
        % (QN, lat_c, lon_c, STATUS, date_c, acc_c, sat_c,
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
    r = subprocess.run(
        ["docker", "compose", "exec", "-T", "database", "mysql", "-uroot",
         "-p" + rootpw(), "--batch", "-N", "-e", sql],
        cwd=COMPOSE_DIR, capture_output=True, text=True)
    return [ln.split("\t") for ln in r.stdout.splitlines() if ln.strip()]


def fnum(s):
    if s is None or s in ("", "\\N", "NULL"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def norm(s):
    return " ".join(sorted(re.sub(r"[^a-z0-9 ]", " ", (s or "").lower()).split()))


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
            "region": rec["region"], "prov": rec["prov"], "status": rec["status"],
            "facility": rec["facility"], "qnum": rec["qnum"],
            "date": rec["date"] if rec["date"] and rec["date"] != "\\N" else "",
            "acc": None if acc is None else round(acc, 1),
            "sat": None if sat is None else int(sat),
            "qaLow": bool(low), "qaDup": False,
            "qaFarHome": False, "qaClusterOut": False,
            "qaFarCentroid": False, "qaOutArea": False,
            "homeKm": None, "clusterKm": None, "provKm": None, "inArea": None,
        })
        regions.add(rec["region"])

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
  .lp b{color:var(--gd)}.lp .k{color:var(--muted);font-size:12px}.lp .qa{color:var(--red);font-weight:600}
  footer{padding:8px 20px;color:var(--muted);font-size:12px;background:var(--card);border-top:1px solid var(--line)}
  footer a{color:var(--g)}
</style>
</head>
<body>
<header><h1>UHC Survey Year 2 — Map Report</h1><div class="s">Synced CAPI cases plotted by captured GPS · F1 / F3 / F4 · with field-QA flags</div></header>
<div class="filters">
  <div class="f"><label for="fInst">Instrument</label><select id="fInst"></select></div>
  <div class="f"><label for="fRegion">Region</label><select id="fRegion"></select></div>
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
</div>
<div class="bar">
  <span class="chip">Plotted: <b id="cPlotted">0</b></span>
  <span class="badge" id="cNofix"></span>
  <span class="badge" id="cBad" style="display:none"></span>
  <span class="badge warn" id="cLow" style="display:none"></span>
  <span class="badge warn" id="cDup" style="display:none"></span>
  <span class="badge warn" id="cDisp" style="display:none"></span>
  <span class="badge warn" id="cArea" style="display:none"></span>
  <span class="legend">
    <span><i class="sw dot" style="background:#006b3f"></i>Completed</span>
    <span><i class="sw dot" style="background:#e5b23b"></i>Partial</span>
    <span><i class="sw dot" style="background:#9aa7a0"></i>Facility/HH</span>
    <span><i class="sw dia" style="background:#9aa7a0"></i>Patient home</span>
    <span><i class="sw flag"></i>QA flag</span>
  </span>
</div>
<div id="map"></div>
<footer>Generated <span id="gen"></span> · auto-refreshes ~every 15 min · tiles © OpenStreetMap contributors · QA: low accuracy (&gt;<span id="tAcc"></span> m / &lt;<span id="tSat"></span> sat), duplicate respondent location, displacement (home &gt;<span id="tHome"></span> km from facility / facility off its cluster), wrong area (outside declared province) · admin areas © faeldon PH JSON maps (2011) · see also the <a href="/docs/dashboard.html">Sync Dashboard</a>.</footer>
<script type="application/json" id="map-data">__PAYLOAD__</script>
<script>
const P = JSON.parse(document.getElementById('map-data').textContent);
document.getElementById('gen').textContent = P.generated;
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
      statSel=document.getElementById('fStatus'), qaSel=document.getElementById('fQa'),
      fromInp=document.getElementById('fFrom'), toInp=document.getElementById('fTo'),
      lPrimary=document.getElementById('lPrimary'), lHome=document.getElementById('lHome'),
      lConn=document.getElementById('lConn');
[['ALL','All instruments'],['f1','F1 · Facility Head'],['f3','F3 · Patient'],['f4','F4 · Household']]
  .forEach(([v,t])=>instSel.add(new Option(t,v)));
regSel.add(new Option('All regions','ALL')); P.regions.forEach(r=>regSel.add(new Option(r,r)));
[['ALL','All statuses'],['Completed','Completed'],['Partial','Partial']].forEach(([v,t])=>statSel.add(new Option(t,v)));
[['ALL','All points'],['flag','Flagged (any)'],['low','Low accuracy'],['dup','Duplicate location'],
 ['disp','Displacement'],['area','Wrong area']].forEach(([v,t])=>qaSel.add(new Option(t,v)));
if(P.dateMin){fromInp.min=P.dateMin;toInp.min=P.dateMin;}
if(P.dateMax){fromInp.max=P.dateMax;toInp.max=P.dateMax;}

const map = L.map('map');
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  {maxZoom:19, attribution:'© OpenStreetMap'}).addTo(map);
const cluster = L.markerClusterGroup({chunkedLoading:true, maxClusterRadius:45});
const lines = L.layerGroup();
map.addLayer(cluster); map.addLayer(lines);
const PH = [12.5, 122.0];

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
  return '<div class="lp"><b>'+esc(p.facility)+'</b><br>'
    +'<span class="k">'+esc(NAMES[p.inst])+' · '+esc(LAYER[p.layer])+'</span><br>'
    +'Q#: '+esc(p.qnum)+'<br>Status: '+esc(p.status)+'<br>'
    +'Declared: '+esc(p.prov)+'<br>Visited: '+d+'<br>'
    +'GPS: '+(p.acc==null?'—':esc(p.acc)+' m')+(p.sat==null?'':', '+esc(p.sat)+' sat')+qa+'</div>';
}
function chip(id,n,label){const e=document.getElementById(id); if(n>0){e.style.display='';e.textContent='⚠ '+n+' '+label;}else{e.style.display='none';}}
function render(){
  const inst=instSel.value, region=regSel.value, status=statSel.value, qa=qaSel.value;
  const fromY=fromInp.value?fromInp.value.replace(/-/g,''):'';
  const toY=toInp.value?toInp.value.replace(/-/g,''):'';
  const pass=p=>{
    if(inst!=='ALL' && p.inst!==inst) return false;
    if(p.layer==='home' ? !lHome.checked : !lPrimary.checked) return false;
    if(region!=='ALL' && p.region!==region) return false;
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
  if(shown.length){map.fitBounds(cluster.getBounds().pad(0.2));}else{map.setView(PH,6);}
}
[instSel,regSel,statSel,qaSel,fromInp,toInp].forEach(el=>el.onchange=render);
[lPrimary,lHome,lConn].forEach(el=>el.onchange=render);
document.getElementById('fReset').onclick=()=>{instSel.value='ALL';regSel.value='ALL';statSel.value='ALL';qaSel.value='ALL';fromInp.value='';toInp.value='';lPrimary.checked=true;lHome.checked=true;lConn.checked=false;render();};
render();
</script>
</body>
</html>
"""

out_html = TEMPLATE.replace("__PAYLOAD__", payload).replace("__FAVICON__", FAVICON)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(out_html)
cnt = lambda k: sum(1 for p in points if p[k])
print("wrote %s (%d bytes); points=%d home=%d | QA low=%d dup=%d farHome=%d clusterOut=%d farCentroid=%d outArea=%d | areas=%s unmatched=%s"
      % (OUT, len(out_html), len(points), sum(1 for p in points if p["layer"] == "home"),
         cnt("qaLow"), cnt("qaDup"), cnt("qaFarHome"), cnt("qaClusterOut"),
         cnt("qaFarCentroid"), cnt("qaOutArea"),
         "%dR/%dP" % (len(REG), len(PROV)), sorted(unmatched)))
