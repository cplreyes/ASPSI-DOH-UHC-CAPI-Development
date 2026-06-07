---
type: deliverable
kind: reconciliation-memo
audience: Kidd (ASPSI main RA) · ASPSI data team · Carl
prepared_by: Carl Patrick L. Reyes
date_drafted: 2026-06-03
status: draft-for-review
related_task: E7-DOC-005
resolves_open_question: CSPro-Section-Draft_2026-04-29.md open-question #1
links: [data-harmonization/codebook.md §15.G, §15.H]
tags: [survey-manual, case-id, questionnaire-number, psgc, harmonization, e7]
---

# Questionnaire-Number Scheme — Reconciliation Memo

Reconciles the **Survey Manual's** "Questionnaire Number" definition with the **actual F1/F3/F4 case-ID structure** in the CSPro dictionaries. This is the resolution path for the CSPro-section draft's open question #1 **and** for the codebook's **§15.H CRITICAL alignment risk** (silent cross-instrument join failure).

> **Why this matters now.** Every cross-instrument analysis join (F1↔F2↔F3↔F4) keys off the facility identifier. If the manual's numbering scheme and the dictionaries' `QUESTIONNAIRE_NO` schema disagree, enumerators write IDs the apps and the analysis can't reconcile — and the failure is **silent** (joins just drop rows). Locking this *before* fieldwork is far cheaper than discovering it in the unified store.

---

## 1. The two schemes, side by side

### 1.A Survey Manual (as written today)
*The Survey Questionnaire → Questionnaire Number*: a **9-digit** number = **6-digit Region/Province/Municipality code + 3-digit case number** (example `035401004` = `035401` geography for Magalang, Pampanga + `004` case). The identifier is **geography-embedded** — the geo code is *inside* the questionnaire number.

### 1.B CSPro dictionaries (as built — F1/F3/F4 `.dcf`)
Verified 2026-06-03 against `FacilityHeadSurvey.dcf`, `PatientSurvey.dcf`, `HouseholdSurvey.dcf`:

| Instrument | Case ID (level `ids`) | Geography captured as | Facility / parent link | Within-facility sequence |
|---|---|---|---|---|
| **F1** | `QUESTIONNAIRE_NO` — **6-digit numeric** | `REGION` / `PROVINCE_HUC` / `CITY_MUNICIPALITY` / `BARANGAY` (PSGC cascade) | — (F1 = **one row per facility**, so `QUESTIONNAIRE_NO` *is* the facility identifier) | — |
| **F3** | `QUESTIONNAIRE_NO` — **6-digit numeric** | facility PSGC + patient-home PSGC (`P_REGION`…`P_BARANGAY`) | **`F3_FACILITY_ID`** (pre-filled; a hard check enforces region match vs F1) | `PATIENT_LISTING_NO` (4-digit) |
| **F4** | `QUESTIONNAIRE_NO` — **6-digit numeric** | household PSGC (`REGION`…`BARANGAY`) | via the **listing form** (`HH_LISTING_NO`) | `HH_LISTING_NO` |

The dictionaries **do not embed geography in the case ID**. `QUESTIONNAIRE_NO` is a standalone 6-digit number; geography is captured authoritatively by the **PSGC cascade fields**; the parent facility is referenced by an explicit link field (`F3_FACILITY_ID`) or via the listing form.

---

## 2. The mismatches

1. **Length:** manual **9 digits** vs dictionary **6 digits**.
2. **Semantics:** manual **embeds geography** in the number; the dictionaries **separate** geography into the PSGC cascade and keep `QUESTIONNAIRE_NO` geography-free.
3. **What the "3-digit case number" maps to:** the manual's trailing 3-digit case counter has **no direct dictionary equivalent** — the closest concepts are F3's `PATIENT_LISTING_NO` (4-digit) and F4's `HH_LISTING_NO`, which are *within-facility* sequence numbers, not part of `QUESTIONNAIRE_NO`.
4. **Facility-identity coupling (the §15.H risk):** the codebook's harmonization plan **uses F1's `QUESTIONNAIRE_NO` as the canonical `facility_id`** and joins every other instrument to it. That only works if `QUESTIONNAIRE_NO` **equals the facility master-list id**. The manual's geo-embedded 9-digit scheme is **not** that — so following the manual literally would break every join.

---

## 3. Recommendation — adopt the dictionary scheme; update the manual to match

The dictionaries are already built, already drive the live CAPI logic, and already feed the harmonization design. The manual text is 2023-SPEED legacy. **Reconcile by updating the manual to the dictionary scheme**, not the reverse:

1. **`QUESTIONNAIRE_NO` = a 6-digit standalone case/facility identifier — not geography-embedded.** Drop the manual's "6-digit geo + 3-digit case = 9-digit" construction.
2. **Geography is captured in-form via the PSGC cascade** (Region → Province/HUC → City/Municipality → Barangay), which is the authoritative geography — *not* derived from the ID. (PSGC vintage is codebook **§15.F**.)
3. **For F1, `QUESTIONNAIRE_NO` = the facility's id from the facility master list** → it is the canonical `facility_id` for all cross-instrument joins (resolves §15.H). This requires the master list to use a 6-digit facility-code scheme (codebook **§15.G**).
4. **F3 and F4 reference their parent facility explicitly** — F3 via `F3_FACILITY_ID` (region-match hard-checked against F1), F4 via the listing form (`HH_LISTING_NO`) — *not* by reconstructing geography from the ID.
5. **Within-facility case numbering** (the manual's "case number" intent) is served by `PATIENT_LISTING_NO` (F3) / `HH_LISTING_NO` (F4) and by the STL's pre-assigned `QUESTIONNAIRE_NO` ranges (per the STL training deck), **not** by a digit slice of `QUESTIONNAIRE_NO`.

### Manual edits this implies (for Kidd to apply)
- Rewrite *The Survey Questionnaire → Questionnaire Number* to define `QUESTIONNAIRE_NO` as the 6-digit case/facility id, with a worked example that is **not** geo-embedded.
- Add one line: "Geographic location is recorded separately via the PSGC region/province/city/barangay selection in the app; it is not encoded in the Questionnaire Number."
- Cross-reference the STL's questionnaire-number range pre-assignment (collision prevention).

---

## 4. The decision this still needs from ASPSI  ⟨DECISION⟩

The reconciliation **direction** is clear (adopt the dictionary scheme); these specifics must be locked by **Carl + ASPSI** before fieldwork, and they are the same items the codebook flags:

- **§15.H — Does F1 `QUESTIONNAIRE_NO` equal the facility master-list `facility_id`?** Confirm yes, and that both use the same 6-digit scheme. *(If they differ, every F1↔F2/F3/F4 join fails silently — this is the critical one.)*
- **§15.G — Is there an authoritative facility master list, and what is its id scheme?** The 6-digit `QUESTIONNAIRE_NO`/`facility_id` must come from it.
- **6-digit composition:** is the 6-digit code a pure serial, or does it encode anything (e.g., a facility-type or region prefix)? Document whatever ASPSI confirms.
- **F2 linkage:** F2's `facility_id` (pre-filled from facility selection) must use the **same** scheme so F2↔F1 joins hold.

Until §15.H/§15.G are confirmed, **do not** print a final numbering example in the master manual — hold the §3 recommendation as the working scheme.

---

## 5. Issue + cross-reference map
| This memo resolves | Connects to |
|---|---|
| **#204** (E7-DOC-005) questionnaire-number reconciliation | CSPro-section draft open-Q #1 |
| Working scheme for the manual rewrite (#200) | codebook **§15.G** (facility master list), **§15.H** (QUESTIONNAIRE_NO ≡ facility_id), **§15.F** (PSGC vintage) |
| Analysis input for the ETL join keys | `data-harmonization/etl-spec.md` (join integrity QA gate) |

**Status:** reconciliation analysis + recommended scheme delivered. The scheme **lock** is the §15.H/§15.G ASPSI decision (above) — same sign-off already tracked in the codebook. Once locked, Kidd applies the §3 manual edits and the example can be finalized.
