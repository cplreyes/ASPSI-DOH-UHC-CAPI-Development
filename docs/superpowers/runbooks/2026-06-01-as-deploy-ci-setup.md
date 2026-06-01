# Runbook — AS auto-deploy CI setup (one-time)

**Owner: Carl. ~15 min, once. Closes the deploy-gap class behind #294 / E4-PWA-014.**

The `.github/workflows/as-deploy.yml` workflow auto-deploys the F2 PWA Apps
Script backend on every push to `main` that touches
`deliverables/F2/PWA/backend/{src,apps-script}/**`. Until the three secrets
below are set, the workflow **skips cleanly** (a yellow `::warning`, never a red
❌) and the manual paste-into-AS-editor runbook
(`2026-05-19-e4-pwa-014-as-redeploy.md`) stays the deploy mechanism. The moment
all three secrets exist, auto-deploy turns on — no workflow edit needed.

> **Why clasp now?** The 2026-05-19 runbook noted the backend deploys by manual
> paste because there was no clasp setup. This runbook *is* that one-time clasp
> setup. After it, `clasp push` / `clasp deploy` are legitimate here.

## What the workflow does each run

1. `npm run build` → regenerate `dist/Code.gs` (gitignored; never trust a stale checkout).
2. `npm test` → backend vitest gate.
3. Verify the v2.0.1 admin handlers are in the bundle (refuses to ship a build that silently dropped them — the #294 failure mode).
4. `clasp push --force` the `dist/` bundle to the prod script.
5. `clasp deploy --deploymentId <AS_DEPLOYMENT_ID>` → publish a **new version of the existing deployment**, so the `/exec` URL (the Worker's `APPS_SCRIPT_URL`) never changes.

## Step 1 — Generate clasp auth (`CLASPRC_JSON`)

On your machine, signed out of other Google accounts (or use a clean browser
profile), authenticate clasp **as the AS project owner**:

```powershell
npm install -g @google/clasp@2.4.2
clasp login    # browser opens → sign in as aspsi.doh.uhc.survey2.data@gmail.com
```

This writes `~/.clasprc.json` (a refresh token). Print it:

```powershell
Get-Content "$env:USERPROFILE\.clasprc.json"
```

Copy the **entire** JSON blob. That is the value for the `CLASPRC_JSON` secret.

> The refresh token is long-lived but not eternal. If auto-deploy starts
> failing auth months from now, re-run `clasp login` and update the secret.

## Step 2 — Get the script ID (`AS_SCRIPT_ID`)

1. Open `https://script.google.com` as the ASPSI mailbox → open **`F2-PWA-Backend`** (prod, NOT `-Staging`).
2. **Project Settings** (gear) → copy the **Script ID**.

## Step 3 — Get the existing deployment ID (`AS_DEPLOYMENT_ID`)

The existing prod Web App deployment — the one whose `/exec` URL is in the
Worker's `APPS_SCRIPT_URL` secret. Keeping this stable is the whole point.

- In the AS editor: **Deploy → Manage deployments** → the active Web App entry → the **Deployment ID** is shown there.
- Or via clasp (after Step 1): `cd deliverables/F2/PWA/backend && printf '{"scriptId":"<id>","rootDir":"dist"}' > .clasp.json && clasp deployments` → copy the `- AKfyc...` ID for the Web App (NOT the `@HEAD` one).

> **Sanity:** the deployment's `/exec` URL must match the Worker's
> `APPS_SCRIPT_URL`. If you pick the wrong deployment ID, the workflow will
> happily redeploy a deployment nobody reads. Confirm the URLs match.

## Step 4 — Set the three repo secrets

Repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Name | Value |
|------|-------|
| `CLASPRC_JSON` | the full `~/.clasprc.json` blob from Step 1 |
| `AS_SCRIPT_ID` | Script ID from Step 2 |
| `AS_DEPLOYMENT_ID` | Deployment ID from Step 3 |

## Step 5 — First run (also deploys the pending #294 backend)

Because the workflow has `workflow_dispatch`, you can deploy the
already-merged-but-never-pushed v2.0.1 handlers immediately — no dummy commit:

1. Repo → **Actions** → **AS deploy — F2 PWA backend** → **Run workflow** → branch `main` → Run.
2. Watch it: build → test → handler-check → push → deploy.
3. **Verify** (per the 2026-05-19 runbook §Verification A): log in at
   `https://f2-pwa.pages.dev/admin/login` as a `password_must_change` admin →
   change password → no "Unknown admin action" banner.

If that passes, #294 (and its downstream #317 / #319 / #325 / #326 / #330) are
fixed — close them with a link to the Actions run.

## Rollback

If a deploy breaks prod: AS editor → **Deploy → Manage deployments** →
pencil-edit the Web App → **Version** dropdown → select the previous version →
Deploy. Same `/exec` URL now serves the prior version. Then revert the offending
commit on `main` so the next auto-deploy doesn't re-ship it.

## Notes / limits

- **Path-filtered** to backend source — unrelated main pushes don't burn an AS version or clasp quota.
- **Concurrency-guarded** (`group: as-deploy-prod`, no cancel) — two deploys never race; a half-pushed `Code.gs` is worse than a queued one.
- **Staging not covered** — this targets prod only. If a staging auto-deploy is wanted later, add a second deployment ID secret + a `staging` branch trigger.
- clasp is installed globally in CI only; it is **not** added to `package.json` (keeps the local build dependency-free, matching the existing setup).
