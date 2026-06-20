#!/usr/bin/env python3
r"""Generate a static, FILTERABLE Sync Dashboard from the CSWeb breakout DBs and
write it to the CSWeb docs site. Runs ON the box (host python3 + docker compose
exec to MySQL). No new service — served by the existing site at
https://csweb.asiansocial.org/docs/dashboard.html.

Embeds one labeled row per synced case (geo/facility/ownership/result/patient-
type/sex) and aggregates + filters CLIENT-SIDE, so the Instrument and Region
filters recompute the charts in the browser. Categorical codes are labeled with
CASE maps from the dcf value sets; facility names via csweb_reports.facility_names
(breakout facility_name is NULL — Android auto-fill blocked).

Refresh: host cron re-runs this (every 15 min). Deploy: scp to /opt/, cron:
  */15 * * * * cd /opt/app && python3 /opt/csweb-dashboard-gen.py >> /var/log/csweb-dashboard.log 2>&1
First built 2026-06-20; filters added 2026-06-20.
"""
import subprocess, json, datetime, html

ENV = "/opt/app/.env"
COMPOSE_DIR = "/opt/app"
OUT = "/opt/app/lamp/www/docs/dashboard.html"

# chart spec per instrument: (row field, chart title, chart type)
SECTIONS = [
    ("F1 — Facility Head Survey", "f1", [
        ("status", "Case Status", "doughnut"),
        ("region", "Cases by Region", "bar"),
        ("facility", "Cases by Facility", "bar"),
        ("ownership", "Ownership", "doughnut"),
        ("service_level", "Service Capacity Level", "bar"),
        ("result", "Result of Visit", "doughnut"),
    ]),
    ("F3 — Patient Survey", "f3", [
        ("status", "Case Status", "doughnut"),
        ("region", "Cases by Region", "bar"),
        ("patient_type", "Patient Type", "doughnut"),
        ("sex", "Sex", "doughnut"),
    ]),
    ("F4 — Household Survey", "f4", [
        ("status", "Case Status", "doughnut"),
        ("region", "Cases by Region", "bar"),
        ("province", "Cases by Province", "bar"),
    ]),
]

# per-case labeled-row queries (one row per non-deleted case)
F1_OWN = "CASE bp.q7_ownership WHEN '1' THEN 'Public' WHEN '2' THEN 'Private' ELSE COALESCE(NULLIF(bp.q7_ownership,''),'(blank)') END"
F1_SVC = ("CASE bp.q8_service_level WHEN '1' THEN 'Primary Care Facility' WHEN '2' THEN 'Level 1 Hospital'"
          " WHEN '3' THEN 'Level 2 Hospital' WHEN '4' THEN 'Level 3 Hospital' ELSE COALESCE(NULLIF(bp.q8_service_level,''),'(blank)') END")
F1_RES = ("CASE fc.enum_result_first_visit WHEN '1' THEN 'Completed' WHEN '2' THEN 'Postponed'"
          " WHEN '3' THEN 'Refused' WHEN '4' THEN 'Incomplete' ELSE COALESCE(NULLIF(fc.enum_result_first_visit,''),'(blank)') END")
F1_CODE9 = ("CONCAT(LPAD(fc.region_code,2,'0'),LPAD(fc.province_huc_code,2,'0'),"
            "LPAD(fc.city_municipality_code,3,'0'),LPAD(fc.facility_no,2,'0'))")

# `date` = visit date (date_first_visited), YYYYMMDD ('' if none) for the date-range filter
# `status` = Completed (fully saved) vs Partial (partial_save_mode set, e.g. 'add')
STATUS = "CASE WHEN c.partial_save_mode IS NULL OR c.partial_save_mode='' THEN 'Completed' ELSE 'Partial' END"
QUERIES = {
    "f1": (["region", "province", "city", "facility", "ownership", "service_level", "result", "date", "status"],
           "SELECT COALESCE(NULLIF(fc.region_name,''),'(unknown)'),"
           " COALESCE(NULLIF(fc.province_name,''),'(unknown)'),"
           " COALESCE(NULLIF(fc.city_name,''),'(unknown)'),"
           " COALESCE(fn.name,'(unlabeled)'), %s, %s, %s,"
           " COALESCE(CAST(fc.date_first_visited_the_facility AS CHAR),''), %s"
           " FROM csweb_f1_breakout.`level-1` l"
           " JOIN csweb_f1_breakout.cases c ON c.id=l.`case-id` AND c.deleted=0"
           " LEFT JOIN csweb_f1_breakout.field_control fc ON fc.`level-1-id`=l.`level-1-id`"
           " LEFT JOIN csweb_f1_breakout.b_facility_profile bp ON bp.`level-1-id`=l.`level-1-id`"
           " LEFT JOIN csweb_reports.facility_names fn ON fn.code9=%s" % (F1_OWN, F1_SVC, F1_RES, STATUS, F1_CODE9)),
    "f3": (["region", "patient_type", "sex", "date", "status"],
           "SELECT COALESCE(NULLIF(fc.region_name,''),'(unknown)'),"
           " CASE fc.patient_type WHEN '1' THEN 'Outpatient' WHEN '2' THEN 'Inpatient' ELSE COALESCE(NULLIF(fc.patient_type,''),'(blank)') END,"
           " CASE bp.q7_sex WHEN '1' THEN 'Male' WHEN '2' THEN 'Female' ELSE COALESCE(NULLIF(bp.q7_sex,''),'(blank)') END,"
           " COALESCE(CAST(fc.date_first_visited AS CHAR),''), %s"
           " FROM csweb_f3_breakout.`level-1` l"
           " JOIN csweb_f3_breakout.cases c ON c.id=l.`case-id` AND c.deleted=0"
           " LEFT JOIN csweb_f3_breakout.field_control fc ON fc.`level-1-id`=l.`level-1-id`"
           " LEFT JOIN csweb_f3_breakout.b_patient_profile bp ON bp.`level-1-id`=l.`level-1-id`" % STATUS),
    "f4": (["region", "province", "date", "status"],
           "SELECT COALESCE(NULLIF(fc.region_name,''),'(unknown)'),"
           " COALESCE(NULLIF(fc.province_name,''),'(unknown)'),"
           " COALESCE(CAST(fc.date_first_visited AS CHAR),''), %s"
           " FROM csweb_f4_breakout.`level-1` l"
           " JOIN csweb_f4_breakout.cases c ON c.id=l.`case-id` AND c.deleted=0"
           " LEFT JOIN csweb_f4_breakout.field_control fc ON fc.`level-1-id`=l.`level-1-id`" % STATUS),
}


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


data = {}
regions = set()
for pfx, (cols, sql) in QUERIES.items():
    rows = []
    try:
        for r in q(sql):
            rec = dict(zip(cols, r))
            rows.append(rec)
            if "region" in rec:
                regions.add(rec["region"])
    except Exception:
        rows = []
    data[pfx] = rows

spec = [{"title": t, "prefix": p, "charts": [{"field": f, "title": ct, "type": ty} for f, ct, ty in c]}
        for t, p, c in SECTIONS]

# visit-date range bounds (for the date inputs), from valid YYYYMMDD values
_valid = [r["date"] for rows in data.values() for r in rows
          if r.get("date", "").isdigit() and len(r["date"]) == 8 and r["date"] != "00000000"]
_iso = lambda d: d[:4] + "-" + d[4:6] + "-" + d[6:8]
date_min = _iso(min(_valid)) if _valid else ""
date_max = _iso(max(_valid)) if _valid else ""

payload_obj = {
    "data": data,
    "spec": spec,
    "regions": sorted(regions),
    "dateMin": date_min,
    "dateMax": date_max,
    "generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
}
# XSS-safe: JSON in a non-executable <script type="application/json">, HTML-escaped,
# read back via JSON.parse(el.textContent). &,<,> can't break out of the tag.
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
<title>UHC Survey Year 2 — Sync Dashboard</title>
<script src="/docs/assets/chart.umd.min.js"></script>
<style>
  :root{--g:#006b3f;--gd:#004d2c;--gold:#e5b23b;--ink:#1c2b25;--muted:#5b6b63;--line:#dfe7e2;--bg:#f4f7f5;--card:#fff}
  *{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,Segoe UI,Roboto,sans-serif;color:var(--ink);background:var(--bg)}
  header{background:var(--g);color:#fff;padding:20px 24px}
  header h1{margin:0;font-size:20px;letter-spacing:-.01em}
  header .s{opacity:.85;font-size:13px;margin-top:4px}
  main{max-width:1180px;margin:0 auto;padding:22px}
  .filters{display:flex;flex-wrap:wrap;gap:16px;align-items:end;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-bottom:16px}
  .filters .f{display:flex;flex-direction:column;gap:4px}
  .filters label{font-size:12px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
  .filters select{font:14px system-ui;padding:7px 10px;border:1px solid var(--line);border-radius:8px;background:#fff;min-width:200px}
  .filters .reset{margin-left:auto;align-self:end;font:13px system-ui;padding:8px 14px;border:1px solid var(--line);border-radius:8px;background:#fff;cursor:pointer}
  .filters .reset:hover{background:var(--bg)}
  .cards{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:8px}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px;box-shadow:0 1px 2px rgba(0,0,0,.04)}
  .card .num{font-size:34px;font-weight:800;color:var(--g);line-height:1}
  .card .lbl{font-weight:600;margin-top:6px}.card .sub{color:var(--muted);font-size:12.5px}
  h2{font-size:17px;color:var(--gd);border-bottom:2px solid var(--g);padding-bottom:6px;margin:30px 0 6px}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}
  .chart{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;box-shadow:0 1px 2px rgba(0,0,0,.04)}
  .chart h3{margin:0 0 10px;font-size:14px;color:var(--ink)}
  .canvas-wrap{position:relative;height:240px}
  .empty{color:var(--muted);font-size:13px;font-style:italic;text-align:center;padding:80px 0}
  footer{max-width:1180px;margin:0 auto;padding:14px 22px 40px;color:var(--muted);font-size:12.5px}
  .note{background:#fffaf0;border:1px solid var(--gold);border-radius:8px;padding:10px 14px;color:#6b5418;font-size:13px;margin:14px 0}
</style>
</head>
<body>
<header><h1>UHC Survey Year 2 — Sync Dashboard</h1><div class="s">Synced CAPI cases from CSWeb · F1 / F3 / F4</div></header>
<main>
  <div class="filters">
    <div class="f"><label for="fInst">Instrument</label><select id="fInst"></select></div>
    <div class="f"><label for="fRegion">Region</label><select id="fRegion"></select></div>
    <div class="f"><label for="fStatus">Status</label><select id="fStatus"></select></div>
    <div class="f"><label for="fFrom">Visit from</label><input type="date" id="fFrom" /></div>
    <div class="f"><label for="fTo">Visit to</label><input type="date" id="fTo" /></div>
    <button class="reset" id="fReset" type="button">Reset</button>
  </div>
  <div class="cards" id="totals"></div>
  <div class="note">Counts exclude deleted cases. Filters recompute the charts in your browser. Empty/blank categories reflect minimal test cases in the current data — they populate as real fieldwork syncs. For the per-case list with facility labels, see the CSWeb <b>Sync Report</b>.</div>
  <div id="sections"></div>
</main>
<footer>Generated <span id="gen"></span> · auto-refreshes ~every 15 min · source: breakout DBs via <code>csweb_reports</code>.</footer>
<script type="application/json" id="dash-data">__PAYLOAD__</script>
<script>
const P = JSON.parse(document.getElementById('dash-data').textContent);
document.getElementById('gen').textContent = P.generated;
const NAMES = {f1:'Facility Head', f3:'Patient', f4:'Household'};
const PAL=['#006b3f','#e5b23b','#1e88e5','#8e44ad','#e64a19','#00897b','#c2185b','#5d4037','#546e7a','#7cb342','#3949ab','#f4511e'];

// --- filter controls ---
const instSel=document.getElementById('fInst'), regSel=document.getElementById('fRegion');
[['ALL','All instruments'],['f1','F1 · Facility Head'],['f3','F3 · Patient'],['f4','F4 · Household']]
  .forEach(([v,t])=>instSel.add(new Option(t,v)));
regSel.add(new Option('All regions','ALL'));
P.regions.forEach(r=>regSel.add(new Option(r,r)));
const fromInp=document.getElementById('fFrom'), toInp=document.getElementById('fTo');
if(P.dateMin){fromInp.min=P.dateMin; toInp.min=P.dateMin;}
if(P.dateMax){fromInp.max=P.dateMax; toInp.max=P.dateMax;}
const statSel=document.getElementById('fStatus');
[['ALL','All statuses'],['Completed','Completed'],['Partial','Partial']].forEach(([v,t])=>statSel.add(new Option(t,v)));

// --- build skeleton once ---
const tc=document.getElementById('totals');
const cardNum={};
['f1','f3','f4'].forEach(k=>{
  const d=document.createElement('div'); d.className='card';
  const num=document.createElement('div'); num.className='num'; num.textContent='0';
  d.appendChild(num);
  const lbl=document.createElement('div'); lbl.className='lbl'; lbl.textContent=k.toUpperCase()+' · '+NAMES[k]; d.appendChild(lbl);
  const sub=document.createElement('div'); sub.className='sub'; sub.textContent='cases (filtered)'; d.appendChild(sub);
  tc.appendChild(d); cardNum[k]=num; d.dataset.k=k;
});
const sec=document.getElementById('sections');
const charts={}; // id -> Chart
P.spec.forEach(s=>{
  const wrapSec=document.createElement('div'); wrapSec.dataset.prefix=s.prefix;
  const h=document.createElement('h2'); h.textContent=s.title; wrapSec.appendChild(h);
  const grid=document.createElement('div'); grid.className='grid'; wrapSec.appendChild(grid);
  s.charts.forEach(c=>{
    const w=document.createElement('div'); w.className='chart';
    const t=document.createElement('h3'); t.textContent=c.title; w.appendChild(t);
    const cw=document.createElement('div'); cw.className='canvas-wrap';
    const cv=document.createElement('canvas'); cv.id=s.prefix+'__'+c.field; cw.appendChild(cv);
    w.appendChild(cw); grid.appendChild(w);
  });
  sec.appendChild(wrapSec); s._el=wrapSec;
});

function agg(rows,field){
  const m=new Map();
  rows.forEach(r=>{const k=(r[field]!==undefined&&r[field]!=='')?r[field]:'(blank)'; m.set(k,(m.get(k)||0)+1);});
  const e=[...m.entries()].sort((a,b)=>b[1]-a[1]);
  return {labels:e.map(x=>x[0]),data:e.map(x=>x[1])};
}
function render(){
  const inst=instSel.value, region=regSel.value, status=statSel.value;
  const fromY=fromInp.value?fromInp.value.replace(/-/g,''):'';
  const toY=toInp.value?toInp.value.replace(/-/g,''):'';
  const pass=r=>{
    if(region!=='ALL' && r.region!==region) return false;
    if(status!=='ALL' && r.status!==status) return false;
    if(fromY||toY){ const d=r.date; if(!(d&&d.length===8)) return false; if(fromY&&d<fromY) return false; if(toY&&d>toY) return false; }
    return true;
  };
  ['f1','f3','f4'].forEach(k=>{
    const rows=(P.data[k]||[]).filter(pass);
    cardNum[k].textContent=rows.length;
    cardNum[k].closest('.card').style.display=(inst==='ALL'||inst===k)?'':'none';
  });
  P.spec.forEach(s=>{
    const show=(inst==='ALL'||inst===s.prefix);
    s._el.style.display=show?'':'none';
    if(!show) return;
    const rows=(P.data[s.prefix]||[]).filter(pass);
    s.charts.forEach(c=>{
      const id=s.prefix+'__'+c.field, cv=document.getElementById(id);
      const a=agg(rows,c.field), bar=c.type==='bar';
      if(charts[id]){charts[id].destroy(); delete charts[id];}
      if(!rows.length){const ctx=cv.getContext('2d');ctx.clearRect(0,0,cv.width,cv.height);return;}
      charts[id]=new Chart(cv,{type:c.type,data:{labels:a.labels,datasets:[{data:a.data,backgroundColor:bar?'#006b3f':PAL,borderWidth:bar?0:1,borderColor:'#fff'}]},
        options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:!bar,position:'bottom',labels:{boxWidth:12,font:{size:11}}}},
        scales:bar?{y:{beginAtZero:true,ticks:{precision:0}},x:{ticks:{font:{size:11}}}}:{}}});
    });
  });
}
instSel.onchange=render; regSel.onchange=render; statSel.onchange=render; fromInp.onchange=render; toInp.onchange=render;
document.getElementById('fReset').onclick=()=>{instSel.value='ALL';regSel.value='ALL';statSel.value='ALL';fromInp.value='';toInp.value='';render();};
render();
</script>
</body>
</html>
"""

out_html = TEMPLATE.replace("__PAYLOAD__", payload).replace("__FAVICON__", FAVICON)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(out_html)
print("wrote %s (%d bytes); rows: f1=%d f3=%d f4=%d; regions=%d"
      % (OUT, len(out_html), len(data["f1"]), len(data["f3"]), len(data["f4"]), len(regions)))
