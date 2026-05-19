# Runbook — E4-PWA-014 / #294: Apps Script Web App redeploy (P0)

**Owner: Carl (requires Google auth for the ASPSI mailbox account — clasp login).**
Claude cannot execute this; the steps below are exact and copy-pasteable.

## Context

R3 P0 #294. The Worker + frontend shipped v2.0.1 on 2026-05-09 (PR #136,
`9bab42b`), but the **Apps Script Web App was last pushed 2026-05-04** —
before PR #134's `adminUsersChangePassword` / bulk-import handlers. So any
admin with `password_must_change=true` (Shan's R2-reset account, and Marriz
once onboarded) hits **"Unknown admin action: admin_users_change_password"**
on first login. The repo source is correct
(`deliverables/F2/PWA/backend/src/AdminDispatch.js:126`,
`AdminUsers.js:271`); only the deployed artifact is stale. Fix = push +
redeploy the AS project. **No code change.**

Root-cause class: CF Pages auto-deploys on merge (`cf-pages-deploy.yml`);
the AS source has **no** equivalent workflow, so "merged → live" does not
hold for backend changes. Permanent fix is the v2.0.2 follow-up below.

## Preconditions

- `clasp` installed (`npm i -g @google/clasp`), logged in as the ASPSI
  mailbox Google account that owns the F2 AS project
  (`clasp login` — opens a browser; **Carl-only**).
- Working dir: `deliverables/F2/PWA/backend/`.
- `.clasp.json` present locally (auth-local, gitignored). If absent, recover
  the **scriptId** from the AS project URL or a prior runbook
  (`docs/superpowers/runbooks/2026-05-02-f2-admin-portal-prod-cutover.md`)
  and recreate it: `{"scriptId":"<id>","rootDir":"src"}`.

## Steps

```sh
cd deliverables/F2/PWA/backend

# 1. Confirm what's about to push (should include AdminUsers.js, AdminDispatch.js)
clasp status

# 2. Push the current repo source to the AS project
clasp push -f

# 3. List existing deployments — note the PRODUCTION deploymentId + version
clasp deployments

# 4. Redeploy the SAME deployment id so the /exec Web App URL is unchanged
#    (Apps Script Web App "freeze-at-deploy": updating the existing
#     deployment keeps the URL stable → NO Worker change needed).
clasp deploy --deploymentId <PROD_DEPLOYMENT_ID> --description "v2.0.1 admin handlers (#294 / E4-PWA-014)"
```

> If — and only if — a **new** deployment is created (new `/exec` URL), the
> Worker's AS base URL secret must be updated and the Worker redeployed:
> `cd ../app && cmd //c "wrangler secret put AS_WEB_APP_URL"` (paste the new
> `/exec` URL), then `wrangler deploy`. Prefer step 4 (same deploymentId) to
> avoid this.

## Verification

```sh
# Worker round-trip — replace <jwt> with a current admin JWT.
curl -i -X POST https://f2-pwa-worker.hcw.workers.dev/admin/api/me/change-password \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json" \
  -d '{"current_password":"...","new_password":"..."}'
# PASS: 200 OK with a new JWT.  FAIL: "Unknown admin action".
```

Then in the Admin Portal: log in with a `password_must_change=true` account
→ complete the forced change-password flow → no error banner.

## Rollback

`clasp deployments` → `clasp deploy --deploymentId <PROD_ID> --versionNumber <prev>`
to pin back to the prior version. (Low risk — this only adds handlers; no
schema/data change.)

## Sequencing

**Ship this BEFORE Marriz is onboarded** — `marriz_admin` will hit the same
error on first login otherwise (companion note on #294).

## Follow-up (v2.0.2, separate issue)

File: add an `as-deploy.yml` GitHub Actions workflow that pushes
`deliverables/F2/PWA/backend/src/*.js` to the AS project and bumps the Web
App deployment on every push to `main` touching that path. Closes the
deploy-gap class entirely. (Eng-lane; tracks under E4-PWA-014 follow-up.)

## Close-out

After verification passes, comment the result on #294 and close it
(`Closes #294` via the close-out, or close manually with a link to this
runbook + the verification output).
