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

## F2 — Healthcare Worker Survey *(self-administered)*

**Prerequisite:** E2-F2-010 (F2 DCF sign-off)

- [ ] **E2-F2-001..060** Standard template per F1 above, adapted for **self-administered mode**:
  - No interviewer present → soft warnings behave differently (respondent confirms, not interviewer)
  - Consent flow differs (self-clicked, not interviewer-read)
  - Eligibility screen must be self-explanatory
  - Question text must be fully unambiguous (no interviewer to interpret)
  - Navigation must be forgiving (respondents may hit wrong buttons)
- [ ] **E3-F2-015** Self-admin UX review: ensure question wording is unambiguous without an interviewer `status::todo` `priority::high` `estimate::1d`
- [ ] **E3-F2-016** Self-admin navigation: back-button tolerance, resume after accidental close `status::todo` `priority::high` `estimate::4h`

*(Full task list to be expanded when F2 enters a sprint.)*

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
