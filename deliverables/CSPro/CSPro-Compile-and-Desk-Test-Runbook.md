---
type: deliverable
kind: runbook
audience: Carl (Data Programmer) — CSPro Designer + CSEntry on Windows
prepared_by: Carl Patrick L. Reyes
date: 2026-06-04
related_tasks: [E6-CAPI-001 (#193), E6-CAPI-002 (#194), E6-CAPI-003 (#195), E2-F3-010 (#251), E2-F4-010 (#253), E3-F1-060 (#161), E2-PLF-006 (#140)]
tags: [cspro, csentry, compile, desk-test, runbook, e6]
---

# CSPro Compile & Desk-Test Runbook — F1 / F3 / F4 (+ PLF)

The turnkey procedure to take the three generator-built instruments through **Designer compile → CSEntry desk-test → gate-issue closure**. This is the keystone that unblocks epic:testing, epic:csweb sync, and the pretest.

> **Why this is a manual step.** CSPro 8.0 is installed, but the compile lives in **Designer** (GUI) and the desk-test in **CSEntry** (GUI, interactive). The headless runners (`CSBatch`, `CSProProductionRunner`, `runpff`) all load a **`.ent` application bundle** — which Designer creates by binding the `.dcf` + `.fmf` + `.ent.apc`; the generators deliberately produce the components, not the `.ent`. So there's no honest headless compile. This runbook makes the GUI pass first-try clean.
>
> **Empirically confirmed (2026-06-04).** Tested `CSProProductionRunner.exe` against an `AppType=Entry` `.pff` over the F1 sample `.csdb` (scratch copy, 40-s timeout): it **hung with no listing output** (entry apps need the interactive engine — production-runner is for batch/tabulate/export, not entry-logic compile). `-?` also returns no console usage. So the GUI requirement is verified, not assumed — don't burn time re-attempting a headless entry compile.

---

## 0. Pre-compile state — already green (2026-06-04)

> **12-digit case-key migration (2026-06-04) — folded in.** All three dicts now key on the decomposed **`RR-PP-MMM-FF-CCC`** (5 ID items: `REGION_CODE`·`PROVINCE_HUC_CODE`·`CITY_MUNICIPALITY_CODE`·`FACILITY_NO`·`CASE_SEQ`); the single 6-digit `QUESTIONNAIRE_NO` is retired, `F3_FACILITY_ID` retired (facility = first 9 digits), `F4_PARENT_F3_CASE_SEQ` added for the F4→F3 link. Dicts re-registered in CSWeb (#235/#251/#253/#140 closed). The desk-test (§3) now also verifies the **id-block entry**.

| Check | F1 | F3 | F4 |
|---|---|---|---|
| Dictionary `.dcf` | ✅ FacilityHeadSurvey.dcf (12-digit id-block) | ✅ PatientSurvey.dcf (id-block) | ✅ HouseholdSurvey.dcf (id-block) |
| Logic `.ent.apc` | ✅ (129 PROC blocks) | ✅ (60) | ✅ (125) |
| Forms `.fmf` | ⚠️ FacilityHeadSurvey.fmf (Apr-21 Designer-refined; **Id-Items form pre-migration** — see ⚠️ below) | ⚠️ PatientSurvey.generated.fmf (skeleton; Id-Items regenerated) | ⚠️ HouseholdSurvey.generated.fmf (skeleton; Id-Items regenerated) |
| **preflight_validate.py** | ✅ ALL CLEAN | ✅ ALL CLEAN | ✅ ALL CLEAN |
| §15.E `LANGUAGE_USED` | ⚠️ not on a form (auto-set in preproc via `getlanguage()`; unplaced ≠ error) | ✅ placed | ✅ placed |
| 12-digit id-block | ⚠️ **in `.dcf` only** — `.fmf`/`.ent` still bind retired `QUESTIONNAIRE_NO`; Id-Items form **re-syncs on Designer open** (drops `QUESTIONNAIRE_NO`, places the 5 items) | ✅ | ✅ |

> ⚠️ **F1 Id-Items drift (caught 2026-06-04, verified).** `FacilityHeadSurvey.fmf` + `.ent` are **Apr-21, pre-migration**: the (Id Items) form `FORM000` places the single retired `QUESTIONNAIRE_NO`, and **none** of the 5 new id items. The `.dcf` (Jun-4) is correct (`REGION_CODE`·2 / `PROVINCE_HUC_CODE`·2 / `CITY_MUNICIPALITY_CODE`·3 / `FACILITY_NO`·2 / `CASE_SEQ`·3 = 12 digits). The (Id Items) form is **dictionary-driven**, so opening the `.ent` in Designer triggers a "dictionary changed — synchronize?" prompt that **auto-rebuilds the Id-Items form** to the 12-digit block. This is **§2 F1 Step 0** below — do it before the smoke. **Do not hand-edit the INI `.fmf`** (the IRON RULE; F1 has no FMF generator — the Id-Items form is Designer/dict-managed).

`preflight_validate.py` statically catches **3 of the 5** Designer error classes below (hardened 2026-06-04): **(1)** PROC-target / dictionary-reference drift (the documented item-name-drift class), **(2)** `setvalueset()` on a non-field working variable (the F1 Q121 trap), **(3)** user-function call-arity mismatch (against the `function` defs in the `.apc` + shared `Capture-Helpers.apc`/`PSGC-Cascade.apc`). It still does **not** catch general syntax errors, type mismatches, or value-set-code-membership — those surface on the real Designer compile and route through the fix-loop below. (Self-tested: the new lints fire on injected faults and ignore nested-paren args; all three instruments stay **ALL CLEAN**.)

---

## 1. THE IRON RULE — fix at the generator, never the artifact

When Designer reports a compile error, **do not edit the `.apc` / `.dcf` / `.fmf` by hand.** Fix the **source table in the generator** and regenerate. Hand-edits are overwritten on the next regenerate and break the single-source-of-truth.

```
Designer error  →  edit F{1,3,4}/generate_apc.py (or generate_dcf.py)
                →  python generate_dcf.py && python generate_apc.py  (+ generate_fmf.py for F3/F4)
                →  python deliverables/CSPro/preflight_validate.py   (must stay ALL CLEAN)
                →  reload in Designer → recompile
```

**Paste the verbatim Designer error to me and I turn the generator fix in this loop** — typically a one-line source-table edit + regenerate.

### Error → cause → fix cheat-sheet
| Designer says | Almost always | Fix | preflight catches? |
|---|---|---|---|
| `'QXX_FOO' is not defined` | item-name drift (logic name ≠ dcf name) | rename in the generator's source table; preflight will confirm | ✅ yes |
| `setvalueset: argument is not a field` | value-set applied to a non-field/computed item | per-option `noinput` gate instead (see F1 Q121 pattern) | ✅ yes (working-var case) |
| `skip to 'LABEL' — label not found` | skip target renamed/positional | point to the correct item code; preflight resolves PROC targets | ✅ yes |
| `function expects N arguments` | helper arity (e.g. `ReadGPSReading`) | match the helper signature in `Capture-Helpers.apc` | ✅ yes (user-defined fns) |
| value-set code not in dictionary | dcf value-set vs logic constant mismatch | align the constant to the dcf value-set | ❌ no — surfaces in Designer |

---

## 2. Per-instrument Designer compile

### F1 — Facility Head  *(closes #161 smoke + feeds #193)*
0. **Id-block re-sync (do this first — see §0 ⚠️). Exact dialog flow, observed live 2026-06-05:** Open **`FacilityHeadSurvey.ent`** in Designer. While "Checking form file FACILITYHEADSURVEY_FF" runs, a **`Rename Item`** dialog pops: *"QUESTIONNAIRE_NO not found in dictionary"* with two radios — *"Rename QUESTIONNAIRE_NO to […]"* and *"Delete QUESTIONNAIRE_NO from the form"* (**this one is pre-selected — leave it**) + a *"Delete all items not found"* checkbox (**leave unchecked** — only this one item drifts; verified 1 of 665 form fields). Click **OK** → a confirm box *"IDS0_FORM: QUESTIONNAIRE_NO deleted; not in dictionary"* → **OK**. The form then finishes loading. **Save the forms.** *(Don't hand-edit the `.fmf`.)*
   - ⚠️ **Verify the id-block is populated.** Deleting `QUESTIONNAIRE_NO` removes it from `FORM000` (`IDS0_FORM`), but I could **not** confirm in automation that Designer auto-places the 5 new id items there. **Open `FORM000` and check it shows `REGION_CODE·PROVINCE_HUC_CODE·CITY_MUNICIPALITY_CODE·FACILITY_NO·CASE_SEQ`.** If they're absent, drag them from the dictionary tree onto the (Id Items) form (they're dict id-items, so they're available), then save.
0b. **Insert the 4 PSGC external dictionaries (else the cascade won't compile).** `FacilityHeadSurvey.ent.apc` `#include`s `../shared/PSGC-Cascade.apc`, whose `onfocus` handlers `loadcase()` four external dicts. The `.ent` ships with **only the input dict**, so Designer ▸ **Add Files ▸ Dictionary** must add all four from `deliverables/CSPro/shared/`: `psgc_region.dcf`, `psgc_province.dcf`, `psgc_city.dcf`, `psgc_barangay.dcf`. Names already match the logic exactly (`PSGC_REGION_DICT`/`R_CODE`/`R_NAME`/`R_PARENT_CODE` … through barangay — verified), so no rename. **Deploy the matching `.dat` files** (`psgc_*.dat`, same folder) with the app to the tablet, or the lookups return 0 at runtime (`errmsg "PSGC region lookup failed — verify psgc_region.dat is deployed"`). *Note: `preflight_validate.py` is blind to this — the `PSGC_*_DICT` refs live in the `#include`d shared file, which preflight harvests for declarations but doesn't reference-scan. So a missing-dict error shows up only at the Designer compile.*
1. Designer → open/create **`FacilityHeadSurvey.ent`**; Input dictionary = `FacilityHeadSurvey.dcf`; Forms = **`FacilityHeadSurvey.fmf`** (Designer-refined; Id-Items re-synced per Step 0); + the 4 PSGC external dicts (Step 0b).
2. Set **`FacilityHeadSurvey.ent.apc`** as the application's main logic.
3. **Build ▸ Compile.** Work the fix-loop until clean.
4. Watch the known-risky spots: **Q121** (per-option `noinput` gates — O10/O11/O12 hospital-only, O13 PCF-only, O14 None→skip Q135), the 7 positional skip-targets, **PSGC cascade** (`onfocus`+`loadcase`+`setvalueset`, external lookup dicts must be on the path), **GPS/photo** helpers, `getlanguage()`→`LANGUAGE_USED`.

> **Step 0b applies to ALL THREE instruments.** F1, F3, and F4 all `#include "../shared/PSGC-Cascade.apc"`, so **each** application needs the **4 PSGC external dicts inserted** (Designer ▸ Add Files ▸ Dictionary: `psgc_region/province/city/barangay.dcf` from `deliverables/CSPro/shared/`) **+ the `.dat` files deployed**. F3 uses the cascade for **both** facility and patient (`P_*`) geo-ID; F4 for household geo-ID. preflight is blind to this (refs live in the `#include`d shared file) — it surfaces as `'PSGC_REGION_DICT' is not defined` at compile. *(Only F1 also needs the Id-Items Step 0; F3/F4 skeletons already carry the 12-digit id-block.)*

### F3 — Patient  *(feeds #194, #251)*
1. Create **`PatientSurvey.ent`**; Input dict = `PatientSurvey.dcf`; Forms = import **`PatientSurvey.generated.fmf`** (then Designer splits oversized sections per `F3-Form-Layout-Plan.md` — the skeleton carries item membership + tab order). **Insert the 4 PSGC dicts (Step 0b).**
2. Set **`PatientSurvey.ent.apc`** as main logic; **Compile.**
3. Risky spots: **outpatient/inpatient branching** at the eligibility screen (#164), the **case-control block in FIELD_CONTROL** (#251 verifies this), Q1 consent gate, **Q162 terminator**, **Q169 routing**.

### F4 — Household  *(feeds #195, #253)*
1. Create **`HouseholdSurvey.ent`**; Input dict = `HouseholdSurvey.dcf`; Forms = import **`HouseholdSurvey.generated.fmf`**. **Insert the 4 PSGC dicts (Step 0b).**
2. Set **`HouseholdSurvey.ent.apc`** main logic; **Compile.**
3. Riskiest of the three — **roster** (`C_HOUSEHOLD_ROSTER`, one member per row), **per-member sub-loop**, **cross-member rules** (one head; spouse implies head), **max-roster soft warning**, **WHO expenditure grid** (Section N flat batteries), **bill-recall chain**, **Q129 Section-M gate**.

### PLF — listing apps  *(closes #140)*
- The PLF is the **F3/F4 listing apps** (`PickPatient()` / `PickHousehold()`). Designer-validate + publish; record the sign-off note on #140.

---

## 3. Desk-test scenarios (CSEntry) → what each closes

Run on a Windows CSEntry build. For each instrument, walk the happy path **and** the targeted scenarios; capture pass/fail + a screenshot per scenario (drop into the issue).

### F1 — #193 (desk test) + #161 (smoke)
- [ ] **Case-key id-block:** the 5 ID items (`REGION_CODE`·`PROVINCE_HUC_CODE`·`CITY_MUNICIPALITY_CODE`·`FACILITY_NO`·`CASE_SEQ`) prompt/accept in order and compose the 12-digit `RR-PP-MMM-FF-CCC` case key; no leftover `QUESTIONNAIRE_NO` field.
- [ ] **Smoke (closes #161):** cover page → every section → last question → save, happy path, no dead-ends.
- [ ] Consent **refuse** → disposition recorded + `endlevel` (interview ends cleanly).
- [ ] **Eligibility** gate blocks ineligible before main questionnaire loads.
- [ ] Age **< 18** → hard block + reenter.
- [ ] **Q121** option behavior: hospital-only options gated; O14 "None" → skips Q135.
- [ ] **PSGC cascade**: region→province→city→barangay narrows correctly.
- [ ] **GPS** captured at start; **verification photo** taken; **AAPOR** disposition set.
- [ ] **Language switch** mid-form → `LANGUAGE_USED` records the active language.

### F3 — #194 (full A–L) + #251 (Designer validation)
- [ ] Full **A–L** walkthrough, sane data, reaches end.
- [ ] **OP vs IP branching** (#164) routes to the correct block at eligibility.
- [ ] **Case-control block in FIELD_CONTROL** correct (#251 sign-off).
- [ ] Q1 consent gate; **Q162 terminator** ends where intended; **Q169 routing** lands correctly.

### F4 — #195 (full A–Q) + #253 (Designer validation)
- [ ] Full **A–Q** walkthrough including the roster.
- [ ] **Roster**: add / edit / remove / reorder members; per-member sub-loop fires on the right conditions.
- [ ] **Cross-member**: only one household head; spouse implies a head exists.
- [ ] **Max-roster** soft warning at unusual sizes.
- [ ] **WHO expenditure grid** (Section N) accepts the PHP batteries; **catastrophic-expenditure** logic sane.
- [ ] **Bill-recall chain** flows; **interval-sampling** sanity (#195).

---

## 4. Gate-issue closure map

| Issue | Closes when | Evidence to attach |
|---|---|---|
| **#161** F1 CSEntry smoke | happy path cover→last question passes | screenshot of final save |
| **#193** F1 desk test | §3 F1 scenarios pass | per-scenario pass/fail + shots |
| **#194** F3 desk test | §3 F3 scenarios pass | A–L walkthrough notes |
| **#195** F4 desk test | §3 F4 scenarios pass | roster + Section N shots |
| **#251** F3 Designer validation | FIELD_CONTROL case-control block verified; full item walkthrough | sign-off note |
| **#253** F4 Designer validation | same scope as F3 | sign-off note |
| **#140** PLF Designer validation | listing apps validated + published | sign-off note |

> When a desk-test surfaces a **logic defect**, it routes to the generator fix-loop (§1) — and the related Epic-3 build issue does **not** reopen; the fix-batch is tracked via the pretest-debrief issue **#199**.

---

## 5. What unblocks next (the cascade)

Once these close: **#196** sync round-trip needs the compiled `.pen` packages → **CSWeb #235/#237** per-survey upload + sync config → **#198/#199** pretest → **#190** F2 pilot. The whole right-hand side of the board keys off this compile.

**I'm standing by for compile errors** — paste any Designer message verbatim and I'll turn the generator fix in the §1 loop (usually a one-line source edit + regenerate + preflight).
