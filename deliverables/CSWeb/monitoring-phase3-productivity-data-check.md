---
title: "Monitoring Phase 3 (Enumerator Productivity) — Data-Check Finding"
category: deliverable
tags: [csweb, monitoring, productivity, phase3, data-check, e8-monitoring]
created: 2026-07-06
status: BLOCKED — needs a post-freeze instrument change
relates_to: goal-prompt-monitoring-dashboard-integration.md (Phase 3)
---

# Phase 3 (Enumerator Productivity) — Data-Check Finding

**Question (the gate before building):** does a **stable per-case interviewer/enumerator
identifier** survive the CSEntry → sync → breakout round-trip, so we can compute cases per
enumerator / team / day?

**Answer: No.** There is no stable per-case enumerator ID in the collected F1/F3/F4 data
today. Building the productivity panel needs a small **instrument change**, which is
**post-freeze** (the pretest freeze stands — data-integrity exceptions only).

## Evidence (from the repo — no box query needed)

| Signal | Where | What it means |
|---|---|---|
| **`"askOperatorId": false`** | every F1/F3/F4 `.ent` (and the compile driver default) | CSEntry's built-in operator-ID capture is **disabled** — no operator id is recorded at case start. |
| **`ENUMERATOR_S_NAME`** (alpha, 50) | `field_control` (→ breakout `enumerator_s_name`) | A **free-text name**, not a key. Blank / typo / "Juan" vs "Juan D." variants make it unusable as a grouping ID. `SURVEY_TEAM_LEADER_S_NAME` is the same shape. |
| Stable **`operator_id`** | `data/roster/roster-source.csv`, `AS_<operator_id>.dat`, hub `FS_OPERATOR_ID` / `hub_operator_id` | The real roster ID exists — but only in the **hub / roster / assignment** layer. It is **not written into the collected F1/F3/F4 case record**. |
| **BT → hub → CSWeb relay** | supervisor-hub MenuApp "Relay to CSWeb" | Cases are Bluetooth-collected from multiple enumerators, then uploaded by the **supervisor's hub account**. So the **CSWeb sync/upload user is the supervisor, not the interviewer** — per-enumerator attribution can't be recovered server-side either. |

**Conclusion:** enumerator attribution must be **stamped into the case at collection time**;
it cannot be reconstructed from `enumerator_s_name` (unreliable) or from the CSWeb upload user
(it's the relaying supervisor).

## What would unblock it (post-freeze instrument change — ASPSI/DOH go/no-go)

Preferred: **write a stable `ENUMERATOR_ID` (roster `operator_id`) into each instrument's
`field_control` at case start.** Cleanest source is the assignment/login the hub already holds:

- The hub distributes `AS_<operator_id>.dat` per enumerator and knows `hub_operator_id`.
- Add a 1-item `ENUMERATOR_ID` (alpha, ~20) to `FIELD_CONTROL` (generator-first, via the shared
  `_case_control_items` in `cspro_helpers.py` so all three instruments get it uniformly), and set
  it at `FIELD_CONTROL` preproc from the assigned operator / login (mirrors how the case-key PSGC
  gate already runs there). It then flows to the breakout as `field_control.enumerator_id` and the
  dashboard groups on it directly.
- Alternative (weaker): flip `askOperatorId: true` so CSEntry captures the login per case — but
  under the hub relay model the device/login mapping is less clean than an explicit roster ID, and
  it changes the enumerator's start flow.

Either is a **field-behavior change** → **not** a data-integrity exception → it waits until after
the pretest gate (freeze), or rides the **Sep rollout hardening** alongside K1/K3 (roster
encryption + SUPERVISOR_ID hierarchy), which already touch this layer.

## Until then

- **Phases 1 & 2 stand on their own** — the on-pace view and coverage-vs-target do not need
  enumerator attribution.
- The dashboard can carry a **team/area proxy** now if useful (cases per facility/day already fall
  out of the Phase-1 submissions data + the facility dimension) — but true per-enumerator
  productivity waits on the `ENUMERATOR_ID` stamp above.

*Prepared 2026-07-06 from the F1/F3/F4 instrument sources + the supervisor-hub relay model.*
