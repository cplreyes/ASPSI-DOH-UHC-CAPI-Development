---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Project-Deliverable-1_Apr20-submitted/Annex F3b_Patient Listing Protocol_UHC Year 2.pdf]]"
date_ingested: 2026-04-20
tags: [protocol, patient-listing, sampling, f3, f3b, ingest-batch-apr20]
---

# Source — Annex F3b: Patient Listing Protocol

Field-operations protocol for listing and selecting patient respondents for the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3 Patient Survey Questionnaire|F3 Patient Survey]] at each sampled health facility.

**Version:** Apr 20 2026 Revised Inception Report submission (−105 KB vs Apr 08 — significant slim from simple listing *form* to streamlined *protocol* document). Renamed from "Patient Listing Form" to "Patient Listing Protocol".

## Scope

- **Target sample per facility**: 1–30 patients, sized to IS and facility patient load. **Oversample by 50%** for non-response backup.
- **Service-type split**: separate protocols for **outpatients** (PCF and hospital OPD) and **inpatients** (hospitals only).
- **Listing instrument**: primary capture via **CSPro on tablet**; physical log sheet as backup.

## Protocol highlights

### Outpatient (PCFs + hospital OPDs)

- Station enumerators at the patient-flow bottleneck (registration for PCFs, OPD registration for hospitals).
- **CSPro-driven randomization**: generates a random interval 1–10 minutes; enumerator waits *n* minutes, approaches the next patient, lists them, and repeats until facility target + backups are met.
- Multiple listing stations: divide target evenly; >3 stations → coordinate with field supervisor.
- Alternative-day listing if facility head denies same-day listing.

### Inpatient (hospitals only)

- Station enumerators at the **discharge / billing station** (patient or representative passes through before leaving).
- **Safety protocol**: enumerators NOT allowed inside hospital wards (infection control + privacy).
- Same random-interval mechanism as outpatient.
- May list the patient's relative/representative when patient is unavailable — patient remains the primary survey target.

### Refusals & exclusions (Section 3)

- Refusal is documented in CSPro and the enumerator waits for the next random interval.
- Exclusions cover inpatient-specific cases (deceased, ICU/critical care, pediatric without guardian).

## Changes from Apr 08 baseline

- **Name change**: "Patient Listing Form" → "Patient Listing Protocol" (annex-label designation "F3b" adopted).
- **Scope broadened from tabular form to documented field-ops protocol** covering location, timing, randomization, multi-station handling, alternative-day fallback, inpatient safety rules, refusals, and exclusions.
- **CSPro integration formalized**: CSPro on tablet is the primary listing capture (not just a paper log). Random-interval generation is a CSPro feature requirement.
- **Sampling reinforcement** ([[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex G DOH Recommendations Matrix|Annex G]] #15): supports patient-exit sampling to include **inpatient + outpatient** (incl. private clinics within hospital premises).

## CAPI Development Notes

- **New requirement**: CSPro listing app must include a **random-interval generator** (1–10 minute range) to drive the listing cadence.
- Patient listing becomes a **separate CSPro screen/mode** feeding into F3 interview selection (not just a paper-log side artifact).
- Handshake with F3: listing produces a patient ID + contact info that F3 interview attaches to.
- Links to the patient replacement protocol (Annex D of the Inception Report).

## Documented divergence — May 6 Survey Manual Working File

> [!note] Listing-methodology divergence (documented, NOT adopted)
> The Survey Manual Working File at `raw/2026-05-06-survey-manual-bundle/2026-05-06_Survey-Manual-Working-File-Kidd.docx` (Kidd's working draft, still under Myra's edit pass) describes a **PhilHealth-registry-based** patient sampling methodology that diverges from Annex F3b.
>
> **Resolution (2026-05-12, Carl):** Build the F3 CAPI quartet and the 110_F3_listing app to Annex F3b — OPD/IPD facility-record-driven sampling, with provenance items capturing facility-internal patient identifiers (OPD case number, ward/bed, admission date for IPD). The PhilHealth-registry approach is documented here for audit trail but is **not adopted** in the CAPI build.
>
> Rationale: Annex F3b is the protocol-of-record (Apr 20 DOH-submitted Revised Inception Report). The May 6 Working File is upstream-review-in-progress (Myra has an active edit pass), so we defer any reconciliation per `feedback_defer_clarifications_during_upstream_review.md`. No CAPI-side clarification email to Kidd/Myra at this time; revisit if Myra's pass changes the protocol-of-record.

## Cross-references

- Paired interview: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3 Patient Survey Questionnaire|F3 Patient Survey]]
- Replacement rules: Annex D — Draft Replacement Protocol (pending ingest)
- Change-rationale map: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex G DOH Recommendations Matrix|Annex G DOH Recommendations Matrix]]
- Programme concept: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/UHC Survey Year 2|UHC Survey Year 2]]

## Sources

- Part of [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Revised Inception Report|Revised Inception Report]] Apr 20 submission to [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/DOH-PMSMD|DOH-PMSMD]]
- Developed by [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/ASPSI|ASPSI]] consultant team
- Raw file: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Project-Deliverable-1_Apr20-submitted/Annex F3b_Patient Listing Protocol_UHC Year 2.pdf|F3b Apr 20 PDF]]
- Apr 08 baseline preserved at: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Project-Deliverable-1/Patient Listing Form_Apr 08.pdf|F3b Apr 08 baseline]]
