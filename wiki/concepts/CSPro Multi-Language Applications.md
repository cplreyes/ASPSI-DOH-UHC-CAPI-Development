---
type: concept
tags: [cspro, capi, multi-language, localization, filipino, english]
source_count: 1
---

# CSPro Multi-Language Applications

CSPro supports building a single CAPI application that contains question text, dictionary labels, and runtime messages in multiple languages. The interviewer switches between them on the fly during the interview. This is essential for the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/UHC Survey Year 2|UHC Survey Year 2]] project, where the F1/F3/F4 CAPI apps must ship in English plus the **seven-language Philippine translation set** (Tagalog, Cebuano, Bisaya, Hiligaynon, Waray, Bicolano, Ilocano) — see [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CAPI Seven-Language Translation Build|CAPI Seven-Language Translation Build]].

## What can be localized

| Element | How |
|---|---|
| **Question text** | Each field's CAPI question text can have a translation per defined language. |
| **Dictionary labels** | Item, value set, and value labels can be entered in each language. When form text is linked to the dictionary item, the form text follows the active language. |
| **Runtime messages** | Messages displayed via `errmsg`, `maketext`, etc. can be defined in multiple languages via the message file (`.mgf`). |
| **String literals in logic** | Wrap any literal string in the `tr` function to make it translatable. |

## Supporting logic functions

| Function | Purpose |
|---|---|
| `getlanguage()` | Returns the currently active language code. |
| `setlanguage(code)` | Switches the active language at runtime (e.g., from a menu the interviewer triggers). |
| `OnChangeLanguage` | Global function callback fired whenever the language changes — useful for forcing a redraw or syncing related state. |
| `tr("...")` | Marks a string literal as translatable. |

The default starting language can also be set in the application's PFF via the `Language` parameter.

## Defining languages

`CAPI menu → Define CAPI Languages` opens a dialog listing the application's current languages. From there you can add, modify, or remove languages.

- Language **names** follow the same rules as item names: must be unique, no spaces.
- The Census Bureau recommends **ISO 639-1 two-letter codes** (e.g., `EN`, `FIL`, `TL`, `ES`, `FR`, `PT`). When ISO codes are used, the initial language on a mobile device will be auto-selected based on the device's OS language.
- Language **labels** can be any descriptive text.

The dictionary and the message file (`.mgf`) can also have multiple languages defined separately.

## Recommended translation workflow

The Census Bureau is unambiguous about ordering:

> "When you develop a multi-language application, it is probably easiest to **finalize and test all the question texts in one language**. Then, once this is done, language specialists can translate them into the other languages."

The reasons:

- Translating before the source language is locked invites version-control churn.
- The question text editor displays text for **two languages side-by-side**, so a translator can copy from the source pane to the target pane and visually align them.
- Bitmaps and formatting paste cleanly between language panes.

For multilingual fills, the fills themselves don't need to be translated — they reference dictionary items, which switch automatically when the language switches. The translator only changes the surrounding text.

## Project relevance

> [!info] As-built status (2026-06-12)
> The project's language set is the **seven-language** requirement of [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CAPI Seven-Language Translation Build|CAPI Seven-Language Translation Build]], not the earlier English + Filipino framing. Per-language QSF plumbing has been wired into the generators since 2026-06-04 (translation overlays folded into the one-step generator pipeline; the generators already emit multi-language QSFs — F1 ×6, F3/F4 ×5), so each delivered translation is a drop-in locale. Batch 1 (Bicolano, Bisaya, Cebuano, Waray) was delivered by ASPSI 2026-06-02 as v3.2 clean files but is not yet wired in; Batch 2 (Tagalog, Ilocano, Hiligaynon) is still pending ASPSI's translation check.

1. **Provision all seven translation languages plus English** in every CAPI application (F1, F3, F4). The generators do this — language definitions, dictionary columns, message file, and PFF are wired up even before a translation lands, so adding the strings later is a drop-in operation, not a rebuild.
2. **Lock English first**, then wire in ASPSI's translated batches as their QC completes. Avoid the temptation to translate as questions are written.
3. **Use ISO codes** so the app starts in the device locale's language automatically without enumerator intervention.
4. **Wrap all `errmsg` strings in the message file** with multi-language entries. Validation errors that appear only in English will confuse Filipino-speaking enumerators in pretests.
5. **Train interviewers on the language switch.** If a respondent prefers English mid-interview, the interviewer needs to know how to flip languages without restarting.
6. **Pretest in every wired language.** Translation issues only surface during real interviews — bake multi-language coverage into the bench test and the SJREB-tracked pretest as each batch is wired in.

## Sources

- (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro 8.0 Complete Users Guide]])
