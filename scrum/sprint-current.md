---
sprint: 001
start: 2026-04-13
end: 2026-04-17
status: active
sprint_length: 1 week (5 working days)
deliverable_anchor: D2 / D3 (extended timeline)
---

# Sprint 001 — Close F1 Design, Unblock F1 Build, Kick Off F2

## Sprint Goal

> **Get F1 out of Design and into Build-ready by Friday**: resolve the six open F1 questions at today's LSS meeting, reconcile DCF v2 against those decisions, complete the CSPro Designer walkthrough, and sign off Epic 2 for F1 so Epic 3 (F1 build) can start in Sprint 002.
>
> **Stretched 2026-04-15:** Kick off F2 (Google Forms track) in parallel. F1 sign-off is not a hard gate — F2's Google Forms path doesn't reuse F1's CSPro patterns, so the two tracks are independent. Sprint 001 now ships the F2 tooling decision memo + cover-block rewrite draft; spec extraction carries into Sprint 002.

Why this goal: F1 is the reference instrument for F3/F4 CSPro builds — every day F1 sits in Design also delays the downstream CSPro pipeline. The six open questions have been frozen for ~3 days waiting on the Apr 13 LSS meeting. F2 is now recognized as a special case (Google Forms primary, optional deferred CSPro encoder) and can run in parallel without waiting on F1.

## Committed Items

<!-- IDs reference epic files in scrum/epics/. Keep statuses in sync there. -->

### Epic 0 — PM & Stakeholder (recurring + one-off)

- [ ] **E0-001** Sprint 001 planning ceremony — set goal, dates, commit items `status::in-progress` `priority::high`
- [ ] **E0-020** SJREB application status check via ASPSI (carry into every sprint until clearance) `status::in-progress` `priority::critical`
- [ ] **E0-032** Track D2/D3 deadline exposure this week `status::in-progress` `priority::high`
- [ ] **E0-060** Attend Apr 13 LSS meeting (3:00 PM); capture decisions on the 6 open F1 items into a meeting note in `scrum/standups/` and feed back to F1 spec `status::todo` `priority::critical` `estimate::3h`

### Epic 2 — F1 Design closeout

- [x] **E2-F1-009** Author `generate_dcf.py` and emit `FacilityHeadSurvey.dcf` covering Q1-Q166 across 15 records `status::done` `priority::critical`
  - Built 2026-04-14. Earlier scrum entries (Apr 11) claiming this was done were premature — no generator existed in the repo. Reconstructed from scratch using `raw/CSPro-Data-Dictionary/FacilityHeadSurvey.dcf` (Carl's manual Q1-Q8 scaffold) as format reference and `F1-Skip-Logic-and-Validations.md` for canonical item names. Output: 15 records, 657 items. Secondary-data records (SEC_HOSP_CENSUS, SEC_HCW_ROSTER, SEC_YK_SERVICES, SEC_LAB_PRICES) intentionally left as empty stubs pending LSS decision.
- [ ] **E2-F1-009b** Reconcile DCF with LSS-meeting decisions on the 6 open items (Q63 day vs month, SECONDARY_DATA structure, NBB split, Q31 NA-skip intent, Q166 nurse list, Q121 dynamic value set) `status::todo` `priority::critical` `estimate::4h`
  - **REOPENED 2026-04-14.** Apr 13 LSS meeting did NOT actually discuss the 6 open items (correction from Carl). The 6 items are encoded as `PENDING_LSS_*` constants in `generate_dcf.py` with default assumptions; flipping any constant regenerates the affected schema. Blocked until the items land on an LSS agenda.
- [ ] **E2-F1-010** F1 DCF opened in CSPro Designer, full validation walkthrough, bug list closed or explicitly deferred, sign-off note recorded → enters Epic 3 `status::todo` `priority::critical` `estimate::4h`
  - Generator + DCF in place 2026-04-14. Designer walkthrough next.

### Epic 3 — F1 Build kickoff (promoted from stretch 2026-04-13)

- [ ] **E3-F1-001** Create `FacilityHeadSurvey.fmf`; lay out Section A (Identification & Cover Page) only `status::todo` `priority::high` `estimate::4h`
  - Promoted from stretch to committed on 2026-04-13 after F1 design closed clean. Targets Wednesday/Thursday once E2-F1-010 sign-off is in.

### Epic 2 — F2 Google Forms track kickoff (added 2026-04-15)

- [x] **E2-F2-011** F2 Tooling & Access Model Decision Memo drafted (8 decisions for ASPSI) `status::done` `priority::critical`
  - Drafted 2026-04-15. Deliverable at `deliverables/F2/F2-0_Tooling-and-Access-Model-Decision-Memo.md`. Carl to send to ASPSI in parallel with build work; recommended defaults proceed on the build side while decisions are in flight.
- [x] **E2-F2-012** F2 cover-block rewrite draft (consent, duration, FIELD CONTROL, facility ID) for ASPSI review `status::done` `priority::critical`
  - Drafted 2026-04-15 at `deliverables/F2/F2-Cover-Block-Rewrite-Draft.md`. 8 cover blocks covered; flags SJREB consent form, completion time, raffle applicability, and facility master list decisions for ASPSI.
- [x] **E2-F2-013** F2 spec extraction (questionnaire body Sections A–J → CSV/MD) `status::done` `priority::critical` `estimate::1d`
  - Drafted 2026-04-15 at `deliverables/F2/F2-Spec.md`. 114 items, verbatim labels, Google Forms risks consolidated (18 SECTION, 9 SPLIT). Pulled from stretch into committed-done on Day 3. Feeds E2-F2-014 next.

### Epic 0 — Process scaffolding (stretch)

- [ ] **E0-010** Define weekly status update format for ASPSI Management Committee — one-page template, paste-ready `status::todo` `priority::high` `estimate::2h`
  - Stretch — useful regardless of sprint outcome; sets up E0-011 next sprint.

## Sprint Backlog Sizing

| Class | Items | Estimate |
|---|---|---|
| **Committed (must-finish)** | E0-001, E0-020, E0-032, E0-060, E2-F1-010, E3-F1-001, E2-F2-012 | ~13h discretionary + recurring |
| **Blocked** | E2-F1-009b (awaiting LSS decision on 6 open items) | ~4h when unblocked |
| **Stretch** | E0-010, E2-F2-013 | +2h + 1d |
| **Already done** | E2-F1-009 (Apr 14 — generator + DCF built from scratch), E0-060 (Apr 13 PM), E2-F2-011 (Apr 15 — F2 tooling memo) | — |

Solo-dev capacity check: 5 working days × ~5h focused work = ~25h. Day 2 closed E2-F1-009. Day 3 (Apr 15) closed E2-F2-011 (F2 tooling memo). E2-F1-009b remains blocked until LSS decides the 6 items; defaults are encoded as `PENDING_LSS_*` constants so the DCF still loads. Remaining committed work: E2-F1-010 (Designer walkthrough), E3-F1-001 (FMF kickoff), E2-F2-012 (F2 cover-block rewrite draft). Stretch: E2-F2-013 (F2 spec extraction — may slip to Sprint 002).

## Daily Notes

<!-- Mid-sprint observations that aren't standup material. Append below. -->

### 2026-04-13 (Mon)
- Sprint 001 kickoff. Pre-sprint context brief was filed Apr 10 standup.
- LSS meeting at 3:00 PM is the gating event for E2-F1-009b — until decisions land, E2-F1-009b cannot start.
- **LSS meeting concluded.** No schema changes required from any of the 6 open F1 items. DCF v2 stands as the final F1 dictionary. E2-F1-009b closed; E2-F1-010 unblocked for Tuesday; E3-F1-001 promoted from stretch to committed. Sprint 001 is now poised to overshoot its goal.

### 2026-04-14 (Tue)
- **Correction to yesterday's note**: Apr 13 LSS meeting did not actually discuss the 6 open F1 items. E2-F1-009b is reopened and blocked.
- **Audit finding**: the prior scrum narrative claimed `generate_dcf.py` existed and a 952-item DCF was generated Apr 11. Reality on disk: only Carl's manual ~105-item scaffold at `raw/CSPro-Data-Dictionary/FacilityHeadSurvey.dcf`, no Python generator. E2-F1-009 was actually the work done today.
- **Built `deliverables/CSPro/F1/generate_dcf.py` from scratch** using the manual scaffold for Q1-Q8 conventions and `F1-Skip-Logic-and-Validations.md` for canonical item names across Q9-Q166. Output: `FacilityHeadSurvey.dcf` with 15 records, 657 items. Secondary-data records left as empty stubs pending LSS. The 6 open items are encoded as `PENDING_LSS_*` constants — flipping any constant + rerun regenerates affected schema.
- Moved `F1_clean.txt` out of `/raw/` to `deliverables/CSPro/F1/inputs/` (not an ASPSI source — internal text extraction).
- Next: E2-F1-010 Designer walkthrough on the freshly generated DCF.

### 2026-04-15 (Wed)
- **F2 scope decisions locked in.** F2 is officially a special case with three capture paths (Google Forms primary, paper→Forms encoding fallback, optional deferred CSPro encoder). F1 sign-off is NOT a hard gate for starting F2. Scheduled the CSPro-F2 track as an optional late build conditional on F2 Google Forms test outcomes.
- **Contradiction found and resolved:** the April 8 F2 PDF is authored using the interviewer-administered template (read-aloud consent, FIELD CONTROL enumerator block, 1.5-hour interview framing). IR says self-admin. Resolution (per Carl): the PDF is mislabeled/stale; ASPSI needs to rewrite the cover blocks. Carl will draft the rewrite to unblock the build. Added as E2-F2-012.
- **F2-0 Tooling & Access Model Decision Memo drafted** (`deliverables/F2/F2-0_Tooling-and-Access-Model-Decision-Memo.md`). 8 decisions for ASPSI: platform, access model, reminder cadence, facility ID, PSGC dropdowns, paper fallback, staff encoder workflow, response custody. Carl to send to ASPSI in parallel with build work; recommended defaults proceed on the build side.
- **Epic 2/3 files updated** with F2 Google Forms track (`E2-F2-011..018` design, `E3-F2-GF-001..015` build) and deferred CSPro track marked `status::deferred`. PB updated to reflect F2 special-case status.
- Next: draft E2-F2-012 cover-block rewrite text today or tomorrow; E2-F2-013 spec extraction as stretch.
- **E2-F2-013 closed same day.** Full body spec at `deliverables/F2/F2-Spec.md` — 114 items verbatim with original PDF question numbers, 18 SECTION + 9 SPLIT Google Forms risks flagged, 6 open items routed to ASPSI. Sprint 001 has now overdelivered on the F2 track.

## Retrospective — Sprint 001 (fill in 2026-04-17)

> 5-minute time-box. Four questions, fixed order. Written, not thought-through-only.
> Don't write self-congratulation; only write what changes next week's behavior.

### 1. Did the sprint goal land? (yes / partial / no — one line why)

_(answer here)_

### 2. What surprised me? (process, not work — max 3 bullets)

-
-
-

### 3. Deadline exposure check — D2 / D3 slip days this week

> The 1%/day penalty (CSA §5) means deadline exposure is the metric, not velocity.
> Answer explicitly even when the answer is "0 days, held steady."

- **D2 exposure:** ___ days (Δ from last week: ___)
- **D3 exposure:** ___ days (Δ from last week: ___)

### 4. One thing to change in Sprint 002

> Exactly one. Not a wishlist. Smallest concrete behavior change.
> If nothing needs changing, write "none — keep the same shape."
> Carry this into Sprint 002's Daily Notes as the first entry so it stays visible.

-

## Definition of Done — Sprint 001

- [ ] All six F1 LSS-meeting questions have a recorded decision (in code comment, log entry, or wiki)
- [ ] DCF v3 (or confirmed v2) opens cleanly in CSPro Designer with no unresolved bug-list items
- [ ] F1 sign-off note appended to `log.md` declaring Epic 2/F1 closed and Epic 3/F1 ready to start
- [ ] Sprint 002 planning happens Friday Apr 17 PM or Monday Apr 20 AM
