# ASPSI-DOH CAPI CSPro Development

Computer-Assisted Personal Interviewing (CAPI) system development for ASPSI | DOH using CSPro and CSEntry, covering survey questionnaire design through CSWeb deployment.

## Project Structure

- `deliverables/` — authored outputs (applications, reports, documentation)
- `raw/` — inputs received (questionnaires, specs from DOH/ASPSI)
- `templates/` — reusable boilerplate for this project
- `wiki/` — LLM Wiki: deep domain knowledge for Claude sessions
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/CLAUDE|Project Schema (CLAUDE.md)]]
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/log|Wiki Log]]

## Wiki Catalog

### Sources
- [[wiki/sources/Source - Revised Inception Report]] — Project overview, methodology, sampling, team, timeline
- [[wiki/sources/Source - Annex F1 Facility Head Survey Questionnaire]] — 34-page questionnaire (Sections A–H + secondary data)
- [[wiki/sources/Source - Annex F2 Healthcare Worker Survey Questionnaire]] — 14-page self-administered questionnaire (Sections A–J)
- [[wiki/sources/Source - Annex F3 Patient Survey Questionnaire]] — 23-page CAPI questionnaire for outpatients/inpatients (Sections A–L)
- [[wiki/sources/Source - Annex F4 Household Survey Questionnaire]] — 26-page CAPI questionnaire, new for Year 2 (Sections A–Q)
- [[wiki/sources/Source - Patient Listing Form]] — 1-page patient recruitment form
- [[wiki/sources/Source - Facility Head Data Dictionary and Value Sets]] — CSPro dictionary structure and value sets for F1
- [[wiki/sources/Source - CSPro Documentation]] — Official Census Bureau documentation index (links to 7 PDFs, support, videos)
- [[wiki/sources/Source - CSPro 8.0 Complete Users Guide]] — 958-page authoritative reference (Designer, CSEntry, CSBatch, CSTab, dictionary, logic)
- [[wiki/sources/Source - CSPro Android CAPI Getting Started]] — 16-page MyCAPI_Intro tutorial walkthrough
- [[wiki/sources/Source - CSPro Android Data Transfer Guide]] — Operational guide for CSWeb / Dropbox / FTP / Bluetooth sync
- [[wiki/sources/Source - Signed CSA Dec 15 2025]] — Carl's signed Consultancy Services Agreement: 6.0 PM × PHP 65K = PHP 390,000 total, deliverable-based payment in 4 tranches, full TOR (10 duties), late penalty 1%/day
- [[wiki/sources/Source - IDinsight UHC Survey 2024 Final Report]] — Year 1 final report (224 pp, IDinsight). Baseline indicators, methodology, sample design, key findings, recommendations. Year 1 used SurveyCTO; Year 2 switches to CSPro.
- [[wiki/sources/Source - DOH TOR UHC Survey Year 2]] — Procurement TOR (REI No. 2025-001, 6 pp). ABC PhP 60M, 9-month duration, scope/deliverables/timeline, implementation arrangement, required qualifications.
- [[wiki/sources/Source - ASPSI Proposal Approach and Methodology]] — ASPSI's winning technical proposal (TPF 4). Sampling design, CAPI workflow (Figure 4.3), team composition (147.75 PM), field deployment plan (6 clusters), 102 UHC-IS + 17 non-UHC IS.

### Entities
- [[wiki/entities/ASPSI]] — Asian Social Project Services, Inc. (implementing organization)
- [[wiki/entities/DOH-PMSMD]] — DOH Performance Monitoring and Strategy Management Division (client)
- [[wiki/entities/SJREB]] — Single Joint Research Ethics Board (ethics clearance — critical blocker)
- [[wiki/entities/ADB]] — Asian Development Bank (technical advisor; Xylee Javier)
- [[wiki/entities/PSA]] — Philippine Statistics Authority (sampling endorsement)
- [[wiki/entities/IDinsight]] — Year 1 implementer (predecessor to ASPSI; Alec Lim is Year 2 reference contact)
- [[wiki/entities/US Census Bureau]] — Author/maintainer of CSPro, CSEntry, CSWeb

### Concepts

**Project domain**
- [[wiki/concepts/UHC Survey Year 2]] — Survey overview, modules, changes from Year 1
- [[wiki/concepts/CSPro]] — Census and Survey Processing System (overview)
- [[wiki/concepts/CSWeb]] — Web server for real-time monitoring and data sync

**CSPro toolchain (from the 8.0 Users Guide)**
- [[wiki/concepts/CSPro Data Dictionary]] — `.dcf` schema: levels, records, items, value sets, relations
- [[wiki/concepts/CSPro Language Fundamentals]] — PROC GLOBAL, declarations, logic objects, variables, expressions, operators
- [[wiki/concepts/CSPro Logic Events]] — preproc/postproc/onfocus/killfocus/onoccchange order of execution
- [[wiki/concepts/CSPro Data Entry Modes]] — system- vs operator-controlled, heads-up vs heads-down
- [[wiki/concepts/CSPro Capture Types]] — Text Box, Radio, Drop Down, Number Pad, Date, etc.
- [[wiki/concepts/CSPro CAPI Strategies]] — forms, fields, questions, blocks, partial save, prefilling
- [[wiki/concepts/CSPro Question Text and Fills]] — fills (`~~item~~`), HTML, conditional questions
- [[wiki/concepts/CSPro Multi-Language Applications]] — multi-language labels, `tr`, `setlanguage`
- [[wiki/concepts/CSPro Synchronization]] — sync architecture, `sync*` functions, troubleshooting
- [[wiki/concepts/CSPro Batch Editing]] — CSBatch, structure/validity/consistency checks, hot decks, imputation
- [[wiki/concepts/CSPro Tabulation]] — CSTab, cross-tabs, area processing, weights, summary stats

### Analyses
- [[wiki/analyses/Analysis - Project Intelligence Brief]] — Full project timeline, decisions, scope changes, blockers, stakeholder dynamics, Carl's positioning

## Deliverables

- `deliverables/CSPro/F1/FacilityHeadSurvey.dcf` — F1 CSPro 8.0 data dictionary v1 (10 records, 649 items) generated from the April 8 questionnaire. Pending Carl's validation in CSPro Designer.
- `deliverables/CSPro/F1/generate_dcf.py` — Reproducible Python generator for the F1 dictionary.
- `deliverables/CSPro/F1/F1-Skip-Logic-and-Validations.md` — Spec covering dcf sanity-check findings (6 bugs), full skip-logic table for all 166 questions, hard/soft/gate validations, and paste-ready CSPro PROC code templates.

## Vault Path

```
analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/
```
