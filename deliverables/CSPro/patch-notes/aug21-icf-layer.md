# Aug-21 ICF layer (read-aloud consent screens)

**Date:** 2026-08-25 · **Module:** `icf_content.py` · **Channel:** DEV

## Footer stamp moved: 06/05/2026 -> 08/21/2026

`clearance_html()`'s "Translated Questionnaire ver." line bumped from `06/05/2026` to
`08/21/2026` as part of the Aug-21 import. This one-line change is high blast-radius: the
clearance block renders on the cover footer **and both ICF screens**, in **all three**
instruments (F1/F3/F4), in **all eight** locales (EN + 7 translations) — 24 render sites per
instrument, 72 total. It is also, on its own, what makes waves 1/3/4 of this pass a
*visible* change on-device: with no `icf.json` translations applied yet (that lands with
Task 10), the stamp bump is the only byte difference in the generated `.qsf` bodies versus
the pre-Aug-21 build. Verified via Step 5 of the task-9 brief:

```
cd deliverables/CSPro
python -c "import icf_content as i; h=i.build_screen_html('F1',1); print('08/21/2026' in h, '06/05/2026' in h)"
# True False
```

## F3-Tagalog header outlier — do not "correct" it

20 of the 21 Aug-21 translated PDFs carry `08/21/2026` in their page **header**; their SJREB
line still prints `06/05/2026` (the header is the newer stamp, the SJREB line is untouched
from the June-5 pack). **F3-Tagalog is the one exception**: it prints `06/05/2026` on
**both** lines — its header was not updated in the Aug-21 pack, unlike every other
instrument/locale combination.

F3-Tagalog is still part of the same Aug-21 delivery, so `clearance_html()` stamps
`08/21/2026` for **all three instruments uniformly** — it does not special-case F3 to keep
`06/05/2026`. This is a deliberate, source-verified decision, not an oversight: a future
pass diffing PDF headers against the code will find F3-Tagalog's header doesn't match the
`08/21/2026` stamp and may be tempted to "fix" F3 back to `06/05/2026`. Don't — the code
stamp reflects the pack date, not any one PDF's un-updated header, and reverting F3 alone
would make the three instruments' footers disagree for no defect-based reason. The outlier
is also recorded in `clearance_html()`'s own docstring for code readers.

## Fix round 1 addendum: EN-match now canonicalized, not byte-exact

`screens_for()`'s per-paragraph translation gate originally compared the icf.json-stored
`EN` to the live `SCREENS` paragraph with `==` — a raw byte comparison. Seven of the
fourteen ICF paragraphs carry curly quotes or a double space that an extractor could
plausibly normalize (F1/F3 screen-1 paragraph 0: `"(ASPSI).  We are"` double space; F1/F3/F4
screen-2 paragraphs with `’`/`‘`/`”` curly quotes), so a byte-exact gate re-introduced the
same silent-fallback class notes_lookup._canon exists to prevent (#1235/#1256). Fixed by
comparing through `notes_lookup._canon()` (imported, not re-implemented, so the two modules
cannot drift) instead of `==`. See `icf_content.py`'s module docstring and `screens_for()`'s
docstring, and `test_screens_for_canonicalizes_en_before_comparing` in
`data/translations-official/test_notes_icf_aug21.py`.

## Task 10: `icf.json` — the seven translations of every consent paragraph

`data/translations-official/extract_icf.py --source <Aug-21 Translations>` reads the 21
translated papers and writes `icf.json` (+ `icf-report.json`). Anchors are the English
paragraphs in `icf_content.SCREENS`, not the paper's own English — the paper opens "Hello,
my name is ... I work for" where the build reads "We work for ...", so paragraph 1 is found
by its identical TAIL (`suffix`) on every paper. The `<b>` contact blocks are boundaries
only and are never translated.

**Per-paper anchor kinds** (7 anchored paragraphs on F1, 8 on F3/F4; contact blocks excluded):

| paper | exact | prefix | suffix | override | dropped-english | dropped-short | missing |
|---|---|---|---|---|---|---|---|
| F1-BCL | 5 | . | 1 | 1 | . | . | . |
| F1-BIS | 6 | . | 1 | . | . | . | . |
| F1-CEB | 6 | . | 1 | . | . | . | . |
| F1-HIL | 6 | . | 1 | . | . | . | . |
| F1-ILO | 6 | . | 1 | . | . | . | . |
| F1-FIL | 5 | . | 1 | 1 | . | . | . |
| F1-WAR | 6 | . | 1 | . | . | . | . |
| F3-BCL | 7 | . | 1 | . | . | . | . |
| F3-BIS | 5 | . | 1 | 2 | . | . | . |
| F3-CEB | 7 | . | 1 | . | . | . | . |
| F3-HIL | 4 | 1 | 1 | . | 1 | . | 1 |
| F3-ILO | 7 | . | . | 1 | . | . | . |
| F3-FIL | 7 | . | 1 | . | . | . | . |
| F3-WAR | 7 | . | 1 | . | . | . | . |
| F4-BCL | 6 | . | 1 | 1 | . | . | . |
| F4-BIS | 7 | . | 1 | . | . | . | . |
| F4-CEB | 7 | . | 1 | . | . | . | . |
| F4-HIL | 7 | . | 1 | . | . | . | . |
| F4-ILO | 7 | . | . | 1 | . | . | . |
| F4-FIL | 7 | . | 1 | . | . | . | . |
| F4-WAR | 7 | . | 1 | . | . | . | . |

`aug21 icf: n_written 152, n_replaced 0, n_overridden 7, n_kept_prior 0` — 159 of a possible
161 stored values. Re-running the extractor over the file it just wrote reports
`n_written 0, n_replaced 0`, i.e. the extraction is stable.

**Fix round 1 (2026-08-25).** The F1-Bisaya and F1-Cebuano papers print the rights/contact
paragraph in full but **drop its trailing colon** and run the translation straight on
("... you can contact Kung aduna ..."). `locate()` splits on whitespace, so `contact:` !=
`contact` cost the whole last anchor word: it stayed at the head of the window and
`polish()`'s lead trim kept it (`looks_english()` needs >= 3 function words to call a lead
English), and `icf.json` shipped `"contact Kung aduna pa kay mga pangutana ..."` for
`F1 icf:2:3` BIS and CEB — one English word the enumerator would read aloud. `locate()` now
retries the anchor with its trailing punctuation stripped and reports that as `exact`, and a
`prefix` match whose leftover tail is too short for the suffix re-match walks the tail off
token by token. Both papers are now `exact` on `icf:2:3`; nothing else in `icf.json` moved.

**Coverage** (`python -c "import icf_content as i; print(i.coverage())"`):

| locale | differs | stored |
|---|---|---|
| FIL | 23 | 23 |
| BCL | 23 | 23 |
| BIS | 23 | 23 |
| CEB | 23 | 23 |
| WAR | 23 | 23 |
| HIL | 21 | 21 |
| ILO | 23 | 23 |

**Seeded overrides** (`aug21-overrides.json`, each with a reason):

| key | why |
|---|---|
| `F1 icf:1:1:FIL` | the F1-Tagalog paper prints **F3's** English coverage sentence where F1's belongs, so the English anchor matches only a prefix and the extractor correctly drops the English remainder; the Tagalog paragraph itself is good and is seeded verbatim. |
| `F3 icf:2:3:BIS`, `F3 icf:2:4:BIS` | the F3-Bisaya paper prints the last two English paragraphs as one run and both Bisaya paragraphs after them, so 2:3's window is empty and 2:4's held both; split back apart, verbatim. |
| `F1 icf:2:1:BCL`, `F4 icf:2:1:BCL`, `F3 icf:1:0:ILO`, `F4 icf:1:0:ILO` | the paper ends these paragraphs with no sentence-final punctuation; wording verbatim, only the `.` restored. |

**Items for ASPSI** (consolidated status, Task 47):

1. **F1-Tagalog page 1, paragraph 2** prints F3's English coverage sentence ("The questions
   will cover your Patient Profile ...") above the correct F1 Tagalog. English-side defect on
   the paper; the CAPI build is unaffected (override seeded).
2. **F3-Hiligaynon consent page** carries an older/other English variant: an extra
   "your family's or child's personal information outside of the study team" clause in the
   privacy paragraph, **no** Php 100 token-of-appreciation sentence in the risks/benefits
   paragraph, and the "Nothing bad will happen ..." paragraph is missing entirely. Two of its
   paragraphs therefore stay English on-device (HIL coverage 21/23) — no Hiligaynon text on
   the paper matches what the instrument says.
3. **Missing sentence-final punctuation** on F1-Bicolano 2:1, F4-Bicolano 2:1 and
   F3/F4-Ilocano 1:0; **F1-Bicolano 2:1 also stops short** of the English (no "You are free to
   decline ..." sentences).
4. The **Ilocano F3/F4 papers bracket every translated paragraph whole** ("(<Ilocano>.)") and
   paragraph 1 is missing its closing bracket. The extractor strips the wrapper.
