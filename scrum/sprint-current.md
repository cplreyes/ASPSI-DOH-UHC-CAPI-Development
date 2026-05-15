---
sprint: 005
start: 2026-05-11
end: 2026-05-15
status: active
sprint_length: 1 week (5 working days)
deliverable_anchor: Goal A — E3-F1-088 (Phase 1 sync mechanic close-out) + E3-F1-PHASE2-PLAN (scope confirmation) · Goal B — Sprint 004 carry close-outs (E3-F1-001 FMF Designer, E4-PWA-014 verify, E4-PWA-015; E0-009 done Day 1 morning; E4-APRT-035 deferred to Sprint 006 to fit R3 cycle) · Goal C — F2 PWA HCW UAT Round 3 cycle (verify-already-shipped + close issues + new-scenarios tester guide + E6-PWA-007 R3 cycle Wed-Fri; NO dev burden — #266/#267/#268 shipped in v1.2.0 release 2026-05-01, surfaced 2026-05-11 late-PM)
---

# Sprint 005 — Close UHC Phase 1 sync, plan Phase 2, run F2 PWA Round 3 cycle (verify-shipped), close light carries

## Sprint Goal

> **Goal A — UHC tablet build (CAPI):** Close the last 5% of UHC Plan 1 — Phase 1 sync mechanics (`E3-F1-088`: syncdata external-dict + CSDB binding) — and confirm scope for Phase 2 (`E3-F1-PHASE2-PLAN`: PLF + F3 + F4_listing + F4 + supervisor menu + EA fence + daily audit Slack). Plan 1 reaches end-to-end-with-sync state by sprint close; Phase 2 has a written scope doc.
> **Goal B — Hygiene + light carries:** Issue-triage ritual (`E0-009`) DONE Day 1 morning. Close light Sprint 004 carries: `E3-F1-001` (F1 FMF Designer pass), `E4-PWA-014` (verify CF Pages auto-deploy resolution), `E4-PWA-015` (Worker PBKDF2 default). `E4-APRT-035` E2/E3 cross-env deferred to Sprint 006 to fit R3 cycle.
> **Goal C — F2 PWA HCW UAT Round 3 cycle (no dev — features already shipped):** Discovery 2026-05-11 late-PM: the three "R3 fix" GH issues (#266/#267/#268) were already implemented + shipped in v1.2.0 release on 2026-05-01; issues remained open as a process gap, not a code gap. Revised scope: verify shipped features in current prod (v2.0.0), close the three issues with code/test references, draft R3 split tester guide (verify-shipped + new-scenarios bundle), open `E6-PWA-007` UAT Round 3 to Shan + Kidd + Marriz Wed, close-out Fri. ~8h Carl-driven, no ship gate.

## Committed Items

### Goal A — UHC Phase 1 sync close-out + Phase 2 scope confirmation

- [~] **E3-F1-088** Phase 1 sync mechanic resolution — `syncdata` external-dict + CSDB binding. **PARTIAL 2026-05-12** — sync mechanics in code via the from-scratch CAPI rebuild (per `project_f3_listing_built_2026_05_12`); tablet verification pending Carl's off-keyboard session. Tablet test runbook at `52a0b27`. Worktree: `.claude/worktrees/uhc-survey-system-build`. *(Tablet-test slice carries to Sprint 006.)* `status::partial` `priority::critical` `estimate::6h`
- [x] **E3-F1-PHASE2-PLAN** Phase 2 plan + scope confirmation — **OVER-DELIVERED 2026-05-12** as built artifacts rather than scope-doc. The Tue 2026-05-12 from-scratch CAPI rebuild shipped F1 + F3 + F4 + 110_F3_listing + 113_F4_listing all end-to-end (83 worktree commits) + Phase 2 tablet test runbook (`52a0b27`). Per memory `project_f3_listing_built_2026_05_12`. `status::done` `priority::high` `estimate::3h`

### Goal B — Hygiene + Sprint 004 carries

- [x] **E0-009** Issue-triage ritual — Day 1 audit **DONE 2026-05-11 morning**. Slot framing decided (15 PR #136 closes kept tagged sprint-005 as off-sprint Saturday grind); R2 lane confirmed moot (30 `fixed-pending-verify` issues all closed; stale label stripped); 101/101 unscheduled Todo dispositioned (4 closed + 2 reslotted to sprint-006 + 95 annotated `unscheduled-by-design`); triage summary kept internal (durable record at `scrum/triage-2026-05-11.md`; Slack broadcast pattern adopted Sprint 006+ per `feedback_first_run_ritual_internal_only`). `status::done` `priority::critical` `estimate::3h`
- [ ] **E3-F1-001** F1 FMF Section A layout in CSPro Designer — generator skeleton `FacilityHeadSurvey.generated.fmf` ready. *(Sprint 004 carry — gated only by Carl's CSPro Designer time slot; not blocked technically.)* `status::todo` `priority::high` `estimate::4h`
- [~] **E4-APRT-035** Cross-platform QA pass close-out — E2 Firefox + E3 Edge passes. **DEFERRED to Sprint 006** (2026-05-11 R3-pivot decision: ~3h freed for R3 pivot absorption; risk mostly visual). PR #54 ready for merge once findings dispositioned. *(Sprint 004 carry.)* `status::deferred` `priority::high` `estimate::3h`
- [x] **E4-PWA-014** Verify CF Pages auto-deploy resolution (#34) — **closed 2026-05-11 PM** via state-confirmation: `gh run list --workflow=cf-pages-deploy.yml` last 8 main runs all `conclusion=success` (2026-05-09 → 2026-05-10); workflow gates on CI `workflow_run` completion. Issue #34 already closed via PR #136 inter-sprint. `status::done` `priority::high` `estimate::30m verify, ~3h fallback if regression returns`
- [x] **E4-PWA-015** Lower Worker PBKDF2 default to 100k (Workers runtime cap) — **closed 2026-05-11 PM** via state-confirmation: `worker/src/admin/auth.ts:18` reads `const PBKDF2_ITERATIONS = 100_000;`; companion seed script also 100k; ceiling constant `PBKDF2_CEIL = 100_000` at auth.ts:20 prevents future drift. Issue #35 already closed via PR #136 inter-sprint. `status::done` `priority::medium` `estimate::1h`

### Goal C — F2 PWA HCW UAT Round 3 cycle (revised 2026-05-11 late-PM after discovery)

**Discovery 2026-05-11 late-PM:** The three "R3 fix" issues (#266 exclusive "I don't know" / #267 "All of the above" auto-select / #268 scale matrix) were already implemented + shipped in v1.2.0 release on 2026-05-01. `Question.tsx::nextMultiValue` + `MatrixQuestion.tsx` carry the implementations; `Question.exclusivity.test.ts` (9 tests) + `MatrixQuestion.test.tsx` (8 tests) all green; `src/generated/items.ts` populates `isExclusive`/`isSelectAll` flags on real items (26 occurrences). Issues remained open as a process gap. Mid-PM "fix-then-ship" framing assumed work-pending; reality is work-already-done.

**Revised plan:** No dev burden. R3 still runs as verify-already-shipped + new-scenarios bundle (~8h Carl-driven, no ship). F1 anchor (`E3-F1-088`) restored to committed; only `E4-APRT-035` stays deferred to fit the R3 cycle.

- [x] **E3-F2-PWA-R3-VERIFY** Verify R3 features in current prod (v2.0.0) — **closed 2026-05-11 PM**: prod header confirmed `v2.0.0 · spec 2026-04-17-m1`; JS bundle `/assets/index-D5Xqbebh.js` contains 31× `isExclusive` + 5× `isSelectAll` occurrences (rule logic + spec data both shipped); enrolled DEMO-HCW-001 in headless browser, Section A walk green (Q5=Physician → Q6 specialty appears), Verde Manual styling renders. Full in-form interactive verification deferred to R3 testers. `status::done` `priority::high` `estimate::30m`
- [x] **E3-F2-PWA-R3-CLOSE-ISSUES** Close GH #266/#267/#268 — **closed 2026-05-11 PM**: all three closed with detailed comments (v1.2.0 release date 2026-05-01, release-notes URL, exact file:line code paths, test file paths, prod bundle evidence, process-gap explanation). Issue #271 retitled to reflect verify-shipped + new-scenarios scope on prod v2.0.0. `status::done` `priority::high` `estimate::30m`
- [ ] **E3-F2-PWA-R3-GUIDE** Draft R3 HCW survey tester guide at `docs/F2-PWA-UAT-Round-3-HCW-Survey-Tester-Guide-2026-05-13.md`. R2 regression + new-scenarios bundle. Mon PM. `status::done` `priority::high` `estimate::4h`
- [ ] **E3-F2-PWA-R3-ADMIN-GUIDE** Draft R3 Admin Portal tester guide at `docs/F2-PWA-UAT-Round-3-Admin-Portal-Tester-Guide-2026-05-13.md`. R2 + v2.0.1 regression (33 closures + 9 patches grouped) + new-scenarios bundle (concurrency, RBAC edges, cross-tab, kill-switch, audit completeness, tablet, large-data). Mon evening. `status::done` `priority::high` `estimate::3h`
- [ ] **E6-PWA-007** GH [#271](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/271) — UAT Round 3 cycle. Open Wed AM (Slack `#f2-pwa-uat` announcement + GitHub guide URL + per-tester admin credentials confirmed). Testers run Wed-Fri AM. Triage + close-out Fri PM. `status::todo` `priority::critical` `estimate::4h Carl-driven (intake + triage rolling)`

### Stretch (not committed — pull from Sprint 006 if base clears mid-week)

- [ ] **E3-F1-011** Add Filipino translations for all question labels and option text. *(Sprint 006 candidate.)* `priority::high` `estimate::4h`
- [ ] **E3-F1-012** Set up multi-language switching (`setlanguage`, language-select on cover page). *(Sprint 006 candidate.)* `priority::high` `estimate::3h`
- [ ] **E3-F1-020** Implement master skip gates (section-level eligibility filters). *(Sprint 006 candidate.)* `priority::high` `estimate::4h`

## Sprint Backlog Sizing

**Pre-pivot (committed Sun 2026-05-10 plan-lock):**

| Class | Items | Estimate |
|---|---|---|
| **Committed (must-finish)** | E3-F1-088, E3-F1-PHASE2-PLAN, E0-009, E3-F1-001, E4-APRT-035 (E2/E3), E4-PWA-014 verify, E4-PWA-015 | ~21h |
| **Already shipped Sat 2026-05-09 inter-sprint** | E4-APRT-041..051, E4-APRT-049a..e, E4-APRT-037 (15 items via PR #136) | n/a |
| **Stretch** | E3-F1-011, E3-F1-012, E3-F1-020 | ~11h |

**Post-pivot-on-pivot (revised Mon 2026-05-11 late-PM after R3-features-already-shipped discovery):**

| Class | Items | Estimate |
|---|---|---|
| **Committed (must-finish)** | E3-F1-088 (restored), E3-F1-PHASE2-PLAN, E3-F1-001, E4-PWA-014 verify, E4-PWA-015, E3-F2-PWA-R3-VERIFY, E3-F2-PWA-R3-CLOSE-ISSUES, E3-F2-PWA-R3-GUIDE, E6-PWA-007 | ~26h |
| **Done Day 1 morning** | E0-009 (3h) | n/a |
| **Already shipped Sat 2026-05-09 inter-sprint** | E4-APRT-041..051, E4-APRT-049a..e, E4-APRT-037 (15 items via PR #136) | n/a |
| **Already shipped 2026-05-01 (process gap surfaced 2026-05-11 late-PM)** | #266/#267/#268 in v1.2.0 release | n/a |
| **Deferred to Sprint 006** | E4-APRT-035 (-3h) | n/a |
| **Stretch** | DROPPED — no headroom | n/a |

> Capacity: ~25h solo-dev week. Revised committed ~26h is ~1h over — accept (or trim PHASE2-PLAN if it sprawls). **Framing decision (E0-009 Day-1 audit, 2026-05-11 morning):** the 15 admin-portal items closed via PR #136 (E4-APRT-041..051 + E4-APRT-049a..e + E4-APRT-037) are kept tagged sprint-005 as **"Sprint 005 admin-portal goal pre-shipped via off-sprint Saturday grind 2026-05-09."** **R3 pivot-on-pivot rationale (Mon late-PM):** the mid-PM "ship 3 fixes then run R3" plan was based on a wrong premise — features already shipped in v1.2.0 release on 2026-05-01 (10 days ago). GH issues #266/#267/#268 stayed open as a process gap, not code gap. Revised: no dev burden, R3 cycle still runs as verify-already-shipped + new-scenarios bundle (~8h Carl-driven), F1 anchor (E3-F1-088) restored. Only E4-APRT-035 stays deferred to absorb the R3 cycle hours. Velocity bookkeeping: PR #136 also documented under Sprint 004 archive Inter-Sprint Activity for cross-reference.

## Daily Notes

### 2026-05-11 (Mon) — Sprint 005 kickoff

- **Carry-forward from Sprint 004 retro Q4:** Day 1 = triage-first ritual before Goal A/B work (`E0-009`). Audit Project #8 sprint-005 slot framing first, then dispose of R2 + unscheduled backlog, then start sync close-out.
- **E0-009 audit findings (Day 1 morning):**
  - **Slot framing decided:** 15 PR #136 closes kept tagged sprint-005 as "admin-portal goal pre-shipped via off-sprint Saturday grind 2026-05-09" (see Sprint Backlog Sizing note above).
  - **Sync drift fixes:** #254 (E3-F1-001) reslotted sprint-004 → sprint-005 in Project #8; #240 (E0-001 recurring sprint-planning ritual) reslotted sprint-001 → unscheduled.
  - **R2 lane moot:** all 30 issues ever tagged `status:fixed-pending-verify` are CLOSED. Sub-task downgraded to label-hygiene cleanup pass (strip stale label from 30 closed issues).
  - **Open-issue label discipline gap surfaced:** 116 open issues in repo, ZERO have any GitHub-side labels (no `surface:`, `severity:`, `epic:`). Project #8 fields are populated; repo labels are not. Logged as observation; not actioned today.
- **Day 1 PM — F2 PWA HCW UAT Round 3 pivot decision (mid-PM):** Carl asked whether R3 was allowed + recommended. Round 2 closed clean Fri 2026-05-09 (47 issues); testers idle this week. Initial decision: ship `#266/#267/#268` (the three R3-feeder UX fixes — ~12h dev) → cut v1.2.0 Tue PM → open `E6-PWA-007` UAT Round 3 (verify + new-scenarios bundle) Wed AM → close-out Fri. New Goal C added; F1 sync close-out deferred; `E4-APRT-035` deferred; Stretch dropped.
- **Day 1 late-PM — pivot-on-pivot after discovery: R3 features already shipped in v1.2.0 release (2026-05-01).** Pre-coding source check found `Question.tsx::nextMultiValue` already implements `isExclusive` + `isSelectAll` rules with 9 passing tests in `Question.exclusivity.test.ts`; `MatrixQuestion.tsx` exists with 8 passing tests in `MatrixQuestion.test.tsx`; `src/generated/items.ts` has 26 occurrences of the new flags; `gh release list` shows `v1.2.0 — UAT Round 3 / Feature batch` released 2026-05-01, `v1.3.0` released same day, current prod is v2.0.0. GH issues #266/#267/#268/#271 remained OPEN as a process gap, not a code gap. Revised plan: no dev burden, R3 cycle still runs (verify-already-shipped + new-scenarios bundle), F1 anchor (`E3-F1-088`) RESTORED to Sprint 005 committed; only `E4-APRT-035` stays deferred to fit the R3 cycle. Goal C tasks rewritten: VERIFY + CLOSE-ISSUES + R3-GUIDE + E6-PWA-007 (no R3-001/002/003 dev tasks, no V120-CUT). Revised committed ~26h vs ~25h capacity (~1h over, accepted).

## Definition of Done — Sprint 005

- [ ] **E3-F1-088** closed: Phase 1 sync mechanic working end-to-end on tablet — `syncdata` external-dict + CSDB binding pushes F1 case data to staging CSWeb (or chosen sync target) on case end without operator intervention. Sync round-trip smoke recorded in `log.md`. *(Initially deferred 2026-05-11 PM, RESTORED late-PM after R3-features-already-shipped discovery.)*
- [ ] **E3-F1-PHASE2-PLAN** closed: Phase 2 scope doc written and reviewed. Covers PLF + F3 + F4_listing + F4 + supervisor menu + EA fence + daily audit Slack. Rough estimate per phase. Decisions on listing-app architecture, case-ID final form, F4 barangay listing held per `project_survey_manual_bundle_ingest_2026_05_07` until Myra's edit pass clears.
- [x] **E0-009** closed 2026-05-11 (Day 1 morning): Project #8 sprint-005 slot framing audited and decision recorded (15 PR #136 closes kept tagged sprint-005 as off-sprint-grind); 30 R2 `fixed-pending-verify` issues confirmed CLOSED + stale label stripped; 101/101 unscheduled Todo dispositioned (4 closed + 2 reslotted to sprint-006 + 95 annotated `unscheduled-by-design` via per-epic boilerplate comments); triage summary Slack post **skipped for first run** (internal-only — durable record in `scrum/triage-2026-05-11.md`; Slack broadcast pattern adopted Sprint 006+).
- [ ] **E3-F1-001** closed: F1 FMF Designer pass complete; `FacilityHeadSurvey.fmf` saved and reviewed. *(Carries from Sprint 004.)*
- [~] **E4-APRT-035** **DEFERRED to Sprint 006** (2026-05-11 R3 pivot). E2 Firefox + E3 Edge cross-env passes complete; PR #54 merged.
- [x] **E4-PWA-014** closed 2026-05-11 PM: CF Pages auto-deploy state confirmed via `gh run list --workflow=cf-pages-deploy.yml` — last 8 runs on `main` all `conclusion=success` (2026-05-09 to 2026-05-10). Workflow correctly gates on CI `workflow_run` completion. Issue #34 was already closed via PR #136 inter-sprint. Sprint task is state-confirmation only — no further action.
- [x] **E4-PWA-015** closed 2026-05-11 PM: Worker PBKDF2 default verified at 100k. `deliverables/F2/PWA/worker/src/admin/auth.ts:18` reads `const PBKDF2_ITERATIONS = 100_000;` (was 600k per #35); companion `worker/scripts/seed-staging-admin.mjs:36` also 100k; enforcement constant `PBKDF2_CEIL = 100_000` at auth.ts:20 prevents future drift. Issue #35 was already closed via PR #136 inter-sprint. Sprint task is state-confirmation only — no further action.
- [x] **E3-F2-PWA-R3-VERIFY** closed 2026-05-11 PM: prod v2.0.0 confirmed live (header `v2.0.0 · spec 2026-04-17-m1`); JS bundle `/assets/index-D5Xqbebh.js` contains 31 `isExclusive` + 5 `isSelectAll` occurrences (rule logic + spec data both shipped); enrolled DEMO-HCW-001 in headless browser, walked Section A, role-gating works (Q5=Physician → Q6 specialty appears), Verde Manual styling renders. Screenshot at `C:/Users/analy/AppData/Local/Temp/f2-prod-v2.0.0-section-a.png`. Full in-form interactive verification (Q25 exclusive rule, Q32 select-all rule, Section J matrix layout) deferred to R3 testers via the verify-shipped section of the tester guide.
- [x] **E3-F2-PWA-R3-CLOSE-ISSUES** closed 2026-05-11 PM: GH #266/#267/#268 all closed with detailed comments (release date 2026-05-01, v1.2.0 release notes URL, exact file:line code paths, test file paths, prod bundle evidence, process-gap explanation). Issue #271 re-titled from "[E6-PWA-007] UAT Round 3 (v1.2.0) — exclusive 'I don't know'..." to "[E6-PWA-007] UAT Round 3 — verify shipped features (v1.2.0 patterns) + new-scenarios bundle, on prod v2.0.0".
- [x] **E3-F2-PWA-R3-GUIDE** closed 2026-05-11 PM (revised late-PM per Carl's "fresh R3 not v1.3.0 internal-QA" framing): Round 3 tester guide at `docs/F2-PWA-UAT-Round-3-HCW-Survey-Tester-Guide-2026-05-13.md`. **5A R2 fix regression** (9 scenarios mapping to the 14 HCW-side R2 closures #108–#122 — token paste, Q9 year+month, Q25 exclusive, Section C YAKAP, Section D NBB/ZBB, Section E1/E2, Section G back-nav, Section J matrix, Submission+Sync) + **5B new-scenarios bundle** (offline / device matrix / edge data / resume / token edges). Verify-shipped (v1.2.0) framing dropped — those features pre-date R2 and would have been touched during R2 walks. Tokens reused from Round 2 (DEMO-HCW-001..008, valid until 2026-06-03). Pending Carl's review pre-announcement Wed AM.
- [x] **E3-F2-PWA-R3-ADMIN-GUIDE** closed 2026-05-11 evening (added per Carl's "forward the testing now" pivot to also include Admin Portal R3): Admin Portal R3 tester guide at `docs/F2-PWA-UAT-Round-3-Admin-Portal-Tester-Guide-2026-05-13.md`. **5A R2 + v2.0.1 regression** (19 scenarios — 13 covering the 33 admin R2 closures #68–#107 grouped by dashboard/area + 6 covering the v2.0.1 patch bundle E4-APRT-041/044/045/048/049/051) + **5B new-scenarios bundle** (concurrent multi-admin, RBAC edge cases, cross-tab session, kill-switch/spec-drift, audit log completeness, FX-017 tablet touch targets, large-data scenarios). Tester credentials reused from Round 2 (`shan_admin` / `kidd_admin`, R2-reset passwords). Pending Carl's review pre-announcement Wed AM.
- [ ] **E6-PWA-007** closed: Round 3 opened Wed 2026-05-13 to Shan (RA) + Kidd (main RA) + Marriz (Data Manager — focus on Sync/Map Report + Data dashboard) via `#f2-pwa-uat` Slack announcement + GitHub guide URLs + admin credentials. Testers run Wed-Fri AM. Triage rolling. R3 close-out Fri PM (label `from-uat-round-3-2026-05` created; all R3 issues triaged; sprint board updated).
- [x] **Sprint 005 retrospective** (4 questions) filled in `sprint-current.md` 2026-05-15; sprint to be archived to `scrum/sprints/sprint-005.md`; `sprint-current.md` reset for Sprint 006.

## Retrospective — Sprint 005

> 5-minute time-box. Four questions, fixed order. Written, not thought-through-only.
> Don't write self-congratulation; only write what changes next week's behavior.
>
> *Drafted by Claude on 2026-05-15 from log/git/memory evidence — Carl to review/edit before archival.*

### 1. Did the sprint goal land? (yes / partial / no — one line why)

Partial-with-overshoot. Goal C landed in-flight (R3 opened Wed AM to Shan + Kidd + Marriz; close-out E6-PWA-007 still rolling Fri PM). Goal B closed cleanly Mon PM via state-confirmation (E4-PWA-014, E4-PWA-015, R3-VERIFY, R3-CLOSE-ISSUES — all four were status-drift fixes; work was already done at sprint open). Goal A planning got out-shipped by a Tue 2026-05-12 from-scratch CAPI rebuild that brought F1 + F3 + F4 + 110_F3_listing + 113_F4_listing all end-to-end (83 worktree commits) + Phase 2 tablet test runbook — Phase 2 was *built*, not just planned; Phase 1 sync mechanic in code with tablet test pending; F1 FMF Designer pass (E3-F1-001) untouched by the rebuild and carries to Sprint 006 in its original shape. Net: 5/5 Goal-B-equivalent items closed, Goal A overshot scope on F3/F4/listing while leaving F1 FMF + tablet verification for Sprint 006.

### 2. What surprised me? (process, not work — max 3 bullets)

- **The sprint plan was a moving target three days running.** Sun resume plan (sync close + Phase 2 scope) → Mon mid-PM R3 pivot (ship 3 fixes then run R3) → Mon late-PM pivot-on-pivot after pre-coding source check (R3 features already shipped 2026-05-01) → Tue from-scratch CAPI rebuild that overshot the original Goal A entirely. Three "SUPERSEDED" memories were written in the first 36h of the sprint (`project_sprint_005_resume_plan`, `project_sprint_005_r3_pivot_2026_05_11`, `project_f3_listing_built_2026_05_12`). The retro structure assumes one direction across the week; this sprint had four.
- **R3 features being already-shipped surfaced a 10-day label-hygiene gap.** GH #266/#267/#268 stayed OPEN despite v1.2.0 shipping them 2026-05-01. Pre-coding source check (memory `feedback_pre_coding_source_check`) caught it before any wasted dev — saved ~12h. But the same Mon E0-009 audit found 116 open issues with zero repo-level labels (`surface:`, `severity:`, `epic:` — only Project #8 fields populated). The label-hygiene gap is structural, not one-off.
- **Wed/Thu quiet on main, loud upstream.** No main-branch commits 5/13–5/14 beyond auto session-end markers, but 5/13 ingested the Survey Manual v1.0 bundle (5 sources + 1 analysis; closed the divergence-deferral set per `feedback_defer_clarifications_during_upstream_review`) and 5/13 expanded the R3 roster (Marriz added). Auto-standup's "no-work-since-last-run" branch (E0-008) would have surfaced that the silence ≠ idle — third sprint in a row where E0-008 sat as stretch and didn't get pulled.

### 3. Deadline exposure check — D2 / D3 / Tranche 2 slip days this sprint

Out of Data Programmer scope per CSA D1–D6 (`feedback_tranche_tracking_out_of_scope.md`). Informational only: deliverable-side state at sprint close — F1 + F3 + F4 + both listing apps end-to-end on `feature/uhc-survey-system-build`; F2 PWA prod stable at v2.0.2 with R3 active to 3 testers (Shan + Kidd + Marriz); Survey Manual v1.0 ingestion complete (divergence-deferral closed); Phase 2 tablet test pending Carl's off-keyboard session.

### 4. One thing to change in Sprint 006

**Pull E0-008 (auto-standup no-work-since-last-run branch) into Sprint 006 *committed*, not stretch — third time it's been deferred.** Sprint 003 had Apr 28 silent, Sprint 004 had May 5/7 silent, Sprint 005 had May 13/14 quiet-on-main-but-loud-upstream. Each retro re-discovers this at archival rather than at the time. ~1h base + 30m for the no-work branch (per Sprint 004 estimate). Pair it with a 30m label-hygiene pass on the 116 open repo issues so the Mon E0-009 Q2 finding doesn't repeat at scale next sprint.
