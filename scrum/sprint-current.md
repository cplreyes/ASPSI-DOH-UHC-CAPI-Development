---
sprint: 011
start: 2026-06-22
end: 2026-06-26
status: planning
sprint_length: 1 week (5 working days)
deliverable_anchor: CAPI field-readiness workstream (thin slice + emergent bucket + real exit criterion) · BUILD E0-SCRUM-SYNC · PhilHealth reinstatement (if PNGs land) · PSA confirm-or-close
created: 2026-06-21 — Mode D skeleton at the S010→S011 boundary
locked: (pending — Mode A lock Mon 2026-06-22)
---

# Sprint 011 — CAPI field-readiness (reframed) + scrum-sync BUILD — SKELETON, lock Monday

> [!info] Where S010 left the project
> R4 patching ran as a continuous stream **past** the sprint boundary (F3/F4 multi-select→roster conversions, F4 Section-C rebuild, then **Cluster-5 break-off + disposition #515/#561**, device-confirmed). Net-new this period: the `capi-multiselect` skill, the Option-B roster pilot, an entire new sub-project — the **Supervisor App** (Phase-1 built + tested; Phase-2 spec/plan, deferred per D7) — and the **CSWeb sync dashboard** (live). Full record: `scrum/sprints/sprint-010.md` + `log.md` 2026-06-20/21 + git `main`.

## Carry-in from Sprint 010

| ID | Item | State | S011 disposition |
|---|---|---|---|
| **E0-SCRUM-SYNC** | Mid/close-of-sprint scrum-state sync + 08:30 drift canary | committed in the S009 retro, **never built** — recurred in S010 (retro Q2) | **BUILD it this sprint** (the retro's #1 change). A tooling task, not a note: extend the 08:30 generator to flag `log.md` newer than `sprint-current.md` by >2 days; sync state mid-week + at close. |
| **R4 field-readiness** | UAT R4 triage stream | ran past S010 as a continuous stream with no closing condition | **Reframe** as a standing workstream: thin committed slice + explicit emergent bucket + a real exit criterion (e.g. N consecutive days with no new tester-blocking finding) instead of "close R4". |
| **capi-multiselect fan-out** | remaining select-alls / cost matrices (Shape A F1 #567; Shape B F3 #672/#674/#675/#688/#689/#691/#692/#693) | recipe encoded; Q92 Option-B pilot device-confirmed | Fan out via the skill; device-test before each fan-out. |
| **E2-F3-PHILHEALTH / E2-F4-PHILHEALTH** | Q38.1/Q38.2 + Q45.1/Q45.2 reinstatement | **blocked on Carl**: save the 3 value-set PNGs from Kidd's 6/9 email | Build rides the patch loop once unblocked. |
| **E0-PSA-001b** | PSA gate outcome confirm | unrecorded (**3rd carry**) | Confirm with Kidd/Myra; assemble-or-close. Don't let it slide a 4th sprint. |
| **Supervisor App go-live prep** | Phase-1 built; needs the QA-supervisor roster | blocked on ASPSI (names for the `supervisor-qa` role) | Named in the plan (per retro Q4); provision `supervisor-qa` when names land. Phase-2 deferred (D7). |
| **Goal B (clasp/#294 + #336)** | #294 retests + #336 disposition | 3rd-sprint carry, untouched | **Close-or-kill** this sprint. |
| **Harmonization codebook ripple** | Q148 + roster + disposition data-shape changes | ETL skeleton live | Update codebook + breakout ETL before real data flows. |
| **Translations Batch 2** | Tagalog-final / Ilocano / Hiligaynon-F3F4 | blocked on ASPSI check | Drop-in when delivered (pipeline proven). |

## Process changes committed from the S010 retro

- [ ] **E0-SCRUM-SYNC** Build the scrum-state sync, don't re-commit the note: extend the 08:30 generator to emit a drift canary when `log.md` is newer than `sprint-current.md` by >2 days, and sync sprint-state mid-week + at close. The test = the S011 retro is filled ON TIME Fri 6/26. `status::todo` `priority::high` `estimate::2h`
- [ ] **E0-UAT-REFRAME** Re-frame "R4 closeout" in the Product Backlog (Epic 6/8) as a standing **CAPI field-readiness** workstream — thin slice + emergent bucket + a defined exit criterion — and name the emergent sub-projects (Supervisor App, capi-multiselect) in the plan so they stop running as invisible capacity. `status::todo` `priority::high` `estimate::1h`

## Candidate Committed Items (lock Monday — Mode A)

### Goal A (candidate) — CAPI field-readiness + scrum-sync build

- [ ] **E0-SCRUM-SYNC** build the drift canary + sync cadence (above). `status::todo` `priority::high` `estimate::2h`
- [ ] **E6-CAPI-FIELDREADY** R4 emergent triage (the `capi-uat-triage` loop) + `capi-multiselect` fan-out, with the exit criterion defined. `status::todo` `priority::critical` `estimate::1d`
- [ ] **E2-F3-PHILHEALTH / E2-F4-PHILHEALTH** build Q38.1/Q38.2 + Q45.1/Q45.2 once the value-set PNGs land. `status::blocked` (PNGs) `priority::critical` `estimate::3h`
- [ ] **E0-PSA-001b** confirm the PSA gate outcome with ASPSI; assemble-or-close (no 4th carry). `status::todo` `priority::high` `estimate::1h`

### Goal B (candidate, opportunistic)

- [ ] **#294 verify-and-close + #336 disposition** — close-or-kill this 3rd-sprint carry. `status::todo` `priority::high` `estimate::2h`

## Definition of Done — Sprint 011

_(to be finalized at Monday's lock)_

- [ ] **E0-SCRUM-SYNC built + proven** — a drift canary actually fires, and sprint-state is synced at close with no 2-day lag.
- [ ] UAT reframed in the backlog with a real exit criterion; emergent work named.
- [ ] PhilHealth live on F3+F4, or explicitly blocked-on-ASPSI documented.
- [ ] PSA gate outcome recorded; bundle assembled or closed as overtaken (no 4th carry).
- [ ] Goal B closed or killed.
- [ ] **Sprint 011 retrospective filled ON TIME Fri 2026-06-26** (the real test of the E0-SCRUM-SYNC fix); archived; `sprint-current.md` reset for Sprint 012.

## Daily Notes

_Auto-standup writes here daily via the `CAPI Scrum Daily Standup MD` scheduled task (08:30 MNL) + the SessionStart hook as intraday top-up._

## Retrospective — Sprint 011

> 5-minute time-box. Four questions, fixed order. Written, not thought-through-only.

### 1. Did the sprint goal land? (yes / partial / no — one line why)

_TBD 2026-06-26._

### 2. What surprised me? (process, not work — max 3 bullets)

_TBD_

### 3. Deadline exposure check — D2 / D3 / Tranche slip days this sprint

_Informational only (out of Data Programmer scope per CSA D1–D6)._

### 4. One thing to change in Sprint 012

_TBD_
