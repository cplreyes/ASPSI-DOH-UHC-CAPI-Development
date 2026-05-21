# UHC Survey System v1.0 — From-Scratch CAPI Rebuild

This is the **v1.0 CAPI rebuild** for the DOH-ASPSI UHC Year 2 Survey, driven by
**Survey Manual v1.0 (post-Myra)** that landed 2026-05-12 (clean final to DOH +
working file edition).

## Scope

Three CSPro/CSEntry instruments only:

| Instrument | Respondent          | Mode                        |
|-----------|---------------------|-----------------------------|
| **F1**    | Facility Head       | CSPro CAPI on Android tablet |
| **F3**    | Patient             | CSPro CAPI on Android tablet |
| **F4**    | Community / Household | CSPro CAPI on Android tablet |

Out of scope (decided by Carl 2026-05-14):
- **F2 (Healthcare Worker)** — separate workstream, F2 PWA already in production.
- **Listing apps** — listing is **manual / paper-based** for both F3 (patients)
  and F4 (households). The instruments capture the interview only; respondent
  selection happens outside CAPI.

## Predecessor

This rebuild supersedes the 2026-05-12 build on `feature/uhc-survey-system-build`
(74 commits, kept as reference at `.claude/worktrees/uhc-survey-system-build/`).
That build included F3/F4 listing apps which v1.0 drops, and predates the
post-Myra Survey Manual v1.0.

## Key conventions

- **Case ID**: 12-digit `RR-PP-MMM-FF-CCC` per
  `wiki/concepts/Questionnaire Numbering Convention.md` (adopted 2026-05-05).
  Five separate ID items in every dictionary: `REGION_CODE` (2) +
  `PROVINCE_HUC_CODE` (2) + `CITY_MUNICIPALITY_CODE` (3) + `FACILITY_NO` (2) +
  `CASE_SEQ` (3). Active 001–699, replacement 700–899, refused 900–999.
- **PSGC anchor**: PSA 1Q 2026 publication. Geographic value sets reused from
  the existing CSV outputs at `deliverables/CSPro/F1/inputs/psgc_*.csv` (do
  not regenerate).
- **F3 → F1 linkage**: shared 9-digit prefix `REGION+PROVINCE+CITY_MUN+FACILITY`.
  No separate `F3_FACILITY_ID` data item (retired in v1.0).
- **F4 → F3 linkage**: dedicated `F4_PARENT_F3_CASE_SEQ` data item (length 3)
  inside the F4 household geo block.
- **F4 region whitelist**: F4 only runs in the 6 HH regions from
  `Sample Distribution 2026-05-12.xlsx` → **III, V, NIR, VII, X, BARMM**.
  Implemented as a config-driven value-set restriction on `REGION_CODE` in the
  F4 DCF (soft gate — easier to amend than an FMF hard gate).
- **NA codes**: NA = highest value at field width — 9 (len 1), 99 (len 2),
  999 (len 3). Not the DHS 7/97 convention.
- **Labels**: verbatim questionnaire text including original question numbers
  (e.g., `Q15. Has this facility...`). No paraphrasing.
- **Generator-first**: every `.dcf` / `.fmf` / `.apc` in this tree is emitted
  by a Python generator. Do NOT hand-edit any of the generated artifacts in
  CSPro Designer. Patch the generator and regenerate.

## Regenerate everything

```
python deliverables/CSPro/UHC-Survey-System-v1.0/build_all.py
```

This walks `F1/`, `F3/`, `F4/` and runs each instrument's `generate_dcf.py`
(and, in later phases, `generate_fmf.py` and APC writers) in order.

## Build phases

| Phase | Scope                                      | Status        |
|-------|--------------------------------------------|---------------|
| 0     | Scaffold + shared helpers                  | done          |
| 1     | F1 DCF                                     | done 2026-05-21 |
| 2     | F3 DCF                                     | done 2026-05-21 |
| 3     | F4 DCF (with region whitelist)             | done 2026-05-21 |
| 4     | FMF (forms) + APC (skip logic) per instrument | in progress  |
| 5     | Tablet smoke test + Designer review        | not started   |

Phase 1 output: `F1/FacilityHeadSurvey.dcf` — 5 ID items (12-digit
RR-PP-MMM-FF-CCC) + 16 records / 668 items. Shared helpers completed:
`value_sets.py`, `cspro_helpers.py`, `psgc.py`, `gps_photo.py` (joining the
pre-existing `case_id.py`).

Phase 2 output: `F3/PatientSurvey.dcf` — 5 ID items + 18 records / 802 items
(Q1-Q178, sections A-L). F3->F1 linkage is the 9-digit RR-PP-MMM-FF ID prefix;
the separate `F3_FACILITY_ID` item is retired. Question items match the
reference F3 build 1:1 (797 shared items, identical type/length).

Phase 3 output: `F4/HouseholdSurvey.dcf` — 5 ID items + 23 records / 621 items
(Q1-Q202, sections A-Q), with the repeating `C_HOUSEHOLD_ROSTER` (max 20).
REGION_CODE value set is restricted to the 6 F4 regions (III, V, NIR, VII, X,
BARMM). F4->F3 linkage is the `F4_PARENT_F3_CASE_SEQ` item. Question items
match the reference F4 build 1:1 (616 shared items, identical type/length).

Phase 4 (in progress) — FMF + APC per instrument:
- F1 FMF: `F1/generate_fmf.py` -> `FacilityHeadSurvey.generated.fmf`. 18-form
  skeleton (one form per record; 0 orphan items). The CSPro Designer pass
  splits the oversized sections (C/D/E/F/G) per `F1-Form-Layout-Plan.md` and
  applies visual polish.
- F1 APC: `F1/generate_apc.py` -> `FacilityHeadSurvey.generated.apc`. CAPI
  logic from `F1-Skip-Logic-and-Validations.md` — framework (case-control,
  consent terminator, PSGC cascade, GPS/photo capture), skip rules,
  why-difficult gates, numeric validations, and 'Other (specify)'
  enforcement. 188 PROC blocks; all skip targets resolve to DCF items.
  Verified against a paper walkthrough in the bench-test pass.
- F3/F4 FMF + F3/F4 APC: not yet started.

Each phase ends at a sign-off checkpoint before the next phase begins.

## Cross-references

- [[wiki/concepts/Questionnaire Numbering Convention]] — case-ID spec
- [[wiki/sources/Source - Survey Manual v1.0 (2026-05-12 Working File post-Myra)]]
- [[wiki/sources/Source - Sample Distribution 2026-05-12]] — F4 region scope
- [[wiki/concepts/PSGC Value Sets]] — PSA 1Q 2026 geographic codes
