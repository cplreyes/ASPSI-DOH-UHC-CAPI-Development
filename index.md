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
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F2 Healthcare Worker Survey Questionnaire]] — **Apr 20 ver.** 125 items, self-admin (Sections A–J); cover-block rewrite still outstanding
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3 Patient Survey Questionnaire]] — **Apr 20 ver.** 178 items, CAPI inpatient+outpatient (Sections A–L); +52 items vs Apr 08
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F4 Household Survey Questionnaire]] — **Apr 20 ver.** 202 items, community survey (Sections A–Q); interval sampling from patient HH
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3b Patient Listing Protocol]] — **Apr 20 ver.** (renamed from Patient Listing Form) field-ops protocol w/ CSPro random-interval generator
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Facility Head Data Dictionary and Value Sets]] — CSPro dictionary structure and value sets for F1
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro Documentation]] — Official Census Bureau documentation index (links to 7 PDFs, support, videos)
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro 8.0 Complete Users Guide]] — 958-page authoritative reference (Designer, CSEntry, CSBatch, CSTab, dictionary, logic)
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro Android CAPI Getting Started]] — 16-page MyCAPI_Intro tutorial walkthrough
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro Android Data Transfer Guide]] — Operational guide for CSWeb / Dropbox / FTP / Bluetooth sync
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
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Shan Lait|Shan]] — CSPro CAPI app QA Tester (also F2 Google Forms)

### Concepts

**Project domain**
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/UHC Survey Year 2]] — Survey overview, modules, changes from Year 1
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Timetable of Activities]] — Table 14 from the Inception Report: 9-month schedule, deliverable dates, A/B/C activity breakdown
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F2 Google Forms Track]] — F2 special case: Google Forms primary, paper→Forms fallback, deferred CSPro
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/PSGC Value Sets]] — PSA 1Q 2026 PSGC (43,803 entries) externalized to `shared/psgc_*.dcf` lookups + `PSGC-Cascade.apc`; DCFs shrink 17 MB → ~1 MB
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro]] — Census and Survey Processing System (overview)
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSWeb]] — Web server for real-time monitoring and data sync

**Working conventions**
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Forward-Only Sign-Off]] — Drive through to testable artifact; test bugs loop back to source docs
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/LSS Meeting]] — Lessons Learned Session; event-driven internal ASPSI retro + tasking
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Team Communication Protocol]] — Formal DOH-facing comms routing (Apr 13); Carl is not an authorized DOH sender

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

**Shared**
- `deliverables/CSPro/cspro_helpers.py` — Shared helpers module (value sets, item builders, parameterized FIELD_CONTROL/GEO_ID/dictionary assembly). All F-series generators import from here.
- `deliverables/CSPro/export_dcf_to_xlsx.py` — Parses any F-series `.dcf` (CSPro 8.0 JSON) and emits a two-sheet workbook (`Dictionary Names and Labels` + `Value Sets`) matching the CSPro Designer export format used in `raw/Sample-Data/`. Run `--all` to regenerate F1/F3/F4 workbooks in one shot. For second-opinion review without requiring CSPro install.
- `deliverables/CSPro/shared/build_psgc_lookups.py` — Generator for the four PSGC external lookup dictionaries. Reads `F1/inputs/psgc_*.csv` (PSA 1Q 2026) and emits `.dcf` + fixed-width `.dat` pairs (region/province/city/barangay).
- `deliverables/CSPro/shared/psgc_region.dcf` + `psgc_region.dat` — 18 regions (parent=sentinel `0000000000`), max 20 occurrences.
- `deliverables/CSPro/shared/psgc_province.dcf` + `psgc_province.dat` — 117 provinces/HUCs keyed by region code, max 30 occurrences.
- `deliverables/CSPro/shared/psgc_city.dcf` + `psgc_city.dat` — 1,658 cities/municipalities keyed by province/HUC code, max 60 occurrences.
- `deliverables/CSPro/shared/psgc_barangay.dcf` + `psgc_barangay.dat` — 42,010 barangays keyed by city/municipality code, max 2,000 occurrences.
- `deliverables/CSPro/shared/PSGC-Cascade.apc` — Reusable CSPro logic module. Four public functions (`FillRegionValueSet`, `FillProvinceValueSet`, `FillCityValueSet`, `FillBarangayValueSet`) invoked from each form's `onfocus` events to drive the cascading region→province→city→barangay dropdowns via `loadcase()` + `setvalueset()`.

**F1 Facility Head Survey**
- `deliverables/CSPro/F1/FacilityHeadSurvey.dcf` — F1 CSPro 8.0 data dictionary (11 records, 655 items, ~0.9 MB) generated from the Apr 20 questionnaire. PSGC items carry placeholder value sets; real options populated at runtime from `shared/psgc_*.dcf` via `PSGC-Cascade.apc`. Secondary-data records (SEC_HOSP_CENSUS, SEC_HCW_ROSTER, SEC_YK_SERVICES, SEC_LAB_PRICES) intentionally empty pending design decision.
- `deliverables/CSPro/F1/FacilityHeadSurvey - Data Dictionary and Value Sets.xlsx` — Excel review export (Designer format). Regenerated by `export_dcf_to_xlsx.py`.
- `deliverables/CSPro/F1/generate_dcf.py` — Reproducible Python generator for the F1 dictionary. Imports shared helpers from `cspro_helpers.py` and uses `build_geo_id("facility")` for the geographic record. The 6 design-blocked items are encoded as `PENDING_DESIGN_*` constants — flip + rerun to swap schema when decisions land.
- `deliverables/CSPro/F1/F1-Skip-Logic-and-Validations.md` — Spec covering dcf sanity-check findings (6 bugs), full skip-logic table for all 166 questions, hard/soft/gate validations, and paste-ready CSPro PROC code templates.
- `deliverables/CSPro/F1/inputs/F1_clean.txt` — Internal text extraction of the F1 questionnaire used as a generator input reference.
- `deliverables/CSPro/F1/inputs/psgc_*.csv` — Single source of truth for PSGC (PSA 1Q 2026). Consumed by `shared/build_psgc_lookups.py`; no longer read by the F-series generators directly.

**F3 Patient Survey**
- `deliverables/CSPro/F3/PatientSurvey.dcf` — F3 CSPro 8.0 data dictionary (15 records, 818 items, ~1.0 MB) generated from the Apr 20 questionnaire. Has both facility PSGC and patient-home `P_` PSGC blocks, both placeholder-VS + cascade-populated. All single-occurrence records. Sections A–L.
- `deliverables/CSPro/F3/PatientSurvey - Data Dictionary and Value Sets.xlsx` — Excel review export (Designer format). Regenerated by `export_dcf_to_xlsx.py`.
- `deliverables/CSPro/F3/generate_dcf.py` — Reproducible Python generator for the F3 dictionary. Imports shared helpers from `cspro_helpers.py` and uses `build_geo_id("facility_and_patient")`.
- `deliverables/CSPro/F3/inputs/F3_clean.txt` — Internal text extraction of the F3 questionnaire used as a generator input reference.

**F4 Household Survey**
- `deliverables/CSPro/F4/HouseholdSurvey.dcf` — F4 CSPro 8.0 data dictionary (21 records, 611 items, ~0.8 MB) generated from the Apr 20 questionnaire. PSGC via `build_geo_id("household", extra_items=[LATITUDE, LONGITUDE])`. Repeating records include C_HOUSEHOLD_ROSTER, H_PHILHEALTH_REG, J_HEALTH_SEEKING. Sections A–Q.
- `deliverables/CSPro/F4/HouseholdSurvey - Data Dictionary and Value Sets.xlsx` — Excel review export (Designer format). Regenerated by `export_dcf_to_xlsx.py`.
- `deliverables/CSPro/F4/generate_dcf.py` — Reproducible Python generator for the F4 dictionary. Imports shared helpers from `cspro_helpers.py`. Section N (Expenditures) uses flat item batteries across multiple reference periods.
- `deliverables/CSPro/F4/inputs/F4_clean.txt` — Internal text extraction of the F4 questionnaire used as a generator input reference.

## Vault Path

```
analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/
```
