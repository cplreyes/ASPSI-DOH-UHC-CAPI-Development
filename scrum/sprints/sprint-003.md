---
sprint: 003
start: 2026-04-27
end: 2026-05-01
status: complete
archived: 2026-05-03
sprint_length: 1 week (5 working days)
deliverable_anchor: E2-F1-010 / Tranche 2 (deadline TBC from DOH)
---

# Sprint 003 — Close F1 sign-off, open FMF build, submit Tranche 2 on confirmation

## Sprint Goal

> **Close E2-F1-010 (F1 Designer sign-off) — two-sprint carry, must not leave this week.** Once F1 sign-off lands, open the FMF build in CSPro Designer for F1 (E3-F1-001 — generator skeleton is ready). E0-010 (define internal weekly status format) closes this sprint with no further deferral. Tranche 2 submission timing is ASPSI/PI lane, not a Sprint 003 deliverable for Carl.

## Committed Items

### Carry-forward from Sprint 002 (priority order)

- [ ] **E2-F1-010** F1 DCF opened in CSPro Designer, full validation walkthrough (including new case-control block: `SURVEY_CODE`, `INTERVIEWER_ID`, `DATE_STARTED`, `TIME_STARTED`, `AAPOR_DISPOSITION`, `FACILITY_NAME`, `FACILITY_ADDRESS`), bug list closed or explicitly deferred, sign-off note recorded `status::todo` `priority::critical` `estimate::4h`
- [ ] **E0-010** Define weekly status update format for ASPSI Management Committee (Carl → Juvy / Dr Claro / Dr Paunlagui) `status::todo` `priority::high` `estimate::2h`

### ASPSI / PI / PMO lane — informational only (NOT Data Programmer scope)

> Scope discipline: **E0-020** (SJREB status), **E0-032** (D2/D3/Tranche deadline tracking), **E0-032a** (DOH-PMSMD matrix coordination triage) are explicitly **not** Carl-owned per the signed CSA D1–D6 (Data Programmer scope = production of CAPI deliverables). They live in ASPSI ops / PI / PMO lane (Juvy / Dr Claro / Dr Paunlagui). Surface as project-level dependencies in `product-backlog.md` and the risk register, not as sprint-board commitments. CAPI-side fallout from the DOH matrix (specific F1/F2/F3/F4 revisions) is folded into the relevant E2/E3 instrument task — not tracked under E0-032a. (Memory: `feedback_data_programmer_scope.md`, `feedback_sjreb_out_of_scope.md`, `feedback_tranche_tracking_out_of_scope.md`, `feedback_e0_032a_out_of_scope.md`.)

### New for Sprint 003

- [ ] **E3-F1-001** F1 FMF Section A layout in CSPro Designer — generator skeleton (`FacilityHeadSurvey.generated.fmf`) is ready; Designer opens the file, applies form-layout-plan splits (per-subsection forms, no scrolling, roster-scrolls-alone), visual polish. Output: Designer-reviewed FMF saved as `FacilityHeadSurvey.fmf`. `status::todo` `priority::high` `estimate::4h`
- [x] **E4-PWA-013** F2 PWA auth re-arch Phase F production cutover — **DONE 2026-05-01**. Staging→main merged (5 conflict files resolved by taking staging wholesale per memory `project_main_staging_diverged_phase_f.md`); main deployed to `f2-pwa.pages.dev` via manual `wrangler pages deploy` (auto-deploy workflow now lives on main, future merges fire automatically); v1.3.0 milestone closed → release-notes pipeline auto-bumped package.json to v1.3.0, generated CHANGELOG, posted GitHub Release + Slack to `#f2-pwa-uat`. Soak gate explicitly waived by Carl ("fix all today"). Production now runs Worker JWT proxy + Verde Manual + 13 fixes (#19–#30 + #35 #45 #46). Smoke: prod canonical 200 OK, bundle hash CGY3qRWK. `status::done` `priority::critical` `actual::~3h cutover`

### Stretch (not committed)

- [ ] **E2-F3-010** F3 DCF Designer validation pass — verify case-control block in FIELD_CONTROL, full item walkthrough; sign-off note recorded `status::todo` `priority::medium` `estimate::3h`
- [ ] **E2-F4-010** F4 DCF Designer validation pass — same scope as F3 `status::todo` `priority::medium` `estimate::3h`
- [ ] **E0-008** Auto-standup retro-injection — extend `.claude/scripts/generate_standup.py` to read the prior sprint's `## Retrospective` Q4 ("One thing to change in Sprint N+1") and surface it as a Day 1 banner in the next sprint's first standup. Closes the ritual gap (Sprint 001→002 and Sprint 002→003 both had retro Q4 captured in `sprint-current.md` Daily Notes but not surfaced in the Day 1 daily standup). `status::todo` `priority::medium` `estimate::1h`

## Sprint Backlog Sizing

| Class | Items | Estimate |
|---|---|---|
| **Committed (must-finish)** | E2-F1-010, E0-010, E3-F1-001, E4-PWA-013 | ~12–13h |
| **Stretch** | E2-F3-010, E2-F4-010, E0-008 | ~7h |

> Capacity: ~25h solo-dev week. Hard commits are ~12–13h (including E4-PWA-013 Phase F decision Mon 2026-04-27) leaving room to pull stretch Designer validations (E2-F3-010 / E2-F4-010) into the week. Sprint board re-scoped 2026-05-01 (sprint close): E0-020 / E0-032 / E0-032a removed as out-of-Data-Programmer-scope; see "ASPSI / PI / PMO lane" section above.

## Daily Notes

### 2026-04-27 (Mon) — Sprint 003 kickoff

- **Carry-forward from Sprint 002 retro Q4:** Day 1 ritual — before writing the Today-plan table, grep deliverables/ for files modified since last standup to catch artifact drift. Prevents standup generator from narrating "pending" on already-done work. (Two occurrences Sprint 001 + Sprint 002.)
- **Tranche 2 status (informational only):** Extension in effect; official revised deadline pending from DOH as of 2026-04-25. Tracking + submission timing is ASPSI/PI lane (not Carl's). Surfaced here so Carl has awareness of where his deliverables sit vs. contracted milestones.

### 2026-04-28 (Tue) — Quiet day (no work)

- **Reconstructed 2026-05-03 during Sprint 003 archival.** Zero commits, zero `deliverables/`/`wiki/`/`scrum/` file changes. No auto-standup generated. Effectively a rest day. Auto-standup generator needs a "no-work-since-last-run" branch — caught at sprint close, candidate scope under E0-008 or sibling tooling task.

### 2026-05-01 (Fri) — Sprint 003 close, scope-discipline cleanup, F2 PWA Phase F cutover

- Out-of-scope items removed from sprint board: **E0-020** (SJREB tracking), **E0-032** (Tranche/deadline tracking), **E0-032a** (DOH-PMSMD matrix triage). All three are ASPSI/PI/PMO lane per CSA D1–D6 Data Programmer scope. They had leaked back into Sprint 003 despite the umbrella memory rule (`feedback_data_programmer_scope.md`); audit-on-detection discipline added to the SJREB + Tranche memories so this doesn't slip again.
- Net Sprint 003 commit drops from 6 → 4 (E2-F1-010, E0-010, E3-F1-001, E4-PWA-013) + 3 stretch (E2-F3-010, E2-F4-010, E0-008).
- **F2 PWA Phase F cutover sprint-day execution.** Carl directed "fix all today" on the F2 PWA. Closed all 15 v1.3.0 internal-QA issues + 3 Phase F-blocker triplet issues (#35 #45 #46). Five PRs squash-merged to staging (#47 #48 #49 #50 #51), staging deployed via manual wrangler. Then **E4-PWA-013** Phase F production cutover executed end-to-end: staging→main merge with 5-file conflict resolution (App.tsx, EnrollmentScreen.tsx, MultiSectionForm.tsx, Question.tsx, button.tsx — staging wholesale per memory), main deployed to `f2-pwa.pages.dev`, v1.3.0 milestone closed → auto release-notes pipeline fired (CHANGELOG bump, GitHub Release v1.3.0, Slack post to `#f2-pwa-uat`). Soak-gate waived per Carl directive. **Sprint 003 board: 1/4 committed done (E4-PWA-013); E2-F1-010 carries to Sprint 004 as a three-sprint carry.**
- **Open manual step:** admin password rotation pending Carl's hands-on (run `deliverables/F2/PWA/worker/scripts/hash-admin-password.mjs` interactively, then `wrangler secret put ADMIN_PASSWORD_HASH`).

## Inter-Sprint Activity (2026-05-02 Sat → 2026-05-03 Sun)

> Work that landed between Sprint 003 close (Fri 2026-05-01) and Sprint 004 start (Mon 2026-05-04). Tracked here for velocity bookkeeping; not part of Sprint 003 commitments. Items requiring follow-through carry into Sprint 004.

### 2026-05-02 (Sat) — F2 Admin Portal R2 gate cleared + Survey Manual + Wiki lint

- **F2 Admin Portal R2 gate CLEARED.** Cloudflare R2 enabled on `aspsi.doh.uhc.survey2.data@gmail.com` account; four buckets created (`f2-admin-staging`, `f2-admin-staging-preview`, `f2-admin`, `f2-admin-preview` — APAC, Standard storage class). Staging worker `f2-pwa-worker-staging` redeployed with `F2_ADMIN_R2` binding + `*/5 * * * *` cron trigger; `wrangler.toml` `[env.staging]` block updated. End-to-end Files-app smoke green on staging (upload → list → download → delete, 0 R2 orphans). Production buckets pre-provisioned but production worker NOT yet redeployed (admin portal bindings ride along with PR #54).
- **Survey Manual ingest + stakeholder section.** `raw/DOH UHC Year 2_Survey Manual Apr 28.docx` ingested via pandoc; companion deliverable `deliverables/Survey-Manual/CAPI-PWA-Stakeholder-Section_2026-05-02.md` drafted (10 sections covering CAPI + PWA channels, end-to-end data flow, quality controls, security/NDU, roles, outputs, items pending finalization).
- **Questionnaire Numbering Convention proposed and parked.** 11-digit decomposed case ID recommendation drafted at `wiki/concepts/Questionnaire Numbering Convention.md` (REGION 2 + PROVINCE_HUC 2 + CITY_MUNICIPALITY 2 + FACILITY_NO 2 + CASE_SEQ 3, stored as 5 separate ID items, displayed composite as `RRPPMMFFCCC`). Replaces current `QUESTIONNAIRE_NO` length-6 single-ID-item shape. **Nothing applied** — awaiting Carl's go-ahead. Memory pointer: `project_questionnaire_numbering_parked.md`.
- **Wiki lint pass.** Removed orphan `wiki/analyses/Analysis - DOH-PMSMD Matrix Feedback Triage.md` (out-of-scope per `feedback_e0_032a_out_of_scope.md`). Cleaned `index.md` F2 item-count line + Phase F cutover state. F3 item-count contradiction resolved (806 stands; 840 was in deleted analysis).
- **F2 Admin Portal concept page** added at `wiki/concepts/F2 Admin Portal.md`.

### 2026-05-03 (Sun) — F2 Admin Portal cross-platform QA pass (paused)

- **QA pass started 2026-05-02 evening, paused 2026-05-03 ~00:30 PHT.** E1 Chrome through Section F + G1/G2 ✅; G3/H/Z + E2-E5 not started. **3 HIGH bugs fixed in-session** (CORS, router, CORS-PATCH); **3 more findings logged for triage**. State preserved at memory `project_qa_pass_state_2026_05_02.md`. Resume target: Sprint 004 Day 1.
- **Sprint 003 archived 2026-05-03** (Mode D ran two days late).

## Definition of Done — Sprint 003

- [ ] **E2-F1-010** closed: F1 DCF walkthrough complete in CSPro Designer (including case-control block), bug list closed or deferred with rationale, sign-off note appended to `log.md`. *(Carried forward to Sprint 004 — three-sprint carry.)*
- [ ] **E3-F1-001** closed: F1 FMF Designer pass complete; `FacilityHeadSurvey.fmf` saved and reviewed. *(Carried forward to Sprint 004 — gated on E2-F1-010.)*
- [ ] **E0-010** closed: weekly status update format defined for Carl's internal tracking (per `feedback_weekly_status_internal_only.md`). *(Partially started 2026-05-01: `deliverables/comms/_weekly-status-template.md` + `weekly-status-2026-05-01.md` drafted; format not formalized as a closed deliverable. Carries to Sprint 004.)*
- [x] **E4-PWA-013** closed 2026-05-01: F2 PWA Phase F cutover **executed** — Worker JWT proxy promoted to production via staging→main merge + manual `wrangler pages deploy`; v1.3.0 milestone closed; release-notes pipeline auto-fired; soak gate explicitly waived per Carl direction. Recorded in `log.md` 2026-05-01 entry.
- [x] **Sprint 003 retrospective** (4 questions) filled 2026-05-03 (Mode D ran two days late — sprint window ended Fri 2026-05-01 but archival deferred to Sun); sprint archived to `scrum/sprints/sprint-003.md`; `sprint-current.md` reset for Sprint 004.

## Retrospective — Sprint 003

> 5-minute time-box. Four questions, fixed order. Written, not thought-through-only.
> Don't write self-congratulation; only write what changes next week's behavior.

### 1. Did the sprint goal land? (yes / partial / no — one line why)

Partial — F2 PWA Phase F cutover (E4-PWA-013) executed Fri 2026-05-01 with soak gate explicitly waived (production now serves Worker JWT proxy + Verde Manual + 13 v1.3.0 fixes); E2-F1-010 (F1 Designer sign-off — the carry-forward anchor) did not close and rolls into Sprint 004 as a three-sprint carry; E0-010 partial-start, E3-F1-001 untouched, all stretch deferred. Net committed: 1/4 done.

### 2. What surprised me? (process, not work — max 3 bullets)

- **Apr 28 (Tue, Day 2) vanished** — zero commits, zero file changes, no auto-standup file generated. First fully quiet sprint day in three sprints; the auto-standup generator silently skipped instead of emitting a "no-work-today" file, so the gap only surfaced at sprint close. Backfilled retroactively 2026-05-03.
- **Friday "fix all today" pivoted Sprint 003 from "F1 sign-off sprint" into "F2 PWA shipping sprint"** — 18 issues closed, v1.3.0 shipped, milestone auto-pipeline fired. Big mid-week scope shift; the original anchor (E2-F1-010) didn't get touched because Carl elected to ship F2 PWA + open F2 Admin Portal AP1–AP4 instead. Two of the three sprints in this project so far have ended with a Friday pivot away from the nominal anchor.
- **Out-of-scope leak repeated** — E0-020 (SJREB) / E0-032 (Tranche/deadline) / E0-032a (DOH-PMSMD matrix) leaked back into Sprint 003 commitments despite the umbrella `feedback_data_programmer_scope.md` rule. Caught at sprint-close audit Fri 2026-05-01; audit-on-detection discipline added to the SJREB + Tranche memories so this doesn't slip a fourth time.

### 3. Deadline exposure check — D2 / D3 / Tranche 2 slip days this sprint

Out of Data Programmer scope per CSA D1–D6 (`feedback_tranche_tracking_out_of_scope.md`). Informational only: D2 / D3 extension still in effect, official revised deadline pending DOH; ASPSI/PI/PMO lane handles tracking + submission timing. Carl's deliverable-side state at sprint close: F2 PWA in production at v1.3.0; F1 DCF Designer-ready (sign-off pending); F3/F4 Build-ready; F2 Admin Portal feature-complete on staging (PR #54 draft).

### 4. One thing to change in Sprint 004

**Sprint goal needs a 2-line goal block to acknowledge parallel workstreams.** Sprint 003 nominally anchored on E2-F1-010 (F1 Designer sign-off) but actually shipped F2 PWA Phase F + opened F2 Admin Portal AP1–AP4 sprints. Single-anchor sprint-goal framing pushes parallel-track work into "scope creep" or "stretch" when in truth Carl is running 3+ workstreams simultaneously (F1 design, F2 PWA, F2 Admin Portal cross-platform QA + soak). Sprint 004 should open with: **Goal A:** primary anchor (F1 Designer sign-off — three-sprint carry, must close); **Goal B:** parallel-track items in flight (F2 Admin Portal QA pass continuation + soak window; F1/F3/F4 Designer validation if Goal A clears).
