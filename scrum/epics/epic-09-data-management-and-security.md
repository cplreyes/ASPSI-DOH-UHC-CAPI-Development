---
epic: 9
title: Data Management and Security
phase: continuous
status: governance-active
last_updated: 2026-04-10
---

# Epic 9 — Data Management and Security

Continuous governance workstream covering data privacy compliance, security architecture, access control, backup strategy, and retention policy. Runs for the full engagement with concrete deliverables staged around Epic 4 (CSWeb) and Epic 8 (Fieldwork Monitoring).

**Ties to Product Backlog:** [[../product-backlog#Epic 9 — Data Management and Security|PB Epic 9]]

## Task conventions

- Task IDs: `E9-NNN`
- Many tasks here are policy deliverables (documents) rather than code

## Tasks

### Legal & Governance Baseline *(already in force)*

- [x] **E9-001** Non-Disclosure Undertaking signed (2025-12-12) `status::done` `priority::critical`
- [x] **E9-002** RA 10173 (Data Privacy Act), RA 8293 (IP Code), RA 10175 (Cybercrime Prevention) obligations acknowledged under NDU `status::done` `priority::critical`
- [x] **E9-003** CSA confidentiality clauses (§10g, §11) in force `status::done` `priority::critical`
- [ ] **E9-004** Maintain NDU compliance throughout engagement (no disclosure of project materials without ASPSI/DOH written consent) `status::ongoing` `priority::critical`

### Privacy & PII Policy

- [ ] **E9-010** PII inventory per instrument — what personally identifiable data does each questionnaire collect? `status::todo` `priority::high` `estimate::4h`
  - Depends on: E2 design passes for each instrument
- [ ] **E9-011** Data minimization review — are there fields we collect but don't need? `status::todo` `priority::medium` `estimate::2h`
- [ ] **E9-012** PII handling protocol document (in transit, at rest, in analysis) `status::todo` `priority::high` `estimate::4h`
- [ ] **E9-013** Data subject rights procedure per RA 10173 (access, rectification, erasure, objection) — how respondents exercise rights during/after fieldwork `status::todo` `priority::medium` `estimate::3h`
- [ ] **E9-014** Consent form wording review with privacy in mind (what are respondents consenting to?) `status::todo` `priority::high` `estimate::2h`

### Infrastructure Security

- [ ] **E9-020** Encryption at rest specification (tablet storage, server storage) `status::todo` `priority::high` `estimate::2h`
- [ ] **E9-021** Encryption in transit specification (sync channel tablet → CSWeb) `status::todo` `priority::high` `estimate::2h`
- [ ] **E9-022** CSWeb server access control policy (who can read, who can export, who can admin) `status::todo` `priority::high` `estimate::3h`
  - Depends on: Epic 4 CSWeb stand-up
- [ ] **E9-023** Authentication model — define roles (interviewer / supervisor / admin / analyst) and credentials per role `status::todo` `priority::high` `estimate::3h`
- [ ] **E9-024** Audit trail design — what data access events are logged, retention of log `status::todo` `priority::medium` `estimate::2h`
- [ ] **E9-025** Tablet lock-screen + device encryption policy for enumerators `status::todo` `priority::high` `estimate::2h`

### Backup & Recovery

- [ ] **E9-030** Backup strategy for server-side data (frequency, location, redundancy) `status::todo` `priority::high` `estimate::3h`
- [ ] **E9-031** Backup strategy for tablet-side data mid-interview (partial save, auto-save) `status::todo` `priority::high` `estimate::2h`
- [ ] **E9-032** Recovery test protocol — can we actually restore from backup? `status::todo` `priority::medium` `estimate::4h`
- [ ] **E9-033** Off-site backup decision (is local backup sufficient? does DOH require a secondary copy?) `status::todo` `priority::medium` `estimate::1h`

### Data Retention & Destruction

- [ ] **E9-040** Data retention policy — how long is respondent data held? Whose policy governs (DOH? RA 10173 default?) `status::todo` `priority::high` `estimate::2h`
- [ ] **E9-041** Audit log retention policy `status::todo` `priority::medium` `estimate::1h`
- [ ] **E9-042** NDU-compliant file turn-over / destruction plan for project close (covers Epic 12 Handover) `status::todo` `priority::high` `estimate::3h`
  - Defines: what transfers to client, what is destroyed, what (if anything) Carl retains under what terms
- [ ] **E9-043** Secure destruction procedure for tablets post-fieldwork (factory reset + cryptographic wipe) `status::todo` `priority::medium` `estimate::2h`

### Incident Response

- [ ] **E9-050** Data breach response protocol (what if a tablet is lost? what if server is compromised?) `status::todo` `priority::medium` `estimate::3h`
- [ ] **E9-051** Incident escalation chain (Carl → ASPSI → DOH → NPC reporting if required) `status::todo` `priority::medium` `estimate::2h`

## Notes

- This epic is **policy-heavy, not code-heavy**. Most tasks produce documents that will later be referenced by other epics (especially Epic 4 CSWeb, Epic 5 Tablets, Epic 12 Handover).
- The National Privacy Commission (NPC) may have reporting requirements for breaches affecting sensitive personal information (RA 10173 §20). E9-051 should account for this.
- Several tasks have natural dependencies on Epic 4 (CSWeb stand-up) — sequence them for the sprint that activates Epic 4.
