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

> **Close E2-F1-010 (F1 Designer sign-off) — two-sprint carry, must not leave this week.** Once F1 sign-off lands, open the FMF build in CSPro Designer for F1 (E3-F1-001 — generator skeleton is ready). E0-010 (define internal weekly status format) closes this sprint with no further deferral. Tranche 2 submission timing is ASPSI/PI lane, not a Sprint 003 deliverable for Carl.

## Committed Items

### Carry-forward from Sprint 002 (priority order)

- [ ] **E2-F1-010** F1 DCF opened in CSPro Designer, full validation walkthrough (including new case-control block: `SURVEY_CODE`, `INTERVIEWER_ID`, `DATE_STARTED`, `TIME_STARTED`, `AAPOR_DISPOSITION`, `FACILITY_NAME`, `FACILITY_ADDRESS`), bug list closed or explicitly deferred, sign-off note recorded `status::todo` `priority::critical` `estimate::4h`
- [ ] **E0-010** Define weekly status update format for ASPSI Management Committee (Carl → Juvy / Dr Claro / Dr Paunlagui) `status::todo` `priority::high` `estimate::2h`

### ASPSI / PI / PMO lane — informational only (NOT Data Programmer scope)

> Scope discipline: **E0-020** (SJREB status), **E0-032** (D2/D3/Tranche deadline tracking), **E0-032a** (DOH-PMSMD matrix coordination triage) are explicitly **not** Carl-owned per the signed CSA D1–D6 (Data Programmer scope = production of CAPI deliverables). They live in ASPSI ops / PI / PMO lane (Juvy / Dr Claro / Dr Paunlagui). Surface as project-level dependencies in `product-backlog.md` and the risk register, not as sprint-board commitments. CAPI-side fallout from the DOH matrix (specific F1/F2/F3/F4 revisions) is folded into the relevant E2/E3 instrument task — not tracked under E0-032a. (Memory: `feedback_data_programmer_scope.md`, `feedback_sjreb_out_of_scope.md`, `feedback_tranche_tracking_out_of_scope.md`, `feedback_e0_032a_out_of_scope.md`.)

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
| **Committed (must-finish)** | E2-F1-010, E0-010, E3-F1-001, E4-PWA-013 | ~12–13h |
| **Stretch** | E2-F3-010, E2-F4-010, E0-008 | ~7h |

> Capacity: ~25h solo-dev week. Hard commits are ~12–13h (including E4-PWA-013 Phase F decision Mon 2026-04-27) leaving room to pull stretch Designer validations (E2-F3-010 / E2-F4-010) into the week. Sprint board re-scoped 2026-05-01 (sprint close): E0-020 / E0-032 / E0-032a removed as out-of-Data-Programmer-scope; see "ASPSI / PI / PMO lane" section above.

## Daily Notes

### 2026-04-27 (Mon) — Sprint 003 kickoff

- **Carry-forward from Sprint 002 retro Q4:** Day 1 ritual — before writing the Today-plan table, grep deliverables/ for files modified since last standup to catch artifact drift. Prevents standup generator from narrating "pending" on already-done work. (Two occurrences Sprint 001 + Sprint 002.)
- **Tranche 2 status (informational only):** Extension in effect; official revised deadline pending from DOH as of 2026-04-25. Tracking + submission timing is ASPSI/PI lane (not Carl's). Surfaced here so Carl has awareness of where his deliverables sit vs. contracted milestones.

### 2026-05-01 (Fri) — Sprint 003 close, scope-discipline cleanup

- Out-of-scope items removed from sprint board: **E0-020** (SJREB tracking), **E0-032** (Tranche/deadline tracking), **E0-032a** (DOH-PMSMD matrix triage). All three are ASPSI/PI/PMO lane per CSA D1–D6 Data Programmer scope. They had leaked back into Sprint 003 despite the umbrella memory rule (`feedback_data_programmer_scope.md`); audit-on-detection discipline added to the SJREB + Tranche memories so this doesn't slip again.
- Net Sprint 003 commit drops from 6 → 4 (E2-F1-010, E0-010, E3-F1-001, E4-PWA-013) + 3 stretch (E2-F3-010, E2-F4-010, E0-008). Honest sprint board: 0/4 committed done at sprint close — F1 Designer sign-off carries to Sprint 004 as a three-sprint carry.

## Definition of Done — Sprint 003

- [ ] **E2-F1-010** closed: F1 DCF walkthrough complete in CSPro Designer (including case-control block), bug list closed or deferred with rationale, sign-off note appended to `log.md`.
- [ ] **E3-F1-001** closed: F1 FMF Designer pass complete; `FacilityHeadSurvey.fmf` saved and reviewed.
- [ ] **E0-010** closed: weekly status update format defined for Carl's internal tracking (per `feedback_weekly_status_internal_only.md`).
- [ ] **E4-PWA-013** closed: F2 PWA Phase F cutover decision recorded in `log.md` — either Worker JWT proxy promoted to production, OR deferral with reason + re-gate criteria documented.
- [ ] **Sprint 003 retrospective** (4 questions) filled in `sprint-current.md` by EOD Fri 2026-05-01; sprint archived to `scrum/sprints/sprint-003.md`; `sprint-current.md` reset for Sprint 004.
