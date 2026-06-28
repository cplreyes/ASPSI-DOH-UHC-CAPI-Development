---
sprint: 012
start: 2026-06-29
end: 2026-07-03
status: planning
sprint_length: 1 week (5 working days)
deliverable_anchor: CAPI field-readiness to a CHECKABLE exit · Day-1 build-or-kill on the perennial carries (E0-SCRUM-SYNC, PSA, Goal B) · support deliverables (codebook/ETL, training finalize, governance) while waiting on ASPSI's pretest date
created: 2026-06-28 — Mode D skeleton at the S011→S012 boundary
locked: pending — Mode A lock at Monday 2026-06-29 kickoff
---

# Sprint 012 — Field-ready to a checkable exit + clear the carries — SKELETON, lock Monday

> [!info] Where S011 left the project
> Build phase essentially complete; project shifted to **field-readiness + waiting on ASPSI's pretest schedule**. The **Supervisor hub Phase-2** shipped end-to-end (login→menu→Bluetooth→CSWeb relay→live reports→offline map), **device-verified on two tablets**, training guide **live**. UAT Round 5 burndown ran via the `capi-uat-triage` loop. Scope clarified: **SJREB + tablets + pretest scheduling are ASPSI/DOH's, not Carl's** — Carl's lane ends at field-ready. Full record: `scrum/sprints/sprint-011.md` + `log.md` + git (`f2aa9f3`, push pending).

## Carry-in from Sprint 011

| ID | Item | State | S012 disposition |
|---|---|---|---|
| **E0-SCRUM-SYNC** | scrum-state sync + 08:30 drift canary | **committed 3× (S009/S010/S011), built 0×** | **Day-1 build-or-kill (Goal A).** Build it as the FIRST task, or formally kill it and accept manual close discipline — no 4th carry as a note. |
| **E0-UAT-REFRAME (finish)** | field-readiness exit criterion | named + reframed in PB; exit criterion **not operationalized** | **Committed (Goal A)** — define a checkable exit (e.g. N consecutive days, no new tester-blocking finding) and wire it into the triage loop's stop condition. |
| **E6-CAPI-FIELDREADY** | UAT R5 burndown + `capi-multiselect` fan-out | standing workstream; R5 active | **Committed (Goal A)** — run to the exit criterion above. Device-test before each multi-select fan-out. |
| **E2-F3-PHILHEALTH / E2-F4-PHILHEALTH** | Q38.1/Q38.2 + Q45.1/Q45.2 reinstatement | **stems+routing captured 2026-06-28** (email ingested); **blocked on Carl**: download the 3 value-set PNGs from Kidd's 2026-06-09 email | **Committed-conditional** — specs updated; builds the moment the images land. |
| **E0-PSA-001b** | PSA gate outcome confirm | **unrecorded (4th carry)** | **Day-1 close-or-kill (Goal A)** — confirm with ASPSI or close as overtaken; no 5th carry. |
| **Goal B (#294 + #336)** | #294 retests + #336 disposition | untouched (4th carry) | **Day-1 close-or-kill** — kill with rationale if not done by EOD Monday. |
| **Supervisor hub go-live** | Phase-2 built + device-verified | needs field-SOP wiring + `supervisor-qa` roster (ASPSI) | Wire into the field SOP; provision `supervisor-qa` when ASPSI sends names. Deferred items (N1/N2/N4, C2 2nd-device, C7 map) stay parked. |
| **Support deliverables** | codebook/ETL ripple · training finalize · governance | buildable now, no external unblock | **Committed (Goal A)** — advance the D4/D6-feeding items while waiting on the pretest date. |
| **E4-F2-ELESTIO** | F2 off Cloudflare → Elestio | planned (19-task); blocked on provisioning | Parked — build Tasks 2–17 locally vs Docker MySQL if slack appears. |
| **Translations Batch 2** | Tagalog-final / Ilocano / Hiligaynon-F3F4 | blocked on ASPSI check | Drop-in when delivered (pipeline proven). |

## Candidate Committed Items (lock Monday — Mode A)

### Goal A (candidate) — clear the carries + field-ready to a checkable exit

- [ ] **E0-SCRUM-SYNC** — FIRST task: build the drift canary + close-of-sprint sync, OR kill it formally. No 4th carry-as-note. `status::todo` `priority::high` `estimate::2h`
- [ ] **E0-PSA-001b** — Day-1 confirm-or-close with ASPSI. No 5th carry. `status::todo` `priority::high` `estimate::1h`
- [ ] **Goal B #294/#336** — Day-1 close-or-kill (kill with rationale if not done Monday). `status::todo` `priority::medium` `estimate::1h`
- [ ] **E0-UAT-REFRAME (finish)** — operationalize the field-readiness exit criterion + wire it into the triage loop. `status::todo` `priority::high` `estimate::1h`
- [ ] **E6-CAPI-FIELDREADY** — UAT R5 burndown to the exit criterion; multi-select fan-out (device-test each). `status::todo` `priority::critical` `estimate::1d`
- [ ] **Support deliverables** — harmonization codebook/ETL ripple, training finalize (decks + Survey Manual screenshots), governance (privacy/backup/retention). `status::todo` `priority::high` `estimate::1d`
- [ ] **E2-F3/F4-PHILHEALTH** — build on PNG arrival (gates + deploy + patch notes + codebook). `status::blocked` (PNGs) `priority::critical` `estimate::3h`

### Goal B (candidate, opportunistic)

- [ ] **Supervisor hub field-SOP wiring** + provision `supervisor-qa` when ASPSI sends names. `status::todo` `priority::medium` `estimate::2h`

## Definition of Done — Sprint 012

_(to be finalized at Monday's lock)_

- [ ] **E0-SCRUM-SYNC built + proven, OR formally killed** — no longer carried as an open note either way.
- [ ] PSA gate outcome recorded or closed-as-overtaken; Goal B closed or killed. No further carry of either.
- [ ] Field-readiness exit criterion defined + wired into the triage loop's stop condition.
- [ ] UAT R5 at (or measurably converging on) the exit criterion.
- [ ] Support deliverables advanced (codebook/ETL, training, governance) — at least one moved to "ready for D5/D6".
- [ ] PhilHealth live on F3+F4, or explicitly blocked-on-Carl (PNGs) documented.
- [ ] **Sprint 012 retrospective filled ON TIME Fri 2026-07-03**; archived; `sprint-current.md` reset for Sprint 013.

## Daily Notes

_Auto-standup writes here daily via the `CAPI Scrum Daily Standup MD` scheduled task (08:30 MNL) + the SessionStart hook as intraday top-up._

## Retrospective — Sprint 012

> 5-minute time-box. Four questions, fixed order. Written, not thought-through-only.

### 1. Did the sprint goal land? (yes / partial / no — one line why)

_TBD 2026-07-03._

### 2. What surprised me? (process, not work — max 3 bullets)

_TBD_

### 3. Deadline exposure check — D2 / D3 / Tranche slip days this sprint

_Informational only (out of Data Programmer scope per CSA D1–D6)._

### 4. One thing to change in Sprint 013

_TBD_
