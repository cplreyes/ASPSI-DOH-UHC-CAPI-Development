---
project: UHC Survey Year 2 — CAPI Development
client: Department of Health (DOH-PMSMD)
implementer: Asian Social Project Services, Inc. (ASPSI)
data_programmer: Carl Patrick L. Reyes
qa_tester: Shan (ASPSI, RA)
contract: CSA signed 2025-12-15, effective 2025-11-14
engagement_window: November 2025 – August 2026
last_updated: 2026-04-25
---

# Product Backlog — UHC Survey Year 2 CAPI Development

> Stakeholder-facing view of the full CAPI (Computer-Assisted Personal Interviewing) development workstream for the DOH Universal Health Care Survey Year 2.
>
> Organized around **13 workstream epics (0–12)** covering the full engagement lifecycle from inception through handover. Epics are derived from the reusable [[2_Areas/IT-Standards/templates/CAPI-Development-Workflow|CAPI Development Workflow]] template — this project is the first reference engagement for that template.
>
> Updated at each sprint close. For day-to-day progress, see `sprint-current.md` (internal sprint view).

---

## 1. Status at a Glance

### Headline (this week)

**Inter-sprint, Sat 2026-04-25 — F2 PWA Rounds 1 + 2 closed; Sprint 003 starts Mon 2026-04-28.** Tranche 2 (40%) was due 2026-04-24; ASPSI confirmed extension in effect, official revised deadline pending from DOH. Sprint 002 closed 2026-04-24 with F3 + F4 specs Build-ready and F1 DCF Designer-ready. Today's heavy lift was the F2 PWA UAT closure (see F2 PWA section below).

**F3 and F4 skip-logic + validation specs both landed 2026-04-21 (Sprint 002 Day 2 overdelivery).** F3 spec reviewed at 1133 lines — all 12 sections A–L, 14 sanity findings, 15 CSPro PROC templates, 6 open questions dispositioned (1 routed to Juvy: Q31 IP_GROUP; 5 spec-decisions with override clause). F4 spec drafted at 904 lines — all 17 sections A–Q, 13 sanity findings (findings #1/#2 CLOSED-BY-VERIFICATION 2026-04-21: `C_HOUSEHOLD_ROSTER` already repeating at `max_occurs=20`, `J_HEALTH_SEEKING` intentionally respondent-level per Apr 20 source), 11 CSPro PROC templates, 8 open questions dispositioned (3 routed to ASPSI, 5 spec-decisions). Both F3 and F4 are **Build-ready**. Deliverables at `deliverables/CSPro/F3/` and `deliverables/CSPro/F4/`.

**F1 skip-logic + validation spec aligned with F3/F4 on 2026-04-21.** F1 spec rewrite added GPS capture via `REC_FACILITY_CAPTURE` (uses `ReadGPSReading()` helper) + verification-photo capture (filename-reference pattern, `TakeVerificationPhoto()` helper) + PSGC cascade (`onfocus` + `loadcase()` + `setvalueset()` via `PSGC-Cascade.apc`). F1 DCF now at **12 records / 671 items**. Shared `.apc` fragments live under `deliverables/CSPro/Capture-Helpers.apc` and `deliverables/CSPro/PSGC-Cascade.apc` — F3/F4 will consume the same helpers. Designer round 2 / sign-off (E2-F1-010) remains the carry-forward from Sprint 001. PSGC value sets still blocked on ASPSI.

**F2 PWA — Production live 2026-04-25 at v1.1.1.** Both UAT rounds closed:

- **v1.1.0 — UAT Round 1** (closed 2026-04-25): 7 issues fixed including the auto-advance bug, mid-section skip logic, Section G role-hide, max-value enforcement on age + tenure fields. Round opened 2026-04-23 by Shan (ASPSI), closed with "Pass with comments" 2026-04-24, all comments addressed and verified 2026-04-25.
- **v1.1.1 — UAT Round 2** (closed 2026-04-25): 6 issues fixed including the gate-question navigation regression (Q12=No / Q31=No couldn't proceed), specialty filter by role (Dentists no longer see medical specialties), real-time validation tooltips, language switcher visibility, and the silent submit-failure fix.

Production: https://f2-pwa.pages.dev. App header shows `v1.1.1 · spec 2026-04-17-m1`. Release notes at GitHub Releases [v1.1.0](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/releases/tag/v1.1.0) and [v1.1.1](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/releases/tag/v1.1.1); CHANGELOG.md auto-maintained.

**Round 3 (v1.2.0) backlog queued** — 3 enhancement issues on the [project board](https://github.com/users/cplreyes/projects/7): exclusive "I don't know" multi-select, "All of the above" auto-select, and matrix view for scale-style questions. ASPSI translation delivery (Filipino + others queued on their side) is the gating dependency for full localisation; switcher architecture is in place to drop them in without code changes.

**Automation in place** (all on `main` since 2026-04-25): GitHub Actions `uat-slack-events.yml` (real-time issue/milestone events to `#f2-pwa-uat`), `uat-slack-digest.yml` (09:00 MNL daily snapshot when a round is active), `uat-release-notes.yml` (milestone-closed → CHANGELOG + GitHub Release + Slack post + auto-bump `package.json`).

**F2 Epic 3 build is complete.** CSPro-encoder and Google Forms fallback tracks are retired and remain least priority — do not reopen unless deployment context changes fundamentally.

Comms infrastructure fully provisioned (project mailbox + Viber group both live, Shan onboarded as QA tester, Juvy confirmed as DOH-routing gate per the Apr 13 Team Communication Protocol).

Comms infrastructure fully provisioned (project mailbox + Viber group both live, Shan onboarded as QA tester, Juvy confirmed as DOH-routing gate per the Apr 13 Team Communication Protocol).

### By Workstream Epic

| # | Epic | Current State | Next Milestone |
|---|---|---|---|
| **0** | CAPI Project Management & Stakeholder Engagement | **Active / Ongoing** | First weekly status update shipped to ASPSI Mgmt Committee |
| **1** | Inception & Engagement Setup | **Done** | — (historical, closed Dec 2025) |
| **2** | Survey Questionnaire Design & Dictionary | **In Progress** (F1 Design — Designer round 2 / sign-off next; **F3 Build-ready, F4 Build-ready** — specs complete 2026-04-21; F2 data model lives inside the PWA spec; PLF Source Captured) | F1 sign-off (E2-F1-010); F3/F4 Designer validation (E2-F3-010, E2-F4-010) |
| **3** | CAPI Application Development | **In Progress** (F2 **PWA in production at v1.1.1**, Rounds 1+2 closed, Round 3 v1.2.0 queued; F1 CSPro build pending Designer sign-off; F3/F4 Build-ready) | F1 `FacilityHeadSurvey.fmf` Section A layout (Sprint 003); F3/F4 build slots TBD; F2 Round 3 features when slot opens |
| **4** | CSWeb Server Setup and Deployment | Not Started | Sync architecture decision documented |
| **5** | Tablet and Field Logistics | Not Started | Tablet provisioning SOP drafted |
| **6** | Testing and Pilot | Not Started | F1 desk test (follows Epic 3); QA Tester (Shan) onboarded to test workflow |
| **7** | Training and Documentation | Not Started | Survey manual outline (tied to D2) |
| **8** | Fieldwork Monitoring and Quality Control | Not Started (activates at fieldwork) | Dashboard requirements defined |
| **9** | Data Management and Security | **Governance Active** (NDU + privacy compliance ongoing) | Secure sync + backup strategy defined |
| **10** | Data Cleaning and Processing | Not Started | Batch edit rules drafted alongside instrument design |
| **11** | Analysis Support & Deliverables | Not Started | Interim tabulation template prepared ahead of D4 |
| **12** | Handover, Closeout & Retrospective | Not Started | NDU-compliant file disposition plan |

### By Survey Instrument

| Instrument | Mode | Pages | Current State |
|---|---|---|---|
| **F1 — Facility Head** | Interviewer-administered (CSPro CAPI) | 34 | **Design — closing** — DCF at 12 records / 671 items (post Apr 21 GPS+photo+PSGC-cascade pass); E2-F1-009b closed 2026-04-17; skip-logic spec aligned with F3/F4 on 2026-04-21; PSGC value sets still blocked on ASPSI; Designer round 2 / sign-off (E2-F1-010) is the next milestone |
| **F2 — Healthcare Worker** | **Self-admin — PWA (primary). Google Forms + CSPro-encoder fallbacks retired 2026-04-17. CSPro F2 track: least priority — do not reopen.** | 14 | **Production live at v1.1.1 (2026-04-25).** UAT Rounds 1 + 2 both closed (13 issues fixed). PWA at `deliverables/F2/PWA/app/`; production https://f2-pwa.pages.dev; staging https://b1e46a55.f2-pwa-staging.pages.dev. UAT automation live (Slack events + daily digest + release-notes pipeline). Round 3 (v1.2.0) backlog queued: 3 enhancement items on the project board. |
| **F3 — Patient** | Interviewer-administered (CSPro CAPI) | 23 | **Design — Build-ready 2026-04-21** (18 records / 840 items, sections A–L). Skip-logic + validation spec reviewed at `deliverables/CSPro/F3/F3-Skip-Logic-and-Validations.md`; 1 question to Juvy (Q31 IP_GROUP). |
| **F4 — Household** | Interviewer-administered (roster-heavy, new for Year 2; CSPro CAPI) | 26 | **Design — Build-ready 2026-04-21** (22 records / 623 items, sections A–Q; skip-logic + validation spec at `deliverables/CSPro/F4/F4-Skip-Logic-and-Validations.md`; `C_HOUSEHOLD_ROSTER` already repeating at `max_occurs=20`, `J_HEALTH_SEEKING` intentionally respondent-level — assumed schema patch closed by verification). |
| **PLF — Patient Listing Form** | Recruitment form | 1 | Source Captured |

---

## 2. Scope at a Glance

What is being built, in numbers:

| Dimension | Count |
|---|---|
| Survey instruments under development | **4** (F1, F2, F3, F4) + 1 recruitment form (PLF) |
| Total questionnaire content | **~98 pages** across all instruments |
| Data entry modes supported | **2** — interviewer-administered and self-administered |
| Languages supported per instrument | **2** — English and Filipino |
| F1 data fields specified | **664** across 12 data records (post Apr 21 GPS+photo+PSGC-cascade pass; includes `REC_FACILITY_CAPTURE`) |
| F2 data fields specified (PWA) | **114 items across 35 sections** — `deliverables/F2/PWA/app/spec/F2-Spec.md` |
| F3 data fields specified | **835** across 18 data records (sections A–L) |
| F4 data fields specified | **618** across 22 data records (sections A–Q; 3 repeating records; flat expenditure batteries in Section N) |
| F1 questions with skip logic mapped | **166** |
| F1 validation rules documented | **4 tiers** — hard stops, soft warnings, display gates, cross-field consistency |
| Target deployment footprint | **6 clusters**, nationally distributed |
| Target facility coverage | **102 UHC-IS + 17 non-UHC-IS** facilities |
| Enumerator devices in scope | Tablet-based (Android via CSEntry) |
| Data pipeline stages | Collection → sync → validation → batch editing → tabulation → delivery |

---

## 3. Contractual Deliverables

| ID | Deliverable | Tranche | Original Due | Current Status |
|---|---|---|---|---|
| **D1** | Approved Inception Report (work plan, sampling, survey design, protocols, tools) | T1 (15%) | 2025-12-12 | **Accepted** |
| **D2** | Approved survey materials & protocols: Survey Manual, SOPs, data collection tools, dialect translations | T2 (30%) | 2026-02-13 | **In Progress** (extended) — F1 instrument component ready; survey manual + SOPs + F2/F3/F4 instruments still in progress |
| **D3** | Approved pre-tested / pilot-tested questionnaires + field operations manuals + training materials | T2 (30%) | 2026-03-13 | **In Progress** (extended) — gated on Epic 6 (pretest) which depends on SJREB |
| **D4** | Approved progress report on piloting + initial preliminary data collection report | T3 (25%) | 2026-07-13 | Not Started |
| **D5** | Approved training documentation (materials + summary report with pre-/post-assessment) | T4 (30%) | 2026-07-31 | Not Started |
| **D6** | Approved full final report + summary slides / policy briefs + dissemination workshop documentation | T4 (30%) | 2026-08-13 | Not Started |

> Per CSA §6, "submission dates may change as agreed with the Client." D2 and D3 are on an agreed extended timeline to accommodate the toolchain switch from SurveyCTO (Year 1) to CSPro (Year 2).
>
> The Inception Report's Table 14 timetable consolidates these six items into four contractual tranches matching the payment schedule (T1–T4). See [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Timetable of Activities]] for the tranche-level view.

---

## 4. Workstream Epics

Each epic below is a long-running workstream that spans its portion of the engagement lifecycle. Epics will be expanded into tasks as work enters active sprints.

---

### Epic 0 — CAPI Project Management & Stakeholder Engagement

**Covers:** Project management discipline (sprint cadence, backlog grooming, Product Backlog maintenance), stakeholder reporting and communications, ethics coordination (SJREB, PSA), risk register, methodology governance, knowledge base maintenance, ongoing contract management, change management when questionnaires or scope evolve mid-engagement.

**Current state:** Active / Ongoing (runs continuously from kickoff through closeout)

**What's done:**
- Project knowledge base scaffolded and catalogued
- CSA, TOR, Inception Report, and prior-year Final Report ingested
- Project Intelligence Brief authored (timeline, decisions, stakeholder dynamics)
- 12-phase CAPI Development Workflow codified into IT Standards as a reusable template
- PSA sampling endorsement captured in the approved Inception Report
- Scrum discipline adopted with per-project Product Backlog and 1-week sprint cadence (Sprint 001 active)
- **Comms infrastructure live:** ASPSI project mailbox (`aspsi.doh.uhc.survey2.data@gmail.com`) for artifacts and decisions of record; CAPI Viber group for real-time coordination
- **Team structure clarified:** Carl as Data Programmer; Shan (ASPSI RA) as QA Tester for the CAPI build

**In flight:**
- SJREB ethics clearance coordination (via ASPSI)
- Ongoing risk tracking and stakeholder communication
- Product Backlog maintenance (this document)
- Authoring the weekly status update format for ASPSI Management Committee — Carl-controlled narrative, not a coordination ask

**Next milestone:** First weekly status update shipped to ASPSI Management Committee.

**Ties to:** Cross-cutting across all other epics. Anchors D1 (ongoing governance).

---

### Epic 1 — Inception & Engagement Setup

**Covers:** The opening phase of every CAPI engagement. Includes client scoping and requirements gathering, stakeholder mapping, kickoff workshop / alignment meeting, scope-of-work review against contract, initial risk register, team introductions and RACI clarification, ingestion of foundational project documents (contract, TOR, prior-year reports, Inception Report), initial sprint plan, approval of the Inception Report as the first contractual deliverable.

**Current state:** **Done** (historical — closed December 2025)

**What's done:**
- Engagement effective date 2025-11-14
- CSA and NDU signed (Dec 12 and Dec 15, 2025)
- TOR reviewed and understood (10 duties of the Data Programmer role)
- Stakeholders mapped: DOH-PMSMD (client), ASPSI (implementer), SJREB (ethics), ADB (technical advisor), PSA (sampling)
- Prior-year IDinsight Final Report ingested as baseline context
- Inception Report authored by ASPSI, approved by client, Tranche 1 released (D1 Accepted)
- Project knowledge base scaffolded

**Closeout status:** Epic complete. Serves as a reference model for future CAPI engagements.

**Ties to:** D1 (Inception Report).

---

### Epic 2 — Survey Questionnaire Design & Dictionary

**Covers:** Per-instrument questionnaire ingestion, data model specification (records, fields, value sets, identifiers, roster structures), field-by-field skip logic mapping, validation rule documentation (hard stops, soft warnings, display gates, cross-field consistency), informed consent form design (English + Filipino), and schema correction passes.

**Current state:** In Progress (F1 Design-closing; F3 Build-ready; F4 Build-ready; F2 spec frozen in PWA; PLF Source Captured)

**Per-instrument status:**

| Instrument | State | Notes |
|---|---|---|
| F1 | **Design — closing** | DCF at 12 records / 671 items after Apr 21 GPS+photo+PSGC-cascade pass. All 166 questions walked for skip logic; spec aligned with F3/F4 architecture. Four-tier validation rules documented. The 6 schema items frozen as `PENDING_DESIGN_*` defaults; **E2-F1-009b closed 2026-04-17**. PSGC value sets still blocked on ASPSI. Designer round 2 / sign-off (E2-F1-010) is the remaining work. |
| F2 | **Data model captured inside the PWA spec** | Data model + skip graph + validation live in `deliverables/F2/PWA/app/spec/F2-Spec.md` (114 items / 35 sections) rather than a CSPro dictionary. The earlier Apr 15 F2-0 tooling memo, cover-block rewrite, Spec.md, Skip-Logic, Validation, Cross-Field, and Apps Script bundle were the inputs that fed the PWA build. Cover-block rewrite still pending ASPSI review. |
| F3 | **Design — Build-ready 2026-04-21** | 18 records / 840 items, sections A–L. Shared `cspro_helpers.py`. Skip-logic + validation spec at `deliverables/CSPro/F3/F3-Skip-Logic-and-Validations.md` (reviewed 2026-04-21). 1 question to Juvy (Q31 IP_GROUP); 5 spec-decisions closed. |
| F4 | **Design — Build-ready 2026-04-21** | 22 records / 623 items, sections A–Q. `C_HOUSEHOLD_ROSTER` repeating (`max_occurs=20`, id-item `MEMBER_LINE_NO`); `H_PHILHEALTH_REG` and `J_HEALTH_SEEKING` respondent-level non-repeating per Apr 20 source rephrase. Flat expenditure batteries in Section N. Skip-logic + validation spec at `deliverables/CSPro/F4/F4-Skip-Logic-and-Validations.md` (draft 2026-04-21). Findings #1 and #2 in §1.A closed-by-verification 2026-04-21. |
| PLF | Source Captured | Implementation decision (CAPI vs paper) precedes design. |

**What's done across the epic:** All five source questionnaires ingested and catalogued. F1 generator + DCF built + cleaned (12/664 post Apr 21 GPS/photo pass). F3 generator + DCF built (18/835); skip-logic + validation spec complete 2026-04-21. F4 generator + DCF built (22/618); skip-logic + validation spec complete 2026-04-21 with 2 P1 schema gaps flagged. Shared `cspro_helpers.py` + `Capture-Helpers.apc` + `PSGC-Cascade.apc` extracted. F2 data model + skip graph + validation captured in the PWA spec.

**In flight:** F1 Designer round 2 / sign-off (E2-F1-010) — the carry-forward miss from Sprint 001. F2 cover-block rewrite still with ASPSI.

**Next milestone:** F1 sign-off (E2-F1-010); F3 Designer validation + sign-off (E2-F3-010); F4 Designer validation + sign-off (E2-F4-010).

**Ties to:** D2, D3.

---

### Epic 3 — CAPI Application Development (CSPro + CSEntry / PWA)

**Covers:** Application build per instrument. F1/F3/F4 are CSPro Designer / CSEntry CAPI applications — form layout, tablet UX, capture types, question text (English + Filipino), skip logic wiring, validation wiring, dynamic value sets, multi-language handling, FIELD_CONTROL block (informed consent, eligibility, AAPOR disposition codes, GPS, photo, interviewer/supervisor IDs, timestamps), and roster engines (F4). F2 is a Progressive Web App — Vite+React+TS installable shell with IndexedDB autosave, skip-logic nav, Apps Script sync backend.

**Current state:** **In Progress.** F2 PWA in production at v1.1.1 (Rounds 1 + 2 closed 2026-04-25; Round 3 v1.2.0 enhancements queued on the project board). F1 CSPro build pending Designer sign-off (E2-F1-010). F3 Build-ready; F4 Build-ready (schema verified 2026-04-21 — assumed roster/health-seeking patch E2-F4-009 closed by verification).

**Per-instrument status:** F2 PWA in production at v1.1.1 (Rounds 1 + 2 closed 2026-04-25; Round 3 v1.2.0 enhancements queued); F1 CSPro pending Designer sign-off + FMF kickoff (FMF deferred to Sprint 003 pending form-layout plan); F3/F4 DCFs built and skip-logic + validation specs complete 2026-04-21, CSPro build slots not yet scheduled.

**Next milestone:** F1 form file (`FacilityHeadSurvey.fmf`) Section A layout after E2-F1-010 sign-off (Sprint 003); F2 PWA Round 3 v1.2.0 enhancements (#16 exclusive multi-select, #17 all-of-the-above auto-select, #18 matrix view) when slot opens.

**Sequencing strategy (CSPro CAPI track):**
1. F1 first as the reference instrument (largest, exercises the full range of patterns) — currently Design-closing, awaiting Designer sign-off; spec aligned with F3/F4 on 2026-04-21 with shared `Capture-Helpers.apc` + `PSGC-Cascade.apc`
2. F3 follows F1 (reuses F1's interviewer-administered patterns) — DCF built, skip-logic + validation spec complete 2026-04-21, Build-ready
3. F4 last (roster engine benefits from patterns refined in F1/F3) — DCF built with `C_HOUSEHOLD_ROSTER` repeating (`max_occurs=20`), `H_PHILHEALTH_REG` and `J_HEALTH_SEEKING` respondent-level per Apr 20 source; skip-logic + validation spec complete 2026-04-21; assumed schema patch (E2-F4-009) closed by verification

**Sequencing strategy (F2 PWA track — independent of the CSPro sequence):**
1. M0 Foundation — Vite+React+TS+Tailwind+shadcn+vite-plugin-pwa installable shell (shipped 2026-04-17)
2. M1 Generator v1 + single-section render (shipped 2026-04-17)
3. M2–M11 — autosave/IndexedDB, skip-logic nav, Apps Script backend, sync orchestrator, full 114-item instrument, validation + cross-field rules, enrollment, i18n, admin dashboard, hardening (shipped 2026-04-18)
4. Pilot readiness checkpoint (open) — three options per `NEXT.md`: run pilot with 5–10 HCWs at one facility / close deferred M11 items first / move to M12 F3/F4 parity
5. Deferred M11 items (slot in only if pilot feedback demands): per-HCW tokens, draft auto-migration across spec versions, iOS push, admin mutations

**F2 PWA note:** The Apr 15 Google Forms / paper / deferred-CSPro three-path model is superseded by the PWA primary build. The PWA is the only active F2 build path. **The CSPro-encoder track for F2 is the least priority item in this engagement** — do not reopen without an explicit decision reversal driven by a deployment-context change. If ASPSI's deployment context ever shifts back, prior artifacts remain under `deliverables/F2/` as fallback starting points only.

**F2 QA/UAT note (2026-04-25):** 3/3 Playwright E2E tests pass (golden path enrollment → 10 sections → review → submit; section lock; language switch). Auto-advance and section-lock UX shipped. UAT Rounds 1 + 2 closed 2026-04-25 — 13 issues fixed across the two rounds (skip-logic, validation, navigation regression, specialty filter, real-time tooltips, language switcher visibility, submit error UX, etc.). Production at https://f2-pwa.pages.dev (v1.1.1 · spec 2026-04-17-m1). Round 3 v1.2.0 enhancements queued: #16 exclusive multi-select, #17 all-of-the-above auto-select, #18 matrix view.

**Ties to:** D2, D3.

---

### Epic 4 — CSWeb Server Setup and Deployment

**Covers:** Sync architecture decision (CSWeb vs Dropbox vs FTP vs Bluetooth, with trade-off documentation), server provisioning, authentication and access control, data dictionary deployment per instrument, round-trip sync testing per instrument, server-side storage and retention.

**Current state:** Not Started

**Next milestone:** Sync architecture decision documented.

**Dependencies:** Sync architecture decision must precede all downstream deployment work.

**Ties to:** D3, TOR Duty 7 (configure web server for uploading completed questionnaires).

---

### Epic 5 — Tablet and Field Logistics

**Covers:** Tablet provisioning SOP, CSEntry installation and configuration, per-role deployment packages (interviewer vs supervisor), sync credential management, backup and recovery plan for mid-interview device failure, spare device strategy, field rollout logistics, device check-in/check-out procedures.

**Current state:** Not Started

**Next milestone:** Tablet provisioning SOP drafted.

**Dependencies:** Requires Epic 3 build and Epic 4 sync architecture.

**Ties to:** D3.

---

### Epic 6 — Testing and Pilot

**Covers:** Per-instrument desk test (walk every skip path manually), bench test with mock cases (youngest/oldest eligible, refusal at each gate, "None of the above" on every multi-select, every Other-specify, maximum roster size, every dynamic branch, every validation rule triggered), pair test with domain expert for interpretation drift, regression test after every schema change, archived test cases for replay, pretest with 10–30 real respondents per instrument, enumerator debrief, iteration cycles.

**Current state:** Not Started

**Per-instrument status:** All instruments Not Started. Testing follows Epic 3 build per instrument.

**Roles:**
- **Carl (Data Programmer)** — author of test specs, owner of desk and bench tests against the build, owner of regression artifacts.
- **Shan (QA Tester, ASPSI RA)** — independent QA pass on each instrument's CAPI build. Receives handoff bundles from Carl with the build, test scripts, known-issue list, and walkthrough notes. Surfaces defects ahead of the SJREB protocol freeze and the formal pretest with respondents.

**Next milestone:** F1 desk test, once F1 build is underway. QA handoff workflow to Shan defined ahead of first F1 build slice ready for review.

**Critical dependency:** Pretest with real respondents requires SJREB clearance (tracked in Epic 0).

**Ties to:** D3 (pre-tested questionnaires).

---

### Epic 7 — Training and Documentation

**Covers:** Survey manual (interviewer guide), field operations manual, enumerator training materials (CSEntry walkthrough, common pitfalls, sync procedure, disposition coding, consent administration), training delivery logistics, pre- and post-training assessment instruments, user manuals for supervisors, contributions to the Inception Report's field protocol documentation.

**Current state:** Not Started

**Next milestone:** Survey manual outline (tied to D2).

**Ties to:** D2 (survey manual, SOPs), D3 (field operations manual, training materials), D5 (training documentation with pre/post assessment).

---

### Epic 8 — Fieldwork Monitoring and Quality Control

**Covers:** Real-time sync monitoring dashboard (daily case counts, completion rates, disposition breakdowns per cluster), hotfix protocol for in-field application issues, issue log with triage and resolution, field-reported anomaly tracking, interviewer performance monitoring, weekly client progress updates during main collection.

**Current state:** Not Started (activates at fieldwork kickoff)

**Next milestone:** Dashboard requirements defined before first deployment.

**Ties to:** TOR Duty 8 (prepare survey data dashboard), TOR Duty 9 (technical support during CAPI survey), D4 (progress report on piloting).

---

### Epic 9 — Data Management and Security

**Covers:** Data privacy compliance (RA 10173 Data Privacy Act, RA 8293, RA 10175), NDU adherence, secure sync transport, access control on server, encryption at rest and in transit, backup strategy, data retention and destruction policy (per NDU turn-over clause), audit trail for all data movement, PII handling protocols.

**Current state:** Governance Active — NDU signed 2025-12-12, privacy compliance ongoing throughout engagement

**What's done:**
- Non-Disclosure Undertaking signed (Dec 12, 2025)
- RA 10173 / RA 8293 / RA 10175 obligations acknowledged
- Confidentiality clause in CSA (§10g, §11) in effect
- Project mailbox provisioned as the ASPSI-custody correspondence/artifact channel (multi-user shared Gmail; treat as shared inbox)

**Next milestone:** Secure sync architecture and backup strategy defined as part of Epic 4.

**Ties to:** NDU, CSA §10g and §11, cross-cutting across all other epics.

---

### Epic 10 — Data Cleaning and Processing

**Covers:** Batch editing pipeline per instrument (structure checks, validity checks, consistency checks, imputation rules where appropriate), CSBatch scripts, edit specifications document, data validation passes on incoming production data, hot-deck imputation strategy, data quality reporting.

**Current state:** Not Started

**Next milestone:** Batch edit rules drafted alongside instrument design (rules are derived from validation rules documented in Epic 2).

**Ties to:** D4 (initial data collection report), D6 (edit specifications in final documentation).

---

### Epic 11 — Analysis Support & Deliverables

**Covers:** Interim tabulation (cross-tabs) for client progress reports during piloting and fieldwork, final dataset exports in multiple formats (CSPro `.dat`, Stata, SPSS, CSV), codebook, edit specifications document, contributions to the final report, policy brief support, dissemination workshop documentation.

**Current state:** Not Started

**Next milestone:** Interim tabulation template prepared ahead of D4.

**Ties to:** D4 (progress report with piloting results), D6 (final report, policy briefs, dissemination).

---

### Epic 12 — Handover, Closeout & Retrospective

**Covers:** End-of-engagement transition and knowledge transfer. Includes system handover package (generator scripts, CSPro application files, CSWeb server admin credentials, batch editing scripts, data dictionary, deployment package), operational runbook for client IT/data team, knowledge transfer sessions with client technical staff, formal client sign-off and acceptance letter, NDU-compliant turn-over or destruction of all project files (per NDU clause), final lessons-learned capture, **retrospective writeback into the CAPI Development Workflow template** (so each engagement compounds methodology improvements), and archival of the project knowledge base into `4_Archives/`.

**Current state:** Not Started

**Next milestone:** NDU-compliant file disposition plan drafted (defines what stays, what transfers to client, what is destroyed at project close).

**Key activities:**
- System handover package assembled
- 1–3 knowledge transfer sessions with client IT/data team
- Operational runbook authored (add user, re-sync, restart server, recover failed sync, export data)
- Client sign-off and acceptance letter received
- NDU-compliant file turn-over / destruction executed
- Lessons-learned session with internal stakeholders
- Refinements fed back into the CAPI Development Workflow living-document log
- Project knowledge base archived to `4_Archives/`

**Why this matters for service replicability:** Without the retrospective writeback step, each engagement teaches lessons but nothing compounds across projects. Epic 12 is the mechanism that turns every CAPI project into an investment in the service offering.

**Ties to:** D6 (final deliverables), NDU turn-over clause, CAPI Development Workflow template (living document).

---

## 5. Risks & Watchlist

| Risk | Likelihood | Impact | Mitigation | Affected Epics |
|---|---|---|---|---|
| SJREB ethics clearance delay | Medium | High — blocks all pretesting and fieldwork | ASPSI actively coordinating; tracked as the long-pole dependency; remains the single most important external dependency | 0, 6 |
| Timeline pressure on D2 / D3 extended window / Tranche 2 | High (Tranche 2 due Fri 2026-04-24) | High — late delivery penalty applies (1% of total per calendar day if no further extension) | Apr 14 matrices + Word tools submission enacted the "submit what's ready and negotiate" mitigation; PMSMD feedback expected Apr 20 → 4-day turnaround if revisions come back. F1/F3/F4 DCFs stable; F2 PWA pilot-ready. | 2, 3, 6, 7 |
| Late questionnaire revisions from client | Low–Medium | Medium | Script-generated data models (F1/F3/F4) re-run in minutes; PWA generator regenerates from `F2-Spec.md`. Reproducible generators absorb revisions cheaply across all four instruments. | 2, 3 |
| Household roster complexity (F4) | Low | Medium | F4 skip-logic + validation spec complete 2026-04-21. Schema verified: `C_HOUSEHOLD_ROSTER` already repeating (`max_occurs=20`, id-item `MEMBER_LINE_NO`); `J_HEALTH_SEEKING` intentionally respondent-level per Apr 20 source rephrase (no roster loop needed for Q101–Q107). WHO expenditure grid + catastrophic-expenditure check + bill-recall chain modeled. | 2, 3 |
| F2 PWA pilot readiness — unfamiliar deployment model for ASPSI ops | **Mitigated 2026-04-25** | Low — UAT closure verified the model works | UAT Rounds 1 + 2 closed cleanly (Shan as tester, GitHub Issues for formal feedback, Slack `#f2-pwa-uat` for coordination). 13 real bugs surfaced + fixed; production at v1.1.1. Slack-bot automation now keeps stakeholders informed for future rounds. Pilot model proved out — keep this row open as a watch item until field deployment, then retire. | 3, 6 |
| F2 PWA deferred-M11 tech debt (per-HCW tokens, draft auto-migration, iOS push, admin mutations) | Low | Low–Medium — mitigations in place, slot in only if pilot feedback demands | Current posture: static enrollment (any HCW ID once facility selected); drift modal forces reload on spec-version change; drafts survive in IndexedDB but may fail validation on breaking schema shifts; admin can edit Config sheet directly. | 3 |
| F2 questionnaire cover blocks authored interviewer-style | High (confirmed) | Low — PWA renders its own cover blocks from spec; print-mode / paper fallback still gated on ASPSI review of the rewrite draft | Draft at `deliverables/F2/F2-Cover-Block-Rewrite-Draft.md` is sitting with ASPSI. PWA primary build proceeds; rewrite feeds any future paper-mode or Google Forms fallback. | 2 |
| QA bandwidth / Shan ramp-up time | Low–Medium | Medium | Shan's first handoff target shifted from the Google Forms Apps Script bundle to the PWA cross-platform QA checklist + (eventually) F1 CSPro bench testing. Handoffs are authored as opinionated walkthroughs, not raw artifacts. | 6 |
| Tablet device failure in field | Low | Medium | Backup/recovery plan required before deployment; partial-save patterns built into every instrument | 5, 8 |
| Sync connectivity in remote clusters | Medium | Medium | Sync architecture decision will weigh offline tolerance; multiple fallback transports available | 4 |
| PII breach or data loss | Low | High — regulatory and reputational | NDU in effect, encryption requirements, audit trail, retention policy to be finalized in Epic 9; project mailbox treated as shared inbox under ASPSI custody | 9 |
| Incomplete handover puts service replicability at risk | Medium | Medium — lessons don't compound across engagements | Epic 12 explicit, retrospective writeback mandatory | 12 |

---

## 6. Timeline & Sequencing Strategy

1. **Epic 0 runs continuously** from kickoff through closeout — PM, risk, ethics coordination, stakeholder reporting, change management.
2. **Epic 1 (Inception) is a discrete early phase** — one-time at engagement start. Already closed for this project.
3. **Epic 9 (Data Management and Security) runs continuously** — data privacy and security governance is always on, with concrete deliverables concentrated around Epic 4 and Epic 8.
4. **Epics 2 → 3 → 6 form the per-instrument pipeline.** Each instrument moves through Design → Build → Testing/Pilot in sequence. Instruments are staggered: F1 first as reference (now Build-ready), F2 second (self-admin), F3 third, F4 last (roster).
5. **Epics 4 and 5 must be ready before the first pretest.** Sync server and tablet logistics are prerequisites for any field activity.
6. **Epic 7 deliverables are staged:** Survey manual outline early (D2), full training materials before pretest (D3), training delivery documentation after (D5).
7. **Epic 8 activates at first deployment** and runs through to end of fieldwork.
8. **Epic 10 activates as data begins flowing** — batch editing rules are authored alongside Epic 2 but only run against real data once Epic 8 is live.
9. **Epic 11 concentrates at the closeout** (D4, D6) but the interim tabulation component runs throughout fieldwork.
10. **Epic 12 is the final phase** — handover package, knowledge transfer, NDU file disposition, retrospective writeback, and archive. Kicks in after D6 acceptance.

**Key dates on the horizon:**
- **D2 / D3 submission** — extended timeline, targeted alongside the first pretest
- **D4 progress report with piloting results** — original due 2026-07-13
- **D5 training documentation** — original due 2026-07-31
- **D6 final report + dissemination** — original due 2026-08-13
- **Engagement close** — targeted end of August 2026

See [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Timetable of Activities]] for the Inception Report's Table 14 view of the same horizon (consolidated to four contractual tranches).

---

## Appendix A — Methodology & Quality Assurance

CAPI development follows a 12-phase workflow codified from industry best practice and grounded in:

- **US Census Bureau CSPro 8.0 Users Guide** — authoritative reference for the toolchain
- **DHS Program** Survey Organization Manual — de-facto gold standard for large-scale CSPro CAPI deployments
- **UNICEF MICS6 / MICS7** CAPI implementation handbook
- **World Bank LSMS+** household survey guidance
- **International Household Survey Network (IHSN)** — survey lifecycle and metadata standards
- **AAPOR Standard Definitions** — disposition codes and response-rate reporting
- **IEEE/ISO/IEC 29148** — requirements specification discipline
- **ISO/IEC 25010** — software quality model (functional correctness, usability)

**Two governing design rules:**

1. **Generator-based artifacts.** Instrument data models are produced by version-controlled scripts, never hand-edited. Late questionnaire revisions are absorbed by re-running, not manual rework. Primary control against timeline risk.
2. **Logic pass before build.** Field-by-field skip logic and validation rules are walked against the data model before any application development begins. Schema issues surface while they are still cheap to fix. Primary control against functional defects. (F1 demonstrated the value of this rule — the Apr 13 LSS confirmation that no schema changes were needed validated the pre-build logic pass investment.)

**Validation rules** are classified into three tiers:
- **Hard stops** — block and re-enter
- **Soft warnings** — warn and accept with confirmation
- **Display gates** — conditional question visibility

**Test coverage discipline:**
- Every skip path walked at least once in desk test
- Every hard validation triggered and cleared in bench test
- Every soft validation triggered and overridden in bench test
- Every dynamic value-set branch exercised
- Pair test with domain expert for interpretation drift
- Independent QA pass by Shan before formal pretest with respondents
- Mock cases archived as regression artifacts

---

## Appendix B — Status Legend

### Epic status values
| State | Definition |
|---|---|
| **Not Started** | No work initiated |
| **Ready to Start** | Upstream blockers cleared; work can begin in the next sprint |
| **In Progress** | Active work underway |
| **Active / Ongoing** | Continuous workstream (e.g., PM, governance) |
| **Governance Active** | Policy and compliance workstream always on, concrete deliverables staged |
| **On Hold** | Paused pending an external dependency |
| **Done** | Epic complete (used for discrete phase epics like Inception) |
| **Closed** | All work complete at engagement close |

### Per-instrument readiness ladder
**Not Started → Source Captured → Design → Build-ready → Build → Internal Testing → Pretest → Ready for Fieldwork → In Production → Closed**

| State | Definition |
|---|---|
| **Not Started** | No work initiated |
| **Source Captured** | Input materials received, ingested, catalogued |
| **Design** | Data model specified; field logic documented and reviewed |
| **Build-ready** | Design closed; schema final; awaiting CAPI Designer build slot |
| **Build** | CAPI application under construction in CSPro Designer |
| **Internal Testing** | Desk, bench, and pair testing |
| **Pretest** | Field validation with a small sample of real respondents |
| **Ready for Fieldwork** | Pretest sign-off received; instrument and application frozen |
| **In Production** | Main data collection underway |
| **Closed** | Data delivered, documentation finalized |

---

## Appendix C — Comms & Custody

| Channel | Purpose | Audience |
|---|---|---|
| **Project mailbox** (`aspsi.doh.uhc.survey2.data@gmail.com`) | Artifacts and decisions of record; ASPSI-custody Drive for CAPI files | Carl, Shan, ASPSI staff (multi-user shared) |
| **CAPI Viber group** | Real-time coordination, ping-velocity questions, build/test handoff notifications | Carl, Shan, ASPSI dev support staff (DOH not in this group) |
| **Local repo** (`C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/`) | **System of record** for all CAPI artifacts. Mailbox/Drive is a mirror, not the canonical store. | Carl |
| **Weekly status update to ASPSI Mgmt Committee** (E0-010, in flight) | Carl-authored narrative of CAPI progress, risks, asks | ASPSI Management Committee |

---

*This backlog is groomed at each sprint close. Epics will be expanded into tasks as work enters active sprints. For granular sprint-level work items, see `sprint-current.md` (internal sprint view).*
