# F2 PWA — Translation Wiring Status & ASPSI Gap-List

**Date:** 2026-06-01 · **Owner (build):** Carl (Data Programmer) · **Owner (content/QC):** ASPSI / Dr. Myra
**Sprint:** 008 Goal A (E2-F2-TRANS-001) · **PSA gate:** 2026-06-12

---

## TL;DR

**All 7 PSA-target languages are now wired** into the F2 HCW survey PWA, extracted faithfully from ASPSI's v2.1/v2.1.1 questionnaire docs (the `Translated Tools_May12` set). Survey-content coverage runs **74–95%** per language; every untranslated string falls back to English at render time, so nothing renders blank. The language switcher now offers English + all 7 dialects.

Source docs were converted (pandoc; Bisaya's legacy `.doc` via LibreOffice→pandoc) and extracted per-language into `spec/translations/{locale}.json`, keyed by exact English source string. **0 orphan keys** in any language — every extracted string matches `items.ts` exactly.

---

## Coverage (vs 373 distinct English survey strings)

| Locale | Wired | % | Source doc |
|---|---|---|---|
| Tagalog (fil) | 287 / 373 | 77% | `Filipino_v2.1.1_…Apr30.docx` |
| Cebuano (ceb) | 289 / 373 | 77% | `Cebuano_v2.1_…Apr28.docx` |
| Bisaya (bis) | 302 / 373 | 81% | `Bisaya_v2.1_…Apr29.docx` (legacy .doc) |
| Ilocano (ilo) | 305 / 373 | 82% | `Ilocano_v2.1_…Apr28.docx` |
| Hiligaynon (hil) | 275 / 373 | 74% | `Hiligaynon_v2.1_…May13.docx` (updated) |
| Waray (war) | 309 / 373 | 83% | `Waray_v2.1_…May7.docx` |
| Bikol/Bicolano (bcl) | 355 / 373 | 95% | `Bicolano_v2.1_…May7.docx` |

**App chrome (UI furniture — buttons, sync, errors):** Tagalog + Cebuano + Bisaya bundles are translated; **Ilocano / Hiligaynon / Waray / Bikol chrome is English-fallback** (these strings aren't in the ASPSI questionnaire docs — they need a separate chrome-translation pass for QC). Survey *content* for all 7 is real.

---

## What was built

- **Locale model**: English + 7 PH languages (Bisaya distinct from Cebuano — 7 layers, not 6). `LocalizedString` carries English (always) + each dialect (optional, English fallback).
- **Runtime resolver** `localized(label, locale)` returns the dialect string when present, else English.
- **Survey-content translations** in `spec/translations/{locale}.json`, keyed by exact English source string. Composable generator pass (`scripts/lib/apply-translations.ts`) overlays them at `npm run generate`; the parser stays pure-English/deterministic.
- **Language switcher** renders one button per `LOCALE_META[...].ready` locale — all 8 today.
- **Verification (all four CI steps, cold):** eslint clean · `tsc -b` clean · `vite build` clean · 456 unit tests pass. Generator reports `translations loaded: fil:287, ceb:289, bis:302, ilo:305, hil:275, war:309, bcl:355`.

---

## ASPSI gap-list — what's left per language

The build never invents survey wording (faithful-only). The unmatched strings per language fall into consistent buckets — **ASPSI to confirm each is intentionally-English, or supply the translation** (then it wires instantly with no code change):

**Common across most languages (the docs left these English):**
- **Role list** (Administrator, Nurse, Midwife, Dentist, …) — most docs print these English-only.
- **Specialty list** (Anesthesia, Dermatology, Pediatrics, …) — English-only.
- **Screening/lab items** (Pap smear, Mammogram, Lipid profile, Chest X-ray, …) — English-only.
- **Section/header titles** (Healthcare Worker Profile, Task Sharing, Job Satisfaction, …) — often English-only.
- **Likert numerals 1–5**, `Year(s)`/`Month(s)` sub-labels — intentionally English (no action).
- Proper-noun programs (BUCAS, GAMOT, YAKAP, NBB, ZBB) — kept English by design.

**Best coverage:** Bikol (95%, only 18 gaps). **Lowest:** Hiligaynon (74%) — its May13 doc left more section titles + option lists English.

> Per-language machine-readable gap = every key in `items.ts` not present in `spec/translations/{locale}.json`.

---

## R3 drift (applies to all languages)

The delivered docs are v2.1/v2.1.1 (Apr28–May13); the instrument shipped R3 changes after. These strings are in no delivered translation and must be added by ASPSI (do not invent — PSA-bound wording):
- **Q47 & Q110** — new **"None"** standalone option.
- **Q36** multi-select; **Q39** removed "Not a physician/dentist" option (no new string).
- **Q52** "No significant impact" / **Q125** "Retire" — verify the exclusive-option translation.
- **Q35** partial-date (#306): help string + Y/M/D/Optional sub-labels — currently English in all locales' chrome.

---

## App-chrome translation (separate follow-up)

`ilo.ts` / `hil.ts` / `war.ts` / `bcl.ts` chrome bundles are English-fallback (the ~45 UI strings — Enroll, Sync, Retry, error banners — aren't in the questionnaire docs). Tagalog/Cebuano/Bisaya chrome IS translated. ASPSI (or a follow-up pass) should supply chrome strings for the other 4; until then those 4 show English app furniture but fully-translated survey content.

---

## How a language gets updated (for the record)

1. Drop/refresh `spec/translations/{locale}.json` (English-string → translation).
2. (Chrome) refresh `src/i18n/locales/{locale}.ts`.
3. `LOCALE_META.{locale}.ready` is already true for all 7.
4. `npm run generate` → `tsc -b` → tests. No per-language code.
