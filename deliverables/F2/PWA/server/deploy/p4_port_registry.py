#!/usr/bin/env python3
r"""P4 registry + config cutover engine (F2-Prod-Migration-Plan §3 P4).

Runs ON the box at /opt/f2-postgres-migration/p4_port_registry.py, next to the
mirror poller, and REUSES the poller's proven primitives verbatim (import, not
copy): the HMAC admin-envelope RPC client, the docker-exec MySQL channel, and
the injection-proof hex-literal encoders. Secrets come from /opt/f2sync/.env —
the same three names the poller uses (APPS_SCRIPT_URL, APPS_SCRIPT_HMAC,
MYSQL_ROOT_PASSWORD). Nothing new is minted, nothing transits chat.

Phases (invoked in order by p4-box-steps.sh; every phase is re-runnable, and
preflight/facilities are FLIP-AWARE so a failed run can be resumed with the
same one-line ssh command):

  preflight    Row-count snapshot (Sheet totals via admin RPCs vs MySQL) +
               schema assertions (uq_qn unique index, facility_type/barangay
               columns) + WIDTH/SHAPE SCAN of the registry rows about to be
               ported (oversize identifiers — e.g. the documented 301-char
               hcw_id incident — and malformed qn are surfaced HERE, before
               anything mutates). Read-only. Post-flip re-run: skips the
               legacy facilities GET and checks f2_facility_master instead.
  facilities   Export FacilityMasterList via the LEGACY signed GET (the only
               reader; it is kill_switch-GATED, so this runs pre-flip) and
               upsert csweb_f2.f2_facility_master — all 7 sheet columns incl.
               barangay. Post-flip re-run: no-op if already exported.
  flip         admin_config_set kill_switch=true on the SHEET, then prove the
               public path is dead (legacy config GET returns E_KILL_SWITCH)
               and the admin envelope is still alive (admin_config_get works).
  counts-gate  Sheet admin_count_responses == MySQL COUNT(*) f2_responses.
               Run AFTER the final --backfill, and AGAIN at the end of the box
               run as the closing tripwire. The ±0 gate.
  port         Sheet→MySQL port: f2_hcws (qn zero-repadded — Sheets numeric
               coercion strips the leading zero of region-0x facility codes;
               dupes collapsed keep-NEWEST), f2_users (PBKDF2 hashes
               verbatim), f2_roles, f2_config (kill_switch FORCED 'false' in
               MySQL — the new stack must accept submits while the old one
               refuses), f2_files metadata, f2_settings, f2_dlq, f2_audit
               (guarded by an auth_kv marker, NOT by row count — f2-api may
               legitimately have written audit rows already). Chunked upserts
               (500 rows/stmt, packet-safe) with the poller's per-row poison
               isolation.
  canary       Heal any stranded canary rows, mint a device JWT inside the
               f2-api container, POST a canary submit to the public origin,
               assert the row lands in MySQL, assert the Sheet total did NOT
               move, then delete the canary row. "Lands ONLY in MySQL."
  unflip       ROLLBACK helper: Sheet kill_switch=false AND MySQL
               kill_switch=true — single write authority is preserved in BOTH
               directions (f2-api gates /exec on f2_config.kill_switch, AS
               Router parity). Re-add the poller cron by hand — printed.

Residual risks accepted by design (documented, Carl-gated):
  - The old Worker's admin envelope stays writable post-flip (paper-encode,
    DLQ replay) until P6 — kill_switch cannot gate it without breaking the
    rollback path. Controls: admins are ~3 known people, old portal is
    read-only BY POLICY from the flip, the end-of-run + pre-P6 counts-gate
    re-runs detect any drift, and encoding is not active pre-pretest.
  - Files nested under a soft-deleted folder are invisible to the metadata
    walk (no R2 list on wrangler 3.114) — reconcile the bucket via the CF
    dashboard before deleting it at P6.
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sync_f2_to_mysql as base  # the poller: call_admin, mysql, _lit_* etc.

# JSON.stringify emits raw UTF-8; python's default ensure_ascii=True would
# \uXXXX-escape non-ASCII (e.g. a legacy 'Niño' folder name) and diverge the
# HMAC canonical string -> E_SIG_INVALID. Byte-equal for all-ASCII payloads,
# so the poller's own behavior is unchanged elsewhere.
base.stable_json = lambda payload: json.dumps(
    payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

import hashlib
import hmac as hmac_mod

import requests

DB = "csweb_f2"
CANARY_FACILITY = "P4CANARY"
PAGE = 500
CHUNK = 500          # rows per INSERT statement (max_allowed_packet safety)
AUDIT_MARKER = "p4:audit_imported"

# column width contract (target DDL) checked in the preflight scan
WIDTHS = {
    "f2_hcws": {"hcw_id": 64, "facility_id": 64, "facility_name": 255,
                "enrollment_token_jti": 64, "status": 32, "qn": 16},
    "f2_users": {"username": 32, "first_name": 64, "last_name": 64,
                 "role_name": 64, "password_hash": 191, "email": 191,
                 "phone": 64, "created_by": 32},
    "f2_config": {"k": 64, "v": 512},
}


# --- tiny typed encoders on top of the poller's literal builders ---------------
def _s(v, blank_null=False, default=""):
    """Any sheet cell -> MySQL string literal. Numbers/bools re-stringified."""
    if v is None or v == "":
        return "NULL" if blank_null else base._lit_str(default)
    if isinstance(v, bool):
        return base._lit_str("true" if v else "false")
    if isinstance(v, float) and v.is_integer():
        return base._lit_str(str(int(v)))  # Sheets numeric ids arrive as floats
    return base._lit_str(str(v) if not isinstance(v, str) else v)


def _ts(v):
    return base._lit_ts(v if v not in (None, "") else None)


def _b01(v, default=0):
    """TRUE/'true'/1/'1' -> 1; FALSE/''/0 -> 0 (or default when blank)."""
    if v in (None, ""):
        return str(default)
    if isinstance(v, bool):
        return "1" if v else "0"
    s = str(v).strip().lower()
    return "1" if s in ("true", "1", "yes") else "0"


def _i(v, default=0):
    return base._lit_int(v, default=default)


def _fixed_digits(v, width, what, errors, ctx):
    """Fixed-width numeric identifier from a sheet cell, repairing Sheets'
    numeric coercion: a cell like '040340002001' stored without a text format
    comes back as the NUMBER 40340002001 (leading zero gone). Numeric-typed
    values are zfill'ed back to width; string values keep their zeros and must
    already be the right shape. Returns the repaired string or None (blank);
    malformed values are appended to `errors` (caller aborts loudly)."""
    if v in (None, ""):
        return None
    if isinstance(v, (int, float)):
        s = str(int(v))
        if len(s) < width:
            s = s.zfill(width)
        if len(s) != width:
            errors.append("%s: numeric %s %r -> %r is not %d digits" % (ctx, what, v, s, width))
            return s
        return s
    s = str(v).strip()
    if re.fullmatch(r"\d+", s) and len(s) != width:
        errors.append("%s: string %s %r is all-digits but not %d wide" % (ctx, what, s, width))
    return s


def mysql_val(pw, sql):
    rows = base.mysql(pw, sql, want_rows=True)
    return rows[0][0] if rows and rows[0] else ""


def upsert(pw, table, cols, value_rows, update_cols=None):
    """Chunked idempotent upsert with the poller's poison-row isolation: a
    failing chunk is retried row-by-row so ONE bad row can't sink the port;
    hard failures are collected and reported together (then raised)."""
    if not value_rows:
        return 0
    update_cols = update_cols or [c for c in cols]
    sets = ", ".join("%s=VALUES(%s)" % (c, c) for c in update_cols)

    def stmt(rows):
        return ("INSERT INTO %s (%s) VALUES %s ON DUPLICATE KEY UPDATE %s;"
                % (table, ", ".join(cols), ",".join(rows), sets))

    written, failures = 0, []
    for i in range(0, len(value_rows), CHUNK):
        chunk = value_rows[i:i + CHUNK]
        try:
            base.mysql(pw, stmt(chunk))
            written += len(chunk)
        except RuntimeError:
            for vr in chunk:   # isolate the poison row(s)
                try:
                    base.mysql(pw, stmt([vr]))
                    written += 1
                except RuntimeError as e:
                    failures.append("%s | row=%.160s" % (e, vr))
    if failures:
        for f in failures:
            print("  ROW FAILED [%s]: %s" % (table, f))
        raise SystemExit("%s: %d row(s) failed to upsert — fix the sheet rows "
                         "(or widths) and re-run this phase" % (table, len(failures)))
    return written


# --- AS RPC helpers -------------------------------------------------------------
def rpc(cfg, action, payload):
    url = base.require(cfg, "APPS_SCRIPT_URL", "F2_AS_URL")
    secret = base.require(cfg, "APPS_SCRIPT_HMAC", "F2_AS_HMAC")
    return base.call_admin(url, secret, action, payload)


def rpc_paged(cfg, action, extra=None):
    """Drain a rows/total/has_more paginated admin RPC."""
    out, offset = [], 0
    while True:
        payload = dict(extra or {})
        payload.update({"limit": PAGE, "offset": offset})
        data = rpc(cfg, action, payload)
        rows = data.get("rows", []) or []
        out.extend(rows)
        if not data.get("has_more"):
            return out, int(data.get("total", len(out)))
        offset += PAGE


def rpc_total(cfg, action):
    """Total row count from a paginated RPC without draining it."""
    return int(rpc(cfg, action, {"limit": 1, "offset": 0}).get("total", -1))


# DEPLOYED-AS REALITY (probed 2026-07-09): the prod bundle predates
# adminConfigGet/adminConfigSet — admin_config_get/set return E_ACTION_UNKNOWN
# ("not loaded"). Every OTHER port RPC is live. So config reads fall back to
# the legacy signed GET (pre-flip only — it is kill_switch-gated), and the
# flip/unflip fall back to a MANUAL F2_Config cell edit that the engine
# instructs, polls for, and verifies.
def _config_rpc_available(e):
    return "E_ACTION_UNKNOWN" not in str(e)


def capture_config(cfg):
    """All F2_Config keys as {k: 'string'} — admin_config_get when deployed,
    else the legacy config GET (handleConfig coerces booleans; un-coerce).
    Returns None when neither path can serve (post-flip on the old bundle)."""
    try:
        return dict(rpc(cfg, "admin_config_get", {}).get("config", {}))
    except RuntimeError as e:
        if _config_rpc_available(e):
            raise
    env = legacy_get(cfg, "config")
    if not env.get("ok"):
        return None   # E_KILL_SWITCH: post-flip, old bundle — no config read path
    out = {}
    for k, v in (env.get("data") or {}).items():
        out[k] = ("true" if v else "false") if isinstance(v, bool) else str(v)
    return out


def sheet_kill_switch(cfg):
    try:
        return rpc(cfg, "admin_config_get", {}).get("config", {}).get("kill_switch")
    except RuntimeError as e:
        if _config_rpc_available(e):
            raise
    env = legacy_get(cfg, "config")
    if env.get("ok"):
        v = (env.get("data") or {}).get("kill_switch")
        return ("true" if v else "false") if isinstance(v, bool) else str(v)
    if (env.get("error") or {}).get("code") == "E_KILL_SWITCH":
        return "true"
    raise RuntimeError("cannot determine sheet kill_switch: %r" % env)


def legacy_get(cfg, action):
    """Signed LEGACY GET (?action=&ts=&sig=). ts is MILLISECONDS (Auth.js:12-14
    compares against Date.now()). Canonical: 'GET|<action>|<ts>|' (empty body).
    Returns the parsed envelope WITHOUT raising on ok:false (callers assert)."""
    url = base.require(cfg, "APPS_SCRIPT_URL", "F2_AS_URL")
    secret = base.require(cfg, "APPS_SCRIPT_HMAC", "F2_AS_HMAC")
    ts = str(int(time.time() * 1000))
    canonical = "GET|%s|%s|" % (action, ts)
    sig = hmac_mod.new(secret.encode(), canonical.encode(), hashlib.sha256).hexdigest()
    r = requests.get(url, params={"action": action, "ts": ts, "sig": sig},
                     timeout=90)  # AS /exec 302-redirects; requests follows
    r.raise_for_status()
    return r.json()


def _fetch_hcws_deduped(cfg):
    """F2_HCWs rows, newest-first from the RPC, collapsed to one row per hcw_id
    KEEPING THE NEWEST (revoke->re-create legally leaves an older revoked row
    with the same hcw_id on the sheet; last-tuple-wins in a multi-row upsert
    would otherwise resurrect the stale revoked row)."""
    rows, total = rpc_paged(cfg, "admin_hcws_list")
    by_id, shadowed = {}, []
    for r in rows:                      # newest first: first occurrence wins
        hid = str(r.get("hcw_id") or "")
        if hid in by_id:
            shadowed.append(hid)
        else:
            by_id[hid] = r
    return list(by_id.values()), total, shadowed


# --- phases ---------------------------------------------------------------------
def phase_preflight(cfg, pw):
    print("== P4 preflight (read-only) ==")
    problems = []
    flipped = sheet_kill_switch(cfg) == "true"
    if flipped:
        print("NOTE: Sheet kill_switch is ALREADY true — post-flip resume mode "
              "(legacy-GET checks are skipped).")

    # Sheet-side totals via admin envelope (total-only reads; nothing drained)
    sheet_resp = int(rpc(cfg, "admin_count_responses", {}).get("total", -1))
    users = rpc(cfg, "admin_users_list", {}).get("users", [])
    roles = rpc(cfg, "admin_roles_list", {}).get("roles", [])
    cfg_keys = capture_config(cfg) or {}
    if not cfg_keys and not flipped:
        problems.append("could not read F2_Config by any path pre-flip")
    files_root = rpc(cfg, "admin_files_list", {}).get("files", [])
    settings = rpc(cfg, "admin_settings_list", {}).get("settings", [])
    dlq_total = rpc_total(cfg, "admin_read_dlq")
    audit_total = rpc_total(cfg, "admin_read_audit")

    if flipped:
        fac_n = int(mysql_val(pw, "SELECT COUNT(*) FROM f2_facility_master;"))
        print("facilities: legacy GET unavailable post-flip; f2_facility_master=%d" % fac_n)
        if fac_n == 0:
            problems.append("post-flip resume but f2_facility_master is EMPTY — "
                            "facilities were never exported; run `unflip`, then "
                            "restart the box steps from the top")
    else:
        fac = legacy_get(cfg, "facilities")
        fac_n = len(fac.get("data", {}).get("facilities", [])) if fac.get("ok") else -1
        if not fac.get("ok"):
            problems.append("legacy facilities GET failed pre-flip: %s" % fac.get("error"))

    # WIDTH/SHAPE SCAN — surface poison rows BEFORE anything mutates.
    hcws, hcws_total, shadowed = _fetch_hcws_deduped(cfg)
    shape_errors = []
    for r in hcws:
        hid = str(r.get("hcw_id") or "?")
        _fixed_digits(r.get("qn"), 12, "qn", shape_errors, "hcw %s" % hid)
        for col, w in WIDTHS["f2_hcws"].items():
            v = r.get(col)
            if v not in (None, "") and len(str(v)) > w:
                shape_errors.append("hcw %s: %s length %d > VARCHAR(%d)"
                                    % (hid, col, len(str(v)), w))
    for u in users:
        un = str(u.get("username") or "?")
        for col, w in WIDTHS["f2_users"].items():
            v = u.get(col)
            if v not in (None, "") and len(str(v)) > w:
                shape_errors.append("user %s: %s length %d > VARCHAR(%d)"
                                    % (un, col, len(str(v)), w))
    for k, v in cfg_keys.items():
        if len(str(v)) > WIDTHS["f2_config"]["v"]:
            shape_errors.append("config %s: value length %d > VARCHAR(512)" % (k, len(str(v))))
    if shadowed:
        print("note: %d duplicate hcw_id sheet row(s) will collapse keep-newest: %s"
              % (len(shadowed), sorted(set(shadowed))))
    problems.extend(shape_errors)

    print("sheet: responses=%d hcws=%d users=%d roles=%d config_keys=%d "
          "files_root=%d settings=%d dlq=%d audit=%d facilities=%d"
          % (sheet_resp, hcws_total, len(users), len(roles), len(cfg_keys),
             len(files_root), len(settings), dlq_total, audit_total, fac_n))
    print("sheet kill_switch=%r" % cfg_keys.get("kill_switch"))

    # MySQL side
    my = {}
    for t in ("f2_responses", "f2_hcws", "f2_users", "f2_roles", "f2_config",
              "f2_files", "f2_settings", "f2_dlq", "f2_audit", "f2_facility_master"):
        my[t] = int(mysql_val(pw, "SELECT COUNT(*) FROM %s;" % t))
    print("mysql: " + " ".join("%s=%d" % kv for kv in sorted(my.items())))

    # Schema assertions
    uq = mysql_val(pw, "SELECT COUNT(*) FROM information_schema.statistics "
                       "WHERE table_schema='%s' AND table_name='f2_hcws' "
                       "AND index_name='uq_qn' AND non_unique=0;" % DB)
    if uq == "0":
        problems.append("f2_hcws.uq_qn UNIQUE index missing — apply: "
                        "ALTER TABLE f2_hcws DROP INDEX ix_qn, ADD UNIQUE KEY uq_qn (qn);")
    for col in ("facility_type", "barangay"):
        n = mysql_val(pw, "SELECT COUNT(*) FROM information_schema.columns "
                          "WHERE table_schema='%s' AND table_name='f2_facility_master' "
                          "AND column_name='%s';" % (DB, col))
        if n == "0":
            problems.append("f2_facility_master.%s missing — the box-steps ALTER "
                            "should have added it before this phase" % col)
    if not users:
        problems.append("admin_users_list returned 0 users — nothing to port; "
                        "the new admin portal would have no logins")

    if problems:
        print("PREFLIGHT PROBLEMS:")
        for p in problems:
            print("  - " + p)
        sys.exit(1)
    print("preflight OK")


def phase_facilities(cfg, pw):
    print("== P4 facilities export (pre-flip; legacy GET is kill_switch-gated) ==")
    if sheet_kill_switch(cfg) == "true":
        n = int(mysql_val(pw, "SELECT COUNT(*) FROM f2_facility_master;"))
        if n > 0:
            print("post-flip resume: f2_facility_master already has %d row(s) — skipping" % n)
            return
        raise SystemExit("kill_switch already true but f2_facility_master is empty — "
                         "run `unflip` first, then restart from the top")
    env = legacy_get(cfg, "facilities")
    if not env.get("ok"):
        raise SystemExit("facilities GET failed: %s" % env.get("error"))
    rows = env["data"]["facilities"]
    cols = ["facility_id", "facility_name", "facility_type", "region",
            "province", "city_mun", "barangay"]
    errors, vals, ported_ids = [], [], []
    for r in rows:
        fid = _fixed_digits(r.get("facility_id"), 9, "facility_id", errors,
                            "facility %r" % r.get("facility_name"))
        ported_ids.append(fid or "")
        vals.append("(%s)" % ",".join([
            base._lit_str(fid or ""), _s(r.get("facility_name")),
            _s(r.get("facility_type")), _s(r.get("region")),
            _s(r.get("province")), _s(r.get("city_mun")), _s(r.get("barangay")),
        ]))
    if errors:
        for e in errors:
            print("  SHAPE: " + e)
        raise SystemExit("facility_id shape errors — fix the sheet and re-run")
    n = upsert(pw, "f2_facility_master", cols, vals)
    missing = [fid for fid in ported_ids
               if mysql_val(pw, "SELECT COUNT(*) FROM f2_facility_master WHERE facility_id=%s;"
                            % base._lit_str(fid)) == "0"]
    if missing:
        raise SystemExit("facilities missing after upsert: %s" % missing)
    print("facilities: sheet=%d upserted=%d presence=all OK" % (len(rows), n))
    # Port f2_config HERE too (pre-flip): on the deployed old bundle the only
    # config reader is the kill_switch-gated legacy GET, so post-flip the port
    # phase can only VERIFY what this pre-flip write already landed.
    _port_config(cfg, pw)


def _await_kill_switch(cfg, want_blocked, minutes=15):
    """Poll the legacy config GET until the public router reaches the wanted
    state (blocked=E_KILL_SWITCH / serving=ok). The AS reads F2_Config live on
    every request, so a manual cell edit takes effect on the next poll."""
    deadline = time.time() + minutes * 60
    while time.time() < deadline:
        env = legacy_get(cfg, "config")
        blocked = (not env.get("ok")
                   and (env.get("error") or {}).get("code") == "E_KILL_SWITCH")
        if blocked == want_blocked:
            return
        print("  ... public router still %s; polling (edit the cell now)"
              % ("serving" if want_blocked else "blocked"), flush=True)
        time.sleep(10)
    raise SystemExit("timed out (%d min) waiting for the kill_switch cell edit — "
                     "nothing mutated; re-run this phase when ready" % minutes)


def phase_flip(cfg, pw):
    print("== P4 flip: kill_switch=true on the SHEET (old stack refuses writes) ==")
    if sheet_kill_switch(cfg) == "true":
        print("flip: sheet kill_switch already true — verifying only")
    else:
        try:
            out = rpc(cfg, "admin_config_set", {"key": "kill_switch", "value": "true"})
            if str(out.get("value")) != "true":
                raise SystemExit("admin_config_set did not confirm: %r" % out)
        except RuntimeError as e:
            if _config_rpc_available(e):
                raise
            # Deployed bundle predates admin_config_set: manual cell edit.
            print("", flush=True)
            print(">>> MANUAL STEP (deployed AS has no admin_config_set):", flush=True)
            print(">>> Open the F2 backend spreadsheet -> F2_Config tab ->", flush=True)
            print(">>> set the `kill_switch` row's value to: true", flush=True)
            print(">>> This script polls every 10s (up to 15 min) and continues", flush=True)
            print(">>> automatically once the public router starts refusing.", flush=True)
            _await_kill_switch(cfg, want_blocked=True)
    # prove the PUBLIC path is dead (legacy GET config now refuses)
    env = legacy_get(cfg, "config")
    code = (env.get("error") or {}).get("code")
    if env.get("ok") or code != "E_KILL_SWITCH":
        raise SystemExit("legacy config GET should be E_KILL_SWITCH, got: %r" % env)
    # admin envelope must still be alive (the port depends on it)
    if int(rpc(cfg, "admin_count_responses", {}).get("total", -1)) < 0:
        raise SystemExit("admin envelope not responding post-flip")
    print("flip OK: sheet kill_switch=true; public router returns E_KILL_SWITCH; "
          "admin envelope still alive")


def phase_counts_gate(cfg, pw):
    print("== P4 counts gate ==")
    sheet = int(rpc(cfg, "admin_count_responses", {}).get("total", -1))
    mysql_n = int(mysql_val(pw, "SELECT COUNT(*) FROM f2_responses;"))
    print("responses: sheet=%d mysql=%d" % (sheet, mysql_n))
    if sheet != mysql_n:
        raise SystemExit(
            "counts gate FAILED (must match ±0).\n"
            "  mysql>sheet: a new-stack submit or stranded canary exists — inspect\n"
            "    SELECT client_submission_id, facility_id, submitted_at_server\n"
            "    FROM f2_responses ORDER BY id DESC LIMIT 10;\n"
            "  sheet>mysql: something wrote the Sheet AFTER the final backfill —\n"
            "    most likely a paper-encode/DLQ-replay on the OLD admin portal\n"
            "    (the admin envelope is not kill_switch-gated). Re-run the final\n"
            "    backfill (flock ... sync_f2_to_mysql.py --backfill) and re-gate.")
    print("counts gate OK (±0)")


def _port_hcws(cfg, pw):
    rows, total, shadowed = _fetch_hcws_deduped(cfg)
    if shadowed:
        print("  f2_hcws: collapsing %d duplicate hcw_id row(s) keep-newest: %s"
              % (len(shadowed), sorted(set(shadowed))))
    cols = ["hcw_id", "facility_id", "facility_name", "enrollment_token_jti",
            "token_issued_at", "token_revoked_at", "status", "created_at", "qn"]
    errors, vals = [], []
    for r in rows:
        hid = str(r.get("hcw_id") or "?")
        qn = _fixed_digits(r.get("qn"), 12, "qn", errors, "hcw %s" % hid)
        fid = r.get("facility_id")
        # facility_id: repair numeric coercion to 9 digits; legacy slug strings pass through
        if isinstance(fid, (int, float)):
            fid = _fixed_digits(fid, 9, "facility_id", errors, "hcw %s" % hid)
        status = r.get("status")
        vals.append("(%s)" % ",".join([
            _s(r.get("hcw_id")),
            _s(fid, blank_null=True),
            _s(r.get("facility_name"), blank_null=True),
            _s(r.get("enrollment_token_jti"), blank_null=True),
            _ts(r.get("token_issued_at")), _ts(r.get("token_revoked_at")),
            _s(status if status not in (None, "") else "pending"),
            _ts(r.get("created_at")),
            base._lit_str(qn) if qn else "NULL",   # blank qn MUST be NULL (uq_qn)
        ]))
    if errors:
        for e in errors:
            print("  SHAPE: " + e)
        raise SystemExit("f2_hcws qn/facility_id shape errors — fix and re-run")
    upsert(pw, "f2_hcws", cols, vals)
    bad = mysql_val(pw, "SELECT COUNT(*) FROM f2_hcws WHERE qn IS NOT NULL AND "
                        "qn NOT REGEXP '^[0-9]{12}$';")
    if bad != "0":
        raise SystemExit("f2_hcws holds %s non-12-digit qn value(s) after port" % bad)
    return "f2_hcws", len(vals), total, "exact(deduped)"


def _port_users(cfg, pw):
    users = rpc(cfg, "admin_users_list", {"include_password_hash": True}).get("users", [])
    nohash = [u.get("username") for u in users if not u.get("password_hash")]
    if nohash:
        raise SystemExit("users without password_hash in export (include flag "
                         "ignored?): %s — refusing to port lockout rows" % nohash)
    cols = ["username", "first_name", "last_name", "role_name", "password_hash",
            "password_must_change", "email", "phone", "created_at", "created_by",
            "last_login_at"]
    vals = []
    for u in users:
        vals.append("(%s)" % ",".join([
            _s(u.get("username")), _s(u.get("first_name")), _s(u.get("last_name")),
            _s(u.get("role_name")), _s(u.get("password_hash")),
            _b01(u.get("password_must_change"), default=0),
            _s(u.get("email")), _s(u.get("phone")),
            _ts(u.get("created_at")), _s(u.get("created_by")),
            _ts(u.get("last_login_at")),
        ]))
    upsert(pw, "f2_users", cols, vals)
    return "f2_users", len(users), len(users), "exact"


def _port_roles(cfg, pw):
    roles = rpc(cfg, "admin_roles_list", {}).get("roles", [])
    flags = ["dash_data", "dash_report", "dash_apps", "dash_users", "dash_roles",
             "dict_self_admin_up", "dict_self_admin_down", "dict_paper_encoded_up",
             "dict_paper_encoded_down", "dict_capi_up", "dict_capi_down"]
    cols = ["name", "is_builtin", "version"] + flags + ["created_at", "created_by"]
    vals = []
    for r in roles:
        cells = [_s(r.get("name")), _b01(r.get("is_builtin")), _i(r.get("version"), 1)]
        cells += [_b01(r.get(f)) for f in flags]
        cells += [_ts(r.get("created_at")), _s(r.get("created_by"))]
        vals.append("(%s)" % ",".join(cells))
    upsert(pw, "f2_roles", cols, vals)   # sheet truth overwrites the DDL seed
    missing = [r.get("name") for r in roles
               if mysql_val(pw, "SELECT COUNT(*) FROM f2_roles WHERE name=%s;"
                            % _s(r.get("name"))) == "0"]
    if missing:
        raise SystemExit("roles missing after upsert: %s" % missing)
    return "f2_roles", len(roles), len(roles), "presence"


def _port_config(cfg, pw):
    conf = capture_config(cfg)
    if conf is None:
        # Post-flip on the old bundle: no config read path. The pre-flip port
        # (phase_facilities) already landed the values — verify, don't write.
        nkeys = int(mysql_val(pw, "SELECT COUNT(*) FROM f2_config;"))
        ks = mysql_val(pw, "SELECT v FROM f2_config WHERE k='kill_switch';")
        if nkeys < 5 or ks != "false":
            raise SystemExit("post-flip config VERIFY failed (keys=%d, kill_switch=%r) "
                             "— the pre-flip config port did not land" % (nkeys, ks))
        print("  f2_config: post-flip verify — %d keys present, kill_switch=false" % nkeys)
        return "f2_config", nkeys, nkeys, "verified(pre-flip port)"
    vals = []
    for k, v in sorted(conf.items()):
        if k == "kill_switch":
            v = "false"   # the NEW stack must accept submits — never port 'true'
        vals.append("(%s,%s)" % (_s(k), _s(v)))
    upsert(pw, "f2_config", ["k", "v"], vals, update_cols=["v"])
    ks = mysql_val(pw, "SELECT v FROM f2_config WHERE k='kill_switch';")
    if ks != "false":
        raise SystemExit("MySQL f2_config.kill_switch=%r — must be 'false'" % ks)
    print("  f2_config: %d keys ported (kill_switch forced false)" % len(conf))
    return "f2_config", len(conf), len(conf), "presence(kill_switch forced false)"


def _port_files(cfg, pw):
    root = rpc(cfg, "admin_files_list", {}).get("files", [])
    all_rows = {str(r.get("file_id")): r for r in root}
    for r in root:
        if r.get("is_folder") in (True, "true"):
            kids = rpc(cfg, "admin_files_list",
                       {"path": "/" + str(r.get("filename"))}).get("files", [])
            for k in kids:
                all_rows[str(k.get("file_id"))] = k
    rows = list(all_rows.values())
    cols = ["file_id", "filename", "content_type", "size_bytes", "uploaded_by",
            "uploaded_at", "description", "deleted_at", "folder_path", "is_folder"]
    vals = []
    for r in rows:
        vals.append("(%s)" % ",".join([
            _s(r.get("file_id")), _s(r.get("filename")),
            _s(r.get("content_type"), default="application/octet-stream"),
            _i(r.get("size_bytes"), 0), _s(r.get("uploaded_by")),
            _ts(r.get("uploaded_at")), _s(r.get("description")),
            "NULL",                                   # soft-deleted rows not exported
            _s(r.get("folder_path"), default="/"),
            _b01(r.get("is_folder")),
        ]))
    upsert(pw, "f2_files", cols, vals)
    return "f2_files", len(rows), len(rows), "exact(live rows; soft-deleted stay on Sheet)"


def _port_settings(cfg, pw):
    rows = rpc(cfg, "admin_settings_list", {}).get("settings", [])
    cols = ["setting_id", "instrument", "included_columns", "interval_minutes",
            "next_run_at", "output_path_template", "last_run_at",
            "last_run_status", "last_run_error", "enabled", "created_by", "created_at"]
    vals = []
    for r in rows:
        inc = r.get("included_columns")
        inc_lit = base._lit_str(json.dumps(inc, ensure_ascii=False)
                                if isinstance(inc, list) else (inc or "[]"))
        vals.append("(%s)" % ",".join([
            _s(r.get("setting_id")), _s(r.get("instrument"), default="F2"), inc_lit,
            _i(r.get("interval_minutes"), 60), _ts(r.get("next_run_at")),
            _s(r.get("output_path_template")), _ts(r.get("last_run_at")),
            _s(r.get("last_run_status")), _s(r.get("last_run_error")),
            _b01(r.get("enabled"), default=1), _s(r.get("created_by")),
            _ts(r.get("created_at")),
        ]))
    upsert(pw, "f2_settings", cols, vals)
    return "f2_settings", len(rows), len(rows), "exact"


def _port_dlq(cfg, pw):
    rows, total = rpc_paged(cfg, "admin_read_dlq")
    cols = ["dlq_id", "received_at_server", "client_submission_id", "reason", "payload_json"]
    vals = []
    for r in rows:
        vals.append("(%s)" % ",".join([
            _s(r.get("dlq_id")), _ts(r.get("received_at_server")),
            _s(r.get("client_submission_id"), blank_null=True),
            _s(r.get("reason")), base._lit_json(r.get("payload_json")),
        ]))
    upsert(pw, "f2_dlq", cols, vals)
    return "f2_dlq", len(rows), total, "exact"


def _port_audit(cfg, pw):
    """Guarded by an auth_kv MARKER, not by row count: f2-api legitimately
    writes f2_audit (admin_login etc.), so 'rows exist' does NOT mean 'sheet
    already imported'. The sheet history is appended alongside live rows;
    the gate checks the DELTA."""
    marked = mysql_val(pw, "SELECT COUNT(*) FROM auth_kv WHERE k=%s;"
                       % base._lit_str(AUDIT_MARKER))
    if marked != "0":
        n = int(mysql_val(pw, "SELECT COUNT(*) FROM f2_audit;"))
        print("  f2_audit: import marker present — already imported, skipping (rows=%d)" % n)
        return "f2_audit", 0, n, "skipped(marker)"
    before = int(mysql_val(pw, "SELECT COUNT(*) FROM f2_audit;"))
    rows, total = rpc_paged(cfg, "admin_read_audit")
    cols = ["audit_id", "occurred_at_server", "occurred_at_client", "event_type",
            "hcw_id", "facility_id", "app_version", "payload_json",
            "actor_username", "actor_jti", "actor_role", "event_resource",
            "event_payload_json", "client_ip_hash", "request_id"]
    vals = []
    for r in rows:
        vals.append("(%s)" % ",".join([
            _s(r.get("audit_id"), blank_null=True), _ts(r.get("occurred_at_server")),
            _s(r.get("occurred_at_client"), blank_null=True),
            _s(r.get("event_type"), default="unknown"),
            _s(r.get("hcw_id"), blank_null=True), _s(r.get("facility_id"), blank_null=True),
            _s(r.get("app_version"), blank_null=True),
            _s(r.get("payload_json"), blank_null=True),
            _s(r.get("actor_username"), blank_null=True),
            _s(r.get("actor_jti"), blank_null=True),
            _s(r.get("actor_role"), blank_null=True),
            _s(r.get("event_resource"), blank_null=True),
            _s(r.get("event_payload_json"), blank_null=True),
            _s(r.get("client_ip_hash"), blank_null=True),
            _s(r.get("request_id"), blank_null=True),
        ]))
    for i in range(0, len(vals), CHUNK):    # packet-safe plain INSERT (surrogate PK)
        chunk = vals[i:i + CHUNK]
        base.mysql(pw, "INSERT INTO f2_audit (%s) VALUES %s;"
                   % (", ".join(cols), ",".join(chunk)))
    after = int(mysql_val(pw, "SELECT COUNT(*) FROM f2_audit;"))
    if after - before != len(vals):
        raise SystemExit("f2_audit delta %d != imported %d" % (after - before, len(vals)))
    base.mysql(pw, "INSERT INTO auth_kv (k, v) VALUES (%s, %s) "
                   "ON DUPLICATE KEY UPDATE v=VALUES(v);"
               % (base._lit_str(AUDIT_MARKER),
                  base._lit_str(dt.datetime.now(dt.timezone.utc).isoformat())))
    return "f2_audit", len(vals), total, "delta(marker set)"


def phase_port(cfg, pw):
    print("== P4 registry port (Sheet → MySQL; admin envelope, immune to kill_switch) ==")
    results = []
    for fn in (_port_hcws, _port_users, _port_roles, _port_config,
               _port_files, _port_settings, _port_dlq, _port_audit):
        results.append(fn(cfg, pw))
    failed = []
    for table, exported, sheet_total, mode in results:
        my = int(mysql_val(pw, "SELECT COUNT(*) FROM %s;" % table))
        note = ""
        if mode.startswith("exact") and my != exported:
            failed.append(table)
            note = "  <-- MISMATCH (did the live f2-api write rows pre-port? investigate)"
        print("  %-12s sheet=%-5s exported=%-5s mysql=%-5s [%s]%s"
              % (table, sheet_total, exported, my, mode, note))
    if failed:
        raise SystemExit("port count gate FAILED for: %s" % failed)
    print("port OK — all registry gates green")


def phase_canary(cfg, pw):
    print("== P4 canary: a submit lands ONLY in MySQL ==")
    # heal any canary stranded by a previous failed run (double-keyed delete)
    stranded = mysql_val(pw, "SELECT COUNT(*) FROM f2_responses WHERE facility_id=%s;"
                         % base._lit_str(CANARY_FACILITY))
    if stranded != "0":
        print("  healing %s stranded canary row(s) from a prior run" % stranded)
        base.mysql(pw, "DELETE FROM f2_responses WHERE facility_id=%s AND "
                       "client_submission_id LIKE 'p4-canary-%%';"
                   % base._lit_str(CANARY_FACILITY))

    sheet_before = int(rpc(cfg, "admin_count_responses", {}).get("total", -1))

    # 1. mint a short-lived device JWT INSIDE the f2-api container (its env
    #    holds JWT_SIGNING_KEY; the key never leaves the box). stdin=DEVNULL:
    #    docker compose exec would otherwise pump OUR stdin — which, under
    #    `ssh 'bash -s' < script`, IS the remainder of the orchestrator script.
    node_js = (
        "const c=require('crypto');const k=Buffer.from(process.env.JWT_SIGNING_KEY,'base64url');"
        "const b=o=>Buffer.from(JSON.stringify(o)).toString('base64url');"
        "const now=Math.floor(Date.now()/1000);"
        "const h=b({alg:'HS256',typ:'JWT'});"
        "const p=b({jti:'p4-canary-'+now,tablet_id:'p4-canary',facility_id:'%s',iat:now,exp:now+900});"
        "const s=c.createHmac('sha256',k).update(h+'.'+p).digest('base64url');"
        "console.log(h+'.'+p+'.'+s);" % CANARY_FACILITY
    )
    tok = subprocess.run(
        ["docker", "compose", "exec", "-T", "f2-api", "node", "-e", node_js],
        cwd="/opt/app", capture_output=True, text=True, timeout=60,
        stdin=subprocess.DEVNULL)
    if tok.returncode != 0:
        raise SystemExit("JWT mint failed: %s" % (tok.stderr or tok.stdout))
    jwt = tok.stdout.strip()

    # 2. canary submit through the real public origin
    spec = mysql_val(pw, "SELECT v FROM f2_config WHERE k='current_spec_version';")
    csid = "p4-canary-" + str(uuid.uuid4())
    body = {"client_submission_id": csid, "spec_version": spec or "2026-07-02-r6",
            "app_version": "p4-gate", "hcw_id": "p4-canary",
            "facility_id": CANARY_FACILITY, "values": {"p4_canary": True}}
    r = requests.post("https://uhc-hcw.asiansocial.org/exec?action=submit",
                      json=body, headers={"Authorization": "Bearer " + jwt}, timeout=30)
    env = r.json()
    if not env.get("ok") or env.get("data", {}).get("status") != "accepted":
        raise SystemExit("canary submit not accepted: HTTP %d %r" % (r.status_code, env))

    # 3. row is in MySQL
    got = mysql_val(pw, "SELECT COUNT(*) FROM f2_responses WHERE client_submission_id=%s;"
                    % base._lit_str(csid))
    if got != "1":
        raise SystemExit("canary row not found in MySQL (count=%s)" % got)

    # 4. the Sheet did NOT move
    sheet_after = int(rpc(cfg, "admin_count_responses", {}).get("total", -1))
    if sheet_after != sheet_before:
        raise SystemExit(
            "Sheet total moved %d -> %d during the canary. Either the canary "
            "leaked to the old stack (bad) or an admin-envelope write (paper-"
            "encode/DLQ-replay on the OLD portal) landed concurrently — check "
            "F2_Audit/F2_Responses tail before concluding." % (sheet_before, sheet_after))

    # 5. remove the canary (double-keyed so nothing else can match)
    base.mysql(pw, "DELETE FROM f2_responses WHERE client_submission_id=%s AND facility_id=%s;"
               % (base._lit_str(csid), base._lit_str(CANARY_FACILITY)))
    left = mysql_val(pw, "SELECT COUNT(*) FROM f2_responses WHERE client_submission_id=%s;"
                     % base._lit_str(csid))
    if left != "0":
        raise SystemExit("canary cleanup failed")
    print("canary OK: accepted at uhc-hcw -> MySQL row -> Sheet unchanged (%d) -> cleaned up"
          % sheet_before)


def phase_unflip(cfg, pw):
    print("== ROLLBACK: Sheet kill_switch=false + MySQL kill_switch=true ==")
    # Single write authority in the rollback direction too: the new stack's
    # /exec gates on f2_config.kill_switch (AS Router parity, added at P4).
    base.mysql(pw, "UPDATE f2_config SET v='true' WHERE k='kill_switch';")
    try:
        rpc(cfg, "admin_config_set", {"key": "kill_switch", "value": "false"})
    except RuntimeError as e:
        if _config_rpc_available(e):
            raise
        print(">>> MANUAL STEP: F2_Config tab -> set `kill_switch` back to: false", flush=True)
        print(">>> Polling until the public router serves again...", flush=True)
        _await_kill_switch(cfg, want_blocked=False)
    env = legacy_get(cfg, "config")
    if not env.get("ok"):
        raise SystemExit("legacy config GET still failing after unflip: %r" % env)
    ks = mysql_val(pw, "SELECT v FROM f2_config WHERE k='kill_switch';")
    print("unflip OK — old stack serves again; new stack refuses writes "
          "(MySQL kill_switch=%s). Re-add the poller cron:" % ks)
    print("  */2 * * * * flock -n /tmp/f2-mysql-sync.lock bash -c 'cd /opt/app && "
          "python3 /opt/f2-postgres-migration/sync_f2_to_mysql.py --env-file "
          "/opt/f2sync/.env' >> /var/log/f2-mysql-sync.log 2>&1")


PHASES = {
    "preflight": phase_preflight,
    "facilities": phase_facilities,
    "flip": phase_flip,
    "counts-gate": phase_counts_gate,
    "port": phase_port,
    "canary": phase_canary,
    "unflip": phase_unflip,
}


def main():
    ap = argparse.ArgumentParser(description="P4 registry+config cutover engine")
    ap.add_argument("phase", choices=sorted(PHASES))
    ap.add_argument("--env-file", default="/opt/f2sync/.env")
    a = ap.parse_args()
    cfg = base.load_env(a.env_file)
    pw = base.require(cfg, "MYSQL_ROOT_PASSWORD", "F2_MYSQL_PW")
    PHASES[a.phase](cfg, pw)


if __name__ == "__main__":
    main()
