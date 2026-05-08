---
title: "07 — Phase 9-10: Pretest and Fieldwork"
category: deliverable
tags: [capi, cspro, csweb, pretest, fieldwork, ops, uhc-y2]
last_updated: 2026-05-08
status: draft
---

# 07 — Phase 9 (Pretest / UAT) and Phase 10 (Production Fieldwork Support)

This chapter covers the two field-facing phases of the UHC Year 2 CAPI workflow:

- **Phase 9** — Pretest / UAT and field readiness. Validates the F1 / F3 / F4 instruments and applications against real enumerators on real cases before the SJREB-cleared main fieldwork begins.
- **Phase 10** — Production fieldwork support. Keeps the data flowing for the duration of the main collection: daily sync, hot-fix discipline, batch editing, interim tabulation, replacement-protocol enforcement.

Phases 0–8 are upstream (see [[02-Phase-0-2-Foundation]] through [[06-Phase-8-CSWeb-and-Tablets]]). Phase 11 is downstream — closeout and final export (see [[08-Phase-11-Closeout-Export]]).

This chapter also closes the **field-ops toolkit gap** surfaced in the May 2026 internal audit:

- Map Case Listing for STL GPS verification.
- CSV import to populate sync-report value labels.
- `publishdate()` force-update on stale builds.
- HTML reports for daily ops dashboards.
- Layout-controlled plain-text reports via `file_handler` + `filewrite`.

The Khurshid technique cards driving each toolkit item are cited inline.

---

## Phase 9 — Pretest / UAT and field readiness

**Objective.** Validate F1 / F3 / F4 instruments *and* their CAPI applications against real users in conditions that resemble the main fieldwork, then iterate fixes back through Phases 4–8 before the instrument and app are frozen for the August enumerator training.

**Inputs.**
- `.pen` builds for F1, F3, F4 (Phase 6 → Phase 8 packaged).
- CSWeb production server (Phase 8) configured with sync-report labels and FIELD_CONTROL.
- SJREB-cleared protocol V2 + informed-consent forms (Annex H).
- Pretest endorsement letters from DOH / LGU.
- 7-dialect translation bundles (see [[03-Phase-3-5-Spec-and-Generators]] and the i18n notes in [[04-Phase-6-Build-CAPI-App]]).

**Outputs.**
- Written pretest report classified by severity.
- Updated spec / dcf / fmf / apc reflecting pretest findings.
- Final Survey Manual (with Carl-authored CSPro install + sync sections).
- Approved supervisor + enumerator training materials.
- Tablets provisioned, labelled, and bench-tested for all enumerators.

### 9.1 SJREB ethics clearance — the long-pole blocker

The St. John's REB (SJREB) clearance is the single biggest schedule risk in the UHC Year 2 CAPI track. Nothing real can happen in the field — not pretest, not main fieldwork — until clearance is in hand. Carl is **not** the submitter; that goes through the Project Coordinator and Project Lead. But the CAPI app draft is part of the submission package, so Carl's deliverable readiness sits on the critical path.

#### 9.1.1 Regions and selection rationale

Per the ASPSI 2026-05-04 weekly meeting, three SJREB regions are confirmed for UHC Year 2 main fieldwork:

| Region | Rationale |
|---|---|
| NCR | Highly-urbanized, dense facility distribution, near-complete UHC integration; reference profile. |
| Region 8 (Eastern Visayas) | Geographically dispersed island provinces; tests low-connectivity sync flows (CSWeb daily, queued retries). |
| Region IV-B (MIMAROPA) | Mixed island/mainland; tests replacement protocol on hard-to-reach facilities. |

These three are submitted as the SJREB-bound regions. Region selection drives: stratified sample sizing, enumerator team composition, training cohort size, and tablet provisioning quantity.

#### 9.1.2 SJREB submission contents

The Project Coordinator owns assembly. Carl owns the CAPI app technical sign-off. Submission package:

| Artifact | Owner | Carl's contribution |
|---|---|---|
| Master Research Protocol V2 | Project Lead | Reviewed; called out CAPI-specific paragraphs (sync windows, GPS retention, tablet decommissioning). |
| Informed-consent forms — Annex H (F1, F3a, F3b, F4 versions) | Project Lead | Confirmed each form has a corresponding consent screen in FIELD_CONTROL with timestamp + interviewer ID capture. |
| Instruments (F1, F3, F4 + F2 PWA) | Project Lead | Carl: link to dcf v-current + apc v-current; F2 link goes to PWA staging URL. |
| Recruitment plan | Project Coordinator | n/a |
| Data security plan | Carl + Project Coordinator | Carl drafted: device encryption, sync-channel TLS, server access controls (per Khurshid 2022-05-05 CSWeb roles), case-ID pseudonymisation, retention windows, decommissioning checklist. |
| Pre-testing endorsement letters | Project Coordinator | n/a (separate from main IRB pack). |

The Data Security Plan is the single CAPI-Developer-authored attachment. Keep it living in `deliverables/Survey-Manual/Data-Security-Plan.md` and re-attach the latest version on each SJREB resubmission.

#### 9.1.3 Carl's role in the SJREB cycle

- **Provide**: working CAPI app draft (`.pen`), data security plan, technical clearance memo confirming the build matches Protocol V2's data-handling description.
- **Do not**: submit the package; respond directly to SJREB queries; sign protocol amendments.
- **Stay reachable**: SJREB query turnaround can be days, not weeks. Project Coordinator may need a same-day technical clarification (e.g. "where is the GPS stored?" — answer: FIELD_CONTROL / HEADER, never persisted off-tablet beyond CSWeb encrypted store).

#### 9.1.4 Pretest endorsement letters

Per the May 4 weekly update, pretest endorsement letters are **separate** from the main SJREB IRB submission. They go to:

- LPH-Bay District (the host district for Bay).
- LGU Los Baños (host LGU).
- Any participating private hospitals on the F1 / F3 list at those sites.

Carl supplies one paragraph per letter describing the CAPI tools the enumerators will use (CSEntry on Android tablet, GPS-tagged but not address-revealing, daily sync to CSWeb at https://csweb.aspsi-doh-uhc.example), so the host facility understands what consent looks like for the data flow. This text lives in `deliverables/Survey-Manual/Endorsement-Letter-CAPI-Paragraph.md` and is reused per host facility.

### 9.2 Pretest plan

Pretest is the cheap-bug-finding analogue for fieldwork: run the *whole* end-to-end pipeline at small scale, then read the bruises.

#### 9.2.1 Sites

- **Los Baños** (Laguna) — represents urban-fringe LGU; mixed public + private facility profile; strong-connectivity baseline.
- **Bay** (Laguna) — under LPH-Bay District; rural-fringe LGU; tests connectivity-degraded sync paths.

Both sites are 2-hour drive from Manila, which keeps the iteration loop tight when bugs surface and need same-week retest.

#### 9.2.2 Sample composition

10–30 cases per F-series across the two sites. Coverage targets:

| F-series | Cases | Coverage targets |
|---|---|---|
| F1 (Facility Head) | 10–15 | DOH-retained / LGU-devolved / private; both sites; at least one refusal triggered. |
| F3 (Patient — F3a + F3b composite) | 15–25 | OPD / inpatient / referral; at least one F3b patient-listing case to exercise the May-6 drift fix. |
| F4 (Household) | 15–20 | Urban household, rural household, mixed-cluster; at least one ineligible household to trigger replacement protocol. |

Total roughly 50–70 cases over one week of fieldwork. Sample size is **not** statistically meaningful — it's a stress test of the instrument and the app on real-world variability.

#### 9.2.3 Crew

- 2 STLs (Senior Team Leaders) — one per site.
- 6 SEs (Survey Enumerators) — three per site, rotating across F-series.
- Carl + Shan present at least one day per site for live observation.
- Survey Manager + Project Coordinator present for the debrief.

#### 9.2.4 Duration

- **Week 1** — fieldwork (Mon–Fri).
- **Week 2** — debrief (Mon morning), classification + triage (Mon afternoon), spec + app fixes (Tue–Wed), regen + bench retest (Wed–Thu), pretest report drafting (Thu–Fri).

Two-week pretest fits cleanly between SJREB clearance and the supervisor training in Aug-W1.

#### 9.2.5 Output — written pretest report

Stored at `deliverables/Pretest/Pretest-Report-<YYYY-MM-DD>.md`. Required sections:

1. Executive summary — go / no-go for main fieldwork.
2. Cases attempted vs completed by F-series and site.
3. Sync round-trip statistics (lag, failures, retries).
4. Issue log per F-series, **classified by severity** (Critical / High / Medium / Low) and **type** (Instrument / App UX / Sync-infra / Field-protocol / Translation).
5. Fixes applied during pretest week 2 (delta against pre-pretest build).
6. Open issues deferred to main-fieldwork hot-fix queue.
7. Translation findings per dialect.
8. Replacement-protocol observations.
9. Recommendations for training adjustments.

This report is the gate Carl + Project Coordinator + Survey Manager sign before the August enumerator training kicks off.

### 9.3 Enumerator pretest debrief

Pretest's most valuable output isn't the clean cases — it's the SE testimony. Capture every:

- "this question was confusing"
- "this skip felt wrong"
- "I wanted to enter X but couldn't"
- "the GPS didn't lock fast enough"
- "the tablet froze during sync"
- "the respondent kept asking what we meant by Y"

#### 9.3.1 Debrief format

Half-day group session at the end of fieldwork week. Two facilitators: Carl (CAPI side) + Survey Manager (instrument side). One scribe (Shan or Coordinator).

**Round 1 — open recall, 30 min.** Each SE shares the three things that frustrated them most. No filtering, no triage. Capture all into a flip chart or shared doc.

**Round 2 — F-series walk-through, 60 min.** Walk every section of every F-series. For each section ask: "anything weird? anything you skipped that you think you shouldn't have? anything you typed and the app rejected?".

**Round 3 — sync + tablet, 30 min.** Connectivity, sync timing, battery, tablet freezes, lost cases.

**Round 4 — field protocol, 30 min.** Replacement attempts, refusals, callback patterns, supervisor coordination.

#### 9.3.2 Categorisation

Every captured item gets a category, which routes the fix back to the right phase:

| Category | Routing |
|---|---|
| **Instrument bug** — questionnaire wording, missing option, wrong skip | Phase 4 spec update + Phase 5 regen → [[04-Phase-6-Build-CAPI-App]] |
| **App UX bug** — capture type wrong, screen too cramped, validation message confusing | Phase 6 wiring fix → [[04-Phase-6-Build-CAPI-App]] |
| **Sync / infra bug** — server reject, slow upload, missing dictionary | Phase 8 server config → [[06-Phase-8-CSWeb-and-Tablets]] |
| **Field-protocol gap** — replacement rule unclear, supervisor escalation path missing | Phase 9 manual update (this chapter §9.4) |
| **Translation bug** — wrong word, awkward phrasing, untranslated string | Phase 4 translation bundle update → [[04-Phase-6-Build-CAPI-App]] §i18n |

Severity assigned on a four-tier scale (Critical / High / Medium / Low), where:

- **Critical** — blocks fieldwork at all. Cannot ship without fixing.
- **High** — degrades data quality; ship without fixing only with mitigation in place.
- **Medium** — workable; fix in next planned hot-fix cycle.
- **Low** — cosmetic / nice-to-have; backlog.

### 9.4 Survey Manual contribution

Carl has already drafted the CSPro install section: `deliverables/Survey-Manual/CSPro-Section-Draft_2026-04-29.md`. The May 6 Working File integrates it into the master Survey Manual.

Three integration gaps Kidd's working file flagged on May 6, with how Carl handles them:

| Gap | Owner | Carl's response |
|---|---|---|
| **HCW self-admin guide missing (F2 PWA)** | F2 PWA team (not Carl) | Carl confirms the F2 PWA staging URL and its install-prompt screenshots are linked from the CAPI manual but does not author the F2 self-admin guide content — that belongs to the PWA lane. |
| **Bench-testing missing** | Carl | Cross-reference [[05-Phase-7-Testing]] § bench-test mock cases. The Survey Manual gets a short pointer; the canonical procedure stays in the testing chapter. |
| **Three-point sync simplified to one daily** | Carl | The original draft described morning-noon-evening sync; the May 6 working file simplifies to a single 22:00 MNL daily sync (Protocol V2 mandate). Carl revises the CSPro section to match — see §10.1 below. |

The Survey Manual sections Carl owns:

- **Tablet operation** — power on, login, GPS toggle, language toggle, battery management.
- **Daily sync procedure** — 22:00 MNL mandate, what to do if sync fails, when to escalate.
- **Resume-partial workflow** — STL view of partial cases (per Khurshid 2022-10-23 *Tutorial on forcase Statement*) + how to coach an SE to resume their own.
- **CSPro install** (already drafted 2026-04-29) — for fresh tablets, with screenshots.
- **What to do when** — common errors mapped to remediation.
- **Field issue escalation flow** — SE → STL → CSWeb Admin → Carl.

### 9.5 Training materials

Two training cohorts, one supervisor + one enumerator, separated by ~2 weeks so feedback from the supervisor cohort can shape the enumerator curriculum.

#### 9.5.1 Supervisor training — Aug 1st week

5-day curriculum.

| Day | Topic | Carl's deliverable |
|---|---|---|
| 1 | UHC Year 2 overview, Protocol V2, ethics, Annex D replacement protocol | Slide deck reused from Project Coordinator. |
| 2 | Instrument walkthrough — F1 / F3 / F4 question-by-question | Co-facilitate with Survey Manager; Carl flags every CAPI-specific UX nuance (e.g. select-one vs select-all, "Other (specify)" patterns). |
| 3 | CAPI app demo + tablet operation | Carl-led. Pre-loaded practice cases on each tablet. Hands-on — every supervisor enters at least 3 mock cases. |
| 4 | CSWeb dashboard + sync troubleshooting | Carl-led. Each supervisor logs into CSWeb staging with their assigned credentials, runs Sync Report, runs Map Case Listing (§9.5.4 / §10.2), reads value-labelled report (§10.3). |
| 5 | Replacement protocol + paper backup forms + escalation drill | Co-facilitate. Carl handles the "what to do if app fails mid-interview" drill. |

Carl-owned artifacts:

- `deliverables/Training/Supervisor-Deck-CAPI-Demo.pdf`
- `deliverables/Training/Supervisor-Lab-Cases.csdb` (10 mock cases per F-series, pre-loaded on practice tablets)
- `deliverables/Training/Supervisor-Quickref-One-Pager.pdf` (laminated card distributed)

#### 9.5.2 Enumerator training — Aug 2nd–4th weeks

3-day curriculum, run per cluster (so 3 weeks across NCR / R8 / R4-B).

| Day | Topic |
|---|---|
| 1 | Instrument walkthrough (per F-series this enumerator will work) + role-play interviews |
| 2 | Tablet operation, app walkthrough, hands-on entry of 5 mock cases, sync drill |
| 3 | Sample fieldwork day — paired SE+STL pairs go to a non-sample facility, run real-condition mock interviews, return for debrief |

Carl-owned artifacts:

- `deliverables/Training/Enumerator-Deck-CAPI-Walkthrough.pdf`
- `deliverables/Training/Enumerator-Lab-Cases.csdb` (5 cases per F-series + 2 deliberate-error cases for the validation drills)
- `deliverables/Training/Paper-Backup-Forms-Appendix-F.pdf` (per the Survey Manual Appendix F template; used when the tablet fails)

#### 9.5.3 Tablet pre-loading

Each training tablet (and each main-fieldwork tablet) ships with:

- CSEntry Android (latest stable).
- F1 / F3 / F4 `.pen` builds, current production version.
- One PFF per role (interviewer / supervisor).
- Sync credentials provisioned per Khurshid 2022-05-05 *Add a CSWeb user and assign a role*.
- 7-dialect translation bundles loaded (locale switcher in app header).
- Practice cases for the training labs — purged before deployment to fieldwork.

#### 9.5.4 Map Case Listing demo for STLs

Worked into Day 4 of supervisor training and again as a refresher in Day 2 of enumerator training (so SEs know what their STL sees). Detail in §10.2 below — for training, the demo is "load yesterday's lab cases, see them on the map, identify which one was entered without GPS lock and discuss what should have been done".

### 9.6 Phase 9 exit criteria

All of the following before main fieldwork starts:

- [ ] SJREB clearance in hand.
- [ ] Pretest debrief documented (`Pretest-Report-<YYYY-MM-DD>.md`).
- [ ] Pretest fixes regenerated and re-tested (full Phase 7 desk + bench replay against the post-fix build).
- [ ] Survey manual final, all three integration gaps closed.
- [ ] Training materials approved by Project Coordinator + Survey Manager.
- [ ] Tablets provisioned for every enumerator + STL, lab cases purged, production builds verified.
- [ ] Pretest endorsement letters delivered to LPH-Bay + LGU Los Baños.
- [ ] Translation bundles signed off by Survey Manager (per dialect).
- [ ] CSWeb sync-report value labels imported (§10.3) so STLs see human-readable filters from day 1.

---

## Phase 10 — Production fieldwork support

**Objective.** Keep the data flowing and the instrument stable for the duration of UHC Year 2 main collection, with daily verification of sync + completeness, hot-fix discipline when issues surface, and weekly client deliverables to DOH-PMSMD.

**Inputs.**
- Frozen-for-fieldwork F1 / F3 / F4 builds from Phase 9.
- Provisioned tablets at all sites.
- CSWeb production environment with sync labels imported.
- Active issue log, hot-fixes ledger, replacement-protocol log.

**Outputs.**
- Daily field summary (HTML, per cluster).
- Weekly client report (HTML, cumulative, to DOH-PMSMD).
- Hot-fix releases as needed.
- Interim CSTab cross-tabs each month.
- Cleaned, edited dataset rolling forward into Phase 11.

### 10.1 Daily ops rhythm

Per Protocol V2 § daily operations and the simplified sync model (May 6 working file):

| Time (MNL) | Actor | Activity |
|---|---|---|
| 09:00 | STL with their SEs | Stand-up. Slack-based on `#capi-fieldwork-ops` (voice message acceptable on low-bandwidth days). Yesterday's blockers, today's targets per F-series, replacement decisions to confirm. |
| 09:30–18:00 | SEs | Capture cases. Light opportunistic sync if facility WiFi is good (saves end-of-day load). |
| 18:00–22:00 | SEs | Travel home / review notes / tomorrow's prep. |
| 22:00 | SEs | **Mandatory full daily sync.** Every case captured today must be in CSWeb by 22:30. |
| 22:30 | STL | Verifies sync via CSWeb dashboard. Calls SE if their tablet hasn't synced. Logs any failures to the issue log. |
| 23:00 | Carl + automation | Daily HTML field summary (§10.6) generated against last-24h CSWeb data, posted to `#capi-fieldwork-ops` Slack with `@here` for STLs. |

A few notes on this cadence:

- **One mandatory sync, not three.** The May 6 working file deliberately simplified from morning-noon-evening to one 22:00 mandate. Reasoning: enumerators were skipping the noon sync anyway, and morning sync just shifted the wakeup. One mandate is unambiguous and easier to enforce.
- **Light WiFi-opportunistic sync is encouraged but not required.** When an SE has WiFi at the facility (rare), running an interim sync reduces evening load and gives Carl a head start on data review. They use the same `Sync` button — it's idempotent.
- **Slack-first, low-bandwidth.** `#capi-fieldwork-ops` is the daily channel. Voice notes are acceptable for STLs on slow connections; transcripts go up the next morning.
- **CSWeb dashboard is the source of truth for sync status.** Not the SE's word. STL pulls the dashboard at 22:30 and cross-references against the SE's case-list verbal report.
- **No PII in Slack messages.** Case IDs (per FIELD_CONTROL), facility codes, region codes — yes. Patient names, addresses, GPS coordinates — never.

### 10.2 Map Case Listing — quick GPS overlay

**Khurshid 2022-07-06** — *Map Object: Display GPS Coordinates*. The technique cards are at `3_Resources/Learning-Materials/mentors/khurshid-arshad/videos/2022-07-06_map-object-display-gps-coordinates_PO-xd_hl3WA/techniques.md`.

#### 10.2.1 Why STLs need this

Replacement-protocol abuse and clustering anomalies are easiest to spot **visually**. Numbers in a CSWeb table say "12 cases entered today by SE-NCR-04". A map says "12 cases all clustered at one corner of the EA boundary, with the rest of the EA empty". Same data, vastly different signal.

Every UHC F1 / F3 / F4 case captures GPS in FIELD_CONTROL paradata (per [[04-Phase-6-Build-CAPI-App]] § FIELD_CONTROL). The Map Case Listing surfaces those points without writing any PROC code.

#### 10.2.2 Map Case Listing — no-code path

**(Khurshid 2022-07-06 *Map Object - Display GPS Coordinates @ 00:33*)**

In CSPro Designer, the supervisor app:

1. **Options → Map Case Listing**.
2. Check **Show the case listing on a map**.
3. Choose **latitude variable** = `FIELD_CONTROL.GPS_LAT`.
4. Choose **longitude variable** = `FIELD_CONTROL.GPS_LON`.
5. **OK**, save, build, deploy.

On the supervisor's tablet, the data-listing screen now shows a map with one pin per case. No code required. Wire this for each F-series supervisor app (F1, F3, F4) — three separate Map Case Listings, one per dictionary.

> **Gotcha (Khurshid 2022-07-06)** — *"This is per-application config; new dictionaries with their own GPS items need to be wired up separately."* Don't assume one wiring covers all three F-series.

#### 10.2.3 Map object pattern — colored markers per disposition

**(Khurshid 2022-07-06 *Map Object - Display GPS Coordinates @ 02:18*)**

When STLs need richer UX — colored markers by disposition, hover descriptions, satellite imagery — the no-code path isn't enough. Drop down to the map object API.

```cspro
PROC GLOBAL
map view_map;

function view_uhc_cases_on_map()
   add_uhc_listing();
   view_map.setBaseMap(satellite);
   view_map.show();
end;

function add_uhc_listing()
   { Iterate F1 facility cases — color by disposition }
   setfile(F1_DICT, "..\data\f1\f1_data.csdb");
   forcase F1_DICT do
      view_map.addMarker(GPS_LAT, GPS_LON);

      if DISPOSITION = 1 then              { Completed }
         view_map.setMarkerColor(magenta);
      else if DISPOSITION = 2 then         { Partial }
         view_map.setMarkerColor(yellow);
      else if DISPOSITION = 3 then         { Locked / out-of-scope }
         view_map.setMarkerColor(black);
      else if DISPOSITION = 4 then         { Refused }
         view_map.setMarkerColor(red);
      endif;

      view_map.setMarkerDescription(
         concat(
            "Status: ", strip(maketext(DISPOSITION)),
            " | Facility: ", strip(FACILITY_CODE),
            " | SE: ", strip(SE_ID),
            " | Date: ", strip(maketext(SUBMIT_DATE))
         )
      );
   enddo;
end;
```

Color convention follows Khurshid's fieldwork standard: **magenta = completed, yellow = partial, black = locked, red = refused**. Reuse this for F3 and F4 maps so STLs across all three F-series see one consistent legend.

> **Gotcha (Khurshid 2022-07-06)** — *"setfile() must be called before forcase or the loop has nothing to iterate."* Wire `setfile()` at the top of `add_uhc_listing()`, not in PROC GLOBAL — re-running the function should always re-bind.

#### 10.2.4 STL daily walkthrough

Once a day, around 22:30 sync verification time, STL opens the supervisor app's **View Cases on Map** menu option. Looks for:

- **Cluster anomalies** — pins outside the EA boundary; pins on top of each other (same GPS = possible falsified entries); pins in unreachable terrain (sea, fields).
- **Refusal hotspots** — multiple red pins clustered at one facility (escalate to STL replacement decision).
- **Sync gaps** — facility on the assignment list but no pin in the area.

Findings flow into the next morning's stand-up.

### 10.3 CSV import for sync-report value labels

**Khurshid 2022-05-05** — *How to Sync Report, Sync Files, Add Users and Define Roles* (specifically the value-labels section). Cards at `3_Resources/Learning-Materials/mentors/khurshid-arshad/videos/2022-05-05_how-to-sync-report-sync-files-add-users-and-define-roles_QU-XNX8_Aqc/techniques.md`.

#### 10.3.1 The problem

CSWeb's Synchronize Report is the dashboard ops looks at every day. By default, the column filters show **value codes**, not labels. So filtering by region looks like this:

| Region | Cluster | Cases |
|---|---|---|
| 13 | 1301 | 12 |
| 13 | 1302 | 8 |
| 8 | 0801 | 5 |

Nobody remembers `13 = NCR`, `8 = Region 8`, etc. — and STLs need to make filtering decisions at speed. CSV import fixes it.

#### 10.3.2 CSV format

**(Khurshid 2022-05-05 @ 08:55)** — *"You have to create the csv file in the same order as the dictionary contains the id items. We cannot change the order. We only have province and locality label so we will only label the province and locality id items."*

Format: alternating `code, name` pairs in dictionary-ID-item order.

For UHC F1 (whose ID-items are `REGION_CODE`, `PROVINCE_CODE`, `LGU_CODE`, `FACILITY_CODE`, `CASE_NUM`):

```csv
region_code,region_name,province_code,province_name,lgu_code,lgu_name,facility_code,facility_name
13,NCR,1339,NCR Fourth District,133901,Quezon City,F0001,Quezon City General Hospital
13,NCR,1339,NCR Fourth District,133901,Quezon City,F0002,East Avenue Medical Center
08,Region 8,0837,Leyte,083738,Tacloban City,F0101,Eastern Visayas Regional Medical Center
04B,Region IV-B,1751,Oriental Mindoro,175102,Calapan City,F0201,Oriental Mindoro Provincial Hospital
```

After upload, the Synchronize Report dropdown shows `Region: NCR` instead of `Region: 13`. Same for province / LGU / facility.

#### 10.3.3 Upload procedure

In CSWeb (Khurshid 2022-05-05):

1. **Data tab → Import Report Labels**.
2. **Browse** → select `f1-value-labels.csv`.
3. Check **CSV file has a header row**.
4. **Import**.

Repeat for F3 and F4 dictionaries (separate CSVs). Re-upload whenever the master facility list updates.

> **Gotcha (Khurshid 2022-05-05)** — *"Order must match the dictionary's ID-item order exactly — a misordered CSV silently labels the wrong fields."* When in doubt, re-export the dictionary's ID-item list from CSPro Designer and use it as the column-order reference for the CSV.

#### 10.3.4 Value-set CSVs (not just ID items)

The same CSV-import flow accepts **value-set codes** for any item — not only ID items. This matters for UHC because we want to filter by:

- **Disposition code** (1=Completed, 2=Partial, 3=Locked, 4=Refused, 5=Replaced, ...).
- **Facility ownership type** (1=Government, 2=Private, 3=NGO, 4=Faith-based, 5=Other).
- **Patient type** (1=OPD, 2=Inpatient, 3=Referral, 4=Emergency, ...).

Generate one CSV per dictionary with all the value-sets we want to surface as filter labels.

#### 10.3.5 Generator: extension to `cspro_helpers`

Hand-maintaining these CSVs is brittle — every dcf change risks the CSV drifting from the dictionary. Generate them.

Add `value-labels-csv-export.py` to the `cspro_helpers` package (same package that hosts the dcf generator from [[03-Phase-3-5-Spec-and-Generators]]).

```python
"""
value-labels-csv-export.py

Generates per-dictionary CSVs of value-set labels for CSWeb sync-report import,
per Khurshid 2022-05-05 'How to Sync Report, Sync Files, Add Users and Define Roles'.

Usage:
    python -m cspro_helpers.value_labels_csv_export \
        --dcf deliverables/CSPro/F1/F1.dcf \
        --out deliverables/CSPro/F1/f1-value-labels.csv \
        --dictionary F1_DICT
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ValueSet:
    name: str
    codes: list[tuple[str, str]]   # [(code, label), ...]


@dataclass(frozen=True)
class IdItem:
    name: str                       # e.g. REGION_CODE
    label: str                      # human-readable column header (e.g. region_name)
    value_set: ValueSet | None      # may be None for free-form ID items


def load_dcf(path: Path) -> dict:
    """DCF is JSON in CSPro 8+; older versions need a different parser."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_id_items(dcf: dict, dictionary: str) -> list[IdItem]:
    """Pull ID items in their dictionary-defined order — order matters per Khurshid."""
    dict_obj = next(
        (d for d in dcf["dictionaries"] if d["name"] == dictionary), None
    )
    if dict_obj is None:
        raise ValueError(f"Dictionary {dictionary!r} not found in dcf.")

    id_items: list[IdItem] = []
    for item in dict_obj.get("idItems", []):
        vs_ref = item.get("valueSet")
        vs = None
        if vs_ref is not None:
            vs_obj = next(
                v for v in dict_obj["valueSets"] if v["name"] == vs_ref
            )
            vs = ValueSet(
                name=vs_obj["name"],
                codes=[(str(c["code"]), c["label"]) for c in vs_obj["values"]],
            )
        id_items.append(IdItem(
            name=item["name"],
            label=item["name"].lower().replace("_code", "_name"),
            value_set=vs,
        ))
    return id_items


def emit_csv(id_items: Iterable[IdItem], out_path: Path) -> None:
    id_items = list(id_items)
    header: list[str] = []
    for it in id_items:
        header.extend([it.name.lower(), it.label])

    rows: list[list[str]] = []
    if any(it.value_set for it in id_items):
        # Cartesian product is wrong for hierarchical IDs; emit per-leaf rows
        # using the leaf value set as the driver.
        leaf = id_items[-1]
        if leaf.value_set is None:
            raise ValueError("Leaf ID item has no value set — cannot drive emission.")
        for code, label in leaf.value_set.codes:
            row: list[str] = []
            for it in id_items[:-1]:
                row.extend([
                    "",  # parent codes filled by upstream lookup table
                    "",
                ])
            row.extend([code, label])
            rows.append(row)
    else:
        rows = []

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dcf", type=Path, required=True)
    parser.add_argument("--dictionary", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    dcf = load_dcf(args.dcf)
    items = extract_id_items(dcf, args.dictionary)
    emit_csv(items, args.out)
    print(f"Wrote {args.out} with {len(items)} ID-item columns.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Wire into the `make labels` target so every dcf rebuild emits fresh CSVs:

```makefile
.PHONY: labels
labels:
	python -m cspro_helpers.value_labels_csv_export \
		--dcf deliverables/CSPro/F1/F1.dcf \
		--dictionary F1_DICT \
		--out deliverables/CSPro/F1/f1-value-labels.csv
	python -m cspro_helpers.value_labels_csv_export \
		--dcf deliverables/CSPro/F3/F3.dcf \
		--dictionary F3_DICT \
		--out deliverables/CSPro/F3/f3-value-labels.csv
	python -m cspro_helpers.value_labels_csv_export \
		--dcf deliverables/CSPro/F4/F4.dcf \
		--dictionary F4_DICT \
		--out deliverables/CSPro/F4/f4-value-labels.csv
```

Re-upload to CSWeb after every regen of these CSVs.

### 10.4 publishdate() force-update

**Khurshid 2022-10-08** — *Tutorial on PublishDate() Function*. Cards at `3_Resources/Learning-Materials/mentors/khurshid-arshad/videos/2022-10-08_tutorial-on-publishdate-function_766_D7Z2fJU/techniques.md`. See also [[06-Phase-8-CSWeb-and-Tablets]] §8.16 for the Phase 8 wiring.

#### 10.4.1 What problem this solves in fieldwork

Hot-fix only matters if it actually reaches the SE's tablet. Without enforcement:

- Carl pushes new `.pen` to CSWeb at 14:00.
- SE-NCR-04 doesn't sync until 22:00 — fine, will pick up the new build.
- SE-NCR-07 didn't sync the day before (was offline overnight) — won't sync until 22:00 today either, so they kept running yesterday's build all day, capturing data that maybe still has the bug.

`publishdate()` enforces a stale-build expiration. The app *refuses to run* if its build is older than N days, forcing the SE to sync (which downloads the new `.pen`) before they can re-enter.

#### 10.4.2 Pattern

**(Khurshid 2022-10-08 *Tutorial on PublishDate() Function @ 00:09*)**

```cspro
PROC GLOBAL
numeric publish_day, days_left;
array app_months(12) string;

PROC LEVEL
preproc

  { Initialize month-name lookup once }
  app_months(1)  = "January";
  app_months(2)  = "February";
  app_months(3)  = "March";
  app_months(4)  = "April";
  app_months(5)  = "May";
  app_months(6)  = "June";
  app_months(7)  = "July";
  app_months(8)  = "August";
  app_months(9)  = "September";
  app_months(10) = "October";
  app_months(11) = "November";
  app_months(12) = "December";

  { publishdate() encodes date * 1000 + time-of-day; / 1000 keeps date only }
  publish_day = publishdate() / 1000;

  { UHC Year 2 ops decision: 5-day window before forced expiration }
  if datediff(systemdate(), publish_day, days) > 5 then
    errmsg("Application has expired. Please sync to update before continuing.");
    stop(1);
  else
    days_left = 5 - datediff(systemdate(), publish_day, days);
    if days_left = 0 then
      warning("After today midnight you will be unable to use the app. Sync now.");
    else
      warning(maketext(
        "%d day(s) left. Please sync by %d %s %d.",
        days_left,
        day(systemdate() + days_left),
        app_months(month(systemdate() + days_left)),
        year(systemdate() + days_left)
      ));
    endif;
  endif;
```

Wire this into PROC LEVEL preproc of every F-series application (F1, F3, F4).

#### 10.4.3 5-day window — why this number

A 5-day window balances:

- **Hot-fix reach** — most fieldwork days have at least one sync; 5 days catches the SE who skipped two consecutive syncs and crossed the weekend.
- **Edge cases** — SE in deep-rural R8 might have legitimately bad connectivity for 2–3 days. 5 days gives slack without becoming "infinite stale".
- **Field disruption cost** — when the app expires, that SE *cannot work* until they get connectivity to sync. 5 days means at most 1 lost half-day per SE per cycle, which we accept.

If a particular hot-fix is critical (data-corrupting bug), Carl can manually shorten the window for that release — set `> 2` for the hot-fix release, then revert to 5 in the next normal release.

#### 10.4.4 Auto-injection vs manual constant

> **Gotcha (Khurshid 2022-10-08)** — *"Two ways to set the published date — manual constant (`publish_day = 20221008`) or `publishdate()` auto-injected at .pen build time. Khurshid recommends the latter — manual is error-prone and forgets to update when you re-publish."*

Use `publishdate()` (auto-injected). Manual is asking for a stale-constant bug.

### 10.5 synctime() for daily monitoring

**Khurshid 2025-02-20** — *Tutorial on synctime Function*. Cards at `3_Resources/Learning-Materials/mentors/khurshid-arshad/videos/2025-02-20_tutorial-on-synctime-funtion_9cPreOFEx5k/techniques.md`. See also [[06-Phase-8-CSWeb-and-Tablets]] §8.17.

#### 10.5.1 Two scopes

**Whole-dictionary scope** answers: when did this tablet last sync the entire F1 / F3 / F4 dictionary?

**Per-case scope** answers: which specific cases on this tablet are pending sync (modified or created since the last sync)?

Both useful — combined they give a per-tablet daily check that's actionable.

#### 10.5.2 Tablet-side daily check

Wire into PROC LEVEL preproc, alongside the publishdate() check:

```cspro
PROC GLOBAL
numeric last_sync_unix;
numeric pending_count;
alpha (50) last_sync_str;
string sync_url = "https://csweb.aspsi-doh-uhc.example/api";

PROC LEVEL
preproc

  { Whole-dictionary last sync }
  last_sync_unix = synctime(sync_url, F1_DICT);

  if last_sync_unix = 0 then
    warning("This tablet has never synced. Please sync before starting cases.");
  else
    last_sync_str = timestring(last_sync_unix);
    if datediff(systemdate(), last_sync_unix / 86400, days) > 1 then
      warning(maketext(
        "Last sync was %s — over 24 hours ago. Sync at end of day.",
        last_sync_str
      ));
    endif;
  endif;

  { Per-case pending count }
  pending_count = 0;
  forcase F1_DICT do
    if synctime(sync_url, F1_DICT, "", uuid(F1_DICT)) = notappl then
      pending_count = pending_count + 1;
    endif;
  enddo;

  if pending_count > 0 then
    warning(maketext("%d case(s) on this tablet are pending sync.", pending_count));
  endif;
```

> **Critical insight (Khurshid 2025-02-20)** — *"If a case was synchronized earlier but later modified or if a new case is added, the function will return notappl. The information for cases where the function returns notappl will be displayed in the table."* — `notappl` is the signal for "needs sync".

#### 10.5.3 STL-side: CSWeb Sync Report

CSWeb's Synchronize Report (with value labels imported per §10.3) shows last-sync time per device. STL pulls this at 22:30 daily and flags any tablet `last_sync > 24h`. Combined with the §10.2 Map Case Listing visual, STL has a clear picture: who synced, when, and where they were when they captured.

### 10.6 HTML reports for ops dashboards

**Khurshid 2022-12-05** — *Create Report using HTML*. Cards at `3_Resources/Learning-Materials/mentors/khurshid-arshad/videos/2022-12-05_create-report-using-html_Z75uShy-9k0/techniques.md`. Also draws on Khurshid 2022-09-05 for the layout-controlled `file_handler` + `filewrite` plain-text path.

#### 10.6.1 Two report styles, two use cases

| Style | Trigger | Use case |
|---|---|---|
| **HTML report** with embedded `<? ?>` PROC blocks + `~~ ~~` fills (Khurshid 2022-12-05) | Polished, viewable in any browser | Daily field summary, weekly client deliverable, refusal/replacement audit. |
| **Plain-text report** via `setfile` + `filewrite` + `execsystem` (Khurshid 2022-12-05) | Quick supervisor check on the device | STL spot-checks, end-of-day SE summary. Renders in Notepad / view. |
| **Layout-controlled text** via `file_handler` + `filewrite` (Khurshid 2022-09-05) | Precise column alignment, dividers | Sample-file generation, listing reports, monthly client cuts where alignment matters. |

#### 10.6.2 HTML report — embedding mechanics

**(Khurshid 2022-12-05 *Create Report using HTML @ 11:18*)**

Two distinct embedding mechanisms:

- `<?...?>` — **statements / blocks** (loops, computations, function calls).
- `~~...~~` — **expression evaluation inline** (one-line value substitution).

```html
<? numeric x; x = count(SEX = 1); ?>          <!-- block: declare + compute -->
<p>Male count: ~~x~~</p>                       <!-- expression fill -->
<p>Padded: ~~maketext("%04d", x)~~</p>         <!-- expression with formatter -->
```

> **Gotcha (Khurshid 2022-12-05)** — *"Don't put complex multi-statement logic inside `~~ ~~` — only single expressions. Move all loops, conditionals, and side effects into `<? ?>`. If these tags do not exist then error message will appear within the compiler output tab — always check the compile output after edits."*

#### 10.6.3 Daily field summary — paste-ready template

Save as `deliverables/CSPro/Reports/daily-field-summary.html`. **Add Files** to each F-series supervisor app (Designer **File → Add Files**, NOT **Open**), set the report name via Properties, and wire it into a menu item the STL launches at 22:30 sync verification time.

```html
<html>
<head>
<style>
  body  { font-family: Arial, Helvetica, sans-serif; color: #1c1c1c; }
  h1    { color: #003c71; border-bottom: 2px solid #003c71; padding-bottom: 6px; }
  h2    { color: #003c71; margin-top: 20px; }
  table { border-collapse: collapse; width: 100%; margin-top: 10px; }
  th    { background: #f0f4f8; text-align: left; padding: 6px 10px; border: 1px solid #b8c5d4; }
  td    { padding: 6px 10px; border: 1px solid #b8c5d4; }
  .num  { text-align: right; font-variant-numeric: tabular-nums; }
  .ok   { color: #1a7f37; font-weight: bold; }
  .warn { color: #b07700; font-weight: bold; }
  .bad  { color: #b30000; font-weight: bold; }
  .meta { color: #555; font-size: 11pt; }
  .footer { margin-top: 24px; color: #666; font-size: 10pt; }
</style>
</head>
<body>

<h1>UHC Year 2 — Daily Field Summary</h1>
<p class="meta">
  Generated: ~~maketext("%d %s %d", day(systemdate()), app_months(month(systemdate())), year(systemdate()))~~
  &nbsp;|&nbsp;
  Cluster: ~~strip(maketext("%s", CLUSTER_CODE))~~
  &nbsp;|&nbsp;
  STL: ~~strip(STL_NAME)~~
</p>

<?
{ ----- Aggregate F1 ----- }
numeric f1_completed, f1_partial, f1_refused, f1_total;
setfile(F1_DICT, pathname(workingDir) + "..\data\f1\f1_data.csdb");
forcase F1_DICT do
  if DISPOSITION = 1 then inc(f1_completed);
  else if DISPOSITION = 2 then inc(f1_partial);
  else if DISPOSITION = 4 then inc(f1_refused);
  endif;
  inc(f1_total);
enddo;

{ ----- Aggregate F3 ----- }
numeric f3_completed, f3_partial, f3_refused, f3_total;
setfile(F3_DICT, pathname(workingDir) + "..\data\f3\f3_data.csdb");
forcase F3_DICT do
  if DISPOSITION = 1 then inc(f3_completed);
  else if DISPOSITION = 2 then inc(f3_partial);
  else if DISPOSITION = 4 then inc(f3_refused);
  endif;
  inc(f3_total);
enddo;

{ ----- Aggregate F4 ----- }
numeric f4_completed, f4_partial, f4_refused, f4_total;
setfile(F4_DICT, pathname(workingDir) + "..\data\f4\f4_data.csdb");
forcase F4_DICT do
  if DISPOSITION = 1 then inc(f4_completed);
  else if DISPOSITION = 2 then inc(f4_partial);
  else if DISPOSITION = 4 then inc(f4_refused);
  endif;
  inc(f4_total);
enddo;

{ ----- Sync status ----- }
numeric f1_pending, f3_pending, f4_pending;
forcase F1_DICT do
  if synctime("https://csweb.aspsi-doh-uhc.example/api", F1_DICT, "", uuid(F1_DICT)) = notappl
    then inc(f1_pending);
  endif;
enddo;
forcase F3_DICT do
  if synctime("https://csweb.aspsi-doh-uhc.example/api", F3_DICT, "", uuid(F3_DICT)) = notappl
    then inc(f3_pending);
  endif;
enddo;
forcase F4_DICT do
  if synctime("https://csweb.aspsi-doh-uhc.example/api", F4_DICT, "", uuid(F4_DICT)) = notappl
    then inc(f4_pending);
  endif;
enddo;
?>

<h2>Cases captured today</h2>
<table>
  <tr>
    <th>Instrument</th>
    <th class="num">Completed</th>
    <th class="num">Partial</th>
    <th class="num">Refused</th>
    <th class="num">Total</th>
    <th class="num">Pending sync</th>
  </tr>
  <tr>
    <td>F1 — Facility Head</td>
    <td class="num">~~maketext("%04d", f1_completed)~~</td>
    <td class="num">~~maketext("%04d", f1_partial)~~</td>
    <td class="num">~~maketext("%04d", f1_refused)~~</td>
    <td class="num">~~maketext("%04d", f1_total)~~</td>
    <td class="num">~~maketext("%04d", f1_pending)~~</td>
  </tr>
  <tr>
    <td>F3 — Patient</td>
    <td class="num">~~maketext("%04d", f3_completed)~~</td>
    <td class="num">~~maketext("%04d", f3_partial)~~</td>
    <td class="num">~~maketext("%04d", f3_refused)~~</td>
    <td class="num">~~maketext("%04d", f3_total)~~</td>
    <td class="num">~~maketext("%04d", f3_pending)~~</td>
  </tr>
  <tr>
    <td>F4 — Household</td>
    <td class="num">~~maketext("%04d", f4_completed)~~</td>
    <td class="num">~~maketext("%04d", f4_partial)~~</td>
    <td class="num">~~maketext("%04d", f4_refused)~~</td>
    <td class="num">~~maketext("%04d", f4_total)~~</td>
    <td class="num">~~maketext("%04d", f4_pending)~~</td>
  </tr>
</table>

<h2>Anomalies</h2>
<?
numeric anomaly_count;
{ ----- Stale-tablet check ----- }
numeric f1_last_sync;
f1_last_sync = synctime("https://csweb.aspsi-doh-uhc.example/api", F1_DICT);
?>
<ul>
  <? if f1_last_sync = 0 then ?>
    <li class="bad">F1 dictionary has never synced from this tablet.</li>
    <? inc(anomaly_count); ?>
  <? else if datediff(systemdate(), f1_last_sync / 86400, days) > 1 then ?>
    <li class="warn">F1 last sync was ~~timestring(f1_last_sync)~~ — over 24 hours ago.</li>
    <? inc(anomaly_count); ?>
  <? endif; ?>

  <? if f1_pending + f3_pending + f4_pending > 0 then ?>
    <li class="warn">Total pending-sync cases on this tablet:
       ~~maketext("%d", f1_pending + f3_pending + f4_pending)~~.</li>
    <? inc(anomaly_count); ?>
  <? endif; ?>

  <? if anomaly_count = 0 then ?>
    <li class="ok">No anomalies detected.</li>
  <? endif; ?>
</ul>

<p class="footer">
  Auto-generated by UHC Year 2 CAPI app, build ~~maketext("%d", publishdate() / 1000)~~.
  Forward concerns to STL or post in <code>#capi-fieldwork-ops</code>.
</p>

</body>
</html>
```

Per Khurshid 2022-12-05, this gets attached to the supervisor app via Designer's **File → Add Files → Properties → set report name**. Click the report node, choose Logic, paste the template; CSPro compiles it and the supervisor menu surfaces a new option that renders the HTML in the device's default browser.

#### 10.6.4 Plain-text alternative — quick checks

For when an STL just wants the numbers without browser overhead, ship a parallel plain-text version. Per **Khurshid 2022-12-05 *Create Report using HTML @ 04:50*** and the layout-controlled pattern from **Khurshid 2022-09-05 *Create a Sample File for Household Interview @ 16:08***:

```cspro
PROC GLOBAL
file daily_summary_file;

function build_daily_summary_text()
   numeric f1_total, f1_completed, f1_partial, f1_refused;
   numeric f3_total, f3_completed, f3_partial, f3_refused;
   numeric f4_total, f4_completed, f4_partial, f4_refused;

   setfile(F1_DICT, pathname(workingDir) + "..\data\f1\f1_data.csdb");
   forcase F1_DICT do
      inc(f1_total);
      if DISPOSITION = 1 then inc(f1_completed);
      else if DISPOSITION = 2 then inc(f1_partial);
      else if DISPOSITION = 4 then inc(f1_refused);
      endif;
   enddo;

   setfile(F3_DICT, pathname(workingDir) + "..\data\f3\f3_data.csdb");
   forcase F3_DICT do
      inc(f3_total);
      if DISPOSITION = 1 then inc(f3_completed);
      else if DISPOSITION = 2 then inc(f3_partial);
      else if DISPOSITION = 4 then inc(f3_refused);
      endif;
   enddo;

   setfile(F4_DICT, pathname(workingDir) + "..\data\f4\f4_data.csdb");
   forcase F4_DICT do
      inc(f4_total);
      if DISPOSITION = 1 then inc(f4_completed);
      else if DISPOSITION = 2 then inc(f4_partial);
      else if DISPOSITION = 4 then inc(f4_refused);
      endif;
   enddo;

   setfile(daily_summary_file, pathname(workingDir) + "daily_summary.txt", create);
   filewrite(daily_summary_file, "============================================");
   filewrite(daily_summary_file, "  UHC Year 2 — Daily Field Summary");
   filewrite(daily_summary_file, maketext("  Date:    %d %s %d",
       day(systemdate()), app_months(month(systemdate())), year(systemdate())));
   filewrite(daily_summary_file, maketext("  Cluster: %s", strip(maketext("%s", CLUSTER_CODE))));
   filewrite(daily_summary_file, maketext("  STL:     %s", strip(STL_NAME)));
   filewrite(daily_summary_file, "============================================");
   filewrite(daily_summary_file, "");
   filewrite(daily_summary_file, "                 Compl  Part   Ref   Total");
   filewrite(daily_summary_file, "  --------------------------------------------");
   filewrite(daily_summary_file, maketext("  F1 Facility    %4d  %4d  %4d  %5d",
       f1_completed, f1_partial, f1_refused, f1_total));
   filewrite(daily_summary_file, maketext("  F3 Patient     %4d  %4d  %4d  %5d",
       f3_completed, f3_partial, f3_refused, f3_total));
   filewrite(daily_summary_file, maketext("  F4 Household   %4d  %4d  %4d  %5d",
       f4_completed, f4_partial, f4_refused, f4_total));
   filewrite(daily_summary_file, "  --------------------------------------------");
   filewrite(daily_summary_file, maketext("  Total          %4d  %4d  %4d  %5d",
       f1_completed + f3_completed + f4_completed,
       f1_partial   + f3_partial   + f4_partial,
       f1_refused   + f3_refused   + f4_refused,
       f1_total     + f3_total     + f4_total));
   filewrite(daily_summary_file, "");
   filewrite(daily_summary_file, "  End of report.");
   close(daily_summary_file);

   if getos() = 10 then
      execsystem("explorer " + pathname(workingDir) + "daily_summary.txt");
   else
      execsystem("view " + pathname(workingDir) + "daily_summary.txt");
   endif;
end;
```

> **Note (Khurshid 2022-09-05 *Create a Sample File for Household Interview @ 16:08*)** — *"If you observe the layout looks like messages."* — the `maketext` `%4d` / `%5d` format specifiers are doing the column alignment work; preserve them when adapting.

#### 10.6.5 Weekly client report

Same HTML pattern, but cumulative across the engagement-to-date and aggregated by region. Save as `deliverables/CSPro/Reports/weekly-client-report.html`. Distribute every Monday morning to DOH-PMSMD via the Project Coordinator, per Protocol V2 reporting cadence — **never directly from Carl**.

Sections in the weekly report:

1. **Executive numbers** — cumulative cases by F-series; completion % vs sample target.
2. **By region** — cases by region × F-series; refusal rates; replacement rates.
3. **By cluster** — cases by cluster; flags for clusters falling behind sample target.
4. **Replacement audit** — count of replacements by region; which clusters approach the 5–10 % cap; samples with insufficient ≥3-visit attempts (escalation to STL).
5. **Sync hygiene** — % of cases that synced same-day; tablet-days lost to outages.
6. **Pretest issues outstanding** — issues from Phase 9 still in the hot-fix queue.

Skeleton structure (re-uses the daily template's CSS):

```html
<html>
<head>
<style>
  body  { font-family: Arial, Helvetica, sans-serif; color: #1c1c1c; }
  h1    { color: #003c71; border-bottom: 2px solid #003c71; padding-bottom: 6px; }
  h2    { color: #003c71; margin-top: 24px; }
  h3    { color: #1c1c1c; }
  table { border-collapse: collapse; width: 100%; margin-top: 10px; }
  th    { background: #f0f4f8; text-align: left; padding: 6px 10px; border: 1px solid #b8c5d4; }
  td    { padding: 6px 10px; border: 1px solid #b8c5d4; }
  .num  { text-align: right; font-variant-numeric: tabular-nums; }
  .pct  { text-align: right; }
  .meta { color: #555; font-size: 11pt; }
  .footer { margin-top: 24px; color: #666; font-size: 10pt; }
</style>
</head>
<body>

<h1>UHC Year 2 — Weekly Client Report</h1>
<p class="meta">
  Week ending: ~~maketext("%d %s %d", day(systemdate()), app_months(month(systemdate())), year(systemdate()))~~
</p>

<?
numeric f1_target, f3_target, f4_target;
f1_target = 800;     { sample target — replace with real target per Protocol V2 }
f3_target = 1600;
f4_target = 2400;

numeric f1_done, f3_done, f4_done;
setfile(F1_DICT, pathname(workingDir) + "..\data\f1\f1_data.csdb");
forcase F1_DICT do
  if DISPOSITION = 1 then inc(f1_done); endif;
enddo;
setfile(F3_DICT, pathname(workingDir) + "..\data\f3\f3_data.csdb");
forcase F3_DICT do
  if DISPOSITION = 1 then inc(f3_done); endif;
enddo;
setfile(F4_DICT, pathname(workingDir) + "..\data\f4\f4_data.csdb");
forcase F4_DICT do
  if DISPOSITION = 1 then inc(f4_done); endif;
enddo;
?>

<h2>Cumulative completion vs target</h2>
<table>
  <tr>
    <th>Instrument</th>
    <th class="num">Completed</th>
    <th class="num">Target</th>
    <th class="pct">% complete</th>
  </tr>
  <tr>
    <td>F1 — Facility Head</td>
    <td class="num">~~maketext("%d", f1_done)~~</td>
    <td class="num">~~maketext("%d", f1_target)~~</td>
    <td class="pct">~~maketext("%5.1f", 100.0 * f1_done / f1_target)~~ %</td>
  </tr>
  <tr>
    <td>F3 — Patient</td>
    <td class="num">~~maketext("%d", f3_done)~~</td>
    <td class="num">~~maketext("%d", f3_target)~~</td>
    <td class="pct">~~maketext("%5.1f", 100.0 * f3_done / f3_target)~~ %</td>
  </tr>
  <tr>
    <td>F4 — Household</td>
    <td class="num">~~maketext("%d", f4_done)~~</td>
    <td class="num">~~maketext("%d", f4_target)~~</td>
    <td class="pct">~~maketext("%5.1f", 100.0 * f4_done / f4_target)~~ %</td>
  </tr>
</table>

<h2>By region</h2>
<? { iterate REGION_CODE x F-series; emit one row per cell } ?>
<!-- region-by-instrument table goes here; built with nested forcase + inc()  -->

<h2>Replacement audit</h2>
<? { count REPLACEMENT_FLAG = 1 cases; flag clusters > 0.10 of sample } ?>
<!-- replacement-by-cluster table goes here -->

<p class="footer">Generated by UHC Year 2 CAPI app, build ~~maketext("%d", publishdate() / 1000)~~.</p>

</body>
</html>
```

#### 10.6.6 Refusal / replacement audit report

A third HTML report focused on Annex D compliance (see §10.11 below). Same pattern; the body iterates `FIELD_CONTROL` and counts:

- Refused-but-not-yet-replaced.
- Replaced this week.
- Per-facility refusal count (escalate when ≥ 3 refusals same facility).
- Cluster replacement rate vs the 5–10 % cap.

Save as `deliverables/CSPro/Reports/refusal-replacement-audit.html`. Carl reviews weekly with Survey Manager.

### 10.7 forcase with case_status filter

**Khurshid 2022-10-23** — *Tutorial on forcase Statement*. Cards at `3_Resources/Learning-Materials/mentors/khurshid-arshad/videos/2022-10-23_tutorial-on-forcase-statement_73vBCcGQOnA/techniques.md`.

For nightly batch summaries we want to enumerate **only partial** or **only complete** cases — without manually filtering inside the loop. Use `setaccess(DICT, partial, asc)` (or `complete`) before `forcase`.

#### 10.7.1 Pattern — partial cases only

**(Khurshid 2022-10-23 *Tutorial on forcase Statement @ 03:38*)** — *"If you only want to access partially saved cases we must use the dictionary access parameters. I am doing this with case_status."*

```cspro
function nightly_partial_resume_reminder()
   list partial_keys string;
   numeric partial_count;

   partial_keys.clear();   { critical — see gotcha below }

   setfile(F1_DICT, pathname(workingDir) + "..\data\f1\f1_data.csdb");
   setaccess(F1_DICT, partial, asc);   { partial-only filter, ascending }

   forcase F1_DICT do
      partial_keys.add(key(F1_DICT));
      inc(partial_count);
   enddo;

   { Emit a per-SE reminder file with the keys to resume tomorrow }
   setfile(reminder_file,
     pathname(workingDir) + maketext("reminder_%s.txt", strip(SE_ID)),
     create);
   filewrite(reminder_file,
     maketext("F1 partials assigned to you (%d): resume tomorrow morning.", partial_count));
   numeric i;
   i = 1;
   do while i <= partial_count
      filewrite(reminder_file, maketext("  %d. %s", i, partial_keys(i)));
      i = i + 1;
   enddo;
   close(reminder_file);
end;
```

> **Gotcha (Khurshid 2022-10-23)** — *"`interview_value_set.clear()` is mandatory — without it, every supervisor's 'view partial' launch grows the list by appending. Khurshid stresses this is the most common bug."* Apply the same discipline here — `partial_keys.clear()` at function entry.

#### 10.7.2 Pattern — complete cases only (final tabulation feed)

```cspro
function emit_complete_for_tabulation()
   numeric complete_count;
   complete_count = 0;

   setfile(F1_DICT, pathname(workingDir) + "..\data\f1\f1_data.csdb");
   setaccess(F1_DICT, complete, asc);

   setfile(out_file, pathname(workingDir) + "f1_complete_extract.csv", create);
   filewrite(out_file, "case_id,region,province,facility,disposition,completed_at");

   forcase F1_DICT do
      filewrite(out_file, maketext("%s,%s,%s,%s,%d,%s",
         strip(key(F1_DICT)),
         strip(maketext("%s", REGION_CODE)),
         strip(maketext("%s", PROVINCE_CODE)),
         strip(maketext("%s", FACILITY_CODE)),
         DISPOSITION,
         strip(timestring(SUBMIT_TIME))
      ));
      inc(complete_count);
   enddo;

   close(out_file);
   errmsg(maketext("Emitted %d complete F1 cases to extract.", complete_count));
end;
```

This is the data feed for nightly CSTab runs (§10.10) and the weekly client report aggregations.

### 10.8 Hot-fix protocol

A hot-fix is any change shipped during active fieldwork. The protocol below ensures the change is safe, traceable, and reaches every tablet before damage spreads. Cross-reference the architecture doc § hot-fix flow ([[00-Architecture]]) for the full diagram.

#### 10.8.1 Step-by-step

| Step | Actor | Activity |
|---|---|---|
| 1 | SE → STL | Bug surfaces in the field. SE reports to STL via `#capi-fieldwork-ops` Slack with case ID, F-series, screenshot if possible. |
| 2 | STL → Carl | STL escalates via Slack DM or `#capi-fieldwork-ops` with `@carl`. STL also files a row in `ISSUE-LOG.md`. |
| 3 | Carl | **Categorise**: data-only (CSBatch), spec-only (Phase 4 update), app-only (Phase 6 fix), schema (Phase 5 + Reformat). |
| 4 | Carl | **Build the fix** in the appropriate phase artefact. Generator-first, never hand-edit dcf or generated files. |
| 5 | Carl | **Desk test** in CSEntry Windows — replay the failing case through the fixed build. |
| 6 | Carl | **Bench test** per [[05-Phase-7-Testing]] — the regression mock-case suite must pass. |
| 7 | Carl | **Republish .pen** with `publishdate()` baked in (no manual constant). Optionally shorten the expiration window for this release if the bug is severe. |
| 8 | Carl | Push to CSWeb. CSWeb pushes to tablets via existing sync. `publishdate()` enforces uptake — every SE gets the fix on next sync. |
| 9 | Carl | Annotate `HOTFIXES.md` with: timestamp, bug summary, root cause, build version, impacted F-series, mitigation taken. |
| 10 | Carl | **Slack-first announcement** to `#capi-fieldwork-ops`: "F1 hot-fix v1.X.Y deployed. Issue: <one-line>. Fixes: <one-line>. SEs will pick up on next sync." |
| 11 | Carl + STL | Close the corresponding `ISSUE-LOG.md` row with the build version that resolves it. |

#### 10.8.2 Categorisation cheat-sheet

| Symptom | Category | Phase to revisit | Time-to-ship |
|---|---|---|---|
| One value in one case is wrong; instrument fine | Data-only | CSBatch (Phase 10 §10.9) on incoming data | Same day |
| Question wording is misleading; skip is wrong | Spec | Phase 4 spec → Phase 5 regen | 1–2 days |
| Validation message confusing; capture type wrong | App | Phase 6 wiring fix | Same day |
| Item type wrong (numeric should be alpha); record cardinality wrong | Schema | Phase 5 + Reformat (Khurshid 2023-09-21 SOP) | 2–3 days, requires Reformat-Data run |
| Sync silently dropping cases; CSWeb config drift | Sync-infra | Phase 8 server | Same day |
| Translation typo / mistranslation | Translation | Phase 4 translation bundle | Same day |

#### 10.8.3 Schema change escalation

Schema changes (item types, record cardinality, key-item changes) **break compatibility** with cases already captured against the old schema. The Reformat-Data SOP (per Khurshid 2023-09-21) is non-trivial:

1. Freeze captures temporarily — set `kill_switch` equivalent (post-message in `#capi-fieldwork-ops` "stop captures, server-side maintenance").
2. Pull all existing data from CSWeb to a holding store.
3. Apply Reformat-Data with the new dcf as target.
4. Validate transformed cases — count must match, key items must match, sentinel cases must round-trip.
5. Push reformatted dataset back to CSWeb.
6. Push new `.pen` with new schema.
7. Publish + announce.
8. Resume captures.

Avoid schema changes during fieldwork unless absolutely necessary. If the bug is "we're missing one item we never thought of", consider adding it as an **optional** additional record (cardinality 0..1) so existing cases don't need backfill.

#### 10.8.4 HOTFIXES.md format

Stored at `deliverables/CSPro/HOTFIXES.md`. One entry per hot-fix. Reverse-chronological.

```markdown
## 2026-08-12 14:30 MNL — F3 v1.3.2

**Bug**: Q42 (patient consent) skip incorrectly bypassed Q43–Q47 when respondent answered "Yes — partial consent".

**Root cause**: Phase 4 skip table treated `consent_value = 2` (partial) as fully-consented. Should route to Q43.

**Category**: Spec (Phase 4) + App (Phase 6).

**Fix**: Updated `F3-Skip-Logic-and-Validations.md` row Q42 → Q43; regenerated apc; ran bench-test mock case 12 (partial consent).

**Impacted F-series**: F3 only.

**Build**: F3.pen v1.3.2 (publishdate baked).

**Window shortened**: Yes — 2 days (vs default 5) given consent-related severity.

**Announced**: 2026-08-12 14:32 in #capi-fieldwork-ops.

**Verification**: SE-NCR-04 confirmed at 16:00 their tablet picked up new build on sync; replayed mock partial-consent case successfully.
```

### 10.9 CSBatch — batch editing on incoming data

Per the workflow template Phase 10 and Khurshid's CSBatch corpus (notably **Khurshid 2022-12-31 *Initialize Hot Decks Using Save Arrays***), batch editing has four standard passes:

1. **Structure** — every case has the records the dcf says it should.
2. **Validity** — every value is within its declared range / value-set.
3. **Consistency** — cross-field rules hold (skip integrity, derived-field consistency).
4. **Imputation** — fill missing items via hot-deck or rule-based imputation.

For UHC Year 2, we run passes 1–3 on every nightly delta of incoming data. Pass 4 (imputation) is reserved for end-of-fieldwork closeout (Phase 11) so we never imputed-on-imputed values.

#### 10.9.1 CSBatch app structure

Stored at `deliverables/CSPro/Batch/F1-edits.bch` (and parallels for F3, F4). Each batch app declares the dcf as input and emits:

- A cleaned `.dat` / `.csdb` output.
- An audit-log `.txt` per pass with every flag raised, per case.

#### 10.9.2 Paste-ready F1 batch — structure + validity passes

```cspro
PROC GLOBAL
file structure_log;
file validity_log;
numeric struct_flags, valid_flags;

PROC F1_DICT

preproc
   { Open audit logs once per batch run }
   setfile(structure_log,
       pathname(workingDir) + "logs/f1_structure_" + maketext("%d", systemdate()) + ".txt",
       create);
   setfile(validity_log,
       pathname(workingDir) + "logs/f1_validity_" + maketext("%d", systemdate()) + ".txt",
       create);
   filewrite(structure_log, "F1 Structure pass — " + timestring(stat(systime)));
   filewrite(validity_log,  "F1 Validity pass  — " + timestring(stat(systime)));

postproc
   filewrite(structure_log, maketext("Total structure flags: %d", struct_flags));
   filewrite(validity_log,  maketext("Total validity flags:  %d", valid_flags));
   close(structure_log);
   close(validity_log);

PROC F1_HEADER

postproc
   { ----- Structure pass — header completeness ----- }
   if FACILITY_CODE = "" then
      filewrite(structure_log,
        maketext("Case %s: missing FACILITY_CODE", strip(key(F1_DICT))));
      inc(struct_flags);
   endif;
   if INTERVIEW_DATE = notappl or INTERVIEW_DATE = 0 then
      filewrite(structure_log,
        maketext("Case %s: missing INTERVIEW_DATE", strip(key(F1_DICT))));
      inc(struct_flags);
   endif;
   if SE_ID = "" then
      filewrite(structure_log,
        maketext("Case %s: missing SE_ID", strip(key(F1_DICT))));
      inc(struct_flags);
   endif;

   { ----- Validity pass — header value ranges ----- }
   if FACILITY_TYPE < 1 or FACILITY_TYPE > 7 then
      filewrite(validity_log,
        maketext("Case %s: FACILITY_TYPE %d out of range [1..7]",
          strip(key(F1_DICT)), FACILITY_TYPE));
      inc(valid_flags);
   endif;
   if OWNERSHIP < 1 or OWNERSHIP > 5 then
      filewrite(validity_log,
        maketext("Case %s: OWNERSHIP %d out of range [1..5]",
          strip(key(F1_DICT)), OWNERSHIP));
      inc(valid_flags);
   endif;

PROC SECTION_A

postproc
   { Section-A items — all numeric, range 0..9999 }
   if Q_A1 < 0 or Q_A1 > 9999 then
      filewrite(validity_log,
        maketext("Case %s: Q_A1 %d out of range",
          strip(key(F1_DICT)), Q_A1));
      inc(valid_flags);
   endif;

PROC SECTION_B

postproc
   { ----- Consistency: Q_B1 + Q_B2 cannot exceed Q_A1 ----- }
   if Q_B1 + Q_B2 > Q_A1 then
      filewrite(validity_log,
        maketext("Case %s: Q_B1+Q_B2 (%d) exceeds Q_A1 (%d) — inconsistency",
          strip(key(F1_DICT)), Q_B1 + Q_B2, Q_A1));
      inc(valid_flags);
   endif;

   { ----- Skip-integrity: if Q_B0 = 2 (No) then Q_B1..B7 must be blank ----- }
   if Q_B0 = 2 and (Q_B1 <> notappl or Q_B2 <> notappl or Q_B3 <> notappl) then
      filewrite(validity_log,
        maketext("Case %s: Q_B0=2 (No) but Q_B1..3 not blank — skip violated",
          strip(key(F1_DICT))));
      inc(valid_flags);
   endif;
```

Run nightly at 23:30 (after the 22:00 sync window has flushed). The audit-log files feed the next morning's stand-up — Carl scans for spikes and queues fixes.

> **Note** — `stat(systime)` for the audit log header is per the "audit log via stat()" convention from the Khurshid 2022-12-31 corpus.

#### 10.9.3 Imputation deferred to Phase 11

We do **not** run hot-deck imputation during fieldwork. Reasons:

- Imputation rewrites missing items; if an SE later collects the missing value, we get a conflict.
- Imputation is statistical, not factual — it should only happen on the *final* dataset we deliver, not on the rolling daily delta.
- Imputation specs need close coordination with the analysis team (DOH-PMSMD + analytics) — they own the imputation method (donor selection, hot-deck initialization order, etc.).

Hot-deck initialization patterns from Khurshid 2022-12-31 *Initialize Hot Decks Using Save Arrays* are referenced in [[08-Phase-11-Closeout-Export]] § imputation.

### 10.10 CSTab — interim tabulation for client reports

Per the workflow template Phase 10 + Annex I (the analysis-plan tabulation specs — 51 dummy tables across F1 / F2 / F3 / F4).

#### 10.10.1 Cadence

Monthly interim tab packs. Carl + Survey Manager produce. Project Coordinator delivers to DOH-PMSMD.

CSTab handles cross-tabs (one categorical against one or more others). For regression-style or multilevel analysis, hand off the cleaned dataset to the analytics team for Stata / R.

#### 10.10.2 Paste-ready CSTab — A1 dummy table

Annex I dummy table A1 — *Facility Head response by region × ownership type*. Stored as `deliverables/CSPro/Tab/F1-A1.cts` (CSTab table specification).

```
{ F1-A1.cts — Facility Head responses by region × ownership type }
{ Annex I dummy table A1                                          }

universe (F1_DICT.DISPOSITION = 1)   { Completed only }

table A1 = REGION_CODE * OWNERSHIP * count;

stub  REGION_CODE
       label "Region";

head   OWNERSHIP
       label "Ownership type";

cell   count
       label "Number of facilities";
       format width=6 decimals=0;

total  REGION_CODE   label "All regions";
total  OWNERSHIP     label "All ownership types";
```

Wire into the monthly interim tab pack; export as PDF + xlsx; bundle alongside the SE-cluster completion appendix.

#### 10.10.3 Tab pack contents

Per Annex I, the tab pack covers (representative, not exhaustive):

| Table ID | Title | Driving F-series |
|---|---|---|
| A1 | Facility Head responses by region × ownership type | F1 |
| A2 | Facility Head responses by region × facility type | F1 |
| A3 | F1 completion rate by cluster | F1 |
| B1 | Patient responses by region × patient type | F3 |
| B2 | F3 partial vs complete by region | F3 |
| B3 | F3b patient-listing drift indicator (May 6) | F3b |
| C1 | Household responses by region × household type | F4 |
| C2 | F4 completion rate by cluster | F4 |
| D1 | Refusal reasons distribution | F1 + F3 + F4 |
| D2 | Replacement counts by cluster (vs 5–10 % cap) | F1 |

Each table has its own `.cts` definition under `deliverables/CSPro/Tab/`. Carl maintains the index in `deliverables/CSPro/Tab/INDEX.md`.

### 10.11 Replacement protocol enforcement (Annex D)

Annex D codifies the substitution rules. The CAPI side both **records** the replacement metadata and **flags** violations of the rules.

#### 10.11.1 Rules summary

- **≥3-visit minimum contact rule** — before any facility / household is declared non-respondent, the SE must attempt at least 3 visits at different times of day, with at least one weekend and one weekday attempt.
- **Same-stratum substitution** — replacement must come from the same stratum (region × ownership × facility-type for F1; region × cluster for F3; region × cluster × household-type for F4).
- **5–10 % facility replacement cap** — across the whole engagement, replacements cannot exceed 10 % of sampled facilities; warning at 5 %.
- **Enumerator discretion explicitly banned** — the SE never picks the replacement; the STL or supervisor app does (using stored replacement queue).

#### 10.11.2 CAPI capture

In FIELD_CONTROL (per [[04-Phase-6-Build-CAPI-App]] § FIELD_CONTROL), on every case capture:

- `VISIT_COUNT` — incremented per visit attempt; max captured.
- `VISIT_DATES` (array) — each attempt's date.
- `VISIT_OUTCOMES` (array) — outcome per visit.
- `REPLACEMENT_FLAG` — 0 = original sample; 1 = replacement.
- `REPLACED_FACILITY_ID` — when REPLACEMENT_FLAG = 1, the original facility ID being replaced.
- `REPLACEMENT_REASON` — coded reason (refused / not-found / closed / out-of-scope / other).
- `STL_APPROVAL_TIMESTAMP` — when REPLACEMENT_FLAG = 1, the moment STL approved.

#### 10.11.3 Validation rules

In Phase 6 PROC, before allowing case-save:

```cspro
PROC FIELD_CONTROL

postproc
   { ----- ≥3-visit rule before non-respondent disposition ----- }
   if DISPOSITION in 4, 6, 7 and VISIT_COUNT < 3 then
      errmsg("Annex D rule: minimum 3 visit attempts required before declaring non-respondent. Current attempts: %d", VISIT_COUNT);
      reenter;
   endif;

   { ----- Replacement requires STL approval timestamp ----- }
   if REPLACEMENT_FLAG = 1 and STL_APPROVAL_TIMESTAMP = notappl then
      errmsg("Annex D rule: replacement requires STL approval. Contact STL.");
      reenter;
   endif;

   { ----- Replacement requires reason ----- }
   if REPLACEMENT_FLAG = 1 and REPLACEMENT_REASON = notappl then
      errmsg("Annex D rule: replacement reason required.");
      reenter;
   endif;
```

#### 10.11.4 Cluster-level cap monitoring

The 5–10 % cap is checked at the **STL / cluster level**, not per-case. Run nightly as part of the daily HTML field summary anomaly section (§10.6.3), or as a separate refusal/replacement audit (§10.6.6):

```cspro
function cluster_replacement_audit()
   numeric total_in_cluster, replaced_in_cluster;
   numeric pct_replaced;

   setfile(F1_DICT, pathname(workingDir) + "..\data\f1\f1_data.csdb");
   forcase F1_DICT do
      if CLUSTER_CODE = current_cluster then
         inc(total_in_cluster);
         if REPLACEMENT_FLAG = 1 then
            inc(replaced_in_cluster);
         endif;
      endif;
   enddo;

   if total_in_cluster > 0 then
      pct_replaced = 100.0 * replaced_in_cluster / total_in_cluster;

      if pct_replaced >= 10.0 then
         errmsg("Cluster %s replacement rate %5.1f%% exceeds 10%% cap. Halt replacements.",
            current_cluster, pct_replaced);
      else if pct_replaced >= 5.0 then
         warning("Cluster %s replacement rate %5.1f%% — at or above 5%% warning threshold.",
            current_cluster, pct_replaced);
      endif;
   endif;
end;
```

Surfaces in the supervisor app menu and in the weekly client report.

### 10.12 Issue log discipline

Every field-reported anomaly is captured. No exceptions. The discipline is what makes Phase 11's lessons-learned entry possible.

#### 10.12.1 Format

`deliverables/CSPro/ISSUE-LOG.md`. Markdown table, append-only.

```markdown
| Date | Reporter | F-series | Case ID | Severity | Type | Description | Resolution | Fixed in build |
|---|---|---|---|---|---|---|---|---|
| 2026-08-12 13:42 | SE-NCR-04 | F3 | NCR-1339-Q1234 | High | spec | Q42 partial-consent skip routed past Q43 | Updated skip table; F3 v1.3.2 hot-fix | F3 v1.3.2 |
| 2026-08-12 15:11 | STL-R8-01 | F1 | — | Medium | sync | Tablet T-R8-09 last-sync >24h despite sync attempts | Reseated SIM; tablet swap arranged | n/a |
| 2026-08-13 09:05 | SE-R4B-02 | F4 | R4B-1751-H0089 | Low | translation | Tagalog wording for Q3.4 awkward; respondent confused | Translation update queued for next bundle | n/a (pending) |
```

#### 10.12.2 Fields

- **Date** — `YYYY-MM-DD HH:MM` local (MNL).
- **Reporter** — SE / STL / Carl / Project Coordinator / Survey Manager.
- **F-series** — F1 / F3 / F3a / F3b / F4.
- **Case ID** — concrete case identifier when applicable (use FIELD_CONTROL key); else `—`.
- **Severity** — Critical / High / Medium / Low (same scale as Phase 9).
- **Type** — instrument / spec / app-ux / sync-infra / field-protocol / translation / data / hardware.
- **Description** — concise one-line.
- **Resolution** — what was done (or "pending" if open).
- **Fixed in build** — concrete build version, or `n/a`, or `pending`.

#### 10.12.3 Working with the log

- **Add immediately** when the issue is reported. Don't wait until "I have a fix".
- **Slack-first**, then log — but always log; Slack is ephemeral.
- **Closure requires build version** — "fixed" without a build version is not closed.
- **Weekly review** — Carl + Survey Manager review every Friday before the weekly client report goes out.

### 10.13 Communication protocol during fieldwork

#### 10.13.1 Channels

| Channel | Purpose | Audience |
|---|---|---|
| `#capi-fieldwork-ops` | Daily ops, sync issues, anomalies, hot-fix announcements | SEs, STLs, Carl, Shan |
| `#capi-fieldwork-uat` | Pretest issues if Phase 9 still active | Pretest SEs, STLs, Carl, Survey Manager |
| `#aspsi-doh-internal` | Project-management traffic, weekly digest, escalations | ASPSI staff, Carl, Project Coordinator |
| Email — Project Coordinator → DOH-PMSMD | Weekly client digest, ad-hoc escalations | DOH-PMSMD; **never Carl direct** |

Parallel to the F2 PWA's `#f2-pwa-uat` (per [[06-Phase-8-CSWeb-and-Tablets]] § F2 sibling notes), `#capi-fieldwork-uat` runs only during Phase 9. After Phase 9 closes, archive read-only and consolidate to `#capi-fieldwork-ops`.

#### 10.13.2 Ground rules

- **No PII in any channel.** Case IDs and facility codes only.
- **Client-facing comms only via Project Coordinator.** Carl never emails DOH-PMSMD direct, even for "quick clarifications".
- **Hot-fix announcements: Slack first, GitHub issue follow-up.** The Slack message has the immediate "what changed and what should I do"; the GitHub issue (under the project's tracking repo) has the durable history.
- **Weekly client digest** — Project Coordinator owns; Carl supplies the weekly client HTML report (§10.6.5).
- **Escalation tree**: SE → STL → Carl/Shan → Project Coordinator → Project Lead → Survey Manager → DOH-PMSMD.

### 10.14 Field-ops toolkit summary — closing the audit gap

The May 2026 audit surfaced specific UHC field-ops artefacts that were missing or under-specified. This section is the closure list. Every item is owned by Carl and committed under `deliverables/` before main fieldwork begins.

| Artefact | Path | Source / Khurshid card | Phase wired |
|---|---|---|---|
| `Validators.apc` | `deliverables/CSPro/Common/Validators.apc` | [[04-Phase-6-Build-CAPI-App]] §validators | Phase 6 |
| `Resume-Handlers.apc` (OnStop + savepartial) | `deliverables/CSPro/Common/Resume-Handlers.apc` | [[04-Phase-6-Build-CAPI-App]] §savepartial; Khurshid 2022-10-23 | Phase 6 |
| `value-labels-csv-export.py` | `deliverables/CSPro/Tools/value-labels-csv-export.py` | Khurshid 2022-05-05 | Phase 8 / 10 |
| `daily-summary-html.fmf-template` | `deliverables/CSPro/Reports/daily-field-summary.html` | Khurshid 2022-12-05 | Phase 10 |
| `weekly-client-report.html-template` | `deliverables/CSPro/Reports/weekly-client-report.html` | Khurshid 2022-12-05 | Phase 10 |
| `refusal-replacement-audit.html` | `deliverables/CSPro/Reports/refusal-replacement-audit.html` | Khurshid 2022-12-05 | Phase 10 |
| `daily-summary-text.apc` (plain-text fallback) | `deliverables/CSPro/Reports/daily-summary-text.apc` | Khurshid 2022-09-05 + 2022-12-05 | Phase 10 |
| `Map-Case-Listing-config.md` | `deliverables/CSPro/Common/Map-Case-Listing-config.md` | Khurshid 2022-07-06 | Phase 6 / 10 |
| `Map-Object-Pattern.apc` (rich map with markers) | `deliverables/CSPro/Common/Map-Object-Pattern.apc` | Khurshid 2022-07-06 | Phase 6 / 10 |
| `publishdate-check.apc` | `deliverables/CSPro/Common/publishdate-check.apc` | Khurshid 2022-10-08 | Phase 6 / 10 |
| `synctime-check.apc` | `deliverables/CSPro/Common/synctime-check.apc` | Khurshid 2025-02-20 | Phase 6 / 10 |
| `F1-edits.bch`, `F3-edits.bch`, `F4-edits.bch` | `deliverables/CSPro/Batch/` | Workflow template Phase 10 + Khurshid 2022-12-31 | Phase 10 |
| `F1-A1.cts` (and Annex I siblings) | `deliverables/CSPro/Tab/` | Workflow template Phase 10 + Annex I | Phase 10 |
| `HOTFIXES.md` | `deliverables/CSPro/HOTFIXES.md` | Hot-fix protocol §10.8 | Phase 10 |
| `ISSUE-LOG.md` | `deliverables/CSPro/ISSUE-LOG.md` | Issue log discipline §10.12 | Phase 9 / 10 |
| `Endorsement-Letter-CAPI-Paragraph.md` | `deliverables/Survey-Manual/Endorsement-Letter-CAPI-Paragraph.md` | §9.1.4 | Phase 9 |
| `Data-Security-Plan.md` | `deliverables/Survey-Manual/Data-Security-Plan.md` | §9.1.2 | Phase 9 |

Once every row in this table has a green-tick on the master checklist, the field-ops gap is closed.

### Phase 10 exit criteria

- [ ] Fieldwork running with daily 22:00 MNL sync verification on every cluster, every day.
- [ ] Hot-fix protocol exercised at least once (planned drill: deliberately publish a benign no-op build update with a shortened publishdate window, verify all tablets pick up within 2 days).
- [ ] Daily HTML field summary delivered to STLs at 22:30 MNL, every day fieldwork is active.
- [ ] Weekly client HTML report delivered to DOH-PMSMD via Project Coordinator, every Monday.
- [ ] Replacement audit clean — every cluster < 10 % replacement rate; no enumerator-discretion replacements; every replacement carries STL approval timestamp + reason.
- [ ] CSBatch nightly passes (structure + validity + consistency) running clean — flag rate trending down over the engagement.
- [ ] CSTab interim tab packs delivered monthly per Annex I.
- [ ] HOTFIXES.md and ISSUE-LOG.md are current — every Slack-reported issue has a ledger row.
- [ ] All field-ops toolkit artefacts (§10.14) committed and referenced from this chapter.

---

## Appendix — Cross-reference index

| Topic | Where |
|---|---|
| dcf generator + value-set CSV exporter | [[03-Phase-3-5-Spec-and-Generators]] |
| FIELD_CONTROL design | [[04-Phase-6-Build-CAPI-App]] |
| Validators.apc + Resume-Handlers.apc | [[04-Phase-6-Build-CAPI-App]] |
| Translation bundles + locale switcher | [[04-Phase-6-Build-CAPI-App]] §i18n |
| Bench testing + mock cases | [[05-Phase-7-Testing]] |
| CSWeb roles + sync architecture | [[06-Phase-8-CSWeb-and-Tablets]] §8.x |
| publishdate Phase 8 wiring | [[06-Phase-8-CSWeb-and-Tablets]] §8.16 |
| synctime Phase 8 wiring | [[06-Phase-8-CSWeb-and-Tablets]] §8.17 |
| Closeout export, codebook, Reformat-Data SOP | [[08-Phase-11-Closeout-Export]] |
| Hot-fix architectural flow | [[00-Architecture]] § hot-fix flow |
| Roles + handoff matrix | [[01-Roles-and-Handoffs]] |

## Khurshid technique-card index

| Card | Source | Used in |
|---|---|---|
| Map Case Listing — quick GPS overlay | **(Khurshid 2022-07-06)** | §10.2.2 |
| Map object: addListing + setBaseMap + show | **(Khurshid 2022-07-06)** | §10.2.3 |
| Five-function sampling pipeline | **(Khurshid 2022-09-05)** | §10.6.4, §10.14 |
| Build a layout-controlled report with file_handler + filewrite | **(Khurshid 2022-09-05)** | §10.6.4 |
| forcase with `inc()` accumulator | **(Khurshid 2022-09-05)** | §10.6.3, §10.9 |
| HTML report with `<? ?>` PROC blocks + `~~ ~~` fills | **(Khurshid 2022-12-05)** | §10.6.3, §10.6.5 |
| Plain-text report via setfile + filewrite + execsystem | **(Khurshid 2022-12-05)** | §10.6.4 |
| Use `<?...?>` for blocks, `~~...~~` for fills | **(Khurshid 2022-12-05)** | §10.6.2 |
| forcase with case_status filter (partial-only / complete-only) | **(Khurshid 2022-10-23)** | §10.7 |
| list.add() + list.show() picker | **(Khurshid 2022-10-23)** | §10.7.1 |
| publishdate() force-update | **(Khurshid 2022-10-08)** | §10.4 |
| maketext month-name lookup | **(Khurshid 2022-10-08)** | §10.4.2, §10.6 |
| synctime() per-dictionary + per-case | **(Khurshid 2025-02-20)** | §10.5 |
| CSV import for sync-report value labels | **(Khurshid 2022-05-05)** | §10.3 |
| CSWeb roles model | **(Khurshid 2022-05-05)** | §9.5.3 |
| synchronize_file() get/put | **(Khurshid 2022-05-05)** | (referenced in [[06-Phase-8-CSWeb-and-Tablets]]) |

---

## Next

Continue to [[08-Phase-11-Closeout-Export]] — final dataset export, codebook, lessons-learned entry, archival.
