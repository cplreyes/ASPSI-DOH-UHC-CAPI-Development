---
sprint: 004
start: 2026-05-04
end: 2026-05-08
status: active
sprint_length: 1 week (5 working days)
deliverable_anchor: Goal A — E2-F1-010 (F1 Designer sign-off, 3-sprint carry) · Goal B — E4-APRT-035 (Admin Portal QA pass) + E4-APRT-039 (M10 sunset soak window opening)
---

# Sprint 004 — Close F1 sign-off (carry), complete Admin Portal QA, open M10 sunset soak

## Sprint Goal

> **Goal A — F1 Designer track:** Close E2-F1-010 (F1 Designer sign-off) — three-sprint carry, must not leave Sprint 004. Open E3-F1-001 (F1 FMF Designer pass) on the same anchor once sign-off lands.
> **Goal B — F2 Admin Portal track:** Resume + complete cross-platform QA pass (E4-APRT-035, paused 2026-05-03 ~00:30 PHT at E1 Chrome G3); execute M10 sunset opening (E4-APRT-039) — rotate `ADMIN_PASSWORD_HASH` on staging Worker, smoke test, open the 7-day soak window with daily monitoring cadence so v2.0.0 release (E4-APRT-040) lands in Sprint 005. Pull F3/F4 Designer validation (E2-F3-010, E2-F4-010) into the week if Goal A clears mid-sprint.

## Committed Items

### Goal A — F1 Designer sign-off + FMF build

- [ ] **E2-F1-010** F1 DCF opened in CSPro Designer, full validation walkthrough (including case-control block: `SURVEY_CODE`, `INTERVIEWER_ID`, `DATE_STARTED`, `TIME_STARTED`, `AAPOR_DISPOSITION`, `FACILITY_NAME`, `FACILITY_ADDRESS`), bug list closed or explicitly deferred, sign-off note recorded `status::todo` `priority::critical` `estimate::4h` *(three-sprint carry — must not leave Sprint 004)*
- [ ] **E3-F1-001** F1 FMF Section A layout in CSPro Designer — generator skeleton `FacilityHeadSurvey.generated.fmf` ready; gated on E2-F1-010 sign-off `status::todo` `priority::high` `estimate::4h`
- [ ] **E0-010** Define internal weekly status update format (Carl's tracking, not for ASPSI Mgmt send per `feedback_weekly_status_internal_only.md`) — partial-start: template + week-1 entry drafted at `deliverables/comms/_weekly-status-template.md` + `deliverables/comms/weekly-status-2026-05-01.md`; close = format formalized as a stable deliverable `status::in-progress` `priority::high` `estimate::1h to close`

### Goal B — F2 Admin Portal QA + M10 sunset soak

- [ ] **E4-APRT-035** Cross-platform QA pass — resume from paused state (memory `project_qa_pass_state_2026_05_02.md`). E1 Chrome through Section F + G1/G2 ✅ at pause; G3/H/Z + E2-E5 not started; 3 findings logged for triage. Sprint 004 close = QA pass complete (or explicitly deferred with rationale); PR #54 ready for merge once findings dispositioned. `status::in-progress` `priority::critical` `estimate::~6h remaining`
- [ ] **E4-APRT-039** M10 sunset — execute `deliverables/F2/PWA/worker/scripts/hash-admin-password.mjs` (interactive) + `wrangler secret put ADMIN_PASSWORD_HASH --env staging` (memory `project_admin_password_rotation_pending.md`); offline backup of new hash; staging smoke test; open 7-day soak window with daily `wrangler tail --env staging` scan for 5xx + auth failures; halt + investigate if sustained error rate >0.5% over any 1h window. v2.0.0 ship (E4-APRT-040) lands in Sprint 005 once soak clears. `status::todo` `priority::critical` `estimate::~1.5h active + 7-day passive monitoring`

### Stretch (not committed)

- [ ] **E2-F3-010** F3 DCF Designer validation pass — verify case-control block in FIELD_CONTROL, full item walkthrough; sign-off note recorded `status::todo` `priority::medium` `estimate::3h`
- [ ] **E2-F4-010** F4 DCF Designer validation pass — same scope as F3 `status::todo` `priority::medium` `estimate::3h`
- [ ] **E0-008** Auto-standup retro-injection — extend `.claude/scripts/generate_standup.py` to read prior sprint's Retro Q4 + surface as Day 1 banner. **New scope add per Sprint 003 Retro Q2:** also add a "no-work-since-last-run" branch so Apr-28-style quiet days emit a placeholder file instead of silently skipping. `status::todo` `priority::medium` `estimate::1h base + 30m for no-work branch`

## Sprint Backlog Sizing

| Class | Items | Estimate |
|---|---|---|
| **Committed (must-finish)** | E2-F1-010, E3-F1-001, E0-010, E4-APRT-035, E4-APRT-039 | ~16.5h active + soak monitoring |
| **Stretch** | E2-F3-010, E2-F4-010, E0-008 | ~7.5h |

> Capacity: ~25h solo-dev week. Hard commits ~16.5h active + soak monitoring leaves ~8h for stretch (F3/F4 Designer passes) if Goal A clears mid-sprint. Goal A is sequential (E2-F1-010 → E3-F1-001); Goal B runs parallel — open the M10 sunset soak window early in the week (E4-APRT-039), run E4-APRT-035 QA pass alongside, then collapse onto Goal A. Daily soak-monitoring is passive (~5 min/day).

## Daily Notes

### 2026-05-04 (Mon) — Sprint 004 kickoff

- **Carry-forward from Sprint 003 retro Q4:** Sprint Goal opens with a 2-line block (Goal A + Goal B) acknowledging parallel workstreams. Single-anchor framing pushed parallel-track work into "scope creep" two sprints running; explicit Goal A / Goal B format makes the parallelism honest.
- **Item ID alignment:** F2 Admin Portal in-flight items mapped to canonical `E4-APRT-035` (QA pass) and `E4-APRT-039` (M10 sunset — already includes "offline backup of ADMIN_PASSWORD_HASH + secret deletion"). Admin password rotation folded into APRT-039 rather than a standalone item.
- **Auto-standup** at `scrum/standups/2026-05-04.md` generated 07:41+08:00 under `status: planning`; patched in place at sprint-status flip (frontmatter + Sprint Goal banner + Today-plan table to surface Goal B Admin Portal items).
- **Sprint board live view** added at `scrum/sprint-board.md` (Dataview kanban-style — auto-renders from `sprint-current.md` `status::` tags).

## Definition of Done — Sprint 004

- [ ] **E2-F1-010** closed: F1 DCF walkthrough complete in CSPro Designer (including case-control block), bug list closed or deferred with rationale, sign-off note appended to `log.md`. *(Three-sprint carry — must not leave Sprint 004.)*
- [ ] **E3-F1-001** closed: F1 FMF Designer pass complete; `FacilityHeadSurvey.fmf` saved and reviewed. *(Gated on E2-F1-010.)*
- [ ] **E0-010** closed: weekly status update format formalized as a stable deliverable (per `feedback_weekly_status_internal_only.md`).
- [ ] **E4-APRT-035** closed: cross-platform QA pass complete (Chrome + Safari + Firefox + iPhone + Android per QA template), or explicitly deferred with documented rationale; PR #54 ready for merge once findings dispositioned.
- [ ] **E4-APRT-039** opened: `ADMIN_PASSWORD_HASH` rotated on staging Worker; offline backup of new hash recorded in private secret store; staging smoke test green; 7-day soak window started with daily `wrangler tail --env staging` cadence + halt-criteria (5xx >0.5% sustained 1h) recorded; v2.0.0 ship (E4-APRT-040) target Sprint 005.
- [ ] **Sprint 004 retrospective** (4 questions) filled in `sprint-current.md` by EOD Fri 2026-05-08; sprint archived to `scrum/sprints/sprint-004.md`; `sprint-current.md` reset for Sprint 005.
