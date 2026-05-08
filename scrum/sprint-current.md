---
sprint: 005
start: 2026-05-11
end: 2026-05-15
status: planning
sprint_length: 1 week (5 working days)
deliverable_anchor: Goal A — E3-F1-088 (Phase 1 sync mechanic resolution) + Phase 2 kickoff · Goal B — F2 v2.0.1 hotfix release (Tier 1 lockout/audit-completeness + Tier 2 visible-UX-gap) + UAT R3 against staging
---

# Sprint 005 — Phase 1 sync close + F2 v2.0.1 hotfix release + UAT Round 3

## Sprint Goal

> **Goal A — UHC Survey System CSPro track:** Close **E3-F1-088** (Phase 1 sync mechanic resolution) — pick Path A (separate "send" app w/ external dict + CSDB binding via `dataFile` property in `.ent` or `setfile()` in code, ~2h) or Path B (accept Phase 1 sync gap, ship Plan 1 substantially proven, revisit sync architecture in Phase 2). On Goal A close: merge worktree `feature/uhc-survey-system-build` to `main`; begin Phase 2 (PLF / F3 / F4_listing / F4 / supervisor menu / EA fence / daily audit Slack) per the build plan.
> **Goal B — F2 PWA + Admin Portal v2.0.1:** Ship Tier 1 hotfixes (lockout-prevention + audit-completeness — E4-APRT-050 / 051 / 045 / 044 / 043) Mon, Tier 2 visible-UX-gap features (E4-APRT-048 / 041 / 042) Wed-Thu, cutover staging→main Fri tagged `v2.0.1`. Run **UAT Round 3 against staging** in parallel with R2 wind-down on prod, both rounds finish clean by Fri 2026-05-15.

## Committed Items

### Goal A — Phase 1 sync resolution + Phase 2 kickoff

- [ ] **E3-F1-088** Phase 1 sync mechanic resolution — `syncdata(PUT, FACILITYHEADSURVEY_DICT)` requires external-dict reference + CSDB binding. **Path A** (~2h): build supervisor "send" app with F1 dict as external + explicit CSDB binding via `dataFile` property in `.ent` dictionaries entry (or `setfile()` in code before sync). **Path B**: accept Phase 1 sync gap, file Phase 2 sync architecture revisit task, mark Plan 1 substantially proven. Disposition decided Day 1. `status::todo` `priority::high` `estimate::2h`
- [ ] **E3-F1-PHASE2-PLAN** Phase 2 plan + scope confirmation — once Phase 1 closes, draft Phase 2 plan covering PLF + F3 + F4_listing + F4 + supervisor menu + EA fence + daily audit Slack (per `project_uhc_build_session_handoff_2026_05_08.md`). Save under `docs/superpowers/plans/`. `status::todo` `priority::high` `estimate::2h`

### Goal B — F2 v2.0.1 release (Tier 1 — lockout-prevention + audit-completeness)

- [ ] **E4-APRT-050** Orphan-admin guard + self-delete guard on `adminUsersDelete` — AS rejects last-Administrator delete (`_countAdmins() ≤ 1`) + self-delete (`username == actor.username`) with `E_CONFLICT`; Worker passes `actor.username` through; integration tests both rejection paths; staging green. `status::todo` `priority::high` `estimate::1.5h` `scrum::sprint-005`
- [ ] **E4-APRT-051** Change-password UI replacing `/admin/me/change-password` placeholder — new `PATCH /admin/api/me/password` Worker route + AS RPC + Verde-Manual-styled form; user-driven pw rotation works without curl. Pairs with **E4-APRT-045**. `status::todo` `priority::high` `estimate::2h` `scrum::sprint-005`
- [ ] **E4-APRT-045** JWT `password_must_change` server-side enforcement — `requirePerm` rejects with `E_PASSWORD_CHANGE_REQUIRED` when claim true and path != change-password; mints fresh JWT after change. `status::todo` `priority::high` `estimate::1.5h` `scrum::sprint-005`
- [ ] **E4-APRT-044** RBAC role-version cache stale-entry fix — cache key on `name` only; mismatch → `E_AUTH_EXPIRED`; refresh on AS round-trip. `status::todo` `priority::high` `estimate::1h` `scrum::sprint-005`
- [ ] **E4-APRT-043** Production `ADMIN_PASSWORD_HASH` deletion (M10 sunset, prod side) — `wrangler secret delete ADMIN_PASSWORD_HASH --env production`; legacy `/admin/login` 500-verify; dead `src/admin.ts` route removed. `status::todo` `priority::high` `estimate::30m` `scrum::sprint-005`

### Goal B — F2 v2.0.1 release (Tier 2 — visible UX gaps)

- [ ] **E4-APRT-048** `last_login_at` write path on successful login — AS RPC writes column + appends F2_Audit row; async (non-blocking on login response). `status::todo` `priority::high` `estimate::30m` `scrum::sprint-005`
- [ ] **E4-APRT-041** Create-HCW UI in Admin Portal — Data dashboard → HCWs → "+ Create HCW" button + `CreateHCWModal.tsx` + AS `admin_hcws_create` + Worker `POST /admin/api/hcws` route. `status::todo` `priority::high` `estimate::3h` `scrum::sprint-005`
- [ ] **E4-APRT-042** Per-tester admin user accounts hardening — documented onboarding pattern + (re-)seed `shan_admin` + `kidd_admin` on staging F2_Users via `seed-staging-admin.mjs`; runbook at `docs/runbooks/admin-onboarding.md`. `status::todo` `priority::high` `estimate::1h` `scrum::sprint-005`

### Goal B — F2 v2.0.1 release (Tier 1.5 — UAT R2 critical pull-ins, ✅ ALL SHIPPED OFF-SPRINT 2026-05-09)

Pulled from `scrum/triage-2026-05-09-off-sprint-backlog.md` and **all shipped Sat 2026-05-09 in the same off-sprint Saturday session**. Branch: `f2-admin-portal-v2.0.1` off `main@v2.0.0`. R3 testers verify in this round.

- [x] **R2-#118+#119** F2 PWA — Section G + Section J data loss on back-nav. Empty-multi-as-filled bug + missing runtime advance gate. `status::done` `actual::3h` `scrum::sprint-005` `severity::critical` `surface::f2-pwa-survey` `commit::484005e`
- [x] **R2-#114** F2 PWA — Sections C/D/E role-gating regression (3 personas tested). `shouldShowSection` only gated G; C/D/E hit the catch-all `return true`. Added SECTION_CDE_ROLES + SECTION_E_ROLES sets. `status::done` `actual::2h` `scrum::sprint-005` `severity::critical` `surface::f2-pwa-survey` `commit::35acbdd`
- [x] **R2-#122** F2 PWA — Double-submit dedup. Anchored client_submission_id on draft id (instead of fresh crypto.randomUUID per call). IDB primary-key upsert + server findExisting both work. `status::done` `actual::1h` `scrum::sprint-005` `severity::critical` `surface::f2-pwa-survey` `commit::bc4ef93`

### Goal B — F2 v2.0.1 release (Tier 1.5b — Bonus R2 fixes pre-built off-sprint, ✅ added 2026-05-09)

Continued the same Saturday session past the 4 criticals. Originally Sprint 006 v2.0.2 candidates per triage report; getting them into v2.0.1 lets R3 testers re-verify them this round.

- [x] **R2-#110** F2 PWA — make Q9 Months required (spec edit + regenerate items.ts/schema.ts). `status::done` `actual::30m` `severity::medium` `commit::211a06b`
- [x] **R2-#108** F2 PWA — token "rejected" → "malformed" copy (en + fil). `status::done` `actual::20m` `severity::low` `commit::641e35a`
- [x] **R2-#69** F2 admin — login "Username or password is incorrect" → "Invalid credentials". `status::done` `actual::20m` `severity::low` `commit::a953436`
- [x] **R2-#109** F2 PWA — distinct offline copy for E_NETWORK on token verify. `status::done` `actual::30m` `severity::low` `commit::70f8495`
- [x] **R2-#117** F2 PWA — item-level role-gate for Section E1 (Q48–Q52); pharmacists skip BUCAS, see only GAMOT. `status::done` `actual::1h` `severity::enhancement` `commit::0c649ce`
- [x] **R2-#93** F2 backend — force UTF-8 in `_gasHmacHex` for non-ASCII filenames (e.g., Plano-Q1-Niño.pdf). `status::done` `actual::1.5h` `severity::medium` `commit::4354701`
- [x] **R2-#120 S.A2** F2 PWA — persist submitted state across refresh via `f2_completed_csid` localStorage flag + "Start new survey" button. `status::done` `actual::1h` `severity::medium` `commit::b41caeb`

**Plus 3 cascade-resolutions** via GH comments + labels (no code change):
- [x] **R2-#112** B.E2 multi-select 0 selections — cascade-fixed by `484005e`. `status::done`
- [x] **R2-#115** C.E2 force-nav — resolved by `35acbdd` (different mechanism). `status::done`
- [x] **R2-#116** Q44 D auto-proceeds — cascade-fixed by `484005e`. `status::done`

### Stretch (not committed)

- [ ] **E4-APRT-049** Design-review 5-fix sweep — button focus rings (#59) + input focus rings (#60) + `rounded-full` sweep (#61) + QuotaWidget warning token (#62) + ReissueTokenModal Escape handler (design-M-4). `status::todo` `priority::medium` `estimate::40m`
- [ ] **E4-APRT-037** Concurrency tests — two-admin reissue race / bulk import + role edit / cron + PWA submit. `status::todo` `priority::medium` `estimate::3h`

> **Demoted to `unscheduled` 2026-05-08 (3-sprint stretch fatigue):** E2-F3-010, E2-F4-010, E0-008 — never pulled across Sprints 003/004/005. Re-pullable via planning when their gating context becomes pertinent (E2-F3-010/F4-010: F3/F4 instrument build slot opens; E0-008: when Day-1 retro-injection becomes valuable for a new tooling sprint).

## Sprint Backlog Sizing

| Class | Items | Estimate |
|---|---|---|
| **Committed (still to do)** | E3-F1-088, E3-F1-PHASE2-PLAN, E4-APRT-050/051/045/044/043, E4-APRT-048/041/042 | ~11h |
| **Done off-sprint 2026-05-09** | Tier 1.5 (#114, #118+#119, #122) + Tier 1.5b (#110, #108, #69, #109, #117, #93, #120-S.A2) + 3 cascade-resolutions | ~7h actuals |
| **Stretch (now feasible)** | E4-APRT-049, E4-APRT-037 | ~3.5h |

> Capacity: ~25h solo-dev week. Off-sprint Saturday session pre-built ~7h of Tier 1.5+1.5b work. Sprint 005 commits now ~11h leaving **~14h headroom** — Tier 3 stretch (~3.5h) very feasible; remainder reserved for R3 bug-fix triage as new findings come in. 3-sprint stretch carry-forwards (E2-F3-010, E2-F4-010, E0-008) demoted to `unscheduled` per Sprint 004 retro Q4. Plan doc: [`docs/superpowers/plans/2026-05-11-sprint-005-v2-0-1-plan.md`](../docs/superpowers/plans/2026-05-11-sprint-005-v2-0-1-plan.md). Off-sprint session log: 10 code commits on `f2-admin-portal-v2.0.1`, 17 R2 issues moved to `status:fixed-pending-verify`, full vitest 409/409 pass.

## Daily Notes

### 2026-05-11 (Mon) — Sprint 005 kickoff

- **Carry-forward from Sprint 004 retro Q4:** *File off-board worktree work as a sprint commitment within the first work session.* Sprint 005 explicitly applies this — **E3-F1-088** is on-board Day 1 as the worktree commitment for Phase 1 sync resolution; the worktree is no longer invisible to the sprint board. Bonus: post-commit Slack notifier surfaces work in `#capi-scrum` from Day 1.
- **Day 1 plan:** E3-F1-088 disposition decision (Path A or B); if Path A, build the supervisor "send" app and verify sync round-trip; if Path B, file Phase 2 sync architecture task and mark Plan 1 closed. Then Tier 1 hotfixes (E4-APRT-050 + E4-APRT-051 + E4-APRT-044). Push to `staging` EOD; CF Pages auto-deploy via `cf-pages-deploy.yml`; smoke against `https://f2-pwa-staging.pages.dev/admin`.
- **Branch strategy:** single `f2-admin-portal-v2.0.1` feature branch off `main`@`v2.0.0`; daily merges to `staging`; single ff-merge `staging`→`main` Fri tagged `v2.0.1`.
- **Anti-confusion guardrails (R2 prod + R3 staging in parallel):** pinned `#f2-pwa-uat` env-table message; two GH labels (`from-uat-round-2-2026-05` + `from-uat-round-3-2026-05-12`); same usernames cross-env with different passwords; schema migrations on staging only Mon-Thu, prod only Fri at cutover.

## Definition of Done — Sprint 005

- [ ] **E3-F1-088** closed: Phase 1 sync mechanic disposition (Path A or B) decided + executed; if Path A, supervisor "send" app sync round-trip verified; if Path B, Phase 2 sync revisit task filed.
- [ ] **E3-F1-PHASE2-PLAN** closed: Phase 2 plan doc saved at `docs/superpowers/plans/`; Phase 2 task IDs filed in epic-03 + Project #8.
- [ ] **Worktree merged:** `feature/uhc-survey-system-build` → `main` (or kept open with explicit reason in retro).
- [ ] **Tier 1 closed:** E4-APRT-050 + E4-APRT-051 + E4-APRT-045 + E4-APRT-044 + E4-APRT-043 all shipped + verified on staging.
- [ ] **Tier 2 closed:** E4-APRT-048 + E4-APRT-041 + E4-APRT-042 all shipped + verified on staging.
- [x] **Tier 1.5 closed off-sprint 2026-05-09:** R2-#118+#119 (G/J data loss) + R2-#114 (C/D/E role-gating) + R2-#122 (double-submit dedup) shipped on `f2-admin-portal-v2.0.1`; GH issues `status:fixed-pending-verify`.
- [x] **Tier 1.5b closed off-sprint 2026-05-09:** R2-#110 + #108 + #69 + #109 + #117 + #93 + #120-S.A2 shipped; cascade-resolutions for #112 + #115 + #116 via GH comments.
- [ ] **v2.0.1 cutover:** staging ff-merge to main Fri 2026-05-15; tag `v2.0.1` pushed; CF Pages auto-deploy fires; prod Worker deployed via `wrangler deploy`; `f2-pwa.pages.dev/admin` Versioning panel reports `v2.0.1`.
- [ ] **UAT R2 wind-down + R3 closure:** both rounds signed off by EOD Fri; v2.0.1 milestone closed → `uat-release-notes.yml` fires → CHANGELOG + GH Release + Slack post.
- [ ] **Sprint 005 retrospective** (4 questions) filled in `sprint-current.md` by EOD Fri 2026-05-15; sprint archived to `scrum/sprints/sprint-005.md`; `sprint-current.md` reset for Sprint 006.
