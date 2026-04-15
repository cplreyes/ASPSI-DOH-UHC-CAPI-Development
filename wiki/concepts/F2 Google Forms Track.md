---
type: concept
tags: [f2, google-forms, apps-script, capi, self-admin, special-case]
source_count: 1
---

# F2 Google Forms Track

F2 (Healthcare Worker Survey) is an **explicit special case** in the project — it is not a CSPro CAPI instrument by default. Unlike F1/F3/F4, the primary build lives in Google Forms driven by a Google Apps Script generator, with CSPro held in reserve as an optional late build.

## Why a special case

- The Revised Inception Report specifies F2 as **self-administered** — HCWs fill the form themselves, no enumerator.
- A tablet-and-CSPro workflow doesn't fit a self-admin respondent population (no trained interviewer, no device, no field logistics).
- Google Forms gives HCWs a familiar web-form experience on their own devices, handles login + email collection natively, and is the fastest path to a testable artifact.
- F1 sign-off is therefore **not** a hard gate for starting F2 — the Google Forms path doesn't reuse F1's CSPro patterns, so the tracks run in parallel.

## Three capture paths

1. **Google Forms (primary).** HCW self-administers within a **3-day window** via a per-facility prefilled link. Reminder emails fire on Day 1 / Day 2 / Day 3 to non-completers (Apps Script time-driven trigger). Response destination is a Google Sheet in the ASPSI project mailbox Drive.
2. **Paper → Forms encoding (fallback).** In low-connectivity areas, HCWs fill paper. ASPSI staff then transcribes paper responses into a **staff-encoder variant** of the same Form — same fields, no sign-in required, `response_source=staff_encoded`. Both self-admin and staff-encoded responses land in the same response Sheet and go through the same POST rules.
3. **CSPro CAPI track (deferred).** Optional late build, scheduled as the **tail** of Epic 3 after F1/F3/F4 CSPro builds are complete. Purpose: let staff encode paper responses into CSPro instead of Google Forms. Activated only if F2 Google Forms testing surfaces a need. Existing `E3-F2-CSPro-*` tasks carry `status::deferred` until the gate decision at `E3-F2-GF-015`.

## Build artifacts

All drafted 2026-04-15 in `deliverables/F2/`:

- **`F2-0_Tooling-and-Access-Model-Decision-Memo.md`** — 8 decisions for ASPSI review (platform, access model, reminder cadence, facility ID, PSGC dropdowns, paper fallback, staff encoder workflow, response custody).
- **`F2-Cover-Block-Rewrite-Draft.md`** — Rewrites the April 8 PDF's interviewer-style cover blocks (consent, duration, FIELD CONTROL, facility ID) for self-admin. Resolves the cover-block contradiction documented in [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F2 Healthcare Worker Survey Questionnaire|Source - Annex F2]].
- **`F2-Spec.md`** — 114-item verbatim body spec with original question numbers, 18 SECTION + 9 SPLIT Google Forms routing risks flagged.
- **`F2-Skip-Logic.md`** — Section graph + normalised routing table + POST-processing triage, restructured for Google Forms' "last-item-of-section" branching constraint.
- **`F2-Validation.md`** — 4 hard-required fields inventory, numeric range inventory, Q103 lifted from grid to standalone.
- **`F2-Cross-Field.md`** — 20 POST rules for `onFormSubmit` + nightly `cleanSheet()` (6 rule groups: response source, consent, section gates, facility-type splits, profile, disposition).
- **`apps-script/`** — Apps Script bundle (`Code.gs`, `Spec.gs`, `FormBuilder.gs`, `OnSubmit.gs`, `Reminders.gs`, `Links.gs`, `Routing.gs`, `README.md`). Two-pass form materializer, per-choice `createChoice(c, pageBreakItem)` routing, prefilled URL generator reading a `FacilityMasterList` Sheet.
- **`F2-Build-Handoff.md`** — 3-phase recipe (Build 15 min / Seed 10 min / Test 45 min per pass) covering paste into script.google.com, `buildForm()` run, `FacilityMasterList` stub with 3 test rows, [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Shan Lait|Shan]]-facing test cases per role bucket + ZBB/NBB split + terminal branch, and a symptom→source-doc bug-routing table per the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Forward-Only Sign-Off|forward-only sign-off rule]].

## Google Forms routing constraints

These are the tactical realities the spec works around:

- **Page-break routing can only read the LAST MultipleChoiceItem of a section.** Every branching question is intentionally the last item in its section. Adding a new item *after* a branching one silently breaks routing.
- **No cross-section memory.** Role bucket is re-asked at `SEC-C-gate` and `SEC-F-router` because Forms cannot remember earlier answers for later routing.
- **Grids and scales don't support section routing.** Facility-type ZBB/NBB dual variants (Q62/Q62.1, Q67/Q67.1, Q78/Q78.1) are all shown to every Section G respondent; `OnSubmit.gs` drops the non-applicable variant in POST based on `facility_type`.
- **Standalone lift for Q103.** Q103 was lifted out of the Q103–Q110 grid into its own single-choice item so Q111 skip-if-Never can fire.

## Open items at handoff

Stubbed with defaults in `Spec.gs`; each is a one-line edit + `rebuildForm()`:

1. Q1 name fields — optional for raffle; remove if SJREB requires anonymization.
2. Completion time estimate — "~25 minutes" placeholder; dry-run gives the real number.
3. Role-bucket UX — re-ask at `SEC-C-gate` / `SEC-F-router` is the current workaround.
4. Facility master list schema — stub `FacilityMasterList` needs replacement with ASPSI's real list.
5. `DISP-03` rapid-submission threshold — 5 min is a guess; dry-run timings give a real baseline.
6. Reminder wording — default copy in `Reminders.gs`; ASPSI may want a more formal tone.

None gate [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Shan Lait|Shan]]'s first test pass.

## Scrum references

- **Epic 2 (design):** E2-F2-011 through E2-F2-018 — all drafted through E2-F2-016 as of 2026-04-15.
- **Epic 3 (build):** E3-F2-GF-001 through E3-F2-GF-015 — -001 through -008 drafted; -009..-015 open (staff encoder variant, paper mirror Doc, Filipino translations, desk test, 3-day dry-run, Shan QA pass, gate decision).
- **Deferred:** E3-F2-CSPro-001..060 carry `status::deferred`.

## Memory

- `memory/project_f2_capture_modes.md` — three capture paths rule.
- `memory/project_f2_self_admin_window.md` — 3-day window is an established field rule.
- `memory/project_f2_questionnaire_rewrite_needed.md` — April 8 PDF cover-block contradiction.
