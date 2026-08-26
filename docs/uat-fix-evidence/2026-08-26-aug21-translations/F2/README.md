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
