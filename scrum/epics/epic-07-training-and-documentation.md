---
epic: 7
title: Training and Documentation
phase: cross-cutting
status: in-progress
last_updated: 2026-04-29
---

# Epic 7 — Training and Documentation

Training materials, fieldwork manuals, in-app help, and reference documentation for both the CAPI (F1/F3/F4) and the F2 PWA tracks. Outputs are owned by Carl as CAPI dev consultant in collaboration with the ASPSI training team (Kidd as main RA).

**Ties to Product Backlog:** [[../product-backlog#Epic 7 — Training and Documentation|PB Epic 7]]
**Methodology:** [[../../../../2_Areas/IT-Standards/templates/CAPI-Development-Workflow|CAPI Development Workflow]]

## Task conventions

- `status::` — `todo` / `in-progress` / `done` / `blocked` / `ongoing`
- `priority::` — `critical` / `high` / `medium` / `low`
- `estimate::` — `30m` / `2h` / `1d` / etc. or `recurring`
- Task IDs: `E7-{track}-NNN` where track ∈ `DOC` (manuals/docs) / `TRAIN` (training delivery) / `HELP` (in-app help)

## Tasks

### Documentation Track *(active 2026-04-29)*

- [ ] **E7-DOC-001** Survey Manual — CSPro / CAPI section rewrite (replace 2023 SPEED legacy text with current deployment) `status::in-progress` `priority::high` `estimate::1d` *(draft delivered for Kidd's review at `deliverables/Survey-Manual/CSPro-Section-Draft_2026-04-29.md`; awaiting integration into master manual)* `scrum::unscheduled`
- [ ] **E7-DOC-002** Survey Manual — CAPI Quick Reference Card appendix `status::in-progress` `priority::medium` `estimate::4h` *(included in E7-DOC-001 draft as a suggested appendix)* `scrum::unscheduled`
- [ ] **E7-DOC-003** Survey Manual — CAPI Troubleshooting Guide appendix `status::in-progress` `priority::medium` `estimate::4h` *(included in E7-DOC-001 draft as a suggested appendix)* `scrum::unscheduled`
- [ ] **E7-DOC-004** Survey Manual — F2 (Healthcare Worker) administration sub-section `status::todo` `priority::medium` `estimate::4h` *(flagged in E7-DOC-001 open-questions; defer until Kidd confirms scope)* `scrum::unscheduled`
- [ ] **E7-DOC-005** Reconcile Questionnaire Number scheme between Survey Manual and F1/F3/F4 case-ID structure `status::todo` `priority::high` `estimate::2h` *(flagged in E7-DOC-001 open-questions)* `scrum::unscheduled`

### Training Track *(not started)*

- [ ] **E7-TRAIN-001** CAPI enumerator training deck — F1/F3/F4 walkthrough `status::todo` `priority::high` `estimate::1d` `scrum::unscheduled`
- [ ] **E7-TRAIN-002** STL training deck — sync, field replacement, end-of-day review `status::todo` `priority::high` `estimate::1d` `scrum::unscheduled`
- [ ] **E7-TRAIN-003** F2 self-admin one-pager for HCWs (link, install, completion window) `status::todo` `priority::medium` `estimate::4h` `scrum::unscheduled`

### In-App Help Track *(F2 PWA only — not started)*

- [ ] **E7-HELP-001** F2 PWA in-app help review — verify copy matches current production v1.1.1 + Verde Manual visual identity `status::todo` `priority::low` `estimate::2h` `scrum::unscheduled`

## Dependencies

- E7-DOC-001 / E7-DOC-002 / E7-DOC-003 — final integration depends on Kidd's review and on F1/F3/F4 builds reaching Designer-validated state for screenshots.
- E7-DOC-004 depends on Kidd confirming whether F2 belongs in the same manual or a separate F2-specific document.
- E7-TRAIN-001 / E7-TRAIN-002 depend on Epic 3 (CAPI build) reaching desk-test-ready, and Epic 5 imaging SOP being drafted.
- E7-HELP-001 is unblocked but low priority while UAT rounds are still open.
