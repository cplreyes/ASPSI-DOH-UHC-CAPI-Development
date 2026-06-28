---
project: UHC Survey Year 2 — CAPI Development
client: Department of Health (DOH-PMSMD)
implementer: Asian Social Project Services, Inc. (ASPSI)
data_programmer: Carl Patrick L. Reyes
qa_tester: Shan (ASPSI, RA)
contract: CSA signed 2025-12-15, effective 2025-11-14
engagement_window: November 2025 – August 2026
last_updated: 2026-06-28
---

# Product Backlog — UHC Survey Year 2 CAPI Development

> Stakeholder-facing view of the full CAPI (Computer-Assisted Personal Interviewing) development workstream for the DOH Universal Health Care Survey Year 2.
>
> Organized around **13 workstream epics (0–12)** covering the full engagement lifecycle from inception through handover. Epics are derived from the reusable [[2_Areas/IT-Standards/templates/CAPI-Development-Workflow|CAPI Development Workflow]] template — this project is the first reference engagement for that template.
>
> Updated at each sprint close. For day-to-day progress, see `sprint-current.md` (internal sprint view).

---

## 1. Status at a Glance

### Headline — 2026-06-28

**The build phase is essentially complete. The project has shifted from building to field-readiness — and that's Carl's last active lane. Everything from the pretest onward is ASPSI/DOH's to run: SJREB ethics clearance, tablet supply, and scheduling the pretest itself. Carl stays ready and waits for the pretest date; he tracks none of those external gates as his own.**

- **F1 / F3 / F4 (CSPro CAPI)** — multi-language instruments built (generator-driven); **on-device build + UAT Round 5 in active bug-burndown**; pretest-readiness + go/no-go assessed (2026-06-27). The **Supervisor hub** (one login → role menu → Bluetooth assignment/collection between tablets → CSWeb relay → live coverage reports → offline EA map) is **built, deployed, and device-verified on two tablets**, with a **live training guide** at `csweb.asiansocial.org/docs/hub-guide.html`. CSWeb 8.0.1 + the sync / map / case-status dashboards are **live**.
- **F2 (HCW PWA)** — **production v2.1.0**, all 7 PSA-target languages, UAT Rounds 1–3 closed. The one open item is migrating it off Cloudflare/Google to a dedicated Elestio instance (planned; provisioning-gated).
- **Net for a Product Owner:** almost everything *buildable* is built. Carl's remaining lane = close the F1/F3/F4 UAT and finish the support deliverables (data pipeline, training/manuals, governance). The **pretest is ASPSI-scheduled** (SJREB + tablets + logistics, all ASPSI/DOH) — Carl waits for the date, then the deliverable chain (D4 → D5 → D6) resumes to engagement close.

### Where We're Going — Roadmap to Close (Aug 2026)

End-to-end critical path:

> **Build ✅ → Field-ready (Carl — nearly done) → ⟦ASPSI: SJREB + schedule pretest⟧ → Pretest → D4 pilot report (Jul 13) → Training / D5 (Jul 31) → Fieldwork → Data cleaning + analysis → D6 final (Aug 13) → Handover & close**
>
> _Carl's responsibility ends at the first arrow's target (field-ready). The bracketed step is ASPSI's; Carl waits for the pretest date, then re-engages on D4._

| Milestone | Due | What it needs | Status |
|---|---|---|---|
| **D2 / D3** — survey materials, manuals, training, pre-tested questionnaires | extended | F1/F3/F4 UAT burndown (Carl, active) · pretest (ASPSI-scheduled) · Kidd's manual review | 🟡 In progress |
| **Pretest** (Epic 6) | ASPSI-scheduled | field-ready instruments (Carl, nearly done) · SJREB clearance + date (ASPSI) | 🟠 Awaiting ASPSI schedule |
| **D4** — pilot progress + initial data report | 2026-07-13 | Pretest → enumerator debrief → report | ⚪ Not started |
| **D5** — training documentation | 2026-07-31 | Training decks + manuals (drafted) + delivery + pre/post assessment | 🟡 Drafted, not final |
| **D6** — final report + dissemination | 2026-08-13 | Fieldwork → data cleaning (Epic 10) → analysis/tabulation (Epic 11) | ⚪ Not started |
| **Handover & close** (Epic 12) | end Aug | Handover package + NDU disposition + retro writeback | ⚪ Not started |

**The handoff — Carl's lane ends at field-ready; the rest is ASPSI/DOH's:**
- **Carl:** get F1/F3/F4 field-ready (UAT burndown) + finish the support deliverables (data pipeline, training, governance). No external unblock needed.
- **ASPSI/DOH:** SJREB ethics clearance · tablet supply · scheduling + running the pretest.

_Neither SJREB nor tablets is a Carl-tracked blocker — both are ASPSI's. The one thing Carl is waiting on is the **pretest schedule**; everything else on his side is in hand._

**What's left, simplified into buckets (most of Carl's lane needs no external unblock):**

| # | Bucket | What's left | Owner / gate |
|---|---|---|---|
| 1 | **F1/F3/F4 field-readiness** (Epic 3/6) | finish CSEntry build + UAT R5 bug-burndown | Carl — active |
| 2 | **PhilHealth reinstatement** (F3/F4) | Q38.1/Q38.2 + Q45.1/Q45.2 — **wordings+routing captured 2026-06-28**; only the value-set option lists remain | Carl saves the 3 PNGs from Kidd's Jun 9 email, then ~3h build |
| 3 | **Data pipeline** (Epic 10/11) | harmonization ETL + codebook + interim tabulation (for D4/D6) | Carl — buildable now |
| 4 | **Training & manuals** (Epic 7) | finalize decks + Survey Manual + enumerator-guide screenshots | Carl + Kidd review |
| 5 | **Security & governance** (Epic 9) | privacy policy, backup/retention, audit trail | Carl — staged |
| 6 | **F2 → Elestio** (Epic 4) | migrate Survey + Admin off Cloudflare | planned — provisioning-gated |
| 7 | **Pretest → fieldwork** (Epic 5/6) | the pretest itself | **ASPSI-owned** — SJREB + tablets + scheduling; Carl waits for the date |
| 8 | **Handover** (Epic 12) | package + knowledge transfer + NDU disposition | at close |

> Day-to-day work lives in `sprint-current.md`; full sprint-by-sprint history in `scrum/sprints/` + `log.md`.

> _Sprint-by-sprint history (Apr–Jun 2026) has been moved out of this top view (2026-06-28) to keep the Product Owner view forward-looking. The full record lives in `scrum/sprints/` and `log.md`._

### By Workstream Epic

| # | Epic | Current State | Next Milestone |
|---|---|---|---|
| **0** | CAPI Project Management & Stakeholder Engagement | **Active / Ongoing** — **Sprint 011 closed 2026-06-28** (retro filled; archived to `sprints/sprint-011.md`); **Sprint 012 skeleton** (Jun 29–Jul 3, locks Mon); daily-standup automation live | Lock S012 Mon; **Day-1 build-or-kill the carries** — E0-SCRUM-SYNC (3× committed / 0× built), PSA confirm (4th carry), Goal B; operationalize the field-readiness exit criterion |
| **1** | Inception & Engagement Setup | **Done** | — (historical, closed Dec 2025) |
| **2** | Survey Questionnaire Design & Dictionary | **Done (design)** — F1/F3/F4 Build-ready, multi-language; 12-digit case-key migration in; F2 data model in the PWA spec; PLF Source Captured | PLF DCF build (E2-PLF-004/005/006) when slotted |
| **3** | CAPI Application Development | **In Progress** — **F2 PWA in production v2.1.0, 7 languages** (UAT R1–R3 closed). **F1/F3/F4 multi-language BUILT + deployed to CSWeb**; **on-device build + UAT Round 5 in active bug-burndown** | **Close the F1/F3/F4 UAT → field-ready** (E3-F1/F3/F4 + E6-CAPI-FIELDREADY) |
| **4** | Backend & Sync Infrastructure (CSWeb for CAPI; Cloudflare/Apps Script for PWA) | **In Progress** — PWA backend live; **CSWeb 8.0.1 LIVE on Elestio** + sync/map/case-status dashboards; **Supervisor hub deployed** to CSWeb | F2 Survey+Admin migration to a dedicated **Elestio** instance (provisioning-gated); CSWeb backup strategy |
| **5** | Field Distribution & Device Management | **In Progress** — CAPI tablet + PWA field-ops SOPs drafted; F2 distribution proven | Tablet supply is ASPSI/DOH logistics (not Carl's gate); Carl's lane = the provisioning SOP, ready when devices land |
| **6** | Testing and Pilot | **In Progress** — PWA UAT R1–R3 closed; **CAPI UAT Round 5 active** (F1/F3/F4 on-device burndown); pretest-readiness assessed 2026-06-27 | Close UAT R5; **pretest blocked on SJREB clearance** (ASPSI/PI lane) |
| **7** | Training and Documentation | **In Progress** — Survey Manual + enumerator/STL/HCW decks + CSEntry field guide drafted; **Supervisor-hub training guide LIVE** | Finalize for D5; fill enumerator-guide screenshots; Kidd's review on the Survey Manual |
| **8** | Fieldwork Monitoring and Quality Control | **In Progress** — **Supervisor hub Phase-1 (QA review) + Phase-2 (login→menu→Bluetooth→relay→reports→map) BUILT + device-verified on 2 tablets + training guide LIVE**; CSWeb dashboards live | Wire the hub into the field SOP at fieldwork start; confirm the QA-supervisor roster (ASPSI) for the `supervisor-qa` role |
| **9** | Data Management and Security | **Governance Active** — Data-Privacy-and-Security-Plan drafted | Finalize privacy policy + secure-sync + backup/retention for both tracks |
| **10** | Data Cleaning and Processing | **Not Started** — shared codebook + harmonization ETL spec drafted (skeleton live) | Per-instrument batch-edit specs once data flows |
| **11** | Analysis Support & Deliverables | **Not Started** | Interim tabulation template ahead of D4; CSV + Stata export pipeline |
| **12** | Handover, Closeout & Retrospective | **Not Started** | NDU-compliant file disposition plan |

### By Survey Instrument

| Instrument | Mode | Pages | Current State |
|---|---|---|---|
| **F1 — Facility Head** | Interviewer-administered (CSPro CAPI) | 34 | **Multi-language built (EN + Cebuano/Bisaya/Hiligaynon/Waray/Bicolano).** DCF 12 records, 12-digit case key; preflight + parity GREEN (2026-06-07). **deployed to CSWeb; on-device build + UAT Round 5 in burndown** (E3-F1-001). fil/ilo English-fallback (ASPSI gap). |
| **F2 — Healthcare Worker** | **Self-admin — PWA (primary). Google Forms + CSPro-encoder fallbacks retired 2026-04-17. CSPro F2 track: least priority — do not reopen.** | 14 | **Production live at v2.1.0 — all 7 PSA-target languages** (PSA F2-share met 2026-06-02). UAT Rounds 1–3 closed. PWA at `deliverables/F2/PWA/app/`; prod https://f2-pwa.pages.dev. Residual: app-chrome translation for ilo/hil/war/bcl; `clasp`/#294 deploy-gap (S009 Goal B). |
| **F3 — Patient** | Interviewer-administered (CSPro CAPI) | 23 | **Multi-language built (EN + Cebuano/Bisaya/Waray/Bicolano).** 18 records, 12-digit case key; preflight + parity GREEN. **deployed to CSWeb; on-device build + UAT Round 5 in burndown** (E3-F3-001 / #251). hil/fil/ilo English-fallback (ASPSI gap). |
| **F4 — Household** | Interviewer-administered (roster-heavy, new for Year 2; CSPro CAPI) | 26 | **Multi-language built (EN + Cebuano/Bisaya/Waray/Bicolano).** 22 records (`C_HOUSEHOLD_ROSTER` repeating), 12-digit case key; preflight + parity GREEN. **deployed to CSWeb; on-device build + UAT Round 5 in burndown** (E3-F4-001 / #253). hil/fil/ilo English-fallback (ASPSI gap). |
| **PLF — Patient Listing Form** | Recruitment form | 1 | Source Captured (Designer-validate + publish deferred — out of the current instrument-dev goal) |

---

## 2. Scope at a Glance

What is being built, in numbers:

| Dimension | Count |
|---|---|
| Survey instruments under development | **4** (F1, F2, F3, F4) + 1 recruitment form (PLF) |
| Total questionnaire content | **~98 pages** across all instruments |
| Data entry modes supported | **2** — interviewer-administered and self-administered |
| Languages supported | **F2 PWA: 7** (Tagalog + Cebuano/Bisaya/Hiligaynon/Waray/Ilocano/Bicolano — production). **F1/F3/F4: EN + Cebuano/Bisaya/Hiligaynon/Waray/Bicolano built**; fil/ilo English-fallback (ASPSI translation gap) |
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

> ⚠️ **Note (2026-06-28):** the per-epic narratives in §4 are **detailed reference and lag the current state** — several still carry Apr–Jun phrasing (e.g. "F2 at v1.1.1", "Epic 6/7 Not Started", "Supervisor App Phase 2 deferred"). **§1 (Headline + Roadmap + the By-Workstream-Epic / By-Instrument tables) is authoritative.** Current reality: F2 is **prod v2.1.0 / 7-language**; F1/F3/F4 are **built, deployed to CSWeb, in UAT Round 5 burndown**; the **Supervisor hub (Phase-1 + Phase-2) is built + device-verified + has a live training guide**; CSWeb 8.0.1 + dashboards are **live**. A full §4 prose refresh is pending; read §1 for status.

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

**In flight (Data Programmer scope):**
- Product Backlog maintenance (this document)
- Defining the internal weekly status format (E0-010) — Carl-controlled internal tracking, *not* a recurring send to ASPSI Mgmt or DOH (per `feedback_weekly_status_internal_only.md`)
- Sprint cadence + scrum artifact upkeep (Sprint 003 closing 2026-05-01)

**ASPSI / PI / PMO lane — informational only (NOT Data Programmer scope per CSA D1–D6):**
- SJREB ethics clearance coordination (E0-020) — owned by ASPSI ops / PI; long-pole dependency for Epic 6 pretest
- D2 / D3 / Tranche 2 timeline + deadline tracking (E0-032) — owned by ASPSI ops / PI / PMO; Carl produces the deliverables, ASPSI manages submission timing
- DOH-PMSMD matrix feedback coordination (E0-032a) — owned by ASPSI ops / PI; CAPI-side revisions fold into the relevant E2/E3 instrument task

**Next milestone:** Internal weekly status format defined (E0-010), used for Carl's tracking and the project record.

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

**Current state (2026-06-28):** **Done (design).** F1/F3/F4 all Build-ready with multi-language dictionaries built; E2-F1-010 Designer sign-off closed 2026-05-04; F2 data model frozen in the PWA spec; PLF Source Captured (DCF build pending — E2-PLF-004/005/006). _(Older Apr detail below retained for reference.)_

**Per-instrument status:**

| Instrument | State | Notes |
|---|---|---|
| F1 | **Build-ready 2026-05-04** | DCF at 12 records / 671 items after Apr 21 GPS+photo+PSGC-cascade pass. All 166 questions walked for skip logic; spec aligned with F3/F4 architecture. Four-tier validation rules documented. The 6 schema items frozen as `PENDING_DESIGN_*` defaults; **E2-F1-009b closed 2026-04-17**. PSGC value sets still blocked on ASPSI. **E2-F1-010 Designer sign-off DONE 2026-05-04** — bug list clean, no deferrals. Unblocks E3-F1-001 (F1 FMF Designer pass). |
| F2 | **Data model captured inside the PWA spec** | Data model + skip graph + validation live in `deliverables/F2/PWA/app/spec/F2-Spec.md` (114 items / 35 sections) rather than a CSPro dictionary. The earlier Apr 15 F2-0 tooling memo, cover-block rewrite, Spec.md, Skip-Logic, Validation, Cross-Field, and Apps Script bundle were the inputs that fed the PWA build. Cover-block rewrite still pending ASPSI review. |
| F3 | **Design — Build-ready 2026-04-21** | 18 records / 840 items, sections A–L. Shared `cspro_helpers.py`. Skip-logic + validation spec at `deliverables/CSPro/F3/F3-Skip-Logic-and-Validations.md` (reviewed 2026-04-21). 1 question to Juvy (Q31 IP_GROUP); 5 spec-decisions closed. |
| F4 | **Design — Build-ready 2026-04-21** | 22 records / 623 items, sections A–Q. `C_HOUSEHOLD_ROSTER` repeating (`max_occurs=20`, id-item `MEMBER_LINE_NO`); `H_PHILHEALTH_REG` and `J_HEALTH_SEEKING` respondent-level non-repeating per Apr 20 source rephrase. Flat expenditure batteries in Section N. Skip-logic + validation spec at `deliverables/CSPro/F4/F4-Skip-Logic-and-Validations.md` (draft 2026-04-21). Findings #1 and #2 in §1.A closed-by-verification 2026-04-21. |
| PLF | Source Captured | Implementation decision (CAPI vs paper) precedes design. |

**What's done across the epic:** All five source questionnaires ingested and catalogued. F1 generator + DCF built + cleaned (12/664 post Apr 21 GPS/photo pass). F3 generator + DCF built (18/835); skip-logic + validation spec complete 2026-04-21. F4 generator + DCF built (22/618); skip-logic + validation spec complete 2026-04-21 with 2 P1 schema gaps flagged. Shared `cspro_helpers.py` + `Capture-Helpers.apc` + `PSGC-Cascade.apc` extracted. F2 data model + skip graph + validation captured in the PWA spec.

**In flight:** ~~F1 Designer round 2 / sign-off (E2-F1-010) — the carry-forward miss from Sprint 001.~~ **CLOSED 2026-05-04 (Sprint 004 Day 1).** F2 cover-block rewrite still with ASPSI. F3/F4 Designer validation queued as Sprint 004 stretch.

**Next milestone:** **E3-F1-001 (F1 FMF Designer pass — UNBLOCKED Day 1 of Sprint 004)**; F3 Designer validation + sign-off (E2-F3-010); F4 Designer validation + sign-off (E2-F4-010).

**Ties to:** D2, D3.

---

### Epic 3 — CAPI Application Development (CSPro + CSEntry / PWA)

**Covers:** Application build per instrument. F1/F3/F4 are CSPro Designer / CSEntry CAPI applications — form layout, tablet UX, capture types, question text (English + Filipino), skip logic wiring, validation wiring, dynamic value sets, multi-language handling, FIELD_CONTROL block (informed consent, eligibility, AAPOR disposition codes, GPS, photo, interviewer/supervisor IDs, timestamps), and roster engines (F4). F2 is a Progressive Web App — Vite+React+TS installable shell with IndexedDB autosave, skip-logic nav, Apps Script sync backend.

**Current state (2026-06-28):** **In Progress.** F2 PWA in **production v2.1.0** (7 languages; UAT R1–R3 closed). F1/F3/F4 **multi-language built, deployed to CSWeb, in UAT Round 5 on-device burndown**; the Supervisor hub is built + device-verified. _(Older detail below from Apr–May retained for reference.)_

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
4. UAT Rounds 1 + 2 (closed 2026-04-25) — Shan as tester, GitHub Issues + Slack `#f2-pwa-uat`, 13 issues fixed; production tagged v1.1.1
5. Round 3 (v1.2.0) backlog queued — #16 exclusive multi-select, #17 all-of-the-above auto-select, #18 matrix view for scale-style questions
6. Deferred M11 items (slot in only if production feedback demands): per-HCW tokens, draft auto-migration across spec versions, iOS push, admin mutations

**F2 PWA note:** The Apr 15 Google Forms / paper / deferred-CSPro three-path model is superseded by the PWA primary build. The PWA is the only active F2 build path. **The CSPro-encoder track for F2 is the least priority item in this engagement** — do not reopen without an explicit decision reversal driven by a deployment-context change. If ASPSI's deployment context ever shifts back, prior artifacts remain under `deliverables/F2/` as fallback starting points only.

**F2 QA/UAT note (2026-04-25):** 3/3 Playwright E2E tests pass (golden path enrollment → 10 sections → review → submit; section lock; language switch). Auto-advance and section-lock UX shipped. UAT Rounds 1 + 2 closed 2026-04-25 — 13 issues fixed across the two rounds (skip-logic, validation, navigation regression, specialty filter, real-time tooltips, language switcher visibility, submit error UX, etc.). Production at https://f2-pwa.pages.dev (v1.1.1 · spec 2026-04-17-m1). Round 3 v1.2.0 enhancements queued: #16 exclusive multi-select, #17 all-of-the-above auto-select, #18 matrix view.

**Ties to:** D2, D3.

---

### Epic 4 — Backend & Sync Infrastructure

**Covers:** Per-track backend provisioning, sync architecture, authentication and access control, server-side storage and retention. The two tracks run independent infrastructure, integrated only at the data-export step (see [Section 5: Cross-Track Integration](#5-cross-track-integration)).

#### 4.A — CAPI track (F1, F3, F4)

- **Sync architecture decision** — CSWeb vs Dropbox vs FTP vs Bluetooth, with trade-off documentation. CSWeb is the recommended default for real-time monitoring.
- **CSWeb server provisioning** — host (cloud / on-prem), TLS, authentication, dictionary deployment per instrument, round-trip sync testing.
- **Server-side storage** — `.dat` retention, dictionary versioning, cross-version migration plan.

#### 4.B — PWA track (F2)

- **Backend** — Google Apps Script Web App (`AKfycb...zETS9D9fQ7ovD`), HMAC-signed batch submit endpoint, idempotency keys, response-sheet write target. Health-check endpoint for monitoring.
- **Hosting** — Cloudflare Pages with two projects: `f2-pwa-staging` (branch `staging`) and `f2-pwa` (branch `main`, production at https://f2-pwa.pages.dev).
- **Service worker / PWA manifest** — vite-plugin-pwa, `skipWaiting` + `clientsClaim` upgrade flow, precache for shell, runtime cache for `/config` and facility list.
- **Runtime config** — `kill_switch`, `broadcast_message`, `min_accepted_spec_version` editable from the Apps Script Config sheet without redeploy.

**Current state (2026-06-28):** PWA backend live (prod Worker + Apps Script; Admin Portal v2.0.0). **CSWeb 8.0.1 (4.A) is LIVE on Elestio** (`csweb.asiansocial.org`) — dictionaries uploaded, sync proven, sync/map/case-status dashboards + the Supervisor hub deployed. Next: migrate F2 to a dedicated Elestio instance (provisioning-gated). _(Older detail below retained for reference.)_

**Next milestone:** CSWeb provisioned for CAPI track + integration ETL spec drafted (lands in Epic 10) so both tracks export to the same downstream format.

**Dependencies:** CSWeb provisioning blocks F1/F3/F4 fieldwork. PWA backend already in production.

**Ties to:** D3, TOR Duty 7 (configure web server for uploading completed questionnaires).

---

### Epic 5 — Field Distribution & Device Management

**Covers:** Per-track field model — how the instrument reaches respondents and how completed cases reach the backend. The two tracks have fundamentally different distribution models: CAPI is push-to-tablet via enumerator; PWA is pull-by-respondent via URL.

#### 5.A — CAPI track (F1, F3, F4)

- **Tablet provisioning SOP** — CSEntry installation, app/PFF deployment, sync credential management, role-specific bundles (interviewer vs supervisor).
- **Backup & recovery** — what happens when a tablet dies mid-interview (local-cache survival + sync replay).
- **Spare device strategy** — N+10% spare ratio for field; hot-swap procedure.
- **Field rollout logistics** — provisioning timeline aligned to enumerator training; check-in / check-out procedures; lost-device protocol.

#### 5.B — PWA track (F2)

- **Distribution-list SOP** — facility-level HCW lists assembled (sourced from F1's HCW roster + ASPSI manual augmentation), URL distributed via the channels HCWs already use (email, organisation portal, Slack), per-facility tracking sheet.
- **Onboarding aid** — one-page "how to fill the form on your device" + in-app help; PWA install prompt surfaces automatically; documented install flow per platform (iOS / Android / Desktop).
- **Reminder ops** — Day 3 / Day 7 nudge protocol for non-completers (email + Slack); response-rate monitoring per facility.
- **Backup & recovery** — IndexedDB persists drafts across navigations and offline; backend retains all `pending_sync` rows until acknowledgement; service worker auto-updates on next session.
- **Distribution rights** — no per-HCW token currently (any HCW ID once facility selected); upgrade path documented as M11 deferred work.

**Current state:** PWA distribution model proven via UAT Rounds 1+2 (Shan as tester, structured Slack + GitHub Issues coordination). CAPI tablet specification drafted 2026-04-29 (E5-CAPI-001 in-progress; awaiting procurement confirmation from ASPSI ops); imaging SOP still ahead.

**Next milestone:** Tablet provisioning SOP drafted (Epic 5.A); F2 distribution-list SOP formalised for production fieldwork (Epic 5.B — currently lives in `#f2-pwa-uat` channel conventions, needs documenting as a runbook).

**Dependencies:** 5.A requires Epic 3 (CSPro build) + Epic 4.A (CSWeb sync architecture). 5.B is unblocked but blocked on getting facility-level HCW lists from ASPSI / DOH for production rollout.

**Ties to:** D3.

---

### Epic 6 — Testing and Pilot

**Covers:** Per-instrument desk test (walk every skip path manually), bench test with mock cases (youngest/oldest eligible, refusal at each gate, "None of the above" on every multi-select, every Other-specify, maximum roster size, every dynamic branch, every validation rule triggered), pair test with domain expert for interpretation drift, regression test after every schema change, archived test cases for replay, pretest with 10–30 real respondents per instrument, enumerator debrief, iteration cycles.

**Current state (2026-06-28):** **In Progress.** F2 PWA tested (Vitest + Playwright; UAT R1–R3 closed). F1/F3/F4 desk-tested + in **UAT Round 5** on-device bug-burndown; pretest-readiness assessed 2026-06-27. The respondent pretest is **blocked on SJREB clearance** (E0-020, ASPSI/PI lane). _(Older detail below retained for reference.)_

**Per-instrument status:** F2 tested + in production; F1/F3/F4 in UAT Round 5 burndown.

**Roles:**
- **Carl (Data Programmer)** — author of test specs, owner of desk and bench tests against the build, owner of regression artifacts.
- **Shan (QA Tester, ASPSI RA)** — independent QA pass on each instrument's CAPI build. Receives handoff bundles from Carl with the build, test scripts, known-issue list, and walkthrough notes. Surfaces defects ahead of the SJREB protocol freeze and the formal pretest with respondents.

**Next milestone:** F1 desk test, once F1 build is underway. QA handoff workflow to Shan defined ahead of first F1 build slice ready for review.

**Critical dependency:** Pretest with real respondents requires SJREB clearance (tracked in Epic 0).

**Ties to:** D3 (pre-tested questionnaires).

---

### Epic 7 — Training and Documentation

**Covers:** Survey manual (interviewer guide), field operations manual, enumerator training materials (CSEntry walkthrough, common pitfalls, sync procedure, disposition coding, consent administration), training delivery logistics, pre- and post-training assessment instruments, user manuals for supervisors, contributions to the Inception Report's field protocol documentation.

**Current state (2026-06-28):** **In Progress.** Survey Manual CSPro section + enumerator/STL/HCW training decks + CSEntry enumerator field guide drafted; the **Supervisor-hub training guide is LIVE** at `csweb.asiansocial.org/docs/hub-guide.html`. Pending Kidd's (RA) review + D5 finalization.

**Next milestone:** Finalize training materials for D5; fill enumerator-guide screenshots; Kidd's Survey-Manual review.

**Ties to:** D2 (survey manual, SOPs), D3 (field operations manual, training materials), D5 (training documentation with pre/post assessment).

---

### Epic 8 — Fieldwork Monitoring and Quality Control

**Covers:** Real-time monitoring across both tracks, hot-fix protocol per track, unified issue log with triage and resolution, field-reported anomaly tracking, weekly client progress updates during main collection.

**Architecture decision (2026-04-25):** Don't force F2 PWA into CSWeb. Instead, build a **thin BI layer above both backends** so ops + DOH see one dashboard while each system stays in its native shape.

- **Cross-track BI dashboard** — Looker Studio (or Metabase / Sheets) connects to:
  - **CAPI side:** CSWeb's PostgreSQL (or its periodic CSV export)
  - **PWA side:** F2's response sheet / Apps Script-managed DB
  - Surfaces side-by-side: response counts by region, completion rates, sync lag, disposition breakdowns, daily case counts.
- **Per-track ops dashboards** continue to exist where useful — CSWeb dashboard for CAPI sync health, F2 admin URL for PWA submission queue — but the BI dashboard is the single stakeholder-facing view.
- **Hot-fix protocol** — CAPI: new PFF push to tablets; PWA: deploy to staging → verify → merge to main → service-worker auto-updates next session.
- **Slack-bot automation** (already live for F2) — issue events + daily 09:00 MNL digest + milestone-closed release notes auto-post to `#f2-pwa-uat`. Pattern replicable for CAPI rounds when fieldwork starts.
- **Issue log** — single GitHub Issues backlog spans both tracks, distinguished by `track:capi` / `track:pwa` labels (or per-instrument labels).

**Current state (2026-06-28):** **In Progress (pre-fieldwork tooling).** PWA monitoring automation live; **Supervisor hub Phase-1 (QA review) + Phase-2 (login → menu → Bluetooth → CSWeb relay → live reports → offline map) BUILT + device-verified on 2 tablets + training guide LIVE**; CSWeb sync/map/case-status dashboards live. Full field activation waits on fieldwork kickoff.

**What's realized (2026-06-21):**
- **E8-SUPERVISOR-001 — Supervisor App Phase 1 (Review Layer): BUILT + tested.** A read-only field-QA report tool (`deliverables/CSWeb/supervisor-app/`, stdlib Python, 14/14 `pytest`) over pulled F1/F3/F4 cases → one **PII-light** HTML report with coverage-vs-plan, partials + disposition (#561), and a 5-rule data-quality flag worklist (no GPS / no photo-on-completed / stuck-partial / disposition-mismatch / consent-contradiction). Spec `docs/superpowers/specs/2026-06-20-supervisor-app-design.md`; plan `docs/superpowers/plans/2026-06-21-supervisor-app-phase1.md`. **Backbone = the Cluster-5 `CASE_DISPOSITION` sentinel** (Epic 3, #515/#561). **C1 CSWeb access RESOLVED:** the report's GET runs on **dictionary-sync, not the web `data` dashboard**, so a scoped **`supervisor-qa`** role (`report` + F1/F3/F4 dictionary sync) holds it; `supervisor-monitor` stays report-only/no-sync (RBAC pack §2 — now 6 roles). Remaining ASPSI input: the QA-supervisor names.
- **E8-SUPERVISOR-002 — Supervisor hub Phase 2 (Bluetooth sync hub): BUILT + deployed + device-verified (2026-06-28).** One login → role menu (supervisor / enumerator) → launch the unmodified F1/F3/F4 instruments; exchange EA assignments + finished interviews between tablets over **Bluetooth** (`syncserver`/`syncconnect`/`syncdata` in logic — corrects the earlier #131 read); **relay collected cases to CSWeb** from the supervisor; live **coverage reports**; **offline EA map**. Device-verified end-to-end on two tablets (itel + Samsung A23); **training guide LIVE** at `csweb.asiansocial.org/docs/hub-guide.html`. Generator-only build (`deliverables/CSPro/supervisor-hub/build_hub_apps.py`); dual-path keeps direct-to-CSWeb the default (conflict-free upsert-by-12-digit-key).
- **E8-BI-001 — CSWeb reporting views + static sync dashboard: LIVE.** A standalone `csweb_reports` DB of 12 SQL views over the F1/F3/F4 breakout DBs (`deliverables/CSWeb/gen-report-views.py`) + a static, filterable Chart.js dashboard (`deliverables/CSWeb/csweb-dashboard-gen.py`) at **`csweb.asiansocial.org/docs/dashboard.html`** — Instrument/Region/Status/visit-date filters, a Case-Status (Completed/Partial) doughnut per instrument, Chart.js vendored locally, 15-min refresh cron on the box. **Note (vs §5.4):** the §5.4 plan named Looker Studio; the realized build is a **static dashboard** (chosen for the box's ~1.7 GB RAM headroom — co-hosting Metabase/JVM risked OOM against live CSWeb). The `csweb_reports` views remain available for direct SQL/BI.

**Next milestone:** Wire the Supervisor App into the field SOP at fieldwork start; confirm the QA-supervisor roster (ASPSI) to provision the `supervisor-qa` role; (when instruments stabilize) run the Phase-2 spike gates.

**Ties to:** TOR Duty 8 (prepare survey data dashboard), TOR Duty 9 (technical support during CAPI survey), D4 (progress report on piloting), [Section 5: Cross-Track Integration](#5-cross-track-integration).

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

**Covers:** Per-instrument batch editing pipeline, **plus the cross-track harmonization step that produces clean unified analysis-ready output.** Both halves matter; the harmonization is what makes the data actually usable across instruments without per-analysis re-work.

#### 10.A — Per-instrument batch editing

- **CAPI track:** CSBatch scripts (structure / validity / consistency / imputation), edit specifications document, hot-deck imputation strategy where appropriate, data quality reporting per instrument.
- **PWA track:** F2 already enforces structural validity at submit time via Zod schema + `superRefine`, so the post-collection batch step is lighter — primarily consistency checks and imputation for missing optional fields. Same edit-specs document discipline applies.

#### 10.B — Cross-track harmonization layer

The **harmonization ETL** is the bridge between raw export and clean analysis-ready dataset. It runs after each batch edit pass and produces both CSV (codebook-driven) and Stata (with labeled values) outputs per instrument, plus a **shared-dimensions table** for cross-instrument joins. See [Section 5: Cross-Track Integration](#5-cross-track-integration) for the data alignment risks and the canonical codebook.

The ETL handles:
- **Naming normalization** — every column follows `<instrument>_<questionId>` (e.g. `f1_q12`, `f2_q12`) so the same Q-number across instruments doesn't collide downstream.
- **Yes / No / DK normalization** — CSPro stores 1/2/8 or Y/N; PWA stores literal `'Yes'`/`'No'`/`'I don't know'`. ETL maps both to a canonical `1`/`2`/`8` with consistent labels.
- **Sex / role / facility-type recoding** — single codebook drives the canonical labels; per-instrument value mismatches caught at ETL time.
- **PSGC alignment** — every instrument carries `region`, `province`, `city_mun`, `barangay` codes from the same PSGC value-set source; ETL validates conformance.
- **Date format normalization** — CSPro YYYYMMDD → ISO 8601; PWA already ISO; output uniform.
- **Missing-vs-skip semantics** — CSPro `NOTAPPL` / `REFUSED` / `DK` and PWA `undefined` (hidden by skip-logic) → unified Stata extended-missing codes (`.a` skipped, `.b` refused, `.c` don't know, `.` truly missing).
- **`_source_instrument` column** added to every row so cross-instrument concatenation is traceable.

**Current state:** Not Started.

**Next milestone:** Shared codebook + harmonization ETL spec drafted alongside instrument design — see [Section 5: Cross-Track Integration](#5-cross-track-integration). Spec captures every shared dimension, every per-instrument coding decision, every recode rule.

**Ties to:** D4 (initial data collection report), D6 (edit specifications in final documentation), Epic 11 (consumer of the harmonized output).

---

### Epic 11 — Analysis Support & Deliverables

**Covers:** Interim tabulation (cross-tabs) for client progress reports, final dataset exports, codebook, edit specifications document, contributions to the final report, policy brief support, dissemination workshop documentation.

**Output formats** (confirmed 2026-04-25): **CSV + Stata (`.dta` with labeled values)** are the primary delivery formats per instrument. CSPro `.dat` retained for archival of raw CAPI track data. Each output corresponds to one instrument; cross-instrument joins happen in the analysis step using the shared keys defined in [Section 5: Cross-Track Integration](#5-cross-track-integration).

Per-instrument deliverables:
- **F1 / F3 / F4** — raw `.dat` (archive) + post-CSBatch `.dat` + harmonized CSV + Stata `.dta`
- **F2** — raw response sheet (JSON / sheet rows; archive) + harmonized CSV + Stata `.dta`
- **Codebook** — single document covers all four instruments; explicitly names the shared-dimension columns with canonical codes; per-instrument variables follow.
- **Edit specifications** — per-instrument document, plus a cross-track harmonization rules document (the ETL spec from Epic 10.B).

**Current state:** Not Started

**Next milestone:** Interim tabulation template prepared ahead of D4.

**Ties to:** D4 (progress report with piloting results), D6 (final report, policy briefs, dissemination), Epic 10.B (harmonization layer is the data source).

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

## 5. Cross-Track Integration

The engagement runs two delivery modes side-by-side: **CAPI** (F1/F3/F4 on CSPro) and **self-admin Web** (F2 on PWA). Each is operationally independent — they deliberately do **not** share infrastructure at runtime. They converge at three coordination points: data export, field operations status reporting, and stakeholder dashboard.

### 5.1 Data field alignment — what aligns and what doesn't

**Honest baseline:** the four instruments have different units of analysis (facility / HCW / patient / household). Most fields are instrument-specific and shouldn't be force-aligned. Cross-instrument value comes from the small set of **shared dimensions** that *do* need to align so joins and stratified analysis are clean.

The risks come from fields that *look* the same across instruments but encode differently — silent merge failures rather than loud schema errors.

#### Shared dimensions (must align across all four instruments)

| Dimension | Why it's shared | Risk if it doesn't align |
|---|---|---|
| `region`, `province`, `city_mun`, `barangay` (PSGC codes) | Geographic stratification; every instrument has it | Two instruments using different PSGC vintages → join failures and wrong region rollups |
| `facility_id`, `facility_type`, `facility_name` | F1's facility is F2's HCW employer is F3's sampling point is F4's PSU linkage | Different facility-id schemes between F1 and F2 → can't link HCWs to facility characteristics |
| `sex` | All four instruments collect this | F1 uses 1/2 (CSPro); F2 PWA stores `'Male'`/`'Female'` strings — same meaning, different shape |
| `age` (or `age_group`) | All four | Number vs binned categorical; missing-vs-DK |
| `role` (HCW only — F1 head + F2 worker) | F1 captures facility head's role; F2 captures HCW's role | Different choice lists; F1 might say "Physician" where F2 says "Physician/Doctor" |
| `philhealth_status` (F1 head, F2 HCW, F3 patient, F4 HH member) | All four ask | Different categorical encodings per instrument |
| `informed_consent` (Y/N + timestamp + interviewer/respondent ID) | Required by ethics; format varies by mode | CAPI captures in FIELD_CONTROL block; PWA records implicitly via submission; need a uniform consent-capture column |
| `survey_date` / `submission_date` | All four | Format consistency (CSPro YYYYMMDD numeric vs PWA ISO 8601) |
| `interviewer_id` (CAPI) / `respondent_self_id` (PWA) | Source attribution | Different field names, similar semantics |
| `disposition_code` | Response status | CAPI uses AAPOR codes; PWA uses simpler `submitted` / `partial` / `abandoned` — needs a mapping |
| `language` (en / fil / others) | Both modes | OK if both capture explicitly; pin from i18n state in PWA, from `setlanguage()` in CSPro |

#### Instrument-specific (do NOT need to align)

The remaining ~95% of each questionnaire — facility staffing tables, HCW satisfaction Likert batteries, patient experience ratings, household roster economics — is meant to stay instrument-specific. Don't try to merge these into a single wide row; analysis joins on the shared keys above and treats the per-instrument fields separately.

### 5.2 Harmonization ETL — where the alignment happens

A small Python (or R) ETL step runs after each batch-edit pass per instrument and produces:

1. **One harmonized CSV per instrument** — columns prefixed `<instrument>_<questionId>` (e.g. `f1_q12`); shared dimensions canonicalized; missing-vs-skip semantics resolved into Stata extended-missing codes.
2. **One Stata `.dta` per instrument** — same data with labeled values, variable labels, value labels per the codebook.
3. **One `shared_dimensions.csv`** — long-format table with one row per (instrument, respondent, dimension) — the join layer for cross-instrument analysis.

Owner of the harmonization step lives in **Epic 10.B**; consumer is **Epic 11**. The ETL spec is the artefact you write before fieldwork starts; the actual implementation runs after data lands.

### 5.3 Field operations coordination — two ops, one status report

The two tracks run independent ops:

- **CAPI track:** ASPSI enumerator coordinator owns assignment per facility/cluster, daily progress via CSWeb dashboard, supervisor sign-off per case.
- **PWA track:** ASPSI ops lead owns URL distribution to facility-level HCW lists, Day 3 / Day 7 reminder protocol for non-completers, response-rate tracking via the F2 backend.

Both feed **one rolled-up daily status report** to ASPSI Mgmt Committee that shows progress on both tracks side-by-side (e.g. "F1: 18/120 facilities complete; F2: 245/600 HCWs responded; F3/F4: not yet open"). The report is a thin daily summary, not a duplicate of either ops team's working dashboard.

### 5.4 Dashboard architecture — BI layer over both backends

Decided 2026-04-25: **don't integrate F2 PWA into CSWeb.** CSWeb is built around CSPro's data model; forcing F2 in means writing a fake `.dcf`, a sync-protocol translator, and a custom CSWeb adapter — significant ongoing tax for no analytical gain.

Instead, build a **Looker Studio dashboard** (recommended for low-touch ops + DOH familiarity; alternatives: Metabase, Google Sheets dashboard) that connects to:
- **CSWeb's PostgreSQL** (or its periodic CSV export) for the CAPI track
- **F2's response sheet** (already a Google Sheet) for the PWA track

That gives ASPSI ops + DOH a single dashboard URL showing both tracks in one view (response counts by region, completion rates, sync lag, daily case counts, disposition breakdowns), without forcing F2's architecture into a shape it shouldn't be. Implementation lives in [Epic 8](#epic-8--fieldwork-monitoring-and-quality-control).

### 5.5 Open dependencies

- **Shared codebook** — **draft v0.1 published 2026-04-25** at `deliverables/data-harmonization/codebook.md`. Covers all 13 cross-instrument dimensions audited against current spec/dcf state. Surfaces 8 open items (15.A–15.H) requiring ASPSI / instrument-design decisions before fieldwork. Codebook will iterate as F1 sign-off lands and F3/F4 Designer passes complete.
- **Facility master list** — single source for `facility_id`, `facility_type`, PSGC codes; used by F1 (cover block), F2 (facility selection), F3 (PSU sampling), F4 (cluster linkage). ASPSI to provide. Currently F2 PWA uses a placeholder facility list.
- **PSGC value-set vintage** — pin one PSGC release (e.g. PSA 2023Q4) for the entire engagement; all instruments use the same.
- **AAPOR ↔ PWA disposition mapping** — small but necessary; document before the harmonization ETL is built.

---

## 6. Risks & Watchlist

| Risk | Likelihood | Impact | Mitigation | Affected Epics |
|---|---|---|---|---|
| SJREB ethics clearance delay | Medium | High — blocks all pretesting and fieldwork | ASPSI actively coordinating; tracked as the long-pole dependency; remains the single most important external dependency | 0, 6 |
| Timeline pressure on D2 / D3 extended window / Tranche 2 | High (Tranche 2 due Fri 2026-04-24) | High — late delivery penalty applies (1% of total per calendar day if no further extension) | Apr 14 matrices + Word tools submission enacted the "submit what's ready and negotiate" mitigation; PMSMD feedback expected Apr 20 → 4-day turnaround if revisions come back. F1/F3/F4 DCFs stable; F2 PWA pilot-ready. | 2, 3, 6, 7 |
| Late questionnaire revisions from client | **Medium (active)** | Medium | **DOH sent a large late comment batch on the Apr-8 tools (forwarded Jun 10) — Myra's 2026-06-12 ruling: PARK all of it; the Apr-20 version stays the accepted baseline; revisit only if items resurface in SJREB/PSA review or pre-testing** ([[Source - DOH June Questionnaire Comments (PARKED) 2026-06-19]]). Build continues to Apr-20; **do not implement the June comments now.** If they reopen post-pretest, the biggest exposure is F1's two-step "since-2019/UHC-Act" restructure (~18 Qs) + F3 expenditure/FIES block + a contested F4 PIDS/DHS restructure. Reproducible generators absorb confirmed revisions cheaply. **Approved-and-building exception:** the PhilHealth Q38.1/Q38.2 + Q45.1/Q45.2 reinstatement (separate, DOH-agreed). | 2, 3, 6 |
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

## 7. Timeline & Sequencing Strategy

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
