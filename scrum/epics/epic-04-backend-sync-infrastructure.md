---
epic: 4
title: Backend & Sync Infrastructure
phase: per-track
status: in-progress
last_updated: 2026-04-25
---

# Epic 4 — Backend & Sync Infrastructure

Server-side and synchronization layer for both survey tracks: **Apps Script + Cloudflare Pages** for the F2 self-admin PWA, and **CSWeb** for the F1/F3/F4 CSPro CAPI track. Covers authentication, data ingestion, storage, and integration ETL between the two tracks.

**Ties to Product Backlog:** [[../product-backlog#Epic 4 — Backend & Sync Infrastructure|PB Epic 4]]
**Methodology:** [[../../../../2_Areas/IT-Standards/templates/CAPI-Development-Workflow|CAPI Development Workflow]]

## Task conventions

- `status::` — `todo` / `in-progress` / `done` / `blocked` / `ongoing`
- `priority::` — `critical` / `high` / `medium` / `low`
- `estimate::` — `30m` / `2h` / `1d` / etc. or `recurring`
- Task IDs: `E4-{track}-NNN` where track ∈ `PWA` / `CSWeb` / `INT` (integration)

## Tasks

### F2 PWA Track *(live in production at v1.1.1, 2026-04-25)*

- [x] **E4-PWA-001** Apps Script backend scaffold (router, handlers, schema) `status::done` `priority::critical`
- [x] **E4-PWA-002** Cloudflare Pages staging + production deploy targets configured `status::done` `priority::critical`
- [x] **E4-PWA-003** HMAC-signed request handshake between PWA and Apps Script `status::done` `priority::high`
- [x] **E4-PWA-004** Sync orchestrator (queue, retry, idempotent submit) `status::done` `priority::high`
- [x] **E4-PWA-005** FacilityMasterList provisioning sheet + `?action=facilities` endpoint `status::done` `priority::high`
- [x] **E4-PWA-006** Submission audit log + de-duplication via `client_submission_id` `status::done` `priority::medium`
- [x] **E4-PWA-007** Runtime config endpoint with kill-switch + spec-drift signal `status::done` `priority::medium`
- [ ] **E4-PWA-010** Backend secrets rotation policy documented (HMAC, Apps Script deploy ID) `status::todo` `priority::medium` `estimate::2h`
- [ ] **E4-PWA-011** Backup + restore runbook for FacilityMasterList + submissions sheets `status::todo` `priority::medium` `estimate::3h`

### CSWeb Track *(not started)*

- [ ] **E4-CSWeb-001** CSWeb server provisioning — host selection, OS, network, TLS `status::todo` `priority::high` `estimate::1d`
- [ ] **E4-CSWeb-002** CSWeb installation + admin account setup `status::todo` `priority::high` `estimate::4h`
- [ ] **E4-CSWeb-003** Per-survey project upload (F1, F3, F4 dictionaries + apps) `status::todo` `priority::high` `estimate::4h`
- [ ] **E4-CSWeb-004** User management — enumerator credentials, role-based access `status::todo` `priority::high` `estimate::3h`
- [ ] **E4-CSWeb-005** Field-tablet sync configuration — endpoint URLs, sync schedule, conflict policy `status::todo` `priority::high` `estimate::3h`
- [ ] **E4-CSWeb-006** Backup strategy for CSWeb data (frequency, retention, restore drill) `status::todo` `priority::medium` `estimate::4h`
- [ ] **E4-CSWeb-007** Monitoring dashboard — sync health, submission counts, field-device status `status::todo` `priority::medium` `estimate::1d`

### Integration ETL *(not started — feeds Epic 8 monitoring + Epic 10 cleaning)*

- [ ] **E4-INT-001** ETL spec drafted — CSWeb (F1/F3/F4) + F2 PWA backend → unified analysis store `status::todo` `priority::high` `estimate::1d`
- [ ] **E4-INT-002** Looker Studio (or equivalent) dashboard prototype over the unified store `status::todo` `priority::medium` `estimate::1d`
- [ ] **E4-INT-003** Codebook-driven harmonization (per `concepts/aspsi-data-harmonization`) wired into ETL `status::todo` `priority::medium` `estimate::TBD`

## Dependencies

- Epic 5 (Field Distribution) depends on E4-CSWeb-005 for tablet sync configuration.
- Epic 6 (Testing) depends on E4-CSWeb-001..003 for staging environment.
- Epic 8 (Fieldwork Monitoring) depends on E4-INT-001..002 for cross-track visibility.
