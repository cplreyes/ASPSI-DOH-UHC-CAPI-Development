# Aug-21 translations — F2 PWA m4 render evidence (2026-08-26)

**Driver:** ASPSI revised Deliverable 2 (Aug-21), 7 translated F2 questionnaires. **Ships as:** spec `2026-08-26-m4` (DEV channel).
**Method:** `npx playwright test -c e2e/playwright.config.ts e2e/locale-shots.spec.ts` against the production build served by `vite preview` (`VITE_F2_PROXY_URL=https://uhc-hcw.asiansocial.org`), backend stubbed by `e2e/fixtures/mock-backend`, enrollment seeded straight into IndexedDB, locale switched exactly the way the app persists it (`localStorage` key `f2_locale`). One screenshot per locale, full page, viewport 1280x1600. The spec stamp visible in the header of every shot is `2026-08-26-m4`.

| file | what it shows |
|---|---|
| `f2_secA_en.png` | Section A in English — the unchanged source wording |
| `f2_secA_fil.png` | Section A in Filipino |
| `f2_secA_ceb.png` | Section A in Cebuano — Q1–Q5 stems from the Aug-21 paper, incl. Q2 employment |
| `f2_secA_bis.png` | Section A in Bisaya |
| `f2_secA_ilo.png` | Section A in Ilocano |
| `f2_secA_hil.png` | Section A in Hiligaynon |
| `f2_secA_war.png` | Section A in Waray |
| `f2_secA_bcl.png` | Section A in Bicolano |
| `f2_consent_fil.png` | the ICF consent gate in Filipino — Part-I paragraphs (study / privacy / benefits / rights) + the contacts line |

**Q2 employment is Filipino-exempt, and that is the source, not the build.** ASPSI's cleared
Aug-21 **FIL** F2 questionnaire prints Q2 in English only — `text-aug21/F2_FIL.txt` reads
`2. What type of employment do you have at this health facility? ☐ Regular ☐ Casual …` with
no Tagalog line beneath it — so `anchor_extract_f2.py` flagged the pair `empty` and wrote
nothing, which is the correct behaviour (never invent a dialect string). The other six papers
DO carry it and the other six shots render it: `f2_secA_ceb.png` shows
`Unsa ang klase sa imong trabaho niini nga pasilidad?`, and `bis/ilo/hil/war/bcl` each carry
their own. That is what proves the survey-body import landed. FIL's Q2 has gone back to
ASPSI's translators on the worklist.

**Option labels stay English on purpose.** The ballot-box option lists (`Regular`, `Casual`,
`Nurse`, `Midwife`, …) are printed in English in every one of the seven papers, so almost none
of them have a translated counterpart to import. `Kaswal` in the Cebuano shot is one of the
few the paper does translate — proof the option channel works where source exists. F2 stores
option **label text**, not positional codes, so nothing about answers or payloads changed.

**Consent:** headings, buttons and the raffle block are deliberately still English (chrome, not
ICF body). The Part-I body paragraphs are the Aug-21 cleared consent text, imported by
`extract_icf_f2.py` into `src/i18n/locales/consent.aug21.ts` and spread last into each locale
bundle; a locale missing a paragraph falls back to English.

**Coverage** (label objects carrying a dialect string, of 740 in `src/generated/items.ts`,
`python scripts/f2-coverage.py`):

| | fil | ceb | bis | ilo | hil | war | bcl |
|---|---|---|---|---|---|---|---|
| before (m3) | 533 (72 %) | 550 (74 %) | 549 (74 %) | 554 (75 %) | 530 (72 %) | 565 (76 %) | 547 (74 %) |
| after (m4) | 594 (80 %) | 611 (83 %) | 570 (77 %) | 617 (83 %) | 593 (80 %) | 625 (84 %) | 587 (79 %) |
---

## m5 (2026-08-27) — the row-inheritance repair

**Ships as:** spec `2026-08-27-m5` (DEV channel), commit `fb91241a`, deployed 2026-08-27
02:29 UTC / 10:29 MNL. `build-info.json` live: sha `fb91241a1e13ff1a5e897bb1c363033a863a9861`
== `git rev-parse HEAD` at deploy time, `matches_main: true`; `deploy-f2-pwa.ps1 -VerifyOnly`
exit 0. `fb91241a` is the **application** commit and is what PROD is serving; the commits
after it in this wave add only evidence (PNGs and markdown, this file included) and change
nothing `vite build` reads, so a live sha of `fb91241a` under a later `main` is correct, not
drift. The next code change re-deploys and moves it.

**What was wrong in m4.** The Aug-21 papers lay an option grid out in two columns, so the PDF
text layer returns both boxed ENGLISH rows first and both translations after them as one
block. The first row's span is then box-to-box (empty) and the whole block falls to the
second row. Q57 `war` took the block:

```
"City / LGU standard referral form":
-  "Syudad / LGU surundon nga porma han pagrefer DOH nga surundon nga porma han pagrefer"
+  "Syudad / LGU surundon nga porma han pagrefer"
```

`DOH standard referral form` itself extracted `empty` on that page, so it kept — and still
keeps — its correct pre-wave value `DOH nga surundon nga porma han pagrefer`. Both rows now
read correctly and neither was typed by hand.

**How it was repaired.** Not by editing a map. The extractor's `f2_sibling_run()` rule (Task
48) now HOLDS such a span instead of writing it; the seven maps were restored from the
pre-wave baseline `af1fa569` (byte-identical, proven by blob sha1) and the whole wave
re-applied through `scripts/apply-paper-translations.py` against the corrected extract, with
the same 17 stale keys retired in the same run and the same 40 `aug21-overrides.json` F2
entries. A second dry run writes 0 / replaces 0 / retires 0.

| file | what it proves |
|---|---|
| `map-delta-m5.txt` | the complete live delta m4 -> m5: **one** value, in `war`. Six maps byte-identical, `items.ts` one line |
| `served-content-m5.txt` | the bundle PROD is serving (`assets/admin-DebwnCUG.js`, 692,097 chars) contains `2026-08-27-m5` and the corrected value, and no longer contains `2026-08-26-m4` or the glued one |
| `f2_secA_*.png`, `f2_consent_fil.png` | re-shot on the m5 build. The ONLY pixels that move between the m4 and m5 shots are the stamp `2026-08-26-m4` -> `2026-08-27-m5` (28x10 px at 190,49; measured per file with a pixel diff) |

The Section A / consent shots cannot show Q57 — it is in Section F — so the served-bundle
string check above is the render proof for this particular row.

**Coverage is unchanged** (a corrected value, not an added one): 740 label objects,
fil 594 (80 %) ceb 611 (83 %) bis 570 (77 %) ilo 617 (83 %) hil 593 (80 %) war 625 (84 %)
bcl 587 (79 %).

**Gates.** `npm run generate`; `tsc -b --force` exit 0; `eslint` exit 0; `vitest run
--maxWorkers=2` 81 files / **703** tests passed (701 + the two new invariants);
`audit-translations.py` exit 0, 0 suspects; `npm run build` exit 0; `locale-shots.spec.ts`
1 passed, `Captured locales: en, fil, ceb, bis, ilo, hil, war, bcl`.

**The guard now sees this class.** `scripts/lib/apply-translations.aug21.test.ts` gained two
invariants that judge an option group rather than one value — no two choices of one question
share a translation, and no choice carries a sibling choice's whole translation. Both were
RED on the m4 maps (the second listing exactly the Q57 row, no false positives) and are GREEN
here. One frozen exception was recorded with its evidence: `fil` `Agree but for clerical
tasks only` / `Disagree for both medical and clerical tasks` share one string in the Aug-21
paper itself and in the June-5 maps, so there is nothing to import — verified pre-existing at
`af1fa569`, not introduced by this wave. **That exception is gone: it was cleared in the fix
round below, and the allowlist now ships empty.**

---

## m5 fix round 1 (2026-08-27) — the duplicate fil option label, cleared

**Ships as:** the same spec stamp `2026-08-27-m5` (this changes a translation, not the
questionnaire), commit `ce05b931`, deployed 2026-08-27 03:16 UTC / 11:16 MNL.
`build-info.json` live: sha `ce05b931e4244ed9c7b00b6ada4f9b1f3092c6b1` == `git rev-parse HEAD`
== `origin/main`, `matches_main: true`; `deploy-f2-pwa.ps1` and `-VerifyOnly` both exit 0.
The stamp is deliberately unchanged — `LOCAL_SPEC_VERSION` versions the SPEC (it invalidates
drafts when items move), and no item, id, choice or code moved here. The commit sha in
`build-info.json` is what identifies this build.

**What was wrong.** The m5 record above disclosed a duplicate pair instead of clearing it, and
it was live: in Tagalog, BOTH rows of the Q95 grid read
`Sumasang-ayon, ngunit para lamang sa mga gawaing klerikal` — the AGREE wording. So a Filipino
respondent choosing `Disagree for both medical and clerical tasks` was reading the **opposite**
of the option they were picking. Pre-existing (present at `af1fa569`, at m4 and at m5), not a
regression of this wave — and shipped anyway, which is what this round fixes.

**How it was repaired — the F1/F3/F4 remedy, not a hand edit.** The Aug-21 fil paper prints
ONE Tagalog string against both rows of that two-column grid, so there is no distinct
candidate to import. An **English option beats a wrong one**: `scripts/apply-paper-
translations.py` gained the `remove: true` override semantic Task 49 gave the CSPro applier,
one entry was added to `aug21-overrides.json` (`F2 → fil`), and the wave was re-applied. The
key is deleted from **fil only** — `--retire`, the deletion F2 had before, would have taken
the six correct translations with it. The other six locales still render their own Disagree
wording; fil renders the English label.

| file | what it proves |
|---|---|
| `map-delta-m5-fix1.txt` | the complete live delta against BOTH baselines: **one** row, `fil` `Disagree for both medical and clerical tasks` removed. Six maps untouched, CRLF intact, 0 lone LFs |
| `served-content-m5-fix1.txt` | the bundle PROD serves (`assets/admin-Bxu9VVRp.js`) contains the AGREE Tagalog string **once** (was twice), carries the English `Disagree…` label, still carries the corrected war Q57 value, and still carries the ceb/war/bcl Disagree wording |
| `f2_secA_*.png`, `f2_consent_fil.png` | re-shot on this build and **byte-identical** to the m5 shots — correct: Q95 is in Section H, and the stamp did not move |

**Coverage:** `fil` 594 → **593** of 740 (79 %) — the single deliberate removal. The other six
are unchanged: ceb 611, bis 570, ilo 617, hil 593, war 625, bcl 587.

**Gates.** `npm run generate` (fil 301 → 300 keys); `tsc -b --force` 0; `eslint` 0;
`vitest run --maxWorkers=2` 81 files / **705** passed; `audit-translations.py` 0 suspects;
`npm run build` 0; `locale-shots.spec.ts` 1 passed; re-apply replay writes 0 / replaces 0 /
removes 0; pre-apply row-inheritance gate RED 0 / pre 0 / accepted 0.

**The guard got sharper too.** The sibling-run invariant's 15-character floor was justified by
a comment claiming no whole option translation is that short. 191 of the option values in
these seven maps are — so the rule could not see a glue of two SHORT options, which is exactly
the Agree/Disagree, Yes/No, Male/Female grid shape that caused the defect. The floor is a
false-positive bound (measured: 17 innocent rows below it, in two families) and now applies
only to the case-folded form; a verbatim form — the sibling's value at one end with its own
capitalisation — carries the short pairs with no floor and no allowlist. Three fixtures pin
the coverage: the m4 war Q57 defect, a 4-character + 11-character glue, and the two innocent
families. The duplicate-label allowlist now ships **empty**.

**Still on the translator worklist:** the fil Q95 Disagree row itself. Deleting it makes the
option honest, not translated — ASPSI's translators still owe the Tagalog wording.
