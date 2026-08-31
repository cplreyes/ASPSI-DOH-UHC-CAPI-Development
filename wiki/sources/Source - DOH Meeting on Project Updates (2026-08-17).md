---
type: source-summary
source: "Read.ai meeting report, Gmail — \"ASPSI DOH UHC Survey Yr2; Meeting with DOH, Project Updates\", 2026-08-17 (report shared by Theo Demaisip)"
date_ingested: 2026-08-25
tags: [meeting, doh, psa, ethics, questionnaire, f1-facility, f2-hcw, f3-patient, f4-household, capi-update-pending]
---

# Source - DOH Meeting on Project Updates (2026-08-17)

**Provenance and reliability.** This is an **AI-generated meeting recap** (Read.ai), not minutes taken by
a participant and not a document ASPSI issued. It was ingested from Gmail on 2026-08-25 because no local
record of this meeting existed. **Treat every item below as a lead to confirm, not as an instruction** —
attribution and wording in automated recaps are unreliable. Nothing here has been actioned in the CAPI.

## Status reported

Ethics approval secured from SJREB (pending final notice) · **PSA clearance obtained** · pre-test completed
2026-07-24 · translated tools submitted · training designs and slide decks submitted 2026-07-30.

**The gate:** DOH concurrence on the major revisions was required *before* the revised survey tools could be
submitted. Lindsley Jeremiah was to walk Director Nakunan through the revised facility-head questions for
that concurrence.

## Action items as recorded

| # | Item | Owner as recorded |
|---|---|---|
| 1 | Submit responses + revised project documents **after** DOH concurrence on major revisions | ASPSI team |
| 2 | Submit the completed **PSA revisions within the week** | ASPSI team |
| 3 | Conduct **training of trainers before field-enumerator training** | ASPSI team |
| 4 | Remove the **"Not yet implemented but planned"** response option where not applicable, **particularly for financing-related items** | Myra Silva-Javier |
| 5 | Provide revised survey tools incorporating the approved facility-head changes | Myra Silva-Javier |
| 6 | Explain revised facility-head questions to Director Nakunan for concurrence | Lindsley Jeremiah |
| 7 | **Revise routing instructions and automate "not applicable" handling** for affected questions | survey team |
| 8 | Submit **specific quality measures** for the HCW and facility-head questionnaires | participant |
| 9 | Incorporate approved methodological changes into the HCW questionnaire | participant |
| 10 | Document each facility's **outpatient queuing system** in facility reporting | field supervisors |
| 11 | **Revise Q18 and remove Q29** from the **patient** questionnaire (F3) | participant |
| 12 | Apply the **income-classification revision** and **remove Q29** from the **household** survey (F4) | participant |

## What this explains, and what it leaves open

**Item 8 is almost certainly the origin of the 2026-08-24 tickets** — #1311 (F1 Q35.2 quality measures,
closed, shipped as F1 v4.0.0) and #1312 (F2 Q24.2, still open). Both were filed as "adopt DOH's final
option list", which is item 8 arriving as a concrete list five weeks later.

> [!warning] Item 4 needs Carl's judgment — the mechanism exists but its scope may not match
> `F1/generate_dcf.py` already carries a **`UHC_ATTRIB_NOPLAN`** 5-option variant that drops
> *"Not yet implemented but planned within the next 1-2 years"* — but it is applied to **Q27.1/Q28.1/Q29.1
> only**, on the reasoning that the option "reads oddly against a policy the facility either applies or
> doesn't". DOH's phrasing singles out **financing-related items**. The option still appears **125 times**
> in the shipped `FacilityHeadSurvey.dcf`. So either the financing items are already covered by that trio,
> or DOH is asking for the NOPLAN variant to be extended. **Unresolved — do not change without confirming
> which questions DOH means.**

**Items 11 and 12 may already be absorbed.** The Aug-17 instrument migration renumbered F3 and F4, and the
generators note the paper-colliding "29." display prefix was dropped because Q29 became a different question.
Whether that satisfies "remove Q29" or is a separate outstanding change is **not determinable from this
recap** — it needs the Aug-17 PAPI or ASPSI confirmation. F4's "income-classification revision" plausibly
corresponds to the parked **F4 Q18 brackets** decision.

Related: [[Source - Updated Survey Instruments (2026-08-17)]] (the instruments themselves, ingested 08-18) · [[Source - ASPSI Team Meeting (2026-08-11)]] · [[Source - ASPSI Subs Zoom Meeting (2026-08-14)]] — the three recovered together on 2026-08-25 from Gmail, none of which had a local record.
