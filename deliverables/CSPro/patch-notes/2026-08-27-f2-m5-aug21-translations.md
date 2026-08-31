# F2 m5 — Aug-21 translations (wave 2)

Patch note for the F2 leg of the Aug-21 translations plan
(`docs/superpowers/plans/2026-08-25-aug21-translations.md`). Deployed 2026-08-27 as spec
`2026-08-27-m5` — first at commit `fb91241a` (§m5), then re-deployed at commit `ce05b931`
(§m5 fix round 1) under the SAME stamp, because that round changes a translation and not the
questionnaire. Spec `2026-08-26-m4` (commit `9ba7a33`, deployed 2026-08-26) is superseded.
The Slack post is the block below; the sections after it are the build record, newest first.
**Deployed and verified live 2026-08-27 — see §m5 fix round 1. Ready to post.**

> **POSTED 2026-08-27 ~13:50 MNL to #f2-pwa-uat** (tester-facing edit of the block below: same facts, build-history bullets folded into plain 'fixed' bullets, evidence links expanded): https://aspsi-doh-uhc-survey2.slack.com/archives/C0AV19GB05P/p1787805060348049

---

🔧 **Healthcare Worker Survey (F2 PWA) — update deployed (spec 2026-08-27-m5)**
*Changed:* All seven language versions (Tagalog, Cebuano, Bisaya, Ilocano, Hiligaynon, Waray, Bicolano) now carry ASPSI's revised Aug-21 translations. Section A Q2 (employment) now reads in the chosen language in Cebuano, Bisaya, Ilocano, Hiligaynon, Waray and Bicolano — the one 2026-08-17 gap that is still English is **Tagalog Q2**, because ASPSI's cleared Tagalog paper prints that question in English only. The consent screen's Part-I paragraphs (study, privacy, benefits, rights, contacts line) now read in the chosen language too (Aug-21 cleared consent text); headings, buttons and the raffle block stay as before. Coverage per language went from fil 72 / ceb 74 / bis 74 / ilo 75 / hil 72 / war 76 / bcl 74 % to fil 80 / ceb 83 / bis 77 / ilo 83 / hil 80 / war 84 / bcl 79 % of the 740 on-screen labels. English wording, option values and saved answers are unchanged.
- **spec 2026-08-27-m5 supersedes 2026-08-26-m4:** one **Waray** option was showing a neighbouring option's translation glued to its own. On Q57 ("What type of referral form do you use to send to higher level facilities?") the choice *City / LGU standard referral form* read `Syudad / LGU surundon nga porma han pagrefer DOH nga surundon nga porma han pagrefer` — its own text plus the DOH row's. It now reads `Syudad / LGU surundon nga porma han pagrefer`, and the DOH choice above it is unchanged. Nothing else moved: every other language and every other question is byte-for-byte what m4 shipped, and no answer, option value or saved draft is affected.
- **Tagalog Q95 no longer shows the wrong option wording:** on the statement *"I think it's okay that health workers share tasks across roles even if they are beyond their job description"*, the choice *Disagree for both medical and clerical tasks* was showing the Tagalog for **Agree** (`Sumasang-ayon, ngunit para lamang sa mga gawaing klerikal`) — the same string as the *Agree but for clerical tasks only* row above it, so the two could not be told apart and the one shown was the opposite of what it meant. ASPSI's Aug-21 Tagalog paper prints that one string against both rows, so there is no Tagalog wording to import: the row now shows its **English** label until ASPSI's translators supply one. The other six languages are unaffected and keep their own wording. Anyone who already answered Q95 in Tagalog should be asked to re-check that answer.
*To get it:* Open the app while online and reload once (pull down or F5); the PWA updates itself on the next load. The header shows spec **2026-08-27-m5** when you're current. Drafts in progress are kept.
*Still English on a screen?* That text had no translation in ASPSI's cleared Aug-21 source for that language — not a build defect; the list has gone back to ASPSI's translators. The ballot-box option lists (Regular / Casual / Nurse / Midwife …) are printed in English in all seven papers, so they stay English on purpose.
*Evidence:* docs/uat-fix-evidence/2026-08-26-aug21-translations/F2/ (Section A in all 8 locales + the consent screen in FIL — Filipino Part-I paragraphs; re-shot on m5, plus `map-delta-m5.txt` and `served-content-m5.txt` for the Waray Q57 row, which is in Section F and so not on any of the shots).

## m5 — the row-inheritance repair (2026-08-27)

**Shipped:** spec `2026-08-27-m5`, commit `fb91241a`, deployed 2026-08-27 10:29 MNL.
Live `build-info.json`: sha `fb91241a1e13ff1a5e897bb1c363033a863a9861` == `git rev-parse HEAD`
at deploy time, `matches_main: true`; `deploy-f2-pwa.ps1 -VerifyOnly` exit 0. The bundle PROD
serves (`assets/admin-DebwnCUG.js`) contains `2026-08-27-m5` and the corrected value and
contains neither `2026-08-26-m4` nor the glued one — `served-content-m5.txt` in the evidence
folder.

**What was wrong.** The Aug-21 papers lay an option grid out in two columns, so the PDF text
layer returns both boxed ENGLISH rows first and both translations after them as one block. The
first row's span is then box-to-box (empty) and the whole block falls to the second row. m4
wrote one such row:

```
war  "City / LGU standard referral form"   (Q57)
-  "Syudad / LGU surundon nga porma han pagrefer DOH nga surundon nga porma han pagrefer"
+  "Syudad / LGU surundon nga porma han pagrefer"
```

`DOH standard referral form` extracted `empty` on that page — the paper's own gap — so it kept
its correct pre-wave value `DOH nga surundon nga porma han pagrefer` in m4 and still does.
Both rows now read correctly and neither was typed by hand.

**How it was repaired — generator-first, no hand edit.** `anchor_extract_f2.f2_sibling_run()`
(Task 48) now HOLDS a span with that signature instead of writing it. The seven maps were
restored from the pre-wave baseline `af1fa569` (byte-identical, proven per file by comparing
the LF-normalised working-tree bytes against the blob's own sha1) and the WHOLE wave was
re-applied through `scripts/apply-paper-translations.py` against
`<ws>/task-48/check/F2` — the corrected extract — with the same 17 stale keys retired in the
same run and the same 40 `aug21-overrides.json` F2 entries, byte-identical. A second dry run
writes 0 / replaces 0 / retires 0.

| locale | override | already | write | replace | retire |
|---|---:|---:|---:|---:|---:|
| fil | 8 | 219 | 16 | 30 | 17 |
| ceb | 2 | 266 | 16 | 2 | 17 |
| bis | 2 | 266 | 12 | 3 | 17 |
| ilo | 11 | 245 | 17 | 5 | 17 |
| hil | 7 | 193 | 17 | 4 | 17 |
| war | 6 | 213 | 15 | 55 | 17 |
| bcl | 4 | 253 | 13 | 3 | 17 |

208 values written (m4's run wrote 209 — the difference is exactly the held Q57 row).

**The live delta m4 → m5 is ONE value.** Six maps are byte-identical to what m4 shipped and
`src/generated/items.ts` differs on one line; `map-delta-m5.txt` in the evidence folder is the
full enumeration. Coverage is therefore unchanged — a corrected value, not an added one:
740 label objects, fil 594 (80 %) ceb 611 (83 %) bis 570 (77 %) ilo 617 (83 %) hil 593 (80 %)
war 625 (84 %) bcl 587 (79 %).

**Pre-apply gates** (against the restored baseline, before `--apply`): `english-furniture` 0,
`mis-anchored` 0, `local-directive` 0, `vs-offset` 0, `whitespace-delta` inserted **0** /
removed 52 (written, per the standing ruling), `truncated` 6 (the same six verified new keys
m4 shipped — the paper prints no terminal `?`); strict-prefix rows 0; paper question-number
furniture 0; row-inheritance gate **0 RED / 0 pre-existing**.

**Build gates:** `npm run generate`; `tsc -b --force` exit 0; `eslint` exit 0;
`vitest run --maxWorkers=2` **81 files / 703 tests passed** (701 + the two new invariants);
`audit-translations.py` exit 0 with 0 suspects; `f2-coverage.py` above the m3 baseline in all
seven locales; `npm run build` exit 0; `locale-shots.spec.ts` 1 passed.

**The guard can now see this class.** `scripts/lib/apply-translations.aug21.test.ts` gained
two invariants that judge an OPTION GROUP rather than one value — which is why m4's gates,
every one of which compared a value against the paper, the English or itself, could not see
it:

* no two choices of one question share a translation (`duplicate-label`);
* no choice carries a sibling choice's whole translation (`sibling-run`).

Both were RED on the m4 maps — the second listing exactly the Q57 row and nothing else — and
are GREEN here. The second rule needs measured bounds to stay honest: the sibling's text must
appear at one END of the value (without that, `More than once a week, but not everyday`
matches the `Around once a week` sitting inside it) and, when the comparison folds case, both
halves must clear 15 characters (without that, every negation built on its own antonym matches
— bcl `Bako pirmi` on `Pirmi`, fil `Hindi ko pa naririnig` on `Hindi`; 17 innocent rows in
all). **That floor is a false-positive bound, not a fact about option length, and the fix
round below says why it is not the whole rule.**

**One frozen exception — SUPERSEDED by the fix round below.** `fil`
`Agree but for clerical tasks only` and `Disagree for both medical and clerical tasks` both
read `Sumasang-ayon, ngunit para lamang sa mga gawaing klerikal`. That is the **paper's own**
repetition — it prints one Tagalog string against both rows of the grid — and it is in the
June-5 maps, in `af1fa569` and in what m4 shipped, so restoring and re-applying cannot clear
it: there is no distinct candidate to import. m5 recorded it in the guard's frozen
`PRE_EXISTING_DUPLICATE_LABELS` and disclosed it. **That was the wrong call and a review said
so:** the shared string is the AGREE wording, so the Disagree row was showing a Tagalog
respondent the opposite of the option they were choosing. §m5 fix round 1 clears it the way
F1/F3/F4 clear that shape — the key is deleted and the English renders — and the allowlist
now ships empty.

**Not changed:** `aug21-overrides.json`'s F2 block (40 entries, byte-identical), the retire
list (the same 17 stale keys), any English wording, any option value, any id, enum or schema.
Nothing to migrate.

---

## m5 fix round 1 — the duplicate fil option label, cleared (2026-08-27)

**Shipped:** the same spec stamp `2026-08-27-m5`, commit `ce05b931`, deployed 2026-08-27
11:16 MNL. Live `build-info.json`: sha `ce05b931e4244ed9c7b00b6ada4f9b1f3092c6b1` ==
`git rev-parse HEAD` == `origin/main`, `matches_main: true`; `deploy-f2-pwa.ps1` and
`-VerifyOnly` both exit 0. **The stamp did not move on purpose:** `LOCAL_SPEC_VERSION`
versions the SPEC — it is what invalidates a draft when items move — and no item, id, choice,
code or schema changed here. The build's identity is its commit sha in `build-info.json`.

**What was wrong.** m5 disclosed a duplicate pair instead of clearing it, and the pair was
live and INVERTED: in Tagalog both rows of Q95 read
`Sumasang-ayon, ngunit para lamang sa mga gawaing klerikal` — the *Agree* wording — so a
respondent picking `Disagree for both medical and clerical tasks` was reading the opposite of
their own answer. Pre-existing (present at `af1fa569`, at m4, at m5), not a regression of this
wave, but shipped anyway.

**How it was repaired — the F1/F3/F4 remedy, generator-first.** The paper carries no distinct
Tagalog candidate, and an English option beats a wrong one (the ledger's rule 10, the same
call Task 49 made for F4). `scripts/apply-paper-translations.py` gained the `remove: true`
override semantic Task 49 gave `apply_aug21.py`; `aug21_overrides.py` now accepts the field in
the F2 block (it used to reject it, correctly, because the applier had no removal path). One
entry was added to `aug21-overrides.json` (`F2 → fil`, with its reason), and the wave was
re-applied. Because the F2 override block is locale-NESTED, the entry is per-locale by
construction: the key is deleted from `fil` only, where `--retire` — the only deletion F2 had
before — would have taken the six correct translations with it.

| locale | override | already | write | replace | remove | retire | saved |
|---|---:|---:|---:|---:|---:|---:|---|
| fil | 8 | 265 | 0 | 0 | **1** | 0 | yes |
| ceb | 2 | 284 | 0 | 0 | 0 | 0 | no |
| bis | 2 | 281 | 0 | 0 | 0 | 0 | no |
| ilo | 11 | 267 | 0 | 0 | 0 | 0 | no |
| hil | 7 | 214 | 0 | 0 | 0 | 0 | no |
| war | 6 | 283 | 0 | 0 | 0 | 0 | no |
| bcl | 4 | 269 | 0 | 0 | 0 | 0 | no |

`unmatched` 0 everywhere. The re-run after it removes 0 as well as writing 0 — a removal is
counted only when there is something to delete, so the wave stays replayable. The live delta
against what m5 deployed is **one row**: `fil` `Disagree for both medical and clerical tasks`,
gone. Six maps untouched, CRLF intact, 0 lone LFs. `items.ts` loses exactly the `fil:` field
of that one choice and keeps `ceb/bis/ilo/hil/war/bcl`.

**Served proof** (`served-content-m5-fix1.txt`): the bundle PROD serves,
`assets/admin-Bxu9VVRp.js`, contains the AGREE Tagalog string **once** (m5 served it twice),
carries the English `Disagree for both medical and clerical tasks` label, still carries the
corrected war Q57 value, and still carries the ceb/war/bcl Disagree wording.

**The guard got sharper.** The sibling-run rule's 15-character floor carried a comment
claiming no whole option translation is that short. **191** of the option values in these
seven maps are shorter — `ceb Agree → Uyon` (4), `war Always → Pirme` (5), every `Yes → Oo`
(2) — so the rule was blind to a glue of two SHORT options, which is exactly the
Agree/Disagree, Yes/No, Male/Female two-column grid that produced the m4 defect in the first
place. The floor is a false-positive bound (measured: 17 innocent rows below it, in two
families) and now applies only to the case-folded comparison; a **verbatim** form — the
sibling's value at one end of this one with its own capitalisation, and, for a head glue, a
capitalised residue — needs no floor and no allowlist, and it is what carries the short pairs.
Measured on the live maps: 0 hits. Three fixtures pin the coverage in the test itself: the m4
`war` Q57 defect, a 4-character + 11-character glue (`Uyon` + `Diri nauyon`), and the two
innocent families. `PRE_EXISTING_DUPLICATE_LABELS` now ships **empty**, the same rule
`duplicate_label_accepted.json` follows on the CSPro side.

**Gates.** `npm run generate` (fil 301 → 300 keys, six locales unchanged); `tsc -b --force` 0;
`eslint` 0; `vitest run --maxWorkers=2` 81 files / **705** tests passed; `audit-translations.py`
0 suspects; `f2-coverage.py` fil 594 → **593** of 740, ceb 611 / bis 570 / ilo 617 / hil 593 /
war 625 / bcl 587 unchanged; `npm run build` 0; `locale-shots.spec.ts` 1 passed and the nine
PNGs came back **byte-identical** (Q95 is in Section H and the stamp did not move);
`aug21_overrides.py` OK; `pytest` translations-official 422 passed / 1 skipped,
`scripts/test_apply_paper_translations.py` 16 passed.

**Not changed:** any English wording, any option value, any id, enum or schema; the other six
locale maps; the retire list; the 40 pre-existing `aug21-overrides.json` F2 entries (the F2
block is now 41). Nothing to migrate.

**Still on the translator worklist:** the fil Q95 Disagree row. Deleting the key makes the
option honest, not translated.

---

## Coverage (label objects of 740) — m4

The plan's "707 label objects / 75 %" figures were wrong; `scripts/f2-coverage.py` counts
740 label objects in `src/generated/items.ts`. Both rows below are that script's own output.

| | fil | ceb | bis | ilo | hil | war | bcl |
|---|---|---|---|---|---|---|---|
| before (m3) | 533 (72 %) | 550 (74 %) | 549 (74 %) | 554 (75 %) | 530 (72 %) | 565 (76 %) | 547 (74 %) |
| after (m4) | 594 (80 %) | 611 (83 %) | 570 (77 %) | 617 (83 %) | 593 (80 %) | 625 (84 %) | 587 (79 %) |
| delta | +61 | +61 | +21 | +63 | +63 | +60 | +40 |

## Deploy

**DEPLOYED 2026-08-26.** `deploy-f2-pwa.ps1` ran clean end to end — guard 1 (checkout
matches `origin/main`), build, guard 2 (built-artifact markers), upload, guard 3 (live
verification):

| field | value |
|---|---|
| commit deployed | `9ba7a3369d4ce070153aa8cc06a07757716df333` (`HEAD` == `origin/main`) |
| live `build-info.json` `sha` | `9ba7a3369d4ce070153aa8cc06a07757716df333` — equals HEAD |
| live `build-info.json` `built_at` | `2026-08-26T01:31:13.8995239Z` (09:31 MNL) |
| `matches_main` | `true` |
| `branch` | `main` |
| bundles | `index-Z0aKrMTK.js`, admin chunk `admin-Bd3Zp6By.js` |
| `deploy-f2-pwa.ps1 -VerifyOnly` | exit 0 — `PROD IS HEALTHY` |
| rollback point on the box | `/opt/app/f2-www.bak-20260826-093113` |
| served bundle content | live `assets/admin-Bd3Zp6By.js` contains the string `2026-08-26-m4` and the Filipino consent paragraph `Layunin ng pag-aaral…`; the m3 string `2026-08-25-m3` is gone |

Post-deploy re-gates on the pushed HEAD: `npx tsc -b --force` exit 0,
`npm test -- --maxWorkers=2` **81 files / 701 tests passed** exit 0, and
`git status --short deliverables/F2` empty.

**One cosmetic quirk in the deploy log.** Its verify block prints
`(no build-info.json on prod - deployed before this script)`. That is a false negative in the
script, not a missing file: line 238 writes `dist/build-info.json` with PowerShell 5.1
`-Encoding utf8`, i.e. **with a BOM**, and the verify block's `ConvertFrom-Json` (line 116)
throws on that BOM and falls into the `catch` at line 118. Fetching the URL directly returns
HTTP 200 with the correct JSON (the values tabled above). Left alone here rather than slipping
an unreviewed change into a deploy script; worth a one-line fix in its own task.

**Why the first deploy attempt failed (superseded — do not run the old recipe).** An earlier
attempt died inside `deploy-f2-pwa.ps1`'s unconditional `npm ci` with
`EPERM: operation not permitted, unlink` against the
`@rolldown/binding-win32-x64-msvc` and `@rollup/rollup-win32-x64-msvc` native bindings. The
cause was **a vitest gate run that was still executing** and held those `.node` files mapped
— not orphaned processes. The remedy is to let the test run finish and retry
`.\deploy-f2-pwa.ps1`; if `npm ci` still EPERMs, stop only the specific vitest PIDs you
yourself started. **Never stop node processes by name or command-line pattern** — MCP servers
and editor tooling also run as `node.exe`. On the retry recorded above, `npm ci` succeeded on
the first try with no process intervention at all.

## Gates on the pushed commit

| gate | result |
|---|---|
| `npx tsc -b --force` | exit 0 |
| `npm run lint` (eslint) | exit 0 |
| `npm test` (vitest) | **81 files / 701 tests passed, exit 0** — complete run at `--maxWorkers=2` on 2026-08-26 (221.54s, zero unhandled errors), re-confirmed post-deploy (173.45s). At **default** concurrency this box reports `2 failed` / `699 passed (701)`: two jsdom `waitFor` timeouts in `MultiSectionForm.test.tsx` that fail identically on the unmodified pre-change tree and pass standalone (13/13) — pre-existing load flake, not a regression from this change |
| `python scripts/audit-translations.py` | exit 0, **0 suspect entries** (the 119 pre-existing ORPHAN-key suspects were cleared by the Task 22 retire pass) |
| `npm run build` | exit 0 — bundle-secrets, bundle-budget and contrast checks all OK |
| `npx playwright test -c e2e/playwright.config.ts e2e/locale-shots.spec.ts` | **1 passed**, `Captured locales: en, fil, ceb, bis, ilo, hil, war, bcl` |
| `python scripts/f2-coverage.py` | above the m3 baseline in all seven locales (table above) |

### Correction against commit `9ba7a33`

Commit `9ba7a33`'s message states “vitest 701/701 in 81 files”. The number is right — it is
reproduced twice above — but **the run cited when that commit was written had not finished and
had in fact crashed**: that evidence file ends `Test Files 35 passed (35)` / `Tests 255 passed
(255)` / `Errors 46 errors` after 46 `Worker exited unexpectedly` pool errors, because its own
worker processes were being torn down by a concurrent `npm ci`. So the gate was asserted before
it was actually green, and the same overstatement reached this note and `log.md`. It has since
been re-run to completion on that exact commit, twice, exit 0 both times. No code changed —
only the record.

## Why Tagalog Q2 is still English

The plan's acceptance check for this wave was "`f2_secA_fil.png` must show the Q2 employment
stem and its options in Filipino". It does not, and it must not: `text-aug21/F2_FIL.txt` — the
text of ASPSI's cleared Aug-21 Tagalog F2 paper — reads

```
2. What type of employment do you have at this health facility?
   ☐ Regular ☐ Casual ☐ Seasonal ☐ Probationary ☐ Project ☐ Fixed-term ☐ Other, specify
```

with no Tagalog line under it. `anchor_extract_f2.py` flagged the pair `empty` and wrote
nothing, which is correct — a dialect string is never invented. The other six papers do carry
Q2 and all six shots render it (`f2_secA_ceb.png`: `Unsa ang klase sa imong trabaho niini nga
pasilidad?`), which is what actually proves the survey-body import landed. Tagalog Q2 is on
the worklist back to ASPSI's translators.

## Parked for the wave close (Task 47)

The F2 translation store is still **flat English-keyed**. Same-English/different-translation
conflicts — 51 known from the 08-17 pass, plus any normalized-key collisions the extractor
reported — remain inexpressible in that shape, so the id-scoped re-key stays parked. Wave 2
is otherwise complete; wave 3 (F4) starts from the Day-0 tooling and is independent of this
wave.

---

# Build record

The sections below are the accumulated per-task record for wave 2, folded in from
`draft-f2-m4-aug21-translations.md` (now deleted). Later sections supersede earlier ones
where they say so.

## Task 12: English-string collector

`deliverables/F2/PWA/app/scripts/lib/english-strings.ts` —
`collectEnglishStrings(result: ParseResult): EnglishStringEntry[]` mirrors the
exact six fields `applyTranslations()` localizes (section.title,
section.preamble, item.label, item.help, choice.label, subField.label);
unique by exact `en` text, first-appearance order, kinds/ids merged when the
same English string recurs.

Snapshot test against the real `spec/F2-Spec.md` (via `parseSpec`):

```
unique English strings (anchor universe) = 393
```

This is the denominator "anchors" the F2 paper extractor
(`anchor_extract_f2.py`, Task 13) reports against.

## Task 13: english-strings.json dump

**F2 anchors: 393**

`deliverables/F2/PWA/app/scripts/dump-english-strings.ts` (`npm run
dump:english`) reads `spec/F2-Spec.md`, runs it through `parseSpec()` +
`collectEnglishStrings()` (Task 12), and writes the deterministic dump
`deliverables/F2/PWA/app/spec/english-strings.json` — shape `{ source, count,
strings, _generated_by }`, no timestamp, so re-dumps of an unchanged spec
produce byte-identical output. Consumed by the F2 paper extractor
(`anchor_extract_f2.py --english-strings ...`, Task 14) and
`load_english_set()` (Task 15) as the anchor universe.

## Task 15: apply-paper-translations.py (F2 apply tool)

`deliverables/F2/PWA/app/scripts/apply-paper-translations.py` merges the Aug-21 F2
extract (`out-aug21/F2/{loc}.json`, Task 14) into `spec/translations/{loc}.json`.
It joins ONLY on the exact English strings in `spec/english-strings.json` (393
anchors, Task 13) - no question-number joins (2026-08-13 row-misalignment scar).
Decision order per key: unmatched -> override -> same-as-English -> already-same ->
write -> replace (Aug-21 wins). Overrides are consulted before the write branch, so
`"keep": null` also suppresses a fresh write; an override for a key the extract never
produced is seeded after the loop (`override_seeded`). `--retire "<English>"`
(repeatable) removes a stale key from every locale map - stale keys are never
hand-deleted. Maps keep their line endings (CRLF today), indent 1,
`ensure_ascii=False`, and are saved only when the content actually changed. No
`_meta` is written into a map: `readMap()` (apply-translations.ts:36) keeps only
non-empty strings and `audit-translations.py:57` skips non-strings, so provenance
goes to `--report` (`out-aug21/F2/apply-report.json`, gitignored) instead.

Dry run, 2026-08-25 (`python scripts/apply-paper-translations.py`, nothing written):

```
DRY RUN  anchors=393
locale  unmatched  override  seeded  same-as-en  already  write  replace  retire  saved
fil             0         0       0           0      180     25       74       0  would
ceb             0         0       0           0      208     22       58       0  would
bis             0         0       0           0      209     20       58       0  would
ilo             0         0       0           0      153     19      109       0  would
hil             0         0       0           0      159     22       46       0  would
war             0         0       0           0      167     18      105       0  would
bcl             0         0       0           0      207     19       54       0  would
```

`unmatched` is 0 in every locale because the Task 14 extractor is already anchored on
the same `english-strings.json` universe. Residue sweeping fires 301 times on bare
trailing question numbers and 4 times on the `N. NextWord` tail (the next question's
number plus the start of its text) - e.g. `hil` "Bills are settled between the
hospital and PhilHealth" loses the `44. Have you heard of the Zero Balance Billing
(ZBB)? ...` bleed.

Open for Task 22 (which owns the `"F2"` section of `aug21-overrides.json`): the
dry-run report carries 163 incoming values across the 7 locales that trip an
`audit-translations.py` check - mostly `<...>` enumerator directives and trailing
section letters swept into a translation cell, plus one clearly mis-anchored key
(`fil` "Awareness on No Balance Billing (NBB) and Zero Balance Billing (ZBB)" whose
Aug-21 span is the English `<Section D to be answered by ...>` note). Those become
`keep`/`keep: null` overrides at apply time, not now.

## Task 16b fix round 1: the extract was re-run (Task 15's table above is superseded)

`anchor_extract_f2.py` loads its span helpers (`clean_span`, `qa_flags`) from
`data/translations-official/anchor_extract.py`. Task 16b added the Aug-21 paper LAYOUT
rules to that module (directive stripping, angle-bracket routing notes, one-line option
rows) **after** the Task 14 extract had been written, so `out-aug21/F2/` was stale: 224 of
its clean values across the seven locales still carried an English interviewer directive
(167) or an angle-bracket routing note (115) — e.g. `fil` "Dentist" →
`otherwise proceed to Q91>` and `ceb` "If yes, was it a result of the UHC Act enacted in
2019?" → `SELECT ONE ANSWER ONLY Kung oo, resulta ba kini …`.

The extract was re-run against the Task-16b extractor and the dry run repeated. Both
counts are now zero. Use THIS table, not the Task 15 one above:

```
DRY RUN  anchors=393
locale  unmatched  override  seeded  same-as-en  already  write  replace  retire  saved
fil             0         0       0           0      202     23       48       0  would
ceb             0         0       0           0      232     22       30       0  would
bis             0         0       0           0      233     19       30       0  would
ilo             0         0       0           0      166     18       93       0  would
hil             0         0       0           0      165     22       33       0  would
war             0         0       0           0      187     18       80       0  would
bcl             0         0       0           0      227     19       30       0  would
```

Incoming write+replace rows: **649 → 485**. Re-running the `audit-translations.py`
signatures over the incoming values (not the store — nothing has been applied) takes the
Task-22 override-candidate count from **163 to 48**:

| audit signature | before | after |
|---|---|---|
| stray angle bracket | 115 | **0** |
| English prose in a dialect slot | 19 | **1** |
| trailing section letter | 47 | 47 |
| value is a DIFFERENT English string | 1 | 1 |

So Task 22 should rebuild its `"F2"` override candidate list from the **current**
`out-aug21/F2/apply-report.json`; the 115 `<…>` candidates named in the Task 15 section
above no longer exist. The 47 trailing-section-letter and 1 mis-anchored-key candidates
are unchanged — they are boundary/truncation classes, not paper-layout furniture.

`spec/translations/{loc}.json` is untouched: every run in this round was a dry run.

## Task 21: Consent screen (chrome `consent.*`)

The F2 consent screen is app chrome, not survey content: it lives in
`src/i18n/locales/{loc}.ts` under `consent.*`, so neither the Task 13
english-strings dump nor `anchor_extract_f2.py` ever saw it, and #1313 left
`infoStudy`/`infoBenefits` English in all seven dialects on 2026-08-25.

`data/translations-official/extract_icf_f2.py` reads the five Part-I paragraphs
straight out of `en.ts` (`infoStudy`, `infoPrivacy`, `infoBenefits`, `infoRights`,
`contactsHeading`), locates each on the Aug-21 F2 paper with
`extract_icf.locate()`, and stores the span up to the next located paragraph.
Output is the generated `src/i18n/locales/consent.aug21.ts`, spread LAST into each
locale's `consent` block — a key the paper does not carry simply stays English.

**35 of 35 paragraphs extracted (7 locales x 5 keys); 0 overrides needed.**

| locale | infoStudy | infoPrivacy | infoBenefits | infoRights | contactsHeading | chars |
|---|---|---|---|---|---|---|
| fil | prefix | prefix | prefix | prefix | exact | 2623 |
| ceb | prefix | prefix | prefix | prefix | exact | 2445 |
| bis | prefix | prefix | prefix | prefix | exact | 2532 |
| ilo | prefix | prefix | prefix | prefix | exact | 2827 |
| hil | prefix | prefix | prefix | prefix | exact | 2981 |
| war | prefix | prefix | prefix | prefix | exact | 2849 |
| bcl | prefix | prefix | prefix | prefix | exact | 2516 |

`prefix` on four of five keys is the expected shape, not a defect: `en.ts` is a
screen and the paper is a read-aloud script, so they diverge MID-paragraph —
en.ts "The survey may take more or less than an hour to complete." / "Your
progress is saved automatically on this device …" against the paper's "The
interview may last for more or less than an hour." `locate()` therefore stops
at "… funded this study." and the paper's own remaining English trails the
anchor. `_drop_english_tail()` walks that leftover off sentence by sentence
(a sentence is the paper's English when `looks_english()` fires or it repeats
>= 60% of the anchor's words once the program names are stripped); a window
whose every sentence is English is dropped as `dropped-english` instead of
being stored empty. Words the paper broke across a PDF line at their own hyphen
are rejoined ("Layunin ng pag-" + "aaral" -> "pag-aaral", not "pag- aaral").

Values are verbatim, including the papers' own quirks: `war` `infoBenefits` ends
without a full stop, `hil` `infoBenefits` omits the PhP 1,000 amount, `ceb`
`infoRights` is a two-sentence condensation, `fil` `infoPrivacy` prints
"isang,pribado". All were checked against the source PDFs — the extractor did not
truncate them.

Out of scope by the spec's own Scope Out ("F2 chrome strings beyond the consent
screen"): headings, buttons, `intro`, the raffle block and `contactsBody` (a
contact TABLE the paper prints cell-by-cell). They stay English and are asserted
unchanged by `src/i18n/consent.aug21.test.ts`.

Evidence: `locale-shots/f2_consent_fil.png` (Playwright `locale-shots.spec.ts`,
which now asserts `requests your participation` is absent and the Tagalog
`Layunin ng pag-aaral na ito` is visible before it captures the shot). The spec
previously captured that screenshot in a loop iteration where the consent gate
could no longer appear — consent is a per-CASE gate (#808), so the `en` pass
consented for every later locale; the `fil` pass now starts a fresh case.

Tester-visible sentence for the Task 23 patch note: *"The consent screen's Part-I
paragraphs now read in the chosen language (Aug-21 cleared consent text); headings
and buttons stay as before."*

## Task 22 (attempt 1): survey-body import — BLOCKED at the review gate (nothing applied) — SUPERSEDED by attempt 2 below

`spec/translations/{loc}.json` and `src/generated/items.ts` are **byte-identical**
to how this task found them (md5-verified). `--apply` was NOT run.

### Coverage baseline (`scripts/f2-coverage.py`, new in this task)

`scripts/f2-coverage.py` is now the single coverage source (the plan's node
one-liner is dropped); both agree exactly on today's tree.

```
label objects: 740
fil533 ceb550 bis549 ilo554 hil530 war565 bcl547
fil72% ceb74% bis74% ilo75% hil72% war76% bcl74%
```

The plan quoted `707` / `fil 75 … bcl 77`; the real committed `items.ts` carries
**740** label objects. The plan's denominator predates a spec revision — 740 is the
number the close-out (Task 44) should read, from this script.

`npm run generate` raw key counts, unchanged: `fil:302, ceb:307, bis:308, ilo:311,
hil:292, war:320, bcl:307`.

### Dry run against the CURRENT (Task 16c) extract

```
DRY RUN  anchors=393
locale  unmatched  override  seeded  same-as-en  already  write  replace  retire  saved
fil             0         0       0           0      202     23       48       0  would
ceb             0         0       0           0      232     22       27       0  would
bis             0         0       0           0      233     19       27       0  would
ilo             0         0       0           0      176     18       81       0  would
hil             0         0       0           0      165     22       28       0  would
war             0         0       0           0      187     18       77       0  would
bcl             0         0       0           0      227     18       27       0  would
```

Incoming write+replace rows: **455** (485 in the Task-16b section above; the extract
was re-run once more by Task 16c). `unmatched` is 0 in every locale.

### The by-category sweep (controller ruling: REBUILT detector rules)

`_defect_sweep_f2.py` (staged at `.superpowers/sdd/2026-08-25-aug21-translations/
task-22/`) **imports** Task 17's rebuilt detectors — `section-heading`,
`english-own-match`, `english-heading`, `ENGLISH_EXTRA`, `CAPS_RUN`,
`LOCAL_IMPERATIVE` — and `anchor_extract.has_directive`; nothing is re-declared.
Only the corpora are F2's (`spec/english-strings.json` anchors; the non-anchor `en:`
literals in `items.ts` as the heading corpus; choice siblings from the dump's `ids`).

One family had to be ADDED, because Task 17's four all assume a long English label
(`len(en) > 40`, ends in `?`/`.`) and more than half of F2's anchors are short option
labels. `mis-anchored` is where the 2026-08-13 row-misalignment scar lives, and every
rule in it is a shape, not a vocabulary: no letters at all; the value IS a different
English anchor; opens on an English word that can only be mid-sentence; ends on a
dangling English connective; audit's own `EN_PROSE` rule; every content word present
in the English corpus (pure English).

```
values --apply would write: 455
values carrying a defect:   134     (29%)

  truncated              98   new-key rows: 7
  mis-anchored           18   new-key rows: 13
  english-furniture      17   new-key rows: 8
  vs-offset               1   new-key rows: 0

  locale          truncated      mis-anchored  english-furnitur         vs-offset
  fil                    12                 5                 3                 0
  ceb                    13                 4                 2                 1
  bis                    14                 2                 3                 0
  ilo                    25                 2                 1                 0
  hil                     7                 2                 4                 0
  war                    11                 2                 2                 0
  bcl                    16                 1                 2                 0
```

**106 of the 134 are `replace` rows** — they overwrite a live value. 26 of those
replace a complete translation with a strict prefix of itself:

| locale | English | current value | Aug-21 value |
|---|---|---|---|
| fil | I am satisfied with the professional development opportunities I have in my job. | Ako ay nasisiyahan sa professional development opportunities na mayroon ako sa aking trabaho | `Ako ay nasisiyahan sa` |
| ceb | Which of the following are included in the YAKAP/Konsulta package? | Hain sa mosunod ang gilakip sa YAKAP/Konsulta package? | `Hain sa mosunod ang gilakip sa` |
| bcl | Which of the following professional development opportunity/ies would be most useful to you? | Arin sa mga minasunod na professional development opportunities an pinaka-useful saimo? | `Arin sa mga minasunod na` |
| ceb | Health center/facility | Health center/pasilidad | `Balita` (the `News` option's value — a value-set offset) |

### Spot check: 10 random `bcl` `replace` rows against the paper

The plan asked for 10; **8 of the 10 are defective**, and only 3 of the 8 are among
the 19 `bcl` rows the sweep flags — so 134 is a floor, not the count:

1. `According to DOLE, …` → value prefixed with the paper's `Note:` furniture.
2. `YAKAP/Konsulta Package` → `Pilion an naangay` — the paper's *directive*, mis-paired.
3. `If yes, what are the implications?` → `… implications? 71a. 71b.` (question-number residue).
4. `What are these pieces of equipment?` → `… (Specify the equipment) I-specify an mga equipment`.
5. `On average, how many hours do you work per day?` → `… nagtatrabaho? Note`.
6. `Are you part of a health facility that is an accredited PhilHealth YAKAP/ Konsulta provider?` → truncated at `… kan Philhealth`.
7. `How many days in a week …?` → `… pasilidad na ini? Number of days Bilang kan aldaw`.
8. `Which of the following professional development opportunity/ies …?` → `Arin sa mga minasunod na`.

### Why this is a stop, not an override list

The plan's Global Constraints: *"overrides are added only for defects the Aug-21
extract actually re-introduces … poisoned extract output is an extractor defect,
never an override."* 134+ overrides across 7 locales is not a residual set — it is
the extractor's output being laundered key by key.

Root cause: `anchor_extract_f2.py` never received the Task 16b/16c treatment. It
borrows `clean_span()` and `qa_flags()` from `anchor_extract.py`, but its own
`extract_text()` keeps the Task-14 span logic — no `cut_at_note()`, no
`anchor_prefix()`/`condensed_candidate()` fallback, no trailing section-letter strip,
and it never passes `siblings=` to `qa_flags()`, so the `grid-bleed` and value-set
offset nets are inert for F2. That is why a span stops dead at an embedded English
anchor (`PhilHealth`, `YAKAP/Konsulta package`) and why the next section's letter and
the next question's number ride in.

`anchor_extract_f2.py` is not in Task 22's Files list, and the fix is the same
plan-level decision Task 17 raised for F1 (which produced Tasks 16b and 16c). The
F2 extractor needs the same round before this import can run.

### Also found, and separable from the block

`spec/translations/*.json` carries **17 stale keys in each of the 7 locales** (119
rows) whose English no longer exists anywhere in the spec — the pre-m3 combined
UHC-attribution battery (`Has the increase in equipment been implemented since the
UHC Act was passed in 2019 and was it a result of the UHC Act?` and its
`Yes, this was …` / `No, this has not …` option set, plus
`Yes/No, specify other reason __________`). They are dead: `localizeString()` looks
up by exact English, so nothing ever reads them.

They are **the entire content of today's `audit-translations.py` output** — 119
suspects, all `ORPHAN key`, zero hits on any other check. Retiring them
(`apply-paper-translations.py --retire "<English>"`, never by hand) takes the audit
to 0 suspects and turns two of the three Task-22 vitest guards green. It is held back
with the rest of this task only because it shares the same `--apply` path.

## Task 22 attempt 2: survey-body import — APPLIED (tables superseded by fix round 1 below)

Attempt 1 stopped because 29 % of the F2 write set was defective. Task 21b ported the
F1 span rules into `anchor_extract_f2.py`; this attempt re-ran the extract with that
tool (byte-identical to the run 21b gated), applied it, and retired the 17 stale keys
in the same run.

### Extract

`anchor_extract_f2.py --source raw/Survey-Instruments-2026-08-21/Translations
--english-strings deliverables/F2/PWA/app/spec/english-strings.json
--out deliverables/CSPro/data/translations-official/out-aug21/F2`

393 anchors. Re-running it reproduced all 15 output files byte-for-byte, so the extract
this import used is exactly the one Task 21b's acceptance gate passed.

**Normalized-key collisions (2, from the extract's QA report)** — both are case-only
duplicates of the same option label and neither reaches the maps, because the join is on
the exact English string, not the normalised one:

- `not applicable` <- `Not Applicable`, `Not applicable`
- `other specify` <- `Other (specify)`, `Other (Specify)`

### Pre-apply gates (all run on the dry-run report, before `--apply`)

| gate | result |
|---|---|
| `english-furniture` in the write set | **0** |
| `mis-anchored` | **0** |
| `local-directive` as a clean value | **0** |
| `vs-offset` | **0** |
| strict-prefix truncations (any kind) | **0** |
| paper question-numbering furniture in a value | **0** |
| ballot box / routing tag / `Note:` label / `(Specify` furniture in a value | **0** |
| `truncated` | 6, all listed below with cause |

The 6 residual rows are all NEW keys whose value is the COMPLETE sentence: the Aug-21
paper prints no terminal `?` on those questions, and the sweep's "long English ending in
`?`" heuristic fires on that. Each was checked against the paper's own text dump — in
every one the next thing the paper prints is the option row, so nothing is cut:

| locale | English | what the paper prints next |
|---|---|---|
| ceb | Does this facility implement DOH licensing standards? | `☐ Yes Oo ☐ No <proceed to Q22> Wala` |
| bis | If yes, was it a result of the UHC Act enacted in 2019? | `☐ Implemented as a direct result of the UHC Act …` |
| bis | Have electronic medical records been used in this facility? | `☐ Yes Oo ☐ No <proceed to Q18> Wala` |
| bis | Have there been changes in the referral system in this facility? | `☐ Yes Oo ☐ No <proceed to Q19> Wala` |
| ilo | Have electronic medical records been used in this facility? | `☐ Yes (Wen) ☐ No <proceed to Q18> (Saan …)` |
| hil | Does this facility implement primary care quality measures? | `☐ Yes Huo ☐ No <proceed to Q25> Wala` |

### Apply

```
APPLIED  anchors=393
locale  unmatched  override  seeded  same-as-en  already  write  replace  retire  saved
fil             0         1       0           0      221     16       37      17  yes
ceb             0         0       0           0      266     16        4      17  yes
bis             0         0       0           0      267     12        5      17  yes
ilo             0         2       0           0      245     17       14      17  yes
hil             0         2       0           0      193     17        9      17  yes
war             0         4       0           0      213     15       58      17  yes
bcl             0         1       0           0      253     14        5      17  yes
```

`unmatched` 0 everywhere. 239 values written or replaced. A second dry run afterwards
writes nothing (`saved = no` on all seven), so the import is replayable.

### The 17 stale keys, retired

Retired with `apply-paper-translations.py --retire "<English>"` in the same run — never
by hand. They are the pre-m3 combined UHC-attribution battery, whose English no longer
exists anywhere in the spec (m3 split it into a "has there been an increase …" item plus a
separate attribution item), so `localizeString()` could never reach them:

- Has the increase in equipment been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?
- Has the increase in supplies been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?
- Has the use of electronic medical records at the facility been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?
- Have the DOH licensing standards been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?
- Have the PhilHealth accreditation requirements been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?
- Have the changes in staffing been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?
- Have the changes to the referral system (inbound or outbound) been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?
- Have the improved clinical practice guidelines been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?
- Have the primary care quality measures been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?
- Have the service delivery protocols been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?
- No, and we have no plans to do this in the next 1-2 years
- No, specify other reason __________
- No, this has not been implemented yet, but we plan to in the next 1-2 years
- Yes, specify other reason __________
- Yes, this has been implemented or improved recently, but not due to the UHC Act
- Yes, this was implemented as a direct result of the UHC Act
- Yes, this was pre-existing, but it has significantly improved due to the UHC Act

The retirement list is not hard-coded: it is recomputed as the keys the live maps hold
that `spec/english-strings.json` no longer contains, and the run refuses unless all seven
maps agree on the same set.

### Overrides (10, `aug21-overrides.json["F2"][loc]`, all `"scope": "survey"`)

**Paper-side defects — `keep: null`, never write; the live value stays (3).** These are
mistakes on the Aug-21 page, not extractor defects, so no span rule can reach them:

| locale | English | the paper's defect |
|---|---|---|
| bcl | Have you heard about the Bagong Urgent Care and Ambulatory Service (BUCAS) center? | prints `☐ YesIyo` with no space, so the `Yes` anchor cannot match |
| ilo | What is your understanding about the No Balance Billing (NBB)? | misprints the option as `Patient does not pay any hospital billn` |
| hil | What is your opinion on the policy of charging different professional fees based on the patient's ability to pay? | the Q82 Likert row is printed with only the local scale labels, so nothing anchors |

**Paper omits terminal punctuation — `keep` = the live value verbatim (5).** The Aug-21
span is a strict prefix of the live value and drops only punctuation:

| locale | English | live value kept |
|---|---|---|
| fil | In your opinion, BUCAS Centers have: | `Sa iyong opinyon, ang BUCAS Center ay:` |
| war | Have you heard about Universal Health Care (UHC) prior to this survey? | `… antes hini nga surbey?` |
| war | Predictable revenue due to capitation | `Mababaruan nga kita tungod han kapitasyon .` |
| war | YAKAP is more comprehensive | `Mas komprehensibo an YAKAP .` |
| war | High volume of patients | `Hataas nga kadamo han mga pasyente .` |

**Found by the two extra scans this task ran, both a defective replace of a complete live
value — `keep` = the live value (2).** The by-category sweep is structurally blind to
both, because each value ends in `.` and so no `truncated` rule fires:

| locale | English | what the extract would have written | kept instead |
|---|---|---|---|
| hil | If yes, what are the implications? | `Kon oo, ano ang mga implikasyon? 71a. 71b.` (the paper's own sub-question numbering) | `Kon oo, ano ang mga implikasyon?` |
| ilo | My work is emotionally exhausting. | `.Makabannog iti emosional ti trabahok.` (the paper prints a stray leading period) | `Makabannog iti emosional ti trabahok.` |

### `npm run generate`

```
generator: 11 section(s), 141 supported item(s), 0 unsupported.
  translations loaded: fil:301, ceb:306, bis:303, ilo:311, hil:292, war:318, bcl:304
```

Those are RAW key counts, and they read slightly LOWER than before because 17 dead keys
were retired from every map in the same run. Against the LIVE key count — raw minus the
17 orphans — every locale gained exactly its write count:

| locale | live before | live after | delta |
|---|---:|---:|---:|
| fil | 285 | 301 | +16 |
| ceb | 290 | 306 | +16 |
| bis | 291 | 303 | +12 |
| ilo | 294 | 311 | +17 |
| hil | 275 | 292 | +17 |
| war | 303 | 318 | +15 |
| bcl | 290 | 304 | +14 |

`src/generated/schema.ts` is unchanged — translations never touch the schema.

### Coverage (`scripts/f2-coverage.py`, the single coverage source)

Label objects in `src/generated/items.ts` carrying a dialect string, out of 740.

| locale | before | after | delta | before % | after % |
|---|---:|---:|---:|---:|---:|
| fil | 533 | 594 | +61 | 72 % | 80 % |
| ceb | 550 | 611 | +61 | 74 % | 83 % |
| bis | 549 | 570 | +21 | 74 % | 77 % |
| ilo | 554 | 617 | +63 | 75 % | 83 % |
| hil | 530 | 593 | +63 | 72 % | 80 % |
| war | 565 | 625 | +60 | 76 % | 84 % |
| bcl | 547 | 597 | +50 | 74 % | 81 % |

Every locale is above its baseline. The denominator is 740, not the plan's 707.

### Gates

| gate | result |
|---|---|
| `npx tsc -b --force` | exit 0 |
| `npm test` | 80 files / 696 tests passed (was 79 / 693 + this task's 3) |
| `python scripts/audit-translations.py` | **exit 0, 0 suspects** (was exit 1, 119 `ORPHAN key`) |
| `git diff --stat` | only the seven `spec/translations/*.json` and `src/generated/items.ts` |
| second dry run | writes 0 — replayable |

No `trailing question number` audit residual survived, so no whitelist is needed.

### Worklist — what is NOT imported this round

809 flagged rows across the seven locales stay in `out-aug21/F2/{loc}_flagged.json` for
Task 45: 433 `empty` (the paper prints no translation under that anchor), 170
`not-in-paper`, 77 `echo-english`, and the rest smaller families. **54 of those are keys
that were clean before Task 21b tightened the span rules** — real translations the paper
carries that this round holds back rather than ship with furniture attached. Two named
gaps for that worklist:

- `fil` Section A `Q2` (`What type of employment do you have at this health facility?`)
  is still English on the Tagalog paper — the question is followed straight by the ballot
  boxes, with no Tagalog under it, so there is nothing to import and nothing may be
  invented.
- `hil` is the weak locale: 167 flagged rows against 98–115 elsewhere, because the
  Hiligaynon paper prints whole option rows in local only, leaving no English to anchor on.

## Task 22 fix round 1: the whitespace ruling, applied (attempt 2's tables above are superseded)

Attempt 2 wrote all 79 rows whose Aug-21 value differed from the live value only by
whitespace. The controller ruling after Task 21b's fix round says to split them: **hold**
the 27 rows where the paper INSERTS an internal space (a word wrapped across a line
break, and the PDF text layer keeps the break as a space) and **write** the 52 rows
where the paper only removes a stray space. Attempt 2 implemented neither half, so
`Umanamong` shipped as `Uma namong`, `Hindi Sang-ayon` as `Hindi Sang- ayon` and `pag-adto`
as `pag- adto` — in the Agree/Disagree scale, the most frequently rendered strings in the
instrument. Nothing could see it: every gate of that wave compared the incoming value
against the PAPER or against the ENGLISH, never against the LIVE value.

This round re-ran the whole import from the pristine maps with the split applied.

### The 27 held rows (`keep` = the live value, reason `PDF line-break whitespace`)

Seeded by script — `<ws>/task-22/_whitespace_holds.py` classifies every whitespace-only
`replace` row of the dry-run report as inserted / removed / mixed, and
`_write_f2_overrides.py` merges the inserted set into `aug21-overrides.json["F2"][loc]`
with `"scope": "survey"`. No key in this table was typed by hand.

| # | locale | English key | live value kept | Aug-21 value rejected |
|---:|---|---|---|---|
| 1 | `bcl` | Of those referred, what is/are the most common way/s you receive referrals from lower-level facilities? | `…paagi kan pag-receive nindo …` | `…paagi kan pag- receive nindo …` |
| 2 | `bcl` | What are the most common tasks you do in your daily work that you could delegate to a more junior staff or different staff member? | `…ng pang-aldaw-aldaw na traba…` | `…ng pang-aldaw- aldaw na traba…` |
| 3 | `bis` | Patient self-care support (e.g., cleaning patients, assisting with toilet) | `…tabang sa pag-adto sa kasily…` | `…tabang sa pag- adto sa kasily…` |
| 4 | `bis` | The following questions ask about awareness of BUCAS center and GAMOT package. Please check the box/es of your answer. | `…ge. Palihog I-chek ang mga b…` | `…ge. Palihog I- chek ang mga b…` |
| 5 | `ceb` | I have been compensated for working overtime. | `… sa akong pag-overtime.` | `… sa akong pag- overtime.` |
| 6 | `ceb` | The following questions ask about No Balance Billing (NBB) and Zero Balance Billing (ZBB). Please check the box/es of your answer. | `…B). Palihug i-check ang kaho…` | `…B). Palihug i- check ang kaho…` |
| 7 | `fil` | Disagree | `Hindi Sang-ayon` | `Hindi Sang- ayon` |
| 8 | `fil` | Facility's standard referral form | `…form ng inyongpasilidad` | `…form ng inyong pasilidad` |
| 9 | `fil` | Hard to coordinate | `…ipag-ugnayan omakipag-coordi…` | `…ipag-ugnayan o makipag-coordi…` |
| 10 | `fil` | Of those referred, what is/are the most common way/s you receive referrals from lower-level facilities? | `…mula sa lower-level faciliti…` | `…mula sa lower- level faciliti…` |
| 11 | `fil` | Strongly Disagree | `…na Hindi Sang-ayon` | `…na Hindi Sang- ayon` |
| 12 | `fil` | What is/are the most common way/s you send referrals to higher level facilities? | `…ng mga pinaka-karaniwang par…` | `…ng mga pinaka- karaniwang par…` |
| 13 | `fil` | What opportunities to develop leadership skill/s would be useful to you? | `…giging kapaki-pakinabang par…` | `…giging kapaki- pakinabang par…` |
| 14 | `hil` | Disagree | `Nagapamalibad` | `Nagapamalib ad` |
| 15 | `hil` | I am treated fairly at the workplace. | `… sa akon gina-ubrahan.` | `… sa akon gina- ubrahan.` |
| 16 | `hil` | Neither Agree nor Disagree | `…on nagapamalibad` | `…on nagapamalib ad` |
| 17 | `hil` | On a scale of 1-5 with 5 as highest, does your professional fee compensate for the medico-legal risks associated with your specific field? | `… risgo medico-legal nga kala…` | `… risgo medico- legal nga kala…` |
| 18 | `hil` | Patients seek healthcare in different ways | `…gita sang pag-atipan sa gaka…` | `…gita sang pag- atipan sa gaka…` |
| 19 | `ilo` | Agree | `Umanamong` | `Uma namong` |
| 20 | `ilo` | Disagree | `…n nga umanamong` | `…n nga umanamon g` |
| 21 | `ilo` | Majority of patients walk-in/self-referred, some are referred | `…walk- in/self-referred, dadd…` | `…walk- in/self- referred, dadd…` |
| 22 | `ilo` | Neither Agree nor Disagree | `…n nga Umanamong wenno Saan n…` | `…n nga Umanamon g wenno Saan n…` |
| 23 | `ilo` | Strongly Agree | `…g nga Umanamong` | `…g nga Umanamon g` |
| 24 | `ilo` | Strongly Disagree | `… a Di Umanamong` | `… a Di Umanamon g` |
| 25 | `ilo` | The final section focuses on your satisfaction about your compensation, working environment, and professional development. Please check the box of your answer. | `…ngaasiyo ta i-check-yo ti ka…` | `…ngaasiyo ta i- check-yo ti ka…` |
| 26 | `war` | Administrative tasks (e.g. writing notes, requesting tests, encoding) | `…-eksamin, pag-encode)` | `…-eksamin, pag- encode)` |
| 27 | `war` | How often do you give discounts/adjustments on your professional fee? | `…diskwento/pag-adjust ha imo …` | `…diskwento/pag- adjust ha imo …` |

Two of those 27 are held by the letter of the ruling even though the inserted space would
have REPAIRED the live value (`fil` `Standard referral form ng inyongpasilidad` and `fil`
`Mahirap makipag-ugnayan omakipag-coordinate` — the live value glues two words). Holding
them changes nothing on the tablet; they are named here so the controller can release them
with a one-line override if the repair is wanted.

### The 52 written rows (stray space removed)

`war` 52 — all of them a space before the sentence's final period
(`… ha pribado nga praktis .` -> `… ha pribado nga praktis.`), which is the Waray paper
cleaning up its own June-5 artefact. Written as the ruling directs.

### Three more overrides the fix round's scans found

| locale | English key | decision | why |
|---|---|---|---|
| `ilo` | What are the most common tasks you do in your daily work that you could delegate to a more junior staff or different staff member? | `keep` = live value | the span opens `b(Ania …` — a stray glyph from the paper's sub-question label |
| `ilo` | I am compensated fairly. | `keep` = live value | the span ends `pannakabayadko.l` — one letter swept from the next printed line |
| `bcl` | Pre-existing prior to UHC but subsequently enhanced or expanded due to UHC Act | `keep: null` | NEW key whose only value is `… dakula an pag- improve …`; a defective new key is never written, so the key stays absent (worklist) |

The `bcl` hold costs 10 label objects (that option label repeats across the UHC-attribution
battery), which is why `bcl` lands at 587/79 % below instead of 597/81 %.

### Corrected pre-apply gates (dry run, before `--apply`)

`_defect_sweep_f2.py` gained a `whitespace-delta` family — a `replace` row whose value
equals the live value once all whitespace is squashed is a decision, never a silent write —
so the table attempt 2 printed can now be read honestly:

| family | attempt 2 (as printed) | attempt 2 (true) | fix round 1 |
|---|---:|---:|---:|
| `english-furniture` | 0 | 0 | 0 |
| `mis-anchored` | 0 | 0 | 0 |
| `local-directive` | 0 | 0 | 0 |
| `vs-offset` | 0 | 0 | 0 |
| `whitespace-delta` — inserted (must hold) | *not detected* | **27** | **0** |
| `whitespace-delta` — removed (write) | *not detected* | 52 | 52 |
| `truncated` | 6 | 6 | 6 |
| values `--apply` would write | 239 | 239 | **209** |

The 6 `truncated` rows are unchanged from attempt 2: all six are NEW keys whose value is
the complete sentence, verified against the paper by `_verify_noterm.py` (the paper prints
no terminal `?`). Strict-prefix rows 0 (`task-21b/_prefix_truncation_f2.py`), paper
question-numbering furniture 0, ballot box / routing tag / `Note:` / leading punctuation 0.

### Apply, gates and coverage after the fix round

```
APPLIED  anchors=393
locale  unmatched  override  seeded  same-as-en  already  write  replace  retire  saved
fil             0         8       0           0      221     16       30      17  yes
ceb             0         2       0           0      266     16        2      17  yes
bis             0         2       0           0      267     12        3      17  yes
ilo             0        11       0           0      245     17        5      17  yes
hil             0         7       0           0      193     17        4      17  yes
war             0         6       0           0      213     15       56      17  yes
bcl             0         4       0           0      253     13        3      17  yes

npm run generate -> translations loaded: fil:301, ceb:306, bis:303, ilo:311, hil:292,
                    war:318, bcl:303        (bcl 303, not 304: the held new key)
```

`aug21-overrides.json["F2"]` now holds **40** entries (13 hand-decided + 27 seeded
whitespace holds), all per (English string, locale), all `"scope": "survey"`.

| locale | coverage before | attempt 2 | fix round 1 | % |
|---|---:|---:|---:|---:|
| fil | 533 | 594 | 594 | 80 % |
| ceb | 550 | 611 | 611 | 83 % |
| bis | 549 | 570 | 570 | 77 % |
| ilo | 554 | 617 | 617 | 83 % |
| hil | 530 | 593 | 593 | 80 % |
| war | 565 | 625 | 625 | 84 % |
| bcl | 547 | 597 | **587** | 79 % |

Denominator 740. Coverage is unchanged from attempt 2 except `bcl`, because a hold keeps
the live value — the label object still carries a dialect string, just the correct one.

| gate | result |
|---|---|
| `npx vitest run scripts/lib/apply-translations.aug21.test.ts` | 7 passed (3 + 4 new shape invariants) |
| `npx tsc -b --force` | exit 0 |
| `npm test` | 80 files / **700** tests passed |
| `python scripts/audit-translations.py` | exit 0, 0 suspects |
| `python scripts/f2-coverage.py` | above baseline in all 7 locales |
| `git diff --stat` | only the 7 `spec/translations/*.json` + `src/generated/items.ts` (`schema.ts` NOT in the diff) |
| second dry run | write 0 / replace 0 / retire 0, `saved no` — replayable |
| `pytest` `translations-official` / `F2 app scripts` | 170 passed / 11 passed |

### The permanent guard

`scripts/lib/apply-translations.aug21.test.ts` (Task 23 commits it) now also asserts the
shape invariants a paper import can violate and a translator never does: no mid-word
`x- y`, no dangling single-letter token, no ballot box / routing tag / `Note:` /
question-number residue, no untrimmed value. Nine pre-existing values that already carried
one of those shapes before this import are listed in a frozen `PRE_EXISTING` set in the test
(2 `ilo` `walk- in`, 1 `hil` value that is an English heading, 6 `bcl` preambles that
abbreviate `sa` as `s`) — worklist items, and the set is frozen so a NEW one fails the
guard. Replayed against attempt 2's maps (`_red_demo.py --regress`) the guard fails 2 of 4
new assertions with all 18 + 6 defective values listed; against the corrected maps it is
green.
