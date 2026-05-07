---
title: E4-APRT-039 — M10 sunset · ADMIN_PASSWORD_HASH deletion (staging)
date: 2026-05-04
sprint: 004
goal: Goal B
status: superseded — see postscript at top
related:
  - docs/superpowers/runbooks/2026-05-01-ap0-apps-script-staging-setup.md
  - docs/superpowers/runbooks/2026-05-02-f2-admin-portal-prod-cutover.md
  - deliverables/F2/PWA/worker/scripts/hash-admin-password.mjs
  - scrum/sprint-current.md
---

# E4-APRT-039 — M10 sunset · `ADMIN_PASSWORD_HASH` deletion (staging)

> ⚠️ **POSTSCRIPT 2026-05-04 — runbook misframed; replaced by inline action.**
>
> The original draft of this runbook (below, retained for the record) framed E4-APRT-039 as a **rotation** of `ADMIN_PASSWORD_HASH` followed by a 7-day soak. That framing was wrong. The canonical task per `scrum/epics/epic-04-backend-sync-infrastructure.md` is **M10 sunset = backup + delete** the orphaned legacy secret; the new Admin Portal uses `/admin/api/login` (checks F2_Users sheet via Apps Script), not `/admin/login` (legacy single-admin secret path).
>
> **What was actually done on 2026-05-04:**
> 1. Generated + pushed a new hash to `ADMIN_PASSWORD_HASH` on staging (harmless misstep — see Sprint 004 Day 1 note in `sprint-current.md`).
> 2. Smoke-tested both paths — confirmed `/admin/login` already returns 500 on any input (pre-existing Phase F collateral) and `/admin/api/login` is unaffected by the secret value.
> 3. Deleted `ADMIN_PASSWORD_HASH` from staging Worker via `wrangler secret delete ADMIN_PASSWORD_HASH --env staging`.
> 4. Post-delete verification: legacy path still 500s (no regression); portal returns 200 for `carl_admin / 100%SetupMe!`.
> 5. **Soak waived** — the legacy path was already non-functional pre-deletion, so 7-day observation would add no information.
>
> **Production-side equivalent** (delete `ADMIN_PASSWORD_HASH` from `f2-pwa-worker.workers.dev`) ships with **E4-APRT-040 v2.0.0** in Sprint 005, per the existing prod-cutover runbook (`docs/superpowers/runbooks/2026-05-02-f2-admin-portal-prod-cutover.md`).
>
> **Open follow-up:** the legacy `/admin/login` route on the staging Worker returns HTTP 500 on any input — likely auth re-arch collateral. Worth a separate issue + fix or removal of the route handler in source.
>
> ---
>
> **The original runbook below is RETAINED FOR THE RECORD but should not be executed.**

---

# (Original draft — DO NOT EXECUTE)

> Sprint 004 Goal B opener. Rotates the staging Worker's admin password hash off the in-chat-shared one, smoke-tests the round trip, then opens the 7-day soak window with daily monitoring. v2.0.0 ship (E4-APRT-040) lands in Sprint 005 once the soak clears clean.

## Pre-flight (read before typing)

- [ ] Confirm PR #47 (PBKDF2 100k cap fix) is on `staging` — check `git log origin/staging --oneline | head -10` for it. If not, halt — the script's 100k iters won't verify.
- [ ] Pick the new admin password (≥12 chars per `hash-admin-password.mjs:80`). Keep it in your password manager **before** running the rotation; if the wrangler push fails mid-flight you'll need it again on retry.
- [ ] Have Slack `#capi-scrum` open — post a one-liner before/after so the post-commit hook isn't the only signal.
- [ ] Log start of work in `log.md` (one line: "E4-APRT-039 start — staging admin pwd rotation").

## Step 1 — Generate the new hash (~3 min)

Run from the worker directory:

```powershell
Set-Location deliverables/F2/PWA/worker
node scripts/hash-admin-password.mjs
```

You'll be prompted: `Admin password (not echoed): `. Type the new password, press Enter. Output is one line in the form `<saltB64url>:<iterations>:<hashB64url>` (iterations will be `100000`).

**Copy the entire output line** — you'll paste it in Step 2. Don't trim whitespace; don't include the surrounding helper text.

> Sanity check: there should be exactly 2 colons in the output. Salt + 100000 + hash.

## Step 2 — Push the secret to staging Worker (~2 min)

From the same directory:

```powershell
wrangler secret put ADMIN_PASSWORD_HASH --env staging
```

Wrangler prompts for the secret value — **paste the full hash line from Step 1 and press Enter**. Wrangler confirms with something like:

```
✨  Success! Uploaded secret ADMIN_PASSWORD_HASH
```

> Gotcha (memory `reference_apps_script_deploy_gotchas.md`): on Windows PowerShell, copying from the terminal output to clipboard sometimes prepends a BOM byte. If the smoke test in Step 3 returns 401 with a hash you're sure is right, BOM is the most likely cause — re-run Step 2 and paste from the script's stdout directly (not via a screen-scrape).

## Step 3 — Smoke test: login round-trip (~5 min)

Verify the new hash actually verifies:

```powershell
curl.exe -i -X POST "https://f2-pwa-worker-staging.hcw.workers.dev/admin/api/login" `
  -H "Content-Type: application/json" `
  -d '{"username":"carl_admin","password":"<NEW_PASSWORD_HERE>"}'
```

(Substitute the actual new password into the JSON body. Single quotes are safe in PowerShell here; if your password contains a single quote, switch to a here-string.)

Expected:
- `HTTP/2 200`
- `Set-Cookie: f2_admin_jwt=...; HttpOnly; Secure; SameSite=Strict; Max-Age=3600` (or whatever the configured TTL is)
- JSON body with `{"ok":true, ...}`

Then verify the **old** password is dead:

```powershell
curl.exe -i -X POST "https://f2-pwa-worker-staging.hcw.workers.dev/admin/api/login" `
  -H "Content-Type: application/json" `
  -d '{"username":"carl_admin","password":"100%SetupMe!"}'
```

Expected: `HTTP/2 401` with `{"ok":false,"error":"invalid_credentials"}` (or equivalent).

If both checks pass, the rotation is live.

## Step 4 — Update the staging credentials memory

The memory `project_f2_admin_staging_creds.md` currently records `carl_admin / 100%SetupMe!`. After Step 3 verifies, update the memory in place:

```
Username: carl_admin
Password: stored in 1Password (or your password manager) — entry "F2 Admin Staging"
Rotated: 2026-05-04 (E4-APRT-039)
Previous: 100%SetupMe! — DEAD as of 2026-05-04
```

Don't write the new password into a tracked file. The memory entry just points at where it lives.

## Step 5 — Open the 7-day soak window (~5 min)

Soak window: **2026-05-04 → 2026-05-11** (7 calendar days). Daily monitoring cadence:

1. **Once per day** (suggested: end of work day, ~17:30 PHT), run:
   ```powershell
   wrangler tail --env staging --format pretty
   ```
   Let it run for **5 minutes** while the F2 PWA staging gets a few canary requests (hit `https://f2-pwa-staging.pages.dev` from a tablet or laptop). Watch for:
   - Any `5xx` log lines
   - Any `auth_failure` / `invalid_credentials` log lines beyond your own test taps
   - Any `R2 binding` errors
   - Any cron handler exceptions (the `*/5 * * * *` scheduled trigger)
2. **Spot-check the Cloudflare dashboard** at `https://dash.cloudflare.com/<account>/workers/services/view/f2-pwa-worker-staging/staging/observability` — error-rate chart should hover at 0% or low single digits.

Append one row per day to the journal in Step 6.

### Halt criteria (do NOT continue the soak)

Halt the soak + open an incident note in `log.md` if **any** of:
- Sustained 5xx error rate **>0.5% over any 1-hour window** (visible on the dashboard chart)
- **Auth failure spike** of >10 invalid_credentials logs/hour from non-test traffic
- Any **R2 write failure** during the 5-min cron windows
- **Anything that looks like a leak** of secrets in logs (defense in depth — staging-only, but still)

If halt: investigate, document, and reset the soak clock from the day after the fix.

## Step 6 — Daily monitoring journal

Maintain at `deliverables/F2/PWA/worker/soak-journal-2026-05-04.md`. Append-only.

```markdown
| Date | Time (PHT) | wrangler tail (5 min): notable lines | Dashboard error rate | Halt? | Notes |
|---|---|---|---|---|---|
| 2026-05-04 | 17:30 | … | 0% | no | soak day 1 — opened today |
| 2026-05-05 | … | … | … | … | … |
| 2026-05-06 | … | … | … | … | … |
| 2026-05-07 | … | … | … | … | … |
| 2026-05-08 | … | … | … | … | … |
| 2026-05-09 | … | … | … | … | … |
| 2026-05-10 | … | … | … | … | … |
| 2026-05-11 | … | … | … | … | END — soak target hit; promote to E4-APRT-040 v2.0.0 ship |
```

> Two of those days (2026-05-09 / 2026-05-10) are weekend. Daily-discipline isn't a CSA requirement; if you skip a day, just note "skipped — no traffic expected" in the row. The point is to catch creeping issues, not perform discipline theater.

## Step 7 — Sprint board hygiene

After Step 3 verifies green:
- Flip `E4-APRT-039` in `scrum/sprint-current.md` from `status::todo` → `status::in-progress` (the soak is now running).
- The Dataview board (`scrum/sprint-board.md`) auto-reflects.
- It moves to `status::done` only on **2026-05-11** (or earlier if halted) when the soak clears clean. v2.0.0 ship (`E4-APRT-040`) is then unblocked for Sprint 005.

## Append to log.md

One-line entry after Step 3 verifies:
```
2026-05-04 — E4-APRT-039 staging admin pwd rotated; old password dead; soak window opened (target close 2026-05-11). v2.0.0 ship pending soak clear.
```

## What NOT to do

- **Don't rotate production yet.** Production Worker (`f2-pwa-worker.hcw.workers.dev`) still uses the pre-cutover credentials; that rotation rides with E4-APRT-040 v2.0.0 ship in Sprint 005.
- **Don't bump PBKDF2 iterations above 100k.** Hard cap on Workers runtime; verifier rejects > 100k. (See Issue #35 + the `MAX_PBKDF2_ITERS` const in `worker/src/admin.ts`.)
- **Don't skip the smoke test.** A bad hash that wrangler accepts will lock you out of the staging admin portal until you re-run Steps 1–3 — and the wrangler-side rotation is non-reversible, so the only way back is forward.
