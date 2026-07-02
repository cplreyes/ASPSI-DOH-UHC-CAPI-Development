---
sprint: 006
start: 2026-05-18
end: 2026-05-22
status: closed
sprint_length: 1 week (5 working days)
deliverable_anchor: Goal A — F1/F3/F4 FMF Designer passes · Goal B — F2 PWA UAT R3 close-out (#271) · Goal C — E0-008 auto-standup retro-injection + E0-009b label hygiene · Goal D (NEW) — stand up CSWeb on a VPS
closed: 2026-05-22 (Mode D retro not written at the time — the close routed straight into the S007 skeleton)
reconstructed: 2026-06-29 — rebuilt from `log.md`, git history (2026-05-18 → 05-22), the four S006 standups, and the Sprint 007 carry-in table. The original `sprint-006.md` was lost (a stash-pop conflict at the S007→S008 boundary re-introduced then dropped S006 content — see `sprint-008.md` frontmatter `revised: 2026-06-02`).
---

# Sprint 006 — F1/F3/F4 Designer passes · F2 PWA R3 close-out · CSWeb on a VPS

> [!note] Reconstructed retro (2026-06-29)
> No Mode-D retrospective file was written at the 2026-05-22 close, and the `sprint-006.md` archive was later lost to a stash-pop conflict. This file is reconstructed after the fact from contemporaneous evidence: `log.md` (entries 923–926 = the S006 plan/re-plan/epic-sync; entry 129 = the F1↔F2 benchmark; entries 227–246 = the Myra R3 ingest), the four daily standups 2026-05-18 → 05-21, the git commit stream for the window, and the **Sprint 007 carry-in table** (which records S006's final state: *2 of 8 committed items closed*). Treat the per-item outcomes as evidence-derived, not a live-logged retro.

## Carry-in from Sprint 005

| ID | Item | S005 state | S006 disposition |
|---|---|---|---|
| **E0-008** | Auto-standup retro-injection / no-work roll-over branch | deferred **3×** (S005 Q4: "pull into S006 *committed*") | **Committed (Goal C).** Closed in S006. |
| **E3-F1-001** | F1 FMF Section A — CSPro Designer pass | reopened 2026-05-18 (prior `done` superseded by the 2026-05-12 from-scratch rebuild) | **Committed (Goal A).** Not started — carries to S007. |

## Context entering Sprint 006 — the 2026-05-18 ASPSI Team Meeting

The sprint was **re-planned at kickoff** against the 2026-05-18 ASPSI Team Meeting (ingested to `wiki/sources/Source - ASPSI Team Meeting 2026-05-18.md`). Four directives drove the plan:

1. **NET-NEW — stand up CSWeb on a VPS** for field-response visibility + tablet sync + data-manager monitoring (Epic 4; couples to the `E3-F1-088` sync target). → **Goal D added.**
2. **Park HCW new features; fix the UAT Round 3 findings** (R3 ran the prior week — `from-uat-round-3-2026-05`, ~13 findings #302–#314 + #294/#296/#298). → **Goal B reframed.**
3. **Back to F1/F3/F4 CSPro dev** while waiting on testers. → **Goal A broadened** to all three FMF Designer passes.
4. **Dialect translation starts; full 7-language build is next week** (the PSA 2026-06-12 critical path lands in S007).

> [!warning] Contradiction flagged at ingest
> Carl reported "fixing R3 findings from last week," but `#271`/`E6-PWA-007` was still OPEN and last touched 2026-05-12 — never formally opened to testers. Same tracking-gap pattern as the S005 `#266–268` discovery.

## Sprint Goal — locked 2026-05-18

> Land the **F1/F3/F4 FMF Designer passes** (Goal A — back-to-CSPro while testers run), **close out F2 PWA UAT Round 3** and reconcile `#271` (Goal B), **ship E0-008 + a label-hygiene pass** (Goal C — the thrice-deferred retro-Q4 item), and **stand up CSWeb on a VPS** (Goal D — NEW; the sync target that unblocks `E3-F1-088`).

Four deliverable anchors / eight committed items:

- **Goal A — F1/F3/F4 FMF Designer passes.** `E3-F1-001` (reopened) + `E3-F3-001` + `E3-F4-001`. Carl-availability-paced (CSPro Designer time).
- **Goal B — F2 PWA UAT Round 3 close-out.** `E6-PWA-007` — fix the ~13 R3 findings, close `#271`, reconcile the label set.
- **Goal C — auto-standup tooling + label hygiene.** `E0-008` (retro-Q4, 4th appearance) + `E0-009b` (30m label-hygiene pass).
- **Goal D — CSWeb on a VPS.** `E4-CSWeb-001` (provision: host/OS/network/TLS) + `E4-CSWeb-002` (install + admin account). Subset commit; `E4-CSWeb-003/005` + `E3-F1-088` tablet-verify are S007 by design.

## Committed Items — final state

### Goal A — F1/F3/F4 FMF Designer passes

- [ ] **E3-F1-001** F1 FMF Section A layout — CSPro Designer pass (reopened). **Not started — Designer time never opened.** `status::carry → S007` *(ultimately swept done 2026-06-13 @ S009 close: combined-view 259-block .fmf, Designer-verified + deployed — closing the five-sprint carry.)*
- [ ] **E3-F3-001** F3 (Patient) FMF Designer pass. **Not started.** `status::carry → S007` *(swept done 2026-06-13 @ S009: 217→237-screen skip-aware combined view.)*
- [ ] **E3-F4-001** F4 (Household) FMF Designer pass. **Not started.** `status::carry → S007` *(swept done 2026-06-13 @ S009: 159→225-screen skip-aware combined view.)*

> Designer passes were Carl-availability-paced, not technically blocked. With Goal B and Goal D consuming the week, no Designer window opened — the dependency-sequencing risk flagged on Day 1 materialized.

### Goal B — F2 PWA UAT Round 3 close-out *(the only goal that moved)*

- [~] **E6-PWA-007** [#271](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/271) — R3 close-out. **Partial.** `#271` itself was confirmed closed Fri 2026-05-15 at R3 end; the fix wave landed across the week but the formal reconcile + the Carl-gated `#294` AS redeploy remained. `status::in-progress → carry (questionnaire-design half) S007`. A substantial admin-portal + survey R3 PR stream shipped to `main`:
  - **#332** UAT R3 close-out — 5 fixes (#296 #298 #302 #313 #308)
  - **#333** F2-PWA backlog cleanup (#286 #289) · **#334** re-ship stranded a11y fixes (#287 #284, integrity correction)
  - **#335** reproduce + root-cause #314 (matrix blank on edit) → **#338** #314 matrix-rehydrate fix + #294 runbook correction
  - **#337** #331 password toggle + #297 DLQ routes (+ #295 dispositioned)
  - **#339** #328 clickable username → change-password entry · **#341** #315 authenticate the Files download path · **#342** #327 audit every admin mutation route
  - Cross-instrument win logged the same week (`log.md` 129): F1↔F2 hard-validation benchmark closed three F1-only gaps (G1 `Q3_AGE` range floor, G2 tenure×age tightened `age−18 → age−20` per Myra R3 #305, G3 final-visit ≥ first-visit date order). Preflight CLEAN + CSEntry compile PASS.

### Goal C — auto-standup tooling + label hygiene

- [x] **E0-008** Auto-standup retro-injection / no-work roll-over branch. **Done** (closed its 4th-appearance streak). The stale "Sprint 005 / Day 8 of 5" auto-standup that mis-fired at this very sprint's kickoff was the exact fixture it closes. `status::done`
- [x] **E0-009b** 30-minute label-hygiene pass. **Done.** `status::done`

### Goal D — CSWeb on a VPS

- [ ] **E4-CSWeb-001** Provision VPS — host/OS/network/TLS. **Runbook authored; not provisioned — blocked on VPS + domain.** `status::carry → S007` *(ultimately LIVE 2026-06-02: Elestio LAMP + CSWeb 8.0.1; `csweb.asiansocial.org` DNS 06-03 — swept @ S009 close.)*
- [ ] **E4-CSWeb-002** CSWeb install + admin account. **Not done — follows -001.** `status::carry → S007` *(installed 2026-06-02; headless wizard, MySQL 8.4 trigger workaround.)*

### Sprint 004 carry passing through

- [ ] **E4-APRT-035** Cross-platform QA close-out (E2 Firefox + E3 Edge). **Deferred** (2026-05-11 R3-pivot decision; risk mostly visual; PR #54 ready pending findings disposition). Continued to carry.

## Carries forward to Sprint 007

- **E3-F1-001 / E3-F3-001 / E3-F4-001** — all three FMF Designer passes (never started).
- **E4-CSWeb-001 / -002** — VPS provision + install (runbooks authored; still gated on VPS + domain).
- **E6-PWA-007** — questionnaire-design half (formal reconcile + `#294` Carl-gated AS push).
- **E4-APRT-035** — cross-platform QA (S004-origin carry).

## Sprint Backlog Sizing — committed vs actual

| Class | Items | Estimate | Actual |
|---|---|---|---|
| **Goal A** | E3-F1-001, E3-F3-001, E3-F4-001 | ~12h | 0h (not started) |
| **Goal B** | E6-PWA-007 | ~6h | ~8h (R3 PR wave; partial — half carries) |
| **Goal C** | E0-008, E0-009b | ~2h | ~2h (both done) |
| **Goal D** | E4-CSWeb-001, E4-CSWeb-002 | ~8h | ~2h (runbooks only; provisioning blocked) |
| **Buffer / overhead** | ceremonies + comms + Myra R3 ingest | ~3h | ~3h |
| **Committed total** | 8 items | **~31h vs ~25h capacity (~6h over)** | **2 of 8 committed closed** |

## Definition of Done — Sprint 006 — final

- [ ] **Goal A** (3 Designer passes) — not started; all carry to S007.
- [~] **Goal B** (`E6-PWA-007` / #271) — R3 fix wave shipped; `#271` closed; formal reconcile + `#294` push carry to S007.
- [x] **Goal C** (`E0-008` + `E0-009b`) — both done.
- [ ] **Goal D** (CSWeb VPS) — runbooks authored; provisioning blocked on VPS + domain; carries to S007.
- [ ] **Sprint 006 retrospective** — not written at close (Mode-D skipped into the S007 skeleton). *Reconstructed 2026-06-29.*

## Daily Notes

**2026-05-18 (Mon, Day 1) — Mode A kickoff + re-plan.** Sprint re-planned at kickoff against the 2026-05-18 ASPSI Team Meeting (Goal D added, Goal B reframed, F3/F4 Designer passes added to Goal A). The auto-generated standup mis-fired as "Sprint 005 / Day 8 of 5" (roll-over not detected) and was replaced with a real S006 Day-1 kickoff — the exact failure `E0-008` targets. Epic-03 / epic-04 ID reconciliation: `E3-F1-001` reopened post-rebuild; canonical `E4-CSWeb-001/002` adopted over freshly-minted duplicates; `E3-F1-088` set `blocked` behind Goal D. Committed ~31h vs ~25h capacity, acknowledged over — sequence by dependency, decide S007 carry at the mid-week checkpoint, not pre-cutting (`log.md` 923–926).

**2026-05-19 → 05-20 (Tue–Wed, Day 2–3) — Goal B moves; everything else waits.** R3 admin-portal + survey fix wave lands on `main` (#332–#338 cluster); `#314` matrix-blank-on-edit reproduced, root-caused, and fixed. F1↔F2 hard-validation benchmark closes three F1-only gaps (`log.md` 129). No Goal A (Designer) or Goal D (provisioning) progress.

**2026-05-21 (Thu, Day 4) — Mode C checkpoint.** Board: **7 To Do / 1 In Progress / 0 Done** of 8 — Goal B (`E6-PWA-007`) the only mover; `#271` confirmed already closed Friday at R3 end; remaining R3 issues routed to ASPSI as `design-decision`. `E0-008` flagged at its 4th deferral — weighted heavily for the next-day close. More R3 PRs land (#339 / #341 / #342).

**2026-05-22 (Fri, Day 5) — close.** `E0-008` + `E0-009b` closed (Goal C complete). Goals A and D carry; `E6-PWA-007` carries its questionnaire-design half. The Mode-D retro was not authored at close — the boundary routed straight into the S007 skeleton (`sprint-007.md` `revised: 2026-05-22 — skeleton created at Sprint 006 close`).

**Inter-sprint, 2026-05-22 → 05-25 — Myra R3 ingest.** Dr. Myra Silva-Javier answered the HCW CAPI Comments matrix 2026-05-21 ("Answered the form already"); ingested to a source-summary + an analysis page with per-issue build/clarify/no-op dispositions and PSA-cascade flags (`log.md` 227–246). This becomes the S007 Goal A input.

## Retrospective — Sprint 006 *(reconstructed 2026-06-29)*

> Reconstructed from evidence; the time-boxed live retro was not written at close.

### 1. Did the sprint goal land? (yes / partial / no — one line why)

**No (2 of 8).** Only Goal C (`E0-008` + `E0-009b`) fully closed. Goal B moved hard (the R3 fix wave) but stayed partial; Goal A (3 Designer passes) never started; Goal D (CSWeb VPS) produced runbooks but no provisioning. 4 of 8 committed items carried to S007.

### 2. What surprised me? (process, not work — max 3 bullets)

- **The kickoff auto-standup mis-fired** ("Sprint 005 / Day 8 of 5") — sprint roll-over wasn't detected. Ironically the exact bug `E0-008` (committed this sprint) fixes; it had to be hand-corrected to even start the sprint.
- **A 4-goal re-plan at kickoff over-committed the week.** ~31h slotted into ~25h capacity. The mid-week "decide the carry" checkpoint never cut anything, so the over-commit resolved itself by Goals A and D simply not starting.
- **Carl-paced Designer work loses every contention.** Whenever a tester-facing or infra goal shares the week, the CSPro Designer passes get no window — three of them slipped untouched.

### 3. Deadline exposure check — D2 / D3 / Tranche slip days this sprint

_Informational only (out of Data Programmer scope per CSA D1–D6)._ SJREB full-board noted as moved to the 2nd week of June 2026 (ASPSI/PI lane).

### 4. One thing to change in Sprint 007

**Plan to capacity.** Stop committing 30h+ into a ~25h sprint. Size to real available hours, sequence strictly by dependency, and protect a dedicated Designer window rather than leaving Goal A to "tester-wait slots" that never materialize. *(S007 carried this prescription forward — and then tripped on a related assumption when the auto-standup hook went silent Wed–Fri; see `sprint-007.md` retro Q2.)*
