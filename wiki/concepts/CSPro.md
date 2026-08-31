---
type: concept
tags: [cspro, capi, software, data-collection]
source_count: 7
---

# CSPro — Census and Survey Processing System

Free, open-source software package developed by the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/US Census Bureau|US Census Bureau]], used for the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/UHC Survey Year 2|UHC Survey Year 2]] CAPI application. Replaces SurveyCTO used in Year 1. Project is locked to CSPro 8.0; canonical references are catalogued in [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro Documentation|Source - CSPro Documentation]] and the authoritative manual is [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro 8.0 Complete Users Guide]].

## Toolchain reference

Detailed concept pages built from the 8.0 Users Guide:

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Data Dictionary]] — `.dcf` schema (the foundation everything else builds on)
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Language Fundamentals]] — PROC GLOBAL, declarations, logic objects, expressions
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Logic Events]] — preproc/postproc/onfocus/killfocus/onoccchange order
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Data Entry Modes]] — system- vs operator-controlled, heads-up vs heads-down
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Capture Types]] — text box, radio, drop down, number pad, date, etc.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro CAPI Strategies]] — forms, fields, blocks, partial save, prefilling
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Question Text and Fills]] — `~~item~~` fills, HTML, conditional question text
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Multi-Language Applications]] — multi-language labels, `tr`, `setlanguage`
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Synchronization]] — `sync*` functions, server types, troubleshooting
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Batch Editing]] — CSBatch, structure/validity/consistency checks, hot decks
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Tabulation]] — CSTab, cross-tabs, area processing, weights

## Why CSPro over SurveyCTO

| Feature | CSPro | SurveyCTO |
|---|---|---|
| Cost | Free, open-source | Paid per-user/submission |
| Scalability | 100K+ cases | Costs grow with volume |
| Customization | Advanced logic (skips, validations, rosters, branching) | Restricted to XLSForm |
| Offline support | Robust tablet CAPI, ideal for low-connectivity | Strong but less seamless |
| Real-time monitoring | [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSWeb|CSWeb]] dashboard | Built-in but less customizable |
| Data export | Native Stata, SPSS, SAS, R, CSV, DBF | CSV/Excel, extra steps needed |
| Post-project ownership | Full independence, self-hosted | Vendor lock-in |
| Deployment | Self-hosted (VPS/Docker) or Dropbox | Cloud-only |

## Role in This Project

1. **Data dictionaries** — built from the finalized F1, F3, and F4 questionnaire annexes, defining records, items, value sets, and validation rules. F2 sits outside the CSPro stack — it is delivered as a PWA, see [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F2 Admin Portal|F2 Admin Portal]].
2. **CAPI application** — tablet-based form with skip logic, range checks, and conversational interview flow. Runs on Android via CSEntry.
3. **Data sync** — completed interviews sent to [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSWeb|CSWeb]] server; program modifications received from it.
4. **Data export** — native export to Stata and other statistical packages for analysis.

## Translation import — name-scoped since Aug-21

Translations reach the dictionary through a pipeline, not by hand. Until the Aug-21 pack the
join was **text-keyed**: `apply_translations()` matched a translation to a question on the
full English label text, so rewording an English question silently orphaned its translation
and the build fell back to English with no error (#1182, #1213). The Aug-21 import replaced
that with a **name-scoped** join — every map key is the dictionary name
(`item:` / `vs:` / `val:`, "name-scoped-v2"), anchored to the printed paper by question
number, so an English reword can no longer detach a translation. The chain is
`aug21_english_delta.py` (build-vs-paper English delta, re-run before every extraction) ->
`anchor_extract.py` (pull each translation from the PDF between two anchors, flag what it
cannot trust) -> `apply_aug21.py` (Aug-21 wins on every key except the reasoned entries in
`aug21-overrides.json`; dry run by default) -> `run_aug21_gates.ps1` (doubling, glued
options, bridge B/C) -> `generate_dcf.py` per instrument. Everything lives under
`deliverables/CSPro/data/translations-official/`; F2, being a PWA with a flat English-keyed
store, has its own pair (`anchor_extract_f2.py`, `apply-paper-translations.py`). See
[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Revised Deliverable 2 Translated Questionnaires (Aug 21)]].

## Development Workflow

Paper questionnaire → pre-test → refine → **create data dictionary** → **build CAPI app** → bench test → pilot test (field) → refine → deploy to enumerator tablets.

## Sources

- (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Revised Inception Report]])
- (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro Documentation]])
- (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro 8.0 Complete Users Guide]])
- (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro Android CAPI Getting Started]])
- (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro Android Data Transfer Guide]])
- (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - ASPSI Proposal Approach and Methodology]]) — describes the CAPI development workflow (Figure 4.3) and commits to CSPro as the binding technical choice
