---
epic: 2
title: Survey Questionnaire Design & Dictionary
phase: per-instrument
status: in-progress
last_updated: 2026-04-10
---

# Epic 2 — Survey Questionnaire Design & Dictionary

Per-instrument design workstream covering questionnaire ingestion, data model specification, skip logic mapping, validation rule documentation, and schema corrections before build.

**Ties to Product Backlog:** [[../product-backlog#Epic 2 — Survey Questionnaire Design & Dictionary|PB Epic 2]]
**Methodology:** [[../../../../2_Areas/IT-Standards/templates/CAPI-Development-Workflow|CAPI Development Workflow]] Phases 1, 3, 4, 5

## Task conventions

- Task IDs: `E2-{instrument}-NNN` (e.g., `E2-F1-001`)
- Each instrument has a standard 10-task template — tasks common across all instruments use the same trailing number

## Standard per-instrument template

| # | Task | Phase |
|---|---|---|
| 001 | Source capture — questionnaire PDF ingested to `raw/` | 1 |
| 002 | Text extraction + wiki source page with section map | 1 |
| 003 | Data model generator authoring (Python script with helpers) | 3 |
| 004 | DCF v1 generation and first open in CSPro Designer | 3 |
| 005 | Skip logic mapping (every conditional jump documented) | 4 |
| 006 | Validation rule inventory (hard stops, soft warnings, display gates) | 4 |
| 007 | Cross-field consistency rules | 4 |
| 008 | Sanity check findings → bug list | 4 |
| 009 | Corrections applied to generator; DCF v2 regenerated | 5 |
| 010 | Designer validation + sign-off to enter Epic 3 (Build) | 5 |

---

## F1 — Facility Head Survey *(interviewer-administered, 34pp)*

**State:** Design — corrections in progress
**Scope:** 10 records · 649 fields · 166 questions · 4 validation tiers
**Reference doc:** `deliverables/CSPro/F1/F1-Skip-Logic-and-Validations.md`

- [x] **E2-F1-001** F1 questionnaire PDF ingested to `raw/` `status::done` `priority::critical`
- [x] **E2-F1-002** F1 text extraction + wiki source page with Section A–H map + secondary data page `status::done` `priority::critical`
- [x] **E2-F1-003** F1 `generate_dcf.py` authored with reusable helpers (`numeric`, `alpha`, `yes_no_item`, `select_one`, `select_all`, `uhc9_item`) + shared value-set constants (`YES_NO`, `YES_NO_DK`, `DICHOTOMOUS`, etc.) `status::done` `priority::critical` `estimate::2d`
- [x] **E2-F1-004** F1 DCF v1 generated: 10 records, 649 items; opens cleanly in CSPro Designer `status::done` `priority::critical`
- [x] **E2-F1-005** F1 skip logic walked for all 166 questions — full skip-logic table authored `status::done` `priority::critical` `estimate::1d`
- [x] **E2-F1-006** F1 validation rule inventory — hard stops, soft warnings, display gates all documented with paste-ready PROC snippets `status::done` `priority::critical` `estimate::1d`
- [x] **E2-F1-007** F1 cross-field consistency rules documented (e.g., tenure ≤ age − 15; if Q51 = No then Q52–Q78 must be blank) `status::done` `priority::critical`
- [x] **E2-F1-008** F1 sanity check — 6 DCF bugs surfaced and queued for Phase 5 correction `status::done` `priority::critical`
- [ ] **E2-F1-009** F1 apply 6 DCF bug fixes to `generate_dcf.py` and regenerate v2 `status::todo` `priority::critical` `estimate::1d`
  - Individual bug items tracked in `F1-Skip-Logic-and-Validations.md §DCF sanity-check findings`
  - **This is the next active task**
- [ ] **E2-F1-010** F1 DCF v2 opened in CSPro Designer, validated, bug list closed or explicitly deferred → sign-off to enter Epic 3 `status::todo` `priority::critical` `estimate::4h`

---

## F2 — Healthcare Worker Survey *(self-administered, 14pp)*

**State:** Source Captured
**Scope:** Sections A–J, self-administered mode (distinct from F1/F3/F4)

- [x] **E2-F2-001** F2 questionnaire PDF ingested to `raw/` `status::done` `priority::high`
- [x] **E2-F2-002** F2 text extraction + wiki source page with Section A–J map `status::done` `priority::high`
- [ ] **E2-F2-003** F2 `generate_dcf.py` authored (reuse F1 helpers where applicable) `status::todo` `priority::high` `estimate::1d`
- [ ] **E2-F2-004** F2 DCF v1 generated and opened in CSPro Designer `status::todo` `priority::high` `estimate::2h`
- [ ] **E2-F2-005** F2 skip logic walked (account for self-admin mode: no interviewer to interpret) `status::todo` `priority::high` `estimate::1d`
- [ ] **E2-F2-006** F2 validation rule inventory (self-admin affects soft warnings — respondent overrides differently) `status::todo` `priority::high` `estimate::1d`
- [ ] **E2-F2-007** F2 cross-field consistency rules `status::todo` `priority::high` `estimate::4h`
- [ ] **E2-F2-008** F2 sanity check findings → bug list `status::todo` `priority::high` `estimate::2h`
- [ ] **E2-F2-009** F2 corrections + DCF v2 regeneration `status::todo` `priority::high` `estimate::4h`
- [ ] **E2-F2-010** F2 Designer validation + sign-off `status::todo` `priority::high` `estimate::2h`

---

## F3 — Patient Survey *(interviewer-administered, 23pp, outpatient + inpatient)*

**State:** Source Captured
**Scope:** Sections A–L, dual-population eligibility

- [x] **E2-F3-001** F3 questionnaire PDF ingested `status::done` `priority::high`
- [x] **E2-F3-002** F3 text extraction + wiki source page with Section A–L map `status::done` `priority::high`
- [ ] **E2-F3-003** F3 `generate_dcf.py` authored `status::todo` `priority::high` `estimate::1d`
- [ ] **E2-F3-004** F3 DCF v1 generated and opened in Designer `status::todo` `priority::high` `estimate::2h`
- [ ] **E2-F3-005** F3 skip logic walked (dual-population eligibility — outpatient vs inpatient branches) `status::todo` `priority::high` `estimate::1d`
- [ ] **E2-F3-006** F3 validation rule inventory `status::todo` `priority::high` `estimate::1d`
- [ ] **E2-F3-007** F3 cross-field consistency rules `status::todo` `priority::high` `estimate::4h`
- [ ] **E2-F3-008** F3 sanity check findings → bug list `status::todo` `priority::high` `estimate::2h`
- [ ] **E2-F3-009** F3 corrections + DCF v2 regeneration `status::todo` `priority::high` `estimate::4h`
- [ ] **E2-F3-010** F3 Designer validation + sign-off `status::todo` `priority::high` `estimate::2h`

---

## F4 — Household Survey *(interviewer-administered, 26pp, new for Year 2)*

**State:** Source Captured
**Scope:** Sections A–Q, household roster with per-member sub-questionnaires — highest structural complexity

- [x] **E2-F4-001** F4 questionnaire PDF ingested `status::done` `priority::high`
- [x] **E2-F4-002** F4 text extraction + wiki source page with Section A–Q map `status::done` `priority::high`
- [ ] **E2-F4-003** F4 `generate_dcf.py` authored (adds roster cardinality handling — household member loop) `status::todo` `priority::high` `estimate::2d`
- [ ] **E2-F4-004** F4 DCF v1 generated and opened in Designer `status::todo` `priority::high` `estimate::4h`
- [ ] **E2-F4-005** F4 skip logic walked (per-member loops + household-level gates) `status::todo` `priority::high` `estimate::2d`
- [ ] **E2-F4-006** F4 validation rule inventory (roster-specific validations: max roster size, age/relation consistency, children cannot be pregnant) `status::todo` `priority::high` `estimate::1d`
- [ ] **E2-F4-007** F4 cross-field consistency rules (within-member + cross-member) `status::todo` `priority::high` `estimate::1d`
- [ ] **E2-F4-008** F4 sanity check findings → bug list `status::todo` `priority::high` `estimate::4h`
- [ ] **E2-F4-009** F4 corrections + DCF v2 regeneration `status::todo` `priority::high` `estimate::1d`
- [ ] **E2-F4-010** F4 Designer validation + sign-off `status::todo` `priority::high` `estimate::4h`

---

## PLF — Patient Listing Form *(recruitment form, 1pp)*

**State:** Source Captured

- [x] **E2-PLF-001** PLF form PDF ingested `status::done` `priority::medium`
- [x] **E2-PLF-002** PLF wiki source page `status::done` `priority::medium`
- [ ] **E2-PLF-003** Implementation decision: lightweight CAPI vs paper-only `status::todo` `priority::medium` `estimate::2h`
- [ ] **E2-PLF-004** If CAPI: `generate_dcf.py` + DCF v1 (minimal, single-record) `status::todo` `priority::medium` `estimate::4h`
- [ ] **E2-PLF-005** If CAPI: minimal skip logic + validation rules `status::todo` `priority::medium` `estimate::2h`
- [ ] **E2-PLF-006** If CAPI: Designer validation + sign-off `status::todo` `priority::medium` `estimate::1h`

## Notes

- F1 is the reference instrument — patterns established here flow into F2/F3/F4.
- F4 deliberately last because the roster engine benefits from all prior lessons.
- All generators share a common helper library (evolving in F1's `generate_dcf.py`) — each subsequent instrument should extract shared helpers into a reusable module.
