# F2 Aug-17 Cutover Runbook (Task 3.5)

Written 2026-08-19 at Task 3.4 closure. Executes the one ordered move that ruling
R14 deferred from 3.4. Grounded in review-verified facts, not assumptions:

- ⚠ CORRECTED 2026-08-19: **the live backend is f2-api** (Node/MySQL,
  `PWA/server/`, `uhc-hcw.asiansocial.org/api`, live since the 2026-08-05
  Model C migration, commit 43c2c40) — empirically confirmed via
  `/api/health` → `{"service":"f2-api"}`. The Apps Script project
  (`PWA/backend/`, Handlers.js) is a RETIRED kill-switch fallback with zero
  traffic; `apps-script/Spec.gs` is a never-deployed prototype. Neither is
  part of this cutover.
- f2-api performs the same architecture this runbook assumed: no per-item id
  validation (values stored as one values_json blob); the ONLY stale-client
  gate is the whole-submission `spec_version` comparison against
  `min_accepted_spec_version` (`server/src/handlers.ts:89-91`). Until that
  floor is raised, an un-updated client's Apr-20 ids are accepted and
  silently commingled; after it is raised, that client gets `E_SPEC_TOO_OLD`
  and must reload.
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
5. **Raise the floor (same sitting):** ⚠ CORRECTED 2026-08-19 during execution —
   the live backend is **f2-api** (Node/MySQL, `PWA/server/`, serving
   `uhc-hcw.asiansocial.org/api` since the 2026-08-05 Model C migration,
   commit 43c2c40); the Apps Script project is a retired kill-switch fallback
   and receives no traffic. The floor lives in MySQL: `f2_config` table,
   `csweb_f2` DB (row DDL-seeded; `handlers.ts:89-91` reads it and rejects
   lexicographically-older `spec_version` with `E_SPEC_TOO_OLD`). Raise it via
   the box's docker-exec pattern:
   `UPDATE f2_config SET v='2026-08-19-m1' WHERE k IN
   ('min_accepted_spec_version','current_spec_version');`
   (rollback: same statement with the prior value `2026-04-17-m1`). Verify: a
   stale client (or a curl with the old spec_version) now receives
   `E_SPEC_TOO_OLD`; a fresh client submits successfully.
6. **Post-cutover:** refresh `locale-shots/` via the existing shot specs; commit
   (WT) `aug17: F2 v3 spec deployed`; Linear ANA-milestone checklist item for 3.5
   marked done; note the cutover timestamp here.

## Cutover timestamps (2026-08-19)

- **PWA deployed**: `2026-08-19T01:06:34Z` (build-info.json `built_at`, sha
  `9c2cebb2`; `deploy-f2-pwa.ps1 -Force` run by Carl after the sanctioned
  automated path was classifier-denied). Live-verified via `-VerifyOnly`
  (all 7 `$RequiredMarkers` present, incl. the new Section B one) shortly after.
- **Floor raised**: shortly after the runbook correction above (commit
  `ca626df`, `2026-08-19T01:29:08Z`) — Carl ran the `f2_config` UPDATE on the
  box directly. Confirmed by Carl's own `SELECT` output: both
  `min_accepted_spec_version` and `current_spec_version` = `2026-08-19-m1`;
  `kill_switch` untouched (`false`). Dual-version window: ~23 minutes
  (`01:06:34Z` → ~`01:29:08Z`).
- **Stale-reject verify**: done at the unit level, not a live production
  submission (no admin credentials available this session to clean up a
  self-registered test case afterward, and self-register requires a real
  facility — didn't want to write a synthetic row into a real facility's
  data). `server/test/handlers.test.ts` — which imports and exercises the
  exact `handleSubmit`/`getConfig` functions now live in `handlers.ts` —
  passes both `rejects E_SPEC_TOO_OLD below min_accepted_spec_version (lexical
  compare)` and `accepts a fresh submission with srv- id + ISO
  server_timestamp` (16/16 tests green). Combined with Carl's direct DB read
  above, this is the verification basis for Step 5's "same sitting" gate.

## Rollback

- PWA: redeploy the previous build via `deploy-f2-pwa.ps1` from the pre-merge
  main (the script's marker rows guard against a stale-build accidental revert —
  a deliberate rollback must revert the marker row too).
- Backend: lower `min_accepted_spec_version` back to the prior value — same
  `f2_config` UPDATE, prior value `2026-04-17-m1` (NOT a clasp deploy; see the
  CORRECTED note above). Data written during the window keys on `spec_version`
  per row, so post-hoc separation is always possible — nothing is destroyed
  either direction.

## Not in scope

- CSWeb/CSEntry: F2 has no CSPro build; nothing to sync there.
- `apps-script/Spec.gs`: stays a committed reference prototype.
