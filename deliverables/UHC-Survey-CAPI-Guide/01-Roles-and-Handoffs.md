---
title: "01 — Roles and Handoffs"
category: deliverable
tags: [capi, cspro, csweb, roles, raci, handoffs, uhc-y2]
last_updated: 2026-05-08
status: draft
---

# 01 — Roles and Handoffs

## 1. Purpose

This document is the canonical role definition and handoff matrix for the UHC Survey Year 2 CAPI build and operations track (F1 Facility Head, F3 Patient, F4 Household — all on CSPro CAPI; F2 Healthcare Worker on PWA, referenced here only at the cross-track seams). It exists to settle four questions in one place:

1. **Who owns each artifact** at each phase of the [[CAPI-Development-Workflow|CAPI Development Workflow]] template (Phases 0–11).
2. **How handoffs are structured** between roles — what the upstream role must deliver, what the downstream role accepts, and how rejections route back.
3. **Who escalates to whom** when something breaks in the field, in the build, in the data, or in the client relationship.
4. **What the comms protocol is**, especially the rule that Carl Patrick Reyes (CAPI Developer) is **not** an authorized DOH-facing sender — every formal client message routes through Juvy Chavez-Rocamora (Project Coordinator), Dr. Paulyn Claro (Project Lead), or Dr. Merlyne Paunlagui (Asst Project Lead / Survey Manager).

The roles inventory in §2 maps to the team composition in [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/ASPSI|ASPSI]] and to the survey-deployment chain in [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Revised Inception Report|the Revised Inception Report]]. The RACI in §3 is opinionated — every phase has at least one Accountable and one Responsible role identified, on the assumption that ambiguous accountability is the single biggest predictor of missed deliverables on this engagement. The handoff matrix in §4 is the operating-procedure layer that the [[02-Phase-0-2-Foundation|Phase 0–2 Foundation]] and [[06-Phase-8-CSWeb-and-Tablets|Phase 8 CSWeb and Tablets]] guides depend on.

This document supersedes ad-hoc role assignments captured in earlier scrum standups and meeting minutes. When this document and a meeting minute disagree, this document is the source of truth for routing, RACI, and escalation; meeting minutes are the source of truth for individual decisions taken on a given date.

---

## 2. Roles inventory

### 2.1 Project Lead

- **Title:** Project Lead / Public Health Specialist
- **Held by:** Dr. Paulyn Jean A. Claro ([[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Dr Paulyn Claro|wiki entity]])
- **Reports to:** ASPSI President (Juvy C. Rocamora in her ASPSI-officer capacity); ultimately to DOH-PMSMD as the contractual counterparty.
- **Reports from:** Survey Manager (Dr. Paunlagui), Health Policy Specialist (Dr. Silva-Javier), Project Coordinator (Juvy), CAPI Developer (Carl), Field Manager (Almendral), all RAs.
- **Phases active:** 0, 1, 2, 4 (sign-off), 5 (sign-off), 7 (sign-off), 8 (sign-off), 9 (sign-off), 10, 11.
- **Inputs:** Final review packages prepared by team leads; SJREB and PSA correspondence via Juvy; client feedback from DOH-PMSMD; ADB/Xylee technical review correspondence.
- **Outputs:** Signed deliverable cover letters; client-facing positions on scope changes; tranche acceptance and payment-release endorsements; final report endorsement.
- **Critical decisions owned:**
  - Scope-change acceptance (in or out, against contract).
  - Tranche-package release decision (does the bundle go to DOH today, or wait for one more pass?).
  - F2 cover-block rewrite review (per Carl's draft at `deliverables/F2/F2-Cover-Block-Rewrite-Draft.md`).
  - Ethics-issue final call (escalation to SJREB).
  - Whether to sign off a deliverable as "as-is with caveats" vs. holding for a fix.
- **Escalation when stuck:** Counterparty escalation — Mr. Lindsley Jeremiah D. Villarante (PMSMD Division Chief) for client-side blockers; ASPSI President / Board for resource conflicts; SJREB direct for ethics issues.

### 2.2 Health Policy Specialist / LSS Convener

- **Title:** Health Policy Development Specialist
- **Held by:** Dr. Ma. Esmeralda "Myra" Silva-Javier ("Doc Myra"), `mcsilva@up.edu.ph` ([[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Dr Myra Silva-Javier|wiki entity]])
- **Reports to:** Project Lead.
- **Reports from:** RAs and CAPI Developer for question-level methodology clarifications.
- **Phases active:** 1 (questionnaire interpretation), 2 (concept-page review on health-policy items), 4 (skip-logic spec review), 5 (spec-correction sign-off), 9 (pretest debrief — convenes the LSS), 10 (interim-finding interpretation), 11 (final-report contributions).
- **Inputs:** Draft questionnaires, F-series skip-logic-and-validation specs, pretest debrief notes, interim cross-tabs, dummy-table outputs (Annex I).
- **Outputs:** Health-policy interpretation memos, item-by-item review comments (e.g. the Row 53 facility-tool clarification cycle), LSS meeting agendas + tasking outputs, final-report health-policy chapters.
- **Critical decisions owned:**
  - Convening the **Lessons-Learned Session (LSS)** for Tranche transitions (e.g. Apr 13 LSS for Tranche-1 → Tranche-2 handover; subsequent post-pretest LSS).
  - Methodology authority on health-policy specifics — UHC-IS classification, indicator interpretation, sub-population definitions.
  - Whether a question-level finding is a wording problem (route back to her) vs. a build problem (route to Carl) vs. an enumerator-instruction problem (route to Survey Manager).
- **Escalation when stuck:** Project Lead for political / client-relationship cover; Survey Manager for sample-design intersections; ADB/Xylee for technical-review reconciliation.

### 2.3 Survey Manager

- **Title:** Asst. Project Lead / Survey Manager
- **Held by:** Dr. Merlyne M. Paunlagui ([[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Merlyne Paunlagui|wiki entity]])
- **Reports to:** Project Lead.
- **Reports from:** Field Manager, STLs (via Field Manager), Survey Enumerators (via STLs), CAPI Developer for any methodology-driven build clarifications.
- **Phases active:** 0 (sample design), 1 (questionnaire methodology review), 4 (cross-field rules review), 5 (spec-correction methodology gate), 7 (bench-test mock-case design review), 9 (pretest plan ownership + ADB-comments-on-pretest response), 10 (fieldwork supervision), 11 (final-report methodology chapters).
- **Inputs:** Inception Report sample design (1,521 F1 / 2,672 F4 / 45 OP + 30 IP F3 per domain); Annex D Replacement Protocol; ADB comments matrix on pretest (Annex G); F-series skip-logic-and-validation specs; STL cluster-level field reports.
- **Outputs:** Pretest plan; methodology approvals on dictionary changes; cross-field consistency rules signed off (e.g. tenure ≤ age − 15 in F1; F2 self-admin 3-day window rule); replacement-cap policing.
- **Critical decisions owned:**
  - Methodological quality across F1/F2/F3/F4 — is a finding methodologically valid, methodologically tolerable, or methodologically fatal?
  - Pretest plan structure: site selection (per May 4 meeting: Los Baños + Bay LPH-Bay District), case-count targets, debrief format.
  - Cross-field consistency rules: which are HARD blocks, which are SOFT warnings, which are post-facto edits in CSBatch.
  - Replacement-cap enforcement: whether a cluster has used its 5–10% cap appropriately or whether enumerator discretion has crept in (Annex D bans this).
- **Escalation when stuck:** Project Lead for scope/scope-change conflicts; LSS convener (Dr. Silva-Javier) for health-policy-vs-methodology trade-offs; Statistician (Faderogao) for sampling-math arbitration.

### 2.4 Project Coordinator

- **Title:** Project Coordinator (and ASPSI President / CSA counterparty signatory in her ASPSI-officer capacity)
- **Held by:** Juvy C. Chavez-Rocamora ([[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Juvy Chavez-Rocamora|wiki entity]])
- **Reports to:** Project Lead.
- **Reports from:** All team members for **anything bound for DOH-PMSMD**. This is the formal-submissions chokepoint.
- **Phases active:** 0–11 (every phase that produces a client-facing deliverable, a status update, or a logistics commitment routes through her).
- **Inputs:** Build artifacts, comment matrices, status updates, scope-change requests, payment-tranche packages, file shares from any team member tagged "for DOH."
- **Outputs:** **Formal DOH submissions** — Jan 30 Inception Report submission; Apr 14 matrices + Word data-collection-tools submission; subsequent tranche packages. Submitted-on-behalf-of-team correspondence. Cross-team scheduling. ASPSI-DOH big-group thread management.
- **Critical decisions owned:**
  - **Formal-submissions gate.** Per the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Team Communication Protocol|Team Communication Protocol]] established Apr 13, no team-to-DOH message goes out except through Juvy / Dr. Claro / Dr. Paunlagui. Juvy is the canonical owner of the actual submission mechanics.
  - When a deliverable bundle is "ready enough" to submit (after Project Lead and Survey Manager sign off, but the assemble-and-send call is hers).
  - Lead-time enforcement: ≥1 working day for review before any deliverable is submitted to DOH (per the protocol; not yet numerically encoded but enforced in practice).
  - Subject-line discipline for ASPSI↔DOH email — relevant subject lines per the Apr 13 protocol; she rejects vague subjects.
- **Escalation when stuck:** Project Lead for content/scope decisions; Survey Manager for methodology-driven submission timing.

> [!important] Carl is NOT a DOH-facing sender
> Per the Apr 13 Team Communication Protocol: only Juvy / Dr. Claro / Dr. Paunlagui may send to DOH. Carl never CC's DOH directly. Every Carl-authored artifact (DCFs, FMFs, skip-logic specs, manual sections, case-ID briefs, tablet-spec memos) is shared **internally** with Juvy + Dr. Claro + Dr. Paunlagui (Dr. Silva-Javier when health-policy-relevant). Juvy decides whether/when it is forwarded to DOH and prepares the cover note.

### 2.5 CAPI Developer

- **Title:** Data Programmer (per CSA TOR) / CAPI Developer (per workflow)
- **Held by:** Carl Patrick L. Reyes (this engagement's author)
- **Reports to:** Project Lead (deliverable acceptance); Survey Manager (methodology-driven build decisions); Project Coordinator (formal-submission timing).
- **Reports from:** CAPI QA Tester (Shan Lait) — Carl's first formal review gate; CSWeb Administrator (TBD) for sync-side issues; STLs/SEs in production for app bugs (escalated through Field Manager).
- **Phases active:** 0 (working environment); 1 (source ingestion + wiki); 2 (CSPro toolchain concept pages); 3 (DCF generators — F1 671 items, F3 806 items, F4 623 items per current state); 4 (skip-logic-and-validations spec); 5 (spec corrections + DCF regen); 6 (FMF + APC application build — F1 dictionary Build-ready 2026-05-04; F1 FMF Section A in flight); 7 (bench testing partner with CAPI QA); 8 (CSWeb deploy + tablet provisioning support); 9 (pretest support); 10 (production fieldwork support — hot-fix protocol); 11 (final dataset export + closeout codebook).
- **Inputs:** Apr 20 questionnaires (F1/F3/F4 + F3b Patient Listing Protocol); Annex G recommendations matrix (drove Apr 20 rev); Annex E indicators matrix; Annex H consent forms (verbatim into CAPI intro screens); CSPro 8.0 Users Guide; Khurshid technique cards; Survey Manual Working File (May 6); Protocol V2 (Apr 30); ASPSI methodology direction from Survey Manager and LSS convener.
- **Outputs:**
  - **F1**: `FacilityHeadSurvey.dcf` (12 records / 671 items), `generate_dcf.py`, `F1-Skip-Logic-and-Validations.md`, `FacilityHeadSurvey.fmf` (in progress), `FacilityHeadSurvey.apc`, `FacilityHeadSurvey.pff`, bench-test seed cases.
  - **F3**: `PatientSurvey.dcf` (18 records / 806 items), `generate_dcf.py`, `generate_fmf.py`, `PatientSurvey.generated.fmf` (19 forms), `F3-Skip-Logic-and-Validations.md` (1,133 lines).
  - **F4**: `HouseholdSurvey.dcf` (22 records / 623 items), `generate_dcf.py`, `generate_fmf.py`, `HouseholdSurvey.generated.fmf` (24 forms), `F4-Skip-Logic-and-Validations.md` (904 lines).
  - **Shared**: `cspro_helpers.py`, `export_dcf_to_xlsx.py`, `shared/build_psgc_lookups.py`, `shared/PSGC-Cascade.apc`, the four PSGC external lookup `.dcf`+`.dat` pairs, `Capture-Helpers.apc` (GPS+photo).
  - **F2 (cross-track for context)**: PWA at production v2.0.0; Admin Portal Sprint AP1–AP4 complete; Round 3 vs staging v2.0.1-rc opens 2026-05-12.
  - **Internal artifacts**: technique cards integrated from Khurshid corpus; this guide; case-ID convention brief; CAPI manual section for Kidd's Working File integration.
- **Critical decisions owned:**
  - Generator-over-hand-edit discipline — every DCF rev goes through the Python generator (Khurshid 2023-09-21 Reformat-Data SOP applies here).
  - Logic-pass-before-form-build — skip-logic-and-validation spec is reviewed before opening Designer or wiring `.fmf`.
  - HARD/SOFT/GATE classification on every validation rule (per the workflow template Phase 4 contract).
  - Naming convention for items (`Q{n}_{SHORT}`, `_OTHER_TXT`, etc.) and for case IDs (12-digit decomposed PSGC-anchored format adopted 2026-05-05).
  - When a dictionary change is regenerate-and-re-bench-test (most cases) vs. surgical hand-edit (avoided as a rule).
  - Hot-fix push protocol — what counts as hotfix-worthy on tablets (in concert with CSWeb Administrator and Field Manager).
- **Escalation when stuck:**
  - Methodology question → Survey Manager (Paunlagui).
  - Health-policy interpretation → Health Policy Specialist (Silva-Javier).
  - Client / scope question → Project Coordinator (Juvy) → Project Lead (Claro).
  - Tooling question (CSPro / CSEntry quirks) → US Census Bureau forum + Khurshid corpus first; ADB/Xylee for cross-tool reviews; WHO/IDinsight for Year-1-comparison context.

### 2.6 CAPI QA Tester

- **Title:** QA Tester (Research Assistant, formally introduced Apr 13, 2026)
- **Held by:** Shan Lait ([[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Shan Lait|wiki entity]]). Earlier wiki content used the spelling "Sean" (phonetic mishearing); canonical is **Shan Lait** per the Apr 13 minutes.
- **Reports to:** CAPI Developer (test-cycle owner) and Survey Manager (test-coverage methodology).
- **Reports from:** N/A — Shan is the first external pair of eyes on every Carl-authored build artifact, by design (per [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Forward-Only Sign-Off|Forward-Only Sign-Off]]).
- **Phases active:** 7 (bench testing — primary lane), 9 (pretest UAT), 10 (production fieldwork regression on hot-fixes), 11 (final-build closeout).
- **Inputs:** Carl-authored DCFs, FMFs, APCs, PFFs, skip-logic specs, bench-test mock-case files, F2 PWA UAT guides.
- **Outputs:**
  - F2 PWA UAT Round 1 + Round 2 closures at v1.1.1 (13 issues fixed Apr 23 → Apr 25).
  - F2 PWA Round 2 reopened against v2.0.0 (in flight with Kidd since 2026-05-04).
  - F2 PWA Round 3 vs staging v2.0.1-rc opens 2026-05-12.
  - 2026-05-07 R2 catch: **E4-APRT-050 orphan-admin guard** finding (specced but not implemented; surfaced via §5.12 step U.E1 of the Admin Portal tester guide).
  - F1 CSPro CAPI bench tests once F1 reaches bench state (F1 dictionary Build-ready 2026-05-04; FMF Section A in flight).
  - F3 / F4 CSPro CAPI bench tests downstream.
  - Bug list with repro steps per [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Forward-Only Sign-Off|Forward-Only Sign-Off]] (symptoms route back to the owning source doc, not up the gate chain).
- **Critical decisions owned:**
  - Bench-test mock-case execution — youngest eligible, oldest eligible, refusal at each gate, "None of the above" on every multi-select, every Other-specify, max roster size, every dynamic value-set branch, every cross-field validation triggered (Phase 7 contract).
  - Bug severity classification (`severity:critical|high|medium|low`) and type (`type:bug|skip-logic|validation|ux|i18n|sync`) per the F2 UAT discipline carried forward to CAPI.
  - Whether a finding is an artifact bug, a spec bug, or an interpretation bug — drives which upstream doc it routes back to.
- **Escalation when stuck:** CAPI Developer (Carl) is the first responder; Survey Manager (Paunlagui) for methodology-driven test coverage gaps; the wider ASPSI mailbox + `#f2-pwa-uat` Slack and (proposed) `#capi-fieldwork-uat` Slack for visibility.

### 2.7 Field Manager

- **Title:** Field Manager
- **Held by:** Ms. Airyne D. Almendral. **CV missing in Annex J** as of the current revision — flagged for Annex J rev2 in [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex J CV of ASPSI Team|Annex J]]. This is an open project-management gap, called out again in §8 below.
- **Reports to:** Project Lead and Survey Manager.
- **Reports from:** Survey Team Leaders (STLs), CSWeb Administrator (for tablet-side ops issues).
- **Phases active:** 0 (logistics planning), 8 (tablet provisioning + sync credentials distribution), 9 (pretest deployment), 10 (production fieldwork — primary lane), 11 (field-side closeout).
- **Inputs:** Tablet provisioning checklist from CSWeb Administrator; PFF + sync URL config from CAPI Developer; cluster-level facility lists (Annex B + Annex C); Annex D Replacement Protocol; training schedule (Aug 1st-week supervisors + Aug 2nd–4th weeks teams per the May 4 meeting); SE/STL roster.
- **Outputs:**
  - Tablet provisioning logistics — receive tablets, image with CSEntry + PFF, distribute to STLs.
  - SE/STL deployment plan — cluster-level team assignments.
  - Replacement-protocol enforcement — STLs report cap usage; Almendral compiles cluster-level totals.
  - Daily field reports rolled up to Project Coordinator.
- **Critical decisions owned:**
  - Tablet replacement when a unit fails in the field (own a small spare pool).
  - SE/STL substitution when an enumerator drops out mid-fieldwork.
  - Whether to pause a cluster's data collection vs. roll forward with replacements (within Annex D's 5–10% cap).
  - Logistics routing for the 7-dialect translation packs (Bisaya / Hiligaynon / Ilocano / etc., per the May 4 meeting).
- **Escalation when stuck:** Survey Manager for methodology-driven decisions (e.g. cap exceeded); Project Lead for client-facing exposure; CAPI Developer for app-side issues escalated up the SE → STL → CSWeb Admin chain.

### 2.8 Survey Team Leaders (STLs)

- **Title:** Survey Team Leader (one per cluster; **6 clusters** per Inception Report)
- **Held by:** **TBA per cluster.** Cluster table in [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Survey Manual Appendix A — RA Contacts|Appendix A — RA Contacts]] is template-only as of 2026-05-08 ("Juan dela Cruz" filler). Names land closer to the Aug 1st-week supervisor training.
- **Reports to:** Field Manager.
- **Reports from:** Survey Enumerators in their cluster (typically 4–8 SEs per STL).
- **Phases active:** 8 (tablet bring-up training), 9 (pretest), 10 (production fieldwork — primary lane), 11 (cluster-level closeout).
- **Inputs:** Cluster-level facility list; tablet kit; sync credentials; Annex D replacement protocol; the Survey Manual Working File (May 6); Annex H consent forms; F1/F3/F4 CAPI app + interviewer guides; this guide's STL onboarding checklist (§7.2).
- **Outputs:**
  - Daily cluster status reports (cases attempted / completed / refused / replaced / pending).
  - SE supervision and field-day debriefs.
  - Daily sync confirmations to CSWeb Administrator.
  - Field anomaly reports — facility refusals, security situations, weather, GPS failures.
  - Replacement-protocol logging per Annex D (which facility was replaced, why, by which substitute).
- **Critical decisions owned:**
  - Day-to-day enumerator deployment within the cluster.
  - Field-level escalation triage — does this anomaly need Field Manager? CAPI Developer? Survey Manager?
  - Whether to invoke replacement (within cap) or push for one more contact attempt (per Annex D ≥3-visit minimum).
  - Cluster-level consistency — visiting all sampled facilities, achieving the per-instrument case targets (F3 OP 45 + IP 30 per domain; F4 follow per-cluster allocation).
- **Escalation when stuck:** Field Manager first; Survey Manager for methodology questions; CSWeb Administrator for sync issues; CAPI Developer (via CSWeb Admin or Field Manager) for app crashes.

### 2.9 Survey Enumerators (SEs)

- **Title:** Survey Enumerator
- **Held by:** **TBA per cluster.** Roster lands in tandem with STL assignments closer to the Aug 2nd–4th weeks team training.
- **Reports to:** STL (their cluster lead).
- **Reports from:** N/A — SEs are the front line.
- **Phases active:** 8 (tablet bring-up training), 9 (pretest), 10 (production fieldwork — the entire household / patient / facility-head data-collection lane).
- **Inputs:** Tablet (provisioned by CSWeb Administrator + Field Manager); CSEntry app with F1/F3/F4 PFFs; sync credentials; consent forms (Annex H — verbatim text on tablet intro screens); Survey Manual Working File (May 6); replacement-protocol briefing; sync-troubleshooting one-pager; this guide's SE onboarding checklist (§7.3).
- **Outputs:**
  - Completed F1 / F3 / F4 cases captured in CSEntry.
  - Daily sync to CSWeb (10 PM upload mandate per Protocol V2).
  - GPS metadata (Capture-Helpers.apc auto-captures); end-of-interview verification photo per facility/HH.
  - Disposition codes (AAPOR-aligned) on every attempted case via FIELD_CONTROL block.
  - Patient Listing Form entries per F3b protocol (CSPro-generated random intervals).
- **Critical decisions owned:**
  - Per-case execution discipline — read questions verbatim, follow skip routing, capture refusals per Annex D ≥3-visit rule.
  - **Enumerator discretion is explicitly banned by Annex D** for replacement decisions — escalate to STL.
  - Whether a sync issue is "try again later" vs. "this needs the STL now."
- **Escalation when stuck:** STL (every time, before anything else); for app crashes, STL routes to CSWeb Admin → CAPI Dev.

### 2.10 CSWeb Administrator

- **Title:** CSWeb Administrator (server + sync ops)
- **Held by:** **TBD / unassigned.** Likely shared between CAPI Developer (Carl) and an ASPSI ops person (candidate: Marriz Garciano as Data Manager, with Juvy / Field Manager as backups). **This role MUST be formally assigned before tablet provisioning begins** (target: ahead of the July tablet provisioning window). See §8.
- **Reports to:** Field Manager (operationally — tablet-readiness gates field deployment); Project Coordinator (administratively).
- **Reports from:** STLs (daily sync confirmations); SEs (via STLs) for app-side anomalies; CAPI Developer for build-deploy handoffs.
- **Phases active:** 8 (CSWeb provisioning + sync architecture), 9 (pretest sync support), 10 (production fieldwork — daily monitoring), 11 (final dataset export support).
- **Inputs:** CSPro `.dcf` (loaded as the dictionary on the server); deploy-ready PFFs; HMAC / sync URL config; user-import CSV (CSWeb bulk import per Khurshid pattern); value-label CSV (for Sync Report dropdowns per Khurshid 2022-05-05).
- **Outputs:**
  - Provisioned Wampserver + CSWeb instance (or chosen sync target — CSWeb is the recommended path per the workflow template Phase 8).
  - **CSWeb users** created via the Khurshid pattern: Users tab → Add User → role dropdown → password (entered twice) → Add **(Khurshid 2022-05-05)**. Don't reuse passwords across users for audit traceability.
  - **CSWeb roles** assigned per the two-built-in + custom model **(Khurshid 2022-05-05)**:
    - **Administrator** — full options + upload/download all dictionaries (Carl + Marriz + Juvy).
    - **Standard user** — cannot access admin options; can upload/download dictionaries (STLs as cluster-scoped users for dashboard read).
    - **Custom roles** — if a sub-team needs report-only or download-only, build a custom role: Add Role → name → check only "Report" → Add → expand permissions via pencil icon.
  - **Sync Report** dashboard with value-label CSV imported (codes-and-labels-in-dictionary-ID-order per Khurshid; misordered CSV silently labels the wrong fields).
  - **Map Report** for cluster-level monitoring.
  - **`synchronize_file()` configuration** — `put` direction for tablet → server uploads of GPS photos and consent images; destination folder `pictures\` created via Files tab → Create Folder **(Khurshid 2022-05-05)**.
  - Daily backup of incoming `.dat` files; recovery plan for CSWeb crashes.
  - Hot-fix push: receive new PFF from CAPI Developer, deploy to CSWeb, push to tablets next sync.
- **Critical decisions owned:**
  - Sync architecture: CSWeb (recommended) vs. Dropbox / FTP / Bluetooth fallback. CSWeb per the May 4 meeting + Protocol V2's 10 PM upload mandate.
  - User-role provisioning model: who is admin, who is standard, who is custom-restricted.
  - Backup cadence and retention.
  - When a sync-side failure is environmental (network, server) vs. app-side (escalate to CAPI Developer).

> [!warning] Open gap
> CSWeb Administrator is **unassigned** as of 2026-05-08. Tablet provisioning expected July; training Aug 1st-week supervisors then Aug 2nd–4th weeks teams. Without a named CSWeb Admin, none of the user CSV / value-label CSV / sync-report-dashboard work blocks can start. Project Lead consideration item.

### 2.11 DOH-PMSMD (client side)

- **Title:** Performance Monitoring and Strategy Management Division — UHC Survey Year 2 client.
- **Held by:** **Mr. Lindsley Jeremiah D. Villarante** (Division Chief, primary counterpart). Supporting cast: DOH Epidemiology Bureau (Dr. Alfonso Miguel Regala) for technical input on indicators; ADB / Xylee Javier as technical advisor; WHO / Dr. Duan Mengjuan as advisory.
- **Reports to:** DOH leadership; ultimately the Office of the Secretary.
- **Reports from:** ASPSI (via Project Coordinator's submissions).
- **Phases active:** 0 (TOR + contract); 4 (review on dictionary spec when forwarded); 5 (review on revisions); 7 (Tranche-1 deliverable review); 9 (pretest sign-off — gates main fieldwork); 10 (interim status acceptance); 11 (final-deliverable acceptance + tranche-payment release).
- **Inputs:** ASPSI submissions via Juvy/Claro/Paunlagui (never direct from Carl); status updates per the bi-monthly cadence (per the Apr 13 protocol).
- **Outputs:**
  - Technical clearance (gates SJREB submission).
  - Tranche acceptance letters.
  - Comment matrices on deliverables (Annex G is the canonical example — 23 remarks from PMSMD / ADB / DOH 11th EXECOM Sep 2024).
  - Certificate of Acceptance per the TOR.
- **Critical decisions owned:**
  - Deliverable acceptance — gates ASPSI tranche payments and, transitively, Carl's compensation per CSA §5.
  - Scope-change approval / rejection.
  - Whether to require a comment-matrix-response cycle on a given submission.
- **Escalation when stuck:** Internal DOH chain; ADB technical mediation; Office of the Secretary if needed.

> [!note] Compensation linkage
> Carl is not directly engaged by DOH, but his payments are gated by DOH acceptance of each deliverable bundle (CSA §5). DOH-PMSMD is the de facto acceptor of Carl's work even with no direct contractual relationship.

### 2.12 SJREB — Single Joint Research Ethics Board

- **Title:** Single Joint Research Ethics Board
- **Held by:** SJREB secretariat + reviewers (institutional).
- **Reports to:** Itself + the institutions it federates.
- **Reports from:** ASPSI (via Project Coordinator + Project Lead).
- **Phases active:** Long-pole blocker for **Phase 9** (pretest) and **Phase 10** (main fieldwork). Cannot be skipped.
- **Inputs:** Survey protocol (V2 circulated by Myra 2026-04-30); F1/F2/F3/F4 instruments; informed consent forms (Annex H); CHD (Center for Health Development) coordination evidence; DOH technical clearance.
- **Outputs:** Ethics clearance — without this, no human-subject contact may occur.
- **Critical decisions owned:**
  - Whether the protocol + instruments + consent flow are ethically acceptable.
  - Whether modifications are required before clearance is granted.
  - Whether a mid-study amendment requires re-review.
- **Escalation when stuck:** No external escalation — SJREB's word is final on ethics. Project Lead + Survey Manager handle any corrective revisions.

> [!warning] Critical-path blocker
> Per the Apr 10 project intelligence brief: SJREB sits at the center of the project's #1 critical blocker chain — Tranche 1 acceptance → DOH technical clearance → SJREB ethics clearance → Pretesting → CAPI bench/field validation → Tranche 2 acceptance → Carl's C-T2 payment (PHP 117,000). 30% of Carl's contract value transits this gate.

### 2.13 PSA — Philippine Statistics Authority

- **Title:** Philippine Statistics Authority — sampling-design endorsement + data-publication clearance.
- **Held by:** PSA institutional.
- **Reports to:** Itself.
- **Reports from:** ASPSI (via Project Coordinator) for the survey-methodology endorsement track.
- **Phases active:** Phase 0 (sampling-design endorsement track in parallel to SJREB); Phase 11 (data-publication clearance for any final-report dissemination).
- **Inputs:** Sampling design from Inception Report; PSGC reference (PSA 1Q 2026 PSGC is the basis of the project's case-ID convention adopted 2026-05-05).
- **Outputs:** Sampling endorsement; PSGC code authority; eventual publication clearance.
- **Critical decisions owned:** Sampling-design acceptability; PSGC authority on geographic codes (the project uses PSA 1Q 2026 PSGC verbatim, externalized to `shared/psgc_*.dcf` lookups).
- **Escalation when stuck:** Survey Manager + Project Lead.

### 2.14 ADB technical advisor

- **Title:** Asian Development Bank technical advisor / reviewer.
- **Held by:** Ms. Xylee Javier ([[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/ADB|wiki entity]]).
- **Reports to:** ADB internally; advises DOH on UHC-related survey work.
- **Reports from:** ASPSI (questionnaire packages forwarded by DOH for technical review).
- **Phases active:** Phase 1 (questionnaire interpretation), Phase 5 (revisions review), Phase 9 (pretest plan review).
- **Inputs:** Questionnaire drafts; pretest plan; comment matrices.
- **Outputs:** Annex G remarks (23 in the current canonical version) — drove the Apr 20 questionnaire revision pass; pretest-plan comments.
- **Critical decisions owned:** Technical-review judgment on whether the survey instruments capture the UHC indicators ADB cares about; which of the 23 Annex G remarks are blocking vs. nice-to-have.
- **Escalation when stuck:** N/A — ADB is an external advisor; their remarks are inputs to ASPSI's response cycle, not a hard gate.

---

## 3. RACI per phase

**RACI definitions (inline):**

- **R — Responsible.** Does the work. Multiple R's allowed.
- **A — Accountable.** The single neck on the line. Exactly one A per cell unless explicitly noted.
- **C — Consulted.** Two-way conversation; their input shapes the deliverable.
- **I — Informed.** One-way notification; they need to know the outcome.
- **(blank)** — Not engaged this phase.

Rows are workflow phases (per [[CAPI-Development-Workflow|the CAPI Development Workflow]] template). Columns are roles.

| Phase | Project Lead | Health-Policy / LSS | Survey Manager | Project Coordinator | CAPI Developer | CAPI QA | CSWeb Admin | Field Manager | STLs | SEs | DOH-PMSMD | SJREB | PSA | ADB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **0 — Project scaffolding** | A | C | R | R | R | I | I | C | | | C | I | C | I |
| **1 — Source ingestion** | C | C | A | I | R | I | | | | | I | | | C |
| **2 — Tool knowledge base** | I | | C | I | A/R | I | I | | | | | | | |
| **3 — Spec / dictionary generation** | C | C | C | I | A/R | I | | | | | I | | C | I |
| **4 — Skip-logic & validation spec** | A | C | R | I | R | C | | | | | I | | | C |
| **5 — Spec / dictionary corrections** | C | C | A | I | R | C | | | | | I | | | I |
| **6 — Application build** | I | C | C | I | A/R | C | C | | | | | | | |
| **7 — Testing** | I | C | C | I | R | A/R | C | C | C | | | | | |
| **8 — Sync / packaging / deployment** | C | I | C | C | R | C | A/R | R | C | C | I | | | |
| **9 — Pretest / UAT & field readiness** | A | R | R | C | R | R | R | R | R | C | I | C | I | C |
| **10 — Production fieldwork support** | C | C | A | C | R | R | R | R | R | R | I | I | | |
| **11 — Closeout** | A | R | R | R | R | C | C | R | C | I | A/I | I | C | I |

**Notes on the table:**

- Phase 0 has dual R's (Survey Manager + Project Coordinator + CAPI Developer) because scaffolding is genuinely shared work — sample design (Survey Manager), CSA + project-folder + index (Project Coordinator and Carl), and toolchain choices (Carl). The Project Lead is Accountable.
- Phase 6 lists **CSWeb Admin as Consulted** because deploy-readiness (Phase 8) influences app-build choices (Phase 6) — sync URL config, FIELD_CONTROL fields that cross-reference server state.
- Phase 7 has **CAPI QA as A/R** (Accountable AND Responsible) because Shan owns the test cycle outcome per the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Forward-Only Sign-Off|Forward-Only Sign-Off]] rule — Carl is the implementer, Shan is the gate.
- Phase 8 has **CSWeb Admin as A/R** because CSWeb provisioning is the deployment-readiness chokepoint. Field Manager is also R because tablet provisioning is half logistics.
- Phase 9 has the broadest engagement — every role except SJREB-Accountability (which sits with Project Lead) and DOH-acceptance (which is Informed during pretest, Accountable at Tranche transition).
- Phase 11 has **DOH-PMSMD as A/I** because final acceptance is theirs (A) but they are not "Responsible" for any of the closeout work (I in the work sense).

---

## 4. Handoff matrix

The from-role → to-role table below is the operating procedure for every artifact crossing a role boundary. Each row reads: **From-role hands off → to To-role: this artifact, with these acceptance criteria.**

| From | To | Artifact | Acceptance criteria | Reject-back path |
|---|---|---|---|---|
| CAPI Developer | CAPI QA | Regenerated `.dcf` + `.fmf` + `.apc` + `.pen` + bench-test seed-case files | Dictionary opens cleanly in Designer; FMF has no orphan items; PROC compiles; seed cases cover every skip path | Reject with bug list per repro-step format → CAPI Dev regenerates |
| CAPI QA | CAPI Developer | Bug list with repro steps + severity / type labels | Each bug names the owning source doc (Forward-Only Sign-Off); severity classified | If bug is interpretation, route to Survey Manager / Health-Policy Specialist |
| CAPI Developer | CSWeb Admin | Deploy-ready `.pen` (or PFF) + sync URL config + dictionary `.dcf` for server | PFF version-tagged; dictionary matches deployed app; sync round-trip tested in dev | Reject if dict mismatch → CAPI Dev re-package |
| CSWeb Admin | Field Manager | Provisioned tablets + sync credentials + tablet bring-up checklist | Each tablet boots, syncs a test case, has the right PFF, has the right sync URL | Reject device → CSWeb Admin re-image |
| CSWeb Admin | CAPI Developer | CSWeb sync logs + value-label CSV templates | Template CSV format follows Khurshid 2022-05-05 codes-in-dictionary-order rule | Reject if columns out of dictionary order → CSWeb Admin re-export from Designer |
| Field Manager | STLs | Enumerator team assignments + replacement-protocol training + provisioned tablets | Cluster targets clearly stated (per Annex B/C/D); SEs identified per cluster | Reject incomplete kit → Field Manager backfills |
| STLs | SEs | Per-day case lists + facility introductions + replacement-rule reminders | SE knows the day's facilities and the Annex D ≥3-visit minimum | SE reports back same-day if a facility is unreachable |
| SEs | STLs | Daily completed-case syncs + field anomalies + replacement requests | Sync confirmation visible on tablet; anomalies described concretely | STL escalates anomaly per §5 |
| STLs | CSWeb Admin | Daily sync confirmations + field anomalies (app-side) | Sync timestamp matches Protocol V2's 10 PM upload mandate | If anomaly is app-side, route forward to CAPI Dev |
| CSWeb Admin | Project Coordinator | Weekly sync stats + completion-by-cluster summary | Numbers reconcile to STL daily reports | Reject mismatch → CSWeb Admin reconciles |
| Project Coordinator | DOH-PMSMD | **Formal weekly / bi-monthly update** (per Apr 13 protocol) | Subject line scoped; cover note approved by Project Lead | DOH may comment-matrix back |
| Project Coordinator | CAPI Developer | DOH change requests / formal client requests with cover note | Carl receives client requests **only via Juvy** — never direct from DOH | Reject if scope violates CSA → Project Lead arbitrates |
| Health-Policy / LSS | All | LSS meeting outputs (tasking, decisions) | Notes reviewed by attendees; approved by Project Lead before any onward share | Open-loop tasking → next LSS |
| Survey Manager | All | Methodology rulings on cross-field rules / replacement-cap policing / pretest-plan calls | Written in spec docs (F-series Skip-Logic-and-Validations files) | Disagreement escalates to Project Lead |
| All | Survey Manager | Methodology questions | Cited against the questionnaire / Protocol V2 / Inception Report | If methodology question is health-policy specific, copy in LSS convener |
| Project Lead | All | Sign-off on Tranche bundles / scope decisions | Written in cover-letter or LSS minutes | Open issues route forward to next phase |
| ADB / Xylee | DOH-PMSMD | Annex G technical comments | Each comment labelled blocking vs. nice-to-have | DOH forwards to ASPSI; ASPSI responds matrix |
| SJREB | Project Lead | Ethics clearance (or revisions-requested) | Clearance letter; revisions clearly itemized | Revisions feed back through Phase 4 → 5 → 6 cycle |
| PSA | Project Lead | Sampling endorsement | Endorsement letter | Revisions feed back through Phase 0 sample-design pass |

**Cross-track seam (F2 PWA → CAPI):** F2 PWA UAT discipline (GitHub Issues + project board + `#f2-pwa-uat` Slack + daily-digest workflow) carries forward into the CAPI track. Specifically:

- **Establish a parallel `#capi-fieldwork-uat` Slack channel** for F1/F3/F4 pretest + production. Receives real-time event posts (issue opened, fixed-pending-verify, milestone closed) per the F2 pattern.
- **Establish a parallel `#capi-ops` Slack channel** for CSWeb Admin + Field Manager + STLs ops chatter. Daily digest at 09:00 MNL during active fieldwork rounds.
- **GitHub Issues with `from-uat-round-N-YYYY-MM` labels** — same convention Shan uses on F2 (`from-uat-round-2-2026-05`).
- **Triage labels mirror F2:** `severity:critical|high|medium|low`, `type:bug|skip-logic|validation|ux|i18n|sync|device|sync-server`. `device` and `sync-server` are CAPI-specific additions.

---

## 5. Escalation paths

For each common situation, the escalation chain below is the pre-agreed default. Roles are expected to follow the chain unless an obvious shortcut applies (e.g. STL going directly to CAPI Developer when Field Manager is unreachable and the case is mid-interview).

### 5.1 Tablet sync fails in the field

```
SE  →  STL  →  CSWeb Admin  →  CAPI Developer (only if app-side)
```

- **SE first attempt:** retry sync per the sync-troubleshooting one-pager (network, time-of-day, credential refresh).
- **STL escalation criterion:** if 2+ SEs in the cluster see the same failure, or one SE sees it across two days, escalate.
- **CSWeb Admin scope:** server-side check — is CSWeb up, are credentials valid, is the dictionary loaded, is the disk full?
- **CAPI Developer scope:** if CSWeb Admin clears the server, and the app is logging a `synchronize_*` failure consistent with a code path, regression-test the PFF and prepare a hot-fix.

### 5.2 App crashes mid-interview

```
SE  →  STL  →  CAPI QA  →  CAPI Developer
```

- **SE first attempt:** record crash context (which question, what was entered) → reopen case → resume.
- **STL:** confirm the crash isn't tablet-specific (memory full, OS update lurking, cracked screen).
- **CAPI QA (Shan):** reproduce on the bench setup with the same case data; classify severity; produce a repro file.
- **CAPI Developer:** patch in generator, regenerate, push hot-fix PFF via CSWeb Admin.

### 5.3 Schema bug discovered (anywhere in the pipeline)

```
Anyone  →  CAPI Developer  (regen + Reformat-Data SOP)
```

- **Generator-over-hand-edit** is the operating rule: never edit the `.dcf` directly; fix the bug in the generator, regenerate, then run the Reformat-Data SOP **(Khurshid 2023-09-21)** so any in-flight cases reformat against the new schema.
- **CSWeb impact:** dictionary on the server must be re-uploaded matching the new generator output.
- **In-flight case impact:** Reformat-Data converts existing `.dat` to the new dictionary; STLs notified before any tablet syncs the new PFF.

### 5.4 Methodology question

```
STL (or SE via STL)  →  Survey Manager
```

- Survey Manager is the methodology authority — sample design, replacement protocol, eligibility filters, cross-field rules.
- If the question is **health-policy specific** (e.g. "how is YAKAP service classified?"), Survey Manager loops in the Health-Policy / LSS Convener.

### 5.5 Ethics issue

```
Anyone  →  Project Lead  →  SJREB
```

- **Examples:** an SE encounters a respondent who appears to have impaired capacity to consent; a household refuses but feels coerced by another household member; a facility head withdraws consent post-interview.
- **Project Lead's role:** decide whether the issue is a single-case correction (drop the case + log) or a protocol-level escalation (return to SJREB with a modification request).
- **SJREB:** binding voice on protocol-level questions.

### 5.6 Replacement-cap exceeded

```
STL  →  Field Manager  →  Survey Manager
```

- **Cap:** 5–10% facility replacements per Annex D.
- **STL:** report the cap-exceedance with a written reason for each replacement.
- **Field Manager:** verify the reasons aren't enumerator-discretion proxies (Annex D explicitly bans enumerator discretion).
- **Survey Manager:** decide whether to (a) accept the over-cap as a documented exception, (b) re-substitute from the same stratum, or (c) pause the cluster.

### 5.7 DOH change request

```
DOH  →  Project Coordinator  →  Project Lead  →  CAPI Developer
                    (NEVER direct to Carl)
```

- **The Apr 13 Team Communication Protocol explicitly bans direct DOH ↔ RA exchanges.**
- If a DOH-PMSMD person pings Carl directly (Viber, email, hallway), Carl flags it back up to Juvy + the ASPSI project mailbox immediately so the team has visibility.
- Project Lead decides whether the change is in-scope vs. out-of-scope vs. needs a contract amendment.
- CAPI Developer implements only after the chain has resolved.

### 5.8 Build artifact rejected by CAPI QA

```
CAPI QA (Shan)  →  CAPI Developer
                  (Forward-Only Sign-Off — symptom routes to source doc owner)
```

- **Forward-Only Sign-Off:** symptoms route back to the owning source doc, not up the gate chain.
- Example: a skip-logic bug found in F1 routes back to `F1-Skip-Logic-and-Validations.md` (Carl), which may itself route back to the questionnaire (Survey Manager) if the spec is correct against the questionnaire but the questionnaire is wrong.
- **No "design sign-off" gate** before Shan — Shan's first read **is** the acceptance gate.

### 5.9 Disagreement between this guide and a meeting minute

```
Read this guide  →  meeting minute is documented but does not override
```

- This guide is the source of truth for routing, RACI, and escalation.
- Meeting minutes are the source of truth for **specific decisions taken on specific dates** (e.g. the Apr 13 decision to make Juvy the formal-submissions gate; the May 4 decision to target June 12 CAPI completion).
- If a meeting minute appears to override this guide on routing/RACI/escalation, treat it as a guide-amendment proposal — raise to Project Lead for a guide update rather than acting on the meeting minute as a one-off override.

---

## 6. Communication protocol

The full text of the protocol lives in [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Team Communication Protocol|Team Communication Protocol]]. The key constraints repeated here:

### 6.1 Routing rules

**Within the team:**

- Streamline. Not every message goes to the big group.
- **Smaller groups** as needed (cluster-level, role-level).
- **Viber** — urgent updates and information only.
- **Email** — file sharing and anything that needs an audit trail. Use relevant subject lines to keep threads searchable.
- **Ms. Juvy must be in the loop** on every team↔team comm. This is non-negotiable.

**From team → DOH:**

- **Authorized senders only:** Juvy / Dr. Claro / Dr. Paunlagui. Three people. No exceptions.
- **Official submissions are done by the Project Coordinator (Juvy).**
- **Team members must prepare and share deliverables in advance** to give Juvy ≥1 working day for review before submission.
- **Viber** — urgent updates only.
- **Email** — file sharing with relevant subject lines.

**From DOH → team:**

- DOH focal → Project Lead / Asst Proj Lead + ASPSI focal (cc: RAs).
- **If DOH follow-ups arise, they are shared in the big ASPSI-DOH group.** No side-channel handling.

**Direct DOH ↔ RA exchanges:**

- **Prohibited.** All DOH requests must be transparently communicated to the entire team.

### 6.2 Implications for Carl (CAPI Developer)

The protocol's implications for the CAPI Developer specifically — these are repeated here because the rule is load-bearing for this guide:

1. **Never CC DOH directly.** Any technical artifact — DCFs, FMFs, skip-logic specs, manual sections, case-ID brief, tablet-spec memo — is shared internally with Juvy (+ Dr. Claro / Dr. Paunlagui). Juvy decides whether/when it forwards to DOH and prepares the cover note.
2. **Submit build artifacts to Juvy with lead time** (≥1 working day until a norm emerges). Don't expect same-day forwarding.
3. **Flag DOH-originating requests that arrive directly.** If someone from PMSMD pings Carl on Viber or email, the **explicit requirement** from the Apr 13 protocol is to bounce that back up to Juvy + the ASPSI project mailbox so the team has visibility. This is not a nice-to-have.
4. **Forward-Only Sign-Off** governs internal bug routing. Comms protocol governs external (DOH-facing) channels. The two rules don't conflict — they govern different lanes.
5. **Bi-monthly status cadence** (per Apr 13 "Other Matters"). Carl's status format aligns to that rhythm.

### 6.3 Tooling discipline (CAPI track inheriting from F2 PWA)

The F2 PWA UAT Slack-bot pattern (see [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F2 Admin Portal|F2 Admin Portal]] and the F2 UAT Slack bot description in the project memory) carries forward to F1/F3/F4 fieldwork:

- **`#f2-pwa-uat`** — existing F2 channel; remains for F2 work.
- **`#capi-fieldwork-uat`** (NEW) — establish at the start of CAPI bench-test phase for F1, before pretest. Receives:
  - Real-time event posts when a `from-uat-round-N-YYYY-MM` issue opens, moves to `fixed-pending-verify`, or closes.
  - Daily 09:00 MNL digest while a round is active.
  - Milestone-closed → CHANGELOG + GitHub Release auto-publish.
- **`#capi-ops`** (NEW) — operations chatter for CSWeb Admin + Field Manager + STLs. Daily-digest cron only fires during active fieldwork rounds.
- **GitHub Issues** with the same severity / type / round / status labels carried over from F2.
- **Google Doc** — the working manual, sample lists, contact lists. Single canonical link per artifact, edits tracked.
- **Email** — formal submissions, anything that needs an audit trail.
- **Viber** — urgent only. Carl uses the CAPI Viber group for ops, not for design discussion.

---

## 7. Onboarding checklists per role (newly-added members)

Three roles have new members joining mid-engagement: CSWeb Administrator (TBD), Survey Team Leaders (TBA per cluster), and Survey Enumerators (TBA per cluster). Each gets a numbered checklist below — read these in order, get the access listed, then schedule the briefing call.

### 7.1 CSWeb Administrator onboarding

1. **Read** [[06-Phase-8-CSWeb-and-Tablets|06 — Phase 8: CSWeb and Tablets]] start to end. This is the operational manual for the role.
2. **Read** [[07-Phase-9-10-Pretest-Fieldwork|07 — Phase 9–10: Pretest and Fieldwork]] for the production-side context.
3. **Read** the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSWeb Users Guide|CSWeb Users Guide source page]] for the permission model (5 dashboards × per-dictionary up/down + 2 built-in roles + custom).
4. **Read** the four Khurshid CSWeb technique cards: roles model, add user + assign role, `synchronize_file()`, value-labels CSV import (all in the [techniques.md](file:///C:/Users/analy/Documents/analytiflow/3_Resources/Learning-Materials/mentors/khurshid-arshad/videos/2022-05-05_how-to-sync-report-sync-files-add-users-and-define-roles_QU-XNX8_Aqc/techniques.md) for the 2022-05-05 video).
5. **Get access:**
   - SSH credentials to the Wampserver host (or container — TBD).
   - CSWeb admin login (separate from server SSH).
   - GitHub repo read access for the CAPI app (for PFF deploys).
   - Slack invite to `#capi-ops`.
   - Email distro: ASPSI project mailbox `aspsi.doh.uhc.survey2.data@gmail.com`.
6. **Receive:** test tablet kit (≥2 tablets) + test PFFs for F1/F3/F4 + a test value-label CSV.
7. **Verify:** end-to-end round trip — tablet → CSWeb → export — using a test case, **before** any production tablet is provisioned.
8. **Sign:** acknowledge the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Team Communication Protocol|Team Communication Protocol]] and this guide's §5 escalation paths.

### 7.2 Survey Team Leader onboarding

1. **Read** [[07-Phase-9-10-Pretest-Fieldwork|07 — Phase 9–10: Pretest and Fieldwork]] in full.
2. **Read** the STL section of [[99-Quick-Reference|99 — Quick Reference]] (one-page summary).
3. **Read** the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex D Replacement Protocol|Annex D Replacement Protocol]] — the ≥3-visit minimum, the same-stratum substitution rule, the 5–10% cap, the explicit ban on enumerator discretion. This is the rule STLs enforce.
4. **Read** the assigned-cluster section of [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Survey Manual Working File (2026-05-06 Kidd)|the Survey Manual Working File (2026-05-06)]].
5. **Get access:**
   - CSWeb dashboard read access for the assigned cluster (custom CSWeb role per Khurshid pattern — restricted to Sync Report + Map Report on the cluster's data).
   - Slack invite to `#capi-fieldwork-uat` and `#capi-ops`.
   - Cluster-level facility list (Annex B + Annex C subset) and cluster-level Patient Listing forms (per F3b protocol).
   - Tablet kit for the cluster (one tablet per SE plus a spare).
6. **Receive:** replacement-protocol briefing (in-person or video call from Field Manager + Survey Manager).
7. **Practice:** run a mock case end-to-end on a tablet — F1, F3, F4 — before the team-of-SEs training.
8. **Sign:** acknowledge this guide's §5 escalation paths and §6 communication protocol (specifically the no-direct-DOH rule).

### 7.3 Survey Enumerator onboarding

1. **Tablet handover** — receive your tablet from the Field Manager / STL with the F1/F3/F4 PFFs preloaded, sync credentials configured, and the consent-form intro screens displaying Annex H text verbatim.
2. **Tablet bring-up training** — per the Field Manager's training plan (Aug 2nd–4th weeks). Covers:
   - CSEntry app navigation.
   - Cover-page / consent-screen flow.
   - The skip-logic UX (when the app jumps a question, why).
   - GPS auto-capture and end-of-interview verification photo (Capture-Helpers).
   - Sync routine — Protocol V2's 10 PM upload mandate.
3. **Replacement-protocol briefing** — Annex D rules: ≥3-visit minimum, same-stratum substitution, no enumerator discretion. **You do not decide replacements; your STL does.**
4. **Sync-troubleshooting one-pager** — the SE's first-line guide before escalating to STL. Covers: network failures, credential refresh, time-of-day patterns, what to do if the tablet won't open the app.
5. **Read** the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex H Informed Consent Forms|Annex H Informed Consent Forms]] — you read this verbatim to respondents. SJREB-approvable text.
6. **Read** the SE section of [[99-Quick-Reference|99 — Quick Reference]].
7. **Sign:** consent / NDA + replacement-protocol acknowledgement.

---

## 8. Open role gaps and risks

This section captures roles, role-elements, and bus-factor risks that are unresolved as of the document date (2026-05-08). Each is owned for resolution by Project Lead unless noted.

### 8.1 CSWeb Administrator unassigned

- **Gap:** CSWeb Administrator role is TBD. Likely shared between CAPI Developer (Carl) and an ASPSI ops person (candidate: Marriz Garciano as Data Manager; backup: Juvy or Field Manager).
- **Why it matters:** None of the user CSV provisioning, value-label CSV import, sync-report-dashboard setup, custom-role creation, or `synchronize_file()` configuration can start without a named owner. Tablet provisioning expected July; supervisor training Aug 1st-week; team training Aug 2nd–4th weeks. Compressed timeline.
- **Action:** Project Lead names the CSWeb Administrator (or formally co-assigns) **before the July tablet-provisioning kick-off**. CAPI Developer cannot wear this hat alone — the role owns sync-side ops while the developer is fielding pretest issues, and the dual-hatting will create response-time gaps.

### 8.2 Field Manager (Almendral) — CV missing in Annex J

- **Gap:** Ms. Airyne D. Almendral's CV is missing from [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex J CV of ASPSI Team|Annex J]]. The other 7 (Claro, Paunlagui, Silva-Javier, Demaisip, Faderogao, Reyes, Garciano) are present.
- **Why it matters:** Annex J is a contractual deliverable bundle component. A missing CV in a downstream Tranche review is exactly the kind of gotcha that leads to a comment-matrix cycle.
- **Action:** Project Coordinator collects the CV from Almendral and queues an Annex J rev2 for the next tranche package.

### 8.3 Multilingual review for 7-dialect translations

- **Gap:** The May 4 meeting confirmed a 7-dialect translation list (Bisaya, Hiligaynon, Ilocano, etc.). Translation review owners are not yet assigned.
- **Likely owners:** ASPSI methodologists with regional language fluency + native-speaker enumerators in each cluster. But this needs to be formalized — translation-review-by-default-from-enumerators is a process risk.
- **Why it matters:** A translation defect surfaces as enumerator confusion in the field, which is the most expensive place to catch it. Pretest is the right moment to surface translation defects, but only if there is a clear feedback path.
- **Action:** Survey Manager assigns one named reviewer per dialect — ideally before pretest (Aug 2nd week). Reviewer reviews the translated CSPro labels (multi-language `tr` / `setlanguage` switch) end-to-end on a tablet.

### 8.4 Backup CAPI Developer — bus factor on Carl is 1

- **Gap:** Carl is the sole CAPI Developer on the engagement. F1 (671 items), F3 (806 items), F4 (623 items), F2 PWA, the case-ID generator, the PSGC cascade, the Capture-Helpers — all live in his head and his repos.
- **Why it matters:** A single point of failure for ~30% of the contract value (Tranche 2 and 3 both depend on the CAPI build), through 5 more months of fieldwork.
- **Mitigations in flight (that reduce but don't eliminate the risk):**
  - Generator-over-hand-edit means rebuilding from scratch is "run the script," not "reverse-engineer the dictionary."
  - This guide + the Phase guides in this folder document the build process well enough for a successor to pick up.
  - The wiki + index.md is the single source of truth for the project state.
- **Mitigations not yet in flight:**
  - No identified backup CAPI Developer.
  - No documented "if Carl is hit by a bus" protocol.
- **Action:** Project Lead consideration. Options: (a) name a backup who shadows Carl through pretest; (b) accept the risk with a documented rollback plan (e.g., revert to Year-1 SurveyCTO-style track if catastrophic); (c) negotiate a contractor backup as a contingency. The choice is a Project Lead call, not a CAPI Developer call.

### 8.5 STL roster — 6 clusters, names TBA

- **Gap:** Per the Inception Report, 6 clusters; per [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Survey Manual Appendix A — RA Contacts|Survey Manual Appendix A]] (May 6), the contact table is template-only ("Juan dela Cruz" filler).
- **Action:** Field Manager + Project Coordinator finalize STL assignments before the Aug 1st-week supervisor training. Names + phones + emails populated in Appendix A. Cluster 5 entry duplicated in current Appendix A (typo) — fix in next rev.

### 8.6 Comms protocol drift risk

- **Gap:** The Apr 13 Team Communication Protocol is enforced via social pressure, not via tooling. The team is small enough today that this works. As STLs and SEs onboard (~30+ field staff), the rule "DOH never reaches RAs directly, RAs never reach DOH directly" is much harder to police.
- **Action:** §7.2 (STL) and §7.3 (SE) onboarding checklists include explicit acknowledgement of the comms protocol. Reinforcement in supervisor training (Aug 1st-week). Project Coordinator monitors for drift and corrects in-channel; Project Lead intervenes if drift becomes structural.

### 8.7 Hot-fix cadence not yet stress-tested

- **Gap:** The hot-fix protocol — CAPI Developer regenerates → CSWeb Admin redeploys → STLs notified → tablets sync the new PFF — has been described but not exercised end-to-end. The first real test will be a pretest finding.
- **Action:** Pretest is the dress rehearsal. Plan to stage a synthetic hot-fix during pretest (e.g., a deliberate skip-logic correction) to validate the chain time-to-deploy. Target: ≤24 hours from finding to all-tablet-rolled.

### 8.8 Patient Listing Form drift across sources

- **Gap:** Three sources describe the F3b Patient Listing Form / Protocol with non-trivial differences: (a) the original [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3b Patient Listing Protocol|Annex F3b Patient Listing Protocol]] (Apr 20) with the CSPro random-interval generator; (b) the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Survey Manual Working File (2026-05-06 Kidd)|Survey Manual Working File (May 6)]] which reverts to per-patient-random-interval; (c) the minimal paper template in [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Survey Manual Appendix F — Patient Listing Form|Appendix F — Patient Listing Form]] missing randomization metadata, eligibility flags, survey-tag, and listing_id.
- **Why it matters:** Three different form realities means three different STL training paths. SEs in the field will follow whichever copy they last saw.
- **Owner:** Survey Manager + CAPI Developer co-own the resolution. Survey Manager makes the methodology call; CAPI Developer implements the chosen path in the random-interval generator + the paper backup template.
- **Action:** Reconcile before pretest. Single canonical Patient Listing Form artefact (digital + paper) lands in this guide's [[03-Phase-3-5-Spec-and-Generators|Phase 3–5 spec]] reference set.

### 8.9 Questionnaire numbering variant — 12-digit case ID

- **Gap:** The [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Questionnaire Numbering Convention|case-ID convention]] adopted 2026-05-05 partitions the last 5 digits as `-FF-CCC` (Facility 2 + Case-per-facility 3). The May 6 Working File splits the last 5 as `-CC-CCC` (respondent-type 2 + sequence-per-type 3) using doubled-digit codes 11/22/33/44. These are not compatible.
- **Owner:** CAPI Developer (Carl) holds the technical authority — the brief at `deliverables/Survey-Manual/Case-ID-Convention-Brief_2026-05-05.{md,docx}` is canonical for the technical implementation. Project Coordinator (Juvy) holds the routing — the brief was prepared for Kidd and needs Project-Lead-level alignment before the manual locks.
- **Action:** Brief is delivered; Project Lead + Project Coordinator + Kidd reconcile against the Working File body. CAPI Developer does not implement the Working File variant; if the team chooses it, the brief is regenerated and the F1/F3/F4 generators + F2 PWA case-ID issuer are updated in lockstep.

### 8.10 IDinsight / Year-1 reference contact

- **Note:** [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/IDinsight|IDinsight]]'s Mr. Alec Lim is the Year 1 reference contact. Useful for: comparison-with-Year-1 questions; SurveyCTO-vs-CSPro implementation differences; respondent-population behavior baselines. Not a project role per se, but an outbound-info source the Survey Manager + CAPI Developer can call on. Routing: through Project Coordinator if formal, direct if methodological-cross-check.

---

## 9. Inter-role cadences and meeting rhythm

The roles and handoffs in §2–§4 only work if the roles meet on a predictable cadence. This section captures the standing meeting rhythm that gives the handoffs places to happen.

### 9.1 Standing meetings

| Cadence | Meeting | Attendees | Owned by | Output |
|---|---|---|---|---|
| Daily (during fieldwork) | Cluster STL sync | STL + SEs in cluster | STL | Cluster sync log; same-day anomalies |
| Daily (during fieldwork) | CSWeb morning check | CSWeb Admin | CSWeb Admin | Sync stats; anomaly list to Field Manager |
| Daily (09:00 MNL, fieldwork rounds) | `#capi-fieldwork-uat` Slack digest | Project Coordinator, CAPI Dev, CAPI QA, Field Manager, STLs | Automation (per F2 pattern) | Digest post |
| Weekly | Field Manager → Project Coordinator status | Field Manager, Project Coordinator | Project Coordinator | Cluster-level status roll-up |
| Weekly | CAPI Dev / CAPI QA bench loop | CAPI Dev, CAPI QA | CAPI Dev | Bug list closure; next-build target |
| Bi-monthly | Project Coordinator → DOH-PMSMD status | Project Lead, Project Coordinator, DOH counterpart | Project Coordinator | Formal status submission |
| Event-driven | LSS Meeting (Lessons-Learned Session) | Full ASPSI team | Health Policy / LSS Convener | LSS minutes; tasking outputs |
| Tranche-end | Internal pre-submission review | Project Lead, Survey Manager, Project Coordinator, CAPI Dev | Project Lead | Submission package signed off |
| Phase-9 | Pretest debrief | All ASPSI roles + STLs | Survey Manager | Pretest findings; iteration backlog |

### 9.2 Notes on cadence

- **Daily cluster sync (STL):** end-of-fieldwork-day, ~30 minutes per cluster. SEs report case counts, refusals, replacement requests, app issues.
- **CSWeb morning check (CSWeb Admin):** before STLs start their day, ~15 minutes. Verifies the previous night's 10 PM upload landed cleanly across all clusters.
- **Daily Slack digest:** automated, no human owner — fires only when a UAT or fieldwork round is active. Stops automatically when the round closes.
- **Weekly bench loop (CAPI Dev / CAPI QA):** during Phase 6–7 build phase, this is the primary review cadence for Carl-Shan handoffs.
- **Bi-monthly DOH status:** per the Apr 13 Team Communication Protocol "Other Matters" — formalized cadence for the Project Coordinator's outbound submissions.
- **LSS Meeting:** event-driven (post-Tranche, post-pretest, post-major-finding). The Apr 13 LSS established the comms protocol; the next LSS is expected post-pretest.

### 9.3 What goes in a status update

For Carl's bi-monthly status to Juvy (which Juvy may forward to DOH), the format is:

1. **Build state per instrument** — F1, F3, F4, F2 lines with current dictionary/FMF/APC/PFF status; bench-test status.
2. **Decisions taken since last update** — specs adopted, generators changed, naming-conventions locked.
3. **Open blockers** — what is waiting on whom (with clear "owned by Juvy / owned by Survey Manager / owned by CSWeb Admin" tags).
4. **Risks surfaced** — anything new in §8 of this guide.
5. **Next-period targets** — concretely what lands in the next two weeks.

This is the format intended for the E0-010 status-format deliverable referenced in the Apr 13 protocol.

---

## 10. Authority matrix for common decisions

Where decisions blur across multiple roles, this matrix names the authoritative voice. Use it when in doubt.

| Decision | Authoritative voice | Consults |
|---|---|---|
| Add an item to the questionnaire | Survey Manager (sign-off); LSS Convener (health-policy items) | CAPI Dev (cost), Project Lead (scope) |
| Remove an item from the questionnaire | Project Lead (sign-off); Survey Manager (methodology call) | LSS Convener, CAPI Dev, ADB |
| Change a HARD validation to SOFT | CAPI Dev (technical) **with** Survey Manager (methodology) | LSS Convener if health-policy weighted |
| Change a value set | CAPI Dev (technical generator change) | Survey Manager, LSS Convener |
| Add a CSWeb user | CSWeb Admin | Project Coordinator (provisions credentials handoff) |
| Add a CSWeb role | CSWeb Admin | CAPI Dev (technical sanity), Project Lead (audit policy) |
| Hot-fix push to all tablets | CAPI Dev (regen) **and** CSWeb Admin (deploy) **and** Field Manager (notify) | Project Coordinator (notification cover) |
| Pause data collection in a cluster | Field Manager (operational) **and** Survey Manager (methodology) | Project Lead |
| Replace a facility (within cap) | STL → Field Manager (cluster-level) | Survey Manager |
| Replace a facility (over cap) | Survey Manager → Project Lead | Field Manager |
| Send to DOH | Project Coordinator (Juvy) | Project Lead (Claro), Survey Manager (Paunlagui) |
| Decline a DOH change request | Project Lead | Project Coordinator, Survey Manager, CAPI Dev |
| Sign off Tranche bundle | Project Lead | Survey Manager, Project Coordinator |
| Accept a comment matrix from DOH | Project Coordinator (assemble response) | Project Lead, Survey Manager, CAPI Dev (technical responses) |
| Convene an LSS | Health Policy / LSS Convener | Project Lead, Survey Manager |
| Stop the project | Project Lead | DOH-PMSMD; ASPSI President |

This matrix is intentionally redundant with §3 RACI — RACI shows phase-by-phase responsibility, this matrix shows decision-by-decision authority. Use whichever lens fits the question.

---

## Next

- [[02-Phase-0-2-Foundation|02 — Phase 0–2: Foundation]] — applies the role definitions in this guide to the early phases (project scaffolding, source ingestion, tool knowledge base).
- [[99-Quick-Reference|99 — Quick Reference]] — one-page summaries per role (STL, SE, CSWeb Admin) suitable for printing or pinning to a Slack channel.

Cross-references:

- [[CAPI-Development-Workflow|CAPI Development Workflow (template)]] — the canonical 12-phase workflow this guide orchestrates.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Team Communication Protocol|Team Communication Protocol]] — the source for §6.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Forward-Only Sign-Off|Forward-Only Sign-Off]] — the source for the bug-routing rules in §5.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/LSS Meeting|LSS Meeting]] — the convening discipline that surfaces lessons-learned into role-and-process amendments.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - ASPSI Team Meeting 2026-04-13|Apr 13 ASPSI Team Meeting]] — establishing meeting for the comms protocol.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - ASPSI Team Meeting 2026-05-04|May 4 ASPSI Team Meeting]] — June 12 CAPI completion target + August training plan + 7-dialect translation list.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Survey Manual Working File (2026-05-06 Kidd)|Survey Manual Working File (May 6)]] — the live ASPSI Survey Manual; receives Carl's CAPI inputs through this guide's handoff matrix.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex D Replacement Protocol|Annex D Replacement Protocol]] — STL / Field Manager / Survey Manager enforcement rules.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex H Informed Consent Forms|Annex H Informed Consent Forms]] — SE-on-tablet verbatim text.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSWeb Users Guide|CSWeb Users Guide source page]] — authoritative reference for the CSWeb permission model invoked in §2.10.

Mentor citations:

- **(Khurshid 2022-05-05)** — CSWeb roles model (administrator / standard user / custom); add a CSWeb user; `synchronize_file()`; import value labels for CSWeb sync reports via CSV.
- **(Khurshid 2023-09-21)** — Reformat-Data SOP, invoked in §5.3 (schema-bug discovery).

---

*End of 01 — Roles and Handoffs.*
