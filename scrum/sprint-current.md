---
sprint: 007
start: 2026-05-25
end: 2026-05-29
status: planning
sprint_length: 1 week (5 working days)
deliverable_anchor: TBD — set at Mode A planning, Mon 2026-05-25
revised: 2026-05-22 — skeleton created at Sprint 006 close (Mode D); awaiting Mode A planning
---

# Sprint 007 — (planning)

> [!note] Planning skeleton
> This file was reset from Sprint 006 at its Mode D close on 2026-05-22. It is a **carry-in + constraints skeleton only** — the Sprint Goal, committed items, sizing, and DoD are filled by `/scrum` **Mode A** on Monday 2026-05-25. Do not treat anything below as committed yet.

> [!warning] `scrum/sprint-007-plan.md` is stale — do not promote it
> A `sprint-007-plan.md` draft exists (authored 2026-05-09, F1-validation-anchored). It **predates the 2026-05-18 ASPSI team-meeting re-plan** and contradicts current reality (it says "CSWeb stand-up waits until F1 build artifact stable" — CSWeb was committed to S006 by the meeting). Mode A should supersede it, not carry it forward.

## Carry-in from Sprint 006

Five items carry from S006 (2/8 committed items closed there — E0-008, E0-009b):

| ID | Item | S006 state | Notes for Mode A |
|---|---|---|---|
| **E3-F1-001** | F1 FMF Section A layout — CSPro Designer pass | todo (never started) | Goal A carry. Gated only on Carl's Designer time. |
| **E3-F3-001** | F3 FMF Designer pass — Patient (18 rec / 840 items) | todo (never started) | Goal A carry. |
| **E3-F4-001** | F4 FMF Designer pass — Household (22 rec / 623 items) | todo (never started) | Goal A carry; heaviest of the three. |
| **E4-CSWeb-001** | Provision VPS — host/OS/network/TLS | runbook authored | Execution-ready. Runbook: `deliverables/CSWeb/CSWeb-on-VPS-Setup-Runbook.md`. **Blocked on:** Carl provisioning a VPS + a domain name (Let's Encrypt won't issue to bare IPs). |
| **E4-CSWeb-002** | CSWeb install + admin account | runbook authored | Execution-ready; same runbook (Part 4). Follows E4-CSWeb-001. |
| **E6-PWA-007** | [#271](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/271) — R3 close-out | partial | 3 R3 bugs shipped to prod (#328/#315/#327), 6 issues closed, #294 cluster root-caused. Remaining: formally close #271, reconcile `from-uat-round-3-2026-05`. Re-verify is tester-paced. |

## Hard external constraint entering Sprint 007

- **PSA clearance gate — 2026-06-12.** PSA will not clear the survey without the CAPI app + **7 distinct translated versions** bundled (Bisaya ≠ Cebuano). QC-finalization (not first-draft) is the binding predecessor. Per the 2026-05-18 team meeting the full 7-language build is **S007 work** — this is the **S007 critical path**. (Ref: `wiki/concepts/CAPI Seven-Language Translation Build.md`, memory `project_capi_translation_psa_deadline`.)

## Also designated S007 (from the 2026-05-18 meeting / S006 deferrals)

- **E4-CSWeb-003 / -005** — per-survey F1/F3/F4 upload + field-tablet sync config (follow E4-CSWeb-001/002).
- **E3-F1-088** — F1 Phase-1 tablet sync-verify; blocked behind E4-CSWeb-005.

## Sprint Goal — DRAFT 2026-05-25

> **Close out F2 PWA UAT Round 3 in v1.3.x** (Dr. Myra Silva-Javier's 2026-05-21 decisions on the 9 questionnaire-design items: 7 buildable in this patch + #271 formal close), **wire the F2 7-language translation pipeline** (PSA 2026-06-12 critical path; F2 only this sprint — CSPro F1/F3/F4 translation is gated on Designer passes still carrying), and **land the F1 FMF Designer pass** (smallest carry, unblocks the F1 build envelope and F1-side translation work in S008).

Three deliverable anchors:

- **Goal A — F2 PWA R3 close-out (v1.3.x patch + #271).** Apply Myra's 2026-05-21 verdicts (7 of 9 fully buildable; 2 sub-items remain `status:blocked` pending the 3-question team follow-up sent today); ship v1.3.x; formally close [#271](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/271) and reconcile the `from-uat-round-3-2026-05` label set. Closes the questionnaire-design half of E6-PWA-007.
- **Goal B — F2 PWA 7-language translation pipeline.** Wire the 7 PSA-target languages (Tagalog, Cebuano, Bisaya, Hiligaynon, Waray, Ilocano, Bicolano) into the F2 PWA i18n config from the Drive source-of-truth; verify each in staging; staging snapshot is the PSA-clearance artifact for the F2 share of the bundle. Switcher architecture is already in place from R1/R2 — this is content-wiring, not infra build.
- **Goal C — F1 FMF Section A Designer pass (E3-F1-001 carry).** Smallest of the three S006 Designer carries; completes the F1 build envelope so F1-side translation can start in S008. Gated only on Carl's CSPro Designer time.

## Committed Items — DRAFT 2026-05-25

### Goal A — F2 PWA R3 close-out

- [ ] **E6-PWA-007a** Apply the 7 buildable Myra decisions in F2 PWA v1.3.x. Staged at `deliverables/F2/PWA/2026-05-25-r3-myra-decisions-issue-updates.md` + `_issue-bodies/{303,304,305,306,307,309,310,311,312}.md`. Build scope: #303 close as no-op · #304 Q52 "no significant impact" exclusive standalone · #305-3b Q9 vs Q4 in-survey block at `years < age − 20` · #306 Q35 per-component DK (year required) · #307-5a Q36 multi-select + skip-logic re-derive · #309-i Q39 dead option removal · #310 Q47 None-standalone · #311 Q110 None-standalone · #312-ii Q125 Retire-standalone. `status::todo` `priority::high` `estimate::8h`
- [ ] **E6-PWA-007b** Formally close [#271](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/271) with linking comment to the 9 R3 issues; reconcile the `from-uat-round-3-2026-05` label set on the surviving sub-items (`status:blocked` retained on `#305-3a`, `#307-5b`, `#309-ii`, `#312-i` pending team-follow-up responses). `status::todo` `priority::high` `estimate::1h`

> **Opportunistic (in-sprint if team responses land):** the 3 follow-up questions sent today on Q9 year floor, Q36 wording, Q38 wording. If any respond mid-sprint, fold the fix into v1.3.x — each is ~1h.

### Goal B — F2 PWA 7-language translation pipeline

- [ ] **E2-F2-TRANS-001** Wire the 7 translated languages into F2 PWA i18n config from the Drive source-of-truth. Per-language smoke test on staging (one HCW survey pass per language). Drive folder + per-language status tracked in [[wiki/concepts/CAPI Seven-Language Translation Build|CAPI Seven-Language Translation Build]]. Known build-input risks (Bisaya household trailing, Ilocano reviewer gap) are ASPSI-owned per memory `project_capi_translation_psa_deadline`; do not chase from the Data Programmer lane — work with whatever languages have QC-finalized strings landed by Wed 2026-05-27. `status::todo` `priority::critical` `estimate::4h`

> **Why F2-only this sprint:** CSPro F1/F3/F4 translation is gated on the F-series Designer passes (still in S006 carry — Goal C tackles F1, F3/F4 still carry). Phasing translation as F2-now → F1 in S008 → F3/F4 in S009 keeps the 2026-06-12 PSA bundle on track without forcing the Designer passes to be rushed. Per memory `feedback_quality_over_deadline`.

### Goal C — F1 FMF Designer pass

- [ ] **E3-F1-001** F1 FMF Section A layout in CSPro Designer — generator emits `FacilityHeadSurvey.generated.fmf`. Three-sprint carry (S005 → S006 → S007). Gated only on Carl's Designer time. epic-03 E3-F1-001 reopened 2026-05-18 (prior `done` superseded by the 2026-05-12 rebuild). `status::todo` `priority::high` `estimate::4h`

> **F3-001 + F4-001 (E3-F3-001, E3-F4-001) NOT committed this sprint.** Carrying again — F1 is the lightest Designer pass and the right one to land first; F3 (18 rec / 840 items) and F4 (22 rec / 623 items roster-heavy) are heavier and stretch S007 over capacity. Per S006 retro Q4 (plan to capacity, not over).

### S007 carries forward to S008

- E3-F3-001 (F3 FMF Designer pass)
- E3-F4-001 (F4 FMF Designer pass)
- E4-CSWeb-001 / -002 (VPS provision + install; still gated on Carl provisioning a VPS + domain name — execution-ready runbook at `deliverables/CSWeb/CSWeb-on-VPS-Setup-Runbook.md`)
- E4-CSWeb-003 / -005 (per-survey upload + tablet sync config; follows CSWeb-001/002)
- E3-F1-088 (F1 Phase-1 tablet sync-verify; blocked behind E4-CSWeb-005)

## Sprint Backlog Sizing — DRAFT 2026-05-25

| Class | Items | Estimate |
|---|---|---|
| **Goal A** | E6-PWA-007a, E6-PWA-007b | ~9h |
| **Goal B** | E2-F2-TRANS-001 | ~4h |
| **Goal C** | E3-F1-001 | ~4h |
| **Opportunistic** | 3 team-follow-up fixes if responses land | ~3h |
| **Buffer / overhead** | sprint ceremonies + comms + verify | ~2h |
| **Committed total** | | **~22h (with ~3h opportunistic, ~25h envelope)** |
| **Carries to S008** | E3-F3-001, E3-F4-001, E4-CSWeb-001/002/003/005, E3-F1-088 | (~25h) |

> **Sizing call:** S006 closed ~7h over capacity (32h committed → 5 items carried). S007 commits 22h hard + 3h opportunistic = 25h envelope, matching S006 retro Q4's prescription "plan to capacity, not over it." Translation pipeline is the **critical path to PSA 2026-06-12** (T-18 days); R3 close-out is the **highest-value win this sprint** (unblocks $#271$ and clears the longest-running engineering debt); F1 Designer pass is the **smallest of the three carries** and the prerequisite for F1 translation in S008.

## Definition of Done — Sprint 007 — DRAFT 2026-05-25

- [ ] **E6-PWA-007a** closed: F2 PWA v1.3.x shipped to prod with the 7 buildable Myra-decision items; release notes tagged; CHANGELOG bumped; F2 staging smoke-tested before the prod cutover.
- [ ] **E6-PWA-007b** closed: [#271](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/271) closed with linking comment to the R3 slate; label reconciliation complete on the 4 sub-items still gated (`#305-3a`, `#307-5b`, `#309-ii`, `#312-i`).
- [ ] **E2-F2-TRANS-001** closed: F2 PWA staging serves all 7 PSA-target languages (or all those with QC-final strings as of Wed 2026-05-27); language switcher verified per locale; staging URL is the PSA-clearance artifact for the F2 share of the 2026-06-12 bundle.
- [ ] **E3-F1-001** closed: F1 `FacilityHeadSurvey.generated.fmf` reviewed in CSPro Designer; layout sign-off documented in `log.md`.
- [ ] **Sprint 007 retrospective** filled Fri 2026-05-29; archived to `scrum/sprints/sprint-007.md`; `sprint-current.md` reset for Sprint 008.

## Daily Notes

_(populated from Day 1)_

## Retrospective — Sprint 007

> 5-minute time-box. Four questions, fixed order. Written, not thought-through-only.

### 1. Did the sprint goal land? (yes / partial / no — one line why)

_TBD_

### 2. What surprised me? (process, not work — max 3 bullets)

_TBD_

### 3. Deadline exposure check — D2 / D3 / Tranche slip days this sprint

_Informational only (out of Data Programmer scope per CSA D1–D6)._

### 4. One thing to change in Sprint 008

_TBD_
