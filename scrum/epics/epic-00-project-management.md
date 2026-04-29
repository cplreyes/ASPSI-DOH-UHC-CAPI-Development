---
epic: 0
title: CAPI Project Management & Stakeholder Engagement
phase: continuous
status: active-ongoing
last_updated: 2026-04-13
---

# Epic 0 — CAPI Project Management & Stakeholder Engagement

Continuous workstream spanning the full engagement. Governs sprint cadence, stakeholder communication, ethics coordination, risk tracking, and change management.

**Ties to Product Backlog:** [[../product-backlog#Epic 0 — CAPI Project Management & Stakeholder Engagement|PB Epic 0]]

## Task conventions

- `status::` — `todo` / `in-progress` / `done` / `blocked` / `ongoing` (for recurring tasks)
- `priority::` — `critical` / `high` / `medium` / `low`
- `estimate::` — `30m` / `2h` / `1d` / etc. or `recurring` for ceremonies
- Task IDs: `E0-NNN`

## Tasks

### Scrum & Backlog Discipline

- [ ] **E0-001** Run sprint planning ceremony each sprint (select items from epic files → sprint-current.md, set sprint goal, confirm dates) `status::ongoing` `priority::high` `estimate::recurring`
  - Sprint 001 planned 2026-04-13 — first execution of this ceremony.
- [ ] **E0-002** Run sprint review + retrospective each sprint close (archive sprint to `sprints/`, capture lessons, update backlog) `status::todo` `priority::high` `estimate::recurring`
- [ ] **E0-003** Backlog grooming session mid-sprint (refine upcoming epic tasks, adjust estimates) `status::todo` `priority::medium` `estimate::recurring`
- [x] **E0-004** Adopt Scrum discipline with per-project Product Backlog, Sprint Backlog, standups `status::done` `priority::high`
- [x] **E0-005** Build `/daily-standup` slash command reading PB + sprint backlog `status::done` `priority::medium`
- [ ] **E0-006** Keep Product Backlog `last_updated` current each sprint close `status::ongoing` `priority::medium`
- [ ] **E0-007** Maintain epic files as tasks activate or mature `status::ongoing` `priority::medium`
- [ ] **E0-008** Auto-standup retro-injection — extend `.claude/scripts/generate_standup.py` to read the prior sprint's `## Retrospective` Q4 ("One thing to change in Sprint N+1") and surface it as a Day 1 banner in the next sprint's first standup `status::todo` `priority::medium` `estimate::1h`
  - Closes the recurring ritual gap observed Sprint 001→002 (artifact-reference rule) and Sprint 002→003 (Day 1 ritual): retro Q4 action items get captured in `sprint-current.md` Daily Notes but not surfaced in the daily ceremony itself. Sprint 003 stretch.

### Sprint-Linked Meetings

- [x] **E0-060** Attend Apr 13 LSS meeting (3:00 PM); capture decisions on the 6 open F1 items into a meeting note in `scrum/standups/` and feed back to F1 spec `status::done` `priority::critical` `estimate::3h`
  - Sprint 001 commitment.
  - Done 2026-04-13. Meeting attended; notes ingested Apr 15 PM at `wiki/sources/Source - ASPSI Team Meeting 2026-04-13.md`. 6 F1 items were not on the agenda — decision-feedback step is N/A. E2-F1-009b tracked separately as blocked pending a technically-scoped LSS session.

### Stakeholder Communication

- [ ] **E0-010** Define weekly status update format (to ASPSI Management Committee) `status::todo` `priority::high` `estimate::2h`
- [ ] **E0-011** Send weekly status updates to ASPSI `status::todo` `priority::high` `estimate::recurring`
- [ ] **E0-012** Define monthly stakeholder brief format (DOH / ADB touchpoint) `status::todo` `priority::medium` `estimate::2h`
- [ ] **E0-013** Prepare monthly stakeholder brief `status::todo` `priority::medium` `estimate::recurring`
- [ ] **E0-014** Define ad-hoc client escalation protocol (what triggers escalation, who owns the call) `status::todo` `priority::medium` `estimate::2h`

### Ethics Coordination

- [ ] **E0-020** SJREB application status check (via ASPSI) — ongoing tracking until clearance received `status::in-progress` `priority::critical` `estimate::ongoing`
  - Notes: long-pole blocker for Epic 6 (Testing and Pilot) pretest phase
- [x] **E0-021** PSA sampling endorsement captured in approved Inception Report `status::done` `priority::critical`

### Risk & Change Management

- [ ] **E0-030** Maintain risk register in Product Backlog §5 `status::ongoing` `priority::high` `estimate::recurring`
- [ ] **E0-031** Define change request protocol for mid-engagement questionnaire revisions (intake form, impact assessment, backlog refresh) `status::todo` `priority::high` `estimate::4h`
- [ ] **E0-032** Track timeline vs deliverable deadlines (D2, D3, D4, D5, D6) weekly `status::ongoing` `priority::high` `estimate::recurring`
- [ ] **E0-033** Set up late delivery penalty tracker (1% of total per calendar day per CSA §5) — calculates exposure if deadlines slip `status::todo` `priority::medium` `estimate::2h`

### Project Governance (already done — baseline)

- [x] **E0-040** Project knowledge base scaffolded (raw/, deliverables/, wiki/, CLAUDE.md, index.md, log.md) `status::done`
- [x] **E0-041** CSA, TOR, Inception Report, Y1 Final Report, ASPSI Proposal, DOH TOR ingested into wiki `status::done`
- [x] **E0-042** Project Intelligence Brief authored (timeline, decisions, stakeholder dynamics, positioning) `status::done`
- [x] **E0-043** 12-phase CAPI Development Workflow codified into IT Standards as reusable template `status::done`
- [x] **E0-044** 13-epic service lifecycle derived from workflow and captured in Product Backlog `status::done`
- [x] **E0-045** Service Offerings area scaffolded at `2_Areas/Service-Offerings/CAPI-Development/` `status::done`

### Handoff Preparation *(activates near project close)*

- [ ] **E0-050** Stakeholder-facing close-out brief template `status::todo` `priority::low` `estimate::3h`
- [ ] **E0-051** Final acceptance letter checklist (what must the client sign off on) `status::todo` `priority::low` `estimate::2h`

## Notes

- This epic has a high proportion of `recurring` and `ongoing` tasks because it's a continuous workstream. Sprint planning should pull in the **active recurring ceremonies** plus any open one-time items relevant to the sprint period.
- Tasks E0-020 and E0-032 should appear in every sprint until resolved.
