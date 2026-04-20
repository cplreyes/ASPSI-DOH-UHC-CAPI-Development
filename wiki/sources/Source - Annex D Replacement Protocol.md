---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Project-Deliverable-1_Apr20-submitted/Annex D_Draft Replacement Protocol_UHC Year 2.pdf]]"
date_ingested: 2026-04-20
tags: [deliverable-1, inception-report, field-ops, replacement-protocol, sampling-integrity, ingest-batch-apr20]
---

# Source — Annex D: Draft Replacement Protocol

1-page field-ops annex defining **when and how** sampled facilities / patients / households may be replaced when the primary selection is unreachable. Marked "Draft" — explicit caveat that private-hospital rules will be refined further.

## Rules per survey module

### Health Facility Survey ([[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F1 Facility Head Survey Questionnaire|F1]])

Replacement permitted only when the sampled facility is:
- Permanently closed, OR
- Misclassified, OR
- Outside the geographic scope, OR
- Refuses participation **after the minimum contact protocol is exhausted**

**Minimum contact protocol:** ≥3 on-site visits at different times and days + phone + email + personal contact before a facility is declared nonresponsive.

**Substitute-selection rule:** Must come from the **same stratum** (UHC / non-UHC IS × facility type × geographic area), randomly drawn from the reserve list, preserving probability proportional to size (PPS).

**Governance:** Supervisors approve all replacements. Detailed documentation required (reason, attempts, substitute facility). Survey disposition reported. **Replacement rate cap: 5–10%.** Weights adjusted for design consistency.

### Patient Survey ([[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3 Patient Survey Questionnaire|F3]])

Replacement triggers: ineligibility, unavailability, refusal, capacity constraint preventing interview.

**Substitute-selection rule:** Next eligible patient in the systematic-interval / random-selection sequence (per [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3b Patient Listing Protocol|F3b listing protocol]]). **Must happen within the same data collection session** to avoid bias.

**Enumerator-discretion ban:** Enumerators explicitly prohibited from picking outside the prescribed selection rules.

**Governance:** Supervisors monitor refusal + unavailability rates. Every replacement logged with reason code, selection order, and outcome (privacy-preserving). Nonresponse weights adjusted.

### Household Survey ([[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F4 Household Survey Questionnaire|F4]])

Replacement triggers: vacant housing unit, non-residential, unsafe, or repeated-contact failure.

**Minimum contact protocol:** ≥3 visits at varied times before noncontact declared.

**Substitute-selection rule:** Replacement households drawn from the **same cluster (barangay PSU)**.

**Governance:** Supervisors approve; visit-sheet documentation with reason codes. Household weights adjusted for nonresponse.

## Private-hospital caveat

> The team will further refine the protocols for surveys in private hospitals, given their more complex nature.

Consistent with the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Revised Inception Report|Revised IR]] Section V.D SJREB-acceptance clause — private hospital inclusion is contingent on ethics-review cooperation; replacement rules there may need a separate pathway.

## CAPI implications

- **No CAPI schema change required** — this is a field-ops protocol, not a question set.
- **Field supervisor tooling**: CSWeb dashboards should surface replacement cases (flagged via a `replacement_flag` + `replacement_reason_code` on the case record). Consider `original_case_id` back-reference so downstream weight computation can pair originals with substitutes.
- **Enumerator CAPI app** should emit replacement attempts as structured events (attempt #, date, time, outcome) rather than free text, so the ≥3-visit threshold is machine-verifiable by the field supervisor before approving a replacement.
- **Weights pipeline** (post-fieldwork, not CAPI): each survey module's weights need a nonresponse adjustment factor; the replacement log is the input.

## Cross-references

- Field-ops partner: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3b Patient Listing Protocol|Annex F3b]] (patient interval-sampling + refusal handling)
- Parent: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Revised Inception Report|Revised Inception Report]] Section V.D (sampling design) + V.E (quality control)
- Sampling frames: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex B List of UHC Integration Sites|Annex B]] + [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex C List of Non UHC Integration Sites|Annex C]]

## Sources

- Raw file: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Project-Deliverable-1_Apr20-submitted/Annex D_Draft Replacement Protocol_UHC Year 2.pdf|Annex D PDF]]
- Authored by [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/ASPSI|ASPSI]] project team
