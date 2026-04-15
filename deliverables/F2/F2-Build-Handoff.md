---
title: F2 Build Handoff — Paste, Run, Test
instrument: F2
version: draft-2026-04-15
depends_on:
  - deliverables/F2/apps-script/
  - deliverables/F2/F2-Spec.md
  - deliverables/F2/F2-Skip-Logic.md
  - deliverables/F2/F2-Validation.md
  - deliverables/F2/F2-Cross-Field.md
author: Carl Reyes
audience: Carl (build), Shan (test)
status: draft-for-review
---

# F2 Build Handoff — Paste, Run, Test

End-to-end recipe to take the F2 Apps Script bundle from `deliverables/F2/apps-script/` and land a live Google Form that Shan can start testing. Three phases: **Build** (Carl, ~15 min), **Seed** (Carl, ~10 min), **Test** (Shan, ~45 min for one full pass).

## Phase 1 — Build (Carl)

### Step 1. Create the Apps Script project

1. Sign in to Google as **`aspsi.doh.uhc.survey2.data@gmail.com`** (the ASPSI project mailbox).
2. Open <https://script.google.com> → **New project**.
3. Rename the project to `F2-HCW-Survey-Builder`.
4. In the editor's left panel, for each file in `deliverables/F2/apps-script/`:
   - Click the **+** next to "Files" → **Script**.
   - Name it exactly (e.g., `Code`, `Spec`, `FormBuilder`, `OnSubmit`, `Reminders`, `Links`, `Routing`). Apps Script appends `.gs` automatically.
   - Paste the file's contents verbatim.
5. Delete the default empty `Code.gs` that Apps Script created at project start (it would conflict with the pasted `Code.gs`).

> **Note.** You do **not** paste `README.md` into Apps Script — that file is documentation only.

### Step 2. Run `buildForm`

1. In the Apps Script editor's top bar, select the **`buildForm`** function from the dropdown.
2. Click **Run**.
3. First run will prompt: "Authorization required" → **Review permissions** → sign in as the project mailbox → **Advanced** → **Go to F2-HCW-Survey-Builder (unsafe)** → **Allow**. The scopes requested are: Forms, Drive, Sheets, Script Triggers, Gmail (for reminders).
4. The run takes ~60–90 seconds. Watch **View → Logs** (Ctrl+Enter) for the three URLs printed at the end:

   ```
   Form:   https://docs.google.com/forms/d/e/.../viewform
   Edit:   https://docs.google.com/forms/d/.../edit
   Sheet:  https://docs.google.com/spreadsheets/d/.../edit
   FormID: 1xxxxx...
   ```

5. Save all three URLs somewhere durable (e.g., paste them into `scrum/sprint-current.md` Daily Notes for today).

### Step 3. Sanity-check the Form

1. Open the **Edit** URL and skim: should see ~35 sections from `SEC-COVER` through `SEC-END`.
2. Open the **Form** (viewform) URL in an incognito window. Google will ask you to sign in (required by the build). Sign in with any non-ASPSI test account (your personal Gmail is fine for a smoke test).
3. Click through the consent page → confirm you land on `SEC-COVER2` (facility confirmation) → click through to Section A.
4. **Don't submit yet** — this smoke pass is just to confirm the build didn't crash silently.

### Known build caveats

- **Page-break routing can only read the LAST multiple-choice item of a section.** Branches are intentionally structured so each branching question is the last item in its section (see `Spec.gs`). If you edit `Spec.gs` and add a new item *after* a branching one in the same section, the routing silently stops working. Rule of thumb: put branching questions alone at the end of their section.
- **Role bucket is re-asked**, not remembered. `SEC-C-gate` and `SEC-F-router` both ask a routing-only confirmation question. This is the Google Forms workaround for lack of cross-section memory and is documented in `F2-Skip-Logic.md` open item #2.
- **Q103 is a standalone single-choice**, not part of Grid #2. This is a deliberate lift from `F2-Validation.md` so Q111 skip-if-Never works. Don't merge it back into the grid without also rewriting the routing.
- **Facility-type ZBB/NBB splits (Q62/Q62.1, Q67/Q67.1, Q78/Q78.1)** are all shown to all Section G respondents. `OnSubmit.gs` drops the non-applicable variant in POST based on `facility_type`. Form-side filtering is intentionally avoided because Forms grids and scale items don't support section routing.

## Phase 2 — Seed (Carl)

### Step 4. Create a test `FacilityMasterList` Sheet

This is a **stub** so Carl can generate prefilled links for testing without waiting on ASPSI's real master list.

1. In the project mailbox Drive, create a new Google Sheet named exactly **`FacilityMasterList`**.
2. Row 1 headers (exact spelling):

   ```
   facility_id | facility_name | facility_type | facility_has_bucas | facility_has_gamot | region | province | city_mun | barangay | hcw_emails
   ```

3. Seed 3 test rows covering the main facility-type splits:

   | facility_id | facility_name | facility_type | facility_has_bucas | facility_has_gamot | region | province | city_mun | barangay | hcw_emails |
   |---|---|---|---|---|---|---|---|---|---|
   | TEST-DOH-01 | DOH Test Hospital A | DOH-retained hospital | Yes | Yes | NCR | Metro Manila | Manila | Test | shan.qa@example.com;carl.test@example.com |
   | TEST-PUB-01 | Public Test Hospital B | Public hospital (non-DOH-retained) | No | Yes | Region III | Bulacan | Malolos | Test | shan.qa@example.com |
   | TEST-RHU-01 | Test RHU C | RHU / Health center | No | No | Region IV-A | Laguna | San Pablo | Test | shan.qa@example.com |

4. Replace `shan.qa@example.com` with Shan's real Google email before generating links.

### Step 5. Run `generateLinks`

1. Back in the Apps Script editor, select **`generateLinks`** from the function dropdown.
2. Click **Run**. The function reads `FacilityMasterList`, generates prefilled URLs, and writes them to a new Sheet named **`F2-Links`** in the same Drive.
3. Open `F2-Links` → copy the `prefilled_url` values for the rows you want Shan to test.

### Step 6. (Optional) Build the staff encoder variant

1. Select **`buildStaffEncoderForm`** and run it.
2. Logs print a second Form URL tagged with `response_source=staff_encoded`.
3. Share the edit URL with the ASPSI encoder team once the primary Form is validated.

## Phase 3 — Test (Shan)

### Step 7. Receive test links

Carl sends Shan 3 prefilled URLs (one per test facility). Each link has a different facility_type / BUCAS / GAMOT combination so Shan can validate the conditional routing across the splits.

### Step 8. Test cases — one pass per facility type

For **each** of the three test links:

1. Open the link in a fresh incognito window and sign in with the test Google account.
2. **Consent pathway:**
   - [ ] Decline consent → confirm you land on the thank-you page and no more questions appear.
   - [ ] Re-open the link, accept consent → confirm you proceed to facility confirmation.
3. **Facility confirmation:**
   - [ ] Fields `facility_type`, BUCAS, GAMOT are pre-filled matching the link you opened.
4. **Section A — Profile:**
   - [ ] Q4 age: try 17 (should reject) and 25 (should accept).
   - [ ] Q5 role: try each of the three role buckets (Doctor, Pharmacist, Barangay Health Worker) in separate passes to validate routing.
5. **Section B:**
   - [ ] Q12 = **No** → confirm you skip directly to the role-bucket gate (not through Q13–Q26).
6. **Section C/D/E1/E2 routing:**
   - [ ] Doctor pass: confirm you see all of Sections C, D, E1 (if BUCAS=Yes), E2 (if GAMOT=Yes).
   - [ ] Pharmacist pass: confirm you skip C + D and land directly on E2.
   - [ ] Other role pass: confirm you skip C/D/E1/E2 entirely and land on Section F.
7. **Section G (physicians/dentists only):**
   - [ ] Doctor pass: see Q56 through Q80 including both Q62 ZBB and Q62.1 NBB on Section G4.
   - [ ] Non-doctor pass: skip Section G entirely (routed from `SEC-F-router`).
8. **Section J terminal branch:**
   - [ ] Q103 = **Never** → confirm Q111 does NOT appear and you go straight to Q112 path.
   - [ ] Q103 = anything else → confirm Q104–Q110 grid + Q111 appear.
   - [ ] Q112 = **No, I haven't thought about it** → confirm you skip Q113/Q114 and go to End of survey.
9. **Submit** each pass and check the response Sheet.

### Step 9. Validate POST rules in the response Sheet

Open the `F2-Responses` Sheet after each submission and verify:

- [ ] `_qa_flags` is empty on clean rows.
- [ ] `_qa_disposition` shows `completed` (or `declined` on the decline pass).
- [ ] `_derived_employment_class` shows `full-time` if Q11 ≥ 8, else `part-time`.
- [ ] For a non-doctor pass, any Q55–Q80 values that leaked get dropped, and `_dropped_fields` lists them.
- [ ] For a non-DOH-retained pass, Q62/Q67/Q78 (ZBB) are dropped. For Private facility pass, both ZBB and NBB are dropped.
- [ ] Try submitting with Q4=12 age + Q9a=10 tenure years (invalid combo if passed) — confirm `PROF-01` appears in `_qa_flags` on the nightly rerun (or re-run `runNightlyCleanSheet` manually).

### Step 10. Bug reporting

When Shan finds a bug or unexpected behavior, route it back to the **owning source doc** per the forward-only sign-off rule (see `memory/feedback_forward_signoff_loopback_bugs.md`):

| Symptom | Fix in |
|---|---|
| Wrong label text, missing question, wrong choices | `deliverables/F2/F2-Spec.md` + `apps-script/Spec.gs` |
| Wrong section routing, skip logic doesn't fire | `deliverables/F2/F2-Skip-Logic.md` + `apps-script/Spec.gs` (branchTo map) |
| Wrong required flag, numeric range rejects valid values | `deliverables/F2/F2-Validation.md` + `apps-script/Spec.gs` |
| POST rule mis-fires (wrong flag, wrong drop) | `deliverables/F2/F2-Cross-Field.md` + `apps-script/OnSubmit.gs` |
| Apps Script crashes, routing mis-wires | `apps-script/FormBuilder.gs` or `Code.gs` |
| Consent or cover-block wording | `deliverables/F2/F2-Cover-Block-Rewrite-Draft.md` + `apps-script/Spec.gs` (SEC-COVER) |

After a fix, re-run **`rebuildForm()`** in Apps Script. This deletes the old Form + Sheet and rebuilds fresh. Shan's test submissions on the old Form are lost — that's expected. Every rebuild cycle starts clean.

## Rollback / reset

- **Delete everything:** run `rebuildForm()` — trashes the old Form + Sheet, clears script properties, rebuilds from `Spec.gs`.
- **Delete the Apps Script project:** from <https://script.google.com> → right-click the project → **Remove**. Any triggers, Forms, and Sheets it owns must also be trashed manually in Drive.
- **Stop reminder emails:** from Apps Script editor → **Triggers** (clock icon) → delete the daily `runRemindersNow` trigger.

## Decisions still open (not blockers)

These are stubbed with defaults in the Spec; flipping any is a one-line `Spec.gs` edit + `rebuildForm()`:

1. **Q1 name fields** — currently optional for raffle. Remove if SJREB requires anonymization.
2. **Completion time estimate** — "~25 minutes" in the cover description is a placeholder; Shan's dry-run gives the real number.
3. **Role-bucket UX** — the re-ask at `SEC-C-gate` and `SEC-F-router` is the current workaround. Open to better ideas if Forms adds cross-section memory.
4. **Facility master list schema** — the stub `FacilityMasterList` above needs to be replaced with the real ASPSI master list once delivered.
5. **DISP-03 rapid-submission threshold** — 5 min is a guess. Shan's dry-run timings will give a real baseline.
6. **Reminder wording** — default copy is in `Reminders.gs`. ASPSI may want a more formal tone.

See `F2-Spec.md` and `F2-Skip-Logic.md` for the full list of ~15 ASPSI-facing decisions. None are gating Shan's first test pass.
