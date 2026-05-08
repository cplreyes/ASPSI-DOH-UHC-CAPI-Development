---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/2026-05-06-survey-manual-bundle/2026-05-06_Appendix-D_Field-Codes]]"
date_ingested: 2026-05-07
tags: [field-codes, case-id, facility-master-list, psgc, replacement-protocol]
---

# Source — Survey Manual Appendix D (Case ID Format + Facility Master)

Circulated by [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Juvy Chavez-Rocamora|Kidd]] alongside the [[Source - Survey Manual Working File (2026-05-06 Kidd)|Working File]] on 2026-05-06. ~897 lines.

> [!note] Source page renamed 2026-05-08 (lint pass)
> Originally filed as "Source — Survey Manual Appendix D (Field Codes)" matching the upstream document title. Renamed to reflect actual content; the upstream `.docx` in `raw/` retains its original filename. Content is:
> - **Lines 1–149** — questionnaire numbering convention (12-digit case-ID format anchored on PSA 1Q 2026 PSGC, with CASE_SEQ partitioning notes)
> - **Lines 151–897** — facility master list with PSGC codes + facility counts per municipality, organized by region
>
> The actual field codes (AAPOR disposition, refusal reasons, replacement reasons, HCW role codes, facility ownership/type codes, PhilHealth/Konsulta/BUCAS/GAMOT/NBB/ZBB codes, consent codes) are **all absent** despite the upstream "Field Codes" title. The doc references "AAPOR disposition codes captured in FIELD_CONTROL" (L32) and *"the manual's existing replacement-protocol rule that 'refused or cancelled cases are assigned a different number range'"* (L26), but does not reproduce the code tables themselves.

## Document structure

- **L1–L149** — Case-ID format spec
- **L151–L897** — Facility master list (PSGC ↔ facility name ↔ count per LGU)

## What this document IS

### Case-ID 12-digit format (L1–L149)

Decomposes the case-ID as `RR-PP-MMM-FF-CCC`:

| Segment | Width | Source |
|---|---|---|
| `RR` Region | 2 | PSA 1Q 2026 PSGC |
| `PP` Province / HUC slot | 2 | PSA 1Q 2026 PSGC |
| `MMM` City / Municipality | 3 | PSA 1Q 2026 PSGC |
| `FF` Facility number | 2 | Sample-frame assignment |
| `CCC` Case sequence | 3 | 001–699 active / 700–899 replacement (per Annex D Replacement Protocol) / 900–999 refused (AAPOR-disposition tagged) |

Verbatim quote (L9–L15): *"The first seven digits (RR-PP-MMM) are the PSA 1Q 2026 PSGC slice"* — confirms PSGC anchoring is **self-served from PSA 1Q 2026** (matches memory `project_aspsi_psgc_value_sets.md`).

### Facility master list (L151–L897)

Cross-references PSGC codes (e.g., "03-54-11" for Magalang per L407–L408) with facility counts per LGU. **This is the operational facility frame** for the F1/F3/F4 dictionaries' facility-master-list lookup.

> [!note] Naming reconciliation with Carl's [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Questionnaire Numbering Convention|Questionnaire Numbering Convention]]
> Appendix D's case-ID format **matches Carl's adopted scheme exactly** — `RR-PP-MMM-FF-CCC` with the partition rule (active / replacement / refused). This is the protocol-side codification of the convention Carl filed via the Apr 30 brief to Kidd. Note however that the [[Source - Survey Manual Working File (2026-05-06 Kidd)|Working File body]] uses a slightly **different decomposition** (`-CC-CCC`, where CC encodes respondent type 11/22/33/44 and CCC is a per-type sequence). The two ASPSI artifacts (Working File body + Appendix D) are **internally inconsistent on this point** — flag back to Kidd.

## What this document is NOT

| Expected code table | Status in Appendix D |
|---|---|
| AAPOR disposition codes | **Absent.** Only references "AAPOR disposition codes captured in FIELD_CONTROL" (L32) without listing them. F1 DCF uses AAPOR 2023 11-code via Carl's generator. |
| Replacement reason codes | **Absent.** The 700–899 CASE_SEQ band marks structural replacement; reason codes live in [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex D Replacement Protocol|Source - Annex D Replacement Protocol]] (a different "Annex D" — name collision worth noting). |
| Refusal reason codes | **Absent.** The 900–999 CASE_SEQ band marks structural refusal; reason codes not enumerated. |
| HCW role codes (physician/nurse/midwife/etc.) | **Absent.** Carl's F2 PWA + F3 spec have these. |
| Facility ownership / type / DOH-retained codes | **Absent.** F1 DCF has these. |
| PhilHealth / Konsulta / BUCAS / GAMOT / NBB / ZBB | **Absent.** Carl's F1/F3 specs cover these. |
| Consent codes / follow-up codes | **Absent.** |

## Conflicts with current CAPI implementation

- **PSGC self-served from PSA 1Q 2026** ✅ — Appendix D's anchoring matches Carl's pipeline (memory `project_aspsi_psgc_value_sets.md`).
- **AAPOR 2023 11-code** — cannot verify match because Appendix D doesn't reproduce the codes. Action: confirm the F1 generator's AAPOR codes match whatever ASPSI considers the canonical set.
- **NA = highest-code-at-field-width convention** ✅ — Appendix D doesn't address item-level NA (only structural CASE_SEQ partition); no conflict with [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F-Series Value Set Conventions|F-Series Value Set Conventions]].
- **F-Series Value Set Conventions** ✅ — no contact points; Appendix D is structural, not item-level.

## Action items for Carl

1. **Confirm AAPOR canonical set** — Appendix D references AAPOR but doesn't list. Cross-check F1 generator vs whatever ASPSI considers canonical (likely AAPOR 2023 11-code).
2. **Reconcile case-ID format with Working File body** — Appendix D matches Carl's brief (`-FF-CCC` with partition). [[Source - Survey Manual Working File (2026-05-06 Kidd)|Working File body]] uses `-CC-CCC` (respondent type + sequence-per-type). One ASPSI artifact contradicts the other.
3. **Update F1 facility master list** — Appendix D's facility list (L151–L897) is the operational frame. Verify F1 generator's facility lookup matches (PSGC codes + counts per LGU).
4. **Watch for "Annex D" naming collision** — *this* "Appendix D — Field Codes" (case-ID + facility master) ≠ the existing wiki source [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex D Replacement Protocol|Source - Annex D Replacement Protocol]]. The latter is the replacement-procedure annex from the Inception Report. Two different docs both labeled "Annex/Appendix D" in different bundles.

## Cross-references

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Questionnaire Numbering Convention|Questionnaire Numbering Convention]] — Carl's adopted scheme; this appendix is the protocol-side codification.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/PSGC Value Sets|PSGC Value Sets]] — PSA 1Q 2026 anchoring.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex D Replacement Protocol|Source - Annex D Replacement Protocol]] — naming collision; different document (Inception Report annex on replacement procedure).
- [[Source - Survey Manual Working File (2026-05-06 Kidd)|Survey Manual Working File]] — Working File §5 questionnaire numbering uses a variant decomposition; reconcile.
- [[Source - Survey Manual Appendix B — Sample Distribution|Appendix B]] — verifies the case-ID widths against actual per-LGU/per-facility max sample sizes.
