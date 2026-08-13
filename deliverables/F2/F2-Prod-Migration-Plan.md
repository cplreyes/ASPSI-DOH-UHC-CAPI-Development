# F2 Production Migration Plan — off Cloudflare/Google, onto the csweb Elestio box, **before pretest**

**Status:** PLAN OF RECORD (decided 2026-07-08) · **Sprint lane:** E4-F2-ELESTIO (S013 Goal A)
**Decision:** Option A — consolidate F2's serving stack onto the existing Elestio-managed CSWeb VM
(`csweb.asiansocial.org`, root@207.148.65.115). Diagram: `f2-serving-migration-options.png`.
Option B (dedicated Elestio service) remains the documented escape hatch if F2 load ever
threatens the CSWeb sync.

## §0 Why now — the greenfield window

Pre-pretest is the cheapest this migration will ever be, and the window closes the day real
fieldwork starts:

- **~Zero real data.** 41 UAT/demo submissions; the store cutover is "stand up and point," not
  dual-write/backfill/reconcile (the adversarial review's "greenfield gate," now exercised).
- **~Zero origin-change cost.** Installed PWAs + IndexedDB (drafts, enrollment, device tokens)
  are pinned to `f2-pwa.pages.dev`. Moving to `uhc-hcw.asiansocial.org` costs a handful of UAT
  tester re-enrollments today; after fielding it would be a device-fleet incident.
- **The store is already waiting.** `csweb_f2` (MySQL, on-box) is live, qn-ready, and
  adversarially reviewed ×2. The API just starts writing what the mirror proved.
- **Motive on record:** Cloudflare free tier won't hold the fielded user load (S013 lock);
  ASPSI meeting 2026-06-22 already declared "F2 migrating off Cloudflare."

## §1 Target architecture (end-state)

```
uhc-hcw.asiansocial.org        (elestio-nginx vhost, auto-TLS — same machinery as csweb/docs)
├─ /                      static PWA build (Vite dist), rsync'd by CI — replaces CF Pages
├─ /api/*                 f2-api container (Node/Hono) in the existing /opt/app compose
│    · POST /api/verify-token        (device enrollment — replaces Worker /verify-token)
│    · POST /api/submit, /api/batch-submit   (JWT-auth'd — replaces Worker /exec→AS)
│    · /api/admin/*                  (sessions, RBAC, HCWs+QN assign, data, files, encode)
│    · auth state: MySQL tables      (csweb_f2.auth_tokens / auth_sessions / auth_users …)
│    · files:      /opt/app/f2-files volume            — replaces R2
│    · cron:       box cron (digests)                  — replaces Worker cron
└─ store: csweb_f2 MySQL = THE store (f2_responses/f2_hcws/f2_config…) — Sheet+AS retired
```
Resource budget: f2-api ≈150–250 MB with `mem_limit`, on ~1.4 GB free / 2.5 GB available.
The dashboard's F2 read becomes a same-box read of the live store; the 2-min mirror poller
retires at cutover.

## §2 Component migration map

| Today (CF/Google) | Target | Notes |
|---|---|---|
| CF Pages `f2-pwa.pages.dev` | nginx static at `uhc-hcw.asiansocial.org/` | like `/docs`; SPA fallback rule replaces `_redirects` (#528) |
| CF Worker `/exec` submit proxy | f2-api `/api/submit` writing `csweb_f2.f2_responses` | idempotent `ON DUPLICATE KEY` on `client_submission_id`; per-item batch results (≤50) — preserves the offline queue contract |
| CF Worker `/verify-token` | f2-api (same JWT verify, incl. `qn` claim) | JWT signing key carried over then rotated (§7) |
| CF Worker admin API | f2-api `/api/admin/*` | port routes; data reads become SQL on `csweb_f2` instead of AS RPCs |
| CF KV `F2_AUTH` | `csweb_f2.auth_*` tables | revocation, token audit, admin sessions, RBAC cache |
| CF R2 `f2-admin*` | `/opt/app/f2-files` (borg-backed) | copy existing objects once |
| Apps Script + Sheet | **retired to read-only archive** | final poller sync = the backfill; Sheet kept frozen as the pre-migration record |
| `F2_HCWs` / `F2_Config` sheets | `csweb_f2.f2_hcws` / `f2_config` tables | one-time port script; QN assignment logic moves into f2-api (port of `adminHcwsCreate`) |
| GH Action `cf-pages-deploy` | build + rsync-to-box deploy job | staging path first, prod on merge to `main`, same CI gate |

## §3 Phases (each gated; nothing user-facing until P5)

**P0 — Already done / in flight.** `csweb_f2` mirror live + cron'd; unified dashboard; 12-digit
QN code-complete. *Fold-in:* the three QN deploy gates (clasp+`runAllMigrations()`, wrangler,
staging→prod) ship on the CURRENT stack first — they keep UAT coherent while P1 is built, and
the app/claims work carries over unchanged. `[Carl-gated]`

**P1 — Build f2-api** (the long pole). Node/Hono service in the staging worktree
(`deliverables/F2/PWA/server/`), porting: submit/batch/verify-token (respondent-critical),
then admin (sessions/RBAC/users/HCWs+QN/data/files/encode). Reuses the app's existing test
discipline (vitest; contract tests against the same fixtures the Worker tests use). Two
tracks deliberately: **P1a respondent path** (pretest-blocking) and **P1b admin path** (may
trail by days — admins are ~3 people on a low-traffic surface; never blocks the pretest).
`[build — me]` GATE: parity test suite green (same cases as worker tests).

**P2 — Stand up dark.** Compose service + `mem_limit` + healthcheck; auth tables DDL into
`csweb_f2`; `f2-files` volume; nginx vhost + DNS `uhc-hcw.asiansocial.org` + Elestio TLS. Dark —
serves only a health endpoint. `[Carl-gated: DNS + compose merge]` GATE: `curl https://uhc-hcw.asiansocial.org/api/health` 200; RAM delta within budget; CSWeb sync unaffected.

**P3 — App re-point + staging smoke.** `VITE_F2_PROXY_URL=https://uhc-hcw.asiansocial.org` build;
static deployed to the vhost; CI rewired (build→rsync). GATE: full happy-path in a browser
against the dark stack (enroll → consent → submit → row lands in `csweb_f2` → dashboard tile
moves) + `tsc -b --force` + suites green.

**P4 — Registry + config cutover (greenfield).** Final poller sync (`--backfill`, expect
`errors=0`); port `F2_HCWs`/`F2_Config`/admin users Sheet→MySQL (one-time script, counts
verified); R2 objects copied. From here `csweb_f2` is authoritative; AS/Sheet write path
disabled (kill_switch) so nothing diverges. `[Carl-gated: the authority flip]`
GATE: row/registry counts match ±0; a canary submit lands ONLY in MySQL.

**P5 — UAT re-enrollment smoke round.** Reissue tokens for the UAT roster (new origin);
testers re-enroll at `uhc-hcw.asiansocial.org`, run the R6-style checklist (self-admin submit,
refusal path #825, admin dashboards, offline queue). The QN now assigns end-to-end for
9-digit-facility enrollments. `[testers + Carl go/no-go]` GATE: zero P1-severity findings.

**P6 — Retirement + hardening.** CF Pages/Worker → dark fallback (redirect page to the new
origin, kept ~30 days); AS deployment archived read-only; **rotate `HMAC_SECRET` + JWT
signing key** (also closes the in-chat-transit item from the mirror walk); purge stale
`.env.local` secrets; add `csweb_f2` + `f2-files` to borg; freshness/alert line for f2-api
in the monitoring layer. `[Carl-gated: rotations + CF changes]`

**P7 — Pretest-ready sign-off.** One-page checklist: URL live · store authoritative ·
dashboard native · backups verified · rollback documented (CF stack intact until +30d) ·
UAT roster re-enrolled · ASPSI told the new URL. **This is the "F2 migration complete"
line item for the sprint DoD.**

## §4 Effort vs the window

P1a+P2+P3 ≈ 1.5–2 focused days · P4+P5 ≈ 0.5–1 day · P1b admin port ≈ 1–1.5 days (may trail)
· P6 ≈ 0.5 day. **Respondent-path pretest-ready in ~3 days of work**; admin trail never blocks.
If ASPSI lands a pretest date before P4: fallback posture = pretest on the CURRENT stack
(it works today; the mirror keeps monitoring unified) and cut over immediately after — the
plan degrades gracefully instead of racing the field.

## §5 Risks & mitigations

- **Origin change** → whole point of pre-pretest timing; UAT-scale re-enrollment only (P5).
- **CSWeb blast radius** → container isolation, `mem_limit`, separate vhost; Option B escape
  hatch documented if load ever misbehaves.
- **Admin-port scope creep** → two-track P1; admin explicitly allowed to trail the pretest.
- **DNS/TLS propagation** → stand up dark (P2) days before any traffic depends on it.
- **Rollback at every phase** → the CF/Google stack stays intact and dark until P6+30d;
  reverting = repoint `VITE_F2_PROXY_URL` and re-enable the AS write path.

## §6 What this does NOT touch

F1/F3/F4 CSPro instruments (freeze stands) · CSWeb sync · the monitoring dashboard (it just
switches from mirror-read to store-read) · the tabulation/ETL lane.

## §7 Secrets (names only — values are Carl-placed)

`JWT_SIGNING_KEY` (carried, then rotated P6) · `MYSQL_ROOT_PASSWORD` → replaced by a
least-priv `f2api` MySQL user at P2 · `APPS_SCRIPT_URL`/`APPS_SCRIPT_HMAC` retire at P4
(rotate on retirement) · admin password hashes migrate as hashes.

## §8 Open items owed by ASPSI (tracked, not blocking the build)

Pretest date (gates P5 scheduling) · F2 facility frame with 9-digit codes (lights up QN
auto-assignment, geo names, coverage-vs-target) · UAT roster confirmation for re-enrollment.
