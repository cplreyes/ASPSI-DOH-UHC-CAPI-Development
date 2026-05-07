---
epic: 5
title: Field Distribution & Device Management
phase: per-track
status: in-progress
last_updated: 2026-05-08
---

# Epic 5 — Field Distribution & Device Management

Getting survey instruments into enumerator hands and keeping them running in the field. Covers **CAPI tablet provisioning** for F1/F3/F4 (CSPro CSEntry), and **PWA URL distribution + install + reminder ops** for F2 self-administration.

**Ties to Product Backlog:** [[../product-backlog#Epic 5 — Field Distribution & Device Management|PB Epic 5]]
**Methodology:** [[../../../../2_Areas/IT-Standards/templates/CAPI-Development-Workflow|CAPI Development Workflow]]

## Task conventions

- `status::` — `todo` / `in-progress` / `done` / `blocked` / `ongoing`
- `priority::` — `critical` / `high` / `medium` / `low`
- `estimate::` — `30m` / `2h` / `1d` / etc. or `recurring`
- Task IDs: `E5-{track}-NNN` where track ∈ `CAPI` (tablets) / `PWA` (self-admin)

## Tasks

### CAPI Tablet Track *(spec drafted 2026-04-29)*

- [ ] **E5-CAPI-001** Tablet specification finalized — model, OS, storage, accessories per enumerator team `status::ongoing` `priority::high` `estimate::recurring` `out_of_scope::data_programmer` `owner::aspsi-ops` `scrum::unscheduled`
  - Tablet procurement is ASPSI ops lane (per CSA D1–D6 — Carl produces deliverables, ASPSI ops handles procurement + spec sign-off with vendor). Spec drafted 2026-04-29; surface in PIB / risk register as a project-level dependency, not in Carl's sprint backlog. Mirrors the E0-020 / E0-032 / E0-032a out-of-scope discipline. Pairs with E4-CSWeb-009 (tablet bring-up SOP) which IS in Data Programmer scope — the SOP runs on whatever model ASPSI procures.
- [ ] **E5-CAPI-002** Tablet procurement + receipt — count matches enumerator headcount + spares `status::todo` `priority::high` `estimate::TBD` `scrum::unscheduled`
- [ ] **E5-CAPI-003** Imaging SOP — base config, MDM enrollment, CSEntry install, security baseline `status::todo` `priority::high` `estimate::1d` `scrum::unscheduled`
- [ ] **E5-CAPI-004** Per-tablet enrollment — bind tablet ID to enumerator ID, push initial CSPro app + dictionary `status::todo` `priority::high` `estimate::recurring` `scrum::unscheduled`
- [ ] **E5-CAPI-005** Field replacement protocol — how to swap a broken/lost tablet without losing in-flight data `status::todo` `priority::high` `estimate::3h` `scrum::unscheduled`
- [ ] **E5-CAPI-006** Charging + connectivity logistics for cluster deployment `status::todo` `priority::medium` `estimate::2h` `scrum::unscheduled`
- [ ] **E5-CAPI-007** Tablet retrieval + decommission SOP at engagement close `status::todo` `priority::medium` `estimate::2h` *(feeds Epic 12)* `scrum::unscheduled`

### F2 PWA Self-Admin Track *(distribution model proven via UAT, 2026-04-25)*

- [x] **E5-PWA-001** Production URL stable + indexable (https://f2-pwa.pages.dev) `status::done` `priority::high`
- [x] **E5-PWA-002** PWA install banner + service-worker registration `status::done` `priority::high`
- [x] **E5-PWA-003** UAT distribution model proven — Slack-shared link, Shan + ASPSI testers reached `status::done` `priority::high`
- [ ] **E5-PWA-004** Production HCW distribution-list SOP — how facilities receive the link, who confirms enrollment, escalation path `status::todo` `priority::high` `estimate::4h` `scrum::unscheduled`
- [ ] **E5-PWA-005** Reminder cadence + automation — periodic nudges to non-respondents (frequency, channel, opt-out) `status::todo` `priority::medium` `estimate::1d` `scrum::unscheduled`
- [ ] **E5-PWA-006** HCW completion-tracking dashboard — who's done, who's pending, by facility `status::todo` `priority::medium` `estimate::1d` `scrum::unscheduled`
- [ ] **E5-PWA-007** Pilot batch SOP — sample-size, success criteria, go/no-go to full rollout `status::todo` `priority::high` `estimate::4h` `scrum::unscheduled`

## Dependencies

- E5-CAPI-003 imaging SOP depends on Epic 3 F1/F3/F4 builds being CSEntry-installable.
- E5-CAPI-004 enrollment depends on E4-CSWeb-004 user management.
- E5-PWA-005 reminder automation may consume a Slack or Gmail webhook — coordinate with Epic 4.
