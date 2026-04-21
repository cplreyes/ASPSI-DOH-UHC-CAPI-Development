---
sprint: 002
start: 2026-04-20
end: 2026-04-24
status: active
sprint_length: 1 week (5 working days)
deliverable_anchor: D2 / Tranche 2 (40% due 2026-04-24)
---

# Sprint 002 — Close F1 design, open F3/F4 logic-pass, submit Tranche 2 honestly

## Sprint Goal

> **Close F1 design cleanly, open the logic-pass gap on F3 and F4, and submit Tranche 2 as an honest status-to-date package.** F1 Designer sign-off (E2-F1-010) formalizes F1 as Design-complete. F3 skip-logic + validation spec (full) + F4 A–F slice bring both instruments up to the `logic-pass-before-build` standard before any FMF build work starts. Tranche 2 cover letter is reframed as extended-window progress-to-date, not a "D2 complete" claim — Juvy/Dr Claro route accordingly. Late-delivery penalty (1%/day, CSA §5) is a status checkpoint, not a forcing function to cut design steps.

## Committed Items

### Carry-forward from Sprint 001 (priority order)

- [ ] **E2-F1-010** F1 DCF opened in CSPro Designer, full validation walkthrough, bug list closed or explicitly deferred, sign-off note recorded `status::todo` `priority::critical` `estimate::4h`
- [ ] **E0-010** Define weekly status update format for ASPSI Management Committee `status::todo` `priority::high` `estimate::2h`
  - Scope updated per Apr 13 meeting notes: format is for Carl → Juvy / Dr Claro / Dr Paunlagui, not Carl → DOH directly.

> **E3-F1-001 (FMF Section A layout) deferred to Sprint 003.** Rationale: FMF work needs an upstream form-layout plan (per CSPro CAPI Strategies — forms per subsection, no scrolling, roster-scrolls-alone). Starting FMF this week without that plan would be the actual shortcut. Form-layout plan becomes a Sprint 003 prerequisite across F1/F3/F4.

### Recurring (every sprint)

- [ ] **E0-020** SJREB application status check via ASPSI `status::in-progress` `priority::critical`
- [ ] **E0-032** Track D2/D3/Tranche 2 deadline exposure this week `status::in-progress` `priority::high`

### New for Sprint 002

- [ ] **E0-032a** Triage DOH-PMSMD feedback on matrices (arrives Apr 20 Mon); route any requested revisions into F1/F2 build state; confirm Tranche 2 submission package with Juvy by Apr 23 `status::todo` `priority::critical` `estimate::TBD`
- [x] **E2-F3-001** F3 skip-logic + validation spec — full instrument, mirroring `F1-Skip-Logic-and-Validations.md` shape. Output: `deliverables/CSPro/F3/F3-Skip-Logic-and-Validations.md` (1133 lines, status: reviewed 2026-04-21; 14 sanity findings, skip-logic + validations for all 12 sections A–L, 15 CSPro PROC templates, 6 originally-open questions dispositioned — 1 routed to Juvy for Q31 IP_GROUP, 5 closed as spec-decisions). F3 Build-ready unblocked. `status::done` `priority::critical` `actual::~0h (spec already authored; review/edit pass only)`
- [x] **E2-F4-001** F4 skip-logic + validation spec — **full instrument A–Q** (rescoped from A–F slice after F3 closed early). Output: `deliverables/CSPro/F4/F4-Skip-Logic-and-Validations.md` (904 lines, status: draft 2026-04-21; 13 sanity findings including 2 P1 schema gaps — `C_HOUSEHOLD_ROSTER` and `J_HEALTH_SEEKING` must be made repeating in `generate_dcf.py` before CAPI build; skip-logic tables for all 17 sections; validations 3.1–3.18 with HARD/SOFT/GATE; 11 CSPro PROC templates including roster loop, WHO expenditure grid, catastrophic-expenditure check, bill-recall chain; 8 open questions dispositioned — 3 routed to ASPSI, 5 spec-decisions with override clause). Mirrors F3 spec shape. `status::done` `priority::critical` `actual::~3h (Apr 21 afternoon)`

### Stretch (not committed)

- [ ] **F2 PWA pilot-readiness decision** — per `deliverables/F2/PWA/app/NEXT.md`: pick one of pilot now / close-deferred M11 items / move to M12 F3-F4 parity. Decision itself is ~30m; follow-through TBD depending on path. `status::todo` `priority::medium` `estimate::30m decision`

## Sprint Backlog Sizing

| Class | Items | Estimate |
|---|---|---|
| **Committed (must-finish)** | E2-F1-010, E0-010, E0-020, E0-032, E0-032a, **E2-F3-001 (done Day 2)**, **E2-F4-001 (done Day 2)** | ~6h remaining + E0-032a unbounded |
| **Stretch** | F2 PWA pilot-readiness decision | 30m decision + follow-through TBD |

> Capacity: ~25h solo-dev week. **E2-F3-001 and E2-F4-001 both closed Day 2** — F3 was already authored (1h review/disposition pass) and F4 compressed to ~3h by mirroring the F3 shape onto the Apr 20 F4 DCF inventory. Remaining hard commits: **F1 sign-off 4h + E0-010 2h**, before E0-032a. 3 days remaining (Wed–Fri) with ~19h of capacity after logic-pass work. Use the released capacity to: (a) route the two P1 F4 schema gaps (`C_HOUSEHOLD_ROSTER` / `J_HEALTH_SEEKING` repeating) as `generate_dcf.py` patches during this sprint, or (b) pull E3-F1-001 FMF Section A layout forward if the form-layout plan materializes mid-sprint. Decision depends on E0-032a size.

## Daily Notes

### 2026-04-20 (Mon)

- **Sprint 002 kickoff carry-forward from Sprint 001 retro Q4:** Require an on-disk artifact reference (file path at minimum, commit SHA preferred) before flipping any `status::done`. No status flip on meeting attendance, verbal confirmation, or "should be done by now." Applies to every item, including recurring ones.

### 2026-04-21 (Tue)

- **Sprint 002 scope reshaped Day 2 to anchor on quality, not payment window.** Initial plan deferred F3/F4 skip-logic specs to Sprint 003 to protect Tranche 2; Carl pushed back — "I don't want shortcuts, quality of development is my prio." Committed list now includes E2-F3-001 (full F3 spec) and E2-F4-001a (F4 A–F slice); E3-F1-001 (FMF Section A) deferred to Sprint 003 because FMF needs an upstream form-layout plan, not a rushed start. Tranche 2 cover letter reframed as status-to-date, not "D2 complete." Capacity is full-to-overflow by design; if E0-032a goes heavy, E2-F4-001a slides before F3 spec integrity is touched.
- **E2-F3-001 closed Day 2 — discovered spec was already authored.** On starting the F3 logic-pass, found `deliverables/CSPro/F3/F3-Skip-Logic-and-Validations.md` already existed at 1133 lines (status: draft) covering all 12 sections A–L with 14 sanity findings, skip-logic tables, HARD/SOFT/GATE validations, and 15 CSPro PROC templates. Auto-standup narrative said "pending" because the Python generator reads sprint-current.md + product-backlog.md but never reads git log — same failure mode the Sprint 001 retro flagged. Reviewed spec against the Apr 20 questionnaire + verified DCF state (15 records / 818 items, matches spec); added item-count drift provenance (387 Apr 08 → 818 Apr 20) and dispositioned the 6 "open" questions: only **Q31 IP_GROUP** needs Juvy (coded list or confirm alpha); five others were already internal spec-decisions, now marked as such with ASPSI override reserved. Flipped `status: draft` → `status: reviewed`. E2-F4-001 **rescoped A–F → full A–Q** given ~10h of released capacity, with A–M/N–Q fallback split kept in reserve.
- **Process flag for Sprint 002 retro:** auto-standup generator (`.claude/scripts/generate_standup.py`) doesn't read git log or file mtimes in `deliverables/` — narrative lags actual artifacts. Second occurrence. Fix for Sprint 003: either extend the generator to diff since last standup, or make it the Day 1 ritual to manually grep for artifact drift before writing the Today-plan table.
- **E2-F4-001 also closed Day 2 — ~3h, not 10–14h.** Wrote `deliverables/CSPro/F4/F4-Skip-Logic-and-Validations.md` full A–Q (904 lines) in one pass, mirroring the F3 spec shape onto the Apr 20 F4 DCF inventory (21 records / 611 items covering Q1–Q202). Two **P1 schema gaps** surfaced and logged as sanity findings: `C_HOUSEHOLD_ROSTER` and `J_HEALTH_SEEKING` are both `occurrences.maximum = 1` in the current dcf but source describes both as per-member loops — must be patched in `generate_dcf.py` before CAPI build. 3 questions batched to ASPSI (Q15 IP_GROUP list — shared with F3 Q31 ask; roster max-occ cap; Section J per-member scope); 5 spec-decisions documented with override clauses.
- **Sprint 002 capacity re-forecast after Day 2:** both F3 and F4 logic-pass work closed; ~19h capacity remaining across Wed–Fri. Options for the released capacity: (a) patch `generate_dcf.py` for the 2 F4 schema gaps, (b) pull E3-F1-001 FMF Section A forward if form-layout plan materializes, (c) absorb DOH-PMSMD feedback (E0-032a) without deadline pressure. Not committing ahead of Wed's E0-032a triage.

## Retrospective — Sprint 002 (fill in 2026-04-24)

> 5-minute time-box. Four questions, fixed order. Written, not thought-through-only.
> Don't write self-congratulation; only write what changes next week's behavior.

### 1. Did the sprint goal land? (yes / partial / no — one line why)

_TBD 2026-04-24_

### 2. What surprised me? (process, not work — max 3 bullets)

_TBD 2026-04-24_

### 3. Deadline exposure check — D2 / D3 / Tranche 2 slip days this week

> The 1%/day penalty (CSA §5) means deadline exposure is the metric, not velocity.
> Answer explicitly even when the answer is "0 days, held steady."

_TBD 2026-04-24_

### 4. One thing to change in Sprint 003

> Exactly one. Not a wishlist. Smallest concrete behavior change.
> If nothing needs changing, write "none — keep the same shape."
> Carry this into Sprint 003's Daily Notes as the first entry so it stays visible.

_TBD 2026-04-24_

## Definition of Done — Sprint 002

- [ ] **Tranche 2 (40%) submission package** submitted via DOH route by EOD Fri 2026-04-24, framed as *status-to-date against an extended D2/D3 window* — not "D2 complete." Cover-letter framing confirmed with Juvy before send. Submission entry logged in `log.md`.
- [ ] **E2-F1-010** closed: F1 DCF walkthrough complete in CSPro Designer, bug list closed or deferred with rationale, sign-off note appended to `log.md`.
- [x] **E2-F3-001** closed 2026-04-21: F3 skip-logic + validation spec reviewed against Apr 20 questionnaire + DCF state, 6 open questions dispositioned (Q31 IP_GROUP routed to Juvy; 5 closed as spec-decisions), `status: reviewed` at `deliverables/CSPro/F3/F3-Skip-Logic-and-Validations.md`. F3 Build-ready.
- [x] **E2-F4-001** closed 2026-04-21: F4 skip-logic + validation spec written full A–Q at `deliverables/CSPro/F4/F4-Skip-Logic-and-Validations.md` (904 lines, draft). 2 P1 schema gaps flagged for `generate_dcf.py` (roster + health-seeking must be repeating records). 3 questions routed to ASPSI (Q15 IP_GROUP list, roster max-occ, Section J loop scope); 5 spec-decisions documented.
- [ ] **E0-032a** closed: DOH-PMSMD matrix feedback triaged; any requested revisions reflected in F1/F2 build state or explicitly deferred with rationale recorded.
- [ ] **Sprint 002 retrospective** (4 questions) filled in `sprint-current.md` by EOD Fri 2026-04-24; sprint archived to `scrum/sprints/sprint-002.md`; `sprint-current.md` reset for Sprint 003.
