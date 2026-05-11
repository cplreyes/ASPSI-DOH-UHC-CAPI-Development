# 110_F3_listing — F3 Patient Listing CAPI app

CAPI listing instrument used **before** F3 fieldwork to enumerate eligible patients per facility and auto-tag each listed patient as either:

- **for patient exit survey** (same-day at-facility F3 interview), or
- **for follow-up household survey** (F4 home visit), or
- **ineligible** (outside catchment / non-functional contact).

Source-of-truth instruments:
- `raw/Project-Deliverable-1_Apr20-submitted/Annex F3b_Patient Listing Protocol_UHC Year 2.pdf` (Apr 20 2026 Revised Inception Report submission).
- `raw/2026-05-06-survey-manual-bundle/2026-05-06_Survey-Manual-Working-File-Kidd.docx` §3.4.1.7 + (pending §3a authoring; see wiki source page).

## Position in the F-series pipeline

```
  STL allocates CASE_SEQ ranges per enumerator
        |
        v
  110_F3_listing  ---->  PATIENT_LISTING_DICT.csdb  (per facility-day session)
        |                       |
        |                       +--- LISTING_TAG=1 -> F3 exit survey same-day
        |                       +--- LISTING_TAG=2 -> F4 household visit later
        |                       +--- LISTING_TAG=3 -> ineligible
        |                       |
        v                       v
  Sync to CSWeb         F3 / F4 entry apps loadcase() on the dictionary
```

The listing app issues no F3/F4 case-IDs itself — it produces the **roster** that F3/F4 read at interview time. Case-ID assignment per the 12-digit decomposed scheme remains the responsibility of F3/F4's own preproc handlers.

## Generator chain

```
generate_dcf.py   ->  PatientListing.dcf
generate_ent.py   ->  PatientListing.ent
generate_fmf.py   ->  PatientListing.fmf  (Designer-owned post-publish)
generate_apc.py   ->  PatientListing.apc  (logic; emitted to .ent.apc by Designer)
```

Run via `python ../build_all.py --env=dev --only=F3LIST` once the entry is added to the `INSTRUMENTS` list in `build_all.py` (see commit 10).

## Auto-tag rule

The PROC that decides LISTING_TAG is intentionally isolated and marked
`PENDING_DESIGN_AUTO_TAG_RULE`. Default is **Candidate A — Distance-gated**
(see `F3-Listing-Skip-Logic-and-Validations.md` §3). Thresholds live as
named constants at the top of the .apc so Myra's edit pass can tune
without restructuring.

## Random-interval cadence engine

The listing app pulls a fresh random interval (within a configured min/max
window per facility) between each listing event so enumerators cannot
self-select cooperative-looking patients. The engine is fully internal —
no external RNG service, no clock sync. Pseudorandom seed derives from
the session timestamp + enumerator ID. Each generated interval is logged
to `REC_RANDOM_INTERVAL_LOG` for audit.

## Listing-session case-ID block

This app uses a **session-scoped** case-ID block distinct from the
12-digit F-series scheme. The listing session is identified by:

```
  RR  PP  MMM  FF  YYYYMMDD  SSS    (20 digits total)
  ^^  ^^  ^^^  ^^  ^^^^^^^^  ^^^
   2   2   3    2      8      3
```

Where SSS is the per-facility-day session sequence. Use
`shared/cspro_helpers.py::build_listing_id_block()` (added in commit 8).

## Line endings

See `.gitattributes` — Designer-owned binaries (.dcf, .fmf, .ent.apc, .ent.mgf, .ent.qsf) are pinned CRLF; generator-emitted sources (.py, .ent, .pff, .md) are pinned LF. Pattern parity with 107_F1 and 111_F3.

## Status

Scaffolded 2026-05-12 per commit 1 of 12. Subsequent commits land DCF
records, FMF, ENT, APC, sync plumbing, build_all wiring, and the
smoke-test pass.
