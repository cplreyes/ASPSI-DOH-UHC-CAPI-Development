---
epic: 0
title: CAPI Project Management & Stakeholder Engagement
phase: continuous
status: active-ongoing
last_updated: 2026-05-01
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

- [ ] **E0-001** Run sprint planning ceremony each sprint (select items from epic files → sprint-current.md, set sprint goal, confirm dates) `status::ongoing` `priority::high` `estimate::recurring` `scrum::unscheduled`
  - Sprint 001 planned 2026-04-13 — first execution of this ceremony.
- [ ] **E0-002** Run sprint review + retrospective each sprint close (archive sprint to `sprints/`, capture lessons, update backlog) `status::todo` `priority::high` `estimate::recurring` `scrum::unscheduled`
- [ ] **E0-003** Backlog grooming session mid-sprint (refine upcoming epic tasks, adjust estimates) `status::todo` `priority::medium` `estimate::recurring` `scrum::unscheduled`
- [x] **E0-004** Adopt Scrum discipline with per-project Product Backlog, Sprint Backlog, standups `status::done` `priority::high`
- [x] **E0-005** Build `/daily-standup` slash command reading PB + sprint backlog `status::done` `priority::medium`
- [ ] **E0-006** Keep Product Backlog `last_updated` current each sprint close `status::ongoing` `priority::medium` `scrum::unscheduled`
- [ ] **E0-007** Maintain epic files as tasks activate or mature `status::ongoing` `priority::medium` `scrum::unscheduled`
- [ ] **E0-008** Auto-standup retro-injection — extend `.claude/scripts/generate_standup.py` to read the prior sprint's `## Retrospective` Q4 ("One thing to change in Sprint N+1") and surface it as a Day 1 banner in the next sprint's first standup `status::todo` `priority::medium` `estimate::1h` `scrum::sprint-004`
  - Closes the recurring ritual gap observed Sprint 001→002 (artifact-reference rule) and Sprint 002→003 (Day 1 ritual): retro Q4 action items get captured in `sprint-current.md` Daily Notes but not surfaced in the daily ceremony itself. Sprint 003 stretch.

### Sprint-Linked Meetings

- [x] **E0-060** Attend Apr 13 LSS meeting (3:00 PM); capture decisions on the 6 open F1 items into a meeting note in `scrum/standups/` and feed back to F1 spec `status::done` `priority::critical` `estimate::3h`
  - Sprint 001 commitment.
  - Done 2026-04-13. Meeting attended; notes ingested Apr 15 PM at `wiki/sources/Source - ASPSI Team Meeting 2026-04-13.md`. 6 F1 items were not on the agenda — decision-feedback step is N/A. E2-F1-009b tracked separately as blocked pending a technically-scoped LSS session.

### Stakeholder Communication

> **Scope split:** Carl owns the *internal* status format (E0-010) for his own tracking + project record per `feedback_weekly_status_internal_only.md`. Recurring stakeholder-facing sends, brief preparation, and escalation-protocol design are PM/PI/PMO lane (Juvy / Dr Claro / Dr Paunlagui) per `feedback_data_programmer_scope.md` and `feedback_comms_lane_discipline.md`.

- [x] **E0-010** Define weekly status update format — *internal-only* (Carl's tracking + project record, not for ASPSI Mgmt or DOH send). **Closed 2026-05-04 (Sprint 004 Day 1).** Template at `deliverables/comms/_weekly-status-template.md` v1.0 stable; week-1 instance at `weekly-status-2026-05-01.md` proved the structure; refinements folded back into template. `status::done` `priority::high` `actual::~30m close (template was already mature from partial-start in Sprint 003)`
- [ ] **E0-011** Send weekly status updates to ASPSI `status::todo` `priority::high` `estimate::recurring` `out_of_scope::data_programmer` `owner::aspsi-pi-pmo` `scrum::unscheduled`
  - Recurring stakeholder-facing send. Per `feedback_weekly_status_internal_only.md`, no recurring send happens from Carl; the internal artifact (E0-010) stays internal. If/when ASPSI wants a stakeholder-facing weekly, ASPSI/PMO authors and ships it.
- [ ] **E0-012** Define monthly stakeholder brief format (DOH / ADB touchpoint) `status::todo` `priority::medium` `estimate::2h` `out_of_scope::data_programmer` `owner::aspsi-pi-pmo` `scrum::unscheduled`
  - Stakeholder-facing brief format design. PM/PI lane.
- [ ] **E0-013** Prepare monthly stakeholder brief `status::todo` `priority::medium` `estimate::recurring` `out_of_scope::data_programmer` `owner::aspsi-pi-pmo` `scrum::unscheduled`
  - Recurring stakeholder-facing send to DOH / ADB. Out per `feedback_comms_lane_discipline.md`.
- [ ] **E0-014** Define ad-hoc client escalation protocol (what triggers escalation, who owns the call) `status::todo` `priority::medium` `estimate::2h` `out_of_scope::data_programmer` `owner::aspsi-pi-pmo` `scrum::unscheduled`
  - Escalation-protocol design = PM/PI lane per `feedback_data_programmer_scope.md`.

### Ethics Coordination *(ASPSI/PI lane — NOT Data Programmer scope)*

> **Scope:** Ethics coordination is owned by ASPSI ops / PI (Dr Claro, Dr Paunlagui, Juvy as PMO) per the signed CSA D1–D6 (TOR + Personnel Schedule). Items below are tracked here for project-level visibility; do not pull into Carl's sprint backlog. See `feedback_sjreb_out_of_scope.md` and `feedback_data_programmer_scope.md`.

- [ ] **E0-020** SJREB application status check (via ASPSI) — ongoing tracking until clearance received `status::in-progress` `priority::critical` `estimate::ongoing` `out_of_scope::data_programmer` `owner::aspsi-pi` `scrum::unscheduled`
  - Notes: long-pole blocker for Epic 6 (Testing and Pilot) pretest phase. Project-level dependency, not Carl-actionable.
- [x] **E0-021** PSA sampling endorsement captured in approved Inception Report `status::done` `priority::critical`

### Risk & Change Management

- [ ] **E0-030** Maintain risk register in Product Backlog §5 `status::ongoing` `priority::high` `estimate::recurring` *(informational consumption only — active risk-register stewardship is PM/PI work)* `scrum::unscheduled`
- [ ] **E0-031** Define change request protocol for mid-engagement questionnaire revisions (intake form, impact assessment, backlog refresh) `status::todo` `priority::high` `estimate::4h` *(protocol-design is PM lane; CAPI-side revisions arising from CRs land under E2/E3 instrument tasks)* `scrum::unscheduled`
- [ ] **E0-032** Track timeline vs deliverable deadlines (D2, D3, D4, D5, D6) weekly `status::ongoing` `priority::high` `estimate::recurring` `out_of_scope::data_programmer` `owner::aspsi-pi-pmo` `scrum::unscheduled`
  - Tranche / deadline tracking owned by ASPSI ops / PI / PMO. Carl is responsible for *production* of the deliverables (D1–D6), not the schedule on which they are accepted and paid. Project-level dependency only; surface in PIB / risk register, not in Carl's sprint backlog. See `feedback_tranche_tracking_out_of_scope.md`.
- [ ] **E0-032a** DOH-PMSMD matrix feedback triage — route requested revisions through the appropriate workstream `status::ongoing` `priority::high` `estimate::recurring` `out_of_scope::data_programmer` `owner::aspsi-pi-pmo` `scrum::unscheduled`
  - Coordination overhead (matrix dispositioning, DOH-side comms) is ASPSI/PI lane. CAPI-technical fallout (specific F1/F2/F3/F4 revisions) folds into the relevant E2/E3 instrument task — not tracked under E0-032a. See `feedback_e0_032a_out_of_scope.md`.
- [ ] **E0-033** Set up late delivery penalty tracker (1% of total per calendar day per CSA §5) — calculates exposure if deadlines slip `status::todo` `priority::medium` `estimate::2h` `out_of_scope::data_programmer` `owner::aspsi-pi-pmo` `scrum::unscheduled`
  - Financial / penalty exposure tracking is PM/PI/PMO lane. See `feedback_data_programmer_scope.md`.

### Project Governance (already done — baseline)

- [x] **E0-040** Project knowledge base scaffolded (raw/, deliverables/, wiki/, CLAUDE.md, index.md, log.md) `status::done`
- [x] **E0-041** CSA, TOR, Inception Report, Y1 Final Report, ASPSI Proposal, DOH TOR ingested into wiki `status::done`
- [x] **E0-042** Project Intelligence Brief authored (timeline, decisions, stakeholder dynamics, positioning) `status::done`
- [x] **E0-043** 12-phase CAPI Development Workflow codified into IT Standards as reusable template `status::done`
- [x] **E0-044** 13-epic service lifecycle derived from workflow and captured in Product Backlog `status::done`
- [x] **E0-045** Service Offerings area scaffolded at `2_Areas/Service-Offerings/CAPI-Development/` `status::done`

### Handoff Preparation *(activates near project close — ASPSI/PI/PMO lane)*

> **Scope:** Stakeholder-facing close-out artifacts are PM/PI/PMO lane per `feedback_data_programmer_scope.md`. Carl's close-out work lives in Epic 12 (system handover package, technical runbook, knowledge-transfer sessions, NDU file disposition, retrospective writeback) — *not* the stakeholder-facing brief or acceptance-letter checklist.

- [ ] **E0-050** Stakeholder-facing close-out brief template `status::todo` `priority::low` `estimate::3h` `out_of_scope::data_programmer` `owner::aspsi-pi-pmo` `scrum::unscheduled`
- [ ] **E0-051** Final acceptance letter checklist (what must the client sign off on) `status::todo` `priority::low` `estimate::2h` `out_of_scope::data_programmer` `owner::aspsi-pi-pmo` `scrum::unscheduled`

## Notes

- This epic has a high proportion of `recurring` and `ongoing` tasks because it's a continuous workstream. **Most are NOT Data Programmer scope** — they're tracked here for project-level visibility but should not auto-pull into Carl's sprints. Sprint planning should pull in the **active recurring ceremonies that are explicitly in Data Programmer scope** (currently: E0-001 sprint planning, E0-002 retros, E0-006 PB upkeep, E0-007 epic upkeep) plus any open one-time items.
- **Out-of-scope guard:** Items annotated `out_of_scope::data_programmer` (currently E0-011, E0-012, E0-013, E0-014, E0-020, E0-032, E0-032a, E0-033, E0-050, E0-051) must NOT be added to `sprint-current.md` as Carl-owned tasks. They live in ASPSI ops / PI / PMO lane (Juvy / Dr Claro / Dr Paunlagui). See `feedback_data_programmer_scope.md` umbrella for the full IN/OUT-of-scope reference.
- **In-scope E0 items** (the ones that should pull into sprints): E0-001, E0-002, E0-003, E0-006, E0-007, E0-008, E0-010 (define internal format only). E0-030 (risk register) is informational consumption only. E0-031 (change-request protocol) is borderline — protocol design is PM lane, but CAPI-side CR handling fold into E2/E3.
- Sprint 003 (2026-04-27 → 2026-05-01) leaked E0-020, E0-032, and E0-032a back into the sprint board despite the umbrella memory rule; cleanup performed at sprint close 2026-05-01. Audit-on-detection discipline added to the relevant memory files so this doesn't slip again.
