---
sprint: 011
start: 2026-06-22
end: 2026-06-26
status: closed
sprint_length: 1 week (5 working days)
deliverable_anchor: CAPI field-readiness workstream (thin slice + emergent bucket + real exit criterion) · BUILD E0-SCRUM-SYNC · PhilHealth reinstatement (if PNGs land) · PSA confirm-or-close
created: 2026-06-21 — Mode D skeleton at the S010→S011 boundary
locked: 2026-06-21 (Mode A, eve of kickoff) — committed set frozen below
closed: 2026-06-28 — retrospective filled from session/git/log evidence (2 days post-end; the very lag E0-SCRUM-SYNC targets — see retro Q2)
---

# Sprint 011 — CAPI field-readiness (reframed) + scrum-sync BUILD — CLOSED 2026-06-28

> [!info] Where S010 left the project
> R4 patching ran as a continuous stream **past** the sprint boundary (F3/F4 multi-select→roster conversions, F4 Section-C rebuild, then **Cluster-5 break-off + disposition #515/#561**, device-confirmed). Net-new this period: the `capi-multiselect` skill, the Option-B roster pilot, an entire new sub-project — the **Supervisor App** (Phase-1 built + tested; Phase-2 spec/plan, deferred per D7) — and the **CSWeb sync dashboard** (live). Full record: `scrum/sprints/sprint-010.md` + `log.md` 2026-06-20/21 + git `main`.

## Carry-in from Sprint 010

| ID | Item | State | S011 disposition |
|---|---|---|---|
| **E0-SCRUM-SYNC** | Mid/close-of-sprint scrum-state sync + 08:30 drift canary | committed in the S009 retro, **never built** — recurred in S010 (retro Q2) | **Committed (Goal A)** — BUILD it (the retro's #1 change). |
| **R4 field-readiness** | UAT R4 triage stream | ran past S010 as a continuous stream with no closing condition | **Committed (Goal A)** as E0-UAT-REFRAME + E6-CAPI-FIELDREADY — reframe as a standing workstream with a real exit criterion. |
| **capi-multiselect fan-out** | remaining select-alls / cost matrices (Shape A F1 #567; Shape B F3 #672/#674/#675/#688/#689/#691/#692/#693) | recipe encoded; Q92 Option-B pilot device-confirmed | Folded into E6-CAPI-FIELDREADY; device-test before each fan-out. |
| **E2-F3-PHILHEALTH / E2-F4-PHILHEALTH** | Q38.1/Q38.2 + Q45.1/Q45.2 reinstatement | **blocked on Carl**: save the 3 value-set PNGs from Kidd's 6/9 email | **Committed-conditional** — builds the moment the PNGs land. |
| **E0-PSA-001b** | PSA gate outcome confirm | unrecorded (**3rd carry**) | **Committed (Goal A)** — confirm-or-close; no 4th carry. |
| **Supervisor App go-live prep** | Phase-1 built; needs the QA-supervisor roster | blocked on ASPSI (names for the `supervisor-qa` role) | Named in the plan (per retro Q4); provision `supervisor-qa` when names land. Phase-2 deferred (D7). |
| **Goal B (clasp/#294 + #336)** | #294 retests + #336 disposition | 3rd-sprint carry, untouched | **Stretch (opportunistic)** — close-or-kill this sprint. |
| **Harmonization codebook ripple** | Q148 + roster + disposition data-shape changes | ETL skeleton live | Update codebook + breakout ETL before real data flows. |
| **Translations Batch 2** | Tagalog-final / Ilocano / Hiligaynon-F3F4 | blocked on ASPSI check | Drop-in when delivered (pipeline proven). |

## Committed Items — LOCKED 2026-06-21 (Mode A) · with close-out outcomes

> The two S010-retro process changes (E0-SCRUM-SYNC, E0-UAT-REFRAME) were committed here as first-class tasks — not parked as notes, which is exactly the failure mode S010 hit. Outcomes annotated at close.

### Goal A — CAPI field-readiness + scrum-sync build

- [ ] **E0-SCRUM-SYNC** ❌ **NOT BUILT (3rd recurrence).** The drift canary / sprint-state sync was committed as a first-class task and still went unbuilt — this retro is again filled days late, the exact failure it targets. `status::todo → carried` `priority::high`
- [~] **E0-UAT-REFRAME** 🟡 **PARTIAL.** The emergent workstream (Supervisor hub, `capi-multiselect`) is now **named** in the Product Backlog and Epic 6/8 reframed as field-readiness (PB refresh 2026-06-28) — but a crisp, checkable **exit criterion** (e.g. N consecutive days no blocking finding) was not operationalized. `status::todo → partial`
- [x] **E6-CAPI-FIELDREADY** ✅ **ADVANCED HARD (this is where the value went).** `capi-uat-triage` loop ran the **UAT Round 5** bug-burndown (F1/F3/F4 fixes deployed); and the **Supervisor hub Phase-2** went from *deferred (D7)* to **BUILT + deployed + device-verified on two tablets** — C1 CSWeb relay confirmed, C4 live coverage reports (`forcase` counts + assignment target), C5 `UR_SUPERVISOR_ID` roster — with a **live training guide** at `csweb.asiansocial.org/docs/hub-guide.html`. Enumerator menu literally verified on the Samsung A23. `status::done (emergent)`
- [ ] **E2-F3-PHILHEALTH / E2-F4-PHILHEALTH** ⏸ **STILL BLOCKED.** Builds the moment Carl saves Kidd's 3 value-set PNGs; PNGs not yet saved. `status::blocked (PNGs) → carried`
- [ ] **E0-PSA-001b** ❌ **NOT RECORDED (now a 4th-sprint carry).** PSA gate outcome still unconfirmed. `status::todo → carried`

### Goal B — opportunistic (stretch)

- [ ] **#294 verify-and-close + #336 disposition** ❌ **UNTOUCHED** (3rd-sprint carry → carried again). `status::todo → carried`

## Parked / planned (blocked — future sprint)

- [ ] **E4-F2-ELESTIO** Migrate F2 Survey + Admin Portal off Cloudflare/Google to a dedicated Elestio instance (`hcw.asiansocial.org`). Planning DONE 2026-06-22 (spec v0.2 + 19-task plan). **BLOCKED on provisioning** (Carl/ASPSI: instance + DNS + cost). Build Tasks 2–17 runnable locally vs Docker MySQL before the instance exists. `status::blocked` (provisioning) `priority::medium`

## Definition of Done — Sprint 011 — outcomes

- [ ] **E0-SCRUM-SYNC built + proven** — ❌ not built (carried, 3rd time).
- [~] UAT reframed in the backlog with a real exit criterion; emergent work named — 🟡 named + reframed in PB; exit criterion not operationalized.
- [ ] PhilHealth live on F3+F4, or explicitly blocked-on-ASPSI documented — ⏸ documented blocked-on-Carl (PNGs).
- [ ] PSA gate outcome recorded — ❌ still unrecorded (4th carry).
- [ ] Goal B closed or killed — ❌ untouched (carried).
- [ ] **Sprint 011 retrospective filled ON TIME Fri 2026-06-26** — ❌ filled 2026-06-28, 2 days late (the exhibit for retro Q2).

> **Net:** the committed *process/admin* items missed across the board; the **real, high-value delivery was emergent** — UAT R5 burndown + the Supervisor hub Phase-2 shipped end-to-end and device-verified, plus the training guide going live. Third consecutive sprint where the plan mispredicted where the value would come from.

## Daily Notes

**Sprint window 2026-06-22 → 06-26 + close 06-28 — emergent delivery dominated.** Significant out-of-board delivery (all in the working tree / committed locally as `f2aa9f3`, push pending Carl):
- **Supervisor hub Phase-2 — COMPLETE + device-verified + live.** C4 live coverage report (`forcase` counts over F1/F3/F4 + received assignment target), C5 roster `UR_SUPERVISOR_ID`; regenerated + deployed to prod CSWeb. End-to-end on **two tablets** (itel + Samsung A23): login → role menu → instrument launch → OnExit return; **C1 Relay-to-CSWeb confirmed**. Training guide rewritten to v1 and **published live**.
- **UAT Round 5** opened across all surfaces; `capi-uat-triage` loop ran F1/F3/F4 fixes + deploys.
- **Product Backlog refresh 2026-06-28** — headline + roadmap + buckets made forward-looking; §4 by-epic + all 8 active epic files dated/refreshed; scope correction applied (SJREB + tablets + pretest scheduling = ASPSI's, not Carl's — Carl's lane ends at field-ready, waits for the pretest date).

## Retrospective — Sprint 011

> 5-minute time-box. Four questions, fixed order. Written, not thought-through-only.

### 1. Did the sprint goal land? (yes / partial / no — one line why)

**Partial — and for the third sprint running, the real output was emergent.** E6-CAPI-FIELDREADY advanced hard: UAT Round 5 burndown via the triage loop, and the **Supervisor hub Phase-2** went from *deferred* to **built + deployed + device-verified on two tablets** with a **live training guide**. But every committed *process/admin* item missed: **E0-SCRUM-SYNC never built (3rd recurrence)**, E0-UAT-REFRAME only partly applied (named in the PB, no operational exit criterion), **PhilHealth still blocked** on the PNGs, **PSA confirm still unrecorded (4th carry)**, Goal B untouched. The sprint itself ran to Day 7/5 with the retro unfilled — the exact failure E0-SCRUM-SYNC exists to prevent.

### 2. What surprised me? (process, not work — max 3 bullets)

- **The stale-snapshot failure is now a three-peat (S009→S010→S011).** The scrum-sync fix has been *committed* three times and *built* zero times; this retro is again filled days late from evidence. Confirmed a third time: a retro action that isn't wired into tooling does not change behavior — it's theater until it's code.
- **Emergent work didn't just beat the plan — it shipped a whole deferred phase.** The Supervisor hub Phase-2 (login→menu→Bluetooth→relay→reports→map) was marked "deferred per D7" at *sprint start* and was **finished + device-verified** by close. When the plan mis-predicts the value source three sprints in a row, the planning frame is the problem, not the execution.
- **"Field-readiness" still has no closing condition.** UAT R5 opened and burned down, but it behaves like an open development stream (new structure surfaces with each fix), not a converging bug queue. The reframe was committed; the exit criterion was never made checkable.

### 3. Deadline exposure check — D2 / D3 / Tranche slip days this sprint

_Informational only (out of Data Programmer scope per CSA D1–D6)._ External-gate posture clarified this sprint: SJREB + tablets + pretest scheduling are ASPSI/DOH's; Carl's lane ends at field-ready and waits for ASPSI's pretest date.

### 4. One thing to change in Sprint 012

**Stop re-committing the carries — build-or-kill them on Day 1, before any CAPI work.** (a) **E0-SCRUM-SYNC**: either actually implement it as the *first* task of the sprint (08:30 generator flags drift when `log.md` is newer than `sprint-current.md` by >2 days; sprint-state synced at close), or formally **kill it** and accept manual close discipline — three misses means it's worth 2 hours up front or it should be dropped, not carried a fourth time. (b) **PSA confirm + Goal B (#294/#336)**: close-or-kill Day 1, no further carry. (c) **Operationalize the field-readiness exit criterion** (e.g. N consecutive days with no new tester-blocking finding) so "field-ready" is a state you can check, not a vibe — and so the loop knows when to stop.
