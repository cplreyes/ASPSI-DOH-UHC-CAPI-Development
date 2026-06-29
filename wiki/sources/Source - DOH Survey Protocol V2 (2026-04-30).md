---
type: source-summary
source: "raw/protocol-and-clearance-2026/DOH Survey Protocol (V2, 30 April).docx — the formal UHC Survey Year 2 study protocol (V2, 30 April 2026), the base document for the SOPs and the SJREB + PSA submissions. Downloaded by Carl + ingested 2026-06-29."
date_ingested: 2026-06-29
tags: [protocol, scope, methodology, sampling, study-design, ethics, sjreb, psa, respondents]
---

# Source - DOH Survey Protocol V2 (2026-04-30)

The **formal study protocol** for the UHC Survey Year 2 (Version 2, 30 April 2026) — the document submitted as the base for the **SJREB ethics** and **PSA-SSRCS** reviews and the foundation for the survey SOPs/manuals. ~32k words; this page captures structure + the scope/sampling facts that matter for the CAPI build. Supersedes/extends the methodology in [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Revised Inception Report]].

## Structure
I. Introduction · II. Research Problem · III. Objectives · IV. Significance · V. Review of Related Literature · VI. Conceptual Framework · VII. **Study Design** · VIII. **Study Population** · IX. **Sampling Design** · X. Measurement Tools · XI. Validity & Reliability Testing · XII. **Data Collection Protocol** · XIII. **Ethical Considerations** · XIV. Data Processing · XV. Statistical Analysis · XVII. Annexes.

## Scope & coverage
- **120 study sites** nationwide = **107 UHC Integration Sites (37 newly designated) + 13 non-UHC IS** ([[Source - UHC Y2 Pre-Testing Plan]]).
- Builds on **Year 1**, which covered **1,135 facility heads, 11,582 healthcare workers, 7,824 patients, and 31,674 household members** (the reference baseline cited in the protocol).
- **Five respondent types / five instruments:** Facility Head (F1) · Healthcare Worker (F2) · Inpatient + Outpatient patients (F3) · Household head / main decision-maker (F4).
- Focus: effect of **progressive PhilHealth benefit implementation (2024→2025)** on financial risk protection, service delivery, and beneficiary experience.

## Sampling design (combination of stratified + cluster)
- **Facility Head:** stratified random by facility type — **1,521 facilities** (914 RHUs/health centers + 607 hospitals).
- **Healthcare Worker:** one-stage stratified design.
- **Patient (F3):** **two-stage stratified cluster** — target **30 inpatients** + **45 outpatients per sampling domain** (95% confidence, 5% margin); inpatient allocation split government/public vs other hospitals.
- **Household (F4):** **32 household survey sites** (16 UHC + 16 non-UHC IS); proposed **1,336 households per group**.
- **Sampling weights** applied to produce representative estimates.
- Patient recruitment uses the **Patient Listing** flow at the facility ([[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3b Patient Listing Protocol]]) — those who complete OPD/consult and consent are listed as prospective respondents.

## Data collection & ethics (relevant to CAPI)
- **CAPI conversion:** final instruments converted to CSPro tablet forms; the protocol references **pre-testing + bench-testing of the CSPro application + pilot testing** as validation steps (§XII).
- **Field re-contact rule:** at least **three contact attempts** before a non-response disposition (field supervisor) — ties to the disposition/result-of-visit logic in the CAPI ([[reference_cspro_breakoff_disposition]]).
- **Informed consent** (Annex H) read verbatim; respondent signs; may decline/withdraw; a present adult HH member may sign where the respondent cannot.
- **Confidentiality:** names kept out of reports; no sharing of personal data — the data-security posture documented in CAPI Manual §XVI.

## Companion clearance docs (same raw folder)
- `POSSIBLE no review for the protocol.docx` — internal analysis concluding **exemption is not available**; **expedited review** is the realistic SJREB track (→ classified **SJREB-2026-31, Expedited**; see [[Source - ASPSI Team Meeting Notes Digest (Apr 27 - Jun 9 2026)]]).
- `Protocol vs Survey manual.docx` — a protocol↔survey-manual **consistency check** (Myra requested PSA-required alignment between the two).

## Cross-references
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/UHC Survey Year 2]] · [[Timetable of Activities]] · [[Source - UHC Y2 Pre-Testing Plan]]
- [[Source - Project Movement and Revised Timeline (Apr-Jun 2026)]] — this protocol is the version under SJREB/PSA review (must stay on the same version, per the June cascade).
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/SJREB]] · [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/PSA]] · [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex B List of UHC Integration Sites]].
