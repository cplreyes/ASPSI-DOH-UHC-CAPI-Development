# Memory-note updates — Aug-21 translations close-out

Proposed edits to Carl's auto-memory after the Aug-21 translation import.
**This file is the proposal only.** The memory files under
`C:/Users/analy/.claude/projects/C--Users-analy-Documents/memory/` are controller-owned; the
main session applies these, not the close-out task.

Facts every entry below is drawn from: `deliverables/CSPro/TRANSLATION-STATUS-2026-08-27.md`,
the four wave notes (`2026-08-26-f1-v4.1.0-…`, `2026-08-26-f2-m4-…`,
`2026-08-26-f4-v3.2.2-…`, `2026-08-27-f3-v6.1.0-aug21-translations.md`), and
`.superpowers/sdd/2026-08-25-aug21-translations/progress.md`.

---

## 1. `project_aspsi_deliverable2_revised_aug21.md` — the driving entry

The description and the **Status** paragraph are now wrong (both say "NOT ingested").

**Description →**

> ASPSI's REVISED Deliverable 2 (Aug-21) = 28 Aug-21 translated questionnaires (F1–F4 × 7
> langs) + Aug-21/24 English masters, at `raw/Survey-Instruments-2026-08-21/`. IMPORTED and
> LIVE: F1 4.1.0 + F2 spec 2026-08-26-m4 + F4 3.2.2 (2026-08-26), F3 6.1.0 (2026-08-27), all
> DEV channel. Close-out done 2026-08-27; worklist + status note ready to send; follow-ups
> F1 4.1.1 / F4 3.2.3 / F3 115.x pending.

**Status paragraph →** replace "NOT ingested (no raw/ folder, no log entry)" with:

> **Status (2026-08-27): IMPORTED, all four instruments LIVE.** Pack on disk at
> `raw/Survey-Instruments-2026-08-21/` (gitignored, immutable, `drive-ids.json` records every
> Drive id). English aligned to the Aug-21 masters first, then each dialect imported
> name-scoped from its own paper. Shipped F1 **v4.1.0** / F2 spec **2026-08-26-m4** /
> F4 **v3.2.2** on 2026-08-26 and F3 **v6.1.0** on 2026-08-27 — all DEV channel; the PSA set
> stays frozen at `capi-psa-2026-08-20`. Coverage gained in all 28 instrument × locale cells
> (+3 to +18 pts): F1 77–81 %, F2 77–84 %, F3 57–74 %, F4 59–71 %. Status page
> `deliverables/CSPro/TRANSLATION-STATUS-2026-08-27.md`; evidence
> `docs/uat-fix-evidence/2026-08-26-aug21-translations/{F1,F2,F4}/` and
> `docs/uat-fix-evidence/2026-08-27-aug21-translations/F3/` (indexed by the latter's
> `README.md`); wiki page `wiki/sources/Source - Revised Deliverable 2 Translated
> Questionnaires (Aug 21).md`. Translator worklist for the remainder —
> `deliverables/CSPro/translator-worklist-aug21.xlsx` (13,194 rows) — plus the ASPSI-facing
> status note `patch-notes/2026-08-27-aug21-translations-status-for-aspsi.md`, both ready for
> Carl to send from clreyes6@up.edu.ph. **DOH's Aug-21 *Review of Deliverable 2* raises no
> instrument or translation item — it is manuals feedback, routed to the manuals lane.**
> Open follow-ups: F1 4.1.1 (68 rows the final extractor now changes + 85 dangling tails),
> F4 3.2.3 (74 clearable holds), F3 115.x generator-side label composition, the
> `Q1141_OTHER_TXT` gate bug and the `PATIENT_TYPE` option-label fragments (both UAT tickets).

## 2. `project_aspsi_translations_pipeline.md`

Currently opens **"CURRENT (2026-08-03): the paper translations ARE delivered and
IMPORTED"** and describes the June-5 text-keyed pipeline. Prepend a new CURRENT block and
demote the 2026-08-03 one:

> **CURRENT (2026-08-27): the Aug-21 revised set is IMPORTED — it supersedes June-5.** Pack at
> `raw/Survey-Instruments-2026-08-21/` (28 translated PDFs + 4 English masters). The join is
> now **name-scoped-v2** — map keys are dictionary names (`item:` / `vs:` / `val:`), anchored
> to the paper by question number — so an English reword can no longer orphan a translation
> the way it did under the June-5 full-English-label match (#1182 / #1213). Chain:
> `aug21_english_delta.py` → `anchor_extract.py` (F2: `anchor_extract_f2.py`) →
> `apply_aug21.py` (F2: `apply-paper-translations.py`) → `run_aug21_gates.ps1` →
> `generate_dcf.py`, all under `deliverables/CSPro/data/translations-official/`. **Aug-21 wins
> on every key except the reasoned entries in `aug21-overrides.json`** (locale-scoped;
> `keep: null` = held, `keep: ""` = render English). Two side layers merge the same way:
> enumerator notes (`extract_notes.py`) and per-language ICF consent (`extract_icf.py`,
> stamped 08/21/2026). Coverage F1 77–81 / F2 77–84 / F3 57–74 / F4 59–71 %. An untranslated
> cell is **not** a build defect — where the paper prints no translation the tool renders
> English on purpose. See [[project_aspsi_deliverable2_revised_aug21]].

## 3. `project_aspsi_cspro_translations.md`

Add an UPDATE block above the existing ones (that file already stacks dated UPDATEs):

> **UPDATE 2026-08-27 (Aug-21 import).** F1 **4.1.0**, F4 **3.2.2** and F3 **6.1.0** are live
> with the Aug-21 maps, DEV channel. Maps are **name-scoped-v2** (`item:`/`vs:`/`val:` keys) —
> the exact-English-label keying described below is superseded; `migrate_maps_namekeys.py`
> did the conversion. ICF consent now renders per language (23/23 paragraphs in every locale
> except HIL 21/23 — the Hiligaynon F3 paper carries an older English consent page) and the
> enumerator notes carry 26–50 translated notes per dialect. Deliberate English holds are in
> `data/translations-official/aug21-overrides.json`, each with a reason: F1 70 entries,
> F3 185, F4 140, F2 40. Runtime `errmsg` messages remain English — out of scope for this
> wave; the ~590-string sheet is a separate request.

## 4. `project_aspsi_f2_pwa_state.md`

> **Spec `2026-08-26-m4` (LIVE 2026-08-26)** — the Aug-21 translation import for the survey
> body plus the consent screen's Part-I paragraphs, in all seven locales. Coverage of the 740
> label objects: fil 80 / bcl 79 / bis 77 / ceb 83 / war 84 / hil 80 / ilo 83 %. The store is
> **still the flat English-keyed one** (the id-scoped re-key stays parked), so the import went
> through `deliverables/F2/PWA/app/scripts/apply-paper-translations.py` against the
> output of `deliverables/CSPro/data/translations-official/anchor_extract_f2.py`.
> Chrome beyond the consent screen (headings, buttons, raffle block) and the
> ballot-box option lists stay English by design; Tagalog Q2
> stays English because ASPSI's cleared Tagalog paper prints it in English only. Coverage is
> measured by `deliverables/F2/PWA/app/scripts/f2-coverage.py` — the single source, never a
> hand-rolled regex.

## 5. `project_aspsi_capi_psa_release.md`

**No change.** The submitted set is unchanged (F1 v3.1.5 · F2 v3.0.0 · F3 v6.0.2 ·
F4 v3.1.3, tag `capi-psa-2026-08-20`) and everything shipped in this wave is DEV channel,
which is exactly what that note already says. Listed here so a reader knows it was checked,
not skipped.

## 6. `MEMORY.md` — index lines

Two lines need re-writing:

**Replace**

> `- [Revised Deliverable 2 (Aug-21)](project_aspsi_deliverable2_revised_aug21.md) — 28 Aug-21 translated PDFs + Aug-21/24 English masters in Drive [B] folder; NOT ingested as of 2026-08-25`

**with**

> `- [Revised Deliverable 2 (Aug-21)](project_aspsi_deliverable2_revised_aug21.md) — IMPORTED + LIVE 2026-08-26/27: F1 4.1.0 / F2 m4 / F4 3.2.2 / F3 6.1.0, all DEV; worklist + status note ready for ASPSI`

**Replace**

> `- [ASPSI translation pipeline](project_aspsi_translations_pipeline.md) — 8-lang set IMPORTED 2026-08-03; 7 locales incl Ilocano; [CSPro F1/F3/F4 extraction+wiring DONE](project_aspsi_cspro_translations.md)`

**with**

> `- [ASPSI translation pipeline](project_aspsi_translations_pipeline.md) — Aug-21 set IMPORTED 2026-08-27, name-scoped-v2 + aug21-overrides.json; supersedes June-5; [CSPro F1/F3/F4 wiring DONE](project_aspsi_cspro_translations.md)`

---

## Checked and deliberately NOT proposed

- **A new memory note for the close-out.** Everything belongs in the five existing ones; a
  sixth would just fragment the Aug-21 story.
- **Any edit under `C:/Users/analy/.claude/`.** Controller-owned; this file is the hand-off.

---

## Fix wave (2026-08-27 afternoon) - what changes in the proposals above

Appended by the wave close-out (Task 52). Everything above was written against the **first**
four builds; all four were superseded the same day by the row-inheritance repair. Still a
proposal - nothing under `C:/Users/analy/.claude/` is touched.

**Versions, everywhere above:** F1 **4.1.1** · F2 spec **2026-08-27-m5** (build `ce05b931`) ·
F4 **3.2.3** · F3 **6.1.2**. Patch-note filenames follow:
`2026-08-27-f1-v4.1.1-aug21-translations.md`, `2026-08-27-f2-m5-…`,
`2026-08-27-f4-v3.2.3-…`, `2026-08-27-f3-v6.1.2-…`.

**§1 `project_aspsi_deliverable2_revised_aug21.md`** - drop "follow-ups F1 4.1.1 / F4 3.2.3
pending" from the description (both shipped) and keep only F3 115.x. In the Status paragraph:
coverage now F1 77-81 % / F2 77-84 % / F3 57-74 % / F4 58-70 % (three cells fell a point when
the wrong-answer rows were deleted); worklist **13,276 rows**, seven sheets. Add one sentence:

> **Fix wave, same day:** a whole-branch review found an option row could silently carry its
> NEIGHBOUR's translation - well-formed text, wrong answer, invisible to coverage and to
> byte-verify. Six live instances corrected (F3 `ceb` LGU/Barangay on 7 questions, F4
> `fil`/`ilo`/`war` option rows, 2 F1 rows, 1 F2 `war` value), each by re-applying the wave
> from the pre-wave baseline with the fixed extractor - never a hand edit. Rows whose only
> paper candidate is a neighbour's words are DELETED (`remove: true`) so the English option
> renders, and go to the worklist.

**§2 `project_aspsi_translations_pipeline.md`** - the override vocabulary is now three, not
two: `keep: null` = held, `keep: ""` = render English, **`remove: true` = delete the key so
English renders**. Add the gate to the chain description:

> `apply_aug21.py` carries a permanent **duplicate-label gate**: a value set in which two
> codes would render the same string blocks the apply (`--fail-on-pre` extends it to
> pre-existing collisions; a RED gate writes nothing, exit 2). `duplicate_label_accepted.json`
> - the only way to declare a pair benign - ships EMPTY. `scan_waivers.json` lets a *named,
> value-pinned* row past a `scan_poisoned_keys` category (7 entries, all F3/`ceb`) instead of
> loosening the scanner for everyone. `_defect_sweep.py` reuses the same gate, so sweep and
> applier cannot disagree. The extractor gained `sibling_run()` + `duplicate_label_keys()`
> (F2 twins included): 76 `duplicate-label` and 4 `sibling-run` rows now go to the worklist
> instead of the maps.

**§3 `project_aspsi_cspro_translations.md`** - the UPDATE block's versions become F1 **4.1.1**,
F4 **3.2.3**, F3 **6.1.2**, and the override counts become F1 **73** / F3 **205** / F4 **157** /
F2 **41** entries (of which 35 are `remove: true`: F1 2, F3 15, F4 13, F2 1).

**§4 `project_aspsi_f2_pwa_state.md`** - the spec heading becomes **`2026-08-27-m5` (LIVE
2026-08-27, build `ce05b931`)**. Worth one line, because it is the trap: a translation-only
redeploy does **not** bump `LOCAL_SPEC_VERSION`, so m5 covers two builds (`fb91241a`, then
`ce05b931`) and **the build sha is what identifies which one PROD serves**. `fil` coverage is
593 of 740, not 594 - the Q95 `Disagree…` key was deleted because the Tagalog paper prints one
string against both rows of that grid, and the live pair was INVERTED. F2's applier gained a
per-locale `remove` for exactly that (`--retire` would have deleted all seven locales).

**§5 `project_aspsi_capi_psa_release.md`** - still **no change**; the frozen set is untouched.

**§6 `MEMORY.md` index lines** - use these instead of the two above:

> `- [Revised Deliverable 2 (Aug-21)](project_aspsi_deliverable2_revised_aug21.md) — IMPORTED + LIVE 2026-08-27: F1 4.1.1 / F2 spec 2026-08-27-m5 (build ce05b931) / F4 3.2.3 / F3 6.1.2, all DEV; row-inheritance repair shipped same day; worklist (13,276 rows) + status note ready for ASPSI`

> `- [ASPSI translation pipeline](project_aspsi_translations_pipeline.md) — Aug-21 set IMPORTED 2026-08-27, name-scoped-v2 + aug21-overrides.json (keep:null / keep:"" / remove:true) + permanent duplicate-label gate; supersedes June-5; [CSPro F1/F3/F4 wiring DONE](project_aspsi_cspro_translations.md)`

**One candidate for a NEW reference note**, offered rather than assumed - the close-out above
argued against a sixth note and that still holds for the *wave*, but the **defect class** is
reusable knowledge that outlives it:

> `reference_row_inheritance_translations.md` — an option row can carry its NEIGHBOUR's
> translation: the text is well-formed and in the right language, so coverage, byte-verify and
> device frames all pass over it. Two page layouts cause it (a two-column grid printing
> `EN EN TR TR`; one translation repeated across rows). Detection = a value set where two codes
> render the same string. Remedy = delete the row, never invent text: an English option beats
> one that repeats another option's words.

Only worth adding if the same shape turns up outside this wave; otherwise it lives in
`TRANSLATION-STATUS-2026-08-27.md` and the wiki source page, both linked from the entries above.
