---
type: weekly-status-report
week: 2026-04-13 to 2026-04-17
sprint: 001
author: Carl Patrick L. Reyes
audience: ASPSI Management Committee
status: DRAFT — finalize Fri Apr 17 PM
---

# Weekly Status — Week of Apr 13 → Apr 17, 2026

**From:** Carl Patrick L. Reyes — Data Programmer
**To:** ASPSI Management Committee
**Sprint:** 001 — Close F1 design and stand up a working F1 prototype
**Reporting period:** Apr 13 – Apr 17, 2026

---

## 1. This Week's Goal

> Finalize the F1 (Facility Head) data dictionary against decisions from the Apr 13 LSS meeting, and bring up a runnable F1 prototype in CSEntry covering the cover page and Section A so the team can see real CAPI data entry — not just a schema on paper.

## 2. Done This Week

- {Filled Friday: e.g. "F1 data dictionary v3 finalized — 11 records, ~952 fields, all six sanity-check items resolved with decisions from the Apr 13 LSS meeting (D2/D3)."}
- {e.g. "F1 dictionary opened in CSPro Designer, walked end-to-end, signed off internally for build."}
- {e.g. "F1 prototype application built in CSPro Designer covering Cover Page + Section A (Facility Head Profile), tested in CSEntry on Windows."}
- {e.g. "Skip-logic and validation specification document finalized and filed alongside the dictionary (D2/D3)."}

## 3. In Progress

- F1 prototype expansion to Sections B–H — targeted for Sprint 002 (Apr 20 – Apr 24).
- F2 (Healthcare Worker) data dictionary — generator authoring kicks off next week.

## 4. Blocked / Needs ASPSI

- **SJREB ethics clearance** — last status update? This is the long-pole dependency for any pretest with real respondents and is currently the single biggest risk to the D3 timeline. Requesting a status note for next week's report.
- {Add any decisions that came out of the Apr 13 LSS meeting that still need ASPSI follow-up — e.g. "Q121 dynamic value set scope: please confirm by Wed Apr 22 whether the hospital-vs-PCF switch should also apply to Q130/Q132."}
- {Any decisions deferred at the LSS meeting that need a written confirmation.}

## 5. Next Week Preview (Sprint 002 — Apr 20 → Apr 24)

- Extend the F1 prototype across all sections (B–H) with question text, skip logic, and FIELD_CONTROL block (consent + eligibility + GPS + AAPOR disposition codes).
- Begin F2 (Healthcare Worker) data dictionary generator, reusing the F1 helper library.
- Continue SJREB tracking and weekly D2/D3 deadline check-in.

## 6. Deliverables Snapshot

| ID | Title | Tranche | Original Due | Status | On Track? |
|---|---|---|---|---|---|
| D1 | Inception Report | T1 (15%) | 2025-12-12 | **Accepted** | ✓ |
| D2 | Survey materials & protocols (Survey Manual, SOPs, data collection tools) | T2 (30%) | 2026-02-13 | In Progress (extended timeline) | Yes — F1 dictionary and skip-logic spec advancing this deliverable |
| D3 | Pretested questionnaires + field operations manuals + training materials | T2 (30%) | 2026-03-13 | In Progress (extended timeline) | Conditional — gated by SJREB clearance for the pretest step |
| D4 | Pilot progress report | T3 (25%) | 2026-07-13 | Not Started | Yes — ~3 months runway |
| D5 | Training documentation | T4 (30%) | 2026-07-31 | Not Started | Yes |
| D6 | Final report + dissemination | T4 (30%) | 2026-08-13 | Not Started | Yes |

## 7. Risks Worth Flagging This Week

- **SJREB clearance delay** — no change in state this week, but every additional week without clearance compresses the pretest window. Requesting a status update from ASPSI ethics coordination.
- **Late questionnaire revisions** — risk reduced this week. The data dictionary is now generator-based (Python script), so any future question revisions can be absorbed by re-running the generator in minutes rather than reworking by hand.

## 8. Instrument States

| Instrument | State (Apr 17) | This-week movement |
|---|---|---|
| F1 — Facility Head | **Build (prototype)** | Advanced from Design to Build — dictionary signed off, working prototype standing up in CSEntry |
| F2 — Healthcare Worker | Source Captured | Generator authoring begins Sprint 002 |
| F3 — Patient | Source Captured | No movement — sequenced after F2 |
| F4 — Household | Source Captured | No movement — sequenced last (roster engine) |
| PLF — Patient Listing | Source Captured | No movement — implementation decision (CAPI vs paper) pending |

---

*This is a Carl-side weekly summary. For the full sprint backlog, epic-by-epic task tracking, and methodology documentation, the project knowledge base is available on request.*
