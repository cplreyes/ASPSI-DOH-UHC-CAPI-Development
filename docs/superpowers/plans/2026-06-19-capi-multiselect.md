# capi-multiselect Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the project-scoped `capi-multiselect` skill, prove it with one Shape A and one Shape B pilot through all gates incl. device-test, fan out across the bounded tester inventory, then retire `capi-form-redesign`.

**Architecture:** A single skill is the source of truth for multi-select conversions: it classifies a question (pure multi-select → **Shape A** tick-all Check Box; multi-select + amounts → **Shape B** Check Box → roster, the doc-grounded Option 2), then applies one canonical recipe per shape and runs verify→Designer-compile→Publish→device-test. Conversions edit the `generate_*.py` generators (never the generated `.dcf/.apc/.fmf/.qsf`) and deploy to CSWeb from the working tree.

**Tech Stack:** CSPro 8.0 Designer + CSEntry; Python generators in `deliverables/CSPro/F{1,3,4}/`; pywinauto GUI drivers in `deliverables/CSPro/automation/`; CSWeb at `csweb.asiansocial.org`.

## Global Constraints

- **No git commits from me.** Leave all changes in the working tree; Carl commits/pushes manually (`feedback_no_git`). Every task ends in the working tree, not a commit.
- **Never hand-edit `.dcf`/`.apc`/`.fmf`/`.qsf`.** Edit the `generate_*.py` and regenerate.
- **CSWeb deploy is serialized + GUI-stateful:** one CSPro Designer at a time; after editing generators always rebuild with a FRESH Designer (`--build --save`, never `--save`-only onto a stale Designer); **never close "CSPro Deploy Application" dialogs** (Carl pre-opens/parks them); the **Publish packager is the real strict gate** (lenient compile can pass while Publish fails).
- **Gates, in order, every conversion:** `verify_questions.py` PASS → Designer compile "Compile Successful" → Publish opens the deploy dialog → (Shape B) device-test before fan-out.
- **Verify `DataCaptureType=CheckBox`** in the regenerated `.fmf` for every converted base (miss the fmf/optimize step → silent single-select data loss).
- **Use literal 2-char `pos("01".."NN")`** for checkbox membership — never `edit("99",k)` (padded-code bug → Q92 grid-skip).
- **Gate amounts from a VISITED field's preproc** (the roster LINE field), never the protected AMT field's own preproc (#617: protected fields skip their preproc).
- **F1 `.fmf` is hand-maintained** (`has_fmf_gen=False`) → use `F1/fmf_checkbox_convert.py`; F3/F4 regenerate forms via `generate_fmf.py`.
- **Device retest = remove + re-add** the app in CSEntry (the ⋮ Update is unreliable; `project_aspsi_csentry_update_propagation`).
- **Repo:** `C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development`. Run Python with `PYTHONIOENCODING=utf-8`.

---

### Task 1: Author the `capi-multiselect` skill

**Files:**
- Create: `.claude/skills/capi-multiselect/SKILL.md`
- Read (to absorb): `.claude/skills/capi-form-redesign/SKILL.md` (recipe §1–6), the spec `docs/superpowers/specs/2026-06-19-capi-multiselect-skill-design.md`

**Interfaces:**
- Produces: the canonical recipe that Tasks 3/5/7 follow and that `capi-uat-triage` will route to.

- [ ] **Step 1: Write the frontmatter** (verbatim):

```yaml
---
name: capi-multiselect
description: Use when converting or standardizing ANY multi-select question on the ASPSI-DOH F1/F3/F4 CSPro/CSEntry instruments — a tester-flagged Yes/No-per-option battery that should be tick-all ("Response Layout", "Question Formatting", "Lesser Page for each Item"), an amount-matrix that should become checkbox + amounts, or a sweep across the remaining inventory. Classifies the question (pure multi-select vs multi-select+amounts), applies the one canonical recipe per shape (Shape A = tick-all Check Box; Shape B = Check Box → roster, Option 2), runs verify→compile→publish→device-test gates, then pilots-then-fans-out. Replaces the ad-hoc checkbox handling in capi-uat-triage and the matrix→roster recipe formerly in capi-form-redesign. Trigger on "fix multiselect", "convert to checkbox/tick-all", "Response Layout", "should be select-all", or a named Yes/No battery.
---
```

- [ ] **Step 2: Write the body sections** (derive prose from the spec; absorb `capi-form-redesign` §1–6 for Shape B):
  1. **When to use / classifier** — the decision tree from spec §6 (amount per option? No→Shape A; Yes→Shape B) + the edge-case flags (exclusive None/IDK, Other-specify, cross-question checks on renamed fields).
  2. **Shape A recipe** — the 4-list from spec §7 (dcf `checkbox_multiselect` alpha N×2 codes; apc checkbox PROC with ≥1, exclusivity for 90-coded + named non-90 like Q87"06"/Q85"19", Other gate on `pos("99")`; fmf `_CHECKBOX_FIELDS` with the **F1 hand-fmf via `fmf_checkbox_convert.py`** caveat; `optimize_capture_types.py` CHECKBOX set). End with "verify `DataCaptureType=CheckBox`".
  3. **Shape B recipe** — the checkbox→roster steps from spec §8 + `capi-form-redesign` §4 (record-type letter pick; dcf roster builder + section split; apc population proc on LINE with literal `pos`, `endgroup`, `protect`, gate-from-LINE-preproc; PROC GLOBAL for renamed cross-checks; fmf roster engine; optimize). Include the ASCII tablet mockup (page 1 checkbox → page 2 roster) from `capi-form-redesign` §1.
  4. **Gates** — spec §9 verbatim (verify→compile→publish→device-test; the publish-is-the-real-gate gotcha; `auto_deploy`; no commit).
  5. **Sweep discipline** — spec §10 (pilot one per shape → device-test → fan out; log skips) + `capi-form-redesign` §3 go/no-go and §5 device-test checklist.
  6. **Gotchas** — spec §12 bullets (silent single-select, #617 protected-preproc, lenient-compile-vs-publish, stale-build remove+re-add, F1 hand-fmf, padded-code).
  7. **Doc citations** — the six CSPro/CSEntry URLs from spec §4.

- [ ] **Step 3: Self-check against the spec** (no code run). Confirm the SKILL.md covers spec §5–§12, the frontmatter triggers correctly, and the two recipes are complete enough to execute Tasks 3 and 5 without re-deciding anything. Fix gaps inline.

- [ ] **Step 4: Confirm the skill is discoverable.** Verify the file path is `.claude/skills/capi-multiselect/SKILL.md` and the frontmatter `name:` matches the directory. (Skill list refresh happens at session start; note it for Carl.)

- [ ] **Step 5: Leave in working tree** (no commit). Note for Carl: new skill authored, not committed.

---

### Task 2: Pre-flight — reconcile the F3 working tree to a clean baseline

**Files:**
- Inspect: `deliverables/CSPro/F3/generate_apc.py`, `generate_dcf.py`, generated `.dcf/.apc/.fmf`; `git status`

**Interfaces:**
- Produces: a known-good F3 baseline (deployed state) so the Shape B pilot starts clean.

- [ ] **Step 1: Snapshot current divergence.** Run:

```bash
cd "<repo>" && git status --short -- deliverables/CSPro/F3
git diff --stat -- deliverables/CSPro/F3/generate_apc.py deliverables/CSPro/F3/generate_dcf.py
```
Expected: shows the uncommitted Q92/Q87/#714 (deployed) changes **plus** the undeployed Q97.1 2-form-flat (`Q971_PROCS`, regenerated 17:57).

- [ ] **Step 2: Confirm no concurrent editor.** Check mtimes of `F3/generate_apc.py` and the generated files; confirm they are not advancing (no other session regenerating). If they are, STOP and surface to Carl.

```bash
ls --time-style=+%H:%M:%S -l deliverables/CSPro/F3/generate_apc.py deliverables/CSPro/F3/PatientSurvey.ent.apc
```

- [ ] **Step 3: Revert ONLY the undeployed Q97.1 2-form-flat** so the pilot re-builds it as a roster from the deployed baseline. Remove the `Q971_PROCS` block + the Q971 dcf section added at 17:57 (the 2-form-flat), keeping the deployed Q92/Q87/#714 changes intact. (Surgical: revert the Q971-specific hunks, not the whole file.)

- [ ] **Step 4: Verify the baseline.** Run:

```bash
PYTHONIOENCODING=utf-8 python deliverables/CSPro/automation/verify_questions.py
```
Expected: `[F3] … PASS` and no `Q971_SOURCES` in the regenerated apc/fmf (back to deployed state).

- [ ] **Step 5: Leave in working tree** (no commit). Report the reconciled baseline to Carl.

---

### Task 3: Pilot Shape A — F1 #567 (Q121–Q134) → tick-all Check Box

**Files:**
- Modify: `deliverables/CSPro/F1/generate_dcf.py`, `deliverables/CSPro/F1/generate_apc.py`, `deliverables/CSPro/F1/fmf_checkbox_convert.py`, `deliverables/CSPro/automation/optimize_capture_types.py`

**Interfaces:**
- Consumes: the Shape A recipe (Task 1 SKILL.md §Shape A).
- Produces: Q121–Q134 as one (or the spec'd grouping of) Check Box base(s) with the Q121→Q122–134 gating preserved.

- [ ] **Step 1: Read the issue + current code.** `gh issue view 567`; read the current Q121–Q134 definition in `F1/generate_dcf.py` and the existing why-difficult gating in `F1/generate_apc.py`. Confirm on paper: Q121 selection should gate which of Q122–Q134 appear (per #567 point 2).

- [ ] **Step 2: Apply the Shape A dcf change.** Convert the Q121–Q134 Yes/No battery to `checkbox_multiselect(...)` per the recipe (alpha, length N×2, `_cb_codes`).

- [ ] **Step 3: Apply the Shape A apc change.** Add the checkbox PROC (≥1 select, Other/exclusive as applicable) and **re-express the Q121→Q122–134 gating as `pos()` membership on the checkbox field** (not Yes/No-per-option).

- [ ] **Step 4: Apply the F1 fmf change.** Run `F1/fmf_checkbox_convert.py` to swap the option-group fields → the Check Box field(s) in the hand-maintained `.fmf` (both `[Field]/[Text]` and the `[Group]` membership manifest). Add the base(s) to `optimize_capture_types.py` CHECKBOX set.

- [ ] **Step 5: Verify (gate 1).** Run:

```bash
PYTHONIOENCODING=utf-8 python deliverables/CSPro/automation/verify_questions.py
```
Expected: `[F1] … reachable N/N … PASS`. Then confirm `DataCaptureType=CheckBox` on the new base(s):

```bash
grep -A8 "Name=Q121" deliverables/CSPro/F1/FacilityHeadSurvey.fmf | grep DataCaptureType
```
Expected: `DataCaptureType=CheckBox`.

- [ ] **Step 6: Diff-check.** `git diff -- deliverables/CSPro/F1/generate_dcf.py deliverables/CSPro/F1/generate_apc.py` — confirm ONLY the Q121–Q134 PROCs/fields changed.

- [ ] **Step 7: Leave in working tree** (no commit).

---

### Task 4: Compile + deploy F1 pilot, then DEVICE-TEST gate (STOP)

**Files:** `deliverables/CSPro/automation/{cspro_compile_driver,csweb_deploy_designer,auto_deploy}.py`

- [ ] **Step 1: Fresh rebuild + compile (gate 2).**

```bash
PYTHONIOENCODING=utf-8 python deliverables/CSPro/automation/cspro_compile_driver.py F1 --build --save
```
Read `automation/shots/F1_compile.png`. Expected: "Compile Successful".

- [ ] **Step 2: Publish (gate 3 — the real gate).** Launch Designer publish, File→Publish and Deploy (single-process Alt+F + click), confirm the "CSPro Deploy Application" dialog opens (Package=FacilityHeadSurvey). If "Compile Failed" modal appears, screenshot the Compiler Output pane and fix the generator.

- [ ] **Step 3: Deploy.**

```bash
PYTHONIOENCODING=utf-8 python deliverables/CSPro/automation/auto_deploy.py F1 --deploy
```
Confirm "Application Deployed Successfully" (restore the parked dialog + screenshot if the upload outran the driver window). Never close the deploy dialog.

- [ ] **Step 4: Hand Carl the device-test checklist (STOP — gate 4).** Remove + re-add FacilityHeadSurvey from CSWeb → fresh case → Section F: Q121–Q134 render as one tick-all checkbox; ticking options in Q121 still gates which appear in Q122–Q134; data stored correctly. **Do not proceed to fan-out until Carl confirms.**

- [ ] **Step 5: Leave in working tree** (no commit). Update #567 per `capi-uat-triage` notify/close once device-confirmed.

---

### Task 5: Pilot Shape B — F3 Q97.1 → Check Box + roster (Option 2)

**Files:**
- Modify: `deliverables/CSPro/F3/generate_dcf.py`, `deliverables/CSPro/F3/generate_apc.py`, `deliverables/CSPro/F3/generate_fmf.py`, `deliverables/CSPro/automation/optimize_capture_types.py`

**Interfaces:**
- Consumes: the Shape B recipe (Task 1 SKILL.md §Shape B); the reconciled F3 baseline (Task 2).
- Produces: `Q971_SOURCES` Check Box + `Q971_ROSTER` repeating record (1 labeled row per ticked item), matching the Q92 canonical pattern.

- [ ] **Step 1: Pick a free record-type letter.** `grep -o '"recordType": *"[^"]*"' deliverables/CSPro/F3/*.dcf | sort -u` → choose an unused letter for the Q97.1 roster.

- [ ] **Step 2: dcf change.** Replace the Q97.1 matrix with ONE `checkbox_multiselect("Q971_SOURCES", …)` + a roster builder `record("Q971_ROSTER", …, [LINE, SRC, AMT], max_occurs=#categories, required=False)`; split the host section around the roster.

- [ ] **Step 3: apc change.** Add `Q971_ROSTER_PROCS`: population proc on the LINE field (literal `pos("01".."0N")` count, `endgroup` past last ticked, auto-set + `protect` SRC, gate AMT enterability **from the LINE preproc**); seed `Q971_*` into `covered`; re-express any Q97.1 cross-check via a `PROC GLOBAL` function.

- [ ] **Step 4: fmf + optimize.** Confirm `generate_fmf.py` emits the roster (the F3 roster engine was ported for Q92 — reuse it); add `Q971_SOURCES` to `_CHECKBOX_FIELDS` and the roster to `_NO_AUTOGROUP_RECORDS` + `FORM_PLAN`; add `Q971_SOURCES` to `optimize_capture_types.py` CHECKBOX.

- [ ] **Step 5: Verify (gate 1).**

```bash
PYTHONIOENCODING=utf-8 python deliverables/CSPro/automation/verify_questions.py
```
Expected: `[F3] … PASS`. Confirm the roster form exists:

```bash
grep -nE "Name=Q971_ROSTER" deliverables/CSPro/F3/PatientSurvey.fmf
```

- [ ] **Step 6: Diff-check.** Confirm only Q97.1 (Q971) PROCs/records changed.

- [ ] **Step 7: Leave in working tree** (no commit).

---

### Task 6: Compile + deploy F3 Q97.1 pilot, then DEVICE-TEST gate (STOP)

- [ ] **Step 1: Fresh rebuild + compile (gate 2).**

```bash
PYTHONIOENCODING=utf-8 python deliverables/CSPro/automation/cspro_compile_driver.py F3 --build --save
```
Read shot. Expected: "Compile Successful"; form tree shows `Q971_ROSTER_FORM` between the two host forms.

- [ ] **Step 2: Publish (gate 3).** File→Publish and Deploy → "CSPro Deploy Application" (Package=PatientSurvey). On "Compile Failed", fix the PROC GLOBAL / generator.

- [ ] **Step 3: Deploy.** `auto_deploy.py F3 --deploy` → confirm "Application Deployed Successfully"; re-park dialog.

- [ ] **Step 4: Device-test checklist (STOP — gate 4).** Remove + re-add PatientSurvey → fresh case → Q97.1: page 1 tick-all checkbox; page 2 shows exactly one labeled amount row per ticked item; amounts enterable; back-nav changes selection → roster re-populates; 0-ticked edge doesn't hang. **Do not fan out until Carl confirms.**

- [ ] **Step 5: Leave in working tree** (no commit). Update #689 (Q97.1 portion) per `capi-uat-triage` once device-confirmed.

---

### Task 7: Fan out Shape B across the F3 cost-matrix cluster

**Files:** `deliverables/CSPro/F3/generate_{dcf,apc,fmf}.py`, `automation/optimize_capture_types.py`

**Precondition:** Tasks 4 and 6 device-confirmed by Carl.

- [ ] **Step 1: Confirm Q92 already matches canonical.** Verify the deployed Q92 roster matches the Shape B recipe; if it diverges, note it (no rework unless needed).

- [ ] **Step 2: Convert each remaining matrix, one at a time**, applying the Shape B recipe (read the question's current matrix → checkbox→roster). For each: `verify_questions` PASS + roster form present + diff-check before moving on. Questions:
  - Q94, Q96 (#674/#675)
  - Q107, Q111 (#691)
  - Q97.2, Q98 (remainder of #689)
  - Q109 (#692)
  - Q112, Q113, Q115 (#693)
  - Q89 (#688)
  Log any question intentionally skipped (silent truncation reads as "done").

- [ ] **Step 3: Batch rebuild + compile + deploy F3** once the cluster is converted (`--build --save`, publish, `auto_deploy F3 --deploy`).

- [ ] **Step 4: Device spot-check** a representative converted question (remove + re-add).

- [ ] **Step 5: Notify + close** each issue via `capi-uat-triage` §4–5 (GitHub comment + close; Slack patch note when the connector is back). Leave in working tree (no commit).

---

### Task 8: Retire `capi-form-redesign`

**Precondition:** `capi-multiselect` authored (Task 1) AND both pilots verified + device-confirmed (Tasks 4, 6) — proving the absorbed recipe works.

**Files:**
- Delete: `.claude/skills/capi-form-redesign/SKILL.md` (and its directory)
- Modify: `.claude/skills/capi-uat-triage/SKILL.md` (if it references `capi-form-redesign`, repoint to `capi-multiselect`)
- Update memory: `reference_capi_form_redesign_skill.md` → rewrite to point at `capi-multiselect` (or delete + replace), and the `MEMORY.md` pointer line.

- [ ] **Step 1: Grep for references.** `grep -rl "capi-form-redesign" .claude/ ` and in the memory dir. List every reference.

- [ ] **Step 2: Repoint references** to `capi-multiselect` (capi-uat-triage routing note; any cross-links).

- [ ] **Step 3: Delete the skill directory** `.claude/skills/capi-form-redesign/`.

- [ ] **Step 4: Update memory** — rewrite `reference_capi_form_redesign_skill.md` to describe `capi-multiselect` (or replace it with a new `reference_capi_multiselect_skill.md` + update `MEMORY.md`). Note Shape B = roster (Option 2) is doc-grounded.

- [ ] **Step 5: Confirm no dangling references** (`grep -rl "capi-form-redesign"` returns nothing). Leave in working tree (no commit).

---

## Self-Review

**Spec coverage:** §5 skill → Task 1; §6 classifier → Task 1; §7 Shape A → Tasks 1, 3; §8 Shape B → Tasks 1, 5; §9 gates → Tasks 4, 6 (and embedded in 3/5/7); §10 sweep/inventory → Tasks 3, 5, 7; §11 relationships + §13 deletion → Task 8; §12 gotchas → Task 1 (codified) + Global Constraints; §14 open items (Q97.1 working-tree reconcile, concurrent-edit check) → Task 2. All covered.

**Placeholder scan:** Generic `Q<n>`/`N×2` are intentional recipe templates, not gaps. Per-question line edits in Tasks 3/5/7 are deliberately recipe-driven (the canonical edit lives in the Task 1 skill; duplicating it per question would violate DRY and require code I can only read at execution). Gates and commands are exact.

**Type/name consistency:** `Q971_SOURCES` / `Q971_ROSTER` (Task 5) match the field-naming used in Tasks 6–7; the four-list step names (dcf `checkbox_multiselect`, apc PROC, fmf `_CHECKBOX_FIELDS`, `optimize_capture_types.py` CHECKBOX) are consistent across Tasks 1, 3, 5, 7.

**Note on TDD/commits:** This plan's "test cycle" is the CSPro gate chain (verify_questions → compile → publish → device-test), not pytest, because the deliverables are a skill doc + generator-driven CSPro artifacts. Per Global Constraints there are no commit steps — Carl commits manually.
