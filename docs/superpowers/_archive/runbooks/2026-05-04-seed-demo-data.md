---
title: Seed staging with realistic demo data for the 2026-05-11 ASPSI demo
date: 2026-05-04
sprint: 004
related:
  - deliverables/F2/PWA/backend/apps-script/SeedDemo.js
  - deliverables/F2/PWA/backend/dist/Code.gs
  - docs/F2-PWA-Demo-Guide-2026-05-11-ASPSI-Internal.md
  - docs/superpowers/runbooks/2026-05-04-fx-006-as-push.md
estimate: ~5 min
---

# Seed staging with realistic demo data for ASPSI demo

> Populates the staging admin portal with **3 facilities + 12 HCWs + 8 self-admin responses + 1 paper-encoded + 2 enrolled-not-yet-submitted + 1 DLQ entry + 2 file uploads + 1 token-reissue audit + 1 failed-login audit** so when ASPSI clicks around the dashboards on Monday, every tab tells a story instead of looking like an empty test scaffold. All rows tagged `DEMO-*` for trivial cleanup.

## Step 1 — Rebuild + push `dist/Code.gs` (~3 min)

Already done if you've shipped the bundle that includes SeedDemo.js. Otherwise:

```powershell
Set-Location deliverables/F2/PWA/backend
npm run build
```

Then paste `dist/Code.gs` into the **`F2-PWA-Backend-Staging`** Apps Script project and Deploy → Manage Deployments → pencil-edit → New version → Deploy. (Same flow as `2026-05-04-fx-006-as-push.md` — see that runbook for the full step-by-step.)

> Sanity check: `Get-Content dist/Code.gs | Select-String -Pattern 'function seedDemoData'` should show the function.

## Step 2 — One-time: confirm staging environment marker (~30 sec)

The seed has a guard rail that refuses to run on production. It looks for either `PROP_ENV=staging` in Script Properties OR a sheet name containing "Staging".

In the staging AS Editor:

1. Project Settings (left sidebar gear icon).
2. Script properties → if `PROP_ENV` is not already `staging`, click **Add script property**, set **Property** = `PROP_ENV`, **Value** = `staging`. Save.

If the sheet name is "F2 PWA Backend — Staging" you can skip this — the fallback name-check covers it. Setting `PROP_ENV` is just belt-and-suspenders.

## Step 3 — Run `seedDemoData()` (~30 sec)

In the AS Editor:

1. From the function dropdown (top toolbar, between the Run/Debug buttons), select **`seedDemoData`**.
2. Click **Run**.
3. First run: AS will prompt for permissions to access your spreadsheet — accept (it's the same permission scope already granted for the rest of the backend).
4. Watch the Execution log (Cmd+Enter / View → Logs). You should see:
   ```
   seedDemoData complete: {"facilities":{"added":3,"skipped":0},"hcws":{"added":12,"skipped":0},"responses":{"added":9,"skipped":0},"dlq":{"added":1,"skipped":0},"files":{"added":2,"skipped":0},"audit":{"added":2,"skipped":0}}
   ```
5. If you see `Refusing to seed demo data: this does not look like a staging sheet` — you're in production, abort. Set `PROP_ENV=staging` on the staging project (not production) and try again.

## Step 4 — Verify in the admin portal (~2 min)

1. Open `https://staging.f2-pwa.pages.dev/admin/login`. Login as `carl_admin` / `100%SetupMe!`.
2. **Data → Responses** → expand the date filter to start from 2026-05-01 → table now shows ~9 submissions across the 3 facilities. Click into one (e.g., Dr. Liza Mendoza) → ResponseDetail shows the answer values.
3. **Data → Audit** → table shows ~70 events; the new `admin_hcws_reissue_token` for `DEMO-HCW-006` and the `admin_login_failed` from `unknown_user` should appear in the most-recent rows.
4. **Data → DLQ** → 1 entry: `DEMO-SUB-012` failed with `E_SPEC_DRIFT`.
5. **Data → HCWs** → 12 HCWs across 3 facilities. `DEMO-HCW-004` and `DEMO-HCW-009` show as `enrolled` (no response yet); the rest show `enrolled` but with response rows (Responses tab).
6. **Configuration → Apps & Settings → Files** → 3 files now (the original test screenshot + 2 demo uploads).
7. **Reports → Map** → markers appear at Quezon City, Infanta, and Balanga (real PSGC-coded coordinates with small jitter so multiple HCWs at one facility don't stack).

## Step 5 — Demo prep / pre-tour

Run the demo guide path from `docs/F2-PWA-Demo-Guide-2026-05-11-ASPSI-Internal.md` end-to-end on the actual presenting machine. Pay attention to:

- **Persona switch** — login as `data_reader_test` after seeing carl_admin's view; the RBAC differences are easier to demo with real-looking data than with empty tables.
- **Reissue token flow** — pick `DEMO-HCW-006` (Dr. Liza Mendoza, Infanta) since the demo data already has a reissue audit event for her, so the audit log "tells the story" alongside.
- **Encode flow** — `DEMO-HCW-008` (Cristina del Rosario, Lab tech) is paper-encoded; navigate to `/admin/encode/DEMO-HCW-008` to demo the paper-encoder workflow.
- **Map clustering** — the 3 facilities are far enough apart that markers don't overlap; close enough zoom shows them as separate pins.

## Step 6 — Cleanup after the demo

When you want staging back to its pre-demo state:

1. AS Editor → function dropdown → `purgeDemoData` → Run.
2. Log shows `purgeDemoData complete: {...counts...}`.
3. Removes every row tagged `DEMO-*` across FacilityMasterList / F2_HCWs / F2_Responses / F2_DLQ / F2_FileMeta / F2_Audit. Existing real data is untouched.

> Cleanup is safe to run anytime, including before re-seeding (the seed is idempotent on its own — re-running just skips existing rows — but if you've manually edited demo rows on the sheet and want to re-seed clean, purge → seed gives you the canonical state.)

## What NOT to do

- **Don't run `seedDemoData()` on production AS.** The guard rail will refuse, but if `SEED_DEMO_ALLOW_PROD=1` was set on prod (don't), the seed would pollute live submissions. Production has its own real ASPSI data once enumerator onboarding starts.
- **Don't paste demo HCW IDs into the production PWA.** They only resolve against staging.
- **Don't promise the demo facilities are real.** They're plausibly named but fictional. If ASPSI asks "is Quezon City Health Center 1 part of our sample?", the answer is "no, this is demo data — your actual sample list lands in `FacilityMasterList` once Juvy provisions it."

## Demo data layout reference

| | What | Count |
|---|---|---|
| Facilities | NCR/QC RHU + IV-A/Infanta DH + III/Bataan Lying-In | 3 |
| HCWs | Mix of physicians/nurses/midwives/pharmacist/lab/dentist/etc | 12 |
| Submitted (self-admin) | Section A complete + sample of B | 8 |
| Paper-encoded | Lab tech, encoded by carl_admin | 1 |
| Enrolled, no submission | Pharmacist + Nursing assistant | 2 |
| DLQ | Health-promotion officer, schema_version drift | 1 |
| Files | Field plan PDF + Facility roster CSV | 2 |
| Audit (demo additions) | Token reissue + failed login | 2 |
| Audit (existing) | Real `admin_login` traffic from carl_admin sessions | ~70 |
