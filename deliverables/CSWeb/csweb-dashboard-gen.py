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

# `syncuser` = the CSWeb account that UPLOADED the case — the only STABLE enumerator key we have.
#
# Why not just use ENUMERATOR_S_NAME: it is free text, 50 chars, retyped into every case. Two people
# called "Maria Santos" collapse into one row; one person typing "M. Santos" on Tuesday splits into
# two. At UAT scale that is invisible; at 100+ enumerators it silently corrupts every per-person
# number — including the replacement share, which is the curbstoning check. A name is not an ID, and
# the instruments carry no ID (INTERVIEWER_ID was removed 2026-06-12; the paper Field Control form
# has a name, not an ID, and the instruments follow the paper form — do NOT re-add a field).
#
# CSWeb already records this server-side, per case, and no instrument change is needed:
#   cspro_sync_history is APPEND-ONLY (revision = AUTO_INCREMENT primary key); every sync inserts a
#   row carrying username + device + dictionary_id + direction. A case's `last_modified_revision` IS
#   that revision. So joining cases.last_modified_revision = cspro_sync_history.revision (direction
#   'put' = upload) names the account that pushed the case.
#   Verified 2026-07-14 against the pre-cleanup backup: F1 cases at revision 111 -> 'aidan' (dict 4),
#   F3 at 114 -> 'aidan' (dict 5), F3 at 118 -> 'alytest' (dict 5). Exact match.
#
# HONEST LIMIT: this is who UPLOADED, not provably who interviewed. Under the RBAC model (one named
# account + one tablet per person) they are the same. They can diverge if a case is Bluetooth-synced
# between devices, or a supervisor uploads for someone. So the panel keeps the typed name visible
# and FLAGS disagreement rather than hiding it behind the login.
SYNCUSER = "COALESCE(NULLIF(sh.username,''),'(unknown)')"
# join once per instrument; `c` is already the cases alias in every query
SYNC_JOIN = (" LEFT JOIN csweb_uhc_y2.cspro_sync_history sh"
             " ON sh.revision = c.last_modified_revision AND sh.direction = 'put'")

QUERIES = {
    "f1": (["region", "province", "city", "facility", "ownership", "service_level", "result", "date", "status", "gps", "code9", "enumerator", "supervisor", "repl", "syncuser"],
           # NB: SYNC_JOIN is concatenated INSIDE the parens, before the % — `%` binds tighter
           # than `+`, so `"..." + SYNC_JOIN % (...)` would try to format SYNC_JOIN (which has no
           # placeholders) and raise. Keep the whole SQL in one parenthesised expression.
           ("SELECT COALESCE(NULLIF(fc.region_name,''),'(unknown)'),"
            " COALESCE(NULLIF(fc.province_name,''),'(unknown)'),"
            " COALESCE(NULLIF(fc.city_name,''),'(unknown)'),"
            " COALESCE(fn.name,'(unlabeled)'), %s, %s, %s,"
            " COALESCE(CAST(fc.date_first_visited_the_facility AS CHAR),''), %s, %s, %s, %s, %s, %s, %s"
            " FROM csweb_f1_breakout.`level-1` l"
            " JOIN csweb_f1_breakout.cases c ON c.id=l.`case-id` AND c.deleted=0"
            " LEFT JOIN csweb_f1_breakout.field_control fc ON fc.`level-1-id`=l.`level-1-id`"
            " LEFT JOIN csweb_f1_breakout.b_facility_profile bp ON bp.`level-1-id`=l.`level-1-id`"
            " LEFT JOIN csweb_f1_breakout.rec_facility_capture g ON g.`level-1-id`=l.`level-1-id`"
            " LEFT JOIN csweb_reports.facility_names fn ON fn.code9=%s"
            + SYNC_JOIN)
           % (F1_OWN, F1_SVC, F1_RES, STATUS, F1_GPS, F1_CODE9, ENUM, SUP, REPL, SYNCUSER, F1_CODE9)),
    "f3": (["region", "patient_type", "sex", "result", "date", "status", "gps", "code9", "enumerator", "supervisor", "repl", "syncuser"],
           ("SELECT COALESCE(NULLIF(fc.region_name,''),'(unknown)'),"
            " CASE fc.patient_type WHEN '1' THEN 'Outpatient' WHEN '2' THEN 'Inpatient' ELSE COALESCE(NULLIF(fc.patient_type,''),'(blank)') END,"
            " CASE bp.q7_sex WHEN '1' THEN 'Male' WHEN '2' THEN 'Female' ELSE COALESCE(NULLIF(bp.q7_sex,''),'(blank)') END,"
            " %s, COALESCE(CAST(fc.date_first_visited AS CHAR),''), %s, %s, LEFT(LPAD(l.`questionnaire_number`,12,'0'),9), %s, %s, %s, %s"
            " FROM csweb_f3_breakout.`level-1` l"
            " JOIN csweb_f3_breakout.cases c ON c.id=l.`case-id` AND c.deleted=0"
            " LEFT JOIN csweb_f3_breakout.field_control fc ON fc.`level-1-id`=l.`level-1-id`"
            " LEFT JOIN csweb_f3_breakout.b_patient_profile bp ON bp.`level-1-id`=l.`level-1-id`"
            " LEFT JOIN csweb_f3_breakout.rec_facility_capture g ON g.`level-1-id`=l.`level-1-id`"
            + SYNC_JOIN)
           % (F3_RES, STATUS, F3_GPS, ENUM, SUP, REPL, SYNCUSER)),
    "f4": (["region", "province", "result", "date", "status", "gps", "code9", "enumerator", "supervisor", "repl", "syncuser"],
           ("SELECT COALESCE(NULLIF(fc.region_name,''),'(unknown)'),"
            " COALESCE(NULLIF(fc.province_name,''),'(unknown)'),"
            " %s, COALESCE(CAST(fc.date_first_visited AS CHAR),''), %s, %s, LEFT(LPAD(l.`questionnaire_number`,12,'0'),9), %s, %s, %s, %s"
            " FROM csweb_f4_breakout.`level-1` l"
            " JOIN csweb_f4_breakout.cases c ON c.id=l.`case-id` AND c.deleted=0"
            " LEFT JOIN csweb_f4_breakout.field_control fc ON fc.`level-1-id`=l.`level-1-id`"
            " LEFT JOIN csweb_f4_breakout.household_geo_id g ON g.`level-1-id`=l.`level-1-id`"
            + SYNC_JOIN)
           % (F4_RES, STATUS, F4_GPS, ENUM, SUP, REPL, SYNCUSER)),
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
  .enumchip{display:flex;align-items:center;gap:8px;background:#e7f3ec;border:1px solid #b7d9c4;color:#004d2c;border-radius:10px;padding:7px 12px;font-size:13px;margin:0 2px 14px;width:fit-content;max-width:100%}
  .enumchip b{font-weight:700}
  .enumchip button{border:none;background:transparent;color:#006b3f;font-size:18px;line-height:1;cursor:pointer;padding:0 2px}
  .enumchip button:hover{color:#d32f2f}
  .covtbl tr.clickable{cursor:pointer}
  .covtbl tr.clickable:hover{background:#f0f7f3}
  .covtbl tr.selrow{background:#e7f3ec}
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
  /* a row with no CSWeb login is keyed on the typed name — the unreliable path. Say so. */
  .covtbl td.nolog{color:var(--muted);font-style:italic}
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
    <div class="f"><label for="fEnum">Enumerator</label><select id="fEnum"></select></div>
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
  <div id="enumChip" class="enumchip" hidden></div>
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
// Enumerator filter — keyed on the CSWeb upload login (syncuser) with typed-name fallback,
// exactly like the productivity panel below, so a person reads the same on both. Built from
// f1/f3/f4 rows only (F2 is self-administered — no enumerator).
const enumSel=document.getElementById('fEnum');
function enumKeyOf(r){ return (r.syncuser&&r.syncuser!=='(unknown)') ? 'u:'+r.syncuser
                     : (r.enumerator&&r.enumerator!=='(unassigned)') ? 'n:'+r.enumerator : ''; }
enumSel.add(new Option('All enumerators','ALL'));
(function(){
  const em=new Map();
  ['f1','f3','f4'].forEach(k=>(P.data[k]||[]).forEach(r=>{
    const key=enumKeyOf(r); if(!key) return;
    let o=em.get(key); if(!o){o={key,login:(r.syncuser&&r.syncuser!=='(unknown)')?r.syncuser:null,names:{}}; em.set(key,o);}
    if(r.enumerator&&r.enumerator!=='(unassigned)') o.names[r.enumerator]=(o.names[r.enumerator]||0)+1;
  }));
  const lbl=o=>{const nm=Object.keys(o.names).sort((a,b)=>o.names[b]-o.names[a])[0]||(o.login?'(no name)':'(unknown)'); return o.login?(nm+' · '+o.login):nm;};
  [...em.values()].map(o=>[o.key,lbl(o)]).sort((a,b)=>a[1].toLowerCase()<b[1].toLowerCase()?-1:1).forEach(([v,t])=>enumSel.add(new Option(t,v)));
})();

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
// plan.provisional is a bool (whole plan) OR an object keyed by instrument — F1 can be real
// (facility-derived denominator) while F3/F4 stay provisional. Resolve PER instrument so a
// real F1 is never tarred with a placeholder warning, and a placeholder is never let through.
function planProvisionalFor(pl, k){
  const pv=(pl||{}).provisional;
  if(pv && typeof pv==='object') return pv[k]!==false;
  return pv!==false;
}
function renderCoverage(pass){
  const cov=document.getElementById('coverage'); cov.innerHTML='';
  const T=P.targets||{};
  const visible=visInsts(instSel.value).filter(k=>T[k]&&Object.keys(T[k]).length);
  if(!visible.length) return;                         // no targets → section hides (graceful)
  const h=document.createElement('h2'); h.textContent='Coverage vs. target'; cov.appendChild(h);
  // Provenance FIRST. A coverage % divided by a placeholder plan renders identically to a
  // real one; this banner is the only thing standing between a fixture and a DOH briefing.
  const pl=P.plan||{};
  const provInsts=visible.filter(k=>planProvisionalFor(pl,k));
  const realInsts=visible.filter(k=>!planProvisionalFor(pl,k));
  if(provInsts.length){
    const w=document.createElement('div'); w.className='planwarn';
    const f=pl.facilities||{}, nf=provInsts.reduce((s,k)=>s+(f[k]||0),0);
    const who=provInsts.map(k=>k.toUpperCase()+' · '+(NAMES[k]||k)).join(', ');
    w.innerHTML='<b>PROVISIONAL ASSIGNMENT PLAN — '+esc(who)+' percentages are not real coverage.</b> '
      +'Their targets come from <b>'+esc(pl.label||'an unlabelled targets.json')+'</b>'
      +(pl.assignments?' ('+pl.assignments+' assignment row'+(pl.assignments===1?'':'s')
         +' across '+nf+' facility slot'+(nf===1?'':'s')+')':'')
      +'. Every % and shortfall for those instruments is measured against that placeholder. Replace '
      +'<code>assignments-source.csv</code> with ASPSI’s real EA plan and re-run '
      +'<code>gen-targets.py --final</code> before quoting them.';
    cov.appendChild(w);
  }
  // Provenance cuts both ways: staying silent on a REAL denominator loses it just as surely
  // as mislabelling a placeholder. Name the source for the instruments that are real.
  if(realInsts.length){
    const r=document.createElement('div'); r.className='cov-note';
    const who=realInsts.map(k=>k.toUpperCase()+' · '+(NAMES[k]||k)).join(', ');
    const src=(realInsts.indexOf('f1')>=0 && pl.f1_source) ? pl.f1_source : (pl.label||'the declared final plan');
    r.innerHTML='<b>'+esc(who)+'</b> — targets are REAL, from <b>'+esc(src)+'</b>.';
    cov.appendChild(r);
  }
  const note=document.createElement('div'); note.className='cov-note';
  note.textContent='Landed = Completed cases in the current view (instrument · region · visit-date). Expected = the assignment plan’s target. The Status filter does not apply here.';
  cov.appendChild(note);
  visible.forEach(k=>{
    const tgt=T[k], comp={}; let untarget=0;
    (P.data[k]||[]).forEach(r=>{ if(r.status!=='Completed'||!pass(r,true,true)) return; if(tgt[r.code9]) comp[r.code9]=(comp[r.code9]||0)+1; else untarget++; });
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
      // KEY on the CSWeb sync login, not the typed name. The name is free text retyped into every
      // case — two "Maria Santos" collapse into one row, one person typing it three ways splits
      // into three, and every per-person number (incl. the replacement share) silently rots at
      // scale. The login is assigned, stable, and recorded server-side per case.
      // Fall back to the typed name only when no sync row exists (e.g. a case that predates this).
      const login=r.syncuser;
      const nm=r.enumerator;
      const key=(login&&login!=='(unknown)') ? 'u:'+login : (nm&&nm!=='(unassigned)' ? 'n:'+nm : null);
      if(!key){unnamed++; return;}
      let o=m.get(key);
      if(!o){o={key,login:(login&&login!=='(unknown)')?login:null,
                cases:0,completed:0,partial:0,repl:0,days:new Set(),last:'',mix:{},sups:{},names:{}}; m.set(key,o);}
      // keep every typed name seen under this login — disagreement is a finding, not noise
      if(nm&&nm!=='(unassigned)') o.names[nm]=(o.names[nm]||0)+1;
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
  note.textContent='Rows are keyed on the CSWeb login that uploaded the case (stable), not the typed '
    +'Enumerator name (free text — two people can share one, and one person can type theirs three ways). '
    +'The login is who SYNCED, which under one-account-per-person is the enumerator; it can differ if a '
    +'case was Bluetooth-transferred or a supervisor uploaded it. A login that typed more than one name '
    +'is flagged — shared tablet, borrowed account, or sloppy typing, all of which corrupt name-keyed '
    +'reporting. A row with no login (—) falls back to the typed name and is not reliable. '
    +'Cases/day = cases in the current view ÷ the distinct days that enumerator was active — '
    +'so it measures pace on the days they actually worked, not calendar days. A rate over a single '
    +'active day is greyed out: it is arithmetic, not a trend. Check Last active before reading a high '
    +'rate as good news. Replaced = the sampled unit was never interviewed (refused at the door, not '
    +'found, or ineligible) and a substitute was drawn; postponed visits are NOT replacements. The share '
    +'is flagged red only at 30% or more over at least 5 cases — a hard catchment legitimately produces '
    +'replacements, so the raw count is not comparable between enumerators. Honours every filter above. '
    +'F2 is absent by design: it is self-administered and has no enumerator. '
    +'Click any row to filter the whole dashboard to that enumerator (click again to clear).'
    +(unnamed?' '+unnamed+' case(s) in view carry no enumerator name.':'');
  el.appendChild(note);
  let rows=[...m.values()].map(o=>{
    const days=o.days.size;
    // display name = the one this login types most often; keep the alternates for the tooltip
    const nameList=Object.keys(o.names).sort((a,b)=>o.names[b]-o.names[a]);
    const name=nameList[0] || (o.login?'(no name typed)':'(unknown)');
    // one login typing several different names is worth a look: a shared tablet, a borrowed
    // account, or just sloppy typing — all of which corrupt name-keyed reporting
    const nameSplit=nameList.length>1;
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
    return {key:o.key, name, login:o.login, nameSplit, nameList, sup,
            cases:o.cases, completed:o.completed, partial:o.partial,
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
    .concat([['login','CSWeb login',''],['name','Enumerator','']])
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
    tr.className='clickable'+(enumSel.value===r.key?' selrow':'');
    tr.title='Click to filter the whole dashboard to this enumerator (click again to clear)';
    tr.onclick=()=>{ enumSel.value=(enumSel.value===r.key?'ALL':r.key); render(); };
    const w=maxCases>0?Math.round(100*r.cases/maxCases):0;
    // "gone quiet" = no case for >2 days against the dashboard's own Manila today
    const idle=(P.today&&r.last)?daysBetween(r.last,P.today):null;
    const lastCls=(idle!==null&&idle>2)?' class="stale"':'';
    const lastTxt=fmtDate(r.last)+((idle!==null&&idle>2)?' ('+idle+'d ago)':'');
    tr.innerHTML=(showSup?'<td>'+esc(r.sup)+'</td>':'')
      +'<td'+(r.login?'':' class="nolog" title="no sync record — this row is keyed on the typed name and may merge or split people"')+'>'
        +esc(r.login||'—')+'</td>'
      +'<td'+(r.nameSplit?' class="hot" title="this one login typed '+r.nameList.length+' different names: '+esc(r.nameList.join(', '))+'"':'')+'>'
        +esc(r.name)+(r.nameSplit?' <span class="pct">(+'+(r.nameList.length-1)+')</span>':'')+'</td>'
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
  const inst=instSel.value, region=regSel.value, status=statSel.value, sup=supSel.value, enumK=enumSel.value;
  const fromY=fromInp.value?fromInp.value.replace(/-/g,''):'';
  const toY=toInp.value?toInp.value.replace(/-/g,''):'';
  // ignoreEnum: Coverage vs. target stays FACILITY-level. Enumerators aren't assigned to
  // facilities in the plan (assignments-source.csv has a blank enumerator_id), so an
  // enumerator filter can't slice a facility target — coverage passes ignoreEnum=true.
  const pass=(r,ignoreStatus,ignoreEnum)=>{
    if(region!=='ALL' && r.region!==region) return false;
    if(sup!=='ALL' && r.supervisor!==sup) return false;
    if(!ignoreEnum && enumK!=='ALL' && enumKeyOf(r)!==enumK) return false;
    if(!ignoreStatus && status!=='ALL' && r.status!==status) return false;
    if(fromY||toY){ const d=r.date; if(!(d&&d.length===8)) return false; if(fromY&&d<fromY) return false; if(toY&&d>toY) return false; }
    return true;
  };
  // enumerator filter chip (click a leaderboard row or use the dropdown to set it)
  const chip=document.getElementById('enumChip');
  if(enumK!=='ALL'){ const opt=enumSel.options[enumSel.selectedIndex];
    chip.hidden=false;
    chip.innerHTML='Filtered to enumerator: <b>'+esc(opt?opt.text:enumK)+'</b> <button type="button" id="enumClear" aria-label="Clear filter" title="Clear">&times;</button>';
    chip.querySelector('#enumClear').onclick=()=>{ enumSel.value='ALL'; render(); };
  } else { chip.hidden=true; chip.innerHTML=''; }
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
instSel.onchange=render; regSel.onchange=render; supSel.onchange=render; enumSel.onchange=render; statSel.onchange=render; fromInp.onchange=render; toInp.onchange=render;
document.getElementById('fReset').onclick=()=>{instSel.value='ALL';regSel.value='ALL';supSel.value='ALL';enumSel.value='ALL';statSel.value='ALL';fromInp.value='';toInp.value='';render();};
render();
</script>
<!-- ===== sync-activity notification bell (2026-07-15) — polls /docs/sync-feed.json ===== -->
<style>
#bellWrap{position:fixed;top:14px;right:20px;z-index:9999;font:14px system-ui,Segoe UI,Roboto,sans-serif}
#bellBtn{position:relative;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.4);border-radius:10px;padding:7px 9px;cursor:pointer;line-height:0}
#bellBtn:hover{background:rgba(255,255,255,.3)}
#bellBadge{position:absolute;top:-7px;right:-7px;min-width:19px;height:19px;padding:0 4px;background:#d32f2f;color:#fff;border-radius:10px;font-size:11px;font-weight:700;line-height:19px;text-align:center;box-shadow:0 0 0 2px #006b3f}
#bellPanel{position:absolute;top:46px;right:0;width:330px;max-height:62vh;background:#fff;color:#1c2b25;border:1px solid #dfe7e2;border-radius:12px;box-shadow:0 10px 34px rgba(0,0,0,.2);overflow:hidden;display:flex;flex-direction:column}
#bellPanel[hidden]{display:none}
#bellHead{padding:11px 14px;font-weight:700;color:#004d2c;border-bottom:1px solid #eef3f0;display:flex;justify-content:space-between;align-items:center;gap:8px}
#bellEnable{font:12px system-ui;padding:4px 9px;border:1px solid #dfe7e2;border-radius:7px;background:#f4f7f5;cursor:pointer;color:#006b3f;font-weight:600;white-space:nowrap}
#bellEnable.on{background:#006b3f;color:#fff;border-color:#006b3f}
.bh-right{display:flex;align-items:center;gap:4px}
#bellClose{font:20px/1 system-ui;width:26px;height:26px;border:none;background:transparent;color:#5b6b63;cursor:pointer;border-radius:6px}
#bellClose:hover{background:#eef3f0;color:#1c2b25}
#bellList{overflow-y:auto;padding:2px 0}
#bellList .brow{padding:9px 14px;border-bottom:1px solid #f1f5f3}
#bellList .brow:last-child{border-bottom:none}
#bellList .brow.fresh{background:#eef8f1}
#bellList .brow.dim{opacity:.6}
#bellList .bmuted{color:#8a9791;font-style:italic}
#bellAlerts:empty{display:none}
.balert{padding:10px 14px;border-bottom:1px solid #fbe3e3;background:#fdf0f0;color:#8a1c1c;font-size:12.8px;line-height:1.45}
.balert b{color:#b71c1c}
.btoast.alert{background:#b71c1c}.btoast.alert b{color:#ffe08a}
#bellList .who{font-weight:700}
#bellList .sub{color:#5b6b63;font-size:12.5px}
#bellList .inst{display:inline-block;font-size:11px;font-weight:700;color:#006b3f;background:#e7f3ec;border-radius:5px;padding:0 6px;margin-right:6px}
.bellEmpty{padding:24px 14px;color:#5b6b63;font-style:italic;text-align:center}
#bellFoot{padding:8px 14px;border-top:1px solid #eef3f0;color:#5b6b63;font-size:11.5px}
#toastWrap{position:fixed;bottom:18px;right:18px;z-index:10000;display:flex;flex-direction:column;gap:10px}
.btoast{background:#004d2c;color:#fff;border-radius:10px;padding:11px 15px;box-shadow:0 6px 24px rgba(0,0,0,.25);max-width:320px;transition:opacity .4s;animation:btin .25s ease}
.btoast b{color:#ffe08a}
@keyframes btin{from{transform:translateX(20px);opacity:0}to{transform:none;opacity:1}}
@media(max-width:820px){#bellPanel{width:290px}#bellWrap{top:12px;right:12px}}
</style>
<div id="bellWrap">
  <button id="bellBtn" title="Sync activity" aria-label="Sync activity">
    <svg viewBox="0 0 24 24" width="21" height="21" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/></svg>
    <span id="bellBadge" hidden>0</span>
  </button>
  <div id="bellPanel" hidden>
    <div id="bellHead"><span>Activity</span><span class="bh-right"><button id="bellEnable" type="button">Enable alerts</button><button id="bellClose" type="button" aria-label="Close" title="Close">&times;</button></span></div>
    <div id="bellAlerts"></div>
    <div id="bellList"><div class="bellEmpty">Waiting for the next device sync&hellip;</div></div>
    <div id="bellFoot">Live &middot; every device sync (upload) appears here</div>
  </div>
</div>
<div id="toastWrap"></div>
<script>
(function(){
  var FEED='/docs/sync-feed.json', LS='uhc_bell_seen_rev';
  var badge=document.getElementById('bellBadge'), panel=document.getElementById('bellPanel'),
      btn=document.getElementById('bellBtn'), list=document.getElementById('bellList'),
      enableBtn=document.getElementById('bellEnable'), toastWrap=document.getElementById('toastWrap'),
      wrap=document.getElementById('bellWrap'), alertBox=document.getElementById('bellAlerts');
  var LS2='uhc_bell_alert_notified';
  var s0=localStorage.getItem(LS);
  var seenRev = s0===null ? null : parseInt(s0,10);
  var notifiedRev=null, latest=[], alerts=[];
  function esc(x){return String(x==null?'':x).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  function fmt(iso){try{return new Date(iso).toLocaleString('en-PH',{hour:'numeric',minute:'2-digit',hour12:true,month:'short',day:'numeric'});}catch(e){return iso||'';}}
  function render(){
    if(!latest.length){list.innerHTML='<div class="bellEmpty">Waiting for the next device sync&hellip;</div>';return;}
    var base=(seenRev==null)?Infinity:seenRev;
    list.innerHTML=latest.map(function(e){
      var tn=e.total_new||0, te=e.total_edited||0, active=(tn>0||te>0);
      var fresh=(e.rev>base&&tn>0)?' fresh':'';
      var det;
      if(active){
        det=(e.items||[]).filter(function(it){return (it.new||0)>0||(it.edited||0)>0;}).map(function(it){
          var p=[]; if(it.new>0)p.push('<b>'+it.new+'</b> new'); if(it.edited>0)p.push('<b>'+it.edited+'</b> edited');
          return '<span class="inst">'+esc(it.inst)+'</span> '+p.join(' + ');
        }).join(' &middot; ')+' &middot; '+fmt(e.time);
      }else{
        det='<span class="bmuted">no new cases</span> &middot; '+fmt(e.time);
      }
      return '<div class="brow'+fresh+(active?'':' dim')+'"><div class="who">'+esc(e.name||e.user)+(e.name?' <span class="sub">'+esc(e.user)+'</span>':'')+' synced</div>'+
             '<div class="sub">'+det+'</div></div>';
    }).join('');
  }
  function badgeUpd(){
    var base=(seenRev==null)?Infinity:seenRev;
    var n=latest.filter(function(e){return e.rev>base&&(e.total_new||0)>0;}).length + alerts.length;
    if(n>0){badge.textContent=n>99?'99+':n;badge.hidden=false;}else{badge.hidden=true;}
  }
  function toast(e){
    var d=(e.items||[]).filter(function(it){return (it.new||0)>0;}).map(function(it){return it.inst+': '+it.new+' new case'+(it.new==1?'':'s');}).join(', ');
    var t=document.createElement('div');t.className='btoast';
    t.innerHTML='&#128276; <b>'+esc(e.name||e.user)+'</b> synced &middot; <b>'+esc(d)+'</b>';
    toastWrap.appendChild(t);
    setTimeout(function(){t.style.opacity='0';setTimeout(function(){t.remove();},400);},6000);
  }
  function osNotify(e){
    if(!('Notification' in window)||Notification.permission!=='granted')return;
    var d=(e.items||[]).filter(function(it){return (it.new||0)>0;}).map(function(it){return it.inst+': '+it.new+' new case'+(it.new==1?'':'s');}).join(', ');
    try{new Notification((e.name||e.user)+' synced',{body:d+' · '+fmt(e.time),tag:'sync-'+e.rev});}catch(err){}
  }
  function renderAlerts(){
    if(!alerts.length){alertBox.innerHTML='';return;}
    alertBox.innerHTML=alerts.map(function(a){
      var txt;
      if(a.type==='dup'){
        txt='<b>Duplicate case key</b> '+esc(a.key)+' &middot; '+esc(a.inst)+' &middot; '+a.n+' cases'+((a.users&&a.users.length)?(' &middot; '+esc(a.users.join(', '))):'');
      }else{
        txt='<b>Off-plan '+(a.n>1?'cases':'case')+'</b> facility '+esc(a.code9)+' &middot; '+esc(a.inst)+' &middot; '+a.n+' not in plan'+((a.users&&a.users.length)?(' &middot; '+esc(a.users.join(', '))):'');
      }
      return '<div class="balert">&#9888;&#65039; '+txt+'</div>';
    }).join('');
  }
  function alertToast(a){
    var msg=(a.type==='dup')?('Duplicate key '+a.key+' ('+a.inst+')'):('Off-plan case '+(a.code9||a.example||'')+' ('+a.inst+')');
    var t=document.createElement('div');t.className='btoast alert';
    t.innerHTML='&#9888;&#65039; <b>'+esc(msg)+'</b>'+((a.users&&a.users.length)?(' &middot; '+esc(a.users.join(', '))):'');
    toastWrap.appendChild(t);
    setTimeout(function(){t.style.opacity='0';setTimeout(function(){t.remove();},400);},9000);
  }
  function alertNotify(a){
    if(!('Notification' in window)||Notification.permission!=='granted')return;
    var title=(a.type==='dup')?'⚠️ Duplicate case key':'⚠️ Case outside the plan';
    var body=(a.type==='dup')?(a.key+' · '+a.inst+' · '+a.n+' cases'):('facility '+a.code9+' · '+a.inst+' · '+a.n+' case(s)');
    if(a.users&&a.users.length)body+=' · '+a.users.join(', ');
    try{new Notification(title,{body:body,tag:a.id,requireInteraction:true});}catch(err){}
  }
  function poll(){
    fetch(FEED+'?_='+Date.now(),{cache:'no-store'}).then(function(r){return r.json();}).then(function(d){
      latest=(d&&d.events)||[]; alerts=(d&&d.alerts)||[];
      if(latest.length){
        var maxRev=latest[0].rev;
        if(seenRev==null){seenRev=maxRev;localStorage.setItem(LS,String(seenRev));}
        if(notifiedRev==null){notifiedRev=maxRev;}
        else if(maxRev>notifiedRev){
          latest.filter(function(e){return e.rev>notifiedRev&&(e.total_new||0)>0;}).sort(function(a,b){return a.rev-b.rev;}).forEach(function(e){toast(e);osNotify(e);});
          notifiedRev=maxRev;
        }
      }
      var firstA=(localStorage.getItem(LS2)===null), seen=[];
      try{seen=JSON.parse(localStorage.getItem(LS2)||'[]');}catch(e){seen=[];}
      var sset={}; seen.forEach(function(k){sset[k]=1;});
      alerts.forEach(function(a){ if(!sset[a.id]){ if(!firstA){alertToast(a);alertNotify(a);} seen.push(a.id); sset[a.id]=1; } });
      localStorage.setItem(LS2, JSON.stringify(seen.slice(-300)));
      render(); renderAlerts(); badgeUpd();
    }).catch(function(){});
  }
  btn.addEventListener('click',function(){
    if(panel.hasAttribute('hidden')){
      panel.removeAttribute('hidden');
      if(latest.length){seenRev=latest[0].rev;localStorage.setItem(LS,String(seenRev));}
      badgeUpd();render();
    }else{panel.setAttribute('hidden','');}
  });
  document.getElementById('bellClose').addEventListener('click',function(ev){ev.stopPropagation();panel.setAttribute('hidden','');});
  document.addEventListener('click',function(ev){if(!wrap.contains(ev.target)){panel.setAttribute('hidden','');}});
  function reflect(){if(('Notification' in window)&&Notification.permission==='granted'){enableBtn.textContent='Alerts on';enableBtn.classList.add('on');}}
  enableBtn.addEventListener('click',function(ev){ev.stopPropagation();
    if(!('Notification' in window)){enableBtn.textContent='Not supported';return;}
    Notification.requestPermission().then(reflect);
  });
  reflect(); poll(); setInterval(poll,20000);
})();
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
