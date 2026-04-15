---
epic: 2
title: Survey Questionnaire Design & Dictionary
phase: per-instrument
status: in-progress
last_updated: 2026-04-15
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

**State:** Design — Designer walkthrough in progress (E2-F1-010); E2-F1-009b reopened pending LSS
**Scope:** 15 records · 657 fields · 166 questions · 4 validation tiers (4 secondary-data records empty pending LSS)
**Reference doc:** `deliverables/CSPro/F1/F1-Skip-Logic-and-Validations.md`

- [x] **E2-F1-001** F1 questionnaire PDF ingested to `raw/` `status::done` `priority::critical`
- [x] **E2-F1-002** F1 text extraction + wiki source page with Section A–H map + secondary data page `status::done` `priority::critical`
- [x] **E2-F1-003** F1 `generate_dcf.py` authored with reusable helpers (`numeric`, `alpha`, `yes_no_item`, `select_one`, `select_all`, `uhc9_item`) + shared value-set constants (`YES_NO`, `YES_NO_DK`, `DICHOTOMOUS`, etc.) `status::done` `priority::critical` `estimate::2d`
- [x] **E2-F1-004** F1 DCF v1 generated: 10 records, 649 items; opens cleanly in CSPro Designer `status::done` `priority::critical`
- [x] **E2-F1-005** F1 skip logic walked for all 166 questions — full skip-logic table authored `status::done` `priority::critical` `estimate::1d`
- [x] **E2-F1-006** F1 validation rule inventory — hard stops, soft warnings, display gates all documented with paste-ready PROC snippets `status::done` `priority::critical` `estimate::1d`
- [x] **E2-F1-007** F1 cross-field consistency rules documented (e.g., tenure ≤ age − 15; if Q51 = No then Q52–Q78 must be blank) `status::done` `priority::critical`
- [x] **E2-F1-008** F1 sanity check — 6 DCF bugs surfaced and queued for Phase 5 correction `status::done` `priority::critical`
- [x] **E2-F1-009** F1 `generate_dcf.py` authored from scratch + `FacilityHeadSurvey.dcf` emitted (Q1-Q166 across 15 records) `status::done` `priority::critical` `estimate::1d`
  - Built 2026-04-14. Earlier scrum entries claiming Apr 11 completion were premature — no generator existed in the repo before today. Reconstructed using `raw/CSPro-Data-Dictionary/FacilityHeadSurvey.dcf` (Carl's manual Q1-Q8 scaffold) for format conventions and `F1-Skip-Logic-and-Validations.md` for canonical item names. Output: 15 records, 657 items. Secondary-data records (SEC_HOSP_CENSUS, SEC_HCW_ROSTER, SEC_YK_SERVICES, SEC_LAB_PRICES) intentionally left as empty stubs — populated once LSS decides the SECONDARY_DATA structure.
- [ ] **E2-F1-009b** Reconcile DCF with LSS-meeting decisions on the 6 open items (Q63 day vs month, SECONDARY_DATA structure, NBB split, Q31 NA-skip intent, Q166 nurse list, Q121 dynamic value set) — patch `PENDING_DESIGN_*` constants in `generate_dcf.py` + regenerate `status::blocked` `priority::critical` `estimate::4h`
  - **REOPENED 2026-04-14.** Apr 13 LSS meeting did NOT actually discuss the 6 open items (correction from Carl on 2026-04-14). Defaults are encoded as `PENDING_DESIGN_Q63_USE_DAY_BUCKETS`, `PENDING_DESIGN_SECONDARY_DATA_AS_STUBS`, `PENDING_DESIGN_NBB_SPLIT_BY_TIER`, `PENDING_DESIGN_Q31_NA_SKIPS`, `PENDING_DESIGN_Q166_NURSES_INCLUDE_AUDITS`, `PENDING_DESIGN_Q121_DYNAMIC_VALUE_SET` in `generate_dcf.py`. Blocked until items land on an LSS agenda.
- [ ] **E2-F1-010** F1 DCF opened in CSPro Designer, validated, bug list closed or explicitly deferred → sign-off to enter Epic 3 `status::todo` `priority::critical` `estimate::4h`
  - **Sprint 001 commitment.** Generator + DCF in place 2026-04-14; Designer walkthrough next.

---

## F2 — Healthcare Worker Survey *(self-administered, 14pp)*

**State:** Design — Google Forms track kickoff 2026-04-15
**Primary mode:** Self-administered via **Google Forms** (3-day window per HCW). Paper fallback encodes back into the same Form. See `memory/project_f2_capture_modes.md`.
**Special case:** F2 does **NOT** flow through the standard DCF pipeline. The Google Forms path is the primary build; the CSPro DCF tasks below are deferred as an **optional late track** (only built if F2 Google Forms testing surfaces a need for a CSPro encoder variant).
**Reference doc:** `deliverables/F2/F2-0_Tooling-and-Access-Model-Decision-Memo.md`

### Google Forms design track *(PRIMARY)*

- [x] **E2-F2-001** F2 questionnaire PDF ingested to `raw/` `status::done` `priority::high`
- [x] **E2-F2-002** F2 text extraction + wiki source page with Section A–J map `status::done` `priority::high`
- [x] **E2-F2-011** F2 Tooling & Access Model Decision Memo drafted (8 decisions: platform, access model, reminders, facility ID, PSGC, paper fallback, encoding workflow, custody) `status::done` `priority::critical`
  - Drafted 2026-04-15 at `deliverables/F2/F2-0_Tooling-and-Access-Model-Decision-Memo.md`. Carl to send to ASPSI (Dr. Claro, Merlyne, Mgmt Committee) in parallel with build work. Recommended defaults proceed on the build side while decisions are in flight.
- [x] **E2-F2-012** F2 cover-block rewrite draft — consent form (remove "read aloud"), interview duration, FIELD CONTROL block removal/replacement, facility/geographic ID block. Draft for ASPSI/Dr. Claro review. `status::done` `priority::critical`
  - Drafted 2026-04-15 at `deliverables/F2/F2-Cover-Block-Rewrite-Draft.md`. Covers 8 cover blocks (title, consent header, PART I information, contact info, PART II consent certificate, FIELD CONTROL, facility/geographic ID, transition). Flags ASPSI decisions needed on click-through consent for SJREB, completion-time estimate, raffle applicability, FIELD CONTROL removal, and facility master list workflow. Carl to send to Dr. Claro + Merlyne for review; build proceeds on questionnaire body in parallel.
- [x] **E2-F2-013** F2 spec extraction — questionnaire body (Sections A–J) → structured CSV/MD (section, item #, verbatim text, type, choices, required, skip-to, validation). Verbatim labels per project rule. `status::done` `priority::critical` `estimate::1d`
  - Drafted 2026-04-15 at `deliverables/F2/F2-Spec.md`. 114 items extracted verbatim, preserving original PDF question numbers as primary item codes and legacy margin codes for traceability. Google Forms translation risks consolidated: 18 items flagged **SECTION** (dedicated section needed for branching), 9 items flagged **SPLIT** (role × facility-type cross-products around Q54/Q55, Q62/Q62.1, Q67/Q67.1, Q78/Q78.1). Six open items flagged for ASPSI/Dr. Claro review (Q1 name capture, Q32 skip anomaly, Q62 facility-type routing, Q63 prompt collapse, Q73/Q77/Q80 optional). Feeds E2-F2-014 (skip logic restructure) and E2-F2-015 (validation inventory).
- [x] **E2-F2-014** F2 skip logic restructured for Google Forms section-based branching. Flag any logic that doesn't survive the translation (per-question skips, multi-condition gates) and propose alternatives. `status::done` `priority::critical` `estimate::4h`
  - Drafted 2026-04-15 at `deliverables/F2/F2-Skip-Logic.md`. Section graph ASCII-diagrammed end-to-end (SEC-0 through SUBMIT), normalised routing table with every `setGoToSectionBasedOnAnswer()` call enumerated for E3-F2-GF-003. Role-gate branching solved via a 3-bucket re-confirmation question (BUCKET-CD / BUCKET-PHARM / BUCKET-OTHER) asked at SEC-C0 and SEC-G-gate-router. Facility-type splits (ZBB vs NBB for Q62/Q62.1, Q67/Q67.1, Q78/Q78.1) handled via a visible "confirm facility type" single-choice driver pre-selected from the URL. No multi-select branches in F2 (confirmed). POST-processing list covers cross-field checks and Q11 derivation. Six open items flagged for ASPSI: facility-type re-confirm UX, role-bucket UX, Q111 lift from grid, Q55 audience, Q44 removal, Q32 PDF anomaly.
- [x] **E2-F2-015** F2 validation rule inventory adapted for self-admin (required fields, regex, numeric ranges — no "interviewer override" pattern) `status::done` `priority::high` `estimate::4h`
  - Drafted 2026-04-15 at `deliverables/F2/F2-Validation.md`. Per-question table for Sections A–J + pre-survey URL params. Four hard-required fields only (consent, facility_type, Q5 role, Q112 leaving) — everything else optional to minimize drop-off on a 114-item self-admin form. Q103 lifted out of the Q103–Q110 frequency grid (standalone single-choice) so Q111 skip-if-Never routing survives the Forms translation. Q68–Q72 kept as standalone 1-5 items (not a grid) because Forms grids don't support mid-grid section routing. Numeric ranges deliberately loose (age 18–80, tenure 0–60y/0–11m, days 1–7, hours 1–24); tight ranges would block submission on self-admin. Push most consistency into POST via F2-Cross-Field.md.
- [x] **E2-F2-016** F2 cross-field consistency rules (limited by Google Forms' single-question validation scope; most cross-field checks move to post-processing on the response Sheet) `status::done` `priority::high` `estimate::2h`
  - Drafted 2026-04-15 at `deliverables/F2/F2-Cross-Field.md`. 6 rule groups × 20 rules targeting Apps Script `onFormSubmit` + nightly `cleanSheet()`: PROF-01..05 (profile plausibility, warn-only), GATE-01..05 (section gate integrity — clean by dropping leaked answers), FAC-01..07 (facility-type ZBB/NBB dual-variant reconciliation), DISP-01..03 (disposition derivation from timestamps, 3-day window check, rapid-submission check), SRC-01..03 (response_source integrity + duplicate detection), CONS-01..02 (consent audit). Severity levels: error/warn/clean/info. Response Sheet gets `_qa_flags`, `_qa_disposition`, `_derived_employment_class`, `_dropped_fields`, `_qa_last_run_at` columns. Order-of-execution diagram runs SRC → CONS → GATE → FAC → PROF → DISP → Write so plausibility warnings don't fire on already-dropped content. 3 open items (FAC-07 DOH-retained duals, DISP-03 rapid threshold, SRC-03 duplicate definition).
- [ ] **E2-F2-017** Shan (QA) reviews F2 spec before build `status::todo` `priority::high` `estimate::2h`
- [ ] **E2-F2-018** F2 spec sign-off → enters Epic 3 Google Forms build `status::todo` `priority::high` `estimate::1h`

### CSPro DCF track *(DEFERRED — optional, conditional on F2 Google Forms test outcomes)*

> These tasks are **not current commitments**. They are parked for potential activation after F2 Google Forms testing, if ASPSI wants a CSPro encoder variant for paper responses (Fallback B of the three-path capture model). If activated, scheduled **last** in the Epic 2 sequence — after F1/F3/F4 DCF work.

- [ ] **E2-F2-003** F2 `generate_dcf.py` authored `status::deferred` `priority::low` `estimate::1d`
- [ ] **E2-F2-004** F2 DCF v1 generated and opened in CSPro Designer `status::deferred` `priority::low` `estimate::2h`
- [ ] **E2-F2-005** F2 skip logic walked (CSPro encoder variant) `status::deferred` `priority::low` `estimate::1d`
- [ ] **E2-F2-006** F2 validation rule inventory (CSPro) `status::deferred` `priority::low` `estimate::1d`
- [ ] **E2-F2-007** F2 cross-field consistency rules (CSPro) `status::deferred` `priority::low` `estimate::4h`
- [ ] **E2-F2-008** F2 sanity check findings → bug list (CSPro) `status::deferred` `priority::low` `estimate::2h`
- [ ] **E2-F2-009** F2 corrections + DCF v2 regeneration `status::deferred` `priority::low` `estimate::4h`
- [ ] **E2-F2-010** F2 Designer validation + sign-off (CSPro) `status::deferred` `priority::low` `estimate::2h`

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
