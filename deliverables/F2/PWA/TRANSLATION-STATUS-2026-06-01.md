# F2 PWA — Translation Wiring Status & ASPSI Gap-List

**Date:** 2026-06-01 · **Owner (build):** Carl (Data Programmer) · **Owner (content/QC):** ASPSI / Dr. Myra
**Sprint:** 008 Goal A (E2-F2-TRANS-001) · **PSA gate:** 2026-06-12

---

## TL;DR

The F2 PWA i18n is now **multi-language by architecture** (English + 7 Philippine languages), wired to consume ASPSI's translated strings with no further code changes per language. **Tagalog is 77% wired** from the delivered Apr30 doc; **Cebuano / Bisaya / Ilocano are 0%** because their per-instrument F2 Word docs are not yet retrievable from the shared Drive (the `[4/4]` subfolders enumerate empty via API — only the Tagalog file is indexed). Hiligaynon / Waray / Bicolano are not delivered at all.

This is a **content-availability** gap, not a build gap. The moment ASPSI's QC'd dialect strings are reachable, wiring each is a mechanical drop-in.

---

## What was built (shippable now)

- **Locale model widened** to `en + fil, ceb, bis, ilo, hil, war, bcl` (Bisaya tracked distinct from Cebuano — 7 layers, not 6). `LocalizedString` now carries English (always) + each dialect (optional, English fallback).
- **Runtime resolver** `localized(label, locale)` returns the dialect string when present, else English — so a partially-translated language degrades gracefully instead of showing blanks.
- **Survey-content translations** live in `spec/translations/{locale}.json`, keyed by the exact English source string. A composable generator pass (`scripts/lib/apply-translations.ts`) overlays them onto the English parse at `npm run generate`. The parser stays pure-English and deterministic (its tests no longer depend on translation files).
- **Language switcher** renders one button per *ready* locale (`LOCALE_META[...].ready` in `src/i18n/index.ts`). Today only English + Tagalog are flagged ready; a dialect appears the instant its translations + chrome bundle are wired and its flag is flipped. No more single `VITE_FIL_READY` env gate.
- **Verification:** `tsc` clean; **451 unit tests pass** (incl. 5 new overlay/dialect tests); `npm run generate` reports `translations loaded: fil:287`.

## Coverage (vs 372 distinct English survey strings)

| Locale | Wired | % | Status |
|---|---|---|---|
| Tagalog (fil) | 287 / 372 | **77%** | From `Filipino_v2.1.1_…Apr30.docx`. 0 orphan keys (clean match). |
| Cebuano (ceb) | 0 / 372 | 0% | Doc not API-retrievable. Chrome draft staged, not wired. |
| Bisaya (bis) | 0 / 372 | 0% | Doc not API-retrievable. Chrome draft staged, not wired. |
| Ilocano (ilo) | 0 / 372 | 0% | Doc not API-retrievable. |
| Hiligaynon / Waray / Bicolano | 0 / 372 | 0% | Not delivered by ASPSI. |

---

## ASPSI gap-list — Tagalog (85 strings the Apr30 doc left in English)

Per the **faithful-only** rule, the build never invents survey wording. The Tagalog doc itself left these **85 strings in English**. ASPSI to confirm each is either (a) intentionally English (then no action — it's correct as-is), or (b) owed a Tagalog string (then add it and we re-wire instantly).

**Likely intentional-English (no action needed) — 7:** Likert numerals `1 2 3 4 5`, and the sub-field labels `Year(s)`, `Month(s)`.

**Answer choices left English (confirm vs. translate) — ~55:**
- *Employment types (6):* Regular · Casual · Seasonal · Probationary · Project · Fixed-term
- *Roles (15):* Administrator · Physician/Doctor · Physician assistant · Nurse · Nursing assistant · Pharmacist/Dispenser · Midwife · Laboratory technician · Medical/ radiologic technologist · Health promotion officer · Nutrition action officer/ coordinator · Physical Therapist · Dentist · Dentist aide · Barangay Health Worker
- *Specialties (22):* No specialty · Anesthesia · Dermatology · Emergency Medicine · Family Medicine · General Surgery · Internal Medicine · Neurology · Nuclear Medicine · Obstetrics and Gynecology · Occupational Medicine · Ophthalmology · Orthopedics · Otorhinolaryngology (ENT) · Pathology · Pediatrics · Physical and Rehabilitation Medicine · Psychiatry · Public health · Radiology · Research · Others (specify)
- *Screening/services (8):* Pap smear · Mammogram · Lipid profile · Thyroid function test · Chest X-ray · Low-dose Chest CT scan · Dental services · All of the above
- *Referral forms (3):* E-referral · DOH standard referral form · City / LGU standard referral form
- *Prof. development (9):* Seminars, conferences, workshops · Supervisory trainings · More training related to my job post · Clinical audits · Surgical audits · Quality assurance meetings · Support for independent professional development: scholarships · Support for independent professional development: research grants · None
- *Other (2):* Neither Agree nor Disagree · Applies only to PhilHealth members and DOH-run hospitals *(this NBB option was not found anywhere in the doc)*

**Section titles / headers left English — ~13:** Healthcare Worker Profile · Universal Health Care (UHC) Awareness · Preventative health care · YAKAP/Konsulta Package · Awareness on No Balance Billing (NBB) and Zero Balance Billing (ZBB) · Awareness on Expanded Health Programs (BUCAS and GAMOT) · Referral patterns · Outbound & Inbound Referrals and Satisfaction · Knowledge, Attitude, And Practices (KAP) on Professional Setting, Charging, And Reimbursement · Task Sharing · Facility Support · Job Satisfaction · What type of employment do you have at this health facility?

> Full machine-readable list: `spec/translations/fil.json` holds the 287 *wired* strings; the 85 above are everything in `items.ts` not present there.

---

## R3 drift (separate from the above)

The delivered docs are **v2.1.1 / Apr30**; the instrument shipped **R3 changes after** that date. These strings are NOT in any delivered translation and must be added by ASPSI when they re-translate (do not invent — they're PSA-bound wording):

- **Q47 & Q110** — new **"None"** standalone option.
- **Q36** — switched to multi-select (stem unchanged; no new string).
- **Q39** — **removed** the "Not a physician/dentist" option (no new string; old translation simply unused).
- **Q52** "No significant impact" / **Q125** "Retire" — verify the delivered translation matches the now-exclusive option.

---

## Blockers / asks for ASPSI

1. **Cebuano / Bisaya / Ilocano F2 docs** — make the per-instrument Word files reachable (the language subfolders show empty over the Drive API; only the Tagalog file is indexed). Once reachable, each wires in minutes.
2. **Tagalog 85-string confirm** — mark each "intentionally English" or supply the Tagalog.
3. **Hiligaynon / Waray / Bicolano** — outstanding delivery (ASPSI-owned; per plan, ship the ready languages and gap the rest).
4. **R3 strings** — translate the post-Apr30 additions above.

## How a new/updated language gets wired (for the record)

1. Drop `spec/translations/{locale}.json` (English-string → translation).
2. (Chrome) add/refresh `src/i18n/locales/{locale}.ts`, register it in `src/i18n/index.ts` resources.
3. Flip `LOCALE_META.{locale}.ready = true`.
4. `npm run generate` → `tsc` → tests. Done. No per-language code.
