---
sprint: 001
start: 2026-04-13
end: 2026-04-17
status: active
sprint_length: 1 week (5 working days)
deliverable_anchor: D2 / D3 (extended timeline)
---

# Sprint 001 — Close F1 Design, Unblock F1 Build

## Sprint Goal

> **Get F1 out of Design and into Build-ready by Friday**: resolve the six open F1 questions at today's LSS meeting, reconcile DCF v2 against those decisions, complete the CSPro Designer walkthrough, and sign off Epic 2 for F1 so Epic 3 (F1 build) can start in Sprint 002.

Why this goal: F1 is the reference instrument for F2/F3/F4 — every day F1 sits in Design also delays the downstream pipeline. The six open questions have been frozen for ~3 days waiting on the Apr 13 LSS meeting. This sprint's value is converting that meeting into committed schema and exiting the design phase.

## Committed Items

<!-- IDs reference epic files in scrum/epics/. Keep statuses in sync there. -->

### Epic 0 — PM & Stakeholder (recurring + one-off)

- [ ] **E0-001** Sprint 001 planning ceremony — set goal, dates, commit items `status::in-progress` `priority::high`
- [ ] **E0-020** SJREB application status check via ASPSI (carry into every sprint until clearance) `status::in-progress` `priority::critical`
- [ ] **E0-032** Track D2/D3 deadline exposure this week `status::in-progress` `priority::high`
- [ ] **E0-060** Attend Apr 13 LSS meeting (3:00 PM); capture decisions on the 6 open F1 items into a meeting note in `scrum/standups/` and feed back to F1 spec `status::todo` `priority::critical` `estimate::3h`

### Epic 2 — F1 Design closeout

- [x] **E2-F1-009** Apply 6 DCF bug fixes to `generate_dcf.py` and regenerate v2 `status::done` `priority::critical`
  - Already completed 2026-04-11 (see log). Pulled into this sprint retroactively so the burndown reflects committed scope.
- [x] **E2-F1-009b** Reconcile DCF v2 with LSS-meeting decisions on the 6 open items (Q63 day vs month, SECONDARY_DATA structure, NBB split, Q31 NA-skip intent, Q166 nurse list, Q121 dynamic value set). `status::done` `priority::critical`
  - Closed 2026-04-13 by LSS meeting confirmation: no schema changes required, DCF v2 stands as final F1 dictionary. See `scrum/standups/2026-04-13.md` for the audit-trail entry.
- [ ] **E2-F1-010** F1 DCF v2 (final) opened in CSPro Designer, full validation walkthrough, bug list closed or explicitly deferred, sign-off note recorded → enters Epic 3 `status::todo` `priority::critical` `estimate::4h`
  - Unblocked 2026-04-13. Start: Tuesday Apr 14.

### Epic 3 — F1 Build kickoff (promoted from stretch 2026-04-13)

- [ ] **E3-F1-001** Create `FacilityHeadSurvey.fmf`; lay out Section A (Identification & Cover Page) only `status::todo` `priority::high` `estimate::4h`
  - Promoted from stretch to committed on 2026-04-13 after F1 design closed clean. Targets Wednesday/Thursday once E2-F1-010 sign-off is in.

### Epic 0 — Process scaffolding (stretch)

- [ ] **E0-010** Define weekly status update format for ASPSI Management Committee — one-page template, paste-ready `status::todo` `priority::high` `estimate::2h`
  - Stretch — useful regardless of sprint outcome; sets up E0-011 next sprint.

## Sprint Backlog Sizing

| Class | Items | Estimate |
|---|---|---|
| **Committed (must-finish)** | E0-001, E0-020, E0-032, E0-060, E2-F1-010, E3-F1-001 | ~10h discretionary + recurring |
| **Stretch** | E0-010 | +2h |
| **Already done** | E2-F1-009 (Apr 11), E2-F1-009b (Apr 13 — closed by LSS confirmation), E0-060 (Apr 13 PM) | — |

Solo-dev capacity check: 5 working days × ~5h focused work = ~25h. Day 1 closed two committed items (E0-060 + E2-F1-009b) ahead of plan; remaining committed work (E2-F1-010 Tue, E3-F1-001 Wed-Thu) is well under capacity for the rest of the sprint.

## Daily Notes

<!-- Mid-sprint observations that aren't standup material. Append below. -->

### 2026-04-13 (Mon)
- Sprint 001 kickoff. Pre-sprint context brief was filed Apr 10 standup.
- LSS meeting at 3:00 PM is the gating event for E2-F1-009b — until decisions land, E2-F1-009b cannot start.
- **LSS meeting concluded.** No schema changes required from any of the 6 open F1 items. DCF v2 stands as the final F1 dictionary. E2-F1-009b closed; E2-F1-010 unblocked for Tuesday; E3-F1-001 promoted from stretch to committed. Sprint 001 is now poised to overshoot its goal.

## Retrospective — Sprint 001 (fill in 2026-04-17)

> 5-minute time-box. Four questions, fixed order. Written, not thought-through-only.
> Don't write self-congratulation; only write what changes next week's behavior.

### 1. Did the sprint goal land? (yes / partial / no — one line why)

_(answer here)_

### 2. What surprised me? (process, not work — max 3 bullets)

-
-
-

### 3. Deadline exposure check — D2 / D3 slip days this week

> The 1%/day penalty (CSA §5) means deadline exposure is the metric, not velocity.
> Answer explicitly even when the answer is "0 days, held steady."

- **D2 exposure:** ___ days (Δ from last week: ___)
- **D3 exposure:** ___ days (Δ from last week: ___)

### 4. One thing to change in Sprint 002

> Exactly one. Not a wishlist. Smallest concrete behavior change.
> If nothing needs changing, write "none — keep the same shape."
> Carry this into Sprint 002's Daily Notes as the first entry so it stays visible.

-

## Definition of Done — Sprint 001

- [ ] All six F1 LSS-meeting questions have a recorded decision (in code comment, log entry, or wiki)
- [ ] DCF v3 (or confirmed v2) opens cleanly in CSPro Designer with no unresolved bug-list items
- [ ] F1 sign-off note appended to `log.md` declaring Epic 2/F1 closed and Epic 3/F1 ready to start
- [ ] Sprint 002 planning happens Friday Apr 17 PM or Monday Apr 20 AM
