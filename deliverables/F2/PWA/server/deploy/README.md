# f2-api deploy artifacts (Plan P2 — stand up dark)

Carl-gated: the box writes + DNS. See `F2-Prod-Migration-Plan.md`.
**Executable source of truth: `p2-box-steps.sh`** (idempotent; run via
`ssh ... 'bash -s' < p2-box-steps.sh` after step 0 below). `Dockerfile` here is
the real build file shipped to the box. Box recon 2026-07-08 (P2 walk):

- elestio-nginx = `elestio/nginx-auto-ssl` with `network_mode: host` — vhosts
  proxy to **loopback published ports** (`127.0.0.1:8787`), NOT a compose
  network, and TLS is **automatic** (cert minted on first HTTPS hit) once the
  domain is in `ALLOWED_DOMAINS` in `/opt/elestio/nginx/.env` AND DNS resolves.
  No manual cert step exists.
- Both secrets (`F2_DB_PASSWORD`, `F2_JWT_SIGNING_KEY`) are **generated on the
  box** by the script and appended to `/opt/app/.env` — never transit chat.
  The JWT key is fresh (the Worker's is write-only in Cloudflare); old Worker
  tokens won't verify on hcw, which is moot pre-P4 since P5 re-enrolls all UAT
  devices — and a never-transited key carries no P6 rotation debt.

## Step 0 — ship the package (run from Windows Git Bash, in `server/`)

```bash
npx tsc -p tsconfig.json   # fresh dist/
tar czf - package.json package-lock.json dist ddl deploy/Dockerfile \
  | ssh -i /c/Users/analy/.ssh/aspsi-csweb root@207.148.65.115 \
    'mkdir -p /opt/f2-api && tar xzf - -C /opt/f2-api \
     && mv -f /opt/f2-api/deploy/Dockerfile /opt/f2-api/Dockerfile \
     && rmdir /opt/f2-api/deploy 2>/dev/null; ls /opt/f2-api'
```

## Compose service — merged into /opt/app/docker-compose.yml by the script

The canonical block lives in `p2-box-steps.sh` step [4/7]. Deltas vs the
original sketch here: `ports: "127.0.0.1:8787:8787"` (host-net nginx proxies
to loopback; the port is never public), a watchtower-disable label (the image
is locally built, not pullable), and the Versioning-panel vars
(`PWA_VERSION`/`PWA_BUILD_SHA`/`API_VERSION`) deferred to P3 when the app
build exists.

`.env` additions (values on-box only, written by the script into /opt/app/.env):
`F2_JWT_SIGNING_KEY` · `F2_DB_PASSWORD` (least-priv `f2api` MySQL user — see ddl/;
P1b widens the grant to include DELETE).

P1b DDL: re-apply `ddl/f2_api_tables.sql` (idempotent) — adds f2_users / f2_roles /
f2_audit / f2_files / f2_settings / auth_kv and makes `f2_hcws.qn` UNIQUE (pre-existing
tables need the ALTER noted in the file). Admin users/roles row data migrates from the
Sheets at P4; until then the DDL seeds only the built-in Administrator ROLE (no users —
create the first user row manually or at P4).

## nginx vhost — uhc-hcw.asiansocial.org (/opt/elestio/nginx/conf.d/)

Written by the script (step [7/7]) in the box's own auto-SSL idiom:
`include resty-server-https.conf` + the domain appended to `ALLOWED_DOMAINS`,
then `docker compose up -d` in /opt/elestio/nginx to recreate the container
(~5 s csweb blip). API locations (`/exec|/verify-token|/api/|/admin/api/`)
proxy to `http://127.0.0.1:8787` with `client_max_body_size 100m`; in P2 the
`location /` fallback also proxies to the API. **At P3** that fallback becomes
the static PWA: mount the build dir into the nginx container or serve static
from f2-api itself, restoring `try_files $uri $uri/ /index.html` (#528 SPA
fallback — cold `/enroll?token=` loads).

## P2 gate

DNS `uhc-hcw.asiansocial.org → 207.148.65.115` (grey-cloud/DNS-only if the zone is
on Cloudflare — auto-SSL needs the direct hit), then
`curl https://uhc-hcw.asiansocial.org/api/health` → `{"ok":true,...}` (first hit
mints the cert; give it a few seconds) · RAM delta ≤ 256 MB · CSWeb sync
unaffected (spot-check a CSEntry sync + the dashboard cron).

## P4 — registry + config cutover (the authority flip)

Adversarially reviewed 2026-07-09 (4 lenses, 30 findings, all confirmed ones
fixed — see log.md). Three artifacts, run in this order (all Carl-gated), plus
`npx wrangler login` verified BEFORE starting (the local leg needs it and it
should not be discovered broken after the flip):

1. **Ship** (local, Git Bash): `npx tsc` + tar the f2-api package →
   `/opt/f2-api` (the server changed at P4: `/exec` now gates on
   `f2_config.kill_switch` — AS Router.js:27 parity + the rollback
   single-authority switch — and facilities serve `barangay`, 7-col sheet
   parity); scp `p4_port_registry.py` → `/opt/f2-postgres-migration/`; scp the
   dashboard-note text fix → `/opt/csweb-dashboard-gen.py`. Exact commands in
   `p4-box-steps.sh` header.
2. **`p4-box-steps.sh`** (via `ssh 'bash -s'`, 10 steps, RE-RUNNABLE — the
   engine phases are flip-aware, so a mid-run failure resumes with the same
   command): guarded ALTERs (`facility_type`, `barangay`) + DDL re-apply →
   f2-api rebuild (`--no-deps`) → preflight (incl. a width/shape scan that
   surfaces poison rows — e.g. the documented 301-char hcw_id class — BEFORE
   anything mutates) → facilities export (pre-flip: the legacy GET is
   kill_switch-gated) → **flip** (Sheet `kill_switch=true`; admin envelope
   stays alive) → **final `--backfill`** under the poller's own flock
   (`errors=0` required) + LPAD repair of Sheets' numeric coercion (qn 11→12,
   facility_id 8→9 — region-0x codes lost a leading zero on the Sheet) →
   counts gate ±0 → registry port (hcws deduped keep-newest + qn re-padded /
   users with PBKDF2 hashes verbatim / roles / config with **`kill_switch`
   forced `false` in MySQL** / files metadata / settings / dlq / audit guarded
   by an auth_kv marker, chunked packet-safe inserts with per-row poison
   isolation) → poller cron retired (crontab backup in /root) → **canary**
   (JWT minted inside the container → submit at the public origin → row in
   MySQL → Sheet total unchanged → row deleted) → closing counts-gate
   tripwire + health.
3. **`p4-local-kv-r2.sh`** (local, wrangler-authed): KV `revoked:`/`token:`
   durable keys → `auth_revoked`/`auth_token_audit` (ephemeral throttle/session
   keys are NOT migrated — everyone re-logs-in); R2 `files/<file_id>` objects →
   `/opt/app/f2-files` with per-file size verification (enumerated from the
   ported `f2_files` metadata — wrangler 3.114 has no `r2 object list`;
   objects absent from R2 but already on-box = new-portal uploads, tolerated).

**Rollback** (any point until P6): `python3 /opt/f2-postgres-migration/p4_port_registry.py unflip`
— Sheet `kill_switch=false` AND MySQL `kill_switch=true`, so exactly one stack
accepts writes in either direction — + re-add the poller cron (printed). The
CF/Google stack stays intact and dark until P6 (+30 days).

Post-P4 residue, by design: the old Worker admin envelope (paper-encode, DLQ
replay, the */5 breakout cron) still writes the FROZEN Sheet if used —
kill_switch cannot gate it without breaking rollback. Controls: disable the
`as-deploy.yml` + `cf-pages-deploy.yml` GitHub workflows (UI toggle, no
commits); the old portal is READ-ONLY BY POLICY (admins are ~3 known people;
encoding is not active pre-pretest); the closing counts-gate + a pre-P6
`counts-gate` re-run detect any drift. The new portal lives at
`uhc-hcw.asiansocial.org/admin` with the ported users. Breakout CSVs have no
post-P6 producer — the harmonization ETL's F2 extract repoints to csweb_f2 SQL
(spec change already noted in etl-spec). Before deleting the R2 bucket at P6,
reconcile it via the CF dashboard (files nested under a soft-deleted folder are
invisible to the metadata walk).
