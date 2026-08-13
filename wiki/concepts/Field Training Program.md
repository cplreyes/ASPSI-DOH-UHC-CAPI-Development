---
type: concept
tags: [training, field-enumerator, field-supervisor, capi, deployment, assessment, fieldwork]
source_count: 3
---

# Field Training Program

The **cascade of five-day trainings that convert the built survey system into a deployed field operation** for the DOH UHC Survey Year 2. Two parallel programs authored by [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Dr Myra Silva-Javier|Myra]] and ingested 2026-07-29:

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Field Supervisor Training Program (MESJ 2026-07-28 FINAL)|Field Supervisors]] — **FINAL**, 16 modules, single venue (Los Baños, Laguna), **August 2026**.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Field Enumerator Training Program (v2 MESJ 2026-07)|Field Enumerators]] — **Version 2**, 15 modules, **four simultaneous sites**.

> [!note] Superseded by the July-30 cut — and the slide decks now exist
> [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - DOH Deliverable No. 2 (2026-07-31)|Deliverable No. 2]] (2026-07-31) carries **July 30 versions of both programs**. The structure below is unchanged and every open item listed at the bottom survives into the new cut. Two changes and one discovery:
> - The SE **Day-3 Household walkthrough is now assigned to the "UHC Y2 Project Team", not CReyes**.
> - FS field practice names five sites and 11 groups (adds **University Health Service**).
> - **ASPSI has already produced the full slide deck set**, including the CAPI modules Carl is named to teach — `fs_MODULE 6_1CAPI TOOL` / `se_MODULE 9_1CAPI TOOL` (33 pp, byte-identical between cohorts) plus four per-instrument decks. See [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/analyses/Analysis - Pretest Findings vs the CAPI Build|the analysis]] for how they relate to the decks Carl built on 2026-07-29.

## The shared five-day skeleton

Both programs run the same architecture, which is itself the design idea: **orientation → tools → supervision/monitoring → live practice → consolidation.**

| Day | Theme | Content |
|---|---|---|
| 0 | Baseline | Evening registration + **pre-test** |
| 1 | Survey orientation and field coordination | Study background, team structure, roles, coordination/entry protocols, ethics and consent |
| 2 | **CAPI and the questionnaires** | CAPI install/use + walkthroughs of all four instruments — **Carl (CReyes) in-charge in both programs** |
| 3 | Implementation and monitoring | FE: nonresponse, checking own work, communication, safety · FS: supervising recruitment/consent, monitoring performance, progress reporting, incidents, site closure |
| 4 | **Field practice** | Real facilities and communities, 2-person groups, observed |
| 5 | Consolidation | Debrief, admin/financial, **post-test** / FIP presentation, closing |

Common mechanics: **groups of 2** (one interviews, one observes and gives feedback, then switch) · only **2–3 modules** of a tool administered · interviews capped at **30 minutes** · inpatient/outpatient split in the morning and swapped in the afternoon · **Hour 8 = LLS** ([[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/LSS Meeting|LSS Meeting]]) · pre-reading (short protocol + questionnaires) issued before the training.

Common observation rubric — observers score: (1) introduction of self and study purpose; (2) ethical compliance; (3) maintaining neutrality; (4) appropriate probing; (5) thanking the respondent.

## Where they diverge

| | Field Enumerators | Field Supervisors |
|---|---|---|
| Status | Version 2 | **FINAL** (28 July) |
| Venue | 4 simultaneous clusters | 1 venue (Los Baños) |
| Cohort | 122–125 FEs (see contradiction) | 22 FSs |
| Spine deliverable | — | **Field Implementation Plan**, built in 3 instalments, presented Day 5 |
| Day 2 tools | F1, F2, Patients (Household on Day 3) | All four on Day 2 |
| Scoring | Weighted: 60% pre/post + 40% daily quizzes; 90/80/70 deployment bands | **4-point observational rubric** |
| Day 3 focus | Doing the work correctly | **Supervising others** doing the work |

## Why this matters to the CAPI build

**Training is the moment the system meets its users at scale** — roughly 145 people across five venues, most touching the CAPI application for the first time.

1. **Carl is a named trainer in both programs** (Day 2, "CReyes"). This is the first document assigning him specific training slots, and it converts the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CAPI Manual Materials (Myra 2026-06-17)|CAPI Manual]] and the CAPI training deck from documentation into **teaching materials with a delivery date**.
2. **The four-simultaneous-sites problem.** One named CAPI trainer cannot cover Pampanga, Laguna, Cebu and Cagayan de Oro concurrently. Resolution options: train-the-trainer for the RAs (the RAs are already co-named "CReyes & Assigned RAs"), recorded/asynchronous CAPI modules, staggered dates, or remote delivery. **An ASPSI scheduling decision** — surfaced, not owned by Carl.
3. **CAPI installation is a training activity, not an IT task.** Day 2 begins with "uploading the data entry applications / accessing the tablet-based questionnaires" for the whole cohort at once — mass first-install, which is where the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Synchronization|remove + re-add]] behaviour and server addressing matter most.
4. **~~Sync-URL cutover should precede training.~~ Reversed 2026-07-31.** The DOH-cleared C5 CAPI Manual and the ASPSI CAPI Tool deck both teach **`csweb.asiansocial.org/csweb/api`**. The sync API is dual-hosted so that address still works — which makes *keeping* it the cheapest option and a cutover the expensive one, since retiring it would contradict cleared documentation in front of the class. See [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/analyses/Analysis - Pretest Findings vs the CAPI Build|the analysis]].
5. **Supervisors are trained to monitor from CAPI data** (M11 "generate performance data from CAPI"; the Data Quality Assurance Plan's "validate CAPI submissions"). That is the Sync Dashboard, Map Report and data room — already built. Supervisor console credentials and a console walkthrough become a training prerequisite.
6. **The FS is first-line CAPI support.** The enumerator test answers make this explicit: on a sync failure, *"inform the Field Supervisor and follow troubleshooting procedures."* Troubleshooting content must therefore be pitched at supervisors, and the escalation path (FE → FS → project team) should match what the console actually lets an FS see.
7. **The assessment content is a de-facto acceptance test of our UX.** Items like "on a validation error, correct the identified item before submission" only make sense if the app's validation messages actually identify the item — which is a design commitment the build must keep honouring.

## Open items

> [!warning] Contradiction — FE headcount
> The enumerator program states **125 FEs** but its cluster table sums to **122**. Sizing of tablets, kits and tokens depends on the real number.

> [!warning] Numbering gap — Supervisor Module 15
> The FS schedule runs M1–M14 then jumps to **M16**; no Module 15 exists. Likely a renumbering artefact (admin/financial is M15 in the FE program).

Other observations worth confirming with ASPSI: the FE program has **two sections both labelled "E."** (field practice and assessment mechanics); several FE learning objectives still read *"as Field Supervisor"* and *"purpose of the Supervisor's Manual"*, apparently carried over from the supervisor source document; FE Day 3 schedules **Modules 12 and 13 both at 03:00**; and the field-practice hour flow **skips Hour 4** in both programs.

Relates to [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Survey Manual Set Architecture (Myra brainstorm 2026-06-08)|the manual-set architecture]] (which anticipated separate Enumerator, Supervisor, CAPI and Training manuals — these programs are that split arriving), [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Timetable of Activities|Timetable of Activities]], [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSWeb|CSWeb]], and [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/ASPSI|ASPSI]].
