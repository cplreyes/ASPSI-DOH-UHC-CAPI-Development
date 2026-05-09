---
sprint: 005
plan_status: confirmed
authored: 2026-05-10
opens: 2026-05-11
closes: 2026-05-15
---

# Sprint 005 — Plan (confirmed)

Sprint 005 commitments and their state at sprint open. This plan is the canonical reference for the Sprint 005 Day 1 framing audit (`E0-009` sub-task #1).

## Anchor

Close UHC Plan 1 (Phase 1 sync mechanics last 5%) + plan Phase 2 + run Day-1 issue-triage ritual before goal work + close Sprint 004 carries. Plan 1 reaches end-to-end-with-sync state by sprint close; backlog hygiene caught up after a month of accumulating without explicit triage.

## Slot state at sprint open

Per Project #8 ([github.com/users/cplreyes/projects/8](https://github.com/users/cplreyes/projects/8)), sprint-005 slot snapshot 2026-05-10:

| Status | Count | Items |
|---|---|---|
| **Done** | 15 | E4-APRT-037, E4-APRT-041, E4-APRT-042, E4-APRT-043, E4-APRT-044, E4-APRT-045, E4-APRT-048, E4-APRT-049, E4-APRT-049a..e (5), E4-APRT-050, E4-APRT-051 |
| **Todo** | 4 | E3-F1-088, E3-F1-PHASE2-PLAN, E4-PWA-014, E4-PWA-015 |

The 15 Done items shipped Sat 2026-05-09 inter-sprint via PR #136 (`9bab42b`). They were tagged `sprint-005` via `Closes #N` trailers at PR merge time. **Day 1 framing audit (E0-009 sub-task #1)** decides whether to leave them in sprint-005 (intentional early-grind framing) or rebill to Sprint 004 Inter-Sprint Activity. Both readings are defensible; the artifact-of-record decision belongs to Carl, not the auto-sync.

## Confirmed commitments (~21h base, ~25h capacity → ~4h headroom)

| ID | Title | Source | Est | Pri |
|---|---|---|---|---|
| **E3-F1-088** | Phase 1 sync mechanic resolution — syncdata external-dict + CSDB binding | UHC build worktree carry | 6h | critical |
| **E3-F1-PHASE2-PLAN** | Phase 2 plan + scope confirmation (PLF + F3 + F4_listing + F4 + supervisor menu + EA fence + daily audit Slack) | UHC build worktree carry | 3h | high |
| **E0-009** | Issue-triage Day 1 ritual (slot framing audit + R2/unscheduled disposition + Slack summary) | New for Sprint 005 (per Sprint 004 retro Q4) | 3h | critical |
| **E3-F1-001** | F1 FMF Section A layout in CSPro Designer | Sprint 004 carry | 4h | high |
| **E4-APRT-035** | Cross-platform QA — E2 Firefox + E3 Edge close-out + PR #54 merge | Sprint 004 carry (E1/E4/E5 done Day 1) | 3h | high |
| **E4-PWA-014** | Verify CF Pages auto-deploy resolution (#34 — likely state-confirmation close) | Sprint 004 carry | 30m–3h | high |
| **E4-PWA-015** | Lower Worker PBKDF2 default to 100k (#35) | Sprint 004 carry | 1h | medium |
| **Total** | | | **~21h** | |

## Stretch (pull if base clears mid-sprint)

| ID | Title | Est | Pri | Note |
|---|---|---|---|---|
| E3-F1-011 | Filipino translations for all question labels + option text | 4h | high | Sprint 006 candidate; pull if multilingual is priority |
| E3-F1-012 | Multi-language switching (`setlanguage`, language-select on cover) | 3h | high | Sprint 006 candidate |
| E3-F1-020 | Master skip gates (section-level eligibility filters) | 4h | high | Sprint 006 candidate; pull if skip gates are priority |

Headroom is ~4h, so at most one stretch item. Pull rule: pick whichever is on Carl's mind Day 5 — multilingual support or skip gates. If neither, leave in Sprint 006 as currently slotted.

## Carry rules (entering from Sprint 004)

- **E3-F1-001** (F1 FMF Designer pass) — three-sprint anchor item now becomes a single-sprint commit; Designer-side work, no upstream gates.
- **E4-APRT-035** cross-env (E2 Firefox + E3 Edge) — risk is mostly visual (focus rings, native-control rendering); time-box at 3h, defer further if a structural bug surfaces.
- **E4-PWA-014** (CF Pages auto-deploy) — auto-deploy fired post-PR #136 merge 2026-05-09; verify with two test pushes (one staging, one main) and close. Fall back to investigation only if regression returns.
- **E4-PWA-015** (PBKDF2 cap) — config change + smoke; should be a 1h close.
- **UHC build worktree** — `feature/uhc-survey-system-build` already at Plan 1 ~95%. Sync close-out (E3-F1-088) finishes the chain. Phase 2 plan (E3-F1-PHASE2-PLAN) is paper, not code.

## Dependencies entering Sprint 005

- **External (still pending, not blocking):** PSGC value sets blocked on ASPSI; tablets blocked on procurement; SJREB clearance via PI lane. None of Sprint 005 work depends on these.
- **Internal — Myra's Survey Manual edit pass** is open per `project_survey_manual_bundle_ingest_2026_05_07`; some Phase 2 scope decisions (F3 listing-app architecture, case-ID final form, F4 barangay listing) wait on her pass. E3-F1-PHASE2-PLAN scope can proceed *with these items marked as held* — Phase 2 plan doc explicitly flags them.

## Out of Sprint 005 scope

- **F3/F4 build kickoff** — waits on Sprint 008+ once F1 patterns proven (per sprint-007-plan.md).
- **CSWeb stand-up** — waits until F1 build artifact stable (Phase 1 sync close-out is prerequisite).
- **Hard validations + soft validations + display gates + dynamic value sets + cross-field consistency** — Sprint 007 work per sprint-007-plan.md.
- **Filipino translations / multi-lang switching / master skip gates** — Sprint 006 base (only pulled to Sprint 005 as stretch headroom permits).
