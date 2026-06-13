---
epic: 3
title: CAPI Application Development (CSPro + CSEntry / PWA)
phase: per-instrument
status: in-progress
last_updated: 2026-05-18
---

# Epic 3 — CAPI Application Development (CSPro + CSEntry / PWA)

Per-instrument application build workstream. Turns the validated data dictionary from Epic 2 into a working data-collection application ready for testing in Epic 6. F1/F3/F4 are built as CSPro/CSEntry CAPI apps; **F2 pivoted to a Progressive Web App on 2026-04-17** and no longer uses the CSPro or Google Forms tracks.

**Ties to Product Backlog:** [[../product-backlog#Epic 3 — CAPI Application Development|PB Epic 3]]
**Methodology:** [[../../../../2_Areas/IT-Standards/templates/CAPI-Development-Workflow|CAPI Development Workflow]] Phase 6

## Status snapshot (2026-05-18)

| Instrument | Mode | Build state |
|---|---|---|
| F1 | CSPro CAPI | Designer sign-off DONE 2026-05-04 (E2-F1-010); **from-scratch CAPI rebuild 2026-05-12** emits F1 end-to-end (generator → `FacilityHeadSurvey.generated.fmf`). **E3-F1-001 REOPENED 2026-05-18** (prior `done` superseded by the rebuild — CSPro Designer pass on Section A outstanding; Sprint 006 Goal A). Phase 1 sync (`E3-F1-088`) code-side partial; tablet-verify deferred to Sprint 007 (blocked behind `E4-CSWeb-005`). |
| F2 | **PWA** (self-admin; CSPro-encoder and Google Forms fallbacks retired; **CSPro F2 track = least priority**) | Production live (v2.0.x + Verde Manual). UAT Rounds 1 + 2 closed; **Round 3 ran 2026-05-13→15** (label `from-uat-round-3-2026-05`, ~13 findings #302–#314); R3 close-out is Sprint 006 Goal B (`E6-PWA-007` / #271). UAT automation pipeline live. |
| F3 | CSPro CAPI | Build-ready; **rebuilt end-to-end 2026-05-12** (incl. 110_F3_listing). FMF Designer pass tracked as **E3-F3-001 — Sprint 006 Goal A**. |
| F4 | CSPro CAPI (roster-heavy) | Build-ready; **rebuilt end-to-end 2026-05-12** (incl. 113_F4_listing). FMF Designer pass tracked as **E3-F4-001 — Sprint 006 Goal A**. |
| PLF | Recruitment form | Closed as duplicate of 110_F3_listing (per 2026-05-12 rebuild). |

## Task conventions

- Task IDs: `E3-{instrument}-NNN`
- Per-instrument standard template below; F4 adds roster-specific tasks

## Standard per-instrument template

| # | Task group |
|---|---|
| 001–003 | Form file + layout + capture types |
| 010–012 | Question text (English + Filipino) |
| 020–024 | Skip logic + validation wiring |
| 030–032 | Dynamic value sets + conditional rendering |
| 040–045 | FIELD_CONTROL block |
| 050 | Partial save / resume behavior |
| 060 | CSEntry Windows smoke test |
| 070 | Roster engine (F4 only) |

---

## F1 — Facility Head Survey

**Prerequisite:** E2-F1-010 (Designer sign-off on F1 DCF)
**Current DCF state (2026-04-21):** 12 records / 671 items. Shared `cspro_helpers.py` in use. PSGC cascade wired via `PSGC-Cascade.apc`; GPS + verification-photo via `Capture-Helpers.apc` (`REC_FACILITY_CAPTURE`). Skip-logic + validation spec at `deliverables/CSPro/F1/F1-Skip-Logic-and-Validations.md` (aligned with F3/F4 Apr 21).
**Sprint 003 prerequisite:** Form-layout plan (forms per subsection, no scrolling, roster-scrolls-alone) must land before E3-F1-001 starts — see Sprint 002 rationale.

### Form layout & UX

- [x] **E3-F1-001** Create form file (`FacilityHeadSurvey.fmf`); lay out Section A (Identification & Cover Page) — **REOPENED 2026-05-18:** prior `done` (pre-2026-04-26) superseded by the 2026-05-12 from-scratch CAPI rebuild; generator now emits `FacilityHeadSurvey.generated.fmf`, the CSPro Designer pass on Section A is still outstanding. **Sprint 006 carry (Goal A).** `status::done` `priority::high` `estimate::4h` ✅ *(swept 2026-06-13 @ S009 close: combined-view .fmf live (inject_blocks-maintained, 259-block screen plan), Designer-verified + deployed; closes the five-sprint carry)*
- [x] **E3-F1-002** Lay out Sections B–H with grouped screens matching interviewer flow `status::done` `priority::high` `estimate::2d`
- [x] **E3-F1-003** Assign capture types per field (radio, drop-down, number pad, date picker) to optimize tablet entry speed `status::done` `priority::high` `estimate::1d`

### Question text + language

- [x] **E3-F1-010** Populate English question text from questionnaire; use `~~item~~` fills for personalized text (facility name, respondent name) `status::done` `priority::high` `estimate::1d`
- [x] **E3-F1-011** Add Filipino translations for all question labels and option text `status::done` `priority::high` `estimate::1d` ✅ *(swept 2026-06-13 @ S009 close: fil.json wired + deployed 6/12 (575 labels, 72.2%; English fallback for the rest))*
- [x] **E3-F1-012** Set up multi-language switching (`setlanguage`, language-select on cover page) `status::done` `priority::high` `estimate::2h` ✅ *(swept 2026-06-13 @ S009 close: as-built: 7-language .dcf + CSEntry native language menu (supersedes setlanguage/cover-page design); live + announced 6/12)*

### Skip logic + validation wiring (`.apc`)

- [x] **E3-F1-020** Implement master skip gates (section-level eligibility filters) `status::done` `priority::high` `estimate::4h` ✅ *(swept 2026-06-13 @ S009 close: cluster-skip gates live (dead-condition pass 6/11 fixed 22 dead gates); verify_questions 672/672)*
- [x] **E3-F1-021** Implement field-level skip logic per `F1-Skip-Logic-and-Validations.md` skip table `status::done` `priority::high` `estimate::1d` ✅ *(swept 2026-06-13 @ S009 close: full skip table in generate_apc; 0 bad-skips per verify_questions gate)*
- [x] **E3-F1-022** Wire hard validations: `errmsg` + `reenter` per rule (age ≥ 18, registered ≤ eligible, date ranges, lat/lon bounds) `status::done` `priority::high` `estimate::1d` ✅ *(swept 2026-06-13 @ S009 close: hard validations live incl. validation-parity pass (G1 age, G2 tenure, G3 visit-date order) 6/12)*
- [x] **E3-F1-023** Wire soft validations: `accept()` overrides per rule (capitation ceilings, unusual values) `status::done` `priority::high` `estimate::4h` ✅ *(swept 2026-06-13 @ S009 close: soft validations live (accept()/warn pattern, photo soft-gate, household-size class))*
- [x] **E3-F1-024** Wire display gates: conditional visibility via `postproc` / `onfocus` `status::done` `priority::high` `estimate::4h` ✅ *(swept 2026-06-13 @ S009 close: display gates live (noinput preprocs + own-screen isolation for gated other-specify, 6/12 sweep))*

### Dynamic behavior

- [x] **E3-F1-030** Implement dynamic value sets (`setvalueset()`) for facility-type-dependent option lists `status::done` `priority::high` `estimate::4h` ✅ *(swept 2026-06-13 @ S009 close: PSGC setvalueset live incl. province-anchored barangay fallback (6/11))*
- [x] **E3-F1-031** Implement cross-field consistency checks (e.g., tenure ≤ age − 15) `status::done` `priority::high` `estimate::4h` ✅ *(swept 2026-06-13 @ S009 close: cross-field checks live (G2 tenure<=age-20 et al.))*
- [ ] **E3-F1-032** Implement conditional question text fills (facility name, respondent name in follow-up questions) `status::todo` `priority::medium` `estimate::2h`

### FIELD_CONTROL block

- [x] **E3-F1-040** Informed consent capture screen (with explicit accept/refuse + timestamp) `status::done` `priority::critical` `estimate::3h` ✅ *(swept 2026-06-13 @ S009 close: verbatim Annex H ICF in CAPI question-text; refusal endlevel; shipped 6/11)*
- [ ] **E3-F1-041** Eligibility screen (must pass before main questionnaire loads) `status::todo` `priority::high` `estimate::2h`
- [x] **E3-F1-042** AAPOR-aligned disposition codes (completed, partial, refused, ineligible, contact attempt, etc.) `status::done` `priority::high` `estimate::3h` ✅ *(swept 2026-06-13 @ S009 close: superseded as designed: AAPOR_DISPOSITION removed 6/12; per-instrument ENUM_RESULT Result-of-Visit captures disposition)*
- [x] **E3-F1-043** GPS capture at start of interview — uses `ReadGPSReading()` helper from `Capture-Helpers.apc`; writes `FACILITY_GPS_*` items via `REC_FACILITY_CAPTURE` trigger block (see F1 spec §3.1.1 / §4.16) `status::done` `priority::high` `estimate::2h` ✅ *(swept 2026-06-13 @ S009 close: GPS auto-fetch onfocus (ReadGPSReading 120,20), fields protected; shipped 6/12)*
- [x] **E3-F1-043a** Verification photo capture — uses `TakeVerificationPhoto()` helper, writes `VERIFICATION_PHOTO_FILENAME` with pattern `case-{QUESTIONNAIRE_NO}-verification.jpg` (F1 spec §3.1.2) `status::done` `priority::high` `estimate::2h` ✅ *(swept 2026-06-13 @ S009 close: verification photo on dedicated end-of-survey form, outcome-gated, case-<QN>.jpg; shipped 6/12)*
- [x] **E3-F1-043b** PSGC cascade wiring — `onfocus` + `loadcase()` + `setvalueset()` per `PSGC-Cascade.apc`; external lookup dictionaries for REGION/PROVINCE_HUC/CITY_MUNICIPALITY/BARANGAY (F1 spec §4.15); blocked on ASPSI PSGC value-set confirmation `status::done` `priority::high` `estimate::3h` ✅ *(swept 2026-06-13 @ S009 close: as-built: single 12-digit QN derives geo (cascade procs removed); barangay picker + 8 PSGC files per deploy)*
- [x] **E3-F1-044** Interviewer ID + Supervisor ID capture `status::done` `priority::high` `estimate::1h` ✅ *(swept 2026-06-13 @ S009 close: as-built: Interview Staff block + Field Control validated/edited-by names (trimmed-FC design 6/12))*
- [x] **E3-F1-045** Date/time stamps (start, end, duration) `status::done` `priority::medium` `estimate::1h` ✅ *(swept 2026-06-13 @ S009 close: as-built: FC visit dates (Date,YYYYMMDD pickers); start/end timestamps descoped in the trimmed FC — drift noted in harmonization codebook)*

### Resilience + smoke test

- [x] **E3-F1-050** Partial save / resume behavior configured (what happens mid-interview) `status::done` `priority::high` `estimate::2h`
- [x] **E3-F1-060** CSEntry Windows smoke test: happy path from cover page to last question `status::done` `priority::high` `estimate::2h` ✅ *(swept 2026-06-13 @ S009 close: smoke-tested repeatedly: desk-test walks + emulator tester-path installs (6/11-6/12))*

### Phase 1 build *(2026-05-08 worktree session — proven end-to-end on tablet)*

- [x] **E3-F1-080** Phase 1 — Python generator pipeline (canonical CSPro 8.0 source emit) `status::done` `priority::critical`
- [x] **E3-F1-081** Phase 1 — `build_all.py` orchestrator + env splice (urls.yaml → .env) `status::done` `priority::critical`
- [x] **E3-F1-082** Phase 1 — `login_app` (101_login) chain entry point `status::done` `priority::critical`
- [x] **E3-F1-083** Phase 1 — `menu_app` (106_menu) enumerator-only menu `status::done` `priority::critical`
- [x] **E3-F1-084** Phase 1 — F1 full generator chain (671 items / 12 records, all artifacts emitted) `status::done` `priority::critical`
- [x] **E3-F1-085** Phase 1 — local CSWeb deploy proven (F7 → Deploy Application wizard) `status::done` `priority::critical`
- [x] **E3-F1-086** Phase 1 — CSEntry tablet sync chain proven (login → menu → F1, end-to-end on real device) `status::done` `priority::critical`
- [x] **E3-F1-087** Phase 1 — CSPro 8.0 syntax gotchas catalog (Phase 2 / F3 / F4 reference) `status::done` `priority::high`
- [x] **E3-F1-088** Phase 1 sync mechanic resolution — `syncdata` external-dict + CSDB binding. Code-side PARTIAL via the 2026-05-12 rebuild. Tablet-verify slice **deferred to Sprint 007** — blocked behind `E4-CSWeb-005` (field-tablet sync config), which is the Sprint 007 carry of the Goal D subset commit (S006 commits only E4-CSWeb-001/002). `status::done` `priority::critical` `estimate::3h` *(tablet round-trip smoke; needs CSWeb VPS sync target up)* ✅ *(swept 2026-06-13 @ S009 close: sync proven: emulator round-trip + R4 testers syncing live to csweb.asiansocial.org (6/12))*
- [x] **E3-F1-PHASE2-PLAN** Phase 2 plan + scope confirmation (PLF + F3 + F4_listing + F4 + supervisor menu + EA fence + daily audit Slack) — **OVER-DELIVERED 2026-05-12** as built artifacts (F1+F3+F4+110_F3_listing+113_F4_listing end-to-end, 83 worktree commits) rather than a scope-doc; closed in Sprint 005. `status::done` `priority::high` `estimate::4h`

---

## F2 — Healthcare Worker Survey *(self-administered — PWA)*

**F2 PWA Epic 3 build is COMPLETE as of 2026-04-23.** M0–M11 shipped 2026-04-17/18; auto-advance + section-lock UX shipped post-M11; 3/3 Playwright E2E tests pass. The prior Google Forms track (E3-F2-GF-001..008) and the deferred CSPro-encoder track are both **RETIRED / SUPERSEDED**. **The CSPro F2 track is the least priority item in this engagement — do not reopen without explicit decision reversal.**

**Build location:** `deliverables/F2/PWA/app/`
**Production:** `https://f2-pwa.pages.dev` (Cloudflare Pages, branch `main`, v1.1.1 codebase + Verde Manual visual identity since 2026-04-26 via PR #42 path-B port + manual `wrangler pages deploy`. Auto-deploy on push currently broken — see [#34](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/34))
**Staging (SUT):** `https://b1e46a55.f2-pwa-staging.pages.dev` (Cloudflare Pages, branch `staging` — deploy URL rotates per push; canonical alias is the project root)
**GitHub repo:** `github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development` (public)
**UAT coordination:** Slack `#f2-pwa-uat` (C0AV19GB05P) + GitHub Issues + project board #7
**Automation:** GitHub Actions workflows on `main` auto-post UAT events / daily digests / release notes to Slack
**Prerequisite:** none — spec frozen and embedded in the PWA

### PWA build track *(PRIMARY — M0–M11 shipped 2026-04-17 / 2026-04-18)*

- [x] **E3-F2-PWA-M0** Vite + React + TypeScript installable shell — PWA manifest, service worker, install prompt `status::done` `priority::critical`
- [x] **E3-F2-PWA-M1** IndexedDB autosave — per-field writes, resume on reload `status::done` `priority::critical`
- [x] **E3-F2-PWA-M2** Skip-logic navigation engine — spec-driven section/question routing `status::done` `priority::critical`
- [x] **E3-F2-PWA-M3** Apps Script backend — sync endpoint, response sheet, deployment URL in runtime config `status::done` `priority::critical`
- [x] **E3-F2-PWA-M4** Sync orchestrator — queue, retry, conflict detection, offline-first `status::done` `priority::critical`
- [x] **E3-F2-PWA-M5** Full 114-item instrument wired from spec `status::done` `priority::critical`
- [x] **E3-F2-PWA-M6** Validation + cross-field rules (POST-submit layer) `status::done` `priority::high`
- [x] **E3-F2-PWA-M7** Enrollment flow — facility link → HCW identity → draft seed `status::done` `priority::high`
- [x] **E3-F2-PWA-M8** i18n scaffold — EN/FIL switching, translation table surfaces `status::done` `priority::high`
- [x] **E3-F2-PWA-M9** Admin dashboard — response counts, sync status, per-HCW drill-down (read-only) `status::done` `priority::medium`
- [x] **E3-F2-PWA-M10** Runtime config kill-switch — disable new draft creation remotely via config endpoint `status::done` `priority::high`
- [x] **E3-F2-PWA-M11** Spec-drift modal — detect client/server spec-version mismatch, block submit until resolved `status::done` `priority::high`

### Deferred from M11 (decision required)

- [ ] **E3-F2-PWA-M12a** Per-HCW tokens (replace email-based identity) `status::deferred`
- [ ] **E3-F2-PWA-M12b** Draft auto-migration across spec versions `status::deferred`
- [ ] **E3-F2-PWA-M12c** iOS push notifications `status::deferred`
- [ ] **E3-F2-PWA-M12d** Admin mutations (beyond read-only) `status::deferred`

### Pilot readiness

- [x] **E3-F2-PWA-QA-001** Automated E2E test suite (Playwright) — 3/3 pass: golden path (enrollment → all 10 sections → review → submit), section lock, language switch. Config: `npx playwright test --config e2e/playwright.config.ts`. `status::done` `priority::critical` `actual::2026-04-23`
- [x] **E3-F2-PWA-QA-002** Shan / ASPSI staff UAT dry-run — UAT Rounds 1 + 2 both closed 2026-04-25; 13 issues filed and fixed across the two rounds. `status::done` `priority::high` `actual::2026-04-23..2026-04-25`
- [x] **E3-F2-PWA-PILOT-001** Pilot decision — **UAT Round 1 is the pilot.** Decision: run pilot via ASPSI staff UAT before production promote. `status::done` `priority::high` `actual::2026-04-23`

### Round 3 / v1.2.0 backlog *(landing window: queued; gating not yet committed to a sprint)*

**UX enhancements** (project board #16/#17/#18, `[github]/projects/7`):

- [ ] **E3-F2-PWA-R3-001** Issue #16 — exclusive "I don't know" multi-select option (selecting it clears other selections; selecting any other clears it) `status::todo` `priority::medium` `estimate::3h`
- [ ] **E3-F2-PWA-R3-002** Issue #17 — "All of the above" auto-select (selecting it auto-selects all other options; deselecting any deselects it) `status::todo` `priority::medium` `estimate::3h`
- [ ] **E3-F2-PWA-R3-003** Issue #18 — matrix view for scale-style questions (one prompt per row, shared response columns) `status::todo` `priority::medium` `estimate::6h`

**Verde Manual visual-identity migration** (anchor: [`deliverables/F2/PWA/app/DESIGN.md`](../../deliverables/F2/PWA/app/DESIGN.md); memorable thing: *"This is real software, not a government form"*):

- [x] **E3-F2-PWA-DESIGN-000** Design consultation + DESIGN.md authored (Verde Manual — DOH-anchored emerald + pale verde paper; Newsreader display + Public Sans Variable body + JetBrains Mono data; hairline-divided layout + 88px gutter + ledger progress) — generated by `/gstack-design-consultation` 2026-04-26 `status::done` `priority::high` `actual::2026-04-26`
- [x] **E3-F2-PWA-DESIGN-001** PR #37 — token migration (`src/index.css` HSL rewrite to Verde Manual; `--radius` 0.5rem→0.25rem; manifest `theme_color` `#0f766e`→`#006B3F`). Merged 2026-04-26 as `47e1553`. `status::done` `priority::high` `actual::2026-04-26`
- [x] **E3-F2-PWA-DESIGN-002** PR #38 — fonts via Bunny CDN with workbox `runtimeCaching` for offline use (Newsreader + Public Sans Variable + JetBrains Mono; Tailwind `font-{serif,sans,mono}` mapped). Merged 2026-04-26 as `c1a97bb`. `status::done` `priority::high` `actual::2026-04-26`
- [x] **E3-F2-PWA-DESIGN-003** PR #39 — layout & components refactor (`<Question>` 80px gutter + JetBrains Mono margin id; `<ProgressBar>` → typographic ledger; killed card patterns in `<EnrollmentScreen>` / `<ReviewSection>`; raw `text-red-*`/`text-green-*` swept to `text-destructive` / `text-primary`; Newsreader applied to all h1/h2 chrome; JetBrains Mono on version subtitle + section eyebrows). Merged 2026-04-26 as `4fd2d92`. 308/308 tests pass; visual smoke confirmed Newsreader + Public Sans + JetBrains Mono all loaded on staging. `status::done` `priority::high` `actual::2026-04-26`
- [x] **E3-F2-PWA-DESIGN-006** Sweep remaining raw Tailwind colors in `PendingCount.tsx` / `BroadcastBanner.tsx` / `SectionTree.tsx` / ReviewSection `warn` severity. Extended `tailwind.config.ts` to alpha-aware HSL slot syntax + new `warning` token; added `--warning` + `--warning-foreground` to `src/index.css`. PR [#40](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/pull/40) merged 2026-04-26 as `1458f29`. Bonus: also fixed a quiet pre-existing bug where `bg-primary/10` in SectionTree was producing malformed CSS in the old non-alpha config. `status::done` `priority::low` `actual::2026-04-26`
- [x] **E3-F2-PWA-DESIGN-007** Polish PR3 punts — Button.tsx shadcn primitive flattened (no shadows on default/destructive/outline/secondary variants), SpecDriftOverlay/KillSwitchOverlay use bg-background + hairline border (no shadow-lg), MultiSectionForm fixed-side nav arrows softened from shadow-md to shadow-sm. PR [#41](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/pull/41) merged 2026-04-26 as `7bfc28a`. `status::done` `priority::low` `actual::2026-04-26`
- [x] **E3-F2-PWA-DESIGN-008** Path-B port to production — cherry-picked the 5 staging Verde Manual commits onto a branch off `main`, resolved EnrollmentScreen and App.tsx conflicts (kept main's pre-auth-rearch single-step Enroll logic + applied Verde styling intent), opened PR [#42](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/pull/42) merged 2026-04-26 as `a1c4a3e`. CF Pages auto-deploy didn't fire on the merge (confirms #34 affects main pushes too); manually deployed via `wrangler pages deploy dist --project-name=f2-pwa --branch=main --commit-hash=a1c4a3ea` (deployment `4f61356a`). Verde Manual now live at `https://f2-pwa.pages.dev`. `status::done` `priority::high` `actual::2026-04-26`
- [ ] **E3-F2-PWA-DESIGN-004** Self-host fonts under `public/fonts/*.woff2` (replaces CDN path from PR #38). **Gated on `pyftsubset`/fontTools tooling** for proper Latin Extended subsetting; lands as a follow-up after Round 3 if Bunny CDN proves problematic. `status::deferred` `priority::low`
- [ ] **E3-F2-PWA-DESIGN-005** Refine Verde Manual hex values from official DOH brand-book PDF (Department Order 2020-0011, Verde Vision 2023+). Current values are best-fit approximations of the visible seal + documented background tint `#e7efe7`. **Async on ASPSI** for PDF acquisition. `status::blocked-external` `priority::low`

### Retired tracks *(do not re-open without explicit decision reversal)*

- **Google Forms track (E3-F2-GF-001..015):** Superseded 2026-04-17 by PWA pivot. 8 tasks (GF-001..008) closed before supersede; remaining (GF-009..015) retired unbuilt. Prior artifacts under `deliverables/F2/apps-script/` retained for reference only.
- **CSPro-encoder track (E3-F2-CSPro-*):** Retired — three-path model (self / paper / staff-encoded-into-CSPro) collapsed to a single PWA path with a print-mode fallback inside the PWA.

---

## F3 — Patient Survey

**Prerequisite:** Form-layout plan (shared with F1/F4 — Sprint 003 prerequisite).
**Current DCF state (2026-04-21):** 18 records / 840 items, sections A–L. Skip-logic + validation spec reviewed 2026-04-21 at `deliverables/CSPro/F3/F3-Skip-Logic-and-Validations.md` (1 question routed to Juvy — Q31 IP_GROUP; 5 spec-decisions closed with override clause). **Build-ready.**

- [x] **E3-F3-001** Create form file (`PatientSurvey.fmf`); CSPro Designer pass on Section A — generator emits the skeleton post-2026-05-12 rebuild. **Sprint 006 committed (Goal A).** `status::done` `priority::high` `estimate::4h` ✅ *(swept 2026-06-13 @ S009 close: Designer-verified + deployed (217->237-screen combined view, skip-aware))*
- [x] **E3-F3-002..060** Standard template; reuses F1's interviewer-administered patterns (PSGC cascade + consent + GPS/photo via `Capture-Helpers.apc`) `status::done` ✅ *(swept 2026-06-13 @ S009 close: full F3 build live: 787/787 reachable, 0 dead, 0 bad-skips; deployed + in UAT R4)*
- [x] **E3-F3-015** Outpatient vs inpatient branching at eligibility screen `status::done` `priority::high` `estimate::4h` ✅ *(swept 2026-06-13 @ S009 close: outpatient/inpatient branching live (sections G/H routing; per-variant ICF); verify_questions PASS)*

*(Full task list to be expanded when F3 enters a sprint.)*

---

## F4 — Household Survey

**Prerequisite:** Form-layout plan (drafted 2026-04-21, [[../../deliverables/CSPro/F4/F4-Form-Layout-Plan|F4-Form-Layout-Plan]]). Schema is already correct — no patch needed.
**Current DCF state (2026-04-21):** 22 records / 623 items, sections A–Q. `C_HOUSEHOLD_ROSTER` is repeating (`max_occurs=20`, id-item `MEMBER_LINE_NO`); `H_PHILHEALTH_REG` and `J_HEALTH_SEEKING` are respondent-level non-repeating per the Apr 20 source rephrase ("singular you/your household member"). Skip-logic + validation spec drafted 2026-04-21 at `deliverables/CSPro/F4/F4-Skip-Logic-and-Validations.md` (3 questions routed to ASPSI, 5 spec-decisions; findings #1/#2 CLOSED-BY-VERIFICATION). **Build-ready.**

F4 inherits the standard template **plus a roster engine**. The household roster loop is the primary technical challenge in this instrument.

- [x] **E3-F4-000** ~~Schema patch — flip `C_HOUSEHOLD_ROSTER` and `J_HEALTH_SEEKING` to repeating records~~ **CLOSED-BY-VERIFICATION 2026-04-21.** Re-inspected generator + emitted DCF before starting patch: `C_HOUSEHOLD_ROSTER` already at `max_occurs=20`, `J_HEALTH_SEEKING` correctly respondent-level per Apr 20 source. No code change. `status::done` `priority::critical`
- [x] **E3-F4-001** Create form file (`HouseholdSurvey.fmf`); CSPro Designer pass on Section A — generator emits the skeleton post-2026-05-12 rebuild (incl. 113_F4_listing). **Sprint 006 committed (Goal A).** `status::done` `priority::high` `estimate::4h` ✅ *(swept 2026-06-13 @ S009 close: Designer-verified + deployed (159->225-screen combined view, skip-aware))*
- [x] **E3-F4-002..060** Standard template per F1 `status::done` ✅ *(swept 2026-06-13 @ S009 close: full F4 build live: 625/625 reachable; deployed + in UAT R4)*
- [x] **E3-F4-070** Household roster grid: add-member, edit-member, remove-member, reorder `status::done` `priority::critical` `estimate::2d` ✅ *(swept 2026-06-13 @ S009 close: roster live: auto line numbers, occurrence control (curocc>Q19 endgroup), desk-tested 6/11)*
- [x] **E3-F4-071** Per-member sub-questionnaire loop (conditional on age/relation/etc.) `status::done` `priority::critical` `estimate::2d` ✅ *(swept 2026-06-13 @ S009 close: per-member loop live (Q35 PWD gates, Q49 next-member jump), desk-tested)*
- [ ] **E3-F4-072** Cross-member consistency rules (e.g., only one household head, spouse implies head exists) `status::todo` `priority::high` `estimate::1d`
- [x] **E3-F4-073** Max roster size validation + soft warning at unusual sizes `status::done` `priority::high` `estimate::2h` ✅ *(swept 2026-06-13 @ S009 close: roster auto-ends at declared size + household-size soft check (fired in desk-test))*
- [x] **E3-F4-074** WHO expenditure grid + catastrophic-expenditure check (Section N flat batteries) `status::done` `priority::high` `estimate::1d` ✅ *(swept 2026-06-13 @ S009 close: Section N expenditure grid live (amount matrices, blank-amount checks on 103 items))*
- [x] **E3-F4-075** Bill-recall chain (Section N) `status::done` `priority::high` `estimate::4h` ✅ *(swept 2026-06-13 @ S009 close: Section M/N bill-recall chain live; covered by verify_questions PASS + deployment)*

*(Full task list to be expanded when F4 enters a sprint.)*

---

## PLF — Patient Listing Form

**Prerequisite:** E2-PLF-006 (implementation decision + any dictionary work)

- [x] **E3-PLF-001** If CAPI: minimal form with facility selector + patient entries grid `status::done` `priority::medium` `estimate::4h` ✅ *(swept 2026-06-13 @ S009 close: PatientListing + F4Listing CAPI apps built 5/12 (see project log))*

## Notes

- **F2 PWA Epic 3 build is COMPLETE (2026-04-23) and in production at v1.1.1 codebase + Verde Manual visual identity (2026-04-26).** UAT Rounds 1 + 2 both closed; 13 issues fixed; production live at https://f2-pwa.pages.dev. Round 3 (v1.2.0) UX enhancements queued: #16/#17/#18 on the project board. **Verde Manual visual-identity migration COMPLETE end-to-end:** 5 staging PRs (#37/#38/#39/#40/#41) + path-B port to main as #42 + manual `wrangler pages deploy` (CF auto-deploy broken per #34). DESIGN.md is the visual source of truth at `deliverables/F2/PWA/app/DESIGN.md`. **CSPro F2 track is least priority — do not reopen.**
- **F1 is the priority CSPro instrument.** Its task breakdown above is the template for F3 and F4.
- **F3 and F4 are Build-ready** as of 2026-04-21; form-layout plans also landed 2026-04-21 ([[../../deliverables/CSPro/Form-Layout-Principles|shared principles]] + per-instrument F1/F3/F4 plans). E3-F4-000 schema patch closed by verification on the same day — the generator and DCF were already correct.
- Reusable CSPro patterns live in `deliverables/CSPro/` as includable `.apc` fragments:
  - `Capture-Helpers.apc` — `ReadGPSReading()`, `TakeVerificationPhoto()`
  - `PSGC-Cascade.apc` — `FillRegionValueSet()`, `FillProvinceValueSet()`, `FillCityValueSet()`, `FillBarangayValueSet()`
  - `cspro_helpers.py` — shared Python generator helpers used by F1/F3/F4 `generate_dcf.py`
- F2/F3/F4 CSPro task lists remain partial stubs — expanded as each instrument enters its build sprint. Front-loading detailed task breakdowns for instruments months away is wasted effort.
