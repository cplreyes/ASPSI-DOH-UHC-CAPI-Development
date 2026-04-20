---
type: concept
tags: [cspro, dcf, value-sets, conventions, f-series, na-coding]
source_count: 0
---

# F-Series Value Set Conventions

Coding conventions that apply across the F-series CSPro dictionaries (F1 Facility Head, F2/F3/F4 when built). These are project-internal decisions, not CSPro mandates — they exist to keep coding consistent across instruments and to give analysts a predictable codebook.

Decided during the `E2-F1-010` Designer walkthrough on 2026-04-14 (see [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/log]] entry for that date).

## "Not Applicable" coding

When a value set includes **"Not applicable" as an explicit pickable option**, encode it as the **highest valid code at the item's field width**:

| Field width | NA code |
|---|---|
| length-1 numeric | `9` |
| length-2 numeric | `99` |
| length-3 numeric | `999` |

### Why this rule (not the DHS 7/97 convention)

The strict DHS/MICS convention layers the top of the field width as a reserved zone:

| Code (length-1) | Reserved meaning |
|---|---|
| 7 | Not applicable |
| 8 | Don't know |
| 9 | Missing / Not stated |

That layout reserves slots for **Don't know** and **Missing** as separately tracked outcomes. The F-series instruments do not track Missing as a distinct concept — non-response is just a blank cell, which CSPro auto-maps to the special value `notappl`. So the DHS reserved zone is dead weight here.

The "highest code = NA" rule:
- matches F1's existing dominant pattern (5 of 7 value sets already used NA=9 before standardization)
- is recognizable as the "least-likely answer goes at the top" intuition analysts already expect
- requires no field-width promotions
- still leaves the lower codes free for substantive options up to the width ceiling

### Important: never use CSPro's `notappl` special value in a value set

CSPro reserves the special value `notappl` for **fields skipped during data entry**. The runtime auto-assigns it when a field is bypassed by skip logic. **Never** mark a value-set entry's "special value" column as `notappl` — doing so collides with CSPro's built-in skip handling and breaks logic that tests `if X = notappl`.

The two concepts must stay distinct:

| Concept | Storage | Where it comes from |
|---|---|---|
| **Field was skipped** | Blank cell, auto-tagged `notappl` by CSPro | PROC skip logic, no value-set entry needed |
| **Enumerator picked "Not Applicable"** | Numeric code (9 / 99 / 999) | Value-set entry with a normal numeric code, no special-value tag |

A field can have both: the value set defines `9 = "Not applicable"` for cases where the enumerator explicitly picks NA, *and* the field can also be skipped by PROC logic, in which case it's blank and tests `= notappl`. These are different outcomes and the analysis annex should distinguish them.

### Edge case: when substantive options exhaust the field width

If a single-response question has so many substantive options that they fill the entire field width, you have two choices:

1. **Promote the field width** (length-1 → length-2). NA then sits at `99`, leaving room for everything.
2. **Squeeze, accepting the loss of any reserved zone.** Substantive options take all codes including the top one. NA cannot be encoded as a pickable option in this case — it can only be expressed via skip-logic blank.

F1's `UHC9_OPTIONS` is the live example of the squeeze case: 7 substantive "yes/no with reason" options + `8 = I don't know` + `9 = Not applicable` fills the entire 1-digit space. There is no Missing slot. This is intentional and `UHC9_OPTIONS` should be left as-is.

**Default rule:** if substantive options would push past 7 in length-1, promote to length-2 instead of squeezing. Squeezing is allowed only when the value set is locked to a printed questionnaire that already has the layout (the UHC9 case).

## How this is enforced

The convention lives in two places:
1. This document, for human reference.
2. [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/F1/generate_dcf.py]] — the generator is the source of truth for actual codes; any change must be made there and regenerated, never hand-edited in CSPro Designer (see [[CSPro Data Dictionary]] for the generator-vs-Designer rule).

## Related

- [[CSPro Data Dictionary]] — overall DCF schema and value-set mechanics
- [[CSPro Capture Types]] — single-response vs multi-mark idioms
- `E2-F1-010` — sprint task where these conventions were ratified
