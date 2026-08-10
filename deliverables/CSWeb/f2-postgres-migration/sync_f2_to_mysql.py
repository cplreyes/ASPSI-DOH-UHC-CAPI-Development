#!/usr/bin/env python3
r"""Read-mirror poller: F2 Healthcare-Worker (PWA) submissions (Google Sheets
backend) -> MySQL `csweb_f2.f2_responses` on the CSWeb box.

Pulls submissions out of the Apps Script backend via the `admin_read_responses`
RPC and UPSERTs them into MySQL keyed on `client_submission_id`, so the unified
CSWeb Sync Dashboard can read F2 from a REAL database (csweb_f2, beside the
csweb_f1/f3/f4 breakouts) with ZERO change to any live F2 write path. The Sheet
stays the sole source of truth; this job is a pure read + idempotent local upsert.

Why MySQL over docker-exec (not a Python DB driver): the dashboard generator
already reaches the box MySQL as `docker compose exec -T database mysql`, which is
PROVEN on this host and needs no host↔container port publishing and no extra host
package. This poller reuses that exact primitive. Untrusted values (answer-dict
JSON, free-text ids) are passed as MySQL HEX string literals (`_utf8mb4 0x..`) or
reformatted numeric/datetime literals — injection-proof by construction (only hex
digits / validated numbers ever reach the SQL), and byte-exact for multibyte JSON.

Idempotent + re-runnable by construction:
  - UNIQUE(client_submission_id) + INSERT ... ON DUPLICATE KEY UPDATE means re-seen
    rows update in place and a re-run (or an overlapping window) never double-inserts.
  - Reads the terminal store (F2_Responses), so BOTH ingress paths (self-admin PWA
    submit AND paper-encoder) are mirrored by this one mechanism.
  - Batch upsert per page; on any DB error it falls back to per-row so one poison
    row (e.g. malformed values_json) can't drop a whole page — the bad row is logged
    and counted (non-zero exit for cron alerting), never silently dropped, and the
    Sheet remains authoritative.

Modes:
  --backfill        Sweep ALL history (from the Unix epoch). Use once, or to
                    reconcile. Paginates to the AS SCAN_CAP (50000).
  --since VALUE     Incremental. VALUE is an ISO-8601 timestamp, OR 'auto' to derive
                    the watermark from MySQL (max(submitted_at_server) - overlap).
  (neither)         Defaults to `--since auto` (safe cron default).

Auth: the `admin_read_responses` RPC is HMAC-authenticated. The signature is
HMAC-SHA256 over the canonical string `action.ts.request_id.stableJson(payload)`
(ts = unix SECONDS, stableJson = one-level key-sorted compact JSON), POSTed as a
JSON body `{action, ts, request_id, payload, hmac}` with NO `?action=` query param
(that is what routes it to the AS admin-envelope branch). URL + secret from the
environment / an --env-file — NEVER hardcoded.

  SECURITY NOTE (from the migration review): APPS_SCRIPT_HMAC is the AS admin-
  envelope MASTER secret — it can sign ANY admin action, not just reads. Placing a
  copy on the box widens its blast radius (box compromise = admin forge/kill-switch).
  Prefer issuing the box a SCOPED read-only credential the AS side authorizes only
  for `admin_read_responses`, and rotate the shared secret at write-path cutover.
  Carl places the secret value; this script only names the env var.

Secrets (env or --env-file; env wins). Keep the poller's secret file DISJOINT from
the master /opt/app/.env (which also holds MYSQL_ROOT_PASSWORD) — use /opt/f2sync/.env:
  APPS_SCRIPT_URL     Apps Script /exec deployment URL          (alias: F2_AS_URL)
  APPS_SCRIPT_HMAC    the AS admin-envelope secret (see note)   (alias: F2_AS_HMAC)
  MYSQL_ROOT_PASSWORD MySQL password for the docker-exec client (alias: F2_MYSQL_PW)

Deploy (box cron — ONE physical line; cron does NOT honor backslash-newline continuation;
flock-guarded; from /opt/app so `database` resolves):
  */2 * * * * flock -n /tmp/f2-mysql-sync.lock bash -c 'cd /opt/app && python3 /opt/f2-postgres-migration/sync_f2_to_mysql.py --env-file /opt/f2sync/.env' >> /var/log/f2-mysql-sync.log 2>&1

Local dev / dry run (no writes):
  python sync_f2_to_mysql.py --backfill --dry-run --env-file ./.env

Requires: requests (pip install requests) + the docker CLI on PATH. No DB driver.
First written 2026-07-07 (MySQL read-mirror; supersedes the Postgres sync draft).
"""
import os, sys, json, time, uuid, hmac, hashlib, logging, argparse, subprocess, math
import datetime as dt

try:
    import requests
except ImportError as e:  # fail loud with the fix, don't half-run
    raise SystemExit("missing dependency (%s). Install with: pip install requests" % e)

# --- constants pinned from the AS backend (AdminData.js) -------------------------
RPC_ACTION   = "admin_read_responses"
PAGE_DEFAULT = 500      # == MAX_LIMIT on the AS side (AdminData.js:21-33)
SCAN_CAP     = 50000    # AS reads the OLDEST 50000 physical sheet rows THEN filters
                        # (AdminData.js readAll(SCAN_CAP,0)) → rows beyond it are UNREACHABLE by
                        # this RPC. Latent: F2_Responses lifetime is ~30K. See run_sync warning.
OVERLAP_MIN  = 15       # default re-fetch window for --since auto; upsert dedups it
EPOCH_ISO    = "1970-01-01T00:00:00.000Z"
HTTP_TIMEOUT = 90

DB       = "csweb_f2"
TABLE    = "f2_responses"
COMPOSE_DIR = "/opt/app"      # cwd for `docker compose` (same as the dashboard gen)

# --- f2_responses column contract (Schema.js, 18 canonical cols, sheet order) ----
COLS = [
    "submission_id", "client_submission_id", "submitted_at_server", "submitted_at_client",
    "source", "spec_version", "app_version", "hcw_id", "facility_id", "device_fingerprint",
    "sync_attempt_count", "status", "values_json", "submission_lat", "submission_lng",
    "source_path", "encoded_by", "encoded_at",
    # 12-digit Questionnaire Number (2026-07-08 qn rollout; sheet column added by
    # the AS migrateAddQnColumn). Absent on pre-rollout AS rows → NULL in the mirror.
    "qn",
]
# columns that may legitimately change after first sync (everything except the
# conflict key); AS/Sheet is authoritative so we mirror the full row on conflict.
UPDATE_COLS = [c for c in COLS if c != "client_submission_id"]
# which columns are which kind, so we emit the right MySQL literal for each.
TS_COLS  = {"submitted_at_server", "submitted_at_client", "encoded_at"}
NUM_COLS = {"submission_lat", "submission_lng"}
INT_COLS = {"sync_attempt_count"}

log = logging.getLogger("f2-mysql-sync")


# --- config / secrets ------------------------------------------------------------
def load_env(path):
    """Merge KEY=VALUE pairs from an .env file (if present) under the real
    environment (real env wins). Mirrors csweb-dashboard-gen.py's .env reader."""
    cfg = {}
    if path and os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip().strip('"').strip("'")
    cfg.update(os.environ)  # real env overrides the file
    return cfg


def require(cfg, *keys):
    """Return the first present, non-empty value among alias keys, or die."""
    for k in keys:
        if cfg.get(k):
            return cfg[k]
    raise SystemExit("missing required secret: set one of %s (env or --env-file)"
                     % " / ".join(keys))


# --- admin-envelope RPC (identical wire contract to the Worker; do not drift) -----
def stable_json(payload):
    """Mirror the Worker's stableJson: one-level key sort, compact separators (no
    spaces). Admin filters are flat, so recursive sort_keys is byte-equal here --
    KEEP SYNC PAYLOADS FLAT or the HMAC will diverge (client.ts:29-32)."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def call_admin(url, secret, action, payload):
    """Signed POST to the AS admin branch. Raises on transport or envelope error."""
    ts, rid = int(time.time()), str(uuid.uuid4())            # ts = unix SECONDS
    canonical = "%s.%s.%s.%s" % (action, ts, rid, stable_json(payload))
    sig = hmac.new(secret.encode(), canonical.encode(), hashlib.sha256).hexdigest()
    body = json.dumps({"action": action, "ts": ts, "request_id": rid,
                       "payload": payload, "hmac": sig})
    # NO ?action= query param -> routes to the AS admin-envelope branch (Code.js:29-47).
    r = requests.post(url, data=body,
                      headers={"Content-Type": "application/json"},
                      timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    env = r.json()
    if not env.get("ok"):
        raise RuntimeError("AS RPC error: %s" % env.get("error"))
    return env.get("data", {})


# --- MySQL literal encoding (injection-proof) ------------------------------------
def _lit_str(v):
    """Arbitrary text -> a MySQL utf8mb4 hex string literal. Only hex digits reach
    the SQL, so no value can break out of the literal. Empty -> ''; None -> NULL."""
    if v is None:
        return "NULL"
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
    if s == "":
        return "''"
    return "_utf8mb4 0x" + s.encode("utf-8").hex()


def _lit_int(v, default=None):
    try:
        return str(int(v)) if v not in (None, "") else ("NULL" if default is None else str(default))
    except (TypeError, ValueError):
        return "NULL" if default is None else str(default)


def _lit_num(v):
    try:
        if v in (None, ""):
            return "NULL"
        f = float(v)
        # float() parses 'inf'/'Infinity'/'nan'/'1e400' WITHOUT raising; those repr() to the
        # bare tokens inf/-inf/nan which are NOT valid MySQL literals → coerce to NULL.
        return repr(f) if math.isfinite(f) else "NULL"
    except (TypeError, ValueError):
        return "NULL"


def _lit_ts(v):
    """ISO-8601 (or Sheet date string) -> a validated `'YYYY-MM-DD HH:MM:SS'` UTC
    literal, reformatted from parsed components (never the raw string), so injection
    is impossible. Unparseable / blank -> NULL."""
    if v in (None, ""):
        return "NULL"
    s = str(v).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            d = dt.datetime.strptime(s, fmt)
            if d.tzinfo is not None:
                d = d.astimezone(dt.timezone.utc).replace(tzinfo=None)
            return "'" + d.strftime("%Y-%m-%d %H:%M:%S") + "'"
        except ValueError:
            continue
    # ISO with 'Z' and >6 fractional digits, or offset like +08:00 that strptime %z
    # rejects on some builds: fall back to a lenient parse of the leading datetime.
    try:
        d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        if d.tzinfo is not None:
            d = d.astimezone(dt.timezone.utc).replace(tzinfo=None)
        return "'" + d.strftime("%Y-%m-%d %H:%M:%S") + "'"
    except ValueError:
        log.warning("unparseable timestamp %r -> NULL", v)
        return "NULL"


def _lit_json(v):
    """AS may return the answer dict already-parsed OR as a JSON string. Emit a
    utf8mb4 hex literal of the JSON TEXT (MySQL validates it into the JSON column);
    multibyte (n~ / emoji) preserved. Blank -> '{}'."""
    if v is None or v == "":
        return _lit_str("{}")
    if isinstance(v, (dict, list)):
        return _lit_str(json.dumps(v, ensure_ascii=False))
    return _lit_str(v)


def row_values_sql(x):
    """Map one AS row dict -> a MySQL "(v1,v2,...)" VALUES literal matching COLS.
    Returns None if the idempotency key is absent (can't upsert without it)."""
    csid = x.get("client_submission_id")
    if not csid:
        return None
    def cell(col):
        if col == "values_json":
            return _lit_json(x.get("values_json"))
        if col in TS_COLS:
            return _lit_ts(x.get(col))
        if col in NUM_COLS:
            return _lit_num(x.get(col))
        if col in INT_COLS:
            return _lit_int(x.get(col), default=1)         # NOT NULL DEFAULT 1
        # string columns with soft NOT-NULL defaults matching the schema
        if col == "source":       return _lit_str(x.get("source") or "PWA")
        if col == "spec_version": return _lit_str(x.get("spec_version") or "")
        if col == "status":       return _lit_str(x.get("status") or "stored")
        if col == "source_path":  return _lit_str(x.get("source_path") or "self_admin")
        return _lit_str(x.get(col))
    return "(" + ",".join(cell(c) for c in COLS) + ")"


# --- MySQL via docker-exec (same primitive as csweb-dashboard-gen.py) -------------
MYSQL_TIMEOUT = 120     # seconds — bound a wedged docker/mysql so a flock isn't held forever


def mysql(pw, sql, want_rows=False):
    """Run SQL against the box MySQL via `docker compose exec -T database mysql`.
    The password is forwarded via the MYSQL_PWD env (named-only with `-e`, NOT on argv)
    so it never lands in the host/container process table. SQL is fed on STDIN (long
    multi-row upserts are fine). Raises RuntimeError on non-zero exit OR timeout so the
    caller can isolate/report (a hang would otherwise block the poller + hold the flock)."""
    try:
        p = subprocess.run(
            ["docker", "compose", "exec", "-T", "-e", "MYSQL_PWD", "database",
             "mysql", "-uroot", "--batch", "-N", DB],
            input=sql, cwd=COMPOSE_DIR, capture_output=True, text=True,
            timeout=MYSQL_TIMEOUT, env={**os.environ, "MYSQL_PWD": pw})
    except subprocess.TimeoutExpired:
        raise RuntimeError("mysql call timed out after %ds (wedged docker/mysql?)" % MYSQL_TIMEOUT)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout or "mysql exit %d" % p.returncode).strip())
    if p.stderr.strip():
        log.debug("mysql stderr: %s", p.stderr.strip())
    if want_rows:
        return [ln.split("\t") for ln in p.stdout.splitlines() if ln.strip()]
    return p.stdout


def _upsert_sql(value_rows):
    # `synced_at=CURRENT_TIMESTAMP` is appended so re-seeing an unchanged row is a REAL
    # change (affected-rows=2) → the freshness stamp always records last-touch. Without it,
    # a byte-identical ON DUPLICATE KEY UPDATE is a no-op that does NOT fire ON UPDATE, so
    # synced_at would freeze at first-insert time and a MAX(synced_at) heartbeat would lie.
    set_clause = ", ".join("%s=VALUES(%s)" % (c, c) for c in UPDATE_COLS) + ", synced_at=CURRENT_TIMESTAMP"
    return ("INSERT INTO %s (%s) VALUES %s ON DUPLICATE KEY UPDATE %s;"
            % (TABLE, ", ".join(COLS), ",".join(value_rows), set_clause))


def upsert_page(pw, value_rows):
    """Batch upsert; on any DB error fall back to per-row so one poison row can't
    drop a whole page. Returns (written, errors)."""
    if not value_rows:
        return (0, 0)
    try:
        mysql(pw, _upsert_sql(value_rows))
        return (len(value_rows), 0)
    except RuntimeError as e:
        log.warning("batch upsert failed (%s); isolating rows one-by-one", e)
    written = errs = 0
    for vr in value_rows:
        try:
            mysql(pw, _upsert_sql([vr]))
            written += 1
        except RuntimeError as e:
            errs += 1
            log.error("row upsert failed: %s | row=%.120s", e, vr)
    return (written, errs)


# --- watermark -------------------------------------------------------------------
def _iso_z(dtobj):
    """UTC ISO-8601, millisecond precision, 'Z' suffix — mirrors the Sheet's
    Date.toISOString() so the lexical `from` comparison lines up."""
    u = dtobj.astimezone(dt.timezone.utc)
    return u.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (u.microsecond // 1000)


def compute_watermark(pw, overlap_min):
    """max(submitted_at_server) - overlap, as an ISO-Z string. None if table empty
    (caller then does a full backfill). submitted_at_server is stored UTC."""
    rows = mysql(pw, "SELECT COALESCE(DATE_FORMAT(MAX(submitted_at_server),"
                     "'%%Y-%%m-%%dT%%H:%%i:%%s.000Z'),'') FROM %s;" % TABLE, want_rows=True)
    hi = rows[0][0] if rows and rows[0] else ""
    if not hi:
        return None
    try:
        d = dt.datetime.strptime(hi, "%Y-%m-%dT%H:%M:%S.000Z").replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None
    return _iso_z(d - dt.timedelta(minutes=overlap_min))


# --- pagination driver -----------------------------------------------------------
def run_sync(pw, url, secret, frm, to, page_size, dry_run):
    offset = 0
    fetched = tot_w = tot_s = tot_e = pages = 0
    while True:
        payload = {"from": frm, "limit": page_size, "offset": offset}
        if to:
            payload["to"] = to                               # keep payload FLAT (HMAC)
        data = call_admin(url, secret, RPC_ACTION, payload)
        rows = data.get("rows", []) or []
        pages += 1
        fetched += len(rows)

        # build value-literals, drop keyless rows, dedupe within the page (keep last)
        # so a single INSERT can't hit the same unique key twice.
        by_csid, keyless = {}, 0
        for x in rows:
            vr = row_values_sql(x)
            if vr is None:
                keyless += 1
                continue
            by_csid[x["client_submission_id"]] = vr
        value_rows = list(by_csid.values())
        tot_s += (len(rows) - len(value_rows) - keyless)     # intra-page dupes -> skipped
        tot_e += keyless
        if keyless:
            log.warning("page offset=%d: %d row(s) missing client_submission_id", offset, keyless)

        if dry_run:
            log.info("[dry-run] page offset=%d fetched=%d upsertable=%d",
                     offset, len(rows), len(value_rows))
        else:
            w, e = upsert_page(pw, value_rows)
            tot_w += w; tot_e += e
            log.info("page offset=%d fetched=%d written=%d skipped_dupe=%d errors=%d",
                     offset, len(rows), w, len(rows) - len(value_rows) - keyless, e)

        if not data.get("has_more"):
            break
        offset += page_size
        if offset >= SCAN_CAP:
            log.warning("hit AS SCAN_CAP=%d at offset=%d. NOTE: admin_read_responses reads the "
                        "OLDEST %d physical sheet rows THEN filters, so submissions beyond that "
                        "are UNREACHABLE by this RPC and narrowing --from/--to will NOT recover "
                        "them — roll/archive F2_Responses below the cap, or change the AS readAll "
                        "to tail-read the newest rows. Stopping this run.", SCAN_CAP, offset, SCAN_CAP)
            break
    return dict(fetched=fetched, written=tot_w, skipped=tot_s, errors=tot_e, pages=pages)


def main():
    ap = argparse.ArgumentParser(
        description="Mirror F2 PWA submissions from the Apps Script backend into MySQL csweb_f2.f2_responses.")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--backfill", action="store_true",
                      help="sweep ALL history (from the Unix epoch)")
    mode.add_argument("--since", metavar="VALUE",
                      help="incremental: an ISO-8601 timestamp, or 'auto' to derive "
                           "the watermark from MySQL (default when no mode is given)")
    ap.add_argument("--from", dest="frm", metavar="ISO",
                    help="override the lower-bound submitted_at_server (advanced)")
    ap.add_argument("--to", metavar="ISO",
                    help="optional upper-bound submitted_at_server (date-window paging)")
    ap.add_argument("--overlap-minutes", type=int, default=OVERLAP_MIN,
                    help="re-fetch overlap for --since auto (default %d)" % OVERLAP_MIN)
    ap.add_argument("--page-size", type=int, default=PAGE_DEFAULT,
                    help="admin RPC page size (default/max %d)" % PAGE_DEFAULT)
    ap.add_argument("--env-file", default="/opt/f2sync/.env",
                    help="path to an .env file with secrets (default /opt/f2sync/.env)")
    ap.add_argument("--dry-run", action="store_true",
                    help="fetch and report counts, but do NOT write to MySQL")
    ap.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    a = ap.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if a.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s", stream=sys.stderr)

    cfg = load_env(a.env_file)
    url = require(cfg, "APPS_SCRIPT_URL", "F2_AS_URL")
    secret = require(cfg, "APPS_SCRIPT_HMAC", "F2_AS_HMAC")
    pw = require(cfg, "MYSQL_ROOT_PASSWORD", "F2_MYSQL_PW")
    if a.page_size < 1 or a.page_size > PAGE_DEFAULT:
        raise SystemExit("--page-size must be 1..%d (AS MAX_LIMIT)" % PAGE_DEFAULT)

    # resolve the read window
    to = a.to
    if a.backfill:
        mode_name, frm = "backfill", (a.frm or EPOCH_ISO)
    elif a.frm:
        mode_name, frm = "explicit-from", a.frm
    else:
        val = a.since or "auto"
        if val.lower() == "auto":
            wm = None if a.dry_run else compute_watermark(pw, a.overlap_minutes)
            mode_name = "since-auto"
            frm = wm or EPOCH_ISO
            if wm is None:
                log.info("%s empty (or dry-run) -> auto falls back to full backfill", TABLE)
        else:
            mode_name, frm = "since-explicit", val

    started = time.time()
    log.info("start mode=%s from=%s to=%s page_size=%d%s",
             mode_name, frm, to or "-", a.page_size, " [DRY-RUN]" if a.dry_run else "")
    stats = run_sync(pw, url, secret, frm, to, a.page_size, a.dry_run)

    elapsed = time.time() - started
    # final one-line summary for cron logs (mirrors csweb-dashboard-gen.py style)
    print("f2-mysql-sync mode=%s from=%s fetched=%d written=%d skipped=%d "
          "errors=%d pages=%d elapsed=%.1fs%s"
          % (mode_name, frm, stats["fetched"], stats["written"], stats["skipped"],
             stats["errors"], stats["pages"], elapsed, " [DRY-RUN]" if a.dry_run else ""))
    # non-zero exit if any row hard-failed, so cron/monitoring can alert
    sys.exit(1 if stats["errors"] else 0)


if __name__ == "__main__":
    main()
