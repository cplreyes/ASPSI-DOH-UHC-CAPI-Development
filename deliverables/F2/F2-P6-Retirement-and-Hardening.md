# F2 P6 — Retirement + Hardening (Cloudflare/Google teardown, rotations, backups)

**Status:** PLAN OF RECORD (drafted 2026-07-09) · **Gate to enter:** P5 passed (zero open P1s)
**Plan parent:** `deliverables/F2/F2-Prod-Migration-Plan.md` §3 P6 · sprint lane E4-F2-ELESTIO

> P4 made `csweb_f2` MySQL authoritative (2026-07-09). The Cloudflare/Google stack is frozen
> — Sheet `kill_switch=true`, deploy workflows disabled — and stays intact as the rollback
> path. **P6 is the point of no return: after the rotations below, `unflip` no longer
> restores service.** Do not start P6 until P5 is signed off and you're prepared to lose the
> rollback.

## P6-DAY RUNBOOK (the single ordered sequence -- everything below is reference)

Run from `deliverables/F2/PWA/server/` in Git Bash. Each step gates the next.

0. **Confirm P5 signed off** -- zero open `from-p5-reenroll-2026-07` P1s on #836; you've made the go/no-go call.
1. **CF auth — two options, browser login covers most of it:**
   - **`npx wrangler login`** (browser OAuth, no token needed) grants `workers_scripts:write`
     + `workers_kv:write` + `pages:write` → covers **Worker delete, KV delete, Pages redirect**
     (3 of the 4 CF steps). It does NOT grant r2 — that scope is absent from wrangler OAuth in
     every version. Sufficient for everything except the R2 bucket delete.
   - **A scoped CF token** (only needed for the R2 bucket delete, the LEAST critical step now
     that F-1 pulled the one real file to the box — the remaining R2 objects are the 2 phantom
     demos with no bytes). If skipping the token, leave the R2 buckets and delete them later, or
     mint a token:  -> save to `C:\Users\analy\.claude\jobs\<job>\tmp\cf_token.txt`.
   dash.cloudflare.com/profile/api-tokens -> Create Custom Token, account-scoped, **Edit** on:
   Workers Scripts * Workers KV Storage * Workers R2 Storage * Cloudflare Pages. (40 chars, no
   `cfat_` prefix -- the earlier `cfat_...` value was rejected by CF verify. Confirm the new one
   authenticates: `CLOUDFLARE_API_TOKEN=$(cat cf_token.txt) npx wrangler r2 bucket list`.)
2. **Dry-run the teardown** -- `bash deploy/p6-teardown.sh`. All Phase-0 gates must pass
   (P5=0 * drift +/-0 * token+R2 ok * F-1 real-files-on-box). It changes nothing.
3. **Deploy the redirect page** -- `cd ../redirect-page && npx wrangler pages deploy . --project-name f2-pwa --branch main --commit-dirty=true` (+ `f2-pwa-staging`). (The teardown also does this in Phase 1; either place is fine.)
4. **Execute teardown** -- `CONFIRM_P6=yes bash deploy/p6-teardown.sh`. It **stops at Phase 2 and
   makes you type `ROTATED`** -- that gate IS the HMAC rotation:
   - Apps Script editor: Project Settings -> Script Properties -> **rotate `HMAC_SECRET`**.
     <- **POINT OF NO RETURN. `unflip` can no longer reach the Sheet after this.**
   - Then type `ROTATED`. The script deletes `/opt/f2sync/.env`, the Workers, KV, and R2 buckets.
5. **Manual closeout** (the script prints this): archive the AS deployment read-only, freeze the
   Sheet (protect tabs + banner), delete `as-deploy.yml`+`cf-pages-deploy.yml` from the repo (you commit).
6. **Reset `carl_admin`** -- its password transited chat during the F-1 retrieval (2026-07-13).
7. **P7 sign-off** (S6): URL live * store authoritative * dashboard native * backups verified
   (WARN F-2 -- the box's borg takes no archives; F2's own nightly dump is verified, but settle borg
   before ticking this) * rollback documented as retired * UAT re-enrolled * ASPSI told the new
   URL * old origin redirects * no live secret transited chat (-> step 6).

Same-pass optional: the KV durable-keys migration (`deploy/p4-local-kv-r2.sh`, needs the step-1
token) -- non-blocking (keys self-expire; re-enrollment moots revocations); do it before deleting KV to keep the audit trail.

## Staged 2026-07-13 (prep done ahead of the gate — P6-day is rotations + teardown only)

- **§4 ETL repoint: DONE.** F2 extract reads `csweb_f2` MySQL direct (`etl/extract_csweb.py`
  `F2_DB`/`F2_TABLES`; etl-spec v0.3 §2.2). The Worker's break-out cron is moot — §3.2 needs
  no predecessor step anymore.
- **§3.7 URL repoints: DONE in the working tree** (ci.yml ×2, uat-slack-events.yml + wording,
  uat_slack_digest.py + button label, landing/index.html, docs-sitemap.excalidraw + PNG
  re-render). Live landing copy updates at the next scp (step 0 of the hardening script).
- **§5 hardening: SCRIPTED** = WT `PWA/server/deploy/p6-hardening-box-steps.sh` (runs the §1
  drift gate, installs nightly csweb_f2 dump + f2-files archive + restore-verify, auth_kv
  sweep cron, ships the f2-api dashboard probe now in `csweb-dashboard-gen.py`). Safe to run
  before the P5 sign-off — nothing irreversible in it.
- **§2+§3 teardown: SCRIPTED + GUARDED** = WT `PWA/server/deploy/p6-teardown.sh`. Dry-run by
  default (`CONFIRM_P6=yes` to execute). Phase 0 hard-gates on: zero open P5 findings · drift
  gate ±0 · real wrangler auth **with R2 reachable** (`whoami` exits 0 when logged out — an
  exit-code check false-passes, so it greps the output and then actually lists buckets) · and
  **F-1: every live `f2_files` object present on the box** — it refuses to delete R2 while any
  byte exists only there. Phase 2 is a typed `ROTATED` gate at the HMAC rotation (the point of
  no return); nothing is deleted before it. Dry-run 2026-07-13: gates 0.1/0.2 pass, 0.3 blocks
  (login pending), 0.4 blocks (3 objects still only in R2) — i.e. the guards work.
- **§3.1 Pages redirect: BUILT** = WT `PWA/redirect-page/` (`_redirects` 301 + self-destructing
  `sw.js` — the old workbox SW serves from cache and never sees a 301, so the SW update path
  is what actually rescues returning testers — + fallback page). Deploy commands in its README.

## §0 What "frozen but alive" means right now (the residue P6 removes)

| Surface | State after P4 | Removed/changed at P6 |
|---|---|---|
| Sheet public path (submit/config/…) | refuses — `E_KILL_SWITCH` | AS deployment archived read-only |
| Sheet **admin envelope** (paper-encode, DLQ replay, breakout cron) | **still writable** — kill_switch gates only the public router (`Router.js:27`) | HMAC rotation kills it; Worker retired |
| CF Pages `f2-pwa.pages.dev` | serves the old build; looks enrolled, can't sync | → redirect page to `uhc-hcw.asiansocial.org`, kept ~30 d |
| CF Worker `f2-pwa-worker` | live; proxies to the frozen Sheet | deleted (after the redirect window) |
| CF Worker cron `*/5` | still mints breakout CSVs from the frozen Sheet — **silently stale** | dies with the Worker |
| KV `F2_AUTH`, R2 `f2-admin` | live | deleted after the local leg copies + bucket reconcile |
| GH workflows `as-deploy`, `cf-pages-deploy` | **disabled** (2026-07-09) | deleted from the repo |
| Poller cron + `/opt/f2sync/.env` | cron retired; secret file remains | secrets purged after HMAC rotation |

## 🔴 Findings from the hardening run (2026-07-13) — BOTH BLOCK P6

**F-1 — R2 file BYTES were never copied; deleting the bucket destroys them (data loss).**
P4 ported the `f2_files` **metadata rows** (3) into `csweb_f2`, but the objects themselves
still live only in R2. `/opt/app/f2-files/` on the box is **empty** (verified 2026-07-13), and
the new server's `LocalFileStore.get()` (`server/src/admin/store.ts:1493`) reads
`${F2_FILES_DIR}/<file_id>` from disk and returns `null` on ENOENT.
Two consequences:
- **Live now, during P5:** the Admin → Files app *lists* files that cannot be downloaded
  (404). Includes a real upload — `Paper-based HCW survey (English).docx.pdf`, 375 KB,
  kidd_admin, 2026-05-18. Testers on leg F may hit this. **The 3 objects (confirmed 2026-07-13): `Demo - Field Plan 2026-Q1.pdf` 243KB, `Demo - Facility Roster.csv` 12KB — both carl_admin demos — and `Paper-based HCW survey (English).docx.pdf` 366KB, kidd_admin (a blank reference form). NO respondent data; nothing irreplaceable — so no urgency, but R2 deletion still stays blocked until the bytes are on the box. Token route failed 2026-07-13 (Carl's supplied `cfat_…` value rejected by CF verify, error 1000); fallback = download the 3 via the still-live old admin portal (f2-pwa.pages.dev/admin, 200, Worker R2 binding intact).}**
- **At §3.4:** deleting the `f2-admin` bucket without copying = permanent loss.
**RESOLVED 2026-07-13 (partial + finding).** Retrieved via the old portal's Worker R2 binding (admin login `carl_admin`, `pull-f2-files-via-portal.sh`): the ONE real file (`Paper-based HCW survey…pdf`, 375224 B) downloaded size-verified and is now on the box at `/opt/app/f2-files/4674faa7-…`. **The 2 `DEMO-FILE-00{1,2}` rows are PHANTOM metadata — their bytes are absent from R2 (`E_NOT_FOUND` on download from both portals); seeded demo stubs, no data to recover.** So F-1's data-loss risk is ELIMINATED. Remaining: soft-delete the 2 phantom rows (`UPDATE f2_files SET deleted_at=UTC_TIMESTAMP() WHERE file_id IN ('DEMO-FILE-001','DEMO-FILE-002')`) so live-rows==box-objects and the teardown guard passes — a prod DB write, held for Carl's approval 2026-07-13. Admin password `carl_admin` transited chat during retrieval → RESET after P6. Original text: **Fix = the P4 local leg** (`deploy/p4-local-kv-r2.sh`), which copies KV keys + R2 objects
size-verified. It has never run — it needs live wrangler auth. The stale June-9 OAuth token
was 400-ing on refresh (and its scope list carried **no R2 scope**); cleared via
`wrangler logout` 2026-07-13, so a fresh `npx wrangler login` should now grant R2. **Run the
local leg and confirm the 3 objects land in `/opt/app/f2-files/` BEFORE any R2 deletion.**

**F-2 — the box's borg backup takes no archives (pre-existing, whole-box, not F2-specific).**
`/opt/borg/backup.sh` runs `preBackup.sh` (mysqldump `--all-databases` →
`/opt/app/lastDump.sql.gz`), then **`borg compact` only — there is no `borg create`** — and
`postBackup.sh` then `rm`s the dump. So each nightly run dumps, compacts, and deletes, leaving
no new archive. `lastDump.sql.gz` is absent between runs, as expected from that sequence.
This predates the migration and affects **CSWeb as much as F2**; the borgbase repo may still
hold old archives (passphrase check not pursued — Carl's infra call).
**Mitigation already in place:** the nightly `csweb_f2` dump + `f2-files` archive installed by
`p6-hardening-box-steps.sh` (19:15 UTC) is **restore-verified** (41 rows restored = live), so
F2 has a working local backup independent of borg. Offsite coverage for it still depends on
either the Elestio panel backup including `/opt/backups/f2`, or borg being repaired.
**P7's "backups verified" line should not be ticked on borg's behalf until F-2 is settled.**

## §1 Prerequisites (must be true before step 1)

- [ ] **P5 signed off** — zero open P1-severity findings (tracking issue #836).
- [ ] **P4 local leg complete** — `deploy/p4-local-kv-r2.sh` has run (needs `npx wrangler login`).
      Blocks §3: you cannot verify the R2 copy you never made. **See F-1 — this is now known to
      be a real data-loss risk, not a formality: the 3 file objects exist ONLY in R2 today.**
- [x] **Drift check green** (2026-07-13: `sheet=41 mysql=41`, ±0) — re-run on P6-day:
      `python3 /opt/f2-postgres-migration/p4_port_registry.py counts-gate`
      returns ±0. A non-zero delta means something wrote the frozen Sheet (paper-encode on the
      old portal); re-run the final backfill and investigate before retiring anything.
- [ ] **R2 bucket reconciled** via the Cloudflare dashboard — the metadata walk cannot see
      objects orphaned under a soft-deleted folder. Confirm the object count matches the
      `f2_files` live-row count (3) plus any known break-out CSVs before deleting the bucket.

## §2 Rotations (the irreversible half — do these first, deliberately)

1. **`APPS_SCRIPT_HMAC` / AS `HMAC_SECRET`** — this is the admin-envelope MASTER secret. It
   can sign ANY admin action (including flipping kill_switch back), and **a copy was pasted
   into a chat transcript** during the mirror walk. Rotating it: (a) kills the old Worker's
   admin envelope — the last un-gated Sheet write path; (b) closes the chat-transit exposure.
   Rotate in the AS editor (Script Properties → `HMAC_SECRET`), then **delete `/opt/f2sync/.env`**
   on the box (its only consumers — the poller and the P4 engine — are retired).
   *After this, `p4_port_registry.py unflip` cannot reach the Sheet. Rollback is over.*
2. **JWT signing key** — **no rotation debt.** The box key was minted on-box at P2 and never
   transited chat; the Worker's key is write-only in Cloudflare and is discarded with the
   Worker. Skip. (Recorded here so the plan's original "rotate JWT at P6" line isn't
   actioned twice.)
3. **`APPS_SCRIPT_URL`** — no secret value, but remove it from `/opt/f2sync/.env` with the file.
4. **Env files** — scanned 2026-07-09: no `.env.local` exists in the app/worker/server trees
   (the parent plan's "purge stale `.env.local`" line is stale — nothing to purge). What
   exists: `app/.env.example`, `app/.env.production` (comments only, no active vars — the
   origin comes from `VITE_F2_PROXY_URL` at build time), `server/.env.example` (names only).
   **Real action:** the build origin lives in `ci.yml` (§3.7) — fix it there.

## §3 Teardown (after the rotations, in order)

1. **CF Pages → redirect page.** Replace the deployed build with a one-page redirect to
   `https://uhc-hcw.asiansocial.org` (keep the deployment, ~30 days). This is what catches a
   tester or bookmark still hitting the old origin — today they get a working-looking form
   that silently never syncs, which is the worst failure mode available.
2. **Delete the CF Worker** `f2-pwa-worker` (and `-staging`). Kills the `*/5` breakout cron —
   confirm §4's ETL repoint is done first, or accept that scheduled F2 CSVs stop.
3. **Delete KV `F2_AUTH`** (`9b293e0c661d4f60b513facc61b11e0b`) — durable keys already in
   `auth_revoked` / `auth_token_audit`.
4. **Delete R2 `f2-admin`** (+ `-staging`, + preview buckets) — only after §1's reconcile.
5. **Archive the AS deployment read-only** and **freeze the Sheet** (protect all tabs, add a
   banner row: "Pre-migration record — authoritative store is csweb_f2 as of 2026-07-09").
   Keep it; it's the archive of record and the audit source for anything the port missed.
6. **Delete the disabled workflows** `as-deploy.yml`, `cf-pages-deploy.yml` from the repo.
7. **Repoint stale URLs** (they become dead links the moment Pages goes):
   - `ci.yml` lines 57, 92 — `VITE_F2_PROXY_URL` → `https://uhc-hcw.asiansocial.org`
   - `uat-slack-events.yml` L25 `STAGING_URL`; `.github/scripts/uat_slack_digest.py` L30-32
     `STAGING_URL`/`PROD_URL`
   - `deliverables/CSWeb/landing/index.html` L551 — admin-portal href → `uhc-hcw…/admin`
   - `docs-sitemap.excalidraw` L89-90 (same URL, re-render)

## §4 Consequences to settle BEFORE the Worker dies

- **RESOLVED 2026-07-13 — option (a) executed:** the harmonization ETL reads `csweb_f2` SQL directly (etl-spec v0.3 §2.2 + `etl/extract_csweb.py`); the break-out feature is moot for F2 and `f2_settings` stays CRUD-only. Original consequence text kept below for the record.
- **Break-out CSV cron has no successor.** The Worker's `runDueSettings` is not ported
  (`server/src/admin/routes.ts:968-969`); `f2_settings` rows are served CRUD-wise but nothing
  consumes them. Two options: (a) **repoint the harmonization ETL's F2 extract to `csweb_f2`
  SQL directly** (`deliverables/Data-Harmonization/etl-spec.md` §2.2 L72,146 currently names
  the R2 CSV) — this makes the break-out feature moot for F2 and is the recommended path; or
  (b) port `runDueSettings` to a box cron. **Decide, don't drift.**
- ~~**ETL spec edit** is required either way~~ — done: etl-spec v0.3 (2026-07-13) describes the SQL path; the R2 object is marked DO-NOT-USE.

## §5 Hardening (the reason P6 isn't just deletion)

> §5 is fully scripted in `p6-hardening-box-steps.sh` (WT deploy dir) — one SSH run.

- [ ] **Backups**: add `csweb_f2` (mysqldump) + `/opt/app/f2-files` to the borg set that
      already covers CSWeb; verify a restore of one table + one file object.
- [ ] **Monitoring**: add an f2-api freshness/health line to the monitoring layer alongside
      the CSWeb checks — `/api/health` + "newest `f2_responses.submitted_at_server` older than
      N hours during a fielding window" alert. The 2-min poller used to be the de-facto
      liveness signal; it's gone.
- [ ] **`auth_kv` sweep**: rows past `expires_at` are treated as absent but never deleted —
      add a nightly `DELETE FROM auth_kv WHERE expires_at < UTC_TIMESTAMP()`.
- [ ] **Elestio custom-domain registration** for `uhc-hcw` (8787) and `capi` (8788), or accept
      the hand-written vhosts. If the panel later generates its own conf for the same
      `server_name`, remove the manual file (duplicate-vhost risk).

## §6 P7 sign-off checklist (what P6 must leave true)

URL live · store authoritative · dashboard native · **backups verified** · rollback documented
as *retired* (not available) · UAT roster re-enrolled · ASPSI told the new URL · old origin
redirects · no live secret transited chat.
