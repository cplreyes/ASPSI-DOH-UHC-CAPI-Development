# F2 PWA — Translation Wiring Status (June-5 paper ingest)

**Date:** 2026-08-03 · **Owner (build):** Carl · **Owner (content/QC):** ASPSI / Aidan / Dr. Myra
**Supersedes:** `TRANSLATION-STATUS-2026-06-02.md`

---

## TL;DR

The **June-5 DOH-cleared translated questionnaires** (Deliverable No. 2, `[FOR DOH ONLY]`, all 8 languages) were ingested for F2 via the **anchor-based extractor** built for the CSPro instruments the same day (`deliverables/CSPro/translations-paper-extract/anchor_extract.py`, F2 variant in the job workspace). Anchors = the PWA's own 377 distinct English survey strings from `src/generated/items.ts`, so June wording cannot leak into the spec. Merge was **add-only** (no existing translation overwritten — the v3.2 docx ingest is table-aligned and higher-trust than PDF span extraction), topped up by a **cross-borrow** from the CSPro F1/F3/F4 locale maps (same English keys, e.g. *Not applicable*, *Emergency Medicine*), with every borrowed pair **individually audited** — 23 junk pairs rejected, 4 corrected.

Verified: `npm run generate` clean · `tsc -b --force` clean · **518/518 tests pass** · production bundle built and content-checked (new strings present, junk absent, proxy origin correct).

## Coverage (real translations, vs 377 distinct English survey strings)

| Locale | v3.2 (Jun-2) | Now | Notes |
|---|---|---|---|
| Filipino (fil) | 287 | **307** | first top-up since v2.1 — June-5 Tagalog paper is its first post-check source |
| Cebuano (ceb) | 299 | **312** | |
| Bisaya (bis) | 304 | **312** | |
| Ilocano (ilo) | 305 | **313** | first top-up since v2.1 |
| Hiligaynon (hil) | 288 | **298** | |
| Waray (war) | 316 | **324** | |
| Bicolano (bcl) | 302 | **310** | |

## Why the remaining ~55–80 gaps per locale are structural, not backlog

Gap decomposition (fil is representative): of 85 missing strings, **47 are clinical/proper terms the DOH paper itself leaves in English** (*Chest X-ray*, *Mammogram*, *Lipid profile*, *Emergency Medicine* panels) — the extraction span after those anchors is literally empty on paper; ~20 are numerals and short option tokens below anchor resolution; the rest are PWA-side meta strings with no paper equivalent. **The June-5 papers are exhausted** — closing more requires ASPSI translator content, not extraction.

## QA notes (what was caught and rejected)

- `Chest X-ray → "Creatinine HbA1c Abdominal ultrasound"` — table bleed, present in **all 7** CSPro-borrow candidates; rejected everywhere.
- hil `City / LGU standard referral form → "Wala sang standard referral form"` — the *next* option's translation ("No standard referral form"); rejected.
- war `LGU/Barangay → "Balaud"` — *Legislation*'s translation; rejected.
- bcl `E-referral → "system)"`, ilo `Barangay Health Worker → "(Trabahador ti Salun-at ti"` — fragments; rejected.
- Trims applied: fil *Seminars…* trailing bleed, bcl `Batas /` → `Batas`, bis `Dili angay (Not applicable)` → `Dili angay`, ilo stray paren.

Machine-extracted additions **await native-speaker skim** (same caveat as the CSPro import). Field reports of odd translations are one-line fixes in `spec/translations/{loc}.json` + `npm run generate`.

## Deploy

**DEPLOYED 2026-08-03 ~11:38 UTC and live-verified** (bundle `index-DhN3LUIe.js` fetched from prod, all sample strings present, junk absent; backup at `/opt/app/f2-www.bak-20260803`). Gotcha for next deploy: Windows scp sets uploaded DIRECTORY modes to 700 — nginx then serves the SPA fallback for every asset; `chmod 755` the dirs after upload. Ship = upload `app/dist/*` → `root@csweb.asiansocial.org:/opt/app/f2-www/` (backup live dir first: `cp -a /opt/app/f2-www /opt/app/f2-www.bak-20260803`). Build requires `VITE_F2_PROXY_URL=https://uhc-hcw.asiansocial.org` inline (the value baked in the live bundle; `.env.local` carries only backend URL + HMAC).
