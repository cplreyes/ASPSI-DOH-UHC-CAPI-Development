---
type: source-summary
source: "Google Drive (read via UP-account connector) — PSA SSRCS Completeness Check Form, DOH-PMSMD/ASPSI 'UHC Survey - Year 2', Transaction No. 26SSRCS06-068, dated 2026-06-09. Linked from the DOH-PMSMD email of 2026-06-11. Ingested 2026-06-29."
date_ingested: 2026-06-29
tags: [psa, ssrcs, clearance, completeness-check, capi, cawi, survey-tools, scoping, process]
---

# Source - PSA SSRCS Completeness Check (26SSRCS06-068, 2026-06-09)

The **Philippine Statistics Authority** Statistical Survey Review and Clearance System (**SSRCS**) **Completeness Check** on ASPSI's submission for the UHC Survey Year 2, **Transaction No. 26SSRCS06-068**, dated **2026-06-09**, prepared by the PSA Statistical Standards Division (Tangson / Catanghal / Aycardo). This is the **PSA statistical-clearance track** (parallel to the SJREB ethics track). Read via Drive from the link in DOH-PMSMD's 2026-06-11 email.

> [!note] What a "completeness check" is
> The PSA **formal 20-working-day review starts only after** the completeness check passes and all clarifications are resolved. *"Issues were observed in some documents"* — so the clock had **not** yet started as of June 9; deficiencies must be cleared first. This is the gate Myra refers to when she says new comments "push back the start of the 20-working-days allotment."

## Core documentary requirements (the SSRCS submission packet)

1. Letter addressed to the **NSCRG** (PSA Undersecretary / National Statistician **Claire Dennis S. Mapa**), explicitly requesting clearance, duly signed.
2. **SSRCS Form 1** (general info, objectives, technical description, questionnaire titles, cost breakdown, timetable, contacts).
3. **Survey Questionnaires (PAPI) + CAPI/CAWI user interface** — all required versions; PAPI↔CAPI/CAWI consistency.
4. **Survey Manual / Manual of Instructions** (comprehensive, agency-approved, full data-collection-through-data-entry instructions + QA).
5. **Compilation of Policy Uses** of survey results.
6. **List of Tables (dummy tables + descriptions)** tied to objectives.
7. **Survey Proposal** (objectives, methodology, sample design, analysis plan, expected outcomes).
8. **SSRCS Form 4** (Statistical Survey Monitoring Form) from the previous application — complete + signed.
Optional: pre-test/pilot results, previous-survey results.

## Issues to address (PSA Remarks — the actionable findings)

- **Form 1 §I item 3.3 (Other Cooperating Agencies):** provide info or mark **N/A**.
- **Survey title inconsistency:** *"Universal Health Care (UHC) Survey – Year 2"* in Form 1 vs the title shown in the submitted questionnaires — **make the title consistent across all materials**.
- **Questionnaire-title inconsistency:** Form 1 questionnaire **Nos. 3 and 4** differ from the titles in the submitted questionnaires — reconcile.
- **Form 1 §IV timeline format:** use either *"nth week Month YYYY"* or *"dd Month YYYY"*.
- **CAPI/CAWI consistency check:** PSA requests **screenshots of the CAWI/CAPI version** of the online questionnaire **or viewer access** to the survey link. *(Directly relevant to our CAPI — interface screen-caps are a clearance input; ties to Myra's note that PSA caps "should be reflective of the revised debugged CAPI versions.")*
- **Submit:** accomplished **SSRCS Form 4 (signed)** + **Previous Survey Results**.
- **Comparison matrix** summarizing changes in the current round vs previous rounds.

## Why it matters here

- The **CAPI/CAWI screenshots requirement** is the formal reason the deployed CSEntry interface feeds the PSA packet — and why re-working tools mid-review forces re-capture (Myra's cascade, see [[Source - Project Movement and Revised Timeline (Apr-Jun 2026)]]).
- All findings are **document-consistency / completeness** items (titles, forms, screen-caps) — not instrument-logic defects. None of them are Carl-build items by themselves; they're ASPSI's submission-packet fixes.

## Cross-references
- [[Source - Project Movement and Revised Timeline (Apr-Jun 2026)]] — the PSA review is one of the two parallel tracks (with SJREB) gating the pretest.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/PSA]] · [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/SJREB]] · [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/DOH-PMSMD]].
- [[Timetable of Activities]] — Activity 2.5 (submission to PSA-SSRCS + SJREB).
