---
title: ASPSI-DOH CAPI CSPro Development
project: ASPSI-DOH-CAPI-CSPro-Development
client: ASPSI / DOH (Department of Health)
client_contact: ASPSI — Kidd · Myra (DOH interface)
offering: CAPI-Development
hat: CAPI / Survey Systems Lead
due: 2026-08-14
milestone: UAT Round 5 sign-off, then August training
acceptance: UAT R5 in progress (Jun 22-27), 6 surfaces — F1/F3/F4 + F2 PWA + Admin + CSWeb
status: UAT Round 5; contract close Aug 14 — extension (Aug training / Sep rollout) requested
state: active
last_contact: 2026-06-26
primary_sensor: "Slack (capi-scrum) + GitHub issues; email NOW available — UP account clreyes6@up.edu.ph connected 2026-06-28 (ASPSI/DOH threads visible; Gmail connector still can't download attachments)"
last_updated: 2026-06-28
---

# ASPSI-DOH CAPI CSPro Development

Computer-Assisted Personal Interviewing (CAPI) system development for ASPSI | DOH using CSPro and CSEntry, covering survey questionnaire design through CSWeb deployment.

## Delivery

> Executive record per the [[2_Areas/IT-Standards/templates/Delivery-Standard|Delivery Standard]]. The full engine room is in `scrum/`; this rolls it up.

### Commitments
- [x] F1/F3/F4 + F2 instruments built & deployed to CSWeb   state::done
- [ ] UAT Round 5 sign-off across 6 surfaces                 state::doing
- [ ] Enumerator training (August)                           state::todo
- [ ] National rollout (September)                           state::todo

### Impediments
- PhilHealth Q38/Q45 reinstatement   status::blocked  owner::Carl  next::save the 3 value-set PNGs from Kidd's 2026-06-09 email (wordings+routing now captured 2026-06-28; only option lists remain)  raised::2026-06-21
- F2 off-Cloudflare → Elestio migration   status::blocked  owner::Carl/ASPSI  next::provision instance + DNS + cost sign-off  raised::2026-06-22

### Accepted
- 2026-05-04 — F2 PWA v2.0.0 (HCW Survey + Admin Portal) to production

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
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - DOH UHC Year 2 Survey Manual]] — **Apr 28 2026 ver. SUPERSEDED 2026-05-12 by v1.0.** ASPSI-authored field manual (~95 pp): background, definitions, SOP (facility selection, courtesy calls, patient listing), data-collection protocol (F1/F2/F3/F4 by instrument), field reminders, quality control, duties of STLs/SEs, data processing. CSPro install section still SPEED 2023 legacy — Carl drafted replacement at `deliverables/Survey-Manual/CSPro-Section-Draft_2026-04-29.md`.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Survey Manual 2026-05-06 - Section 3a]] — **Targeted §3a ingest of the May 6 Working File** (partial, pre-Myra). §3a auto-tag rule gap (build-critical for F3b listing) + TRANSPORT_MODE 12-option enumeration resolved via F3 Q70/Q73. Superseded by v1.0 2026-05-12.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Survey Manual v1.0 (2026-05-12 Working File post-Myra)]] — **v1.0 Working File, post-Myra edits.** 38pp PDF. Closes Dr. Myra Silva-Javier's review pass open since 2026-04-30. Sent by Kidd to Myra 2026-05-12 14:45 PST. 2 of 5 prior divergences resolved (HCW self-admin, sync architecture); 2 still open (bench-testing, case-ID §5.1 with internal inconsistencies); 1 newly shifted (patient listing now mandates systematic vs F3 app's random-interval); 1 newly surfaced (SE count Table 1 vs xlsx).
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Survey Manual v1.0 (2026-05-12 Clean Final to DOH)]] — **v1.0 Clean Final.** ~99.9% identical to Working File; ~177-line diff mostly page-numbering. Sent by Kidd to DOH PMSMD 2026-05-12 15:50 PST. **PSA submission target 2026-05-19.** Appendix index G/H/I shifted (NDU Appendix G removed), one Annex F4 reference dropped.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Sample Distribution 2026-05-12]] — **Sample frame xlsx, 9 sheets.** 1,521 facilities (911 RHU + 244 Pub Hosp + 366 Priv Hosp), 8,940 patients (3,540 IP + 5,400 OP), 2,670 HHs (6 regions only). Per-cluster, per-region, per-municipality breakdowns + 1,529-row sampled-facility master list (canonical F1 sample frame). 6 clusters + named Field Supervisor candidates.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - ASPSI Team Meeting 2026-05-11]] — Internal meeting notes by Shan. Tool translations (6/7 dialects done, Bisaya pending 2026-05-13); CAPI dialect integration owned by Carl, 10-day estimate, gates pre-test; PSA Form under Sir Francis review; SJREB deadline 2026-05-27; pre-test in Bay/Los Baños 4th week of June; Del-1 payment pending.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - ASPSI Weekly Update Draft 2026-05-11]] — Short DOH-facing weekly draft (Del-2 status); Carl is not a sender per `feedback_comms_lane_discipline`. Informational only.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - ASPSI Team Meeting 2026-05-18]] — Carl's own stand-up notes. **This week: park HCW features, fix UAT R3 findings, back to F1/F3/F4 CSPro, stand up CSWeb on a VPS** (field visibility + tablet sync + data-manager monitoring), start dialect translation (full build next week). Myra: Tagalog help ~weekend. SJREB full-board 2nd week June (out of DP scope). Contradiction flagged: R3 "findings last week" vs #271 still OPEN/untouched since 2026-05-12.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CAPI Translations PSA Deadline (Myra 2026-05-13)]] — **Email, Myra → Carl, call-firmed.** PSA will not clear the survey without the **CAPI app + 7 translated versions**; hard internal deadline **2026-06-12**. Separate/later PSA stream from the manual+sampling submission; this one is Carl's. Carl confirmed alignment (quality not compromised).
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Survey Tool Translation Delivery Status 2026-05-15]] — **Email thread, Aidan ↔ Myra, Carl cc'd.** Translation pipeline behind the 06-12 gate: Drive folder source-of-truth; per-language status; **7 distinct languages** (Bisaya ≠ Cebuano); QC/back-translation is the binding step; **Bisaya Household incomplete, Ilocano has no QC reviewer** (build-input risk, ASPSI-owned). Supersedes the 05-11 "6/7 done" snapshot.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - HCW CAPI Comments Matrix (Myra answers 2026-05-21)]] — **Google Doc, Aidan → Myra, Carl+Merlyne+Marriz cc'd.** Marriz's 9 R3 questionnaire-design findings (GH `#303`/`#304`/`#305`/`#306`/`#307`/`#309`/`#310`/`#311`/`#312`) sent to Myra as a decision matrix; Myra answered same day. 3 approved-as-suggested, 2 approved with modification, 1 more restrictive than suggested, 2 different shape, 1 overrode Carl's suggestion (Q36 → multi-select), 1 not answered (Q36 past-tense wording). Top-of-doc decisions tighten the Q9-vs-Q4 rule to in-survey block at `tenure < age − 20`.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - PhilHealth Reinstatement Email (Kidd 2026-06-09)]] — **Email, Kidd → Carl, 2026-06-09.** DOH-agreed reinstatement of 2 conditional PhilHealth-registration sub-questions omitted after OAAED comments (emphasized by Sir LJ): **F3 Q38.1/Q38.2** + **F4 Q45.1/Q45.2** (*"When did you register and receive your PhilHealth PIN?"* / *"Why are you not registered with PhilHealth?"*). Verbatim stems + routing captured; the 3 attached PNGs holding the **value sets** can't be downloaded via the connector → Carl saves them, then build (~3h, dcf+apc+qsf ×2 + codebook). E2-F3/F4-PHILHEALTH.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - DOH June Questionnaire Comments (PARKED) 2026-06-19]] — **Build-posture decision.** DOH (Xylee "XJ" Javier / OAAED / HCFinancing / WHO / ADB) sent a large wave of comments on the **April 8** F1/F2/F3 tools (forwarded Jun 10). Myra's ruling: **PARK all of them** — the **April 20 version is the accepted baseline**; the comments are deferred to **SJREB/PSA review + pre-testing** and answered with finality only if they resurface. **No instruction to Carl; keep building to April 20.** Big parked items: F1 two-step "since-2019/UHC-Act" restructure (~18 Qs); F3 new expenditure block + FIES assets; F4 contested DOH April-15 PIDS/DHS HH restructure (team instructed NOT to follow; no F4 matrix yet). CAPI-native asks (numeric codes, exclusive-blocking, GPS, auto-age, listing form) mostly already built.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Survey Tool Translations Delivery (Aidan 2026-06-02)]] — **Translation delivery (Drive link).** Batch 1 (Bicolano/Bisaya/Cebuano/Waray) **DONE**; Batch 2 (Tagalog/Ilocano/Hiligaynon) **PENDING** (QC). Versions: 3.1 tracked / **3.2 clean (use for build)**. Confirms the standing Batch-2 gap.
- _Inputs received (attachments not connector-downloadable — Carl to save):_ **CAPI manual materials** (Myra → Carl, 2026-06-17 "for the CAPI MANUAL": `CAPI_topic outline.docx`, `CAPI_style guide.docx`, `CAPI_Manual (for CAPI).pdf`, `Filling out Forms with ODK Collect.pdf`) — Epic 7 (D5) manual structure/style inputs; **Pretesting Plan** (Myra → Kidd, 2026-06-08 "Survey Manual and Pretesting Plan" + ChatGPT brainstorm doc) — Epic 6 pretest input. Team-meeting notes (Jun 1 / Jun 9 / Jun 22) are docx attachments, not ingested.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - ASPSI Team Meeting 2026-06-22]] — Carl's stand-up + team discussion. **Last week:** F3/F4 stop/withdraw handling (Marriz's flag), Supervisor review tool v1, live CSWeb monitoring dashboard, UAT R5 opened (Jun 22–27). **This week:** continued tester-driven dev, align to the Survey Manual beyond the instruments-only MVP, Supervisor tool go-live, plan F2 Survey+Admin migration off Cloudflare (free-tier limits). 309 instrument issues resolved to date. **Headline outcome:** monitoring dashboard positioned as the **basis for an extension request — Aug Training, Sep Rollout** (pushes past the Aug 14 official close; proposed, not approved).

### Analyses

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/analyses/Analysis - 2026-05-12 Survey Manual v1.0 Divergence Re-eval]] — Scorecard of the 5 open divergences from May 7 ingest against the post-Myra Working File: 2 resolved (HCW self-admin, sync), 2 still open (bench-testing, case-ID §5.1), 1 shifted direction (patient listing now systematic vs F3 app's random-interval), 1 newly surfaced (SE count 100 vs 124). Residual shortlist for Kidd + PSA submission window 2026-05-19.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/analyses/Analysis - 2026-05-21 HCW R3 Myra Decisions to Build Actions]] — Per-GH-issue action plan derived from Myra's 2026-05-21 decisions. 8 of 9 R3 questionnaire items buildable in F2 v1.3.x this sprint; 1 closeable as no-op (`#303`); 4 sub-items need a single follow-up to the team (year floor on `#305-3a`, wording on `#307-5b` and `#309-ii`, translation slot for new `#312-i` option text). PSA 2026-06-12 translation cascade flagged on Q35 DK labels, Q38 reword, and Q125 new option.

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
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Marriz]] — ASPSI Data Manager; recurring CAPI UAT tester (R3–R5); raises questionnaire-design / data-quality findings (flagged the F3/F4 stop/withdraw fix)

### Concepts

**Project domain**
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/UHC Survey Year 2]] — Survey overview, modules, changes from Year 1
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Timetable of Activities]] — Table 14 from the Inception Report: 9-month schedule, deliverable dates, A/B/C activity breakdown. **+ proposed 2026-06-22 extension** (Aug Training / Sep Rollout) past the Aug 14 close, dashboard-evidenced
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F2 Google Forms Track]] — **RETIRED 2026-04-17.** Historical record of the Google Forms track superseded by the PWA build. Reference only.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/PSGC Value Sets]] — PSA 1Q 2026 PSGC (43,803 entries) externalized to `shared/psgc_*.dcf` lookups + `PSGC-Cascade.apc`; DCFs shrink 17 MB → ~1 MB
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/GPS and Photo Capture]] — F1/F3/F4 auto-GPS metadata blocks + end-of-interview verification photo; shared `Capture-Helpers.apc`; F3→F1 linkage via `F3_FACILITY_ID`
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro]] — Census and Survey Processing System (overview)
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSWeb]] — Web server for real-time monitoring and data sync
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CAPI Seven-Language Translation Build]] — **(2026-05-13)** CAPI app must ship in 7 distinct languages (Bisaya ≠ Cebuano), finalized + bundled for **PSA clearance by 2026-06-12**; Drive folder source-of-truth; S007 critical path; QC-finalization (not first-draft) is the binding predecessor

**Working conventions**
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Forward-Only Sign-Off]] — Drive through to testable artifact; test bugs loop back to source docs
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Quality Over Deadline]] — Standing stance: quality holds over deadlines. The seven-language PSA date (2026-06-12) was held to quality rather than rushed; root-cause fixes preferred over papering over
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
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/analyses/Analysis - 2026-05-12 Survey Manual v1.0 Divergence Re-eval]] — (also linked in Sources/Analyses subsection above) divergence scorecard against the post-Myra Working File
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/analyses/Analysis - 2026-05-21 HCW R3 Myra Decisions to Build Actions]] — Per-GH-issue build action plan for the 9 R3 questionnaire-design items decided by Myra 2026-05-21; sequenced for F2 v1.3.x; flags 3 sub-items needing one short follow-up to the team

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
- `deliverables/CSPro/F1/FacilityHeadSurvey.dcf` — F1 CSPro 8.0 data dictionary (**12 records / 671 items**, ~0.9 MB; post Apr 21 GPS+photo+PSGC-cascade + Apr 22 case-control extension). PSGC items carry placeholder value sets; populated at runtime via `PSGC-Cascade.apc`. Secondary-data records intentionally empty pending design decision.
- `deliverables/CSPro/F1/FacilityHeadSurvey - Data Dictionary and Value Sets.xlsx` — Excel review export (Designer format). Regenerated by `export_dcf_to_xlsx.py`.
- `deliverables/CSPro/F1/generate_dcf.py` — Reproducible Python generator for the F1 dictionary. Imports shared helpers from `cspro_helpers.py` and uses `build_geo_id("facility")` for the geographic record. The 6 design-blocked items are encoded as `PENDING_DESIGN_*` constants — flip + rerun to swap schema when decisions land.
- `deliverables/CSPro/F1/F1-Skip-Logic-and-Validations.md` — Spec covering dcf sanity-check findings (6 bugs), full skip-logic table for all 166 questions, hard/soft/gate validations, and paste-ready CSPro PROC code templates.
- `deliverables/CSPro/F1/inputs/F1_clean.txt` — Internal text extraction of the F1 questionnaire used as a generator input reference.
- `deliverables/CSPro/F1/inputs/psgc_*.csv` — Single source of truth for PSGC (PSA 1Q 2026). Consumed by `shared/build_psgc_lookups.py`; no longer read by the F-series generators directly.

**F3 Patient Survey**
- `deliverables/CSPro/F3/PatientSurvey.dcf` — F3 CSPro 8.0 data dictionary (**18 records / 806 items**; post Apr 21 GPS+photo+PSGC-cascade + Apr 22 case-control extension + Apr 22 duplicate-item fix). Facility PSGC + patient-home `P_` PSGC blocks. Sections A–L.
- `deliverables/CSPro/F3/PatientSurvey - Data Dictionary and Value Sets.xlsx` — Excel review export. Regenerated by `export_dcf_to_xlsx.py`.
- `deliverables/CSPro/F3/generate_dcf.py` — Reproducible Python generator. Uses `build_geo_id("facility_and_patient")`.
- `deliverables/CSPro/F3/generate_fmf.py` — FMF skeleton generator. Emits `PatientSurvey.generated.fmf` (19 forms, 0 orphan items); form labels carry intended Designer splits inline.
- `deliverables/CSPro/F3/PatientSurvey.generated.fmf` — Generated FMF skeleton (19 forms). Designer opens this for form splits, skip wiring, and PROC logic from `F3-Skip-Logic-and-Validations.md`.
- `deliverables/CSPro/F3/F3-Skip-Logic-and-Validations.md` — Full skip-logic + validation spec (reviewed 2026-04-21; 1,133 lines; sections A–L; 14 sanity findings; 15 CSPro PROC templates; Q31 IP_GROUP routed to Juvy).
- `deliverables/CSPro/F3/inputs/F3_clean.txt` — Internal text extraction of the F3 questionnaire.

**F4 Household Survey**
- `deliverables/CSPro/F4/HouseholdSurvey.dcf` — F4 CSPro 8.0 data dictionary (**22 records / 623 items**; post Apr 21 GPS+photo+PSGC-cascade + Apr 22 case-control extension; schema verified correct). `C_HOUSEHOLD_ROSTER` repeating (`max_occurs=20`); `H_PHILHEALTH_REG` + `J_HEALTH_SEEKING` respondent-level. Sections A–Q.
- `deliverables/CSPro/F4/HouseholdSurvey - Data Dictionary and Value Sets.xlsx` — Excel review export. Regenerated by `export_dcf_to_xlsx.py`.
- `deliverables/CSPro/F4/generate_dcf.py` — Reproducible Python generator. Section N (Expenditures) uses flat item batteries across multiple reference periods.
- `deliverables/CSPro/F4/generate_fmf.py` — FMF skeleton generator. Emits `HouseholdSurvey.generated.fmf` (24 forms, 0 orphan items); roster on its own form per layout principles.
- `deliverables/CSPro/F4/HouseholdSurvey.generated.fmf` — Generated FMF skeleton (24 forms). Designer opens this for form splits, roster wiring, and PROC logic from `F4-Skip-Logic-and-Validations.md`.
- `deliverables/CSPro/F4/F4-Skip-Logic-and-Validations.md` — Full skip-logic + validation spec (draft 2026-04-21; 904 lines; sections A–Q; 13 sanity findings with findings #1/#2 CLOSED-BY-VERIFICATION; 11 CSPro PROC templates; 3 questions to ASPSI).
- `deliverables/CSPro/F4/inputs/F4_clean.txt` — Internal text extraction of the F4 questionnaire.

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
