# Runbook — E4-PWA-014 / #294: Apps Script Web App redeploy (P0)

**Owner: Carl (requires Google auth on `aspsi.doh.uhc.survey2.data@gmail.com` to open the production AS project).**
Claude cannot execute this; the steps below are exact and copy-pasteable.

> **Revised 2026-05-20.** The original draft of this runbook referenced `clasp` commands, but the F2 backend does **not** use clasp — there's no `.clasp.json`, no clasp dependency in `package.json`, and the established deploy workflow (per `2026-05-04-fx-006-as-push.md` and `2026-05-02-f2-admin-portal-prod-cutover.md`) is **`npm run build` → manual paste into the AS editor → publish new version on the existing deployment**. Trying `clasp push` would have failed at step 1.

## Context

R3 P0 #294. The Worker + frontend shipped v2.0.1 on 2026-05-09 (PR #136,
`9bab42b`), but the **Apps Script Web App was last pushed 2026-05-04** —
before PR #134's `adminUsersChangePassword` / bulk-import handlers. So any
admin with `password_must_change=true` (Shan's R2-reset account, and Marriz
once onboarded) hits **"Unknown admin action: admin_users_change_password"**
on first login. The repo source is correct
(`deliverables/F2/PWA/backend/src/AdminDispatch.js:126`,
`AdminUsers.js:271`); only the deployed artifact is stale. Fix = build +
paste + republish the AS Web App version. **No code change.**

Root-cause class: CF Pages auto-deploys on merge (`cf-pages-deploy.yml`);
the AS source has **no** equivalent workflow, so "merged → live" does not
hold for backend changes. Permanent fix is the v2.0.2 follow-up below.

## Preconditions

- Google session signed in as `aspsi.doh.uhc.survey2.data@gmail.com` (the
  ASPSI mailbox — owner of the production AS project).
- Node.js + npm available (you already have these — the F2 PWA app uses them).
- Working dir: `deliverables/F2/PWA/backend/`.
- The production AS project is named **`F2-PWA-Backend`** (NOT `-Staging`).
  Per `2026-05-02-f2-admin-portal-prod-cutover.md`.

## Steps

### Step 1 — Rebuild dist (~30 sec, idempotent)

```powershell
Set-Location deliverables/F2/PWA/backend
npm run build
```

Output: `dist/Code.gs` (single-file bundle of all `src/*.js`), `dist/appsscript.json`, `dist/Admin.html`. The build is idempotent — re-running on a clean tree produces byte-identical output.

> **Sanity check** the v2.0.1 handlers are in the bundle:
> ```powershell
> Get-Content dist/Code.gs | Select-String -Pattern 'admin_users_change_password|adminUsersChangePassword' | Select-Object -First 3
> ```
> Should return at least 2 hits (the dispatcher entry + the function definition). If 0 hits, the build didn't pick up the v2.0.1 source — investigate `scripts/build.mjs` ordering before continuing.

### Step 2 — Open the PRODUCTION AS project (~1 min)

1. Open `https://script.google.com` while signed in as `aspsi.doh.uhc.survey2.data@gmail.com`.
2. Open the project named **`F2-PWA-Backend`**.
3. **Verify production, not staging:** top-left should say `F2-PWA-Backend` (no `-Staging` suffix). If it says `-Staging`, close it and open the right project. **Pushing to staging here is wrong** — staging is its own project with its own `/exec` URL.

### Step 3 — Paste the new Code.gs (~1 min)

1. In the AS Editor, click `Code.gs` in the left file tree.
2. Select all (`Ctrl+A`) and delete.
3. Open `dist/Code.gs` from this repo locally, copy all, paste into the AS Editor.
4. Click **Save** (floppy icon, or `Ctrl+S`). Wait for "Saved" to appear next to the project name.

> **Don't paste only changed lines** — always replace the whole `Code.gs`. Partial pastes leave stale code in the rest of the file.

### Step 4 — Publish a new VERSION of the EXISTING deployment (~2 min)

You're **not** creating a new deployment — you're publishing a new version of the existing prod Web App so the `/exec` URL stays the same (worker's `APPS_SCRIPT_URL` secret keeps working).

1. Editor → **Deploy** → **Manage deployments**.
2. Find the existing prod Web App in the list (URL ending `/exec`). Click the **pencil icon** to edit it.
3. **Version:** dropdown → **New version**.
4. **Description:** `v2.0.1 admin handlers (#294 / E4-PWA-014) — adds admin_users_change_password, admin_users_bulk_import, etc.`
5. Leave **Execute as** and **Who has access** untouched.
6. Click **Deploy**.
7. Confirmation modal shows the **same `/exec` URL** as before — that's correct (URL is stable across versions). Close the modal.

> **Don't create a new deployment.** A new deployment generates a new `/exec` URL; the worker's `APPS_SCRIPT_URL` secret would still point at the old one and the v2.0.1 handlers would still be unreachable.

## Verification

### A. Quick portal check (~30 sec — preferred)

1. Open `https://f2-pwa.pages.dev/admin/login`.
2. Log in as any admin with `password_must_change=true` (e.g., Shan's account, or seed one if needed).
3. Should redirect to `/admin/me/change-password`.
4. Enter current + new password → click **Update**.
5. **PASS:** redirects to the dashboard; no error banner.
   **FAIL:** banner says `Unknown admin action: admin_users_change_password` — re-check Step 4 (did you click the pencil-edit, or did you accidentally create a new deployment?).

### B. Worker round-trip via curl (alternative)

```sh
# Replace <jwt> with a current admin JWT from a logged-in session.
curl -i -X POST https://f2-pwa-worker.hcw.workers.dev/admin/api/me/change-password \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json" \
  -d '{"current_password":"...","new_password":"..."}'
```

PASS: `200 OK` with a new JWT in the response body. FAIL: `"Unknown admin action"` error envelope.

## Rollback

If something breaks after deploy:

1. Editor → **Deploy** → **Manage deployments** → pencil-edit the prod Web App.
2. **Version:** dropdown → select the **previous version number** (whatever was live before today's push).
3. Click **Deploy**. The same `/exec` URL now serves the prior version.

Low-risk path overall — this push only **adds** new handler entries; existing handlers and data are untouched. No migration, no schema change.

## Sequencing

**Ship this BEFORE Marriz is onboarded** — `marriz_admin` will hit the same
error on first login otherwise (companion note on #294).

## Follow-up (v2.0.2, separate issue)

File: add an `as-deploy.yml` GitHub Actions workflow that runs `npm run build` in `deliverables/F2/PWA/backend/`, then uses **`clasp`** (with a service account or PAT-equivalent stored as a repo secret) to push `dist/Code.gs` to the AS project and publish a new version on every push to `main` touching `deliverables/F2/PWA/backend/src/**`. Closes the deploy-gap class entirely. (Eng-lane; tracks under E4-PWA-014 follow-up.)

> Adopting clasp at that point also lets future runbooks reference `clasp push` / `clasp deploy` legitimately — but it requires a one-time setup pass (clasp install, `.clasp.json` with the production scriptId, service account auth). Not in scope for #294.

## Close-out

After verification passes:
1. Comment the verification result on #294 and close it (e.g., `Closes #294` in a commit message, or close manually with a link to this runbook).
2. Add `status:fixed-pending-verify` → wait for Shan/Marriz first-login confirmation → close.
3. Optional: append a one-liner to `log.md`: `#294 AS redeploy: prod F2-PWA-Backend now carries v2.0.1 admin handlers. Verified via change-password flow.`
