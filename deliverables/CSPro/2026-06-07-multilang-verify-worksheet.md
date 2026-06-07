---
type: deliverable
kind: verification-worksheet
audience: Carl (Data Programmer) — CSPro Designer + CSEntry 8.0 on Windows
date: 2026-06-07
sprint: 009
related_tasks: [E3-F1-001, E3-F3-001, E3-F4-001]
gate: PSA clearance 2026-06-12
source_of_truth: deliverables/CSPro/TRANSLATION-STATUS-2026-06-03.md
tags: [cspro, csentry, multi-language, verify, phase-3, s009]
---

# S009 CSPro Multi-Language Verify Worksheet — F1 / F3 / F4 (Phase 3)

Operationalizes the **multi-language** half of the Phase-3 verify (TRANSLATION-STATUS §"Phase 3"
+ Compile/Desk-Test Runbook §2–§3). This is the **language layer on top** of the base English
compile — it does not replace the English desk-test (#193/#194/#195), it adds the per-language pass.

## Pre-checks — AI-side, GREEN as of 2026-06-07 (don't re-do)

| Check | F1 | F3 | F4 |
|---|---|---|---|
| `preflight_validate.py` (PROC / setvalueset / arity / refs) | ✅ ALL CLEAN | ✅ ALL CLEAN | ✅ ALL CLEAN |
| Language parity (every label array has all declared langs) | ✅ 2463/2463 | ✅ 2831/2831 | ✅ 2232/2232 |
| Declared languages | EN·BCL·BIS·CEB·WAR·**HIL** (6) | EN·BCL·BIS·CEB·WAR (5) | EN·BCL·BIS·CEB·WAR (5) |

> **fil (Tagalog) + ilo (Ilocano)** — and **hil for F3/F4** — are **not declared** (no ASPSI source).
> Those render English-fallback and are the **E0-PSA-002 go/no-go gap**, not a defect to fix here.

## GUI setup prerequisites (from the Runbook — do once per instrument before language testing)

- [ ] **F1 only — Id-block re-sync (Runbook §2 F1 Step 0):** open `FacilityHeadSurvey.ent`; on the
      `Rename Item` dialog leave **"Delete QUESTIONNAIRE_NO from the form"** selected, **"Delete all
      items not found"** unchecked → OK → OK. Then open `FORM000` and confirm the 5 id items
      (`REGION_CODE·PROVINCE_HUC_CODE·CITY_MUNICIPALITY_CODE·FACILITY_NO·CASE_SEQ`) are placed; drag
      from the dict tree if absent. Save forms. **Do not hand-edit the `.fmf`.**
- [ ] **All three — insert the 4 PSGC external dicts (Runbook §2 Step 0b):** Designer ▸ Add Files ▸
      Dictionary → `psgc_region/province/city/barangay.dcf` from `deliverables/CSPro/shared/`, and
      deploy the matching `.dat` files. (preflight is blind to these — a miss shows as
      `'PSGC_REGION_DICT' is not defined` only at compile.)

## Per-instrument language verify

For **each** instrument, after a clean English compile, run the language matrix. Mark P/F and drop a
screenshot per language into the gate issue. **If a logic/label defect appears → Runbook §1 IRON RULE
(fix the generator + regenerate + re-preflight), never hand-edit the artifact.**

### Common checks (run per language)
1. **Designer load** — `.dcf` opens; the language appears in the language list (Designer ▸ Languages).
2. **Forms render** — `.fmf` shows the translated label for question text + answer options + section
   headings (English-fallback where the dialect entry equals English — expected, not a failure).
3. **Language selection enabled** — the app exposes the language switch (sync `.qsf` `languages:` block
   if Designer flags a mismatch; question text is empty, so dict labels are the prompts).
4. **CSEntry toggle** — switch to the language; prompts re-render; **skip logic + validations still fire
   identically** to English (toggle does not alter flow). `LANGUAGE_USED` records the active language.

### F1 — Facility Head  (closes **E3-F1-001**)
| Lang | Designer loads | Forms render | Switch works | Skip logic intact | Notes |
|------|----------------|--------------|--------------|-------------------|-------|
| EN (base) | ☐ | ☐ | ☐ | ☐ | English sign-off (was still pending CSEntry) |
| Cebuano (CEB) | ☐ | ☐ | ☐ | ☐ | 72% coverage |
| Bisaya (BIS) | ☐ | ☐ | ☐ | ☐ | 68% — distinct from CEB ✔ |
| Hiligaynon (HIL) | ☐ | ☐ | ☐ | ☐ | 63% |
| Waray (WAR) | ☐ | ☐ | ☐ | ☐ | 68% |
| Bicolano (BCL) | ☐ | ☐ | ☐ | ☐ | 90% |

### F3 — Patient  (closes **E3-F3-001**)
| Lang | Designer loads | Forms render | Switch works | Skip logic intact | Notes |
|------|----------------|--------------|--------------|-------------------|-------|
| EN (base) | ☐ | ☐ | ☐ | ☐ | English sign-off |
| Cebuano (CEB) | ☐ | ☐ | ☐ | ☐ | 82% |
| Bisaya (BIS) | ☐ | ☐ | ☐ | ☐ | 52% — **eyeball a Q↔translation sample** (fuzzy-match caveat) |
| Waray (WAR) | ☐ | ☐ | ☐ | ☐ | 68% |
| Bicolano (BCL) | ☐ | ☐ | ☐ | ☐ | 59% — eyeball sample |

### F4 — Household  (closes **E3-F4-001**)
| Lang | Designer loads | Forms render | Switch works | Skip logic intact | Notes |
|------|----------------|--------------|--------------|-------------------|-------|
| EN (base) | ☐ | ☐ | ☐ | ☐ | English sign-off; verify roster + Section N |
| Cebuano (CEB) | ☐ | ☐ | ☐ | ☐ | 73% |
| Bisaya (BIS) | ☐ | ☐ | ☐ | ☐ | 66% |
| Waray (WAR) | ☐ | ☐ | ☐ | ☐ | 72% |
| Bicolano (BCL) | ☐ | ☐ | ☐ | ☐ | 65% — eyeball sample |

## Done = ready to bundle (feeds E0-PSA-001)

- [ ] All three instruments compile clean in Designer (English) and load all declared languages.
- [ ] Each declared language: forms render + switch works + skip logic intact (matrix above all P).
- [ ] English base signed off in CSEntry.
- [ ] Any defect routed through the generator fix-loop (§1) and re-preflighted to ALL CLEAN.
- [ ] Outcome (incl. the fil/ilo/hil-F3F4 English-fallback gap) captured for the **E0-PSA-001** bundle
      and the **E0-PSA-002** ASPSI go/no-go.

> **Paste any Designer compile error verbatim** and I'll turn the generator fix in the §1 loop
> (one-line source edit + regenerate + preflight), then you re-open in Designer.
