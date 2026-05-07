---
epic: 10
title: Data Cleaning and Processing
phase: closeout-prep
status: not-started
last_updated: 2026-05-08
---

# Epic 10 — Data Cleaning and Processing

Post-fieldwork data cleaning, validation, harmonization across the four instruments, and preparation for analysis. Activates as fieldwork wraps; runs in parallel with Epic 11 (Analysis Support).

**Ties to Product Backlog:** [[../product-backlog#Epic 10 — Data Cleaning and Processing|PB Epic 10]]
**Methodology:** [[../../../../2_Areas/IT-Standards/templates/CAPI-Development-Workflow|CAPI Development Workflow]] — Phase 5 (corrections during fieldwork) + Phase 11 (closeout cleanup)
**Implementation reference:** [[../../deliverables/UHC-Survey-CAPI-Guide/03-Phase-3-5-Spec-and-Generators|UHC Guide Phase 3-5]] + [[../../deliverables/UHC-Survey-CAPI-Guide/08-Phase-11-Closeout-Export|UHC Guide Phase 11]]

## Task conventions

- `status::` — `todo` / `in-progress` / `done` / `blocked` / `ongoing`
- `priority::` — `critical` / `high` / `medium` / `low`
- `estimate::` — `30m` / `2h` / `1d` / etc. or `recurring`
- Task IDs: `E10-{track}-NNN` where track ∈ `CLEAN` (cleaning rules) / `BATCH` (CSBatch passes) / `HARM` (harmonization) / `ETL` (cross-track ETL)

## Tasks

### Mid-fieldwork corrections SOP *(Sprint 005 candidate — May 8 audit gap)*

- [ ] **E10-CLEAN-001** Phase 5 Reformat-Data SOP for fieldwork-time corrections `status::todo` `priority::high` `estimate::4h` `scrum::sprint-005`
  - **Trigger:** May 8 audit gap. Pre-fieldwork, generator regenerate is fine. Post-fieldwork, **you cannot just regenerate the dcf** — old data won't load against the new schema. Per Khurshid 2023-09-21 *Tutorial on: Data Reformatting*: **"Don't enter new cases before reformatting — old data won't recover."** Also: **schema changes break .dat but not .csdb** — UHC must use .csdb storage.
  - **Deliverables:**
    - 2-line addition to `2_Areas/IT-Standards/templates/CAPI-Development-Workflow.md` Phase 5 documenting `.csdb` as canonical storage format
    - `deliverables/CSPro/Reformat-Data-SOP.md` — Tools → Reformat Data with old + new dictionary as the production correction path; paste-ready Reformat PFF; decision tree for "regenerate" vs "Reformat" vs "keep-both-items"
    - Verification that all F1/F3/F4 entry apps default to `.csdb` not `.dat`
  - **References:** [[../../deliverables/UHC-Survey-CAPI-Guide/03-Phase-3-5-Spec-and-Generators|Phase 3-5 guide §5.2]].

### CSBatch passes

- [ ] **E10-BATCH-001** CSBatch structure pass — every case has expected records `status::todo` `priority::high` `estimate::4h` `scrum::unscheduled`
- [ ] **E10-BATCH-002** CSBatch validity pass — every value within range `status::todo` `priority::high` `estimate::4h` `scrum::unscheduled`
- [ ] **E10-BATCH-003** CSBatch consistency pass — cross-field rules `status::todo` `priority::high` `estimate::4h` `scrum::unscheduled`
- [ ] **E10-BATCH-004** CSBatch imputation pass — hot-deck for missing data per Khurshid 2022-12-31; audit log via `stat()` `status::todo` `priority::medium` `estimate::1d` `scrum::unscheduled`

### Cross-instrument harmonization

- [ ] **E10-HARM-001** Codebook v1.0 — finalize the cross-instrument harmonized codebook (currently v0.2 draft per `deliverables/data-harmonization/`) `status::todo` `priority::high` `estimate::1w` `scrum::unscheduled`
  - **Reference:** `project_aspsi_data_harmonization.md` memory.
- [ ] **E10-HARM-002** Variable-rename ETL — apply harmonized names across F1/F3/F4 dat files + F2 PWA submissions sheet `status::todo` `priority::high` `estimate::1w` `scrum::unscheduled`

### Cross-track ETL

- [ ] **E10-ETL-001** Unified store ETL — CSWeb (F1/F3/F4) + F2 PWA backend (Apps Script + Sheets) into a single Stata/SPSS-ready dataset per instrument `status::todo` `priority::high` `estimate::1w` `scrum::unscheduled`

## Dependencies

- All E10 tasks activate post-fieldwork. Mid-fieldwork only E10-CLEAN-001 is relevant (Reformat-Data SOP must be in place BEFORE any field correction is needed).
- E10-HARM-* depends on Codebook v1.0 sign-off from Survey Manager.

## Notes

- The Reformat-Data SOP (E10-CLEAN-001) is the **highest-priority Sprint 005 candidate** in this epic — it's the safety-net for any mid-fieldwork schema bug. Without it, a mid-field correction is destructive.
- All ETL outputs land in `deliverables/data-harmonization/` per existing structure.
