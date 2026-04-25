---
project: UHC Survey Year 2 — CAPI Development
artifact: Cross-instrument harmonization — open items requiring ASPSI / instrument-design decisions
audience: Juvy, Dr Claro, Dr Paunlagui (ASPSI Mgmt Committee + instrument-design owner)
date: 2026-04-25
author: Carl Patrick L. Reyes (data programmer)
related: deliverables/data-harmonization/codebook.md (v0.2)
---

# Open items for ASPSI — cross-instrument data harmonization

## Cover note

I drafted a cross-instrument codebook (v0.2 attached) so the four UHC Survey Year 2 instruments — F1 Facility Head, F2 Healthcare Worker (PWA), F3 Patient, F4 Household — produce data that can be cleanly merged on shared dimensions (geography, facility, sex, age, PhilHealth status, dates, etc.) at analysis time without per-analysis re-work.

Most of the alignment I can handle silently in the harmonization ETL. **Six items require ASPSI's input** before I can implement end-to-end. None block the current sprint's work; all block production data delivery later. Most are small instrument-design decisions; a couple are operational pickups (PSGC vintage, facility master list).

I've grouped them by urgency. Items 1–3 below are the ones to resolve in the next 1–2 weeks if possible — they affect instrument design that's still in flight (F1 sign-off, F3/F4 Designer pass, F2 v1.2.0). Items 4–6 are operational and can be answered any time before main fieldwork.

For each item I've named a **recommended option** so the discussion has a default to either approve or override.

---

## 1. F4 respondent sex allows "Other" — how do we harmonize?

**Context:** F4 (Household Survey) respondent question `Q3_SEX` includes `'Other'` as a third option. F1 (`Q4_SEX`), F2 (`Q3`), and F3 (`Q7_SEX`) all use only Male / Female. F4's roster items also use Male / Female only.

**Decision needed:** how should `'Other'` be encoded in the harmonized dataset?

**Options:**
1. **Add canonical code `3 = Other`** to the cross-instrument codebook. Pros: preserves the response. Cons: F1/F2/F3 will show no `3`s, which may look like missingness in cross-instrument tables.
2. **Treat as `.c` (don't know)** when harmonized. Pros: maintains binary sex comparison across instruments. Cons: loses respondent's stated identity.
3. **Carry as a separate `sex_other` boolean flag** alongside the binary `sex` column. Pros: preserves the distinction without breaking binary comparisons. Cons: extra column.

**Recommendation:** Option 3 (separate flag). Most analytically faithful — the binary sex column stays clean for cross-instrument tabulation, and the flag is available for analyses that need it.

---

## 2. F2 PWA — should we capture explicit consent as a data field?

**Context:** F1, F3, F4 all capture `CONSENT_GIVEN` in their FIELD_CONTROL block (numeric 1=Yes/2=No). If a respondent refuses, the row is created with `CONSENT_GIVEN=2` and the interview ends — providing an audit trail of explicit refusals. **F2 PWA does not capture consent as a data field.** A respondent who declines simply never reaches the form; no row is created, so refusals are indistinguishable from non-contacts in the data.

**Decision needed:** add explicit consent capture to F2 PWA?

**Options:**
1. **Add a `consent_given` checkbox + payload field to F2.** Captures explicit refusal; stores `consent_given=No` rows for audit purposes (no questionnaire data, just the refusal record). Small UI + Apps Script change.
2. **Leave F2 as is.** F2 refusals stay implicit — analysed only as a function of "HCWs in distribution list minus HCWs who submitted".

**Recommendation:** Option 1 (add the field). Three reasons: (a) ethics-board audit symmetry with F1/F3/F4, (b) it lets us distinguish "saw the form, refused" from "never opened the link" — different ops responses, (c) tiny change for F2 v1.2.0 (Round 3 batch already in flight).

If we go with Option 1, I'll spec the UI and ship it alongside the existing Round 3 enhancements (#16/#17/#18). No additional cost.

---

## 3. Add `LANGUAGE_USED` to FIELD_CONTROL across F1 / F3 / F4

**Context:** None of the four instruments currently records the language the survey was administered in. F2 already has the locale at runtime (English / Filipino), I just need to inject it into the submission payload — that's a Carl-owned change for v1.2.0. **F1 / F3 / F4 don't capture it at all.** Without this, post-hoc language-stratified analysis is impossible (we can't tell whether non-response or item-level missingness varies by language of administration).

**Decision needed:** add `LANGUAGE_USED` (numeric 1=English, 2=Filipino) to F1 / F3 / F4 FIELD_CONTROL?

**Options:**
1. **Add the field**, captured at submit-time from CSPro's `getlanguage()`. Tiny dcf addition; CSPro PROC code is one line.
2. **Skip it.** Live without language stratification in analysis.

**Recommendation:** Option 1. Negligible cost (one item per instrument), real analytical value (identify translation-dependent items, language-stratify response rates).

ASPSI may add other languages later (per ongoing translation pipeline) — recommend the value set extend gracefully (e.g. 1=en, 2=fil, 3+=future) rather than being binary.

---

## 4. Facility master list — when can ASPSI publish it?

**Context:** Every instrument needs a single canonical facility master list to drive `facility_id`, `facility_type`, `facility_name`, and PSGC geography. Currently:
- F1's `QUESTIONNAIRE_NO` is the de-facto facility-id key, but the scheme isn't formalised against an external master list.
- F2 PWA uses a placeholder facility list (production rollout needs the real one).
- F3 / F4 will need it for their cover blocks once they enter Build phase.

**Decision needed:** ASPSI to publish the canonical facility master list with these columns: `facility_id`, `facility_name`, `facility_type` (one of RHU/CHO/Hospital_L1/Hospital_L2/Hospital_L3), `region_code`, `province_code`, `city_mun_code`, `barangay_code`.

**Status:** I believe ASPSI has been working on this; just confirming when it's ready and where it lives (GitHub? Google Sheet? Bundled into the F1 dcf?). F2 PWA can swap to it within a day of receipt.

---

## 5. Pin the PSGC vintage for the engagement

**Context:** The PSA publishes PSGC updates quarterly (rebrandings, new barangays, mergers). If different instruments (or the same instrument across pretest and main fieldwork) use different PSGC vintages, geographic rollups silently disagree.

**Decision needed:** pick one PSGC release (e.g. PSA 2023Q4 or whichever is the most recent stable release at fieldwork start) and freeze it for the entire engagement.

**Recommendation:** PSA 2023Q4 unless ASPSI has a reason to prefer a more recent vintage. Pin it now; bundle the canonical PSGC value-set file with the facility master list (#4 above).

---

## 6. F1 `QUESTIONNAIRE_NO` ≡ facility master list `facility_id`?

**Context:** Cross-instrument joins all key off `facility_id`. F1's `QUESTIONNAIRE_NO` (in FIELD_CONTROL) is one row per facility. **For joins to work, F1's `QUESTIONNAIRE_NO` schema must equal the facility master list's `facility_id` schema** — same format, same values.

**Decision needed:** confirm F1's `QUESTIONNAIRE_NO` scheme is reconciled with the facility master list (#4 above), or define the mapping rule if they differ intentionally.

**Implications if they don't align:** every cross-instrument join silently fails (or partially fails, which is worse). E.g. F1 reports facility staffing; F2 reports HCW satisfaction; analyst tries to join and gets fewer matched rows than expected because the id schemes don't reconcile.

This is the smallest item but the highest blast-radius. Worth resolving when #4 is published.

---

## How to respond

Easiest path: reply on this thread (or via Slack / email) with your call on each item — even a one-line "OK to recommendation" is enough for the items where you're happy with the default. I'll incorporate into codebook v0.3 and update the instrument designs as needed.

If anything needs deeper discussion, happy to meet briefly. The goal is to lock these decisions before F1 enters production fieldwork so the harmonization ETL can run cleanly the first time.

— Carl
