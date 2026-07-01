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
| **E0-SCRUM-SYNC** | scrum-state sync + 08:30 drift canary | ✅ **BUILT + PROVEN 2026-06-30** (after 3× committed / 0× built) | **Done.** Drift canary wired into `generate_standup.py` (callout + `--check-drift` CLI + `sprint-drift` log line) and the 08:30 `daily-standup-md.ps1` wrapper (`PROBE-SPRINT-DRIFT`). Fires when `log.md` outpaces `sprint-current.md` by >2 days. No longer a carry. |
| **E0-UAT-REFRAME (finish)** | field-readiness exit criterion | ✅ **DONE 2026-06-30** — criterion operationalized (R5 close-out, 06-29) AND now **wired into the loop** | **Done.** `deliverables/CSPro/automation/check_field_ready.py` gates the `capi-uat-triage` loop: FIELD-READY (0 open actionable F1/F3/F4 + newest finding ≥ quiet-days old, ASPSI items carved out) → loop stops; persists a `field_ready` block in `triage-state.json`. Skill §7 updated to consult it every cycle. Verified FIELD-READY today. |
| **E6-CAPI-FIELDREADY** | UAT R5 burndown + `capi-multiselect` fan-out | standing workstream; **R5 closed 2026-06-29** | **R5 closed** (exit criterion met: 0 open R5 issues). FIELDREADY continues as standing for desk-test reopens + multi-select fan-out (device-test each). |
| **E2-F3-PHILHEALTH / E2-F4-PHILHEALTH** | Q38.1/Q38.2 + Q45.1/Q45.2 reinstatement | ✅ **DONE — built + deployed during UAT R5** (#764 F3 Q38.1/Q38.2; #794 F4 Q45.1; #795 F4 Q45.2; CSWeb 2026-06-25/27). ASPSI supplied the value sets via the tickets; the "blocked on Kidd's PNGs" framing was STALE. | **Closed** — not a carry. Open follow-ups (optional, ASPSI confirm): F3 Q38.2 is tick-all vs F4 Q45.2 single; "I don't know" deployed as −98 (locked std) not the paper's −55. |
| **E0-PSA-001b** | PSA gate outcome confirm | **CLOSED — out of lane 2026-06-30** | **Closed as overtaken.** PSA-SSRCS clearance is an ASPSI/DOH gate (mid-review per the 2026-06-29 PB; formal 20-day clock not yet started), not a Carl-tracked sprint task — removing it as a recurring carry. If Carl wants a status ping, that's his comm to ASPSI to send. |
| **Goal B (#294 + #336)** | #294 retests + #336 disposition | **KILLED 2026-06-30** | **Killed per the pre-agreed Monday rule** (not actioned Day-1). Both are F2-PWA-track residuals; F2 is production v2.1.0. Any real remnant of #294 (clasp deploy-gap) / #336 lives in the F2 backlog, not as a recurring carry in the CAPI sprint. |
| **Supervisor hub go-live** | Phase-2 built + device-verified | needs field-SOP wiring + `supervisor-qa` roster (ASPSI) | Wire into the field SOP; provision `supervisor-qa` when ASPSI sends names. Deferred items (N1/N2/N4, C2 2nd-device, C7 map) stay parked. |
| **Support deliverables** | codebook/ETL ripple · training finalize · governance | buildable now, no external unblock | **Committed (Goal A)** — advance the D4/D6-feeding items while waiting on the pretest date. |
| **E4-F2-ELESTIO** | F2 off Cloudflare → Elestio | planned (19-task); blocked on provisioning | Parked — build Tasks 2–17 locally vs Docker MySQL if slack appears. |
| **Translations Batch 2** | Tagalog-final / Ilocano / Hiligaynon-F3F4 | blocked on ASPSI check | Drop-in when delivered (pipeline proven). |

## Committed Items (locked 2026-06-29 — Mode A)

### Goal A — clear the carries + field-ready to a checkable exit

- [x] **E0-SCRUM-SYNC** — ✅ **BUILT + proven 2026-06-30.** Drift canary in `generate_standup.py` (standup callout + `--check-drift`/`--drift-days` CLI + `sprint-drift` log line) and the 08:30 `daily-standup-md.ps1` wrapper (`PROBE-SPRINT-DRIFT`); fires when `log.md` is >2d newer than `sprint-current.md`. Tested: silent at 0.4d today, fires at `--drift-days 0`. The 3× note is now code. `status::done` `priority::high` `estimate::2h`
- [x] **E0-PSA-001b** — **Closed as overtaken / out of lane 2026-06-30.** PSA-SSRCS is an ASPSI/DOH gate (mid-review), not a Carl sprint carry. No 5th carry. `status::done (closed)` `priority::high` `estimate::1h`
- [x] **Goal B #294/#336** — **Killed 2026-06-30** per the pre-agreed Monday rule (not actioned Day-1); F2-track residuals belong in the F2 backlog. `status::done (killed)` `priority::medium` `estimate::1h`
- [x] **E0-UAT-REFRAME (finish)** — ✅ **DONE 2026-06-30.** Criterion operationalized (R5 close-out 06-29) + now **wired**: `automation/check_field_ready.py` is the loop's stop-condition gate (FIELD-READY/CLEAR-PENDING/NOT-READY/UNKNOWN → exit 0/10/20/30; persists `field_ready` to `triage-state.json`); `capi-uat-triage` skill §7 runs it every cycle and stops on FIELD-READY. Verified FIELD-READY today (0 open, last finding 3.8d ago). `status::done` `priority::high` `estimate::0.5h`
- [x] **E6-CAPI-FIELDREADY** — **UAT R5 closed 2026-06-29** (exit criterion met; see close-out note). Standing FIELDREADY continues for desk-test reopens + multi-select fan-out (device-test each). `status::done (R5) · standing` `priority::critical`
- [ ] **Support deliverables** — harmonization codebook/ETL ripple, training finalize (decks + Survey Manual screenshots), governance (privacy/backup/retention). **CAPI Manual (D5/Epic 7) banked COMPLETE ~98% at lock (2026-06-29)** — 24 on-device screenshots + filled code-list annexes + purple 93pp PDF; only ASPSI's §H support-contact names remain. `status::in-progress` `priority::high` `estimate::1d`
- [x] **E2-F3/F4-PHILHEALTH** — ✅ DONE: built + deployed in UAT R5 (#764 F3 Q38.1/Q38.2 tick-all; #794 F4 Q45.1; #795 F4 Q45.2 single; CSWeb 2026-06-25/27). Confirmed in live DCFs. Not pending — the "download the 3 PNGs" item was a stale-record false alarm (2026-06-29). `status::done`

### Goal B — opportunistic

- [~] **Supervisor hub → UAT Round 6.** ✅ 2026-06-29: 8-account/2-team tester roster (fs-01/fs-02 + se-001..se-006) built in `build_hub_apps.py`, **redeployed to prod CSWeb + device-verified on the itel** (new se-001 enumerator + fs-02 supervisor menus render); credentials in `supervisor-hub/config/` (`uat-r6-csweb-users.csv` + `UAT-R6-tester-credentials.md`, DO-NOT-COMMIT). **Remaining:** ASPSI imports the CSWeb accounts + supplies real tester names + holds `supervisor-qa`; then open the R6 round artifacts (tracking issue/form/channel). `status::in-progress` `priority::medium`

## Definition of Done — Sprint 012

_Finalized at lock 2026-06-29._

- [x] **E0-SCRUM-SYNC built + proven** (2026-06-30) — no longer carried as an open note. The 3× retro action is now wired into the daily generator + scheduled wrapper.
- [x] PSA gate **closed-as-overtaken**; Goal B **killed**. No further carry of either.
- [x] Field-readiness exit criterion defined + **wired into the triage loop's stop condition** (2026-06-30 — `check_field_ready.py` gate + skill §7).
- [x] UAT R5 **closed 2026-06-29** (exit criterion met; see `deliverables/CSPro/CAPI-UAT-Round-5-Closeout-2026-06-29.md`).
- [x] Support deliverables advanced (codebook/ETL, training, governance) — at least one moved to "ready for D5/D6". ✅ **CAPI Manual moved to ready-for-D5 at lock (2026-06-29)**; codebook/ETL + governance still in flight.
- [ ] PhilHealth live on F3+F4, or explicitly blocked-on-Carl (PNGs) documented.
- [ ] **Sprint 012 retrospective filled ON TIME Fri 2026-07-03**; archived; `sprint-current.md` reset for Sprint 013.

## Daily Notes

_Auto-standup writes here daily via the `CAPI Scrum Daily Standup MD` scheduled task (08:30 MNL) + the SessionStart hook as intraday top-up._

**Mon 2026-06-29 — Sprint 012 LOCKED (Mode A).** 8 items committed (7 Goal A + 1 Goal B); ~26h estimated; 1 blocked (E2-PHILHEALTH, waiting on Carl's 3 value-set PNGs), 1 critical-path (E6-CAPI-FIELDREADY). **Day-1 order:** (1) E0-SCRUM-SYNC build-or-kill — FIRST task; (2) E0-PSA-001b + Goal B #294/#336 close-or-kill by EOD. **Banked at lock:** CAPI Manual (D5/Epic 7) complete ~98% — DoD "support deliverable ready-for-D5" already met.

**Tue 2026-06-30 — the three carries cleared.** **E0-SCRUM-SYNC BUILT + proven** (4th sprint, finally code not a note): drift canary added to `generate_standup.py` (standup callout + `--check-drift`/`--drift-days` CLI + `sprint-drift` log line) and to the 08:30 `daily-standup-md.ps1` wrapper (`PROBE-SPRINT-DRIFT`) — fires when `log.md` is >2 days newer than `sprint-current.md`; tested silent at today's 0.4d and firing at `--drift-days 0`. **E0-PSA-001b closed as overtaken** (ASPSI/DOH gate, not a Carl carry). **Goal B #294/#336 killed** per the pre-agreed Monday rule (F2-track residuals → F2 backlog). DoD's two hardest clauses now satisfied; Wed–Fri left for support deliverables (codebook/ETL, governance) while waiting on ASPSI's pretest date. _Side effect: syncing this board reset the drift clock, so the canary I just built won't false-fire — it earned its first clean day by being used._

**Tue 2026-06-30 (cont.) — E0-UAT-REFRAME finished + standup parser fixed.** **E0-UAT-REFRAME DONE:** the field-readiness exit criterion is now *wired*, not just operationalized — `deliverables/CSPro/automation/check_field_ready.py` is the `capi-uat-triage` loop's stop-condition gate (FIELD-READY/CLEAR-PENDING/NOT-READY/UNKNOWN ↔ exit 0/10/20/30; checks 0-open-actionable + quiet-window via live `gh`, carves out ASPSI-owned labels, persists a `field_ready` block to `triage-state.json`); skill §7 consults it every cycle and stands the loop down on FIELD-READY. Verified **FIELD-READY** today (0 open, last finding 3.8d ago). **Standup parser fix:** `generate_standup.py`'s `TASK_LINE` now captures the whole bold label, so committed items with spaces/`#`/`/` IDs (`Support deliverables`, `Goal B #294/#336`, `E2-F3/F4-PHILHEALTH`, `E0-UAT-REFRAME (finish)`, the hub item) are no longer silently dropped — the board went from a misleading 3/3 to a true **5 done / 3 in-progress / 8 total**. Both are accuracy fixes in the same spirit as the drift canary: the scrum/UAT state now reports itself honestly.

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
