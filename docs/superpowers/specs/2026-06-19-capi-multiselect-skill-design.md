# Design Spec — `capi-multiselect` skill

- **Date:** 2026-06-19
- **Status:** Approved design → ready for implementation plan
- **Project:** ASPSI-DOH-CAPI-CSPro-Development (F1 Facility Head, F3 Patient, F4 Household — CSPro/CSEntry)
- **Author context:** Carl produces CAPI; ASPSI is the DOH interface. Decisions surface as in-chat go/no-go.

## 1. Problem

Multi-select questions are currently fixed in **divergent, hand-rolled ways**, which has shipped bugs and inconsistency:

- **Pure multi-select** (Yes/No-per-option → tick-all checkbox) is done ad-hoc inside `capi-uat-triage` via the `CHECKBOX_CONVERT` table. Mechanically correct but un-skilled and easy to half-apply (the silent single-select data-loss trap when the `optimize`/fmf steps are missed).
- **Multi-select + amounts** has been built **two different ways**: a **roster** (Q92) via `capi-form-redesign`, and a hand-rolled **2-form-flat** (Q97.1). Same problem, two shapes — exactly the divergence testers are implicitly objecting to.

Testers keep filing these as "Response Layout" / "Question Formatting" / "Lesser Page for each Item" issues. The fix recipe lives partly in a skill (`capi-form-redesign`), partly in a memory card (`reference_cspro_checkbox_conversion_lists`), and partly in ad-hoc generator edits. There is no single, authoritative, correct skill.

## 2. Goal / Non-goals

**Goal:** One skill — `capi-multiselect` — that is the single source of truth for converting/standardizing **any** multi-select question across F1/F3/F4, baking in the hard-won CSPro gotchas and the verify→compile→publish→device-test discipline, then driving a bounded sweep to eliminate the tester-flagged Yes/No batteries.

**Non-goals:**
- Not a replacement for the broad `capi-uat-triage` loop (that stays; it *calls* this skill for multi-select work).
- Not general form redesign beyond multi-select (section splits/merges unrelated to multi-select are out of scope; in practice `capi-form-redesign`'s only proven use is the multi-select+amounts case, which this absorbs).
- Not Option 1 (inline dynamic amounts) — see §4.

## 3. Tester-grounded requirements

The testers converged on one pattern (the same suggestion block appears verbatim across #672/#674/#675/#691/#689/#692/#693) and sketched it (image on #689/#691/#692/#693):

1. **Tick-all checkbox** — "Respondents should tick all choices that apply." Replace every Yes/No-per-option battery. (Universal.)
2. **For amount-bearing questions**, after ticking, amount boxes for the **ticked options only**, each **labeled with its item**, on **fewer pages** (their complaint: each option/amount currently gets its own page → "Q92/Q94 spans multiple pages even though it's a single question").

They offered **Option 1** (one page, amounts appear inline under ticked options) or **Option 2** (two pages: ticks → amount boxes for ticked items). **Decision: Shape B is locked to Option 2 / roster** (see §4 for the doc-grounded rationale).

## 4. CSPro/CSEntry documentation grounding

Verified against the official CSPro 8.0 User's Guide / CSEntry docs:

- **Check Box capture type (Shape A mechanism):** field must be **alphanumeric**, length = **a multiple of the max response-code length**; each value-set code renders as one checkbox; selections stored left-to-right. Our 2-char-code, length=N×2 recipe matches. — [Check Box](https://www.csprousers.org/help/CSPro/check_box.html), [Capture Types](https://www.csprousers.org/help/CSPro/capture_types.html)
- **Roster / Option 2 (Shape B mechanism):** a roster is a grid where **each row = one occurrence**; an **occurrence-control field sets the number of rows dynamically from logic** → one row per ticked item. `curocc()` + occurrence navigation are core features. Proven on Q92. — [Repeating Groups (CSEntry)](https://www.csprousers.org/help/CSEntry/repeating_groups_of_fields.html), [Change Roster Properties](https://www.csprousers.org/help/CSPro/change_roster_properties.html)
- **Option 1 (inline dynamic) — rejected, doc-grounded:** the only dynamic show/hide is `set attributes ... visible/hidden`, **deprecated as of CSPro 7.1**; its current replacement `setproperty` **dropped the visibility property** (only `HideInCaseTree` remains, which is case-tree-only, not the entry screen). Option 1 would rest on deprecated/removed functionality with undocumented on-screen behavior → not a supported standard. — [Set Attributes](https://www.csprousers.org/help/cspro/set_attributes_statement.html), [SetProperty](https://www.csprousers.org/help/CSPro/setproperty_function.html)

## 5. The skill

**Name:** `capi-multiselect` (project-scoped, `analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/.claude/skills/capi-multiselect/`).

**Entry point / when to use:** any time a question is (or should be) a multi-select — a tester-flagged Yes/No battery, a "Response Layout / Question Formatting / Lesser Page" issue, an amount-matrix that should be checkbox+amounts, or a sweep across the remaining inventory. `capi-uat-triage` routes multi-select findings here instead of hand-rolling them.

**Structure:** classify → apply the canonical recipe for the shape → run the gates → (for the sweep) pilot → device-test → fan out.

## 6. Classifier (decision tree)

Given a candidate question, read the spec/DCF and decide:

- Does each selectable option carry a **follow-up amount or sub-value**?
  - **No → Shape A** (pure multi-select / tick-all checkbox).
  - **Yes → Shape B** (multi-select + amounts → checkbox → roster).
- Edge cases the classifier must flag (not silently guess): exclusive options (None / I don't know / "regular check-up only"), "Other (specify)" options, and cross-question checks that reference the fields being renamed.

## 7. Shape A recipe — tick-all checkbox

The canonical **4-list** change, applied via one shared helper so F1/F3/F4 converge at the *code* level (not just docs):

1. **`generate_dcf.py`** — `checkbox_multiselect(base, label, value_set, with_other_txt=…)`: alpha field, length = N×2, codes `_cb_codes()` (01.. real, 99 Other, 90 exclusive None/IDK).
2. **`generate_apc.py`** — checkbox PROC: `≥1` select (hard), exclusivity soft/hard for the 90-coded (and named non-90 exclusives like the Q87 "06" / Q85 "19" patterns), preproc gate if any, `Other (specify)` text gated on `pos("99",…)`.
3. **`generate_fmf.py`** — add the base to `_CHECKBOX_FIELDS`. **F1 caveat:** F1's `.fmf` is hand-maintained (`has_fmf_gen=False`); use `fmf_checkbox_convert.py` (the form-replacement tool) — F3/F4 regenerate the form automatically.
4. **`automation/optimize_capture_types.py`** — add the base to the `CHECKBOX` set, or it silently ships single-select (data loss).

**Verify `DataCaptureType=CheckBox`** in the regenerated fmf for every converted base.

## 8. Shape B recipe — checkbox → roster (Option 2)

The proven Q92 pattern (absorbed from `capi-form-redesign` §4), per instance:

1. **`generate_dcf.py`** — replace the flat `yes_no + _AMT` matrix with ONE `checkbox_multiselect("Q<n>_SOURCES", …)`; add a roster record `Q<n>_PAY_ROSTER` (`LINE`, `SRC` select_one, `AMT` numeric, `max_occurs=len(options)`, `required=False`); split the host section around the roster (record-before / roster / record-after).
2. **`generate_apc.py`** — population proc on the LINE field (preproc): count ticked via **literal 2-char `pos("01".."NN")`** (not `edit("99",k)` — that padded-code bug caused the Q92 grid-skip), `endgroup` past the last ticked, auto-set + `protect` `Q<n>_PAY_SRC`, gate `AMT` enterability **from the LINE preproc (a visited field), never the protected AMT's own preproc** (#617 footgun: protected fields skip their preproc). Fix renamed cross-checks via a `PROC GLOBAL` function.
3. **`generate_fmf.py`** — roster engine: `Repeat=`/`Type=Record`/`Max=`, skip `_emit_blocks` for rosters, add to `_NO_AUTOGROUP_RECORDS` + `_CHECKBOX_FIELDS` + `FORM_PLAN` (roster form between the two host forms).
4. **`optimize_capture_types.py`** — add `Q<n>_SOURCES` to `CHECKBOX`.

## 9. Gates (every conversion)

In order: `python automation/verify_questions.py` → **PASS** (reads bound `.fmf`; run *after* `--build`) → Designer compile (`cspro_compile_driver.py F<n> --build --save`, read shot for "Compile Successful") → **Publish packager** (the *real* strict gate — catches `alpha<>numeric` the lenient compile misses) → for **Shape B**, **device-test on emulator/tablet** before fan-out (record-structure change). Deploy via `auto_deploy.py F<n> --deploy`. Do not commit (CSWeb deploy is git-independent).

## 10. Sweep methodology + bounded inventory

Pilot one instance per shape → device-test → fan out (do not blind-sweep Shape B). Log any question skipped.

- **Shape A (pure multi-select):** F1 **#567** (Section F Q121–134) + any remaining flagged; most of the F1/F3 batches are already converted (closed).
- **Shape B (multi-select + amounts), F3 cost matrices:** **#672** (Q92 — already a roster, keep), **#674/#675** (Q94/Q96), **#691** (Q107/Q111), **#689** (Q97.1/Q97.2/Q98), **#692** (Q109), **#693** (Q112/113/115), **#688** (Q89). Re-canonicalize **Q97.1 from 2-form-flat → roster** so all match.

## 11. Relationship to other skills

- **`capi-uat-triage`** — kept. Stops hand-rolling checkboxes; routes multi-select findings to `capi-multiselect`.
- **`cspro-compile-validate` / `cspro-auto-deploy` / `cspro-patch-fix` / `cspro-crash-recovery`** — kept; the build/compile/deploy mechanics `capi-multiselect` uses.
- **`capi-form-redesign`** — **deprecated → deleted** after `capi-multiselect` absorbs its matrix→roster recipe + the illustrate→scope→go/no-go→pilot→device-test→fan-out discipline. **Sequence: build + verify `capi-multiselect` first, then delete `capi-form-redesign`** (deleting first loses the reference implementation).

## 12. Risks / gotchas (codified into the skill)

- **Silent single-select** if the fmf `_CHECKBOX_FIELDS` or `optimize` CHECKBOX step is missed (`reference_cspro_checkbox_conversion_lists`). Always verify `DataCaptureType=CheckBox`.
- **#617 protected-preproc**: protected fields skip their preproc; gate amounts from a visited field.
- **Lenient compile vs strict publish**: the Designer compile can pass while Publish fails — Publish is the gate.
- **Stale build false-negatives**: device retests need **remove + re-add** (`project_aspsi_csentry_update_propagation`).
- **F1 hand-fmf** divergence (`has_fmf_gen=False`) — needs `fmf_checkbox_convert.py`, unlike F3/F4.
- **Padded-code bug**: use literal 2-char `pos()`, never `edit("99",k)`.

## 13. Success criteria

- `capi-multiselect` exists, is self-contained, cites the CSPro docs, and encodes both recipes + the gates + the classifier + the sweep.
- A pilot conversion (one Shape A + one Shape B) passes all gates and device-test.
- `capi-form-redesign` is deleted with no loss of capability.
- The tester-flagged Yes/No batteries are eliminated across the bounded inventory, all using the *same* shape.

## 14. Open items (carry into the plan)

- The F3 working tree currently holds an **undeployed Q97.1 2-form-flat** redesign (regenerated 17:57 today, after the 15:34 deploy, by an out-of-scope edit). The Q97.1→roster re-canonicalization **supersedes** it; reconcile the working tree as part of the sweep (and confirm no other session is editing F3 concurrently before building).
- Confirm the bounded inventory is complete (no flagged multi-select left off the list) before declaring the sweep done.
