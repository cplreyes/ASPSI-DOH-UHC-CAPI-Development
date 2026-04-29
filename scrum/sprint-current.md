---
sprint: 003
start: 2026-04-27
end: 2026-05-01
status: active
sprint_length: 1 week (5 working days)
deliverable_anchor: E2-F1-010 / Tranche 2 (deadline TBC from DOH)
---

# Sprint 003 — Close F1 sign-off, open FMF build, submit Tranche 2 on confirmation

## Sprint Goal

> **Close E2-F1-010 (F1 Designer sign-off) — two-sprint carry, must not leave this week.** Once F1 sign-off lands, open the FMF build in CSPro Designer for F1 (E3-F1-001 — generator skeleton is ready). Submit Tranche 2 the moment DOH issues the official revised deadline. E0-010 (weekly status format for ASPSI Mgmt Committee) closes this sprint with no further deferral.

## Committed Items

### Carry-forward from Sprint 002 (priority order)

- [ ] **E2-F1-010** F1 DCF opened in CSPro Designer, full validation walkthrough (including new case-control block: `SURVEY_CODE`, `INTERVIEWER_ID`, `DATE_STARTED`, `TIME_STARTED`, `AAPOR_DISPOSITION`, `FACILITY_NAME`, `FACILITY_ADDRESS`), bug list closed or explicitly deferred, sign-off note recorded `status::todo` `priority::critical` `estimate::4h`
- [ ] **E0-010** Define weekly status update format for ASPSI Management Committee (Carl → Juvy / Dr Claro / Dr Paunlagui) `status::todo` `priority::high` `estimate::2h`
- [ ] **E0-032a** DOH-PMSMD matrix feedback triage — route any requested revisions into F1/F2 build state or explicitly defer with rationale `status::todo` `priority::critical` `estimate::TBD`

### Recurring (every sprint)

- [ ] **E0-020** SJREB application status check via ASPSI `status::todo` `priority::critical`
- [ ] **E0-032** Track D2/D3/Tranche 2 deadline exposure this week — confirm official revised deadline from DOH; submit package immediately on confirmation `status::todo` `priority::high`

### New for Sprint 003

- [ ] **E3-F1-001** F1 FMF Section A layout in CSPro Designer — generator skeleton (`FacilityHeadSurvey.generated.fmf`) is ready; Designer opens the file, applies form-layout-plan splits (per-subsection forms, no scrolling, roster-scrolls-alone), visual polish. Output: Designer-reviewed FMF saved as `FacilityHeadSurvey.fmf`. `status::todo` `priority::high` `estimate::4h`
- [ ] **E4-PWA-013** F2 PWA auth re-arch Phase F production cutover decision — by ~17:35 PHT today, assess Issue #33 (Section F/G multi-select state pollution) + #34 (CF Pages auto-deploy broken on both branches) status; if both resolved AND ≥24h clean staging soak holds, execute production cutover of Worker JWT proxy to `f2-pwa.pages.dev` per `docs/superpowers/runbooks/2026-04-26-f2-auth-cutover.md`; if either still open, document deferral with reason and re-gate criteria in `log.md`. `status::todo` `priority::critical` `estimate::2h decide + 1h cut OR 0h defer`

### Stretch (not committed)

- [ ] **E2-F3-010** F3 DCF Designer validation pass — verify case-control block in FIELD_CONTROL, full item walkthrough; sign-off note recorded `status::todo` `priority::medium` `estimate::3h`
- [ ] **E2-F4-010** F4 DCF Designer validation pass — same scope as F3 `status::todo` `priority::medium` `estimate::3h`
- [ ] **E0-008** Auto-standup retro-injection — extend `.claude/scripts/generate_standup.py` to read the prior sprint's `## Retrospective` Q4 ("One thing to change in Sprint N+1") and surface it as a Day 1 banner in the next sprint's first standup. Closes the ritual gap (Sprint 001→002 and Sprint 002→003 both had retro Q4 captured in `sprint-current.md` Daily Notes but not surfaced in the Day 1 daily standup). `status::todo` `priority::medium` `estimate::1h`

## Sprint Backlog Sizing

| Class | Items | Estimate |
|---|---|---|
| **Committed (must-finish)** | E2-F1-010, E0-010, E0-032a, E0-020, E0-032, E3-F1-001, E4-PWA-013 | ~14–15h + E0-032a unbounded |
| **Stretch** | E2-F3-010, E2-F4-010, E0-008 | ~7h |

> Capacity: ~25h solo-dev week. Hard commits are ~14–15h (including E4-PWA-013 Phase F decision today) leaving room for E0-032a if it arrives heavy, or pulling stretch Designer validations (E2-F3-010 / E2-F4-010) into the week.

## Daily Notes

### 2026-04-27 (Mon) — Sprint 003 kickoff

- **Carry-forward from Sprint 002 retro Q4:** Day 1 ritual — before writing the Today-plan table, grep deliverables/ for files modified since last standup to catch artifact drift. Prevents standup generator from narrating "pending" on already-done work. (Two occurrences Sprint 001 + Sprint 002.)
- **Tranche 2 status:** Extension in effect; official revised deadline not yet received from DOH as of 2026-04-25. Monitor and submit immediately on confirmation.

## Definition of Done — Sprint 003

- [ ] **E2-F1-010** closed: F1 DCF walkthrough complete in CSPro Designer (including case-control block), bug list closed or deferred with rationale, sign-off note appended to `log.md`.
- [ ] **E3-F1-001** closed: F1 FMF Designer pass complete; `FacilityHeadSurvey.fmf` saved and reviewed.
- [ ] **E0-010** closed: weekly status update format defined and first draft sent to ASPSI Mgmt Committee.
- [ ] **E0-032a** closed or explicitly deferred: DOH-PMSMD matrix feedback dispositioned.
- [ ] **E4-PWA-013** closed: F2 PWA Phase F cutover decision recorded in `log.md` — either Worker JWT proxy promoted to production, OR deferral with reason + re-gate criteria documented.
- [ ] **Tranche 2** submitted if official revised deadline is issued this week.
- [ ] **Sprint 003 retrospective** (4 questions) filled in `sprint-current.md` by EOD Fri 2026-05-01; sprint archived to `scrum/sprints/sprint-003.md`; `sprint-current.md` reset for Sprint 004.
