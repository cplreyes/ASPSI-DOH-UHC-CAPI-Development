---
sprint: 004
start: 2026-05-04
end: 2026-05-08
status: planning
sprint_length: 1 week (5 working days)
deliverable_anchor: TBD at Mon 2026-05-04 kickoff
---

# Sprint 004 — TBD (planning, kickoff Mon 2026-05-04)

## Sprint Goal

> _TBD — write at Mon 2026-05-04 kickoff. Per Sprint 003 Retro Q4: this sprint goal should be a 2-line block acknowledging parallel workstreams, not a single anchor. Suggested shape:_
>
> **Goal A:** _Primary anchor — close E2-F1-010 (F1 Designer sign-off) — three-sprint carry, must not leave Sprint 004._
> **Goal B:** _Parallel tracks — resume F2 Admin Portal cross-platform QA pass (paused 2026-05-03 ~00:30 PHT at E1 Chrome G3) + open 7-day soak window on staging Worker JWT/admin bindings; pull F3/F4 Designer validation (E2-F3-010, E2-F4-010) into the week if Goal A clears mid-sprint._

## Committed Items

> _Stub — formalize at Mon 2026-05-04 kickoff. Carry-forward inventory below pulls from Sprint 003 unfinished work + parallel-track items in flight at sprint boundary._

### Carry-forward from Sprint 003 (priority order)

- [ ] **E2-F1-010** F1 DCF opened in CSPro Designer, full validation walkthrough (including case-control block: `SURVEY_CODE`, `INTERVIEWER_ID`, `DATE_STARTED`, `TIME_STARTED`, `AAPOR_DISPOSITION`, `FACILITY_NAME`, `FACILITY_ADDRESS`), bug list closed or explicitly deferred, sign-off note recorded `status::todo` `priority::critical` `estimate::4h` *(three-sprint carry — must not leave Sprint 004)*
- [ ] **E0-010** Define internal weekly status update format (Carl's tracking, not for ASPSI Mgmt send per `feedback_weekly_status_internal_only.md`) — partial-start: template + week-1 entry drafted at `deliverables/comms/_weekly-status-template.md` + `deliverables/comms/weekly-status-2026-05-01.md`; close = format formalized as a stable deliverable `status::in-progress` `priority::high` `estimate::1h to close`
- [ ] **E3-F1-001** F1 FMF Section A layout in CSPro Designer — generator skeleton `FacilityHeadSurvey.generated.fmf` ready; gated on E2-F1-010 sign-off `status::todo` `priority::high` `estimate::4h`

### F2 Admin Portal — in flight at sprint boundary

- [ ] **F2 Admin Portal cross-platform QA pass — resume** from paused state (memory `project_qa_pass_state_2026_05_02.md`). E1 Chrome through Section F + G1/G2 ✅ at pause; G3/H/Z + E2-E5 not started; 3 findings logged for triage. Sprint 004 close = QA pass complete (or explicitly deferred with rationale) `status::in-progress` `priority::critical` `estimate::TBD`
- [ ] **F2 Admin Portal v2.0.0 release gates** — cross-platform QA pass + 7-day staging soak (M10 sunset). PR #54 draft → ready for merge once gates clear. `status::in-progress` `priority::critical` `estimate::soak window-bound`
- [ ] **Admin password rotation** (open manual step from Sprint 003) — `deliverables/F2/PWA/worker/scripts/hash-admin-password.mjs` interactive run + `wrangler secret put ADMIN_PASSWORD_HASH` (memory `project_admin_password_rotation_pending.md`) `status::todo` `priority::high` `estimate::15m`

### Stretch carry-forward from Sprint 003

- [ ] **E2-F3-010** F3 DCF Designer validation pass `status::todo` `priority::medium` `estimate::3h`
- [ ] **E2-F4-010** F4 DCF Designer validation pass `status::todo` `priority::medium` `estimate::3h`
- [ ] **E0-008** Auto-standup retro-injection — extend `.claude/scripts/generate_standup.py` to read prior sprint's Retro Q4 + surface as Day 1 banner. **New scope add per Sprint 003 Retro Q2:** also add a "no-work-since-last-run" branch so Apr-28-style quiet days emit a placeholder file instead of silently skipping. `status::todo` `priority::medium` `estimate::1h base + 30m for no-work branch`

## Sprint Backlog Sizing

| Class | Items | Estimate |
|---|---|---|
| **Committed (must-finish)** | TBD at kickoff |  |
| **Stretch** | TBD at kickoff |  |

## Daily Notes

> _Empty — populates as Sprint 004 progresses. First entry at Mon 2026-05-04 kickoff should record carry-forward from Sprint 003 retro Q4 (parallel-workstream sprint-goal framing)._

## Definition of Done — Sprint 004

> _TBD at kickoff. Recurring checkboxes (carry over from prior sprints):_

- [ ] **Sprint 004 retrospective** (4 questions) filled in `sprint-current.md` by EOD Fri 2026-05-08; sprint archived to `scrum/sprints/sprint-004.md`; `sprint-current.md` reset for Sprint 005.
