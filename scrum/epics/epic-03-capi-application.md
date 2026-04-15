---
epic: 3
title: CAPI Application Development (CSPro + CSEntry)
phase: per-instrument
status: not-started
last_updated: 2026-04-10
---

# Epic 3 — CAPI Application Development (CSPro + CSEntry)

Per-instrument application build workstream. Turns the validated data dictionary from Epic 2 into a working CSEntry application ready for testing in Epic 6.

**Ties to Product Backlog:** [[../product-backlog#Epic 3 — CAPI Application Development|PB Epic 3]]
**Methodology:** [[../../../../2_Areas/IT-Standards/templates/CAPI-Development-Workflow|CAPI Development Workflow]] Phase 6

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

**Prerequisite:** E2-F1-010 (Designer sign-off on F1 DCF v2)

### Form layout & UX

- [ ] **E3-F1-001** Create form file (`FacilityHeadSurvey.fmf`); lay out Section A (Identification & Cover Page) `status::todo` `priority::high` `estimate::4h`
- [ ] **E3-F1-002** Lay out Sections B–H with grouped screens matching interviewer flow `status::todo` `priority::high` `estimate::2d`
- [ ] **E3-F1-003** Assign capture types per field (radio, drop-down, number pad, date picker) to optimize tablet entry speed `status::todo` `priority::high` `estimate::1d`

### Question text + language

- [ ] **E3-F1-010** Populate English question text from questionnaire; use `~~item~~` fills for personalized text (facility name, respondent name) `status::todo` `priority::high` `estimate::1d`
- [ ] **E3-F1-011** Add Filipino translations for all question labels and option text `status::todo` `priority::high` `estimate::1d`
- [ ] **E3-F1-012** Set up multi-language switching (`setlanguage`, language-select on cover page) `status::todo` `priority::high` `estimate::2h`

### Skip logic + validation wiring (`.apc`)

- [ ] **E3-F1-020** Implement master skip gates (section-level eligibility filters) `status::todo` `priority::high` `estimate::4h`
- [ ] **E3-F1-021** Implement field-level skip logic per `F1-Skip-Logic-and-Validations.md` skip table `status::todo` `priority::high` `estimate::1d`
- [ ] **E3-F1-022** Wire hard validations: `errmsg` + `reenter` per rule (age ≥ 18, registered ≤ eligible, date ranges, lat/lon bounds) `status::todo` `priority::high` `estimate::1d`
- [ ] **E3-F1-023** Wire soft validations: `accept()` overrides per rule (capitation ceilings, unusual values) `status::todo` `priority::high` `estimate::4h`
- [ ] **E3-F1-024** Wire display gates: conditional visibility via `postproc` / `onfocus` `status::todo` `priority::high` `estimate::4h`

### Dynamic behavior

- [ ] **E3-F1-030** Implement dynamic value sets (`setvalueset()`) for facility-type-dependent option lists `status::todo` `priority::high` `estimate::4h`
- [ ] **E3-F1-031** Implement cross-field consistency checks (e.g., tenure ≤ age − 15) `status::todo` `priority::high` `estimate::4h`
- [ ] **E3-F1-032** Implement conditional question text fills (facility name, respondent name in follow-up questions) `status::todo` `priority::medium` `estimate::2h`

### FIELD_CONTROL block

- [ ] **E3-F1-040** Informed consent capture screen (with explicit accept/refuse + timestamp) `status::todo` `priority::critical` `estimate::3h`
- [ ] **E3-F1-041** Eligibility screen (must pass before main questionnaire loads) `status::todo` `priority::high` `estimate::2h`
- [ ] **E3-F1-042** AAPOR-aligned disposition codes (completed, partial, refused, ineligible, contact attempt, etc.) `status::todo` `priority::high` `estimate::3h`
- [ ] **E3-F1-043** GPS capture at start of interview `status::todo` `priority::high` `estimate::2h`
- [ ] **E3-F1-044** Interviewer ID + Supervisor ID capture `status::todo` `priority::high` `estimate::1h`
- [ ] **E3-F1-045** Date/time stamps (start, end, duration) `status::todo` `priority::medium` `estimate::1h`

### Resilience + smoke test

- [ ] **E3-F1-050** Partial save / resume behavior configured (what happens mid-interview) `status::todo` `priority::high` `estimate::2h`
- [ ] **E3-F1-060** CSEntry Windows smoke test: happy path from cover page to last question `status::todo` `priority::high` `estimate::2h`

---

## F2 — Healthcare Worker Survey *(self-administered — SPECIAL CASE)*

**F2 is not a CSPro CAPI instrument by default.** Primary build track is **Google Forms** (self-admin by HCW, 3-day window, paper fallback encoded back into the same Form). See `memory/project_f2_capture_modes.md` and `memory/project_f2_questionnaire_rewrite_needed.md`.

**Prerequisite:** E2-F2-018 (F2 Google Forms spec sign-off)

### Google Forms build track *(PRIMARY)*

- [x] **E3-F2-GF-001** Google Apps Script generator skeleton — reads spec CSV/MD, emits a Google Form in the project mailbox Drive, re-runnable on spec revisions `status::done` `priority::critical` `estimate::1d`
  - Drafted 2026-04-15 at `deliverables/F2/apps-script/`. `Code.gs` is the entry point — `buildForm()`, `rebuildForm()`, trigger installation. Spec is baked in as structured JS in `Spec.gs` rather than parsed from MD at runtime (Apps Script has no reliable MD parser and the spec is large enough that JS data is clearer to diff).
- [x] **E3-F2-GF-002** Spec → Form builder: sections, questions, choices, required flags, validation (regex/numeric ranges), help text `status::done` `priority::critical` `estimate::1d`
  - `Spec.gs` contains all 114 items across 35 sections with verbatim labels and numeric ranges from `F2-Validation.md` (Q4 age 18–80, Q9a years 0–60, Q10 days 1–7, Q11 hours 1–24, etc.). `FormBuilder.gs` is a two-pass materializer: pass 1 clears any existing items, pass 2 walks sections in order creating (pageBreak, items) pairs so Forms' implicit "items belong to the most recent page break" rule produces correct groupings.
- [x] **E3-F2-GF-003** Section-based skip logic wiring (`setJumpTo` / section branching) per the restructured logic from E2-F2-014 `status::done` `priority::critical` `estimate::4h`
  - `FormBuilder.wireRouting_` applies per-choice `PageNavigationType` via `createChoice(text, pageBreakItem)` on the last branching item of each section. Forward-reference targets are resolved via a `pages` dict keyed by sectionId (see `F2-Skip-Logic.md` for the section graph). Role-bucket gates re-ask role at `SEC-C-gate` and `SEC-F-router` since Forms has no cross-section memory.
- [x] **E3-F2-GF-004** Consent click-through + acknowledgement as required first section (replaces "read aloud" flow) `status::done` `priority::critical` `estimate::2h`
  - `SEC-COVER` is the first section with the consent click-through. Decline routes to `SEC-DECLINE` (thank-you page); consent routes to `SEC-COVER2` (facility confirmation). `OnSubmit.CONS-02` drops all Q* body answers on declined submissions as a defensive POST check.
- [x] **E3-F2-GF-005** Facility ID handling — unique prefilled link per facility (Apps Script generator reads a facility master list, emits one prefilled link per row) `status::done` `priority::high` `estimate::4h`
  - `Links.gs` implements `generateLinks()` which reads a `FacilityMasterList` Sheet (columns: facility_id, facility_name, facility_type, facility_has_bucas, facility_has_gamot, region, province, city_mun, barangay, hcw_emails semicolon-separated) and emits one prefilled URL per (facility × HCW email) into a new `F2-Links` Sheet. Prefills facility_id, facility_type, BUCAS, GAMOT, and response_source=self via `FormResponse.toPrefilledUrl()`.
- [x] **E3-F2-GF-006** Google sign-in required; response destination configured → Google Sheet in project mailbox Drive `status::done` `priority::high` `estimate::1h`
  - `Code.buildForm` calls `setRequireLogin(true)`, `setCollectEmail(true)`, and `setDestination(SPREADSHEET, ss.getId())`. Response sheet is named `F2-Responses` in the same Drive.
- [x] **E3-F2-GF-007** `response_source` auto-captured field — distinguishes `self` vs `staff_encoded` submissions `status::done` `priority::high` `estimate::1h`
  - Hidden `response_source` field lives in `SEC-COVER2` and is prefilled by `Links.generateLinks()` (self) or by `Code.buildStaffEncoderForm` (staff_encoded). `OnSubmit.SRC-01..03` validates source integrity.
- [x] **E3-F2-GF-008** Reminder cadence automation (Apps Script time-driven trigger) — Day 1 / Day 2 / Day 3 reminders to non-completers reading the response Sheet `status::done` `priority::high` `estimate::4h`
  - `Reminders.gs` installed as a 09:00 Manila daily trigger by `Code.installReminderTrigger_`. `runRemindersNow()` reads `F2-Links` + the response Sheet, diffs by email, and sends Day 1/2/3 nudges via `MailApp.sendEmail`. Also manually runnable for testing.
- [ ] **E3-F2-GF-009** Staff encoder variant of the Form (Fallback A) — prefilled `response_source=staff_encoded`, no sign-in required, accessible to ASPSI staff only `status::todo` `priority::high` `estimate::2h`
- [ ] **E3-F2-GF-010** Paper mirror Google Doc generator — same Apps Script reads the spec and emits a print-ready Doc `status::todo` `priority::high` `estimate::4h`
- [ ] **E3-F2-GF-011** Filipino translations wired into the Form (second-language variant or bilingual inline) `status::todo` `priority::high` `estimate::1d`
- [ ] **E3-F2-GF-012** Desk test — walk every skip path from the spec against the generated Form `status::todo` `priority::critical` `estimate::4h`
- [ ] **E3-F2-GF-013** 3-day internal dry-run test with 1–2 testers — validates save/resume across the window and reminder firing `status::todo` `priority::critical` `estimate::3d (elapsed)`
- [ ] **E3-F2-GF-014** Shan QA pass on the generated Form + test cases `status::todo` `priority::high` `estimate::4h`
- [ ] **E3-F2-GF-015** Gate decision — after test, assess whether the deferred F2-CSPro track should be activated or stay parked `status::todo` `priority::medium` `estimate::1h`

### CSPro CAPI track *(DEFERRED — optional late build)*

> Conditional on E3-F2-GF-015 gate decision. If activated, scheduled **last** in the Epic 3 sequence after F1/F3/F4 CSPro builds are complete. ASPSI-facing purpose: let staff encode paper F2 responses into CSPro instead of Google Forms. See `memory/project_f2_capture_modes.md`.

- [ ] **E3-F2-CSPro-001..060** CSPro Designer build using standard F1 template, adapted for paper-to-CAPI encoding workflow (no interviewer text, no GPS, no live consent — encoder reads from paper) `status::deferred` `priority::low`

---

## F3 — Patient Survey

**Prerequisite:** E2-F3-010 (F3 DCF sign-off)

- [ ] **E3-F3-001..060** Standard template; reuses F1's interviewer-administered patterns
- [ ] **E3-F3-015** Outpatient vs inpatient branching at eligibility screen `status::todo` `priority::high` `estimate::4h`

*(Full task list to be expanded when F3 enters a sprint.)*

---

## F4 — Household Survey

**Prerequisite:** E2-F4-010 (F4 DCF sign-off)

F4 inherits the standard template **plus a roster engine**. The household roster loop is the primary technical challenge in this instrument.

- [ ] **E3-F4-001..060** Standard template per F1
- [ ] **E3-F4-070** Household roster grid: add-member, edit-member, remove-member, reorder `status::todo` `priority::critical` `estimate::2d`
- [ ] **E3-F4-071** Per-member sub-questionnaire loop (conditional on age/relation/etc.) `status::todo` `priority::critical` `estimate::2d`
- [ ] **E3-F4-072** Cross-member consistency rules (e.g., only one household head, spouse implies head exists) `status::todo` `priority::high` `estimate::1d`
- [ ] **E3-F4-073** Max roster size validation + soft warning at unusual sizes `status::todo` `priority::high` `estimate::2h`

*(Full task list to be expanded when F4 enters a sprint.)*

---

## PLF — Patient Listing Form

**Prerequisite:** E2-PLF-006 (implementation decision + any dictionary work)

- [ ] **E3-PLF-001** If CAPI: minimal form with facility selector + patient entries grid `status::todo` `priority::medium` `estimate::4h`

## Notes

- **F1 is the priority.** Its full task breakdown above is the template for the others.
- F2/F3/F4 task lists are stubs — they'll be expanded as each instrument enters its build sprint. Front-loading detailed task breakdowns for instruments months away is wasted effort because the specifics will shift.
- Reusable patterns established in F1 (e.g., consent flow, FIELD_CONTROL block, GPS capture) should be extracted into includable `.apc` fragments for later instruments.
