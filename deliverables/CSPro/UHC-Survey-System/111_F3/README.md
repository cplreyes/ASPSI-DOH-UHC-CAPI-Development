# 111_F3 — Patient Survey (F3)

CAPI instrument for the F3 Patient Survey (in-patient + out-patient).
Source-of-truth: `raw/Project-Deliverable-1_Apr20-submitted/Annex F3_Patient Survey Questionnaire_UHC Year 2.pdf` (Apr 20 2026 Revised Inception Report submission, 178 numbered items across sections A–L).

## Pre-rebuild snapshot

The pre-2026-05-11 F3 generator + dcf + skip-logic spec are archived at:

```
deliverables/.archive/pre-rebuild-2026-05-11/CSPro/F3/
```

That archive is **code reference only** — item-label verbatims must be re-verified against the Apr 20 PDF on each ingest into this rebuild.

## Rebuild scope

- 12-digit decomposed case-ID block via `shared/cspro_helpers.py::build_id_block()`.
- FIELD_CONTROL via `build_field_control(survey_code="F3", date_label_entity="the Patient")` + extras (PATIENT_TYPE).
- Geographic ID via `build_geo_id("facility_and_patient")` — facility PSGC + patient-home PSGC (P_-prefixed).
- Facility + patient-home GPS capture records + verification-photo block (shared `_gps_fields()` / `_photo_block()`).
- Sections A–L following the verbatim Apr 20 PDF text.
- **`F3_FACILITY_ID` retired** — F3↔F1 linkage is derived from the shared first 9 digits of the case-ID (RR+PP+MMM+FF).

## Generator chain

```
generate_dcf.py   ->  PatientSurvey.dcf
generate_ent.py   ->  PatientSurvey.ent
generate_fmf.py   ->  PatientSurvey.fmf  (Designer-owned post-publish)
generate_apc.py   ->  PatientSurvey.apc  (logic; emitted to .ent.apc by Designer)
```

Run via `python ../build_all.py --env=dev --only=F3` once the F3 entry is added to the `INSTRUMENTS` list in `build_all.py`.

## Logic spec

`F3-Skip-Logic-and-Validations.md` is the source-of-truth for skip rules and validations; PROC code in `generate_apc.py` derives from it. Patch the spec first, regenerate the apc.

## Listing app dependency

F3 case-IDs (12-digit) are issued by the **sibling 110_F3_listing** CSPro listing app, which generates the patient sample per facility, syncs the case list to enumerator tablets, and F3 consumes the IDs at interview time. See the listing app's own README once it lands.

## Line endings

See `.gitattributes` — Designer-owned binaries (.dcf, .fmf, .ent.apc, .ent.mgf, .ent.qsf) are pinned CRLF; generator-emitted sources (.py, .ent, .pff, .md) are pinned LF. Pattern parity with 107_F1.
