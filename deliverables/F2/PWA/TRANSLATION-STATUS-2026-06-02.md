# F2 PWA — Translation Wiring Status (v3.2 ingest)

**Date:** 2026-06-02 · **Owner (build):** Carl · **Owner (content/QC):** ASPSI / Aidan / Dr. Myra
**Supersedes:** `TRANSLATION-STATUS-2026-06-01.md` · **PSA gate:** 2026-06-12

---

## TL;DR

Aidan's **`DOH UHC Yr2_Translated Questionnaires`** drop (v3.2 / v3.1, **all four annexes**) was ingested for the F2 HCW survey PWA. The **5 F2 languages present in the drop** (Cebuano, Bisaya, Waray, Hiligaynon, Bicolano) were re-extracted from their v3.2 docs and **merged prefer-real** over the prior v2.1 maps. Coverage is up across the board and the R3-drift option strings are now translated.

**Tagalog (fil) and Ilocano (ilo) were NOT in this drop** — they stay at their prior v2.1 maps. Verified: lint clean, generated/translation files typecheck clean, 465/465 tests pass.

---

## Coverage (real translations only, vs 373 distinct English survey strings)

| Locale | Prior (v2.1) | Now (v3.2) | % | Source doc |
|---|---|---|---|---|
| Cebuano (ceb) | 278 | **299** | 80% | `Cebuano_v3.2_Annex_F2_…May26.docx` |
| Bisaya (bis) | 301 | **304** | 82% | `Bisaya_v3.2_Annex F2_…May28.doc` (legacy .doc) |
| Waray (war) | 309 | **316** | 85% | `Waray_v3.2_Annex F2_…May26.docx` |
| Hiligaynon (hil) | 269 | **288** | 77% | `Hiligaynon_v3.1_Annex F2_…June1.docx` |
| Bicolano (bcl) | 297 | **302** | 81% | `Bicolano_v3.2_Annex F2_…May25.docx` |
| Tagalog (fil) | 287 | 287 | 77% | *unchanged — not in this drop* |
| Ilocano (ilo) | 305 | 305 | 82% | *unchanged — not in this drop* |

**Methodology note — honest counts.** These numbers count **real translations only** (entries where the dialect string differs from English). Earlier snapshots counted English-repeat "no-op" entries as covered — e.g. Bicolano's old raw **355** included ~58 English repeats; genuine translated content is **302**. App rendering is identical either way (a no-op falls back to English at render time), so this is a reporting correction, not a regression. `npm run generate` now reports: `fil:287, ceb:299, bis:304, ilo:305, hil:288, war:316, bcl:302`.

---

## Merge logic (why coverage can't regress)

**Prefer-real merge:** for each key, the v3.2 translation wins **when it is a real translation**; where the v3.2 doc repeated English but the v2.1 map had a real translation, the v2.1 string is **kept**; a key is dropped only when *both* versions are English. This guarantees coverage is monotonic. **0 orphan keys** — every key matches `items.ts` exactly.

---

## Bisaya distinctness — CONFIRMED (was a false alarm)

The extraction agent flagged the v3.2 "Bisaya" doc as possibly Cebuano. A string-overlap check disproved it:

- new-Bisaya vs new-Cebuano: **11%** identical full-strings (they only share common Visayan words like *Oo/Wala*).
- new-Bisaya vs our shipped v2.1 Bisaya: **91%** identical → same language, consistent across versions.
- shipped-Bisaya vs new-Cebuano: **8%** → what we shipped is real Bisaya, not Cebuano.

Bisaya is a legitimate distinct locale and was safe to adopt.

---

## R3-drift strings — mostly closed by v3.2

Closed (now translated where the doc provided it):
- **"None"** standalone option → translated in **ceb** (*Wala*), **bis** (*Wala*), **war** (*waray*), **bcl** (*Wara*). ⚠️ **hil** left standalone "None" in English (its doc only translated "None of the above…").
- **"No significant impact"** → translated in all 5.
- **"Retire"** → translated in all 5.

Still open:
- **Q35 partial-date helper** — *"Year is required. Leave month or day blank if you don't recall them."* is **not present in ANY v3.x doc**, so it renders English in every locale's survey content. (ASPSI to supply wording, or we accept English by design.) Note the chrome Y/M/D/Optional sub-labels are a separate chrome concern below.
- **fil + ilo** — not in this drop; they remain at v2.1 coverage and still lack the same R3 strings. Await Aidan's fil/ilo v3.x docs.

---

## Intentionally English (by design, across all docs)

Likert numerals 1–5, the job-role list (Nurse, Midwife, Dentist…), medical specialties (Anesthesia, Dermatology…), screening/lab items (Pap smear, Mammogram, Chest X-ray…), `Year(s)`/`Month(s)` sub-labels, and proper-noun programs (BUCAS, GAMOT, YAKAP, NBB, ZBB). These appear English in the source docs and correctly fall back to English.

---

## App chrome — unchanged by this drop

Chrome strings (Enroll, Sync, Retry, error banners — the ~45 UI-furniture strings) are **not** in the questionnaire docs, so this ingest doesn't change them. **ceb / bis / fil** chrome bundles are translated; **ilo / hil / war / bcl** chrome remains English-fallback. A separate chrome-translation pass (or an ASPSI chrome string list) is still needed for those four.

---

## Other annexes in the drop — NOT wired (separate workstream)

The drop also contains **F1 (Facility Head), F3 (Patient), F4 (Household)** v3.2 translations for ceb/bis/war/bcl (plus hil F1), and per-language `_zip files` of full survey tools. **These were not wired** — F1/F3/F4 are **CSPro instruments** (`deliverables/CSPro/{F1,F3,F4}`), which have no i18n pipeline; the PWA only consumes F2. Adding multi-language to the CSPro instruments is a separate effort/decision (CSPro supports label translation files, but none exist yet).

---

## How a language gets updated (unchanged recipe)

1. Refresh `spec/translations/{locale}.json` (English-string → translation).
2. (Chrome) refresh `src/i18n/locales/{locale}.ts`.
3. `LOCALE_META.{locale}.ready` is already true for all 7.
4. `npm run generate` → `tsc -b` → tests. No per-language code.

**Source of this ingest:** `Downloads\DOH UHC Yr2_Translated Questionnaires-…\` (Batch 1_May28 + Batch 2_June2), shared into the personal Drive by `spprt.aspsi.doh.uhc.survey2@gmail.com`.
