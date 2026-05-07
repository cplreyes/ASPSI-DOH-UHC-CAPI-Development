---
epic: 0
title: CAPI Project Management & Stakeholder Engagement
phase: continuous
status: active-ongoing
last_updated: 2026-05-08
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
- [x] **E0-040** Backlog ledger + GH Project #8 governance setup — **Closed 2026-05-06 (Sprint 004 Day 3).** Out-of-sprint tooling work surfaced from PO-visibility ask. Stamped `scrum::<slot>` on 136 epic-file tasks via `.claude/scripts/tag_backlog_slots.py` (idempotent, sprint-rollover-friendly). Built two Dataview surfaces for Obsidian-side grooming: `scrum/backlog-groom.md` (5 query blocks: active sprint / next sprint / Carl-lane unscheduled / out-of-scope / count snapshot) and `scrum/backlog-board.md` (kanban-shape pivot of slot × priority + sprint-current status pivot). Project #8 expanded from F2-Admin-only to umbrella backlog: renamed to "UHC CAPI - Backlog"; added Priority/Sprint Slot/Epic single-select fields with 4/3/12 options respectively; bulk-imported 94 in-scope unscheduled drafts via `setup_project_8_full_backlog.py` (regex fixed to allow lowercase IDs after first run missed CSWeb-001..007 + F1-043a/b); imported 22 historical sprint cards via `import_historical_sprints.py` (sprint-001..004 latest-occurrence-wins); filed 5 new Sprint 005 tickets in `epic-04` (E4-APRT-043 prod-hash sunset, E4-APRT-046 Files: Create Folder, E4-APRT-047 Files: Rename, E4-APRT-048 last_login_at write, E4-APRT-049 design-review sweep umbrella) + cross-linked via `tracked::#NN`; closed 3 stale items retroactively (E4-PWA-013 Phase F, E4-PWA-014 CF Pages auto-deploy, E4-PWA-015 PBKDF2 cap); flipped E0-001 + E2-F1-009b done in `sprint-001.md` and deleted 3 out-of-scope drafts (E0-020/032/032a). Final state: 134 cards on Project #8 (15 Done / 119 Open / sprint-001..005 + unscheduled). Reusable scripts: `tag_backlog_slots.py`, `setup_project_8_sprint_005.py`, `setup_project_8_full_backlog.py`, `import_historical_sprints.py`, `resume_field_assignment.py`, `add_review_status.py` (all under `.claude/scripts/`). `status::done` `priority::medium` `actual::~3h`
- [x] **E0-041** Markdown↔GH Project auto-sync hook — **Closed 2026-05-06 (Sprint 004 Day 3).** Wrote `.claude/scripts/sync-markdown-to-gh.py` invoked from existing `.git/hooks/post-commit` (alongside parse-task-changes.py Slack notifier). Reads same git diff format; for each changed task line in `scrum/epics/*.md` or `scrum/sprint-current.md`, syncs to Project #8: `[ ]→[x]` closes the linked issue (via `tracked::#NN`) or sets Status:Done on draft; `scrum::<slot>` change updates Sprint Slot field; `status::<value>` change updates Status field (mapped: todo/in-progress/review/done); `priority::<value>` change updates Priority field. Background, non-blocking, ~3-4 sec per commit. Logs to `sync-markdown-to-gh.log`. End-to-end tested: priority high→medium→high round-trip on E4-APRT-037 / issue #63 succeeded both directions; retroactive E0-001 + E2-F1-009b closures auto-flipped Status:Done on GH within seconds. `status::done` `priority::medium` `actual::~1.5h`
- [x] **E0-042** Slack sprint snapshot workflow — **Closed 2026-05-06 (Sprint 004 Day 3).** GitHub Action at `.github/workflows/sprint-snapshot.yml` posts cross-sprint Done/Open/Total summary table to #capi-scrum on cron triggers (Mon 00:00 UTC = 08:00 PHT for kickoff; Fri 10:00 UTC = 18:00 PHT for closeout) plus `workflow_dispatch` for manual runs. Generator at `.github/scripts/post_sprint_snapshot.py` queries Project #8 via GraphQL (renders monospace table per sprint slot), authenticated via `GH_PROJECTS_TOKEN` repo secret (PAT with read:project). Slack post via `SLACK_WEBHOOK_URL` repo secret. Caught + fixed: regex truncation that mangled webhook URL on first secret-set; section-detection bug where Definition-of-Done items leaked into Stretch bucket; cp1252 console encoding crashes on em-dashes (PYTHONIOENCODING=utf-8). Tested via `gh workflow run --ref f2-admin-portal -f mode=start` — Slack post landed in #capi-scrum with the 134-card breakdown. `status::done` `priority::medium` `actual::~1h`

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

### Knowledge Base & Living Document Maintenance *(post-2026-05-08 audit)*

- [ ] **E0-070** Fold May 8 audit findings into the workflow template living-doc log `status::todo` `priority::high` `estimate::1h` `scrum::sprint-005`
  - **Trigger:** UHC-Survey-CAPI-Guide drafting + 5-gap audit completed 2026-05-08. The `2_Areas/IT-Standards/templates/CAPI-Development-Workflow.md` is a living document; per `project_capi_workflow.md` memory, learnings from each engagement compound into it.
  - **Deliverable:** Append a row to the "Living-document log" table at the end of the template covering: (a) the 5 audit gaps surfaced + their resolutions; (b) the new "Phases vs Epics" naming convention codified in scrum/README; (c) cross-link to the UHC-Year-2 instance at `1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/UHC-Survey-CAPI-Guide/`.
- [x] **E0-080** Phase ↔ Epic cross-walk note in scrum/README.md `status::done` `priority::medium` `actual::2026-05-08`
  - Done 2026-05-08 alongside Bucket A scrum cleanup. Cross-walk codified at `scrum/README.md` "Phases vs epics" section.

### Handoff Preparation *(activates near project close — ASPSI/PI/PMO lane)*

> **Scope:** Stakeholder-facing close-out artifacts are PM/PI/PMO lane per `feedback_data_programmer_scope.md`. Carl's close-out work lives in Epic 12 (system handover package, technical runbook, knowledge-transfer sessions, NDU file disposition, retrospective writeback) — *not* the stakeholder-facing brief or acceptance-letter checklist.

- [ ] **E0-050** Stakeholder-facing close-out brief template `status::todo` `priority::low` `estimate::3h` `out_of_scope::data_programmer` `owner::aspsi-pi-pmo` `scrum::unscheduled`
- [ ] **E0-051** Final acceptance letter checklist (what must the client sign off on) `status::todo` `priority::low` `estimate::2h` `out_of_scope::data_programmer` `owner::aspsi-pi-pmo` `scrum::unscheduled`

## Notes

- This epic has a high proportion of `recurring` and `ongoing` tasks because it's a continuous workstream. **Most are NOT Data Programmer scope** — they're tracked here for project-level visibility but should not auto-pull into Carl's sprints. Sprint planning should pull in the **active recurring ceremonies that are explicitly in Data Programmer scope** (currently: E0-001 sprint planning, E0-002 retros, E0-006 PB upkeep, E0-007 epic upkeep) plus any open one-time items.
- **Out-of-scope guard:** Items annotated `out_of_scope::data_programmer` (currently E0-011, E0-012, E0-013, E0-014, E0-020, E0-032, E0-032a, E0-033, E0-050, E0-051) must NOT be added to `sprint-current.md` as Carl-owned tasks. They live in ASPSI ops / PI / PMO lane (Juvy / Dr Claro / Dr Paunlagui). See `feedback_data_programmer_scope.md` umbrella for the full IN/OUT-of-scope reference.
- **In-scope E0 items** (the ones that should pull into sprints): E0-001, E0-002, E0-003, E0-006, E0-007, E0-008, E0-010 (define internal format only). E0-030 (risk register) is informational consumption only. E0-031 (change-request protocol) is borderline — protocol design is PM lane, but CAPI-side CR handling fold into E2/E3.
- Sprint 003 (2026-04-27 → 2026-05-01) leaked E0-020, E0-032, and E0-032a back into the sprint board despite the umbrella memory rule; cleanup performed at sprint close 2026-05-01. Audit-on-detection discipline added to the relevant memory files so this doesn't slip again.
