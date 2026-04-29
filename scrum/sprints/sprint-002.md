---
sprint: 002
start: 2026-04-20
end: 2026-04-24
status: complete
sprint_length: 1 week (5 working days)
deliverable_anchor: D2 / Tranche 2 (40% due 2026-04-24)
archived: 2026-04-25
---

# Sprint 002 — Close F1 design, open F3/F4 logic-pass, submit Tranche 2 honestly

## Sprint Goal

> **Close F1 design cleanly, open the logic-pass gap on F3 and F4, and submit Tranche 2 as an honest status-to-date package.** F1 Designer sign-off (E2-F1-010) formalizes F1 as Design-complete. F3 skip-logic + validation spec (full) + F4 A–F slice bring both instruments up to the `logic-pass-before-build` standard before any FMF build work starts. Tranche 2 cover letter is reframed as extended-window progress-to-date, not a "D2 complete" claim — Juvy/Dr Claro route accordingly. Late-delivery penalty (1%/day, CSA §5) is a status checkpoint, not a forcing function to cut design steps.

## Committed Items

### Carry-forward from Sprint 001 (priority order)

- [ ] **E2-F1-010** F1 DCF opened in CSPro Designer, full validation walkthrough, bug list closed or explicitly deferred, sign-off note recorded `status::todo` `priority::critical` `estimate::4h`
- [ ] **E0-010** Define weekly status update format for ASPSI Management Committee `status::todo` `priority::high` `estimate::2h`
  - Scope updated per Apr 13 meeting notes: format is for Carl → Juvy / Dr Claro / Dr Paunlagui, not Carl → DOH directly.

> **E3-F1-001 (FMF Section A layout) deferred to Sprint 003.** Rationale: FMF work needs an upstream form-layout plan (per CSPro CAPI Strategies — forms per subsection, no scrolling, roster-scrolls-alone). Starting FMF this week without that plan would be the actual shortcut. Form-layout plan becomes a Sprint 003 prerequisite across F1/F3/F4.

### Recurring (every sprint)

- [ ] **E0-020** SJREB application status check via ASPSI `status::in-progress` `priority::critical`
- [ ] **E0-032** Track D2/D3/Tranche 2 deadline exposure this week `status::in-progress` `priority::high`

### New for Sprint 002

- [ ] **E0-032a** Triage DOH-PMSMD feedback on matrices (arrives Apr 20 Mon); route any requested revisions into F1/F2 build state; confirm Tranche 2 submission package with Juvy by Apr 23 `status::todo` `priority::critical` `estimate::TBD`
- [x] **E2-F3-001** F3 skip-logic + validation spec — full instrument, mirroring `F1-Skip-Logic-and-Validations.md` shape. Output: `deliverables/CSPro/F3/F3-Skip-Logic-and-Validations.md` (1133 lines, status: reviewed 2026-04-21; 14 sanity findings, skip-logic + validations for all 12 sections A–L, 15 CSPro PROC templates, 6 originally-open questions dispositioned — 1 routed to Juvy for Q31 IP_GROUP, 5 closed as spec-decisions). F3 Build-ready unblocked. `status::done` `priority::critical` `actual::~0h (spec already authored; review/edit pass only)`
- [x] **E2-F4-001** F4 skip-logic + validation spec — **full instrument A–Q** (rescoped from A–F slice after F3 closed early). Output: `deliverables/CSPro/F4/F4-Skip-Logic-and-Validations.md` (904 lines, status: draft 2026-04-21; 13 sanity findings including 2 P1 schema gaps — `C_HOUSEHOLD_ROSTER` and `J_HEALTH_SEEKING` must be made repeating in `generate_dcf.py` before CAPI build; skip-logic tables for all 17 sections; validations 3.1–3.18 with HARD/SOFT/GATE; 11 CSPro PROC templates including roster loop, WHO expenditure grid, catastrophic-expenditure check, bill-recall chain; 8 open questions dispositioned — 3 routed to ASPSI, 5 spec-decisions with override clause). Mirrors F3 spec shape. `status::done` `priority::critical` `actual::~3h (Apr 21 afternoon)`

### Stretch (not committed)

- [x] **F2 PWA pilot-readiness decision** — Decision: UAT Round 1 is the pilot. QA done (3/3 E2E pass), SUT deployed, `#f2-pwa-uat` Slack channel live, GitHub Issues UAT template active. Epic 3 F2 build closed 2026-04-23. CSPro F2 track = least priority. `status::done` `priority::medium` `actual::2026-04-23`

## Sprint Backlog Sizing

| Class | Items | Estimate |
|---|---|---|
| **Committed (must-finish)** | E2-F1-010, E0-010, E0-020, E0-032, E0-032a, **E2-F3-001 (done Day 2)**, **E2-F4-001 (done Day 2)** | ~6h remaining + E0-032a unbounded |
| **Stretch** | F2 PWA pilot-readiness decision | 30m decision + follow-through TBD |

> Capacity: ~25h solo-dev week. **E2-F3-001 and E2-F4-001 both closed Day 2**, plus a Day 2 F1 spec-alignment pass (~1.5h) that landed Capture-Helpers / PSGC-Cascade architecture into the F1 spec, epic-02, and epic-03. Remaining hard commits: **F1 Designer sign-off 4h (E2-F1-010) + E0-010 2h**, before E0-032a. 3 days remaining (Wed–Fri) with ~17h of capacity after logic-pass work. Use the released capacity to: (a) route the two P1 F4 schema gaps (`C_HOUSEHOLD_ROSTER` / `J_HEALTH_SEEKING` repeating) as `generate_dcf.py` patches (E2-F4-009) during this sprint, or (b) pull E3-F1-001 FMF Section A layout forward if the form-layout plan materializes mid-sprint. Decision depends on E0-032a size.

## Daily Notes

### 2026-04-20 (Mon)

- **Sprint 002 kickoff carry-forward from Sprint 001 retro Q4:** Require an on-disk artifact reference (file path at minimum, commit SHA preferred) before flipping any `status::done`. No status flip on meeting attendance, verbal confirmation, or "should be done by now." Applies to every item, including recurring ones.

### 2026-04-21 (Tue)

- **Sprint 002 scope reshaped Day 2 to anchor on quality, not payment window.** Initial plan deferred F3/F4 skip-logic specs to Sprint 003 to protect Tranche 2; Carl pushed back — "I don't want shortcuts, quality of development is my prio." Committed list now includes E2-F3-001 (full F3 spec) and E2-F4-001a (F4 A–F slice); E3-F1-001 (FMF Section A) deferred to Sprint 003 because FMF needs an upstream form-layout plan, not a rushed start. Tranche 2 cover letter reframed as status-to-date, not "D2 complete." Capacity is full-to-overflow by design; if E0-032a goes heavy, E2-F4-001a slides before F3 spec integrity is touched.
- **E2-F3-001 closed Day 2 — discovered spec was already authored.** On starting the F3 logic-pass, found `deliverables/CSPro/F3/F3-Skip-Logic-and-Validations.md` already existed at 1133 lines (status: draft) covering all 12 sections A–L with 14 sanity findings, skip-logic tables, HARD/SOFT/GATE validations, and 15 CSPro PROC templates. Auto-standup narrative said "pending" because the Python generator reads sprint-current.md + product-backlog.md but never reads git log — same failure mode the Sprint 001 retro flagged. Reviewed spec against the Apr 20 questionnaire + verified DCF state (15 records / 818 items, matches spec); added item-count drift provenance (387 Apr 08 → 818 Apr 20) and dispositioned the 6 "open" questions: only **Q31 IP_GROUP** needs Juvy (coded list or confirm alpha); five others were already internal spec-decisions, now marked as such with ASPSI override reserved. Flipped `status: draft` → `status: reviewed`. E2-F4-001 **rescoped A–F → full A–Q** given ~10h of released capacity, with A–M/N–Q fallback split kept in reserve.
- **Process flag for Sprint 002 retro:** auto-standup generator (`.claude/scripts/generate_standup.py`) doesn't read git log or file mtimes in `deliverables/` — narrative lags actual artifacts. Second occurrence. Fix for Sprint 003: either extend the generator to diff since last standup, or make it the Day 1 ritual to manually grep for artifact drift before writing the Today-plan table.
- **E2-F4-001 also closed Day 2 — ~3h, not 10–14h.** Wrote `deliverables/CSPro/F4/F4-Skip-Logic-and-Validations.md` full A–Q (904 lines) in one pass, mirroring the F3 spec shape onto the Apr 20 F4 DCF inventory (21 records / 611 items covering Q1–Q202). Initially logged two "P1 schema gaps" (`C_HOUSEHOLD_ROSTER` / `J_HEALTH_SEEKING` assumed non-repeating) — later re-verified and **closed both on 2026-04-21: generator and emitted DCF were already correct** (`C_HOUSEHOLD_ROSTER` at `max_occurs=20`; `J_HEALTH_SEEKING` intentionally respondent-level per Apr 20 source rephrase). Spec entries flipped to CLOSED-BY-VERIFICATION; E2-F4-009 closed. 3 questions batched to ASPSI (Q15 IP_GROUP list — shared with F3 Q31 ask; roster max-occ cap confirmation; Q202 worry-reasons option count); 5 spec-decisions documented with override clauses.
- **F1 skip-logic + validation spec aligned with F3/F4 architecture (Day 2 absorbed work).** Rewrote `deliverables/CSPro/F1/F1-Skip-Logic-and-Validations.md` to mirror the Apr 21 F3/F4 shape: §1 bug-dispositions table (6 items — 4 closed, 2 open for ASPSI: Q63 day/month buckets, SECONDARY_DATA structure); §3.1.1 GPS capture via `FACILITY_CAPTURE_GPS` + 6 `FACILITY_GPS_*` items; §3.1.2 verification photo via `VERIFICATION_PHOTO_FILENAME` (filename-reference pattern, `case-{QUESTIONNAIRE_NO}-verification.jpg`); §4.15 PSGC cascade via `onfocus` + `loadcase()` + `setvalueset()` (shared `PSGC-Cascade.apc`); §4.16 GPS/photo PROCs via shared `Capture-Helpers.apc` (`ReadGPSReading()`, `TakeVerificationPhoto()`). DCF footer updated to 12 records / 664 items (from 11/655). Consumed ~1.5h of Day 2 released capacity. Epic 3 + Epic 2 epic files updated to match (PSGC/GPS/photo tasks flagged for CSPro build in E3-F1-043/043a/043b).
- **Sprint 002 capacity re-forecast after Day 2:** both F3 and F4 logic-pass work closed; F1 spec-alignment pass also landed; form-layout plan landed (shared principles + F1/F3/F4 per-instrument plans); E2-F4-009 schema patch CLOSED-BY-VERIFICATION 2026-04-21 (generator + DCF already correct — findings #1/#2 in F4 spec were stale). Capacity is even more freed than forecast; ~17h+ remaining across Wed–Fri. Options for the released capacity: (a) pull E3-F1-001 FMF Section A forward now that the layout plan is in place, (b) absorb DOH-PMSMD feedback (E0-032a) without deadline pressure, (c) draft E0-010 weekly status format. Not committing ahead of Wed's E0-032a triage.

### 2026-04-22 (Wed)

- **Case-control extension landed across F1/F3/F4 DCFs (Route 1b).** Added a shared 5-item case-start block — `SURVEY_CODE` (per-instrument literal), `INTERVIEWER_ID`, `DATE_STARTED`, `TIME_STARTED`, `AAPOR_DISPOSITION` — to `FIELD_CONTROL` record in all three generators via new `cspro_helpers._case_control_items(survey_code)` helper. F1 additionally gained `FACILITY_NAME` + `FACILITY_ADDRESS` baked into `build_geo_id("facility")` (parity with F3's `facility_and_patient` mode). AAPOR 2023 Standard Definitions 10th ed. value set (11 codes, 3-digit zero-filled) attached to `AAPOR_DISPOSITION` — research-grade, publishable in methodology section. New item counts: **F1 12/671 (+7), F3 18/840 (+5), F4 22/623 (+5)**. Preproc prefill templates added to all three skip-logic specs (F1 §4.17, F3 §4.16, F4 §4.12) — `sysdate()`/`systime()` for timestamps, literal for SURVEY_CODE, `AAPOR_DISPOSITION = 0` (000 In Progress) with consent-refusal rewrite to `210`.
- **Why this expanded into Day 3 instead of staying inside Day 2's FMF kickoff:** pre-flight check on E3-F1-001 surfaced a DCF/plan drift — form-layout plan referenced `SURVEY_CODE`, `INTERVIEWER_ID`, `DATE_STARTED`, `TIME_STARTED`, `AAPOR_DISPOSITION`, `FACILITY_NAME`, `FACILITY_ADDRESS` as Form 1/Form 2 fields, but none existed in the DCF. Three options surfaced: realign plan → DCF (cheap, loses discipline), extend DCF → plan (proper, requires ASPSI re-review), or hybrid (defer to Sprint 003). Chose **(b) extend DCF** to establish proper case-control discipline now rather than retrofit later. Also fixed Cat 1 cosmetic plan typos (`PROVINCE` → `PROVINCE_HUC`, `CITY_MUN` → `CITY_MUNICIPALITY`, `Q2_DESIGNATION` → `Q2_FACILITY_ROLE`) in the same pass.
- **Downstream impact:** E2-F1-010 / E2-F3-010 / E2-F4-010 Designer sign-off scope updated to include the new case-control block — added notes to each in `epics/epic-02-questionnaire-design.md`. No new tasks opened — the re-review fits inside existing Designer walkthroughs. Preproc PROC wiring itself is Epic 3 work (lands with the FMF build, not the DCF).
- **E3-F1-001 kickoff (in progress after case-control lands):** generator-first route chosen (hybrid per form-layout-plan §6) — `generate_fmf.py` emits the skeleton (form names, labels, item membership, tab order); Designer handles visual polish. Non-destructive — writes to `FacilityHeadSurvey.generated.fmf`; existing scaffold untouched until Designer-reviewed.
- **E3-F3-001 kickoff (F3 FMF skeleton landed).** `deliverables/CSPro/F3/generate_fmf.py` authored and run; output at `deliverables/CSPro/F3/PatientSurvey.generated.fmf` (1023 lines, 19 forms, 0 orphan items — every non-container DCF item placed exactly once). Structure: FORM000 Id item, FORM001 top-level container, FORM002–FORM004 FC/Geo/Facility-GPS, FORM005 Patient-home GPS + verification photo (bundled), FORM006 Section A (Q1 gate), FORM007–FORM017 one-form-per-section skeleton for B–L, FORM018 closing with FIELD_CONTROL case-end items. Form labels carry the intended Designer splits inline (e.g., "B. Patient Profile — split into B1/B2/B3 in Designer") so the 32-form screen-density plan stays visible without pre-splitting at generation. Form-level skips (Q1/Q162/Q169) deferred to Designer per form-layout-plan §2.
- **E3-F4-001 kickoff (F4 FMF skeleton landed).** `deliverables/CSPro/F4/generate_fmf.py` authored and run; output at `deliverables/CSPro/F4/HouseholdSurvey.generated.fmf` (851 lines, 24 forms, 0 orphan items). Shape mirrors F3 but reflects F4-specifics: FORM002 FC case-start (includes `HH_LISTING_NO`), FORM003 `HOUSEHOLD_GEO_ID` carries both PSGC cascade and GPS items (Designer splits PSGC from GPS trigger), FORM004 `REC_CASE_VERIFICATION` photo-only (F4 has no separate GPS capture record — GPS lives in geo-id), FORM007 `C_HOUSEHOLD_ROSTER` on its own form per Form-Layout-Principles §8 (one roster per form, no adjacent fields), FORM008 `C_HH_PRIVATE_INS_GATE` isolates Q47 from the roster loop, FORM018 (M) and FORM019 (N) flagged for 3-way / 6-way Designer splits (bill-recall chain + WHO expenditure grid), FORM023 closing. Form-level skips (Q1 consent, Q129 Section-M gate, Q142 bill-recall chain) deferred to Designer per form-layout-plan §2.

### 2026-04-23 (Thu)

- **F2 PWA Epic 3 build closed.** Auto-advance + section-lock UX shipped earlier this sprint; today: 3/3 Playwright E2E tests passing (golden path, section lock, language switch); two production bugs fixed (`multi` checkbox array defaulting + empty-string Zod stripping); SUT deployed to Cloudflare Pages staging (`5466a539.f2-pwa-staging.pages.dev`). UAT Round 1 launched — `#f2-pwa-uat` Slack channel live, `docs/F2-PWA-UAT-Guide.md` published, GitHub Issues templates active. GitHub repo renamed to `ASPSI-DOH-UHC-CAPI-Development` and made public; remote URL updated. CSPro F2 track explicitly deprioritised as least priority in all scrum files.

## Inter-Sprint Activity (2026-04-25 Sat → 2026-04-27 Mon AM)

> Work that landed between Sprint 002 close (Fri 2026-04-24) and Sprint 003 start (Mon 2026-04-27). Tracked here for velocity bookkeeping; not part of Sprint 002 commitments. Items requiring follow-through carry into Sprint 003 as new commitments (see E4-PWA-013).

### 2026-04-25 (Sat) — F2 PWA UAT closure + automation

- **UAT Round 1 (v1.1.0) closed** with 7 fixes (auto-advance bug, mid-section skip logic, Section G role-hide, max-value enforcement on age + tenure fields). Round opened 2026-04-23 by Shan (ASPSI), closed with "Pass with comments" 2026-04-24, comments addressed and verified 2026-04-25.
- **UAT Round 2 (v1.1.1) closed** with 6 fixes (gate-question navigation regression Q12=No / Q31=No, specialty filter by role, real-time validation tooltips, language switcher visibility, silent submit-failure fix). Production deployed to `f2-pwa.pages.dev`; release notes published as `v1.1.0` and `v1.1.1`; CHANGELOG.md auto-maintained.
- **UAT automation infrastructure** went live on `main`: `uat-slack-events.yml` (real-time issue/milestone events to `#f2-pwa-uat`), `uat-slack-digest.yml` (09:00 MNL daily snapshot when active), `uat-release-notes.yml` (milestone-closed → CHANGELOG + GitHub Release + Slack post + auto-bump `package.json`).
- **`/gstack-cso` security audit** flagged a CRITICAL finding: HMAC inlined into the Vite bundle, exposing it to anyone who downloaded the staging build. Auth re-arch design drafted (`docs/superpowers/specs/2026-04-26-f2-pwa-auth-rearch-design.md`).
- **Sprint 002 archived** end of day; `sprint-current.md` reset for Sprint 003.

### 2026-04-26 (Sun) — F2 PWA design system + auth re-arch + Verde Manual to production

- **F2 PWA design system codified.** `/gstack-design-consultation` produced `deliverables/F2/PWA/app/DESIGN.md` — visual source of truth anchored on *"This is real software, not a government form."* Direction: **Verde Manual** — clinical stationery + utility on DOH "Verde Vision / Berde para sa bayan" institutional palette. App-level `CLAUDE.md` added at `deliverables/F2/PWA/app/CLAUDE.md` to scope gstack to the F2 PWA workstream.
- **Visual-identity migration shipped to staging in 5 PRs** (all merged): #37 tokens, #38 fonts, #39 layout & components, #40 DESIGN-006 sweep + alpha-aware HSL slot syntax + raw-Tailwind-color sweep, #41 polish (flattened buttons, hairline-edged modals).
- **F2 PWA auth re-architecture cut over to staging.** PR #31 (Cloudflare Worker JWT proxy replacing HMAC-in-bundle) merged to `staging` and live on `f2-pwa-staging.pages.dev`, mitigating the 2026-04-25 CSO CRITICAL finding. Worker URL: `https://f2-pwa-worker.hcw.workers.dev`. Disruption window ~18 min (longer than runbook's 4–6 min — see Issue #34). Runbook at `docs/superpowers/runbooks/2026-04-26-f2-auth-cutover.md`.
- **Three Round 3 issues filed** during the cutover smoke test:
  - **#33** Section F/G multi-select state pollution — Phase F blocker.
  - **#34** CF Pages auto-deploy not firing on staging push (later confirmed broken on main too) — Phase F blocker or runbook rewrite.
  - **#35** Worker PBKDF2 600k iters exceeds Workers' 100k cap — operational gotcha, fixed at runtime.
- **PR #32 hot-fix** opened for the EnrollmentScreen pre-refresh regression (deployed manually).
- **Verde Manual visual identity LIVE in production via path B.** Cherry-picked the 5 staging Verde commits onto `main` via PR #42 (`a1c4a3e`); resolved conflicts in `App.tsx` (h1 styling) and `EnrollmentScreen.tsx` (kept main's pre-auth-rearch single-step logic + applied Verde styling intent). Auth re-arch (PR #31) intentionally NOT in this port — stays on staging awaiting Phase F gate. GitHub auto-deploy didn't fire on the merge to main (confirms #34 affects main too). Manually deployed via `wrangler pages deploy dist --project-name=f2-pwa --branch=main --commit-hash=a1c4a3ea` after `npm install -g wrangler` (deployment `4f61356a-51fb-4ea2-aeb0-647edc678be0`). Canonical `f2-pwa.pages.dev` now serves Verde Manual.

### Carry-into-Sprint 003

- **E4-PWA-013** F2 PWA auth re-arch Phase F production cutover decision — gated on #33 + #34 resolution + ≥24h clean staging soak; earliest window ~17:35 PHT 2026-04-27. Added to Sprint 003 committed items.
- **E3-F2-PWA-DESIGN-004** self-host fonts (gated on `pyftsubset`) — backlog, not yet sprinted.
- **E3-F2-PWA-DESIGN-005** refine hex from official DOH brand-book PDF — blocked-external on ASPSI.

## Retrospective — Sprint 002

> 5-minute time-box. Four questions, fixed order. Written, not thought-through-only.
> Don't write self-congratulation; only write what changes next week's behavior.

### 1. Did the sprint goal land? (yes / partial / no — one line why)

Partial — F3/F4 logic-pass closed Day 2 (exceeded goal), FMF skeletons landed Day 3; F1 Designer sign-off (E2-F1-010) not closed; Tranche 2 extended (no official new deadline as of Apr 25), submission pending.

### 2. What surprised me? (process, not work — max 3 bullets)

- F3 spec was already 1133 lines when the sprint opened — auto-standup said "pending" because the generator never reads deliverables/ file mtimes. Second occurrence of this exact failure mode in two sprints.
- F4 full A–Q spec closed in ~3h vs 10–14h estimated; released capacity was absorbed by case-control DCF extension on Day 3 instead of FMF kickoff — good trade, but the scope shift wasn't visible in the sprint goal until it happened.
- Both P1 schema gaps (`C_HOUSEHOLD_ROSTER`, `J_HEALTH_SEEKING`) self-closed on re-verification; the "findings" were stale notes written before checking the generator output.

### 3. Deadline exposure check — D2 / D3 / Tranche 2 slip days this week

Tranche 2 (40%) extended by DOH — new deadline not yet officially communicated as of 2026-04-25. No new contractual slip days introduced this week (extension was in effect before Apr 24 target). Late-delivery penalty exposure: pending official deadline confirmation. Deadline exposure remains open until DOH issues the revised window in writing.

### 4. One thing to change in Sprint 003

Day 1 ritual: before writing the Today-plan table, grep deliverables/ for files modified since last standup to catch artifact drift. Prevents the standup generator from narrating "pending" on already-done work. (Two occurrences across Sprint 001 and Sprint 002.)

## Definition of Done — Sprint 002

- [ ] **Tranche 2 (40%) submission package** submitted via DOH route by EOD Fri 2026-04-24, framed as *status-to-date against an extended D2/D3 window* — not "D2 complete." Cover-letter framing confirmed with Juvy before send. Submission entry logged in `log.md`. *(Carried forward — extension deadline not yet issued)*
- [ ] **E2-F1-010** closed: F1 DCF walkthrough complete in CSPro Designer, bug list closed or deferred with rationale, sign-off note appended to `log.md`. *(Carried forward to Sprint 003)*
- [x] **E2-F3-001** closed 2026-04-21: F3 skip-logic + validation spec reviewed against Apr 20 questionnaire + DCF state, 6 open questions dispositioned (Q31 IP_GROUP routed to Juvy; 5 closed as spec-decisions), `status: reviewed` at `deliverables/CSPro/F3/F3-Skip-Logic-and-Validations.md`. F3 Build-ready.
- [x] **E2-F4-001** closed 2026-04-21: F4 skip-logic + validation spec written full A–Q at `deliverables/CSPro/F4/F4-Skip-Logic-and-Validations.md` (904 lines). Initially flagged 2 P1 schema gaps for `generate_dcf.py` (roster + health-seeking); both CLOSED-BY-VERIFICATION later Day 2 when re-inspecting the generator before patching — `C_HOUSEHOLD_ROSTER` already `max_occurs=20`, `J_HEALTH_SEEKING` intentionally respondent-level per Apr 20 source rephrase. 3 questions routed to ASPSI (Q15 IP_GROUP list, roster max-occ cap confirmation, Q202 worry-reasons option count); 5 spec-decisions documented.
- [ ] **E0-032a** closed: DOH-PMSMD matrix feedback triaged; any requested revisions reflected in F1/F2 build state or explicitly deferred with rationale recorded. *(Carried forward to Sprint 003)*
- [x] **Sprint 002 retrospective** filled in 2026-04-25; archived to `scrum/sprints/sprint-002.md`; `sprint-current.md` reset for Sprint 003.
