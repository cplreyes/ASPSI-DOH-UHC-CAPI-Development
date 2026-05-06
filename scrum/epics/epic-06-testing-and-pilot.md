---
epic: 6
title: Testing and Pilot
phase: per-track
status: in-progress
last_updated: 2026-04-25
---

# Epic 6 — Testing and Pilot

Pre-production verification and limited-scale field pilot before full rollout. Covers **automated test stacks, manual UAT, accessibility, and pilot batches** for both the F2 PWA (live) and the F1/F3/F4 CAPI track (pending Epic 3 sign-off + Epic 5 tablet provisioning).

**Ties to Product Backlog:** [[../product-backlog#Epic 6 — Testing and Pilot|PB Epic 6]]
**Methodology:** [[../../../../2_Areas/IT-Standards/templates/CAPI-Development-Workflow|CAPI Development Workflow]]

## Task conventions

- `status::` — `todo` / `in-progress` / `done` / `blocked` / `ongoing`
- `priority::` — `critical` / `high` / `medium` / `low`
- `estimate::` — `30m` / `2h` / `1d` / etc. or `recurring`
- Task IDs: `E6-{track}-NNN` where track ∈ `PWA` / `CAPI`

## Tasks

### F2 PWA Track *(test stack live; UAT Rounds 1+2 closed 2026-04-25)*

- [x] **E6-PWA-001** Vitest unit suite scaffold + 306 passing tests across 42 files `status::done` `priority::high`
- [x] **E6-PWA-002** Playwright E2E configuration with mock-backend fixtures `status::done` `priority::high`
- [x] **E6-PWA-003** Cross-platform QA checklist drafted (`deliverables/F2/PWA/2026-04-18-cross-platform-qa-checklist.md`) `status::done` `priority::high`
- [x] **E6-PWA-004** UAT Round 1 (v1.1.0) — opened by Shan 2026-04-23, closed 2026-04-24, 7 issues fixed `status::done` `priority::critical`
- [x] **E6-PWA-005** UAT Round 2 (v1.1.1) — opened 2026-04-25, closed same day, 6 issues fixed `status::done` `priority::critical`
- [x] **E6-PWA-006** Internal QA + design-review pass (Round 3 internal-QA) — 12 issues filed as #19-#30, milestone v1.3.0 2026-04-25 `status::done` `priority::high`
- [~] **E6-PWA-007** UAT Round 3 (v1.2.0) — exclusive "I don't know", "All of the above" auto-select, scale-style matrix (#16/#17/#18). Code shipped in v2.0.0 (Phase F cutover merge `2a6dd34`); GH issues closed 2026-05-01 as `status:fixed-pending-verify`. **Folded into the UAT Round 2 reopened against v2.0.0** (Shan + Kidd) rather than a separate Round 3 — close milestone v1.2.0 after sign-off to fire the auto-release-notes pipeline (or fold into v2.0.0 release notes). `status::in-progress` `priority::high`
- [ ] **E6-PWA-008** F2 production pilot batch — small facility cohort, success criteria, go/no-go to full rollout `status::todo` `priority::high` `estimate::1d` `scrum::unscheduled`
- [ ] **E6-PWA-009** axe-core / Lighthouse a11y audit — full report, AA compliance gate `status::todo` `priority::medium` `estimate::4h` `scrum::unscheduled`
- [ ] **E6-PWA-010** Performance baseline — Core Web Vitals, bundle size budget, regression tracking `status::todo` `priority::medium` `estimate::4h` `scrum::unscheduled`

### CAPI Track *(not started — depends on Epic 3 sign-off + Epic 5 tablets)*

- [ ] **E6-CAPI-001** F1 desk test — DCF + FMF walkthrough on CSEntry tablet, sample data entry `status::todo` `priority::high` `estimate::1d` `scrum::unscheduled`
- [ ] **E6-CAPI-002** F3 desk test — full A–L walkthrough with sanity scenarios `status::todo` `priority::high` `estimate::1d` `scrum::unscheduled`
- [ ] **E6-CAPI-003** F4 desk test — household roster + interval sampling sanity, full A–Q `status::todo` `priority::high` `estimate::1d` `scrum::unscheduled`
- [ ] **E6-CAPI-004** Sync round-trip test — tablet → CSWeb → ETL → unified store `status::todo` `priority::high` `estimate::4h` `scrum::unscheduled`
- [ ] **E6-CAPI-005** QA Tester (Shan) handoff workflow extended to CAPI — bug-report template, severity rubric, milestone label `status::todo` `priority::high` `estimate::3h` `scrum::unscheduled`
- [ ] **E6-CAPI-006** Pretest pilot — 1-cluster live run with real enumerators on real respondents (gated by SJREB clearance, see E0-020) `status::blocked` `priority::critical` `estimate::1w` `scrum::unscheduled`
- [ ] **E6-CAPI-007** Pretest debrief + bug triage → Epic 3 fix batch `status::todo` `priority::high` `estimate::4h` `scrum::unscheduled`

## Dependencies

- E6-CAPI-001..003 require Epic 3 builds complete (F1 awaits E2-F1-010 sign-off; F3/F4 are Build-ready).
- E6-CAPI-004 requires E4-CSWeb-001..005.
- E6-CAPI-006 requires E0-020 SJREB clearance (long-pole blocker).
- E6-PWA-007 (Round 3) — Epic 3 v1.2.0 implementation done; verification folded into UAT Round 2 reopened against v2.0.0.
