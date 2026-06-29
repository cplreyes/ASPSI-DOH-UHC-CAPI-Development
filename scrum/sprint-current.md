---
sprint: 012
start: 2026-06-29
end: 2026-07-03
status: active
sprint_length: 1 week (5 working days)
deliverable_anchor: CAPI field-readiness to a CHECKABLE exit · Day-1 build-or-kill on the perennial carries (E0-SCRUM-SYNC, PSA, Goal B) · support deliverables (codebook/ETL, training finalize, governance) while waiting on ASPSI's pretest date
created: 2026-06-28 — Mode D skeleton at the S011→S012 boundary
locked: 2026-06-29 (Mode A — Monday kickoff)
---

# Sprint 012 — Field-ready to a checkable exit + clear the carries

> [!info] Where S011 left the project
> Build phase essentially complete; project shifted to **field-readiness + waiting on ASPSI's pretest schedule**. The **Supervisor hub Phase-2** shipped end-to-end (login→menu→Bluetooth→CSWeb relay→live reports→offline map), **device-verified on two tablets**, training guide **live**. UAT Round 5 was **closed 2026-06-29** (78/79 issues resolved, 1 cosmetic deferred — `deliverables/CSPro/CAPI-UAT-Round-5-Closeout-2026-06-29.md`); the burndown ran via the `capi-uat-triage` loop. Scope clarified: **SJREB + tablets + pretest scheduling are ASPSI/DOH's, not Carl's** — Carl's lane ends at field-ready. Full record: `scrum/sprints/sprint-011.md` + `log.md` + git (`f2aa9f3`, push pending).

## Carry-in from Sprint 011

| ID | Item | State | S012 disposition |
|---|---|---|---|
| **E0-SCRUM-SYNC** | scrum-state sync + 08:30 drift canary | **committed 3× (S009/S010/S011), built 0×** | **Day-1 build-or-kill (Goal A).** Build it as the FIRST task, or formally kill it and accept manual close discipline — no 4th carry as a note. |
| **E0-UAT-REFRAME (finish)** | field-readiness exit criterion | named + reframed in PB; exit criterion **operationalized 2026-06-29** (R5 close-out note defines + applies it); loop stop-condition wiring still todo | **Committed (Goal A)** — define a checkable exit (e.g. N consecutive days, no new tester-blocking finding) and wire it into the triage loop's stop condition. |
| **E6-CAPI-FIELDREADY** | UAT R5 burndown + `capi-multiselect` fan-out | standing workstream; **R5 closed 2026-06-29** | **R5 closed** (exit criterion met: 0 open R5 issues). FIELDREADY continues as standing for desk-test reopens + multi-select fan-out (device-test each). |
| **E2-F3-PHILHEALTH / E2-F4-PHILHEALTH** | Q38.1/Q38.2 + Q45.1/Q45.2 reinstatement | ✅ **DONE — built + deployed during UAT R5** (#764 F3 Q38.1/Q38.2; #794 F4 Q45.1; #795 F4 Q45.2; CSWeb 2026-06-25/27). ASPSI supplied the value sets via the tickets; the "blocked on Kidd's PNGs" framing was STALE. | **Closed** — not a carry. Open follow-ups (optional, ASPSI confirm): F3 Q38.2 is tick-all vs F4 Q45.2 single; "I don't know" deployed as −98 (locked std) not the paper's −55. |
| **E0-PSA-001b** | PSA gate outcome confirm | **unrecorded (4th carry)** | **Day-1 close-or-kill (Goal A)** — confirm with ASPSI or close as overtaken; no 5th carry. |
| **Goal B (#294 + #336)** | #294 retests + #336 disposition | untouched (4th carry) | **Day-1 close-or-kill** — kill with rationale if not done by EOD Monday. |
| **Supervisor hub go-live** | Phase-2 built + device-verified | needs field-SOP wiring + `supervisor-qa` roster (ASPSI) | Wire into the field SOP; provision `supervisor-qa` when ASPSI sends names. Deferred items (N1/N2/N4, C2 2nd-device, C7 map) stay parked. |
| **Support deliverables** | codebook/ETL ripple · training finalize · governance | buildable now, no external unblock | **Committed (Goal A)** — advance the D4/D6-feeding items while waiting on the pretest date. |
| **E4-F2-ELESTIO** | F2 off Cloudflare → Elestio | planned (19-task); blocked on provisioning | Parked — build Tasks 2–17 locally vs Docker MySQL if slack appears. |
| **Translations Batch 2** | Tagalog-final / Ilocano / Hiligaynon-F3F4 | blocked on ASPSI check | Drop-in when delivered (pipeline proven). |

## Committed Items (locked 2026-06-29 — Mode A)

### Goal A — clear the carries + field-ready to a checkable exit

- [ ] **E0-SCRUM-SYNC** — FIRST task: build the drift canary + close-of-sprint sync, OR kill it formally. No 4th carry-as-note. `status::todo` `priority::high` `estimate::2h`
- [ ] **E0-PSA-001b** — Day-1 confirm-or-close with ASPSI. No 5th carry. `status::todo` `priority::high` `estimate::1h`
- [ ] **Goal B #294/#336** — Day-1 close-or-kill (kill with rationale if not done Monday). `status::todo` `priority::medium` `estimate::1h`
- [~] **E0-UAT-REFRAME (finish)** — exit criterion **operationalized 2026-06-29** via the R5 close-out note (defines + applies it; R5 declared closed). Remaining: wire the stop-condition into the triage loop. `status::in-progress` `priority::high` `estimate::0.5h`
- [x] **E6-CAPI-FIELDREADY** — **UAT R5 closed 2026-06-29** (exit criterion met; see close-out note). Standing FIELDREADY continues for desk-test reopens + multi-select fan-out (device-test each). `status::done (R5) · standing` `priority::critical`
- [ ] **Support deliverables** — harmonization codebook/ETL ripple, training finalize (decks + Survey Manual screenshots), governance (privacy/backup/retention). **CAPI Manual (D5/Epic 7) banked COMPLETE ~98% at lock (2026-06-29)** — 24 on-device screenshots + filled code-list annexes + purple 93pp PDF; only ASPSI's §H support-contact names remain. `status::in-progress` `priority::high` `estimate::1d`
- [x] **E2-F3/F4-PHILHEALTH** — ✅ DONE: built + deployed in UAT R5 (#764 F3 Q38.1/Q38.2 tick-all; #794 F4 Q45.1; #795 F4 Q45.2 single; CSWeb 2026-06-25/27). Confirmed in live DCFs. Not pending — the "download the 3 PNGs" item was a stale-record false alarm (2026-06-29). `status::done`

### Goal B — opportunistic

- [~] **Supervisor hub → UAT Round 6.** ✅ 2026-06-29: 8-account/2-team tester roster (fs-01/fs-02 + se-001..se-006) built in `build_hub_apps.py`, **redeployed to prod CSWeb + device-verified on the itel** (new se-001 enumerator + fs-02 supervisor menus render); credentials in `supervisor-hub/config/` (`uat-r6-csweb-users.csv` + `UAT-R6-tester-credentials.md`, DO-NOT-COMMIT). **Remaining:** ASPSI imports the CSWeb accounts + supplies real tester names + holds `supervisor-qa`; then open the R6 round artifacts (tracking issue/form/channel). `status::in-progress` `priority::medium`

## Definition of Done — Sprint 012

_Finalized at lock 2026-06-29._

- [ ] **E0-SCRUM-SYNC built + proven, OR formally killed** — no longer carried as an open note either way.
- [ ] PSA gate outcome recorded or closed-as-overtaken; Goal B closed or killed. No further carry of either.
- [ ] Field-readiness exit criterion defined + wired into the triage loop's stop condition.
- [x] UAT R5 **closed 2026-06-29** (exit criterion met; see `deliverables/CSPro/CAPI-UAT-Round-5-Closeout-2026-06-29.md`).
- [x] Support deliverables advanced (codebook/ETL, training, governance) — at least one moved to "ready for D5/D6". ✅ **CAPI Manual moved to ready-for-D5 at lock (2026-06-29)**; codebook/ETL + governance still in flight.
- [ ] PhilHealth live on F3+F4, or explicitly blocked-on-Carl (PNGs) documented.
- [ ] **Sprint 012 retrospective filled ON TIME Fri 2026-07-03**; archived; `sprint-current.md` reset for Sprint 013.

## Daily Notes

_Auto-standup writes here daily via the `CAPI Scrum Daily Standup MD` scheduled task (08:30 MNL) + the SessionStart hook as intraday top-up._

**Mon 2026-06-29 — Sprint 012 LOCKED (Mode A).** 8 items committed (7 Goal A + 1 Goal B); ~26h estimated; 1 blocked (E2-PHILHEALTH, waiting on Carl's 3 value-set PNGs), 1 critical-path (E6-CAPI-FIELDREADY). **Day-1 order:** (1) E0-SCRUM-SYNC build-or-kill — FIRST task; (2) E0-PSA-001b + Goal B #294/#336 close-or-kill by EOD. **Banked at lock:** CAPI Manual (D5/Epic 7) complete ~98% — DoD "support deliverable ready-for-D5" already met.

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
