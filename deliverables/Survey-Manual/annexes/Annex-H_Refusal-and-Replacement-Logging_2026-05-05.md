# Annex H — Refusal and Replacement Logging

**Audience:** Field Supervisors, Data Programmer, sampling analysts
**Purpose:** Describes how refusals, ineligibilities, and replacements are recorded, how replacement chains are linked, and how the daily replacement report is generated, in fulfillment of Protocol §XII's documentation requirement.

---

## Why this matters

Refusals and replacements influence the final sampling weights. Without structured documentation, the analyst cannot adjust weights correctly, and the survey's representativeness claims become indefensible. Every refusal and every replacement must be auditable from the analytic dataset back to the field decision that produced it.

## Where logging happens

All facility-level and case-level non-response is logged inside CSPro on a structured form, separate from the main case record:

- **F0d — Refusal & Replacement Log** (the Field Supervisor's app) for facility-level coordination, replacement decisions, and contact-attempt tracking
- **Refusal forms inside F1, F3a, F3b, F4a, F4b** for case-specific reasons (refused listing, refused interview, ineligible at point of contact, etc.)

The two are joined by case ID during analysis.

## Reason codes (canonical list)

Used in both F0d and the per-module refusal forms:

| Code | Reason | When used |
|---|---|---|
| 01 | Refused listing | Patient/household refused to be listed at the intercept stage |
| 02 | Refused interview | Listed respondent refused at the interview stage |
| 03 | Ineligible at listing | Failed eligibility screening at intercept (residency, age, completed-consultation, etc.) |
| 04 | Ineligible at interview | Eligibility issue surfaced after listing |
| 05 | Unreachable | Three contact attempts exhausted with no response |
| 06 | Infectious / grave case | Patient health status precludes interview; visited last per Protocol |
| 07 | Cognitive limitation | Respondent cannot understand or respond |
| 08 | Companion unavailable | Required companion (for minor/elderly/infirm patient) was not available |
| 09 | Logistical (security, weather) | Field conditions prevented contact |
| 10 | Other | Free-text; flagged for analyst review |
| 99 | Not applicable | Internal use |

## Contact-attempt protocol

Per Protocol §XII, three contact attempts at three different days/times are required before classifying a household or facility head as non-responsive. F0d captures each attempt:

| Attempt | Field |
|---|---|
| Date | Date of the attempt |
| Time | Approximate time |
| Method | In-person visit / phone / SMS / Viber |
| Outcome | Responded / no answer / declined / scheduled callback |
| Note | Free text |

The form blocks classification of a case as "unreachable" until at least three attempts are recorded with three distinct dates.

## Replacement chain

Every replacement case is linked to the original it replaces via the `REPLACEMENT_FOR` field, populated automatically from F0d when the Field Supervisor draws a replacement.

```
Original case (refused/unreachable) → REPLACEMENT_1 → (if also refused) → REPLACEMENT_2 → ...
```

The chain is visible in the analytic dataset and is used by the analyst to apply non-response weights.

## Replacement rules (recap from Protocol §IX, §XII)

| Rule | Source |
|---|---|
| Replacement comes from the same stratum (UHC IS or non-UHC IS, facility type, geographic area) | Protocol §XII |
| Replacement is randomly selected from the pre-approved reserve list | Protocol §XII |
| Replacement rates are limited to 5–10 percent | Protocol §IX |
| Sampling weights are adjusted accordingly | Protocol §IX |

## Replacement-rate exceedance escalation

The Field Supervisor monitors the running replacement rate per facility daily through F0c. The escalation chain (proposed; pending Methodology Clarification Request M3):

| Threshold | Action |
|---|---|
| ≥ 8% | F0e escalation to Survey Manager + Project Lead |
| ≥ 10% (cap reached) | F0e escalation to PI; data flagged for downweighting or exclusion (decision: PI + Survey Manager + DOH-PMSMD focal person) |

## Daily replacement report

Generated each morning by the Data Programmer from CSWeb F0d records. Distribution:

- Field Supervisors (their own coverage)
- Survey Manager (all)
- Project Lead (all)

Report columns:

| Column | Source |
|---|---|
| Date of report | Run date |
| Facility ID | F0d |
| Facility name | Facility master |
| Original case count | F0d |
| Refusals in last 24h | F0d |
| Replacements drawn in last 24h | F0d |
| Cumulative replacement count | Running |
| Cumulative replacement rate (%) | Running, vs target sample |
| Threshold flag | None / 8% warning / 10% cap exceeded |
| Last action taken | F0d / F0e |

## Analyst handoff

At the close of fieldwork, the analyst receives:

- The full F0d table from CSWeb
- The per-module refusal forms (F1, F3a, F3b, F4a, F4b)
- The replacement chain (`REPLACEMENT_FOR` linkage) joined to the analytic dataset
- The signed-off version of each CAPI application (for instrument provenance per Annex G)

The analyst applies non-response weights using the procedure documented in the project's Sampling Weight SOP.
