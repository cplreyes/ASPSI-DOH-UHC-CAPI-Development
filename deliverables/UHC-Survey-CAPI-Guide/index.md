---
title: "UHC Survey Year 2 — CAPI Implementation Guide"
category: deliverable
tags: [capi, cspro, csweb, csentry, uhc, doh, aspsi, implementation-guide]
last_updated: 2026-05-08
status: draft-complete
---

# UHC Survey Year 2 — CAPI Implementation Guide

End-to-end implementation guide for the **F1 Facility Head**, **F3 Patient**, and **F4 Household** instruments of the DOH UHC Year 2 Survey, built on **CSPro Designer + CSEntry Android + CSWeb**. The F2 Healthcare Worker instrument runs on the parallel PWA track and is referenced where it intersects (shared case-ID convention, shared backend operations).

> **Mentor lineage**: Patterns marked **(Khurshid YYYY-MM-DD)** trace back to a specific tutorial in the [[3_Resources/Learning-Materials/mentors/khurshid-arshad/_index|Khurshid Arshad CAPI corpus]] (74 videos, phase-tagged).

> **Workflow lineage**: This guide is the UHC Year 2 instance of the reusable [[2_Areas/IT-Standards/templates/CAPI-Development-Workflow|CAPI Development Workflow]] living-document template.

---

## Read order by audience

### If you are the CAPI Developer (Carl)
Start with `00` → `01` → `02` → `03` → `04` → `05` → `06` → `07` → `08`. Skim the role section of `01`, then go deep on every phase.

### If you are the CAPI QA Tester (Shan)
`00` for the system map, then `05` (testing) and `99` (your role's cheat sheet). Skim `04` so you know what patterns to test against.

### If you are the CSWeb Administrator
`00` for the system map, then `06` (provisioning + tablet bring-up) is your build doc and `07` (fieldwork) is your runbook. `99` has your daily-ops cheat sheet.

### If you are a Survey Team Leader / Field Manager / Enumerator
`00` for the system map, `07` (pretest + fieldwork) for the work itself, `99` for the cheat sheet you actually carry.

### If you are the Project Coordinator (Juvy) or Project Lead (Dr Claro)
`00` (system map) + `01` (roles + handoffs) + `99` (your cheat sheet) is enough for client-facing comms. Read `07` once to understand the fieldwork rhythm.

---

## File map

| File | Phases | What's inside |
|---|---|---|
| [[00-Architecture]] | — | System diagram, data flow, components, network topology, storage decisions, case-ID convention |
| [[01-Roles-and-Handoffs]] | — | Role definitions, RACI per phase, handoff matrix, escalation paths, ASPSI comms protocol |
| [[02-Phase-0-2-Foundation]] | 0, 1, 2 | Project scaffolding, source ingestion, tool knowledge base |
| [[03-Phase-3-5-Spec-and-Generators]] | 3, 4, 5 | Python `.dcf` generator, skip-logic spec, three-tier validation, fieldwork-time corrections |
| [[04-Phase-6-Build-CAPI-App]] | 6 | Forms, `.apc` logic, multi-language, `FIELD_CONTROL`, GPS+photo, durable resume, dynamic value sets |
| [[05-Phase-7-Testing]] | 7 | Desk test, bench mock cases, regression-as-data, Android file-based trace |
| [[06-Phase-8-CSWeb-and-Tablets]] | 8 | Wampserver + CSWeb provisioning, MySQL backing DB, tablet bring-up, sync URL, PFF packaging |
| [[07-Phase-9-10-Pretest-Fieldwork]] | 9, 10 | SJREB, pretest, training, daily monitoring, hot-fix protocol, CSBatch + CSTab |
| [[08-Phase-11-Closeout-Export]] | 11 | STATA/SPSS export pipelines, Task Scheduler unattended runs, archive, lessons-learned |
| [[99-Quick-Reference]] | — | One-page cheat sheets per role |

---

## How to use this guide

1. **Don't read it linearly cover-to-cover.** Use the audience map above.
2. **Every code snippet is paste-ready** — but read the surrounding context, especially Khurshid citations, before applying.
3. **Treat it as a living document.** When fieldwork teaches you something, append to the relevant phase doc and bump the `last_updated` field.
4. **Cite back.** When you do something this guide tells you to do, link the artifact you produce back to the relevant section so the next person can trace your reasoning.

---

## Document status

| File | Lines | Status | Owner |
|---|---:|---|---|
| 00-Architecture | 916 | draft | Carl |
| 01-Roles-and-Handoffs | 748 | draft | Carl |
| 02-Phase-0-2-Foundation | 794 | draft | Carl |
| 03-Phase-3-5-Spec-and-Generators | 1,384 | draft | Carl |
| 04-Phase-6-Build-CAPI-App | 2,389 | draft | Carl |
| 05-Phase-7-Testing | 848 | draft | Carl |
| 06-Phase-8-CSWeb-and-Tablets | 1,934 | draft | Carl |
| 07-Phase-9-10-Pretest-Fieldwork | 1,677 | draft | Carl |
| 08-Phase-11-Closeout-Export | 1,188 | draft | Carl |
| 99-Quick-Reference | 792 | draft | Carl |
| **Total** | **12,670** |  |  |

All 10 content files are first-draft complete (2026-05-08). Next pass: walkthrough review, cross-link verification, append Khurshid date checks, and update each file's `status:` to `reviewed` once Carl signs off.
