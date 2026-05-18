---
sprint: 006
start: 2026-05-18
end: 2026-05-22
status: active
sprint_length: 1 week (5 working days)
deliverable_anchor: Goal A — F1/F3/F4 FMF Designer passes (E3-F1-001/F3-001/F4-001) · Goal B — F2 PWA UAT Round 3 close-out (R3 ran last wk; fix findings + close #271) · Goal C — scrum tooling + hygiene (E0-008 retro Q4 + E0-009b) · Goal D — CSWeb on a VPS, subset commit (E4-CSWeb-001 provision + E4-CSWeb-002 install; 003/005 + E3-F1-088 → S007)
revised: 2026-05-18 — re-planned against the 2026-05-18 ASPSI Team Meeting (CSWeb VPS added as Goal D; Goal B reframed; F3/F4 Designer passes added)
---

# Sprint 006 — F1/F3/F4 Designer passes, F2 PWA R3 close-out, CSWeb on a VPS

## Sprint Goal

> **Goal A — UHC CAPI Designer passes:** F1/F3/F4 FMF Designer passes (`E3-F1-001`, `E3-F3-001`, `E3-F4-001`). *(E3-F1-088 tablet-verify deferred to Sprint 007 — blocked behind `E4-CSWeb-005`, a S007 carry of the Goal D subset commit.)*
> **Goal B — F2 PWA UAT Round 3 close-out:** R3 **ran last week** (informally, outside #271 — confirmed via the `from-uat-round-3-2026-05` label + ~13 tester findings #302–#314 / #294 / #296 / #298). Triage + fix the findings, close [#271](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/271), reconcile the #271 tracking gap.
> **Goal C — Scrum tooling + hygiene (retro Q4 prescribed change):** Ship `E0-008` (auto-standup no-work-since-last-run branch) **committed** — third deferral; today's stale "Day 8 of 5" auto-standup is the exact failure E0-008 fixes. Pair with the 30m label-hygiene pass (`E0-009b`).
> **Goal D — CSWeb on a VPS (NEW, from the 2026-05-18 team meeting):** Stand up CSWeb on a VPS for field-response visibility, field-ops + tablet-sync management, data-manager monitoring. **Subset commit on canonical epic-04 IDs:** `E4-CSWeb-001` (provision) + `E4-CSWeb-002` (install) this sprint; `E4-CSWeb-003`/`-005` + `E3-F1-088` carry to S007.

## Committed Items

### Goal A — F1/F3/F4 Designer passes

- [ ] **E3-F1-001** F1 FMF Section A layout in CSPro Designer — generator emits `FacilityHeadSurvey.generated.fmf`. epic-03 E3-F1-001 **reopened 2026-05-18** (prior `done` superseded by the 05-12 rebuild). *(Carry — gated only on Carl's Designer time.)* `status::todo` `priority::high` `estimate::4h`
- [ ] **E3-F3-001** F3 FMF Designer pass — Patient instrument (18 records / 840 items). `status::todo` `priority::high` `estimate::4h`
- [ ] **E3-F4-001** F4 FMF Designer pass — Household instrument (22 records / 623 items, roster-heavy). `status::todo` `priority::high` `estimate::4h`

> **E3-F1-088** (Phase 1 sync tablet-verify, ~3h) **deferred to Sprint 007** — blocked behind `E4-CSWeb-005` (field-tablet sync config), a S007 carry of the Goal D subset commit. Runbook `52a0b27`; worktree `.claude/worktrees/uhc-survey-system-build`.

### Goal B — F2 PWA UAT Round 3 close-out

- [ ] **E6-PWA-007** [#271](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/271) — R3 close-out. R3 ran last week outside #271 (process gap — same pattern as the S005 #266–268 discovery). Triage + fix the ~13+ R3 findings (#302–#314 HCW survey + #294/#296/#298), close #271 with a comment linking the `from-uat-round-3-2026-05` issues, reconcile the tracking gap. Re-verify is tester-paced. `status::todo` `priority::critical` `estimate::6h Carl-driven`

### Goal C — Scrum tooling + hygiene

- [ ] **E0-008** Auto-standup no-work-since-last-run branch in `.claude/scripts/generate_standup.py` — detect sprint roll-over + no-commits window, surface "silence ≠ idle". Retro Q4 prescribed (3rd deferral). `status::todo` `priority::high` `estimate::1.5h`
- [ ] **E0-009b** Label-hygiene pass — apply `surface:`/`severity:`/`epic:` to the ~116 open repo issues (Project #8 fields populated, repo labels not). `status::todo` `priority::medium` `estimate::0.5h`

### Goal D — CSWeb on a VPS (NEW; canonical epic-04 IDs — subset commit)

- [ ] **E4-CSWeb-001** Provision VPS — host/OS/network/TLS; CSWeb web UI reachable over HTTPS. `status::todo` `priority::critical` `estimate::1d`
- [ ] **E4-CSWeb-002** CSWeb install + admin account setup. `status::todo` `priority::critical` `estimate::4h`

> **S007 carry:** `E4-CSWeb-003` (per-survey upload F1/F3/F4) + `E4-CSWeb-005` (field-tablet sync config). E3-F1-088 tablet-verify is blocked behind E4-CSWeb-005 → also S007. Local CSWeb deploy already proven (`E3-F1-085`) — VPS work is replication; the 1d on E4-CSWeb-001 likely compresses.

### Stretch — DROPPED (no headroom; full translation is S007 per 2026-05-18 meeting)

- E3-F1-011 / E3-F1-012 / E3-F1-020 — Filipino translation + multi-language + master skip gates. Carl confirmed **full dialect build is next week (S007)**; Myra's Tagalog help lands ~weekend. May *start* opportunistically but not committed.

## Sprint Backlog Sizing

| Class | Items | Estimate |
|---|---|---|
| **Goal A** | E3-F1-001, E3-F3-001, E3-F4-001 | ~12h |
| **Goal B** | E6-PWA-007 (R3 fix + close) | ~6h |
| **Goal C** | E0-008, E0-009b | ~2h |
| **Goal D** | E4-CSWeb-001 (1d) + E4-CSWeb-002 (4h) | ~12h |
| **Committed total** | | **~32h** |
| **Deferred to S007** | E3-F1-088, E4-CSWeb-003, E4-CSWeb-005 | (~10h) |
| **Stretch** | DROPPED | — |

> [!warning] Committed ~32h vs ~25h capacity — ~7h over.
> A genuine capacity overcommit, not a deadline-protection cut. Carl chose all four goals at the 2026-05-18 re-plan with quality-over-speed reaffirmed. **Not recommending logic/Designer work be deferred to protect a deadline** (per `feedback_quality_over_deadline`). Sequence by dependency; the mid-week checkpoint decides what carries to S007:
>
> **Critical path:** Goal D (E4-CSWeb-001 provision → E4-CSWeb-002 install) is the CSWeb keystone; its S007 tail (E4-CSWeb-003/005) gates E3-F1-088 (already deferred to S007 by design). Run Goal D early. Goal B re-verify is tester-paced (fix-and-hand-back). Goal C is small + independent (good filler). Goal A Designer passes are independent, parallelizable with tester-wait windows.
>
> **Most likely S007 carry if the week is full:** one Designer pass (E3-F4-001 — heaviest/newest) or E4-CSWeb-002 if VPS provisioning (E4-CSWeb-001, 1d) eats the week. Decide at the Wed/Thu checkpoint — not pre-emptively.

## Daily Notes

### 2026-05-18 (Mon) — Sprint 006 kickoff (re-planned vs the team meeting)

- **Carry-forward from Sprint 005 retro Q4:** Ship E0-008 (auto-standup no-work branch) **committed** — 3rd deferral; today's stale "Day 8 of 5" auto-standup *is* the failure mode. Pair with 30m label-hygiene (E0-009b).
- **Late kickoff note:** S005 ran full cadence + retro 05-15 but mechanical close (archive + reset) was skipped over the weekend; done today 05-18 at S006 Day-1.
- **Re-plan vs 2026-05-18 ASPSI Team Meeting** (ingested → `wiki/sources/Source - ASPSI Team Meeting 2026-05-18.md`):
  - **Goal D added (NEW):** stand up CSWeb on a VPS — field-response visibility + tablet-sync mgmt + data-manager monitoring. **ID reconciliation:** canonical `E4-CSWeb-001..007` already existed in epic-04 — Goal D uses them; **subset commit** = E4-CSWeb-001 (provision) + E4-CSWeb-002 (install) this sprint; E4-CSWeb-003/005 + E3-F1-088 → S007. epic-03 **E3-F1-001 reopened** (prior `done` stale post-05-12 rebuild). epic-03/epic-04 edited 2026-05-18 to register E3-F3-001/E3-F4-001 + sync status.
  - **Goal B reframed:** R3 *ran last week* (confirmed via `from-uat-round-3-2026-05` label + #302–#314 / #294 / #296 / #298). #271 stayed open as a tracking gap. Goal B = fix R3 findings + close #271 + reconcile, not "open + run".
  - **Goal A broadened:** added E3-F3-001 + E3-F4-001 (F3/F4 FMF Designer passes) alongside E3-F1-001.
  - **Translation:** confirmed S007 (full build next week); Myra Tagalog help ~weekend. Stretch dropped.
  - **SJREB:** full-board 2nd week of June 2026 — informational only, out of DP scope.

## Definition of Done — Sprint 006

- [ ] **E3-F1-001 / E3-F3-001 / E3-F4-001** closed: each instrument's `.fmf` saved + reviewed in CSPro Designer.
- [ ] **E6-PWA-007** closed: R3 findings (#302–#314 + #294/#296/#298) triaged + fixed-or-dispositioned; #271 closed with linking comment; `from-uat-round-3-2026-05` issues reconciled; sprint board updated.
- [ ] **E0-008** closed: no-work/roll-over branch live in `generate_standup.py`; verified against the 05-18 stale-standup scenario.
- [ ] **E0-009b** closed: ~116 open issues carry repo-side `surface:`/`severity:`/`epic:` labels.
- [ ] **E4-CSWeb-001** closed: VPS provisioned; CSWeb reachable over HTTPS (host/OS/network/TLS).
- [ ] **E4-CSWeb-002** closed: CSWeb installed; admin account works; ready for per-survey upload (E4-CSWeb-003, S007).
- [ ] *S007 carry (not S006 DoD): E4-CSWeb-003 app upload · E4-CSWeb-005 sync config · E3-F1-088 tablet-verify.*
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
