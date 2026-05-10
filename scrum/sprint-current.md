---
sprint: 005
start: 2026-05-11
end: 2026-05-15
status: active
sprint_length: 1 week (5 working days)
deliverable_anchor: Goal A — E3-F1-088 (Phase 1 sync mechanic close-out, last 5% of UHC build) + E3-F1-PHASE2-PLAN (scope confirmation) · Goal B — E0-009 (issue-triage Day 1 ritual) + carry close-outs (E3-F1-001 FMF Designer, E4-APRT-035 E2/E3 cross-env, E4-PWA-014 verify, E4-PWA-015)
---

# Sprint 005 — Close UHC Phase 1 sync, plan Phase 2, triage backlog, close Sprint 004 carries

## Sprint Goal

> **Goal A — UHC tablet build (CAPI):** Close the last 5% of UHC Plan 1 — Phase 1 sync mechanics (`E3-F1-088`: syncdata external-dict + CSDB binding) — and confirm scope for Phase 2 (`E3-F1-PHASE2-PLAN`: PLF + F3 + F4_listing + F4 + supervisor menu + EA fence + daily audit Slack). Plan 1 reaches end-to-end-with-sync state by sprint close; Phase 2 has a written scope doc.
> **Goal B — Hygiene + carries:** Run the issue-triage ritual Day 1 (`E0-009`) BEFORE goal work — audit Project #8 sprint-005 slot framing for the 15 items closed via PR #136 (intentional early-grind vs. sync drift), and dispose of the ~9 R2 `fixed-pending-verify` + ~100 unscheduled Todo issues. Close Sprint 004 carries: `E3-F1-001` (F1 FMF Designer pass), `E4-APRT-035` E2/E3 cross-env, `E4-PWA-014` (verify CF Pages auto-deploy resolution), `E4-PWA-015` (Worker PBKDF2 default).

## Committed Items

### Goal A — UHC Phase 1 sync close-out + Phase 2 scope confirmation

- [ ] **E3-F1-088** Phase 1 sync mechanic resolution — `syncdata` external-dict + CSDB binding. Last 5% of Plan 1 (Sprint 004 Day 5 closed login → menu → F1 chain on tablet; sync mechanics carry). Per `project_uhc_build_session_handoff_2026_05_08`. Worktree: `.claude/worktrees/uhc-survey-system-build`. `status::todo` `priority::critical` `estimate::6h`
- [ ] **E3-F1-PHASE2-PLAN** Phase 2 plan + scope confirmation — PLF + F3 + F4_listing + F4 + supervisor menu + EA fence + daily audit Slack. Written scope doc at `docs/superpowers/specs/2026-05-11-uhc-phase-2-scope.md` (or similar). `status::todo` `priority::high` `estimate::3h`

### Goal B — Hygiene + Sprint 004 carries

- [ ] **E0-009** Issue-triage ritual — Day 1 audit. Three sub-tasks per Sprint 004 Retro Q4: (1) audit Project #8 sprint-005 slot — confirm framing of the 15 already-closed items; (2) triage 9 R2 `fixed-pending-verify` + ~100 unscheduled Todo issues (close / slot to a sprint / keep unscheduled with rationale captured in issue body); (3) post triage summary to `#capi-scrum`. `status::todo` `priority::critical` `estimate::3h`
- [ ] **E3-F1-001** F1 FMF Section A layout in CSPro Designer — generator skeleton `FacilityHeadSurvey.generated.fmf` ready. *(Sprint 004 carry — gated only by Carl's CSPro Designer time slot; not blocked technically.)* `status::todo` `priority::high` `estimate::4h`
- [ ] **E4-APRT-035** Cross-platform QA pass close-out — E2 Firefox + E3 Edge passes only (E1/E4/E5 already verified Sprint 004 Day 1). PR #54 ready for merge once findings dispositioned. *(Sprint 004 carry.)* `status::todo` `priority::high` `estimate::3h`
- [ ] **E4-PWA-014** Verify CF Pages auto-deploy resolution (#34) — auto-deploy fired post-merge 2026-05-09 per Sprint 004 Inter-Sprint Activity; this item likely closes via state-confirmation rather than full investigation. `status::todo` `priority::high` `estimate::30m verify, ~3h fallback if regression returns`
- [ ] **E4-PWA-015** Lower Worker PBKDF2 default to 100k (Workers runtime cap) — #35. Single-line config change + smoke. `status::todo` `priority::medium` `estimate::1h`

### Stretch (not committed — pull from Sprint 006 if base clears mid-week)

- [ ] **E3-F1-011** Add Filipino translations for all question labels and option text. *(Sprint 006 candidate.)* `priority::high` `estimate::4h`
- [ ] **E3-F1-012** Set up multi-language switching (`setlanguage`, language-select on cover page). *(Sprint 006 candidate.)* `priority::high` `estimate::3h`
- [ ] **E3-F1-020** Implement master skip gates (section-level eligibility filters). *(Sprint 006 candidate.)* `priority::high` `estimate::4h`

## Sprint Backlog Sizing

| Class | Items | Estimate |
|---|---|---|
| **Committed (must-finish)** | E3-F1-088, E3-F1-PHASE2-PLAN, E0-009, E3-F1-001, E4-APRT-035 (E2/E3), E4-PWA-014 verify, E4-PWA-015 | ~21h |
| **Already shipped Sat 2026-05-09 inter-sprint** | E4-APRT-041..051, E4-APRT-049a..e, E4-APRT-037 (15 items via PR #136) | n/a |
| **Stretch** | E3-F1-011, E3-F1-012, E3-F1-020 | ~11h |

> Capacity: ~25h solo-dev week. Committed ~21h leaves ~4h headroom — pull at most one Sprint 006 candidate as stretch (E3-F1-011 if multilingual is the priority, E3-F1-020 if skip gates are). **15 admin-portal items already Done** in Project #8 sprint-005 slot. **Framing decision (E0-009 Day-1 audit, 2026-05-11):** these 15 items (E4-APRT-041..051 + E4-APRT-049a..e + E4-APRT-037) are kept tagged sprint-005 as **"Sprint 005 admin-portal goal pre-shipped via off-sprint Saturday grind 2026-05-09 (PR #136)."** Sprint 005 effectively starts Day 1 with ~75% of slot already Done; remaining sprint scope is the 5 explicit Todo items above (Goal A + Goal B carries). Velocity bookkeeping: PR #136 also documented under Sprint 004 archive Inter-Sprint Activity for cross-reference.

## Daily Notes

### 2026-05-11 (Mon) — Sprint 005 kickoff

- **Carry-forward from Sprint 004 retro Q4:** Day 1 = triage-first ritual before Goal A/B work (`E0-009`). Audit Project #8 sprint-005 slot framing first, then dispose of R2 + unscheduled backlog, then start sync close-out.
- **E0-009 audit findings (Day 1 morning):**
  - **Slot framing decided:** 15 PR #136 closes kept tagged sprint-005 as "admin-portal goal pre-shipped via off-sprint Saturday grind 2026-05-09" (see Sprint Backlog Sizing note above).
  - **Sync drift fixes:** #254 (E3-F1-001) reslotted sprint-004 → sprint-005 in Project #8; #240 (E0-001 recurring sprint-planning ritual) reslotted sprint-001 → unscheduled.
  - **R2 lane moot:** all 30 issues ever tagged `status:fixed-pending-verify` are CLOSED. Sub-task downgraded to label-hygiene cleanup pass (strip stale label from 30 closed issues).
  - **Open-issue label discipline gap surfaced:** 116 open issues in repo, ZERO have any GitHub-side labels (no `surface:`, `severity:`, `epic:`). Project #8 fields are populated; repo labels are not. Logged as observation; not actioned today.

## Definition of Done — Sprint 005

- [ ] **E3-F1-088** closed: Phase 1 sync mechanic working end-to-end on tablet — `syncdata` external-dict + CSDB binding pushes F1 case data to staging CSWeb (or chosen sync target) on case end without operator intervention. Sync round-trip smoke recorded in `log.md`.
- [ ] **E3-F1-PHASE2-PLAN** closed: Phase 2 scope doc written and reviewed. Covers PLF + F3 + F4_listing + F4 + supervisor menu + EA fence + daily audit Slack. Rough estimate per phase. Decisions on listing-app architecture, case-ID final form, F4 barangay listing held per `project_survey_manual_bundle_ingest_2026_05_07` until Myra's edit pass clears.
- [x] **E0-009** closed 2026-05-11 (Day 1 morning): Project #8 sprint-005 slot framing audited and decision recorded (15 PR #136 closes kept tagged sprint-005 as off-sprint-grind); 30 R2 `fixed-pending-verify` issues confirmed CLOSED + stale label stripped; 101/101 unscheduled Todo dispositioned (4 closed + 2 reslotted to sprint-006 + 95 annotated `unscheduled-by-design` via per-epic boilerplate comments); triage summary Slack post **skipped for first run** (internal-only — durable record in `scrum/triage-2026-05-11.md`; Slack broadcast pattern adopted Sprint 006+).
- [ ] **E3-F1-001** closed: F1 FMF Designer pass complete; `FacilityHeadSurvey.fmf` saved and reviewed. *(Carries from Sprint 004.)*
- [ ] **E4-APRT-035** closed: E2 Firefox + E3 Edge cross-env passes complete (or explicitly deferred with rationale); PR #54 merged.
- [ ] **E4-PWA-014** closed: CF Pages auto-deploy state confirmed (one push to staging + one to main both fire `cf-pages-deploy.yml` workflow without manual `wrangler pages deploy`); #34 closed.
- [ ] **E4-PWA-015** closed: Worker PBKDF2 default lowered to 100k; smoke green; #35 closed.
- [ ] **Sprint 005 retrospective** (4 questions) filled in `sprint-current.md` by EOD Fri 2026-05-15; sprint archived to `scrum/sprints/sprint-005.md`; `sprint-current.md` reset for Sprint 006.
