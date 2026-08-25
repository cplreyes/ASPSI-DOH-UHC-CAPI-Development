# Aug-17 CAPI Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update all four CAPI instruments (CSPro F1/F3/F4 + F2 PWA) from the Apr-20 baseline to the Aug-17 instrument set — English-first, fully re-keyed, with an independent machine countercheck proving verbatim text, numbering, sectioning, skips, validations, and error/warning behavior.

**Architecture:** Two lanes (CSPro, PWA), five waves gated by a three-tier verification stack. The change lane edits the existing generators; a separate countercheck engine reduces both the paper (pandoc extracts) and the build (dcf/qsf/apc; items.ts/schema.ts/skip-logic.ts) to one normalized item table and diffs them at 100% coverage, failing on any difference not whitelisted in an approved-divergence register.

**Tech Stack:** Python 3 (generators, countercheck tools, openpyxl crosswalk), CSPro 8.0 (Designer/CSEntry via pywinauto automation), TypeScript/React/Vite (F2 PWA, tsx generator, vitest, Playwright), PowerShell deploy scripts.

**Spec:** `docs/superpowers/specs/2026-08-18-aug17-capi-migration-design.md` (approved 2026-08-18; decision log inside)

## Global Constraints

- **Two checkouts, fixed roles.** CSPro generator edits, compile, version stamps, and deploys happen in the **MAIN checkout** (`C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development\`, hereafter `MAIN/`) — its `deliverables/CSPro` is the live v2.1.16/3.1.13/2.1.11 state; `auto_deploy.py` ROOT and `stamp_version.py` both resolve there. Countercheck tooling, normalized tables, crosswalk, divergence register, and all F2 PWA work stay in the **worktree** (`...\.claude\worktrees\f2-productivity-panel\`, hereafter `WT/`) — the Aug-17 extracts live only there, gitignored (NDU policy). Never copy verbatim paper tables into MAIN.
- **Versions (from MAIN `versions.json`, the SSOT):** the baseline MOVES — at plan-review time MAIN was already at F1 2.1.17 / F3 3.1.14 / F4 2.2.0 (2026-08-18); Task 0.1 records the actual baseline and re-diffs plan assumptions against it. Targets: **F1 → 3.0.0, F3 → 4.0.0, F4 → 3.0.0** via `py automation/stamp_version.py set <KEY> <ver>` from `MAIN/deliverables/CSPro/`; **F2 PWA → 3.0.0** (displayed app/build version in `package.json` + build-info) **with `LOCAL_SPEC_VERSION = 2026-08-<dd>-m1`** as the client force-update gate (structured `-mN` so `spec-version.ts` compares numerically). All line numbers in this plan are HINTS — re-resolve by symbol name at execution.
- **Naming (Decision 6, full re-key):** item names follow Aug-17 numbers: `Q10_<STEM>`; decimal subs `Q10_1_<STEM>`; letter subs `Q71A_<STEM>`; other-specify `Q<NN>_<STEM>_OTHER_TXT`. Case IDs, the 12-digit `QUESTIONNAIRE_NUMBER`, geo/PSGC items, capture records (GPS/photo), `BREAKOFF`, `CASE_DISPOSITION`, `ENUM_RESULT_*` do **not** rename.
- **Codes — precedence rule:** the paper's codes win everywhere (all four MAJOR bumps are declared data-shape breaks), ASCENDING always; checkbox codes fixed-width via `_cb_codes` (real→01.., Other→99, exclusive→90). **Append-only applies strictly to non-paper system sets** (`ENUM_RESULT_*`, `BREAKOFF`, `CASE_DISPOSITION`) and to any code the paper leaves unchanged. No `"` in any value-set label (pen-packager crash that reports SUCCESS). No em-dashes in dcf/fmf labels/titles (Android mojibake); qsf HTML may use them. Labels ≤255 chars — shorten at source, never rely on the truncator.
- **Translation join keys differ by lane (2026-08-17 migration).** CSPro locale files (`F{n}/translations/*.json`) are **NAME-SCOPED** (`_meta.format: name-scoped-v2`; keys `item:<NAME>`, `vs:<NAME>_VS*`, `val:<NAME>_VS*:<code>`, `record:*`; legacy text keys hard-crash `generate_dcf` via `cspro_helpers.py` SystemExit) — the CSPro re-join therefore moves keys per the **item RENAME map**, not English text. The F2 PWA store (`spec/translations/*.json`) and notes.json remain **exact-English-text keyed**. Values verbatim always; never longest-match; never hand-authored dialect text. Missing key = silent English fallback (the Decision-2 interim behavior for new items).
- **CSPro generation order is load-bearing:** `generate_dcf.py` → `generate_apc.py` (reads written .dcf) → `generate_fmf.py` (reads written .apc) → `generate_qsf.py`; then `optimize_capture_types.py <KEY>` after every fmf bind. A checkbox conversion syncs FIVE lists (dcf call, apc `CHECKBOX_BASES`+`CHECKBOX_CONVERT`, fmf `_CHECKBOX_FIELDS`, optimizer `CHECKBOX`).
- **Compile truth:** Designer "Compile Successful" is untrustworthy; `csentry_verify.py <KEY>` (no `.ent.err` after CSEntry launch) is the gate. `preflight_validate.py` must stay ALL CLEAN. `verify_questions.py`, `skip_boundary_check.py`, `fmf_block_check.py` run after every regen.
- **F2 PWA:** the generator reads `WT/deliverables/F2/PWA/app/spec/F2-Spec.md` (mirror; also update canonical `deliverables/F2/F2-Spec.md`). Never create Q108 unless the Aug-17 paper numbers it (it does — Q1–Q124 continuous — see Task 3.1 for the gap retirement). `npm run generate` after every skip-logic.ts edit. `npx tsc -b --force` before push. Deploy ONLY via `deploy-f2-pwa.ps1`.
- **Standing invariants:** GPS form dead last + warm-radio + `ReleaseGPS()` before any early `endlevel`; `endlevel` statement form (no parens); locals declared at top of proc; `noinput` postprocs still run (guard other-specify skips); protected fields skip their preproc; F1 pilot-jump env vars (`F1_PILOT_JUMP` etc.) never set for deploy builds; paradata `.pff` switch preserved; CSWeb stays 8.0.x; keep-and-filter (no purge, never touch `oauth_*`).
- **Defects (Decision 3):** fix with documented interpretation; ambiguous cardinality defaults to current build; every intentional paper↔build difference gets a divergence-register row BEFORE the diff gate is expected to pass.
- **Git:** commit per task in the checkout where the edit landed, message style `aug17: <what>`; never push or merge — Carl handles publication. (Deploys to CSWeb/tablets follow the standing autodeploy-after-compile-verify instruction and are separate from git.) Files under `instruments-aug17-extract/` are gitignored — only `aug17-tools/` code commits.
- **Shell:** `&&`-chained command blocks in this plan run in **Git Bash**; PowerShell 5.1 rejects `&&` (use `A; if ($?) { B }` there). Python always via the `py` launcher on Windows.
- **Review gate:** every generator-editing task's diff gets a **two-stage subagent review** (stage 1 finds, stage 2 adversarially verifies; explicit OUTPUT DISCIPLINE, line-anchored findings) before its instrument's Tier-1-clean task — part of the ship gate.
- **Deploy byte-verify (all three CSPro deploys):** after every `auto_deploy.py <KEY> --deploy`, byte-verify the uploaded package (search the blob for known label bytes via `bytes.find` over the utf-16-le encoding — whole-blob decode false-negatives at odd offsets); the known failure mode is a truncated upload that reports SUCCESS.

## File Structure (new files)

Tool CODE is committed at `WT/deliverables/CSPro/aug17-tools/`; all DATA derived from the paper stays in the gitignored `WT/deliverables/CSPro/instruments-aug17-extract/` (NDU policy). Every tool takes `--data-dir` (default: `../instruments-aug17-extract` relative to the tools dir).

```
aug17-tools/                      # COMMITTED (code only, no verbatim paper text)
  rowspec.py            # shared Row dataclass + CSV schema + normalizers
  paper_tables.py       # F{n}-extract.md -> normalized/F{n}-paper.csv
  build_tables.py       # MAIN dcf/qsf/apc + WT PWA generated TS (+cross-field.ts) -> normalized/F{n}-build.csv
  aug17_diff.py         # paper vs build diff, register-aware; exit 1 on unregistered diffs
  crosswalk.py          # normalized tables + maps/ + status/ -> aug17-crosswalk.xlsx
  rejoin_translations.py# CSPro name-scoped key mover + PWA english re-key + carryover reports
  propose_renames.py    # old build table x new paper table -> maps/F{n}-renames.csv proposals
  test_tools.py         # pytest (fixtures use INVENTED sample text, never verbatim paper)
  fixtures/

instruments-aug17-extract/        # GITIGNORED (NDU)
  F{1..4}-extract.md, F{1..4}-inventory.md   (already present)
  normalized/F{1..4}-{paper,build}.csv
  maps/F{n}-renames.csv   # old_name,new_name,change_class  (drives CSPro key moves + crosswalk)
  maps/F{n}-english-rekey.csv  # old_english,new_english    (PWA + notes lanes only)
  reports/                # diff + carryover + gate outputs
  status/F{n}-verify.json # tier statuses feeding the crosswalk
  aug17-approved-divergences.md
  aug17-ASPSI-clarifications.md
  aug17-crosswalk.xlsx    # generated artifact (delivered by file, never committed)
```

MAIN-side new files: `MAIN/deliverables/CSPro/F1/generate_fmf.py` (Task 2.3) and per-instrument generator edits in place. Worktree PWA edits in place under `WT/deliverables/F2/PWA/app/`.

## Normalized row schema (the contract every tool shares)

CSV columns (defined once in `tools/rowspec.py`, consumed everywhere):

```
inst        F1|F2|F3|F4
qnum        paper number as printed: "10", "10.1", "71a"; section rows use "" 
item_name   build-side field name (paper side: expected name per naming rules)
section     section letter/title as printed
kind        item | section_header | note | consent | instruction
stem        verbatim question text (single-space-normalized, smart-quotes folded)
options     JSON: [{"code":"1","label":"Yes"},...]  ([] when none)
qtype       single | multi | number | text | date | grid | image
cardinality single | multi
skip        rule text, normalized "IF <cond> GOTO <qnum>" (paper) / derived from apc or skip-logic.ts (build)
validation  range/cross-field text incl. sentinels
messages    error/warning confirmation text (hard vs soft tagged "E:"/"W:")
```

Normalizations (the ONLY tolerated text differences): collapse whitespace, fold smart quotes/apostrophes to ASCII, strip HTML tags on the build side, strip the leading "NN. " number prefix from stems before comparing (numbering is compared via `qnum`, not inside the stem). Everything else must byte-match or carry a register row.

---

## WAVE 0 — Foundations

### Task 0.1: Working-area verification (no code)

**Files:**
- Read only: `MAIN/deliverables/CSPro/versions.json`, `WT/deliverables/CSPro/instruments-aug17-extract/README.md`

- [ ] **Step 1: Record the ACTUAL MAIN baseline** — `py automation/stamp_version.py show` from `MAIN/deliverables/CSPro/` (at plan-review time: F1 2.1.17 / F3 3.1.14 / F4 2.2.0, 2026-08-18 — the fleet is being actively patched; whatever `show` prints now is the baseline). Record it in `reports/baseline.md`.
- [ ] **Step 2: Re-diff plan assumptions against HEAD** — the recon snapshot predates the baseline. Before seeding the register (Task 0.4) or starting any wave: (a) check whether F3's Q18 income brackets are ALREADY implemented (`Q18_BRACKET`/`Q18_INCOME_BRACKET` in `F3/generate_dcf.py` — they were at review time: strike that part of Task 1.1 Step 2 if so); (b) diff the F4 2.2.0 delta (`git log`/diff of `F4/generate_*.py` since 2.1.11) and strike any Wave-1 work item already landed; (c) list "current build" facts the cardinality defaults + register seeds rely on and re-verify each. Write findings to `reports/baseline-drift.md`.
- [ ] **Step 3: Confirm extracts present** — `WT/deliverables/CSPro/instruments-aug17-extract/F{1..4}-extract.md` and `F{1..4}-inventory.md` exist. If missing, regenerate per the folder README (pandoc from `MAIN/raw/Survey-Instruments-2026-08-17/`).
- [ ] **Step 4: Create the scaffolds** — committed `WT/deliverables/CSPro/aug17-tools/{fixtures/}`; gitignored `instruments-aug17-extract/{normalized,maps,reports,status}/`; confirm `git check-ignore deliverables/CSPro/instruments-aug17-extract` passes in WT and that `aug17-tools` does NOT match any ignore rule.
- [ ] **Step 5: Locale-bridge sanity pass** — the 2026-08-17 name-scoped migration left visibly mis-bridged values in F1 (`item:ENUMERATOR_S_NAME: "Resulta"`, `item:FIELD_EDITED_BY: "Resulta aCodes: 1"`, glued `item:RESP_POSITION` in `F1/translations/fil.json`). Spot-check each instrument's `item:` values against `translations/legacy-textkey-2026-08-17/` per locale (script or sampled eyeball, ~30 rows/locale); list corrupt rows in `reports/locale-bridge-defects.md` and fix them from the legacy archive BEFORE any carryover work builds on these files.
- [ ] **Step 6: Commit** (WT, aug17-tools scaffold only) — `aug17: countercheck scaffold`

### Task 0.2: `rowspec.py` + `paper_tables.py` — paper-side normalized tables

**Files:**
- Create: `aug17-tools/rowspec.py`, `aug17-tools/paper_tables.py`, `aug17-tools/test_tools.py`, `aug17-tools/fixtures/f3_snippet.md`
- Output: `instruments-aug17-extract/normalized/F{1..4}-paper.csv` (gitignored)

**Interfaces:**
- Produces: `Row` dataclass (fields = schema above) with `Row.to_csv_row()`/`from_csv_row()`; `normalize_text(s: str) -> str` (whitespace collapse, smart-quote fold, strip leading `r"^\d+[a-z]?(\.\d+)?\.\s+"` number prefix when `strip_qnum=True`); `parse_extract(md_text: str, inst: str) -> list[Row]`; CLI `python aug17-tools/paper_tables.py F3` writes `normalized/F3-paper.csv`.
- Consumes: nothing (root of the chain).

- [ ] **Step 1: Write failing tests** in `tools/test_tools.py`:

```python
from rowspec import Row, normalize_text
from paper_tables import parse_extract

def test_normalize_text_folds_quotes_and_prefix():
    assert normalize_text("10.  What is the patient’s sex?", strip_qnum=True) == "What is the patient's sex?"

def test_parse_extract_emits_item_rows():
    md = open("fixtures/f3_snippet.md", encoding="utf-8").read()
    rows = [r for r in parse_extract(md, "F3") if r.kind == "item"]
    assert any(r.qnum == "7" and "sex" in r.stem.lower() for r in rows)
    q7 = next(r for r in rows if r.qnum == "7")
    assert {"code": "1", "label": "Male"} in q7.options
```

The fixture `fixtures/f3_snippet.md` reproduces the REAL pandoc grid-table STRUCTURE (copy the table skeleton/markup shapes from `F3-extract.md`) with **invented question text** — fixtures are committed and must carry no verbatim paper content. Cover: one section header, one single-select with options, one skip instruction, one `{.mark}` span, one interviewer note. Parser robustness against the real files is proven by the Step-5 full runs + spot check instead.
- [ ] **Step 2: Run to verify FAIL** — `cd deliverables/CSPro/aug17-tools && py -m pytest test_tools.py -x -q`. Expected: import errors.
- [ ] **Step 3: Implement `rowspec.py`** — dataclass + csv writer/reader + `normalize_text` (regexes: `\s+`→space; `[‘’]`→`'`; `[“”]`→`"`; optional qnum-prefix strip). ~80 lines.
- [ ] **Step 4: Implement `paper_tables.py`** — walk the extract line-by-line: detect section headers (bold all-caps runs inside grid tables — reuse the heuristics documented in each `F{n}-inventory.md` §1–2, which cite the exact line numbers of every section/item); detect item starts by `^\**\s*\d+[a-z]?(\.\d+)?\.` ; accumulate stems until the options/next-item boundary; parse option lines (`1 Label`, `01 Label`, checkbox glyphs); capture `(Skip to Q..)` / `(If ... go to ...)` fragments into `skip`; interviewer directives into `kind=note`. Where the inventory catalogs a paper defect (broken ref, duplicate item), parse it AS PRINTED — the divergence register handles it later. Expected item counts to assert per instrument (from the ingest): F1 186, F2 137, F3 180 + 4 artifacts, F4 206.
- [ ] **Step 5: Tests pass** — same pytest command, then full runs: `py aug17-tools/paper_tables.py F1` … `F4`. Eyeball 10 random rows of each CSV against the paper extract (spot check, note results in `reports/paper-tables-spotcheck.md`).
- [ ] **Step 6: Commit** (WT, aug17-tools only — the CSVs are gitignored data) — `aug17: paper-table tool`

### Task 0.3: `build_tables.py` — build-side normalized tables

**Files:**
- Create: `aug17-tools/build_tables.py`; extend `aug17-tools/test_tools.py`; fixtures `fixtures/mini.dcf` (a 2-item CSPro-8.0 JSON dict), `fixtures/mini_items.ts`
- Output: `normalized/F{1,3,4}-build.csv` (CSPro), `normalized/F2-build.csv` (PWA)

**Interfaces:**
- Consumes: `Row`/`normalize_text` from Task 0.2.
- Produces: `parse_dcf_qsf_apc(inst_dir: Path, base: str) -> list[Row]`; `parse_pwa(app_dir: Path) -> list[Row]`; CLI `py aug17-tools/build_tables.py F3 --cspro-dir <MAIN>/deliverables/CSPro` and `py aug17-tools/build_tables.py F2 --pwa-dir <WT>/deliverables/F2/PWA/app`.

- [ ] **Step 1: Failing tests** — `test_parse_dcf_emits_options` (mini.dcf has one select with values `[{"pairs":[{"value":"1"}],"labels":[{"text":"Yes"}]}]` → Row.options `[{"code":"1","label":"Yes"}]`); `test_parse_pwa_reads_items_ts` (regex-extract `id`, `label: { en: '...' }`, `choices` values from mini_items.ts — reuse audit-translations.py's proven regex `en: '((?:[^'\\]|\\.)*)'`).
- [ ] **Step 2: FAIL run.**
- [ ] **Step 3: Implement CSPro side** — dcf is JSON (`json.load`, labels take the `language=="EN"` entry or `labels[0]`); qnum derived from item name (`Q10_1_STEM` → `10.1`, `Q71A_` → `71a`); stems preferentially from the **qsf** (literal EN question text, HTML-stripped — the same `load_qsf` approach as `MAIN/deliverables/data-harmonization/generate_codebook.py:load_qsf`, yaml.safe_load utf-8-sig); skips/validations parsed from the `.ent.apc` (`skip to`, `errmsg`, range patterns — reuse the regexes in `automation/verify_questions.py:83-90` and `skip_boundary_check.parse_apc`); messages from `errmsg` literals + the `.ent.mgf` EN section. Off-form/system items (`KNOWN_OFFFORM` set in verify_questions.py, GPS/photo/BREAKOFF/disposition/PSGC/ICF plumbing) are tagged `kind=consent`/skipped from item comparison via an `EXCLUDE_ITEMS` set defined at the top of the file with a comment per name.
- [ ] **Step 4: Implement PWA side** — parse `src/generated/items.ts` (regex per line-item; ids, en labels, choice values, `required`, `subFields`) + `src/generated/schema.ts` (min/max) + `src/lib/skip-logic.ts` (predicate keys per section, rendered as `skip` text `visible-if: <predicate source>`) + `src/lib/cross-field.ts` rules with their `crossField.*` EN message strings from `src/i18n/locales/en.ts` into `Row.validation`/`Row.messages` (severity tags E:/W: from the rule's severity field); `qnum` = numeric part of id.
- [ ] **Step 5: Tests pass; baseline runs** — generate all five build CSVs against the CURRENT (pre-migration) artifacts. They will disagree with the paper massively — that's the Task 0.4 baseline.
- [ ] **Step 6: Commit** (WT, aug17-tools only) — `aug17: build-table tool`

### Task 0.4: `aug17_diff.py` + the approved-divergence register

**Files:**
- Create: `aug17-tools/aug17_diff.py`, `instruments-aug17-extract/aug17-approved-divergences.md` (scaffold + first entries); extend `aug17-tools/test_tools.py`
- Output: `reports/F{n}-diff.md`, `status/F{n}-verify.json` (tier-1 field)

**Interfaces:**
- Consumes: normalized CSVs (0.2/0.3), register file.
- Produces: CLI `py aug17-tools/aug17_diff.py F3` → exit 0 iff every difference is registered; report sections: `MISSING_IN_BUILD`, `EXTRA_IN_BUILD`, `STEM_DIFF`, `OPTION_DIFF`, `ORDER_DIFF`, `SECTION_DIFF`, `NOTE_DIFF`, `CARDINALITY_DIFF`, `SKIP_DIFF`, `VALIDATION_DIFF`, `MESSAGE_DIFF`, `DISPOSITION_DIFF`, `REGISTERED (n)`. `DISPOSITION_DIFF` is a special rule: each instrument's paper result-of-visit code list is compared against the build's `ENUM_RESULT_*` value set even though disposition items are excluded from stem comparison — the Aug-17 sets diverge per instrument (F1/F2 4-code · F3 6-code · F4 4-code no-Refused) and MUST be caught here. `load_register() -> dict[(inst, qnum, cls)] -> RegisterRow`.

Register row format (markdown table, one per divergence):

```
| inst | qnum/item | class | paper says | build does | rationale / ticket |
|---|---|---|---|---|---|
| F3 | order:G,H | capi-adaptation | G/H after primary-care | G/H front-loaded | Paper's own "Note for CAPI Version"; Carl 2026-08-18 |
```

`class` ∈ `defect-fix | capi-adaptation | fill | formatting | cardinality-default | system-item`.

- [ ] **Step 1: Failing tests** — `test_diff_flags_stem_change` (STEM_DIFF, exit 1); `test_registered_divergence_passes` (register row → exit 0, listed REGISTERED); `test_cardinality_diff` (single vs multi → CARDINALITY_DIFF); `test_message_diff` (differing E:/W: text → MESSAGE_DIFF); `test_disposition_diff` (paper 6-code vs build 5-code ENUM_RESULT → DISPOSITION_DIFF).
- [ ] **Step 2: FAIL run.**
- [ ] **Step 3: Implement** — join paper↔build on `qnum` (fall back to `item_name` for unnumbered rows); compare normalized fields; order comparison = sequence of qnums per section. Output markdown report + update `status/<inst>-verify.json` `{"tier1": "pass"|"fail", "diff_counts": {...}, "ts": ...}`.
- [ ] **Step 4: Seed the register** — from the wiki defect catalogs (`wiki/sources/Source - Updated Survey Instruments (2026-08-17).md` per-instrument sections + `F{n}-inventory.md` defect lists), write the initial rows for every KNOWN paper defect we will fix (F1: 8 skip defects; F2: Q121→Q113 gate, Preventative/Preventive, 8 cardinality defaults; F3: Q124-Q25 banner→Q125, Q98 duplicate item 15, Q159/Q162 gate, auto-number artifacts; F4: 'Yes' in 120→Q45, Q11↔Q40 mismatch note, sentinel normalization to −98/−99) plus the standing CAPI adaptations (F3 front-load; F3/F4 `~~...~~` fills; computed `[DO NOT ASK]` rows; consent/ICF screens; disposition/BREAKOFF system items).
- [ ] **Step 5: Tests pass; baseline diff run** for all four instruments — confirm the report reads sensibly (it will be red; that is the migration TODO list in machine form).
- [ ] **Step 6: Commit** (WT, aug17-tools only; the register itself is gitignored data) — `aug17: diff engine`

### Task 0.5: `crosswalk.py` — the shareable workbook

**Files:**
- Create: `aug17-tools/crosswalk.py`; extend tests. Inputs: `normalized/*`, `maps/F{n}-renames.csv`, `status/F{n}-verify.json`
- Output: `aug17-crosswalk.xlsx` (one sheet per instrument + a READ-ME sheet)

**Interfaces:**
- Consumes: everything above.
- Produces: CLI `py aug17-tools/crosswalk.py` (regenerates the whole workbook; never hand-edited). Sheet columns: `old Q# | old item | new Q# | new item | change class (unchanged/reworded/new/removed/renumbered-only) | value-set delta | cardinality | skip delta | tier1 text | tier2 logic | tier3 desk`.

- [ ] **Step 1: Failing test** — `test_crosswalk_change_class`: rename row + identical stems → `renumbered-only`; absent old → `new`; absent new → `removed`; stem differs → `reworded`.
- [ ] **Step 2: FAIL; implement with openpyxl** (header freeze, filter row, conditional fill green/amber/red on the three tier columns — plain openpyxl `PatternFill`).
- [ ] **Step 3: Generate the skeleton** — CREATE headed, near-empty `maps/F3-renames.csv` + `maps/F4-renames.csv` here (stable numbering; rows appear only for additions/removals); `maps/F1-renames.csv`/`F2-renames.csv` get seeded in Tasks 2.1/3.1 — `crosswalk.py` must tolerate a missing map file with a WARNING row, never a crash. Run `py aug17-tools/crosswalk.py`; open the xlsx once to sanity-check.
- [ ] **Step 4: Commit** (WT, aug17-tools only) — `aug17: crosswalk generator`

### Task 0.6: `rejoin_translations.py` — locale key mover + carryover report

**Files:**
- Create: `aug17-tools/rejoin_translations.py`; extend tests with `fixtures/mini_fil_scoped.json` + `fixtures/mini_fil_text.json`
- Inputs: **CSPro mode:** `maps/F{n}-renames.csv` (`old_name,new_name`) — CSPro locale files are NAME-SCOPED since 2026-08-17. **PWA mode:** `maps/F2-english-rekey.csv` (`old_english,new_english`) — the PWA store is still English-text-keyed.
- Targets: CSPro `MAIN/deliverables/CSPro/F{n}/translations/{fil,bcl,bis,ceb,war,hil,ilo}.json` (keys `item:<NAME>`, `vs:<NAME>_VS*`, `val:<NAME>_VS*:<code>`, `record:*`; `_meta.format: name-scoped-v2`); PWA `WT/deliverables/F2/PWA/app/spec/translations/{7}.json`
- Output: `reports/F{n}-translation-carryover.md`

**Interfaces:**
- Produces: `py aug17-tools/rejoin_translations.py F3 --map maps/F3-renames.csv [--apply]` (dry-run default prints planned moves) and `py aug17-tools/rejoin_translations.py F2 --pwa --map maps/F2-english-rekey.csv [--apply]`. CSPro mode moves every scoped key whose embedded item name matches a rename row: `item:OLD→item:NEW`, `vs:OLD_VS1→vs:NEW_VS1`, `val:OLD_VS1:3→val:NEW_VS1:3` — values verbatim, `_meta` preserved; follow the key-walk conventions of `MAIN/deliverables/CSPro/data/translations-official/migrate_maps_namekeys.py` and `cspro_helpers.walk_labeled_nodes`. Report lists **carried**, **fell-back**, **new**. ⚠ A bare rename would carry a translation even where the English ALSO changed — for every rename row whose new stem ≠ old stem (per the normalized tables), the tool DROPS the `item:` translation to English-fallback and lists it fell-back (Decision 2: reworded English has no cleared translation yet). Same per-code rule for `val:` rows whose option label text changed. A `--stale-from-tables` mode covers instruments WITHOUT renames (F3/F4): it compares old-build vs new-paper stems/option labels for EVERY item and drops the translations of changed English to fallback (name-scoped keys survive rewording, but Decision 2 forbids showing a translation of superseded English). Fell-back+new across instruments = the ASPSI translation work order.

- [ ] **Step 1: Failing tests** — `test_scoped_rename_moves_all_key_kinds` (item:/vs:/val: all move, values verbatim, `_meta` untouched); `test_reworded_stem_drops_to_fellback` (rename row + stem-changed flag → item: key not carried, listed fell-back); `test_unmapped_scoped_keys_untouched`; `test_pwa_mode_rekeys_english`; `test_legacy_text_key_refused` (CSPro mode on a file without `_meta.format: name-scoped-v2` → hard error pointing at the name-scope migration); `test_stale_from_tables_drops_reworded`.
- [ ] **Step 2: FAIL; implement** — collision = error; everything unmapped stays byte-identical; write back `ensure_ascii=False, indent=2` matching current style; emit the report.
- [ ] **Step 4: Tests pass. Commit** (WT, aug17-tools only) — `aug17: translation re-join tool`

### Task 0.7: ASPSI clarification list (draft)

**Files:**
- Create: `aug17-ASPSI-clarifications.md`

- [ ] **Step 1: Draft** — one numbered item per register row of class `defect-fix` or `cardinality-default`, phrased as a question with our implemented default stated (e.g. "Q67 contradicts the Section-D accreditation banner; CAPI implements <interpretation>; please confirm."). Add the two standing asks: the Secondary-Data PAPI annex file, and the BUCAS singular/plural consent-vs-Q88 inconsistency. Group by instrument, cite paper Q numbers only (no internal names — ASPSI reads paper).
- [ ] **Step 2: Done** — the list is gitignored data; it ships to Carl as a file at Wave 4. No commit.

---

## WAVE 1 — F3 + F4 (patch-scale, MAIN checkout)

Work happens in `MAIN/deliverables/CSPro/F3|F4/`. Every task's regen loop is:
(Git Bash) `py generate_dcf.py && py generate_apc.py && py generate_fmf.py && py generate_qsf.py`, then from `automation/`: `py optimize_capture_types.py <KEY>`, `py verify_questions.py`, `py skip_boundary_check.py`, `python ../preflight_validate.py` — all clean before moving on.

### Task 1.1: F3 content pass — stems, options, notes (English verbatim)

**Files:**
- Modify: `MAIN/deliverables/CSPro/F3/generate_dcf.py` (build_section_a..l value-set lists + labels), `F3/generate_qsf.py` (INSTRUCTIONS / INSTRUCTIONS_BY_NAME / SECTION_INTROS)
- Create: `WT/.../maps/F3-english-rekey.csv`

**Interfaces:**
- Consumes: `normalized/F3-paper.csv` rows (the per-item truth) + `F3-inventory.md` §5–8 (the 21 highlighted edits, with extract line citations).
- Produces: edited English labels that Task 1.4's diff will verify; the rekey map for Task 1.4's translation re-join.

Work items (each = edit rows in the named structure, per the paper table):
- [ ] **Step 1: Payment-source matrices gain "Quantified Free Service"** — append the QFS option to the Q98 and Q113 source lists fed to `_build_payment_roster` (source lists live beside their `build_section_g/h` callers). ⚠ Adding a source to a `Q<n>_SOURCES` checkbox changes the packed field length AND the roster `max_occurs` (both derive from `len(sources)`) — data-shape change, covered by the 4.0.0 MAJOR. Codes: append at the next ascending code; do not renumber existing sources.
- [ ] **Step 2: Q18 income bands** — implement exactly what `normalized/F3-paper.csv` row qnum=18 shows (banded value set replacing/augmenting the amount field). If the paper keeps an amount + adds bands, the band item is NEW (`Q18_1_...` style not applicable — follow the paper's own numbering); if it replaces, retire the amount item and register nothing (it's paper-conform). Update the `RANGE_CHECKS` row / `allow_sentinels` accordingly (Task 1.2 double-checks).
- [ ] **Step 3: Remaining highlighted stem/option edits** — walk every `{.mark}` row of `normalized/F3-paper.csv` (cross-checked against the inventory's highlighted-edit list: PhilHealth/NBB relabels, "None" options, Q148 coding code 19, bill-item wrappers) and apply each to its `build_section_x()` label or option list. Keep labels ≤255 chars and quote-free.
- [ ] **Step 4: Retitle** — the paper is now "In-Patient and Out-Patient Survey Questionnaire". Apply it where the title actually renders: the dictionary label in `build_f3_dictionary()` and the qsf cover/BUILD_FOOTER header block; ensure the title row exists in the normalized tables so Tier-1 checks it. Keep `versions.json` app display name "Patient Survey" (fleet continuity) — register row `class=formatting` for that one divergence.
- [ ] **Step 4b: Consent updates** — per the shared Aug-17 consent architecture: edit `MAIN/deliverables/CSPro/icf_content.py` `SCREENS["F3"]` to the paper's consent text — **Php 100 token** mention and the certificate contact block (SJREB + DOH Lindsley Jeremiah D. Villarante + ASPSI **Paulyn Jean A. Claro**, `inquiry.aspsi.doh.uhc.survey2@gmail.com`) — verbatim from `normalized/F3-paper.csv` consent rows. English-only (ICF translation policy unchanged). Add Tier-3 evidence rows (consent screens shot on device).
- [ ] **Step 5: Notes/instructions** — update `INSTRUCTIONS`/`SECTION_INTROS` entries whose paper text changed (keys are paper Q numbers — numbering is stable, so mostly value edits). New English note text will fall back to English in locales (expected, Decision 2).
- [ ] **Step 6: Stale-translation prep** — F3's name-scoped keys survive rewording, so nothing orphans; instead the reworded-English items must DROP to English fallback (Decision 2) via the re-join tool's `--stale-from-tables` mode in Task 1.4. Here: emit `maps/F3-english-rekey.csv` only for the English-text-keyed side lanes — qsf INSTRUCTIONS text changes that shadow notes.json keys (flag those rows `# notes.json` — their locale text re-joins in the post-delivery translation pass via `extract_notes.py`, part of the Task 4.4 work order, NOT in this plan).
- [ ] **Step 7: Regen loop clean; commit** (MAIN) — `aug17: F3 content pass (stems/options/notes)`

### Task 1.2: F3 logic pass — skips, validations, defect fixes

**Files:**
- Modify: `F3/generate_apc.py` (SKIP_RULES / RANGE_CHECKS / CHECKBOX_CONVERT / CUSTOM_VALIDATION), `F3/procs/extra_procs.apc` (+ `covered` set for any new PROC)
- Modify: `WT/.../aug17-approved-divergences.md` (row per fix)

**Interfaces:** consumes `normalized/F3-paper.csv` skip/validation columns; produces logic the Tier-2 matrix (Task 1.5) asserts.

- [ ] **Step 1: Apply paper skip changes** — for every row where paper `skip` ≠ build `skip` in the baseline diff: simple dichotomous → edit the `(field, cond, target)` row in `SKIP_RULES`; multi-branch → the PROC in `extra_procs.apc` (add name to `covered`). PROC-collision SystemExit = fold the skip into the existing bespoke PROC.
- [ ] **Step 2: Fix the catalogued defects** (register rows already exist from Task 0.4): broken `Q124-Q25` banner → route to Q125; Q159 "Not applicable" must land on the Section-L gate Q162 (not jump it); duplicate item 15 in Q98 → single item; the two Word auto-number artifacts are paper-only (no build item; register `class=defect-fix`, build omits).
- [ ] **Step 3: New/changed validations** — QFS amount rows inherit the roster amount gates automatically (`build_roster_procs`); Q18 band/amount validation per Step-2 shape; any new error/warning text goes through `errmsg` literals (numberize assigns stable numbers).
- [ ] **Step 3b: Result-of-visit 6-code set** — reconcile `ENUM_RESULT_OPTIONS_F3` (cspro_helpers) with the paper's 6-code list (adds Completed-at-Hospital, Completed-at-Home, Withdraw) APPEND-ONLY, and rebuild the F3 `DISPOSITION_PROCS` BREAKOFF→Result-of-Visit→CASE_DISPOSITION mapping accordingly; Tier-1 `DISPOSITION_DIFF` and a Tier-2 matrix row per code prove it.
- [ ] **Step 4: Regen loop clean (incl. `skip_boundary_check.py`); commit** (MAIN) — `aug17: F3 logic pass`

### Task 1.3: F3 front-load reorder (outpatient G / inpatient H before primary-care utilization)

**Files:**
- Modify: `F3/generate_dcf.py` (`build_f3_dictionary()` records list :2312-2330), `F3/generate_fmf.py` (`FORM_PLAN` :82), `F3/generate_apc.py` (`BRANCHING` :1087, section-exit `SKIP_RULES` rows), `F3/procs/extra_procs.apc` (targets), `F3/F3-Form-Layout-Plan.md`

Three places move in lockstep (recon: PROC order does NOT need to move — only targets):
- [ ] **Step 1: FORM_PLAN** — move G's 13 entries ('G. Outpatient Care' … 'cont. 6') and H's 9 entries as contiguous runs, preserving the roster interleave order (Q92/Q94/Q96/Q97.1/Q97.2/Q98 for G), to their new position per the paper's "Note for CAPI Version" (immediately before the primary-care utilization block — read the exact anchor from `F3-inventory.md` §CAPI-note).
- [ ] **Step 2: records list** — move `*build_section_g()` / `*build_section_h()` splats to the same relative position in `build_f3_dictionary()`.
- [ ] **Step 3: Retarget skips** — `BRANCHING` (Q88 preproc `PATIENT_TYPE<>1` and Q105 preproc `PATIENT_TYPE<>2` destinations), the G/H exit rows currently anchored on `Q116_NBB_HEARD`, and any `extra_procs.apc` target that assumed A–F precede G. Derive the full retarget list mechanically: grep `skip to` in the generated `.ent.apc` for targets in sections that changed relative order.
- [ ] **Step 4: Verify the reorder** — regen loop; `skip_boundary_check.py` clean; `fmf_block_check.py F3/PatientSurvey.fmf` clean; desk-walk the form order in CSEntry (`csentry_verify.py F3` then a quick `csentry_runner.py` scenario hitting the G entry from the Patient-Type gate). Register row `class=capi-adaptation` already present.
- [ ] **Step 5: Update `F3-Form-Layout-Plan.md`; commit** (MAIN) — `aug17: F3 front-load G/H reorder`

### Task 1.4: F3 rebuild, translation re-join, Tier-1 clean

**Files:**
- Modify: `MAIN/deliverables/CSPro/F3/translations/*.json` (via tool), regenerated build artifacts
- Run: WT tools against MAIN artifacts

- [ ] **Step 1: Stale-translation pass** — `py aug17-tools/rejoin_translations.py F3 --stale-from-tables --apply` (drops translations of reworded English to fallback; F3 has no renames); review `reports/F3-translation-carryover.md`; re-run `py generate_dcf.py` and confirm the printed per-locale coverage drop equals exactly the reported fell-back count — no more, no less.
- [ ] **Step 2: Full regen + static gates** — the Wave-1 regen loop, then `py automation/cspro_compile_driver.py F3 --build --save` and `py automation/csentry_verify.py F3` (must produce no `.ent.err`).
- [ ] **Step 3: Tier-1 diff to green** — `py aug17-tools/build_tables.py F3 --cspro-dir MAIN/deliverables/CSPro && py aug17-tools/aug17_diff.py F3`. Iterate on content/register until exit 0. Every fix loops back through the generators (never patch artifacts).
- [ ] **Step 4: Regenerate crosswalk; commit** (MAIN + WT) — `aug17: F3 tier-1 clean`

### Task 1.5: F3 Tier-2 logic matrix + Tier-3 desk evidence

**Files:**
- Modify: `MAIN/deliverables/CSPro/Desk-Test-Scenario-Matrix.md` (F3 DT rows), `automation/scenarios/f3_*.txt`
- Create: `WT/.../reports/F3-tier2-matrix.md`; evidence under `MAIN/deliverables/CSPro/automation/shots/`

- [ ] **Step 1: Build the Tier-2 matrix** — one row per skip/validation/confirmation in `normalized/F3-paper.csv` (+ register rows): `| rule | trigger input | expected behavior (R hard / S soft / SKIP→target / NOINPUT) | check |`. Mechanical checks run via `verify_questions.py` (dead conditions, targets) — already green; behavioral rows map to scenario steps.
- [ ] **Step 2: Update scenarios** — numbering is stable so existing `f3_*.txt` files mostly survive; update typed codes for changed value sets (QFS source code, Q18 bands, Q148 code 19) and note-lines; add one scenario for the front-loaded G/H entry order and one exercising a QFS payment roster row end-to-end.
- [ ] **Step 3: Run + read** — `py automation/csentry_runner.py automation/scenarios/<each>.txt`; read the shot trails; record PASS/FAIL per DT row in the matrix; tablet-capture the QFS matrix + front-load order per the uat-fix-evidence pattern into `docs/uat-fix-evidence/<date>-aug17-migration/F3/`.
- [ ] **Step 4: Rewrite `F3/F3-Skip-Logic-and-Validations.md`** to the Aug-17 rules (the codebook generator regex-parses it for the skip/universe columns).
- [ ] **Step 5: Stamp statuses** — set tier2/tier3 in `status/F3-verify.json`; regenerate crosswalk. Commit (MAIN + WT) — `aug17: F3 tier-2/3 evidence`

### Task 1.6: F3 version 4.0.0 + deploy

- [ ] **Step 1:** `py automation/stamp_version.py set F3 4.0.0` (MAIN; re-stamps pff + regenerates qsf footer), then `show` = no drift.
- [ ] **Step 2:** `py automation/cspro_compile_driver.py F3 --build --save` → `csentry_verify.py F3` → static gates once more (the stamp regenerated the qsf).
- [ ] **Step 3:** Deploy per standing autodeploy: `py automation/auto_deploy.py F3 --deploy` (CSPRO_ADMIN_USER/_PASS_FILE set; success only on the 'successfully' popup). Byte-verify the uploaded package label set (dcf-label quote trap check).
- [ ] **Step 4:** Append the VERSIONING.md history row; announce in the UAT channel per convention. Commit (MAIN) — `aug17: F3 v4.0.0 deployed`

### Task 1.7: F4 content pass — bill decomposition rewrite, GAMOT block, roster code 13

**Files:**
- Modify: `MAIN/deliverables/CSPro/F4/generate_dcf.py` (`build_section_m()` ≈:1590; the GAMOT/BUCAS section builder; `build_section_c()` roster relationship value set; Q202 list), `F4/generate_qsf.py` (INSTRUCTIONS keys 141/143 + new-module notes), `MAIN/deliverables/CSPro/icf_content.py` `SCREENS["F4"]` (Php 100 token mention + Claro certificate block, verbatim from the F4 consent rows)
- Create: `WT/.../maps/F4-english-rekey.csv`

- [ ] **Step 1: Rewrite Q139–Q143 per the paper** — edit `build_section_m()` item rows and the local value-set lists (`Q141_BILL_ITEMS` ≈:1603, `Q143_HOW_PAID` ≈:1612 — re-grep, lines drift). The paper's new **16-source Q142 settlement matrix** (includes Quantified Free Service, NO ZBB line) replaces the current 10-option `Q143_HOW_PAID`-era shape — implement exactly what `normalized/F4-paper.csv` rows 139–143 show, keeping every surviving option's existing code and appending new ones ascending. ⚠ Q141's odd checkbox contract (with_other_txt=False, Other=paper code 07 via `CHECKBOX_OTHER_CODE`) — re-derive from the new paper codes, and if the paper renumbers within the module, that IS allowed here only because 3.0.0 is a declared data-shape break; note each such recode in the crosswalk value-set-delta column.
- [ ] **Step 2: GAMOT block Q69–Q78** — implement the unlettered GAMOT module per the paper rows (mirrors F1/F3 GAMOT stems; new items in the awareness section's builder). New checkbox bases follow the FIVE-list sync (dcf call, apc CHECKBOX_BASES+CHECKBOX_CONVERT, fmf `_CHECKBOX_FIELDS`, AND `automation/optimize_capture_types.py` CHECKBOX — its set explicitly enumerates F4 bases; omitting one silently demotes a multi-select to DropDown = data loss).
- [ ] **Step 3: Small deltas** — Q34 relationship code **13 Grandfather/Grandmother** appended (roster value set, append-only); Q202's COVID-19 option per paper; Q11↔Q40 education-list mismatch: implement each list as ITS paper table prints it, register `class=defect-fix` noting the cross-list inconsistency for ASPSI.
- [ ] **Step 4: Sentinel normalization** — paper's mixed sentinel families (−98/−99, −55, 88) normalize to the locked −98 DK / −99 REFUSED standard; register `class=capi-adaptation` (one row covering the family); the literals live in ~6 places (apc amount-gate templates ≈:1437/:1522, review predicates ≈:1598, the sentinel-hint errmsg text near the Q18 bracket cross-check and the `_PURCHASED_PHP`/`_INKIND_PHP` subtotal machinery, qsf Q18 note, codebook §0.2) — this task only asserts no NEW sentinel values enter; the existing standard stays.
- [ ] **Step 5: Rekey map + regen loop clean; commit** (MAIN) — `aug17: F4 content pass`

### Task 1.8: F4 logic pass + rebuild + Tier-1

**Files:**
- Modify: `F4/generate_apc.py` (SKIP_RULES ≈:823, BILL_VALIDATION ≈:956, CHECKBOX_* ≈:500-567, `covered`), `F4/procs/extra_procs.apc`; translations via tool; register rows

- [ ] **Step 1: Bill-module logic** — rebuild the Q139–143 chain per paper: gates Q140/Q142 (`= 2` skips), the Q141.1 ≤ Q139 cap in `BILL_VALIDATION`, new Q142-matrix checkbox PROC rows; the skip INTO Section N stays occurrence-explicit (`N_FOOD_ITEM(1)`).
- [ ] **Step 2: Defect fixes** — stale `(Only answer if 'Yes' in 120)` → gate on Q45 (register row exists); Q135↔Q130 hidden dependency made explicit per paper; GAMOT block gating per its paper skip column (mirror the AREA_HAS_GAMOT auto-answer pattern in `extra_procs.apc` if the paper area-gates it).
- [ ] **Step 2b: Result-of-visit 4-code no-Refused set** — reconcile `ENUM_RESULT_OPTIONS_F4` with the paper's list (1 Completed · 2 Postponed · 3 Incomplete · 4 Withdraw — no Refused) append-only against existing codes, and align `DISPOSITION_PROCS`; Tier-1 `DISPOSITION_DIFF` + Tier-2 rows prove it.
- [ ] **Step 3: Translation re-join + full rebuild + Tier-1 to green** — same sequence as Task 1.4 with F4 substituted (`rejoin_translations.py F4`, coverage non-drop check, `cspro_compile_driver.py F4 --build --save`, `csentry_verify.py F4`, `aug17_diff.py F4` exit 0).
- [ ] **Step 4: Commit** (MAIN + WT) — `aug17: F4 logic + tier-1 clean`

### Task 1.9: F4 Tier-2/3 evidence + v3.0.0 deploy

- [ ] **Step 1: Tier-2 matrix + scenarios** — update `f4_validations.txt` / `f4_breakoff_*.txt` typed codes and notes for the new bill matrix and GAMOT block; add a bill-decomposition walkthrough scenario (Q138→Q143 with the 16-source matrix, receipt/no-receipt branches) and a GAMOT-gate scenario. Rewrite the F4 DT rows in `Desk-Test-Scenario-Matrix.md`.
- [ ] **Step 2: Run scenarios, read shots, tablet-capture** the bill module + GAMOT into `docs/uat-fix-evidence/<date>-aug17-migration/F4/`; rewrite `F4/F4-Skip-Logic-and-Validations.md` to the Aug-17 rules; stamp tier2/3 statuses; regenerate crosswalk.
- [ ] **Step 3: Version + deploy** — `stamp_version.py set F4 3.0.0` → `show` clean → compile driver + csentry_verify + gates → `auto_deploy.py F4 --deploy` (review.html rides along automatically). VERSIONING.md row. Commit (MAIN + WT) — `aug17: F4 v3.0.0 deployed`

---

## WAVE 2 — F1 rebuild (MAIN checkout)

F1 is renumbered AND restructured (Q1–153 + 33 decimal subs; new modules; Secondary Data + consent retained per Decision 7). The .fmf is currently hand-maintained — Task 2.3 replaces that with an F3-style `generate_fmf.py`, which the renumber forces anyway (nearly every `Name=`/`Item=` line changes).

### Task 2.1: F1 rename map (carried items)

**Files:**
- Create: `WT/.../maps/F1-renames.csv` (`old_name,new_name,change_class`), `aug17-tools/propose_renames.py`

**Interfaces:**
- Consumes: `normalized/F1-build.csv` (old world) + `normalized/F1-paper.csv` (new world).
- Produces: the rename map consumed by Tasks 2.2/2.4/2.5 and `crosswalk.py`.

- [ ] **Step 1: Failing test** — `test_propose_renames_matches_by_stem`: identical normalized stems, different qnums → one row `old_name,new_name,renumbered-only`; changed stem but unique fuzzy best-match (difflib ratio ≥ 0.85) → `reworded` flagged for review; no match → left for hand resolution.
- [ ] **Step 2: Implement `propose_renames.py`** — join on `normalize_text(stem, strip_qnum=True)` exact first, fuzzy second; emit `maps/F1-renames.csv` plus `reports/F1-rename-unresolved.md` for the remainder.
- [ ] **Step 3: Hand-resolve the remainder** against `F1-inventory.md` (moved/merged/removed items; the Apr-20 Secondary-Data stubs map to themselves — they are retained unchanged and get `change_class=unchanged`). Every old item ends classified: renamed / reworded / removed; every new paper item without an old partner is `new`.
- [ ] **Step 4: Commit** (WT, aug17-tools only — propose_renames.py; the map itself is gitignored) — `aug17: rename proposer`

### Task 2.2: F1 dictionary rebuild — re-key + new structure + new content

**Files:**
- Modify: `MAIN/deliverables/CSPro/F1/generate_dcf.py` (all build_section_* to Aug-17 structure), `MAIN/deliverables/CSPro/icf_content.py` `SCREENS["F1"]` — the Aug-17 consent DID change (program list incl. GAMOT, certificate contact block w/ Paulyn Jean A. Claro + Villarante, Year-2 mailbox): apply verbatim from the F1 consent rows
- Create: `WT/.../maps/F1-english-rekey.csv`

**Interfaces:**
- Consumes: rename map (2.1), `normalized/F1-paper.csv`.
- Produces: the Aug-17 dictionary the apc/fmf/qsf generators and diff consume. New-item naming per Global Constraints.

- [ ] **Step 1: Add a two-step helper** — the C-section attribution battery (base question + highlighted `.1` "…a result of the UHC Act enacted in 2019?" probe, ~30 pairs) gets one factory in `F1/generate_dcf.py`:

```python
def two_step(base_name, base_label, probe_qnum, options=YES_NO, probe_options=YES_NO_DK):
    """Aug-17 C-battery: base item + its .1 UHC-attribution probe.
    Probe naming: Q24_X -> Q24_1_UHC_ATTRIB. Skip wiring lives in generate_apc (probe
    asked only when the base signals a change) - this factory only shapes the dict."""
    probe_name = f"{base_name.split('_')[0]}_1_UHC_ATTRIB"
    probe_label = f"{probe_qnum}. Was this a result of the UHC Act enacted in 2019?"  # verbatim from paper row
    return [select_one(base_name, base_label, options, length=1),
            select_one(probe_name, probe_label, probe_options, length=1)]
```

(Verbatim probe wording comes from `normalized/F1-paper.csv` — the paper repeats it with slight per-item variations; emit each row's actual text, falling back to a shared constant only where the paper is itself identical.)
- [ ] **Step 2: Rebuild the section builders to the Aug-17 map** — `F1-inventory.md` §2 is the full section/item layout (A Profile Q1–6 · B Facility Q7–8 · C UHC Q9–37+subs · D YAKAP Q38–87 · E BUCAS+GAMOT Q88–104 · F DOH Licensing Q105–121 · G Service Delivery Q122–149 · H HRH Q150–153). Carried items: rename per the map (same builder call, new name + new label text from the paper row). New: GAMOT Q95–98, stock-outs Q99–104, DOH-IS Q21–23, PHO Q139–140, and every other `new` row. Removed rows: delete the builder call. Secondary-Data stubs (`build_secondary_data_stubs`) and the ICF/consent record stay byte-identical (Decision 7) — register rows `class=system-item` cover their absence from the paper body.
- [ ] **Step 3: Checkbox re-sync** — every renamed/new checkbox base updates the F1 sync lists it still needs after Task 2.3 (apc `CHECKBOX_BASES`/`CHECKBOX_CONVERT_A`, new fmf generator's `_CHECKBOX_FIELDS`, optimizer `CHECKBOX` set in `automation/optimize_capture_types.py`).
- [ ] **Step 4: Stem-change flags for the re-join** — the CSPro re-join keys on `maps/F1-renames.csv` (name-scoped locale keys); `propose_renames.py --emit-stem-flags` adds a `stem_changed` column (old-build vs new-paper stems) so the tool drops reworded items to English fallback while carrying pure renumbers. Also emit a small `maps/F1-english-rekey.csv` for the English-keyed side lanes (qsf INSTRUCTIONS; `# notes.json` rows → Task 4.4 work order).
- [ ] **Step 5: `python generate_dcf.py` runs clean** (coverage report prints; expect a large legitimate coverage drop pending Task 2.5's re-key). Commit (MAIN) — `aug17: F1 dictionary rebuild`

### Task 2.3: F1 `generate_fmf.py` (adopt the F3 pattern; retire the injectors)

**Files:**
- Create: `MAIN/deliverables/CSPro/F1/generate_fmf.py`
- Modify: `MAIN/deliverables/CSPro/automation/cspro_compile_driver.py` (SPECS F1 `has_fmf_gen: True`), `automation/optimize_capture_types.py` (no change needed unless F1-specific list), retired scripts left in place with a tombstone docstring (do NOT delete — they document history): `inject_blocks.py, inject_case_key.py, inject_icf.py, inject_breakoff.py, inject_field_control_end.py, inject_gps_end.py, inject_q2_other_txt.py, inject_q163_other_txt.py, inject_short_component_labels.py, inject_date_display.py/remove_date_display.py, fmf_checkbox_convert.py`

**Interfaces:**
- Consumes: `FacilityHeadSurvey.dcf` + `.ent.apc` (same contract as F3's generator: `parse_apc()` for skip-aware blocks).
- Produces: `FacilityHeadSurvey.generated.fmf`; the compile driver copies → `.fmf` + optimize pass.

- [ ] **Step 1: Port** `F3/generate_fmf.py` structure (FORM_PLAN, `derive_block_plan`, `parse_apc`, `_CHECKBOX_FIELDS`, `_OFF_FORM_ITEMS`, MAX_CHUNK=5) into `F1/generate_fmf.py`.
- [ ] **Step 2: Encode F1's form order as FORM_PLAN**, reproducing every invariant the injectors enforced: case-key form 0 (level IDs) → geo form (with BREAKOFF spliced on it) → ICF 2-screen forms (blocks named `ICF_BLK_*`, never `DG_*`) → sections A–H per Aug-17 order → Secondary-Data stub forms → Field Control form → Verification Photo → **GPS dead last**. Short component labels (Q5/Q6 splits) become explicit `[Text]` overrides in the generator; the Q2/Q163 other-txt fields are ordinary generated fields now.
- [ ] **Step 3: Wire the driver** — flip F1's `has_fmf_gen` in `cspro_compile_driver.SPECS`; confirm `--build` runs dcf→apc→fmf→copy→optimize for F1 like F3/F4.
- [ ] **Step 4: Gate** — `fmf_block_check.py F1/FacilityHeadSurvey.fmf` clean; `verify_questions.py` reachability clean (add any genuinely off-form new items to `KNOWN_OFFFORM` with reasons); Designer opens the fmf without silent crash; `csentry_verify.py F1` (after Task 2.4 gives it a compilable apc).
- [ ] **Step 5: Tombstone the injectors** (docstring header: "Retired 2026-08-.. — superseded by generate_fmf.py; kept for history") and update the pipeline docstring that lived in `inject_q2_other_txt.py` to point at the new canonical order.
- [ ] **Step 6: `inject_scoped_option_labels.py` disposition** — this LIVE dcf-side post-processor (#1222 per-question Bikol Dae/Dai option labels, keyed to Apr-20 Q numbers) is invalidated by the re-key. Verify the per-question values already live in `F1/translations/bcl.json`'s name-scoped `val:`/`vs:` keys (they should, post 2026-08-17 migration — confirm against `translations/legacy-textkey-2026-08-17/`); if yes, tombstone the injector; if not, re-key its map from `maps/F1-renames.csv` and add it to the F1 regen loop after `generate_dcf.py`. Commit (MAIN) — `aug17: F1 generate_fmf adoption`

### Task 2.4: F1 logic rebuild

**Files:**
- Modify: `MAIN/deliverables/CSPro/F1/generate_apc.py` (SKIP_RULES, ROUTING_PROCS, BESPOKE_PROCS, WHY_DIFF_GATES, CHECKBOX_BASES/CHECKBOX_CONVERT_A, uhc9/two-step wiring), `F1/procs/control_procs.apc` (unchanged unless the cover changed — expect no edit), register rows for the 8 catalogued defects

- [ ] **Step 1: Re-key every table** — apply `maps/F1-renames.csv` across SKIP_RULES / ROUTING_PROCS keys+bodies / BESPOKE_PROCS / WHY_DIFF_GATES / CHECKBOX_* / `covered` seeds (mechanical sed-style pass, then hand-review the diff).
- [ ] **Step 2: New logic** — two-step battery gating (each `.1` probe asked only on the base's change-signal codes, per the paper's skip column — one SKIP_RULES row or a small ROUTING_PROCS entry per pair; ~30, generate them from the paper table with a loop in the generator rather than 30 hand rows); GAMOT/stock-out module gates; DOH-IS Q21–23 fan; PHO Q139–140 public-hospital gate; the 8 defect fixes per their register rows (Q67 banner contradiction, Q65/Q68–71 missing exits, Q137→Q141 orphan fix, Q148 SELECT-ALL mislabel → implement per register decision, Section-E banner vs gates, Q94 gate, Q117 sequence, Q102/Q101 duplication).
- [ ] **Step 3: Preserve the battery-gate machinery** — WHY_DIFF_GATES ranges re-anchored to the new Q numbers (the licensing-difficulty battery moved to F Q105–121); keep the aligned 2-char chunk scan; keep the #376 dual-other no-skip auto-rewrites (conditions stay in recognized shapes).
- [ ] **Step 4: Regen + gates** — full loop; `preflight_validate.py` ALL CLEAN; `verify_questions.py` (dead conditions catch stale codes); `skip_boundary_check.py`; `cspro_compile_driver.py F1 --build --save`; **`csentry_verify.py F1`** green. Commit (MAIN) — `aug17: F1 logic rebuild`

### Task 2.5: F1 translations + Tier-1 clean

- [ ] **Step 1:** `py aug17-tools/rejoin_translations.py F1 --map maps/F1-renames.csv --apply` (name-scoped key moves + stem-changed drops); regen dcf; coverage must recover to ≈ pre-migration minus the genuinely-new/reworded strings; `reports/F1-translation-carryover.md` reviewed (fell-back list ≈ new modules + two-step battery + rewordings — sanity-check a sample).
- [ ] **Step 2:** `py aug17-tools/build_tables.py F1 --cspro-dir MAIN/deliverables/CSPro && py aug17-tools/aug17_diff.py F1` → iterate to exit 0 (content fixes through generators; divergences through the register).
- [ ] **Step 3:** Regenerate crosswalk (F1 sheet now fully populated: renames + new + removed). Commit (MAIN + WT) — `aug17: F1 tier-1 clean`

### Task 2.6: F1 Tier-2/3, spec docs, v3.0.0 deploy

- [ ] **Step 1: Rewrite `F1/F1-Skip-Logic-and-Validations.md`** to the Aug-17 numbering/rules (the codebook generator regex-parses this file — its skip/universe columns depend on it).
- [ ] **Step 2: Tier-2 matrix + scenarios** — F1 scenarios (`f1_*.txt`) need the renumber treatment: casekey widths unchanged; typed codes/notes re-pointed. New scenarios: two-step battery (base-No skips probe; base-Yes asks it), GAMOT + stock-out flow, PHO gate, Secondary-Data stubs still reachable. Rewrite F1 DT rows in `Desk-Test-Scenario-Matrix.md`.
- [ ] **Step 3: Run + evidence** — runner trails read; tablet captures of the battery, GAMOT, and the UPDATED consent screens (certificate/contact block per Task 2.2) into `docs/uat-fix-evidence/<date>-aug17-migration/F1/`; stamp statuses; crosswalk regen.
- [ ] **Step 4: Version + deploy** — `stamp_version.py set F1 3.0.0` → `show` clean → compile + csentry_verify + gates → `auto_deploy.py F1 --deploy` (8 PSGC files ride per add_files; CORRECTED 2026-08-19: facility_lookup must NOT ride -- removed 2026-06-10, its PRESENCE re-creates the Android startup loop). Release note via release_notes.py (VERSIONING.md table retired 2026-08-19). Commit (MAIN + WT) — `aug17: F1 v3.0.0 deployed`

---

## WAVE 3 — F2 PWA (worktree; runs in parallel after Wave 0)

All commands from `WT/deliverables/F2/PWA/app/` unless noted. Every content change ships with `npm run generate`, `npm test`, `npx tsc -b --force`, and a `LOCAL_SPEC_VERSION` bump at the end of the wave.

### Task 3.1: Spec rewrite to Aug-17 (renumber + new content)

**Files:**
- Modify: `spec/F2-Spec.md` (the build source) AND `deliverables/F2/F2-Spec.md` (canonical mirror — same edit, kills the known drift), `scripts/lib/emit-items.ts` (NUMBERING_GAP retirement)
- Create: `WT/.../maps/F2-renames.csv`, `maps/F2-english-rekey.csv`

- [ ] **Step 1: Renumber rows** — Aug-17 F2 numbers Q1–Q124 **continuously** (the old Q108 gap is gone). For each carried row: set `pdf_q` to the new number, keep the old id in `legacy_q`. Record every id move in `maps/F2-renames.csv` (old id → new id). Full re-key per Decision 6: **data keys follow the new ids.**
- [ ] **Step 2: Retire the display gap** — in `scripts/lib/emit-items.ts` remove the `NUMBERING_GAP = 108` shift. Failing test first: a renumbered row above the old gap emits **NO `displayNumber` override** (the emitter only writes displayNumber when display ≠ id; with the gap retired, `displayNumberFor` returns undefined for every id and the renderer falls back to the id).
- [ ] **Step 3: New content rows** — Section-B attribution battery (two-step preliminaries), Q47 ZBB-challenges checklist, employment-type definition block under Q2, DOLE hours note under Q11, E split into E1 (BUCAS) / E2 (GAMOT) — paper's E1/E2 sub-sectioning is implemented as the existing ITEM-LEVEL split (structural split deliberately avoided per R2-#117); register row `class=capi-adaptation`. Grid batteries use the `**Grid #N — name** (choices)` header convention. All stems/choices verbatim from `normalized/F2-paper.csv`.
- [ ] **Step 3b: Consent/landing text** — apply the Aug-17 F2 consent changes (PhP 1,000 raffle mention + certificate contact block w/ Paulyn Jean A. Claro) to the PWA's consent/enrollment content — locate it via the `enrollment.*`/consent keys in `src/i18n/locales/en.ts` and any consent component under `src/components/`; English bundle first, other 7 bundles keep English placeholders (chrome-bundle mirror rule).
- [ ] **Step 3c: Result-of-visit register row** — the paper's F2 result-of-visit field control has no PWA equivalent (self-administered; completion states live server-side) — register `class=capi-adaptation` so DISPOSITION_DIFF passes deliberately.
- [ ] **Step 4: Cardinality defaults** — the 8 ambiguous select-one/select-all lists keep the CURRENT build's type (register rows `class=cardinality-default`, one each, mirrored in the ASPSI list).
- [ ] **Step 5: Generate + tests** — `npm run generate` (unsupported-row log empty), `npm test`. Commit (WT) — `aug17: F2 spec rewrite`

### Task 3.2: Routing + validation rewrite

**Files:**
- Modify: `src/lib/skip-logic.ts` (predicates re-keyed to new ids + new cadre routing), `src/lib/cross-field.ts` (SECTION_G_FIELDS/SECTION_CD_FIELDS id lists + any `v.Qnn` reads), `src/i18n/locales/*.ts` (only if new crossField keys appear)

- [ ] **Step 1: Re-key predicates** — apply `maps/F2-renames.csv` to every predicate key and every `v.Qnn` reference. Keys keep the required `    Qnn: (` line format (the generator regex-reads this file).
- [ ] **Step 2: New cadre routing** — pharmacists/dispensers skip C–E1 and enter at E2 (extend the E-section item predicates + `shouldShowSection` branches); Section G reached via Q61/Q62 per-option routing for physicians/dentists (`SECTION_G_ROLES` unchanged unless the paper's role list changed — check the paper row); other non-core cadres enter at F per the paper's Section-B exit map. Role strings must equal Q5 choice values verbatim.
- [ ] **Step 3: Defect fixes** — Q121-gates-on-Q114 → gate on Q113 (register row); `Preventative`/`Preventive` gate-string mismatch → single spelling matching the choice value.
- [ ] **Step 4: `npm run generate` (mandatory after skip-logic edits), `npm test`** — update `skip-logic.test.ts` / cross-field tests to the new ids as part of this task, adding cases for: pharmacist path (skips C–E1, sees E2), physician path (sees G), and one two-step battery pair. Commit (WT) — `aug17: F2 routing rewrite`

### Task 3.3: Translations re-key + audit

- [ ] **Step 1:** From `WT/deliverables/CSPro/`: `py aug17-tools/rejoin_translations.py F2 --map maps/F2-english-rekey.csv --pwa --apply` (map built from the spec diff: changed English label/choice strings; PWA keys carry NO number prefixes, so carried-over stems mostly survive untouched — the map is small).
- [ ] **Step 2:** `npm run generate && python scripts/audit-translations.py` — zero ORPHAN/misjoin findings; review the fell-back list (new battery + rewordings) into `reports/F2-translation-carryover.md`.
- [ ] **Step 3:** Commit (WT) — `aug17: F2 translations re-keyed`

### Task 3.4: Downstream key consumers + Tier-1

**Files:**
- Modify: `WT/deliverables/CSWeb/f2-item-labels.json` (regenerate from the new items.ts — see the generator noted in the codebook's error message / `csweb-spss-gen.py` footer — then COPY to `MAIN/deliverables/CSWeb/f2-item-labels.json` with md5 verification: the codebook's search order prefers MAIN and would otherwise read the stale copy), `WT/deliverables/F2/apps-script/Spec.gs` (+ any sibling .gs carrying Q-ids — the backend column map; deploy via the established clasp automation), `src/admin/data/ResponseDetail.tsx` — locate all consumers with `grep -rl "Q71a\|Q109" deliverables/F2 --include='*.gs' --include='*.ts' --include='*.tsx'` from WT root

- [ ] **Step 1: Backend/admin re-key** — apply `maps/F2-renames.csv` to every consumer found; new-id columns append; keep `legacy_q` documented in the crosswalk so old submissions remain interpretable (spec-version gate blocks new submissions on old ids anyway).
- [ ] **Step 2: Tier-1** — `py aug17-tools/build_tables.py F2 --pwa-dir WT/deliverables/F2/PWA/app && py aug17-tools/aug17_diff.py F2` → iterate to exit 0.
- [ ] **Step 3: F2 Tier-2 matrix + a11y** — build `reports/F2-tier2-matrix.md` (paper rule → expected behavior for every skip/validation/cross-field message), executed via the vitest suites + targeted Playwright specs; run the a11y suite (`a11y.test.tsx` in `npm test` — confirm it ran, don't assume); capture cadre-routing evidence (pharmacist/physician/nurse paths) into `docs/uat-fix-evidence/<date>-aug17-migration/F2/`; stamp tier2/tier3 into `status/F2-verify.json`.
- [ ] **Step 4:** `npm test && npx tsc -b --force`; crosswalk regen. Commit (WT) — `aug17: F2 tier-1/2 clean + consumers re-keyed`

### Task 3.5: F2 e2e, version, deploy

- [ ] **Step 1: e2e refresh** — update `e2e/golden-path.spec.ts` personas to the new visible paths (physician, pharmacist, nurse), matrix/preamble specs to new ids; `npm run e2e` green.
- [ ] **Step 2: Version** — F2 PWA → **3.0.0**: bump `package.json` version (surfaces in build-info.json at deploy) so the generation marker matches the fleet; set `LOCAL_SPEC_VERSION = '2026-08-<dd>-m1'` in `src/lib/draft.ts:18` (structured `-mN`); coordinate the server `min_accepted_spec_version` raise so stale clients force-update.
- [ ] **Step 3: Deploy markers** — add a `$RequiredMarkers` row in `deploy-f2-pwa.ps1` probing the Section-B battery's RENDER path (a string unique to the new battery UI), keeping all existing rows.
- [ ] **Step 4: Deploy** — `npm run build`; from WT root: `powershell -File deliverables\F2\PWA\deploy-f2-pwa.ps1 -DryRun` then the real run per the script's guards (HEAD gate handled per established branch practice — Carl merges or authorizes -Force); post-deploy `-VerifyOnly`; refresh `locale-shots/` via the existing shot specs. Commit (WT) — `aug17: F2 v3 spec deployed`

---

## WAVE 4 — Cross-cutting closeout

### Task 4.1: Codebook + DDI refresh

**Files:**
- Run: `MAIN/deliverables/data-harmonization/generate_codebook.py`; inputs it reads were refreshed by Waves 1–3 (dcf/qsf, rewritten `F{n}-Skip-Logic-and-Validations.md`, `versions.json`, regenerated `f2-item-labels.json`)

- [ ] **Step 1:** From MAIN root: `py deliverables/data-harmonization/generate_codebook.py` — full xlsx/html/pdf set regenerates with the 3.0.0/4.0.0 stamps. "Unmatched skip sources" mentioning ONLY pre-Aug-17 names are expected residue of superseded spec rows; anything else = a Wave-1/2 spec-doc miss, loop back.
- [ ] **Step 2:** Refresh the Dictionary-Macros xlsx snapshot (`export_dcf_to_xlsx.py --all`) for reviewers.
- [ ] **Step 3:** Write `reports/tabulation-remap-note.md` — the old→new variable/code map extracted from the crosswalk, addressed to the PSA-tabulation owner (tabulation breakdowns key on codes).
- [ ] **Step 4: Remap decision recorded** — `generate_codebook.py` derives entirely from the NEW build artifacts, so it needs no `--remap` input; the crosswalk is the authoritative old→new mapping for downstream consumers (PSA tabulation, analysts, historical data), and its three tier columns ARE the Decision-5 "migration progress dashboard". Record both statements on the crosswalk's READ-ME sheet. Precondition check: `MAIN/deliverables/CSWeb/f2-item-labels.json` md5-matches the WT copy (Task 3.4). Commit (MAIN + WT) — `aug17: codebook + remap note`

### Task 4.2: CSWeb + fleet cutover readiness

- [ ] **Step 1:** Confirm the three new-generation CSPro packages are live on CSWeb (Wave-1/2 deploys) and `stamp_version.py show` reports no drift.
- [ ] **Step 2:** Tablet propagation — "Update Installed Applications" misses redeploys: issue the fresh-install instruction to the tester/enumerator channel per the CSEntry-update-propagation runbook note; verify one tablet per instrument shows the v3/v4 footer on the first screen.
- [ ] **Step 3:** Keep-and-filter posture check (no execution unless Carl schedules the cutover): pretest cases still tagged phase=pretest/A1; new-generation test cases classify under the correct activity; no purge, `oauth_*` untouched. The full cutover (runbook §4 minus step 4) runs when Carl declares the survey activity — out of this plan's scope.

### Task 4.3: Evidence pack + crosswalk final

- [ ] **Step 1:** Assemble `docs/uat-fix-evidence/<date>-aug17-migration/` (F1/F3/F4 tablet captures + F2 locale shots + scenario shot-trail index) with the SHA-pinned README per the uat-fix-evidence pattern.
- [ ] **Step 2:** Final `py aug17-tools/crosswalk.py` — every row shows tier1/tier2/tier3 green (or a register reference); deliver `aug17-crosswalk.xlsx` to Carl via file (never committed).
- [ ] **Step 3:** Wiki + memory + log updates (project CLAUDE.md rules): update `Source - Updated Survey Instruments (2026-08-17)` status line (CAPI update DONE, versions), `project_aspsi_aug17_instruments` memory, `log.md` entry. Commit (WT) — `aug17: evidence + closeout records`

### Task 4.4: ASPSI clarifications + translation work order

- [ ] **Step 1:** Finalize `aug17-ASPSI-clarifications.md` — reconcile against what implementation actually did (each item cites its register row + implemented default). Hand to Carl for dispatch through the ASPSI channel (his UP email; Carl does no DOH comms).
- [ ] **Step 2:** Emit the translation work order — concatenate the four `F{n}-translation-carryover.md` fell-back+new lists into `reports/aug17-translation-work-order.md`, grouped by instrument with paper Q numbers, ready for the ASPSI translation delivery ask. When that delivery lands, the existing translation pipeline (locale files + `audit-translations.py` + notes.json regen via `extract_notes.py` in MAIN) takes over — separate pass, out of scope here.
- [ ] **Step 3:** Final commit; hand the completion summary to Carl (versions deployed, crosswalk delivered, work order + clarifications ready to send).

---

## Wave gates (restated)

| Gate | Condition to pass |
|---|---|
| Wave 0 → 1 | All tools' pytest green; baseline paper tables spot-checked; register seeded |
| Instrument ships | `aug17_diff.py <inst>` exit 0 · static gates clean · `csentry_verify` green (CSPro) / `npm test`+`tsc -b --force`+e2e green (F2) · generator-diff two-stage subagent review done · Tier-2 matrix executed · Tier-3 evidence captured · crosswalk row statuses green |
| Wave 4 close | Codebook regenerated · remap note delivered · evidence pack assembled · clarifications + work order handed to Carl |

## Execution notes for the worker

- The **normalized paper CSV is the single content truth** during implementation. Never retype text from the docx or the wiki — copy from the CSV row (it came from the extract verbatim). If a CSV row looks wrong, fix `paper_tables.py` (or record a parse-limitation row in the register), regenerate, and only then edit content.
- When Tier-1 shows a diff you believe is correct-as-built, the fix is a register row with a rationale — never a normalization hack in the diff tool.
- Batch commits per task; MAIN and WT commits are separate (never push, never merge — Carl handles git publication).
- If CSEntry/Designer automation misbehaves (focus-steal guard raises, dialogs missing), stop and re-run — never type into unverified windows; don't use the desktop while drivers run.


