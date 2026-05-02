# F2 Admin Portal — Production Cutover Runbook

**Date drafted:** 2026-05-02
**Owner:** Carl Patrick Reyes
**Drives:** Sprint AP4 Task 4.10 (v2.0.0 release). This is the production analog of AP0 (`2026-05-01-ap0-apps-script-staging-setup.md`). Read AP0 first if you haven't done it — this runbook assumes the same shape.
**Design spec:** `docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md`
**Implementation plan:** `docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md`
**Estimated time:** 45–60 min once all prerequisites are met. Most of that is paste-and-deploy.

---

## When to run this

Run this **after** all of the following are true:

1. **`f2-admin-portal` PR is merged to `main`** — production deploys from `main`. If the PR is still open, finish review first.
2. **R2 is enabled** on the ASPSI Cloudflare account (`Aspsi.doh.uhc.survey2.data@gmail.com's Account`, ID `b0887ce8ba4e531c00abfe0127b4bc5b`). If `wrangler r2 bucket create` errors with "R2 not enabled", click "Purchase R2 Plan" in the dashboard first.
3. **Staging soak completed** — at least 7 days of staging traffic with the Sprint AP1–AP4 features live, no unexplained errors in `wrangler tail f2-pwa-worker-staging`. If you're cutting earlier, document why.
4. **You're hands-on at a Windows PowerShell** signed into Google as `aspsi.doh.uhc.survey2.data@gmail.com` with `wrangler whoami` reporting the same identity.

If any of those is false — STOP. Cutting over with broken prereqs leaves you with a half-migrated production stack and no clean rollback.

---

## Pre-flight (5 min)

Run these first; they're cheap and they catch the common gotchas.

```powershell
cd C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development
git checkout main
git pull
git status
# Working tree should be clean. If not, stash or commit before continuing.

cd deliverables\F2\PWA\backend
npm test
# Backend should be green (~173 tests).
npm run build
# Should emit dist/Code.gs > 100k chars.

cd ..\worker
wrangler whoami
# Identity must be aspsi.doh.uhc.survey2.data@gmail.com.
```

If any step errors — STOP.

---

## Architecture overview

```
                   STAGING (parallel)                      PRODUCTION (cutover target)
                   ─────────────────                       ───────────────────────────
Sheets workbook    F2 PWA Backend — Staging                F2 PWA Backend — <prod name>
AS project         F2-PWA-Backend-Staging                  F2-PWA-Backend
Web App URL        https://script.google.com/macros/s/.../exec (existing prod /s/ id)
HMAC secret        24c7d... (staging, ROTATE)              PROP_HMAC_SECRET (production, untouched)
Worker secrets     --env staging                           production (no --env flag)
KV namespace       4235ee802d3546b8a20dffa7a5af5ad3        9b293e0c661d4f60b513facc61b11e0b
R2 bucket          f2-admin-staging (after R2 enabled)     f2-admin
Cron               */5 * * * *                              */5 * * * *
```

The production AS project, Sheets workbook, and HMAC secret all already exist (Phase F was Apr 26). This runbook just adds the admin portal RPCs to the production deployment and turns on R2 + the cron + the new worker bindings.

---

## Part 1 — Run the schema migration on production sheet (10 min)

This is the only **destructive** step in the entire runbook. Read carefully.

### 1a. Snapshot the production sheet first

1. Open the production "F2 PWA Backend — <prod name>" workbook.
2. File → Make a copy → name it `F2 PWA Backend — Pre-AP backup <YYYY-MM-DD>`.
3. Move the copy to a "F2 / pre-cutover backups" Drive folder.

If `runAllMigrations` does anything wrong, you restore from this copy (rename back to original, repoint `SPREADSHEET_ID`). The migration is idempotent and additive but a snapshot is cheap insurance.

### 1b. Paste the bundle into the production AS project

1. https://script.google.com → open the **production** `F2-PWA-Backend` project (NOT the staging one).
2. Editor → `Code.gs` → Ctrl+A → delete.
3. Open `deliverables\F2\PWA\backend\dist\Code.gs` (latest build, should be > 115k chars). Select all → copy → paste into editor.
4. Ctrl+S to save. Wait for "Saved" indicator.
5. If `appsscript.json` differs from `dist/appsscript.json` (oauthScopes), update it the same way. Otherwise skip.

**Do not deploy yet** — we run the migration first against the editor's HEAD code (no Web App version bump needed for the function call).

### 1c. Run the migration

1. AS editor → function dropdown → `runAllMigrations` → Run.
2. Watch the Execution log:
   - Should report `created: ['F2_Users','F2_Roles','F2_HCWs','F2_FileMeta','F2_DataSettings']` (5 new admin sheets).
   - Should report `added: [...]` for the F2_Responses extension columns and the F2_Audit extension columns. **First-run on production will add columns; second-run is a no-op.**
3. Switch to the production Sheets tab. Verify all 5 admin tabs appear.

If `runAllMigrations` fails partway, restore from the 1a backup, delete the corrupted partial sheets, and investigate before retrying. The migration uses `getF2Spreadsheet()` which falls back to `openById(SPREADSHEET_ID)` if the script isn't bound — so it should work in both bound and standalone modes, but verify which mode the production AS is in via Project Settings → Script Properties (does `SPREADSHEET_ID` exist?).

### 1d. Deploy the new Web App version

1. AS editor → top-right Deploy → **Manage deployments**.
2. Existing production deployment → ✏️ pencil → Version: **New version**.
3. Description: `Admin Portal v2.0.0 — sprint AP1-AP4`.
4. Click Deploy → confirm.

The Web App URL stays the same. The PWA + worker continue to talk to it as before; the new admin RPCs just become available.

---

## Part 2 — Seed the first production admin (5 min)

Mirror of AP0 Part 4, but pointed at production.

### 2a. Capture production HMAC

1. Production AS project → Project Settings → Script Properties.
2. Copy the value of `HMAC_SECRET` to a temporary scratchpad (NOT the staging value — these are different).

### 2b. Seed the first admin via the bootstrap script

```powershell
cd C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development\deliverables\F2\PWA\worker

# Production AS Web App URL (paste yours from Manage Deployments dialog):
$env:APPS_SCRIPT_URL  = "https://script.google.com/macros/s/<PROD_DEPLOYMENT_ID>/exec"
$env:APPS_SCRIPT_HMAC = "<production HMAC_SECRET from Part 2a>"

node scripts/seed-staging-admin.mjs `
  --username carl_admin `
  --password '<choose a strong production password — DO NOT reuse staging>' `
  --first-name Carl `
  --last-name Reyes `
  --email carlpatricklreyes@gmail.com
```

The script prints `DONE` when both the Administrator role + the user row are created. If the role already exists from staging-side testing (it shouldn't, on production), the script handles E_CONFLICT idempotently and continues.

### 2c. Seed the second Administrator (per spec §8 — two-admin minimum)

Repeat the seed command for a backup Administrator. Spec requires ≥2 Administrators so a single password loss doesn't lock out the org. If you don't have a co-Administrator yet, create a placeholder:

```powershell
node scripts/seed-staging-admin.mjs `
  --username admin_breakglass `
  --password '<random 16+ char password>' `
  --first-name "Break" --last-name "Glass" --email TBD@aspsi.com.ph
```

Store the breakglass password in 1Password / a sealed envelope. Update the email to a real co-admin's address as soon as that person is identified.

---

## Part 3 — Configure production worker (15 min)

### 3a. Create production R2 buckets

> **DONE 2026-05-02** — R2 enabled on the account; `f2-admin` + `f2-admin-preview` (and the staging mirrors `f2-admin-staging` + `f2-admin-staging-preview`) created via `wrangler r2 bucket create`. Verify with:
>
> ```powershell
> wrangler r2 bucket list
> ```
>
> Expect all four buckets present, APAC region, default Standard storage class. If anything's missing, rerun the `create` commands below.

```powershell
cd C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development\deliverables\F2\PWA\worker
wrangler r2 bucket create f2-admin
wrangler r2 bucket create f2-admin-preview
```

If both succeed, R2 is enabled and the production buckets exist. If they error with "R2 not enabled", enable R2 in the Cloudflare dashboard first (Purchase R2 Plan) and rerun.

The production `wrangler.toml` already declares the `f2-admin` R2 binding at the top level (Sprint 1 Task 1.1), so no toml change is needed.

### 3b. Set production worker secrets

The production worker `f2-pwa-worker` (no `-staging` suffix) already has `JWT_SIGNING_KEY`, `APPS_SCRIPT_URL`, and `APPS_SCRIPT_HMAC` set from Phase F. Verify and rotate as needed:

```powershell
# Verify each secret is set (won't reveal value):
wrangler secret list

# If JWT_SIGNING_KEY is older than ~3 months, rotate it. ANY rotation invalidates
# all in-flight JWTs — every admin must re-login. Schedule for off-hours.
$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
$key = [Convert]::ToBase64String($bytes) -replace '\+','-' -replace '/','_' -replace '=',''
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText("C:\Users\analy\AppData\Local\Temp\jwt.txt", $key, $utf8NoBom)
cmd.exe /c "type C:\Users\analy\AppData\Local\Temp\jwt.txt | wrangler secret put JWT_SIGNING_KEY"
Remove-Item C:\Users\analy\AppData\Local\Temp\jwt.txt
```

> **PowerShell BOM gotcha:** Always use the `cmd.exe /c "type <utf8-no-bom-file> | wrangler secret put ..."` pattern for any secret containing characters that `atob()` parses (URLs, base64 keys, etc.). Direct `"value" | wrangler secret put` adds a UTF-8 BOM that breaks downstream parsing — surfaced during AP0.

### 3c. Verify the production worker config

The production `wrangler.toml` declares one cron trigger and the R2 binding at the top level (no `[env.staging]` scope). Inspect:

```powershell
Get-Content wrangler.toml
```

Confirm:
- `[[kv_namespaces]]` binding `F2_AUTH` with the **production** id (`9b293e0c661d4f60b513facc61b11e0b`).
- `[[r2_buckets]]` binding `F2_ADMIN_R2` with `bucket_name = "f2-admin"`.
- `[triggers]` with `crons = ["*/5 * * * *"]`.
- `[observability]` enabled.

### 3d. Deploy to production

```powershell
wrangler deploy
# (no --env flag = production)
```

Expected output: `Deployed f2-pwa-worker triggers` with `https://f2-pwa-worker.<account>.workers.dev` and `schedule: */5 * * * *`. Save the worker URL.

---

## Part 4 — Smoke-test production (5 min)

Mirror AP0 Part 5, against production.

### 4a. Auth-success smoke

Mirror the staging test. The PWA hits the production worker at the same domain it's been using (`f2-pwa.pages.dev/admin/api/*`).

```powershell
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText(
  "C:\Users\analy\AppData\Local\Temp\login.json",
  '{"username":"carl_admin","password":"<your prod password>"}',
  $utf8NoBom
)
curl.exe -i -X POST "https://f2-pwa.pages.dev/admin/api/login" `
  -H "Content-Type: application/json" `
  --data "@C:\Users\analy\AppData\Local\Temp\login.json"
Remove-Item C:\Users\analy\AppData\Local\Temp\login.json
```

Expected: `HTTP/1.1 200 OK`, body `{"token":"eyJ...","role":"Administrator","role_version":1,...}`, `X-Request-Id` header.

If you get `401 E_AUTH_INVALID`, the seed script didn't run successfully — re-run Part 2.

### 4b. Privileged route smoke

```powershell
$tk = "<paste token from 4a>"
curl.exe -i -X GET "https://f2-pwa.pages.dev/admin/api/dashboards/users" `
  -H "Authorization: Bearer $tk"
```

Expected: `HTTP/1.1 200 OK`, body listing your seeded admins.

### 4c. UI smoke

Browser → `https://f2-pwa.pages.dev/admin/login` → log in with carl_admin → click through:
- Data dashboard (will show real production responses if any exist)
- Reports
- Apps & Settings (Versioning panel populated, Files works now that R2 is bound)
- Users (your seeded admins listed)
- Roles (Administrator + DataReader if you migrated test roles, otherwise just Administrator)
- Sign out → redirects to /admin/login

Don't run mutations on production yet — verify reads first.

---

## Part 5 — M10 sunset (Sprint 4 Task 4.9)

The legacy `ADMIN_PASSWORD_HASH`-gated admin UI in `deliverables/F2/PWA/worker/src/admin.ts` is now dead code. Remove it on a 7-day soak schedule:

1. **Day 0 (today):** Confirm no traffic still hits `/admin/login` (legacy M10 path) by tailing for 5 min: `wrangler tail f2-pwa-worker --search "/admin/login" --status ok`. Should be silent — the new portal uses `/admin/api/login`, distinct path.
2. **Day 0:** Backup `ADMIN_PASSWORD_HASH` value to 1Password / sealed envelope. We're about to delete it.
3. **Day 7:** If still no legacy traffic, `wrangler secret delete ADMIN_PASSWORD_HASH`. Delete the dead routes from `src/admin.ts` (handlers `handleAdminLogin`, `handleIssueToken`, `handleListTokens`, `handleRevokeToken`, `handleAdminUi`) and their wiring in `src/index.ts`. Commit + redeploy.

---

## Part 6 — v2.0.0 release (Sprint 4 Task 4.10)

After Part 5 soak completes:

1. Update `CHANGELOG.md` with v2.0.0 entry covering all sprint AP1–AP4 features + the dogfood-surfaced fixes.
2. Bump `app/package.json` and `app/src/version.ts` to `2.0.0`.
3. Tag the release: `git tag -a v2.0.0 -m "F2 Admin Portal v2.0.0"`.
4. Push tag: `git push origin v2.0.0`.
5. Announce in `#capi-scrum` (the post-commit Slack notifier handles auto-announce on `feat:` commits, but a manual heads-up is appropriate for a major version).

---

## Rollback

If smoke fails or production breaks:

1. **Worker:** `wrangler rollback` (Cloudflare keeps prior versions; pick the pre-cutover one).
2. **AS:** Manage deployments → revert to the prior Web App version. The new admin RPCs become unavailable; the legacy submit/audit/facilities/config/spec-hash paths continue working.
3. **Sheet:** If migrations corrupted data, restore from the Part 1a snapshot copy, repoint `SPREADSHEET_ID` to the restored sheet's id, and rerun `setupBackend` to reattach.
4. **Worker secrets:** Cloudflare doesn't expose old values. If rotation went wrong, re-set from your local backup — that's why Part 5 step 2 says back up before deleting.

The migration is additive — restoring the old AS deployment leaves the new sheets in place, which is harmless (they're just unread).

---

## Operational notes (carry-overs from AP0)

These bit us during AP0 and would bite again on production if not respected:

- **Standalone vs bound AS:** If the production project is a standalone script (Project Settings → no bound document), the `getF2Spreadsheet()` helper depends on `SPREADSHEET_ID` being set. Verify it exists before running migrations.
- **PowerShell + wrangler secret put:** Use `cmd.exe /c "type <file> | wrangler secret put NAME"` with the file written via `[System.IO.File]::WriteAllText(path, value, (New-Object System.Text.UTF8Encoding $false))`. Direct PowerShell pipe adds a UTF-8 BOM that breaks atob() / fetch() / HMAC parsing.
- **AS Web App freeze-at-deploy:** Editor saves don't update the served code until you Deploy → Manage deployments → New version. Re-paste alone is not enough.
- **Cron triggers fire on UTC clock:** `*/5 * * * *` means every 5 minutes from UTC midnight. After redeploy, the next tick is up to 5 min away.
- **Seed script HMAC + URL must match the deployment exactly.** Running seed against the staging URL with production HMAC (or vice versa) silently fails with E_SIG_INVALID — your secret leak is the diagnostic, so triple-check before running.
