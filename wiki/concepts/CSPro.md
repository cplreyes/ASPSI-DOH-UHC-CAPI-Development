---
type: concept
tags: [cspro, capi, software, data-collection]
source_count: 6
---

# CSPro — Census and Survey Processing System

Free, open-source software package developed by the [[wiki/entities/US Census Bureau|US Census Bureau]], used for the [[wiki/concepts/UHC Survey Year 2|UHC Survey Year 2]] CAPI application. Replaces SurveyCTO used in Year 1. Project is locked to CSPro 8.0; canonical references are catalogued in [[wiki/sources/Source - CSPro Documentation|Source - CSPro Documentation]] and the authoritative manual is [[wiki/sources/Source - CSPro 8.0 Complete Users Guide]].

## Toolchain reference

Detailed concept pages built from the 8.0 Users Guide:

- [[wiki/concepts/CSPro Data Dictionary]] — `.dcf` schema (the foundation everything else builds on)
- [[wiki/concepts/CSPro Language Fundamentals]] — PROC GLOBAL, declarations, logic objects, expressions
- [[wiki/concepts/CSPro Logic Events]] — preproc/postproc/onfocus/killfocus/onoccchange order
- [[wiki/concepts/CSPro Data Entry Modes]] — system- vs operator-controlled, heads-up vs heads-down
- [[wiki/concepts/CSPro Capture Types]] — text box, radio, drop down, number pad, date, etc.
- [[wiki/concepts/CSPro CAPI Strategies]] — forms, fields, blocks, partial save, prefilling
- [[wiki/concepts/CSPro Question Text and Fills]] — `~~item~~` fills, HTML, conditional question text
- [[wiki/concepts/CSPro Multi-Language Applications]] — multi-language labels, `tr`, `setlanguage`
- [[wiki/concepts/CSPro Synchronization]] — `sync*` functions, server types, troubleshooting
- [[wiki/concepts/CSPro Batch Editing]] — CSBatch, structure/validity/consistency checks, hot decks
- [[wiki/concepts/CSPro Tabulation]] — CSTab, cross-tabs, area processing, weights

## Why CSPro over SurveyCTO

| Feature | CSPro | SurveyCTO |
|---|---|---|
| Cost | Free, open-source | Paid per-user/submission |
| Scalability | 100K+ cases | Costs grow with volume |
| Customization | Advanced logic (skips, validations, rosters, branching) | Restricted to XLSForm |
| Offline support | Robust tablet CAPI, ideal for low-connectivity | Strong but less seamless |
| Real-time monitoring | [[wiki/concepts/CSWeb|CSWeb]] dashboard | Built-in but less customizable |
| Data export | Native Stata, SPSS, SAS, R, CSV, DBF | CSV/Excel, extra steps needed |
| Post-project ownership | Full independence, self-hosted | Vendor lock-in |
| Deployment | Self-hosted (VPS/Docker) or Dropbox | Cloud-only |

## Role in This Project

1. **Data dictionaries** — built from finalized questionnaire annexes (F1–F4), defining records, items, value sets, and validation rules.
2. **CAPI application** — tablet-based form with skip logic, range checks, and conversational interview flow. Runs on Android via CSEntry.
3. **Data sync** — completed interviews sent to [[wiki/concepts/CSWeb|CSWeb]] server; program modifications received from it.
4. **Data export** — native export to Stata and other statistical packages for analysis.

## Development Workflow

Paper questionnaire → pre-test → refine → **create data dictionary** → **build CAPI app** → bench test → pilot test (field) → refine → deploy to enumerator tablets.

## Sources

- (Source: [[wiki/sources/Source - Revised Inception Report]])
- (Source: [[wiki/sources/Source - CSPro Documentation]])
- (Source: [[wiki/sources/Source - CSPro 8.0 Complete Users Guide]])
- (Source: [[wiki/sources/Source - CSPro Android CAPI Getting Started]])
- (Source: [[wiki/sources/Source - CSPro Android Data Transfer Guide]])
- (Source: [[wiki/sources/Source - ASPSI Proposal Approach and Methodology]]) — describes the CAPI development workflow (Figure 4.3) and commits to CSPro as the binding technical choice
