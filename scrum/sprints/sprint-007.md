---
sprint: 007
start: 2026-05-25
end: 2026-05-29
status: closed
sprint_length: 1 week (5 working days)
deliverable_anchor: Goal A — F2 PWA R3 close-out (Myra slate + #271) · Goal B — F2 7-language translation pipeline (PSA 2026-06-12 critical path) · Goal C — F1 FMF Designer pass (smallest carry)
closed: 2026-06-01 — Mode D archive at the S007→S008 boundary
revised: 2026-05-22 — skeleton created at Sprint 006 close (Mode D); Mode A planning Mon 2026-05-25
---

# Sprint 007 — F2 PWA R3 close-out · F2 translation pipeline · F1 FMF Designer pass

## Carry-in from Sprint 006

Five items carried from S006 (2/8 committed items closed there — E0-008, E0-009b):

| ID | Item | S006 state | S007 disposition |
|---|---|---|---|
| **E3-F1-001** | F1 FMF Section A layout — CSPro Designer pass | todo (never started) | **Not done — carries to S008.** Designer time never opened. |
| **E3-F3-001** | F3 FMF Designer pass — Patient (18 rec / 840 items) | todo (never started) | **Not committed S007 (sized out). Carries to S008.** |
| **E3-F4-001** | F4 FMF Designer pass — Household (22 rec / 623 items) | todo (never started) | **Not committed S007 (sized out). Carries to S008.** |
| **E4-CSWeb-001** | Provision VPS — host/OS/network/TLS | runbook authored | **Not done — still blocked on VPS + domain. Carries to S008.** |
| **E4-CSWeb-002** | CSWeb install + admin account | runbook authored | **Not done — follows -001. Carries to S008.** |
| **E6-PWA-007** | [#271](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/271) — R3 close-out | partial | **Done (questionnaire-design half).** Engineering-bug half complete except the Carl-gated AS push and tester-paced re-verify. |

## Hard external constraint entering Sprint 007

- **PSA clearance gate — 2026-06-12.** PSA will not clear the survey without the CAPI app + **7 distinct translated versions** bundled (Bisaya ≠ Cebuano). Per the 2026-05-18 ASPSI team meeting the full 7-language build is S007 work — this is the **S007 critical path**.

## Sprint Goal — LOCKED 2026-05-25

> **Close out F2 PWA UAT Round 3 in v1.3.x** (Dr. Myra Silva-Javier's 2026-05-21 decisions on the 9 questionnaire-design items: 7 buildable in this patch + #271 formal close), **wire the F2 7-language translation pipeline** (PSA 2026-06-12 critical path; F2 only this sprint — CSPro F1/F3/F4 translation is gated on Designer passes still carrying), and **land the F1 FMF Designer pass** (smallest carry, unblocks the F1 build envelope and F1-side translation work in S008).

Three deliverable anchors:

- **Goal A — F2 PWA R3 close-out (v1.3.x patch + #271).** Apply Myra's 2026-05-21 verdicts (7 of 9 fully buildable; 2 sub-items remain `status:blocked` pending the 3-question team follow-up sent 2026-05-25); ship v1.3.x; formally close [#271](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/271) and reconcile the `from-uat-round-3-2026-05` label set. Closes the questionnaire-design half of E6-PWA-007.
- **Goal B — F2 PWA 7-language translation pipeline.** Wire the 7 PSA-target languages into the F2 PWA i18n config from the Drive source-of-truth; verify each in staging; staging snapshot is the PSA-clearance artifact for the F2 share of the bundle.
- **Goal C — F1 FMF Section A Designer pass (E3-F1-001 carry).** Smallest of the three S006 Designer carries.

## Committed Items — final state

### Goal A — F2 PWA R3 close-out

- [x] **E6-PWA-007a** Apply the buildable Myra decisions in F2 PWA. **Done 2026-05-28 (PR #347, merged to main → CF Pages auto-deploy):** #303 closed no-op · #304 Q52 exclusive standalone · #305-3b Q9-vs-Q4 in-survey block at `years ≥ age − 20` (warn→error) · #307-5a Q36 single→multi · #309-i Q39 dead option removed · #310 Q47 None-standalone · #311 Q110 None-standalone · #312-ii Q125 Retire-standalone. Forward sign-off into `F2-Spec.md` / `F2-Skip-Logic.md` / `F2-Cross-Field.md`. 446 unit tests + tsc + codegen green. **#306 (Q35 per-component DK) DEFERRED** — needs a generator extension for per-subfield-optional `multi-field`; filed as a follow-up on the issue. **Note:** formal v1.3.x version tag + CHANGELOG carries to S008 (release-notes workflow's job; gstack-ship does not bump version per app CLAUDE.md). `status::done`
- [x] **E6-PWA-007b** [#271](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/271) reconciled 2026-05-28 with a linking comment to the full #303–#312 slate (was already CLOSED at S006 close-out). Label set reconciled: `status:blocked` retained on the 4 surviving sub-items (#305-3a, #307-5b, #309-ii, #312-i) pending team-follow-up responses; `#304/#310/#311` closed; `#303` closed no-op; `#306` open (deferred). `status::done`

> **Goal A bonus (off-plan, in-sprint):** Three admin-portal R3 PRs also landed during Goal A work — PR #345 (`#343` date-filter defaults empty across Audit/DLQ/Sync/Map), PR #346 (`#318` BulkImport modal a11y + `#344` Roles-delete optimistic UI), and PR #342 was completed pre-sprint then shipped (#327 audit-coverage). Plus per-issue triage comments on #294/#317/#319/#322/#323/#324/#325/#326/#330/#340/#344. None were on the S007 plan; they were tester re-files Mon morning and went through the same v1.3.x cutline.

### Goal B — F2 PWA 7-language translation pipeline

- [ ] **E2-F2-TRANS-001** Wire the 7 translated languages into F2 PWA i18n config from the Drive source-of-truth. **Not done — never started.** No standup or commit signal 2026-05-27 → 2026-05-29. `status::carry → S008` `priority::critical (PSA T-11 from 2026-06-01)`

### Goal C — F1 FMF Designer pass

- [ ] **E3-F1-001** F1 FMF Section A layout in CSPro Designer. **Not done — Designer time never opened.** `status::carry → S008`

### S007 carries forward to S008

- **E2-F2-TRANS-001** (Goal B — now S008 critical path)
- **E3-F1-001** (Goal C — four-sprint carry: S005 → S006 → S007 → S008)
- **v1.3.x formal release tag** (release-notes workflow; closes E6-PWA-007a's DoD tail)
- **#294 prod AS push** (Carl-gated on Google auth; recurring deploy-gap class — wire `clasp` to close it for good)
- **3 Myra clarifications** (Q9 0+0 / Q36 wording / Q38 wording — `status:blocked` until team responses land)
- **E3-F3-001 / E3-F4-001** (F3/F4 FMF Designer passes; sized out of S007)
- **E4-CSWeb-001 / -002 / -003 / -005** (VPS provision + install + per-survey upload + tablet sync; still gated on VPS + domain)
- **E3-F1-088** (F1 Phase-1 tablet sync-verify; blocked behind E4-CSWeb-005)
- **#336** PR (R3 #314 diagnosis from 2026-05-19 — needs disposition)

## Sprint Backlog Sizing — committed vs actual

| Class | Items | Estimate | Actual |
|---|---|---|---|
| **Goal A** | E6-PWA-007a, E6-PWA-007b | ~9h | ~9h (done) + ~3h off-plan admin-portal hotfixes |
| **Goal B** | E2-F2-TRANS-001 | ~4h | 0h (not started) |
| **Goal C** | E3-F1-001 | ~4h | 0h (not started) |
| **Opportunistic** | 3 team-follow-up fixes if responses land | ~3h | 0h (no responses landed in-sprint) |
| **Buffer / overhead** | sprint ceremonies + comms + verify | ~2h | ~2h |
| **Committed total** | | **~22h** | **~14h delivered (1 of 3 goals)** |

## Definition of Done — Sprint 007 — final

- [x] **E6-PWA-007a** core code shipped to main + CF Pages auto-deploy. *Formal v1.3.x tag + CHANGELOG carry to S008.*
- [x] **E6-PWA-007b** [#271](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/271) reconciled; label set complete on the 4 surviving sub-items.
- [ ] **E2-F2-TRANS-001** — not started; carries to S008 as critical path.
- [ ] **E3-F1-001** — not started; carries to S008.
- [x] **Sprint 007 retrospective** filled 2026-06-01; archived to `scrum/sprints/sprint-007.md`; `sprint-current.md` reset for Sprint 008.

## Daily Notes

**2026-05-25 (Mon, Day 1) — Mode A planning locked.** Sprint goal + three deliverable anchors set per the file above. Myra's 2026-05-21 decision matrix staged at `deliverables/F2/PWA/2026-05-25-r3-myra-decisions-issue-updates.md` + per-issue `_issue-bodies/` files. 3 follow-up questions sent to the team (Q9 floor, Q36 wording, Q38 wording).

**2026-05-26 (Tue, Day 2) — Auto-standup wrote; tactical sections still stubs (sprint frontmatter `status: planning`).** No code progress logged.

**2026-05-27 → 2026-05-29 (Wed–Fri, Day 3–5) — No standup files written.** SessionStart hook did not fire on these days (or wrote outside `scrum/standups/`). Goal A code did land on 2026-05-28 (3 PRs to main) per `git log`; no Goal B / Goal C signal.

**2026-05-28 — Goal A landed (R3 close-out).** Shipped 3 PRs across the R3 admin-portal + survey halves:
- PR #345 → #343 (date-filter defaults empty: Audit/DLQ/Sync/Map).
- PR #346 → #318 (BulkImport modal a11y: ESC + backdrop + scroll) + #344 (Roles delete optimistic UI).
- PR #347 → R3 Myra build-ready bundle: closes #304/#310/#311, partials on #305/#307/#309/#312, #306 deferred.
Plus: #294 prod AS-push runbook surfaced to Carl (deploy gated on his Google auth); downstream admin-portal items #317/#319/#325/#326/#330 flagged as AS-deploy-gap-dependent (retest after push); #322 kill-switch UI + #340 pwd_version JWT deferred to v2.0.2 with rationale. E6-PWA-007 (#271) questionnaire-design half complete; engineering-bug half complete except the AS-push (Carl-gated) and tester-paced re-verify.

**Inter-sprint, 2026-05-28 evening → 2026-06-01 (Mon) — Mode D close-out.** Sprint period closed Fri 2026-05-29; retro deferred to Mon at the S007→S008 boundary because the standup automation didn't fire Wed–Fri and there was no in-sprint trigger to write Q1–Q4. #294 prod AS push diagnosed across multiple paste attempts; signed-probe diagnostic script staged in `$CLAUDE_JOB_DIR/probe-as.mjs`, not yet executed. Identifies the recurring deploy-gap class and motivates a `clasp` wiring in S008.

## Retrospective — Sprint 007

> 5-minute time-box. Four questions, fixed order. Written, not thought-through-only.

### 1. Did the sprint goal land? (yes / partial / no — one line why)

**Partial.** Goal A shipped in full (3 PRs to main + per-issue triage on the R3 slate); Goal B (translation pipeline — the **PSA 2026-06-12 critical path**) and Goal C (F1 FMF Designer pass) **never started**. 1 of 3 goals delivered.

### 2. What surprised me? (process, not work — max 3 bullets)

- **The auto-standup hook silently dropped Wed–Fri.** The S006 retro Q4 prescription ("plan to capacity") assumed reliable daily signal to recalibrate mid-sprint. With no standups 5/27–5/29, the sprint ran open-loop on Goals B and C — and they slipped without an in-sprint trigger to flag it.
- **The Goal A scope ballooned via tester re-files.** PR #347 (the planned Myra bundle) shipped on plan, but Mon morning brought 3 admin-portal R3 issues (`#343`, `#318`, `#344`) that consumed real time before #347 and weren't on the S007 sizing.
- **#294 (AS push) is a fragile manual deploy class, not a one-off.** Multiple paste attempts hit "wrong project" / "stale folder" / "URL drift" traps with the GUI paste workflow. Symptom-and-fix posture won't close this; wiring `clasp` is the move.

### 3. Deadline exposure check — D2 / D3 / Tranche slip days this sprint

_Informational only (out of Data Programmer scope per CSA D1–D6)._

### 4. One thing to change in Sprint 008

**Sequence the PSA critical path FIRST and singularly.** S008 must commit Goal B (translation pipeline) as the headline and treat F1 Designer (Goal C) and everything else as opportunistic. PSA gate is 2026-06-12 (last day of S009); S008 must deliver translation pipeline staging-ready by 2026-06-05 so S009 owns submission/clearance work. Also: **wire `clasp` to close the #294-class AS-deploy gap permanently** before more time leaks to GUI paste sessions. Also: **verify the standup automation is firing daily** (S006 retro called this out indirectly; S007 actually tripped on it).
