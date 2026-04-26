# F2 PWA Auth Cutover Runbook

**Date drafted:** 2026-04-26
**Owner:** Carl Patrick Reyes
**Drives:** Merge of PR #31 (`feat(F2): auth re-arch — Worker JWT proxy replaces HMAC-in-bundle`)
**Design spec:** `docs/superpowers/specs/2026-04-26-f2-pwa-auth-rearch-design.md`
**Estimated total time:** 45–75 min, including a 4–6 min disruption window
**Pick a low-traffic time:** ASPSI overnight Manila (after 22:00 PHT) or a confirmed enumerator-idle hour. Avoid mid-interview windows.

---

## Why this needs a runbook

Three systems must change in a specific order, with a brief window where in-flight requests fail:

```
PWA (Cloudflare Pages)  ──────►  Apps Script /exec
       │                              ▲
       │                              │ HMAC_OLD (in bundle, leaked)
       └─── after cutover ───────►  Worker  ──── HMAC_NEW ───► Apps Script /exec
                                       (PWA re-points; Apps Script accepts only HMAC_NEW)
```

Critical facts:

- The bundled `VITE_F2_HMAC_SECRET` is currently in production (`f2-pwa.pages.dev`, v1.1.1 + matrix view #18). Anyone who downloads the bundle has it.
- Apps Script currently accepts `HMAC_OLD`. Once we rotate `PROP_HMAC_SECRET` to `HMAC_NEW`, every signature with `HMAC_OLD` fails.
- The new PWA bundle (in PR #31) calls the Worker URL instead of Apps Script directly. It does NOT sign with HMAC at all — the Worker does.
- **Therefore:** between rotating Apps Script and deploying the new PWA, nothing reaches the spreadsheet. Tablets running the old bundle queue submissions in IndexedDB (per F2 PWA's offline-first design); they will retry once the new bundle is fetched.

The cutover order minimises this window to ~4–6 minutes.

---

## Pre-flight (before the cutover window)

These can be done at any time. Do them an hour or two before the cutover so the deploy is ready to fire.

### 0.1 — Confirm PR #31 is CI-green

```bash
gh pr view 31 --json mergeable,statusCheckRollup -q '{mergeable, checks: [.statusCheckRollup[] | {name, conclusion}]}'
```

Expected: `mergeable: "MERGEABLE"`, both `app` and `worker` jobs `conclusion: "SUCCESS"`. If `worker` is missing, the new CI job (commit `4c43f12`) hasn't run yet — push a no-op or wait.

### 0.2 — Run worker tests locally one more time

```bash
cd deliverables/F2/PWA/worker
npm ci
npm test -- --run
```

Expect 15 tests passing (jwt: 8, hmac: 4, sentinel: 3).

### 0.3 — Check that no enumerator submission is in-flight

Open `https://script.google.com/macros/s/<id>/exec?action=audit&...` (with current HMAC) or check the Apps Script execution log. If submissions are arriving, postpone or coordinate with ASPSI ops.

---

## Phase A — Provision the Cloudflare Worker

Time: 15–25 min. No production impact yet.

### A.1 — Authenticate wrangler

```bash
cd deliverables/F2/PWA/worker
npx wrangler login
```

If you don't already have a Cloudflare account/API token configured.

### A.2 — Create the KV namespace

```bash
npx wrangler kv:namespace create F2_AUTH
npx wrangler kv:namespace create F2_AUTH --preview
```

Both commands print an `id`. Capture them.

### A.3 — Update `wrangler.toml` with the KV ids

Edit `deliverables/F2/PWA/worker/wrangler.toml`:

```toml
[[kv_namespaces]]
binding = "F2_AUTH"
id = "<paste production id here>"
preview_id = "<paste preview id here>"
```

Commit this on the branch. The auto-commit hook covers `deliverables/`, so it'll push too — that's fine, the values aren't secrets.

### A.4 — Generate `JWT_SIGNING_KEY`

```bash
openssl rand -base64 32 | tr -d '=' | tr '+/' '-_'
```

Capture the 43-character base64url string. This is your worker's HS256 signing key.

### A.5 — Generate `APPS_SCRIPT_HMAC` (the new HMAC, will replace `PROP_HMAC_SECRET`)

```bash
openssl rand -hex 32
```

Capture the 64-character lowercase hex. This is what Apps Script will rotate to in Phase C.

### A.6 — Generate `ADMIN_PASSWORD_HASH`

Pick a strong admin password (≥12 chars). You will need it whenever you mint or revoke tokens via `/admin/`.

```bash
node deliverables/F2/PWA/worker/scripts/hash-admin-password.mjs
# Enter password (not echoed). Capture the printed
# <salt>:<iterations>:<hash> string. iterations = 600,000.
```

### A.7 — Set the four worker secrets

```bash
cd deliverables/F2/PWA/worker
echo "<JWT_SIGNING_KEY from A.4>"     | npx wrangler secret put JWT_SIGNING_KEY
echo "<APPS_SCRIPT_HMAC from A.5>"    | npx wrangler secret put APPS_SCRIPT_HMAC
echo "<ADMIN_PASSWORD_HASH from A.6>" | npx wrangler secret put ADMIN_PASSWORD_HASH
echo "https://script.google.com/macros/s/<deployment-id>/exec" | npx wrangler secret put APPS_SCRIPT_URL
```

Replace `<deployment-id>` with the actual Apps Script web app deployment id you currently use in the PWA.

### A.8 — Deploy the worker

```bash
npx wrangler deploy
```

Capture the deployed worker URL (e.g., `https://f2-pwa-worker.<account>.workers.dev`). You'll need it in Phase D.

---

## Phase B — Test the worker in isolation

Time: 5 min. Worker is live but Apps Script still uses `HMAC_OLD`, so `/exec` will fail. That's expected; we test what we can.

### B.1 — Confirm `/admin/` loads

Open `https://f2-pwa-worker.<account>.workers.dev/admin/` in a browser. You should see the admin UI with a Sign in form.

### B.2 — Sign in and issue a test token

Type the admin password from A.6. After login, fill:
- Facility: `F-001` (or any test value)
- Tablet label: `cutover-smoke-test`
- TTL (days): `7`
Click Issue. The token should display. Copy it. Note the JTI (visible in the table that refreshes below).

### B.3 — Confirm `/exec` rejects unauthorised requests

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST "https://f2-pwa-worker.<account>.workers.dev/exec?action=config"
```

Expected: `400` (missing Authorization header).

### B.4 — Confirm `/exec` rejects malformed bearer

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST -H "Authorization: Bearer not-a-jwt" "https://f2-pwa-worker.<account>.workers.dev/exec?action=config"
```

Expected: `401`.

### B.5 — Revoke the smoke-test token

In `/admin/`, click Revoke next to the `cutover-smoke-test` row. Confirm the table updates.

### B.6 — Don't proceed to /exec smoke test yet

A successful `/exec` round-trip requires Apps Script to accept the worker's HMAC, which is `HMAC_NEW`. Apps Script still has `HMAC_OLD`. The full round-trip happens in Phase D after rotation.

---

## Phase C — Rotate Apps Script (CUTOVER MOMENT — DISRUPTION STARTS)

Time: 1 min. **Active tablets running the old bundle stop working from this point until Phase D completes.**

### C.1 — Open Apps Script project

Open the F2 backend project in Apps Script editor. Path is in `deliverables/F2/PWA/backend/`'s `appsscript.json` deployment notes.

### C.2 — Update `PROP_HMAC_SECRET`

Project Settings → Script Properties → edit `PROP_HMAC_SECRET` → paste the value from A.5 (the new 64-char hex). Save.

### C.3 — Don't re-deploy the Apps Script web app

The web app deployment doesn't need re-deploying — Script Properties take effect immediately. The deployment URL stays the same.

### C.4 — START YOUR STOPWATCH

From this moment, every PWA submission with the old bundle fails. Move to Phase D immediately.

### C.5 — Verify the worker now reaches Apps Script

```bash
# Issue a fresh token via /admin/, capture as TOK
TOK="<paste fresh JWT here>"
curl -s -X GET -H "Authorization: Bearer $TOK" "https://f2-pwa-worker.<account>.workers.dev/exec?action=config"
```

Expected: a valid JSON response from your `handleConfig` (e.g., `{"ok": true, "config": {...}}`). If you get `502 E_BACKEND_UNREACHABLE` or HMAC failure, **the rotation did not stick** — re-check Script Properties in C.2 before proceeding.

---

## Phase D — Activate the new PWA (DISRUPTION ENDS WHEN THIS COMPLETES)

Time: 3–5 min for Cloudflare Pages deploy.

### D.1 — Confirm PR #31 still merges cleanly

```bash
gh pr view 31 --json mergeable -q .mergeable
```

Should be `MERGEABLE`. If not, rebase against `staging`.

### D.2 — Set `VITE_F2_PROXY_URL` on Cloudflare Pages

The PWA reads the worker URL from `VITE_F2_PROXY_URL` (`deliverables/F2/PWA/app/src/lib/env.ts`). It is NOT hardcoded in source; it's a build-time env var picked up by Vite from Cloudflare Pages's environment.

Cloudflare dashboard → Pages → your project → Settings → Environment variables. Set:

| Environment | Variable | Value |
|---|---|---|
| **Preview** (staging) | `VITE_F2_PROXY_URL` | the worker URL from A.8 |
| **Production** (post Phase F) | `VITE_F2_PROXY_URL` | the production worker URL (set during Phase F.1) |

If `VITE_F2_PROXY_URL` is unset at build time, `getSyncEnv()` throws and the PWA fails to render — that's the safety net. There is no fallback to direct Apps Script in the code (HMAC-in-bundle was removed in commit `2a165c0`); the worker is the only path.

Confirm it's set BEFORE the next step (D.3 merge) — the merge auto-triggers a Pages rebuild, and the build will fail without this env var.

### D.3 — Merge PR #31 to staging

```bash
gh pr merge 31 --squash --delete-branch
```

Or merge via GitHub UI if you prefer.

### D.4 — Watch the Cloudflare Pages deploy

```bash
# Cloudflare Pages auto-deploys on push to staging branch.
# Watch the deploy via the dashboard or:
gh run watch
```

Wait until staging shows the new deploy is live (~3 min). The Pages URL is `https://f2-pwa-staging.pages.dev` per `wiki/sources` notes (or whatever's in your Cloudflare Pages config).

### D.5 — STOP YOUR STOPWATCH

Disruption window ends when D.4 finishes.

---

## Phase E — Smoke test on staging

Time: 5–10 min. End-to-end, real PWA, real worker, real Apps Script.

### E.1 — Open staging in a fresh browser

Open `https://f2-pwa-staging.pages.dev/` in an incognito window. Confirm the app loads. Header should still show v1.1.1 + spec version.

### E.2 — Verify the bundle does NOT contain the HMAC

Open DevTools → Sources → Page → find the main JS bundle. Search for `VITE_F2_HMAC_SECRET` — should be gone. Search for the old HMAC value (any 64-char hex token from history) — should not appear. Search for `f2-pwa-worker` — should appear (the worker URL the bundle now calls).

### E.3 — Enroll a test tablet

Go through enrollment. In `/admin/` issue a token for facility `F-001` (or your test facility). Copy the token, paste into the staging PWA's enrollment screen. Confirm enrollment succeeds.

### E.4 — Submit a test interview

Walk through one full interview (use UAT persona `UAT-NURSE-01`). At the end, submit. Confirm:
- The submit-success UI appears.
- The Apps Script audit log (or spreadsheet) shows the new row.
- The Apps Script execution log shows a successful `handleSubmit` call coming from the worker IP.

### E.5 — Confirm IndexedDB-queued submissions drained

If any tablets had submissions queued during the disruption window, they should re-fire automatically once they fetch the new bundle. Check the spreadsheet for any out-of-order or duplicated `client_submission_id` rows; the existing dedup should handle them.

---

## Phase F — Production cutover (separate, scheduled)

Same shape, but on the `main` branch and `f2-pwa.pages.dev`. Run only after Phase E has been clean for at least 24 hours.

Steps:
1. Repeat A.1–A.7 for a **production worker** (e.g., `f2-pwa-worker-prod`). Use a **fresh** JWT_SIGNING_KEY and admin password — never reuse staging secrets in prod.
2. Update `APPS_SCRIPT_URL` to the production Apps Script deployment, if separate from staging.
3. Open a PR `staging → main`.
4. Repeat Phase C–E pointed at production.
5. Decommission the staging worker if it's no longer needed (optional).

---

## Rollback procedure

If anything in Phase D or E shows the wrong data, broken submissions, or any loss of integrity, roll back immediately.

### Rollback option 1 — Revert PR #31 on staging

```bash
git checkout staging
git revert -m 1 <PR #31 merge commit sha>
git push origin staging
```

This restores the old PWA bundle (which signs with `HMAC_OLD`). The bundle is still in production until Cloudflare Pages re-deploys (~3 min).

**Then revert Apps Script:** in Apps Script Script Properties, set `PROP_HMAC_SECRET` back to the value before C.2. (Capture the old value before C.2 — see Pre-flight 0.4 below.)

### Rollback option 2 — Forward-fix on staging

If only certain handlers misbehave, deploy a fix forward. Don't roll back if the forward-fix is small.

### Pre-flight 0.4 — CAPTURE THE OLD HMAC BEFORE C.2

Before rotating Apps Script, copy the current `PROP_HMAC_SECRET` value to a secure local note. You will need it if you have to roll back.

---

## Disruption-window math

- Phase C: 1 min (Apps Script rotation)
- Phase D.3: ~10 sec (PR merge)
- Phase D.4: 3–5 min (Cloudflare Pages deploy)

Total expected disruption: **~4–6 min**.

During this window:
- Active tablets running the old bundle: submissions get HMAC failures from Apps Script. PWA's existing IndexedDB buffer queues them. They retry on next sync.
- New tablets accessing the PWA fresh: get the new bundle (or cached old bundle), hit the worker (or fail), worker reaches Apps Script with new HMAC, success.

---

## Communication template

Slack `#capi-scrum` post (paste before Phase C):

```
F2 PWA auth cutover starts in 5 min. Brief disruption (~5 min) expected
where staging submissions queue locally. Live submissions retry automatically
once the new bundle deploys. Tracking: PR #31, runbook
docs/superpowers/runbooks/2026-04-26-f2-auth-cutover.md.
```

Post again on D.5:

```
F2 PWA auth cutover complete on staging. Smoke testing in progress.
HMAC no longer in client bundle. Worker URL: <A.8>.
```

---

## Post-cutover follow-ups

After Phase F succeeds:

- [ ] Delete `VITE_F2_HMAC_SECRET` from Cloudflare Pages env var settings.
- [ ] Clean up local `deliverables/F2/PWA/app/.env.local` — remove the stale `VITE_F2_BACKEND_URL` and `VITE_F2_HMAC_SECRET` lines (no longer read by the code), add `VITE_F2_PROXY_URL` for local dev.
- [ ] Delete the `?action=admin` HTML and `PROP_ADMIN_SECRET` from Apps Script per spec §3.
- [ ] Lower `ttl_days` max from 365 → 90 in `worker/src/admin.ts:143` (P2 finding from `/review`).
- [ ] Add `purpose` claim to JwtClaims, drop the `__admin_session__` sentinel (P2 finding from `/review`).
- [ ] Add CF Rate Limiting on `/admin/login` (P2 finding from `/review`).
- [ ] Add a `worker-test` health check to `/canary` once `/canary` is wired up.
