---
sprint: 014
start: 2026-07-20
end: 2026-07-24
status: active
sprint_length: 1 week (5 working days)
deliverable_anchor: PRETEST WEEK — same-day field support · daily data-quality sweep of incoming cases · fleet on current builds · GPS-on-endlevel shipped-or-declined · debrief-ready record (feeds D4) · F2 serving migration + hub/R6 opportunistic only
created: 2026-07-20 — cut at the LATE S013 close (Day 15 of 5)
locked: 2026-07-20 (Mode A — Monday kickoff); RE-LOCKED 2026-07-20 (Carl — "focus this sprint to Pretesting this week")
---

# Sprint 014 — PRETEST WEEK (field support + data QA); F2/hub opportunistic

> [!info] Where S013 left the project
> **Closed LATE 2026-07-20 (Day 15 of 5) — goal PARTIAL, value high.** The pretest went live Wed 07-15 (Brgy. Mayondon, Los Baños) and reactive field support rightfully took the lane: #157 GPS → end-of-flow, #840 paradata `.pff` switch, the GPS warm-radio patch, and the F3 Q162 Field-Control fix all shipped from live tester reports, ending at **fleet F1 v1.1.4 · F3 v1.1.5 · F4 v1.4.4 (2026-07-19)** with the UAT gate at **CLEAR-PENDING** (0 open actionable; quiet window ages out ~07-21). F2's data-plane reached the prod server (07-08) but the serving migration stopped at a written plan-of-record; the hub stayed blocked-on-ASPSI. Full record: `scrum/sprints/sprint-013.md` + `log.md` (2026-07-19 entries ×4).

## Sprint Goal

> **Pretesting IS the sprint.** Support the live pretest end-to-end this week: same-day field support on every tester report, a **daily data-quality sweep** of incoming cases (catch the next Q162-class pattern in-flight, not after), the fleet confirmed on current builds, and the **GPS-on-endlevel decision shipped-or-declined** — so the pretest completes with clean, complete data and a **debrief-ready record feeding D4**. F2 serving migration and hub/R6 move **only with slack**. _Re-locked to Carl's direction the same day the sprint locked — the S013-retro rule working as intended._

## Carry-in from Sprint 013

| ID | Item | State | S014 disposition |
|---|---|---|---|
| **Pretest reactivity** | pretest LIVE since 07-15; triage loop + `check_field_ready.py` gate at **CLEAR-PENDING** (quiet window ~07-21); 6 affected F3 cases have posted recovery steps; fleet tablets beyond the itel still on v1.1.3/v1.4.3 until testers tap UPDATE | standing, hot | **Goal A — the sprint headline.** Same-day loop + daily data QA + fleet shepherding + recovered-case watch. |
| **GPS-on-endlevel design gap** | flagged 07-19, NOT shipped: postponed/refused/replaced outcomes `endlevel` before the end-of-flow GPS forms → those cases save with **no facility GPS** (map plotting + replacement tracking); proposed ~1–2 s warm read in the endlevel branch | Carl's call | **Goal A decision item** — pretest data-integrity; decide + ship-or-decline this week. |
| **E4-F2-PROD** (was E4-F2-ELESTIO) | data-plane DONE on prod (mirror + unified dashboard + 12-digit QN); serving migration = plan-of-record `deliverables/F2/F2-Prod-Migration-Plan.md` (8 gated phases; respondent path ~3 focused days; admin port may trail) | ready to execute | **Goal B (demoted at the re-lock)** — advance only with slack; no commitment this week. |
| **Supervisor App finalization + UAT R6** | hub Designer compile pending; LoginApp update pending server-side (07-15); R6 blocked on ASPSI accounts + real names + `supervisor-qa` | blocked-on-ASPSI | **Goal B** — reactive: finalize + open R6 the day ASPSI lands the accounts. |
| **F3 "Closing - case end" relabel** | 07-19 triage suggestion: the closing block's name hides that it IS the survey-team/Field-Control section — testers reported it "missing" partly on naming | small, freeze-adjacent (label-only) | **Goal B** — opportunistic; pretest-driven, so it may ride any deploy this week. |
| **ETL extraction (E10) + tabulation follow-ups** | deferred since 07-06; variable/data inconsistencies from the 197-table mapping feed it | backlog | Not S014 — revisit after the pretest (backlog). |
| **E3-RELEASE-001 · E8-SUPERVISOR-003** | release lane + hub rename, spec'd 07-15 | parked post-pretest | Not S014. |
| **Support deliverables (governance · training finalize)** | unchanged two sprints running | opportunistic | Goal B if slack appears. |
| **Translations Batch 2** | blocked on ASPSI delivery | drop-in when delivered | Reactive. |

## Committed Items — LOCKED 2026-07-20 (Mode A) · RE-LOCKED 2026-07-20 to PRETEST FOCUS (Carl)

### Goal A — the pretest week

- [ ] **Pretest field support (standing, FIRST priority)** — same-day triage/fix/deploy loop on tester reports (`capi-uat-triage` + `check_field_ready.py` gate each run, currently CLEAR-PENDING); shepherd the fleet onto v1.1.4/v1.1.5/v1.4.4 (UPDATE per patch notes — treat stale-build reports as suspect until the build is confirmed); watch the 6 recovered F3 cases land on sync. `status::in-progress` `priority::critical`
- [ ] **Pretest data-quality sweep (daily)** — every day, sweep the incoming cases (responses data room CSVs / dashboard) for blank-section, missing-field, and off-plan patterns — the Q162 blanking sat in the data for two days before anyone looked; this catches the next one in-flight. Log findings; anything real enters the triage loop same-day. `status::in-progress` `priority::high` `estimate::0.5h/day`
- [ ] **GPS-on-endlevel decision (Carl) — ship-or-decline this week** — postponed/refused/replaced cases currently save with NO facility GPS (`endlevel` fires before the end-of-flow GPS forms). If go: ~1–2 s warm read in the endlevel branch, shipped as a data-integrity exception (cheap on the warm radio); if no-go: rationale recorded here + backlog. Pretest replacements make this live NOW (BREAKOFF 5/6/7 = replacement flow). `status::todo` `priority::high` `estimate::0.5d`
- [ ] **Debrief-ready pretest record (feeds D4)** — keep a running per-day account of pretest issues found/fixed, affected cases + recovery status, and data-quality observations, so the enumerator debrief and the D4 pilot report can be assembled without archaeology. (GitHub #839 tracker + log.md are the sources; this item = keeping them current daily.) `status::in-progress` `priority::medium`

### Goal B — opportunistic (must not displace the pretest)

- [ ] **E4-F2-PROD — F2 serving migration, respondent path** — *demoted at the re-lock*: advance the plan-of-record phases (`deliverables/F2/F2-Prod-Migration-Plan.md`) only in slack hours; no completion commitment this week. `status::todo (slack only)` `priority::medium` `estimate::—`
- [ ] **Supervisor App finalization (+ UAT R6)** — hub Designer compile + deploy (LoginApp update pending server-side since 07-15); open R6 the day ASPSI imports the accounts + sends real names. `status::blocked-on-ASPSI` `priority::medium` `estimate::1d`
- [ ] **F3 "Closing - case end" relabel** — rename the closing block so testers recognize the survey-team/Field-Control section (label-only; from the 07-19 triage). Rides any F3 deploy this week. `status::todo` `priority::low` `estimate::0.5h`
- [ ] **Support deliverables** — governance + training finalize (Kidd review): only if the week gives slack. `status::todo` `priority::low`

## Definition of Done — Sprint 014

- [ ] **Every pretest tester report handled same-day** (root-caused + fixed/deployed, or explicitly triaged with a stated next step); triage gate consulted each run.
- [ ] **Data-quality sweep ran every fieldwork day** — findings logged even when clean ("swept, clean" counts; silence doesn't).
- [ ] **GPS-on-endlevel decision RECORDED** (shipped, or declined with rationale) — it does not silently carry a third sprint.
- [ ] **Debrief-ready record current at week's end** — a D4-feeding account of the pretest exists without archaeology.
- [ ] Fleet confirmed on v1.1.4/v1.1.5/v1.4.4 (or the holdout tablets named).
- [ ] R6 opened, or still-blocked-on-ASPSI re-documented with the date last checked. F2 advances only in slack — no DoD claim on it this week.
- [ ] **Board honesty, S013 edition:** if reality shifts again, the board is re-locked the SAME DAY (this re-lock is the first exercise of the rule); on the first "Sprint window exceeded" standup warning, the sprint is closed-or-rolled that morning.
- [ ] **Sprint 014 retrospective filled ON TIME Fri 2026-07-24**; archived; `sprint-current.md` reset for Sprint 015.

## Daily Notes

_Auto-standup writes here daily via the `CAPI Scrum Daily Standup MD` scheduled task (08:30 MNL) + the SessionStart hook as intraday top-up._

**Mon 2026-07-20 — Sprint 014 LOCKED (Mode A) at the late S013 close.** Six items committed (3 Goal A + 3 Goal B). Standing context at lock: pretest live (fieldwork week 2); fleet at F1 v1.1.4 / F3 v1.1.5 / F4 v1.4.4 (itel confirmed; other tablets pending tester UPDATE); UAT gate CLEAR-PENDING (quiet window from the 07-19 findings ages out ~07-21 — a clean next triage run flips it FIELD-READY); Carl-side loose ends from the weekend: drop stash `gps-merge-set-aside-2026-07-19` (`bcb76de2`) after review; hub LoginApp update pending. S013's retro action is baked into this sprint's DoD (close-or-roll on first warning; re-lock same-day on lane shifts).

**Mon 2026-07-20 (later) — S014 RE-LOCKED to PRETEST FOCUS (Carl: "focus this sprint to Pretesting this week").** Same-day re-lock per the S013-retro rule, first exercise. Goal A is now the pretest week itself: standing field support + a NEW **daily data-quality sweep** of incoming cases (the Q162 lesson institutionalized — the pattern sat in live data two days before anyone swept) + **GPS-on-endlevel ship-or-decline** (live now via the BREAKOFF replacement flow) + a **debrief-ready record feeding D4**. **F2 serving migration DEMOTED to Goal B slack-only** (was Goal A at the morning lock); hub/R6 unchanged (blocked-on-ASPSI). Linear mirror re-pointed to match (ANA-262 parent + ANA-264 demotion + new data-QA sub-issue).

**Mon 2026-07-20 (intraday) — triage run clean · #831 tackled end-to-end · F2 pretest data flowing.** `/capi-uat-triage`: zero tester activity in all 4 channels since Saturday's patch notes; no new GH issues/comments/reopens; gate **CLEAR-PENDING** (0 open actionable, quiet window to ~07-21). Then, on Carl's ask, took the one open non-tracker issue **#831** (F2: remove a bad response — token pasted into HCW ID): built the durable **admin void action** across all three tiers (AS `admin_void_response` + audit-trail row · Worker POST route w/ `dash_data` perm · Response-Detail "Void response…" button) + voided-row exclusions in AS reports/breakouts and both CSWeb generators. Gates: backend 207/207 · worker 241/241 · app 518/518 + tsc clean. **Draft PR #846** (repo stacks + app UI; NOTE: CI deploy workflows are disabled since the 07-14 cutover — the merge deploys nothing by itself); the **live f2-api stack got its own implementation** in the `aspsi-f2-staging-wt` server source (voidResponse in both stores + POST route + coverage/map/revisions exclusions, 143/143 + tsc clean) — **f2-api deploy deliberately held until post-pretest** (a container rebuild restarts the live respondent path); generators already deployed on-box (backed up, LF-verified, regen clean). **#831 CLOSED** — the reported row verified OUT of the operational data plane (demo-era data retired at the 07-14 cutover; live store = 28 real pretest rows, facility 040340210); **#847 filed** (encoder-path HCW-ID format validation, the queued follow-up). _Data-QA sweep, F2 side (today):_ 28 pretest responses flowing (27 stored + 1 refusal, latest 2026-07-20 08:04 MNL); dashboard counts F1=2 · F3=8 · F4=17 · F2=28 — F1's second case landed.

## Retrospective — Sprint 014

> 5-minute time-box. Four questions, fixed order. Written, not thought-through-only.

### 1. Did the sprint goal land? (yes / partial / no — one line why)

_TBD 2026-07-24._

### 2. What surprised me? (process, not work — max 3 bullets)

_TBD_

### 3. Deadline exposure check — D2 / D3 / Tranche slip days this sprint

_Informational only (out of Data Programmer scope per CSA D1–D6)._

### 4. One thing to change in Sprint 015

_TBD_
