---
sprint: 010
start: 2026-06-15
end: 2026-06-19
status: planning
sprint_length: 1 week (5 working days)
deliverable_anchor: UAT Round 4 closeout → field-ready sign-off posture · PhilHealth reinstatement build (F3/F4) · PSA gate outcome confirm
created: 2026-06-13 — Mode D skeleton at the S009→S010 boundary
locked: (pending — Mode A lock Mon 2026-06-15)
---

# Sprint 010 — R4 closeout + PhilHealth reinstatement (+ PSA confirm) — SKELETON, lock Monday

> [!info] Where S009 left the project
> All three CAPI instruments are **live on CSWeb, multi-language (F1 ×7 / F3 ×6 / F4 ×6), under active UAT Round 4** (closes **Mon 2026-06-15 AM**). The publish→deploy pipeline is fully agent-driven; mid-round patching is routine (9 deploys in S009 Day 5 alone). Full record: `scrum/sprints/sprint-009.md` + `log.md` 2026-06-12 entries.

## Carry-in from Sprint 009

| ID | Item | State | S010 disposition |
|---|---|---|---|
| **E0-PSA-001** | PSA bundle / gate outcome | gate date passed, outcome **unrecorded** | **Confirm with Kidd/Myra first** — if PSA still needs a formal bundle, assemble from the live deployed artifacts (now stronger than the planned bundle); else close as overtaken. |
| **R4 tracking #368/#369/#370** | UAT Round 4 closeout | round closes Mon AM | Headline candidate: ingest findings, triage fix-vs-route, patch via the (now-encoded) `cspro-patch-fix` loop, reconcile + close tracking issues, drive to zero. Includes #371–#375 + #376 retest confirmations. |
| **PhilHealth reinstatement** | F3 Q38.1/Q38.2 + F4 Q45.1/Q45.2 (Kidd 6/9 email; DOH-agreed) | **blocked on Carl**: save the 3 value-set PNGs from the email | Build rides the patch loop once unblocked (dcf+apc+qsf ×2 + codebook ripple). |
| **Translations Batch 2** | Tagalog (checked-final) / Ilocano / Hiligaynon-F3F4 | blocked on ASPSI translation check | Drop-in when delivered (pipeline proven: maps → regenerate → deploy). **Relay the F4 Flu/Fever doc defect to Kidd.** |
| **Q148 CheckBox rollout decision** | ~60 remaining select-alls across F1/F3/F4 | awaiting R4 verdict on the Q148 pilot | Decide post-R4; recipe encoded in `cspro-patch-fix`. |
| **Harmonization codebook ripple** | Q148 data-shape change (+ PhilHealth adds when built) | ETL skeleton live | Update codebook + breakout ETL before any real data flows. |
| **Goal B (clasp/#294)** | #294 prod retests (#317/#319/#325/#326/#330) | clasp CI landed 6/1 (#348); retests unverified | Verify-and-close, ~1h. Third-sprint carry — close it or kill it. |
| **#336** | R3 #314 diagnosis PR | open since 5/19 | Disposition: merge / close-with-rationale / kill. |
| **3 Myra clarifications** | #305-3a / #307-5b / #309-ii | `status:blocked` | Opportunistic fold-in if responses land. |

## Process change committed from the S009 retro

- [ ] **E0-SCRUM-SYNC** Mid-sprint + close-of-sprint scrum-state sync: fold log.md/GH outcomes into this file's `status::` fields at least once mid-week; extend the 08:30 generator to flag drift (log.md newer than sprint-current by >2 days → canary line). Prevents the stale Mon/Fri Slack snapshots. `status::todo` `priority::high` `estimate::1h`

## Candidate Committed Items (lock Monday — Mode A)

### Goal A (candidate) — UAT Round 4 closeout → field-ready posture

- [ ] **E6-CAPI-R4-CLOSE** Ingest all R4 findings (#368/#369/#370 + channel reports), triage fix-vs-route, patch + deploy + notify per instrument, reconcile + close the tracking issues. Includes #371–#375 (AWSP retest) + #376 verify. `status::todo` `priority::critical` `estimate::1d`
- [ ] **E2-F3-PHILHEALTH / E2-F4-PHILHEALTH** Build Q38.1/Q38.2 + Q45.1/Q45.2 reinstatement (conditional; value sets from the email PNGs), gates + deploy + patch notes + codebook addition. `status::blocked` (PNGs) `priority::critical` `estimate::3h`
- [ ] **E0-PSA-001b** Confirm the PSA gate outcome with ASPSI; assemble-or-close the bundle accordingly. `status::todo` `priority::high` `estimate::1h`

### Goal B (candidate, opportunistic)

- [ ] **#294 verify-and-close** + **#336 disposition**. `status::todo` `priority::high` `estimate::2h`

## Definition of Done — Sprint 010

_(to be finalized at Monday's lock)_

- [ ] R4 closed: every finding fixed+deployed or dispositioned; tracking issues #368/#369/#370 reconciled + closed.
- [ ] PhilHealth questions live on F3+F4 (or explicitly blocked-on-ASPSI documented).
- [ ] PSA gate outcome recorded; bundle assembled or closed as overtaken.
- [ ] E0-SCRUM-SYNC in place (no stale snapshot on Fri 6/19).
- [ ] Sprint 010 retrospective filled Fri 2026-06-19; archived; `sprint-current.md` reset for Sprint 011.

## Daily Notes

_Auto-standup writes here daily via the `CAPI Scrum Daily Standup MD` scheduled task (08:30 MNL) + the SessionStart hook as intraday top-up._

**Inter-sprint (2026-06-19 → 06-21) — Supervisor App + Cluster 5 + CSWeb dashboard shipped.** Significant out-of-sprint-board delivery at/after the S010 boundary (all committed + pushed to `main`):
- **Cluster 5 (#515/#561)** — mid-interview break-off + off-form `CASE_DISPOSITION` completeness sentinel BUILT in the F3/F4 generators, deployed, and **device-confirmed on the itel** (withdraw → jump to closing → record → `endlevel` skips the photo → clean "Accept this case?"). Found+fixed a real device bug (verification-photo loop on a no-interview disposition). #515/#561 CLOSED. This is R4-adjacent closeout (Epic 3).
- **Supervisor App Phase 1 (Review Layer)** — built + tested (14/14 pytest), a PII-light field-QA report (coverage/partials/flags) reusing the Cluster-5 disposition; C1 CSWeb access resolved to a scoped `supervisor-qa` role. **Phase 2 (Bluetooth hub)** spec + plan written, build deferred (D7). Epic 8 (E8-SUPERVISOR-001/-002).
- **CSWeb reporting views + static sync dashboard** — LIVE at `csweb.asiansocial.org/docs/dashboard.html` (Epic 8, E8-BI-001).
- **Board hygiene** — #712 + 9 Tagalog issues closed; open 40 → 31.
- Product Backlog updated (Epic 8 now In Progress; new headline). _S010 retro still pending (carries the E0-SCRUM-SYNC drift-fix item — this stale `sprint-current.md` is itself the exhibit)._

## Retrospective — Sprint 010

> 5-minute time-box. Four questions, fixed order. Written, not thought-through-only.

### 1. Did the sprint goal land? (yes / partial / no — one line why)

_TBD 2026-06-19._

### 2. What surprised me? (process, not work — max 3 bullets)

_TBD_

### 3. Deadline exposure check — D2 / D3 / Tranche slip days this sprint

_Informational only (out of Data Programmer scope per CSA D1–D6)._

### 4. One thing to change in Sprint 011

_TBD_
