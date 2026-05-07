---
epic: 8
title: Fieldwork Monitoring and Quality Control
phase: production-fieldwork
status: not-started
last_updated: 2026-05-08
---

# Epic 8 — Fieldwork Monitoring and Quality Control

Active monitoring layer that runs during main fieldwork (post-pretest, post-tablet-deployment). Covers daily sync verification, hot-fix protocol, in-flight quality control, replacement-protocol enforcement, and supervisor-side dashboards.

**Ties to Product Backlog:** [[../product-backlog#Epic 8 — Fieldwork Monitoring and Quality Control|PB Epic 8]]
**Methodology:** [[../../../../2_Areas/IT-Standards/templates/CAPI-Development-Workflow|CAPI Development Workflow]] — Phase 10
**Implementation reference:** [[../../deliverables/UHC-Survey-CAPI-Guide/07-Phase-9-10-Pretest-Fieldwork|UHC Guide Phase 9-10]]

## Task conventions

- `status::` — `todo` / `in-progress` / `done` / `blocked` / `ongoing`
- `priority::` — `critical` / `high` / `medium` / `low`
- `estimate::` — `30m` / `2h` / `1d` / etc. or `recurring`
- Task IDs: `E8-{track}-NNN` where track ∈ `OPS` (operations toolkit) / `MON` (monitoring) / `CSWeb` (CSWeb-side) / `BI` (cross-track BI dashboards)

## Tasks

### Phase 10 fieldwork ops toolkit *(Sprint 005 candidate — May 8 audit gap)*

- [ ] **E8-OPS-001** Phase 10 fieldwork ops toolkit — Map Case Listing widget, publishdate/synctime fields, HTML status reports for STLs, CSV value-label exporter `status::todo` `priority::high` `estimate::2d` `scrum::sprint-005`
  - **Trigger:** May 8 audit gap. Khurshid corpus has 5 specific Phase 10 techniques (Map Case Listing 2022-07-06, CSV sync-report value labels 2022-05-05, publishdate forced-update 2022-10-08, synctime tracking 2025-02-20, HTML reports 2022-12-05) that are not yet wired into UHC. Fieldwork starts in August; toolkit must be in place before then.
  - **Deliverables:**
    - `value-labels-csv-export.py` extension to `cspro_helpers` — emits CSV per dictionary for CSWeb sync-report import
    - `daily-summary-html.fmf-template` — HTML report template per Khurshid 2022-12-05 with `<?...?>` PROC blocks for daily field summaries
    - `weekly-client-report.html-template` — cumulative cases by region/cluster/instrument
    - `refusal-replacement-audit.html-template` — per-facility refusal counts vs 5–10% cap
    - `Map-Case-Listing-Setup.md` — supervisor walkthrough (no-code GPS overlay on .csdb pulls from CSWeb)
    - `publishdate-version-gating.apc` — forces enumerator update on stale builds
    - `synctime-monitoring.apc` — daily reminder if last sync >24h
  - **References:** [[../../deliverables/UHC-Survey-CAPI-Guide/07-Phase-9-10-Pretest-Fieldwork|Phase 9-10 guide §10.2–10.6]].
- [ ] **E8-MON-001** Daily ops rhythm runbook — STL stand-up, mid-day check-in, evening sync verification, 22:00 MNL upload mandate per Protocol V2 `status::todo` `priority::high` `estimate::4h` `scrum::unscheduled`
- [ ] **E8-MON-002** Hot-fix protocol — categorisation cheat-sheet (data-only vs spec-only vs app-only vs schema), 11-step runbook, HOTFIXES.md ledger format `status::todo` `priority::high` `estimate::3h` `scrum::unscheduled`
- [ ] **E8-MON-003** Issue log discipline — ISSUE-LOG.md format covering date, reporter, F-series, case ID, severity, description, resolution, fixed-in-build `status::todo` `priority::high` `estimate::2h` `scrum::unscheduled`

### Replacement protocol enforcement

- [ ] **E8-OPS-002** Annex D replacement protocol enforcement in CAPI — capture replacement reason + replaced-facility ID in FIELD_CONTROL; STL audit via CSWeb Reports `status::todo` `priority::high` `estimate::3h` `scrum::unscheduled`

### Cross-track BI dashboard

- [ ] **E8-BI-001** Cross-track BI dashboard scaffolded (CSWeb + F2 PWA backend in one view) — Looker Studio or equivalent reading from MySQL + Google Sheets in parallel `status::todo` `priority::medium` `estimate::1w` `scrum::unscheduled`
  - **Reference:** `project_aspsi_data_harmonization.md` memory + Codebook v0.2 cross-instrument harmonization plan.

## Dependencies

- All Phase 10 tasks depend on Epic 4 CSWeb stand-up (E4-CSWeb-008) being complete.
- E8-OPS-002 depends on E3 entry-app FIELD_CONTROL design.
- E8-BI-001 depends on Epic 10 codebook harmonization being far enough along to define unified field names.

## Notes

- Epic 8 activates at fieldwork start (August 2026 per current plan).
- The toolkit (E8-OPS-001) must be built BEFORE fieldwork, not during. Building it during is the canonical "we should have done this earlier" mistake.
- All HTML/PROC report templates live under `deliverables/CSPro/Fieldwork-Ops-Toolkit/` once delivered.
