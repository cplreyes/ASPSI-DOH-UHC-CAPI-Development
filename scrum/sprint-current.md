---
sprint: 007
start: 2026-05-25
end: 2026-05-29
status: planning
sprint_length: 1 week (5 working days)
deliverable_anchor: TBD — set at Mode A planning, Mon 2026-05-25
revised: 2026-05-22 — skeleton created at Sprint 006 close (Mode D); awaiting Mode A planning
---

# Sprint 007 — (planning)

> [!note] Planning skeleton
> This file was reset from Sprint 006 at its Mode D close on 2026-05-22. It is a **carry-in + constraints skeleton only** — the Sprint Goal, committed items, sizing, and DoD are filled by `/scrum` **Mode A** on Monday 2026-05-25. Do not treat anything below as committed yet.

> [!warning] `scrum/sprint-007-plan.md` is stale — do not promote it
> A `sprint-007-plan.md` draft exists (authored 2026-05-09, F1-validation-anchored). It **predates the 2026-05-18 ASPSI team-meeting re-plan** and contradicts current reality (it says "CSWeb stand-up waits until F1 build artifact stable" — CSWeb was committed to S006 by the meeting). Mode A should supersede it, not carry it forward.

## Carry-in from Sprint 006

Five items carry from S006 (2/8 committed items closed there — E0-008, E0-009b):

| ID | Item | S006 state | Notes for Mode A |
|---|---|---|---|
| **E3-F1-001** | F1 FMF Section A layout — CSPro Designer pass | todo (never started) | Goal A carry. Gated only on Carl's Designer time. |
| **E3-F3-001** | F3 FMF Designer pass — Patient (18 rec / 840 items) | todo (never started) | Goal A carry. |
| **E3-F4-001** | F4 FMF Designer pass — Household (22 rec / 623 items) | todo (never started) | Goal A carry; heaviest of the three. |
| **E4-CSWeb-001** | Provision VPS — host/OS/network/TLS | runbook authored | Execution-ready. Runbook: `deliverables/CSWeb/CSWeb-on-VPS-Setup-Runbook.md`. **Blocked on:** Carl provisioning a VPS + a domain name (Let's Encrypt won't issue to bare IPs). |
| **E4-CSWeb-002** | CSWeb install + admin account | runbook authored | Execution-ready; same runbook (Part 4). Follows E4-CSWeb-001. |
| **E6-PWA-007** | [#271](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/271) — R3 close-out | partial | 3 R3 bugs shipped to prod (#328/#315/#327), 6 issues closed, #294 cluster root-caused. Remaining: formally close #271, reconcile `from-uat-round-3-2026-05`. Re-verify is tester-paced. |

## Hard external constraint entering Sprint 007

- **PSA clearance gate — 2026-06-12.** PSA will not clear the survey without the CAPI app + **7 distinct translated versions** bundled (Bisaya ≠ Cebuano). QC-finalization (not first-draft) is the binding predecessor. Per the 2026-05-18 team meeting the full 7-language build is **S007 work** — this is the **S007 critical path**. (Ref: `wiki/concepts/CAPI Seven-Language Translation Build.md`, memory `project_capi_translation_psa_deadline`.)

## Also designated S007 (from the 2026-05-18 meeting / S006 deferrals)

- **E4-CSWeb-003 / -005** — per-survey F1/F3/F4 upload + field-tablet sync config (follow E4-CSWeb-001/002).
- **E3-F1-088** — F1 Phase-1 tablet sync-verify; blocked behind E4-CSWeb-005.

## Sprint Goal

_TBD — Mode A, Mon 2026-05-25._

## Committed Items

_TBD — Mode A. Note the Q4 retro prescription from S006: plan to capacity (~25h), not over it._

## Definition of Done — Sprint 007

_TBD — Mode A._

## Daily Notes

_(populated from Day 1)_

## Retrospective — Sprint 007

> 5-minute time-box. Four questions, fixed order. Written, not thought-through-only.

### 1. Did the sprint goal land? (yes / partial / no — one line why)

_TBD_

### 2. What surprised me? (process, not work — max 3 bullets)

_TBD_

### 3. Deadline exposure check — D2 / D3 / Tranche slip days this sprint

_Informational only (out of Data Programmer scope per CSA D1–D6)._

### 4. One thing to change in Sprint 008

_TBD_
