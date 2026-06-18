# F2 PWA — Remaining Work Backlog (Survey + Admin Portal)

> **Living checklist of everything left to do on the F2 Healthcare Worker Survey PWA
> and its Admin Portal.** Work these against the **staging** environment, then promote to
> prod. Supersedes the old `NEXT.md` (which was frozen at the April UAT R1/R2 era,
> pre-v2.0.0, pre-Admin-Portal).
>
> **Last reconciled:** 2026-06-16 — **against the actual codebase** (18-item audit across
> `app/src`, `worker/src`, `backend/`), the scrum epics, GitHub issues, and CHANGELOG. The
> prior version of this file was stale: **10 items it listed as TODO were already shipped**
> (v2.0.1/v2.0.2). Statuses below now carry file:line / PR evidence.

## Status snapshot

| Thing | State |
|---|---|
| **Prod** | `v2.1.0` live at https://f2-pwa.pages.dev (HCW Survey + Admin Portal, all 7 PH languages) |
| **Staging** | https://f2-pwa-staging.pages.dev (project `f2-pwa-staging`, branch `staging`) |
| **Admin Portal** | v2.0+ live; Users dashboard, RBAC + persona switching, JWT/`password_must_change`, `last_login_at`, kill-switch, DLQ requeue, bulk-import, files+folders+rename all shipped. |
| **⚠️ Worker deploy gap** | **CI's version-stamped Worker deploy is failing** — `CLOUDFLARE_API_TOKEN` lacks `Workers Scripts: Edit` (error 10000). Pages (frontend) deploys fine; **any new/changed Worker route will NOT reach staging until the token is fixed or the Worker is deployed manually (`wrangler deploy`).** Blocks the broadcast-editor + all backend features. *(Carl's fix.)* |
| **⚠️ English-only mode** | **Temporarily ON** in both prod + staging (`VITE_ENGLISH_ONLY` in `.env.production`, 2026-06-16, Shan screenshot request). The language switcher is hidden until this is reverted. |
| **Open F2 GitHub issues** | 5 Survey bugs (`epic:f2-pwa`) — Section A. 3 of them now fix-on-staging (this session). |

## What's actually actionable (post-audit)

- **Buildable now, frontend/CI-only (fully shippable via Pages):** _none open_ — E6-PWA-009 (a11y: axe + contrast + Lighthouse gates) and E6-PWA-010 (perf: bundle-size + Lighthouse gates) both shipped 2026-06-17.
- **Code-complete, Worker-deploy-gated to go live** (last M12d piece): **broadcast_message admin editor** — built + wired + tested across all layers (2026-06-17); the new Worker route only answers once the Worker redeploys (CF token fix), so the editor self-hides on staging until then.
- **Blocked on Carl/ASPSI inputs:** #543 + #528 (a staging token) · DESIGN-005 (DOH brand-book PDF) · FacilityMasterList real rows + M8/M9 facility flags (real facility data incl. BUCAS/GAMOT) · E4-INT-003 (ASPSI sign-offs).
- **Not started:** E4-INT-002 Looker dashboard.

## How to work + ship on staging

The deploy is **push-triggered + CI-gated** (not manual wrangler anymore):

1. Branch off `staging` (or work on it directly for this push-to-deploy flow).
2. Edit + `npm run test` + `npx tsc -b --force` locally (CI runs typecheck + lint + vitest).
3. **Survey content/skip/validation changes go in `spec/F2-Spec.md` (+ the F2-Skip-Logic/
   Validation/Cross-Field docs), then `npm run generate`.** Never hand-edit `src/generated/*`.
   Admin-portal changes are plain React in `src/admin/**` (no generator).
4. Push to `staging` → **CI — F2 PWA** runs → on green, **CF Pages deploy** auto-ships the
   frontend to `f2-pwa-staging`. **Worker changes need the deploy-gap fix above.**
5. Forward-only sign-off: fold every behavioral fix back into the owning F2 spec doc.

---

## A. Survey — Active bugs (UAT, `epic:f2-pwa`) — DO FIRST

Ordered by severity / blocking impact.

- [ ] **#543 — Cold Enrollment** · `Critical (cannot proceed)` · Enrollment · **BLOCKED — needs a staging enrollment URL + a current valid test token (and ideally a revoked one)**
  Pre-filled token rejected as **"Token malformed. Contact ASPSI ops."** — user cannot
  enroll at all. Likely token format/validation or the enrollment-URL token param. Pairs
  with #528. Can't be safely guess-fixed without a reproducible token. *(Windows Chrome.)*
- [ ] **#539 — Role-Select (section role-gating)** · `High` · routing · **FIX ON STAGING (`45144cf`) — pending tester UAT**
  Section visibility per persona didn't match the spec'd routing. Required behavior:
  **C/D/E1** = Admin, Physician/Doctor, Nurse, Midwife, Dentist only (note: there is **no**
  "Nutritionist-Dietician" Q5 choice — the spec's summary word maps to no real role, and the
  detailed/exclude lists put *Nutrition action officer/coordinator* in the **excluded** set);
  **Pharmacist/Dispenser** → skip to **E2**; **Physician Assistant, Nursing/Lab/Med-tech,
  Health Promo, Nutrition officer, PT, Dentist aide, BHW, Other** → no C–E1, go to E2;
  **Section G** = Physicians + Dentists only.
  Root cause: `SECTION_CDE_ROLES`/`SECTION_G_ROLES` in `skip-logic.ts` still held the stale
  R2-#114 list (Physician assistant + Nutrition officer leaked C/D/E; PA also leaked G).
  Fix removed all three + collapsed `cross-field.ts`'s duplicate `BUCKET_CD` into the exported
  `SECTION_CDE_ROLES` (single source of truth). All 16 roles traced vs spec; 214 lib tests +
  #539 persona regressions green. *(Aidan re-test 2026-06-16: only PA + Nutrition officer
  remained.)*
- [ ] **#524 — Skip Logic (premature auto-advance)** · `High` · navigation · **FIX ON STAGING (`da7bfb7`) — pending tester UAT**
  Answering a question auto-skipped to the next section while required-but-initially-hidden
  questions remained (observed **Q23, Q44, Q54, Q123**; worse toward section end). Same class
  as the historical #10 auto-advance bug. Fix: `Section.tsx` fires an un-debounced `onInteract`
  on every field change; `MultiSectionForm.tsx` holds the 400ms advance timer in a ref and
  cancels it on any interaction, so a section only advances after the respondent goes idle.
  Regression test added. *(Windows Chrome.)*
- [ ] **#528 — Token Auto-prefilled** · `Medium-High` · Enrollment · **BLOCKED — same token need as #543**
  Token is **not** auto-prefilled when the enrollment URL is opened fresh/incognito (5A.1);
  Verify should be one-tap. Related to #543 (token handling). *(Android tablet Chrome.)*
- [ ] **#587 — Q9 vs Q4 inline validation timing (Section A)** · `Medium` · validation UX · **FIX ON STAGING (`0ef91d2`) — pending tester UAT**
  The tenure-vs-age cross-field check (`PROF-01`: years of service < age − 20) only fired at
  the **review** stage, not before section navigation. Fix: new pure `sectionBlockingErrors()`
  in `cross-field.ts` returns error-severity findings whose fields belong to the section being
  left; `MultiSectionForm.handleSectionValid` fires it inline at section exit (covers manual
  Next *and* #524 auto-advance), blocks the advance, and shows the message in a destructive
  strip that clears on edit/nav. Also catches `PROF-05` (zero tenure). Unit + integration
  tests added. The rule itself was unchanged — a *when-it-fires* fix. *(iPad Safari, v2.1.0.)*

## B. Survey — Features / polish

- [x] **E3-F2-PWA-DESIGN-004 — Self-host fonts** — ✅ **DONE (v2.0.2, PR #274 / #162).** 22 subsetted
  woff2 (latin + latin-ext) under `public/fonts/`, `fonts.css` linked in `index.html`,
  regenerable via `scripts/self_host_fonts.py`, Tailwind mapped, SW-precached. No CDN refs.
- [ ] **E3-F2-PWA-DESIGN-005 — Verde Manual hex refinement** · **BLOCKED — no DOH brand-book PDF**
  (Dept Order 2020-0011, Verde Vision 2023+) in the vault. Current values are best-fit
  approximations. Won't refine without the source — refusing to invent hex values.
- [ ] **M8/M9 tech debt — facility flags + `response_source`** · **DEFERRED (needs real facility data)**
  E1/E2 gating is currently **role-only** (`SECTION_CDE_ROLES`/`SECTION_E_ROLES`; this is what
  #539 fixed). The spec (`F2-Spec.md:189,203`) also gates E1 on `facility_has_bucas` and E2 on
  `facility_has_gamot`, plus per-respondent `response_source` (`F2-Spec.md:67`). Neither flag is
  in the schema (`db.ts:35`, AS `FACILITY_MASTER_LIST_COLUMNS`) nor the sync payload — explicitly
  deferred since M4/M8. Implementing it needs the facility data to carry BUCAS/GAMOT flags.
- [ ] **FacilityMasterList — real rows** · **BLOCKED — only 3 `DEMO-` rows exist**
  Infra is complete + tested (backend handler, `facilities-client.ts`, IndexedDB cache,
  enrollment UI). Real facility data (`facility_id, name, type, region, province, city_mun,
  barangay` — + ideally BUCAS/GAMOT flags for M8/M9) has never been loaded into the staging/prod
  sheet. Backend serves real rows the moment they're added.

## C. Admin Portal

- [x] **E4-APRT-046 — Files: Create Folder** — ✅ **DONE end-to-end** (`Files.tsx` + worker `apps.ts`/`routes.ts` + AS `AdminFiles.js` + tests).
- [x] **E4-APRT-047 — Files: Rename** — ✅ **DONE end-to-end** (inline rename + worker PATCH + AS RPC + tests).
- [x] **Admin mutations (was M12d)** — ✅ **all code shipped;** the broadcast editor only awaits the Worker deploy to go live:
  - [x] **Kill-switch toggle** — ✅ DONE (`DataSettings.tsx` + worker `/kill-switch` + AS + a11y/E2E/backend tests).
  - [x] **Requeue-from-DLQ** — ✅ DONE (`DLQTab.tsx` Replay/Delete + worker + AS + a11y test).
  - [x] **`admin_users_change_password` + bulk-import** — ✅ DONE (`ChangePasswordPage` + `BulkImportModal` + worker handlers + 8-case test suite).
  - [x] **`broadcast_message` editor** — ✅ **CODE-COMPLETE across all layers + tests; goes live on the
    Worker deploy.** Admin UI (`BroadcastSection` in `DataSettings.tsx` — self-hides on a 404 until the
    route deploys, surfaces other load errors instead of vanishing; 2026-06-17), worker route + handler
    (`BROADCAST_RE` + `handleBroadcastGet/Set` in `routes.ts`/`handlers/data.ts` — dash_apps-gated, audited
    `admin_broadcast_set`, 280-char cap, empty clears), and AS dispatch (`admin_config_get/set` →
    `adminConfigGet/Set`, `broadcast_message` seeded in `Schema.js` `F2_CONFIG_DEFAULTS`) all in place and
    tested (FE 4 + worker 23 + backend 22 green). **Still Worker-deploy-gated:** the new route only answers
    once the Worker redeploys (CF token fix) — until then the editor self-hides. Removes the "ops edits the
    Config sheet directly" workaround.
- [x] **Admin Portal design-review MINORs** — ✅ **DONE.** All 15 MINOR-tier findings shipped in the
  v2.0.1 patch bundle (E4-APRT-049a..e), verified in UAT R3.

## D. Backend / Worker / Ops

- [x] **E4-PWA-015 — Worker PBKDF2 at 100k** — ✅ **DONE** (`worker/src/admin/auth.ts:18,65,109` — floor 10k / ceil 100k, tested).
- [x] **E4-PWA-010 — Secrets rotation policy doc** — ✅ **DONE** (`docs/superpowers/runbooks/2026-05-12-f2-secrets-rotation.md`, v2.0.2 / PR #276 / #172 — JWT, HMAC, AS deploy ID).
- [x] **E4-PWA-011 — Backup + restore runbook** — ✅ **DONE** (`docs/superpowers/runbooks/2026-05-12-f2-pwa-backup-restore.md`, v2.0.2 / PR #276 — Sheet + R2 + KV).
- [ ] **⚠️ Worker CI deploy token** — fix `CLOUDFLARE_API_TOKEN` to include `Workers Scripts: Edit`
  (error 10000) so the version-stamped Worker deploy stops failing. **Unblocks the broadcast
  editor + every future backend route.** *(Carl — Cloudflare dashboard.)*
- [ ] **Admin password rotation (prod side)** — `worker/scripts/hash-admin-password.mjs` →
  `wrangler secret put ADMIN_PASSWORD_HASH` (staging done; prod pending).

## E. Integration / ETL

- [ ] **E4-INT-002 — Looker Studio (or equivalent) dashboard** over the unified store · `est 1d` · **TODO (not started).** Internal admin dashboards exist but not the external unified-store viz.
- [ ] **E4-INT-003 — Codebook-driven harmonization** wired into ETL · **PARTIAL — blocked on ASPSI sign-offs.**
  Skeleton + QA gates + 7 of ~17 dimensions transformed (`deliverables/data-harmonization/etl/`); dry-run passed.
  Missing: 10 dimensions, F2 extraction path, codebook §15 open items (facility master list, QUESTIONNAIRE_NO map, sex-Other, PSGC vintage).

## F. Testing / Pilot / Quality

- [ ] **E6-PWA-008 — F2 production pilot batch** — small facility cohort, success criteria, go/no-go · `est 1d` · *(needs real facilities — see Section B.)*
- [x] **E6-PWA-009 — a11y audit** — ✅ **DONE.** Three CI gates now cover a11y: the 37 axe-core
  component tests, the **contrast gate** (`scripts/check-contrast.mjs` in `npm run build` — parses
  `index.css`, fails on a WCAG-AA regression), and the **full-page Lighthouse a11y-score gate**
  (`@lhci/cli`, `lighthouse` job in `ci.yml` — fails if `/` or `/admin/login` drops below 100/100,
  audited in headless Chrome ×3). The sub-AA Verde Manual findings the contrast gate first surfaced
  (light ochre 2.70:1, dark primary 2.99:1, dark destructive 3.13:1) were **fixed 2026-06-17** (`343b1a0`,
  DESIGN.md Decisions Log) — all 20 pairs now ≥ AA, **zero exceptions**. **Deferred:** deep authed
  surfaces (Lighthouse needs a session token, blocked #543/#528) — public entry points gated today.
- [x] **E6-PWA-010 — Performance baseline** — ✅ **DONE.** Two CI gates: the **bundle-size budget**
  (`scripts/check-bundle-budget.mjs` in `npm run build` — gzip floors: eager first-paint ≤ 250 KB,
  admin ≤ 150 KB, any chunk ≤ 350 KB) and the **Lighthouse-score gate** (`@lhci/cli`, `lighthouse`
  job in `ci.yml`) asserting perf/LCP/CLS/TBT against a served build on every push/PR
  (`PERFORMANCE.md` → "Lighthouse-score gate"). CLS is a hard `error`; perf/LCP/TBT are `warn` pending
  a few green CI runs to establish the runner baseline, then promoted to `error`.

## G. Deferred / not committed (slot in only if pilot demands)

- [x] **E3-F2-PWA-M12a — Per-HCW enrollment tokens** — ✅ effectively DONE (device_token enrollment + reissue handlers + tests).
- [ ] **E3-F2-PWA-M12b — Draft auto-migration across spec versions** · **PARTIAL** — drift detection + reload modal exist (`SpecDriftOverlay.tsx`); no auto-migration logic.
- [ ] **E3-F2-PWA-M12c — iOS push notifications** · **TODO (zero implementation).**

## ✅ Done / superseded (kept for traceability — do NOT re-do)

- **Survey bugs shipped this session (staging, pending UAT):** #524, #539, #587.
- **a11y + perf CI gates (2026-06-17, staging):** WCAG-AA contrast fix (`343b1a0` — all 20 token
  pairs ≥ AA, gate exceptions removed) + full-page **Lighthouse-score gate** (`@lhci/cli`, `lighthouse`
  job in `ci.yml`; a11y + CLS hard-gated, perf/LCP/TBT warn). Closes **E6-PWA-009 + E6-PWA-010**.
- **Already shipped but were stale-listed as TODO (v2.0.1/v2.0.2):** DESIGN-004 fonts,
  E4-APRT-046 Create Folder, E4-APRT-047 Rename, kill-switch, DLQ requeue, change-password,
  bulk-import, admin design MINORs, E4-PWA-015 PBKDF2, E4-PWA-010 secrets runbook,
  E4-PWA-011 backup runbook, M12a per-HCW tokens.
- **R3 UX features** — exclusive "I don't know" (#16), "All of the above" auto-select (#17),
  scale-style matrix (#18): **all CLOSED/shipped.**
- **E4-PWA-014 — CF Pages auto-deploy (#34):** `cf-pages-deploy.yml` deploys on push to
  staging/main; #294 (AS deploy gap) closed.
- **Admin Portal v2.0.1 hotfix queue:** #294 / #317 / #319 / #325 / #326 / #330 — all CLOSED.
- **Multi-language:** all 7 PH languages wired + live (currently masked by the temporary
  English-only flag — see snapshot above).

---

### Revert the temporary English-only mode (when screenshots are done)

Set `VITE_ENGLISH_ONLY=false` (or remove it) in `.env.production`, rebuild, redeploy to both
prod + staging. The language switcher + all 7 locales return immediately (they're still wired).
