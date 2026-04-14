---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Documentations/CSPro 8.0 Complete Users Guide]]"
date_ingested: 2026-04-09
tags: [cspro, reference, official, capi, dictionary, logic, csweb, sync]
---

# Source - CSPro 8.0 Complete Users Guide

The official 958-page CSPro 8.0 user manual published by the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/US Census Bureau|US Census Bureau]]. This is the authoritative reference for the entire CSPro toolchain — Designer, CSEntry, CSBatch, CSTab, Forms Designer, Data Dictionary, and the CSPro logic language. Catalogued via [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro Documentation|Source - CSPro Documentation]] and downloaded as a local PDF.

## What it covers

The guide is organized into the following major sections:

| Section | Pages | What's in it |
|---|---|---|
| The CSPro System / What's New | 25–48 | Overview, capabilities, full release history through 8.0 |
| CSPro General Concepts and Functionality | 55–70 | Workspaces, data sources, encryption, Unicode, **Synchronization Overview**, paradata, **multiple-language applications**, mapping, questionnaire view |
| Data Dictionary Module | 79–122 | Levels, records, items, value sets, relations, dictionary screen layout, security |
| The CSPro Language | 123–180 | Declaration sections, procedural sections, statements (proc, preproc, onfocus, killfocus, postproc, onoccchange), variables, expressions, operators, files |
| Data Entry Module | 181–272 | Data entry philosophies, **system- vs operator-controlled**, **skip issues**, path on/off, forms designer, data entry editing, **CAPI Data Entry**, capture types, multimedia, CAPI strategies, network entry, **Android Data Entry** |
| Batch Editing | 273–301 | Batch edit applications, structure & consistency edits, hot decks, imputation, reporting |
| Tabulation | 302–426 | Cross-tabs, area processing, formatting, post-calculation, table data sources |
| Statements and Functions Reference | 448–end | Alphabetical reference for every CSPro function and statement, including all `Sync*`, `Map`, `Audio`, `Image`, `Case`, `File`, `HashMap`, `ValueSet`, etc. objects |

## Highlights extracted for this project

The full guide is too large to mirror in the wiki. Concept pages have been created from the sections most relevant to the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/UHC Survey Year 2|UHC Survey Year 2]] CAPI build:

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Data Entry Modes]] — system- vs operator-controlled, heads-up vs heads-down, skip philosophies, data entry path on/off
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Capture Types]] — Barcode, Check Box, Date, Drop Down/Combo Box, Number Pad, Radio Button, Slider, Text Box, Toggle Button
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro CAPI Strategies]] — forms, fields, questions, organization, multi-language, breaking off, partial save, prefilling, blocks
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Question Text and Fills]] — fills, conditional questions, HTML in fills, occurrence labels, user-defined function fills
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Synchronization]] — synchronization architecture, server types (CSWeb / Dropbox / FTP / Bluetooth), `sync*` logic functions, deployment, troubleshooting via `sync.log`
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Multi-Language Applications]] — multiple-language question text, dictionary labels, messages, `tr` function, `setlanguage` / `getlanguage`
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Logic Events]] — order of execution for `preproc`, `onfocus`, `killfocus`, `postproc`, `onoccchange`; blocks; consistency edits

## Notes and caveats

- The PDF is the printed export of the in-app F1 help system, so it lacks some interactive elements (cross-links between functions). For function-level details, the in-app help is still the most usable form.
- Version is locked to **8.0.0**. Newer 8.0.x patches may add features not described here. The "What's New in CSPro 8.0?" section (p. 41) lists the breaking changes versus 7.x.
- Page numbers above refer to the *table of contents page numbers in the PDF*, which may differ slightly from the absolute page positions due to front matter.
