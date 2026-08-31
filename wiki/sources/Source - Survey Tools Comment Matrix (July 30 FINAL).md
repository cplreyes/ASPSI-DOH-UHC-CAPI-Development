---
type: source-summary
source: "Google Doc — \"Survey Tools_Comment Matrix (July 30, FINAL)\", ASPSI's responses to reviewer comments as of June 9; cited by DOH in the Deliverable-2 review; read via the Drive connector 2026-08-25"
url: "https://docs.google.com/document/d/1CDygV6Yr3NR_BpsJvr1S7fWfUgw_Rxhv/edit"
date_ingested: 2026-08-25
tags: [doh-review, comment-matrix, two-step-battery, f1-facility, f2-hcw, f3-patient, f4-household, ingest-batch-aug25]
---

# Source - Survey Tools Comment Matrix (July 30, FINAL)

**ASPSI's formal response document** to the reviewer (ADB-WHO / DOH) comments as of June 9, per instrument.
DOH cites this in [[Source - DOH Review of Deliverable 2 (2026-08-13)]] as the reason it did not press its
questionnaire comments further. Read 2026-08-25; it is link-shared, so no download was needed.

## F1 — the two-step battery, and a commitment that was kept

The reviewer asked ~18 times whether questions should follow the two-step pattern of Q10/Q11 and Q35/Q36 —
ask *"has X changed since 2019?"* first, then *"was it due to the UHC Act?"* — naming **Q19, Q21, Q23, Q25,
Q27, Q29, Q31, Q39–Q48**. ASPSI's answer is identical on every row, and ends with a commitment:

> *"Selected questions were revised… the others were retained but the response categories were expanded to
> ensure no overlap… This answer structure was initially retained from Year 1 tools for consistency. This was
> not flagged during SJREB during Year 1 and during the numerous review cycles in Year 2.
> **Based on the pre-testing result, these questions will be broken to a two-step question.**"*

> [!success] Commitment DELIVERED by the Aug-17 migration — verified
> `F1/generate_dcf.py` now builds **"Q9–Q37 with 23 two-step pairs, 8 follow-up"** — the Section C
> UHC-attribution battery. The thing ASPSI promised the reviewer in July is what shipped in August.

## ★ F1 and F2 were given deliberately opposite answers

Same reviewer comment, same two-step question, **different commitments**:

| | ASPSI's answer |
|---|---|
| **F1 Facility Head** | *"Based on the pre-testing result, these questions **will be broken** to a two-step question."* |
| **F2 HCW** | *"…there is no need to make this a two-step question… Based on the pre-testing results, the current answer options and structure **will be retained**."* |

This divergence is **intentional and on record**. Do not "harmonise" F2 to match F1's battery — the flat
structure with expanded response categories is the answer ASPSI gave DOH.

## F3 — three CAPI claims, and one open ask on Carl

ASPSI answered several F3 comments with *"The CAPI version has been corrected"*:

- **Q65 next-question instruction** — corrected
- **BUCAS wording** ("applicable only to respondents in LGUs with functional/operational BUCAS center") — corrected
- **Q54 / Q86 option definitions** — corrected

> [!important] Q54 and Q86 definitions ARE in the CAPI — verified 2026-08-25
> The reviewer's row reads *"These definitions will be added. = but not added."* ASPSI replied that the CAPI
> was corrected, and **that is accurate**:
> - **Q54** carries inline definitions from **#787 (R5)** — *"General practitioner (a doctor who is qualified
>   for medical practice)"*, *"Specialty Care Provider/Specialist (a doctor with more expertise…)"*.
> - **Q86** carries them from **#1052 (pretest 2026-08-04)** — *"minor surgery involves minimally invasive,
>   low-risk procedures often performed on an outpatient basis"* and *"claiming of medical clearance for
>   travel, fit to work, surgery, etc."* — the exact text the reviewer asked for.
>
> **So the "Missing option definitions" rows in [[Source - CAPI Comment Matrix (Aly consolidated, 2026-08-14)]]
> describe the PAPI questionnaire, not the CAPI.** The CAPI is done; any remaining gap is on the paper tool.

**Open ask on Carl.** On the F3 result-of-visit codes ASPSI added *"Completed at hospital"*, *"Completed at
Home"* and *"Withdraw Participation/Consent"*. The reviewer asked what a plain *"Completed"* now means, given
the two specific variants. ASPSI's reply ends:

> *"When completed, check if this came out in the CAPI version."*

That is a verification request against the CAPI's Result-of-Visit value set that does not appear to have been
closed out. Related: [[reference_cspro_breakoff_disposition]].

## Other positions ASPSI put on record

- **No expenditure questions in the patient survey** — deliberate: *"there is no direct utility for the data…
  We do not collect data that we do not intend to analyze."* Same for FIES asset items. The **WHO expenditure
  module went into the household form** instead, with relevant expenditure items in the patient tool.
- **Disposition codes** — the ADB-WHO household code list (NO HOUSEHOLD MEMBER AT HOME, DWELLING VACANT, etc.)
  was **rejected for both F2 and F3** as inappropriate for healthcare workers and for facility-administered
  patient interviews. Refusals are recorded on a separate form, not in this code set.
- **F1 financing** — Php 1,700 per-capita rate plus viability/costing and payment-status tracking at
  **Q61, Q61.1, Q62**; old Q96/Q97 (OOP for basic accommodation) survive as **Q141/Q142**.
- **F4** — no re-formatting: *"since the questionnaire is going to be CAPI-based, the re-organization is not
  necessary… the sequence of the questions was deliberate."*
