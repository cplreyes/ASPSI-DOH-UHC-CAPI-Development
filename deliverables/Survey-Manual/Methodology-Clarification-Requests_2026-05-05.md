# Methodology Clarification Requests for the V2 Protocol

**From:** Carl Patrick L. Reyes, Data Programmer
**Date:** 2026-05-05
**To:** Dr. Ma. Esmeralda Silva, Dr. Paulyn Jean Claro, Dr. Daisy Demaisip
**Re:** CAPI implementation has surfaced six items in the V2 Protocol that warrant clarification or refinement.

None affect the survey's overall design intent; all affect how the protocol cascades into the Survey Manual, SOPs, and DOH-required documentation.

---

## Why this document exists

CAPI development for Year 2 has reached the stage where the Protocol's operational text must translate into concrete CSPro logic, value sets, eligibility checks, and field workflow. In that translation, the CAPI team identified items where the Protocol either (a) references a procedure that is not implementable in CSPro, (b) leaves an operational rule unspecified, or (c) creates an ambiguity that downstream documents (Manual, SOPs) cannot resolve without the methodology team's guidance.

We are raising these now, before the F3a/F3b/F4a/F4b CSPro applications are finalized for bench testing, so that any methodology refinement flows naturally into all the DOH-aligned documents in one cycle rather than as later patches.

---

## M1 — Patient intercept procedure  *(BLOCKER for F3a build)*

**Affected Protocol section:** §IX (Sampling Design — Patient survey)

**Current Protocol text:**

> *"Patient selection will follow a randomized interval procedure similar to the outpatient protocol. Enumerators will wait for the number of minutes randomly generated in CSPro before approaching the next eligible patient or representative. After each listing attempt, CSPro will generate another random waiting interval, and this process will continue until the required number of inpatient listings for the facility, including the estimated number of backup cases, has been completed."*

**Issue:** CSPro/CSEntry has no native countdown timer or scheduled-action primitive. There is no precedent for this pattern in CSPro documentation, the CSPro Users Forum, the CSPro Examples repository, or in any DHS/MICS implementation we could locate. Implementing it would require enumerator self-policing of a phone clock, which produces poor paradata and is enforcement-fragile.

This procedure also represents a departure from the Year 1 IDinsight methodology that the Protocol cites as its baseline elsewhere. The Year 1 approach (IDinsight, 2024, p. 43–44) was list-everyone-in-window, with sampling applied *after* the listing window closed: *"Once listing was completed, the first two-thirds of the listed frame were the main respondents. The rest of the listed names served as the list of backup respondents."*

**Proposed refinement:** Adopt the Year 1 list-everyone-in-window pattern for inpatient discharge and hospital OPD intercept. Specifically:

> *"At each selected hospital, enumerators station themselves at the discharge area (for inpatients) or OPD post-consultation area (for outpatients) for the designated listing window and list every eligible patient who passes through. After the listing window closes, the CSPro Patient Listing application designates the first two-thirds of the listed pool as main respondents and the last third as backup respondents, in the order patients were listed. Where the listed pool exceeds the per-facility target, a random start is drawn via CSPro's `randomin()` function and a systematic sampling interval is applied to the listed pool."*

**Rationale:**
- CSPro-native (no custom timing primitives needed)
- Methodologically validated in PH context (Year 1 ran nationwide)
- Matches the Protocol's own cited precedent
- Preserves longitudinal comparability with Year 1 data
- Auditable: every listing decision is paradata-logged

**Downstream document impact:**
- Survey Manual §Patient Listing Protocols (lines 1424–1543 of Apr 28 draft)
- F3a CAPI application sampling logic
- Enumerator training materials
- Field Operations SOP
- Sampling weight computation methodology

**Decision needed by:** Before F3a bench testing begins.

---

## M2 — Inpatient residency requirement  *(HIGH)*

**Affected Protocol sections:** §VIII (Study Population), §IX (Sampling Design)

**Issue:** The Apr 30 comparison output (CLAUDE Comparison: Protocol vs Survey Manual) flagged that the Protocol V2 does not state a residency requirement for inpatients, while the Respondent Selection document and Year 1 IDinsight methodology required *"resident of the same province as the health facility, lived there ≥6 months."*

Without resolution, F3a's eligibility screen for inpatient listing is ambiguous: should the enumerator screen on residency, or only on "preparing for discharge"?

**Question for the methodology team:** Is the residency requirement intentionally dropped in V2, or was the omission inadvertent?

**Downstream document impact:**
- Survey Manual §Patient Eligibility
- F3a CAPI eligibility screening logic
- Patient ICF (residency mention may need adjustment)

**Decision needed by:** Before F3a bench testing begins.

---

## M3 — Replacement rate exceedance handling  *(MEDIUM)*

**Affected Protocol section:** §IX (Sampling Design), §XII (Data Collection Protocol)

**Current Protocol text:**

> *"Replacement rates are limited to 5–10 percent, and sampling weights are adjusted accordingly."*

**Issue:** The Protocol states the cap but does not specify what happens if a facility or cluster approaches or exceeds it. F0d's daily replacement report will surface exceedance in real time, but the Field Supervisor needs a written escalation rule.

**Proposed refinement:** Add a paragraph specifying the escalation chain, e.g.:

> *"When a facility approaches the 8% replacement rate, the Field Supervisor escalates to the Survey Manager and Project Lead. When the 10% cap is exceeded, the facility's data is flagged for either downweighting or exclusion from the analysis, with the decision made jointly by the Project Lead, Survey Manager, and DOH-PMSMD focal person. All such decisions are documented in the project's amendment log."*

**Downstream document impact:**
- Survey Manual §Quality Control / Replacement
- F0d issue-ticket logic
- Sampling weight SOP
- Field Supervisor training

**Decision needed by:** Before fieldwork deployment.

---

## M4 — Hospital OPD "completed consultation" eligibility check  *(MEDIUM)*

**Affected Protocol section:** §VIII (Study Population — Patient Survey)

**Current Protocol text:**

> *"prospective outpatient respondents from hospitals are those who have completed their OPD consultations. Patients still waiting to be seen or mid-consultation are not eligible."*

**Issue:** How does the enumerator determine "completed"? There are three possible mechanisms: (a) self-reported by the patient, (b) confirmed by facility staff, (c) inferred from enumerator station location (post-OPD exit point). The CAPI screening logic and the field instructions diverge depending on which is chosen.

**Proposed refinement:** Specify which mechanism applies. Recommendation: self-reported by the patient via a screening question, captured as the first item in F3a (e.g., "Have you completed your consultation today?" yes/no/refused). This is auditable, doesn't require facility-staff interruption, and is enumerator-implementable.

**Downstream document impact:**
- Survey Manual §Outpatient Listing Protocols
- F3a CAPI screening logic
- Enumerator training

**Decision needed by:** Before F3a bench testing begins.

---

## M5 — HCW master list as the formal 60% denominator  *(LOW)*

**Affected Protocol sections:** §VIII (Study Population — HCW), §IX (HCW survey), §XII (Data Collection Protocol)

**Issue:** §IX references the master list of HCWs as a coordination artifact. §XII references the 60% response threshold and the ≤40% midpoint follow-up trigger. These are connected operationally — the master list is the denominator — but the Protocol does not explicitly link them.

**Proposed refinement:** Add a clarifying sentence to §IX (HCW survey):

> *"The master list of qualified HCWs obtained by the Field Supervisor at the courtesy call constitutes the formal denominator against which the 60% response threshold and ≤40% midpoint follow-up trigger described in §XII are computed. The list excludes BHWs per the eligibility criteria in §VIII."*

**Downstream document impact:**
- Survey Manual §HCW Survey
- F2 admin portal denominator logic
- F0b form design

**Decision needed by:** Before F2 admin portal handoff to Field Supervisor training.

---

## M6 — GPS and verification photo as paradata  *(LOW)*

**Affected Protocol section:** §XII (Data Collection Protocol)

**Issue:** The current F1, F3, and F4 CAPI design auto-captures GPS coordinates and one verification photo per case. This is established CAPI practice and is reflected in the Survey Manual. The Protocol does not explicitly require it; without acknowledgment, these become "implementation details" rather than methodological commitments.

**Proposed refinement:** Add one sentence to §XII (Data Collection Protocol):

> *"Each completed CAPI case is auto-stamped with GPS coordinates at start and end, and includes one verification photo of the facility (for facility visits) or at the enumerator's discretion documenting the visit (for household visits, with no image of the respondent's face). These together form a paradata anchor used for case authenticity audits and back-checks."*

**Downstream document impact:**
- Survey Manual §Quality Control
- ICFs (one-line mention of photo capture for transparency)

**Decision needed by:** Before SJREB resubmission, if the Protocol is updated.

---

## Document-alignment matrix

For DOH alignment, here is which documents need to be updated for each item if the methodology team decides to incorporate the proposed refinement.

| Item | Protocol | Survey Manual | Annexes | ICFs | Training | SOPs | Indicator Matrix |
|---|---|---|---|---|---|---|---|
| **M1** Patient intercept | §IX | §Patient Listing | F3a logic | — | Enumerator | Field Ops, Sampling | — |
| **M2** Inpatient residency | §VIII, §IX | §Patient Eligibility | F3a logic | Patient ICF | Enumerator | — | — |
| **M3** Replacement exceedance | §IX, §XII | §Replacement | F0d logic | — | Supervisor | Sampling, Replacement | — |
| **M4** OPD completion check | §VIII | §Outpatient Listing | F3a logic | — | Enumerator | — | — |
| **M5** HCW master denominator | §IX | §HCW Survey | F0b, F2 admin | — | Supervisor | — | — |
| **M6** GPS + photo | §XII | §Quality Control | All CAPI modules | All ICFs (1 line) | All | — | — |

---

## Recommended next step

Schedule a 30-minute methodology-team discussion (Myra, Doc Paulyn, Daisy, Carl) to walk through M1–M4 (the items affecting F3a build). M5 and M6 can be resolved asynchronously by email. Once decisions are recorded, the document cascade can proceed in a single coordinated pass.

The Data Programmer is available for any technical context the team needs during that discussion.
