---
type: concept
tags: [cspro, capture-types, capi, form-design, controls]
source_count: 2
---

# CSPro Capture Types

CSPro lets you specify how each field is rendered for the operator. The base type is **Text Box**; other types are called **capture types** (sometimes "extended controls"). Capture type is set on the dictionary item or on the form field directly — a field-level setting overrides the dictionary-level one. Selecting `Capture Types: CAPI Mode` in the Drag Options dialog when dragging an item to a form makes CSPro pick a capture type automatically based on the field's first value set.

In the CSPro Designer, fields with a capture type are outlined in **blue**; Number Pad fields use a lighter blue.

## The twelve capture types

| Capture type | Numeric ok | Alpha ok | What it does | Notes |
|---|---|---|---|---|
| **Barcode** | yes | yes | Opens the device camera and scans a barcode or QR code | Android only — Windows shows a Text Box. Can also be invoked from logic via `Barcode.read`. |
| **Check Box** | no | yes | Multi-response selection | Field length must be a multiple of the longest value code; each code goes into the field left-to-right as boxes are checked. Length controls how many can be selected (e.g., length 5 + 1-char codes = pick up to 5). |
| **Date** | yes | yes | Date picker | Item must be length 4, 6, or 8. No value set required. The chosen date format determines storage. |
| **Drop Down** | yes | yes | Discrete-value selector. Visually identical to Radio Button on Windows; **renders as radio buttons on Android**. | Value set may not contain "to values" (ranges). |
| **Combo Box** | yes | yes | Like Drop Down but supports value sets with ranges (`to values`). On Android: text box + button that pops up the full value set including ranges and discrete codes (e.g., a "Missing" code). |
| **Number Pad** | yes | no | Numpad for finger/mouse entry | **No effect on Android** — the native numeric keyboard is already shown. |
| **Radio Button** | yes | yes | Discrete-value selector with all options visible | Value set may not contain ranges. |
| **Slider** | yes | no | Numeric range slider, defined by `to values` in the value set | Android only — Windows shows a text box (numeric only). |
| **Text Box** (default, with tickmarks) | yes | yes | Plain entry field. On Windows, tickmarks divide each character. Tick-marked text boxes are not resizable. | The fallback / no-capture-type rendering. |
| **Text Box (No Tickmarks)** | no | yes | Alpha-only text entry, resizable horizontally | Useful for connecting scripts (e.g., Arabic) or composite-character languages. |
| **Text Box (Multiline)** | no | yes | Multi-line alpha text. Resizable both axes. | Newlines stored as `\n`. On Windows enter line breaks with Ctrl+Enter (Enter alone moves to the next field). Status bar shows characters used / total. |
| **Toggle Button** | yes | yes | Single on/off button. Selecting → the value goes in; not selecting → field validates as `notappl` (numeric) or `""` (alpha). | Define one value-set value for the field. Optionally pair it with a value mapped to `notappl` / `""` so the unselected state has a label too. |

## Validation behavior

| Capture type | Numeric field validation | Alphanumeric field validation |
|---|---|---|
| Barcode | In value set | In value set |
| Check Box | n/a | Composed of values in the value set |
| Combo Box | In value set | In value set (only for fields of length 1) |
| Date | In value set **and** a valid date | In value set **and** a valid date |
| Radio Button / Drop Down | In value set | In value set |
| Slider | In value set | n/a |
| Text Box / Number Pad | In value set | In value set (only for fields of length 1) |
| Toggle Button | In value set or `notappl` | In value set or blank |

## Hiding the capture type window title

By default CSEntry displays the value set's label as the window title for the capture control. Hide it from logic:

```
setproperty(dictionary_symbol, "ShowExtendedControlTitle", "No");
```

## Project relevance

> [!info] As-built (2026-06-12): capture types are generator-owned
> For F1 (Facility Head), F3 (Patient), and F4 (Household), capture types are **not** hand-assigned in Designer (the CAPI Mode drag described above is no longer the project mechanism). They are assigned by `automation/optimize_capture_types.py`, which runs inside `cspro_compile_driver --build` for **all** instruments. The pipeline rules:
>
> - **Drop Down** for any value set with **>= 7 options**, and for all cascade (lookup) fields.
> - **Numeric length-8 YYYYMMDD date fields** → the combined `Date,YYYYMMDD` capture type; legacy standalone `CaptureDateFormat` lines are **stripped**.
> - **Multi-select questions** are modeled as **per-option Yes/No fields** — except **Q148_CONDITIONS**, which is a true **Check Box** multi-select (Other = 99). The CHECKBOX assignment wins over the DropDown rule.
>
> **Packager is stricter than Designer:** the Designer Publish/Deploy **packager is a stricter FMF parser than Designer open+compile**. A `Date` capture type paired with a legacy `CaptureDateFormat` line compiles cleanly in Designer but was **rejected by the deploy packager on 2026-06-12** — which is why the generator strips the legacy lines. (Source: log.md entry 2026-06-12)

Still-valid general notes for the tablet build:

- **Free-text "Other (specify)" fields** are isolated behind gated other-specify logic in the combined-view screens rather than relying on capture-type choice alone.
- **Signatures and consent images** → use the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro CAPI Strategies|Signature]] and Camera multimedia features (separate from capture types — driven by `image.captureSignature` / `image.takePhoto`).
- **Number Pad** is a no-op on Android and not worth setting for the tablet build.

## Sources

- (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro 8.0 Complete Users Guide]])
- (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro Android CAPI Getting Started]])
