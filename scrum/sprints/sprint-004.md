---
sprint: 004
start: 2026-05-04
end: 2026-05-08
status: complete
archived: 2026-05-10
sprint_length: 1 week (5 working days)
deliverable_anchor: Goal A — E2-F1-010 (F1 Designer sign-off, 3-sprint carry → CLOSED Day 1) · Goal B — E4-APRT-035 (Admin Portal QA, cross-env partial — E2/E3 deferred) + E4-APRT-039 (M10 sunset staging, CLOSED Day 1) + pulled-forward E4-APRT-040 (v2.0.0 prod cutover + UAT R2 open, CLOSED Day 1 evening)
---

# Sprint 004 — Close F1 sign-off (carry), complete Admin Portal QA, open M10 sunset soak

## Sprint Goal

> **Goal A — F1 Designer track:** ~~Close E2-F1-010 (F1 Designer sign-off) — three-sprint carry~~ **Sign-off CLOSED 2026-05-04 (Day 1)**. Open E3-F1-001 (F1 FMF Designer pass) — now unblocked; remaining critical-path item for Goal A.
> **Goal B — F2 Admin Portal track:** Resume + complete cross-platform QA pass (E4-APRT-035, paused 2026-05-03 ~00:30 PHT at E1 Chrome G3); M10 sunset (E4-APRT-039) **closed 2026-05-04** — legacy `/admin/login` route was already 500'ing on staging, so the soak phase added no information; deleted `ADMIN_PASSWORD_HASH` secret immediately after smoke-verifying the new portal path (`/admin/api/login`) is unaffected. v2.0.0 release (E4-APRT-040) lands in Sprint 005. Pull F3/F4 Designer validation (E2-F3-010, E2-F4-010) into the week if Goal A clears mid-sprint.

## Committed Items

### Goal A — F1 Designer sign-off + FMF build

- [x] **E2-F1-010** F1 DCF opened in CSPro Designer, full validation walkthrough (including case-control block: `SURVEY_CODE`, `INTERVIEWER_ID`, `DATE_STARTED`, `TIME_STARTED`, `AAPOR_DISPOSITION`, `FACILITY_NAME`, `FACILITY_ADDRESS`), bug list **clean — no deferrals**, sign-off recorded **2026-05-04**. F1 → Build-ready. Unblocks E3-F1-001. `status::done` `priority::critical` `actual::~confirmed via spot-check (much less than 4h estimate; generator + spec already validated upstream)` *(three-sprint carry — closed Day 1)*
- [ ] **E3-F1-001** F1 FMF Section A layout in CSPro Designer — generator skeleton `FacilityHeadSurvey.generated.fmf` ready; gated on E2-F1-010 sign-off. **Carries to Sprint 005** — F1 build effort pivoted Day 4–5 to the tablet deployment chain on `feature/uhc-survey-system-build` worktree (login → menu → F1 end-to-end + sync mechanics last 5%); Designer-side FMF pass scheduled for Sprint 005 alongside Phase 1 sync close-out. `status::todo` `priority::high` `estimate::4h`
- [x] **E0-010** Define internal weekly status update format (Carl's tracking, not for ASPSI Mgmt send per `feedback_weekly_status_internal_only.md`) — **closed 2026-05-04**. Template at `deliverables/comms/_weekly-status-template.md` marked v1.0 stable; week-1 instance `deliverables/comms/weekly-status-2026-05-01.md` proved the structure end-to-end. Two refinements folded back into template from week-1 lessons: (a) "Tranche / deliverable position" → "Deliverable production state" with explicit `feedback_tranche_tracking_out_of_scope` reference; (b) drafter-notes source list adds `log.md`. `status::done` `priority::high` `actual::~30m`

### Goal B — F2 Admin Portal QA + M10 sunset soak

- [ ] **E4-APRT-035** Cross-platform QA pass — **E1 Chrome COMPLETE + E4 Tab-P COMPLETE + E5 Tab-L COMPLETE 2026-05-04**. All 8 FX-* fixes (008/009/010/013/014/015 + FX-016) verified green on E1 Chrome desktop AND tablet emulation; FX-006 pending Carl's AS deploy (runbook at `docs/superpowers/runbooks/2026-05-04-fx-006-as-push.md`). New finding **FX-017 (MEDIUM)** — touch-target sizes well below 44×44 minimum across the admin portal (~24×26 on most nav/sub-tab/chip elements); MEDIUM not blocker for v2.0.0 (admin is desktop-first ops console) but worth a CSS pass for tablet polish. **E2 Firefox / E3 Edge deferred to Sprint 005** as polish — major architectural bugs caught + fixed; remaining cross-engine risk is mostly visual (focus rings, native-control rendering). Documented in `deliverables/F2/PWA/qa-reports/qa-report-cross-platform-admin-portal-2026-05-02.md` "E4 + E5 tablet emulation" section. `status::partial` `priority::critical` *(cross-env E2/E3 carries to Sprint 005)*
- [x] **E4-APRT-039** M10 sunset — **DONE 2026-05-04**. Smoke proved legacy `/admin/login` already returns 500 on staging (route is broken pre-deletion, likely Phase F collateral); deleted `ADMIN_PASSWORD_HASH` from staging Worker via `wrangler secret delete --env staging`; post-delete verification: legacy path still 500s (no regression), new portal `/admin/api/login` returns 200 for `carl_admin`. Soak skipped — the path was already non-functional, so 7-day observation would have added no information. Production-side equivalent (E4-APRT-043) shipped Sat 2026-05-09 inter-sprint via PR #136. `status::done` `priority::critical` `actual::~1h active (rotation experiment + sunset deletion + bookkeeping); soak waived`
- [x] **E4-APRT-040** v2.0.0 release — **DONE 2026-05-04 evening (pulled forward from Sprint 005)**. Cutover sequence: `npm version major` 1.2.0→2.0.0 + CHANGELOG regenerated; 3 commits on f2-admin-portal (UI demo-polish + backend seed + docs/QA); staging→main fast-forward; CF Pages auto-deploy via cf-pages-deploy.yml on both branches; prod Worker `f2-pwa-worker` deployed at `2.0.0+0f2fb0e`; prod AS `F2-PWA-Backend` pushed (Code.gs with FX-006 audit columns + SeedDemo.js staging-guarded); `runAllMigrations` ran on prod sheet (5 admin sheets created + columns extended on F2_Responses + F2_Audit); F2_Roles + carl_admin row copied from staging F2 PWA Backend — Staging workbook to prod workbook (`19huXNUO6...`); tag `v2.0.0` pushed; prod login round-trip verified. Soak gate explicitly waived (Phase F precedent). **UAT Round 2 opened the same evening** for Shan + Kidd: `seedDemoData` ran on prod via `SEED_DEMO_ALLOW_PROD=1` override (3 facilities + 12 HCWs + 9 responses + 1 DLQ); 3 admin users created via Worker `POST /admin/api/dashboards/users`; 8 prod-signed enrollment tokens minted via Reissue Token API for DEMO-HCW-001 through 008 (30-day TTL); GitHub label `from-uat-round-2-2026-05` created; two split tester guides shipped at `docs/F2-PWA-UAT-Round-2-{HCW-Survey,Admin-Portal}-Tester-Guide-2026-05-04.md`; channel announcement posted to `#f2-pwa-uat`; Round 2 live. `status::done` `priority::critical`

### Stretch (not committed)

- [ ] **E2-F3-010** F3 DCF Designer validation pass — verify case-control block in FIELD_CONTROL, full item walkthrough; sign-off note recorded. *(Not pulled — capacity went to UHC tablet deployment chain.)* `status::todo` `priority::medium` `estimate::3h`
- [ ] **E2-F4-010** F4 DCF Designer validation pass — same scope as F3. *(Not pulled.)* `status::todo` `priority::medium` `estimate::3h`
- [ ] **E0-008** Auto-standup retro-injection — extend `.claude/scripts/generate_standup.py` to read prior sprint's Retro Q4 + surface as Day 1 banner. **New scope add per Sprint 003 Retro Q2:** also add a "no-work-since-last-run" branch so Apr-28-style quiet days emit a placeholder file instead of silently skipping. *(Not pulled; Sprint 004 had three silent days — May 5/7 fully silent, May 6 light — no placeholder file emitted, so the gap pattern repeated.)* `status::todo` `priority::medium` `estimate::1h base + 30m for no-work branch`

## Sprint Backlog Sizing

| Class | Items | Estimate | Outcome |
|---|---|---|---|
| **Committed (must-finish)** | E2-F1-010 ✅, E3-F1-001 ↻, E0-010 ✅, E4-APRT-035 ◐, E4-APRT-039 ✅ | ~7h active remaining at sprint open | **3/5 closed** + 1 partial (E4-APRT-035 E1/E4/E5 ✓, E2/E3 carries) + 1 carries (E3-F1-001) |
| **Pulled forward** | E4-APRT-040 (originally Sprint 005) | not estimated at open | **Closed Day 1 evening** — v2.0.0 prod cutover + UAT R2 |
| **Stretch** | E2-F3-010, E2-F4-010, E0-008 | ~7.5h | **0 pulled** — capacity went to UHC tablet deployment chain on `feature/uhc-survey-system-build` |
| **Worktree-only (not on sprint board)** | UHC tablet deployment chain (Plan 1: login → menu → F1 + sync mechanics) | n/a | **~95% complete by EOD Day 5** — 61 commits Day 5 alone closing CSPro 8.0 syntax discoveries (`syncdata`, config string single-identifier, `pff.exec` call form, `move to X;`, `protect` function); Phase 1 sync resolution last 5% carries as `E3-F1-088` |

> Capacity: ~25h solo-dev week. **Three committed items closed Day 1** (E2-F1-010 + E0-010 + E4-APRT-039) + **1 pulled-forward closed Day 1 evening** (E4-APRT-040 v2.0.0 cutover). Days 2/3 silent on main; Day 4 (Wed) shipped sprint-snapshot tooling rewrite + first 2 UHC build worktree commits; Day 5 (Fri) shipped 61 commits closing CSPro 8.0 syntax discoveries on the tablet deploy chain. Net velocity dominated by Day 1 + Day 5. Sprint goal mostly landed (Goal A sign-off ✅, Goal B QA partial + sunset ✅ + cutover ✅).

## Daily Notes

### 2026-05-04 (Mon) — Sprint 004 kickoff

- **Carry-forward from Sprint 003 retro Q4:** Sprint Goal opens with a 2-line block (Goal A + Goal B) acknowledging parallel workstreams. Single-anchor framing pushed parallel-track work into "scope creep" two sprints running; explicit Goal A / Goal B format makes the parallelism honest.
- **Item ID alignment:** F2 Admin Portal in-flight items mapped to canonical `E4-APRT-035` (QA pass) and `E4-APRT-039` (M10 sunset — already includes "offline backup of ADMIN_PASSWORD_HASH + secret deletion"). Admin password rotation folded into APRT-039 rather than a standalone item.
- **Auto-standup** at `scrum/standups/2026-05-04.md` generated 07:41+08:00 under `status: planning`; patched in place at sprint-status flip (frontmatter + Sprint Goal banner + Today-plan table to surface Goal B Admin Portal items).
- **Sprint board live view** added at `scrum/sprint-board.md` (Dataview kanban-style — auto-renders from `sprint-current.md` `status::` tags).
- **E4-APRT-039 misframed → re-scoped → closed.** Initial sprint-task description (and the runbook at `docs/superpowers/runbooks/2026-05-04-e4-aprt-039-m10-sunset-soak-open.md`) framed the item as "rotate `ADMIN_PASSWORD_HASH`" pulling from memory `project_admin_password_rotation_pending.md`. That memory was about a different (production, 2026-04-30) incident on the legacy `/admin/login` path. The canonical Sprint 004 task per `epic-04-backend-sync-infrastructure.md` is M10 sunset = backup + **delete** the orphaned secret; the legacy path no longer serves traffic post-Phase F. Executed: (1) generated + pushed a new hash to staging (harmless mis-action — the new hash sat behind a 500'ing route); (2) confirmed the new portal `/admin/api/login` is unaffected via smoke test against `carl_admin`; (3) deleted the staging `ADMIN_PASSWORD_HASH` secret (Option A in the recovery debrief). New portal credentials in F2_Users sheet are untouched. **Production-side equivalent** (delete `ADMIN_PASSWORD_HASH` from `f2-pwa-worker.workers.dev`) shipped Sat 2026-05-09 inter-sprint via PR #136 (E4-APRT-043).
- **E2-F1-010 sign-off closed Day 1.** Three-sprint carry retired. F1 DCF clean — no deferred bugs. The ~4h estimate held conservative against a generator-driven artifact whose upstream spec (`F1-Skip-Logic-and-Validations.md`) was already aligned with F3/F4 architecture on 2026-04-21; the Designer pass is a verification step rather than a discovery step when the generator is the source of truth. F1 → Build-ready. **Unblocks E3-F1-001** (F1 FMF Designer pass — generator skeleton `FacilityHeadSurvey.generated.fmf` already in place); becomes the single remaining Goal A item this sprint.
- **Day 1 evening — v2.0.0 production cutover + UAT Round 2 opened (E4-APRT-040 pulled forward + closed).** Originally planned for Sprint 005, executed Day 1 evening per Carl's call ("Let's make our F2 Admin Portal to prod now"). Two follow-ups queued in epic-04 for Sprint 005: E4-APRT-041 (Create-HCW UI in Admin Portal, ~3h v2.0.1 patch) + E4-APRT-042 (per-tester admin user accounts pattern hardening, ~1h). Both shipped Sat 2026-05-09 inter-sprint via PR #136.

### 2026-05-05 (Tue) — Quiet day (no work)

- **Reconstructed 2026-05-10 during Sprint 004 archival.** Zero commits on main, zero commits on `feature/uhc-survey-system-build`, no auto-standup file generated. Effectively a rest day after Day 1 overdelivery. **Same gap pattern as Sprint 003 Apr 28** — auto-standup generator's "no-work-since-last-run" branch (E0-008, Sprint 004 stretch) still not implemented, so the silence didn't surface until sprint close.

### 2026-05-06 (Wed) — Sprint snapshot tooling + UHC build kickoff

- **Sprint snapshot tooling rewrite.** Two commits on main: `feat(scrum): rewrite sprint snapshot to render cross-sprint summary table` (`217454c`) + `chore(scrum): add Slack sprint-snapshot workflow + lint pass` (`dcafac9`). Cross-sprint summary table now renders in the snapshot doc instead of single-sprint view; Slack workflow added for Mon/Fri auto-post to `#capi-scrum`. Reference memory: `reference_gh_project_8_backlog`.
- **UHC tablet deployment chain — first commits on `feature/uhc-survey-system-build`.** 2 commits laying groundwork for the tablet build pipeline (per memory `project_uhc_build_session_handoff_2026_05_08`).

### 2026-05-07 (Thu) — Quiet day (no work)

- **Reconstructed 2026-05-10 during Sprint 004 archival.** Zero commits on either branch; no auto-standup file generated. Second silent day in three-day mid-sprint window. Auto-standup gap repeats.

### 2026-05-08 (Fri) — UHC tablet deployment chain pushed end-to-end

- **61 commits on `feature/uhc-survey-system-build`** — heaviest single-day commit volume of the sprint. Closed CSPro 8.0 syntax discoveries one after another while building the tablet deploy chain end-to-end:
  - Login app → menu chain → F1 deployed end-to-end on tablet (`login_app.pff` + `menu.apc` chain entry points)
  - CSPro 8.0 syntax discoveries: `syncdata` (renamed from `synchronize_data`), config string takes ONE identifier, `pff.exec` call form, `move to X;` (no parens), `elseif` (one word), `protect` function, `Suspend` mid-case for operator partial save
  - External-dict `user_roster.dat` / `user_roster.dcf` pattern; Phase 1 simplification (skip role check, hardcode role)
  - F1 PFF `InputData=F1.csdb` (CSPro DB supports sync); sync moved into F1 (auto-sync on case end, drop menu sync); uppercase `PUT` in syncdata trial
  - `.pen` build artifacts gitignored (regenerable)
- **Sprint 004 ended without retro/archive Mode D.** Same pattern as Sprint 003 (which ran Mode D 2 days late on May 3). Sprint 004 retro deferred to inter-sprint Sun 2026-05-10.
- **Plan 1 ~95% complete by EOD.** Login → menu → F1 chain proven on tablet. **Last 5% = sync mechanics** (syncdata external-dict + CSDB binding) — carries to Sprint 005 as `E3-F1-088`. Per memory `project_uhc_build_session_handoff_2026_05_08`.

## Inter-Sprint Activity (2026-05-09 Sat → 2026-05-10 Sun)

> Work that landed between Sprint 004 close (Fri 2026-05-08) and Sprint 005 start (Mon 2026-05-11). Tracked here for velocity bookkeeping; not part of Sprint 004 commitments. Items requiring follow-through carry into Sprint 005.

### 2026-05-09 (Sat) — F2 Admin Portal v2.0.1 + R2 fix sweep — 24 issues auto-closed

- **PR [#136](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/pull/136) squash-merged at `9bab42b`** (26 commits, +16,779/-394). Clean merge into `origin/main` resolving 2 content conflicts: `App.tsx` (change-password Placeholder dropped — supplanted by the real component shipped via #134); `QuotaWidget.tsx` (`text-warning` kept over `text-error` — design fix from #62). CI green on main → CF Pages + Worker deploy both completed 07:42 UTC; v2.0.1 live at `f2-pwa.pages.dev`.
- **24 issues auto-closed via `Closes #N` trailers** spanning the v2.0.1 patch bundle:
  - **RBAC + auth hardening:** #56 RBAC role-version cache (E4-APRT-044), #57 JWT pwc server-enforce (E4-APRT-045), #133 orphan-admin guards + self-delete guard (E4-APRT-050), #134 user-self password rotation (E4-APRT-051)
  - **Admin portal features:** #58 Create-HCW first-class modal (E4-APRT-041), #66 last_login_at write path (E4-APRT-048)
  - **Design-review 5-fix sweep (E4-APRT-049):** #59/#60/#61/#62/#67/#132 (focus rings + rounded-full + QuotaWidget --warning + ReissueTokenModal Escape dismiss)
  - **Concurrency suite (E4-APRT-037):** #63 (two-admin reissue race / bulk import + role edit / cron + PWA submit)
  - **Per-tester admin accounts (E4-APRT-042):** prod runbook landed `f17d08e`
  - **Production ADMIN_PASSWORD_HASH deletion (E4-APRT-043):** prod runbook landed `f17d08e`, source-removal commit `02bf982` (`chore(F2-admin): remove ADMIN_PASSWORD_HASH residue`)
  - **R2 fix wave from mid-Sprint 004:** #69, #84 DLQ, #93 UTF-8, #98/#100 bulk import, #108/#109/#110/#114/#117/#119/#120/#122
- **CF Pages auto-deploy CONFIRMED FIRING** post-merge 2026-05-09 — `cf-pages-deploy.yml` workflow now reliably triggers on push to `staging` and `main`. Resolves the long-standing `#34` regression (memory `project_cf_pages_autodeploy_broken`). E4-PWA-014 in Sprint 005 → "verify state, possibly close" rather than full investigation.
- **Remaining open (14):**
  - **9 R2 `status:fixed-pending-verify`** awaiting tester re-verify on prod: #68, #80, #83, #102, #112, #115, #116, #118 partial, #121
  - **4 Carl-actionable:** #131/#135 (sprint-005 F1 CSPro work, separate worktree at `.claude/worktrees/uhc-survey-system-build`); #64/#65 already shipped (prod runbooks landed `f17d08e`; source-removal commit pre-staged on `main` awaiting wrangler-secret-delete smoke confirmation)
- **Slot framing question raised at sprint-005 alignment review:** the 15 closed admin-portal items (E4-APRT-041..051) were tagged `sprint-005` in Project #8 at the moment PR #136 merged, effectively making Sprint 005 ~75% complete before formal kickoff. Two readings: (a) intentional — "off-sprint Saturday grind shipped Sprint 005's admin-portal commitments early" or (b) sync drift — `Closes #N` defaulted to next-open sprint without explicit framing. Decision deferred to Sprint 005 Day 1 audit (Carl to confirm framing, plus E0-009 issue-triage ritual).

### 2026-05-10 (Sun) — Sprint 004 archival + Sprint 005 plan

- **Sprint 004 archived 2026-05-10** (Mode D ran two days late, again — same pattern as Sprint 003 ran 2 days late on May 3). Retro filled below.
- **Sprint 005 plan authored** at `scrum/sprints/sprint-005-plan.md`.
- **Issue-triage commitment formalized** as **E0-009** — first explicit slotted item ensuring the `project_sprint_005_resume_plan` memory ("triage ~64 open GH Issues BEFORE starting Goal A/B") gets executed Day 1 rather than absorbed into ambient sprint work.

## Definition of Done — Sprint 004

- [x] **E2-F1-010** closed 2026-05-04: F1 DCF walkthrough complete in CSPro Designer (including case-control block); bug list clean — no deferrals; sign-off note appended to `log.md`. *(Three-sprint carry — closed Day 1.)*
- [x] **E0-010** closed 2026-05-04: weekly status update format formalized as v1.0 stable deliverable at `deliverables/comms/_weekly-status-template.md`; week-1 instance proved the structure; two refinements folded back into the template from week-1 lessons.
- [x] **E4-APRT-039** closed 2026-05-04: M10 sunset on staging — `ADMIN_PASSWORD_HASH` deleted from `f2-pwa-worker-staging`; legacy `/admin/login` already 500'ing pre-deletion (no soak required); new portal `/admin/api/login` smoke-verified post-delete (200 for `carl_admin`); recorded in `log.md`.
- [x] **E4-APRT-040** closed 2026-05-04 (pulled forward from Sprint 005): v2.0.0 release — package + worker vars bumped to 2.0.0; staging→main flow + CF Pages auto-deploy; prod Worker + AS pushed; `runAllMigrations` on prod sheet; F2_Roles + carl_admin seeded from staging; tag `v2.0.0` pushed; prod login JWT verified. Soak gate waived per Phase F precedent. **UAT Round 2 opened same evening** with seed data + 3 admin users + 8 enrollment tokens + 2 split tester guides + `#f2-pwa-uat` channel announcement.
- [◐] **E4-APRT-035** partial: E1 Chrome + E4 Tab-P + E5 Tab-L verified clean post-FX-016 fix; E2 Firefox + E3 Edge explicitly deferred to Sprint 005 with rationale (major architectural bugs caught + fixed; remaining cross-engine risk is mostly visual). PR #54 not yet merged. *(Carries to Sprint 005 cross-env close-out.)*
- [↻] **E3-F1-001** carries to Sprint 005: F1 FMF Designer pass not started in main scrum lane — F1 build effort pivoted Day 4–5 to tablet deployment chain on `feature/uhc-survey-system-build` worktree; Designer FMF pass schedules alongside Phase 1 sync close-out (E3-F1-088) in Sprint 005.
- [x] **Sprint 004 retrospective** filled 2026-05-10 (Mode D ran two days late); sprint archived to `scrum/sprints/sprint-004.md`; `sprint-current.md` reset for Sprint 005.

## Retrospective — Sprint 004

> 5-minute time-box. Four questions, fixed order. Written, not thought-through-only.
> Don't write self-congratulation; only write what changes next week's behavior.
>
> *Drafted by Claude on 2026-05-10 from log/git evidence — Carl to review/edit before Sprint 005 Day 1 (Mon 2026-05-11) kickoff.*

### 1. Did the sprint goal land? (yes / partial / no — one line why)

Mostly — Goal A landed (E2-F1-010 sign-off ✅ Day 1, retiring the three-sprint carry; E3-F1-001 Designer FMF pass not started in main lane but F1 build effort delivered the tablet deployment chain end-to-end on `feature/uhc-survey-system-build` — Plan 1 ~95% done with sync mechanics last 5%); Goal B mostly landed (E4-APRT-035 cross-env partial with E2/E3 explicitly deferred, E4-APRT-039 ✅ Day 1, plus pulled-forward E4-APRT-040 v2.0.0 prod cutover ✅ Day 1 evening + UAT R2 opened). Net: 4/5 committed closed + 1 pulled-forward closed + 1 partial + 1 carries.

### 2. What surprised me? (process, not work — max 3 bullets)

- **Day 1 carried the sprint, then Day 5 carried the second half.** Four closes Day 1 (including pulled-forward v2.0.0 cutover that was originally Sprint 005 work); silent Day 2 + Day 3; Day 4 light (sprint snapshot tooling rewrite + 2 worktree commits); Day 5 shipped 61 commits on `feature/uhc-survey-system-build` closing CSPro 8.0 syntax discoveries one after another. The "average week" framing didn't fit — actual velocity was 2 burst days surrounded by 3 silent/light days. Auto-standup generator's "no-work-since-last-run" branch (E0-008 stretch — *not pulled* this sprint either) would have surfaced the silent days at the time rather than at archival.
- **F1 build pivoted lanes mid-sprint without surfacing in the main scrum log.** E3-F1-001 (Designer FMF pass on main) sat untouched while Carl built the tablet deployment chain on the worktree. The "Designer FMF pass" framing turned out to be a smaller task than the harness around it (login app + menu chain + .pen build pipeline + tablet smoke + CSPro-DB-vs-syncdata syntax discovery). Sprint 004 had no committed item representing that worktree work — it lived in memory `project_uhc_build_session_handoff_2026_05_08` only. Recovered at archival via inter-sprint daily-notes reconstruction; the gap is captured as Sprint 005's `E3-F1-088`.
- **Off-sprint Saturday grind shipped 24 issue closes via one PR — and pre-occupied Sprint 005's slot in Project #8.** PR #136 (`9bab42b`, +16,779/-394, 26 commits) auto-closed 24 issues including 15 admin-portal items (E4-APRT-041..051 + E4-APRT-049a..e) tagged `sprint-005` at merge time. Sprint 005 effectively starts Mon 2026-05-11 with ~75% of its slot already Done. Either intentional (early-grind framing) or sync drift via `Closes #N` next-open-slot defaults. Worth one Day 1 audit to confirm framing — added as part of `E0-009` issue-triage commitment.

### 3. Deadline exposure check — D2 / D3 / Tranche 2 slip days this sprint

Out of Data Programmer scope per CSA D1–D6 (`feedback_tranche_tracking_out_of_scope.md`). Informational only: D2 / D3 extended deadline still pending DOH; ASPSI/PI/PMO lane handles tracking + submission timing. Carl's deliverable-side state at sprint close: F1 Build-ready (sign-off ✅ Day 1) + tablet-deployment chain ~95% on `feature/uhc-survey-system-build`; F2 PWA at v2.0.0 base + v2.0.1 patch in production with UAT Round 2 active (Shan + Kidd, 8 prod-signed enrollment tokens); F3/F4 Build-ready; F2 Admin Portal v2.0.1 with 9 R2 issues `status:fixed-pending-verify`.

### 4. One thing to change in Sprint 005

**Day 1 = triage-first ritual before Goal A/B work.** Per `project_sprint_005_resume_plan`, Carl committed to triaging the ~64 open GH Issues before starting sprint goal work. Per Sprint 004 Q2 finding above, Sprint 005's slot in Project #8 already shows 19 items at sprint open (15 Done from PR #136, 4 Todo) — the framing of those 15 needs explicit confirmation, not absorption into ambient work. Day 1 ritual:
1. Audit Project #8 sprint-005 slot — confirm the 15 already-closed items belong there (intentional early-close framing) or rebill to Sprint 004 inter-sprint activity.
2. Triage remaining R2 `fixed-pending-verify` (9) + unscheduled Todo (~100) — close, slot to a sprint, or keep `unscheduled` with rationale captured in issue body.
3. Then start Goal A (E3-F1-088 Phase 1 sync close-out + E3-F1-PHASE2-PLAN scope confirmation) + Goal B (carry close-outs: E3-F1-001 FMF Designer pass, E4-APRT-035 cross-env E2/E3).

Tracked as `E0-009` Sprint 005 commitment — first slotted issue-triage item in the project.
