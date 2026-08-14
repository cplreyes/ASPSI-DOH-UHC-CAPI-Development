# Translation verbatim audit — F1 / F3 / F4 against the DOH-cleared June-5 questionnaires

**Date:** 2026-08-14 · **Reference:** `raw/DOH-Deliverable-2-2026-07-31/Data collection tools/`
(32 PDFs, 8 languages × 4 instruments, the SJREB-cleared set the tool footer already cites
as *Translated Questionnaire ver. 06/05/2026*).

Every translatable string in the three deployed CAPI instruments was joined to that source
by **question number** and compared. Nothing here was authored; the cleared source is
treated as authoritative throughout.

## Verdict

**Where the tool has a translation, it is overwhelmingly the cleared one: 92.1% of the
13,925 comparable strings match verbatim.** The problem is not wrong translations — it is
**missing** ones, plus a set of lexical choices the cleared source itself never settled.

| | strings |
|---|---|
| Verbatim / equivalent to the cleared source | **12,824** (92.1%) |
| Genuinely different wording | **1,101** (7.9%), in 395 distinct classes |
| Tool shows English while a cleared translation exists | **2,348** |
| → of those, safe to apply verbatim today | **1,737** |
| Legitimately English on both sides (acronyms, programme names) | 3,145 |

## 1. The biggest win: 1,737 strings can be filled today

These are questions where the tablet currently shows English although the cleared
questionnaire has a translation. No new translation work, no wording decision — the
cleared text simply is not reaching the tool. Machine-readable list: `safe_to_apply.json`.

| locale | safe to apply | share of its recoverable gap |
|---|---|---|
| ILO | 556 | 77% |
| HIL | 440 | 82% |
| BIS | 161 | 73% |
| CEB | 150 | 74% |
| FIL | 147 | 67% |
| BCL | 142 | 65% |
| WAR | 141 | 62% |

Ilocano and Hiligaynon — the two weakest locales in the tool — are where most of the
recoverable text sits, so this closes the worst gaps first.

The remaining 611 are held back deliberately: an enumerator directive is glued to the
cleared string, a page footer survived extraction, or the string is truncated. Those are
extraction damage, not cleared wording, and must not be pasted in.

## 2. Needs an ASPSI / translator decision — cannot be fixed in code

**The cleared source contradicts itself on four recurring answer labels.** For these,
"make it verbatim" has no single answer, and applying one form mechanically would just
move the inconsistency around. One ruling each is needed (per instrument, if the split
is deliberate):

- **"No"** — the largest item. Bikol is cleared as `Dae` throughout F1 but `Dai`
  throughout F3/F4. Bisaya and Cebuano flip in *both* directions — `Wala` at F3 Q22,
  `Dili` at F1 Q54 (Cebuano alone hangs 44 occurrences on this). Waray uses `Dire`,
  `Diri`, `Waray` and the apparent typo `Warat` interchangeably.
  *Note: Cebuano legitimately splits dili/wala by aspect, so the answer may well be
  per-question — it just needs documenting either way.*
- **"Don't know"** — Hiligaynon has five renderings (`Wala kabalo`, `Indi kabalo`,
  `Indi ko kabalo`, `Wala ko nabal-an`, `Wala ko hibalo`); Bisaya four; Bikol three
  (`Dai ko aram` / `Dai aram` / `Dae ko aram`); Ilocano three, one misspelled.
- **"Not applicable"** — Bikol four forms, Bisaya three. **Hard stop in Filipino F3 Q15:
  the cleared source maps both "Don't know" and "Not applicable" to `Hindi alam`.**
  Adopting verbatim would collapse two distinct answer codes into one identical label.
- **"Other (specify)"** — Hiligaynon has seven tails (`(ispecify)`, `(ispecificar)`,
  `Iban(specify)`, `(Ipahayag)`, `(Ispecified)`, …); Ilocano splits `Dadduma` vs
  `Sabali`; Bikol splits `Iba pa (pakispecify)` vs `Iba (ispecify)`.

## 3. Value-set offsets — do not adopt, and worth checking on the paper tool

A handful of cleared cells appear shifted by one row against their option, so adopting
them would silently **relabel an answer code**:

- HIL F4 Q25 — `Ginabahinan namon sa komunidad` vs cleared `May kaugalingon kami`
  (*"we share it with the community"* vs *"we have our own"* — opposite meanings)
- WAR F4 Q9 — the NO option carries the YES text
  (`Oo (ginpresentar ngan ginpamatud-an an kard)`)
- BCL F1 Q115 `3-3 na bulan` (an impossible range) and F1 Q120 `31-60 na bulan` on a
  question asked in days
- BIS F1 Q33 `Matag onom ka bulan` → `Kada bulan`; F4 Q6 `Diborsyado` → `Legal nga bulag`
- ILO F1 Q63 `1-2 a bulan` → `(kurang a makabulan)`
- CEB F4 Q195 — cleared cell is a fragment of an unrelated question

## 4. Live CAPI defects surfaced by the audit

Independent of this pass, these should be ticketed — in each the **cleared side is
correct**, so they are also the highest-value adopts:

- **WAR F3 Q2** shows an out-of-pocket-cost prompt under `Q2_RELATIONSHIP`
- **CEB F3 Q147** shows raw English to Cebuano respondents
- **BIS F3 Q161** and **CEB F4 Q78** are truncated at `<Ask if answer in Q159 is`
- **CEB F1 Q140** ends on a dangling `Langay ang bayad sa`
- **BIS F1 Q121** carries a glued English routing note plus a dangling smart quote
- **F1 Q43 (BCL/FIL)** — the tool holds only an English tail fragment; the cleared
  Filipino is the correct full question

## 5. Fill placeholders need code, not text

`[facility_name_input]` / `[FACILITY_NAME_INPUT]` / `[FACILITY_NGARAN_INPUT]` appear in
the cleared text of F3 Q88 / Q143 / Q144 / Q162 / Q172. These must be mapped to CSPro fill
syntax (`~~field~~`), never pasted as literal text. That is a generator change.

## 6. Structural finding — why this keeps recurring

`apply_translations()` matches a translation to a question by its **full English label
text**. Any edit to an English question — a rewording, a renumber, even a comma —
silently orphans its translation and the tool falls back to English with **no error**.
That is the mechanism behind #1182 and #1213 and a large share of the gap above.

**The durable fix is to key translations on question number or item name + value code**,
exactly as this reference does, instead of on the English sentence.

## Method and honest limits

- Join is by question number, taken from the CAPI's own English labels.
- The questionnaire body is located as the run reaching the highest question number, so
  the cover table and F1's secondary-data annex (which reuse 1–6) do not hijack it.
- Options are matched on their **own English text**, never by position, and never across
  a differing digit — `Level 3 Hospital` and `Level 1 Hospital` are 94% similar and a
  similarity threshold alone paired them.
- Comparison ignores routing tokens, enumerator directives and editorial brackets on both
  sides, so their presence never by itself counts as divergence.
- **Limit:** mechanical signatures cannot catch semantic damage. Row-offset cases like the
  HIL Q25 opposite-meaning pair were found by per-locale review, not by regex. Treat
  §3 as a sample of that class, not an exhaustive list.
- `Waray_F4` is monolingual in the source, unlike its 31 siblings; its options are
  positional and flagged `option_confidence: "positional"`.

## Files

| file | purpose |
|---|---|
| `official_translations.json` | the cleared corpus, question number → per-locale text |
| `text/` | verbatim dumps of all 32 PDFs |
| `verbatim_report.json` | every comparison with its verdict |
| `safe_to_apply.json` | the 1,737 strings ready to fill |
| `classes/<LOCALE>.md` | divergence classes per locale, for translator review |
| `verify_verbatim.py`, `assess_recoverable.py`, `analyse_divergence.py` | rebuild it all |
