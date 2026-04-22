---
title: F2 Google Form — Apps Script build bundle
instrument: F2
version: draft-2026-04-21-apr20
supersedes: draft-2026-04-15 (April 8 PDF)
source_docs:
  - deliverables/F2/F2-Spec.md (Apr 20 rev)
  - deliverables/F2/F2-Skip-Logic.md (Apr 20 rev)
  - deliverables/F2/F2-Validation.md (Apr 20 rev)
  - deliverables/F2/F2-Cross-Field.md (Apr 20 rev)
  - deliverables/F2/F2-Cover-Block-Rewrite-Draft.md
target: script.google.com (ASPSI project mailbox `aspsi.doh.uhc.survey2.data@gmail.com`)
author: Carl Reyes
status: build-draft-apr20
---

# F2 Google Form — Apps Script build bundle

This directory is an **Apps Script project** that builds the F2 Healthcare Worker Survey as a Google Form. Paste the files into a new script at https://script.google.com while signed in as the ASPSI project mailbox. Running `buildForm()` materializes the Form, wires skip logic, attaches the `onFormSubmit` POST-processing trigger, and installs the daily reminder trigger.

## File map

| File | Purpose |
|---|---|
| `Code.gs` | Main entry — `buildForm()`, `rebuildForm()`, custom menu, orchestration |
| `Spec.gs` | Full Apr 20 spec as structured JS data (124 actual items, numbered Q1–Q125 with Q108 as a PDF numbering gap) — sections, items, choices, routing |
| `FormBuilder.gs` | Helpers that materialize spec entries into Form items |
| `Routing.gs` | Section-based branching helpers (`setGoToPageBasedOnAnswer`) |
| `OnSubmit.gs` | `onFormSubmit` trigger — runs the 20 POST rules from F2-Cross-Field.md |
| `Reminders.gs` | Time-driven trigger — Day 1/2/3 reminders to non-completers |
| `Links.gs` | Prefilled-link generator from a facility master list Sheet |

## One-time setup

1. Sign in to Google as `aspsi.doh.uhc.survey2.data@gmail.com`.
2. Open https://script.google.com → New project → name it `F2-HCW-Survey-Builder`.
3. For each `.gs` file in this directory, create a matching file in the Apps Script editor and paste the contents verbatim. (Apps Script auto-merges `.gs` files into one namespace.)
4. In the editor, run the `buildForm` function. First run will prompt for auth scopes: Forms, Drive, Sheets, Script triggers.
5. After the run completes, the script log prints the Form URL, the linked response Sheet URL, and the Form ID. Save these.
6. Open the Form → Settings → Responses → "Collect email addresses" is already set by the script. Confirm. Form is live.

## Rebuilding after a spec change

1. Edit `Spec.gs` (or any other file).
2. Run `rebuildForm()` — this deletes the existing Form/Sheet and creates new ones. All test submissions are lost; all triggers are re-installed cleanly.
3. Alternatively run `buildForm()` with a different `FORM_TITLE` constant to keep both versions side-by-side.

## Running the reminder job manually

- `runRemindersNow()` — sends Day 1/2/3 reminders based on the current response Sheet state. Useful for testing.
- The time-driven trigger installed by `buildForm()` runs this function daily at 09:00 Manila time.

## Generating per-facility links

- Prepare a Sheet named `FacilityMasterList` in the same Drive with columns: `facility_id`, `facility_name`, `facility_type`, `facility_has_bucas`, `facility_has_gamot`, `region`, `province`, `city_mun`, `barangay`, `hcw_emails` (semicolon-separated).
- Run `generateLinks()` — writes a new Sheet `F2-Links` with one row per facility × HCW, including the prefilled URL.

## Staff encoder variant

- `buildStaffEncoderForm()` creates a parallel Form with `response_source=staff_encoded` baked in and sign-in disabled. Shares the same response Sheet so POST rules apply uniformly.

## Known limitations / open items

- **Section-based routing only.** Forms does not support per-question branching; any rule in `F2-Skip-Logic.md` that needs per-question skip is handled by placing the branching question alone on its own page.
- **No cross-section memory.** Role bucket (BUCKET-CD / BUCKET-PHARM / BUCKET-OTHER) is re-asked at each gate rather than remembered from Q5. See `F2-Skip-Logic.md` open item #2.
- **Q114 lifted from Grid #2 (Apr 20).** See `F2-Validation.md` — Q114 is a standalone single-choice so Q122 skip-if-Never survives the Forms translation. (Was Q103 in the Apr 08 spec.)
- **Facility-type triple-pair (Apr 20).** Q69/Q70, Q75/Q76, Q87/Q88 — ZBB + NBB siblings instead of the Apr 08 ZBB-with-NBB-.1 pattern. Handled via three facility-type router sections (SEC-G3, SEC-G-scales, SEC-G-Q87) per `F2-Skip-Logic.md`.
- **Q108 numbering gap.** Apr 20 PDF numbers items Q1–Q125 but Q108 is omitted. Builder must NOT emit a Q108 field. Cross-field `SCHEMA-01` rule guards against accidental emission.
- **~15 ASPSI decisions still open.** The build uses defaults from the spec docs; flipping any default is a one-line `Spec.gs` edit followed by `rebuildForm()`.

## Handoff to Shan

See `deliverables/F2/F2-Build-Handoff.md` for the tester-facing recipe (when written — task #11).
