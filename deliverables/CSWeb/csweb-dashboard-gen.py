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

Case list (Phase 4, 2026-07-17): a per-case drill-down table at the bottom — one row
per synced case (QN · facility/area · result · status · visit · enumerator · login),
honouring every filter, with a search box. Each F1/F3/F4 row deep-links to the CSWeb
Sync Report's View case modal (?dict=<DICT>&case=<QN> — on-box patch #7 auto-opens
it; CSWeb login required), so full responses are one click away WITHOUT putting any
response data on this unauthenticated page. `qn` is the RAW stored key (legacy
region-01 keys may be 11-digit unpadded) so the deep link always matches the case.

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
import subprocess, json, datetime, html, argparse, hashlib
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import portal_shell as PS
import phase_lib
import activity_lib

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
    " LEFT(COALESCE(NULLIF(r.qn,''),r.facility_id,''),9),"
    # qn = the full stored key for the Case list (12-digit QN post-2026-07-08; earlier
    # rows fall back to facility_id/slug).
    " COALESCE(NULLIF(r.qn,''),r.facility_id,''),"
    # sub = submission_id, the F2 Admin Portal's own response key. It is what
    # GET /admin/api/dashboards/data/responses/:id resolves on, and what the Data
    # tab's ?q= filter matches unambiguously - unlike qn, which is a 12-digit number
    # the q filter could also find inside another row's values_json.
    " COALESCE(r.submission_id,'')"
    " FROM csweb_f2.f2_responses r"
    " LEFT JOIN csweb_f2.f2_facility_master fm ON fm.facility_id=r.facility_id"
    # #831: voided responses (admin void action, status='voided') never count.
    " WHERE COALESCE(r.status,'') <> 'voided'")

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
    "f1": (["region", "province", "city", "facility", "ownership", "service_level", "result", "date", "status", "gps", "code9", "enumerator", "supervisor", "repl", "syncuser", "qn"],
           # NB: SYNC_JOIN is concatenated INSIDE the parens, before the % — `%` binds tighter
           # than `+`, so `"..." + SYNC_JOIN % (...)` would try to format SYNC_JOIN (which has no
           # placeholders) and raise. Keep the whole SQL in one parenthesised expression.
           ("SELECT COALESCE(NULLIF(fc.region_name,''),'(unknown)'),"
            " COALESCE(NULLIF(fc.province_name,''),'(unknown)'),"
            " COALESCE(NULLIF(fc.city_name,''),'(unknown)'),"
            " COALESCE(fn.name,'(unlabeled)'), %s, %s, %s,"
            " COALESCE(CAST(fc.date_first_visited_the_facility AS CHAR),''), %s, %s, %s, %s, %s, %s, %s,"
            " COALESCE(l.`questionnaire_number`,'')"
            " FROM csweb_f1_breakout.`level-1` l"
            " JOIN csweb_f1_breakout.cases c ON c.id=l.`case-id` AND c.deleted=0"
            " LEFT JOIN csweb_f1_breakout.field_control fc ON fc.`level-1-id`=l.`level-1-id`"
            " LEFT JOIN csweb_f1_breakout.b_facility_profile bp ON bp.`level-1-id`=l.`level-1-id`"
            " LEFT JOIN csweb_f1_breakout.rec_facility_capture g ON g.`level-1-id`=l.`level-1-id`"
            " LEFT JOIN csweb_reports.facility_names fn ON fn.code9=%s"
            + SYNC_JOIN)
           % (F1_OWN, F1_SVC, F1_RES, STATUS, F1_GPS, F1_CODE9, ENUM, SUP, REPL, SYNCUSER, F1_CODE9)),
    "f3": (["region", "patient_type", "sex", "result", "date", "status", "gps", "code9", "enumerator", "supervisor", "repl", "syncuser", "qn"],
           ("SELECT COALESCE(NULLIF(fc.region_name,''),'(unknown)'),"
            " CASE fc.patient_type WHEN '1' THEN 'Outpatient' WHEN '2' THEN 'Inpatient' ELSE COALESCE(NULLIF(fc.patient_type,''),'(blank)') END,"
            " CASE bp.q7_sex WHEN '1' THEN 'Male' WHEN '2' THEN 'Female' ELSE COALESCE(NULLIF(bp.q7_sex,''),'(blank)') END,"
            " %s, COALESCE(CAST(fc.date_first_visited AS CHAR),''), %s, %s, LEFT(LPAD(l.`questionnaire_number`,12,'0'),9), %s, %s, %s, %s,"
            " COALESCE(l.`questionnaire_number`,'')"
            " FROM csweb_f3_breakout.`level-1` l"
            " JOIN csweb_f3_breakout.cases c ON c.id=l.`case-id` AND c.deleted=0"
            " LEFT JOIN csweb_f3_breakout.field_control fc ON fc.`level-1-id`=l.`level-1-id`"
            " LEFT JOIN csweb_f3_breakout.b_patient_profile bp ON bp.`level-1-id`=l.`level-1-id`"
            " LEFT JOIN csweb_f3_breakout.rec_facility_capture g ON g.`level-1-id`=l.`level-1-id`"
            + SYNC_JOIN)
           % (F3_RES, STATUS, F3_GPS, ENUM, SUP, REPL, SYNCUSER)),
    "f4": (["region", "province", "result", "date", "status", "gps", "code9", "enumerator", "supervisor", "repl", "syncuser", "qn"],
           ("SELECT COALESCE(NULLIF(fc.region_name,''),'(unknown)'),"
            " COALESCE(NULLIF(fc.province_name,''),'(unknown)'),"
            " %s, COALESCE(CAST(fc.date_first_visited AS CHAR),''), %s, %s, LEFT(LPAD(l.`questionnaire_number`,12,'0'),9), %s, %s, %s, %s,"
            " COALESCE(l.`questionnaire_number`,'')"
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
    "f2": (["region", "province", "result", "source", "date", "status", "gps", "code9", "qn",
            "sub"], F2_SQL),
}


def rootpw():
    with open(ENV) as f:
        for line in f:
            if line.startswith("MYSQL_ROOT_PASSWORD"):
                return line.split("=", 1)[1].strip()
    raise SystemExit("MYSQL_ROOT_PASSWORD not found in " + ENV)


def q(sql):
    # --default-character-set=utf8mb4: without it the client negotiates latin1, the
    # server transcodes, and the first enye in a selected value (Biñan, Peña) becomes
    # byte 0xF1 — which crashes the strict UTF-8 decode. Found 2026-07-18 via the
    # responses generator (which SELECTs everything); latent here until a ñ lands in a
    # selected field. errors="replace" backstops any genuinely broken byte.
    r = subprocess.run(
        ["docker", "compose", "exec", "-T", "database", "mysql", "-uroot",
         "-p" + rootpw(), "--default-character-set=utf8mb4", "--batch", "-N", "-e", sql],
        cwd=COMPOSE_DIR, capture_output=True, text=True, errors="replace")
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
  .enumchip[hidden]{display:none}  /* display:flex would otherwise beat the hidden attribute's UA rule */
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
  /* Audit F5: progress and exception measures used to sit in one undifferentiated row of
     six, so a rising "No GPS fix" read exactly like a rising "Completed". They are now two
     labelled groups, and the exception group is set off by a rule and a warning glyph. */
  .kpiwrap{display:grid;grid-template-columns:2fr 1fr;gap:20px;align-items:start;margin-bottom:6px}
  .kpigrp{min-width:0}
  .kpigrp .kpis{grid-template-columns:repeat(4,1fr);margin-bottom:0}
  .kpigrp.attn .kpis{grid-template-columns:repeat(2,1fr)}
  .kpigrp.attn{border-left:3px solid var(--red);padding-left:15px}
  .grph{font-size:11px;font-weight:800;letter-spacing:.11em;text-transform:uppercase;color:var(--muted);margin:0 2px 9px}
  .kpigrp.attn .grph{color:var(--red)}
  /* Audit F4: the comparator line. Deliberately quiet - it must be readable without
     competing with the number it qualifies. */
  .kpi .cmp{margin-top:7px;font-size:11.5px;font-weight:600;color:var(--muted);min-height:15px}
  /* Audit F12: one-line universe statement per panel. */
  .universe{color:var(--muted);font-size:12.5px;margin:-6px 2px 14px;max-width:95ch}
  /* Audit F6: shown only while the enumerator filter is active. */
  .scopebadge{background:#fff8e6;border-left:3px solid var(--gold);color:#5c4708;font-size:12.5px;
    margin:2px 2px 12px;padding:8px 12px;border-radius:0 8px 8px 0}
  @media(max-width:1100px){.kpiwrap{grid-template-columns:1fr}
    .kpigrp.attn{border-left:0;padding-left:0;border-top:3px solid var(--red);padding-top:14px}}
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
  /* ===== Downloads band (2026-07-18, post-#843): dual case-data paths ===== */
  .dl{display:flex;flex-wrap:wrap;gap:10px;margin:10px 2px;align-items:center}
  .dl .rl{font-size:12.5px;color:var(--muted);min-width:168px;font-weight:700}
  .dl a{display:inline-block;padding:8px 14px;border-radius:10px;font-weight:700;font-size:13px;text-decoration:none;border:1.5px solid var(--g);color:var(--gd);background:#fff}
  .dl a:hover{background:#eef7f2}
  .dl a.zip{background:var(--g);color:#fff;border-color:var(--g)}
  .dl a.zip:hover{background:var(--gd)}
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
  /* ===== purpose bands + accordion + quality panel (2026-07-17 IA redesign) ===== */
  .band{margin:42px 2px 14px;padding-bottom:9px;font-size:13px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:var(--gd);display:flex;align-items:center;gap:10px;border-bottom:2px solid rgba(0,107,63,.16);scroll-margin-top:10px}.band:first-of-type{margin-top:24px}#caselist{max-height:62vh;overflow:auto;border:1px solid #e2e9e5;border-radius:10px;background:#fff}#caselist table{margin:0}#caselist thead th{position:sticky;top:0;z-index:2;background:#f4f8f6;box-shadow:inset 0 -1px 0 #e2e9e5}.cl-hint{font-size:12px;color:#63736a;margin:8px 2px 0}@media(max-width:900px){#caselist{max-height:70vh}}
  header nav{margin-top:10px;display:flex;flex-wrap:wrap;gap:6px 18px;font-size:13px}
  header nav a{color:#fff;opacity:.92;text-decoration:none;border-bottom:1px solid rgba(255,255,255,.45);padding-bottom:1px}
  header nav a:hover{opacity:1;border-bottom-color:#fff}
  header nav .here{opacity:1;font-weight:700;border-bottom:2px solid var(--gold)}
  .howto{margin:14px 2px 4px;border:1px solid var(--line);border-left:4px solid var(--g);border-radius:10px;background:#fff}
  .howto>summary{cursor:pointer;padding:11px 14px;font-weight:700;color:var(--gd);font-size:14px;list-style:none}
  .howto>summary::-webkit-details-marker{display:none}
  .howto>summary::before{content:"▸ ";color:var(--g)}
  .howto[open]>summary::before{content:"▾ "}
  .howto .body{padding:2px 16px 14px;font-size:13.5px;color:var(--ink);line-height:1.55}
  .howto .body p{margin:6px 0}
  .howto .body ul{margin:6px 0 6px 18px;padding:0}
  .howto .body li{margin:3px 0}
  .howto .body a{color:var(--g);font-weight:600}
  .howto .jump{margin-top:10px;display:flex;flex-wrap:wrap;gap:8px}
  .howto .jump a{font-size:12.5px;background:#eef3f0;border:1px solid var(--line);border-radius:999px;padding:4px 11px;text-decoration:none}
  .band::after{content:"";flex:1;height:2px;background:var(--g);opacity:.22;border-radius:1px}
  details.inote{margin:2px 2px 10px}
  details.inote summary{cursor:pointer;color:var(--muted);font-size:12px;font-style:italic;user-select:none;width:fit-content}
  details.inote summary:hover{color:var(--gd)}
  details.inote[open] summary{margin-bottom:4px}
  .covtbl tr.grp>td{background:#f4f8f5;font-weight:700;color:var(--gd)}
  .covtbl tr.grp.prov>td{background:#fbfdfb;font-weight:600}
  .covtbl .sub2{color:var(--muted);font-weight:400;font-size:12px}
  .covtbl .caret{display:inline-block;width:16px;color:var(--g);font-weight:700}
  .covtbl td.ind1{padding-left:30px}
  .covtbl td.ind2{padding-left:48px;font-weight:400;color:var(--ink)}
  .covsearch{font:13px system-ui;padding:6px 10px;border:1px solid var(--line);border-radius:8px;background:#fff;min-width:280px;margin:0 0 8px;display:block}
  .qtiles{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:8px}
  .qtile{background:var(--card);border:1px solid var(--line);border-top:3px solid var(--g);border-radius:12px;padding:12px 14px;cursor:pointer;box-shadow:0 1px 2px rgba(0,0,0,.04)}
  .qtile .num{font-size:26px;font-weight:800;line-height:1;color:var(--g)}
  .qtile.warn{border-top-color:var(--gold)}.qtile.warn .num{color:#b7860b}
  .qtile.bad{border-top-color:var(--red)}.qtile.bad .num{color:var(--red)}
  .qtile .lbl{color:var(--muted);font-size:11.5px;font-weight:600;margin-top:5px;text-transform:uppercase;letter-spacing:.03em}
  .qtile.sel{outline:2px solid var(--g)}
  /* A 7-column coverage table is wider than a tablet. It used to widen the whole
     document, so the page itself scrolled sideways and the headings drifted off
     screen. Now each wide table scrolls within its own panel. Restoring display:table
     on the tbody keeps column widths computing as a table, so the header row stays
     aligned with the body (verified in-browser: identical cell widths). */
  .covtbl{display:block;overflow-x:auto;max-width:100%}
  .covtbl>tbody{display:table;width:100%;min-width:720px}
  /* ---- BI canvas (2026-07-29) ---------------------------------------------
     Composition, not paint. The page used to be one 1240px column of full-width
     sections, which reads as a document you scroll rather than a dashboard you
     take in. Wider canvas, consistent panel cards, panels sharing rows, sticky
     controls, tighter type. Scoped to this page: .canvas and the neutral tokens
     are overridden here rather than in portal.css, which the map and the data
     room also load. */
  .canvas{max-width:1600px!important;padding:20px 24px 56px!important}
  body{background:#eef1f5}
  main{font-size:14px}
  /* Panels become cards so the eye reads regions of a canvas, not a continuous page. */
  #coverage,#productivity,#quality,#sections{background:#fff;border:1px solid #d8dee7;
    border-radius:6px;padding:14px 16px;margin-bottom:16px;box-shadow:0 1px 3px rgba(16,32,64,.06)}
  #coverage>h2:first-child,#productivity>h2:first-child{margin-top:0}
  /* Two panels per row where both fit; one per row where they do not. No fixed
     column count, so this degrades to the old stack on a narrow screen instead
     of squashing a table nobody can then read. */
  .bigrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(620px,1fr));
    gap:16px;align-items:start;margin-bottom:16px}
  .bigrid>*{min-width:0;margin-bottom:0}
  .band{margin:22px 2px 10px;padding-bottom:6px;font-size:11.5px;letter-spacing:.13em;
    border-bottom:1px solid #d8dee7;color:#33455a}
  .band:first-of-type{margin-top:10px}
  .chart{border-radius:6px;box-shadow:0 1px 3px rgba(16,32,64,.06);border-color:#d8dee7;
    padding:12px 14px}
  /* KPI accent moves from the top edge to the left edge - the Power BI card idiom,
     and it survives the tighter vertical rhythm better than a top rule. */
  .kpi{border-radius:6px;border-top:1px solid #d8dee7;border-left:4px solid var(--g);
    padding:11px 13px;box-shadow:0 1px 3px rgba(16,32,64,.06)}
  .kpi.ok{border-left-color:#0f7b46}
  .kpi.warn{border-left-color:#c98a12}
  .kpi.bad{border-left-color:#c62828}
  .kpi .num{font-size:26px}.kpi .lbl{font-size:10.5px}.kpi .cmp{font-size:10.5px}
  .card{border-radius:6px;box-shadow:0 1px 3px rgba(16,32,64,.06)}
  .card .num{font-size:26px}
  .qtile{border-radius:6px;padding:10px 12px}
  .universe{font-size:11.5px;margin:-2px 2px 10px}
  /* A BI canvas keeps its controls reachable; below the bell's z-index so the
     alert panel still opens over it. */
  .filters{border-radius:6px;border-color:#d8dee7;position:sticky;top:0;z-index:30;
    box-shadow:0 2px 10px rgba(16,32,64,.10)}
  @media(max-width:1000px){.filters{position:static;box-shadow:none}}
  /* One dense KPI header band instead of two stacked rows: Progress | Needs
     attention | By instrument, 4-2-4 tiles across the canvas. This is the part
     that makes the top of the page read as a dashboard rather than a document. */
  .kpiwrap{grid-template-columns:2fr 1fr 2fr}
  .kpigrp.insts .cards{grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:0}
  .kpigrp.insts .card{padding:11px 13px;cursor:pointer}
  .kpigrp.insts .card .num{font-size:22px}
  .kpigrp.insts .card .lbl{font-size:11px;font-weight:600;margin-top:4px}
  .kpigrp.insts .card .sub{font-size:10.5px}
  /* The leaderboard grows with the team - 6 enumerators in the pretest, dozens at
     rollout. Bound it so it stays a panel on the canvas instead of becoming the
     page, exactly like the case list below. */
  #productivity .covtbl{max-height:440px;overflow:auto}
  /* Tables fill their panel. Auto-width left the case list floating short of the
     card edge, which reads as a rendering fault on a wide canvas. */
  #caselist table{width:100%}
  #coverage .covtbl>tbody,#productivity .covtbl>tbody{width:100%}
  #productivity .covtbl thead th,#productivity .covtbl tr:first-child th{position:sticky;top:0;z-index:2;
    background:#f4f6f9;box-shadow:inset 0 -1px 0 #d8dee7}
  @media(max-width:1360px){.kpiwrap{grid-template-columns:1fr}
    .kpigrp.insts{border-top:1px solid #d8dee7;padding-top:12px}}
  .qmore{color:var(--muted);font-size:12px;font-style:italic;margin:4px 2px 10px}
  h2.sechead{display:flex;align-items:center;gap:8px;cursor:pointer;user-select:none}
  h2.sechead .caret{color:var(--g)}
  h2.sechead .cnt{color:var(--muted);font-size:12.5px;font-weight:400}
  h2.sechead .f2s{font-size:12px;color:var(--muted);font-weight:400;margin-left:auto}
  h2.sechead .f2s.badapi{color:var(--red);font-weight:700}
  .card{cursor:pointer}
  .card.sel{outline:2px solid var(--g)}
  @media(max-width:820px){.qtiles{grid-template-columns:repeat(2,1fr)}}
  .clbar{margin:2px 2px 8px;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
  .clbar input{font:13px system-ui;padding:7px 10px;border:1px solid var(--line);border-radius:8px;background:#fff;width:360px;max-width:100%}
  .clbar .dlink{color:var(--g);font-weight:600;font-size:13px;text-decoration:none;white-space:nowrap}
  .clbar .dlink:hover{text-decoration:underline}
  .covtbl td.mono{font-family:ui-monospace,'Cascadia Mono',Consolas,monospace;font-size:12px;white-space:nowrap}
  .covtbl a.rlink{color:var(--g);font-weight:600;text-decoration:none;white-space:nowrap}
  .covtbl a.rlink:hover{text-decoration:underline}
  /* Secondary link: present but deliberately quiet — most readers want the console
     viewer; only someone editing a case needs CSWeb. */
  .covtbl a.rlink2{margin-left:9px;font-size:11.5px;font-weight:600;color:var(--muted);text-decoration:none;white-space:nowrap}
  .covtbl a.rlink2:hover{color:var(--g);text-decoration:underline}
  .covtbl .instchip{display:inline-block;font-size:11px;font-weight:700;color:#006b3f;background:#e7f3ec;border-radius:5px;padding:0 6px}
  @media(max-width:820px){.kpis,.kpigrp .kpis{grid-template-columns:repeat(2,1fr)}.cards{grid-template-columns:1fr}.covbar{width:90px}}
</style>
</head>
<body>
<header><h1>UHC Survey Year 2 — Sync Dashboard</h1><div class="s">Fieldwork monitoring for the ASPSI × DOH UHC survey · F1 / F3 / F4 (CSEntry tablets) · F2 (Healthcare-Worker PWA)</div></header>
<!-- The old "Site sections" second nav died with the shared-shell migration:
     confirmed absent from the deployed page 2026-08-09. The sidebar is the
     one navigation; a second one contradicting it was the defect. -->
<main>
  <details class="howto"><summary>New here? What this page is and how to use it</summary>
    <div class="body">
      <p><b>What this is.</b> A read-only monitoring view of survey data as it arrives from the field.
      Tablets (F1/F3/F4) and the healthcare-worker web form (F2) sync into CSWeb; this page re-reads that
      database <b>every 2 minutes</b> and shows where collection stands. Nothing here changes any data.</p>
      <p><b>Who it's for.</b> ASPSI and DOH staff supervising fieldwork, and analysts pulling data.
      For step-by-step instructions on collecting or syncing, use <a href="/help.html">Help &amp; guides</a>.</p>
      <p><b>How to read it.</b> The filter bar at the top (instrument, region, supervisor, enumerator,
      status, visit dates) drives <i>every</i> section below it — set a filter once and the whole page follows.
      Coverage-vs-plan deliberately ignores the enumerator filter, because the plan assigns facilities, not people.</p>
      <ul>
        <li><b>Status now</b> — headline counts: cases in, completed vs partial, visited today, missing GPS.</li>
        <li><b>Progress vs plan</b> — submissions over time, and coverage against the assignment plan (region → province → facility), plus enumerator productivity.</li>
        <li><b>Data quality</b> — things worth acting on today: no-GPS cases, partials older than 2 days, cases outside the plan, and live sync alerts.</li>
        <li><b>Instrument detail</b> — per-instrument charts (collapsed; click a heading to expand).</li>
        <li><b>Case drill-down</b> — the case list. Search it, sort it, export the filtered view to CSV, or open any case's full responses — every instrument opens here on this console, on the same login as this page.</li>
        <li><b>Downloads</b> — get the data out: CSPro sync files, CSV/SPSS/Stata/R exports, the CSPro applications, and the codebook.</li>
      </ul>
      <p><b>Definitions that trip people up.</b> "Today" is Manila time. F2 is self-administered, so it never
      counts as no-GPS and is always recorded as completed. Case counts here follow the filters, so they can
      differ from CSWeb's raw Data tab.</p>
      <div class="jump"><a href="#b-status">Status now</a><a href="#b-progress">Progress vs plan</a><a href="#b-quality">Data quality</a><a href="#b-detail">Instrument detail</a><a href="#b-cases">Case drill-down</a><a href="#b-downloads">Downloads</a></div>
    </div>
  </details>
  <div class="filters">
    <div class="f"><label for="fInst">Instrument</label><select id="fInst"></select></div>
    <div class="f"><label for="fRegion">Region</label><select id="fRegion"></select></div>
    <div class="f"><label for="fSup">Field supervisor</label><select id="fSup"></select></div>
    <div class="f"><label for="fEnum">Enumerator</label><select id="fEnum"></select></div>
    <div class="f"><label for="fStatus">Status</label><select id="fStatus"></select></div>
    <div class="f"><label for="fPhase">Phase</label><select id="fPhase"></select></div>
    <div class="f"><label for="fAct">Activity</label><select id="fAct"></select></div>
    <div class="f"><label for="fFrom">Visit from</label><input type="date" id="fFrom" /></div>
    <div class="f"><label for="fTo">Visit to</label><input type="date" id="fTo" /></div>
    <button class="reset" id="fReset" type="button">Reset</button>
  </div>
  <div id="enumChip" class="enumchip" hidden></div>
  <h2 class="band" id="b-status">Status now</h2>
  <p class="universe">Every synced case matching the filters above. F2 is self-administered, so it is always recorded as Completed and never counted as missing a GPS fix.</p>
  <div class="kpiwrap">
    <section class="kpigrp" aria-labelledby="grpProg">
      <h3 class="grph" id="grpProg">Progress</h3>
      <div class="kpis">
        <div class="kpi"><div class="num" id="kTotal">0</div><div class="lbl">Cases (filtered)</div><div class="cmp" id="cTotal"></div></div>
        <div class="kpi ok"><div class="num" id="kCompleted">0</div><div class="lbl">Completed</div><div class="cmp" id="cCompleted"></div></div>
        <div class="kpi warn"><div class="num" id="kPartial">0</div><div class="lbl">Partial</div><div class="cmp" id="cPartial"></div></div>
        <div class="kpi"><div class="num" id="kToday">0</div><div class="lbl">Visited today</div><div class="cmp" id="cToday"></div></div>
      </div>
    </section>
    <section class="kpigrp attn" aria-labelledby="grpAttn">
      <h3 class="grph" id="grpAttn">&#9888; Needs attention</h3>
      <div class="kpis">
        <div class="kpi warn"><div class="num" id="kRepl">0</div><div class="lbl">Replacements</div><div class="cmp" id="cRepl"></div></div>
        <div class="kpi bad"><div class="num" id="kNogps">0</div><div class="lbl">No GPS fix</div><div class="cmp" id="cNogps"></div></div>
      </div>
    </section>
    <section class="kpigrp insts" aria-labelledby="grpInst">
      <h3 class="grph" id="grpInst">By instrument</h3>
      <div class="cards" id="totals"></div>
    </section>
  </div>
  <div class="freshness">Data as of <b id="fresh"></b> · auto-refreshes ~every 2 min · "today" = <span id="todayLbl"></span> (Manila)</div>
  <h2 class="band" id="b-progress">Progress vs plan</h2>
  <p class="universe">Submissions counted by visit date. Coverage is measured against the assignment plan, which allocates facilities to places rather than to people &mdash; so it answers &ldquo;are these facilities covered?&rdquo;, not &ldquo;how much did this person do?&rdquo;</p>
  <div class="chart wide"><h3>New submissions per day</h3><p class="sub">Bars are cases received that day; the line is the trailing 7-day average. Both use the same scale, so a flat or falling week is visible.</p><div class="canvas-wrap"><canvas id="trend" role="img" aria-label="Bar chart of new submissions per day with a trailing seven-day average line. The figures are listed in the case list table below."></canvas></div></div>
  <div id="coverage"></div>
  <div id="productivity"></div>
  <h2 class="band" id="b-quality">Data quality</h2>
  <p class="universe">Exceptions among the filtered cases, ignoring the Status filter so a partial case can still be flagged. F2 is excluded from GPS checks by design.</p>
  <div id="quality"></div>
  <h2 class="band" id="b-detail">Instrument detail</h2>
  <div class="note">Counts exclude deleted cases. Filters recompute every tile in your browser. Empty/blank categories reflect minimal test cases in the current data — they populate as real fieldwork syncs. Per-case drill-down: the <b>Case list</b> at the bottom — every row opens its full responses here on this console.</div>
  <div id="sections"></div>
  <h2 class="band" id="b-cases">Case drill-down</h2>
  <p class="universe">One row per synced case in the current view. This is record-level operational data, not weighted survey estimates.</p>
  <h3>Case list</h3>
  <div class="cov-note">Every synced case in the current view — honours every filter above. Every row opens its <b>full question-by-question detail on this console</b>, on the same login as this page — no second sign-in, for any instrument. F1/F3/F4 also carry a quieter <b>CSWeb</b> link, because CSWeb is still where a case is edited; this viewer is read-only. Coded answers show the stored code with its codebook label alongside, so this page always agrees with the CSV/SPSS/Stata/R exports. QN is shown exactly as stored. <b>Export CSV</b> downloads the current view (every metadata column, including ones this table hides). The <b>Responses data room</b> holds the full answer spreadsheets — one wide CSV per instrument plus roster CSVs, and the labeled SPSS/Stata/R extracts (same login as this page).</div>
  <div class="clbar"><input type="search" id="clSearch" placeholder="Search QN, facility, enumerator, login&hellip;" /><button class="reset" id="clExport" type="button">Export CSV</button><a class="dlink" href="/docs/data/" target="_blank" rel="noopener">Responses data room &#8599;</a></div>
  <div class="cov-sum" id="clSum"></div>
  <div id="caselist"></div>
  <p class="cl-hint" id="clHint">The list scrolls within this panel and reflects every filter above. Use Download CSV for the full set.</p>
__DOWNLOADS__
</main>
<footer>Generated <span id="gen"></span> · source: F1/F3/F4 breakout DBs via <code>csweb_reports</code> + F2 <code>csweb_f2</code> mirror · see also the <a href="/docs/map.html" style="color:#006b3f">Map Report</a>.</footer>
<script type="application/json" id="dash-data">__PAYLOAD__</script>
<script>
const P = JSON.parse(document.getElementById('dash-data').textContent);
document.getElementById('gen').textContent = P.generated;
document.getElementById('fresh').textContent = P.generated;
document.getElementById('todayLbl').textContent = P.today ? (P.today.slice(0,4)+'-'+P.today.slice(4,6)+'-'+P.today.slice(6,8)) : '—';
// Reporting rule (audit F1/F2): a percentage on a tiny base is noise with a
// decimal point, and at n=1 it describes one identifiable person. Below this
// base the rate is emitted as null - which the renderers already show as an
// em dash - so the underlying count stays visible while the rate is withheld.
const MIN_BASE = 25;
const NAMES = {f1:'Facility Head', f3:'Patient', f4:'Household', f2:'Healthcare Worker'};
// Audit F9: the old ramp leaned on hues that deuteranopes cannot separate. This is the
// Okabe-Ito colour-blind-safe qualitative set, with the ASPSI green kept in first place so
// the brand still leads. Categories are also always labelled, so hue is never the only cue.
const PAL=['#006b3f','#E69F00','#56B4E9','#CC79A7','#0072B2','#D55E00','#009E73','#7F3C8D','#8C8C8C','#B26F16','#3B7EA1','#A15C5C'];
// instrument prefixes, in section order (F1, F3, F4, F2) — derived once so every
// per-instrument loop below (cards, KPIs, coverage) stays in sync with the sections.
const INSTS = P.spec.map(s=>s.prefix);

// --- filter controls ---
const instSel=document.getElementById('fInst'), regSel=document.getElementById('fRegion');
const phaseSel=document.getElementById('fPhase');
const actSel=document.getElementById('fAct');
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
phaseSel.add(new Option('All phases','ALL'));
actSel.add(new Option('All activities','ALL'));
(()=>{const have=new Set(); INSTS.forEach(k=>(P.data[k]||[]).forEach(r=>have.add(r.activity||'unassigned')));
 (P.actreg||[]).filter(a=>have.has(a.id)).forEach(a=>actSel.add(new Option(a.label,a.id)));
 if(have.has('unassigned'))actSel.add(new Option('Unassigned','unassigned'));})();
(()=>{const ps=new Set(); INSTS.forEach(k=>(P.data[k]||[]).forEach(r=>ps.add(r.phase||'unphased')));
 ['pretest','training','survey','unphased'].filter(x=>ps.has(x)).forEach(x=>phaseSel.add(new Option(x[0].toUpperCase()+x.slice(1),x)));})();
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
  d.title='Click to filter the dashboard to this instrument (click again to clear)';
  d.onclick=()=>{ instSel.value=(instSel.value===k?'ALL':k); render(); };
  tc.appendChild(d); cardNum[k]=num; d.dataset.k=k;
});
const sec=document.getElementById('sections');
const charts={}; // id -> Chart
P.spec.forEach(s=>{
  const wrapSec=document.createElement('div'); wrapSec.dataset.prefix=s.prefix;
  // collapsed-by-default section (2026-07-17 IA redesign) — charts build lazily on first
  // expand, because Chart.js cannot size itself on a hidden canvas. The F2 health note is
  // summarised in the header so an outage is never hidden behind a collapsed section.
  s._open=false;
  const h=document.createElement('h2'); h.className='sechead';
  const car=document.createElement('span'); car.className='caret'; car.textContent='▸'; h.appendChild(car);
  h.appendChild(document.createTextNode(s.title+' '));
  const cnt=document.createElement('span'); cnt.className='cnt'; h.appendChild(cnt);
  s._cnt=cnt; s._car=car;
  if(s.prefix==='f2' && P.f2meta){
    const f2s=document.createElement('span'); f2s.className='f2s';
    if(P.f2meta.err){ f2s.textContent='F2 read FAILED — see note inside'; f2s.classList.add('badapi'); }
    else{
      f2s.textContent=(P.f2meta.n||0)+' submission'+(P.f2meta.n===1?'':'s')
        +(P.f2meta.last?' · last '+P.f2meta.last.slice(0,4)+'-'+P.f2meta.last.slice(4,6)+'-'+P.f2meta.last.slice(6,8):'');
      if(P.f2meta.api===false){ f2s.textContent+=' · f2-api DOWN'; f2s.classList.add('badapi'); }
    }
    h.appendChild(f2s);
  }
  h.title='Click to expand / collapse';
  h.onclick=()=>{ s._open=!s._open; render(); };
  wrapSec.appendChild(h);
  const body=document.createElement('div'); s._body=body; body.style.display='none';
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
    body.appendChild(fn);
  }
  const grid=document.createElement('div'); grid.className='grid'; body.appendChild(grid);
  s.charts.forEach(c=>{
    const w=document.createElement('div'); w.className='chart';
    const t=document.createElement('h3'); t.textContent=c.title; w.appendChild(t);
    const cw=document.createElement('div'); cw.className='canvas-wrap';
    const cv=document.createElement('canvas'); cv.id=s.prefix+'__'+c.field; cw.appendChild(cv);
    w.appendChild(cw); grid.appendChild(w);
  });
  wrapSec.appendChild(body);
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
function setCmp(id,txt){ const e=document.getElementById(id); if(e) e.textContent=txt; }
function renderKpis(passOf){
  let tot=0,comp=0,part=0,today=0,nogps=0,repl=0,gpsElig=0,last7=0;
  visInsts(instSel.value).forEach(k=>{
    (P.data[k]||[]).forEach(r=>{ if(!passOf(r))return;
      tot++; if(r.status==='Completed')comp++; else if(r.status==='Partial')part++;
      if(P.today && r.date===P.today)today++;
      if(k!=='f2') gpsElig++;   // F2 is self-administered — it captures no GPS by design,
                                // so counting it in the denominator would invent a problem
      if(r.gps==='0'||r.gps===0)nogps++;
      if(r.repl==='1')repl++;   // BREAKOFF 5/6/7 — sampled unit never interviewed, substitute drawn
      const d=r.date;
      if(P.today && d && /^\d{8}$/.test(d) && d!=='00000000'){
        const age=daysBetween(d,P.today); if(age>=0&&age<7) last7++;
      }
    });
  });
  kTotal.textContent=tot; kCompleted.textContent=comp; kPartial.textContent=part;
  kToday.textContent=today; kNogps.textContent=nogps; kRepl.textContent=repl;
  // Audit F4: a bare count cannot answer "is this good?", which is the only question a
  // KPI exists to answer. Each tile now carries a reference point. Every comparator that
  // is a rate shows its base and obeys MIN_BASE, so none of them can print a confident
  // percentage on a base too small to carry one.
  const rate=(n,d,noun)=>d>=MIN_BASE ? (Math.round(100*n/d)+'% of '+d+(noun?' '+noun:''))
                                     : ('base too small (n='+d+')');
  setCmp('cTotal', last7+' in the last 7 days');
  setCmp('cCompleted', rate(comp,tot,'cases'));
  setCmp('cPartial', rate(part,tot,'cases'));
  setCmp('cToday', 'vs '+(Math.round(10*last7/7)/10)+'/day over 7 days');
  setCmp('cRepl', rate(repl,tot,'cases'));
  setCmp('cNogps', rate(nogps,gpsElig,'GPS-eligible'));
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
  // Reporting rule (audit F1/F2): a percentage on a tiny base is noise with a
  // decimal point, and at n=1 it describes one identifiable person. Below this
  // base we emit null, which every renderer already shows as an em dash.
  const roll7=daily.map((_,i)=>{const w=daily.slice(Math.max(0,i-6),i+1);
    return Math.round(10*w.reduce((a,b)=>a+(b||0),0)/w.length)/10;});
  charts.trend=new Chart(cv,{data:{labels,datasets:[
      {type:'bar',label:'New per day',data:daily,backgroundColor:'#e5b23b',order:2,yAxisID:'y'},
      // Audit F3: the cumulative series lived on a second y-axis, so its slope was
      // an artefact of scaling AND it only ever rose - the chart read as growth on
      // days when nothing arrived. Replaced with a 7-day mean on the SAME axis,
      // which is comparable to the bars and can fall.
      {type:'line',label:'7-day average',data:roll7,borderColor:'#006b3f',backgroundColor:'#006b3f',tension:.25,pointRadius:0,borderWidth:2,order:1,yAxisID:'y'}]},
    options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
      plugins:{legend:{position:'bottom',labels:{boxWidth:12,font:{size:11}}}},
      scales:{y:{position:'left',beginAtZero:true,ticks:{precision:0},title:{display:true,text:'new/day'}},
              // (no second axis - audit F3 removed the cumulative series that used it;
              //  leaving the scale declared risks it reappearing on a future edit)
              x:{ticks:{font:{size:10},maxRotation:60,minRotation:0}}}}});
}
// --- Phase 2: coverage vs. target ---
const provByCode={};   // code9 -> province from cases (fallback area when targets aren't masterlist-enriched)
INSTS.forEach(k=>(P.data[k]||[]).forEach(r=>{ if(r.code9 && r.province && r.province!=='(unknown)' && !provByCode[r.code9]) provByCode[r.code9]=r.province; }));
const covSort={};      // inst -> {col,dir}
// accordion state — lives OUTSIDE render() so filter changes and column sorts never
// collapse what the reader opened. An explicit click always beats the auto-default
// (rows with any landed case start open); a live search force-opens every match.
const covUser=new Map();   // 'inst|region' / 'inst|region|province' -> explicit open/closed
const covSearch={};        // inst -> facility search string
let covFocus=null;         // instrument whose search box must regain focus after a re-render
function esc(s){const d=document.createElement('div'); d.textContent=(s==null?'':s); return d.innerHTML;}
// Audit F9: green/amber/red is the classic red-green trap. Vermillion replaces the red -
// it separates from green for the ~8% of men with red-green deficiency. The percentage is
// printed beside every bar, so the number, not the hue, carries the meaning.
function covColor(pct){ return pct>=80?'#006b3f':(pct>=40?'#E69F00':'#D55E00'); }
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
  // Audit F6: this panel ignores the enumerator filter on purpose. Explaining that only in
  // the page's general copy means a reader who filters to one person sees these numbers
  // not move and concludes the panel is broken. Say it here, and only when it applies.
  if(enumSel.value!=='ALL'){
    const b=document.createElement('p'); b.className='scopebadge';
    b.textContent='Not filtered by enumerator. The plan assigns facilities to places, not to people, so these figures cover every enumerator working these facilities.';
    cov.appendChild(b);
  }
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
  const noteWrap=document.createElement('details'); noteWrap.className='inote';
  noteWrap.innerHTML='<summary>&#9432; how to read this section</summary>';
  const note=document.createElement('div'); note.className='cov-note';
  note.textContent='Landed = Completed cases in the current view (instrument · region · visit-date). Expected = the assignment plan’s target. The Status filter does not apply here. Region and province rows roll their facilities up — click a row to open it; rows with any landed case start open. The search finds facilities by name or 9-digit code.';
  noteWrap.appendChild(note); cov.appendChild(noteWrap);
  visible.forEach(k=>{
    const tgt=T[k], comp={}; let untarget=0;
    (P.data[k]||[]).forEach(r=>{ if(r.status!=='Completed'||!pass(r,true,true)) return; if(tgt[r.code9]) comp[r.code9]=(comp[r.code9]||0)+1; else untarget++; });
    const facs=Object.keys(tgt).map(code=>{
      const t=tgt[code], exp=+t.target||0, landed=comp[code]||0;
      return {code, name:t.name||('(code '+code+')'), region:t.region||'(region TBD)',
              area:t.province||provByCode[code]||'(area TBD)', exp, landed,
              pct: exp>=MIN_BASE?Math.round(100*landed/exp):null, base: exp, short: Math.max(0,exp-landed)};
    });
    const provAll=new Set(facs.map(f=>f.area)), provAct=new Set(facs.filter(f=>f.landed>0).map(f=>f.area));
    const sumExp=facs.reduce((s,r)=>s+r.exp,0), sumLanded=facs.reduce((s,r)=>s+r.landed,0);
    const opct=sumExp>=MIN_BASE?Math.round(100*sumLanded/sumExp):null;
    const title=document.createElement('div'); title.className='cov-inst'; title.textContent=k.toUpperCase()+' · '+NAMES[k]; cov.appendChild(title);
    const sum=document.createElement('div'); sum.className='cov-sum';
    // opct is null whenever the plan is below MIN_BASE. Interpolating it produced a
    // literal "(null%)" on the page; say what the suppression means instead.
    const opctTxt=(opct==null)?'rate withheld \u2014 plan under '+MIN_BASE:opct+'%';
    sum.innerHTML='<b>'+sumLanded+'</b> / '+sumExp+' completed ('+opctTxt+') across '+facs.length+' facilit'+(facs.length===1?'y':'ies')
      +(provAll.size>1?' in '+provAll.size+' provinces (<b>'+provAct.size+'</b> started)':'')
      +(untarget?' · <b>'+untarget+'</b> completed at facilities not in the plan':'');
    cov.appendChild(sum);
    // facility search — filters the accordion and force-opens whatever matches
    const si=document.createElement('input'); si.type='search'; si.className='covsearch';
    si.placeholder='Search facility name or 9-digit code…'; si.value=covSearch[k]||'';
    si.oninput=()=>{ covSearch[k]=si.value; covFocus=k; render(); };
    cov.appendChild(si);
    const q=(covSearch[k]||'').trim().toLowerCase();
    const shown=q?facs.filter(f=>f.name.toLowerCase().indexOf(q)>=0||f.code.indexOf(q)>=0):facs;
    // group facilities region -> province, aggregating on the way. Grouping keys come ONLY
    // from the targets' own strings — never joined to case-row region names, which are
    // survey-internal and word-reordered (the known name-mismatch trap). Cases contribute
    // to landed exclusively via code9, which is already the join key.
    const regs=new Map();
    shown.forEach(f=>{
      let R=regs.get(f.region); if(!R){R={name:f.region,provs:new Map(),exp:0,landed:0,fac:0}; regs.set(f.region,R);}
      let V=R.provs.get(f.area); if(!V){V={name:f.area,rows:[],exp:0,landed:0}; R.provs.set(f.area,V);}
      V.rows.push(f); V.exp+=f.exp; V.landed+=f.landed; R.exp+=f.exp; R.landed+=f.landed; R.fac++;
    });
    const fin=o=>{o.pct=o.exp>=MIN_BASE?Math.round(100*o.landed/o.exp):null; o.base=o.exp; o.short=Math.max(0,o.exp-o.landed); return o;};
    const st=covSort[k]||{col:'pct',dir:-1};
    const val=(o,c)=> (c==='name') ? (o.name||'').toLowerCase()
                    : (c==='area') ? ((o.area!==undefined?o.area:o.name)||'').toLowerCase()
                    : (o[c]==null?-1:o[c]);
    const cmp=(a,b)=>{const x=val(a,st.col),y=val(b,st.col); const d=(x<y?-1:x>y?1:0)*st.dir;
      if(d) return d; const nx=(a.name||'').toLowerCase(), ny=(b.name||'').toLowerCase(); return nx<ny?-1:nx>ny?1:0;};
    const isOpen=key=>{ if(q) return true; if(covUser.has(key)) return covUser.get(key); return null; };
    const tbl=document.createElement('table'); tbl.className='covtbl';
    const cols=[['name','Region / Province / Facility',''],['area','Area',''],['exp','Expected','n'],['landed','Landed','n'],['pct','%','n'],['short','Shortfall','n'],['bar','Progress','s']];
    const thead=document.createElement('tr');
    cols.forEach(([c,lbl,cl])=>{ const th=document.createElement('th'); if(cl)th.className=cl;
      th.textContent=lbl+(st.col===c?(st.dir>0?' ▲':' ▼'):'');
      if(c!=='bar'){th.onclick=()=>{covSort[k]={col:c,dir:(st.col===c?-st.dir:1)}; render();};}
      thead.appendChild(th); });
    tbl.appendChild(thead);
    const numCells=o=>{
      const pct=o.pct==null?'—':o.pct+'%', col=o.pct==null?'#5b6b63':covColor(o.pct);
      return '<td class="n">'+o.exp+'</td><td class="n">'+o.landed+'</td>'
        +'<td class="n pct" style="color:'+col+'">'+pct+'</td>'
        +'<td class="n short'+(o.short?'':' zero')+'">'+o.short+'</td>'
        +'<td class="s"><div class="covbar"><span style="width:'+Math.min(100,o.pct||0)+'%;background:'+col+'"></span></div></td>';
    };
    [...regs.values()].map(fin).sort(cmp).forEach(R=>{
      const rk=k+'|'+R.name, ro=isOpen(rk), rOpen=(ro===null)?(R.landed>0):ro;
      const tr=document.createElement('tr'); tr.className='grp clickable';
      tr.innerHTML='<td><span class="caret">'+(rOpen?'▾':'▸')+'</span>'+esc(R.name)+'</td>'
        +'<td class="sub2">'+R.provs.size+' province'+(R.provs.size===1?'':'s')+' · '+R.fac+' facilit'+(R.fac===1?'y':'ies')+'</td>'+numCells(R);
      tr.onclick=()=>{ covUser.set(rk,!rOpen); render(); };
      tbl.appendChild(tr);
      if(!rOpen) return;
      [...R.provs.values()].map(fin).sort(cmp).forEach(V=>{
        const pk=rk+'|'+V.name, po=isOpen(pk), pOpen=(po===null)?(V.landed>0):po;
        const tp=document.createElement('tr'); tp.className='grp prov clickable';
        tp.innerHTML='<td class="ind1"><span class="caret">'+(pOpen?'▾':'▸')+'</span>'+esc(V.name)+'</td>'
          +'<td class="sub2">'+V.rows.length+' facilit'+(V.rows.length===1?'y':'ies')+'</td>'+numCells(V);
        tp.onclick=()=>{ covUser.set(pk,!pOpen); render(); };
        tbl.appendChild(tp);
        if(!pOpen) return;
        V.rows.slice().sort(cmp).forEach(r=>{ const tf=document.createElement('tr');
          tf.innerHTML='<td class="ind2">'+esc(r.name)+'</td><td>'+esc(r.area)+'</td>'+numCells(r);
          tbl.appendChild(tf); });
      });
    });
    cov.appendChild(tbl);
    if(covFocus===k){ si.focus(); const n=si.value.length; try{si.setSelectionRange(n,n);}catch(e){} covFocus=null; }
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
  // the Team band label is emitted HERE (not in the static skeleton) so it vanishes
  // together with the panel when no enumerator is in view — no orphaned heading.
  const band=document.createElement('div'); band.className='band'; band.textContent='Team'; el.appendChild(band);
  const h=document.createElement('h2'); h.textContent='Enumerator productivity'; el.appendChild(h);
  const noteWrap=document.createElement('details'); noteWrap.className='inote';
  noteWrap.innerHTML='<summary>&#9432; how to read this table</summary>';
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
  noteWrap.appendChild(note); el.appendChild(noteWrap);
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
    const replPct = o.cases>=MIN_BASE ? Math.round(100*o.repl/o.cases) : null;
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
// --- Data quality panel (2026-07-17 IA redesign) ---
// Gives the bell's transient signals an on-page home + itemises what the KPIs only count.
// Honours every filter EXCEPT Status (a quality problem must not hide because the status
// filter is set to Completed). F2 is excluded from the GPS tile by design: it is
// self-administered and its gps flag is a deliberate constant, never a real fix.
const QMAX=40;                 // list cap — beyond this it's a data pull, not a glance
let qOpen=null;                // which tile's list is expanded
let qAlertsStr=null;           // latest sync-feed alerts as JSON string (null = not loaded yet)
let lastPass=null;             // the current render()'s pass fn, for feed-driven re-renders
function fmtYmd(d){return (d&&/^\d{8}$/.test(d)&&d!=='00000000')?d.slice(0,4)+'-'+d.slice(4,6)+'-'+d.slice(6,8):'—';}
function enumLbl(r){
  const nm=(r.enumerator&&r.enumerator!=='(unassigned)')?r.enumerator:'';
  const lg=(r.syncuser&&r.syncuser!=='(unknown)')?r.syncuser:'';
  return nm&&lg?nm+' · '+lg:(nm||lg||'—');
}
function renderQuality(pass){
  const el=document.getElementById('quality'); if(!el) return; el.innerHTML='';
  const nogps=[],stale=[],oop=[];
  visInsts(instSel.value).forEach(k=>{
    const tgt=(P.targets||{})[k], hasPlan=!!(tgt&&Object.keys(tgt).length);
    (P.data[k]||[]).forEach(r=>{ if(!pass(r,true)) return;
      if(k!=='f2'&&(r.gps==='0'||r.gps===0)) nogps.push({k,r});
      if(r.status==='Partial'&&P.today&&r.date&&/^\d{8}$/.test(r.date)&&r.date!=='00000000'){
        const age=daysBetween(r.date,P.today); if(age>2) stale.push({k,r,age});
      }
      if(hasPlan&&r.status==='Completed'&&!tgt[r.code9]) oop.push({k,r});
    });
  });
  const alerts=qAlertsStr?JSON.parse(qAlertsStr):[];
  const tiles=[
    {id:'nogps', n:nogps.length, lbl:'No GPS fix', cls:nogps.length?'bad':''},
    {id:'stale', n:stale.length, lbl:'Partials >2 days old', cls:stale.length?'warn':''},
    {id:'oop',   n:oop.length,   lbl:'Completed off-plan', cls:oop.length?'warn':''},
    {id:'alerts',n:alerts.length,lbl:qAlertsStr===null?'Live alerts (loading…)':'Live alerts', cls:alerts.length?'bad':''}
  ];
  const grid=document.createElement('div'); grid.className='qtiles';
  tiles.forEach(t=>{ const d=document.createElement('div'); d.className=('qtile '+t.cls).trim()+(qOpen===t.id?' sel':'');
    d.title='Click to list the cases behind this number';
    d.innerHTML='<div class="num">'+t.n+'</div><div class="lbl">'+t.lbl+'</div>';
    d.onclick=()=>{ qOpen=(qOpen===t.id?null:t.id); renderQuality(pass); };
    grid.appendChild(d); });
  el.appendChild(grid);
  const noteWrap=document.createElement('details'); noteWrap.className='inote';
  noteWrap.innerHTML='<summary>&#9432; how to read this panel</summary>'
    +'<div class="cov-note">Honours the filters above except Status. F2 is self-administered — it captures no GPS by design and is never counted here. '
    +'Live alerts (no-sync warnings, duplicate case keys, off-plan uploads) come from the sync feed, refresh every 20 seconds, ignore the filters, and clear when the underlying issue is resolved — a no-sync warning clears as soon as that enumerator uploads again.</div>';
  el.appendChild(noteWrap);
  if(!qOpen) return;
  const mk=(headCols,rows,rowHtml)=>{
    const t=document.createElement('table'); t.className='covtbl';
    t.innerHTML='<tr>'+headCols.map(c=>'<th scope="col">'+c+'</th>').join('')+'</tr>'
      +rows.slice(0,QMAX).map(rowHtml).join('');
    el.appendChild(t);
    if(rows.length>QMAX){ const m=document.createElement('div'); m.className='qmore';
      m.textContent='…and '+(rows.length-QMAX)+' more — narrow the filters to see them.'; el.appendChild(m); }
  };
  if(qOpen==='nogps') mk(['Instrument','Facility / Area','Enumerator','Visit date'],nogps,
    x=>'<tr><td>'+x.k.toUpperCase()+'</td><td>'+esc(x.r.facility||x.r.province||'—')+'</td><td>'+esc(enumLbl(x.r))+'</td><td>'+fmtYmd(x.r.date)+'</td></tr>');
  if(qOpen==='stale') mk(['Instrument','Facility / Area','Enumerator','Visit date','Age'],stale,
    x=>'<tr><td>'+x.k.toUpperCase()+'</td><td>'+esc(x.r.facility||x.r.province||'—')+'</td><td>'+esc(enumLbl(x.r))+'</td><td>'+fmtYmd(x.r.date)+'</td><td class="n">'+x.age+'d</td></tr>');
  if(qOpen==='oop') mk(['Instrument','Facility code','Area','Enumerator'],oop,
    x=>'<tr><td>'+x.k.toUpperCase()+'</td><td>'+esc(x.r.code9||'—')+'</td><td>'+esc(x.r.province||'—')+'</td><td>'+esc(enumLbl(x.r))+'</td></tr>');
  if(qOpen==='alerts') mk(['Type','Detail'],alerts,
    a=>'<tr><td>'+(a.type==='silence'?'🔔 No sync':a.type==='dup'?'⚠️ Duplicate key':'⚠️ Off-plan')+'</td><td>'
      +(a.type==='silence'
        ? esc(a.name||a.user||'')+' ('+esc(a.user||'')+') · '+(a.hours||0)+' h since the last upload'+(a.level==='high'?' · 3+ days':'')
        : a.type==='dup'
        ? esc(a.key||'')+' · '+esc(a.inst||'')+' · '+(a.n||0)+' cases'
        : 'facility '+esc(a.code9||a.example||'')+' · '+esc(a.inst||'')+' · '+(a.n||0)+' not in plan')
      +((a.users&&a.users.length)?' · '+esc(a.users.join(', ')):'')+'</td></tr>');
}
// The panel does its OWN 20-second fetch of the sync feed (a second tiny GET of a static
// file) so the notification bell's IIFE below stays byte-identical. Re-render only when
// the alert set actually changes — a full render() every 20s would flicker the charts.
function qpoll(){
  fetch('/docs/sync-feed.json?_='+Date.now(),{cache:'no-store'}).then(r=>r.json()).then(d=>{
    const s=JSON.stringify((d&&d.alerts)||[]);
    if(s!==qAlertsStr){ qAlertsStr=s; if(lastPass) renderQuality(lastPass); }
  }).catch(()=>{});
}
qpoll(); setInterval(qpoll,20000);
// --- Case list (drill-down to specific cases, 2026-07-17) ---
// One row per synced case in the current view. Every row can now reach its full
// detail, each in the app that owns it:
//   F1/F3/F4 → the CSWeb Sync Report (?dict=<DICT>&case=<QN> — on-box patch #7
//              auto-opens the View case modal)
//   F2       → the F2 Admin Portal's Data tab, filtered to that submission
// In both cases the answers themselves stay behind that app's own login and never
// enter this page's payload.
const DICT={f1:'FACILITYHEADSURVEY_DICT',f3:'PATIENTSURVEY_DICT',f4:'HOUSEHOLDSURVEY_DICT'};
// F2 lives in its own app (uhc-hcw.asiansocial.org). Its admin SPA routes
// /admin/data/responses/<submission_id> to the single-response detail view — the
// router's exact-match chain ends in a regex fallback that pulls the id straight
// out of location.pathname, so this resolves on a cold load, and _redirects already
// serves index.html for it. Same URL the portal's own UI links to. Separate sign-in
// from this console.
const F2_ADMIN='https://uhc-hcw.asiansocial.org/admin';
// The F2 portal's login screen navigates to a hardcoded /admin/data and discards the
// route you asked for, so signing in there landed you on its list instead of the case
// (Carl, 2026-07-30). The console now renders F2 detail itself from /docs/f2/<id>.json,
// so an F2 case opens on the SAME single login as a CSWeb case. The portal URL is kept
// as the deep-link-out for anyone who wants the owning app.
function f2DetailUrl(r){ return (r && r.sub) ? '/docs/f2-case.html?id='+encodeURIComponent(r.sub) : ''; }
function f2PortalUrl(r){ return (r && r.sub) ? F2_ADMIN+'/data/responses/'+encodeURIComponent(r.sub) : ''; }
const CL_CAP=400;   // render cap — the summary line says when it bites
let caseSort={col:'date',dir:-1};
function areaOf(k,r){ return k==='f1' ? (r.facility||'(unlabeled)') : (r.province||r.region||'—'); }
// shared by the table render AND the CSV export, so both always see the exact same
// slice: instrument/region/supervisor/enumerator/status/date filters + the search box.
// Keeps the raw row as `r` so the export can reach fields the table doesn't show.
function collectCases(pass){
  const q=(document.getElementById('clSearch').value||'').trim().toLowerCase();
  const out=[];
  visInsts(instSel.value).forEach(k=>{
    (P.data[k]||[]).forEach(r=>{ if(!pass(r)) return;
      const en=(r.enumerator&&r.enumerator!=='(unassigned)')?r.enumerator:'';
      const lg=(r.syncuser&&r.syncuser!=='(unknown)')?r.syncuser:'';
      const o={k, r, qn:r.qn||'', area:areaOf(k,r), region:r.region||'', result:r.result||'',
               status:r.status||'', date:r.date||'', en, lg, repl:r.repl==='1'};
      if(q){ const hay=(o.qn+' '+o.area+' '+o.region+' '+o.en+' '+o.lg+' '+o.result).toLowerCase();
             if(hay.indexOf(q)<0) return; }
      out.push(o);
    });
  });
  return out;
}
const isoDate=d=>(d&&/^\d{8}$/.test(d)&&d!=='00000000')?d.slice(0,4)+'-'+d.slice(4,6)+'-'+d.slice(6,8):'';
// export columns: every payload field, labeled; blank where an instrument lacks the field
const CSV_COLS=[
  ['inst',o=>o.k.toUpperCase()], ['questionnaire_number',o=>o.qn],
  ['phase',o=>o.r.phase||'unphased'], ['activity',o=>o.r.activity||'unassigned'],
  ['region',o=>o.r.region||''], ['province',o=>o.r.province||''], ['city',o=>o.r.city||''],
  ['facility',o=>o.k==='f1'?(o.r.facility||''):''],
  ['ownership',o=>o.r.ownership||''], ['service_level',o=>o.r.service_level||''],
  ['patient_type',o=>o.r.patient_type||''], ['sex',o=>o.r.sex||''],
  ['capture_mode',o=>o.r.source||''],
  ['result',o=>o.result], ['status',o=>o.status], ['visit_date',o=>isoDate(o.date)],
  ['enumerator',o=>o.en], ['csweb_login',o=>o.lg],
  ['supervisor',o=>{const s=o.r.supervisor; return (s&&s!=='(unassigned)')?s:'';}],
  ['replacement',o=>o.repl?'1':'0'],
  ['gps_fix',o=>o.r.gps===undefined?'':(o.r.gps==='0'?'0':'1')],
  ['facility_code9',o=>o.r.code9||''],
  // The export is what people reconcile off-platform, so it carries the same
  // full-detail target the table links to - resolved, not reassembled by hand.
  ['f2_submission_id',o=>o.r.sub||''],
  ['full_detail_url',o=>(DICT[o.k]&&o.qn)
      ? '/docs/case.html?inst='+o.k+'&qn='+encodeURIComponent(o.qn)
      : (o.k==='f2'?f2DetailUrl(o.r):'')]];
function csvCell(v){ v=String(v==null?'':v); return /[",\n\r]/.test(v)?'"'+v.replace(/"/g,'""')+'"':v; }
function exportCaseCsv(){
  if(!lastPass) return;
  const rows=collectCases(lastPass);           // the FULL filtered view — not the 400-row render cap
  const lines=[CSV_COLS.map(c=>c[0]).join(',')];
  rows.forEach(o=>lines.push(CSV_COLS.map(c=>csvCell(c[1](o))).join(',')));
  const blob=new Blob(['\ufeff'+lines.join('\r\n')],{type:'text/csv;charset=utf-8'});  // BOM so Excel reads UTF-8 (enye names)
  const a=document.createElement('a');
  a.href=URL.createObjectURL(blob);
  a.download='uhc-cases-'+(P.today||'export')+'-'+rows.length+'.csv';
  document.body.appendChild(a); a.click();
  setTimeout(()=>{URL.revokeObjectURL(a.href); a.remove();},500);
}
function renderCaseList(pass){
  const el=document.getElementById('caselist'); el.innerHTML='';
  const q=(document.getElementById('clSearch').value||'').trim().toLowerCase();
  let rows=collectCases(pass);
  const total=rows.length;
  const st=caseSort;
  const val=(o,c)=> (c==='inst') ? o.k : (c==='qn'||c==='date') ? (o[c]||'') : ((o[c]||'')+'').toLowerCase();
  rows.sort((a,b)=>{const x=val(a,st.col),y=val(b,st.col); return (x<y?-1:x>y?1:0)*st.dir;});
  const capped=rows.length>CL_CAP; if(capped) rows=rows.slice(0,CL_CAP);
  const sum=document.getElementById('clSum');
  sum.innerHTML='<b>'+total+'</b> case'+(total===1?'':'s')+' in view'
    +(capped?' · showing the first '+CL_CAP+' — narrow the filters or search':'')
    +(q?' · search: “'+esc(q)+'”':'');
  if(!total) return;
  const tbl=document.createElement('table'); tbl.className='covtbl';
  const cols=[['inst','Inst',''],['qn','QN',''],['area','Facility / area',''],['result','Result',''],
              ['status','Status',''],['date','Visit',''],['en','Enumerator',''],['lg','CSWeb login',''],['link','Full detail','s']];
  const thead=document.createElement('tr');
  cols.forEach(([c,lbl,cl])=>{ const th=document.createElement('th'); if(cl)th.className=cl;
    th.textContent=lbl+(st.col===c?(st.dir>0?' ▲':' ▼'):'');
    if(c!=='link'){th.onclick=()=>{caseSort={col:c,dir:(st.col===c?-st.dir:1)}; if(lastPass)renderCaseList(lastPass);};}
    thead.appendChild(th); });
  tbl.appendChild(thead);
  const fd=d=>(d&&/^\d{8}$/.test(d)&&d!=='00000000')?d.slice(0,4)+'-'+d.slice(4,6)+'-'+d.slice(6,8):'—';
  rows.forEach(r=>{ const tr=document.createElement('tr');
    const f2url=(r.k==='f2')?f2DetailUrl(r.r):'';
    const link=(DICT[r.k]&&r.qn)
      // Console viewer first — same single sign-in as this page, matching F2.
      // CSWeb stays as a second, quieter link because it is still where a case is
      // EDITED; this viewer is read-only.
      ? '<a class="rlink" target="_blank" rel="noopener" title="Opens this case in full detail on this console — no second sign-in" href="/docs/case.html?inst='+r.k+'&qn='+encodeURIComponent(r.qn)+'">Responses ↗</a>'
        + '<a class="rlink2" target="_blank" rel="noopener" title="Open in CSWeb — the editing surface; needs a CSWeb login" href="/csweb/sync-report?dict='+DICT[r.k]+'&case='+encodeURIComponent(r.qn)+'">CSWeb</a>'
      : f2url
      ? '<a class="rlink" target="_blank" rel="noopener" title="Opens this response in full detail on this console — no second sign-in" href="'+f2url+'">Responses ↗</a>'
      : '<span class="mix" title="no full-detail view — this F2 row predates submission-id tracking">—</span>';
    tr.innerHTML='<td><span class="instchip">'+r.k.toUpperCase()+'</span></td>'
      +'<td class="mono">'+esc(r.qn||'—')+'</td>'
      +'<td>'+esc(r.area)+'</td>'
      +'<td'+(r.repl?' class="hot" title="replacement — the sampled unit was never interviewed; a substitute was drawn"':'')+'>'+esc(r.result||'—')+'</td>'
      +'<td class="short'+(r.status==='Partial'?'':' zero')+'">'+esc(r.status||'—')+'</td>'
      +'<td class="mono">'+fd(r.date)+'</td>'
      +'<td>'+esc(r.en||'—')+'</td>'
      +'<td'+(r.lg?'':' class="nolog" title="no sync record — no CSWeb account attributable"')+'>'+esc(r.lg||'—')+'</td>'
      +'<td class="s">'+link+'</td>';
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
    if(phaseSel.value!=='ALL' && (r.phase||'unphased')!==phaseSel.value) return false;
    if(actSel.value!=='ALL' && (r.activity||'unassigned')!==actSel.value) return false;
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
  renderCaseList(pass);
  renderQuality(pass);
  lastPass=pass;             // lets the 20s feed poll refresh the quality panel alone
  // INSTS (not a hardcoded f1/f3/f4 list) so F2 keeps its own card — the productivity
  // panel above still skips F2 internally, since it has no enumerator.
  INSTS.forEach(k=>{
    // pass() takes optional ignore-flags, so it must NEVER be handed to filter()
    // directly - filter() would supply (index, array) as those flags.
    const rows=(P.data[k]||[]).filter(r=>pass(r));
    cardNum[k].textContent=rows.length;
    const card=cardNum[k].closest('.card');
    card.style.display=(inst==='ALL'||inst===k)?'':'none';
    card.classList.toggle('sel', inst===k);
  });
  P.spec.forEach(s=>{
    const show=(inst==='ALL'||inst===s.prefix);
    s._el.style.display=show?'':'none';
    if(!show) return;
    const rows=(P.data[s.prefix]||[]).filter(r=>pass(r));   // see note above
    s._cnt.textContent='· '+s.charts.length+' chart'+(s.charts.length===1?'':'s')+' · '+rows.length+' case'+(rows.length===1?'':'s')+' in view';
    s._car.textContent=s._open?'▾':'▸';
    s._body.style.display=s._open?'':'none';
    if(!s._open){
      // free the hidden charts so re-expanding always builds fresh against current filters
      s.charts.forEach(c=>{const id=s.prefix+'__'+c.field; if(charts[id]){charts[id].destroy(); delete charts[id];}});
      return;
    }
    if(typeof Chart==='undefined') return;           // charts need the vendored lib
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
instSel.onchange=render; phaseSel.onchange=render; actSel.onchange=render; regSel.onchange=render; supSel.onchange=render; enumSel.onchange=render; statSel.onchange=render; fromInp.onchange=render; toInp.onchange=render;
document.getElementById('fReset').onclick=()=>{instSel.value='ALL';regSel.value='ALL';phaseSel.value='ALL';actSel.value='ALL';supSel.value='ALL';enumSel.value='ALL';statSel.value='ALL';fromInp.value='';toInp.value='';document.getElementById('clSearch').value='';render();};
document.getElementById('clSearch').oninput=()=>{ if(lastPass) renderCaseList(lastPass); };
document.getElementById('clExport').onclick=exportCaseCsv;
render();

// The assignment plan lives outside the page now (see build()). It is fetched once,
// from a URL whose hash changes only when the plan does, so a 2-minute refresh costs
// nothing. Coverage is the only panel that needs it and already hides itself when the
// plan is absent, so nothing above blocks on this request.
(function loadPlan(){
  if(!P.targetsUrl) return;
  const cov=document.getElementById('coverage');
  if(cov) cov.innerHTML='<p class="cov-note" id="planWait">Loading the assignment plan\u2026</p>';
  fetch(P.targetsUrl,{cache:'force-cache'})
    .then(r=>r.ok?r.json():Promise.reject(r.status))
    .then(j=>{ P.targets=j||{}; render(); })
    .catch(()=>{ const w=document.getElementById('planWait');
      if(w) w.textContent='Coverage vs. plan is unavailable \u2014 the assignment plan did not load. Every other panel on this page is unaffected.'; });
})();
</script>
<!-- ===== sync-activity notification bell (2026-07-15) — polls /docs/sync-feed.json ===== -->
<style>
#bellWrap{position:fixed;top:14px;right:20px;z-index:9999;font:14px system-ui,Segoe UI,Roboto,sans-serif}
#bellBtn{position:relative;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.4);border-radius:10px;padding:7px 9px;cursor:pointer;line-height:0;transition:background .15s ease}
#bellBtn:hover{background:rgba(255,255,255,.3)}
#bellBtn:focus-visible{outline:2px solid #e5b23b;outline-offset:2px}
#bellBadge{position:absolute;top:-7px;right:-7px;min-width:19px;height:19px;padding:0 5px;background:#d32f2f;color:#fff;border-radius:10px;font-size:11px;font-weight:700;line-height:19px;text-align:center;box-shadow:0 0 0 2px #006b3f}
#bellBadge.calm{background:#0a7f4a}
#bellPanel{position:absolute;top:46px;right:0;width:372px;max-height:74vh;background:#fff;color:#1c2b25;border:1px solid #dfe7e2;border-radius:14px;box-shadow:0 16px 44px rgba(9,30,20,.22);overflow:hidden;display:flex;flex-direction:column;animation:bpin .16s ease-out}
@keyframes bpin{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}
#bellPanel[hidden]{display:none}
#bellHead{padding:12px 14px 11px;border-bottom:1px solid #eef3f0;display:flex;justify-content:space-between;align-items:center;gap:8px}
#bellHead .ttl{font-weight:700;color:#004d2c;font-size:14.5px;flex:1;min-width:0}
#bellHead .ttl small{display:block;font-weight:400;font-size:11.5px;color:#7b8a83;margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#bellHead .bh-right{flex:0 0 auto}
#bellEnable{font:12px system-ui;padding:4px 9px;border:1px solid #dfe7e2;border-radius:7px;background:#f4f7f5;cursor:pointer;color:#006b3f;font-weight:600;white-space:nowrap}
#bellEnable.on{background:#006b3f;color:#fff;border-color:#006b3f}
.bh-right{display:flex;align-items:center;gap:4px}
#bellClose{font:20px/1 system-ui;width:26px;height:26px;border:none;background:transparent;color:#5b6b63;cursor:pointer;border-radius:6px}
#bellClose:hover{background:#eef3f0;color:#1c2b25}
#bellTools{display:flex;align-items:center;gap:5px;padding:7px 12px;border-bottom:1px solid #eef3f0;background:#fbfdfc}
#bellTools select{font:11.5px system-ui;padding:3px 6px;border:1px solid #dfe7e2;border-radius:6px;background:#fff;color:#1c2b25;max-width:118px;flex:0 1 auto;min-width:0}
#bellTools button{font:11.5px system-ui;padding:3px 8px;white-space:nowrap;border:1px solid #dfe7e2;border-radius:6px;background:#fff;color:#5b6b63;cursor:pointer}
#bellTools button:hover{background:#eef3f0;color:#1c2b25}
#bellTools button.on{background:#006b3f;color:#fff;border-color:#006b3f}
#bellTools .spacer{margin-left:auto}
#bellTools :focus-visible,#bellHead :focus-visible{outline:2px solid #006b3f;outline-offset:1px}
#bellScroll{overflow-y:auto;flex:1}
/* section headings — the fix for one undifferentiated scroll */
.bsec{position:sticky;top:0;z-index:2;background:#f4f7f5;border-bottom:1px solid #e6ede9;padding:6px 13px;font-size:10.5px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:#5b6b63;display:flex;align-items:center;gap:7px}
.bsec .n{background:#dfe7e2;color:#41514a;border-radius:9px;padding:0 6px;font-size:10px;line-height:15px;min-width:16px;text-align:center}
.bsec.attn{background:#fdf3f3;border-bottom-color:#f6dede;color:#8a1c1c}
/* class display:flex would otherwise beat the hidden attribute (same trap as
   the .enumchip empty-pill bug, 2026-07-17) */
.bsec[hidden]{display:none}
.bsec.attn .n{background:#f3d3d3;color:#8a1c1c}
/* alert rows: severity rail + name-first copy + right-aligned relative age */
.balert{display:flex;gap:9px;padding:10px 13px;border-bottom:1px solid #f4eaea;background:#fdf5f5;font-size:13px;line-height:1.4;border-left:3px solid #d32f2f}
.balert:last-child{border-bottom:none}
.balert.quiet{background:#fffaef;border-bottom-color:#f4ecd8;border-left-color:#e0a52d}
.balert.acked{opacity:.5}
.balert .bic{flex:0 0 auto;font-size:13px;line-height:1.35}
.balert .bbody{flex:1;min-width:0}
.balert .bt{color:#1c2b25;font-weight:600}
.balert .bt b{color:#8a1c1c}
.balert.quiet .bt b{color:#8a6412}
.balert .bwhy{color:#6b7a73;font-size:11.8px;margin-top:2px}
.balert .bage{flex:0 0 auto;color:#8a9791;font-size:11px;font-variant-numeric:tabular-nums;white-space:nowrap;padding-top:1px}
.balert .tier{display:inline-block;font-size:9.5px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:#fff;background:#c62828;border-radius:4px;padding:1px 5px;margin-left:6px;vertical-align:1px}
/* activity rows */
#bellList .brow{display:flex;gap:9px;padding:9px 13px;border-bottom:1px solid #f4f7f5}
#bellList .brow:last-child{border-bottom:none}
#bellList .brow.fresh{background:#f0f9f4;border-left:3px solid #0a7f4a;padding-left:10px}
#bellList .brow.dim{opacity:.55}
#bellList .bbody{flex:1;min-width:0}
#bellList .who{font-weight:700;color:#1c2b25;font-size:13px}
#bellList .who .lg{font-weight:400;color:#8a9791;font-size:11.5px;margin-left:4px}
#bellList .sub{color:#5b6b63;font-size:12.2px;margin-top:2px}
#bellList .bage{flex:0 0 auto;color:#8a9791;font-size:11px;font-variant-numeric:tabular-nums;white-space:nowrap;padding-top:2px}
#bellList .bmuted{color:#9aa8a1;font-style:italic}
#bellList .inst{display:inline-block;font-size:10.5px;font-weight:700;color:#006b3f;background:#e7f3ec;border-radius:5px;padding:0 6px;margin-right:5px}
.bellEmpty{padding:22px 16px;color:#7b8a83;font-size:12.8px;text-align:center}
.ballclear{padding:18px 16px;text-align:center;color:#2f6b4f;background:#f3fbf6;border-bottom:1px solid #e2f0e8}
.ballclear .big{font-size:22px;line-height:1}
.ballclear .t{font-weight:700;color:#046a38;margin-top:5px;font-size:13.5px}
.ballclear .s{color:#6b7a73;font-size:11.8px;margin-top:2px}
#bellFoot{padding:8px 13px;border-top:1px solid #eef3f0;color:#7b8a83;font-size:11px;background:#fbfdfc}
#toastWrap{position:fixed;bottom:18px;right:18px;z-index:10000;display:flex;flex-direction:column;gap:10px;max-width:min(360px,calc(100vw - 36px))}
.btoast{position:relative;background:#004d2c;color:#fff;border-radius:11px;padding:11px 34px 11px 15px;box-shadow:0 8px 28px rgba(9,30,20,.3);transition:opacity .4s,transform .4s;animation:btin .25s ease;font-size:13px;line-height:1.4}
.btoast b{color:#ffe08a}
.btoast .x{position:absolute;top:6px;right:8px;border:none;background:transparent;color:rgba(255,255,255,.65);font:16px/1 system-ui;cursor:pointer;padding:2px 4px;border-radius:5px}
.btoast .x:hover{background:rgba(255,255,255,.16);color:#fff}
.btoast.alert{background:#b71c1c}.btoast.alert b{color:#ffe08a}
.btoast.quiet{background:#8a5a00}.btoast.quiet b{color:#ffe9b3}
@keyframes btin{from{transform:translateX(20px);opacity:0}to{transform:none;opacity:1}}
@media(max-width:820px){#bellPanel{width:min(330px,calc(100vw - 24px));max-height:70vh}#bellWrap{top:12px;right:12px}}
@media(prefers-reduced-motion:reduce){#bellPanel,.btoast{animation:none}}
</style>
<div id="bellWrap">
  <button id="bellBtn" title="Notifications" aria-label="Notifications" aria-expanded="false" aria-haspopup="dialog">
    <svg viewBox="0 0 24 24" width="21" height="21" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/></svg>
    <span id="bellBadge" hidden>0</span>
  </button>
  <div id="bellPanel" role="dialog" aria-label="Notifications" hidden>
    <div id="bellHead"><span class="ttl">Notifications<small id="bellSummary">Loading&hellip;</small></span><span class="bh-right"><button id="bellEnable" type="button">Enable alerts</button><button id="bellClose" type="button" aria-label="Close" title="Close">&times;</button></span></div>
    <div id="bellTools">
      <select id="bellEnum" title="Filter by enumerator"><option value="">All enumerators</option></select>
      <button id="bellSound" type="button" title="Play a sound on new activity" aria-label="Sound on new activity">&#128266;</button>
      <button id="bellEdited" type="button" title="Also notify when a sync only edits existing cases">Edited</button>
      <button id="bellRead" type="button" class="spacer" title="Clear the badge and acknowledge current alerts">Read all</button>
    </div>
    <div id="bellScroll">
      <div id="bellAlertSec" class="bsec attn" hidden><span>Needs attention</span><span class="n" id="bellAlertN">0</span></div>
      <div id="bellAlerts" aria-live="polite"></div>
      <div id="bellActSec" class="bsec"><span>Recent activity</span><span class="n" id="bellActN">0</span></div>
      <div id="bellList"><div class="bellEmpty">Waiting for the next device sync&hellip;</div></div>
    </div>
    <div id="bellFoot">Updates every 20s &middot; alerts stay until you mark them read</div>
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
  var LS2='uhc_bell_alert_notified', LS3='uhc_bell_prefs', LS4='uhc_bell_ack';
  // prefs: snd = beep on new activity, edt = also notify on edited-only syncs,
  // enm = enumerator filter. All persist per browser; all default OFF/empty so
  // the page behaves exactly as before until someone opts in.
  var prefs={snd:0,edt:0,enm:''};
  try{prefs=Object.assign(prefs,JSON.parse(localStorage.getItem(LS3)||'{}'));}catch(e){}
  function savePrefs(){try{localStorage.setItem(LS3,JSON.stringify(prefs));}catch(e){}}
  var ack={};
  try{(JSON.parse(localStorage.getItem(LS4)||'[]')).forEach(function(k){ack[k]=1;});}catch(e){}
  function saveAck(){try{localStorage.setItem(LS4,JSON.stringify(Object.keys(ack).slice(-400)));}catch(e){}}
  // A short WebAudio blip — no asset to host, and it stays silent until the user
  // has interacted with the page (browsers block audio before a gesture anyway).
  var actx=null;
  function beep(alert){
    if(!prefs.snd)return;
    try{
      actx=actx||new (window.AudioContext||window.webkitAudioContext)();
      if(actx.state==='suspended'){actx.resume();}
      var o=actx.createOscillator(), g=actx.createGain(), t=actx.currentTime;
      o.type='sine'; o.frequency.setValueAtTime(alert?520:760,t);
      if(alert)o.frequency.setValueAtTime(430,t+0.13);
      g.gain.setValueAtTime(0.0001,t);
      g.gain.exponentialRampToValueAtTime(0.09,t+0.02);
      g.gain.exponentialRampToValueAtTime(0.0001,t+(alert?0.30:0.18));
      o.connect(g);g.connect(actx.destination);o.start(t);o.stop(t+(alert?0.32:0.2));
    }catch(e){}
  }
  function activeCount(e){return (e.total_new||0)+(prefs.edt?(e.total_edited||0):0);}
  var s0=localStorage.getItem(LS);
  var seenRev = s0===null ? null : parseInt(s0,10);
  var notifiedRev=null, latest=[], alerts=[];
  // toasts are dismissible and self-limiting: 4 on screen at once is plenty
  function addToast(t,ms){
    toastWrap.appendChild(t);
    while(toastWrap.children.length>4)toastWrap.removeChild(toastWrap.firstChild);
    var kill=function(){t.style.opacity='0';setTimeout(function(){if(t.parentNode)t.remove();},400);};
    var x=t.querySelector('.x'); if(x)x.addEventListener('click',kill);
    setTimeout(kill,ms);
  }
  function esc(x){return String(x==null?'':x).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  function fmt(iso){try{return new Date(iso).toLocaleString('en-PH',{hour:'numeric',minute:'2-digit',hour12:true,month:'short',day:'numeric'});}catch(e){return iso||'';}}
  // Relative age is what a monitor actually reads ("3 days ago"), so it leads;
  // the absolute stamp stays in the title attribute for when precision matters.
  function ago(iso){
    try{
      var ms=Date.now()-new Date(iso).getTime();
      if(!isFinite(ms))return '';
      var m=Math.round(ms/60000);
      if(m<1)return 'just now';
      if(m<60)return m+' min ago';
      var h=Math.round(m/60);
      if(h<24)return h+' h ago';
      var d=Math.round(h/24);
      return d===1?'yesterday':(d+' days ago');
    }catch(e){return '';}
  }
  // one phrasing used by the toast AND the OS notification, so they never drift
  function detail(e){
    return (e.items||[]).filter(function(it){return (it.new||0)>0||(prefs.edt&&(it.edited||0)>0);})
      .map(function(it){
        var p=[];
        if(it.new>0)p.push(it.new+' new case'+(it.new==1?'':'s'));
        if(prefs.edt&&it.edited>0)p.push(it.edited+' edited');
        return it.inst+': '+p.join(' + ');
      }).join(', ');
  }
  function fillEnum(){
    var sel=document.getElementById('bellEnum'); if(!sel)return;
    var seenU={}, opts=[];
    latest.forEach(function(e){ if(e.user&&!seenU[e.user]){seenU[e.user]=1;opts.push([e.user,e.name||e.user]);} });
    opts.sort(function(a,b){return a[1].localeCompare(b[1]);});
    var want='<option value="">All enumerators</option>'+opts.map(function(o){
      return '<option value="'+esc(o[0])+'">'+esc(o[1])+'</option>';}).join('');
    if(sel.innerHTML!==want){sel.innerHTML=want;}
    if(sel.value!==prefs.enm)sel.value=prefs.enm;
  }
  function render(){
    if(!latest.length){list.innerHTML='<div class="bellEmpty">Waiting for the next device sync&hellip;</div>';return;}
    var base=(seenRev==null)?Infinity:seenRev;
    var rows=prefs.enm?latest.filter(function(e){return (e.user||'')===prefs.enm;}):latest;
    if(!rows.length){list.innerHTML='<div class="bellEmpty">No syncs from '+esc(prefs.enm)+' yet&hellip;</div>';return;}
    list.innerHTML=rows.map(function(e){
      var tn=e.total_new||0, te=e.total_edited||0, active=(tn>0||te>0);
      var fresh=(e.rev>base&&tn>0)?' fresh':'';
      var det;
      if(active){
        det=(e.items||[]).filter(function(it){return (it.new||0)>0||(it.edited||0)>0;}).map(function(it){
          var p=[]; if(it.new>0)p.push('<b>'+it.new+'</b> new'); if(it.edited>0)p.push('<b>'+it.edited+'</b> edited');
          return '<span class="inst">'+esc(it.inst)+'</span> '+p.join(' + ');
        }).join(' &middot; ');
      }else{
        det='<span class="bmuted">connected, no new cases</span>';
      }
      return '<div class="brow'+fresh+(active?'':' dim')+'" title="'+esc(fmt(e.time))+'">'+
             '<span class="bbody"><div class="who">'+esc(e.name||e.user)+(e.name?'<span class="lg">'+esc(e.user)+'</span>':'')+'</div>'+
             '<div class="sub">'+det+'</div></span>'+
             '<span class="bage">'+esc(ago(e.time))+'</span></div>';
    }).join('');
    var an=document.getElementById('bellActN'); if(an)an.textContent=rows.length;
  }
  // one plain-language line under the title, so the panel says how things ARE
  function summarise(){
    var el=document.getElementById('bellSummary'); if(!el)return;
    var nAl=alerts.filter(function(a){return !ack[a.id];}).length;
    var last=latest.length?ago(latest[0].time):null;
    el.textContent=(nAl?(nAl+' need'+(nAl===1?'s':'')+' attention'):'All clear')
      +(last?(' \u00b7 last sync '+last):'');
  }
  function badgeUpd(){
    var base=(seenRev==null)?Infinity:seenRev;
    // only UNACKNOWLEDGED alerts count — before this the badge could never reach
    // zero while any alert existed, which trained people to ignore it entirely.
    var nAl=alerts.filter(function(a){return !ack[a.id];}).length;
    var n=latest.filter(function(e){return e.rev>base&&activeCount(e)>0;}).length + nAl;
    if(n>0){
      badge.textContent=n>99?'99+':n;
      badge.hidden=false;
      // red = unresolved alerts; green = only unread sync activity
      badge.classList.toggle('calm',nAl===0);
      btn.setAttribute('aria-label',nAl?(nAl+' alerts need attention'):(n+' new syncs'));
    }else{badge.hidden=true;btn.setAttribute('aria-label','Notifications');}
    summarise();
  }
  function toast(e){
    var d=detail(e);
    var t=document.createElement('div');t.className='btoast';
    t.innerHTML='&#128276; <b>'+esc(e.name||e.user)+'</b> synced &middot; <b>'+esc(d)+'</b>'
      +'<button class="x" type="button" aria-label="Dismiss">&times;</button>';
    addToast(t,6000);
  }
  function osNotify(e){
    if(!('Notification' in window)||Notification.permission!=='granted')return;
    var d=detail(e);
    try{new Notification((e.name||e.user)+' synced',{body:d+' · '+fmt(e.time),tag:'sync-'+e.rev});}catch(err){}
  }
  // Each alert answers three questions in a fixed place: WHO/WHAT (bold, first),
  // WHY IT MATTERS / what to do (muted second line), HOW OLD (right rail).
  function alertParts(a){
    if(a.type==='silence'){
      var tier=(a.level==='high')?'<span class="tier">3+ days</span>':'';
      return {ic:'&#128276;',
        t:'<b>'+esc(a.name||a.user)+'</b> has not synced'+tier,
        why:'No upload for '+a.hours+' h &middot; check the tablet or reach the enumerator',
        age:ago(a.since), ttl:'Last upload '+fmt(a.since), quiet:(a.level!=='high')};
    }
    var who=(a.users&&a.users.length)?(' &middot; '+esc(a.users.join(', '))):'';
    if(a.type==='dup'){
      return {ic:'&#9888;&#65039;',
        t:'<b>Duplicate case key</b> '+esc(a.key),
        why:esc(a.inst)+' &middot; '+a.n+' cases share this key'+who+' &middot; resolve before analysis',
        age:'', ttl:'', quiet:false};
    }
    return {ic:'&#9888;&#65039;',
      t:'<b>Case outside the plan</b> &middot; facility '+esc(a.code9||a.example||''),
      why:esc(a.inst)+' &middot; '+a.n+' case'+(a.n>1?'s':'')+' not in the assignment plan'+who,
      age:'', ttl:'', quiet:false};
  }
  function renderAlerts(){
    var sec=document.getElementById('bellAlertSec'), cnt=document.getElementById('bellAlertN');
    if(!alerts.length){
      alertBox.innerHTML='<div class="ballclear"><div class="big">&#9989;</div>'
        +'<div class="t">Nothing needs attention</div>'
        +'<div class="s">No missed syncs, duplicate keys or off-plan cases.</div></div>';
      if(sec)sec.hidden=true;
      return;
    }
    if(sec)sec.hidden=false;
    if(cnt)cnt.textContent=alerts.length;
    // unacknowledged first, then loudest, so the top of the list is the next thing to do
    var ordered=alerts.slice().sort(function(x,y){
      var ax=ack[x.id]?1:0, ay=ack[y.id]?1:0; if(ax!==ay)return ax-ay;
      var lx=(x.level==='high'||x.type!=='silence')?0:1, ly=(y.level==='high'||y.type!=='silence')?0:1;
      if(lx!==ly)return lx-ly;
      return (y.hours||0)-(x.hours||0);
    });
    alertBox.innerHTML=ordered.map(function(a){
      var p=alertParts(a);
      var cls='balert'+(p.quiet?' quiet':'')+(ack[a.id]?' acked':'');
      return '<div class="'+cls+'"'+(p.ttl?(' title="'+esc(p.ttl)+'"'):'')+'>'
        +'<span class="bic">'+p.ic+'</span>'
        +'<span class="bbody"><span class="bt">'+p.t+'</span>'
        +'<div class="bwhy">'+p.why+'</div></span>'
        +(p.age?('<span class="bage">'+esc(p.age)+'</span>'):'')
        +'</div>';
    }).join('');
  }
  function alertToast(a){
    var msg=(a.type==='silence')?('No sync from '+(a.name||a.user)+' in '+a.hours+' h')
      :(a.type==='dup')?('Duplicate key '+a.key+' ('+a.inst+')'):('Off-plan case '+(a.code9||a.example||'')+' ('+a.inst+')');
    var t=document.createElement('div');t.className='btoast '+((a.type==='silence'&&a.level!=='high')?'quiet':'alert');
    t.innerHTML='&#9888;&#65039; <b>'+esc(msg)+'</b>'+((a.users&&a.users.length)?(' &middot; '+esc(a.users.join(', '))):'')
      +'<button class="x" type="button" aria-label="Dismiss">&times;</button>';
    addToast(t,9000);
  }
  function alertNotify(a){
    if(!('Notification' in window)||Notification.permission!=='granted')return;
    var title=(a.type==='silence')?'🔕 No sync from '+(a.name||a.user)
      :(a.type==='dup')?'⚠️ Duplicate case key':'⚠️ Case outside the plan';
    var body=(a.type==='silence')?(a.hours+' hours since the last upload · '+fmt(a.since))
      :(a.type==='dup')?(a.key+' · '+a.inst+' · '+a.n+' cases'):('facility '+a.code9+' · '+a.inst+' · '+a.n+' case(s)');
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
          var fresh=latest.filter(function(e){return e.rev>notifiedRev&&activeCount(e)>0;}).sort(function(a,b){return a.rev-b.rev;});
          fresh.forEach(function(e){toast(e);osNotify(e);});
          if(fresh.length)beep(false);
          notifiedRev=maxRev;
        }
      }
      var firstA=(localStorage.getItem(LS2)===null), seen=[];
      try{seen=JSON.parse(localStorage.getItem(LS2)||'[]');}catch(e){seen=[];}
      var sset={}; seen.forEach(function(k){sset[k]=1;});
      var newAl=0;
      alerts.forEach(function(a){ if(!sset[a.id]){ if(!firstA){alertToast(a);alertNotify(a);newAl++;} seen.push(a.id); sset[a.id]=1; } });
      if(newAl)beep(true);
      fillEnum();
      localStorage.setItem(LS2, JSON.stringify(seen.slice(-300)));
      render(); renderAlerts(); badgeUpd();
    }).catch(function(){});
  }
  function openPanel(){
    panel.removeAttribute('hidden');
    btn.setAttribute('aria-expanded','true');
    if(latest.length){seenRev=latest[0].rev;localStorage.setItem(LS,String(seenRev));}
    badgeUpd();render();
    var f=panel.querySelector('#bellEnum'); if(f)f.focus();
  }
  function closePanel(refocus){
    panel.setAttribute('hidden','');
    btn.setAttribute('aria-expanded','false');
    if(refocus)btn.focus();
  }
  btn.addEventListener('click',function(){
    if(panel.hasAttribute('hidden'))openPanel(); else closePanel(false);
  });
  document.getElementById('bellClose').addEventListener('click',function(ev){ev.stopPropagation();closePanel(true);});
  document.addEventListener('keydown',function(ev){
    if(ev.key==='Escape'&&!panel.hasAttribute('hidden')){closePanel(true);}
  });
  document.addEventListener('click',function(ev){if(!wrap.contains(ev.target)){panel.setAttribute('hidden','');}});
  function reflect(){if(('Notification' in window)&&Notification.permission==='granted'){enableBtn.textContent='Alerts on';enableBtn.classList.add('on');}}
  enableBtn.addEventListener('click',function(ev){ev.stopPropagation();
    if(!('Notification' in window)){enableBtn.textContent='Not supported';return;}
    Notification.requestPermission().then(reflect);
  });
  var soundBtn=document.getElementById('bellSound'), editedBtn=document.getElementById('bellEdited'),
      readBtn=document.getElementById('bellRead'), enumSel=document.getElementById('bellEnum');
  function reflectPrefs(){
    soundBtn.classList.toggle('on',!!prefs.snd);
    editedBtn.classList.toggle('on',!!prefs.edt);
  }
  soundBtn.addEventListener('click',function(ev){ev.stopPropagation();
    prefs.snd=prefs.snd?0:1;savePrefs();reflectPrefs();if(prefs.snd)beep(false);});
  editedBtn.addEventListener('click',function(ev){ev.stopPropagation();
    prefs.edt=prefs.edt?0:1;savePrefs();reflectPrefs();render();badgeUpd();});
  enumSel.addEventListener('change',function(ev){ev.stopPropagation();
    prefs.enm=enumSel.value;savePrefs();render();});
  readBtn.addEventListener('click',function(ev){ev.stopPropagation();
    if(latest.length){seenRev=latest[0].rev;localStorage.setItem(LS,String(seenRev));}
    alerts.forEach(function(a){ack[a.id]=1;});saveAck();
    badgeUpd();render();renderAlerts();});
  reflectPrefs(); reflect(); poll(); setInterval(poll,20000);
})();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Unified portal shell (2026-07-25). The dashboard now renders inside the same
# sidebar / topbar / footer chrome as capi.asiansocial.org, via the shared
# portal_shell module. The large TEMPLATE above is left intact; its outer
# chrome is re-wrapped here so the change stays small and reversible. The
# notification bell, the payload script and all dashboard JS (everything below
# the footer) are untouched. Served on csweb during pretest; the sidebar links
# point back to the portal origin so navigation is unified across domains.
# ---------------------------------------------------------------------------
_DESC = ("Fieldwork monitoring for the ASPSI \u00d7 DOH UHC Survey Year 2 \u2014 "
         "F1/F3/F4 CSEntry tablets and the F2 healthcare-worker web form.")

_CHROME_RULES = (
    "header{background:var(--g);color:#fff;padding:20px 24px}",
    "header h1{margin:0;font-size:20px;letter-spacing:-.01em}",
    "header .s{opacity:.85;font-size:13px;margin-top:4px}",
    "footer{max-width:1180px;margin:0 auto;padding:14px 22px 40px;color:var(--muted);font-size:12.5px}",
    "header nav{margin-top:10px;display:flex;flex-wrap:wrap;gap:6px 18px;font-size:13px}",
    "header nav a{color:#fff;opacity:.92;text-decoration:none;border-bottom:1px solid rgba(255,255,255,.45);padding-bottom:1px}",
    "header nav a:hover{opacity:1;border-bottom-color:#fff}",
    "header nav .here{opacity:1;font-weight:700;border-bottom:2px solid var(--gold)}",
    "body{margin:0;font:15px/1.5 system-ui,Segoe UI,Roboto,sans-serif;color:var(--ink);background:var(--bg)}",
)


def _shellify_dashboard(t):
    head_chrome, _, rest1 = t.partition("<main>")
    main_content, _, rest2 = rest1.partition("</main>")
    footer_block, _, scripts = rest2.partition("</footer>")
    # page CSS = the single <style> block in the old head; strip its chrome rules
    css = head_chrome.split("<style>", 1)[1].split("</style>", 1)[0]
    for rule in _CHROME_RULES:
        css = css.replace(rule, "")
    css = css.replace("main{max-width:1180px;margin:0 auto;padding:22px}",
                      "main{max-width:none;margin:0;padding:0}")
    footer_inner = footer_block.split("<footer>", 1)[1]
    base = PS.PORTAL_ORIGIN
    crumbs = [("UHC Survey Year 2", PS.P + "/"),
              ("Monitoring", PS.P + "/monitoring/"),
              ("Sync Dashboard", None)]
    # dashboard + map are same-origin on csweb during pretest
    seg = ('<div class="tb-seg"><a class="on" href="/docs/dashboard.html">Sync Dashboard</a>'
           '<a href="/docs/map.html">Map</a></div>')
    # No lock pill: the identity chip open_shell puts in .tb-right already says
    # who is signed in, which is the true version of what the pill implied.
    tb_right = seg
    head_html = PS.head("UHC Survey Year 2 \u2014 Sync Dashboard", _DESC, extra_css=css)
    head_html = head_html.replace(
        "</head>", '<script src="/docs/assets/chart.umd.min.js"></script>\n</head>')
    opened = (head_html + '\n<body>\n<div class="app">\n'
              + PS.sidebar(PS.P + "/monitoring/", base)
              + '\n<div class="main">\n<div class="topbar"><div class="crumbs">'
              + PS.crumbs_html(crumbs, base) + '</div><div class="tb-right">' + tb_right + PS.SIGNOUT_CHIP
              + '</div></div>\n<div class="canvas">\n<main>')
    closed = ('\n</main>\n<footer class="page-foot">' + footer_inner + '</footer>\n'
              '</div>\n</div>\n</div>\n')
    out = opened + main_content + closed + PS.SIGNOUT_JS + scripts
    # one canonical verde across css, client JS and the bell
    out = out.replace("#006b3f", "#046a38").replace("#004d2c", "#04331d")
    return out


TEMPLATE = _shellify_dashboard(TEMPLATE)


def build(data, targets=None, plan=None, errored=None, f2_api_ok=None):
    """Assemble the payload + HTML from a {inst: [row-dict,...]} data map.

    `plan`    = assignment-plan provenance (provisional vs final) for the coverage banner.
    `errored` = the set of instruments whose live query failed (surfaced on the F2
                freshness note).
    """
    errored = errored or set()
    # activity phase per case (Carl, 2026-07-27): roster wins, date falls back.
    _preg = phase_lib.load()
    _areg = activity_lib.load()
    for _rows in data.values():
        for _r in _rows:
            _d = _r.get("date") or ""
            _day = ("%s-%s-%s" % (_d[:4], _d[4:6], _d[6:8])
                    if _d.isdigit() and len(_d) == 8 and _d != "00000000" else None)
            _u = _r.get("syncuser")
            _lg = None if not _u or _u == "(unknown)" else _u
            _r["phase"] = phase_lib.phase_of(_lg, _day, _preg)
            _r["activity"] = activity_lib.activity_of(_lg, _day, _areg)
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
    # The assignment plan is 1,521 static facilities - 185 KB that does not change
    # between 2-minute regenerations. Inline, it was 53% of the page. It now ships as
    # its own cacheable file; the hash busts that cache only when the plan really
    # changes. `targets` stays in the payload as an empty object so every consumer
    # keeps its existing shape and its existing "no plan yet" fallback.
    plan_blob = json.dumps(targets or {}, separators=(",", ":"))
    plan_url = "/docs/plan.json?v=" + hashlib.md5(plan_blob.encode("utf-8")).hexdigest()[:10]
    payload_obj = {
        "data": data,
        "spec": spec,
        "regions": sorted(regions),
        "supervisors": sorted(supervisors),
        "dateMin": date_min,
        "dateMax": date_max,
        "today": today,
        "targets": {},            # externalised - fetched from targetsUrl, see above
        "targetsUrl": plan_url,
        "f2meta": f2meta,
        "plan": plan or {},
        "actreg": activity_lib.public_view(),
        "generated": now_utc.strftime("%Y-%m-%d %H:%M UTC"),
    }
    # XSS-safe: JSON in a non-executable <script type="application/json">, HTML-escaped,
    # read back via JSON.parse(el.textContent). &,<,> can't break out of the tag.
    payload = html.escape(json.dumps(payload_obj), quote=False)
    out = (TEMPLATE.replace("__PAYLOAD__", payload).replace("__FAVICON__", FAVICON)
           .replace("__DOWNLOADS__", downloads_html()))
    return out, plan_blob


DATA_MANIFEST = "/opt/app/lamp/www/docs/data/manifest.json"
SPSS_MANIFEST = "/opt/app/lamp/www/docs/data/spss-manifest.json"
CSPRO_MANIFEST = "/opt/app/lamp/www/docs/data/cspro-manifest.json"
CODEBOOK_MANIFEST = "/opt/app/lamp/www/docs/data/codebook-manifest.json"


def _load_manifest(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def downloads_html():
    """Downloads band: CSPro sync .pffs + data-room zip bundles (manifest-driven).

    Three INDEPENDENT paths by design (post-#843): the .pff route needs the CSWeb
    sync API; the CSV zips are built straight from MySQL by csweb-responses-gen,
    so they keep working when the app/API is down; the SPSS/Stata/R zips are
    built from those CSVs + the questionnaire codebooks by csweb-spss-gen
    (labels embedded; the R zips carry a codebook CSV instead).
    Renders gracefully (pffs only) if a manifest has not been generated yet."""
    man = _load_manifest(DATA_MANIFEST)
    spss = _load_manifest(SPSS_MANIFEST)
    cspro = _load_manifest(CSPRO_MANIFEST)
    cbook = _load_manifest(CODEBOOK_MANIFEST)
    inst_meta = man.get("instruments") or {}
    spss_meta = spss.get("instruments") or {}
    gen = man.get("generated")
    out = ['<h2 class="band" id="b-downloads">Downloads</h2>']
    out.append('<div class="cov-note">Three independent ways to pull case data, so a broken sync path never '
               'blocks analysis. <b>CSPro sync</b>: download a .pff and double-click it &mdash; CSPro Data Viewer '
               'pulls a full <code>.csdb</code> (photos included) from the sync API. Run it in a <b>new folder</b> '
               'for a complete pull; re-running in the same folder fetches increments only. <b>Direct export</b>: '
               'zip of analysis-ready CSVs built straight from the database every ~2 min &mdash; works even when '
               'the CSWeb app or sync API is down; values are raw stored codes. <b>Stats exports</b>: the same '
               'cases packaged for SPSS (<code>.sav</code>) and Stata (<code>.dta</code>) with variable labels '
               '(question text) and value labels (code &rarr; answer) embedded from the questionnaire codebook, '
               'and for R (<code>.rds</code> plus a codebook CSV, raw codes preserved). '
               '<b>CSPro packages</b>: the complete CAPI entry applications (compiled .pen + Designer source + '
               'lookup files) and the questionnaire dictionaries, so CSPro users can run the instruments '
               'locally &mdash; extracted apps start with an empty local case file, no sync. '
               '<b>Codebook</b>: what every variable means — label, question, universe (who was asked), '
               'value codes and validation rules, as Excel + PDF, documented to the DDI/PSADA convention. '
               'Same login as this page.</div>')
    out.append('<div class="dl"><span class="rl">CSPro sync (.pff)</span>')
    for label, fn in (("F1 &mdash; Facility Head", "facilityheadsurvey_dict.pff"),
                      ("F3 &mdash; Patient", "patientsurvey_dict.pff"),
                      ("F4 &mdash; Household", "householdsurvey_dict.pff")):
        out.append('<a href="/docs/data/%s" download>%s</a>' % (fn, label))
    out.append('</div>')
    zrow = ['<div class="dl"><span class="rl">Direct export (CSV zip)</span>']
    for inst, label in (("f1", "F1"), ("f3", "F3"), ("f4", "F4"), ("f2", "F2")):
        m = inst_meta.get(inst)
        if m:
            zrow.append('<a class="zip" href="/docs/data/%s" download>%s &mdash; %s cases</a>'
                        % (m["zip"], label, m["cases"]))
    zrow.append('<a href="/docs/data/" target="_blank" rel="noopener">browse all CSVs &#8599;</a></div>')
    out.append("".join(zrow))
    for fkey, rl in (("spss", "SPSS export (.sav zip)"),
                     ("stata", "Stata export (.dta zip)"),
                     ("r", "R export (.rds zip)")):
        srow = ['<div class="dl"><span class="rl">%s</span>' % rl]
        have = False
        for inst, label in (("f1", "F1"), ("f3", "F3"), ("f4", "F4"), ("f2", "F2")):
            m = spss_meta.get(inst) or {}
            # "zips" is the per-format manifest; fall back to the legacy
            # spss-only "zip" key during a deploy window
            z = (m.get("zips") or {}).get(fkey) or (m.get("zip") if fkey == "spss" else None)
            if z:
                have = True
                srow.append('<a class="zip" href="/docs/data/%s" download>%s &mdash; %s cases</a>'
                            % (z, label, m["cases"]))
        comb = (spss.get("combined_zips") or {}).get(fkey) or (
            spss.get("combined") if fkey == "spss" else None)
        if comb and have:
            srow.append('<a href="/docs/data/%s" download>all instruments</a>' % comb)
        srow.append('</div>')
        if have:
            out.append("".join(srow))
    cbi = cbook.get("instruments") or {}
    brow = ['<div class="dl"><span class="rl">Codebook (Excel / PDF)</span>']
    have_b = False
    for inst, label in (("f1", "F1"), ("f3", "F3"), ("f4", "F4"), ("f2", "F2")):
        m = cbi.get(inst) or {}
        if m.get("xlsx"):
            have_b = True
            brow.append('<a class="zip" href="/docs/data/%s" download>%s &mdash; %s vars</a>'
                        % (m["xlsx"], label, m.get("variables", "")))
            if m.get("pdf"):
                brow.append('<a href="/docs/data/%s" download>%s PDF</a>' % (m["pdf"], label))
    combb = cbook.get("combined") or {}
    if combb.get("pdf") and have_b:
        brow.append('<a href="/docs/data/%s" download>all instruments (PDF)</a>' % combb["pdf"])
    brow.append('</div>')
    if have_b:
        out.append("".join(brow))
    cins = cspro.get("instruments") or {}
    crow = ['<div class="dl"><span class="rl">CSPro app (zip)</span>']
    have_c = False
    for inst, label in (("f1", "F1"), ("f3", "F3"), ("f4", "F4")):
        m = cins.get(inst) or {}
        if m.get("zip"):
            have_c = True
            crow.append('<a class="zip" href="/docs/data/%s" download>%s &mdash; v%s</a>'
                        % (m["zip"], label, m.get("version", "?")))
    if cspro.get("dictionaries_zip") and have_c:
        crow.append('<a href="/docs/data/%s" download>dictionaries (.dcf)</a>'
                    % cspro["dictionaries_zip"])
    crow.append('</div>')
    if have_c:
        out.append("".join(crow))
    if gen:
        stamp = 'export bundles generated %s' % html.escape(str(gen), quote=False)
        if spss.get("generated"):
            stamp += ' &middot; stats exports %s' % html.escape(str(spss["generated"]), quote=False)
        out.append('<div class="cov-sum">%s &middot; refreshed ~every 2 min</div>' % stamp)
    return chr(10).join(out)


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
    out_html, plan_blob = build(data, targets, plan, errored, api_ok)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(out_html)
    # Sidecar: written every run so it can never drift from the hash the page asks
    # for, but byte-identical between runs, so the browser cache keeps working.
    plan_path = os.path.join(os.path.dirname(a.out) or ".", "plan.json")
    with open(plan_path, "w", encoding="utf-8") as f:
        f.write(plan_blob)
    print("wrote %s (%d bytes) + plan.json (%d bytes); rows: f1=%d f3=%d f4=%d f2=%d%s"
          % (a.out, len(out_html), len(plan_blob),
             len(data.get("f1", [])), len(data.get("f3", [])),
             len(data.get("f4", [])), len(data.get("f2", [])), " [SAMPLE]" if a.sample else ""))


if __name__ == "__main__":
    main()
