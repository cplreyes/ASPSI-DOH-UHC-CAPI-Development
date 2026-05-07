# AP0 — Apps Script Staging Setup Runbook

**Date drafted:** 2026-05-01
**Owner:** Carl Patrick Reyes
**Drives:** F2 Admin Portal Sprint AP1 unblock (Tasks 1.5, 1.6, 1.10, 1.13, 1.15, 1.16) and all Sprint 2/3/4 backend RPCs
**Design spec:** `docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md`
**Implementation plan:** `docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md`
**Estimated time:** 30–45 min, all in your Google account; no production touch points.

---

## Why this needs a runbook

The F2 Admin Portal worker code is feature-complete on `f2-admin-portal` through Task 1.17 — login, RBAC, logout, throttle, and HMAC client all unit-tested — but the worker can't be smoke-tested against a real Apps Script backend without an isolated staging environment. Pointing the worker at production AS would mean seeding admin users into the live F2_Users sheet and signing requests with the production HMAC secret, both of which are unrecoverable mistakes.

AP0 builds a parallel AS deployment:

```
                   PRODUCTION (untouched)                STAGING (new)
                   ─────────────────────                 ─────────────
Sheets workbook    "F2 PWA Backend — 2026-04-XX"         "F2 PWA Backend — Staging"
AS project         F2-PWA-Backend                        F2-PWA-Backend-Staging
Web App URL        https://script.google.com/.../exec    https://script.google.com/.../exec  (different /s/ id)
HMAC secret        PROP_HMAC_SECRET (production)         PROP_HMAC_SECRET (fresh, staging-only)
Worker secrets     APPS_SCRIPT_URL/HMAC (production)     APPS_SCRIPT_URL/HMAC (--env staging)
```

Once AP0 lands, every remaining Sprint AP1 task can run end-to-end: deploy AS → push worker to `--env staging` → curl the Web App URL → see real round-trip.

---

## Pre-flight

- [ ] You're signed into Google as `aspsi.doh.uhc.survey2.data@gmail.com` (the project mailbox).
- [ ] You're on the `f2-admin-portal` branch with no uncommitted changes (`git status` is clean).
- [ ] Local node is set up so `npm run build` works in `deliverables/F2/PWA/backend/`.
- [ ] `wrangler` is authed as the same Google identity (`wrangler whoami`).

If any of those fail, fix them first — none are AP0 work, they're prerequisites you've done before.

---

## Part 1 — Create the staging Sheets workbook (5 min)

1. Go to https://sheets.google.com (signed in as the project mailbox).
2. Blank → name it **`F2 PWA Backend — Staging`** (the human-readable name doesn't matter to the code, only the spreadsheet ID does).
3. Star the file or drop it in a "F2 / staging" Drive folder so it doesn't get lost.
4. Copy the spreadsheet ID from the URL — it's the long string between `/d/` and `/edit`. You'll paste it into Script Properties in Part 2.

**Why a separate workbook (not a tab in the production sheet):** AS Migrations.js operates on `SpreadsheetApp.getActiveSpreadsheet()` and creates 5 new sheets. Running it against production would litter the live workbook. Cleaner to keep them physically separate.

---

## Part 2 — Create the staging Apps Script project (10 min)

### 2a. Build the bundle locally

```powershell
cd deliverables\F2\PWA\backend
npm run build
```

This emits `dist/Code.gs` and `dist/appsscript.json`. The bundle now includes `Migrations.js` and `AdminAudit.js` (Task 2.7 fixed `scripts/build.mjs` ORDER). One paste, one bundle.

### 2b. Create the AS project

1. Go to https://script.google.com → **New project**.
2. Rename to **`F2-PWA-Backend-Staging`** (top-left).
3. Replace the default `Code.gs` contents with the contents of `dist/Code.gs`.
4. Project Settings (gear icon) → **Show "appsscript.json" manifest file in editor** → check the box.
5. Back in the editor, open `appsscript.json` and replace its contents with `dist/appsscript.json`.

Save (Ctrl+S).

### 2c. Bind the Sheets workbook

In the AS editor, open Project Settings → **Script Properties** → **Add script property**:

- Property: `SPREADSHEET_ID`
- Value: the spreadsheet ID you copied in Part 1.

This wires the AS project to your staging workbook (the existing `Setup.js` reads this property to find its target sheet).

### 2d. Run setupBackend()

1. In the editor, top dropdown → select function `setupBackend`.
2. Click **Run**.
3. First run prompts for OAuth — review scopes (Sheets, Script Properties), allow.
4. Wait for "Setup complete" in the Execution log.

This creates the base sheets (`F2_Responses`, `F2_Audit`, `F2_Config`, `Facility_Master_List`, `F2_DLQ`) and generates a fresh `HMAC_SECRET` ScriptProperty.

### 2e. Run runAllMigrations()

1. Top dropdown → `runAllMigrations` → Run.
2. Verify the log: should report 5 admin sheets created (`F2_Users`, `F2_Roles`, `F2_HCWs`, `F2_FileMeta`, `F2_DataSettings`) plus the column extensions on `F2_Responses` and `F2_Audit`.
3. Open the staging workbook in another tab and confirm the new sheets exist with the documented columns.

---

## Part 3 — Capture the staging HMAC secret + Web App URL (5 min)

### 3a. Read the staging HMAC secret

Project Settings → Script Properties → copy the value of `HMAC_SECRET`.

**This is staging-only**, distinct from production. Do **not** commit it; do **not** post it in Slack. Keep it in a temporary buffer for Part 4 — you'll paste it into `wrangler secret put` once and then it lives only in Cloudflare.

### 3b. Deploy as Web App

Editor → **Deploy** → **New deployment** → cog icon → **Web app**:

- Description: `staging v1`
- Execute as: **Me** (`aspsi.doh.uhc.survey2.data@gmail.com`)
- Who has access: **Anyone** (the worker is the only caller; HMAC verifies authenticity)
- → **Deploy**

Copy the Web App URL (`https://script.google.com/macros/s/<staging-id>/exec`). Save it for Part 4.

### 3c. Smoke-test the bare AS deployment (optional but cheap)

```powershell
curl.exe -X POST "<staging Web App URL>" -H "Content-Type: application/json" -d "{}"
```

Expected response: `{"ok":false,"error":{"code":"E_AUTH","message":"..."}}` (or similar — anything that's a JSON error body proves the Web App is alive and rejecting unsigned requests).

---

## Part 4 — Configure the Worker staging environment (10 min)

### 4a. Add the `[env.staging]` block to wrangler.toml

Edit `deliverables/F2/PWA/worker/wrangler.toml`. Add a staging environment block that inherits the bindings but overrides the worker name so it deploys to a separate staging Worker:

```toml
[env.staging]
name = "f2-pwa-worker-staging"

[[env.staging.kv_namespaces]]
binding = "F2_AUTH"
id = "<TBD — create with wrangler kv:namespace create F2_AUTH --env staging>"
preview_id = "<TBD>"

[[env.staging.r2_buckets]]
binding = "F2_ADMIN_R2"
bucket_name = "f2-admin-staging"
preview_bucket_name = "f2-admin-staging-preview"
```

Then create the staging KV namespace and bucket:

```powershell
cd deliverables\F2\PWA\worker
wrangler kv:namespace create F2_AUTH --env staging
wrangler kv:namespace create F2_AUTH --env staging --preview
# (R2 bucket creation only works after R2 is enabled on the account — see "R2 deferred" below.)
```

Paste the returned IDs into the `id` and `preview_id` fields and commit the wrangler.toml change.

> **R2 deferred:** R2 isn't yet enabled on the ASPSI Cloudflare account. The R2 binding under `[env.staging]` will fail to deploy until you click "Purchase R2 Plan" in the Cloudflare dashboard. If you want to defer this and get login/logout smoke-testing first, comment out the `[[env.staging.r2_buckets]]` block — Sprint 1 doesn't exercise R2.

### 4b. Set the staging secrets

```powershell
cd deliverables\F2\PWA\worker
wrangler secret put APPS_SCRIPT_URL --env staging
# Paste the staging Web App URL from Part 3b.

wrangler secret put APPS_SCRIPT_HMAC --env staging
# Paste the staging HMAC_SECRET from Part 3a.

wrangler secret put JWT_SIGNING_KEY --env staging
# Generate a fresh staging key — DO NOT reuse production:
#   openssl rand -base64 32 | tr -d '=' | tr '+/' '-_'
# Or in PowerShell:
#   [Convert]::ToBase64String([byte[]]([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))) -replace '\+','-' -replace '/','_' -replace '=',''

wrangler secret put ADMIN_PASSWORD_HASH --env staging
# Sunsetting M10 secret. Set to the literal string "deprecated" — staging tests
# don't exercise the M10 admin path, and the worker's Env type still requires it.
```

### 4c. Deploy the worker to staging

```powershell
wrangler deploy --env staging
```

Save the deployed worker URL (`https://f2-pwa-worker-staging.<account>.workers.dev`).

---

## Part 5 — Smoke-test the round trip (5 min)

This is the same shape as Task 1.16's planned E2E smoke, run early to validate AP0:

```powershell
# Expect 401 E_AUTH_INVALID (no users seeded yet — but this proves the
# worker reaches AS, AS verifies the HMAC, and AS returns "no users").
curl.exe -X POST "https://f2-pwa-worker-staging.<account>.workers.dev/admin/api/login" `
  -H "Content-Type: application/json" `
  -d '{\"username\":\"nobody\",\"password\":\"x\"}'
```

Expected: HTTP 401, body `{"ok":false,"error":{"code":"E_AUTH_INVALID",...}}`, response header `X-Request-Id: <uuid>`.

If you get **502 E_BACKEND** instead, the worker reached the worker but AS rejected — most likely an HMAC mismatch (re-check Part 4b's `APPS_SCRIPT_HMAC` matches the staging `HMAC_SECRET` you saved in Part 3a, byte-for-byte, no whitespace).

If you get **500** or a Cloudflare error page, the staging Worker isn't deployed correctly — `wrangler tail --env staging` to see the live logs.

---

## Definition of done

AP0 is complete when:

- [ ] Staging Sheets workbook exists with all migrated tabs (`F2_Users`, `F2_Roles`, `F2_HCWs`, `F2_FileMeta`, `F2_DataSettings`, plus extended `F2_Responses` and `F2_Audit` columns).
- [ ] Staging AS project deployed as Web App; URL captured.
- [ ] `[env.staging]` block + KV namespace exist in `wrangler.toml` (committed).
- [ ] Worker staging secrets set: `APPS_SCRIPT_URL`, `APPS_SCRIPT_HMAC`, `JWT_SIGNING_KEY`, `ADMIN_PASSWORD_HASH`.
- [ ] `wrangler deploy --env staging` succeeds.
- [ ] Smoke curl against `/admin/api/login` returns 401 E_AUTH_INVALID with `X-Request-Id` header (proves the round trip).

Once those check, Sprint AP1 is unblocked. Pick up at Task 1.5 (AS HMAC verifier on doPost — needs the staging deployment to test) and proceed in plan order.

---

## Rollback / recovery

AP0 is **additive**. Production is never touched. If anything goes wrong:

- Delete the staging AS project (script.google.com → file → move to trash).
- Delete the staging Sheets workbook.
- `wrangler delete f2-pwa-worker-staging` to remove the staging Worker.
- Revert the `[env.staging]` block in `wrangler.toml`.

Production keeps running on the existing AS deployment + main worker the whole time.

---

## Notes for production cutover (Sprint 4, future)

When Sprint 4 cuts the admin portal over to production AS, you'll re-run `npm run build` and re-paste `dist/Code.gs` into the **production** AS project, then run `runAllMigrations` and (optionally) `backfillSourcePath` on the production sheet. Both migrations are idempotent — re-running is safe.
