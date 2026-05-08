---
title: "04 — Phase 6: CAPI Application Build"
category: deliverable
tags: [capi, cspro, csentry, application-build, multi-language, gps, uhc-y2]
last_updated: 2026-05-08
status: draft
---

# 04 — Phase 6: CAPI Application Build

This is the longest doc in the suite for a reason. Phase 6 is where every prior decision — dictionary shape, skip routing, validation tier, value-set composition, capture record layout, sample-frame mechanics — gets wired into a working CSEntry application. Done well, the application is boring to use: enumerator opens it, walks the questions, hits Submit, and the case lands in CSWeb. Done sloppily, it leaks bad data into analysis for a year.

> **Required reading order before this doc:**
>
> 1. [[02-Phase-0-2-Foundation]] — folder layout, mode decisions, ethics path.
> 2. [[03-Phase-3-5-Spec-and-Generators]] — questionnaire ingest + dcf generator.
> 3. [[03-Phase-3-5-Spec-and-Generators]] — skip-logic spec + validation tiers (HARD / SOFT / GATE) + dcf v2.
>
> Phase 6 assumes you have a v2 dcf that opens cleanly in Designer, a written `<Instrument>-Skip-Logic-and-Validations.md`, and a `<Instrument>-Form-Layout-Plan.md` per [[../CSPro/Form-Layout-Principles]]. If any of those are missing or stale, **stop and finish them first**. Form rework after Designer is an order of magnitude more expensive than spec work.

---

## 6.1 Phase 6 mental model

By the time you reach Phase 6, four things are already true:

1. The dcf is **validated** — Designer opens it, item count matches printed questionnaire (allowing for select-all expansion), every value set is bound. See [[03-Phase-3-5-Spec-and-Generators]] §2.6.
2. The **skip-logic spec is written** — every conditional jump in the questionnaire has a row in the skip table, every cross-field check has a tier (HARD / SOFT / GATE) and a paste-ready PROC template. See [[03-Phase-3-5-Spec-and-Generators]] §3.4.
3. The **form-layout plan is approved** — every record maps to a form (or a form split), every form fits the row budget, capture forms are isolated from data-entry forms. See [[../CSPro/Form-Layout-Principles]] §10.
4. **Ethics clearance is in motion** — Phase 6 build runs in parallel with the SJREB clearance pipeline; you do not wait for ethics to start building, but no pretest case is ever entered until clearance is in hand.

Phase 6 itself is **Designer wiring** — turning data structure into an interview tool. The work happens in a fixed inside-out order:

1. Form file (.fmf) skeleton — generator-emitted, Designer-polished.
2. Question text + fills — readable prompts with personalization.
3. Skip logic in .apc — the spec's skip table, paste-ready.
4. Validation wiring — the spec's HARD / SOFT / GATE rules.
5. Externalized validators (.apc helpers) — reusable across instruments.
6. Externalized error messages — translation surface.
7. Dynamic value sets — context-dependent option lists (PSGC cascade, role-based filtering).
8. Capture types per item — Radio / Drop Down / Number Pad / Date / Text Box / Multi-select grid.
9. FIELD_CONTROL block — consent + eligibility + AAPOR + GPS + interviewer IDs.
10. GPS + photo capture — `Capture-Helpers.apc` wiring + paradata.
11. Durable resume — OnStop + savepartial.
12. Multi-language — three-stack model (dictionary / questions / messages) + per-language value sets.
13. Block organization — Add Block + block-level preproc.
14. Sample-file integration (F4 only).
15. EA boundary fence — optional geofencing.
16. PFF + entry application packaging.

Each section below covers one of those steps with paste-ready snippets adapted to the UHC F1/F3/F4 instruments.

> **Codification anchor.** Every Khurshid technique cited below is one of the cards in `3_Resources/Learning-Materials/mentors/khurshid-arshad/videos/<date_slug>/techniques.md`. Where a snippet is adapted to UHC, the original Khurshid pattern is cited with a date and (where helpful) the video title; the adaptation is then noted explicitly so future readers can trace what changed and why.

---

## 6.2 Form file (.fmf) construction

### 6.2.1 .fmf vs .ent — which file is what

| File | Purpose | Hand-edited? |
|---|---|---|
| `<Instrument>.dcf` | Data dictionary — record / item / value-set definitions. | No — generator emits it. |
| `<Instrument>.fmf` | Form file — visual layout: which items go on which form, control type, position, labels. | Generator emits a skeleton; **Designer is the editor of record** for layout polish. |
| `<Instrument>.ent` | Entry application — top-level package referencing dcf + fmf + .apc + .mgf + config. | Designer-managed. |
| `<Instrument>.ent.apc` | Application logic — PROC GLOBAL + per-form / per-item handlers. Skip logic, validations, capture wiring, language switches. | Hand-edited (with snippets pasted from spec + helper APCs `#include`d). |
| `<Instrument>.ent.qsf` | Question text (CAPI questions). | Designer + Question Text editor. |
| `<Instrument>.ent.mgf` | Message file — error/warning strings, externalised by ID, multi-language. | Designer-managed via the Messages tab. |
| `<Instrument>.pff` | Program Information File — what CSEntry runs at launch. Specifies dcf, fmf, app, data-output path, language, sync settings. | Generated/edited at packaging. |

The **entry application** (`.ent`) is the umbrella. Designer's "Application Properties" dialog drives the .ent fields. Everything else is a satellite file linked from there.

### 6.2.2 Building a form by dragging dictionary items

**(Khurshid 2022-03-27 *Tutorial 1: Create Login Application*)** — the canonical Designer workflow:

1. Open `<Instrument>.ent` in CSPro Designer.
2. **Forms tab** → right-click → New Form → name it per the form-layout plan (e.g. `FC_METADATA`, `A1_PROFILE`).
3. **Dictionary tree** (left pane) → expand the record (e.g. `FIELD_CONTROL`) → select the item.
4. **Drag** the item onto the form canvas. Designer drops a label + control bound to that dictionary item.
5. Right-click the control → Properties → set **Capture Type** (Radio / Drop Down / Number Pad / Date / Text Box / Multi-select), label position, font, size.
6. Tab order is **reading order** unless you explicitly override it — top-to-bottom, left-to-right. Do not use tab order to implement skip logic; that lives in the .apc.

**Toggle dictionary tree between names and labels with `Ctrl+T`** **(Khurshid 2022-03-27)**. Names are useful when you're cross-referencing the .apc; labels are useful when laying out forms (the label is what the enumerator sees).

### 6.2.3 Form layout principles

All form construction follows the rules in [[../CSPro/Form-Layout-Principles]]. The compressed version:

- One form per natural questionnaire subsection. Never combine two subsections on one form.
- No vertical scroll on capture forms. Row budget ≤ 12 comfortable, ≤ 16 hard ceiling.
- Rosters scroll alone — no adjacent non-roster fields on a roster form.
- One logical question per field. Skip logic in `.apc`, not packed into UI.
- Tap targets must be touch-sized — Galaxy Tab A 10.1" is the reference device.
- "Other (specify)" follow-up text fields always sit on the same form as their parent.

Read [[../CSPro/Form-Layout-Principles]] §1–§10 in full before starting. The **review checklist** in §10 is the gate before you sign off any .fmf.

### 6.2.4 One form per natural questionnaire section

Per-instrument form counts (from the per-F-series form-layout plans):

| Instrument | Records | Items | Forms (planned) | Splits driven by |
|---|---|---|---|---|
| **F1 Facility Head** | 12 | ~671 | **29** (25 built + 4 stub rosters) | Section C split 5×, Section D 4× (Q51 gate), Section G 4× named subsections, secondary-data rosters. |
| **F3 Patient** | 18 | ~806 | **30** | Section B 3× (demographics / disability / income), Section G/H 3× each (payment matrix), Section I 3× (NBB+ZBB / MAIFIP / distress), Q1 patient-vs-proxy gate. |
| **F4 Household** | 22 | ~623 | **24** | Roster cardinality (one form per roster), Section roster + per-person blocks, sample-file linkage form. |

For F1, see [[../CSPro/F1/F1-Form-Layout-Plan]] §2–§3 for the full form-by-form inventory. F3 plan: [[../CSPro/F3/F3-Form-Layout-Plan]]. F4 plan: [[../CSPro/F4/F4-Form-Layout-Plan]].

### 6.2.5 FMF skeleton generators (F3 and F4)

F3 and F4 ship a `generate_fmf.py` next to the dcf generator. It emits `<Instrument>.generated.fmf` — a skeleton .fmf with:

- One Designer "form" per record (or per record-group, when records are bundled — e.g. F3's `REC_PATIENT_HOME_CAPTURE` + `REC_CASE_VERIFICATION` share Form 4).
- Form labels carrying intended Designer splits inline (e.g. `"B. Patient Profile - split into B1/B2/B3 in Designer"`).
- Item membership preserved in source order.
- Default fonts + form size — Designer resizes per density.

The generator is **non-destructive** — it writes to `*.generated.fmf` and never overwrites the committed `<Instrument>.fmf`. Designer wiring is for the **manual splits** the labels signal, plus PROC bindings (skip routing, capture-trigger handlers, language switches) that the skeleton has no awareness of.

Why not generate the final .fmf? Three reasons:

1. **Visual polish is hand work.** Field positions, label widths, font sizes, paired-column layouts (Yes/No + small numeric on one row) all rely on tablet-screen judgment.
2. **Capture-trigger affordances** — the GPS button, the photo button, the camera icon — get sized and placed so an enumerator hits them on the first tap. That's a Designer-eye decision.
3. **Hand-editing the binary .fmf is cheap once the skeleton exists.** Designer's per-form drag-drop is fast; recreating layout from scratch every time the dcf changes is what hurts. Skeleton + Designer = best of both.

F1 was hand-built first (it shipped before the skeleton generator was codified). F3 and F4 follow the skeleton approach. The skeleton generator pattern itself codifies into the workflow template at [[../../../2_Areas/IT-Standards/templates/CAPI-Development-Workflow]] Phase 6.

```python
# F3/generate_fmf.py — reads from dcf, emits skeleton .fmf with intended splits
FORM_PLAN = [
    ("FC Metadata - case start",
     [("FIELD_CONTROL", {"names": FIELD_CONTROL_CASE_START})]),
    ("FC Geographic ID + F1 linkage",
     [("PATIENT_GEO_ID", None)]),
    ("FC Facility GPS Capture",
     [("REC_FACILITY_CAPTURE", None)]),
    ("FC Patient Home GPS + Verification Photo",
     [("REC_PATIENT_HOME_CAPTURE", None),
      ("REC_CASE_VERIFICATION", None)]),
    ("A. Informed Consent (Q1 gate)",
     [("A_INFORMED_CONSENT", None)]),
    ("B. Patient Profile - split into B1/B2/B3 in Designer",
     [("B_PATIENT_PROFILE", None)]),
    # ... 16 forms total
    ("Closing - case end",
     [("FIELD_CONTROL", {"names": FIELD_CONTROL_CASE_END})]),
]
```

Run it:

```bash
cd deliverables/CSPro/F3
python generate_fmf.py    # writes PatientSurvey.generated.fmf next to this file
```

Designer then opens `PatientSurvey.generated.fmf`, splits the labelled forms into B1/B2/B3 etc., and saves as `PatientSurvey.fmf` (the committed form file).

### 6.2.6 Form-tree organisation tips

- Name forms `<SECTION>_<TOPIC>` — `A1_PROFILE`, `A2_CONSENT_CONTACTS`, `D1_ACCRED_GATE`, `D2_ACCRED_OPS`. Keeps the form tree scannable.
- Use **section labels** at the top of each form to remind the enumerator which questionnaire section they're in. Section labels cost 0.5 row in the budget (per [[../CSPro/Form-Layout-Principles]] §2).
- Bundle GPS + photo trigger fields onto one **capture form** placed at the natural break (after geographic ID for F1, after consent for F3 patient home, after household roster for F4). Never interleave capture triggers with substantive questions.

---

## 6.3 Question text + fills

The "top half" of each entry screen on a tablet is the **question prompt** the enumerator reads to the respondent. CSPro lets you customise this text per item and per language, with runtime fills, conditional variants, and HTML formatting.

### 6.3.1 The `~~item~~` fill syntax

**(Khurshid 2022-04-05 *Tutorial 3: Writing CSPro Code and Add External Dictionary*)** — fills personalize question text using prior responses.

Pattern: wrap a CSPro logic expression inside paired tildes inside the question text:

```text
Welcome ~~Q1_NAME~~, you said you have been at this facility for
~~Q5_YEARS_AT_FACILITY~~ years and ~~Q5_MONTHS_AT_FACILITY~~ months.
Was this position a promotion?
```

At runtime CSEntry resolves each `~~...~~` against the current case and renders:

```text
Welcome Maria Santos, you said you have been at this facility for
3 years and 6 months.
Was this position a promotion?
```

UHC-specific fill points worth wiring:

| Where | Fill | Why |
|---|---|---|
| F1 Q3 onwards | `~~Q1_NAME~~` | Enumerator says the facility head's name back to confirm — rapport. |
| F3 Section H (inpatient) Q107 onwards | `~~Q14_FACILITY_NAME~~` | "When you were admitted to ~~Q14_FACILITY_NAME~~..." — anchors recall. |
| F4 per-person roster questions | `~~R_NAME(curocc())~~` | "How old is ~~R_NAME(curocc())~~?" — disambiguates between roster occupants. |
| All instruments — closing screen | `~~SURVEY_CODE~~`, `~~QUESTIONNAIRE_NO~~` | Confirms identity at submit. |

**Gotcha:** the expression inside `~~ ~~` must resolve at the moment the question is displayed. Referencing fields not yet entered yields blank. Order question flow accordingly — fills only work backward, never forward.

### 6.3.2 HTML in question text

CSPro question text accepts a small subset of HTML:

```html
<b>Read aloud to respondent:</b><br>
"In the past 6 months, did you receive any in-patient care
at this facility?"<br><br>
<i>Interviewer note:</i> if respondent asks for clarification,
read the WHO definition once: "in-patient care means staying
overnight at the facility for medical care."
```

Tags supported include `<b>`, `<i>`, `<u>`, `<br>`, `<font color="...">`, `<span style="...">`. Use this to:

- **Distinguish what the interviewer reads** from interviewer notes — a common Census Bureau convention is black for read-aloud, blue or italic for instructions to the interviewer.
- **Bold key terms** (definitions, exclusion criteria) so they stand out at a glance.
- **Inject line breaks** between the prompt and its instructions.

Don't go overboard. CSEntry on small tablets renders HTML conservatively; complex layouts collapse. Keep tags to readability aids.

### 6.3.3 Conditional question text

**(Khurshid 2023-03-08 *Create Conditional Questions*)** — multiple question texts on a single item, selected at runtime by a condition.

Use case: F4 roster question that should phrase differently for the household head vs other members:

| Condition | Question text |
|---|---|
| `curocc() = 1` | "Please confirm the household head's name." |
| `curocc() > 1` | "Please enter the name of household member ~~curocc()~~." |

In Designer:

1. Select the item → **CAPI Questions** icon.
2. **Conditions pane** → right-click → Add Condition → enter `curocc() = 1` → fill in the question text in each language.
3. Add another condition → `curocc() > 1` → fill in the alternate text.

Conditions evaluate **top-down**. Put the more specific condition first, the catch-all last.

**(Khurshid 2022-09-26 *Multi Languages for CAPI and Valuesets* @ 05:50)**: dummy variables make conditions cleaner. Instead of `curocc() = 1 and HH_TYPE = 1`, declare a numeric `IS_HEAD_FIRST_OCC` in PROC GLOBAL, set it once at the right point, and use `IS_HEAD_FIRST_OCC = 1` as the condition. Easier to read, easier to reuse across multiple items.

### 6.3.4 Question text macros

**(Khurshid 2023-03-06 *Question Text Macros*)** — bulk-manage question text via the Macros dialog.

When dozens of items share the same boilerplate ("Read aloud to respondent:" + "Interviewer note:"), define a macro once and reference it across items. Saves typing + ensures consistency.

In Designer: **CAPI menu → Macros → New Macro** → give it a name like `READ_ALOUD_PREFIX` → enter the macro body. Then in any item's question text, reference it as `{macro:READ_ALOUD_PREFIX}`.

**UHC application:** define macros for:

- `READ_ALOUD` — "Read aloud to respondent:" prefix.
- `INTERVIEWER_NOTE` — "Interviewer note:" prefix in italic blue.
- `DK_REFUSE_NOTE` — "If respondent says 'don't know' or refuses, mark accordingly without prompting."
- `OTHER_SPECIFY_NOTE` — "If 'Other' is selected, the next field will ask you to specify."

Bulk-applied across all 600+ F1 items, the macros save real authoring time and eliminate copy-paste drift.

---

## 6.4 Skip logic in .apc

The `<Instrument>.ent.apc` file is the application's logic. Its top-level structure mirrors the dictionary tree: PROC GLOBAL at the top, then PROC <FORM> blocks for form-level logic, then PROC <ITEM> blocks for per-item handlers.

### 6.4.1 The .apc file structure

```cspro
{ FacilityHeadSurvey.ent.apc — generated by CSPro Designer
  Hand-edited for skip logic, validations, capture wiring, language switches.
  External APCs included at the top so their functions resolve everywhere. }

#include "../shared/PSGC-Cascade.apc"
#include "../shared/Capture-Helpers.apc"
#include "../shared/Validators.apc"
#include "../shared/Resume-Handlers.apc"

PROC GLOBAL
  numeric currentYYYYMMDD;
  numeric currentYear;
  numeric currentMonth;

  function OnStop()
    savepartial();
    savesetting("last_field",
                concat(strip(getsymbol(curfield())), "_",
                       maketext(curocc())));
  end;

  function OnChangeLanguage()
    savesetting("save_last_language", getlanguage());
    { switch any per-language value sets here — see §6.13.4 }
  end;


PROC FACILITYHEADSURVEY_FF        { application-level entry }
preproc
  currentYYYYMMDD = systemdate("YYYYMMDD");
  currentYear  = int(currentYYYYMMDD / 10000);
  currentMonth = int(currentYYYYMMDD / 100) % 100;

  { language preference: load saved or default to English }
  if loadsetting("save_last_language") <> "" then
    setlanguage(loadsetting("save_last_language"));
  else
    setlanguage("en");
  endif;


PROC FIELD_CONTROL
preproc
  { case-control prefills — see §6.10 build_field_control }
  SURVEY_CODE     = "F1";
  DATE_STARTED    = systemdate("YYYYMMDD");
  TIME_STARTED    = systemtime("HHMMSS");
  AAPOR_DISPOSITION = 0;        { 000 — In Progress }


PROC CONSENT_GIVEN
postproc
  if CONSENT_GIVEN = 2 then       { No — respondent withdraws }
    AAPOR_DISPOSITION = 210;      { 210 — Refusal — respondent }
    ENUM_RESULT_FINAL_VISIT = 3;  { Refused }
    errmsg("Consent not given. Close the questionnaire and code as Refused.");
    endgroup;                     { terminate — do not enter Section A }
  endif;


PROC Q5_MONTHS_AT_FACILITY
postproc
  if (Q5_YEARS_AT_FACILITY * 12 + Q5_MONTHS_AT_FACILITY) < 6 then
    AAPOR_DISPOSITION = 410;      { 410 — Not eligible }
    ENUM_RESULT_FINAL_VISIT = 4;  { Incomplete }
    errmsg(1001);                 { externalised — see §6.7 }
    endgroup;
  endif;


PROC Q10_HAS_PRIMARY_PKG
postproc
  if Q10_HAS_PRIMARY_PKG = 2 then     { No }
    skip to Q12_PCB_LICENSING;
  endif;


PROC REGION                      { PSGC cascade — see §6.8 }
onfocus
  FillRegionValueSet(REGION);
```

A few rules of thumb that this skeleton encodes:

- **Includes at the top.** All shared `.apc` modules are pulled in once, so their `function` declarations resolve in every PROC below.
- **PROC GLOBAL first.** Globals (current date, helpers, OnStop, OnChangeLanguage) before any form-level PROC.
- **Application-level (`<DICT>_FF`) `preproc` runs once per case** at case-open. Use it for one-shot setup: current-date computation, language load, paradata config.
- **Form-level (`PROC <FORM>`) preproc** runs once per form-entry. Use it for prefills + form-scope conditions.
- **Item-level (`PROC <ITEM>`) handlers** carry the actual skip / validation logic.

### 6.4.2 Unconditional `skip to`

The simplest skip — always jump to a specific item:

```cspro
PROC Q160_END_OF_INPATIENT_BLOCK
postproc
  skip to Q200_NEXT_SECTION;     { unconditional }
```

Used for **block terminators** — at the end of a gated subsection, jump past it. The dependent fields between are reached only via conditional logic upstream.

### 6.4.3 Conditional `if` + `skip to`

The standard skip pattern. Read the spec's skip table row, write one PROC per row:

```cspro
{ F1 Section C - Q10 row of skip table:
  Q10 HAS_PRIMARY_PKG = No (2) -> Q12 (skip Q11) }
PROC Q10_HAS_PRIMARY_PKG
postproc
  if Q10_HAS_PRIMARY_PKG = 2 then
    skip to Q12_PCB_LICENSING;
  endif;
```

For multi-value triggers:

```cspro
{ Q14 PHU_CREATED in {No-planned, No-no-plans, No-other, IDK, NA} (5..9)
  -> Q16 (skip Q15) }
PROC Q14_PHU_CREATED
postproc
  if Q14_PHU_CREATED in 5:9 then       { range syntax: 5..9 }
    skip to Q16_HEALTH_PROMO_UNIT;
  endif;
```

For multi-target routing (different skip targets per branch):

```cspro
{ F1 Q80 INTEND_ACCRED — five-way routing per spec §2 }
PROC Q80_INTEND_ACCRED
postproc
  if Q80_INTEND_ACCRED in 1,2 then
    skip to Q84_END_NONACC;        { Yes-in-process / Yes-not-in-process }
  elseif Q80_INTEND_ACCRED = 3 then
    skip to Q82_DECIDED_NOT;       { No, decided not to }
  elseif Q80_INTEND_ACCRED = 4 then
    skip to Q83_TRIED_FAILED;      { No, tried and failed }
  elseif Q80_INTEND_ACCRED = 5 then
    skip to Q81_NOT_THOUGHT;       { No, haven't thought about it }
  elseif Q80_INTEND_ACCRED = 6 then
    skip to Q85_DK_REGROUP;        { I don't know }
  endif;
```

### 6.4.4 Block-level `preproc` (collective gating)

**(Khurshid 2022-09-21 *Working with Blocks*)** — when a whole subsection should skip on a single condition, gate at the block level rather than the field level.

Use case: F3 inpatient block (Section H, Q107–Q120) should be entered only if Q31 = "in-patient" (the patient's care setting was inpatient). Twelve fields all share the same gate — write it once at the block level instead of twelve times at the field level.

```cspro
PROC INPATIENT_BLOCK
preproc
  if Q31_CARE_SETTING <> 1 then    { 1 = in-patient }
    endgroup;                       { skip the entire block }
  endif;
```

Block-level gating also lets you set per-occurrence prefills:

```cspro
PROC ROSTER_BLOCK
preproc
  if curocc() > N_HHM then
    endgroup;                       { done — exit the roster block }
  endif;
  if curocc() = 1 then
    R_RELATIONSHIP = 1;              { occ 1 is always head }
    setProperty(R_RELATIONSHIP, "Protected", "Yes");
  else
    R_RELATIONSHIP = notappl;
    setProperty(R_RELATIONSHIP, "Protected", "No");
  endif;
```

Block-level postproc is the place for cross-field consistency checks scoped to the block:

```cspro
PROC DOB_BLOCK
postproc
  numeric dob_yyyymmdd;
  dob_yyyymmdd = DOB_YEAR * 10000 + DOB_MONTH * 100 + DOB_DAY;
  if not datevalid(dob_yyyymmdd) then
    errmsg(1010, dob_yyyymmdd);     { externalised }
    reenter;
  endif;
  if dob_yyyymmdd > sysdate("YYYYMMDD") then
    errmsg(1011);
    reenter;
  endif;
```

### 6.4.5 Production-grade paste-ready: F3 Section H gate

Per F3-Skip-Logic-and-Validations.md: "if Q31 = in-patient, ask Section H (Q107–Q120); else skip to Section I (Q121)."

Two complementary patterns — block preproc for the subsection skip, plus item-level skip on the gate item itself for safety.

```cspro
{ Item-level guard on the gate question — early skip if not inpatient }
PROC Q31_CARE_SETTING
postproc
  if Q31_CARE_SETTING <> 1 then       { 1 = in-patient }
    skip to Q121_SECTION_I_ENTRY;
  endif;


{ Block-level guard — defends against a corrupted Q31 or jump-back navigation }
PROC H_INPATIENT_CARE
preproc
  if Q31_CARE_SETTING <> 1 then
    endgroup;
  endif;


{ Item-level guards inside the block, for defence-in-depth }
PROC Q107_HOSPITAL_ADMITTED
preproc
  if Q31_CARE_SETTING <> 1 then
    skip to Q121_SECTION_I_ENTRY;
  endif;
```

The triple-guard (item-on-gate, block preproc, first-item preproc) survives forward navigation, jump-back navigation, and partial-save resume. Belt and braces — F3 inpatient is a 14-question subsection and the cost of accidentally entering it for the wrong respondent is much higher than the cost of three lines of guard logic.

---

## 6.5 Validation wiring (HARD / SOFT / GATE)

The three validation tiers are defined in [[03-Phase-3-5-Spec-and-Generators]] §3.4. Recap:

- **HARD** — block + force re-entry. Use `errmsg` + `reenter`.
- **SOFT** — warn but allow override. Use `accept(...)` and treat the operator's "Yes, proceed" as binding.
- **GATE** — display-conditional. Use `setProperty(item, "Visible", "Yes/No")` or `setProperty(item, "Protected", "Yes/No")` in the item's `onfocus`, or skip the item entirely via item-level `skip to next`.

Every rule in the spec's validation tables maps to one of these patterns.

### 6.5.1 HARD — block + reenter

```cspro
{ F1 §3.2: Q3_AGE must be 18..90 }
PROC Q3_AGE
postproc
  numeric AGE_LO_HARD = 18;
  numeric AGE_HI_HARD = 90;
  if Q3_AGE < AGE_LO_HARD or Q3_AGE > AGE_HI_HARD then
    errmsg(2010, Q3_AGE, AGE_LO_HARD, AGE_HI_HARD);
    reenter;
  endif;
```

Externalised messages — see §6.7. The constants `AGE_LO_HARD` / `AGE_HI_HARD` could move to PROC GLOBAL if reused across items; keep them local for one-off rules.

### 6.5.2 HARD — cross-field consistency

```cspro
{ F1 §3.2: tenure consistency. Q5 (years at this facility) must be
  <= Q6 (total years in any health-related role). }
PROC Q6_MONTHS_HEALTH
postproc
  numeric tenureMos;
  numeric healthMos;
  tenureMos = Q5_YEARS_AT_FACILITY * 12 + Q5_MONTHS_AT_FACILITY;
  healthMos = Q6_YEARS_HEALTH * 12 + Q6_MONTHS_HEALTH;

  if healthMos < tenureMos then
    errmsg(2020, healthMos, tenureMos);
    reenter;
  endif;

  if Q6_YEARS_HEALTH > (Q3_AGE - 18) then
    errmsg(2021, Q6_YEARS_HEALTH, Q3_AGE - 18);
    reenter;
  endif;
```

Place cross-field checks in the **postproc of the trigger item** — the item the operator just left that completes the cross-field condition. Here Q6_MONTHS_HEALTH triggers the check because Q5 + Q6_YEARS_HEALTH must already be set when entering Q6_MONTHS_HEALTH's postproc.

### 6.5.3 SOFT — warn but allow override

```cspro
{ F1 §3.5: Q57_CAPITATION_AMT > 1700 PHP — warn ("Above PhilHealth max — confirm"),
  let the enumerator confirm and proceed. }
PROC Q57_CAPITATION_AMT
postproc
  if Q57_CAPITATION_AMT > 5000 then
    errmsg(3010, Q57_CAPITATION_AMT);   { HARD ceiling at 5000 — block }
    reenter;
  endif;

  if Q57_CAPITATION_AMT > 1700 then
    if accept("Capitation amount %d PHP exceeds the PHP 1,700 PhilHealth max. Confirm?",
              "Yes, confirm", "No, re-enter", Q57_CAPITATION_AMT) <> 1 then
      reenter;
    endif;
  endif;
```

Two checks in one PROC — note the order. HARD ceiling first; SOFT warning only if HARD passes. The `accept(...)` returns 1 for the first option, 2 for the second; we treat anything non-1 as "re-enter."

### 6.5.4 SOFT — age plausibility

```cspro
{ F1 §3.2: Q3_AGE > 75 — warn ("Unusually old for an active facility head") }
PROC Q3_AGE
postproc
  if Q3_AGE < 18 or Q3_AGE > 90 then
    errmsg(2010, Q3_AGE, 18, 90);
    reenter;
  endif;
  if Q3_AGE > 75 then
    if accept("Facility head age %d is unusually high — confirm?",
              "Yes, confirm", "No, re-enter", Q3_AGE) <> 1 then
      reenter;
    endif;
  endif;
```

### 6.5.5 GATE — display-conditional via setProperty

```cspro
{ F1 §3.4: Q11 enabled iff Q10 = Yes (1). Implement as onfocus setProperty
  on Q11 — the field is visible but protected when the gate is closed. }
PROC Q11_PRIMARY_PKG_STATUS
onfocus
  if Q10_HAS_PRIMARY_PKG = 1 then
    setProperty(Q11_PRIMARY_PKG_STATUS, "Protected", "No");
  else
    Q11_PRIMARY_PKG_STATUS = notappl;
    setProperty(Q11_PRIMARY_PKG_STATUS, "Protected", "Yes");
  endif;
```

The `notappl` assignment ensures the value reads as "not applicable" when the gate is closed, so downstream analysis can distinguish "not asked because gate closed" from "asked and refused."

### 6.5.6 GATE — skip to next (alternative)

For pure display gating you can also `skip to next` from the item's preproc — the field is reached, the preproc decides not to ask, and CSEntry advances:

```cspro
PROC Q11_PRIMARY_PKG_STATUS
preproc
  if Q10_HAS_PRIMARY_PKG <> 1 then
    Q11_PRIMARY_PKG_STATUS = notappl;
    skip to next;
  endif;
```

**Choose one consistently per project.** The setProperty pattern shows the field on screen as protected; the `skip to next` pattern hides it entirely. UHC uses **setProperty for GATE within a form** (so the enumerator sees the field exists and can scroll back if needed) and **`skip to`** for whole-section gates that span multiple forms.

### 6.5.7 GATE — value-set narrowing (Q121 / facility-type-aware)

```cspro
{ F1 Q121 — hide hospital-only options for non-hospital facilities. }
PROC Q121_DOH_LIC_DIFFICULT
preproc
  if Q8_SERVICE_LEVEL = 1 then           { Primary Care Facility }
    setvalueset(Q121_DOH_LIC_DIFFICULT, vs_q121_pcf);
  else                                    { Hospital levels }
    setvalueset(Q121_DOH_LIC_DIFFICULT, vs_q121_hospital);
  endif;
postproc
  if Q121_O14_NONE = 1 then               { "None of the above" }
    skip to Q135_NBB_CURR;
  endif;
```

This is half display-gating, half dynamic value sets — covered in detail in §6.8.

---

## 6.6 Externalised validators (.apc files)

**(Khurshid 2022-05-26 *Work with External Logic File (.apc)*)** — when the same validation pattern shows up in multiple items or multiple instruments, externalise it.

### 6.6.1 Why use external .apc

Two reasons:

1. **DRY across items in one application.** Instead of repeating a 7-line alpha-only check in five name fields, write it once and call `check_string($)` from each.
2. **DRY across applications.** F1's PSGC-validator should be the same as F3's PSGC-validator. Maintaining one shared file beats keeping three drifting copies.

The UHC project already has two shared APCs: `PSGC-Cascade.apc` (4-level geographic cascade) and `Capture-Helpers.apc` (GPS + photo). Phase 6 build adds two more: `Validators.apc` (reusable validators) and `Resume-Handlers.apc` (OnStop + partial-case helpers).

### 6.6.2 Refactor inline validation into a function

Start in the per-application .apc with a function in PROC GLOBAL:

```cspro
PROC GLOBAL
function check_string(alpha s)
  numeric i;
  for i = 1 to length(s) do
    if not (substring(s, i, 1) in range("a","z") or
            substring(s, i, 1) in range("A","Z") or
            substring(s, i, 1) = " ") then
      errmsg(4001);
      reenter;
    endif;
  enddo;
end;
```

Then in each item's postproc:

```cspro
PROC Q1_NAME           postproc check_string($);
PROC RESP_NAME         postproc check_string($);
PROC FACILITY_NAME     postproc check_string($);
```

### 6.6.3 Externalize functions into a shared `.apc`

When the same function lives in F1, F3, F4 — extract.

1. Copy the function bodies to a new `Validators.apc` file under `deliverables/CSPro/shared/`.
2. Wrap them in a comment block with prerequisites + usage.
3. In each instrument's `<Instrument>.ent.apc`, add `#include "../shared/Validators.apc"` at the top.
4. Remove the duplicated function definitions from the per-app PROC GLOBAL.

`shared/Validators.apc` skeleton:

```apc
{ Validators.apc — reusable CSPro validation functions for UHC instruments.

  Include this module in each instrument's .ent.apc:
      #include "../shared/Validators.apc"

  Provides:
  - check_alpha_only(s)             — letters + spaces only (HARD).
  - check_ph_mobile(s)              — Philippine mobile number (11 digits, starts with 09).
  - check_email_basic(s)            — basic email shape (SOFT — for warn-and-allow).
  - check_psgc_format(code, level)  — 10-digit PSGC code at the right administrative level.
  - check_age_tenure_consistency(age, years_at_facility, years_in_role)
                                    — multi-arg check used by F1 §3.2, F3 §3.x.

  Errors are emitted via numbered errmsg IDs from the shared message file
  shared/Validators.mgf so translations live in one place per language.
}

PROC GLOBAL


function check_alpha_only(alpha s)
  numeric i;
  for i = 1 to length(s) do
    if not (substring(s, i, 1) in range("a","z") or
            substring(s, i, 1) in range("A","Z") or
            substring(s, i, 1) = " " or
            substring(s, i, 1) = "-" or
            substring(s, i, 1) = "'") then
      errmsg(4001);
      reenter;
    endif;
  enddo;
end;


function check_ph_mobile(alpha s)
  { Philippine mobile: 11 digits, starts with "09" }
  numeric i;
  if length(s) <> 11 then
    errmsg(4010, length(s));
    reenter;
  endif;
  if substring(s, 1, 2) <> "09" then
    errmsg(4011);
    reenter;
  endif;
  for i = 1 to 11 do
    if not (substring(s, i, 1) in range("0","9")) then
      errmsg(4012, i);
      reenter;
    endif;
  enddo;
end;


function check_email_basic(alpha s)
  { SOFT validator — does not call reenter. Caller decides on the SOFT path. }
  numeric pos_at, pos_dot;
  pos_at  = pos("@", s);
  pos_dot = pos(".", s);
  if pos_at = 0 or pos_dot = 0 or pos_dot < pos_at then
    if accept(tr("Email address looks malformed — confirm?"),
              tr("Yes, confirm"),
              tr("No, re-enter")) <> 1 then
      reenter;
    endif;
  endif;
end;


function check_psgc_format(numeric code, alpha level)
  { 10-digit PSGC code, padded with zeros where needed.
    'level' is one of "region", "province", "city", "barangay" — drives
    the trailing-zero / non-zero pattern check. }
  numeric digits;
  digits = length(maketext("%d", code));
  if digits <> 10 then
    errmsg(4020, level, digits);
    reenter;
  endif;
  { region-level codes end in 8 zeros, province in 5, city in 2, barangay 0 }
  numeric tail_zeros;
  if level = "region" then     tail_zeros = 8;
  elseif level = "province" then tail_zeros = 5;
  elseif level = "city" then     tail_zeros = 2;
  else                            tail_zeros = 0;     { barangay — full code }
  endif;
  numeric divisor;
  divisor = 10 ** tail_zeros;
  if (code % divisor) <> 0 then
    errmsg(4021, level);
    reenter;
  endif;
end;


function check_age_tenure_consistency(numeric age,
                                       numeric years_at_facility,
                                       numeric years_in_role)
  { Used by F1 §3.2 / F3 §3.x. Caller passes Q3_AGE, Q5_YEARS, Q6_YEARS;
    function emits the right errmsg via reenter. }
  if years_at_facility > (age - 18) then
    errmsg(4030, years_at_facility, age - 18);
    reenter;
  endif;
  if years_in_role < years_at_facility then
    errmsg(4031, years_in_role, years_at_facility);
    reenter;
  endif;
  if years_in_role > (age - 18) then
    errmsg(4032, years_in_role, age - 18);
    reenter;
  endif;
end;
```

In the per-instrument `.apc`:

```cspro
#include "../shared/Validators.apc"

PROC Q1_NAME           postproc check_alpha_only($);
PROC RESP_NAME         postproc check_alpha_only($);
PROC RESP_MOBILE       postproc check_ph_mobile($);
PROC RESP_EMAIL        postproc check_email_basic($);

PROC Q6_YEARS_HEALTH
postproc
  check_age_tenure_consistency(Q3_AGE, Q5_YEARS_AT_FACILITY, Q6_YEARS_HEALTH);
```

Five lines of per-instrument plumbing replace dozens of inline checks per file, and any tweak (e.g. allowing apostrophes in names per a Filipino name pattern) is a one-line change in `Validators.apc` that benefits F1, F3, F4 simultaneously.

### 6.6.4 Design rule: shared APC = pure functions; per-instrument .apc = wiring

Keep this discipline:

- `shared/<Helper>.apc` — only declares helpers in PROC GLOBAL. Never references a per-instrument item by name.
- `<Instrument>.ent.apc` — does the wiring: `#include`s shared APCs, writes per-form / per-item PROC blocks, calls helper functions with the instrument's items.

The shared APCs are a **library**; each instrument's .apc is the **application**.

---

## 6.7 Externalised error messages

**(Khurshid 2022-06-22 *External Error Messages*)** — error strings live in the message file (`.mgf`), referenced by ID from PROC code, with format specifiers for runtime fills.

Recap from [[03-Phase-3-5-Spec-and-Generators]] §3.6: numbered IDs in the Messages tab, `%s` / `%d` / `%f` format specifiers, `errmsg(1001, AGE)` from PROC.

### 6.7.1 Why externalise

Three reasons:

1. **Translation surface.** All user-facing strings are in one file, the `.mgf`. The translator gets one document to translate, not 600+ scattered `errmsg` calls.
2. **Consistency.** When the same rule fires from multiple items (e.g. several "Other (specify) is required" checks), one ID + one message means one consistent UX.
3. **Audit.** Counting message-ID calls in the .apc tells you how many places fire each rule — useful for QA coverage.

### 6.7.2 Message-file structure

```text
{ Validators.mgf — reusable error messages for UHC validators.
  Wired by errmsg(<ID>, ...) calls from Validators.apc + per-instrument .apc.
  Multi-language sections per Khurshid 2022-09-26 — one
  language= header per language, IDs reused across sections. }

language=en

1001 Respondent must have at least 6 months in current position. End interview and code as Refused/Incomplete.
1010 Date of birth %d is not a valid calendar date.
1011 Date of birth cannot be in the future.

2010 Age %d is outside the allowed range %d to %d.
2020 Years in any health-related role (%d months) cannot be less than years at this facility (%d months).
2021 Years in health (%d) exceeds working-age years available (%d).

3010 Capitation amount %d PHP is implausibly high — re-enter.
3020 Registered patients (%d) cannot exceed eligible patients (%d).

4001 Only letters, spaces, hyphens, and apostrophes are allowed in this field.
4010 Mobile number must be 11 digits — got %d.
4011 Mobile number must start with "09".
4012 Character at position %d is not a digit.
4020 PSGC code at %s level must be 10 digits — got %d.
4021 PSGC code does not match expected pattern for %s level.
4030 Years at facility (%d) exceeds working-age years available (%d).
4031 Years in role (%d) cannot be less than years at this facility (%d).
4032 Years in role (%d) exceeds working-age years available (%d).

language=fil

1001 Ang respondent ay dapat may hindi bababa sa 6 na buwan sa kasalukuyang posisyon. Tapusin ang panayam at i-code bilang Refused/Incomplete.
1010 Ang kapanganakan na %d ay hindi balidong petsa sa kalendaryo.
1011 Ang kapanganakan ay hindi maaaring nasa hinaharap.

2010 Ang edad na %d ay hindi nasa pinapayagang saklaw na %d hanggang %d.
2020 Ang mga taon sa anumang papel na may kaugnayan sa kalusugan (%d na buwan) ay hindi maaaring mas mababa sa mga taon sa pasilidad na ito (%d na buwan).
{ ... and so on for each ID ... }
```

**Gotcha (Khurshid 2022-09-26):** "Please do not put space before and after the `=` sign — it will give you error." The `language=en` header is exact; `language = en` breaks parsing.

### 6.7.3 Calling externalised messages from PROC

```cspro
PROC Q3_AGE
postproc
  if Q3_AGE < 18 or Q3_AGE > 90 then
    errmsg(2010, Q3_AGE, 18, 90);    { %d %d %d substituted in order }
    reenter;
  endif;
```

Format specifiers:

| Specifier | Use |
|---|---|
| `%s` | String (alpha item, literal). |
| `%d` | Integer. |
| `%f` | Float. |
| `%%` | Literal percent sign. |

Order of substitution = order of arguments. Multi-arg messages should keep the order stable across languages — translators pick up the placeholders verbatim and re-arrange the surrounding sentence.

### 6.7.4 ID-numbering convention

The UHC project uses 4-digit IDs grouped by tier and section:

| Range | Use |
|---|---|
| 1000–1099 | Eligibility / consent (HARD terminators) |
| 1100–1199 | Date / time validity |
| 2000–2999 | Section-specific HARD validators (one block per section) |
| 3000–3999 | Section-specific SOFT validators |
| 4000–4999 | Reusable validators in `Validators.apc` |
| 5000–5999 | Capture (GPS / photo / paradata) errors |
| 9000–9999 | Reserved for future use |

Reserve ranges per section so adding a new HARD validator to F1 Section D doesn't collide with F3 Section H.

---

## 6.8 Dynamic value sets

When the option list for an item depends on a prior answer or runtime context, use **dynamic value sets**: `setvalueset(item, vs)` swaps the active value set on the fly.

### 6.8.1 `setvalueset()` for context-dependent option lists

**(Khurshid 2022-04-09 *CSPro: User and Configuration Settings*)** — `setvalueset(item, vs)` switches the live value set, so the dropdown / radio renders the new options without leaving the field.

```cspro
{ F1 Q121 facility-type-aware option list }
PROC Q121_DOH_LIC_DIFFICULT
preproc
  if Q8_SERVICE_LEVEL = 1 then               { Primary Care Facility }
    setvalueset(Q121_DOH_LIC_DIFFICULT, vs_q121_pcf);
  elseif Q8_SERVICE_LEVEL in 2:4 then        { Levels 1-3 Hospital }
    setvalueset(Q121_DOH_LIC_DIFFICULT, vs_q121_hospital);
  else
    setvalueset(Q121_DOH_LIC_DIFFICULT, vs_q121_default);
  endif;
```

The value sets `vs_q121_pcf`, `vs_q121_hospital`, `vs_q121_default` are declared in the dictionary alongside the item's primary value set; the generator emits all three and the Designer doesn't need to touch them.

### 6.8.2 Build a dynamic value set from runtime roster data

**(Khurshid 2022-07-25 *Tutorial 2: Dynamic Value Set*)** — for selections drawn from a runtime-built list (e.g. F4 "which household member do you want to interview?").

```cspro
{ F4 — Q40 KISH_RESPONDENT — pick from eligible household members.
  Eligible = age >= 18, not the respondent themselves. }
PROC Q40_KISH_RESPONDENT
preproc
  ValueSet vs;
  numeric i;
  for i = 1 to count(R_PERSON) do
    if R_AGE(i) >= 18 then
      vs.add(R_NAME(i), i);     { label = name, value = roster occurrence }
    endif;
  enddo;
  setvalueset(Q40_KISH_RESPONDENT, vs);
```

The `ValueSet` object is built at runtime from roster items, then bound via `setvalueset`. The dropdown shows person names; the stored value is the occurrence number used to look up other roster fields downstream.

### 6.8.3 Linked value sets

**(Khurshid 2023-09-12 *Linked Value Sets*)** — when a parent value set drives a child value set deterministically. The PSGC cascade is the canonical example.

### 6.8.4 valueset.sort + valueset.remove

**(Khurshid 2023-09-18 *ValueSet Sort and Remove*)** — manipulate value sets after construction.

Use case: F4 question "which household member did NOT receive vaccination this year?" — drop already-selected occupants from the option list to enforce one-at-a-time selection across multiple visits.

```cspro
PROC Q88_UNVAX_PERSON
preproc
  ValueSet vs;
  numeric i;
  for i = 1 to count(R_PERSON) do
    vs.add(R_NAME(i), i);
  enddo;

  { drop already-selected occupants stored in prior occurrences }
  numeric prior_occ;
  for prior_occ = 1 to curocc() - 1 do
    vs.remove(Q88_UNVAX_PERSON(prior_occ));
  enddo;

  vs.sort();      { alphabetical by label }
  setvalueset(Q88_UNVAX_PERSON, vs);
```

### 6.8.5 PSGC cascade as the canonical UHC example

The Philippine Standard Geographic Code (PSGC) cascade is the single most important dynamic-value-set pattern in the UHC project. Every instrument (F1, F3, F4) uses it. The pattern is codified in `shared/PSGC-Cascade.apc` and works as follows:

**Prerequisites** (per the .apc file's header):

- The four PSGC external dictionaries are inserted in the application: `psgc_region.dcf`, `psgc_province.dcf`, `psgc_city.dcf`, `psgc_barangay.dcf`. Each has its own `.dat` file with the actual PSGC roster.
- The main dictionary exposes four numeric length-10 items: `REGION`, `PROVINCE_HUC`, `CITY_MUNICIPALITY`, `BARANGAY`.
- The PSGC dictionaries each have a single record with key items the lookup uses (`R_PARENT_CODE`, `P_PARENT_REGION`, `C_PARENT_PROVINCE`, `B_PARENT_CITY`).

**Cascade API** (the four functions `PSGC-Cascade.apc` exposes):

```apc
function FillRegionValueSet(numeric targetItem)
function FillProvinceValueSet(numeric targetItem, numeric parentRegion)
function FillCityValueSet(numeric targetItem, numeric parentProvince)
function FillBarangayValueSet(numeric targetItem, numeric parentCity)
```

Each function:
1. Sets the parent-code key on the relevant PSGC dictionary's lookup record.
2. `loadcase()`s the children for that parent.
3. Loops the children, building a runtime `ValueSet`.
4. Binds the ValueSet to the target item via `setvalueset()`.

**Wiring in the per-instrument .apc** — onfocus handlers per field, so reverse navigation re-populates the value set (Logic Tip #4 from the CSPro 8.0 Users Guide p.188):

```cspro
PROC REGION
onfocus
  FillRegionValueSet(REGION);

PROC PROVINCE_HUC
onfocus
  FillProvinceValueSet(PROVINCE_HUC, REGION);

PROC CITY_MUNICIPALITY
onfocus
  FillCityValueSet(CITY_MUNICIPALITY, PROVINCE_HUC);

PROC BARANGAY
onfocus
  FillBarangayValueSet(BARANGAY, CITY_MUNICIPALITY);
```

That's it — four PROC blocks, four function calls. The PSGC dictionary maintains itself; whenever PSA publishes a new quarterly PSGC, regenerate the four `.dat` files via `shared/build_psgc_lookups.py` and the apps continue to work without recompilation.

**For F3** which has both facility geo (`REGION` etc.) and patient-home geo (`P_REGION` etc.), the .apc adds a parallel set of functions prefixed `P_` (`FillPatientRegionValueSet`, etc.) — same pattern, different items.

### 6.8.6 Production-grade paste-ready: PSGC cascade for F1

Prerequisites in `FacilityHeadSurvey.dcf`:

- External dicts inserted: `psgc_region.dcf`, `psgc_province.dcf`, `psgc_city.dcf`, `psgc_barangay.dcf`.
- Main dict items: `REGION`, `PROVINCE_HUC`, `CITY_MUNICIPALITY`, `BARANGAY` (all numeric length 10, on `FIELD_CONTROL`).

Wiring in `FacilityHeadSurvey.ent.apc`:

```cspro
#include "../shared/PSGC-Cascade.apc"

PROC FIELD_CONTROL_FORM
onfocus
  { force re-population on form re-entry — defends against stale value sets }
  FillRegionValueSet(REGION);
  if REGION <> 0 then
    FillProvinceValueSet(PROVINCE_HUC, REGION);
    if PROVINCE_HUC <> 0 then
      FillCityValueSet(CITY_MUNICIPALITY, PROVINCE_HUC);
      if CITY_MUNICIPALITY <> 0 then
        FillBarangayValueSet(BARANGAY, CITY_MUNICIPALITY);
      endif;
    endif;
  endif;


PROC REGION
onfocus
  FillRegionValueSet(REGION);


PROC PROVINCE_HUC
onfocus
  FillProvinceValueSet(PROVINCE_HUC, REGION);


PROC CITY_MUNICIPALITY
onfocus
  FillCityValueSet(CITY_MUNICIPALITY, PROVINCE_HUC);


PROC BARANGAY
onfocus
  FillBarangayValueSet(BARANGAY, CITY_MUNICIPALITY);
```

Designer-side: each PSGC field is a **Drop Down** capture type, sized for ~30 visible items (some provinces have 1000+ barangays — drop-down is fine because users scroll/type-ahead).

---

## 6.9 Capture types per item

The capture type is the UI control CSEntry uses to render the field on the tablet. Choosing the right one improves entry speed and reduces enumerator error.

**(Khurshid 2022-09-21 *Working with Blocks*** — capture-type guidance throughout the form-design tutorials**)** + the workflow template's [[../../../2_Areas/IT-Standards/templates/CAPI-Development-Workflow]] Phase 6 capture-type table:

| Source type | Default capture type | Notes |
|---|---|---|
| Yes/No | Radio group, horizontal | Use shared value set `VS_YES_NO`. ≤ 4 options on one row. |
| 3–7 option single-select | Radio group, vertical | One option per row — touch-target size. |
| 8+ option single-select | Drop Down | Sort by frequency if known, else source order. |
| Multi-select (select-all) | Multi-select grid | Mutual-exclusion rules in postproc. |
| "Other (specify)" parent | Same as parent | Follow-up text on same form, skip-gated. |
| Short text (≤ 80 chars) | Text Box (single-line) | — |
| Long text (> 80 chars) | Text Box (3-line) | Multi-line. |
| Integer count | Number Pad | Range check in postproc. |
| Decimal / currency | Number Pad with decimal | PHP, 2 decimal places. |
| Year | Number Pad, 4 digits | Range check survey-min .. current. |
| Month | Drop Down (01–12) | Easier than Number Pad for 2-digit. |
| Date | Date Picker | — |
| Time | Time Picker | 24-hour. |
| PSGC | Drop Down (cascade) | See §6.8.5. |

### 6.9.1 Setting capture type in Designer

1. Select the control on the form.
2. Right-click → Properties → **Use** tab → **Capture Type** dropdown.
3. Pick from: Radio Buttons (Horizontal), Radio Buttons (Vertical), Drop Down, Combo Box, Number Pad, Text Box, Date Picker, Time Picker, Multi-select Grid.

### 6.9.2 Enforcing capture type in the dcf

The dcf doesn't directly carry capture-type info — but the `cspro_helpers.py` builders set length, decimal places, value-set bindings, and zero-fill so that Designer's defaults pick a sensible capture type. For example:

```python
yes_no("Q10_HAS_PRIMARY_PKG", "Has primary care package")
# emits a length-1 numeric with VS_YES_NO bound
# Designer defaults to Radio Horizontal because length=1 + 2-option VS

select_one("Q121_DOH_LIC_DIFFICULT", "Why DOH licensing is difficult",
           options=Q121_OPTIONS, length=2)
# length-2 + 14 options -> Designer defaults to Drop Down

alpha("RESP_NAME", "Respondent name", length=50)
# length-50 alpha -> Designer defaults to Text Box single-line

alpha("Q103_NO_BUCAS_REASON", "Reason no BUCAS", length=200)
# length-200 alpha -> Designer defaults to Text Box multi-line
```

Designer overrides — set explicitly in the .fmf — survive regenerations because regen targets the dcf, not the fmf.

### 6.9.3 Tablet UX patterns

- **Number Pad on tablets opens an on-screen keypad** with large digits and Enter — fast for numeric entry. Use it for every numeric field, not just calendar pickers.
- **Date Picker opens a native Android date dialog** with day/month/year wheels — much faster than typing YYYYMMDD into a Number Pad.
- **Drop Down auto-shows on focus** in CAPI mode — enumerator taps the field, list opens, taps the option, list closes. No keyboard.
- **Multi-select Grid renders as a checkbox column** on the tablet. Each tap toggles a row. Add a "None of the above" row at the top with mutual-exclusion enforcement in postproc.
- **Radio (horizontal) is the fastest 2-option control** — single tap, no keyboard, no dropdown roundtrip. Use for every Yes/No.

---

## 6.10 FIELD_CONTROL block (informed-consent + eligibility + AAPOR + GPS)

`FIELD_CONTROL` is the always-first record on every UHC instrument, built by `cspro_helpers.build_field_control(survey_code, ...)`. It bundles five concerns:

1. **Case-control metadata** — survey code, interviewer ID, date/time started, AAPOR disposition.
2. **Visit metadata** — date first / final visit, total visits, enumerator names, validator/editor names.
3. **Informed consent** — `CONSENT_GIVEN` (Y/N), with terminator logic.
4. **Enumerator result codes** — `ENUM_RESULT_FIRST_VISIT`, `ENUM_RESULT_FINAL_VISIT`.
5. **Capture triggers** (paired record `REC_FACILITY_CAPTURE` / `REC_PATIENT_HOME_CAPTURE`) — GPS + verification photo, written by helpers but flagged from FIELD_CONTROL forms.

### 6.10.1 The generated FIELD_CONTROL record structure (F1 example)

From `build_field_control("F1")` in `cspro_helpers.py`:

| Item | Type | Length | Purpose |
|---|---|---|---|
| `SURVEY_CODE` | alpha | 2 | "F1" / "F3" / "F4" |
| `INTERVIEWER_ID` | numeric | 4 | Zero-fill; manually entered |
| `DATE_STARTED` | numeric | 8 | YYYYMMDD; auto-prefilled in preproc |
| `TIME_STARTED` | numeric | 6 | HHMMSS; auto-prefilled in preproc |
| `AAPOR_DISPOSITION` | numeric | 3 | Initial 000; rewritten at consent / eligibility / closing |
| `SURVEY_TEAM_LEADER_S_NAME` | alpha | 50 | — |
| `ENUMERATOR_S_NAME` | alpha | 50 | — |
| `FIELD_VALIDATED_BY` | alpha | 50 | — |
| `FIELD_EDITED_BY` | alpha | 50 | — |
| `DATE_FIRST_VISITED` | numeric | 8 | — |
| `DATE_FINAL_VISIT` | numeric | 8 | — |
| `TOTAL_NUMBER_OF_VISITS` | numeric | 1 | — |
| `ENUM_RESULT_FIRST_VISIT` | numeric | 1 | 1=Completed / 2=Postponed / 3=Refused / 4=Incomplete |
| `ENUM_RESULT_FINAL_VISIT` | numeric | 1 | Same value set |
| `CONSENT_GIVEN` | numeric | 1 | 1=Yes / 2=No |
| (PSGC fields) | numeric | 10 ea | `REGION`, `PROVINCE_HUC`, `CITY_MUNICIPALITY`, `BARANGAY` |

For F1 the PSGC sits inside FIELD_CONTROL (per-facility geo); for F3/F4 there's also a parallel patient-home / household geo block.

### 6.10.2 AAPOR-aligned disposition codes

Per `cspro_helpers.AAPOR_DISPOSITION_OPTIONS`:

| Code | Label | When set |
|---|---|---|
| `000` | In Progress (initial) | FIELD_CONTROL.preproc — case start |
| `110` | Complete interview | CLOSING form, after final submit |
| `120` | Partial interview / break-off | Tenure-eligibility termination, OnStop with non-completed flag |
| `210` | Refusal — respondent | CONSENT_GIVEN postproc when Consent = No |
| `211` | Refusal — gatekeeper / household | Pre-consent gatekeeper refusal recorded by enumerator |
| `220` | Non-contact — respondent unavailable | Multiple visits without successful contact |
| `230` | Other eligible non-interview | — |
| `310` | Unknown eligibility — facility/household | — |
| `320` | Unknown eligibility — respondent | — |
| `410` | Not eligible — out of sample / ineligible | Tenure < 6 months termination |
| `450` | Not eligible — other | Catch-all |

The `000` sentinel is ASPSI-internal; AAPOR's published table starts at `110`. Useful because the dispositoin field is always populated even before any decision.

### 6.10.3 FIELD_CONTROL.preproc — case-start setup

```cspro
PROC FIELD_CONTROL
preproc
  SURVEY_CODE       = "F1";
  if INTERVIEWER_ID = notappl then
    if loadsetting("interviewer_id") <> "" then
      INTERVIEWER_ID = tonumber(loadsetting("interviewer_id"));
    endif;
  endif;
  DATE_STARTED      = systemdate("YYYYMMDD");
  TIME_STARTED      = systemtime("HHMMSS");
  AAPOR_DISPOSITION = 0;     { 000 — In Progress }
```

The interviewer-ID load via `loadsetting` is handed off from the login app per [[#6.17 PFF and entry application packaging]].

### 6.10.4 Consent flow with HTML-dialog confirmation

**(Khurshid 2022-04-24 *Using HTML Dialogs for displaying logic function*)** — for high-stakes confirmations, use a custom HTML dialog instead of the default `accept()` text prompt.

The pattern works like this:

1. Author a small HTML file (e.g. `consent.html`) under `<app>/htmldialogs/` describing the consent statement, with two buttons (`Yes — proceed` / `No — refuse`).
2. In the FIELD_CONTROL.preproc or CONSENT_GIVEN.onfocus, `accept(...)` reads the HTML and shows the styled dialog instead of the plain text prompt.
3. The button mapping (1 = Yes, 2 = No) is the same as `accept()`.

```cspro
PROC CONSENT_GIVEN
onfocus
  numeric choice;
  choice = accept(htmlfile := "htmldialogs/consent_F1.html");
  if choice = 2 then
    CONSENT_GIVEN = 2;
    AAPOR_DISPOSITION = 210;
    ENUM_RESULT_FIRST_VISIT = 3;
    ENUM_RESULT_FINAL_VISIT = 3;
    errmsg(1001);            { externalised — "Consent not given. Code as Refused." }
    endgroup;                { skip the rest of the case }
  else
    CONSENT_GIVEN = 1;
  endif;
```

`htmldialogs/consent_F1.html` skeleton:

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body { font-family: Arial, sans-serif; padding: 20px; max-width: 600px; }
    h1 { color: #003366; font-size: 18pt; }
    p { font-size: 12pt; line-height: 1.5; }
    .buttons { margin-top: 20px; text-align: center; }
    .buttons button { padding: 10px 20px; margin: 5px; font-size: 12pt; }
    .yes { background: #2a7a2a; color: white; }
    .no  { background: #aa2222; color: white; }
  </style>
</head>
<body>
  <h1>Informed Consent — UHC Year 2 Facility Head Survey</h1>
  <p>By proceeding, the facility head respondent confirms they have:</p>
  <ul>
    <li>Read or been read the Annex H1 Informed Consent Form;</li>
    <li>Had the opportunity to ask questions and have them answered;</li>
    <li>Voluntarily agreed to participate in this research.</li>
  </ul>
  <p>Confirm consent to proceed with the interview?</p>
  <div class="buttons">
    <button class="yes" onclick="accept(1)">Yes — proceed</button>
    <button class="no"  onclick="accept(2)">No — refuse</button>
  </div>
</body>
</html>
```

Per Annex H, UHC has **four ICFs** — H1 (F1 Facility Head), H2 (F3 Patient), H3 (F4 Household), and one for HCW (web-survey, not CSPro). Each gets its own `consent_<F>.html` with the right text. The pattern is identical; the file changes per instrument.

### 6.10.5 Eligibility screen

Tenure < 6 months is the standard F1 eligibility filter. Already shown above (§6.5.2). Pattern repeats for each instrument's eligibility check:

- **F1** — facility head's tenure in current position ≥ 6 months.
- **F3** — patient confirmed they received care at the sampled facility within the recall window.
- **F4** — household confirmed at least one member meets the eligibility criteria (e.g. Yakap-eligible age band).

Failure → AAPOR `410` (not eligible) + `endgroup` to skip the substantive sections.

### 6.10.6 GPS auto-capture for paradata

Two GPS captures per case:

1. **Foreground capture** — on a capture form, fired by the enumerator tapping a button. Writes to `REC_FACILITY_CAPTURE` (F1) / `REC_PATIENT_HOME_CAPTURE` (F3) / household equivalent (F4). This is the verifiable "interview took place here" record.
2. **Background paradata GPS** — silent, every ~minute throughout the interview, written to the Paradata file (`*.par`). This is the auditable "where the enumerator was during the interview" stream.

Enable paradata GPS via Application Properties — see §6.11.

### 6.10.7 Interviewer / supervisor IDs

`INTERVIEWER_ID` is loaded from the login-app handoff. For supervisor cross-fields (e.g. F1's `FIELD_VALIDATED_BY`), use plaintext alpha so any reviewer name can be entered post-hoc by the supervisor.

```cspro
PROC INTERVIEWER_ID
preproc
  if INTERVIEWER_ID = notappl then
    if loadsetting("interviewer_id") <> "" then
      INTERVIEWER_ID = tonumber(loadsetting("interviewer_id"));
    endif;
  endif;
postproc
  if INTERVIEWER_ID = notappl or INTERVIEWER_ID = 0 then
    errmsg(5001);   { "Interviewer ID required." }
    reenter;
  endif;
```

---

## 6.11 GPS + photo capture

Already covered structurally in [[03-Phase-3-5-Spec-and-Generators]] §2.7 (the dcf records) and [[../CSPro/Form-Layout-Principles]] §6.2 (the trigger placement). Phase 6 wiring uses the pre-built helpers in `shared/Capture-Helpers.apc`.

### 6.11.1 Foreground capture wiring

```cspro
#include "../shared/Capture-Helpers.apc"

{ Facility GPS — on a dedicated capture form. }
PROC FACILITY_CAPTURE_GPS
onfocus
  if ReadGPSReading(120, 20) then       { 120s timeout, 20m target accuracy }
    FACILITY_GPS_LATITUDE   = maketext("%f", gps(latitude));
    FACILITY_GPS_LONGITUDE  = maketext("%f", gps(longitude));
    FACILITY_GPS_ALTITUDE   = maketext("%f", gps(altitude));
    FACILITY_GPS_ACCURACY   = gps(accuracy);
    FACILITY_GPS_SATELLITES = gps(satellites);
    FACILITY_GPS_READTIME   = gps(readtime);
  endif;
  FACILITY_CAPTURE_GPS = notappl;       { reset trigger so button re-arms }


{ Verification photo — on the same or adjacent capture form. }
PROC CAPTURE_VERIFICATION_PHOTO
onfocus
  string fn;
  fn = "case-" + maketext("%06d", QUESTIONNAIRE_NO) + "-verification.jpg";
  if TakeVerificationPhoto(fn) then
    VERIFICATION_PHOTO_FILENAME = fn;
  endif;
  CAPTURE_VERIFICATION_PHOTO = notappl;


{ Post-capture sanity checks on the lat/lon items, not the trigger. }
PROC FACILITY_GPS_LATITUDE
postproc
  numeric lat;
  lat = tonumber(FACILITY_GPS_LATITUDE);
  if lat <> notappl and (lat < 4.5 or lat > 21.5) then
    errmsg(5010, lat);
    move to FACILITY_CAPTURE_GPS;
  endif;


PROC FACILITY_GPS_LONGITUDE
postproc
  numeric lon;
  lon = tonumber(FACILITY_GPS_LONGITUDE);
  if lon <> notappl and (lon < 116.5 or lon > 127.0) then
    errmsg(5011, lon);
    move to FACILITY_CAPTURE_GPS;
  endif;


PROC VERIFICATION_PHOTO_FILENAME
postproc
  if ENUM_RESULT_FINAL_VISIT = 1 and length(strip(VERIFICATION_PHOTO_FILENAME)) = 0 then
    errmsg(5020);    { "Verification photo required when case marked Completed." }
    move to CAPTURE_VERIFICATION_PHOTO;
  endif;
```

Philippine bounding box: lat 4.5–21.5, lon 116.5–127.0. Out-of-box coords → re-capture (the operator has likely tapped the trigger before the GPS got a fix).

### 6.11.2 Background paradata GPS

**(Khurshid 2023-09-09 *Tutorial on Obtain GPS in the Background*)** — silent, ~once per minute, written to the Paradata file (`*.par`).

Configure:

1. Designer → **Options → Application Properties → Paradata** section.
2. **Event collection options** → enable Paradata.
3. **Data source** → check **GPS** under "Paradata events to collect."
4. **GPS coordinates** → enter `1` in the text box. (Khurshid: "When the GPS location value is set to 1, CSEntry will try to save the interview GPS coordinates approximately once every minute.")
5. OK → save (Ctrl+S) → publish + deploy.

Verify after first test run: a `<Instrument>.par` file should appear alongside `<Instrument>.dat`. Open it in **Paradata Viewer** (CSPro tools). The Case Key Info table + GPS Event table can be joined on case-info sequence.

### 6.11.3 Cross-link paradata GPS with case data via VLOOKUP

**(Khurshid 2023-09-09 @ 04:05)** — post-fieldwork analysis pattern:

1. Paradata Viewer → Case Key Info table → Save Result to Excel → keep Case Info (sequence) + Key (case ID).
2. Paradata Viewer → GPS Event table → Save Result to Excel → keep Case Info, Latitude, Longitude.
3. Excel: VLOOKUP from GPS Event's `Case Info` to Case Key Info's `Key` → each GPS row carries the case ID.
4. VLOOKUP from case ID into the main data file's lat/lon → side-by-side comparison.
5. Compute distance between paradata GPS and dictionary GPS — large gaps flag suspicious cases.

For UHC's QC pipeline, this becomes a daily / weekly analysis — Carl runs it in Phase 10 via a scripted notebook and posts flagged cases to the Slack channel.

### 6.11.4 Map Object — display GPS coordinates on a map

**(Khurshid 2022-07-06 *Map Object*)** — supervisor visualisation pattern: open a map, drop pins for each captured case, set a base map.

```cspro
PROC SHOW_FIELD_MAP
onfocus
  Map m;
  m.addListing(FacilityListing,
               "FACILITY_NAME",
               "FACILITY_GPS_LATITUDE",
               "FACILITY_GPS_LONGITUDE");
  m.setBaseMap("OpenStreetMap");
  m.show();
```

Used in a supervisor menu app (see §6.17), not in the data-entry app. Lets the supervisor visually confirm the day's case spread without leaving the tablet.

### 6.11.5 Where the helpers live

| Helper | File | Purpose |
|---|---|---|
| `ReadGPSReading(maxTimeSec, desiredAccuracyM)` | `shared/Capture-Helpers.apc` | Open GPS, read, close, return 1/0. |
| `TakeVerificationPhoto(filename)` | `shared/Capture-Helpers.apc` | Launch camera, resample, save JPG. |
| `_gps_fields(prefix)` | `cspro_helpers.py` | dcf builder for GPS items. |
| `_photo_block(prefix)` | `cspro_helpers.py` | dcf builder for photo items. |
| `build_capture_record(...)` | per-instrument `generate_dcf.py` | Builds `REC_FACILITY_CAPTURE` etc. |

The helpers are unit-tested via the project's dcf-export-to-Excel round-trip (`export_dcf_to_xlsx.py`) — change them in one place and every instrument picks up the change on next regen.

---

## 6.12 Durable resume — OnStop + savepartial

**(Khurshid 2022-09-21 *Working with Blocks*)** — critical pattern for tablet field work. Without it, an enumerator dropping the tablet, the battery dying, or the OS killing the app mid-interview means the partial case is lost.

### 6.12.1 Why this is non-negotiable

UHC F4 household interviews can run 60–90 minutes. F1 facility-head interviews run 45–60. F3 patient interviews run 30–45. **All of them are long enough** that "tablet died at minute 35" is a real, recurring scenario. Field surveys without OnStop + savepartial wiring lose 2–5% of cases to silent partial loss; they show up in the data export as duplicates or as suspiciously short cases.

### 6.12.2 The minimum safe pattern

```cspro
PROC GLOBAL
  function OnStop()
    savepartial();
  end;
```

Three lines. Add to every F-series .apc. CSEntry calls `OnStop` whenever the user presses Stop, Escape, Ctrl+S, or the OS forcibly exits the app. `savepartial()` writes the case in its current state to the data file with a partial-flag set.

### 6.12.3 The production-grade pattern

Beyond the minimum, save the cursor position so the next session resumes where it left off:

```cspro
PROC GLOBAL
  function OnStop()
    savepartial();
    savesetting("last_field",
                concat(strip(getsymbol(curfield())), "_",
                       maketext(curocc())));
    savesetting("last_case",
                maketext(QUESTIONNAIRE_NO));
  end;
```

`getsymbol(curfield())` returns the dictionary name of the current field. `curocc()` returns the current roster occurrence. The encoded "last position" string (e.g. `"Q12_PCB_LICENSING_1"`) is enough to navigate back to the field on resume.

### 6.12.4 Resume on next launch

In the application-level preproc:

```cspro
PROC FACILITYHEADSURVEY_FF
preproc
  numeric n_cases;
  n_cases = keylist(MAIN_DICT);     { count of cases in the data file }

  if n_cases > 0 and loadsetting("last_field") <> "" then
    numeric choice;
    choice = accept(tr("Resume from last position?"),
                    tr("Yes, resume"),
                    tr("No, start fresh"));
    if choice = 1 then
      { CSEntry handles partial-resume natively when the case is reopened. }
      { The saved last_field setting is informational — for UI hint. }
    else
      savesetting("last_field", "");      { user chose fresh — clear }
    endif;
  endif;
```

Pair with a `forcase` + `case_status` filter (Khurshid 2022-10-23 *Working with Cases*) to enumerate partial cases on relaunch:

```cspro
function ListPartialCases()
  forcase MAIN_DICT where case_status = partial do
    { build a UI list of case keys for the user to pick from }
    putdialogvalue(case_key);
  endcase;
end;
```

### 6.12.5 Externalise via Resume-Handlers.apc

To keep the per-instrument .apc clean, extract OnStop / partial-case helpers into `shared/Resume-Handlers.apc`:

```apc
{ Resume-Handlers.apc — reusable OnStop + partial-case helpers for UHC.

  Include:
      #include "../shared/Resume-Handlers.apc"

  Provides:
  - SavePartialWithMarker()  — wraps savepartial() + savesetting("last_field", ...).
  - ClearResumeMarker()      — clears the last_field setting (call from CLOSING.postproc).
  - PromptResume()           — accept() prompt; returns 1 (resume) / 2 (fresh).
}

PROC GLOBAL


function SavePartialWithMarker()
  savepartial();
  savesetting("last_field",
              concat(strip(getsymbol(curfield())), "_",
                     maketext(curocc())));
end;


function ClearResumeMarker()
  savesetting("last_field", "");
end;


function PromptResume()
  numeric n_cases;
  n_cases = keylist(MAIN_DICT);
  if n_cases > 0 and loadsetting("last_field") <> "" then
    PromptResume = accept(tr("Resume from last position?"),
                          tr("Yes, resume"),
                          tr("No, start fresh"));
  else
    PromptResume = 0;
  endif;
end;
```

Per-instrument:

```cspro
#include "../shared/Resume-Handlers.apc"

PROC GLOBAL
  function OnStop()
    SavePartialWithMarker();
  end;


PROC FACILITYHEADSURVEY_FF
preproc
  numeric resume_choice;
  resume_choice = PromptResume();
  if resume_choice = 2 then
    ClearResumeMarker();
  endif;


PROC CLOSING_FORM
postproc
  ClearResumeMarker();        { case completed — wipe the marker }
```

Three lines of wiring per instrument; the helper file is one place to update if the resume UX evolves.

---

## 6.13 Multi-language

**(Khurshid 2022-09-26 *Multi Languages for CAPI and Valuesets*)** — three independent stacks must be translated for a fully-localised application.

### 6.13.1 The three-stack model

| Stack | Where labels live | How to translate |
|---|---|---|
| **Dictionary labels** | `*.dcf` — item, value-set, value labels. | Edit menu → Languages → add language → re-enter every label per language. |
| **CAPI question text** | `*.qsf` — per-item question text. | Options → Data Entry → "Use question text"; CAPI menu → Define CAPI Languages → add. Per item, CAPI Questions icon, fill in text per language. |
| **Messages tab** | `*.mgf` — error / warning strings. | Messages tab in logic editor; mark sections with `language=Name`. |

A common bug pattern: translate questions and value-sets but forget the messages file. The interview reads in Filipino, but every error message pops up in English. UAT round 1 finds this; budget time to do the third stack.

### 6.13.2 Per-language value-set naming convention

`<item>_vs1_<lang>` — name encodes both the version (`vs1`) and the language code.

For UHC F1 example value set `FACILITY_TYPE`:

| Value-set name | Language | Sample label (first option) |
|---|---|---|
| `FACILITY_TYPE_vs1_en` | English | "Primary Care Facility" |
| `FACILITY_TYPE_vs1_fil` | Filipino | "Pasilidad ng Pangunahing Pangangalaga" |
| `FACILITY_TYPE_vs1_bis` | Cebuano | "Pasilidad sa Panguna nga Pag-atiman" |
| `FACILITY_TYPE_vs1_hil` | Hiligaynon | "Pasilidad sang Panguna nga Pag-atipan" |
| `FACILITY_TYPE_vs1_ilo` | Ilokano | "Pasilidad iti Kangrunaan a Panangaywan" |
| `FACILITY_TYPE_vs1_war` | Waray | "Pasilidad han Pangurok-na nga Pag-atiman" |
| `FACILITY_TYPE_vs1_pam` | Kapampangan | "Pasilidad ning Manibalu a Pamamasa" |
| `FACILITY_TYPE_vs1_pag` | Pangasinan | "Pasilidad na Manunan a Panangasikaso" |

**Values are identical across language variants** — only labels change. If you ever recode (add a new option), update **every** language's value set in lockstep.

Workflow per Khurshid 2022-09-26:

1. Build the English set first: right-click item → Add Value Set → name `<item>_vs1_en` → fill code/label pairs.
2. Copy the entire value set, paste it after the last value label → "Insert After" → rename to `_vs1_<lang>` → translate the labels.
3. Repeat for each additional language.

### 6.13.3 ISO language codes

Use ISO 639-1 / 639-3 two- or three-letter codes:

| Language | ISO code |
|---|---|
| English | `en` |
| Filipino / Tagalog | `fil` (or `tl`) |
| Cebuano (Bisaya) | `bis` |
| Hiligaynon | `hil` |
| Ilokano | `ilo` |
| Waray | `war` |
| Kapampangan | `pam` |
| Pangasinan | `pag` |

When ISO codes are used, CSEntry on a Filipino-locale tablet **auto-selects Filipino at first launch** without explicit `setlanguage()`. ASPSI 2026-05-04 meeting: 7 dialects required. Document the pattern; the actual translations land later in Phase 9 once English is locked.

### 6.13.4 Runtime language switching

Three functions handle language switching at runtime:

```cspro
PROC GLOBAL
  function OnChangeLanguage()
    savesetting("save_last_language", getlanguage());
    { switch any per-language value sets }
    if getlanguage() = "fil" then
      setvalueset(FACILITY_TYPE, FACILITY_TYPE_vs1_fil);
      setvalueset(YES_NO,        YES_NO_vs1_fil);
      { ... etc }
    elseif getlanguage() = "bis" then
      setvalueset(FACILITY_TYPE, FACILITY_TYPE_vs1_bis);
      setvalueset(YES_NO,        YES_NO_vs1_bis);
    elseif getlanguage() = "hil" then
      setvalueset(FACILITY_TYPE, FACILITY_TYPE_vs1_hil);
      setvalueset(YES_NO,        YES_NO_vs1_hil);
    { ... etc — one branch per supported language }
    else
      { default — English }
      setvalueset(FACILITY_TYPE, FACILITY_TYPE_vs1_en);
      setvalueset(YES_NO,        YES_NO_vs1_en);
    endif;
  end;
```

| Function | Purpose |
|---|---|
| `setlanguage("fil")` | Switch to Filipino at runtime. CSEntry refreshes question text + dictionary labels + messages. |
| `getlanguage()` | Read current language code. |
| `OnChangeLanguage` | Reserved global function — fires on every `setlanguage()` call. Use it to switch per-language value sets via `setvalueset()`. |

**Gotcha:** `setlanguage("fil")` switches **question text**, **dictionary labels**, and **errmsg strings** automatically (the latter because the .mgf has `language=fil` sections). It does **not** switch value-set bindings — those need explicit `setvalueset()` calls.

### 6.13.5 Persisted language pattern

```cspro
{ Application-level preproc — load saved or default to English. }
PROC FACILITYHEADSURVEY_FF
preproc
  if loadsetting("save_last_language") <> "" then
    setlanguage(loadsetting("save_last_language"));
  else
    setlanguage("en");          { project-wide default during build }
  endif;
```

This pairs with `OnChangeLanguage` (above) which writes `savesetting("save_last_language", getlanguage())` whenever the user switches.

Net effect:

- First launch on English-locale tablet → English (default).
- First launch on Filipino-locale tablet → Filipino (auto-detected from ISO code).
- User switches to Cebuano mid-session → Cebuano remembered for next launch on the same tablet.

### 6.13.6 The `tr()` function for translatable string literals

Wrap any string literal in PROC code with `tr()` to mark it translatable:

```cspro
if accept(tr("Continue from last position?"),
          tr("Yes"),
          tr("No")) = 1 then
  { resume }
endif;
```

Each `tr(...)` call resolves against the .mgf at runtime. Without `tr()`, the literal is hard-coded English regardless of `setlanguage()`.

### 6.13.7 What translates and what doesn't

| Translates | Stays in English |
|---|---|
| Dictionary item labels | Item names |
| Value-set labels | Value codes |
| CAPI question text | Field IDs |
| `errmsg` strings via .mgf IDs | `errmsg` IDs |
| `tr(...)` wrapped string literals | PROC code identifiers |
| Help text | Comment blocks |

Item names, value codes, message IDs, and field IDs are language-neutral and stable across translations. Translation churn affects only labels + question text + message strings + help. Plan accordingly: translation is a string-substitution task, not a code task.

### 6.13.8 ASPSI translation pipeline

Per [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/ASPSI Translation Pipeline]] (planned 2026-05-04 ASPSI meeting): 7 dialects required, but ASPSI has not delivered translations yet. Build the **switcher infrastructure** to accept drop-in locales:

1. Define all 8 languages (`en` + 7 dialects) in CAPI Languages dialog.
2. Add `language=<code>` sections to the .mgf for each, populated initially with English text + a TODO comment.
3. Create per-language value sets (`*_vs1_<lang>`) populated initially with English labels + TODO.
4. Wire `OnChangeLanguage` to switch all value sets per language.
5. When ASPSI delivers translations (Excel rows of `id, en, fil, bis, ...`), the team substitutes in place — no PROC code changes.

The infrastructure cost is ~1 hour per instrument; the translation cost is whatever ASPSI quotes for the actual linguistic work.

---

## 6.14 Block organization

**(Khurshid 2022-09-21 *Working with Blocks*)** — blocks group related fields on the form, support collective gating, and unlock runtime field-property toggles.

### 6.14.1 What a block does

| Behaviour | Block-on | Block-off |
|---|---|---|
| Tablet rendering | All block fields appear on one screen, enumerator can enter in any order. | Strict per-field navigation. |
| Logic | Block-level preproc / postproc / onfocus available — single place for cross-field logic. | Logic only at item level. |
| Movement | `skip to <BLOCK_NAME>`, `move to <BLOCK_NAME>` work — reorder fields without rewriting movement. | Movement uses field names directly. |

### 6.14.2 Adding a block in Designer

1. On the form, **Ctrl+click multiple fields** to multi-select.
2. Right-click → **Add Block**.
3. Give it a label and a name.
4. OK — the block appears in the form tree with a **red icon**.

To remove: select block → right-click → Delete Block → answer **No** to "Do you want to delete the fields in the block?" (keeps the items, removes only the grouping). Yes removes both.

### 6.14.3 Block-level preproc for collective gating

(Already shown in §6.4.4.) The pattern:

```cspro
PROC F_INPATIENT_BLOCK
preproc
  if Q31_CARE_SETTING <> 1 then
    endgroup;             { skip the entire block }
  endif;
```

For UHC, use blocks for:

- **Section subdividers** — e.g. F1 Section C-1 (UHC awareness questions Q9–Q12), C-2 (Units & Roles Q13–Q22), each its own block.
- **Eligibility-gated subsections** — F3 inpatient block (Section H), F3 outpatient block (Section G), gated on Q31.
- **Hospital-only subsections** — F1 Q132–Q134 hospital pricing block, gated on Q8 = hospital level.
- **Roster blocks** — F4 per-person roster block, with `endgroup` on `curocc() > N_HHM`.

### 6.14.4 setProperty for runtime field protection inside block logic

**(Khurshid 2022-09-21 @ 13:08)** — toggle field properties (Protected / Visible) at runtime inside a block's preproc.

```cspro
PROC ROSTER_PERSON_BLOCK
preproc
  if curocc() > N_HHM then
    endgroup;
  endif;
  if curocc() = 1 then
    R_RELATIONSHIP = 1;            { auto-set: occ 1 is head }
    setProperty(R_RELATIONSHIP, "Protected", "Yes");
  else
    R_RELATIONSHIP = notappl;       { not yet entered }
    setProperty(R_RELATIONSHIP, "Protected", "No");
  endif;

  if AGE >= 7 and AGE < 12 then
    EDUCATION_LEVEL = notappl;
    setProperty(EDUCATION_LEVEL, "Protected", "Yes");
  elseif AGE >= 12 then
    setProperty(EDUCATION_LEVEL, "Protected", "No");
  endif;
```

**Pair every "Protected = Yes" branch with a corresponding "Protected = No" branch elsewhere** — otherwise a field stays protected once set, even when the gating condition flips.

### 6.14.5 setProperty values worth knowing

| Property | Values | Purpose |
|---|---|---|
| `Protected` | `"Yes"` / `"No"` | Read-only toggle. |
| `Visible` | `"Yes"` / `"No"` | Show/hide. |
| `BackgroundColor` | hex `"#FFEEAA"` | Visual emphasis. |
| `FontColor` | hex `"#FF0000"` | Visual warning. |
| `Italic` / `Bold` / `Underline` | `"Yes"` / `"No"` | Type style. |

Use sparingly. Most UHC gating is binary (asked / not asked); over-styling makes screens noisy.

---

## 6.15 Sample-file integration (F4)

**(Khurshid 2022-09-05 *Create a Sample File for Household Interview*)** — F4 uses interval sampling from patient-listed households.

### 6.15.1 The F4 sample-file pipeline

The F4 sample is built by Phase 0/1 of fieldwork, not by the CAPI app:

1. **F3b Patient Listing** (Annex F3b — the patient listing protocol) — enumerator team visits each sampled facility, captures the patient roster for the recall window. Output: per-facility CSV of patient IDs + household geo (PSGC + GPS).
2. **Concatenate per-enumerator files** — one combined patient-list CSV per supervisor cluster.
3. **Interval sampling with random offset** — pick every k-th household using a supervisor-specific random offset to draw the F4 sample.
4. **Per-enumerator file split** — distribute the F4 sample back to enumerators, one file per assigned cluster.

### 6.15.2 Sample-file format

```csv
SAMPLE_ID,FACILITY_ID,PATIENT_ID,HH_REGION,HH_PROVINCE,HH_CITY,HH_BARANGAY,HH_GPS_LAT,HH_GPS_LON
F4-0001,1300010000,P000123,13000000,1300010000,1300010100,1300010100001,14.5995,121.0123
F4-0002,1300010000,P000156,13000000,1300010000,1300010100,1300010100007,14.6012,121.0145
...
```

Place at `<F4 app>/sample/<cluster_code>.csv`, attach as an **external dictionary** in the F4 app.

### 6.15.3 Loading the sample file in F4 .apc

```cspro
{ External dict — F4_SAMPLE_DICT — declared via Add Files in Designer. }

PROC HOUSEHOLDSURVEY_FF
preproc
  { resolve sample file path — could be passed via PFF parameter }
  string sample_file;
  sample_file = pathname(workingDir) + "sample/" +
                loadsetting("cluster_code") + ".csv";
  setfile(F4_SAMPLE_DICT, sample_file);


PROC SAMPLE_ID
onfocus
  { populate dropdown from sample dict }
  ValueSet vs;
  forcase F4_SAMPLE_DICT do
    vs.add(maketext("%s — HH at %s", PATIENT_ID, HH_BARANGAY), SAMPLE_ID);
  endcase;
  setvalueset(SAMPLE_ID, vs);


PROC SAMPLE_ID
postproc
  { pull household geo + patient ID from the sample row }
  if loadcase(F4_SAMPLE_DICT, SAMPLE_ID) = 0 then
    errmsg(5030, SAMPLE_ID);     { "Sample ID not found in cluster file." }
    reenter;
  endif;
  HH_REGION    = F4_SAMPLE_DICT.HH_REGION;
  HH_PROVINCE  = F4_SAMPLE_DICT.HH_PROVINCE;
  HH_CITY      = F4_SAMPLE_DICT.HH_CITY;
  HH_BARANGAY  = F4_SAMPLE_DICT.HH_BARANGAY;
  HH_GPS_LAT_PRELOAD = F4_SAMPLE_DICT.HH_GPS_LAT;
  HH_GPS_LON_PRELOAD = F4_SAMPLE_DICT.HH_GPS_LON;
  PATIENT_ID   = F4_SAMPLE_DICT.PATIENT_ID;
  FACILITY_ID  = F4_SAMPLE_DICT.FACILITY_ID;
```

### 6.15.4 forcase + inc() for forward-only iteration with running totals

When the F4 app needs to enumerate the sample (e.g. for a per-cluster progress dashboard):

```cspro
function ListSampleProgress()
  numeric total, completed;
  total = 0;
  completed = 0;

  forcase F4_SAMPLE_DICT do
    inc(total);
    if loadcase(F4_DATA, F4_SAMPLE_DICT.SAMPLE_ID) = 1 then
      if ENUM_RESULT_FINAL_VISIT = 1 then
        inc(completed);
      endif;
    endif;
  endcase;

  errmsg(6010, completed, total);    { "Cluster progress: %d of %d cases done." }
end;
```

`forcase` walks the external dict forward-only. `inc(var)` is shorthand for `var = var + 1`. The pattern shows up wherever you need to summarise an external-dict roster.

### 6.15.5 Sample integrity validations

```cspro
{ Reject sample IDs that don't match the assigned cluster. }
PROC SAMPLE_ID
postproc
  if substring(SAMPLE_ID, 1, length(loadsetting("cluster_code"))) <>
     loadsetting("cluster_code") then
    errmsg(5031, SAMPLE_ID, loadsetting("cluster_code"));
    reenter;
  endif;
```

Refer to [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3b Patient Listing Protocol]] for the listing → sampling protocol details.

---

## 6.16 EA boundary fence — optional geofencing

**(Khurshid 2022-08-03 *Restrict an Enumerator from Working Outside the EA Boundary*)** — KML-defined polygon + point-in-polygon test against enumerator GPS.

### 6.16.1 The pattern

1. **Draw the EA polygon** in Google Earth → click vertices → close the polygon (start = end vertex).
2. **Save as KML**.
3. **Convert to Excel** — open KML in Notepad, copy the `<coordinates>` block, paste into Excel, Text-to-Columns by comma, transpose, add `EA_ID, vertex_seq, longitude, latitude` columns.
4. **Convert to CSPro external dict** — Tools → Excel to CSPro → save as `polygon_dict.dcf` + `polygon_dict.dat`.
5. **In the EA-number item postproc**, run a **point-in-polygon test** against current GPS:

```cspro
PROC EA_NUMBER
postproc
  if not ReadGPSReading(60, 30) then
    errmsg(5040);    { "GPS unavailable — cannot verify EA boundary." }
    exit;
  endif;
  numeric cur_lon, cur_lat;
  cur_lon = gps(longitude);
  cur_lat = gps(latitude);

  if loadcase(POLYGON_DICT, EA_NUMBER) = 0 then
    errmsg(5041, EA_NUMBER);
    reenter;
    exit;
  endif;

  numeric count_n, find_n, i;
  count_n = count(POLYGON_DICT.POLY_REC);
  find_n = 0;
  for i = 1 to count_n - 1 do
    { compare edge (i, i+1) against horizontal ray from cur_lat through cur_lon }
    if (POLY_LAT(i) <= cur_lat and POLY_LAT(i+1) > cur_lat) or
       (POLY_LAT(i+1) <= cur_lat and POLY_LAT(i) > cur_lat) then
      numeric x_intersect;
      x_intersect = POLY_LON(i) +
                    (cur_lat - POLY_LAT(i)) /
                    (POLY_LAT(i+1) - POLY_LAT(i)) *
                    (POLY_LON(i+1) - POLY_LON(i));
      if x_intersect > cur_lon then
        find_n = find_n + 1;
      endif;
    endif;
  enddo;

  { odd crossings = inside; even = outside }
  if (find_n % 2) = 0 then
    errmsg(5042);    { "You are outside the assigned EA boundary." }
    reenter;
  endif;
```

### 6.16.2 Visual feedback on rejection

Khurshid recommends generating an on-device KML showing the polygon + the enumerator's current point, opened in Google Earth or the device's KML viewer:

```cspro
function ShowBoundaryViolation(numeric cur_lon, numeric cur_lat)
  string out_kml;
  out_kml = pathname(workingDir) + "violation.kml";
  { copy master KML, append <Placemark> for current location }
  { ... see Khurshid 2022-08-03 @ 11:08 for full helper }
  if getos() = 10 then
    execsystem("explorer " + out_kml);
  else
    execsystem("view " + out_kml);
  endif;
end;
```

### 6.16.3 Should UHC adopt EA boundary fencing?

**Recommendation per instrument:**

- **F1 (single facility)** — **NO**. Single facility, GPS verifies presence, not boundary; geofence overhead doesn't pay off. Keep GPS capture only.
- **F3 (patient interview, often at the facility or patient home)** — **NO** for MVP. Patient could be interviewed at home in another barangay; geofence would create false positives. Revisit if QC sees facility-shifting patterns.
- **F4 (household, interval-sampled from patient listing)** — **MAYBE — barangay-level fence**. Each F4 household has a known barangay from the listing; an enumerator straying to a different barangay should trigger a soft warning. Implement at barangay level, not EA level.

Action: log as TODO in [[../../../1_Projects/ASPSI-DOH-CAPI-CSPro-Development/scrum/product-backlog]]; revisit during F4 sprint planning. Do not block Phase 6 build on this.

---

## 6.17 PFF and entry application packaging

The Program Information File (PFF) is what CSEntry actually launches. Each PFF references one entry app (`.ent`) plus runtime parameters: language, sync settings, prefilled key values.

### 6.17.1 Build a PFF object to chain-launch another application

**(Khurshid 2022-04-15 *Tutorial 1: Create PFF and Menu Application*)** — programmatically construct a PFF at runtime to launch a second CSPro app from the first. Common pattern: login app → menu app → instrument data-entry app.

```cspro
PROC GLOBAL
PFF f1_pff;

function LaunchF1()
  f1_pff.setProperty("Version", "CSPro 8.0");
  f1_pff.setProperty("ApplicationType", "entry");
  f1_pff.setProperty("StartMode", "add");
  f1_pff.setProperty("FullScreen", "yes");
  f1_pff.setProperty("Application",
                     "..\\F1\\FacilityHeadSurvey.ent");
  f1_pff.setProperty("InputData",
                     "..\\F1\\data\\F1_data.dat");
  f1_pff.setProperty("Language", "en");
  f1_pff.setProperty("OnExit",
                     "..\\menu\\menu_app.pff");
  f1_pff.save();
  f1_pff.execute();
end;
```

| Property | Purpose |
|---|---|
| `Version` | CSPro version (`8.0`). |
| `ApplicationType` | `entry` for data-entry; `batch` for CSBatch. |
| `StartMode` | `add` / `modify` / `view`. |
| `FullScreen` | `yes` / `no` — recommended `yes` on tablets. |
| `Application` | Path to the `.ent`. |
| `InputData` | Path to the `.dat`. |
| `Language` | Initial language code. |
| `OnExit` | Path to the PFF to chain on close (returns to menu). |

### 6.17.2 Per-application HTML dialog directory

**(Khurshid 2022-04-24 *Using HTML Dialogs for displaying logic function*)** — set per-application HTML-dialog directory in PFF:

```cspro
f1_pff.setProperty("HtmlDialogsPath", "..\\F1\\htmldialogs");
```

This lets each instrument carry its own consent.html, choose.html, etc., picked up at runtime without polluting the global CSPro install.

### 6.17.3 Toggle HTML dialogs per application

**(Khurshid 2022-04-18)** — Application Properties → "Use Custom HTML Dialogs" checkbox enables per-app dialogs. When unchecked, CSPro falls back to its default text prompts (cleaner for desk-test, friendlier for field).

### 6.17.4 Customise the global accept-dialog template

**(Khurshid 2022-04-24)** — `choose.html` is the global template the `accept(...)` function renders when no custom HTML is specified. Style it once for branding consistency.

`htmldialogs/choose.html` skeleton:

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body { font-family: Arial, sans-serif; padding: 24px;
           background: linear-gradient(180deg, #f8f8f8 0%, #fff 100%); }
    .prompt { font-size: 14pt; margin-bottom: 24px; }
    .buttons { display: flex; gap: 12px; }
    .buttons button { flex: 1; padding: 12px;
                       font-size: 13pt; border: 0; border-radius: 6px;
                       background: #2a5a8a; color: white; }
    .buttons button.secondary { background: #888; }
  </style>
</head>
<body>
  <div class="prompt">{prompt}</div>
  <div class="buttons">
    <button onclick="accept(1)">{button_1}</button>
    <button class="secondary" onclick="accept(2)">{button_2}</button>
  </div>
</body>
</html>
```

`{prompt}`, `{button_1}`, `{button_2}` are CSPro's substitution tokens — replaced at runtime with the strings passed to `accept(...)`.

### 6.17.5 Authenticate-then-launch pattern

**(Khurshid 2022-04-15)** — login app validates credentials, then launches the menu/data-entry app via PFF:

```cspro
PROC LOGIN_APP_PASSWORD
postproc
  USER_NAME_PASSWORD = LOGIN_APP_ID;
  if loadcase(USERNAME_PASSWORD_DICT, USER_NAME_PASSWORD) = 0 then
    errmsg(7001);    { "Login ID not found." }
    reenter;
  endif;

  if USER_NAME_PASSWORD_DICT.PASSWORD <> $ or $ = "" then
    errmsg(7002);    { "Incorrect password." }
    reenter;
  endif;

  if getos() = 20 then    { Android tablet }
    if DEVICE_ID <> USERNAME_PASSWORD_DICT.DEVICE_ID then
      errmsg(7003);  { "Login not authorised on this device." }
      reenter;
    endif;
  endif;

  { handoff context to menu app }
  savesetting("interviewer_id",
              maketext("%d", USERNAME_PASSWORD_DICT.INTERVIEWER_ID));
  savesetting("supervisor_id",
              maketext("%d", USERNAME_PASSWORD_DICT.SUPERVISOR_ID));
  savesetting("login_role",
              maketext("%d", USERNAME_PASSWORD_DICT.ROLE));

  if USERNAME_PASSWORD_DICT.ROLE = 1 then
    LaunchSupervisorMenu();
  else
    LaunchEnumeratorMenu();
  endif;
```

Keys handed off via `savesetting(...)` are read on the menu side via `loadsetting(...)`. Settings persist across app launches on the same device.

### 6.17.6 UHC packaging structure

```
deliverables/CSPro/
├── login/
│   ├── LoginApp.ent
│   ├── LoginApp.fmf
│   ├── LoginApp.ent.apc
│   └── LoginApp.pff
├── menu/
│   ├── MenuApp.ent             (enumerator menu)
│   ├── SupervisorMenuApp.ent   (supervisor menu)
│   └── htmldialogs/
│       ├── choose.html
│       └── about.html
├── F1/
│   ├── FacilityHeadSurvey.ent
│   ├── FacilityHeadSurvey.fmf
│   ├── FacilityHeadSurvey.ent.apc
│   ├── FacilityHeadSurvey.pff
│   └── htmldialogs/
│       └── consent_F1.html
├── F3/
│   ├── PatientSurvey.ent
│   ├── PatientSurvey.pff
│   └── htmldialogs/
│       └── consent_F3.html
├── F4/
│   ├── HouseholdSurvey.ent
│   ├── HouseholdSurvey.pff
│   └── htmldialogs/
│       └── consent_F4.html
└── shared/
    ├── PSGC-Cascade.apc
    ├── Capture-Helpers.apc
    ├── Validators.apc
    ├── Resume-Handlers.apc
    ├── psgc_*.dcf / .dat
    └── Validators.mgf
```

The menu app is the user-facing chooser — it lists F1 / F3 / F4 (filtered by role from the login handoff) and chains-launches the right entry app via PFF.

---

## 6.18 Helper APCs in the UHC project

Existing + planned shared APCs:

| APC | Status | Purpose | Provides |
|---|---|---|---|
| `PSGC-Cascade.apc` | **Built** | 4-level Philippine geo cascade. | `FillRegionValueSet`, `FillProvinceValueSet`, `FillCityValueSet`, `FillBarangayValueSet`. |
| `Capture-Helpers.apc` | **Built** | GPS + verification photo. | `ReadGPSReading(maxTimeSec, desiredAccuracyM)`, `TakeVerificationPhoto(filename)`. |
| `Validators.apc` | **TODO Phase 6** | Reusable validators. | `check_alpha_only`, `check_ph_mobile`, `check_email_basic`, `check_psgc_format`, `check_age_tenure_consistency`. |
| `Resume-Handlers.apc` | **TODO Phase 6** | OnStop + partial-case helpers. | `SavePartialWithMarker`, `ClearResumeMarker`, `PromptResume`. |
| `Sample-Helpers.apc` | **TODO Phase 6 (F4 only)** | Sample-file integration helpers. | `LoadSampleRow`, `ListSampleProgress`, `ValidateClusterID`. |

Each has the same skeleton:

```apc
{ <Helper>.apc — <one-line purpose>.

  Include in each instrument's .ent.apc:
      #include "../shared/<Helper>.apc"

  Prerequisites:
  - <list dictionary item names the helper assumes>
  - <list externally-referenced concepts>

  Provides:
  - <fn1>(...)  — <one-line>
  - <fn2>(...)  — <one-line>
}

PROC GLOBAL
  { ... function definitions ... }
```

### 6.18.1 Discipline rules

- **Pure functions only.** No item references except via parameters; no implicit globals.
- **errmsg via shared .mgf IDs** — every error string lives in `Validators.mgf` (or per-helper .mgf) so it's translatable.
- **Self-documenting header** — every helper file opens with a comment block listing prerequisites + provided functions.
- **Versioned in the file path** — when refactoring, keep the API stable across instruments. If breaking changes are needed, version the file (`Validators.apc.v2`) and migrate instruments one at a time.

### 6.18.2 When to extract a helper

The 2-of-3 rule:

- If a function is called from **2 places** in the same instrument → keep inline in that instrument's PROC GLOBAL.
- If a function is called from **2 instruments** → extract to a shared APC.
- If a function would be called from a **3rd instrument** → must be a shared APC.

Resist premature extraction. The PSGC cascade started inline; it became shared once F3 was added.

---

## 6.19 Build sequencing per F-series

Per the project state (F1 leading) and the ASPSI 2026-05-04 meeting target of June 12 CAPI completion:

### 6.19.1 F1 — first build, UAT pattern reference

- 12 records / ~671 items / 29 forms (25 + 4 stub rosters).
- **Status (2026-05-08)**: Build-ready, FMF Designer Walkthrough complete, .pff packaged.
- Pattern reference for F3 + F4 — every helper APC, every PROC pattern, every FMF convention validated here first.
- Pretest target: late May 2026.

### 6.19.2 F3 — patient survey (inpatient + outpatient branches)

- 18 records / ~806 items / 19 forms.
- **Adds**: F1 ↔ F3 linkage via `F3_FACILITY_ID`, two GPS captures (facility + patient home), Q1 patient-vs-proxy gate, Q31 inpatient-vs-outpatient routing, Q162 hard terminator.
- Reuses: every helper APC built for F1 + the FMF skeleton generator.
- Build target: mid-late May 2026.

### 6.19.3 F4 — household survey (with roster)

- 22 records / ~623 items / 24 forms.
- **Adds**: household roster + per-person blocks, Kish-grid respondent selection (if used), sample-file integration via Annex F3b listing, household geo (HH-prefixed PSGC + GPS).
- Reuses: every helper APC + skeleton generator + roster-block patterns from any roster-bearing F1 records.
- Build target: late May / early June 2026.

### 6.19.4 Build order rationale

F1 first because:

1. Smallest in form count (29 vs 30 vs 24 — actually F4 is smallest by forms but F1 is simpler in pattern complexity).
2. No roster — pattern complexity is bounded to single-occurrence forms.
3. Single GPS / single facility — simplest capture story.
4. Pattern reference for F3 + F4.

F3 second because it adds patient-home capture + facility linkage — incremental complexity over F1, but no roster.

F4 last because it adds household roster (multi-occurrence) + sample-file integration + per-person blocks — the most patterns at once.

### 6.19.5 Parallel work items during sequencing

While F1 is in pretest, F3 build proceeds. While F3 is in pretest, F4 build proceeds. The pipeline overlaps to hit June 12.

Cross-cutting items (build once, all three benefit):

- All shared APCs (`Validators.apc`, `Resume-Handlers.apc`, `Sample-Helpers.apc` for F4).
- `Validators.mgf` shared message file (all instruments include it).
- Login app + menu app (one each, all instruments chain off them).
- Consent HTML files (per instrument, but built from one template).

---

## 6.20 Phase 6 exit criteria

The .ent + .fmf + .apc + .mgf bundle is ready to advance to [[05-Phase-7-Testing]] when **all** of the following are true:

- [ ] **App loads in CSEntry Windows** without errors. Designer's Compile + Test run is green.
- [ ] **Happy-path traversal works** — you can open a fresh case, walk from the cover page to the last question, and submit without hitting an unexpected error.
- [ ] **Every skip from the Phase 4 spec is wired** — every row in the spec's skip table has a corresponding PROC block in the .apc, and a desk-test confirms the jump fires.
- [ ] **Every HARD validation is wired** — every HARD row in §3 of the spec has an `errmsg(<id>) + reenter` pattern in the right item's postproc.
- [ ] **Every SOFT validation is wired** — every SOFT row uses `accept(...)` and treats `<> 1` as re-enter.
- [ ] **Every GATE is wired** — every GATE row uses `setProperty(item, "Protected", "Yes/No")` in onfocus, or `skip to next` in preproc, consistently.
- [ ] **Externalized error messages** — every `errmsg` call uses a numeric ID, and every ID has a matching entry in `*.mgf` (one section per language at minimum, with English populated and other languages stubbed if pending translation).
- [ ] **Multi-language stub in place** — English at minimum. CAPI Languages dialog has 8 entries (`en` + 7 dialects) declared. Per-language value sets created (English populated, others stubbed). `OnChangeLanguage` switches per-language value sets. `setlanguage("en")` is the default.
- [ ] **OnStop + savepartial enabled** — at minimum `function OnStop() savepartial(); end;` in PROC GLOBAL. Production grade: `SavePartialWithMarker` from `Resume-Handlers.apc`.
- [ ] **FIELD_CONTROL with consent + GPS + AAPOR + interviewer ID** — `build_field_control` block intact, consent gate terminator wired, GPS capture form wired, paradata GPS configured, interviewer-ID prefill from login handoff.
- [ ] **PSGC cascade wired** — four `onfocus` handlers on REGION / PROVINCE_HUC / CITY_MUNICIPALITY / BARANGAY each calling the right `Fill*ValueSet` helper.
- [ ] **Capture-trigger fields auto-reset** — `FACILITY_CAPTURE_GPS = notappl` after read; `CAPTURE_VERIFICATION_PHOTO = notappl` after capture. Buttons re-arm for retry.
- [ ] **Helper APCs `#include`d** — `PSGC-Cascade.apc`, `Capture-Helpers.apc`, `Validators.apc`, `Resume-Handlers.apc` (and `Sample-Helpers.apc` for F4) at the top of the .apc.
- [ ] **PFF packaged** — `<Instrument>.pff` exists, points to the right `.ent`, the right `.dat`, the right HTML-dialog directory, and `OnExit` returns to menu.
- [ ] **Cross-instrument: login + menu apps wired** — login validates against `usernames_passwords.dcf`, hands off via `savesetting`, menu chains via PFF.
- [ ] **Form-layout review checklist passed** — every item in [[../CSPro/Form-Layout-Principles]] §10 is checked.
- [ ] **One round of pair-test with the spec author** — walk every section once with the spec open, confirm intent matches behaviour. Catch interpretation drift before pretest.

If any box above is unchecked, **return to that section** (not to Phase 5). Phase 6 → Phase 7 progression is one-way; once Phase 7 testing starts, every fix is a regression-test cost.

---

## 6.21 Common pitfalls (codified failures from the build pipeline)

A short list of mistakes the team has made or watched happen, gathered as you go:

1. **Skip target points to a missing field.** When an item is renamed in the dcf but the .apc still references the old name, `skip to <OLD_NAME>` silently no-ops and the skip never fires. **Mitigation:** regen the dcf, then run a grep over the .apc for any item names that no longer exist in the dcf.
2. **`reenter` without `errmsg`.** A bare `reenter` puts the cursor back without telling the operator why. **Mitigation:** always pair `errmsg` immediately before `reenter`.
3. **`accept()` confused with Enter-key.** On a tablet, the Enter key may be hidden. Use `accept(...)`'s buttons for explicit yes/no choices; never assume Enter = Yes.
4. **Forgetting to reset capture triggers.** If `FACILITY_CAPTURE_GPS` isn't reset to `notappl`, the trigger button stays disabled after one capture. Operators report "GPS button doesn't work" in pretest. **Mitigation:** every capture handler ends with `<TRIGGER> = notappl;`.
5. **Per-language value sets out of sync.** Adding a new option to the English value set without adding it to Filipino/Cebuano leaves those languages missing the option. **Mitigation:** keep per-language value sets in lockstep; update all languages before committing.
6. **`tr()` forgotten on literal strings.** A hard-coded `"Continue?"` in PROC code stays English forever. **Mitigation:** wrap every user-facing literal in `tr()`; lint pass before PR.
7. **OnStop not declared in PROC GLOBAL.** If declared elsewhere, CSEntry doesn't find it and Stop button = lose case. **Mitigation:** all `function OnStop()` declarations in PROC GLOBAL; verify by re-reading the .apc top section before sign-off.
8. **PSGC dictionary not deployed.** The `psgc_*.dat` files must be on the tablet alongside the .ent or the cascade fails silently with empty dropdowns. **Mitigation:** PFF's deployment package includes the entire `shared/` folder.
9. **HTML-dialog file referenced by relative path that breaks on tablet.** Tablet path separators are forward slash; Windows accepts both. Use forward slashes consistently in `htmlfile := "..."` arguments. **Mitigation:** test the dialog on a real tablet, not just in CSEntry Windows.
10. **`endgroup` in the wrong scope.** `endgroup` exits the current group. If you call it from a field deeper than expected, you exit the wrong block. **Mitigation:** always know which group you're in; prefer block-level preproc with `endgroup` rather than scattered field-level `endgroup` calls.
11. **Paradata file not deployed for sync.** Without explicit sync configuration, `<Instrument>.par` doesn't reach CSWeb. QC pipelines that rely on paradata silently get nothing. **Mitigation:** sync configuration includes paradata files explicitly.
12. **Block-level setProperty toggles drift.** If a block's preproc protects a field on one path but doesn't unprotect on another, the field stays locked. **Mitigation:** every `setProperty(<>, "Protected", "Yes")` has a paired `setProperty(<>, "Protected", "No")` elsewhere in the same scope.

---

## Cross-references

- [[../CSPro/Form-Layout-Principles]] — universal form-layout rules (read before any FMF work).
- [[../CSPro/F1/F1-Form-Layout-Plan]] — F1's per-form inventory.
- [[../CSPro/F3/F3-Form-Layout-Plan]] — F3's per-form inventory.
- [[../CSPro/F4/F4-Form-Layout-Plan]] — F4's per-form inventory.
- [[../CSPro/F1/F1-Skip-Logic-and-Validations]] — F1 spec, source of paste-ready PROC.
- [[../CSPro/F3/F3-Skip-Logic-and-Validations]] — F3 spec.
- [[../CSPro/F4/F4-Skip-Logic-and-Validations]] — F4 spec.
- [[../CSPro/shared/PSGC-Cascade]] — PSGC cascade implementation.
- [[../CSPro/shared/Capture-Helpers]] — GPS + photo helpers.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Logic Events]] — preproc / onfocus / postproc firing order.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro CAPI Strategies]] — Census Bureau design patterns.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Multi-Language Applications]] — three-stack language model.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/GPS and Photo Capture]] — capture-record structure across instruments.

---

## Appendix A — Popstan supervisor-app pattern *(folded from CAPI-Development-Playbook 2026-04-21)*

The US Census Bureau ships an official CAPI reference architecture as part of CSPro 8.0 — the **Popstan CAPI Census** sample. It's not a separate "CSEntry Supervisor" binary; it's a **three-application composition** that implements role-based supervisor-vs-interviewer workflows inside the ordinary CSEntry runtime. **Recommended as the scaffold for the F1/F3/F4 field deployment.**

Reference location: `3_Resources/Tools-and-Software/CSPro/Examples 8.0/1 - Data Entry/CAPI Census/` (and upstream at `github.com/CSProDevelopment/examples`).

### A.1 Architecture — three cooperating apps + shared dictionaries

```
                         +-------------------+
                         |    Login.ent      |
                         | username + PIN    |
                         | writes persistent |
                         | login_supervisor  |
                         | login_interviewer |
                         +---------+---------+
                                   |
                                   v
                         +-------------------+
                         |    Menu.ent       |
                         | reads persistent  |
                         | role, branches:   |
                         +---------+---------+
                          /                  \
                         v                    v
           +--------------------+   +----------------------+
           | M_SUPERVISOR_MENU  |   | M_INTERVIEWER_MENU   |
           |  - create intvrs   |   |  - select assignment |
           |  - assign EAs      |   |  - collect cases     |
           |  - sync w/ intvrs  |   |  - sync w/ super     |
           |  - sync w/ HQ      |   |    (BT)              |
           |  - status report   |   |  - logout            |
           +---------+----------+   +----------+-----------+
                     |                         |
                     v                         v
           +--------------------+   +----------------------+
           |  (sync operations) |   |  F1 / F3 / F4 .ent   |
           +--------------------+   +----------------------+
```

Shared dictionaries drive role logic:

| Dictionary | Purpose | Key items |
|---|---|---|
| `PSC_STAFF_DICT` | Who is who | `staff_code` (UUID), `username`, PIN, **role**, **`S_SUPERVISOR_STAFF_CODE`** (links interviewer → their supervisor) |
| `PSC_ASSIGNMENTS_DICT` | Who does what where | province, district, EA, `staff_code`, **`A_ROLE`** (1=interviewer, 2=supervisor) |
| `PSC_GEOCODES_DICT` | Geographic hierarchy | **In UHC, replaced with the four `shared/psgc_*.dcf` externals already built.** |

### A.2 Role-branching logic

`Menu.ent.apc` (paste-ready, simplified from the Popstan sample lines 47–114 + 259–262):

```cspro
numeric isInterviewer;

if login_interviewer <> "" then
  saved_staff_code = login_interviewer;
  isInterviewer = true;
elseif login_supervisor <> "" then
  saved_staff_code = login_supervisor;
  isInterviewer = false;
endif;

{ ... load the assignment's A_ROLE from PSC_ASSIGNMENTS_DICT ... }

if A_ROLE = 1 then
  skip to M_INTERVIEWER_MENU;
elseif A_ROLE = 2 then
  skip to M_SUPERVISOR_MENU;
endif;
```

Both menus live in the same `Menu.fmf`; enumerators and supervisors install the same `.pen` package but see different UI.

### A.3 Mapping Popstan → UHC F1/F3/F4

| Popstan component | UHC equivalent | Notes |
|---|---|---|
| `Login/` | Reuse as-is | No change needed. |
| `Menu/` with `M_SUPERVISOR_MENU` + `M_INTERVIEWER_MENU` | Customize labels; add F2 PWA launch button to interviewer menu | F2 is self-admin PWA (`https://f2-pwa.pages.dev`); interviewer menu can offer "Open F2 link" via `execsystem("...")`. |
| `Household/` (single app) | **Three launch buttons**: F1 Facility, F3 Patient, F4 Household — each calls the corresponding `.ent` via `execpff` | Menu items visible to an enumerator depend on assignment type. |
| `PSC_GEOCODES_DICT` | `shared/psgc_*.dcf` externals + `PSGC-Cascade.apc` | Already built. |
| `PSC_STAFF_DICT` | Seed from ASPSI's roster — STLs + enumerators per cluster (May 4 meeting confirms 6 clusters, ~50 SEs) | CSV → seed script. |
| `PSC_ASSIGNMENTS_DICT` | Seed from cluster allocation plan | From the Survey Manager's fieldwork map. |
| `Interviewer-Status-Report.html` | Customize KPIs for F-series: cases completed by form type, daily rate, replacement-protocol flags | Live on-tablet dashboard for STLs. |
| Bluetooth sync (supervisor↔enumerator) | Keep as-is | Backup channel; primary remains CSWeb. |
| Dropbox for HQ sync | **Replace with CSWeb** | Per Popstan readme: *"for a census CSWeb would be a more appropriate solution."* |

### A.4 Recommended adoption path

1. Clone the `CAPI Census/` sample into `deliverables/CSPro/supervisor_scaffold/` (keep original read-only in `3_Resources/`).
2. Replace `PSC_GEOCODES_DICT` references with our PSGC externals; wire `PSGC-Cascade.apc`.
3. Strip Popstan-specific `Household` form; replace with three launch buttons → F1/F3/F4 `.ent` files via `execpff`.
4. Seed `PSC_STAFF_DICT` from ASPSI HR list (use a Python seeder, not hand-typed).
5. Customize `Interviewer-Status-Report.html` for F-series KPIs.
6. Swap Dropbox sync for CSWeb sync endpoints (see [[06-Phase-8-CSWeb-and-Tablets]]).
7. Package the full bundle (`Login` + `Menu` + 3× F-app) as one `.pen`; deploy through CSWeb Packages.
8. Train supervisors on first-run setup (supervisor password → create supervisor PIN → create enumerator usernames).

### A.5 Open decisions for UHC adoption

- Single `PSC_STAFF_DICT` across F1/F3/F4, or per-form? (Recommend single — same enumerator may work multiple forms.)
- Should F2 PWA launch from the same menu? (`execsystem` to open the URL is trivial.)
- Supervisor dashboard KPIs — discuss with Field Manager.
- Supervisor password rotation policy — fixed or per-wave?

---

## Next

[[05-Phase-7-Testing]] — desk testing, bench testing with mock cases, pair testing, regression-as-data, pretest readiness gate.
