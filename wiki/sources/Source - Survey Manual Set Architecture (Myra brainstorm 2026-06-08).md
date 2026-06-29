---
type: source-summary
source: "Email — Myra (mcsilva@up.edu.ph) → Kidd, cc Carl, 2026-06-08 'Survey Manual and Pretesting Plan'; 2 docx in raw/survey-manual-brainstorm/"
date_ingested: 2026-06-28
tags: [survey-manual, documentation, epic-7, manual-set, dhs-model, notebooklm]
---

# Source - Survey Manual Set Architecture (Myra brainstorm 2026-06-08)

**Two ChatGPT/NotebookLM working docs Myra circulated** (sent 2026-06-08 "Survey Manual and Pretesting Plan"; re-attached from the 1 June brainstorm). Filed at `raw/survey-manual-brainstorm/` (gitignored). These reframe the whole survey-documentation deliverable and define a drafting workflow.

> [!note] No standalone "Pretesting Plan" doc here
> Despite the email subject, these two attachments are the **survey-manual architecture brainstorm** + a **NotebookLM drafting workflow** — not a separate pretest plan. Pretest content (Epic 6) is referenced as a *section of the Operations Manual*, not a distinct document in this drop.

## 1. Manual-set architecture (`UHC survey manual (MESJ, CHATGPT results 1 June).docx`)

**Core recommendation: split the documentation into FOUR linked-but-distinct manuals (DHS model), not one combined field manual.** The current ASPSI/UHC outline mixes four purposes — survey governance, enumerator instructions, supervisor instructions, and CAPI use — which the DHS manuals keep separate:

| Manual | Models (DHS) | Scope | Owner |
|---|---|---|---|
| **Survey Operations Manual** | DHS Survey Organization Manual | overall design/governance: structure, staffing, work plan, timetable, budget, sample design, **CAPI, pretest, recruitment, training, data collection, QC, data processing, analysis, dissemination** | ASPSI |
| **Field Enumerator's Manual** | DHS Interviewer's Manual | respondent contact, interviewing technique, field procedures, **general questionnaire completion**, then tool-specific instructions (F1/F2/F3/F4) | ASPSI |
| **Field Supervisor's Manual** | DHS Supervisor's Manual | logistics, team management, maps/navigation, assigning work, nonresponse control, daily output checks, observation, re-interview/QC, escalation — **not** the question-by-question guide | ASPSI |
| **CAPI Manual** | (separate per DHS — paper teaches question text; CAPI handled separately) | device + app use, assignments, data entry, sync, troubleshooting, supervisor features | **Carl** ([[Source - CAPI Manual Materials (Myra 2026-06-17)]]) |
| (Training Manual) | DHS Training Manual | recruitment, training design, practice, testing, early field supervision | ASPSI |

**Key implication for Carl:** DHS explicitly **separates CAPI from questionnaire content** — the paper questionnaire teaches question text/probes/coding; CAPI procedures live in their own manual. This validates the standalone **CAPI Manual** (Carl's deliverable) and means data-cleaning/processing/tabulation/analysis sections move OUT of the enumerator/supervisor manuals into the **Operations Manual**. (15 reference tables in the doc map each ASPSI outline section to its DHS home + source.)

## 2. NotebookLM drafting workflow (`UHC survey manual (NotebookLM workflow).docx`)

A process for using **NotebookLM as the first-draft generator** for the manual set:
- One **master notebook** ("Survey Manual Set Development") with all sources uploaded under clear names (Source 01 Protocol, 02 Draft Manual, 03 Style & Design Guide, 04–07 per-manual outlines, 08 Survey Tools…).
- **Per-manual working notebooks** (Enumerator / Supervisor / **CAPI App** / Data-Quality+Processing / optional Training, Tool-Reference), each loaded with only its relevant sources + the common ones.
- Staged prompts: (1) source-synthesis/understand-first, (2) manual-set architecture, then per-manual drafting — referring to specific source names.
- The **CAPI App Manual Notebook** sources: CAPI outline + screenshots/workflow notes + survey tools + data-entry rules + error-checking rules + sync/upload + troubleshooting + style guide.

## Cross-references

- [[Source - CAPI Manual Materials (Myra 2026-06-17)]] — the CAPI Manual's own outline + style (Carl's slice of this set).
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - DOH UHC Year 2 Survey Manual]] — the existing combined manual this restructure would supersede.
- Epic 7 (Training & Documentation) / D5 — the deliverable this reorganizes.
