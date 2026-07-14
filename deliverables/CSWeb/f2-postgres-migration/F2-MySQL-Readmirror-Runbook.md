# F2 → MySQL read-mirror on the CSWeb box — Runbook

**Goal:** give F2 (Healthcare-Worker PWA) a **real database** on the CSWeb box so the
unified Sync Dashboard shows F2 beside F1/F3/F4 — with **zero change to F2's live write
path**. F2 data lands in a new MySQL database `csweb_f2`, kept fresh by a poller that
reads the existing Apps Script backend; the dashboard reads it through its existing
`q()` docker-exec path.

## Decisions this runbook implements (2026-07-07)

- **Engine = MySQL 8** (not Postgres). F2 lives in the SAME `lamp-mysql8` container as
  `csweb_f1/f3/f4_breakout` — no new container, no new engine, ~0 extra RAM. The
  dashboard reads it exactly like the other three instruments.
- **Scope = read-mirror.** `csweb_f2` is a queryable **copy**; Google Sheets + Apps
  Script stay F2's **write authority**, and the Elestio end-state is untouched.
- **Deferred (Phase B, Carl-gated):** making the app write to `csweb_f2` *directly*
  and retiring the Sheet (full primary cutover). NOT built here — see §7.
- This folder's name (`f2-postgres-migration/`) is the working title from the first
  design pass; the shipped artifacts are MySQL. The Postgres drafts were removed to
  avoid an operator running the wrong engine's files.

## Artifacts (all in `deliverables/CSWeb/f2-postgres-migration/`, except the generator)

| File | Role |
|---|---|
| `csweb_f2_schema.sql` | MySQL DDL: `csweb_f2` DB + `f2_responses` + `f2_facility_master`. Idempotent. |
| `sync_f2_to_mysql.py` | The poller: Apps Script `admin_read_responses` → UPSERT into `csweb_f2.f2_responses`. Reuses the `docker compose exec database mysql` primitive (no new host deps beyond `requests`). |
| `csweb-dashboard-gen.py` | (in `deliverables/CSWeb/`) — patched inline: F2 is a 4th section/instrument reading `csweb_f2`. |
| `f2-store-scope-decision-mysql.png` | the scope-fork decision diagram. |

## Secrets (names only — Carl places the values; never in the repo)

Keep the poller's secrets **disjoint** from the master `/opt/app/.env` (which also holds
`MYSQL_ROOT_PASSWORD` for the whole stack). Put the poller's in `/opt/f2sync/.env` (perms `600`):

| Var | Where | Notes |
|---|---|---|
| `APPS_SCRIPT_URL` | `/opt/f2sync/.env` | Apps Script `/exec` deployment URL |
| `APPS_SCRIPT_HMAC` | `/opt/f2sync/.env` | **See security note below** — this is the AS admin master secret |
| `MYSQL_ROOT_PASSWORD` | `/opt/f2sync/.env` | for the poller's docker-exec mysql client (or alias `F2_MYSQL_PW`) |

> **SECURITY NOTE (from the migration review, CONFIRMED-high):** `APPS_SCRIPT_HMAC` is the
> Apps Script admin-envelope **master** secret — it can sign *any* admin action, not just
> reads. Copying it to the box widens its blast radius (box compromise ⇒ forge/kill-switch
> the live survey). **Preferred:** issue the box a **scoped read-only credential** the AS
> side authorizes only for `admin_read_responses`, and rotate the shared secret when/if
> Phase B lands. Until then, treat the box as full-trust for F2 admin, not read-only.

---

## Phase A — stand up the read-mirror  (this is the whole near-term build)

### A1. Create the database + tables  ·  `[Carl-gated: runs SQL as root]`
From `/opt/app` (so the `database` service resolves). **First load the master secret into the
shell** — `$MYSQL_ROOT_PASSWORD` lives in `/opt/app/.env` but a compose `.env` is NOT exported
into your interactive shell, so it must be sourced or the `-p` flag collapses to a bare `-p` and
auth fails:
```bash
cd /opt/app
set -a; . /opt/app/.env; set +a          # puts MYSQL_ROOT_PASSWORD in scope for the next commands
docker compose exec -T database mysql -uroot -p"$MYSQL_ROOT_PASSWORD" \
  < /opt/f2-postgres-migration/csweb_f2_schema.sql
```
**GATE A1** (same shell, so the var is still set):
```bash
docker compose exec -T database mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -N -e \
  "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='csweb_f2';"   # → 2
```
Dark change; nothing user-facing yet. **Rollback:** `DROP DATABASE csweb_f2;` (empty, safe).

### A2. Deploy + run the poller (backfill once)  ·  `[automatable + Carl places secrets]`
Put `sync_f2_to_mysql.py` at `/opt/f2-postgres-migration/`, create `/opt/f2sync/.env`
(the 3 vars above, `chmod 600`), then a full backfill:
```bash
cd /opt/app && python3 /opt/f2-postgres-migration/sync_f2_to_mysql.py \
  --backfill --env-file /opt/f2sync/.env
```
Dry-run first if you want to see counts without writing: add `--dry-run`.
**GATE A2:** the run prints `f2-mysql-sync … written=N errors=0`, and
`SELECT COUNT(*) FROM csweb_f2.f2_responses;` matches the Sheet's row count (± in-flight).
The poller needs `pip3 install requests` on the host and reaches MySQL via `docker compose exec`
from `/opt/app` (no MySQL host port needed). **Rollback:** `TRUNCATE csweb_f2.f2_responses;` and re-run.

### A3. Schedule the incremental sync  ·  `[automatable]`
Add a flock-guarded cron beside the dashboard cron (2-min cadence to match). **ONE physical line**
— cron does NOT honor backslash-newline continuation; a multi-line entry silently fails to run:
```
*/2 * * * * flock -n /tmp/f2-mysql-sync.lock bash -c 'cd /opt/app && python3 /opt/f2-postgres-migration/sync_f2_to_mysql.py --env-file /opt/f2sync/.env' >> /var/log/f2-mysql-sync.log 2>&1
```
`--since auto` is the default (watermark = `max(submitted_at_server) − 15 min`; the UPSERT dedups
the overlap). The poller `sys.exit(1)` on any row error — but note the recipe above **redirects
both streams to the log with no `MAILTO`, so cron will NOT act on that exit code**. To actually be
alerted, do ONE of: (a) set `MAILTO=you@…` at the top of the crontab and drop the `2>&1` so stderr
mails on failure; (b) run a separate log-scan alert (`grep -q "errors=[1-9]\|ERROR" the log`); or
(c) a freshness alarm on `MAX(synced_at)` (the poller bumps it every successful run — a frozen
value = the poller is not running). A wedged run is bounded: `mysql()` has a 120 s timeout and the
schedule uses `flock -n`, but add `flock -w 30` / wrap in `timeout 600` if you want a hung holder
force-released rather than skipped.

> **Scale note (latent):** `admin_read_responses` returns the OLDEST 50 000 physical sheet rows
> then filters, so if `F2_Responses` ever exceeds 50 000 rows the NEWEST submissions become
> unreachable and the mirror silently caps (F2_Responses lifetime is ~30 K, so latent). If it
> approaches the cap, roll/archive the sheet or switch the AS `readAll` to tail-read.

### A4. Ship the patched dashboard generator  ·  `[Carl deploy — scp, as today]`
`scp csweb-dashboard-gen.py root@…:/opt/csweb-dashboard-gen.py`. Its 2-min cron re-runs it;
the F2 read is fault-tolerant and self-diagnosing — if `csweb_f2` does not exist yet the F2 note
reads "F2 query failed — csweb_f2 may not exist yet"; once created-but-empty it reads "No F2
submissions mirrored yet"; F1/F3/F4 always render unaffected. So A4 can safely precede or follow
A1–A3 (the generator won't break if the DB isn't up).
**GATE A4:** load `https://csweb.asiansocial.org/docs/dashboard.html` — the Instrument filter
lists **F2 · Healthcare Worker**, the F2 card + section render, and the F2 count matches
`SELECT COUNT(*) FROM csweb_f2.f2_responses;`. **Rollback:** re-scp the pre-F2 generator.

**End of Phase A: F2 has a real DB and appears in the unified dashboard. Sheets is still F2's
source of truth. This satisfies "a real DB for F2" with the smallest, safest change.**

---

## §4  What Phase A does NOT change (by design)

- The **live F2 write path** (PWA → Cloudflare Worker → Apps Script → Sheet) is untouched.
- **Geo rollup is deferred.** `f2_facility_master` is empty until seeded from the CAPI facility
  frame with region/province **byte-identical to CSWeb's F1/F3/F4** names; until then F2 rolls
  up under `(unknown)` (degrades gracefully). Coverage-vs-target is likewise deferred (no F2
  sample frame exists yet — same reason F2 has no `targets.json` entry).
- **GPS:** F2 is self-administered (no geolocation), so the generator fixes `gps='1'` for F2 —
  it must never inflate the "No GPS fix" KPI. (Do NOT switch to a lat/lng-derived rule unless
  F2 actually starts capturing coordinates.)

---

## §7  Phase B — full primary cutover  (DEFERRED · Carl-gated · NOT built here)

Only if you later decide `csweb_f2` should become F2's **write authority** (retiring the Sheet).
This is the destructive, field-affecting half and collides with the Elestio end-state, so it
stays a deliberate decision, not a default. When/if chosen, it needs (each its own gate):
1. **Dual-write** — the Worker writes each accepted submit to a box ingest endpoint *and* the
   Sheet; the poller keeps running as the reconciliation net. Sheet still authoritative.
2. **Companion state** — before cutover, backfill the config/enrolment state the write path
   depends on (`min_accepted_spec_version` spec-gate, HCW enrollment/refusal registry) that the
   read-mirror does NOT carry; otherwise the spec-gate is OFF and refusal-tagging no-ops.
3. **Primary flip** — Worker writes `csweb_f2` synchronously (idempotent `INSERT … ON DUPLICATE
   KEY UPDATE`), stop the Sheet, retire the poller. Decide explicitly whether F2 rows are
   mutable-after-insert (corrections) — if so the ingest path must UPDATE on conflict, not ignore.
4. **Rollback** must reverse-sync **provenance-preserving** (do NOT replay self-admin rows through
   the paper-encoder path, which would mislabel `source_path`).
5. Resolve the **box-vs-Elestio end-state** first: if Elestio is F2's real home, the box stays a
   READ mirror (Phase A only) and Phase B is struck to avoid a second migration.

---

## Review findings addressed by the MySQL read-mirror

The MySQL + read-mirror decision **dissolves most of the 31 Postgres-design findings** (no new
container/roles/cluster ⇒ no superuser-landmine, no host↔container connectivity gap, no
new-role drift; no write path ⇒ no `f2_config`/`f2_hcws`/batch-semantics gaps). The rest are
handled here: one canonical name set (`csweb_f2` / `f2_responses` / `f2_facility_master`), one
geo derivation (inline in the generator, not a second view), `gps='1'` for F2 (no false no-GPS),
disjoint secrets file, a visible F2 freshness note + non-zero poller exit (no silent flatline),
per-row upsert isolation (no silent drop), and the HMAC-scope security note above. The Elestio
end-state question and the spec-gate/enrolment backfill are quarantined to the deferred Phase B.
