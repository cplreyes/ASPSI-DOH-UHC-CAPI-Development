---
project: UHC Survey Year 2 — CAPI Development
client: Department of Health (DOH-PMSMD)
implementer: Asian Social Project Services, Inc. (ASPSI)
data_programmer: Carl Patrick L. Reyes
qa_tester: Shan (ASPSI, RA)
contract: CSA signed 2025-12-15, effective 2025-11-14
engagement_window: November 2025 – August 2026
last_updated: 2026-04-15
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

**F1 dictionary rebuilt 2026-04-14; F2 Google Forms track kicked off 2026-04-15.** `generate_dcf.py` was authored from scratch and `FacilityHeadSurvey.dcf` regenerated to **15 records, 657 items** — earlier scrum entries claiming an Apr 11 v2/952-item build were premature (no generator existed before today). The Apr 13 LSS meeting did **not** in fact discuss the 6 open F1 items; `E2-F1-009b` is reopened as `blocked` until LSS decides. F1 awaits the Designer walkthrough (E2-F1-010) before declaring Build-ready.

**F2 is now recognized as a special case with three capture paths** (Google Forms primary, paper→Forms encoding fallback, optional deferred CSPro encoder). F1 sign-off is NOT a hard gate — the Google Forms path doesn't reuse F1's CSPro patterns, so F2 kickoff runs in parallel with F1 close-out. F2-0 Tooling & Access Model Decision Memo drafted Apr 15 (`deliverables/F2/F2-0_Tooling-and-Access-Model-Decision-Memo.md`) with 8 decisions for ASPSI. A separate finding surfaced during extraction: the April 8 F2 PDF is authored using the interviewer-administered template (read-aloud consent, FIELD CONTROL enumerator block, 1.5-hour interview framing) — the cover blocks will need a self-admin rewrite before the Google Form can ship (Carl drafts, ASPSI reviews). Comms infrastructure is fully provisioned (project mailbox + Viber group both live, QA tester onboarded).

### By Workstream Epic

| # | Epic | Current State | Next Milestone |
|---|---|---|---|
| **0** | CAPI Project Management & Stakeholder Engagement | **Active / Ongoing** | First weekly status update shipped to ASPSI Mgmt Committee |
| **1** | Inception & Engagement Setup | **Done** | — (historical, closed Dec 2025) |
| **2** | Survey Questionnaire Design & Dictionary | **In Progress** (F1 Design closing — Designer walkthrough next; **F2 Google Forms track kicked off 2026-04-15**; F3/F4/PLF Source Captured) | F1 sign-off (E2-F1-010); F2 cover-block rewrite draft + spec extraction |
| **3** | CAPI Application Development | **Ready to Start (F1); F2 Google Forms build pending spec** | F1 form file — Section A laid out in CSPro Designer; F2 Apps Script generator scaffolded |
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
| **F1 — Facility Head** | Interviewer-administered (CSPro CAPI) | 34 | **Design — closing** — DCF rebuilt 2026-04-14 (15 records, 657 items); Designer walkthrough (E2-F1-010) in progress; E2-F1-009b reopened pending LSS on 6 items |
| **F2 — Healthcare Worker** | **Self-admin — Google Forms (primary); paper→Forms encoding fallback; optional deferred CSPro encoder** | 14 | **Design — Google Forms track kicked off 2026-04-15.** Tooling memo drafted; cover-block rewrite + spec extraction next. |
| **F3 — Patient** | Interviewer-administered (CSPro CAPI) | 23 | Source Captured |
| **F4 — Household** | Interviewer-administered (roster-heavy, new for Year 2; CSPro CAPI) | 26 | Source Captured |
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
| F1 data fields specified | **657** across 15 data records (4 secondary-data records empty pending LSS) |
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

**Current state:** In Progress (F1 closed; F2–F4 + PLF pending)

**Per-instrument status:**

| Instrument | State | Notes |
|---|---|---|
| F1 | **Design — closing** | DCF rebuilt from scratch 2026-04-14: 15 records, 657 items (4 secondary-data records empty pending LSS). All 166 questions walked for skip logic. Four-tier validation rules fully documented. The 6 schema items from the field-logic pass are encoded as `PENDING_DESIGN_*` constants in `generate_dcf.py`; **E2-F1-009b is reopened/blocked** — the Apr 13 LSS meeting did not in fact discuss them. Designer walkthrough (E2-F1-010) in progress. |
| F2 | **Design — Google Forms track kicked off 2026-04-15** | **SPECIAL CASE** — not a CSPro CAPI instrument by default. Primary build is Google Forms (self-admin by HCW, 3-day window). Paper fallback encodes back into the same Form. Optional CSPro encoder variant is deferred as a late conditional build. Tooling & Access Model Decision Memo drafted (`deliverables/F2/F2-0_Tooling-and-Access-Model-Decision-Memo.md`). Cover-block rewrite dependency surfaced — April 8 PDF uses interviewer template; Carl drafting rewrite for ASPSI review. |
| F3 | Source Captured | Outpatient + inpatient dual-population eligibility to be mapped during design. |
| F4 | Source Captured | Household roster structure is the headline design challenge. |
| PLF | Source Captured | Implementation decision (CAPI vs paper) precedes design. |

**What's done across the epic:** All five source questionnaires ingested and catalogued. F1 generator + DCF built. F2 Tooling & Access Model Decision Memo drafted (2026-04-15).

**In flight:** F1 Designer walkthrough (E2-F1-010); E2-F1-009b blocked on LSS decisions for the 6 open items. F2 Google Forms design track active in parallel — cover-block rewrite draft (E2-F2-012) and spec extraction (E2-F2-013) are the next deliverables.

**Next milestone:** F1 sign-off (E2-F1-010); F2 spec sign-off (E2-F2-018).

**Ties to:** D2, D3.

---

### Epic 3 — CAPI Application Development (CSPro + CSEntry)

**Covers:** CSPro Designer application build per instrument — form layout, tablet UX, capture types, question text (English + Filipino), skip logic wiring, validation wiring (hard stops via error + re-enter, soft warnings via accept, display gates via conditional visibility), dynamic value sets (context-dependent option lists), multi-language handling, FIELD_CONTROL block (informed consent, eligibility screening, AAPOR disposition codes, GPS, interviewer/supervisor IDs, timestamps), and roster engines (F4).

**Current state:** **Ready to Start (F1 CSPro CAPI); F2 Google Forms build pending spec sign-off.** F1 design closed clean Apr 13, no remaining blockers from Epic 2 for F1. F2 primary build is on a parallel Google Forms track, not the CSPro sequence.

**Per-instrument status:** F1 ready to start; F2 Google Forms track pending spec (E2-F2-018); F3/F4 not started (each follows its own Epic 2 closeout); F2-CSPro encoder deferred as optional late build.

**Next milestone:** F1 form file (`FacilityHeadSurvey.fmf`) created in CSPro Designer; F2 Apps Script generator scaffolded once spec signs off.

**Sequencing strategy (CSPro CAPI track):**
1. F1 first as the reference instrument (largest, exercises the full range of patterns)
2. F3 follows F1 (reuses F1's interviewer-administered patterns)
3. F4 last (roster engine benefits from patterns refined in F1/F3)
4. **F2-CSPro encoder variant** (conditional, optional) — if activated after F2 Google Forms testing, scheduled as the tail of this sequence after F1/F3/F4 are complete

**Sequencing strategy (F2 Google Forms track — parallel, independent of CSPro sequence):**
1. F2 Tooling & Access Model Decision Memo → ASPSI (done 2026-04-15)
2. F2 cover-block rewrite draft (E2-F2-012)
3. F2 spec extraction + skip-logic restructure for section-based branching (E2-F2-013..018)
4. F2 Apps Script generator + Form build (E3-F2-GF-001..011)
5. F2 desk test + 3-day dry-run (E3-F2-GF-012..014)
6. Gate decision: activate deferred F2-CSPro track, or leave parked (E3-F2-GF-015)

**F2 special-case note:** F2 does not flow through the CSPro Design → CSPro Build pipeline for its primary build. The Google Forms track is managed as a standalone sub-workstream inside Epics 2 and 3. The optional late F2-CSPro build reuses the standard CSPro patterns from F1/F3/F4, but only if activated. See `memory/project_f2_capture_modes.md` and the F2 sections of `scrum/epics/epic-02-questionnaire-design.md` and `scrum/epics/epic-03-capi-application.md`.

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
| Timeline pressure on D2 / D3 extended window | Medium | High — late delivery penalty applies (1% of total per calendar day if no further extension) | F1 design closed clean (Apr 13) — pipeline ahead of where it was a week ago. F2–F4 design pipeline next. Sequenced instrument delivery; reproducible generators absorb late questionnaire revisions cheaply | 2, 3, 6, 7 |
| Late questionnaire revisions from client (F2–F4) | Low–Medium | Medium | Script-generated data models re-run in minutes; F1 came through clean which is one favorable data point but not predictive of F2–F4 | 2, 3 |
| Household roster complexity (F4) | Medium | Medium | F4 sequenced last so lessons from F1/F2/F3 inform the roster design | 2, 3 |
| Self-administered mode (F2) unfamiliarity | Low | Medium | F2 reframed 2026-04-15 as a special case: Google Forms primary, paper→Forms encoding fallback, optional deferred CSPro encoder. Decouples F2 from CSPro CAPI pipeline complexity; unfamiliarity absorbed into a tooling memo + Apps Script generator, not into a CSPro app. | 2, 3 |
| F2 questionnaire cover blocks authored interviewer-style | High (confirmed) | Low–Medium — rewrite is modest but gated on ASPSI review | Carl drafting rewrite text (consent, duration framing, FIELD CONTROL removal, facility ID self-admin mapping) for ASPSI/Dr. Claro review. Build proceeds on the questionnaire body (Sections A–J) in parallel; cover blocks wired in last. | 2, 3 |
| F2 Google Forms skip-logic limitations (section-based only) | Medium | Low–Medium — some per-question branching won't survive translation cleanly | Spec extraction flags affected items; restructure logic into section boundaries; fall back to inline instructions where section split is impractical. | 2, 3 |
| QA bandwidth / Shan ramp-up time on CSPro toolchain | Low–Medium | Medium | QA handoff bundles authored as opinionated walkthroughs (not raw artifacts) so Shan can productively review without deep CSPro internals knowledge | 6 |
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
