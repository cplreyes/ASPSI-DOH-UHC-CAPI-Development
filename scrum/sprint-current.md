---
sprint: 006
start: 2026-05-18
end: 2026-05-22
status: active
sprint_length: 1 week (5 working days)
deliverable_anchor: Goal A — F1/F3/F4 FMF Designer passes + E3-F1-088 tablet-verify · Goal B — F2 PWA UAT Round 3 close-out (R3 ran last wk; fix findings + close #271) · Goal C — scrum tooling + hygiene (E0-008 retro Q4 + E0-009b) · Goal D — stand up CSWeb on a VPS (field visibility + tablet sync + data-manager monitoring; enabling dep for E3-F1-088)
revised: 2026-05-18 — re-planned against the 2026-05-18 ASPSI Team Meeting (CSWeb VPS added as Goal D; Goal B reframed; F3/F4 Designer passes added)
---

# Sprint 006 — F1/F3/F4 Designer passes, F2 PWA R3 close-out, CSWeb on a VPS

## Sprint Goal

> **Goal A — UHC CAPI Designer passes + sync verify:** F1/F3/F4 FMF Designer passes (`E3-F1-001`, `E3-F3-001`, `E3-F4-001`) and tablet-verify the Phase 1 sync mechanic (`E3-F1-088`, now sequenced **behind Goal D** — needs the CSWeb VPS as the sync target).
> **Goal B — F2 PWA UAT Round 3 close-out:** R3 **ran last week** (informally, outside #271 — confirmed via the `from-uat-round-3-2026-05` label + ~13 tester findings #302–#314 / #294 / #296 / #298). Triage + fix the findings, close [#271](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/271), reconcile the #271 tracking gap.
> **Goal C — Scrum tooling + hygiene (retro Q4 prescribed change):** Ship `E0-008` (auto-standup no-work-since-last-run branch) **committed** — third deferral; today's stale "Day 8 of 5" auto-standup is the exact failure E0-008 fixes. Pair with the 30m label-hygiene pass (`E0-009b`).
> **Goal D — CSWeb on a VPS (NEW, from the 2026-05-18 team meeting):** Stand up CSWeb on a VPS for field-response visibility, field-ops + tablet-sync management, and data-manager monitoring. **Enabling dependency for `E3-F1-088`** — the sync mechanic needs a real sync target.

## Committed Items

### Goal A — F1/F3/F4 Designer passes + sync verify

- [ ] **E3-F1-001** F1 FMF Section A layout in CSPro Designer — generator skeleton `FacilityHeadSurvey.generated.fmf` ready. *(Multi-sprint carry — gated only on Carl's Designer time.)* `status::todo` `priority::high` `estimate::4h`
- [ ] **E3-F3-001** F3 FMF Designer pass — Patient instrument (18 records / 840 items). Analogous to E3-F1-001. `status::todo` `priority::high` `estimate::4h`
- [ ] **E3-F4-001** F4 FMF Designer pass — Household instrument (22 records / 623 items, roster-heavy). Analogous to E3-F1-001. `status::todo` `priority::high` `estimate::4h`
- [ ] **E3-F1-088** Phase 1 sync mechanic — **tablet-test slice** (carry from S005). **Blocked-by: Goal D** (CSWeb VPS must be up as the sync target). Off-keyboard verification + sync round-trip smoke recorded in `log.md`. Runbook `52a0b27`. Worktree `.claude/worktrees/uhc-survey-system-build`. `status::blocked` `priority::critical` `estimate::3h`

### Goal B — F2 PWA UAT Round 3 close-out

- [ ] **E6-PWA-007** [#271](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/271) — R3 close-out. R3 ran last week outside #271 (process gap — same pattern as the S005 #266–268 discovery). Triage + fix the ~13+ R3 findings (#302–#314 HCW survey + #294/#296/#298), close #271 with a comment linking the `from-uat-round-3-2026-05` issues, reconcile the tracking gap. Re-verify is tester-paced. `status::todo` `priority::critical` `estimate::6h Carl-driven`

### Goal C — Scrum tooling + hygiene

- [ ] **E0-008** Auto-standup no-work-since-last-run branch in `.claude/scripts/generate_standup.py` — detect sprint roll-over + no-commits window, surface "silence ≠ idle". Retro Q4 prescribed (3rd deferral). `status::todo` `priority::high` `estimate::1.5h`
- [ ] **E0-009b** Label-hygiene pass — apply `surface:`/`severity:`/`epic:` to the ~116 open repo issues (Project #8 fields populated, repo labels not). `status::todo` `priority::medium` `estimate::0.5h`

### Goal D — CSWeb on a VPS (NEW)

- [ ] **E4-CSWEB-001** Provision VPS + install CSWeb (PHP 8 + MySQL/MariaDB + HTTPS). Base server hardening + CSWeb web UI reachable. `status::todo` `priority::critical` `estimate::4h`
- [ ] **E4-CSWEB-002** Deploy F1/F3/F4 apps to the CSWeb VPS (Designer Deploy Application wizard per `reference_csweb_deploy_flow`) + wire `syncdata` target + tablet round-trip smoke (case push + Sync Report visible). Unblocks E3-F1-088. `status::todo` `priority::critical` `estimate::4h`

### Stretch — DROPPED (no headroom; full translation is S007 per 2026-05-18 meeting)

- E3-F1-011 / E3-F1-012 / E3-F1-020 — Filipino translation + multi-language + master skip gates. Carl confirmed **full dialect build is next week (S007)**; Myra's Tagalog help lands ~weekend. May *start* opportunistically but not committed.

## Sprint Backlog Sizing

| Class | Items | Estimate |
|---|---|---|
| **Goal A** | E3-F1-001, E3-F3-001, E3-F4-001, E3-F1-088 | ~15h |
| **Goal B** | E6-PWA-007 (R3 fix + close) | ~6h |
| **Goal C** | E0-008, E0-009b | ~2h |
| **Goal D** | E4-CSWEB-001, E4-CSWEB-002 | ~8h |
| **Committed total** | | **~31h** |
| **Stretch** | DROPPED | — |

> [!warning] Committed ~31h vs ~25h capacity — ~6h over.
> This is a genuine capacity overcommit, not a deadline-protection cut. Carl chose all four goals at the 2026-05-18 re-plan with quality-over-speed explicitly reaffirmed. **Not recommending any logic/Designer work be deferred to protect a deadline** (per `feedback_quality_over_deadline`). Instead, sequence by the dependency chain and let the mid-week checkpoint decide what realistically lands vs. carries to S007:
>
> **Critical path:** Goal D (E4-CSWEB-001 → E4-CSWEB-002) is the keystone — it unblocks E3-F1-088. Run Goal D early. Goal B re-verify is tester-paced (fix-and-hand-back, don't block on it). Goal C is small + independent (good filler). Goal A Designer passes (F1/F3/F4) are independent and parallelizable with tester wait windows.
>
> **Most likely S007 carry if the week is full:** one of the three Designer passes (E3-F4-001 is the heaviest/newest) or the E3-F1-088 tablet-verify if Goal D runs late. Decide at the Wed/Thu checkpoint — not pre-emptively.

## Daily Notes

### 2026-05-18 (Mon) — Sprint 006 kickoff (re-planned vs the team meeting)

- **Carry-forward from Sprint 005 retro Q4:** Ship E0-008 (auto-standup no-work branch) **committed** — 3rd deferral; today's stale "Day 8 of 5" auto-standup *is* the failure mode. Pair with 30m label-hygiene (E0-009b).
- **Late kickoff note:** S005 ran full cadence + retro 05-15 but mechanical close (archive + reset) was skipped over the weekend; done today 05-18 at S006 Day-1.
- **Re-plan vs 2026-05-18 ASPSI Team Meeting** (ingested → `wiki/sources/Source - ASPSI Team Meeting 2026-05-18.md`):
  - **Goal D added (NEW):** stand up CSWeb on a VPS — field-response visibility + tablet-sync mgmt + data-manager monitoring. Enabling dep for E3-F1-088.
  - **Goal B reframed:** R3 *ran last week* (confirmed via `from-uat-round-3-2026-05` label + #302–#314 / #294 / #296 / #298). #271 stayed open as a tracking gap. Goal B = fix R3 findings + close #271 + reconcile, not "open + run".
  - **Goal A broadened:** added E3-F3-001 + E3-F4-001 (F3/F4 FMF Designer passes) alongside E3-F1-001.
  - **Translation:** confirmed S007 (full build next week); Myra Tagalog help ~weekend. Stretch dropped.
  - **SJREB:** full-board 2nd week of June 2026 — informational only, out of DP scope.

## Definition of Done — Sprint 006

- [ ] **E3-F1-001 / E3-F3-001 / E3-F4-001** closed: each instrument's `.fmf` saved + reviewed in Designer.
- [ ] **E3-F1-088** closed: sync round-trip smoke recorded in `log.md` from a real tablet session against the Goal-D CSWeb VPS.
- [ ] **E6-PWA-007** closed: R3 findings (#302–#314 + #294/#296/#298) triaged + fixed-or-dispositioned; #271 closed with linking comment; `from-uat-round-3-2026-05` issues reconciled; sprint board updated.
- [ ] **E0-008** closed: no-work/roll-over branch live in `generate_standup.py`; verified against the 05-18 stale-standup scenario.
- [ ] **E0-009b** closed: ~116 open issues carry repo-side `surface:`/`severity:`/`epic:` labels.
- [ ] **E4-CSWEB-001** closed: CSWeb reachable over HTTPS on the VPS; admin login works.
- [ ] **E4-CSWEB-002** closed: F1/F3/F4 deployed; a tablet case syncs and is visible in the CSWeb Sync Report.
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
