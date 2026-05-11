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
> **Goal C — F2 PWA HCW UAT Round 3 cycle (no dev — features already shipped):** Discovery 2026-05-11 late-PM: the three "R3 fix" GH issues (#266/#267/#268) were already implemented + shipped in v1.2.0 release on 2026-05-01; issues remained open as a process gap, not a code gap. Revised scope: verify shipped features in current prod (v2.0.0), close the three issues with code/test references, draft R3 split tester guide (verify-shipped + new-scenarios bundle), open `E6-PWA-007` UAT Round 3 to Shan + Kidd Wed, close-out Fri. ~8h Carl-driven, no ship gate.

## Committed Items

### Goal A — UHC Phase 1 sync close-out + Phase 2 scope confirmation

- [ ] **E3-F1-088** Phase 1 sync mechanic resolution — `syncdata` external-dict + CSDB binding. Last 5% of Plan 1 (Sprint 004 Day 5 closed login → menu → F1 chain on tablet; sync mechanics carry). Per `project_uhc_build_session_handoff_2026_05_08`. Worktree: `.claude/worktrees/uhc-survey-system-build`. *(Initially deferred 2026-05-11 PM under R3-pivot framing, then RESTORED late-PM after R3-features-already-shipped discovery — no dev burden, F1 anchor stays.)* `status::todo` `priority::critical` `estimate::6h`
- [ ] **E3-F1-PHASE2-PLAN** Phase 2 plan + scope confirmation — PLF + F3 + F4_listing + F4 + supervisor menu + EA fence + daily audit Slack. Written scope doc at `docs/superpowers/specs/2026-05-11-uhc-phase-2-scope.md` (or similar). `status::todo` `priority::high` `estimate::3h`

### Goal B — Hygiene + Sprint 004 carries

- [x] **E0-009** Issue-triage ritual — Day 1 audit **DONE 2026-05-11 morning**. Slot framing decided (15 PR #136 closes kept tagged sprint-005 as off-sprint Saturday grind); R2 lane confirmed moot (30 `fixed-pending-verify` issues all closed; stale label stripped); 101/101 unscheduled Todo dispositioned (4 closed + 2 reslotted to sprint-006 + 95 annotated `unscheduled-by-design`); triage summary kept internal (durable record at `scrum/triage-2026-05-11.md`; Slack broadcast pattern adopted Sprint 006+ per `feedback_first_run_ritual_internal_only`). `status::done` `priority::critical` `estimate::3h`
- [ ] **E3-F1-001** F1 FMF Section A layout in CSPro Designer — generator skeleton `FacilityHeadSurvey.generated.fmf` ready. *(Sprint 004 carry — gated only by Carl's CSPro Designer time slot; not blocked technically.)* `status::todo` `priority::high` `estimate::4h`
- [~] **E4-APRT-035** Cross-platform QA pass close-out — E2 Firefox + E3 Edge passes. **DEFERRED to Sprint 006** (2026-05-11 R3-pivot decision: ~3h freed for R3 pivot absorption; risk mostly visual). PR #54 ready for merge once findings dispositioned. *(Sprint 004 carry.)* `status::deferred` `priority::high` `estimate::3h`
- [ ] **E4-PWA-014** Verify CF Pages auto-deploy resolution (#34) — auto-deploy fired post-merge 2026-05-09 per Sprint 004 Inter-Sprint Activity; this item likely closes via state-confirmation rather than full investigation. `status::todo` `priority::high` `estimate::30m verify, ~3h fallback if regression returns`
- [ ] **E4-PWA-015** Lower Worker PBKDF2 default to 100k (Workers runtime cap) — #35. Single-line config change + smoke. `status::todo` `priority::medium` `estimate::1h`

### Goal C — F2 PWA HCW UAT Round 3 cycle (revised 2026-05-11 late-PM after discovery)

**Discovery 2026-05-11 late-PM:** The three "R3 fix" issues (#266 exclusive "I don't know" / #267 "All of the above" auto-select / #268 scale matrix) were already implemented + shipped in v1.2.0 release on 2026-05-01. `Question.tsx::nextMultiValue` + `MatrixQuestion.tsx` carry the implementations; `Question.exclusivity.test.ts` (9 tests) + `MatrixQuestion.test.tsx` (8 tests) all green; `src/generated/items.ts` populates `isExclusive`/`isSelectAll` flags on real items (26 occurrences). Issues remained open as a process gap. Mid-PM "fix-then-ship" framing assumed work-pending; reality is work-already-done.

**Revised plan:** No dev burden. R3 still runs as verify-already-shipped + new-scenarios bundle (~8h Carl-driven, no ship). F1 anchor (`E3-F1-088`) restored to committed; only `E4-APRT-035` stays deferred to fit the R3 cycle.

- [ ] **E3-F2-PWA-R3-VERIFY** Verify R3 features in current prod (v2.0.0): exclusive "I don't know" rule (Q with #16-pattern), "All of the above" auto-select rule (Q with #17-pattern), matrix view (consecutive single-type questions sharing scale choices). 30 min in-browser smoke. Mon late-PM. `status::todo` `priority::high` `estimate::30m`
- [ ] **E3-F2-PWA-R3-CLOSE-ISSUES** Close GH #266/#267/#268 with comments referencing v1.2.0 release + code paths (`Question.tsx::nextMultiValue`, `MatrixQuestion.tsx`) + test paths (`Question.exclusivity.test.ts`, `MatrixQuestion.test.tsx`). Note process gap. Mon late-PM. `status::todo` `priority::high` `estimate::30m`
- [ ] **E3-F2-PWA-R3-GUIDE** Draft R3 tester guide at `docs/F2-PWA-UAT-Round-3-HCW-Survey-Tester-Guide-2026-05-13.md`. Scope: verify shipped features in prod v2.0.0 + new-scenarios bundle (offline / device matrix [real Android tablet + low-end Android phone + iPhone Safari + Firefox mobile] / edge data [long text, special chars, Word paste, whitespace, emoji] / resume [mid-form close + force-quit recovery] / token edges [expired, reused, malformed paste, copy with extra whitespace]). Modeled on Round 2 split-guide format. Tue. `status::todo` `priority::high` `estimate::4h`
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
- [ ] **E4-PWA-014** closed: CF Pages auto-deploy state confirmed (one push to staging + one to main both fire `cf-pages-deploy.yml` workflow without manual `wrangler pages deploy`); #34 closed.
- [ ] **E4-PWA-015** closed: Worker PBKDF2 default lowered to 100k; smoke green; #35 closed.
- [x] **E3-F2-PWA-R3-VERIFY** closed 2026-05-11 PM: prod v2.0.0 confirmed live (header `v2.0.0 · spec 2026-04-17-m1`); JS bundle `/assets/index-D5Xqbebh.js` contains 31 `isExclusive` + 5 `isSelectAll` occurrences (rule logic + spec data both shipped); enrolled DEMO-HCW-001 in headless browser, walked Section A, role-gating works (Q5=Physician → Q6 specialty appears), Verde Manual styling renders. Screenshot at `C:/Users/analy/AppData/Local/Temp/f2-prod-v2.0.0-section-a.png`. Full in-form interactive verification (Q25 exclusive rule, Q32 select-all rule, Section J matrix layout) deferred to R3 testers via the verify-shipped section of the tester guide.
- [x] **E3-F2-PWA-R3-CLOSE-ISSUES** closed 2026-05-11 PM: GH #266/#267/#268 all closed with detailed comments (release date 2026-05-01, v1.2.0 release notes URL, exact file:line code paths, test file paths, prod bundle evidence, process-gap explanation). Issue #271 re-titled from "[E6-PWA-007] UAT Round 3 (v1.2.0) — exclusive 'I don't know'..." to "[E6-PWA-007] UAT Round 3 — verify shipped features (v1.2.0 patterns) + new-scenarios bundle, on prod v2.0.0".
- [x] **E3-F2-PWA-R3-GUIDE** closed 2026-05-11 PM: Round 3 tester guide drafted at `docs/F2-PWA-UAT-Round-3-HCW-Survey-Tester-Guide-2026-05-13.md` (~280 lines, modeled on Round 2 format). Two parts: 5A verify-shipped (Q25 exclusive / Q32 select-all+exclusive / Section J matrix) + 5B new-scenarios bundle (offline / device matrix / edge data / resume / token edges). HCW-survey-only this round (no Admin Portal companion). Tokens reused from Round 2 (DEMO-HCW-001..008, valid until 2026-06-03). Pending Carl's review pre-announcement Wed AM.
- [ ] **E6-PWA-007** closed: Round 3 opened Wed 2026-05-13 to Shan + Kidd via `#f2-pwa-uat` Slack announcement + GitHub guide URL + admin credentials. Testers run Wed-Fri AM. Triage rolling. R3 close-out Fri PM (label `from-uat-round-3-2026-05` created; all R3 issues triaged; sprint board updated).
- [ ] **Sprint 005 retrospective** (4 questions) filled in `sprint-current.md` by EOD Fri 2026-05-15; sprint archived to `scrum/sprints/sprint-005.md`; `sprint-current.md` reset for Sprint 006.
