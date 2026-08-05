---
title: F2 (HCW Survey) Admin Portal — Feature Audit & Gap Analysis
date: 2026-07-15
author: Carl Patrick Reyes (Analytiflow) — for ASPSI-DOH UHC Y2
status: Audit / analysis — no build actions taken
scope: F2 HCW Survey PWA admin console (uhc-hcw.asiansocial.org/admin)
verdict: Pretest-ready as-is; gaps are rollout-hardening backlog, none block pretest
---

# F2 Admin Portal — Feature Audit & Gap Analysis

**What this is.** A structured audit of the F2 (Healthcare-Worker Survey) admin portal:
(1) a map of what it does today, drawn from the source; (2) a best-practice reference model
for what a survey data-collection admin console *should* have, anchored to standards and to the
market-leading tools; (3) a feature-by-feature comparison against those tools; and (4) a
prioritized gap analysis with recommendations.

**What this is not.** This is not a build. Nothing here changes the instrument. **F2 is
pretest-ready as it stands** — the 2026-07-15 on-device bench test proved the whole operation
end-to-end (provision → enrol → consent → survey → submit → sync → monitor, plus the refusal
path). Every gap below is **rollout-hardening backlog for the full DOH deployment**, not a
pretest blocker. Carl decides what, if anything, to act on.

**Why it matters for this survey specifically.** F2 collects data from healthcare workers for a
DOH survey. Under the Philippine Data Privacy Act (RA 10173), personal + health-adjacent data is
**Sensitive Personal Information (SPI)** and the admin console is held to the strictest governance
tier. That reframes the audit: the sharpest gaps are not "missing features" — they are
**compliance and data-stewardship capabilities** an SPI-processing system is expected to support.

---

## 0. Executive summary

**Bottom line:** F2's admin portal is **CSWeb's console pattern with the operational middle filled
in.** It shares CSWeb's exact 5-dashboard IA (Data · Report · Apps · Users · Roles) and its
per-dashboard + per-dictionary role model — then adds the real data grid, dead-letter recovery,
kill switch, broadcast, versioning, and paper-encode that CSWeb (a thin sync-relay) lacks. In
several dimensions it **exceeds every mainstream CAPI platform**, and in one it is genuinely
**ahead of all of them**. Its gaps cluster in one place: **analyst-facing data handling** —
getting governed data out (export, API), correcting it, and honouring data-subject rights.

| | Count | Examples |
|---|---|---|
| **Above-standard strengths** | 9 | DLQ+replay *(unique — 0/7 CAPI tools have it)* · **console-level consent + refusal capture** *(0/7 have it)* · 11-dimension RBAC · kill switch / quota / broadcast · dual-mode (device+paper) entry · proven offline sync · versioning · map monitoring · audit log |
| **P1 — compliance / data-integrity gaps** | 5 | analyst export path · DSAR (locate/export/erase a subject) · consent-version record durability · retention & disposal policy · export-time de-identification |
| **P2 — operational / QC gaps** | 4 | in-console review/correction workflow *(table-stakes: 6/7 have it)* · AAPOR disposition-coded rates · per-actor progress KPIs · GPS-vs-assignment check |
| **P3 — analytics / integration** | 3 | in-portal analytics (freq/crosstab/trend) · read/OData API for BI · SSO / IP allowlisting |

**The one gap I'd flag hardest:** there is **no working analyst-facing data-export path** in the
reviewed build (no ad-hoc download; the scheduled break-out generator is stubbed — see §1.4).
Ad-hoc export and a REST data-pull API are the two things **all 7** benchmarked CAPI platforms
ship — they are the definition of table-stakes. For a survey whose entire purpose is to produce a
dataset, "how does clean data get to the statistician" is the first question a reviewer will ask.
This is the highest-value, most-defensible thing to close before rollout — and it is not hard.

---

## 1. Current-state map (from source)

Verified against the F2 server (`deliverables/F2/PWA/server/src/admin/`) and the admin web app
(`.../app/src/…/admin`), 2026-07-15.

### 1.1 Information architecture

```
F2 Admin Portal (uhc-hcw.asiansocial.org/admin)
│
├── OPERATE
│   ├── Data            dash_data
│   │    ├── Responses (submissions table)        list · detail (read-only)
│   │    ├── HCW registry                          create · mint / reissue enrolment token
│   │    ├── Audit log                             who/what/when
│   │    └── Dead-letter queue (DLQ)               failed submissions · replay · purge
│   ├── Reports         dash_report
│   │    ├── Sync / coverage report                enrolled vs submitted vs pending
│   │    └── Map report (Leaflet)                  geographic submission monitoring
│   └── Encode          dash_data
│        └── Paper-questionnaire transcription     office data entry for paper HCWs
│
├── CONFIGURE
│   ├── Apps & Settings dash_apps
│   │    ├── Versioning                            build version surfaced to devices
│   │    ├── Files                                 upload / folders / delete (100 MB cap)
│   │    ├── Data Settings                         scheduled break-out export config + run-now
│   │    ├── Quota                                 Apps-Script daily-cap widget (20k)
│   │    ├── Broadcast                             message push to field devices (≤280 char)
│   │    └── Kill switch                           disable submissions platform-wide
│   ├── Users           dash_users
│   │    ├── CRUD · bulk import                    letters-only names, pw ≥ 8
│   │    └── Revoke sessions                       force logout
│   └── Roles           dash_roles
│        └── RBAC editor                           11 permission dimensions (below)
│
└── CROSS-CUTTING
     ├── Login / logout · change-password (forced-change gate)
     ├── Session management (JTI + per-user revocation)
     ├── SJREB informed-consent gate + refusal capture
     └── Offline-first PWA sync (client outbox → Sync now)
```

### 1.2 Admin API surface (≈40 endpoints, all RBAC-gated)

| Area | Endpoints (representative) | Gate |
|---|---|---|
| Auth / self | `POST /login` · `POST /logout` · `PATCH /me/password` | — / forced-change |
| Data | `GET /dashboards/data/responses` · `…/responses/:id` (read-only) · `…/audit` · `…/dlq` · `POST …/dlq/:id/replay` · `DELETE …/dlq/:id` · `…/hcws` | `dash_data` |
| Encode | `POST /encode/:hcwId` | `dash_data` |
| Reports | `GET /dashboards/report/sync` · `…/report/map` | `dash_report` |
| Apps | `…/apps/version` · `…/apps/quota` · `…/apps/kill-switch` (GET/PATCH) · `…/apps/broadcast` (GET/PATCH) · `…/apps/files` (GET/POST/PATCH/DELETE + folders) · `…/apps/data-settings` (GET/POST/PATCH/DELETE + run-now) | `dash_apps` |
| Users | `…/users` (GET/POST) · `…/users/bulk-import` · `…/users/:u` (PATCH/DELETE) · `…/users/:u/revoke-sessions` | `dash_users` |
| Roles | `…/roles` (GET/POST) · `…/roles/:name` (PATCH/DELETE) | `dash_roles` |
| HCW provisioning | `POST /hcws` · `POST /hcws/:id/reissue-token` | `dash_data` |

### 1.3 RBAC model — 11 permission dimensions

Enforced by `requirePerm()` → cached-role version check with authoritative refetch on mismatch,
plus JTI + per-user token revocation and a forced-password-change gate that bars every
RBAC-guarded route.

- **5 module flags** (dashboard access): `dash_data`, `dash_report`, `dash_apps`, `dash_users`, `dash_roles`
- **6 data-source × direction flags** (which data streams a role may see/act on):
  `dict_self_admin_up/down`, `dict_paper_encoded_up/down`, `dict_capi_up/down`

This is **finer-grained than most survey platforms**, which stop at project-level roles. F2 can
say "this role may read self-administered submissions but not paper-encoded ones" — a genuine
differentiator (see §3).

### 1.4 Data-handling reality (the important nuances)

- **Submissions are immutable in the console.** `responses` and `responses/:id` are GET-only.
  There is no edit, correct, or delete endpoint for accepted submissions. Corrections today mean
  DB-level work (this is what Shan's #831 removal required).
- **No ad-hoc export.** There is no "download filtered responses as CSV/Excel" action.
- **Scheduled break-out export is configured but not running in this build.** `data-settings`
  lets you define scheduled break-outs and stamp `run-now`, but the source explicitly notes the
  cron generator "is NOT ported… rows are due-stamped but no cron consumes them yet." So the
  analyst-facing export path is, in practice, **absent** in the reviewed build.
- **No live external / OData API** for pulling data into analysis tools.
- **Consent is captured** as `consent_given` + `consent_timestamp`; refusals are recorded
  server-side as `status=refusal` even though nothing is kept on the device (verified in the
  bench test). What is *not* evident is durable storage of the **consent-text version** as an
  auditable artifact (see gap P1-C).

---

## 2. Best-practice reference model — what a survey admin console should have

Synthesized from the market-leading tools (§3) and the governing standards. Two tiers:
**must-have** (table stakes / compliance) and **advanced** (differentiators). Anchors in
brackets.

### 2.1 MUST-HAVE (table stakes / compliance)

| # | Capability | F2 today | Anchor |
|---|---|---|---|
| M1 | Granular RBAC + least privilege | ✅ **exceeds** (11 dims) | ISO 27001 A.5.15; REDCap/Qualtrics |
| M2 | Comprehensive audit log (view/edit/export/delete, tamper-protected, exportable) | ◑ has audit log; verify it logs **exports & views**, and that it's exportable | ISO 27001 A.8.15; REDCap |
| M3 | Encryption in transit + at rest | ◑ HTTPS in transit; at-rest posture to confirm/document | RA 10173 IRR §28; NPC 16-01 |
| M4 | Treat health/personal data as SPI (restrict, tag, minimize) | ◑ RBAC restricts; no field-level PII tagging | RA 10173 (SPI incl. health) |
| M5 | Consent as an auditable record (state + timestamp + **text version**, retained) | ◑ state+timestamp yes; **version retention** = gap | 45 CFR 46.115/.116; REDCap e-Consent |
| M6 | Data-subject request support: locate → export → correct → erase an individual | ✗ **gap** | RA 10173 rights; GDPR 15/16/17/20 |
| M7 | Configurable retention + secure disposal (with research ≥3-yr hold) | ✗ **gap** | 45 CFR 46.115; RA 10173 IRR |
| M8 | Multi-format export **with metadata** — CSV/Excel + Stata/SPSS/SAS + codebook | ✗ **gap** (no working export) | DDI / BLS; REDCap export |
| M9 | Standard disposition coding → AAPOR outcome rates (RR/COOP/REF/CON) | ◑ enrolled/submitted/pending/refusal counts; not AAPOR-coded | AAPOR Standard Definitions |
| M10 | Field-level validation at entry (type/range/format/consistency) | ✅ (instrument-side; required-banner #809) | REDCap; DIME HFC |
| M11 | Duplicate detection & resolution on a stable case key | ◑ QN partition prevents collisions; no dedup **surface** | DIME; iefieldkit |
| M12 | DPO accountability + breach-response readiness + NPC registration/PIA | ◑ org/process, not a console feature — flag for the engagement | RA 10173 IRR §26; NPC 17-01 |
| M13 | Data minimization / purpose limitation in what's collected & exposed | ✅ (lean instrument; RBAC-scoped exposure) | RA 10173; GDPR |

### 2.2 ADVANCED (differentiators)

| # | Capability | F2 today | Anchor |
|---|---|---|---|
| A1 | De-identified / anonymized export mode (strip identifiers, date-shift) | ✗ | REDCap de-id; 45 CFR 46.111 |
| A2 | Query / data-resolution workflow (flag → assign → track to closure) | ✗ | REDCap Data Resolution Workflow |
| A3 | Double / independent entry + comparison | ✗ (single paper-encode path) | REDCap Double Data Entry |
| A4 | Live fieldwork dashboard + field-check tables (per-actor productivity, duration outliers, item-missingness) | ◑ coverage + map; not per-actor KPIs | DHS FCTs; DIME HFC |
| A5 | Back-check / re-interview module (random 10–20% sub-sample) | ✗ (lower priority for HCW census) | DIME Back Checks |
| A6 | GPS/location verification vs assignment | ◑ map shows points; no automated flag | DIME; IRI |
| A7 | SSO + IP allowlisting + API access controls | ✗ (bearer-token admin auth) | Qualtrics; SurveyMonkey Enterprise |
| A8 | Field-level access tags/roles (view vs edit vs export per sensitive field) | ◑ stream-level, not field-level | Qualtrics data-access roles |
| A9 | Divisions / org-unit scoping (facility/region sees only its own) | ◑ RBAC + facility filter; not formal org-scoping | Qualtrics Divisions |
| A10 | Kill switch / quota / broadcast / versioning (operational safety) | ✅ **exceeds** | (rare in survey tools) |

Legend: ✅ present/strong · ◑ partial · ✗ absent.

---

## 3. External-tool comparison

F2 against the seven platforms a reviewer would benchmark against — using the same 15-feature
admin-console taxonomy as the cited platform research (official docs only; see §6). F2 is
purpose-built and single-instrument; the others are general platforms — so a "✗" often reflects
*scope choice*, not immaturity.

Legend: `Y` present · `~` partial/indirect/add-on · `N` absent · `n/a` not applicable to F2's design.

| # | Admin-console feature | **F2** | ODK Central | SurveyCTO | KoBo | Ona | Survey Sol. | CommCare | CSWeb |
|---|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| 1 | User & role management (RBAC) | **Y** (11-dim) | Y | Y | Y | Y | Y | Y | Y |
| 2 | Submission table: view/filter/**edit**/delete | ~ (view only) | Y | Y | Y | Y | Y | Y | **N** |
| 3 | Ad-hoc multi-format **export** | **N** (stubbed) | Y | Y | Y | Y | Y | Y | ~ |
| 4 | **REST/OData API** for data pull | **N** | Y (OData) | Y | Y | Y | Y (+GraphQL) | Y | Y (sync) |
| 5 | Fieldwork monitoring dashboards | ~ (coverage) | ~ | Y | ~ | ~ | Y | Y | ~ |
| 6 | Geographic / **map** monitoring | **Y** | Y | Y | Y | Y | Y | Y | Y |
| 7 | Automated data-quality flags (dup/GPS/outlier) | ~ | ~ | **Y** | ~ | ~ | ~ | ~ | N |
| 8 | Case / **assignment** dispatch | n/a (census) | ~ | Y | N | ~ | **Y** | Y | ~ |
| 9 | Submission **deduplication** engine | ~ (key+idempotency) | ~ | ~ | ~ | ~ | ~ | **Y** | N |
| 10 | **Audit trail** / edit log | **Y** | Y | ~ | Y | Y | Y | Y | ~ |
| 11 | PII / encryption / access control | ~ | Y | Y | Y | Y | ~ | Y | ~ |
| 12 | Offline sync + session mgmt | **Y** | ~ | Y | ~ | ~ | Y | Y | Y |
| 13 | Form/version mgmt + update push | **Y** | Y | Y | Y | Y | Y | Y | Y |
| 14 | **Paper/office** web data entry | **Y** | Y | Y | Y | Y | Y | Y | N (n/a) |
| 15 | **Broadcast** / notify field devices | **Y** (≤280c) | N | ~ | ~ | ~ | ~ | **Y** | N |
| + | **Dead-letter queue + replay** | **Y** | N | N | N | N | N | N | N |
| + | Console-level **consent + refusal** capture | **Y** | N | N | N | N | N | N | N |
| + | **De-identified** export mode | N | ~ | ~ | N | ~ | ~ | Y | N |
| + | **DSAR** (locate/export/erase a subject) | N | N | N | ~ | N | N | ~ | N |

**Reading the matrix:**
- **F2 wins outright** on two rows *no CAPI platform has at all* — **DLQ + replay** and
  **console-level consent/refusal capture** (across all 7, consent is a form-design construct, not
  a console feature). It also leads on **broadcast** (only CommCare matches), RBAC granularity, and
  first-class **paper-encode** (CSWeb, its closest sibling, lacks it entirely).
- **F2 trails on exactly one cluster** — rows 2–4, **getting governed data in and out**: no
  in-console edit/review, no ad-hoc export, no data-pull API. Ad-hoc export and a REST API are
  **7/7 table-stakes**; this is the clearest, least-controversial gap.
- **F2 vs CSWeb (its lineage):** CSWeb is "the outlier — a thin sync-relay missing the
  operational-management middle (rows 2, 7, 9, 14, 15) but strong on plumbing (12, 13)." **F2 is
  CSWeb with that middle built in** — it fills the data grid, paper-encode, broadcast, and adds DLQ
  and consent on top. The one place F2 *didn't* out-build CSWeb is export/API, where CSWeb at least
  has a REST sync feed and a MySQL break-out. That's precisely the gap to close.
- **The health/PHI analogues** — CommCare (HIPAA + signed BAA, dedup engine, de-identified
  exports, 6-yr audit) and, in the research world, **REDCap** (e-consent, de-id export, audit of
  views/exports) — are the benchmarks for the compliance features in §4's P1. They're the closest
  analogues to F2's DOH/SPI context.

---

## 4. Gap analysis (prioritized)

Priority reflects **DOH/SPI compliance and data-integrity risk first**, then operational value,
then nice-to-have — and is weighted for F2's actual shape (complete-enumeration HCW census,
largely self-administered).

### P1 — compliance / data-integrity (close before full rollout)

**P1-A · No working analyst-facing export path.** *(M8)*
No ad-hoc download; scheduled break-out generator stubbed. For a survey whose deliverable *is* a
dataset, this is the highest-value fix. → **Add an export the console can trigger**: filtered
responses → CSV/Excel now; labeled Stata/SPSS with a codebook next. Effort: **S–M**.

**P1-B · No data-subject-request (DSAR) support.** *(M6)*
RA 10173 gives subjects rights to access, rectify, erase/block, and port their data; the console
can't locate → export → correct → delete one person's record. → **A "find HCW → view/export/erase"
admin action** (Qualtrics-style). Effort: **M**. *(Ties to P2-A correction workflow.)*

**P1-C · Harden the consent lead: retain the consent-text version.** *(M5)*
This is F2 building on a strength, not fixing a deficiency — **console-level consent/refusal
capture is something 0/7 CAPI platforms have.** Today `consent_given` + timestamp are stored; to
make it audit-grade for SJREB, also stamp the *version of the consent text the subject saw* onto
each case (the spec already versions — store the consent-doc version alongside). Effort: **S**.

**P1-D · No retention & secure-disposal policy in the system.** *(M7)*
No configurable retention window or disposal action, and no research-retention hold (≥3 yr
post-study). → **A retention setting + documented disposal path** (even if manual initially).
Effort: **S** (policy) / **M** (automation).

**P1-E · No export-time de-identification.** *(A1)*
Analyst and ethics-board datasets should be producible with identifiers stripped / dates shifted.
→ Fold into P1-A as a **"de-identified export" mode**. Effort: **S** on top of P1-A.

### P2 — operational / QC (rollout value)

**P2-A · No in-console review/correction workflow.** *(table-stakes 6/7; cf. A2)*
Submissions are GET-only; fixing a bad value means DB surgery. A **review/validation status**
(approve / reject / on-hold) is now **table-stakes — 6/7 platforms have it** (only CSWeb, F2's
thin-relay sibling, doesn't), and field-level **correct-on-server with a correction log** is the
SurveyCTO/REDCap benchmark. → At minimum a **supervised single-field correction with audit**;
ideally a status + query-resolution queue. Effort: **M–L**. *(Highest-value P2 item.)*

**P2-B · No AAPOR disposition-coded outcome rates.** *(M9)* Counts exist (enrolled / submitted /
pending / refusal); formal disposition codes + RR/COOP/REF/CON don't. Aligns F2 reporting with
F1/F3/F4 and the survey manual. → **Compute standard rates from a uniform per-case disposition.**
Effort: **S–M**.

**P2-C · No per-actor progress KPIs / field-check-table view.** *(A4)* Coverage + map exist;
per-coordinator productivity, duration outliers, item-missingness don't. *Lower priority for F2*
(self-administered census, less enumerator-fraud surface than household surveys). Effort: **M**.

**P2-D · GPS captured but not verified against assignment.** *(A6)* Map plots points; nothing
flags "all submissions from one spot." *Lower priority for F2* (facility-fixed, self-admin).
Effort: **M**.

> **Not a gap — duplicate handling is already at parity.** QN partitioning + `client_submission_id`
> idempotency put F2 in line with 6/7 platforms; a *true dedup engine* (property-match rules +
> merge/close) exists only in CommCare. Worth a "possible duplicates" list eventually, but F2 is
> not behind here.

### P3 — analytics / integration (nice-to-have)

**P3-A · No in-portal analytics** beyond coverage + map (no frequency tables, crosstabs,
trend-over-time). → Coordinators export to analyse today; fine short-term. Effort: **M–L**.

**P3-B · No live external / OData API.** → Once P1-A exists, an OData/REST read feed lets analysts
connect BI tools directly. Effort: **M**.

**P3-C · No SSO / IP allowlisting.** → Enterprise-grade; likely overkill for this deployment.
Effort: **M**. *Recommend: defer.*

---

## 5. Recommendations & sequencing

**Nothing here blocks tomorrow's pretest.** F2 is proven end-to-end on-device. Treat this as the
rollout-hardening backlog and sequence by compliance value ÷ effort:

1. **Before full rollout (compliance-critical, mostly small):**
   **P1-A** working export (+ **P1-E** de-id mode) → **P1-C** consent-version stamp → **P1-D**
   retention policy → **P1-B** DSAR action. This is the defensible core for an SPI-processing DOH
   system, and most of it is S/M effort.
2. **Early in rollout (data-quality):** **P2-A** supervised review/correction workflow (closes a
   table-stakes gap) → **P2-B** AAPOR-coded rates (aligns F2 with F1/F3/F4).
3. **Consider / defer:** **P2-C/D** (lower priority given F2's census shape) · **P3** analytics &
   API once export exists · **P3-C** SSO — defer.
4. **Engagement-level, not console features:** **M12** — designate the DPO, confirm NPC
   registration + PIA for the survey, document encryption-at-rest and the breach-notification path.
   Worth raising with ASPSI as the data controller regardless of console features.

**F2's strengths to preserve and publicize:** the DLQ+replay, 11-dimension RBAC, kill switch /
quota / broadcast, dual-mode entry, and proven offline sync are real assets — several exceed the
commercial tools. The audit's message is not "F2 is behind"; it's "F2 is strong, with a specific,
closeable gap in *getting governed data out*, and a compliance checklist worth completing because
this is DOH health data."

---

## 6. Sources

**Standards & governance:** AAPOR Standard Definitions (10th ed.) · ISO/IEC 27001:2022 Annex A
5.15 (access control) & 8.15 (logging) · PH Data Privacy Act RA 10173 + IRR Rule VI §26–28 (NPC) ·
NPC Circular 16-01 (gov data security) & 17-01 (registration threshold) · 45 CFR 46 Common Rule
§46.111/.115/.116 (consent docs, ≥3-yr retention) · GDPR Arts. 15/16/17/20 (data-subject rights).

**Fieldwork QC:** World Bank DIME Wiki (High-Frequency Checks, Back Checks, Monitoring Data
Quality) · DHS Program MR30 / Supervisor-Editor Manual (field-check tables) · US BLS PUMD + DDI
(export-format standards) · IRI Survey QC.

**Platform admin feature sets** (official docs, cite-or-NOT-FOUND):
- REDCap — projectredcap.org technical overview; UW-Madison KB; Harris et al. 2009
- Qualtrics — permissions, data-access, security, data-privacy pages
- SurveyMonkey — enterprise admin, roles, HIPAA
- ODK Central — docs.getodk.org (central-users, -submissions, -api, -entities, -server-audits, -encryption, -forms)
- SurveyCTO — docs.surveycto.com (user-roles, reviewing-and-correcting, export-options, api-access, monitoring-quality, case-management, encrypting, device-security)
- KoBoToolbox — support.kobotoolbox.org (managing-permissions, viewing-validating-data, export-download, api, synchronous-exports, mapping-gps, activity-logs, is-my-data-safe)
- Ona — api.ona.io static docs (projects, data, forms, submission_review, submission_stats, entities, orgs, restservices)
- World Bank Survey Solutions — docs.mysurvey.solutions (account-types, workspaces, survey-workflow, data-export-tab, api, reports-tab, supervisor-map-dashboard, assignment_status, audit-log, web-interviewing)
- Dimagi CommCare — dimagi.atlassian.net/wiki (roles-permissions, submit-history, DET, data-apis, worker-monitoring, geospatial, dedup, case-sharing, HIPAA, web-apps, conditional-alerts)
- CSPro CSWeb — csprousers.org/help/CSWeb (adding_roles, accessing_data, data_settings, sync_report, map_report, production) + github.com/csprousers/csweb (swagger)

**Fieldwork QC & standards:** AAPOR Standard Definitions 10th ed. · DIME Wiki (HFC / Back Checks /
Monitoring Data Quality) · DHS MR30 & Supervisor-Editor Manual · BLS PUMD + DDI · ISO 27001:2022
Annex A 5.15/8.15 · RA 10173 + IRR (NPC) · NPC Circ 16-01/17-01 · 45 CFR 46 · GDPR Arts. 15/16/17/20.

**Current-state (primary):** F2 server `deliverables/F2/PWA/server/src/admin/{routes,rbac,store,
auth,reports}.ts`; F2 admin web app; F2 bench-test report 2026-07-15.

*Full URL-level citations are held in the research working notes and can be appended on request.*
