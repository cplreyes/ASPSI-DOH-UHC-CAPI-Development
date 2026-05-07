---
epic: 2
title: Survey Questionnaire Design & Dictionary
phase: per-instrument
status: in-progress
last_updated: 2026-04-21
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

**State:** **Build-ready 2026-05-04.** Designer walkthrough complete (E2-F1-010 closed); bug list clean — no deferrals. The 6 `PENDING_DESIGN_*` defaults stand as final; no further LSS reconciliation. Unblocks E3-F1-001 (FMF Designer pass).
**Scope (as of 2026-04-21):** 12 records · 671 items · 166 questions · 4 validation tiers (post Apr 21 GPS+photo+PSGC-cascade pass + case-control extension — SURVEY_CODE/INTERVIEWER_ID/DATE_STARTED/TIME_STARTED/AAPOR_DISPOSITION + FACILITY_NAME/FACILITY_ADDRESS; secondary-data records consolidated; `REC_FACILITY_CAPTURE` added for GPS/photo triggers)
**Reference docs:**
- `deliverables/CSPro/F1/F1-Skip-Logic-and-Validations.md` — skip-logic + validation spec (aligned with F3/F4 Apr 21 architecture)
- `deliverables/CSPro/Capture-Helpers.apc` — shared GPS + verification-photo helpers
- `deliverables/CSPro/PSGC-Cascade.apc` — shared PSGC cascade (REGION → PROVINCE_HUC → CITY_MUNICIPALITY → BARANGAY)

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
- [x] **E2-F1-009b** ~~Reconcile DCF with LSS-meeting decisions on the 6 open items~~ **CLOSED 2026-04-17 — defaults stand as final.** The 6 items (Q63 day vs month, SECONDARY_DATA structure, NBB split, Q31 NA-skip intent, Q166 nurse list, Q121 dynamic value set) remain encoded as `PENDING_DESIGN_Q63_USE_DAY_BUCKETS`, `PENDING_DESIGN_SECONDARY_DATA_AS_STUBS`, `PENDING_DESIGN_NBB_SPLIT_BY_TIER`, `PENDING_DESIGN_Q31_NA_SKIPS`, `PENDING_DESIGN_Q166_NURSES_INCLUDE_AUDITS`, `PENDING_DESIGN_Q121_DYNAMIC_VALUE_SET` in `generate_dcf.py` — these are the final design decisions. If any item needs to change later, flip the constant + regenerate. `status::done` `priority::critical`
- [x] **E2-F1-010** F1 DCF opened in CSPro Designer, validated, bug list **clean — no deferrals** → sign-off recorded **2026-05-04**; F1 → Build-ready; unblocks E3-F1-001 `status::done` `priority::critical` `actual::~confirmed via spot-check (well under 4h estimate)`
  - **Sprint 001 commitment.** Generator + DCF in place 2026-04-14; Designer walkthrough next.
  - **Scope update 2026-04-21:** DCF extended with case-control block (SURVEY_CODE, INTERVIEWER_ID, DATE_STARTED, TIME_STARTED, AAPOR_DISPOSITION) + FACILITY_NAME + FACILITY_ADDRESS → 12 records / 671 items. Walkthrough now covers the new fields alongside the existing scope. AAPOR 2023 11-code value set attached; preproc prefill spec in `F1-Skip-Logic-and-Validations.md` §4.17.
  - **Closed 2026-05-04 (Sprint 004 Day 1).** Three-sprint carry retired. Generator-driven artifact whose upstream spec was already aligned with F3/F4 architecture on 2026-04-21 — Designer pass was a verification step, not a discovery step. Sign-off appended to `log.md`.

---

## F2 — Healthcare Worker Survey *(self-administered, 14pp)*

**State:** Design-complete — spec frozen and embedded in the PWA build (2026-04-17 pivot).
**Primary mode:** **PWA** (Vite+React+TS, installable, IndexedDB autosave, Apps Script sync). Google Forms track and CSPro-encoder track both **RETIRED**. See Epic 3.
**Reference docs:**
- `deliverables/F2/F2-Spec.md` — 114 items across sections A–J (verbatim labels)
- `deliverables/F2/F2-Skip-Logic.md` — section-graph + routing (now rendered by PWA nav engine)
- `deliverables/F2/F2-Validation.md` — required fields + numeric ranges
- `deliverables/F2/F2-Cross-Field.md` — POST-submit consistency rules
- `deliverables/F2/PWA/app/` — canonical build artifact

### Design artifacts *(feed the PWA build in Epic 3)*

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
- [x] **E2-F2-017** Shan (QA) brought into the F2 workflow `status::done` `priority::high`
- [x] **E2-F2-018** F2 spec frozen → consumed by PWA build `status::done` `priority::high`
  - Superseded the original "Google Forms sign-off" framing when F2 pivoted to PWA 2026-04-17. Spec is frozen at `F2-Spec.md` / `F2-Skip-Logic.md` / `F2-Validation.md` / `F2-Cross-Field.md` and embedded in the PWA.

### Retired tracks *(kept for historical traceability; do not re-open)*

- **CSPro DCF track (E2-F2-003..010):** Retired 2026-04-17. F2 is a self-admin PWA instrument; no CSPro DCF will be produced. Prior `deferred` status superseded.
- **Google Forms build track (E3-F2-GF-009..015):** Retired 2026-04-17 (see Epic 3). Closed GF-001..008 artifacts under `deliverables/F2/apps-script/` retained for reference.

---

## F3 — Patient Survey *(interviewer-administered, 23pp, outpatient + inpatient)*

**State:** Design — Build-ready as of 2026-04-21.
**Scope (as of 2026-04-21):** 18 records · 806 items · sections A–L · dual-population eligibility (post case-control extension — SURVEY_CODE/INTERVIEWER_ID/DATE_STARTED/TIME_STARTED/AAPOR_DISPOSITION).
**Reference doc:** `deliverables/CSPro/F3/F3-Skip-Logic-and-Validations.md` (reviewed 2026-04-21; 14 sanity findings; 15 CSPro PROC templates; 1 question routed to Juvy — Q31 IP_GROUP).

- [x] **E2-F3-001** F3 questionnaire PDF ingested `status::done` `priority::high`
- [x] **E2-F3-002** F3 text extraction + wiki source page with Section A–L map `status::done` `priority::high`
- [x] **E2-F3-003** F3 `generate_dcf.py` authored (shared `cspro_helpers.py`) `status::done` `priority::high`
- [x] **E2-F3-004** F3 DCF v1 generated and opened in Designer `status::done` `priority::high`
- [x] **E2-F3-005** F3 skip logic walked — all sections A–L with dual-population branching `status::done` `priority::high`
- [x] **E2-F3-006** F3 validation rule inventory (HARD/SOFT/GATE) `status::done` `priority::high`
- [x] **E2-F3-007** F3 cross-field consistency rules `status::done` `priority::high`
- [x] **E2-F3-008** F3 sanity check findings → 14 findings; 5 spec-decisions closed with ASPSI override clause `status::done` `priority::high`
- [x] **E2-F3-009** F3 corrections + DCF refresh through Apr 20 source update (18 records / 806 items) `status::done` `priority::high`
- [ ] **E2-F3-010** F3 Designer validation + sign-off `status::todo` `priority::high` `estimate::2h` `scrum::sprint-004`
  - **Scope update 2026-04-21:** DCF extended with case-control block (SURVEY_CODE, INTERVIEWER_ID, DATE_STARTED, TIME_STARTED, AAPOR_DISPOSITION) → 18 records / 806 items. Preproc spec in `F3-Skip-Logic-and-Validations.md` §4.16.
  - Pending Juvy confirmation on Q31 IP_GROUP (coded list vs alpha).

---

## F4 — Household Survey *(interviewer-administered, 26pp, new for Year 2)*

**State:** Design — **Build-ready** as of 2026-04-21 (schema verified; no patch needed).
**Scope (as of 2026-04-21):** 22 records · 623 items · sections A–Q · household roster with per-member sub-tables — highest structural complexity (post case-control extension — SURVEY_CODE/INTERVIEWER_ID/DATE_STARTED/TIME_STARTED/AAPOR_DISPOSITION).
**Reference doc:** `deliverables/CSPro/F4/F4-Skip-Logic-and-Validations.md` (draft 2026-04-21; 13 sanity findings, findings #1–#2 CLOSED-BY-VERIFICATION 2026-04-21 — `C_HOUSEHOLD_ROSTER` already repeating (`max_occurs=20`), `J_HEALTH_SEEKING` intentionally respondent-level per Apr 20 source; 11 CSPro PROC templates; 3 questions routed to ASPSI).

- [x] **E2-F4-001** F4 questionnaire PDF ingested `status::done` `priority::high`
- [x] **E2-F4-002** F4 text extraction + wiki source page with Section A–Q map `status::done` `priority::high`
- [x] **E2-F4-003** F4 `generate_dcf.py` authored (shared `cspro_helpers.py`) `status::done` `priority::high`
- [x] **E2-F4-004** F4 DCF v1 generated and opened in Designer `status::done` `priority::high`
- [x] **E2-F4-005** F4 skip logic walked — all sections A–Q with roster + WHO expenditure + bill-recall chain `status::done` `priority::high`
- [x] **E2-F4-006** F4 validation rule inventory (validations 3.1–3.18 with HARD/SOFT/GATE) `status::done` `priority::high`
- [x] **E2-F4-007** F4 cross-field consistency rules (within-member + cross-member) `status::done` `priority::high`
- [x] **E2-F4-008** F4 sanity check findings → 13 findings (findings #1, #2 later reclassified as stale — see E2-F4-009) `status::done` `priority::high`
- [x] **E2-F4-009** ~~F4 corrections — patch `generate_dcf.py` to flip `C_HOUSEHOLD_ROSTER` + `J_HEALTH_SEEKING` to repeating records~~ **CLOSED-BY-VERIFICATION 2026-04-21.** Re-inspected the generator and the emitted DCF before starting the patch: `C_HOUSEHOLD_ROSTER` already emits `max_occurs=20` with `MEMBER_LINE_NO` id-item (`generate_dcf.py:487`, `HouseholdSurvey.dcf:2836`). `J_HEALTH_SEEKING` correctly stays at `max_occurs=1` — respondent-level per the Apr 20 source rephrase ("singular you/your household member"; `generate_dcf.py:984–989`). F4 spec §1.A findings #1 and #2 were stale against the generator; spec updated. No code change. `status::done` `priority::critical`
- [ ] **E2-F4-010** F4 Designer validation + sign-off `status::todo` `priority::high` `estimate::4h` `scrum::sprint-004`
  - **Scope update 2026-04-21:** DCF extended with case-control block (SURVEY_CODE, INTERVIEWER_ID, DATE_STARTED, TIME_STARTED, AAPOR_DISPOSITION) → 22 records / 623 items. Preproc spec in `F4-Skip-Logic-and-Validations.md` §4.12.
  - Pending ASPSI confirmation on Q15 IP_GROUP list.

---

## PLF — Patient Listing Form *(recruitment form, 1pp)*

**State:** Source Captured

- [x] **E2-PLF-001** PLF form PDF ingested `status::done` `priority::medium`
- [x] **E2-PLF-002** PLF wiki source page `status::done` `priority::medium`
- [ ] **E2-PLF-003** Implementation decision: lightweight CAPI vs paper-only `status::todo` `priority::medium` `estimate::2h` `scrum::unscheduled`
- [ ] **E2-PLF-004** If CAPI: `generate_dcf.py` + DCF v1 (minimal, single-record) `status::todo` `priority::medium` `estimate::4h` `scrum::unscheduled`
- [ ] **E2-PLF-005** If CAPI: minimal skip logic + validation rules `status::todo` `priority::medium` `estimate::2h` `scrum::unscheduled`
- [ ] **E2-PLF-006** If CAPI: Designer validation + sign-off `status::todo` `priority::medium` `estimate::1h` `scrum::unscheduled`

## Notes

- F1 is the reference interviewer-administered CSPro instrument — patterns established here flow into F3/F4.
- F2 is the outlier — it took the self-admin PWA path and no longer follows the DCF pipeline.
- Shared helpers live in `deliverables/CSPro/cspro_helpers.py` (Python generator) and in `deliverables/CSPro/Capture-Helpers.apc` + `deliverables/CSPro/PSGC-Cascade.apc` (CSPro `.apc` fragments). F1/F3/F4 all consume these.
- F3 and F4 moved from "Source Captured" to "Build-ready" in a compressed window 2026-04-16 (DCFs built) → 2026-04-21 (skip-logic + validation specs complete). F4's assumed "repeating-record schema patch" (E2-F4-009) turned out to already be implemented — closed by verification 2026-04-21.
