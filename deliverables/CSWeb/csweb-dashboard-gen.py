#!/usr/bin/env python3
r"""Generate a static, FILTERABLE Sync Dashboard from the CSWeb breakout DBs and
write it to the CSWeb docs site. Runs ON the box (host python3 + docker compose
exec to MySQL). No new service — served by the existing site at
https://csweb.asiansocial.org/docs/dashboard.html.

Embeds one labeled row per synced case (geo/facility/ownership/result/patient-
type/sex/gps-fix) and aggregates + filters CLIENT-SIDE, so the Instrument and
Region filters recompute the charts in the browser. Categorical codes are labeled
with CASE maps from the dcf value sets; facility names via
csweb_reports.facility_names (breakout facility_name is NULL — Android auto-fill
blocked).

Monitoring layer (Phase 1, 2026-07-06): a KPI scorecard strip (completed · today ·
Completed/Partial · no-GPS · freshness), a submissions-over-time chart (daily +
cumulative), and a full Result-of-Visit disposition breakdown for F3/F4 (F1 already
had one). All recompute under the existing filters. No new data, no new service.

Refresh: host cron re-runs this (every 2 min, flock-guarded, since 2026-06-26 —
near-real-time for fieldwork; was every 15 min). Deploy: scp to /opt/, cron:
  */2 * * * * flock -n /tmp/csweb-dashboard.lock bash -c "cd /opt/app && python3 /opt/csweb-dashboard-gen.py" >> /var/log/csweb-dashboard.log 2>&1
First built 2026-06-20; filters added 2026-06-20; cadence tightened 2026-06-26;
monitoring layer 2026-07-06.

Local dev (off-box, no MySQL): render tiles against a fixture instead of the box —
  python csweb-dashboard-gen.py --sample fixture.json --out /tmp/dashboard.html
The fixture is {"f1":[{col:val,...}], "f3":[...], "f4":[...]} using the same column
names the live queries return (see QUERIES cols). On-box verification against real
synced cases remains the final gate.
"""
import subprocess, json, datetime, html, argparse

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
        ("result", "Result of Visit", "doughnut"),
    ]),
    ("F4 — Household Survey", "f4", [
        ("status", "Case Status", "doughnut"),
        ("region", "Cases by Region", "bar"),
        ("province", "Cases by Province", "bar"),
        ("result", "Result of Visit", "doughnut"),
    ]),
    # F2 = Healthcare-Worker PWA, mirrored into csweb_f2 (read-mirror, 2026-07-07).
    # Different shape from the CSEntry breakouts: no server-side Completed/Partial
    # (every stored submission is complete) and no GPS (self-administered) — its
    # disposition is Submitted vs Refusal. Coverage-vs-target stays DEFERRED (no F2
    # sample frame yet), so F2 has no targets entry and the coverage section skips it.
    ("F2 — Healthcare Worker Survey (PWA)", "f2", [
        ("result", "Disposition — Submitted / Refusal", "doughnut"),
        ("region", "Cases by Region", "bar"),
        ("source", "Capture Mode", "doughnut"),
    ]),
]

# --- per-case labeled-row queries (one row per non-deleted case) ---
F1_OWN = "CASE bp.q7_ownership WHEN '1' THEN 'Public' WHEN '2' THEN 'Private' ELSE COALESCE(NULLIF(bp.q7_ownership,''),'(blank)') END"
F1_SVC = ("CASE bp.q8_service_level WHEN '1' THEN 'Primary Care Facility' WHEN '2' THEN 'Level 1 Hospital'"
          " WHEN '3' THEN 'Level 2 Hospital' WHEN '4' THEN 'Level 3 Hospital' ELSE COALESCE(NULLIF(bp.q8_service_level,''),'(blank)') END")
# F1 Result-of-Visit (verbatim value set, ENUM_RESULT_OPTIONS_F1).
# Prefer the FINAL visit, fall back to the FIRST. This read used to be first-visit-only, which
# was wrong for any early-ended case: PROC BREAKOFF writes ENUM_RESULT_FINAL_VISIT (never the
# first), so a broken-off — and now a Replaced(5) — F1 case would never have surfaced here.
# F3/F4 already read final_visit; this makes all three agree.
F1_RESRAW = "COALESCE(NULLIF(fc.enum_result_final_visit,''),NULLIF(fc.enum_result_first_visit,''),'')"
F1_RES = ("CASE %s WHEN '1' THEN 'Completed' WHEN '2' THEN 'Postponed'"
          " WHEN '3' THEN 'Refused' WHEN '4' THEN 'Incomplete' WHEN '5' THEN 'Replaced'"
          " ELSE COALESCE(NULLIF(%s,''),'(blank)') END" % (F1_RESRAW, F1_RESRAW))
# F3/F4 disposition = enum_result_final_visit (set by the closing / BREAKOFF handler);
# verbatim value sets ENUM_RESULT_OPTIONS_F3 / _F4 from cspro_helpers.py
F3_RES = ("CASE fc.enum_result_final_visit WHEN '1' THEN 'Completed' WHEN '2' THEN 'Completed at the Hospital'"
          " WHEN '3' THEN 'Postponed' WHEN '4' THEN 'Incomplete' WHEN '5' THEN 'Completed at Home'"
          " WHEN '6' THEN 'Withdraw Participation/Consent' WHEN '7' THEN 'Replaced'"
          " ELSE COALESCE(NULLIF(fc.enum_result_final_visit,''),'(blank)') END")
F4_RES = ("CASE fc.enum_result_final_visit WHEN '1' THEN 'Completed' WHEN '2' THEN 'Postponed'"
          " WHEN '3' THEN 'Incomplete' WHEN '4' THEN 'Withdraw Participation/Consent'"
          " WHEN '5' THEN 'Replaced'"
          " ELSE COALESCE(NULLIF(fc.enum_result_final_visit,''),'(blank)') END")
F1_CODE9 = ("CONCAT(LPAD(fc.region_code,2,'0'),LPAD(fc.province_huc_code,2,'0'),"
            "LPAD(fc.city_municipality_code,3,'0'),LPAD(fc.facility_no,2,'0'))")

# `date` = visit date (date_first_visited), YYYYMMDD ('' if none) for the date-range filter
# `status` = Completed (fully saved) vs Partial (partial_save_mode set, e.g. 'add')
STATUS = "CASE WHEN c.partial_save_mode IS NULL OR c.partial_save_mode='' THEN 'Completed' ELSE 'Partial' END"
# `gps` = '1' if a GPS fix (lat AND lon captured), else '0' — mirrors the Map Report's no-fix badge.
# GPS lives in a dedicated capture table keyed on level-1-id (alias g).
def _gps(lat, lon):
    return ("CASE WHEN g.%s IS NULL OR g.%s='' OR g.%s IS NULL OR g.%s='' THEN '0' ELSE '1' END"
            % (lat, lat, lon, lon))
F1_GPS = _gps("facility_gps_latitude", "facility_gps_longitude")
F3_GPS = _gps("facility_gps_latitude", "facility_gps_longitude")
F4_GPS = _gps("latitude", "longitude")

# --- F2 (Healthcare-Worker PWA) — read from the csweb_f2 mirror (NOT a breakout) ---
# Same q() docker-exec path, different DB + shape. Plain string (NOT %-formatted), so
# the DATE_FORMAT %Y%m%d tokens survive verbatim. status='Completed'/gps='1' are fixed
# by design: F2 has no partial-save and no geolocation (self-administered), so it must
# never inflate the Partial or "No GPS fix" KPIs. submitted_at_server is UTC → shifted
# to Manila (+08:00) so F2's trend/"today" line up with the CSEntry visit dates.
F2_RES  = "CASE r.status WHEN 'refusal' THEN 'Refusal' ELSE 'Submitted' END"
F2_SRC  = "CASE r.source_path WHEN 'paper_encoded' THEN 'Paper-encoded' ELSE 'Self-administered' END"
F2_DATE = "COALESCE(DATE_FORMAT(CONVERT_TZ(r.submitted_at_server,'+00:00','+08:00'),'%Y%m%d'),'')"
F2_SQL = (
    "SELECT COALESCE(NULLIF(fm.region,''),'(unknown)'),"
    " COALESCE(NULLIF(fm.province,''),'(unknown)'), "
    + F2_RES + ", " + F2_SRC + ", " + F2_DATE + ", 'Completed', '1',"
    # code9 = first 9 of the 12-digit QN (2026-07-08 rollout) — the same
    # facility code F1 uses, so F2 joins targets.json/geo like the others;
    # falls back to facility_id for pre-qn rows (demo slugs → no join, as before).
    " LEFT(COALESCE(NULLIF(r.qn,''),r.facility_id,''),9)"
    " FROM csweb_f2.f2_responses r"
    " LEFT JOIN csweb_f2.f2_facility_master fm ON fm.facility_id=r.facility_id")

# `enumerator` = FIELD_CONTROL.ENUMERATOR_S_NAME (CHAR 50, all three dicts) — the field-control
# record is already joined as `fc` for every instrument, so productivity costs one column.
# F2 has no counterpart by design: it is self-administered, so it never appears in this panel.
ENUM = "COALESCE(NULLIF(fc.enumerator_s_name,''),'(unassigned)')"
# `supervisor` = FIELD_CONTROL.SURVEY_TEAM_LEADER_S_NAME (CHAR 50, all three dicts). The SAAD
# benchmark navigates by Field Supervisor ("whose team is behind?"); this is that dimension.
SUP = "COALESCE(NULLIF(fc.survey_team_leader_s_name,''),'(unassigned)')"

# `repl` = 1 if this case is a REPLACEMENT — the sampled unit was never interviewed and a
# substitute was drawn. Read off FIELD_CONTROL.BREAKOFF, whose 5/6/7 codes (refused at the
# door / not found / ineligible) are IDENTICAL across F1/F3/F4 by design — that uniformity is
# the whole reason we count on BREAKOFF rather than the per-instrument Result-of-Visit code
# (Replaced is 5 in F1/F4 but 7 in F3, because the lists have different lengths).
#
# Postponed (BREAKOFF 3) is deliberately EXCLUDED: that unit gets revisited, not substituted.
# Counting it would overstate the rate and blunt the signal this exists to give — a high
# replacement rate for one enumerator is the standard curbstoning check (ASPSI, 2026-07-14).
REPL = "CASE WHEN fc.breakoff IN ('5','6','7') THEN '1' ELSE '0' END"

QUERIES = {
    "f1": (["region", "province", "city", "facility", "ownership", "service_level", "result", "date", "status", "gps", "code9", "enumerator", "supervisor", "repl"],
           "SELECT COALESCE(NULLIF(fc.region_name,''),'(unknown)'),"
           " COALESCE(NULLIF(fc.province_name,''),'(unknown)'),"
           " COALESCE(NULLIF(fc.city_name,''),'(unknown)'),"
           " COALESCE(fn.name,'(unlabeled)'), %s, %s, %s,"
           " COALESCE(CAST(fc.date_first_visited_the_facility AS CHAR),''), %s, %s, %s, %s, %s, %s"
           " FROM csweb_f1_breakout.`level-1` l"
           " JOIN csweb_f1_breakout.cases c ON c.id=l.`case-id` AND c.deleted=0"
           " LEFT JOIN csweb_f1_breakout.field_control fc ON fc.`level-1-id`=l.`level-1-id`"
           " LEFT JOIN csweb_f1_breakout.b_facility_profile bp ON bp.`level-1-id`=l.`level-1-id`"
           " LEFT JOIN csweb_f1_breakout.rec_facility_capture g ON g.`level-1-id`=l.`level-1-id`"
           " LEFT JOIN csweb_reports.facility_names fn ON fn.code9=%s"
           % (F1_OWN, F1_SVC, F1_RES, STATUS, F1_GPS, F1_CODE9, ENUM, SUP, REPL, F1_CODE9)),
    "f3": (["region", "patient_type", "sex", "result", "date", "status", "gps", "code9", "enumerator", "supervisor", "repl"],
           "SELECT COALESCE(NULLIF(fc.region_name,''),'(unknown)'),"
           " CASE fc.patient_type WHEN '1' THEN 'Outpatient' WHEN '2' THEN 'Inpatient' ELSE COALESCE(NULLIF(fc.patient_type,''),'(blank)') END,"
           " CASE bp.q7_sex WHEN '1' THEN 'Male' WHEN '2' THEN 'Female' ELSE COALESCE(NULLIF(bp.q7_sex,''),'(blank)') END,"
           " %s, COALESCE(CAST(fc.date_first_visited AS CHAR),''), %s, %s, LEFT(LPAD(l.`questionnaire_number`,12,'0'),9), %s, %s, %s"
           " FROM csweb_f3_breakout.`level-1` l"
           " JOIN csweb_f3_breakout.cases c ON c.id=l.`case-id` AND c.deleted=0"
           " LEFT JOIN csweb_f3_breakout.field_control fc ON fc.`level-1-id`=l.`level-1-id`"
           " LEFT JOIN csweb_f3_breakout.b_patient_profile bp ON bp.`level-1-id`=l.`level-1-id`"
           " LEFT JOIN csweb_f3_breakout.rec_facility_capture g ON g.`level-1-id`=l.`level-1-id`"
           % (F3_RES, STATUS, F3_GPS, ENUM, SUP, REPL)),
    "f4": (["region", "province", "result", "date", "status", "gps", "code9", "enumerator", "supervisor", "repl"],
           "SELECT COALESCE(NULLIF(fc.region_name,''),'(unknown)'),"
           " COALESCE(NULLIF(fc.province_name,''),'(unknown)'),"
           " %s, COALESCE(CAST(fc.date_first_visited AS CHAR),''), %s, %s, LEFT(LPAD(l.`questionnaire_number`,12,'0'),9), %s, %s, %s"
           " FROM csweb_f4_breakout.`level-1` l"
           " JOIN csweb_f4_breakout.cases c ON c.id=l.`case-id` AND c.deleted=0"
           " LEFT JOIN csweb_f4_breakout.field_control fc ON fc.`level-1-id`=l.`level-1-id`"
           " LEFT JOIN csweb_f4_breakout.household_geo_id g ON g.`level-1-id`=l.`level-1-id`"
           % (F4_RES, STATUS, F4_GPS, ENUM, SUP, REPL)),
    # F2 carries no enumerator/supervisor/repl by design: it is self-administered, so it has
    # no field-control record. Its rows simply lack those keys — the productivity panel skips
    # F2 entirely, and `r.repl==='1'` is false for a missing key, so the Replacements KPI is
    # unaffected. Do NOT synthesise placeholder columns for it.
    "f2": (["region", "province", "result", "source", "date", "status", "gps", "code9"], F2_SQL),
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
    # Raise on a real MySQL error rather than silently returning [] — otherwise a
    # broken query (e.g. csweb_f2 not created yet) is indistinguishable from "no rows"
    # and would be mis-reported as an empty mirror. fetch_live catches this per-instrument.
    if r.returncode != 0:
        raise RuntimeError((r.stderr or "mysql query failed").strip())
    return [ln.split("\t") for ln in r.stdout.splitlines() if ln.strip()]


def fetch_live():
    """One labeled-row dict list per instrument, from the box's breakout DBs. Returns
    (data, errored): errored = the set of instruments whose query FAILED (vs simply
    returned zero rows), so a broken query is reported as a degraded state, not "no data"."""
    data, errored = {}, set()
    for pfx, (cols, sql) in QUERIES.items():
        try:
            data[pfx] = [dict(zip(cols, r)) for r in q(sql)]
        except Exception as e:
            errored.add(pfx)
            data[pfx] = []
            print("WARN: %s query failed: %s" % (pfx, str(e)[:200]))
    return data, errored


def f2_api_health():
    """f2-api service probe (P6 hardening): True/False from the box's loopback-published
    port. The retired 2-min poller was F2's de-facto liveness signal; this replaces it.
    Data freshness is covered separately by f2meta.last."""
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:8787/api/health", timeout=5) as r:
            return r.status == 200 and b'"ok":true' in r.read(200)
    except Exception:
        return False


def load_sample(path):
    """Off-box dev: read the same row shape from a JSON fixture instead of MySQL.
    Returns (data, errored) to match fetch_live; a fixture never errors."""
    obj = json.load(open(path, encoding="utf-8"))
    return {k: list(obj.get(k, [])) for k in QUERIES}, set()


# Phase 2 coverage-vs-target: per-EA-facility sample targets, built by gen-targets.py
# and scp'd to the box next to this generator. Absent file → coverage tiles hide gracefully.
TARGETS = "/opt/targets.json"


def load_targets(path):
    """({inst: {code9: {name, region, province, target}}}, plan) — ({}, {}) if absent.

    `plan` is the assignment-plan provenance written by gen-targets.py. A targets.json
    predating that stamp has no `plan` block: treat it as PROVISIONAL, never as final.
    An unlabelled plan is far more likely to be a leftover fixture than ASPSI's real EA
    plan, and a fake coverage % is indistinguishable from a real one on screen.
    """
    try:
        obj = json.load(open(path, encoding="utf-8"))
    except Exception:
        return {}, {}
    plan = obj.get("plan") or {"label": "unlabelled targets.json", "provisional": True}
    plan.setdefault("provisional", True)
    return obj.get("targets", {}), plan


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
  :root{--g:#006b3f;--gd:#004d2c;--gold:#e5b23b;--red:#d32f2f;--ink:#1c2b25;--muted:#5b6b63;--line:#dfe7e2;--bg:#f4f7f5;--card:#fff}
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
  .kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:6px}
  .kpi{background:var(--card);border:1px solid var(--line);border-top:3px solid var(--g);border-radius:12px;padding:14px 16px;box-shadow:0 1px 2px rgba(0,0,0,.04)}
  .kpi .num{font-size:30px;font-weight:800;color:var(--ink);line-height:1}
  .kpi .lbl{color:var(--muted);font-size:12px;font-weight:600;margin-top:5px;text-transform:uppercase;letter-spacing:.03em}
  .kpi.ok{border-top-color:var(--g)}.kpi.ok .num{color:var(--g)}
  .kpi.warn{border-top-color:var(--gold)}.kpi.warn .num{color:#b7860b}
  .kpi.bad{border-top-color:var(--red)}.kpi.bad .num{color:var(--red)}
  .freshness{color:var(--muted);font-size:12.5px;margin:2px 2px 16px}
  .freshness b{color:var(--ink)}
  .cards{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:8px}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px;box-shadow:0 1px 2px rgba(0,0,0,.04)}
  .card .num{font-size:34px;font-weight:800;color:var(--g);line-height:1}
  .card .lbl{font-weight:600;margin-top:6px}.card .sub{color:var(--muted);font-size:12.5px}
  h2{font-size:17px;color:var(--gd);border-bottom:2px solid var(--g);padding-bottom:6px;margin:30px 0 6px}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}
  .chart{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;box-shadow:0 1px 2px rgba(0,0,0,.04)}
  .chart h3{margin:0 0 10px;font-size:14px;color:var(--ink)}
  .chart.wide{margin-bottom:18px}
  .canvas-wrap{position:relative;height:240px}
  .chart.wide .canvas-wrap{height:230px}
  .empty{color:var(--muted);font-size:13px;font-style:italic;text-align:center;padding:80px 0}
  footer{max-width:1180px;margin:0 auto;padding:14px 22px 40px;color:var(--muted);font-size:12.5px}
  .note{background:#fffaf0;border:1px solid var(--gold);border-radius:8px;padding:10px 14px;color:#6b5418;font-size:13px;margin:14px 0}
  .cov-note{color:var(--muted);font-size:12px;font-style:italic;margin:2px 2px 10px}
  .cov-inst{margin:14px 0 6px;font-size:14px;font-weight:700;color:var(--gd)}
  .cov-sum{color:var(--muted);font-size:12.5px;margin:0 2px 8px}
  .cov-sum b{color:var(--ink)}
  .covtbl{width:100%;border-collapse:collapse;font-size:13px;background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;margin-bottom:6px}
  .covtbl th,.covtbl td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:middle}
  .covtbl th{background:#eef3f0;color:var(--gd);font-size:12px;cursor:pointer;user-select:none;white-space:nowrap}
  .covtbl th.n,.covtbl td.n{text-align:right}
  .covtbl th.s{text-align:center}
  .covtbl tr:last-child td{border-bottom:none}
  .covtbl .short{color:#b7860b;font-weight:600}.covtbl .short.zero{color:var(--muted);font-weight:400}
  .covbar{position:relative;height:10px;width:150px;background:#e5e7eb;border-radius:6px;overflow:hidden;display:inline-block;vertical-align:middle}
  .covbar>span{position:absolute;left:0;top:0;bottom:0;border-radius:6px}
  .covtbl .pct{font-weight:700}
  .planwarn{background:#fdf3d7;border:1px solid #e5b23b;border-left:5px solid #b7860b;
            border-radius:8px;padding:10px 13px;margin:8px 0 10px;color:#6b5200;
            font-size:13px;line-height:1.5}
  .planwarn code{background:#fff;border:1px solid #e2d6a8;border-radius:4px;padding:0 4px}
  .mix{color:var(--muted);font-size:12px;white-space:nowrap}
  .rate{font-weight:700}
  /* a rate over a single active day is arithmetic, not a trend — de-emphasise it so it
     cannot be misread as strong performance (one busy day then silence outranks everyone) */
  .rate.lowconf{font-weight:400;color:var(--muted)}
  /* replacement share: only flagged red once the denominator is big enough to mean something
     (>=5 cases and >=30% replaced). The count alone is not comparable across enumerators —
     a hard catchment legitimately produces more replacements than an easy one. */
  .covtbl td.hot{color:var(--red);font-weight:700}
  .covtbl .pct{font-weight:400;color:var(--muted);font-size:11px}
  .covtbl td.hot .pct{color:var(--red)}
  .stale{color:#b7860b}
  @media(max-width:820px){.kpis{grid-template-columns:repeat(2,1fr)}.cards{grid-template-columns:1fr}.covbar{width:90px}}
</style>
</head>
<body>
<header><h1>UHC Survey Year 2 — Sync Dashboard</h1><div class="s">Unified monitoring · F1 / F3 / F4 (CSEntry) · F2 (Healthcare-Worker PWA)</div></header>
<main>
  <div class="filters">
    <div class="f"><label for="fInst">Instrument</label><select id="fInst"></select></div>
    <div class="f"><label for="fRegion">Region</label><select id="fRegion"></select></div>
    <div class="f"><label for="fSup">Field supervisor</label><select id="fSup"></select></div>
    <div class="f"><label for="fStatus">Status</label><select id="fStatus"></select></div>
    <div class="f"><label for="fFrom">Visit from</label><input type="date" id="fFrom" /></div>
    <div class="f"><label for="fTo">Visit to</label><input type="date" id="fTo" /></div>
    <button class="reset" id="fReset" type="button">Reset</button>
  </div>
  <div class="kpis">
    <div class="kpi"><div class="num" id="kTotal">0</div><div class="lbl">Cases (filtered)</div></div>
    <div class="kpi ok"><div class="num" id="kCompleted">0</div><div class="lbl">Completed</div></div>
    <div class="kpi warn"><div class="num" id="kPartial">0</div><div class="lbl">Partial</div></div>
    <div class="kpi"><div class="num" id="kToday">0</div><div class="lbl">Visited today</div></div>
    <div class="kpi warn"><div class="num" id="kRepl">0</div><div class="lbl">Replacements</div></div>
    <div class="kpi bad"><div class="num" id="kNogps">0</div><div class="lbl">No GPS fix</div></div>
  </div>
  <div class="freshness">Data as of <b id="fresh"></b> · auto-refreshes ~every 2 min · "today" = <span id="todayLbl"></span> (Manila)</div>
  <div class="chart wide"><h3>Submissions over time — new per day &amp; cumulative</h3><div class="canvas-wrap"><canvas id="trend"></canvas></div></div>
  <div id="coverage"></div>
  <div id="productivity"></div>
  <div class="cards" id="totals"></div>
  <div class="note">Counts exclude deleted cases. Filters recompute every tile in your browser. Empty/blank categories reflect minimal test cases in the current data — they populate as real fieldwork syncs. For the per-case list with facility labels, see the CSWeb <b>Sync Report</b>.</div>
  <div id="sections"></div>
</main>
<footer>Generated <span id="gen"></span> · auto-refreshes ~every 2 min · source: F1/F3/F4 breakout DBs via <code>csweb_reports</code> + F2 <code>csweb_f2</code> mirror · see also the <a href="/docs/map.html" style="color:#006b3f">Map Report</a>.</footer>
<script type="application/json" id="dash-data">__PAYLOAD__</script>
<script>
const P = JSON.parse(document.getElementById('dash-data').textContent);
document.getElementById('gen').textContent = P.generated;
document.getElementById('fresh').textContent = P.generated;
document.getElementById('todayLbl').textContent = P.today ? (P.today.slice(0,4)+'-'+P.today.slice(4,6)+'-'+P.today.slice(6,8)) : '—';
const NAMES = {f1:'Facility Head', f3:'Patient', f4:'Household', f2:'Healthcare Worker'};
const PAL=['#006b3f','#e5b23b','#1e88e5','#8e44ad','#e64a19','#00897b','#c2185b','#5d4037','#546e7a','#7cb342','#3949ab','#f4511e'];
// instrument prefixes, in section order (F1, F3, F4, F2) — derived once so every
// per-instrument loop below (cards, KPIs, coverage) stays in sync with the sections.
const INSTS = P.spec.map(s=>s.prefix);

// --- filter controls ---
const instSel=document.getElementById('fInst'), regSel=document.getElementById('fRegion');
instSel.add(new Option('All instruments','ALL'));
INSTS.forEach(k=>instSel.add(new Option(k.toUpperCase()+' · '+NAMES[k], k)));
regSel.add(new Option('All regions','ALL'));
P.regions.forEach(r=>regSel.add(new Option(r,r)));
const fromInp=document.getElementById('fFrom'), toInp=document.getElementById('fTo');
if(P.dateMin){fromInp.min=P.dateMin; toInp.min=P.dateMin;}
if(P.dateMax){fromInp.max=P.dateMax; toInp.max=P.dateMax;}
const supSel=document.getElementById('fSup');
supSel.add(new Option('All supervisors','ALL'));
(P.supervisors||[]).forEach(x=>supSel.add(new Option(x,x)));
const statSel=document.getElementById('fStatus');
[['ALL','All statuses'],['Completed','Completed'],['Partial','Partial']].forEach(([v,t])=>statSel.add(new Option(t,v)));

// --- KPI + trend refs ---
const kTotal=document.getElementById('kTotal'), kCompleted=document.getElementById('kCompleted'),
      kPartial=document.getElementById('kPartial'), kToday=document.getElementById('kToday'),
      kNogps=document.getElementById('kNogps');

// --- build skeleton once ---
const tc=document.getElementById('totals');
const cardNum={};
INSTS.forEach(k=>{
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
  // F2 reads the live store (csweb_f2 became authoritative at the P4 cutover,
  // 2026-07 serving migration) — surface freshness so an empty/failed read is
  // visible (not a silent flatline). n=0 → an explicit "no data yet" note.
  if(s.prefix==='f2' && P.f2meta){
    const fn=document.createElement('div'); fn.className='cov-note';
    fn.textContent = P.f2meta.err
      ? 'F2 query failed — csweb_f2 may not exist yet, or the schema/columns changed. Check the generator log; F1/F3/F4 are unaffected.'
      : P.f2meta.n
      ? (P.f2meta.n+' submission'+(P.f2meta.n===1?'':'s')+' from the Healthcare-Worker PWA'
         + (P.f2meta.last ? ' · last submission '+P.f2meta.last.slice(0,4)+'-'+P.f2meta.last.slice(4,6)+'-'+P.f2meta.last.slice(6,8) : '')
         + ' · csweb_f2 is F2’s store of record (uhc-hcw.asiansocial.org)')
      : 'No F2 submissions yet (csweb_f2 empty). csweb_f2 is F2’s store of record — submissions arrive via uhc-hcw.asiansocial.org.';
    if(P.f2meta.api===true||P.f2meta.api===false){
      const svc=document.createElement('span');
      svc.textContent=P.f2meta.api?' \u00b7 f2-api: OK':' \u00b7 f2-api: UNREACHABLE \u2014 uhc-hcw submissions are failing; check the f2-api container';
      if(!P.f2meta.api){svc.style.color='var(--red)';svc.style.fontWeight='600';}
      fn.appendChild(svc);
    }
    wrapSec.appendChild(fn);
  }
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
// visible instruments for the current Instrument filter
function visInsts(inst){ return inst==='ALL' ? INSTS : [inst]; }
// KPI strip — recomputes over every filtered, visible row
function renderKpis(passOf){
  let tot=0,comp=0,part=0,today=0,nogps=0,repl=0;
  visInsts(instSel.value).forEach(k=>{
    (P.data[k]||[]).forEach(r=>{ if(!passOf(r))return;
      tot++; if(r.status==='Completed')comp++; else if(r.status==='Partial')part++;
      if(P.today && r.date===P.today)today++;
      if(r.gps==='0'||r.gps===0)nogps++;
      if(r.repl==='1')repl++;   // BREAKOFF 5/6/7 — sampled unit never interviewed, substitute drawn
    });
  });
  kTotal.textContent=tot; kCompleted.textContent=comp; kPartial.textContent=part;
  kToday.textContent=today; kNogps.textContent=nogps; kRepl.textContent=repl;
}
// submissions-over-time — daily + cumulative across filtered, visible rows
function renderTrend(passOf){
  const day=new Map();
  visInsts(instSel.value).forEach(k=>{
    (P.data[k]||[]).forEach(r=>{ if(!passOf(r))return;
      const d=r.date; if(!(d&&d.length===8&&/^\d{8}$/.test(d)&&d!=='00000000'))return;
      day.set(d,(day.get(d)||0)+1);
    });
  });
  const cv=document.getElementById('trend');
  if(charts.trend){charts.trend.destroy(); delete charts.trend;}
  if(typeof Chart==='undefined') return;            // KPIs already set; charts need the vendored lib
  const keys=[...day.keys()].sort();
  const labels=keys.map(d=>d.slice(0,4)+'-'+d.slice(4,6)+'-'+d.slice(6,8));
  const daily=keys.map(d=>day.get(d)); let run=0; const cum=daily.map(n=>run+=n);
  if(!keys.length){const ctx=cv.getContext('2d');ctx.clearRect(0,0,cv.width,cv.height);return;}
  charts.trend=new Chart(cv,{data:{labels,datasets:[
      {type:'bar',label:'New per day',data:daily,backgroundColor:'#e5b23b',order:2,yAxisID:'y'},
      {type:'line',label:'Cumulative',data:cum,borderColor:'#006b3f',backgroundColor:'#006b3f',tension:.25,pointRadius:2,borderWidth:2,order:1,yAxisID:'y2'}]},
    options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
      plugins:{legend:{position:'bottom',labels:{boxWidth:12,font:{size:11}}}},
      scales:{y:{position:'left',beginAtZero:true,ticks:{precision:0},title:{display:true,text:'new/day'}},
              y2:{position:'right',beginAtZero:true,grid:{drawOnChartArea:false},ticks:{precision:0},title:{display:true,text:'cumulative'}},
              x:{ticks:{font:{size:10},maxRotation:60,minRotation:0}}}}});
}
// --- Phase 2: coverage vs. target ---
const provByCode={};   // code9 -> province from cases (fallback area when targets aren't masterlist-enriched)
INSTS.forEach(k=>(P.data[k]||[]).forEach(r=>{ if(r.code9 && r.province && r.province!=='(unknown)' && !provByCode[r.code9]) provByCode[r.code9]=r.province; }));
const covSort={};      // inst -> {col,dir}
function esc(s){const d=document.createElement('div'); d.textContent=(s==null?'':s); return d.innerHTML;}
function covColor(pct){ return pct>=80?'#006b3f':(pct>=40?'#e5b23b':'#d32f2f'); }
function renderCoverage(pass){
  const cov=document.getElementById('coverage'); cov.innerHTML='';
  const T=P.targets||{};
  const visible=visInsts(instSel.value).filter(k=>T[k]&&Object.keys(T[k]).length);
  if(!visible.length) return;                         // no targets → section hides (graceful)
  const h=document.createElement('h2'); h.textContent='Coverage vs. target'; cov.appendChild(h);
  // Provenance FIRST. A coverage % divided by a placeholder plan renders identically to a
  // real one; this banner is the only thing standing between a fixture and a DOH briefing.
  const pl=P.plan||{};
  if(pl.provisional!==false){
    const w=document.createElement('div'); w.className='planwarn';
    const f=pl.facilities||{}, nf=(f.f1||0)+(f.f3||0)+(f.f4||0);
    w.innerHTML='<b>PROVISIONAL ASSIGNMENT PLAN — these percentages are not real coverage.</b> '
      +'Targets come from <b>'+esc(pl.label||'an unlabelled targets.json')+'</b>'
      +(pl.assignments?' ('+pl.assignments+' assignment row'+(pl.assignments===1?'':'s')
         +' across '+nf+' facility slot'+(nf===1?'':'s')+')':'')
      +'. Every % and shortfall below is measured against that placeholder. Replace '
      +'<code>assignments-source.csv</code> with ASPSI’s real EA plan and re-run '
      +'<code>gen-targets.py --final</code> before quoting any of this.';
    cov.appendChild(w);
  }
  const note=document.createElement('div'); note.className='cov-note';
  note.textContent='Landed = Completed cases in the current view (instrument · region · visit-date). Expected = the assignment plan’s target. The Status filter does not apply here.';
  cov.appendChild(note);
  visible.forEach(k=>{
    const tgt=T[k], comp={}; let untarget=0;
    (P.data[k]||[]).forEach(r=>{ if(r.status!=='Completed'||!pass(r,true)) return; if(tgt[r.code9]) comp[r.code9]=(comp[r.code9]||0)+1; else untarget++; });
    let rows=Object.keys(tgt).map(code=>{
      const t=tgt[code], exp=+t.target||0, landed=comp[code]||0;
      return {name:t.name||('(code '+code+')'), area:t.province||provByCode[code]||'(area TBD)', exp, landed,
              pct: exp>0?Math.round(100*landed/exp):null, short: Math.max(0,exp-landed)};
    });
    const st=covSort[k]||{col:'pct',dir:1};
    const val=(o,c)=> (c==='name'||c==='area') ? (o[c]||'').toLowerCase() : (o[c]==null?-1:o[c]);
    rows.sort((a,b)=>{const x=val(a,st.col),y=val(b,st.col); return (x<y?-1:x>y?1:0)*st.dir;});
    const sumExp=rows.reduce((s,r)=>s+r.exp,0), sumLanded=rows.reduce((s,r)=>s+r.landed,0);
    const opct=sumExp>0?Math.round(100*sumLanded/sumExp):0;
    const title=document.createElement('div'); title.className='cov-inst'; title.textContent=k.toUpperCase()+' · '+NAMES[k]; cov.appendChild(title);
    const sum=document.createElement('div'); sum.className='cov-sum';
    sum.innerHTML='<b>'+sumLanded+'</b> / '+sumExp+' completed ('+opct+'%) across '+rows.length+' facilit'+(rows.length===1?'y':'ies')
      +(untarget?' · <b>'+untarget+'</b> completed at facilities not in the plan':'');
    cov.appendChild(sum);
    const tbl=document.createElement('table'); tbl.className='covtbl';
    const cols=[['name','Facility',''],['area','Area',''],['exp','Expected','n'],['landed','Landed','n'],['pct','%','n'],['short','Shortfall','n'],['bar','Progress','s']];
    const thead=document.createElement('tr');
    cols.forEach(([c,lbl,cl])=>{ const th=document.createElement('th'); if(cl)th.className=cl;
      th.textContent=lbl+(st.col===c?(st.dir>0?' ▲':' ▼'):'');
      if(c!=='bar'){th.onclick=()=>{covSort[k]={col:c,dir:(st.col===c?-st.dir:1)}; render();};}
      thead.appendChild(th); });
    tbl.appendChild(thead);
    rows.forEach(r=>{ const tr=document.createElement('tr');
      const pct=r.pct==null?'—':r.pct+'%', col=r.pct==null?'#5b6b63':covColor(r.pct);
      tr.innerHTML='<td>'+esc(r.name)+'</td><td>'+esc(r.area)+'</td>'
        +'<td class="n">'+r.exp+'</td><td class="n">'+r.landed+'</td>'
        +'<td class="n pct" style="color:'+col+'">'+pct+'</td>'
        +'<td class="n short'+(r.short?'':' zero')+'">'+r.short+'</td>'
        +'<td class="s"><div class="covbar"><span style="width:'+Math.min(100,r.pct||0)+'%;background:'+col+'"></span></div></td>';
      tbl.appendChild(tr); });
    cov.appendChild(tbl);
  });
}
// --- Phase 3: enumerator productivity (F1/F3/F4) ---
// F2 never appears here: it is self-administered, so it has no enumerator. visInsts()
// only ever returns f1/f3/f4, so that exclusion is structural rather than a special case.
let prodSort={col:'cases',dir:-1};
function daysBetween(a,b){                      // YYYYMMDD strings -> whole days
  const d=s=>Date.UTC(+s.slice(0,4),+s.slice(4,6)-1,+s.slice(6,8));
  return Math.round((d(b)-d(a))/86400000);
}
function renderProductivity(pass){
  const el=document.getElementById('productivity'); el.innerHTML='';
  const m=new Map(); let unnamed=0;
  visInsts(instSel.value).forEach(k=>{
    (P.data[k]||[]).forEach(r=>{ if(!pass(r)) return;
      const n=r.enumerator;
      if(!n||n==='(unassigned)'){unnamed++; return;}
      let o=m.get(n);
      if(!o){o={name:n,cases:0,completed:0,partial:0,repl:0,days:new Set(),last:'',mix:{},sups:{}}; m.set(n,o);}
      o.cases++;
      if(r.status==='Completed')o.completed++; else if(r.status==='Partial')o.partial++;
      if(r.repl==='1')o.repl++;
      const d=r.date;
      if(d&&/^\d{8}$/.test(d)&&d!=='00000000'){o.days.add(d); if(d>o.last)o.last=d;}
      o.mix[k]=(o.mix[k]||0)+1;
      const sv=r.supervisor||'(unassigned)'; o.sups[sv]=(o.sups[sv]||0)+1;
    });
  });
  if(!m.size) return;                           // no named enumerators in view -> hide, like coverage
  const h=document.createElement('h2'); h.textContent='Enumerator productivity'; el.appendChild(h);
  const note=document.createElement('div'); note.className='cov-note';
  note.textContent='Cases/day = cases in the current view ÷ the distinct days that enumerator was active — '
    +'so it measures pace on the days they actually worked, not calendar days. A rate over a single '
    +'active day is greyed out: it is arithmetic, not a trend. Check Last active before reading a high '
    +'rate as good news. Replaced = the sampled unit was never interviewed (refused at the door, not '
    +'found, or ineligible) and a substitute was drawn; postponed visits are NOT replacements. The share '
    +'is flagged red only at 30% or more over at least 5 cases — a hard catchment legitimately produces '
    +'replacements, so the raw count is not comparable between enumerators. Honours every filter above. '
    +'F2 is absent by design: it is self-administered and has no enumerator.'
    +(unnamed?' '+unnamed+' case(s) in view carry no enumerator name.':'');
  el.appendChild(note);
  let rows=[...m.values()].map(o=>{
    const days=o.days.size;
    // an enumerator normally sits under one team leader; if the data says otherwise, say so
    // rather than silently picking one — a person straddling two teams is a finding, not a tie
    const sv=Object.keys(o.sups);
    const sup = sv.length===0 ? '(unassigned)'
              : sv.length===1 ? sv[0]
              : 'multiple ('+sv.length+')';
    // replacement SHARE is the curbstoning signal, not the raw count: an enumerator working a
    // hard area legitimately racks up replacements, so only the proportion is comparable. Same
    // small-denominator discipline as cases/day — a share over <5 cases is noise, so it is not
    // flagged (2 of 3 replaced = 67% would otherwise outrank every real outlier).
    const replPct = o.cases>0 ? Math.round(100*o.repl/o.cases) : null;
    return {name:o.name, sup, cases:o.cases, completed:o.completed, partial:o.partial,
            repl:o.repl, replPct, replHot: (o.cases>=5 && replPct>=30), days,
            rate: days>0 ? Math.round(10*o.cases/days)/10 : null, last:o.last, mix:o.mix};
  });
  const st=prodSort;
  const val=(o,c)=> (c==='name'||c==='sup')?((o[c]||'').toLowerCase())
                  : (c==='last')?(o.last||'')
                  : (o[c]==null?-1:o[c]);
  rows.sort((a,b)=>{const x=val(a,st.col),y=val(b,st.col); return (x<y?-1:x>y?1:0)*st.dir;});
  const maxCases=rows.reduce((s,r)=>Math.max(s,r.cases),0);
  const totCases=rows.reduce((s,r)=>s+r.cases,0);
  const sum=document.createElement('div'); sum.className='cov-sum';
  sum.innerHTML='<b>'+rows.length+'</b> enumerator'+(rows.length===1?'':'s')
    +' · <b>'+totCases+'</b> case'+(totCases===1?'':'s')+' in view';
  el.appendChild(sum);
  const showMix=(instSel.value==='ALL');
  const showSup=(supSel.value==='ALL');   // redundant once you have drilled into one team
  const cols=(showSup?[['sup','Field supervisor','']]:[])
    .concat([['name','Enumerator','']])
    .concat(showMix?[['mix','Mix','']]:[])
    .concat([['cases','Cases','n'],['completed','Completed','n'],['partial','Partial','n'],
             ['repl','Replaced','n'],
             ['days','Active days','n'],['rate','Cases/day','n'],['last','Last active',''],
             ['bar','Volume','s']]);
  const tbl=document.createElement('table'); tbl.className='covtbl';
  const thead=document.createElement('tr');
  cols.forEach(([c,lbl,cl])=>{ const th=document.createElement('th'); if(cl)th.className=cl;
    th.textContent=lbl+(st.col===c?(st.dir>0?' ▲':' ▼'):'');
    if(c!=='bar'&&c!=='mix'){th.onclick=()=>{prodSort={col:c,dir:(st.col===c?-st.dir:(c==='name'?1:-1))}; render();};}
    thead.appendChild(th); });
  tbl.appendChild(thead);
  const fmtDate=d=>d?d.slice(0,4)+'-'+d.slice(4,6)+'-'+d.slice(6,8):'—';
  const fmtMix=mx=>['f1','f3','f4'].filter(k=>mx[k]).map(k=>k.toUpperCase()+' '+mx[k]).join(' · ')||'—';
  rows.forEach(r=>{ const tr=document.createElement('tr');
    const w=maxCases>0?Math.round(100*r.cases/maxCases):0;
    // "gone quiet" = no case for >2 days against the dashboard's own Manila today
    const idle=(P.today&&r.last)?daysBetween(r.last,P.today):null;
    const lastCls=(idle!==null&&idle>2)?' class="stale"':'';
    const lastTxt=fmtDate(r.last)+((idle!==null&&idle>2)?' ('+idle+'d ago)':'');
    tr.innerHTML=(showSup?'<td>'+esc(r.sup)+'</td>':'')
      +'<td>'+esc(r.name)+'</td>'
      +(showMix?'<td class="mix">'+esc(fmtMix(r.mix))+'</td>':'')
      +'<td class="n">'+r.cases+'</td>'
      +'<td class="n">'+r.completed+'</td>'
      +'<td class="n short'+(r.partial?'':' zero')+'">'+r.partial+'</td>'
      +'<td class="n'+(r.repl?'':' zero')+(r.replHot?' hot" title="'+r.replPct+'% of the cases for this enumerator were replaced — worth a look"'
                                        :'"')+'>'
        +r.repl+(r.repl?' <span class="pct">('+r.replPct+'%)</span>':'')+'</td>'
      +'<td class="n">'+r.days+'</td>'
      +'<td class="n rate'+(r.days<2?' lowconf" title="only one active day — a rate over a single day is not a trend':'')+'">'
        +(r.rate==null?'—':r.rate.toFixed(1))+'</td>'
      +'<td'+lastCls+'>'+esc(lastTxt)+'</td>'
      +'<td class="s"><div class="covbar"><span style="width:'+w+'%;background:#006b3f"></span></div></td>';
    tbl.appendChild(tr); });
  el.appendChild(tbl);
}
function render(){
  const inst=instSel.value, region=regSel.value, status=statSel.value, sup=supSel.value;
  const fromY=fromInp.value?fromInp.value.replace(/-/g,''):'';
  const toY=toInp.value?toInp.value.replace(/-/g,''):'';
  const pass=(r,ignoreStatus)=>{
    if(region!=='ALL' && r.region!==region) return false;
    if(sup!=='ALL' && r.supervisor!==sup) return false;
    if(!ignoreStatus && status!=='ALL' && r.status!==status) return false;
    if(fromY||toY){ const d=r.date; if(!(d&&d.length===8)) return false; if(fromY&&d<fromY) return false; if(toY&&d>toY) return false; }
    return true;
  };
  renderKpis(pass);
  renderTrend(pass);
  renderCoverage(pass);
  renderProductivity(pass);
  // INSTS (not a hardcoded f1/f3/f4 list) so F2 keeps its own card — the productivity
  // panel above still skips F2 internally, since it has no enumerator.
  INSTS.forEach(k=>{
    const rows=(P.data[k]||[]).filter(pass);
    cardNum[k].textContent=rows.length;
    cardNum[k].closest('.card').style.display=(inst==='ALL'||inst===k)?'':'none';
  });
  if(typeof Chart==='undefined') return;             // per-instrument charts need the vendored lib
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
instSel.onchange=render; regSel.onchange=render; supSel.onchange=render; statSel.onchange=render; fromInp.onchange=render; toInp.onchange=render;
document.getElementById('fReset').onclick=()=>{instSel.value='ALL';regSel.value='ALL';supSel.value='ALL';statSel.value='ALL';fromInp.value='';toInp.value='';render();};
render();
</script>
</body>
</html>
"""


def build(data, targets=None, plan=None, errored=None, f2_api_ok=None):
    """Assemble the payload + HTML from a {inst: [row-dict,...]} data map.

    `plan`    = assignment-plan provenance (provisional vs final) for the coverage banner.
    `errored` = the set of instruments whose live query failed (surfaced on the F2
                freshness note).
    """
    errored = errored or set()
    regions, supervisors = set(), set()
    for rows in data.values():
        for rec in rows:
            if rec.get("region"):
                regions.add(rec["region"])
            sup = rec.get("supervisor")
            if sup and sup != "(unassigned)":
                supervisors.add(sup)
    spec = [{"title": t, "prefix": p, "charts": [{"field": f, "title": ct, "type": ty} for f, ct, ty in c]}
            for t, p, c in SECTIONS]
    # visit-date range bounds (for the date inputs), from valid YYYYMMDD values
    _valid = [r["date"] for rows in data.values() for r in rows
              if r.get("date", "").isdigit() and len(r["date"]) == 8 and r["date"] != "00000000"]
    _iso = lambda d: d[:4] + "-" + d[4:6] + "-" + d[6:8]
    date_min = _iso(min(_valid)) if _valid else ""
    date_max = _iso(max(_valid)) if _valid else ""
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    # "today" for the KPI compares against device-local (Manila, UTC+8) visit dates
    today = (now_utc + datetime.timedelta(hours=8)).strftime("%Y%m%d")
    # F2 mirror freshness: count + last submission date (Manila YYYYMMDD from the query)
    _f2 = data.get("f2", [])
    _f2dates = [r["date"] for r in _f2
                if r.get("date", "").isdigit() and len(r["date"]) == 8 and r["date"] != "00000000"]
    f2meta = {"n": len(_f2), "last": max(_f2dates) if _f2dates else "", "err": "f2" in errored,
              "api": f2_api_ok}
    payload_obj = {
        "data": data,
        "spec": spec,
        "regions": sorted(regions),
        "supervisors": sorted(supervisors),
        "dateMin": date_min,
        "dateMax": date_max,
        "today": today,
        "targets": targets or {},
        "f2meta": f2meta,
        "plan": plan or {},
        "generated": now_utc.strftime("%Y-%m-%d %H:%M UTC"),
    }
    # XSS-safe: JSON in a non-executable <script type="application/json">, HTML-escaped,
    # read back via JSON.parse(el.textContent). &,<,> can't break out of the tag.
    payload = html.escape(json.dumps(payload_obj), quote=False)
    return TEMPLATE.replace("__PAYLOAD__", payload).replace("__FAVICON__", FAVICON)


def main():
    ap = argparse.ArgumentParser(description="Generate the CSWeb Sync Dashboard.")
    ap.add_argument("--sample", metavar="FIXTURE.json",
                    help="off-box dev: build from a JSON fixture instead of MySQL")
    ap.add_argument("--out", default=OUT, help="output HTML path (default: %(default)s)")
    ap.add_argument("--targets", default=TARGETS, help="targets.json path (default: %(default)s)")
    a = ap.parse_args()
    data, errored = load_sample(a.sample) if a.sample else fetch_live()
    api_ok = None if a.sample else f2_api_health()
    targets, plan = load_targets(a.targets)
    out_html = build(data, targets, plan, errored, api_ok)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(out_html)
    print("wrote %s (%d bytes); rows: f1=%d f3=%d f4=%d f2=%d%s"
          % (a.out, len(out_html), len(data.get("f1", [])), len(data.get("f3", [])),
             len(data.get("f4", [])), len(data.get("f2", [])), " [SAMPLE]" if a.sample else ""))


if __name__ == "__main__":
    main()
