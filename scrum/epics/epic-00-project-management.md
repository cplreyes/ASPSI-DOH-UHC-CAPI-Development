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

- [x] **E0-010** ~~Define weekly status update format (to ASPSI Management Committee)~~ **re-scoped 2026-04-30 → internal weekly status snapshot only** `status::done` `priority::high` `estimate::2h`
  - **Re-scoped 2026-04-30:** Format defined as `deliverables/comms/_weekly-status-template.md` and first instance at `deliverables/comms/weekly-status-2026-05-01.md`. Both are **internal-only artifacts** for Carl's tracking + project record — NOT for sending to ASPSI Mgmt or DOH. See memory `feedback_weekly_status_internal_only`.
- [ ] **E0-011** ~~Send weekly status updates to ASPSI~~ **out-of-scope for Data Programmer 2026-04-30** `status::out-of-scope` `priority::n/a`
  - **Re-scoped 2026-04-30:** With E0-010 redefined as internal-only, the recurring "send to ASPSI Mgmt" action is moot. Carl writes the weekly internal snapshot at sprint close as continuity for himself; no recurring stakeholder send is in his lane. See memory `feedback_weekly_status_internal_only`.
- [ ] **E0-012** ~~Define monthly stakeholder brief format (DOH / ADB touchpoint)~~ **out-of-scope for Data Programmer 2026-04-30** `status::out-of-scope` `priority::n/a`
  - **Re-scoped 2026-04-30:** Monthly DOH / ADB touchpoint briefs are stakeholder-coordination work owned by ASPSI ops / PI (Juvy / Dr Claro / Dr Paunlagui), not Data Programmer scope. See memory `feedback_data_programmer_scope`.
- [ ] **E0-013** ~~Prepare monthly stakeholder brief~~ **out-of-scope for Data Programmer 2026-04-30** `status::out-of-scope` `priority::n/a`
  - **Re-scoped 2026-04-30:** Same as E0-012 — stakeholder-facing brief preparation is ASPSI ops / PI work. See memory `feedback_data_programmer_scope`.
- [ ] **E0-014** ~~Define ad-hoc client escalation protocol (what triggers escalation, who owns the call)~~ **out-of-scope for Data Programmer 2026-04-30** `status::out-of-scope` `priority::n/a`
  - **Re-scoped 2026-04-30:** Escalation protocol definition is project-management work owned by ASPSI ops / PI / PMO, not Data Programmer scope. The Apr 13 Team Communication Protocol already routes escalations through Dr Claro / Dr Paunlagui. See memory `feedback_data_programmer_scope`.

### Ethics Coordination

- [ ] **E0-020** ~~SJREB application status check (via ASPSI)~~ **out-of-scope for Data Programmer 2026-04-30** `status::out-of-scope` `priority::n/a`
  - **Re-scoped 2026-04-30:** SJREB tracking is in ASPSI ops / PI lane (Dr Claro, Dr Paunlagui, Juvy as PMO), not Data Programmer scope per the signed CSA's TOR + Personnel Schedule. SJREB remains a project-level dependency for Epic 6 (Testing and Pilot) pretest timelines and stays visible in `wiki/entities/SJREB.md` and the risk register, but is no longer a Carl-owned recurring task. See memory `feedback_sjreb_out_of_scope`.
- [x] **E0-021** PSA sampling endorsement captured in approved Inception Report `status::done` `priority::critical`

### Risk & Change Management

- [ ] **E0-030** Maintain risk register in Product Backlog §5 `status::ambiguous` `priority::tbd` `estimate::recurring`
  - **Pending Carl decision 2026-04-30:** Risk register stewardship is borderline — Carl needs *awareness* of risks affecting his CAPI work but *active register maintenance* is PM work. Pending Carl's call on whether informational consumption is enough vs. owning the register. See memory `feedback_data_programmer_scope` § Ambiguous.
- [ ] **E0-031** ~~Define change request protocol for mid-engagement questionnaire revisions (intake form, impact assessment, backlog refresh)~~ **out-of-scope for Data Programmer 2026-04-30** `status::out-of-scope` `priority::n/a`
  - **Re-scoped 2026-04-30:** Change-request protocol design is project-management work owned by ASPSI ops / PI / PMO. Carl's role on a CR is *technical impact assessment* (a specific incoming task), not protocol design. See memory `feedback_data_programmer_scope`.
- [ ] **E0-032** ~~Track timeline vs deliverable deadlines (D2, D3, D4, D5, D6) weekly~~ **out-of-scope for Data Programmer 2026-04-30** `status::out-of-scope` `priority::n/a`
  - **Re-scoped 2026-04-30:** Tranche / deliverable deadline tracking is in ASPSI ops / PI / PMO lane, not Data Programmer scope. Tranche state can appear in the weekly internal snapshot's *Tranche / deliverable position* section as informational project context (Carl needs awareness for his own work planning), but active tracking, deadline confirmations from DOH, and submission timing are not Carl's concern. See memory `feedback_tranche_tracking_out_of_scope`.
- [ ] **E0-033** ~~Set up late delivery penalty tracker (1% of total per calendar day per CSA §5)~~ **out-of-scope for Data Programmer 2026-04-30** `status::out-of-scope` `priority::n/a`
  - **Re-scoped 2026-04-30:** Financial / penalty exposure tracking is ASPSI ops / PMO work, not Data Programmer scope. See memory `feedback_tranche_tracking_out_of_scope` and `feedback_data_programmer_scope`.

### Project Governance (already done — baseline)

- [x] **E0-040** Project knowledge base scaffolded (raw/, deliverables/, wiki/, CLAUDE.md, index.md, log.md) `status::done`
- [x] **E0-041** CSA, TOR, Inception Report, Y1 Final Report, ASPSI Proposal, DOH TOR ingested into wiki `status::done`
- [x] **E0-042** Project Intelligence Brief authored (timeline, decisions, stakeholder dynamics, positioning) `status::done`
- [x] **E0-043** 12-phase CAPI Development Workflow codified into IT Standards as reusable template `status::done`
- [x] **E0-044** 13-epic service lifecycle derived from workflow and captured in Product Backlog `status::done`
- [x] **E0-045** Service Offerings area scaffolded at `2_Areas/Service-Offerings/CAPI-Development/` `status::done`

### Handoff Preparation *(activates near project close)*

- [ ] **E0-050** ~~Stakeholder-facing close-out brief template~~ **out-of-scope for Data Programmer 2026-04-30** `status::out-of-scope` `priority::n/a`
  - **Re-scoped 2026-04-30:** Stakeholder-facing close-out artifacts are ASPSI ops / PI work. Carl's close-out scope is **technical handoff** of the CAPI codebases, dictionaries, generators, and final-state documentation under D5 / D6 — surfaced separately in Epic 12 (Handover, Closeout & Retrospective). See memory `feedback_data_programmer_scope`.
- [ ] **E0-051** ~~Final acceptance letter checklist (what must the client sign off on)~~ **out-of-scope for Data Programmer 2026-04-30** `status::out-of-scope` `priority::n/a`
  - **Re-scoped 2026-04-30:** Acceptance routing is ASPSI↔DOH process; Carl provides technical sign-off readiness on CAPI deliverables, not the acceptance protocol design. See memory `feedback_data_programmer_scope`.

## Notes

- This epic has a high proportion of `recurring` and `ongoing` tasks because it's a continuous workstream. Sprint planning should pull in the **active recurring ceremonies** plus any open one-time items relevant to the sprint period.
- **Major role-scope cleanup 2026-04-30.** This epic's center of gravity was originally *project management & stakeholder engagement*, much of which sits in ASPSI ops / PI / PMO lane rather than Data Programmer scope. The 2026-04-30 re-scope marked **E0-011 / E0-012 / E0-013 / E0-014 / E0-020 / E0-031 / E0-032 / E0-033 / E0-050 / E0-051** as out-of-scope; **E0-010** redefined as internal-only and closed; **E0-030** (risk register) flagged ambiguous pending Carl's call. The remaining Carl-owned items in this epic are **E0-008** (auto-standup retro-injection tooling) — purely internal scrum infrastructure. See memory `feedback_data_programmer_scope` for the IN/OUT scope reference.
