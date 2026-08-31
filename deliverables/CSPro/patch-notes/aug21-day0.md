# Aug-21 translations — Day 0 tooling notes

## Baseline delta 2026-08-25 (superseded by Fix round 1 below — see that section
## for the current numbers and the two corrections that changed them)

Tool: `deliverables/CSPro/data/translations-official/aug21_english_delta.py`
(Task 0 of `docs/superpowers/plans/2026-08-25-aug21-translations.md`). This is a
REPORT, not a gate — it never exits non-zero except on a missing input PDF.
F1/F2/F4 measured on the written build (dcf / items.ts); F3 measured on the
**pre-apply generator dictionary** via `--generator F3` (reuses
`migrate_maps_namekeys.capture_source_dict`), per the Task 0 pre-flight ruling
— the written `PatientSurvey.dcf` has already had `#714` facility-placeholder
neutralisation applied, which rewrites bracket placeholders to plain text and
would otherwise cause false diffs.

```
inst  match  total  diffs paper-only
F1      184    186      2          0
F2      125    134      9          1
F3      154    184     30          0
F4      129    166     37         27
```

(Run commands: `--only F1`, `--only F2`, `--only F3 --generator F3`, `--only F4`;
`--out` defaults to `deliverables/CSPro/data/translations-official/out-delta/`,
gitignored.)

### Per-instrument artefact list

**F1** — diffs: `30.1`, `75`.
- Q75 — real reword (paper: "amount" instead of build's phrasing) — confirmed
  content difference, matches the plan's expectation.
- Q30.1 — parser artefact, not a content reword: the paper inserts an inline
  instruction ("SELECT ONE ANSWER ONLY.") between the question and its
  parenthetical note that the build's item label does not carry. Documented,
  not fixed (instruction text belongs in a form-layout property, not the
  question label).
- paper_only: 0.

**F2** — diffs: `1`–`9` (all of Q1–Q9).
- Expected and documented in the plan: the paper's numbered employment-type
  *definitions* under Q2's help text reuse "1."–"9." as their own list, so
  every one of Q1–Q9's paper occurrences is that definition list, not the
  question restated. No English content changed on F2 (out of scope).
- Build item count = **134** (matches the Task 0 pre-flight ruling's expected
  count exactly). **Corrected in fix round 1** — the 7 excluded `id: 'Qn...'`
  occurrences are NOT all "subFields" as this note originally (and wrongly,
  self-contradictorily) said. Two different reasons, verified against the raw
  build and paper:
  - `Q71a`, `Q71b` (items.ts:139-140) ARE genuine top-level items
    (`section: 'G'`), not subFields — but ITEM_RE's `Q\d{1,3}(?:_\d)?` pattern
    doesn't match a letter-suffixed id, so they never enter the count. This
    isn't a coverage gap to widen the regex for: the Aug-21 paper itself never
    numbers them as their own gate-able entries either — it renders
    `71. If yes, what are the implications?` once, then folds `71a.` and
    `71b.` in as un-numbered sub-labels under that same "71." occurrence
    (`71a. <For those who answered "Yes" in Q69>` / `71b. <...Q70>`, verified
    against the raw PDF text). Out of the numbered-English gate by design on
    both sides.
  - `FB1`–`FB5` are genuine top-level items too, but their ids never start
    with `Q` at all — end-of-survey feedback questions with no question
    number on either the build or the paper, so ITEM_RE's `Q`-prefix
    correctly never matches them regardless of numbering.
  - The real `subFields` (`Q1_1`/`Q1_2`/`Q1_3`/`Q9_1`/`Q9_2`) are excluded
    correctly, as designed — but were never part of this 7-item count in the
    first place: they carry no `section:`, so they were never among the 141
    top-level `section:`-bearing ids to begin with.
- paper_only: `71` — the paper numbers a Q71 that the build only carries as
  `Q71a`/`Q71b` (no bare `Q71` item). Documented, not fixed here.

**F3** (measured on the pre-apply generator dictionary) — diffs: `1`–`9`,
`47`, `69`, `94`, `96`, `98`, `106`, `107`, `109`, `112`, `113`, `115.1`,
`129`, `131`–`134`, `136`–`140`.
- Real rewords / structural differences confirmed present, as the plan
  requires: `47`, `69`, `94`, `96`, `98` are all diffs. `106`–`113`,
  `131`–`140` are the bill-detail / rating-scale rows where the build's short
  roster-row label doesn't restate the full paper question (expected — the
  full question lives once, above the roster).
- **Deviation from the plan's prediction, verified not a tool bug — survives
  fix round 1's tightened bracket rule:** `66` and `88` are listed in the plan
  as items that "must still appear as diffs (real rewords)". Measured against
  the pre-apply generator dictionary (the ruling-mandated method), both are
  genuine content **matches** — the only difference is the facility-placeholder
  token (build: `[facility_name_input]` / `[FACILITY_NAME_INPUT]`, paper:
  `[facility_name]`), a MID-sentence fill placeholder in both ("Is
  `[facility_name]` the facility...") that `textnorm.norm()` correctly folds
  away on both sides. Fix round 1 tightened `norm()` to stop folding away
  LEADING bracket instructions (see F4 below, where that WAS hiding a real
  gap) — that tightening does not touch this mid-sentence case, so `66`/`88`
  correctly remain matches, not diffs, under the corrected rule too. This is a
  genuine mismatch between the plan's prediction (written before the
  facility-placeholder normalisation was confirmed against the real Aug-21
  paper) and the current F3 build/paper text, not tool leniency — flagged for
  Carl, not silently fixed away.
- **Deviation from the plan's prediction, also verified:** the plan says
  `paper_only` should list `97.1`, `97.2`, `115.1`, `115.2` as "un-numbered
  stubs by design". Measured against the actual F3 generator, all four ARE
  numbered build items (e.g. build `115.1` = `"115.1 Other items included in
  the bill — Doctor's Professional Fee"`), so they correctly appear as content
  **diffs** (the paper's full checkbox list vs. the build's per-row roster
  label), not as `paper_only`. `paper_only` for F3 is empty. This is a factual
  mismatch between the plan text and the current F3 generator — flagged for
  Carl, not something Task 0 should paper over.
- paper_only: 0 (see above).

**F4** — diffs: `2`, `30`, `35`, `36`, `40`, `42`–`49` (incl. `45.1`, `45.2`),
`67`, `117`, `118`, `131`, `135`, `157`, `177`, `182`, `185`, `186`–`202`.
- Required diffs present: `30`, `35`, `36`, `40`, `67`, `117`, `118`, `131`,
  `135` — **fixed in round 1**. `117`/`131`/`135` were false MATCHES before
  the fix: the paper's LEADING bracket instruction (`[Answer only "yes" in
  Q112]`, `[Ask only if they went to a DOH-retained hospital]`) was being
  stripped by the Step-3 spec's original unconditional bracket rule, same as
  F3's mid-sentence facility-placeholder fills — but a build that carries no
  such instruction anywhere is a real content gap, not noise to normalise
  away. `textnorm.norm()` now only strips a bracket that has non-whitespace
  text before it (a mid-sentence fill); a bracket at the very start of the
  string is left as literal words, so it no longer prefix-matches a build stem
  that lacks it. Re-measured after the fix: F4 dropped from 129/166 match to
  126/166 (37 diffs → 40), all three required rows now present, with no
  change to F1 (184/186), F2 (125/134), or F3 (154/184, `66`/`88` still
  correctly match — see above).
- `42`–`49`, `186`–`202` and the `Q157/177/182/185` auto-computed totals are
  new-instrument items the paper doesn't carry in the same numbered form
  (financial-module questions added/renumbered in the Aug-21 revision) —
  document, no fix expected here.
- paper_only: 27 (`142`, `144`–`170` excl. `157`) — the paper's C1 household
  roster/finance block has more numbered sub-items than the build's current
  numbering in that range. Matches the plan's expectation that the spurious
  27-row paper_only band would shrink to "numbers the paper really has beyond
  the build" rather than disappear.

### Wave rule (replaces "diffs 0")

Each wave's "align EN" task re-runs `aug21_english_delta.py --only F<n>`
(F3 measures the generator dict by default now, with or without
`--generator F3` — fix round 1) before its extraction step, and must reach
diffs limited to the documented artefact list above for that instrument — any
new, undocumented diff blocks the wave until triaged.

## `.gitignore`

One block appended at the end of the repo-root `.gitignore`
(`# Aug-21 translation import (2026-08-25)`) covering `out-delta/`,
`out-aug21/`, `aug21_apply_diff.json`, `aug21_pre_findings.json`,
`aug21_post_findings.json` under
`deliverables/CSPro/data/translations-official/`. Verified with
`git check-ignore -v` against `out-delta/f1_english_delta.json`.

## Fix round 1 (2026-08-25)

Three review findings fixed in `aug21_english_delta.py` / `textnorm.py`; the
per-instrument sections above are corrected in place (not left as a separate
stale record) and marked "fixed in round 1" / "corrected in fix round 1"
wherever a number or a rationale changed.

1. **F3 default routing.** The bare `python aug21_english_delta.py` used to
   silently measure F3 on the WRITTEN `PatientSurvey.dcf` (the one method the
   reconciled interface forbids), and the correcting `--generator F3` flag
   used to filter the run down to F3 alone, dropping F1/F2/F4 — so no single
   command ever produced a correct four-instrument table. Fixed: F3 now
   always measures the pre-apply generator dict (`GENERATORS` membership
   decides this, not the flag); `--generator` is still accepted but no longer
   filters `--only`. Re-run of the bare command from repo root, one process,
   all four instruments, F3 on the generator dict:
   ```
   inst  match  total  diffs paper-only
   F1      184    186      2          0
   F2      125    134      9          1
   F3      154    184     30          0
   F4      126    166     40         27
   ```
   (F4's numbers already reflect fix 3 below, measured in the same run.)
2. **F2 exclusion-list rationale.** The original note called all 7 excluded
   `id: 'Qn...'` occurrences "subFields" — false, and self-contradicting its
   own next line. Corrected in the F2 section above: `Q71a`/`Q71b` are real
   top-level items excluded because the paper itself never numbers them as
   independent gate-able entries (folded into Q71's own occurrence); `FB1`–
   `FB5` are real items whose ids simply aren't `Q`-prefixed; the true
   `subFields` were never part of the 141-id top-level count to begin with.
   No behaviour change — the 134 count and diffs are unchanged; only the
   documentation was wrong.
3. **Leading vs. mid-sentence brackets.** `textnorm.norm()` used to strip
   ANY bracketed run unconditionally, so a paper-only LEADING instruction
   bracket (F4 `117`/`131`/`135`: `[Answer only "yes" in Q112]`) was folded
   away exactly like a MID-sentence fill placeholder (F3 `66`/`88`:
   `[facility_name]`) — hiding the fact the build carries no such instruction
   anywhere. Fixed: only a bracket preceded by non-whitespace text is
   stripped now; a leading bracket is left as literal words, which fails to
   prefix-match a build stem that lacks them. Re-measured (see table above):
   F4 match dropped 129→126 / diffs rose 37→40, with `117`/`131`/`135` now
   present as required; F1/F2 unchanged (no brackets involved); F3's
   legitimate mid-sentence matches (`66`/`88`, `143`/`162`/`172`) are
   unaffected — confirmed by re-running `--only F3` and diffing the printed
   Q-list against the pre-fix run.

Tests: `deliverables/CSPro/data/translations-official/test_aug21_english_delta.py`
gained 5 cases covering all three fixes (`test_norm_strips_midsentence_bracket_but_keeps_leading_instruction`,
`test_compare_flags_paper_only_leading_instruction_as_diff`,
`test_compare_matches_midsentence_facility_placeholder_regardless_of_token`,
`test_generator_flag_does_not_filter_the_instrument_list`,
`test_f3_uses_the_generator_by_default_with_no_flag`). Full run:
`cd deliverables/CSPro/data/translations-official; python -m pytest
test_aug21_english_delta.py -q` → `9 passed`.

**Still open, not a tool defect — flagged for Carl:** F3 `66`/`88` remain
matches, not diffs, even under the tightened rule (they're mid-sentence
facility-placeholder fills on both sides, genuinely the same content). The
brief's Step-5 acceptance table predicted these as required diffs; that
prediction does not hold against the actual current F3 build + paper text.
The fix in this round specifically targeted and resolved the class of bug the
review found (a paper-only LEADING instruction bracket producing a false
match); it does not — and should not — turn a genuine mid-sentence content
match into a diff. If this is still felt to be wrong, it needs an explicit
ruling, not further tool tightening (further loosening the mid-sentence rule
would just reintroduce the same false-match class this round fixed).

## Extractor

Tool: `deliverables/CSPro/data/translations-official/anchor_extract.py` (Task 1).
Anchors come from the **BUILD's** English via `cspro_helpers.walk_labeled_nodes()`,
so keys are byte-identical to what `apply_translations()` looks up. Output
(`out-aug21/<INST>/{loc}.json`, `{loc}_flagged.json`, `QA-REPORT.md`) is
gitignored; **nothing** is written into the build or into `F<n>/translations/` —
`apply_aug21.py` is the only writer.

Two standing rules, both load-bearing:

- **F3 anchors always come from `--generator F3`**, never from the written
  `PatientSurvey.dcf` — that file is written *after* `#714` facility-placeholder
  neutralisation, so its English is not the English the paper was translated
  from. (`capture_source_dict` re-runs `generate_dcf.py`; verified byte-identical
  — `git status --short deliverables/CSPro/F3` was empty after both runs.)
- The June-5 script at `deliverables/CSPro/translations-paper-extract/` is
  **superseded for imports**. It stays on disk (gitignored) as the historical run
  record only; its text-prep/span/QA code was copied verbatim into the committed
  tool, since a committed tool must not import a gitignored file.

### F1 — 1349 anchors, `FacilityHeadSurvey.dcf` (written build)

| locale | anchored | clean | flagged | differ from live |
|---|---|---|---|---|
| FIL | 434 | 839 | 167 | 169 |
| BCL | 434 | 833 | 173 | 186 |
| BIS | 433 | 820 | 185 | 188 |
| CEB | 435 | 817 | 191 | 171 |
| WAR | 429 | 869 | 132 | 208 |
| HIL | 434 | 863 | 144 | 199 |
| ILO | 432 | 848 | 156 | 253 |

Flag digest top 3: `empty` 389, `table-bleed` 320, `length-ratio` 311.
(New flags: `glued-short-label` 41, `ends-with-other-label` 11.)

### F3 — 1710 anchors, `--generator F3` (pre-apply dictionary)

| locale | anchored | clean | flagged | differ from live |
|---|---|---|---|---|
| FIL | 554 | 804 | 291 | 317 |
| BCL | 559 | 762 | 331 | 160 |
| BIS | 570 | 795 | 316 | 145 |
| CEB | 570 | 801 | 304 | 180 |
| WAR | 572 | 817 | 299 | 172 |
| HIL | 550 | 702 | 383 | 94 |
| ILO | 567 | 846 | 264 | 115 |

Flag digest top 3: `table-bleed` 752, `length-ratio` 732, `empty` 636.
(New flags: `glued-short-label` 298, `ends-with-other-label` 127.)

The **differ** column is the number of clean pairs whose value is not what the
live map holds today — i.e. exactly what a `--apply` would overwrite. It must be
explained by the merge dry-run before anything is applied (Tasks 4-7).

### Notes for the later waves

- `glued-short-label` is **not** ILO-specific and nowhere near the ~25% share
  that would justify raising its 4-char floor for Ilocano: per-locale it is
  3.5% of ILO's F1 flags (6/171) and 13.0% of ILO's F3 flags (45/347), against
  3.2% / 12.9% for FIL. No per-locale floor is needed; decide finally in Task 6.
- The "is this anchor part of my own English?" guard on both new flags is
  **word-bounded** (`" male "` inside `" male nurse "`, but not inside
  `" female "`). A plain substring guard suppressed 11 of F1's 26 short-anchor
  collisions - including `("male", "female")`, the 2026-08-17 spill itself. Fixed
  2026-08-25 (fix round 1); the numbers above are the post-fix run (F1 BIS moved
  822/183 -> 820/185, `glued-short-label` 39 -> 41; F3 unchanged).
- `is-other-label` (F1 5, F3 56) and `glued-short-label` samples are printed in
  each `QA-REPORT.md`; they are the worst classes and feed the
  `aug21-overrides.json` review in Task 6.
- Anchors drop the `— Hours` / `— Minutes` component suffix (mirror of
  `generate_qsf._strip_component_suffix`), so `item:Q67_TRAVEL_HH` anchors on
  `"67. How much time does it take to reach the nearest pharmacy from your
  home?"`. F4 Q67 still does not match, but for an English reason, not a suffix
  one: the Aug-21 paper reads *"how much time does it take **for you** to
  reach"*. That is Task 27's English alignment, and it is why English alignment
  must precede extraction in every wave.
- Container labels (`dict:` / `level:` / `record:`) are deliberately **not**
  anchored: they are page furniture that matches headers/footers and opens
  spurious spans.

## Task 2: regression lock

`test_anchor_extract.py` gained
`test_extractor_output_is_accepted_by_apply_translations` — a synthetic
`--instrument F9` fixture is extracted, then the written `fil.json` is fed
straight into the real `cspro_helpers.apply_translations()` (not a mock),
proving zero legacy (non-`:`) keys and a labels-node shape the walker fully
covers. Regression lock, not fail-first: passed on first run, as Task 1's
`write_outputs`/`dcf_anchors` already emit name-scoped keys and only
dict/level/record/item/valueSet/value nodes.

```
cd deliverables/CSPro/data/translations-official
python -m pytest test_anchor_extract.py -q -k accepted   # 1 passed
python -m pytest test_anchor_extract.py test_aug21_english_delta.py -q   # 20 passed
```

## F1 raw yield (extractor only, pre-merge)

Real-data round trip: `cspro_helpers.apply_translations()` fed the F1
`out-aug21/F1/` extractor output directly (no live-map edits), from repo root:

```
$env:PYTHONIOENCODING='utf-8'
@'
import sys
sys.path.insert(0, "deliverables/CSPro")
sys.path.insert(0, "deliverables/CSPro/F1")
from cspro_helpers import apply_translations
import generate_dcf as g
apply_translations(g.build_dictionary(), "deliverables/CSPro/data/translations-official/out-aug21/F1")
'@ | python -
```

No `SystemExit`. Result — **pre-alignment (Q75 not yet reworded)**, a
key-presence count only (still includes whatever `glued-short-label` /
`ends-with-other-label` did not catch); not "usable yield" until the merge
dry-run (Tasks 3-7) reconciles the `differ` column below against it:

```
    FIL: 839/1363 labels translated (61%)
    BCL: 833/1363 labels translated (61%)
    BIS: 820/1363 labels translated (60%)
    CEB: 817/1363 labels translated (59%)
    WAR: 869/1363 labels translated (63%)
    HIL: 863/1363 labels translated (63%)
    ILO: 848/1363 labels translated (62%)
```

F1 `differ from live` counts (from the extractor table above, baseline live
map FIL67 BCL67 BIS67 CEB63 WAR67 HIL66 ILO62):

| locale | differ from live |
|---|---|
| FIL | 169 |
| BCL | 186 |
| BIS | 188 |
| CEB | 171 |
| WAR | 208 |
| HIL | 199 |
| ILO | 253 |

Together these are the before-columns of the Wave-1 coverage table. Neither
the 1363-total yield percentages nor the differ counts are "usable yield" on
their own — the merge dry-run in Tasks 3-7 reconciles them.

## Task 5: merge dry run (`apply_aug21.py` CLI)

`apply_aug21.py` gained the CLI half of the merge tool: `load_extract`,
`stamp_meta`, `run`, `built_dcf_keys`, `print_table`, `main`. Default report path
is the TOOL directory (`data/translations-official/aug21_apply_diff.json`,
gitignored), printed absolute at the end of every run. `--unmatched` reads the
already-BUILT `F<n>/<App>.dcf` for the anchor denominator — no generator run, so
a dry run cannot rewrite the `.dcf`.

**F1 dry run (2026-08-25) — the Wave-1 "before" row.**

```
python data/translations-official/apply_aug21.py --only F1 --unmatched

F1  locale  written replaced override  same flagged unmatched
    fil         177      169        0   493     167       357
    bcl         189      186        0   458     173       357
    bis         160      188        0   472     185       358
    ceb         187      171        0   459     191       355
    war         212      208        0   449     132       362
    hil         192      199        0   472     144       356
    ilo         211      253        0   384     156       359

DRY RUN - diff written to ...\data\translations-official\aug21_apply_diff.json
```

`replaced` per locale: FIL 169, BCL 186, BIS 188, CEB 171, WAR 208, HIL 199,
ILO 253 — **identical, locale for locale, to the extractor's "differ from live"
column** recorded in the F1 raw-yield section above. That is the reconciliation
that section asked for: every pair the extractor flagged as differing from the
live map is exactly one `replaced` row in the merge, and nothing else is.
`override` is 0 for all seven locales because `aug21-overrides.json` is still
empty (Task 6 seeds it).

`written` (new keys) + `replaced` = the writes a `--apply` would make; `same`
(already identical) and `flagged` (never written) account for the rest.
`unmatched` ≈ 357/1349 build anchors the Aug-21 F1 paper never yielded a clean
pair for in that locale.

Nothing was written: `git status --short deliverables/CSPro/F1` is empty after
the run — no `translations/*.json` change and no `FacilityHeadSurvey.dcf`
change.

**One latent bug fixed on the way.** `apply_safe.load_map()` read the map with
Python's default universal-newline translation, so the `crlf` flag it returns
could never be `True` — `save_map()` would then rewrite a CRLF map entirely with
LF endings (a 100%-of-lines diff on every write). Every live map is LF today, so
this never bit, but the Aug-21 merge is the first tool to write maps in bulk.
Fixed by reading with `newline=""`; both call sites (`apply_safe` itself and
`apply_aug21.run`) pass the flag straight back to `save_map`, so real-data
behaviour is unchanged and only the CRLF branch starts working.

## Extractor layout rules (Task 16b)

Task 17 blocked on 2026-08-25 because the Aug-21 extract glued English interviewer
furniture into 830 of the 1,374 values `--apply` would have written. The cause was not the
QA flags — it was the paper's LAYOUT, which `anchor_extract.py` (a June-5 tool) had never
been shown. Five rules were added to it; nothing else about the span algorithm changed,
and where none of the five fires the extractor's answer is byte-identical to before
(`test_plain_span_is_untouched_by_the_layout_rules`).

### 1. Interviewer directives are excised, not anchored around

The Aug-21 papers print the instruction **between** the English question and its
translation, and again in the local language, in ALL CAPS:

```
12.2. What is the main role of the public health unit? READ OPTIONS OUT LOUD.
SELECT ONE ANSWER ONLY. Ano ang pangunahing tungkulin ng public health unit?
```

`DIRECTIVE_PATTERNS` (22 case-insensitive, word-bounded regexes) is harvested from the 21
`text-aug21/*.txt` dumps — every recurring ALL-CAPS run plus the mixed-case enumerator
notes. Hits across all 21 dumps (`len(rx.findall(blob))`, so nested families double-count):

| pattern family | hits | pattern family | hits |
|---|---|---|---|
| `PROCEED TO Q<n>` | 1237 | `ENUMERATOR:` | 140 |
| `READ [ALL] [THE] OPTIONS [OUT LOUD\|ALOUD]` | 1028 | `DO NOT ASK` | 112 |
| `SELECT ALL THAT APPLY` | 791 | `NOTE TO ENUMERATOR […]:` | 108 |
| `DO NOT READ [THE] [OPTIONS] [OUT LOUD\|ALOUD]` | 683 | `ENUMERATOR NOTE\|INSTRUCTION […]:` | 77 |
| `AMOUNT IN PESOS` | 578 | `SKIP TO Q<n>` | 26 |
| `SELECT ONE ANSWER ONLY` | 476 | `READ OUT LOUD` | 22 |
| `SELECT ALL THE ANSWER OPTIONS …` | 20 | `FOR [THE] ENUMERATOR …:` | 20 |
| `IF NO RECEIPT WAS PROVIDED` | 19 | `IF MORE THAN ONE, ASK FOR THE MAIN SOURCE` | 14 |
| `SKIP THIS QUESTION WHEN …` | 14 | `PLEASE LIST DOWN ALL MEDICINES …` | 14 |
| `PROBE:` | 13 | `IF YES[,] INDICATE\|SPECIFY` | 11 |
| `SKIP IF ANSWERED …` | 8 | `INTERVIEWER NOTE\|INSTRUCTION […]:` | 0 |

`INTERVIEWER …` scores 0 on the Aug-21 pack; it is in the list because the brief named it and
because it is the obvious sibling of `ENUMERATOR NOTE` — a directive that costs
nothing to carry and that a later pack may well print.

**Deviation from the Task-16b brief, on evidence.** The brief specified "the candidate is
the text AFTER the LAST directive match". That is right for the Tagalog/Cebuano layout but
wrong for the Ilocano one, where the translation comes **first** and the directive last:

```
52. Which of the following requirements were difficult to comply with for
accreditation? (Ania kadagiti sumaganad a kasapulan ti narigat a tungpalen para iti
akreditasion?) READ OPTIONS OUT LOUD. SELECT ALL THAT APPLY.
(BASAEN TI OPTIONS ITI NAIPAAY. PILIEN AMIN NGA AGaplikar.)
```

Worse, every paper repeats the directive in the local language, in ALL CAPS, so "after
the last match" lands on THAT: measured by re-running the whole F1 extract with the
brief's rule, **at least 332** of the seven locales' clean values (FIL 70, BCL 52, BIS 66,
CEB 64, WAR 66, HIL 6, ILO 8 — a lower bound, it only counts values that are fully
uppercase) become the translated directive instead of the translation. A new defect in
place of the old one.

`strip_directives()` therefore **excises** each directive and keeps the text on both sides, which is correct for both layouts.
`skip_translated_directive()` additionally consumes the local-language repeat: an unbroken
run of ≥ 3 capitalised words immediately after an English directive. That test is layout,
not vocabulary, so it needs no per-language list — and it is scoped to "right after a
directive" so a real acronym run (`BUCAS, GAMOT, NBB, ZBB` inside a question) is untouched.

Nothing is left in the value: if the paper printed only the directive, the row is flagged
`directive-only`; if a directive survives cleaning at all, it is flagged `directive-bleed`
and can never be clean. The instruction text itself already has a home — `extract_notes.py`'s
`note:const:_READ_ONE/_READ_ALL/_SELECT_ONE/_DNR_ALL/_DNR_UNPROMPTED` keys.

### 2. One-line option rows

`☐ Yes Oo ☐ No Hindi` — `No` is below `MIN_BOUND`, so it never bounded `Yes`'s span and the
value came out `Oo No Hindi`. Two changes:

* a **sub-`MIN_BOUND` option label anchors when it sits behind a ballot box**
  (`behind_box()`), so it both emits its own translation and bounds its siblings'. The box
  is load-bearing, not decoration: Ilocano `no` means "if", and the F1 ILO paper has 154
  word-bounded `no` of which only 67 are behind a box — anchoring the bare word would chop
  87 real translations mid-sentence.
* **no span crosses a box glyph** (`cut_at_box()`). A stem's translation is printed before
  its option row, and an option's before the next box.
* `MAX_OCC` 64 → 400: a box-anchored `Yes`/`No` occurs ~60× per paper and must bound
  *every* row it opens.

Cost, measured and accepted: where a paper puts the English option and its translation in
two **adjacent** box rows (`☐ LGU Outreach (e.g., …) ☐ Serbisyo gawas ha LGU (…)`), the box
cut loses the translation — 4 values across the seven F1 locales, all of which become
`empty` worklist rows. Without the box cut, 5+ values per locale instead ship glued English
(`… nag-iha? Less than 30 days Waray pa 30 ka adlaw`). Furniture in a live map is the worse
outcome, so the box cut stays.

### 3. Routing notes

`SKIP_NOTE` widened from 60 to 200 chars (`<Question for facilities that are only
YAKAP-accredited, otherwise proceed to Q88>` is 78), plus `TRAILING_NOTE` for a note the
span cut in half (its `>` is past the next anchor) and `ARROW_NOTE` for `→ Q51` / `-> Q51`.
A residual `<` or `>` is flagged `routing-note` — that catches a note's *tail*
(`Hindi ito naaangkop sa mga ospital>`), which is furniture, not a translation.

### 4. Condensed labels (the Q75 class)

`item:Q75_IS_1700_ENOUGH`'s dcf label is a CSPro-255-cap condensation of a longer paper
paragraph, so the verbatim anchor was never found — and an anchor that is never found
produced **no output at all**, neither clean nor flagged. Q75 stayed English in all seven
locales and nobody saw it, while `item:Q74_REGISTERED_PATIENTS`'s span ran on into Q75's
English paragraph.

`anchor_prefix()` gives any label longer than 12 normalised words a fallback anchor: its
first 12 words, used only when the full label is absent and only if the prefix occurs
exactly once. Finding it also **ends the previous anchor's span**, which is what fixes the
Q74 bleed. The span then opens with the rest of the paper's English, so
`condensed_candidate()` drops leading sentences that read as English
(`extract_notes.looks_english`) or that are literally part of the label — the label's tail
("Based on your practice, is this enough?") scores below `looks_english`'s three-function-word
bar, hence the second test. The pair is **always** flagged `label-condensed`, never clean:
the translator has to confirm which English the translation answers. 52–53 rows per locale.

### 5. `not-in-paper`

Every anchor the paper never printed is now written to `{loc}_flagged.json` with
`tr: ""` and flag `not-in-paper`, so it reaches the Task-45 translator worklist instead of
vanishing. 160–167 rows per locale for F1. Anchors below `MIN_EMIT` are still skipped, and
are counted in QA-REPORT.md as `sub-min-emit` (1 for F1 — `item:REGION`).

### Before / after — F1, over the seven `out-aug21/F1/{loc}.json` CLEAN maps

Both columns measured, not quoted: the pre-task extractor was re-run from
`<ws>/task-16b/before/` into a scratch out dir and reproduced Task 17's numbers exactly.

| metric (all 7 locales) | before | after |
|---|---|---|
| values matching a `DIRECTIVE_PATTERNS` regex | **855** | **0** |
| values with an English `Yes … No` pair or a sibling option's English | **345** | **0** |
| values containing `<` or `>` | **159** | **0** |
| `item:Q75_IS_1700_ENOUGH` | absent from clean AND flagged, ×7 | `label-condensed`, ×7 |
| clean pairs | 839/833/820/817/869/863/848 | 1044/1023/1025/1009/1042/1033/1040 |
| flagged rows | 167/173/185/191/132/144/156 | 303/324/322/338/305/314/307 |
| `differ from live` | 169/186/188/171/208/199/253 | 133/162/185/145/205/152/266 |

(855 vs the Task-17 report's 857 is the denominator: that count was over the `--apply`
write set, this one over the clean maps.)

Per-locale before→after clean-map churn: 666/640/640/626/658/657/662 values unchanged,
172–201 changed, 175–207 newly clean (the `Yes`/`No`/`Male`/`Female` option translations
that could never anchor before), 1–30 lost — every lost one now carries a flag
(`routing-note`, `starts-mid-english`, `directive-only`, `empty`).

Dry run `apply_aug21.py --only F1 --unmatched`: `replaced` **1,248** (was 1,374 with 830
poisoned); **0** of the 1,248 carries a directive, a `Yes … No` pair or an angle bracket.

### `--unmatched` → the `dcf-unanchored` column

The column counts BUILT-dcf keys the extract produced nothing for — the opposite direction
from the "extract key with no map key" the Task-17 brief described, and non-zero by
construction. It is printed as `dcf-unanchored`, its `--help` says INFORMATIONAL and names
the real drift check (`anchor_extract.py`'s own `keys not in dcf: []` line), and it is no
longer a STOP condition anywhere. With `not-in-paper` rows now emitted it fell from
~357 per locale to **16**: the 14 `dict:`/`level:`/`record:` container keys excluded from
`ANCHOR_KINDS` by design, plus `item:REGION` / `vs:REGION_VS1` (sub-`MIN_EMIT`).

### New flags

`directive-only`, `directive-bleed`, `grid-bleed`, `routing-note`, `label-condensed`,
`not-in-paper` — all six documented in `MEAN` and counted per locale in a new
"Aug-21 layout flags per locale" table in `QA-REPORT.md`.

### Not fixed here

* The English **notes** the Ilocano paper prints between the question and the options
  ("These are the requirements for YAKAP/Konsulta accreditation outlined by DOH.") are not
  directives and stay inside those spans. They are `note:`-layer content (Task 8).
* `item:Q12_2_PHU_ROLE` still truncates at "Ano ang pangunahing tungkulin ng" because the
  Tagalog keeps "public health unit" in English and that phrase is itself an anchor. That
  is the pre-existing boundary/truncation class Task 17 reviews, not a layout rule.
* `anchor_extract_f2.py` imports `clean_span`/`qa_flags` from this module, so the F2
  extract in `out-aug21/F2/` (Tasks 13/14) predated these rules. It has been re-run — see
  "F2 re-run" below.

Tests: `test_anchor_extract.py` gained 20 tests (79 → 99 in `translations-official`);
`aug17-tools` unchanged at 121 passed + the 1 pre-existing CRLF-fixture failure.

### F2 re-run (fix round 1)

`anchor_extract_f2.py` borrows `clean_span()` / `qa_flags()` from this module by explicit
path, so the layout rules reach the F2 extract for free — but only when the extract is
re-run. The copy in `out-aug21/F2/` was produced by Tasks 13/14 **before** the rules
existed and still carried the furniture, so it was re-run against this extractor:

```
python anchor_extract_f2.py \
  --source ../../../../raw/Survey-Instruments-2026-08-21/Translations \
  --english-strings ../../../F2/PWA/app/spec/english-strings.json \
  --out out-aug21/F2
```

Over the seven `out-aug21/F2/{loc}.json` CLEAN maps:

| metric, all 7 F2 locales | before (Tasks 13/14) | after |
|---|---|---|
| values matching a `DIRECTIVE_PATTERNS` regex | **167** | **0** |
| values containing `<` or `>` | **115** | **0** |
| union of the two (the poisoned set) | **224** | **0** |
| clean pairs | 1,932 | 1,897 |
| flagged rows | 592 | 627 |

Churn: 1,708 values unchanged, 187 changed (the directive/note excised in place), 2 newly
clean, 37 dropped from the clean maps — and **all 37** appear in the matching
`{loc}_flagged.json`, so nothing is silently lost. `grid-bleed` cannot fire on F2: the
F2 extractor calls `qa_flags(en, tr, nlabels)` positionally and never passes `siblings`,
which is correct — F2 has no value sets, and its own box-prefix anchor rule
(`SHORT_ANCHOR`) already bounds the one-line option rows.

The F2 apply tool was re-checked in dry run (`python scripts/apply-paper-translations.py`,
nothing written, `git status --short spec/translations` empty): the incoming write+replace
set fell from 649 rows to 485, of which **0** carry a directive, an angle bracket or an
English `Yes … No` pair.


## Extractor layout rules, round 2 (Task 16c)

Task 17 attempt 2 ran a by-category sweep over **every** value `apply_aug21.py --only F1`
would write and found **249 of 2,690 (9.3%) still defective**: 149 truncated, 66 English
furniture, 26 local-language directives, 8 value-set offsets — and **79 of them on keys the
maps do not hold yet**, which `aug21-overrides.json` could not reach at all. This round
closes that layer. No live map, `.dcf`, `.apc`, `.fmf` or `.qsf` was touched; `--apply` was
not run.

### 1. A one-word `val:` option label bounds a span only behind a ballot box

Task 16b introduced `behind_box()` for sub-`MIN_BOUND` labels (`Yes`, `No`). The
truncations came from the labels just ABOVE that floor: `PhilHealth` (10 normalised chars),
`Public`, `Private`, `Facility`, `Monthly`, `Quarterly`, `Female`, `Midwife` … 37 one-word
`val:` anchors in F1 alone. Each of them is a legal boundary at every occurrence, including
its occurrences inside a translated sentence — so `Mayroon bang public health unit ang
pasilidad na ito?` shipped as `Mayroon bang`.

The gate is now: a normalised label that is ONE WORD and belongs to nothing but `val:` keys
anchors only where it sits behind a box. Multi-word option labels are deliberately NOT
gated — `Single, never married` never turns up mid-sentence, and plenty of papers print
option rows with no box at all (`test_multi_word_option_labels_still_bound_without_a_box`).

### 2. Two more directives, and the English NOTES leave the span

`DIRECTIVE_PATTERNS` += `TICK THE CATEGORY THAT CORRESPONDS…` and `No\.? of [Dd]ays\s*:?`
— the day-count grid header the Aug-21 F1 papers print on Q49/Q50/Q107 (38 rows).

The papers' English NOTES are a different animal and get a different rule. `These are the
requirements for YAKAP/Konsulta accreditation outlined by DOH.` (Q52) and `Our focus is
specifically on referrals external to the facility…` (Q142) are printed, in all seven
locales, AFTER the question's translation and BEFORE the option rows — so the note **ends
the span** (`cut_at_note()`), exactly as a ballot box does. Excising it instead would keep
the note's LOCAL translation and glue it onto the question label, which is how the June-5
`bcl` map came to hold `… para sa akreditasyon? Ini an mga requirements para sa
YAKAP/Konsulta accreditation kan DOH.`

Q44's capitation gloss (`Capitation is the amount per year per registered patient…`) is
English furniture too, but the papers do not agree on where they print it: BEFORE the
translation in fil/bcl/war/hil/ilo, AFTER it in ceb. Cutting there would throw five real
translations away, so it is flagged `english-furniture` and never cleaned — the worklist
row still carries the text for the translator to salvage. `has_furniture()` is the net
under the span cut, exactly as `has_directive()` is the net under `strip_directives()`.

### 3. `local-directive` — the repeat with no English original in front of it

`skip_translated_directive()` consumes a ≥3-word capitalised run **immediately after** an
English directive. Where the paper prints only the local rendering, or prints it after the
translation rather than after the English directive, nothing consumes it:

```
[bcl] vs:Q36_QUALITY_CHALL_VS1  '… sa saindong lugar? Dae pagbasahon ki makusog. Pilion an
                                 mga dapat na kasimbagan na itatao sa respondent'
[ceb] vs:Q13_2_HPU_ROLE_VS1     '… sa health promotion unit? BASAHA UG KUSOG ANG MGA TUBAG.
                                 PILI USA LANG KA TUBAG'
```

These are FLAGGED, not excised. Excision would need to fire on an ALL-CAPS run anywhere in
the span, and a real acronym run (`BUCAS, GAMOT, NBB, ZBB` inside a question) is the same
shape; the flag can tell them apart because it also has the anchor's own English to check
against, and `clean_span()` does not. Cost: 26 F1 rows and 20 F2 rows become worklist rows
instead of shipping a directive. Measured before the rule was written, over the seven F1
and seven F2 clean maps (9,113 values): **40 hits, every one a real directive, no false
positive**.

### 4. Overrides are consulted BEFORE the "key absent → write" branch

`merge_locale()` reached `r.writes[key] = val` without ever looking at
`aug21-overrides.json`, so an override — which names a value to *keep* — had no meaning for
a key the map does not have. 79 of the 249 defective values were exactly that, and there
was no lever to hold them back. Now:

* `"keep": null` = **never write this key**, new or existing (counted `override`);
* `"keep": "<text>"` on a key the map does not hold = **write that text** (counted
  `override`);
* everything else is unchanged — an existing key with an override still keeps its current
  value, and `override_stale` still warns when the `keep` text has drifted from the map.

`aug21_overrides.validate_overrides()` accepts `keep: null` on F1/F3/F4 keys (F2 already
allowed it). A non-string, non-null `keep` is still a schema error.

### 5. Round-2 polish on the 16b rules

* `clean_span()` strips a lone `(` / `)` left behind when the span cut one half of the
  Ilocano parenthesised layout away, and returns `""` for a candidate with no alphanumerics
  at all (an `empty` worklist row beats a one-glyph value). This alone fixed 16 F2 values.
* `directive-only` is set only when the cleaned residue is **empty** — it claims the paper
  printed no translation, and a sub-`MIN_EMIT` residue is not nothing. A routing-note tail
  now keeps `routing-note` alone.
* `TRAILING_NOTE` strips only a fragment that opens with a word (`<\s*[A-Za-z]`), so the
  option label `<18 years` falls through to the `routing-note` flag instead of being
  silently truncated to `Wala pa sa`.
* the `grid-bleed` sibling scan ignores siblings under 3 normalised chars unless the anchor
  is itself a sub-`MIN_BOUND` one-line option row — Ilocano `no` means "if", and
  `val:Q105_DOH_LICENSED_VS1:4` → `Diak ammo no ania ti DOH licensing` (English: *I don't
  know what DOH licensing is*) was being thrown away as grid furniture.
* the three Aug-21 sibling scans in `qa_flags()` are one `_other_label_in()` helper; the
  June-5 `contains-other-label` scan keeps its own substring guard and is left verbatim.
* `extract()` takes an optional `text=` page string, so the box rules are testable without
  a symbol font installed (`test_anchor_extract.py` was font-gated on `seguisym.ttf`).

### Before / after — the F1 write set (`apply_aug21.py --only F1 --unmatched`, dry run)

| defect family (Task 17's sweep, unchanged) | before (attempt 2) | after |
|---|---:|---:|
| values `--apply` would write | 2,690 | 2,595 |
| carrying a defect | **249 (9.3%)** | **59 (2.3%)** |
| `truncated` | 149 | 51 |
| `english-furniture` | 66 | **0** |
| `local-directive` | 26 | **0** |
| `vs-offset` | 8 | 8 |
| strict-prefix truncations on a full-sentence key, stopping mid-sentence | **54** | **0** |
| values carrying an English-prose sentence (open scan, not the 4 known phrases) | 7 | **0** |

Per-locale clean pairs: 1044/1023/1025/1009/1042/1033/1040 → 1039/1007/1026/1005/1021/1020/1037
(FIL/BCL/BIS/CEB/WAR/HIL/ILO). The 16b gate still holds over the clean maps: **0**
directive, **0** routing, `item:Q75_IS_1700_ENOUGH` `label-condensed` in all seven
`_flagged.json`. The one `grid` hit the 16b gate script now reports is the Ilocano
`Diak ammo no ania ti DOH licensing` above — the gate script keeps 16b's over-broad regex;
`qa_flags` deliberately no longer flags it.

### The residual, listed with its cause

51 `truncated` rows survive. None of them is the class this round was for:

| cause | rows | what it is |
|---|---:|---|
| `paper-paren-unclosed` | 30 | the closing paren is past the next anchor, because a LONGER option's English contains a shorter option's English (`Other public facility (e.g., … barangay health centers …)`) or because the Ilocano paper's own parens are unbalanced. A multi-word `val:` boundary; the box gate is deliberately not applied to those. Keys: `val:Q147_EXTERNAL_SERVICES_GO_VS1:03` ×7, `val:Q13_2_HPU_ROLE_VS1:{1,3,4}`, `val:Q37_ACCESS_CHALL_VS1:{01,04}`, `val:Q36_QUALITY_CHALL_VS1:04`, `val:Q63_ENROLL_INITIATIVES_VS1:06`. |
| `no-terminal-punct` | 14 | the value is a complete sentence that does not end in `?`/`.` — the sweep's heuristic firing on a correct value (`item:Q64_ENROLL_CHALL`, `item:Q129_OOP_REASON`, `item:Q45_PERF_INDICATORS`, `item:Q86_EXPAND_NEXT`, `item:Q94_BUCAS_DECONGEST`). |
| `section-heading` | 7 | `item:Q140_UNCLEAR_PROTOCOL`, all seven locales: the paper prints the SECTION heading (`Outbound-Inbound Referral Process and Satisfaction`) right after the question. Headings are `record:`/`level:` labels, excluded from the anchor set by design (they match page headers and footers), so nothing bounds them. |

The 8 `vs-offset` rows are unchanged and are **not** extractor work: 5 are false positives
where the Aug-21 extract *repairs* a pre-existing bcl offset, and 3 are genuine June-5
re-introductions in ceb (`val:Q10_1_UHC_ATTRIB_VS1:9`, `val:Q12_2_PHU_ROLE_VS1:9`,
`val:Q150_HR_CHALL_VS1:03`). Those 3 are the override candidates Task 17 seeds.

### F2 re-run

`anchor_extract_f2.py` imports `clean_span`/`qa_flags`, so `out-aug21/F2/` was re-run:
clean 1,897 → 1,877, flagged 627 → 647. Churn: 1,861 unchanged, 16 changed (all the
leading lone `(`), 0 new, **20 dropped — every one of them a trailing local directive
(`PILIA ANG TANAN NGA APLIKADO`, `PILIEN AMIN NGA AGaplikar`), and all 20 appear in the new
`{loc}_flagged.json`**; 0 clean keys were dropped without a flagged row. The F2 apply tool
re-checked in dry run (nothing written, `git status --short spec/translations` empty):
incoming write+replace **485 → 455**.

### Controller ratifications carried forward (Tasks 28/40)

* Task 16b's deviations are RATIFIED: directives are EXCISED (both sides kept) and the
  local-language repeat is skipped — not "text after the last directive"; sibling option
  labels bound spans only behind a box glyph; the 12-word prefix is derived in `extract()`;
  the "end of line" boundary is dropped (`pdf_text()` collapses the page to one line) and
  is recorded as dropped.
* `item:Q75_IS_1700_ENOUGH` stays English this build in all seven locales — it is a
  `label-condensed` worklist row, not an import.
* `dcf-unanchored` is INFORMATIONAL, never a STOP. The drift check is
  `anchor_extract.py`'s own `keys not in dcf: []` line.

### 7. Fix round 1 (review follow-up, same day)

Three holes in the rules above, all found by review before anything was applied:

* **`local_directive()` scanned only the FIRST caps run.** `CAPS_RUN.search()` stopped at
  the question's own acronym run, so a value that opens with `… sa BUCAS GAMOT NBB?` and
  then carries a real directive (`PILIA ANG TANAN NGA APLIKADO`) came back clean. It now
  tests **every** run — `any(m.group(0) not in en for m in CAPS_RUN.finditer(tr))` — and the
  `LOCAL_IMPERATIVE` opener list stays as the second test. The acceptance sweep's own copy
  of the classifier had the same blind spot, so the "local-directive = 0" gate could not
  tell "none present" from "not detected"; it was fixed the same way and the gate re-run.
  Re-run result: the seven F1 clean maps and the sixteen F2 files are **byte-identical**
  (md5, 31/31) — no F1/F2 value depended on the blind spot, but the rule and the gate are
  now honest.
* **A MISSING `keep` field validated clean.** Loosening `keep` to allow `null` also made an
  omitted or misspelled field read as `null` = "never write this key", which would silently
  suppress an import instead of failing the gate. `validate_overrides()` now requires the
  field to be **present** on both the F1/F3/F4 and the F2 blocks
  (`entry must name 'keep' (use null to mean never write)`); an explicit `null` is still
  accepted. The live `aug21-overrides.json` has 0 such rows and still validates `OK`.
* **`merge_locale()` skipped flagged keys BEFORE consulting the overrides.** The plan says
  accepted flagged spans are expressed as overrides, never hand-copied — but a
  `keep: "<text>"` override on a flagged key was a silent no-op. Overrides are now consulted
  first: `keep: "<text>"` on a flagged key **writes that text** (counted `override`; counted
  `same` when the map already holds it), `keep: null` still never writes, and a flagged key
  with no override is still `flagged_skipped`. This is the lever for the 26 F1 / 20 F2 rows
  this round moved into `{loc}_flagged.json`. Note that `{loc}.json` and `{loc}_flagged.json`
  are disjoint, so the rule had to be applied on the flagged-keys pass, not only inside the
  pairs loop.

Gates after the fixes: `translations-official` **127 passed** (121 + 6 new), `aug17-tools`
121 passed + the 1 pre-existing CRLF-fixture failure, `aug21_overrides.py` → `OK`, and the
F1 acceptance sweep unchanged — 2,595 write values, 59 defective (truncated 51, vs-offset 8),
**english-furniture 0, local-directive 0, mid-sentence strict-prefix truncations 0**.

## F2 extractor layout rules (Task 21b)

2026-08-26. `anchor_extract_f2.py` only. `anchor_extract.py` was **not** touched, so the
F1 outputs in `out-aug21/F1/` are byte-identical (16/16 md5 OK) and no F1/F3/F4 evidence
moves.

### Why

Task 16b handed `anchor_extract_f2.py` `clean_span()` and `qa_flags()`, so F2 picked up
the *cleaning* rules — but its own `extract_text()` still carried Task 14's SPAN logic.
Task 22 measured the result on the real write set and stopped: of the 455 values
`--apply` would write, **134 (29%) carried a defect**, 106 of them `replace` rows over a
live value, 26 of those replacing a complete translation with a strict prefix of itself,
and one of them (`ceb` `Health center/facility` -> `Balita`, the `News` option's value)
re-introducing the 2026-08-13 row-misalignment scar.

### The rules

The F1 16b/16c round expressed in what F2 has. F1 gates on dcf key kinds (`val:`); F2
gates on the spec KINDS `spec/english-strings.json` has carried since Task 13, so
`dump-english-strings.ts` needed **no change** — `ids` on a `choice.label` entry is
already the parent item's id. `extract_text(text, labels, meta=None)` takes the metadata
as a new optional argument; with no `meta` nothing is gated and the Task-14 answer stands
(`test_meta_is_optional_and_absent_meta_keeps_the_task_14_span_rules`).

1. **Option labels are box-gated** (fact 1). An anchor whose spec kinds are nothing but
   `choice.label` counts only where the paper prints it behind a ballot box, and its span
   never crosses the next box (`cut_at_box`). `Professional development opportunities` is
   Q109's option and also sits inside Q107's translation, where it cut `Ako ay nasisiyahan
   sa professional development opportunities na mayroon ako sa aking trabaho` down to
   `Ako ay nasisiyahan sa`; `Regular` did the same to Q36's capitation option. Measured
   over the seven papers before the rule was written: 4,715 anchor occurrences, of which
   615 sit mid-sentence and ~460 of those are option labels.
2. **Section titles are letter-gated** (fact 1, second half). `YAKAP/Konsulta Package`
   (53 mid-sentence occurrences), `Task Sharing` (9) and `Job Satisfaction` (7) count only
   behind their section letter (`C. `, `E2. `). Inside Q32's Bicolano sentence the same
   words cut the translation to `Arin sa mga masunod an kaiba sa` AND handed the heading
   the SELECT-ALL directive that followed it (`Pilion an naangay`) — one rule, both
   defects.
3. **English furniture ends a span** (fact 2), and is the `english-furniture` net if it
   survives. Every pattern was counted in all seven `text-aug21/F2_*.txt` dumps before it
   was added (per-paper counts in the source):

   | pattern | per paper | what it is |
   |---|---|---|
   | `Number of (days\|hours)` | 5 | the item's `inputLabel`, never localized |
   | `(Specify …)` | 2-5 | `(Specify the equipment)`, an input hint |
   | `Year(s) Month(s)` / `Years … Month …` | 1 | the duration sub-field row |
   | `Month … Day … Year` | 3 | the date sub-field row |
   | `<n>. Regular Employment:` | 1 | the employment definitions block |
   | `A doctor's professional fee is` | 1 | the KAP section gloss |
   | `Please think about your experience in this post` | 2 | an item preamble |
   | `GPS Coordinates` / `Province/HUC` | 1 | the facility header row |

   Alongside them: the note LABEL (`Note:` 17x, `Tandaan:` 1x, `Pahinumdom:` 2x) is
   stripped at the head and the tail of a value and ENDS the span when it appears in the
   middle (Hiligaynon prints only the local half of the DOLE note, so no English anchor
   bounds Q11); a trailing run of sub-question numbers (`… implikasyon? 71a. 71b.`) and a
   trailing section letter (`… ng iyong sagot. A.`) are stripped.
4. **Value-set siblings reach `qa_flags`** (fact 4). `f2_siblings()` groups choice labels
   by parent item id and the set is passed as `siblings=`, which the F2 side never did —
   the `grid-bleed` net was inert. Alongside it a new F2 net, `own_english_inside()`: the
   papers reflow a two-column option grid into `☐ News ☐ Health center/facility Balita
   Health center/facility ☐ Legislation`, so the span that opens on the SECOND label holds
   the FIRST label's translation plus its own English. Nothing in `qa_flags()` can see
   that — it is not an echo, not a sibling's English, not a directive — and it is exactly
   the row that shipped `Balita` as ceb `Health center/facility`. Flagged
   `english-furniture`.
5. **Condensed and not-in-paper rows** (fact 5). A label the paper printed in a longer
   form falls back to its 12-word prefix (`anchor_prefix` + `condensed_candidate`,
   `label-condensed`); an anchor the paper never printed becomes a `not-in-paper` worklist
   row instead of vanishing — 28-31 rows per locale, 71 for `hil`.
6. **Sentence-final `.` / `:` are restored.** `clean_span()` ends with
   `.strip(" .:;,-")`, which is right on an option row and wrong on a sentence.
   Measured with this rule neutered and every other rule in place: 312 write rows, **160
   of them a strict prefix of the value the live map already held** (`… sa akong
   trabaho.` replaced by `… sa akong trabaho`); with it, 239 and 5.
   `restore_terminal_stop()` puts the character back only when the paper's own span ended
   in it, so nothing is invented.
7. **Two mixed-case local directives.** Every other local rendering in the F2 papers is
   ALL CAPS and `anchor_extract.CAPS_RUN` already sees it; Bicolano prints `Pilion an
   naangay`, `Basahon asin Pilion …` and `Saro lang an pillion na simbag` in sentence
   case, so `F2_LOCAL_IMPERATIVE` (F2-local, `anchor_extract.py` untouched) flags them
   `local-directive`.

### Before / after

The before column is measured, not quoted: `<ws>/task-21b/_compare_f2.py --rerun-before`
runs the pre-edit `anchor_extract_f2.py` next to the CURRENT `anchor_extract.py` into a
scratch dir and reproduces Task 22's numbers exactly (fil 273/93 … bcl 272/94).

| metric | before | after |
|---|---:|---:|
| values `--apply` would write | 455 | **239** |
| carrying a defect (`_defect_sweep_f2.py`) | **134 (29%)** | **10 (4.2%)** |
| `english-furniture` | 17 | **0** |
| `mis-anchored` | 18 | **0** |
| `vs-offset` | 1 | **0** |
| `local-directive` (as a clean value) | 0 | **0** |
| strict-prefix rows on a full-sentence key, stopping mid-sentence | 15 | **0** |
| `replace` rows shortening a live value to under 70% (Task 22's metric) | 26 | **0** |
| strict-prefix rows of any kind | 97 | 5 (punctuation-only) |
| `replace` rows over a live value | 315 | 132 |
| clean values carrying an F2 furniture phrase | 30 | **0** |
| clean values carrying a local directive | 2 | **0** |
| clean pairs / flagged rows (7 locales) | 1,877 / 647 | 1,832 / 884 |

Clean-map churn: **1,323 unchanged, 458 changed, 51 new, 96 dropped — and all 96 dropped
keys carry a flagged worklist row**, so nothing is silently lost.

### The residual (10 rows, with cause)

| cause | rows | what it is |
|---|---:|---|
| `no-terminal-punct` | 7 | the paper prints no `?` at the end of the translation (`ceb` Q21, `bis` Q13.1/Q17/Q18, `ilo` Q17, `hil` Q24, `war` Q12 — all verified in the dumps). The value is the complete sentence; the sweep's "long English ending in `?`" heuristic fires on it. |
| `paper-typo-glued-option` | 2 | the option's English is mistyped on the paper so no anchor can match: `☐ YesIyo` (bcl Q48) and `Patient does not pay any hospital billn` (ilo Q43). |
| `grid-row-untranslated-english` | 1 | `hil` Q82: the Likert row is printed with only the local labels (`Wala gid Talagsa Kon kis-a Permi Permi gid`), so nothing anchors and the scale bleeds into the question. |

The 5 remaining strict-prefix rows all drop a single punctuation mark the paper does not
print (`I have worked overtime for:` in 4 locales, `war` Q12's `?`). None drops a word.

### Spot checks

All **8** of the bcl rows Task 22's hand check found defective are now clean or flagged
(`<ws>/task-21b/evidence/bcl-8-rows.txt`): 5 clean and correct against the paper, 3 held
back (`YAKAP/Konsulta Package` -> `english-furniture` + `routing-note`; the PhilHealth
accreditation question -> `local-directive`; the professional-development question ->
`contains-other-label`). A fresh 10-row random `bcl` spot check against
`F2_BCL.txt` is **9/10 clean** — the one miss is the `☐ YesIyo` paper typo above.

### Gates

`translations-official` **160 passed** (140 baseline + 20 new), `aug17-tools` 131 passed
+ the 1 pre-existing CRLF-fixture failure, `deliverables/F2/PWA/app` `pytest scripts/`
11 passed. `--apply` was NOT run: the seven `spec/translations/*.json`,
`src/generated/items.ts` and `aug21-overrides.json` are md5-identical to how this task
found them. `dump-english-strings.ts` was not changed, so no npm gate was needed.

### Fix round 1 (review follow-up, same day) — box-less scale runs, `gate-rejected`

The review measured the round-1 worklist and found the `not-in-paper` reason factually
wrong on **77 of 247** rows: the anchor IS printed on the paper, verbatim, and it was the
new box / section-letter gate that rejected every occurrence. All 77 are `choice.label`
strings, and 42 of them are the two Likert vocabularies — which the seven papers print as
a **box-less run**, `Never Hindi kailanman Rarely Bihira Sometimes Minsan Often Madalas
Always Lagi` (F2_FIL.txt) — i.e. rows that were clean before Task 21b and that the box
gate alone made unanchorable. That was fact 4 half-implemented: the brief says an option's
span ends at the next box glyph **or the next sibling label**, and only the box half was
built.

**Rule (`sibling_run_occurrences()`).** A value set (`f2_option_groups()`: choice labels
sharing a parent item id) whose members the gate rejected is re-examined as a printed row.
Members within `F2_RUN_GAP` (60) normalised chars of each other form a chain; a chain
carrying `F2_RUN_MIN` (3) DISTINCT members is a row, not prose, and its occurrences anchor
exactly as a boxed option does. Two guards keep it off the boxed grids:

* the value set is skipped entirely if any member survives the gate somewhere on the
  paper (that set is printed behind boxes and needs no rescue). The membership test runs
  on the DE-OVERLAPPED occurrences — `☐ Agree but for medical tasks only` is a boxed hit
  of the bare `Agree` option too, and taking it at face value kept the whole Agree/
  Disagree scale rejected in all seven locales;
* a ballot box printed BETWEEN two members breaks the chain. `☐ LGU/Barangay
  LGU/Barangay ☐ Social Media Social Media` (F2_CEB.txt Q42) is three box-less sibling
  occurrences inside the gap — an option grid's echo translations, not a run. Without
  this guard the rule handed ceb `Health center/facility` the span `Balita` and put the
  2026-08-13 mis-anchoring scar straight back (measured: the sweep's `vs-offset` and one
  `english-furniture` row reappeared).

**Rule (`gate-rejected`).** An anchor with no surviving occurrence is still a worklist
row, but with the reason the paper supports: `not-in-paper` only when the words are
nowhere on the page, `gate-rejected` when they are on the page and every occurrence
failed a gate. Added to `LAYOUT_FLAGS`, so the QA report counts it per locale.

| the worklist reason | round 1 | after fix round 1 |
|---|---:|---:|
| `not-in-paper` rows | 247 | **170** |
| ... of which the paper prints verbatim (wrong reason) | **77 (31 %)** | **0** |
| `gate-rejected` rows | — | 2, both `hil` (`None`, `Neither Satisfied nor Dissatisfied: …`) |
| clean values over the seven maps | 1 832 | **1 907** |
| values `--apply` would write | 239 | 249 |
| values carrying a defect (`task-22/_defect_sweep_f2.py`) | 10 | **10** |

All 42 rows the review named are clean again and 21 of them are byte-identical to the
pre-Task-21b value; the other 21 differ only in whitespace (see below). The two rows with
no live value at all now carry a reason that is true: fil `Neither Agree nor Disagree` is
`empty` (the paper prints the label with no translation after it) and hil `None` is
`gate-rejected`. Both Likert scales match the live map in six locales; ilo `Never` is
held by the pre-existing `length-ratio` net and hil `Seldom` is genuinely not on the
Hiligaynon paper (it prints `Sometime`).

The acceptance gates are unchanged: **english-furniture 0, mis-anchored 0,
local-directive 0, vs-offset 0, strict-prefix truncations on a full-sentence key 0**;
the residual is the same 10 `truncated` rows with the same causes; the 8 bcl rows from
Task 22's hand check are byte-identical to round 1; the 10-row random bcl spot check is
**9/10**, same sample, same single miss (the `☐ YesIyo` paper typo).

**A whitespace class this round makes slightly larger, and does not fix.** 79 of the 249
write rows differ from the live value ONLY by internal whitespace. 52 REMOVE a stray space
the live map carries (`… nga praktis .` -> `… nga praktis.`) and are improvements; 27
INSERT one, because the Aug-21 PDF text layer breaks a word across a line (`pag-adto` ->
`pag- adto`, `Umanamong` -> `Uma namong`). 18 of those 27 predate this fix round; the
9 the scale run adds are ilo/fil/hil Agree-scale rows. The extractor reads the text layer
faithfully and has no view of the live map, so this is a paper-fidelity question for
Task 22, not an extractor defect — it is reported, not pre-empted.


## Leading question-number strip (Task 32b)

`anchor_extract.py` gained `strip_question_number()` (2026-08-26), the rule that closes the
one regression F4 v3.2.0 shipped: **the Waray papers print the paper's question number in
front of the LOCAL row as well as the English one**, so a span opened
`26. Mayda ba refrigerator o freezer an pamilya?` and the number rode into the map. The
other six papers number only the English row, which is why WAR was the only locale affected.

**The rule** (instrument-agnostic, applied in `extract()` immediately after
`strip_legend_code()`, so the own-match gate and `qa_flags()` judge the translation and not
the paper's furniture):

* a value that opens with a question-number token — `27. `, `71a. `, `45.1. `, i.e. digits,
  an optional sub-number, an optional letter, a full stop and **whitespace** — loses that
  token. `2 ka tuig`, `1.5 kilometro` and `27.Mayda` are not tokens and are untouched;
* the token is dropped **silently** when its number is the question number the key itself
  names (`item:Q27_…`, `vs:Q27_…_VS1`, `val:Q140_…_VS1:04`, and the sub-numbered
  `item:Q45_1_…` = 45.1);
* when it **contradicts** the key — or the key carries no `Qnn` to check it against — the
  token is still dropped but the row is flagged **`paper-number-mismatch`** and becomes a
  worklist row, never clean: the printed number is evidence that the paper's text may answer
  a different question than the key it landed on, and that is a translator question;
* the strip is refused when the remainder is this anchor's OWN English with its number
  removed — that row is an `echo-english` worklist row and stripping the number would hide
  the echo from `qa_flags()`.

**Measured blast radius** (re-extract of every Aug-21 paper on the same PDFs):

| instrument | values stripped | rows newly held (`paper-number-mismatch`) | rows that JOIN the clean map | other differences |
|---|---:|---:|---:|---:|
| F1 (7 papers) | 0 | 2 (war `item:/vs:Q46_KNOW_PAY_FREQ`, printed `59.`) | 0 | **0** |
| F2 (7 papers) | 0 | 0 | 0 | **0** (F2 has its own `extract_text()` and imports neither `extract()` nor the new rule) |
| F4 (7 papers) | 186 (war only) | 13 (12 war, 1 bis) | 24 (war) | **0** |

The 24 F4 rows that JOIN the clean map are a second-order effect of the same defect and are
all war: `digits_of(en)` already stripped a leading question number from the ENGLISH but
`digits_of(tr, strip_qnum=False)` did not from the translation, so the paper's number showed
up as an extra digit and the row was held `digit-mismatch`. With the number gone the digit
sets agree. Two of the 24 are held anyway by the by-category sweep — war
`item:/vs:Q72_GAMOT_OBTAINED` (the GAMOT applicability note, the class Task 28 fix round 1
already held for the other six locales) and war `item:Q18_INCOME_AMOUNT` (the
`Tick the income category …` directive) — so `aug21-overrides.json["F4"]` widened three
existing `keep: null` holds to include `war`. No entry was added, no `keep` changed.

**Effect on the live F4 maps** (v3.2.0 -> v3.2.1, measured `task-32b/_map_delta.py`):

| locale | keys | changed | detail |
|---|---:|---:|---|
| war | 1044 -> 1037 | 187 | 180 leading-number strips + 7 keys removed (the held rows the wave had created) |
| bis | 965 | 0 | `_meta` provenance counters only (its one held row was already an override) |
| fil / bcl / ceb / hil / ilo | — | **0** | byte-identical |

Nothing else moved: the delta classifier reports **0 `other` rows**. Waray label coverage
goes 1010 -> 1003 of 1403 (71%, unchanged as a percentage).

**Seven war rows are held for the translators**, not fixed, because their paper number
contradicts the CAPI's and the text may therefore answer a different question:

| key (war) | key says | the paper printed |
|---|---|---|
| `item:Q27_REFRIGERATOR` / `vs:Q27_REFRIGERATOR_VS1` | Q27 | `26.` |
| `item:Q28_TELEVISION` / `vs:Q28_TELEVISION_VS1` | Q28 | `27.` |
| `item:Q29_WASHING_MACHINE` / `vs:Q29_WASHING_MACHINE_VS1` | Q29 | `28.` |
| `val:ENUM_RESULT_FINAL_VISIT_PICK_VS1:4` | (no `Qnn`) | `1.` — the whole four-option grid collapsed into one value label |

Those seven keys had no pre-wave value, so holding them removes them from `war.json` and the
Waray screens fall back to English until a translator rules. `item:Q52_UHC_SOURCE` /
`vs:Q52_UHC_SOURCE_VS1` (paper `53.`) and `item:Q64_MEDICATIONS_LIST` (paper `67.`) are held
too, but they carry a pre-wave value, so those screens keep the June-5 Waray text.

**Paper-side residue this rule does NOT touch** — 10 values still open with a number, every
one of them **pre-existing** (present in the maps before the Aug-21 wave, and the Aug-21
extract offers no clean replacement): war `item:/vs:Q52_UHC_SOURCE` (`53.`),
`vs:Q65_CONDITIONS_VS1` (`65.`), `vs:Q93_WHY_NOT_VS1` (`93.`), `item:/vs:Q143_HOW_PAID`
(`143.`), `val:ENUM_RESULT_FIRST_VISIT_VS1:4` and `val:ENUM_RESULT_FINAL_VISIT_VS1:4`
(`1. Kumpleto 2. Gin-usod …`), and hil `val:Q6_CIVIL_STATUS_VS1:8` /
`val:Q39_CIVIL_STATUS_VS1:8` (`40. Highest level of education` — English furniture). WAR was
carrying 41 such rows before the wave and 195 after it; it now carries 8. Repairing the
residue means a hand edit of a map outside the apply path, which the wave rules forbid, so it
is on the worklist.

## Whole-value bracket strip (Task 33b)

**The defect.** The Aug-21 **Tagalog** F4 paper is a bilingual layout: it prints the English
line and puts the Filipino gloss in square brackets after it (`☐ Male [Lalaki]`,
`☐ Female [Babae]`). The extractor kept the delimiter as if it were sentence text, so
**459 of the 949 values in `F4/translations/fil.json` (~48%) shipped in v3.2.1 wholly wrapped
in `[ … ]`** — 441 `val:` option labels, 9 `item:`, 9 `vs:`. The pre-wave map had **0**; every
other F4 locale has 0; F1's Aug-21-imported `fil.json` has 0 of 1256. Q3 regressed from
`Lalaki` / `Babae` to `[Lalaki]` / `[Babae]`, which is what
`docs/uat-fix-evidence/2026-08-26-aug21-translations/F4/f4_q2_1_age_fil.png` caught on a
tablet. The other six papers are monolingual, which is exactly why only Filipino was hit.

**The rule** — `anchor_extract.py`, `strip_wrapping_brackets()`, called from `clean_span()` so
every instrument gets it. A value whose WHOLE content is enclosed in ONE matching pair of
square brackets loses that pair. Three deliberate limits, each with a test:

* the opening bracket's **partner must be the final character** — `[A] at [B]` opens and closes
  with a bracket and balances, but it is two glosses, not one wrap, and counting `[` against
  `]` cannot tell them apart;
* **exactly one pair** goes, so `[[Lalaki]]` still shows a bracket rather than being repaired
  into a shape no paper printed;
* an **unbalanced** value is left alone — a cut span is a worklist matter, and
  `trim_unbalanced_parens` / `trim_unbalanced_quotes` deliberately do not know brackets either.

Parentheses are untouched: `clean_span`'s own loop already unwraps a whole balanced paren group
(the Ilocano layout, Task 16c/27) and the ILO directive constants legitimately keep their
`( … )`.

`extract()` looks for the pair a **second** time after `strip_legend_code()` /
`strip_question_number()`, because those two remove furniture printed OUTSIDE the gloss
(`[Mahirap magparehistro] 01`) and can uncover a wrap `clean_span` never saw — 10 FIL legend
rows on Q45.1 / Q45.2 reached the clean map that way in the first pass of this fix. The second
look only runs when one of those two actually fired, so a genuine double wrap still loses
exactly one pair.

**Why no new flag and no echo guard** (unlike Task 32b's number strip): `qa_flags()` judges
through `norm_for_match()`, which folds every non-alphanumeric character to a space — so
`[Male]` and `Male` were ALREADY the same string to it. Stripping the pair cannot change a
single flag decision, cannot hide an `echo-english`, and cannot create a "joiner". The measured
extract confirms it: clean-row counts are **identical** in all seven locales before and after.

**Blast radius, measured.**

| extract | fil | bcl | bis | ceb | war | hil | ilo |
|---|---:|---:|---:|---:|---:|---:|---:|
| clean rows unwrapped | **459** | 0 | 0 | 0 | 0 | 0 | 0 |
| rows that joined / left the clean map | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| any other difference | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

F1 re-extracted with the fixed extractor and diffed key-by-key against the extractor's
immediately-before output: **0 changed rows in all seven locales** (F1's papers do not use the
convention). F2 shares `clean_span` but its seven Aug-21 extracts contain **no value with a
bracket at all**; `test_anchor_extract_f2.py` 40 passed.

**Live F4 map delta, v3.2.1 → v3.2.2** (`task-33b/_map_delta.py`):

| locale | keys | changed | detail |
|---|---:|---:|---|
| fil | 948 | **459** | all of them one whole-value bracket pair removed |
| bcl / bis / ceb / war / hil / ilo | — | **0** | byte-identical files, `_meta` included |

Nothing else moved: the delta classifier reports **0 rows of any other kind**, and **0 values
in any shipped map are still wholly wrapped**. Label coverage is unchanged in every locale
(FIL 917 / BCL 949 / BIS 933 / CEB 977 / WAR 1003 / HIL 830 / ILO 956 of 1403), because the
strip changes values, not key presence.

A second-order proof worth keeping: the fil `--apply` write set fell from 468 `replace` rows to
**144**, and `same` rose from 258 to 582. 324 Filipino rows the wave had been "replacing" were
identical to the live June-5 value all along — the brackets were the only difference. The
byte-verify says the same thing from the other side: `val:Q3_SEX_VS1:1` comes back
`[unchanged-since-baseline] 'Lalaki'`.

**Paper-side residue this rule does NOT touch** — 11 values still carry a bracket somewhere,
**none of them wholly wrapped**, 8 of them pre-existing (in the maps before the Aug-21 wave):

| locale | key | value | provenance |
|---|---|---|---|
| fil | `val:Q77_WHY_GENERIC_VS1:03` | `[Madaling mabili/makuha` | pre-existing |
| fil | `val:Q79_REG_SOURCE_VS1:03`, `val:Q80_ASSIST_VS1:03`, `val:Q84_WHERE_ASSIST_VS1:03` | `para sa bawat Filipino]` | pre-existing |
| fil | `val:Q141_BILL_ITEMS_VS1:01`, `val:Q196_FOREGONE_VS1:99` | `> [Kuwarto ]`, `[Iba pa (pakispecify)]_________` | pre-existing |
| hil | `vs:Q131_NBB_OOP_VS1`, `vs:Q135_ZBB_OOP_VS1` | `[Pamangkuta kon …] Sa tion …` | pre-existing |
| fil | `val:Q195_INCOME_PCT_VS1:2`, `:5` | `% [Mas mababa sa 1% ]`, `% [Higit sa 6% ]` | **wave-written** |
| war | `val:Q111_METHOD_VS1:3` | `[Tawag ha telepono tikang …` | **wave-written** |

The three wave-written rows are span-boundary residue, not the gloss convention: the bracket is
not the first or last character, so the whole-value rule correctly refuses them and they stay
visibly wrong instead of being silently half-repaired. They are on the worklist. For scale, the
pre-wave F4 maps carried **19** bracket-bearing rows (12 internal, 7 unbalanced) against 11 now.

**Wave 4 note.** Bracketed lines in the Aug-21 Tagalog papers: **F1 0, F2 0, F3 503, F4 455**.
The F3 import is on the fixed extractor, so it will not reproduce this — but any F3 extract
taken before this rule landed must be discarded rather than merged.


## Row-inheritance class (Task 48)

2026-08-27, from the FINAL whole-branch review. An option row silently inherits a
NEIGHBOURING row's translation. The value is well-formed, in the right language and of the
right length, so none of the 23 flags above fires and the row ships clean. Six confirmed
instances shipped (F3 CEB × 7 questions, F4 FIL/ILO/WAR, F2 WAR live in production) plus a
seventh in F1 BCL that this task confirmed.

**Mechanism 1 — the adjacent-English PAIR.** The PDFs lay some option grids out in two
columns, so the text comes out column by column: two boxed ENGLISH rows, then BOTH their
translations as one un-boxed block.

```
☐ Legislation ☐ LGU/ Barangay Balaod LGU/Barangay                     (F3_CEB.txt, Q36)
☐ DOH standard referral form ☐ City / LGU standard referral form
Syudad / LGU surundon nga porma han pagrefer DOH nga surundon nga …   (F2_WAR.txt, Q57)
```

The first row's span is box-to-box and therefore EMPTY, which leaves the whole block to the
second row. What the second row takes is never its own translation: either the neighbour's
alone (where the trailing row is untranslated on the paper — `LGU/Barangay` is printed
verbatim, so the anchor re-matches on its own echo and bounds the span at it, handing code
06 `Balaod`, which is code 02 `Legislation`'s text) or both glued (the F2 WAR row). The
page does not say which half is whose — the F2 block prints the two translations in the
REVERSE order of their English rows — so `anchor_extract.sibling_run()` /
`anchor_extract_f2.f2_sibling_run()` hold the whole pair: `sibling-run` on the trailing
candidate, `empty` on the row before it.

An empty predecessor is NOT on its own evidence of a block, and that is the expensive half
of the rule: the papers routinely leave ONE option row in English and translate the next
(`☐ Annulled ☐ Widowed Balo`). Firing on the empty predecessor alone moved **~230 correct
values** to the worklist across the 28 papers. The rule therefore also requires one of two
BLOCK signatures — the span ends at another occurrence of THIS anchor (`block-echo`), or the
span is more than `PAIR_BLOCK_RATIO` (2.0) times an English label at least
`PAIR_BLOCK_MIN_EN` (20) chars long (`block-size`) — plus three pair guards: both rows
behind a ballot box, the two occurrences not overlapping (`No` inside `No, but have
submitted requirements …` cost 20 correct F1 values), and the predecessor a PAIR partner
rather than one more row of a list the paper left wholly in English.

**Mechanism 2 — the duplicate label.** Two codes of ONE value set end up with the same
translated label while their English differs, either because the PAPER repeats one
translation across option rows (F4 FIL Q45.2 codes 01/02/03; F3 HIL Q34 prints
`Tatay sang Pasyente` against grandmother, uncle, aunt AND Other) or because one English
label lives in two value sets and the poisoned occurrence won the count (F4 WAR
Q128/Q134 code 05). Two choices a respondent cannot tell apart and an answer code the
analyst cannot recover, so neither row is written: `duplicate-label` on both.

**The permanent gate.** `apply_aug21.duplicate_label_rows()` judges the map the apply WOULD
leave behind — the only place both sides of a collision are visible, because the extractor
only ever sees one. Two exemptions and only two: identical ENGLISH (the padded `01`/`1`
pair, the legacy `8`/`99` "Other (specify)" pair) and a key the dictionary no longer
defines (it renders nothing, so it cannot collide — which is what makes most of the legacy
padded pairs benign). A group containing a key this apply writes is RED and blocks
`--apply`; a group it does not touch is reported as pre-existing.

Measured against the seven papers of all four instruments, the whole class costs 8 F1 / 27
F3 / 50 F4 / 3 F2 clean values, and gains nothing wrong: 0 rows changed value, 0 rows moved
the other way.

**Fix round 1 (2026-08-27) — the gate has a strict mode, and a blocked run says so.**
The first cut treated only a collision containing a key THIS apply writes as RED; every
other collision printed `pre` and stopped nothing. That is the right DEFAULT (ten-odd
legacy collisions no apply can reach would otherwise RED every dry run in the wave) and
the wrong only mode: the F4 WAR `Q128_NBB_UNDERSTAND_VS1` 03/05 pair — the exact shipped
row this class is named after — is a `pre` group, so the publish it must stop was allowed.

`apply_aug21.py --fail-on-pre` and `_defect_sweep.py --fail-on-pre` are the strict path an
instrument PUBLISHES on: an un-ruled collision over a live value set blocks there too. A
collision a human has judged correct is ruled in `duplicate_label_accepted.json`
(`<inst>` → `"<locale>/<value_set>"` → codes + a mandatory reason; a set that grows a third
colliding code stops being covered). It ships EMPTY — every pre-existing set still standing
over a live value set was hand-checked and is a real defect or an open translator question.

The blocked run also stopped lying: the last line now reads `BLOCKED` when nothing was
written (it read `APPLIED` before, chosen from the FLAG rather than from the outcome), and
a block exits 2 whether or not `--apply` was passed — a dry run's gate result has to survive
being read by a script that sees only the exit code.

The sweep itself is now a repo tool: `data/translations-official/_defect_sweep.py`,
`--inst F1|F3|F4`, `--diff` / `--maps-dir` so it can judge a restored-baseline rehearsal,
exit 1 when the gate blocks. It is task-17/28's detector minus their per-task hand-review
tables (`CLEARED`, `PRECISE`), plus the duplicate-label gate.
