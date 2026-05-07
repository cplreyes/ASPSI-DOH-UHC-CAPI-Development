---
epic: 7
title: Training and Documentation
phase: cross-cutting
status: in-progress
last_updated: 2026-05-08
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
- [ ] **E7-DOC-006** Survey Manual — fold Phase 8 CSWeb provisioning + tablet bring-up SOP excerpts into manual annexes `status::todo` `priority::medium` `estimate::3h` `scrum::unscheduled`
  - **Trigger:** Pairs with E4-CSWeb-008 (provisioning runbook) + E4-CSWeb-009 (tablet bring-up SOP). Fold operations-relevant excerpts into Annex 1 / Annex 2 of the Survey Manual so STLs and Field Manager have them in the manual itself.
  - **References:** [[../../deliverables/UHC-Survey-CAPI-Guide/06-Phase-8-CSWeb-and-Tablets|UHC Guide Phase 8]].
- [ ] **E7-DOC-007** Cross-link `docs/guides/CAPI-Development-Playbook.md` content into UHC-Survey-CAPI-Guide; archive playbook `status::todo` `priority::medium` `estimate::3h` `scrum::sprint-005`
  - **Trigger:** May 8 audit found ~85% overlap between the playbook and the new guide. Playbook predates the guide and was its seed material; now creates a conflicting source-of-truth.
  - **Deliverable:** Extract the 2 unique sections from the playbook (Popstan supervisor-app pattern → `04-Phase-6-Build-CAPI-App.md`; VPS Nginx provisioning specifics → `06-Phase-8-CSWeb-and-Tablets.md`), then delete `docs/guides/CAPI-Development-Playbook.md` after content fold is verified.

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
