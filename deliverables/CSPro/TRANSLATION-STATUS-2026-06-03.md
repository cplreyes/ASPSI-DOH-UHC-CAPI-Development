# CSPro F1/F3/F4 Translation — Status & Pipeline

**Date:** 2026-06-03 (rev. 2026-06-04: overlay folded into generators) · **Owner (build):** Carl · **Owner (content):** ASPSI · **PSA gate:** 2026-06-12

> **2026-06-04 update:** the multi-language overlay is now **built into each generator** — `generate_dcf.py` self-applies translations, so there is no separate overlay step and regenerating can no longer reset a `.dcf` to English. The old `apply_dcf_translations.py` is deprecated (refuses to run). See the Pipeline section. This was triggered by the 12-digit case-key rebuild, which had silently dropped F3/F4 translations under the old two-step flow.

## TL;DR

The **F1 / F3 / F4 CSPro dictionaries are now multi-language.** Each `.dcf` declares a `languages` array and carries a per-language entry in every `labels` array (question text, answer options, headings), so CSEntry can show the survey in English + the delivered dialects. Translations were extracted faithfully from the v3.2 questionnaire drop (2026-06-02), QC'd, and overlaid via a composable generator pass. **What remains is CSPro Designer + CSEntry verification on Windows (Phase 3).**

## Languages wired (source-limited)

| Instrument | Languages in `.dcf` |
|---|---|
| F1 Facility Head | EN + Cebuano, Bisaya, Hiligaynon, Waray, Bikol (6) |
| F3 Patient | EN + Cebuano, Bisaya, Waray, Bikol (5) |
| F4 Household | EN + Cebuano, Bisaya, Waray, Bikol (5) |

**Not wired — no translated source exists (ASPSI):** Tagalog (fil) and Ilocano (ilo) for F1/F3/F4; Hiligaynon for F3/F4. These stay English.

## Coverage (real translations of the instrument's English labels)

| Lang | F1 / 795 | F3 / 1,050 | F4 / 855 |
|---|---|---|---|
| Bicolano | 716 (90%) | 616 (59%) | 554 (65%) |
| Cebuano | 569 (72%) | 866 (82%) | 622 (73%) |
| Waray | 542 (68%) | 718 (68%) | 619 (72%) |
| Bisaya | 539 (68%) | 550 (52%) | 562 (66%) |
| Hiligaynon | 501 (63%) | — | — |

Untranslated labels fall back to English at render time (CSPro shows the English label when a dialect entry equals it). Gaps = operational/field-control labels (AAPOR codes, GPS, dates — absent from the questionnaires), option lists the docs left English (specialties, lab tests, transport modes), mismatched income brackets, and free-text/auto-computed fields.

## Pipeline (generator-first — never hand-edit the `.dcf`)

```
python <INST>/generate_dcf.py    # emits the FULLY multi-language dictionary
```

- One step. Each `generate_dcf.py` `main()` calls `cspro_helpers.apply_translations(dictionary, <INST>/translations)` before writing — declaring the `languages` array and expanding every `labels` array to one `{text, language}` entry per active locale (English fallback per missing key).
- **Locales are auto-discovered by file existence**: drop a `translations/<loc>.json` next to the generator and re-run — no code change. Declaration order lives in `cspro_helpers.TRANSLATION_LANGUAGES` (`EN, FIL, BCL, BIS, CEB, WAR, HIL`); `FIL`/`HIL` are skipped for F3/F4 because no map exists. Maps are keyed by the exact English label text.
- ✅ Regenerating no longer resets the `.dcf` to English — the failure mode the old two-step flow had. **`apply_dcf_translations.py` is deprecated** and refuses to run (running it on the new output would corrupt the `language` tags).

## QC performed (2026-06-03)

Deterministic pass over all 13 maps: 0 orphan keys, 0 empty values, English/no-op entries dropped, leaked routing notes (`<padayon sa Qxx>` etc.) stripped, markup checked. **Bisaya confirmed distinct from Cebuano** (5% / 16% / 17% identical across F1/F3/F4). Post-overlay validation: all `.dcf` parse as JSON; every label array has exactly one entry per declared language.

## Phase 3 — remaining (Carl, on Windows CSPro)

1. Open each `.dcf` in **CSPro Designer** — confirm it loads with the declared languages.
2. Confirm the **forms (`.fmf`) render translated labels** and **enable language selection** in the app; sync the `.qsf` `languages:` block if Designer flags a mismatch (question text is empty, so dict labels are the prompts).
3. Run in **CSEntry**, toggle each language, confirm prompts render and skip logic is intact.
4. Note: the English F1/F3/F4 base was itself still pending CSEntry sign-off — verify English alongside the dialects.

**QC caveat for content review:** the lower-coverage maps (F3 Bisaya 52%, F3/F4 Bicolano) leaned partly on fuzzy-matching during extraction — worth an eyeball pass on a sample of question↔translation alignment during CSEntry review.
