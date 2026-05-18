---
sprint: 006
start: 2026-05-18
end: 2026-05-22
status: active
sprint_length: 1 week (5 working days)
deliverable_anchor: Goal A — close UHC tablet build (E3-F1-088 tablet-verify + E3-F1-001 F1 FMF Designer pass) · Goal B — F2 PWA UAT Round 3 cycle run + close-out (E6-PWA-007 / #271, carry) · Goal C — scrum tooling + hygiene (E0-008 auto-standup no-work branch — retro Q4 prescribed; + 30m label-hygiene pass)
---

# Sprint 006 — Close UHC tablet build, run F2 PWA Round 3, ship the auto-standup no-work branch

## Sprint Goal

> **Goal A — UHC tablet build close-out (CAPI):** Tablet-verify the Phase 1 sync mechanic (`E3-F1-088` carry — off-keyboard session, runbook `52a0b27`) and complete the F1 FMF Designer pass (`E3-F1-001` — multi-sprint carry, gated only on Carl's CSPro Designer time slot, not technically blocked).
> **Goal B — F2 PWA UAT Round 3 cycle (carry):** Run and close `E6-PWA-007` ([#271](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/271) — still OPEN, never opened to testers per #271 last-touch 2026-05-12). Guides already drafted 05-13. Open to Shan + Kidd + Marriz, testers run, triage + close-out.
> **Goal C — Scrum tooling + hygiene (retro Q4 prescribed change):** Ship `E0-008` (auto-standup no-work-since-last-run branch) as a **committed** item — third deferral; today's stale "Day 8 of 5" auto-standup is the exact failure E0-008 fixes. Pair with a 30m label-hygiene pass on the 116 open repo issues (`E0-009` Q2 finding).

## Committed Items

### Goal A — UHC tablet build close-out

- [ ] **E3-F1-088** Phase 1 sync mechanic — **tablet-test slice** (carry from S005). Off-keyboard verification + sync round-trip smoke recorded in `log.md`. Runbook `52a0b27`. Worktree `.claude/worktrees/uhc-survey-system-build`. `status::todo` `priority::critical` `estimate::3h`
- [ ] **E3-F1-001** F1 FMF Section A layout in CSPro Designer — generator skeleton `FacilityHeadSurvey.generated.fmf` ready. *(Multi-sprint carry — gated only on Carl's Designer time.)* `status::todo` `priority::high` `estimate::4h`

### Goal B — F2 PWA UAT Round 3 cycle

- [ ] **E6-PWA-007** [#271](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/271) — UAT Round 3 cycle. Guides drafted 05-13 (`docs/F2-PWA-UAT-Round-3-{HCW-Survey,Admin-Portal}-Tester-Guide-2026-05-13.md`). Open to Shan + Kidd + Marriz (`#f2-pwa-uat` + guide URLs + per-tester creds), testers run, triage rolling, close-out. `status::todo` `priority::critical` `estimate::4h Carl-driven`

### Goal C — Scrum tooling + hygiene

- [ ] **E0-008** Auto-standup no-work-since-last-run branch in `.claude/scripts/generate_standup.py` — detect sprint roll-over + no-commits window, surface "silence ≠ idle". Retro Q4 prescribed (3rd deferral). `status::todo` `priority::high` `estimate::1.5h`
- [ ] **E0-009b** Label-hygiene pass — apply `surface:`/`severity:`/`epic:` to the 116 open repo issues (Project #8 fields populated, repo labels not). `status::todo` `priority::medium` `estimate::0.5h`

### Stretch (pull if base clears mid-week)

- [ ] **E3-F1-011** Filipino translations for all question labels + option text. `priority::high` `estimate::4h`
- [ ] **E3-F1-012** Multi-language switching (`setlanguage`, language-select on cover). `priority::high` `estimate::3h`
- [ ] **E3-F1-020** Master skip gates (section-level eligibility filters). `priority::high` `estimate::4h`

## Sprint Backlog Sizing

| Class | Items | Estimate |
|---|---|---|
| **Committed** | E3-F1-088 (tablet slice), E3-F1-001, E6-PWA-007, E0-008, E0-009b | ~13h |
| **Carry-context** | E4-APRT-035 (S005-deferred cross-env QA, PR #54) — pull if Goal A/B clear early | +3h |
| **Stretch** | E3-F1-011, E3-F1-012, E3-F1-020 | ~11h |

> Capacity ~25h solo-dev week. Committed ~13h leaves ~12h headroom — E4-APRT-035 first pull, then F1 i18n stretch. Goal A tablet-test is Carl-availability-paced (off-keyboard); Goal B is tester-paced — committed kept deliberately lean so the slack absorbs both.

## Daily Notes

### 2026-05-18 (Mon) — Sprint 006 kickoff

- **Carry-forward from Sprint 005 retro Q4:** Ship E0-008 (auto-standup no-work branch) **committed** — 3rd deferral; today's stale "Day 8 of 5" auto-standup *is* the failure mode. Pair with 30m label-hygiene pass on 116 open repo issues.
- **Late kickoff note:** S005 ran full cadence + retro 05-15 but mechanical close (archive + reset) was skipped over the weekend; done today 05-18 at S006 Day-1.
- **Pending input:** Carl opened `Downloads/May 18, 2026 Monday ASPSI Team Meeting.txt` — same-day team meeting, not yet ingested; may carry new directives that reshape this plan.

## Definition of Done — Sprint 006

- [ ] **E3-F1-088** closed: sync round-trip smoke recorded in `log.md` from a real tablet session.
- [ ] **E3-F1-001** closed: `FacilityHeadSurvey.fmf` saved + reviewed.
- [ ] **E6-PWA-007** closed: R3 opened to 3 testers, ran, triaged, `from-uat-round-3-2026-05` issues dispositioned, sprint board updated.
- [ ] **E0-008** closed: no-work/roll-over branch live in `generate_standup.py`; verified against the 05-18 stale-standup scenario.
- [ ] **E0-009b** closed: 116 open issues carry repo-side `surface:`/`severity:`/`epic:` labels.
- [ ] **Sprint 006 retrospective** (4 questions) filled 2026-05-22; archived to `scrum/sprints/sprint-006.md`; `sprint-current.md` reset for Sprint 007.

## Retrospective — Sprint 006

> 5-minute time-box. Four questions, fixed order. Written, not thought-through-only.

### 1. Did the sprint goal land? (yes / partial / no — one line why)

_TBD 2026-05-22_

### 2. What surprised me? (process, not work — max 3 bullets)

_TBD_

### 3. Deadline exposure check — D2 / D3 / Tranche slip days this sprint

_Informational only (out of Data Programmer scope per CSA D1–D6)._

### 4. One thing to change in Sprint 007

_TBD_
