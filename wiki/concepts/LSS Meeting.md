---
type: concept
tags: [aspsi, scrum, meetings, process]
source_count: 2
---

# LSS Meeting

**LSS** = **Lessons Learned Session**, an internal [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/ASPSI|ASPSI]] meeting convened after a major deliverable submission to **retrospect on process and assign work** for the next tranche. Scope is deliberately **process + tasking + communication**, NOT technical design decisions on questionnaire content, schema, or skip logic.

## What counts as LSS scope (and what doesn't)

**In scope:**
- Retrospect on the previous tranche (what went well / what hurt calendar velocity).
- Communication-line corrections and coordination rules.
- Tasking and responsibility assignment across upcoming deliverables.
- Team/RA onboarding and introductions.
- Administrative matters (shared folders, status update cadence, COA questions).

**Out of scope:**
- Per-question decisions on instrument logic (skip patterns, value sets, field widths).
- Schema choices in CSPro data dictionaries.
- Any item that would change a `.dcf` or `.fmf` file.

Technical design decisions of that kind need a **separate, narrowly-scoped design-review meeting** with Dr. Paunlagui (Survey Manager) or whoever owns the instrument's content — not an LSS.

## Apr 13, 2026 LSS — what happened

Convened by "Doc Myra" ([[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Dr Myra Silva-Javier|Dr Myra Silva-Javier]]) on 2026-04-10 (08:45) following the Apr 8 Tranche 1 v5 resubmission. Held Mon Apr 13, 2026, 3:00 PM. Meeting notes and slides circulated Apr 15 PM; ingested at [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - ASPSI Team Meeting 2026-04-13|Source — ASPSI Team Meeting, 2026-04-13]].

Agenda (verbatim from slides): **Lessons Learned → Communication Lines → Tasking → Other Matters**. This is a textbook LSS — it fit the scope definition above cleanly. The meeting produced:

- A formal [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Team Communication Protocol|Team Communication Protocol]] (DOH comms routing gated through Juvy / Dr. Claro / Dr. Paunlagui; Carl is not an authorized DOH-facing sender).
- Formal D2 role assignments, including Carl's written scope as "CAPI development + bench-testing" and Shan Lait's onboarding as QA Tester.
- A requested cadence shift from weekly → bi-monthly status updates to DOH (affects E0-010).
- A COA no-cost-extension clarification item.

Carl was cc'd on the invite but did not attend; attendance roll excluded him.

## Relationship to the 6 open F1 items — resolved category confusion

> [!warning] Prior mental-model error (corrected 2026-04-15)
> Between 2026-04-10 and 2026-04-15 the project operated under the assumption that the Apr 13 LSS meeting would decide the **6 open F1 technical items**: Q63 day-vs-month, SECONDARY_DATA structure, NBB hospital census split, Q31 NA-skip intent, Q166 PD nurses list, Q121 dynamic value set. After reading the actual Apr 13 meeting minutes on Apr 15, this was recognized as a category error. **Those 6 items were never in LSS scope** — they're technical design decisions on instrument logic, which LSS explicitly excludes. Booking them on a future LSS agenda won't work; they need a different forum.

**Correct routing for the 6 items:** a narrowly-scoped **technical design review meeting** (working title: "F1 Design Decision Review") with Dr. Paunlagui and whoever owns the substantive content for each section. Carl requests this as a separate agenda item, not as an extension of LSS.

**Code-side impact:** the 6 items are encoded as `PENDING_DESIGN_*` constants in `deliverables/CSPro/F1/generate_dcf.py` (renamed from `PENDING_LSS_*` on 2026-04-15 to reflect the corrected routing). Flipping any constant + regenerating updates the affected schema.

**Scrum-side impact:** `E2-F1-009b` remains `status::blocked`, but the blocker text is updated — no longer waiting on an LSS, waiting on the convened technical design review.

## Cadence

LSS meetings are **event-driven**, not recurring — called after each tranche resubmission or at Doc Myra's discretion. Distinct from Carl's solo-scrum daily standups and sprint ceremonies.

## Source

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - ASPSI Team Meeting 2026-04-13|Source — ASPSI Team Meeting, 2026-04-13]] (formal minutes + slides from the Apr 13 LSS)
- Scheduling context: Apr 10 email thread summarized in [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/analyses/Analysis - Project Intelligence Brief|Analysis - Project Intelligence Brief]]
