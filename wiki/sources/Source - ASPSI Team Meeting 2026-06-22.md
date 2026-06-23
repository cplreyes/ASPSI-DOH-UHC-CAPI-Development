---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/scrum/standups/2026-06-22-aspsi-team-meeting]]"
date_ingested: 2026-06-22
tags: [team-meeting, meeting-notes, capi-status, standup, monitoring-dashboard, timeline-extension, uat-round-5, f2-server-migration, survey-manual]
---

# Source — ASPSI Team Meeting 2026-06-22

> Internal ASPSI team meeting, Monday 2026-06-22. Source is **Carl's own stand-up notes** (first-person, 3 stand-up points + an issues-tackled snapshot) plus the **team discussion outcomes** captured at the bottom. Same brief format as the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - ASPSI Team Meeting 2026-05-18|2026-05-18 meeting]]. Headline outcome: the **field-monitoring dashboard** is being positioned as the **basis for a timeline-extension request** (Training → Aug, Rollout → Sep).

## Carl's stand-up

### 1. Last week

- **F3/F4 mid-interview stop/withdraw handling** — working on device; finished vs. partial cases now cleanly separated in the data. (Raised by **[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Marriz|Marriz]]**.)
- **Supervisor workflow / review tool (v1)** built — coverage vs. plan, partials, and data-quality flags.
- **[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSWeb|CSWeb]] monitoring dashboard is live** — cases by instrument, region, status, date; improved maps and visualization.
- **UAT Round 5 OPENED** (June 22–27) across all surfaces (F1, F3, F4, F2, Admin, CSWeb).

### 2. This week

- **Continued development together with the testers** — run Round 5 and turn feedback into fixes as it comes in.
- **Align with the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - DOH UHC Year 2 Survey Manual|Survey Manual]], not just the instruments-only MVP** — broaden from the forms to the full survey operation (monitoring, supervisor review, field-ops/training). Explicit move away from the earlier "Survey Instruments only (MVP)" scope note.
- **Get the Supervisor review tool ready to go live.**
- **Plan the move of the F2 Survey + Admin Portal off Cloudflare to our own server** — free-tier limits are being hit, and that setup won't carry the full intended user load once live (still in development now).

#### Issues tackled per instrument so far (resolved through UAT)

| Instrument | Resolved |
|---|---|
| F1 — Facility Head | 51 |
| F3 — Patient | 43 |
| F4 — Household | 124 |
| F2 — HCW survey + Admin Portal | 79 |
| CSWeb | 7 |
| PLF | 5 |

Round 5 (June 22–27) just opened — 6 logged, 0 closed yet (Day 1). Instrument rows sum to 309 of 644 total closed; the remainder are infra/docs/process/field-ops issues with no instrument tag.

### 3. Blockers / constraints

- **None reported.** ("No blockers yet.")

## Items routed to the ASPSI RAs (post-meeting breakout)

These were pulled out of the stand-up so the team meeting stays high-level; each is tackled with the concerned person afterward:

- **PhilHealth option lists** — the 3 images from [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - HCW CAPI Comments Matrix (Myra answers 2026-05-21)|Kidd]]'s June 9 email, to build F3 Q38.1/Q38.2 and F4 Q45.1/Q45.2 (PhilHealth registration reinstatement).
- **QA-supervisor names** — to bring the Supervisor tool live.
- **Translations** — Hiligaynon (F3 & F4), Tagalog and Ilocano (F1–F4) still pending from ASPSI.
- **Checkbox style** piloted on F3 Q148 — decide whether to roll it out to the other ~60 select-all questions or keep on Q148 only.
- **Supervisor app Phase 2** (Bluetooth sync hub) — build now or keep deferred.

## Team discussion — Monitoring dashboard as basis for an extension request

The team's central ask is a **field-monitoring dashboard / visualizations** that surface, ahead of time:

- Overall progress and **what is lagging**
- **Coverage per site**
- **Enumerator performance metrics**
- Regions, lag, completion rates, coverage — visible in advance

The explicit purpose discussed: this data becomes the **basis for a request of extension**:

- **August** — for **Training**
- **September** — for **Rollout**

> [!note] Strategic read
> The dashboard is no longer just an ops tool — it's the evidentiary backbone for a schedule-extension ask to DOH. An Aug-Training / Sep-Rollout timeline pushes the conduct + rollout well past the official close in the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Timetable of Activities|Timetable of Activities]] (project close Aug 14, 2026). See the contradiction callout below.

## CAPI-side implications for Carl

| Item | Implication |
|---|---|
| **Survey-Manual alignment (beyond MVP)** | Scope broadens from the four instruments to the full survey operation — monitoring, supervisor review, field-ops/training. Consistent with the Sprint 011 reframe of "CAPI field-readiness" as a standing workstream. |
| **F2 server migration** | Net-new infra scope. Cloudflare free-tier limits are an active constraint; the PWA on free CF won't carry the intended HCW user load. A move to an own/managed server (the same posture as the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSWeb|CSWeb]] VPS) needs sizing + a migration plan. |
| **Dashboard = extension basis** | Raises the priority of completeness/accuracy of the monitoring views (coverage per site, enumerator metrics, lag by region) — these now carry an external, contractual argument, not just internal visibility. |
| **Round 5 live** | Tester-driven fixes are the week's primary throughput; 309 instrument issues resolved to date frames the maturity argument. |

> [!warning] Contradiction / shift — official timeline vs. proposed extension
> The [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Timetable of Activities|Timetable of Activities]] (Table 14, Revised Inception Report) sets **Conduct of Survey at Months 4–7** and **project close at Aug 14, 2026**, with training in Months 3–4. This meeting proposes **Training in August and Rollout in September 2026** — a multi-month slip beyond the contracted schedule. Recorded as a **proposed extension request under preparation**, not an approved change. The schedule/penalty exposure tied to those dates lives in [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Signed CSA Dec 15 2025|the signed CSA]] (1%/day late penalty); the extension decision is ASPSI/DOH-lane, out of Data Programmer scope.

## Cross-references

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - ASPSI Team Meeting 2026-05-18|Prior stand-up meeting, 2026-05-18]] — established the CSWeb-VPS / field-visibility intent that this dashboard realizes.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSWeb|CSWeb]] — host of the live monitoring dashboard + the migration-target posture.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Timetable of Activities|Timetable of Activities]] — the official schedule the proposed extension would move.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Quality Over Deadline|Quality Over Deadline]] — the standing stance the extension request operationalizes (hold quality, move the date with evidence).
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Marriz|Marriz]] — Data Manager; flagged the F3/F4 stop/withdraw handling shipped last week.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F2 Admin Portal|F2 Admin Portal]] — co-migrates with the F2 Survey off Cloudflare.
