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
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Revised Inception Report]] — **Apr 20 PDF ver.** Project overview, Section V methodology (1,521 F1 / 2,672 F4 / 45 OP + 30 IP patients per domain), 18 tables + 7 figures, Del-1 through Del-4 timeline, PHP 59.48M total budget
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F1 Facility Head Survey Questionnaire]] — **Apr 20 ver.** 37 pp, 166 items (Sections A–H + Secondary Data); +40 items vs Apr 08
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F2 Healthcare Worker Survey Questionnaire]] — **Apr 20 ver.** 124 items across 125 numbered slots (Q108 gap), self-admin (Sections A–J)
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3 Patient Survey Questionnaire]] — **Apr 20 ver.** 178 items, CAPI inpatient+outpatient (Sections A–L); +52 items vs Apr 08
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F4 Household Survey Questionnaire]] — **Apr 20 ver.** 202 items, community survey (Sections A–Q); interval sampling from patient HH
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3b Patient Listing Protocol]] — **Apr 20 ver.** (renamed from Patient Listing Form) field-ops protocol w/ CSPro random-interval generator
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Facility Head Data Dictionary and Value Sets]] — CSPro dictionary structure and value sets for F1
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro Documentation]] — Official Census Bureau documentation index (links to 7 PDFs, support, videos)
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro 8.0 Complete Users Guide]] — 958-page authoritative reference (Designer, CSEntry, CSBatch, CSTab, dictionary, logic)
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro Android CAPI Getting Started]] — 16-page MyCAPI_Intro tutorial walkthrough
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro Android Data Transfer Guide]] — Operational guide for CSWeb / Dropbox / FTP / Bluetooth sync
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSWeb Users Guide]] — **Authoritative for CSWeb permission model.** 7-page clipping from csprousers.org/help/CSWeb. Two permission axes (5 dashboards + per-dictionary up/down), two built-in roles (Administrator, Standard User), CSV bulk user import, Sync Report + Map Report, Data Settings relational break-out.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Signed CSA Dec 15 2025]] — Carl's signed Consultancy Services Agreement: 6.0 PM × PHP 65K = PHP 390,000 total, deliverable-based payment in 4 tranches, full TOR (10 duties), late penalty 1%/day
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - IDinsight UHC Survey 2024 Final Report]] — Year 1 final report (224 pp, IDinsight). Baseline indicators, methodology, sample design, key findings, recommendations. Year 1 used SurveyCTO; Year 2 switches to CSPro.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - DOH TOR UHC Survey Year 2]] — Procurement TOR (REI No. 2025-001, 6 pp). ABC PhP 60M, 9-month duration, scope/deliverables/timeline, implementation arrangement, required qualifications.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - ASPSI Proposal Approach and Methodology]] — ASPSI's winning technical proposal (TPF 4). Sampling design, CAPI workflow (Figure 4.3), team composition (147.75 PM), field deployment plan (6 clusters), 102 UHC-IS + 17 non-UHC IS.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - ASPSI Team Meeting 2026-04-13]] — Internal team meeting minutes + slides. Process-focused (lessons learned, comms lines, tasking); did NOT discuss the 6 open F1 items. Established the Team Communication Protocol.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex G DOH Recommendations Matrix]] — 23 remarks from PMSMD / ADB (Xylee Javier) / DOH 11th EXECOM Sep 2024, with ASPSI response for each. Change-rationale map for F1/F2/F3/F4 Apr 20 revisions.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex A Data to be Collected and Sources]] — Data-to-sources crosswalk, CHE methodology (Budget Share vs. Capacity-to-pay, Nguyen 2023), and F1 Secondary Data template (Patient Load, HR matrix, YAKAP/Konsulta services + pricing).
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex B List of UHC Integration Sites]] — **107 UHC IS** as of Nov 2025 by integration-year cohort (2020/2022/2023/2024/2025) × region × class (HUC/ICC). Sampling-frame input for F1/F4.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex C List of Non UHC Integration Sites]] — **13 non-UHC IS** as of Nov 2025 (Makati, Pateros, Angeles, Olongapo, Cavite, Camarines Sur, Negros Oriental, Siquijor, Tacloban, Sulu, Cotabato, Lanao del Sur, Tawi-Tawi). Sampling-frame input for F1/F4.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex D Replacement Protocol]] — Field-ops replacement rules: ≥3-visit minimum contact protocol; same-stratum substitution; 5–10% cap on facility replacements; enumerator discretion explicitly banned.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex E Suggested Indicators]] — 104-indicator matrix × 8 HLRQs with DOH RETAIN/AMEND/OMIT verdicts and Year 2 Source crosswalk (PATIENT / HH / FACILITY / HCW / Secondary Data).
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex H Informed Consent Forms]] — 4 ICFs (F1/F2/F3/F4); F3/F4 PhP 100 token + witness clause; F2 PhP 1,000 raffle. SJREB-approvable text that CAPI intro screens must mirror verbatim.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex I Dummy Tables]] — 51 analysis-plan tabulation specs: A1–A14 (F1), B1–B10 (F2), C1–C18 (F3), D1–D9 (F4). Mar 06 2026 header — pre-dates Apr 20 questionnaires.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex J CV of ASPSI Team]] — 7 CVs (Claro, Paunlagui, Silva-Javier, Demaisip, Faderogao, Reyes, Garciano). Field Manager Almendral's CV missing — flag for Annex J rev2.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - gstack Claude Code Skill Pack]] — Garry Tan's 23-skill Claude Code pack (`/qa`, `/review`, `/ship`, `/investigate`, etc.). Adopted **F2 PWA only**, 2026-04-26.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - DOH UHC Year 2 Survey Manual]] — **Apr 28 2026 ver.** ASPSI-authored field manual (~95 pp): background, definitions, SOP (facility selection, courtesy calls, patient listing), data-collection protocol (F1/F2/F3/F4 by instrument), field reminders, quality control, duties of STLs/SEs, data processing. CSPro install section still SPEED 2023 legacy — Carl drafted replacement at `deliverables/Survey-Manual/CSPro-Section-Draft_2026-04-29.md`.

### Entities

**Organizations**
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/ASPSI]] — Asian Social Project Services, Inc. (implementing organization)
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/DOH-PMSMD]] — DOH Performance Monitoring and Strategy Management Division (client)
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/SJREB]] — Single Joint Research Ethics Board (ethics clearance — critical blocker)
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/ADB]] — Asian Development Bank (technical advisor; Xylee Javier)
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/PSA]] — Philippine Statistics Authority (sampling endorsement)
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/IDinsight]] — Year 1 implementer (predecessor to ASPSI; Alec Lim is Year 2 reference contact)
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/US Census Bureau]] — Author/maintainer of CSPro, CSEntry, CSWeb

**People — ASPSI team**
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Dr Paulyn Claro]] — ASPSI Project Lead; signs off deliverables, reviews F2 cover-block rewrite
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Dr Myra Silva-Javier]] — Health policy specialist ("Doc Myra"); convenes LSS meetings
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Merlyne Paunlagui]] — Survey Manager; methodological quality + pretest plan
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Juvy Chavez-Rocamora]] — Project Coordinator; formal DOH-facing submissions gate (Apr 14 matrices; Jan 30 IR)
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Shan Lait|Shan]] — CSPro CAPI app QA Tester; also participating in F2 PWA UAT Round 1

### Concepts

**Project domain**
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/UHC Survey Year 2]] — Survey overview, modules, changes from Year 1
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Timetable of Activities]] — Table 14 from the Inception Report: 9-month schedule, deliverable dates, A/B/C activity breakdown
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F2 Google Forms Track]] — **RETIRED 2026-04-17.** Historical record of the Google Forms track superseded by the PWA build. Reference only.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/PSGC Value Sets]] — PSA 1Q 2026 PSGC (43,803 entries) externalized to `shared/psgc_*.dcf` lookups + `PSGC-Cascade.apc`; DCFs shrink 17 MB → ~1 MB
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/GPS and Photo Capture]] — F1/F3/F4 auto-GPS metadata blocks + end-of-interview verification photo; shared `Capture-Helpers.apc`; F3→F1 linkage via `F3_FACILITY_ID`
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro]] — Census and Survey Processing System (overview)
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSWeb]] — Web server for real-time monitoring and data sync

**Working conventions**
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Forward-Only Sign-Off]] — Drive through to testable artifact; test bugs loop back to source docs
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/LSS Meeting]] — Lessons Learned Session; event-driven internal ASPSI retro + tasking
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Team Communication Protocol]] — Formal DOH-facing comms routing (Apr 13); Carl is not an authorized DOH sender
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/gstack F2 PWA Workflow]] — Adopted gstack skill subset for F2 PWA build/QA/review/ship loop; `/ship` constrained to branch+PR (release-notes workflow owns versioning)
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Questionnaire Numbering Convention]] — **(adopted 2026-05-05)** 12-digit decomposed case ID (Region 2 + Province 2 + Municipality 3 + Facility 2 + Case 3), anchored on PSA 1Q 2026 PSGC, covering F1/F2/F3/F4. Brief drafted for Kidd at `deliverables/Survey-Manual/Case-ID-Convention-Brief_2026-05-05.{md,docx}`; implementation footprint (cspro_helpers + F1/F3/F4 generators + F2 PWA case-ID issuer + manual addendum) pending sprint scheduling.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F2 Admin Portal]] — Operations console (admin-only routes in F2 PWA): Users/Roles CRUD with versioning, force-revoke sessions, HCW token reissue with CAS, Apps dashboard shell. **Sprints AP1–AP4 complete; PR #54 merged 2026-05-04; v2.0.0 live in prod; UAT Round 2 open with Shan + Kidd.** Sprint 005 polish backlog (E4-APRT-040 prod M10 sunset, E4-APRT-044 RBAC cache eviction, E4-APRT-045 password_must_change server-side enforcement, design-review HIGH/MEDIUM findings) tracked in current sprint file.

**CSPro toolchain (from the 8.0 Users Guide)**
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Data Dictionary]] — `.dcf` schema: levels, records, items, value sets, relations
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F-Series Value Set Conventions]] — project-internal coding rules: NA = highest code at field width, never use `notappl` in value sets
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Language Fundamentals]] — PROC GLOBAL, declarations, logic objects, variables, expressions, operators
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Logic Events]] — preproc/postproc/onfocus/killfocus/onoccchange order of execution
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Data Entry Modes]] — system- vs operator-controlled, heads-up vs heads-down
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Capture Types]] — Text Box, Radio, Drop Down, Number Pad, Date, etc.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro CAPI Strategies]] — forms, fields, questions, blocks, partial save, prefilling
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Question Text and Fills]] — fills (`~~item~~`), HTML, conditional questions
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Multi-Language Applications]] — multi-language labels, `tr`, `setlanguage`
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Synchronization]] — sync architecture, `sync*` functions, troubleshooting
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Batch Editing]] — CSBatch, structure/validity/consistency checks, hot decks, imputation
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Tabulation]] — CSTab, cross-tabs, area processing, weights, summary stats

### Analyses
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/analyses/Analysis - Project Intelligence Brief]] — Full project timeline, decisions, scope changes, blockers, stakeholder dynamics, Carl's positioning
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/analyses/Analysis - Apr 20 DCF Generator Audit]] — Per-generator patch targets for F1/F3/F4 DCF generators + F2 Google-Forms spec, mapped to Annex G remarks

## Deliverables

**Active CSPro build — UHC-Survey-System scaffold**
- `deliverables/CSPro/UHC-Survey-System/` — Active F-series build scaffold (Phase 1 in progress; F1 promotion next). Houses `107_F1/`, `shared/`, and `Form-Layout-Principles.md`. See `docs/superpowers/plans/2026-05-08-uhc-survey-system-build-phase-1.md` for the runbook.
- `deliverables/CSPro/UHC-Survey-System/shared/cspro_helpers.py` — Active shared helpers module for the new build (value sets, item builders, parameterized FIELD_CONTROL/GEO_ID/dictionary assembly).
- `deliverables/CSPro/UHC-Survey-System/shared/build_psgc_lookups.py` — Generator for the four PSGC external lookup dictionaries (relocated 2026-05-12 from `deliverables/CSPro/shared/`). Reads PSGC CSVs (PSA 1Q 2026; archived under `deliverables/.archive/pre-rebuild-2026-05-11/CSPro/F1/inputs/`) and emits `.dcf` + fixed-width `.dat` pairs (region/province/city/barangay).
- `deliverables/CSPro/UHC-Survey-System/shared/psgc_region.dcf` + `psgc_region.dat` — 18 regions (parent=sentinel `0000000000`), max 20 occurrences.
- `deliverables/CSPro/UHC-Survey-System/shared/psgc_province.dcf` + `psgc_province.dat` — 117 provinces/HUCs keyed by region code, max 30 occurrences.
- `deliverables/CSPro/UHC-Survey-System/shared/psgc_city.dcf` + `psgc_city.dat` — 1,658 cities/municipalities keyed by province/HUC code, max 60 occurrences.
- `deliverables/CSPro/UHC-Survey-System/shared/psgc_barangay.dcf` + `psgc_barangay.dat` — 42,010 barangays keyed by city/municipality code, max 2,000 occurrences.
- `deliverables/CSPro/UHC-Survey-System/shared/PSGC-Cascade.apc` — Reusable CSPro logic module. Four public functions (`FillRegionValueSet`, `FillProvinceValueSet`, `FillCityValueSet`, `FillBarangayValueSet`) invoked from each form's `onfocus` events to drive the cascading region→province→city→barangay dropdowns via `loadcase()` + `setvalueset()`.
- `deliverables/CSPro/UHC-Survey-System/shared/Capture-Helpers.apc` — Reusable GPS + verification-photo helpers (`ReadGPSReading`, `TakeVerificationPhoto`). Relocated 2026-05-12 from `deliverables/CSPro/shared/`.
- `deliverables/CSPro/UHC-Survey-System/Form-Layout-Principles.md` — Form-layout principles for tablet ergonomics (relocated 2026-05-12 from `deliverables/CSPro/`).

**Pre-rebuild CSPro snapshot — archived 2026-05-11**

The Apr 20-22 F1/F3/F4 build (DCFs, FMFs, generators, spec docs) and the two root-level helper scripts that lived at `deliverables/CSPro/{cspro_helpers.py, export_dcf_to_xlsx.py, F1/, F3/, F4/, shared/}` were archived under `deliverables/.archive/pre-rebuild-2026-05-11/CSPro/` during the Sprint 005 R3 archive sequence. They remain greppable as reference material for the new build; treat them as frozen.

- `deliverables/.archive/pre-rebuild-2026-05-11/CSPro/cspro_helpers.py` — Pre-rebuild shared helpers module.
- `deliverables/.archive/pre-rebuild-2026-05-11/CSPro/export_dcf_to_xlsx.py` — Parser/exporter from any F-series `.dcf` (CSPro 8.0 JSON) to a two-sheet workbook.
- `deliverables/.archive/pre-rebuild-2026-05-11/CSPro/F1/` — Pre-rebuild F1 Facility Head Survey build (12 records / 671 items DCF; `FacilityHeadSurvey.{dcf,ent,ent.apc,ent.mgf,ent.qsf,fmf,pff,cslog}`; `generate_dcf.py`; `F1-Skip-Logic-and-Validations.md`; `F1-Form-Layout-Plan.md`; `F1-FMF-Designer-Walkthrough.md`; `inputs/F1_clean.txt`; `inputs/psgc_*.csv` (PSA 1Q 2026 source CSVs + parser); `sample042126.csdb`; Excel review export).
- `deliverables/.archive/pre-rebuild-2026-05-11/CSPro/F3/` — Pre-rebuild F3 Patient Survey build (18 records / 840 items DCF; `PatientSurvey.dcf`; `PatientSurvey.generated.fmf`; `generate_dcf.py` + `generate_fmf.py`; `F3-Skip-Logic-and-Validations.md` (1,133 lines, reviewed 2026-04-21, Q31 IP_GROUP to Juvy); `F3-Form-Layout-Plan.md`; `inputs/F3_clean.txt`; Excel review export).
- `deliverables/.archive/pre-rebuild-2026-05-11/CSPro/F4/` — Pre-rebuild F4 Household Survey build (22 records / 623 items DCF; `HouseholdSurvey.dcf`; `HouseholdSurvey.generated.fmf`; `generate_dcf.py` + `generate_fmf.py`; `F4-Skip-Logic-and-Validations.md` (904 lines, draft 2026-04-21, 3 questions to ASPSI); `F4-Form-Layout-Plan.md`; `inputs/F4_clean.txt`; Excel review export).

**F2 Healthcare Worker Survey — PWA (primary build, Epic 3 complete)**
- `deliverables/F2/PWA/app/` — Canonical PWA build (Vite + React + TypeScript + Tailwind + shadcn/ui). M0–M11 shipped 2026-04-17/18; auto-advance + section-lock UX shipped post-M11. **Epic 3 build complete 2026-04-23.** **Phase F cutover landed 2026-05-01** — production runs Worker JWT proxy + Verde manual + v1.3.0 fixes at `f2-pwa.pages.dev`. [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F2 Admin Portal|Admin Portal]] work (Sprint AP1) in flight on `f2-admin-portal` branch.
- `deliverables/F2/PWA/app/spec/F2-Spec.md` — 124-item spec (Apr 20 ver., Q1–Q125 with Q108 gap), canonical source of truth for the PWA build.
- `deliverables/F2/PWA/app/e2e/golden-path.spec.ts` — Playwright E2E tests: golden path (enrollment → 10 sections → review → submit), section lock, language switch. Run: `npx playwright test --config e2e/playwright.config.ts`.
- `deliverables/F2/PWA/app/NEXT.md` — Authoritative post-M11 decision log and deferred backlog (per-HCW tokens, draft auto-migration, iOS push, admin mutations).
- `deliverables/F2/F2-Spec.md` — Apr 20 spec (canonical labels, 124 items Q1–Q125).
- `deliverables/F2/F2-Skip-Logic.md` — Section graph + routing for the PWA nav engine.
- `deliverables/F2/F2-Validation.md` — Required fields, numeric ranges, hard/soft rules.
- `deliverables/F2/F2-Cross-Field.md` — 20 POST-submit consistency rules (Apps Script `onFormSubmit`).

**UAT and QA**
- `docs/F2-PWA-UAT-Guide.md` — UAT Round 1 guide for ASPSI staff. 10 scenarios (TC-001–TC-010), 2 personas (UAT-NURSE-01 / UAT-PHYS-01), staging URL, sign-off instructions. Public: `github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/blob/staging/docs/F2-PWA-UAT-Guide.md`.
- `.github/ISSUE_TEMPLATE/bug_report.yml` — Structured GitHub Issue template for bug reports (labels: `bug`).
- `.github/ISSUE_TEMPLATE/uat_feedback.yml` — Structured GitHub Issue template for UAT feedback (labels: `uat-feedback`).

## Vault Path

```
analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/
```

**GitHub:** https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development (public as of 2026-04-23; renamed from `ASPSI-DOH-CAPI-CSPro-Development`). Local folder name unchanged.
