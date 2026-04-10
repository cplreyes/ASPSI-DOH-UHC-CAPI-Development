---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Documentations/CSPro Android CAPI Getting Started]]"
date_ingested: 2026-04-09
tags: [cspro, capi, csentry, android, walkthrough, tutorial]
---

# Source - CSPro Android CAPI Getting Started

A 16-page tutorial published by the [[wiki/entities/US Census Bureau|US Census Bureau]] that walks through building a small CAPI application called `MyCAPI_Intro` from a fresh CSPro install. The example targets CSPro 6.1 but the workflow is essentially identical in 8.0. This is the closest official walkthrough to what Carl is building for [[wiki/concepts/UHC Survey Year 2|UHC Survey Year 2]] (F1, F3, F4).

## What the walkthrough builds

A simple household-roster CAPI app with six items per person:

| Item | Type | Notes |
|---|---|---|
| `HOUSEHOLD_ID` | numeric, length 4 | identifier item |
| `NAME` | alpha, length 20 | used in fills (`%NAME%` filled into later question text) |
| `SEX` | numeric, length 1 | values 1=male, 2=female |
| `RELATIONSHIP` | numeric, length 1 | **two value sets** — male relationships and female relationships, switched dynamically using `setvalueset` in the `onfocus` of `RELATIONSHIP` |
| `AGE` | numeric, length 3 | range 0–115 |
| `LITERATE` | numeric, length 1 | 1=literate, 2=not |

Each item is dragged from the dictionary tree onto the form. Because the ID item and the `PERSON_REC` items go on the same form, `PERSON_REC` is rendered as a **roster** in the designer; on the device, each question still appears one-per-screen.

## Workflow steps the doc covers

1. **Examine the data dictionary** — items, lengths, value sets, multiple value sets per item.
2. **Create a CAPI Data Entry Application** (`File → New → CAPI Data Entry Application`).
3. **Drag items from the dictionary tree to the form** (`HOUSEHOLD_ID`, then `PERSON_REC` becomes a roster). Accept the Drag Options defaults.
4. **Add CAPI question text** for each item via the Forms Tree → right-click → "View CAPI Questions".
5. **Use fills** with `%item_name%` syntax for substitutions — e.g., `Is %NAME% male or female?`. (Note: in CSPro 8.0 the canonical syntax is double tildes, `~~NAME~~` — see [[wiki/concepts/CSPro Question Text and Fills]].)
6. **Switch value sets dynamically** based on prior responses — `setvalueset(RELATIONSHIP, RELATIONSHIP_MALE_VS)` in the `OnFocus` of `RELATIONSHIP`, conditional on `SEX`.
7. **End a roster** by detecting a blank `NAME` and using `endgroup` to close out the household, with an `accept` dialog asking "continue / end roster".
8. **Publish to a tablet**:
    - Run the app on Windows once to auto-create the `.pff` file.
    - `File → Publish Entry Application (.pen)` to create the `.pen` file.
    - Copy both files via USB to the `csentry` folder on the device. CSEntry detects the application automatically.
9. **Survey the available controls**: Text Box, Text Box (no tickmarks), Text Box (multiline), Radio Button, Drop Down, Combo Box, Check Box, Number Pad, Date Control. (Number Pad has no effect on Android — already the native keypad.) See [[wiki/concepts/CSPro Capture Types]] for the full reference.
10. **Navigate the case tree** — back/forward buttons, "Show case tree" Windows option (Android always shows it).
11. **Copy data files off the device** via USB by following the path defined in the `.pff` file.

## Why this matters for the project

This walkthrough is the minimum-viable end-to-end process for **F1 (Facility Head)**, **F3 (Patient)**, and **F4 (Household)**. The patterns Carl will lift directly:

- **Dynamic value sets** via `setvalueset` in `onfocus` — F3 has outpatient/inpatient routing and F4 has household-member-conditional questions; both will use this.
- **Roster + endgroup pattern** — F4 household roster will end on a blank name signal exactly like the walkthrough.
- **Fills with `%item%` (or `~~item~~` in 8.0)** — already needed across all four annexes for personalized question text.
- **Bench-test deploy via USB** — for the Tranche 2 demonstration before any CSWeb/SJREB clearance, this is the path to "CAPI app ready" without needing the server stack.

## Notes and caveats

- Fill syntax in this doc uses `%NAME%`. **CSPro 8.0 uses `~~NAME~~`.** The 8.0 syntax is in [[wiki/sources/Source - CSPro 8.0 Complete Users Guide]] (CAPI Strategies → Questions). Use `~~ ~~` for new work.
- Document uses 6.1 screenshots; UI in 8.0 is similar but the menus have moved slightly.
- Does not cover synchronization (CSWeb/Dropbox), multi-language applications, or paradata. Those are in the Complete User's Guide and the [[wiki/sources/Source - CSPro Android Data Transfer Guide]].
