# Aug-21 Translations — Design

**Date:** 2026-08-25 · **Status:** Approved by Carl (design presented in chat, "Approve — write the spec")
**Drives:** bringing all four CAPI instruments (CSPro F1/F3/F4 + F2 PWA) up to ASPSI's **revised
Deliverable 2 (Aug-21)** — the 28 translated questionnaires (7 languages × 4 instruments) plus the
Aug-21 English masters they are keyed to — on top of the Aug-17-aligned builds that went live
2026-08-19/20. Companion diagram: `deliverables/CSPro/Translations-Aug21-Options-2026-08-25.png`
(+ `.excalidraw`).

## Decision log (all Carl, 2026-08-25)

| # | Decision | Ruling |
|---|---|---|
| 1 | Scope | **Aug-21 questionnaire text** (questions, options, notes/directives, consent) **with the English re-alignment** F1/F3/F4 need to match the Aug-21 paper. **Runtime error/validation messages stay English** — the PDFs carry no source for them (F1 200 · F3 236 · F4 154 CAPI-only strings). |
| 2 | Conflicts | **Aug-21 wins** wherever it differs from a value already in the maps (June-5 import or Aug-14/17 hand repairs), **except a tracked override list** — keys where Aug-21 still carries a defect we already fixed are kept, each with a written reason. Nothing is protected silently. |
| 3 | Sequencing | **Option A — per-instrument waves**: tooling once, then **F1 → F2 → F4 → F3**, each wave = align EN → import Aug-21 → build → verify → deploy → patch note. (B "one coordinated release" and C "translations first, align later" rejected — see the diagram.) |
| 4 | Versions | F1 **4.1.0** (live 4.0.0) · F2 spec **2026-08-2x-m4** (live m3) · F4 **3.2.0** (live 3.1.4) · F3 **6.1.0** (live 6.0.3; minor — *corrected 2026-08-25 evening: the four bill-detail sub-items already exist in the build, so no data-shape change*). PSA submission set stays frozen at `capi-psa-2026-08-20`; everything here ships on the DEV channel. |

## Why now

- ASPSI submitted the revised Deliverable 2 to DOH on **2026-08-21** (Aidan, thread "ASPSI DOH UHC
  Survey Yr 2_Deliverable 2 Submission", Carl cc'd). It sat unnoticed until 2026-08-25.
- The live builds carry the **June-5** cleared translations, re-keyed onto the Aug-17 English on
  Aug 17–19; every item DOH reworded fell back to English. Measured 2026-08-25 (label arrays
  translated, generator denominator): F1 62–67 %, F3 43–61 % (HIL 43), F4 50–66 % (HIL 50),
  F2 75–80 % of 707 label objects.
- Training week is **Sept 07**; the whole design fits one sprint (≈4–5 working days).

## Scope

**In:** the 28 Aug-21 translated PDFs and 4 Aug-21 English PDFs; English alignment of F1/F3/F4 to
the Aug-21 paper (F2's Aug-24 English already matches the build); the extractor/merge tooling
changes that make the import repeatable; notes-layer and consent text from the same PDFs;
rebuild, verification, deployment and patch notes per instrument; evidence set; coverage
re-measurement; a consolidated status Carl can forward to ASPSI.

**Out (non-goals):** runtime error/validation messages (Decision 1); F2 chrome strings beyond the
consent screen; any English change that is not on the Aug-21 paper; DOH comms (Carl builds, ASPSI
communicates); purging or migrating collected data (no data-shape change in this build); the F3
115.x Shape-B conversion (open item).

## Source documents

- `raw/Survey-Instruments-2026-08-21/English/F{1..4}-English_…_Aug21.pdf` — Aug-21 English masters
  (F2's file was re-modified 2026-08-24; it matches the current build).
- `raw/Survey-Instruments-2026-08-21/Translations/F{1..4}-{Bicolano,Bisaya,Cebuano,Hiligaynon,
  Ilocano,Tagalog,Waray}_…_Aug21.pdf` — 28 bilingual PDFs, all text-extractable (PyMuPDF), stamped
  `ICF ver.07/25/2026 | Translated Questionnaire ver.08/21/2026`. F2-Bicolano uses an inline
  "English line / Bicolano line" layout; the others print translation under each English row.
- `raw/Survey-Instruments-2026-08-21/drive-ids.json` — Drive file ids (folder `[B] Revised_Del
  2_Aug21`, owner Aidan). `raw/` is gitignored (FOR-DOH-ONLY provenance).
- Baseline comparison: `deliverables/CSPro/F{1,3,4}/*.dcf` labels and
  `deliverables/F2/PWA/app/src/generated/items.ts` vs the Aug-21 English (2026-08-25 run, results
  in the job workspace; the plan re-runs it as Task 0).

## What the Aug-21 English changes (verified 2026-08-25)

| Instrument | Delta vs the build | Kind |
|---|---|---|
| F1 | Q75 stem reworded ("maximum per capita rate **amount** … is **at** Php 1,700") | wording |
| F2 | none (Aug-24 English = build) | — |
| F4 | Q30 roster name caption, Q35/Q36 disability wording, Q40 "education **completed**" (reverses the earlier tester ruling #608 "attended/reached" — the DOH-submitted paper wins; say so in the patch note), Q67 pharmacy-travel stem, printed gates on Q117/Q118/Q131/Q135; Q2 month+year and Q2.1 age **already in the build** | wording |
| F3 | Q47 stem ("packages for the following health services:" — the four per-service items already exist), Q69, Q94/Q96/Q98 stems; facility-name fills in Q66/Q88 **already wired** (`_pipe_fills` → `~~FACILITY_NAME~~`) but the dcf-side neutral placeholder map lacks HIL/ILO; **97.1/97.2/115.1/115.2 already exist** (`Q971_*`/`Q972_*` Shape B; `Q1141_*`/`Q1142_*` flat Yes/No + amount matrix) — labels re-synced only | wording (+ one locale gap) |

**F3 bill-detail sub-items (paper text; already in the build — verified against `F3/generate_dcf.py` 2026-08-25 evening, see Architecture):**
- **97.1** "Other than the expenses above … which of the following were also included in the bill?
  How much were you charged or billed?" — select all: Doctor's Professional Fee · Medical equipment
  or supplies · Non-medical expenses (e.g. Hygiene kit) · Other expenses · **None**; amount per
  ticked option.
- **97.2** "Did you pay for any other expenses during your OPD visit that were NOT included in the
  outpatient bill?" — Yes → amounts for a) Doctor's Professional Fee, b) Diagnostic or laboratory
  procedure, c) Medical equipment or supplies, d) Medicines or drugs, e) Non-medical expenses:
  travel, f) Other expenses; **No** (did not pay for any other expenses).
- **115.1** inpatient twin of 97.1 with six options: Doctor's Professional Fee · Medical equipment
  or supplies · Non-medical expenses · Diagnostic or laboratory procedure inside the facility ·
  Medicines or drugs inside the facility · Other expenses · **None**.
- **115.2** "Did you pay for any other expenses during your confinement that were not included in
  the hospital bill?" — Yes → amounts for Medical equipment or supplies bought outside the facility ·
  Payment made directly to doctor/s and their secretary · Food · Transportation · Donation to the
  facility · Allowance for caregiver · Other (specify); **No**.

## Architecture

### The one constraint that shapes everything

The paper extractor anchors on the **build's** English (each `walk_labeled_nodes()` node's EN text).
An item's translation can only be recovered from the PDF once that item's English matches the
Aug-21 paper. Therefore, inside every wave, **English alignment precedes extraction**; and the
tooling must anchor on the *current* dcf/items, never on a cached label list.

### Day 0 — tooling (once)

| Component | Change | Where |
|---|---|---|
| Paper extractor | `anchor_extract.py` gains `--source DIR --instrument F<n> --dcf PATH --out DIR` (today: hardcoded June-5 folder + three dcf paths) and emits **name-scoped keys directly** (`item:` / `vs:` / `val:`), by anchoring on `cspro_helpers.walk_labeled_nodes()` (key, EN text) pairs. Existing QA flags (`is-other-label`, `digit-mismatch`, `table-bleed`, …) stay; output = `{loc}.json` (clean) + `{loc}_flagged.json` + `QA-REPORT.md`. | script committed at `deliverables/CSPro/data/translations-official/anchor_extract.py`; data output stays gitignored |
| Merge (Decision 2) | New `apply_aug21.py` beside `apply_safe.py`: for each extracted pair — if key absent → write; if present and equal → `already_same`; if present and different → **replace**, unless the key is listed in `aug21-overrides.json` → keep + count as `override`. Writes `_meta.sources.aug21 = {date, file, n_written, n_replaced, n_overridden}`. `--dry-run` default, `--apply` to write, `--only F<n>`. Report per instrument × locale. | `deliverables/CSPro/data/translations-official/` |
| Overrides | `aug21-overrides.json`: `{ "F3": { "val:Q5_SEX_VS1:1": { "keep": "…", "reason": "Aug-21 PDF still swaps Male/Female (June-5 defect carried)" } } }`. Seeded from the Aug-14/17 repair lists (`remediate_scan.py` output, `FINDINGS.md`) — only entries the Aug-21 extract *actually* re-introduces are added, during each wave's merge dry-run. | same |
| Gates (unchanged) | `scan_poisoned_keys.py` (DOUBLED / SELF_ECHO / IS_OTHER_EN / EN_FRAGMENT / WRONG_Q_CLEARED / GLUED_CLEARED / STALE_KEY) and `aug17-tools/bridge_check.py --check` run after every merge; both must be clean before regeneration. | `data/translations-official/` + `aug17-tools/` |
| Notes layer | `extract_notes.py` today reads pre-dumped text under `data/translations-official/text/` (no PDF input). It gains `--source DIR` (PDF → text via PyMuPDF into a `text-aug21/` dump) and `--provenance aug21`; `notes.json` gains an `aug21` provenance block; same Aug-21-wins rule keyed on the full English string. | same |
| Consent / ICF | `deliverables/CSPro/icf_content.py` today holds the consent paragraphs as **English-only constants** (`SCREENS['F1'|'F3'|'F4']`, `CONTINUE_OPTIONS`) consumed by `F{1,3,4}/generate_qsf.py`. It gains a per-language layer: `data/translations-official/icf.json` `{F<n>: {paragraph_key: {EN, FIL, …}}}` filled by the extractor from the PDFs' ICF pages (anchor set = the English paragraphs), plus `icf_content.screens_for(inst, lang)` with English fallback; `generate_qsf.py` emits the consent screen per language through it. | `deliverables/CSPro/icf_content.py` + `data/translations-official/icf.json` |
| F2 apply | New committed `deliverables/F2/PWA/app/scripts/apply-paper-translations.py`: input = the F2 extractor output (English-text-keyed, since the PWA store is flat English-keyed), join = **exact English string** against `spec/F2-Spec.md`'s section titles, item labels, help, choice labels, sub-field labels (the same set `applyTranslations()` covers); Aug-21-wins + `aug21-overrides.json` (F2 section); writes `spec/translations/{loc}.json`; report. Question-number joins are **not** used (the 2026-08-13 row-misalignment scar). | F2 PWA |

### Waves (Decision 3)

| Wave | Instrument | English alignment (generator edits) | Import | Build + gates | Ship |
|---|---|---|---|---|---|
| 1 | **F1 → 4.1.0** | Q75 stem in `generate_dcf.py` | 7 PDFs → maps | `generate_dcf.py` (prints per-locale %), `verify_questions.py`, fresh-Designer compile (`cspro-compile-validate`), emulator locale shots | publish → `auto_deploy.py F1`; #f1-uat patch note |
| 2 | **F2 → m4** | none | 7 PDFs → `spec/translations` | `npm run generate` (byte-diff = translations only), `tsc -b --force`, vitest, `locale-shots.spec.ts`, `audit-translations.py` | `deploy-f2-pwa.ps1`; #f2-pwa-uat note |
| 3 | **F4 → 3.2.0** | Q30/Q35/Q36/Q40/Q67 labels; Q117/Q118/Q131/Q135 printed gates as qsf help text | 7 PDFs → maps | as wave 1 | as wave 1; #f4-uat |
| 4 | **F3 → 6.1.0** | Q47/Q69/Q94/Q96/Q98 stems; 97.1/97.2/115.1/115.2 label + option text re-synced to the paper; `_FACILITY_NEUTRAL` gains HIL/ILO | 7 PDFs → maps | as wave 1 + `skip_boundary_check.py F3` + a desk scenario through 97.1/97.2/115.1/115.2 in one non-English locale | as wave 1; #f3-uat (minor: remove + re-add; codes unchanged) |
| 5 | close | — | — | coverage re-measured 4 × 7; evidence under `docs/uat-fix-evidence/2026-08-2x-aug21-translations/` | consolidated status to Carl → ASPSI; wiki source page; memory update |

Waves are independent after Day 0; a problem in one does not hold the others. Order is by size of
delta so the cheapest instrument proves the pipeline first.

### F3 bill-detail sub-items — already built (correction)

The 2026-08-25 build-vs-paper delta reported 97.1/97.2/115.1/115.2 as "paper-only" because their dcf
labels are not number-prefixed. Reading `F3/generate_dcf.py` shows they exist:

- **97.1 / 97.2** = `Q971_SOURCES` + `Q971_ROSTER` (:1229, :1413-1419, roster map :1509) and
  `Q972_SOURCES` + roster (:1236, :1433-1443, :1519) — the checkbox → roster-with-amounts shape,
  with apc procs `Q971_ROSTER_PROCS` (:290) / `Q972_ROSTER_PROCS` (:613) in `generate_apc.py`.
- **115.1 / 115.2** = `Q1141_IN_BILL` (:1629) / `Q1142_NOT_IN_BILL` (:1637) emitted as a **flat
  Yes/No + `_AMT` matrix** (:1727-1755, `Q1141_NONE`, `Q1142_HAS_OTHER`), deliberately left out of the
  Shape-B conversion (comment :1760-1762).

**Decision (Carl, 2026-08-25):** keep 115.1/115.2 in their current flat shape — it works, testers have
not flagged it, and changing the data shape two weeks before training buys nothing for translations.
The wave therefore only re-syncs these items' English labels/options to the Aug-21 paper text (so
the extractor anchors match) and imports their translations. No new records → **F3 6.1.0 (minor)**.
A Shape-B conversion of 115.x stays an open item.

### Facility-name fills (F3 Q66, Q88) — already wired; close the HIL/ILO gap

The generator already carries the paper tokens (`Q66_SAME_AS_USUAL` label "66. Is [facility_name_input]
the facility…" :968-969; `Q88_WHY_VISIT` "…visiting [FACILITY_NAME_INPUT]…" :1323-1325) and
`generate_qsf.py::_pipe_fills` (:400-404) substitutes `~~FACILITY_NAME~~` in **every** language's
question text. The dcf label shown on-device is neutralised by `_neutralise_facility_placeholder`
(:2486) using `_FACILITY_NEUTRAL` (:2460-2467), which has **no HIL or ILO entry** — those two locales
fall back to the raw token. The wave adds the HIL/ILO neutral phrases (from the Aug-21 PDFs' own
wording of Q66/Q88) and verifies the fill renders in all 8 languages. Translation keys stay the
paper text, so the Aug-21 extractor anchors match without special-casing.

### Translation data model (unchanged)

- CSPro maps: `deliverables/CSPro/F{1,3,4}/translations/{fil,bcl,bis,ceb,war,hil,ilo}.json`,
  `name-scoped-v2` (`item:` / `vs:` / `val:`), consumed by `cspro_helpers.apply_translations` at
  `generate_dcf.py` time; English fallback per missing key; `_meta` carries provenance.
- Notes: `data/translations-official/notes.json` via `notes_lookup.py` (full-English-string keys).
- F2: `spec/translations/{loc}.json`, exact-English-string keys, applied by
  `scripts/lib/apply-translations.ts` during `npm run generate`.
- Nothing changes format; the Aug-21 import only changes *values* and adds provenance.

## Verification design

1. **Per merge:** `apply_aug21.py --dry-run` report reviewed (written / replaced / overridden /
   flagged counts per locale) → overrides added only for re-introduced defects → `--apply` →
   `scan_poisoned_keys.py` clean → `bridge_check.py --check` clean.
2. **Per build:** generator per-locale % (before/after in the wave note) → `verify_questions.py`
   PASS → fresh-Designer compile Successful → for F3, `skip_boundary_check.py` + a desk scenario
   through 97.1/97.2/115.1/115.2 (tick / None / No paths) → byte-verify the deployed package
   against the maps (the 2026-08-14 method).
3. **Per deploy:** emulator locale shots of one changed question per instrument in ≥2 languages
   (the 2026-08-17 capture method, sideloaded from the deployed package) → PNGs SHA-pinned under
   `docs/uat-fix-evidence/`.
4. **F2:** vitest, `tsc -b --force`, `locale-shots.spec.ts`, `audit-translations.py` exit 0,
   `build-info.json` sha check after `deploy-f2-pwa.ps1`.
5. **Close:** coverage table 4 × 7 before/after; every replaced value traceable to a PDF; every
   override to a reason.

## Deployment & cutover

- CSPro: publish from a fresh Designer, `auto_deploy.py F<n> --deploy` (instrument-locked),
  `versions.json` stamped via `stamp_version.py bump F<n> --minor --notes ...`. Patch notes lead with
  **remove + re-add**; all three CSPro bumps are MINOR (codes unchanged), so no data-shape warning.
- F2: commit → push (HEAD == origin/main is the script's gate) → `deploy-f2-pwa.ps1`; spec stamp
  `LOCAL_SPEC_VERSION` → m4; no package bump (release workflow owns it).
- Git: the F2 commit follows the 08-20 precedent; CSPro generator/map changes stay in the working
  tree for Carl (deploy is independent of git); evidence commits are the loop's sanctioned write.

## Risks

| Risk | Mitigation |
|---|---|
| Aug-21 PDFs carry June-5's known defects (option swaps, glued fragments) | overrides seeded from the Aug-14/17 repair lists; `scan_poisoned_keys` after every merge; flagged files are the translator worklist |
| Extractor mis-pairs on reworded stems (anchor text ≠ paper text) | English alignment precedes extraction inside each wave; dry-run report lists unmatched anchors per locale before any write |
| F3 label re-sync silently changes a stored code | labels/options change text only; `verify_questions.py` + the checkbox value-set ascending rule guard codes; `aug21_english_delta.py` proves the build matches the paper before extraction |
| F2-Bicolano's different layout yields fewer pairs | anchor-based extraction is layout-independent; low yield shows up in the dry-run report, not in the build |
| Running out of week before F3 | waves are independent — F1/F2/F4 ship regardless; F3 has its own patch note |

## Errata (plan wins; recorded 2026-08-25 evening)

- `apply_aug21.py`: the plan makes the dry run the DEFAULT (`--apply` writes) instead of a `--dry-run` flag, and stamps a sixth `_meta.sources.aug21` field `n_flagged_skipped`. The plan's reconciled-names table is the single source of truth for these names.
- Deployment: "F3's note carries the MAJOR/data-shape warning" was corrected in place on 2026-08-25 (F3 = 6.1.0 MINOR).

## Open items (non-blocking)

- F3 115.1/115.2 Shape-B conversion (flat Yes/No + amount matrix today) — deferred by decision above; revisit after training.

- Runtime error messages: emit the ~590-string sheet (`messages-registry.json` × 3) for ASPSI's
  translators — a separate request, not this build.
- F2 store re-key to id-scoped keys (Task 3.3 of the Aug-17 plan) — still parked; this import
  works on the flat English-keyed store.
- The Aug-21 "Review of Deliverable 2" (DOH, manuals feedback) — no instrument or translation
  items; logged for the manuals lane.

## Artifacts index

- This spec; plan: `docs/superpowers/plans/2026-08-25-aug21-translations.md` (next step).
- Diagram: `deliverables/CSPro/Translations-Aug21-Options-2026-08-25.{excalidraw,png}`.
- Memory: `project_aspsi_deliverable2_revised_aug21` (pack location + status).
- Evidence (to be created): `docs/uat-fix-evidence/2026-08-2x-aug21-translations/`.
