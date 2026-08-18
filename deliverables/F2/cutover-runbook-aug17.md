# F2 Aug-17 Cutover Runbook (Task 3.5)

Written 2026-08-19 at Task 3.4 closure. Executes the one ordered move that ruling
R14 deferred from 3.4. Grounded in review-verified facts, not assumptions:

- **The live backend is the Apps Script project at `PWA/backend/src/Handlers.js`**
  (clasp-managed). `apps-script/Spec.gs` is a never-deployed prototype (no
  doPost/doGet) — its re-key was prepared+committed for reference only; deploying
  it is NOT part of this cutover.
- Handlers.js performs **no per-item id validation**: values land verbatim as one
  `values_json` blob (Handlers.js:29). The ONLY stale-client gate is the
  whole-submission `spec_version` comparison against `min_accepted_spec_version`
  (Handlers.js:61-64). Until that floor is raised, an un-updated client's Apr-20
  ids are accepted and silently commingled; after it is raised, that client gets
  `E_SPEC_TOO_OLD` and must reload.
- PWA client stamps `LOCAL_SPEC_VERSION = '2026-08-19-m1'` (`src/lib/draft.ts`),
  with the RENAMED_VALUES draft-migration table carrying in-flight drafts across
  the re-key.

## Ordering rationale (R14)

Raise the backend floor **immediately after** the new PWA is live — never before
(active interviews on the current build would be rejected mid-shift), and not
"later" (every hour in between is a dual-version window in which stale cached
clients write Apr-20 ids into the same table). The spec-version gate is the only
protection; the window should be minutes, not hours.

## Steps

1. **Pre-flight (WT, no deploy):**
   - `npx vitest run` green; `npx tsc -b --force` clean (standing rule before any push).
   - `npm run e2e` green after the Step-1 persona/id refresh (plan Task 3.5 Step 1).
   - Spec mirrors md5-identical: `spec/F2-Spec.md` == `deliverables/F2/F2-Spec.md`.
   - Version stamp: `package.json` → 3.0.0; confirm `LOCAL_SPEC_VERSION = '2026-08-19-m1'`.
   - Add the new `$RequiredMarkers` row to `deploy-f2-pwa.ps1` probing the Section-B
     battery RENDER path (keep all existing rows).
2. **DECISION POINT (Carl):** `deploy-f2-pwa.ps1` gates on `HEAD == origin/main`.
   Either merge branch `worktree-f2-productivity-panel` to main first (preferred:
   the deployed build is then reproducible from main), or authorize `-Force`.
3. **Deploy the PWA:** `npm run build`, then
   `powershell -File deliverables\F2\PWA\deploy-f2-pwa.ps1 -DryRun` → real run →
   post-deploy `-VerifyOnly`. (Prod = nginx `/opt/app/f2-www`; NEVER any other path.)
4. **Verify live:** load the prod URL fresh (bypass SW cache), confirm the header
   build stamp/generation marker and one Section-B battery item render; submit a
   smoke response and confirm it lands with `spec_version = 2026-08-19-m1`.
5. **Raise the floor (same sitting):** set `min_accepted_spec_version =
   '2026-08-19-m1'` in the backend config and `clasp push` + deploy the Apps
   Script project (established clasp lane). Verify: a stale client (or a curl
   with the old spec_version) now receives `E_SPEC_TOO_OLD`; a fresh client
   submits successfully.
6. **Post-cutover:** refresh `locale-shots/` via the existing shot specs; commit
   (WT) `aug17: F2 v3 spec deployed`; Linear ANA-milestone checklist item for 3.5
   marked done; note the cutover timestamp here.

## Rollback

- PWA: redeploy the previous build via `deploy-f2-pwa.ps1` from the pre-merge
  main (the script's marker rows guard against a stale-build accidental revert —
  a deliberate rollback must revert the marker row too).
- Backend: lower `min_accepted_spec_version` back to the prior value (one-line
  config + clasp deploy). Data written during the window keys on `spec_version`
  per row, so post-hoc separation is always possible — nothing is destroyed
  either direction.

## Not in scope

- CSWeb/CSEntry: F2 has no CSPro build; nothing to sync there.
- `apps-script/Spec.gs`: stays a committed reference prototype.
