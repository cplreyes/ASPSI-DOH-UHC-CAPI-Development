---
sprint: 015
start: 2026-08-24
end: 2026-08-28
status: active
sprint_length: 1 week (5 working days)
deliverable_anchor: TRAINING RUNWAY (T-2) — instruments closed out · fleet on current builds · timestamp feature scoped · manuals tested · translations re-measured, so the week of Sept 07 trains on a stable, current, verified build
created: 2026-08-24 — cut at the LATE S014 close (Day 32 of 5)
locked: 2026-08-24 (Monday kickoff, post-meeting)
---

# Sprint 015 — TRAINING RUNWAY (T-2 to the week of Sept 07)

> [!info] Where S014 left the project
> **Closed LATE 2026-08-24 (Day 32 of 5) — partial on the work, failed on the container.** The
> pretest completed, and ~4½ weeks of major delivery landed with no sprint around it: CSWeb
> console unification, the Bicolano translation wave, the **Aug-17 instrument migration**, UAT
> Round 7, and the **PSA submission set frozen and sent 2026-08-21**. Full record:
> `scrum/sprints/sprint-014.md`.

> [!important] The date that changes the shape of everything
> **TOT + Survey Training: week of September 07** (ASPSI team meeting, 2026-08-24). This sprint
> and the next are the entire runway. Every item below answers one question: *does this make the
> week of Sept 07 trainable?*

## Build state at lock

| | Submitted to PSA (frozen, tag `capi-psa-2026-08-20`) | Current DEV |
|---|---|---|
| F1 Facility Head | v3.1.5 | v3.1.6 |
| F2 HCW (PWA) | v3.0.0 | — |
| F3 Patient | v6.0.2 | v6.0.3 |
| F4 Household | v3.1.3 | v3.1.4 |

Every build after the freeze carries a **DEV BUILD — NOT THE VERSION SUBMITTED TO PSA** banner.
Promotion gates, channels and rollback: the `capi-devops` skill.

## Carry-in from Sprint 014

| Item | State | S015 disposition |
|---|---|---|
| **UAT Round 7** | open since 08-19; 23 findings closed 08-20; trackers #1282–#1285 open | **Goal A** — drive actionable to zero before training. |
| **#1311 · #1312** | filed 08-24: F1 Q35.2 + F2 Q24.2, both "adopt DOH's final option list" | **Goal A** — same class; ship together. |
| **Fleet propagation** | tablets still on pre-Aug-17 builds; 4 R7 tickets were stale apps, not defects | **Goal A, critical** — trainees must install the current build. |
| **Automatic start/finish timestamp** | NEW, from the 08-24 meeting | **Goal A** — scope before building. |
| **Manuals** | "should be tested" (08-24 meeting) | **Goal A**. |
| **Roster — 147 accounts** | asked Aug 3, Aug 10, Aug 24; still on 7 | **Goal B** — blocked-on-ASPSI; chase. |
| **Translations** | Aug-17 rewrote the English; old percentages void; error messages still 0% | **Goal A** for the measurement, **Goal B** for supply. |
| **Parked data items** | F3 payment-source order · F4 Q18 brackets · -98/-99 gate · F2 Q120 + "None" | **Goal B** — R7 is the window to decide. |
| **`/scrum` Modes A + D** | stubbed since April; root cause of the S014 overrun | **Goal B** — the S014 retro action. |

## Committed Items — LOCKED 2026-08-24

### Goal A — make the week of Sept 07 trainable

- [ ] **Close UAT Round 7 to zero actionable** — #1311 (F1 Q35.2) + #1312 (F2 Q24.2) adopt DOH's final option lists, plus anything new. Ship as versioned DEV builds through the `capi-devops` gates, never as quiet edits. `status::todo` `priority::critical`
- [ ] **Fleet propagation — every tablet on the current build** — REMOVE + RE-ADD, not the Update menu, which misses redeploys. Name any holdout device. Highest-value item in the sprint: four R7 tickets were stale apps, and a training room installing a stale build repeats that at scale. `status::todo` `priority::critical` `estimate::0.5d`
- [ ] **Scope the automatic start/finish timestamp BEFORE building it** — paradata already timestamps entry activity per case. If the ask is operational (duration per interview, supervisor visibility) this is a **report off existing data**; if it must be a visible questionnaire field it is a **build change with data-shape impact**. Settle which at the Performance Metrics meeting, then implement. `status::todo` `priority::high` `estimate::0.5d scope + TBD build`
- [ ] **Re-measure translation coverage against the Aug-17 English** — the Aug-10 percentages are void; the English moved underneath them. Produce a defensible per-language, per-instrument number, with the error/validation-message gap (still 0%) stated separately. Training in Ilocano or Hiligaynon depends on this being known rather than guessed. `status::todo` `priority::high` `estimate::0.5d`
- [ ] **Manuals tested against the current build** — walk the CAPI Manual + the 4 tool guides against what ships today, not the version they were written for. The Aug-17 renumbering moved question IDs, so any manual citing old numbers is wrong in a training room. `status::todo` `priority::high`

### Goal B — supporting / blocked

- [ ] **Roster chase — 147 accounts (22 FS + 125 SE)** — fourth ask. Names in a list is enough. Training Day 2 has everyone installing at once; 7 logins cannot do it. `status::blocked-on-ASPSI` `priority::high`
- [ ] **Performance Metrics meeting (this week)** — bring the timestamp scoping question plus the existing paradata / dashboard capability. `status::todo` `priority::medium`
- [ ] **Organizational meeting (this week)** — deployment assignments, centralized secretariat, call centre, institutional memory. Carl's input: what CAPI support the field actually needs during rollout. `status::todo` `priority::medium`
- [ ] **Parked data items — decide or hold** — R7 is open, which is the window for the four data-shape decisions. Escalate once, record the answer, do not chase. `status::blocked-on-ASPSI` `priority::medium`
- [ ] **Implement `/scrum` Mode D + Mode A** — the S014 retro action: close+archive+reset, and plan, as actual commands. Until it exists, the manual rule stands. `status::todo` `priority::medium` `estimate::0.5d`

## Definition of Done — Sprint 015

- [ ] **UAT R7 actionable count at zero**, or every remaining item explicitly triaged with a next step and an owner.
- [ ] **Fleet verified on the current build** — device by device, holdouts named. "Patch note posted" does not count.
- [ ] **Timestamp feature scoped and decided** (report vs build), and shipped if the answer is "report".
- [ ] **Translation coverage re-measured** — a real number against the Aug-17 English, error messages called out separately.
- [ ] **Manuals walked against the current build**; every stale question reference fixed or listed.
- [ ] Roster escalated a fourth time, with the training-day consequence stated plainly.
- [ ] **Sprint 015 closed ON TIME Friday 2026-08-28** — retro filled, archived, `sprint-current.md` reset. First exercise of the S014 rule: if a standup warns "window exceeded", the sprint closes that morning before any other work.

## Daily Notes

**Mon 2026-08-24 — Sprint 015 LOCKED at the late S014 close.** Ten items (5 Goal A + 5 Goal B).
Context at lock: PSA submission sent Fri 08-21; submitted set frozen and recoverable; DEV channel
open; UAT R7 live with #1311/#1312 filed this morning; **training dated — week of Sept 07**, which
makes this T-2 and reframes the sprint as training runway. Carried from the ASPSI meeting: the new
timestamp feature, manuals to be tested, and the Performance Metrics + Organizational meetings this
week. Still blocked on ASPSI: the 147-account roster (fourth ask) and translation supply.

## Retrospective — Sprint 015

> 5-minute time-box. Four questions, fixed order. Written, not thought-through-only.
> **Due Friday 2026-08-28** — on time, per the S014 retro action.

### 1. Did the sprint goal land? (yes / partial / no — one line why)

_TBD 2026-08-28._

### 2. What surprised me? (process, not work — max 3 bullets)

_TBD_

### 3. Deadline exposure check

_Informational only (out of Data Programmer scope per CSA D1–D6)._

### 4. One thing to change in Sprint 016

_TBD_
