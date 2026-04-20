---
sprint: 002
start: 2026-04-20
end: 2026-04-24
status: active
sprint_length: 1 week (5 working days)
deliverable_anchor: D2 / Tranche 2 (40% due 2026-04-24)
---

# Sprint 002 — Ship the Tranche 2 submission package

## Sprint Goal

> **Ship the Tranche 2 (40%) submission package by Fri 2026-04-24.** Triage DOH-PMSMD matrix feedback into F1/F2 build state, close F1 Designer sign-off (E2-F1-010) so F1 design is formally complete, and confirm Tranche 2 package contents with Juvy for Dr Claro's submission route. Late-delivery penalty is 1%/day after Apr 24 (CSA §5) — deadline exposure is the metric, not velocity.

## Committed Items

### Carry-forward from Sprint 001 (priority order)

- [ ] **E2-F1-010** F1 DCF opened in CSPro Designer, full validation walkthrough, bug list closed or explicitly deferred, sign-off note recorded `status::todo` `priority::critical` `estimate::4h`
- [ ] **E3-F1-001** Create `FacilityHeadSurvey.fmf`; lay out Section A (Identification & Cover Page) only `status::todo` `priority::high` `estimate::4h`
- [ ] **E0-010** Define weekly status update format for ASPSI Management Committee `status::todo` `priority::high` `estimate::2h`
  - Scope updated per Apr 13 meeting notes: format is for Carl → Juvy / Dr Claro / Dr Paunlagui, not Carl → DOH directly.

### Recurring (every sprint)

- [ ] **E0-020** SJREB application status check via ASPSI `status::in-progress` `priority::critical`
- [ ] **E0-032** Track D2/D3/Tranche 2 deadline exposure this week `status::in-progress` `priority::high`

### New for Sprint 002

- [ ] **E0-032a** Triage DOH-PMSMD feedback on matrices (arrives Apr 20 Mon); route any requested revisions into F1/F2 build state; confirm Tranche 2 submission package with Juvy by Apr 23 `status::todo` `priority::critical` `estimate::TBD`

### Stretch (not committed)

- [ ] **F2 PWA pilot-readiness decision** — per `deliverables/F2/PWA/app/NEXT.md`: pick one of pilot now / close-deferred M11 items / move to M12 F3-F4 parity. Decision itself is ~30m; follow-through TBD depending on path. `status::todo` `priority::medium` `estimate::30m decision`

## Sprint Backlog Sizing

| Class | Items | Estimate |
|---|---|---|
| **Committed (must-finish)** | E2-F1-010, E3-F1-001, E0-010, E0-020, E0-032, E0-032a | ~10h + E0-032a unbounded |
| **Stretch** | F2 PWA pilot-readiness decision | 30m decision + follow-through TBD |

> Capacity: ~25h solo-dev week. Hard-committed ~10h; E0-032a depends entirely on DOH-PMSMD feedback scope and can absorb the remaining ~15h if revisions are heavy. Stretch is a decision, not a build push — intentional, because Tranche 2 is the anchor.

## Daily Notes

<!-- Mid-sprint observations that aren't standup material. Mode B on Monday Apr 20 will seed this with the Sprint 001 retro Q4 carry-forward. -->

## Retrospective — Sprint 002 (fill in 2026-04-24)

> 5-minute time-box. Four questions, fixed order. Written, not thought-through-only.
> Don't write self-congratulation; only write what changes next week's behavior.

### 1. Did the sprint goal land? (yes / partial / no — one line why)

_TBD 2026-04-24_

### 2. What surprised me? (process, not work — max 3 bullets)

_TBD 2026-04-24_

### 3. Deadline exposure check — D2 / D3 / Tranche 2 slip days this week

> The 1%/day penalty (CSA §5) means deadline exposure is the metric, not velocity.
> Answer explicitly even when the answer is "0 days, held steady."

_TBD 2026-04-24_

### 4. One thing to change in Sprint 003

> Exactly one. Not a wishlist. Smallest concrete behavior change.
> If nothing needs changing, write "none — keep the same shape."
> Carry this into Sprint 003's Daily Notes as the first entry so it stays visible.

_TBD 2026-04-24_

## Definition of Done — Sprint 002

- [ ] **Tranche 2 (40%) submission package** confirmed with Juvy and submitted via DOH route by EOD Fri 2026-04-24; submission entry logged in `log.md`.
- [ ] **E2-F1-010** closed: F1 DCF walkthrough complete in CSPro Designer, bug list closed or deferred with rationale, sign-off note appended to `log.md`.
- [ ] **E0-032a** closed: DOH-PMSMD matrix feedback triaged; any requested revisions reflected in F1/F2 build state or explicitly deferred with rationale recorded.
- [ ] **Sprint 002 retrospective** (4 questions) filled in `sprint-current.md` by EOD Fri 2026-04-24; sprint archived to `scrum/sprints/sprint-002.md`; `sprint-current.md` reset for Sprint 003.
