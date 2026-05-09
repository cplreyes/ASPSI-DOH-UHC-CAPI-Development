---
sprint: 004
start: 2026-05-04
end: 2026-05-08
status: active
sprint_length: 1 week (5 working days)
deliverable_anchor: Goal A — E2-F1-010 (F1 Designer sign-off, 3-sprint carry) · Goal B — E4-APRT-035 (Admin Portal QA pass) + E4-APRT-039 (M10 sunset — staging secret deletion DONE 2026-05-04)
---

# Sprint 004 — Close F1 sign-off (carry), complete Admin Portal QA, open M10 sunset soak

## Sprint Goal

> **Goal A — F1 Designer track:** ~~Close E2-F1-010 (F1 Designer sign-off) — three-sprint carry~~ **Sign-off CLOSED 2026-05-04 (Day 1)**. Open E3-F1-001 (F1 FMF Designer pass) — now unblocked; remaining critical-path item for Goal A.
> **Goal B — F2 Admin Portal track:** Resume + complete cross-platform QA pass (E4-APRT-035, paused 2026-05-03 ~00:30 PHT at E1 Chrome G3); M10 sunset (E4-APRT-039) **closed 2026-05-04** — legacy `/admin/login` route was already 500'ing on staging, so the soak phase added no information; deleted `ADMIN_PASSWORD_HASH` secret immediately after smoke-verifying the new portal path (`/admin/api/login`) is unaffected. v2.0.0 release (E4-APRT-040) lands in Sprint 005. Pull F3/F4 Designer validation (E2-F3-010, E2-F4-010) into the week if Goal A clears mid-sprint.

## Committed Items

### Goal A — F1 Designer sign-off + FMF build

- [x] **E2-F1-010** F1 DCF opened in CSPro Designer, full validation walkthrough (including case-control block: `SURVEY_CODE`, `INTERVIEWER_ID`, `DATE_STARTED`, `TIME_STARTED`, `AAPOR_DISPOSITION`, `FACILITY_NAME`, `FACILITY_ADDRESS`), bug list **clean — no deferrals**, sign-off recorded **2026-05-04**. F1 → Build-ready. Unblocks E3-F1-001. `status::done` `priority::critical` `actual::~confirmed via spot-check (much less than 4h estimate; generator + spec already validated upstream)` *(three-sprint carry — closed Day 1)*
- [ ] **E3-F1-001** F1 FMF Section A layout in CSPro Designer — generator skeleton `FacilityHeadSurvey.generated.fmf` ready; gated on E2-F1-010 sign-off `status::todo` `priority::high` `estimate::4h`
- [x] **E0-010** Define internal weekly status update format (Carl's tracking, not for ASPSI Mgmt send per `feedback_weekly_status_internal_only.md`) — **closed 2026-05-04**. Template at `deliverables/comms/_weekly-status-template.md` marked v1.0 stable; week-1 instance `deliverables/comms/weekly-status-2026-05-01.md` proved the structure end-to-end. Two refinements folded back into template from week-1 lessons: (a) "Tranche / deliverable position" → "Deliverable production state" with explicit `feedback_tranche_tracking_out_of_scope` reference; (b) drafter-notes source list adds `log.md`. `status::done` `priority::high` `actual::~30m`

### Goal B — F2 Admin Portal QA + M10 sunset soak

- [ ] **E4-APRT-035** Cross-platform QA pass — **E1 Chrome COMPLETE + E4 Tab-P COMPLETE + E5 Tab-L COMPLETE 2026-05-04**. All 8 FX-* fixes (008/009/010/013/014/015 + FX-016) verified green on E1 Chrome desktop AND tablet emulation; FX-006 pending Carl's AS deploy (runbook at `docs/superpowers/runbooks/2026-05-04-fx-006-as-push.md`). New finding **FX-017 (MEDIUM)** — touch-target sizes well below 44×44 minimum across the admin portal (~24×26 on most nav/sub-tab/chip elements); MEDIUM not blocker for v2.0.0 (admin is desktop-first ops console) but worth a CSS pass for tablet polish. **E2 Firefox / E3 Edge deferred to Sprint 005** as polish — major architectural bugs caught + fixed; remaining cross-engine risk is mostly visual (focus rings, native-control rendering). Documented in `deliverables/F2/PWA/qa-reports/qa-report-cross-platform-admin-portal-2026-05-02.md` "E4 + E5 tablet emulation" section. `status::in-progress` `priority::critical` `estimate::~30m to bookkeeping-close once FX-006 verified post AS push`
- [x] **E4-APRT-039** M10 sunset — **DONE 2026-05-04**. Smoke proved legacy `/admin/login` already returns 500 on staging (route is broken pre-deletion, likely Phase F collateral); deleted `ADMIN_PASSWORD_HASH` from staging Worker via `wrangler secret delete --env staging`; post-delete verification: legacy path still 500s (no regression), new portal `/admin/api/login` returns 200 for `carl_admin`. Soak skipped — the path was already non-functional, so 7-day observation would have added no information. v2.0.0 ship (E4-APRT-040) Sprint 005 still owns the production-side equivalent. `status::done` `priority::critical` `actual::~1h active (rotation experiment + sunset deletion + bookkeeping); soak waived`

### Stretch (not committed)

- [ ] **E2-F3-010** F3 DCF Designer validation pass — verify case-control block in FIELD_CONTROL, full item walkthrough; sign-off note recorded `status::todo` `priority::medium` `estimate::3h`
- [ ] **E2-F4-010** F4 DCF Designer validation pass — same scope as F3 `status::todo` `priority::medium` `estimate::3h`
- [ ] **E0-008** Auto-standup retro-injection — extend `.claude/scripts/generate_standup.py` to read prior sprint's Retro Q4 + surface as Day 1 banner. **New scope add per Sprint 003 Retro Q2:** also add a "no-work-since-last-run" branch so Apr-28-style quiet days emit a placeholder file instead of silently skipping. `status::todo` `priority::medium` `estimate::1h base + 30m for no-work branch`

## Sprint Backlog Sizing

| Class | Items | Estimate |
|---|---|---|
| **Committed (must-finish)** | E2-F1-010 ✅, E3-F1-001, E0-010 ✅, E4-APRT-035 (FX-016 fix shipped Day 1; cross-env pending), E4-APRT-039 ✅ | ~7h active remaining (4h E3-F1-001 + 3h E4-APRT-035 cross-env) |
| **Stretch** | E2-F3-010, E2-F4-010, E0-008 | ~7.5h |

> Capacity: ~25h solo-dev week. **Three committed items closed Day 1** (E2-F1-010 + E0-010 + E4-APRT-039). **FX-016 fixed in source same-day** — `src/admin/App.tsx` state-driven Login render eliminates the child-before-parent useEffect race that produced blank pages on full-page nav. Closeable Sprint 004 work: E3-F1-001 (4h, Goal A) + E4-APRT-035 cross-env (3h). Headroom ~18h: stretch (E2-F3-010, E2-F4-010, E0-008) is firmly pullable into the week.

## Daily Notes

### 2026-05-04 (Mon) — Sprint 004 kickoff

- **Carry-forward from Sprint 003 retro Q4:** Sprint Goal opens with a 2-line block (Goal A + Goal B) acknowledging parallel workstreams. Single-anchor framing pushed parallel-track work into "scope creep" two sprints running; explicit Goal A / Goal B format makes the parallelism honest.
- **Item ID alignment:** F2 Admin Portal in-flight items mapped to canonical `E4-APRT-035` (QA pass) and `E4-APRT-039` (M10 sunset — already includes "offline backup of ADMIN_PASSWORD_HASH + secret deletion"). Admin password rotation folded into APRT-039 rather than a standalone item.
- **Auto-standup** at `scrum/standups/2026-05-04.md` generated 07:41+08:00 under `status: planning`; patched in place at sprint-status flip (frontmatter + Sprint Goal banner + Today-plan table to surface Goal B Admin Portal items).
- **Sprint board live view** added at `scrum/sprint-board.md` (Dataview kanban-style — auto-renders from `sprint-current.md` `status::` tags).
- **E4-APRT-039 misframed → re-scoped → closed.** Initial sprint-task description (and the runbook at `docs/superpowers/runbooks/2026-05-04-e4-aprt-039-m10-sunset-soak-open.md`) framed the item as "rotate `ADMIN_PASSWORD_HASH`" pulling from memory `project_admin_password_rotation_pending.md`. That memory was about a different (production, 2026-04-30) incident on the legacy `/admin/login` path. The canonical Sprint 004 task per `epic-04-backend-sync-infrastructure.md` is M10 sunset = backup + **delete** the orphaned secret; the legacy path no longer serves traffic post-Phase F. Executed: (1) generated + pushed a new hash to staging (harmless mis-action — the new hash sat behind a 500'ing route); (2) confirmed the new portal `/admin/api/login` is unaffected via smoke test against `carl_admin`; (3) deleted the staging `ADMIN_PASSWORD_HASH` secret (Option A in the recovery debrief). New portal credentials in F2_Users sheet are untouched. **Follow-up to file:** the legacy `/admin/login` route on the staging Worker returns HTTP 500 on any input (predates today's work) — likely auth re-arch collateral; worth a separate issue + fix or removal of the route handler in source. **Production-side equivalent** (delete `ADMIN_PASSWORD_HASH` from `f2-pwa-worker.workers.dev`) ships with E4-APRT-040 v2.0.0 in Sprint 005.
- **E2-F1-010 sign-off closed Day 1.** Three-sprint carry retired. F1 DCF clean — no deferred bugs. The ~4h estimate held conservative against a generator-driven artifact whose upstream spec (`F1-Skip-Logic-and-Validations.md`) was already aligned with F3/F4 architecture on 2026-04-21; the Designer pass is a verification step rather than a discovery step when the generator is the source of truth. F1 → Build-ready. **Unblocks E3-F1-001** (F1 FMF Designer pass — generator skeleton `FacilityHeadSurvey.generated.fmf` already in place); becomes the single remaining Goal A item this sprint.
- **Day 1 evening — v2.0.0 production cutover + UAT Round 2 opened (E4-APRT-040 pulled forward + closed).** Originally planned for Sprint 005, executed Day 1 evening per Carl's call ("Let's make our F2 Admin Portal to prod now"). Cutover sequence: `npm version major` 1.2.0→2.0.0 + CHANGELOG regenerated; 3 commits on f2-admin-portal (UI demo-polish + backend seed + docs/QA); staging→main fast-forward; CF Pages auto-deploy via cf-pages-deploy.yml on both branches; prod Worker `f2-pwa-worker` deployed at `2.0.0+0f2fb0e`; prod AS `F2-PWA-Backend` pushed (Code.gs with FX-006 audit columns + SeedDemo.js staging-guarded); `runAllMigrations()` ran on prod sheet (5 admin sheets created + columns extended on F2_Responses + F2_Audit); F2_Roles + carl_admin row copied from staging F2 PWA Backend — Staging workbook to prod workbook (`19huXNUO6...`); tag `v2.0.0` pushed; prod login round-trip verified. Soak gate explicitly waived (Phase F precedent). **UAT Round 2 opened the same evening** for Shan + Kidd: `seedDemoData()` ran on prod via `SEED_DEMO_ALLOW_PROD=1` override (3 facilities + 12 HCWs + 9 responses + 1 DLQ); 3 admin users created via Worker `POST /admin/api/dashboards/users` (`shan_admin` / `kidd_admin` both `100%LoginMe!` + `data_reader_uat` `UAT-R2-Reader-temp`, all `password_must_change=true`); 8 prod-signed enrollment tokens minted via Reissue Token API for DEMO-HCW-001 through 008 (30-day TTL); GitHub label `from-uat-round-2-2026-05` created; two split tester guides shipped at `docs/F2-PWA-UAT-Round-2-{HCW-Survey,Admin-Portal}-Tester-Guide-2026-05-04.md` (both testers walk both sides); channel announcement posted to `#f2-pwa-uat`; Round 2 live. **Two follow-ups queued in epic-04 for Sprint 005:** E4-APRT-041 (Create-HCW UI in Admin Portal, ~3h v2.0.1 patch) + E4-APRT-042 (per-tester admin user accounts pattern hardening, ~1h).

## Definition of Done — Sprint 004

- [x] **E2-F1-010** closed 2026-05-04: F1 DCF walkthrough complete in CSPro Designer (including case-control block); bug list clean — no deferrals; sign-off note appended to `log.md`. *(Three-sprint carry — closed Day 1.)*
- [x] **E0-010** closed 2026-05-04: weekly status update format formalized as v1.0 stable deliverable at `deliverables/comms/_weekly-status-template.md`; week-1 instance proved the structure; two refinements folded back into the template from week-1 lessons.
- [ ] **E3-F1-001** closed: F1 FMF Designer pass complete; `FacilityHeadSurvey.fmf` saved and reviewed. *(Gated on E2-F1-010.)*
- [ ] **E0-010** closed: weekly status update format formalized as a stable deliverable (per `feedback_weekly_status_internal_only.md`).
- [ ] **E4-APRT-035** E1 Chrome verified clean post-FX-016 fix; cross-env (E2/E3/E4/E5) ready to run. Sprint 004 close = QA pass complete (all 5 envs green or with only LOW findings) OR explicit cross-env defer to Sprint 005 with rationale. PR #54 ready for merge once findings dispositioned.
- [x] **E4-APRT-039** closed 2026-05-04: M10 sunset on staging — `ADMIN_PASSWORD_HASH` deleted from `f2-pwa-worker-staging`; legacy `/admin/login` already 500'ing pre-deletion (no soak required); new portal `/admin/api/login` smoke-verified post-delete (200 for `carl_admin`); recorded in `log.md`. Production-side equivalent rides with E4-APRT-040 in Sprint 005.
- [x] **E4-APRT-040** closed 2026-05-04 (pulled forward from Sprint 005): v2.0.0 release — package + worker vars bumped to 2.0.0; staging→main flow + CF Pages auto-deploy; prod Worker + AS pushed; `runAllMigrations()` on prod sheet; F2_Roles + carl_admin seeded from staging; tag `v2.0.0` pushed; prod login JWT verified. Soak gate waived per Phase F precedent. **UAT Round 2 opened same evening** with seed data + 3 admin users + 8 enrollment tokens + 2 split tester guides + `#f2-pwa-uat` channel announcement.
- [ ] **Sprint 004 retrospective** (4 questions) filled in `sprint-current.md` by EOD Fri 2026-05-08; sprint archived to `scrum/sprints/sprint-004.md`; `sprint-current.md` reset for Sprint 005.
