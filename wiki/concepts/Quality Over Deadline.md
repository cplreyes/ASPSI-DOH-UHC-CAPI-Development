---
type: concept
tags: [working-convention, quality, deadline, psa, capi]
source_count: 2
---

# Quality Over Deadline

The project's standing working convention: **quality holds over deadlines**. Dates are planning constraints to sequence around — not reasons to cut logic, validation, or Designer work, and not reasons to paper over defects.

## Where the stance is on record

- **Carl's reply to the PSA deadline (2026-05-13).** When Dr. Myra firmed the hard 2026-06-12 PSA date for the CAPI app + 7 translated versions, Carl confirmed alignment while explicitly holding quality: *"timeline allowing sufficient development time without compromising quality."* (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CAPI Translations PSA Deadline (Myra 2026-05-13)]])
- **2026-05-18 stand-up.** Carl explicitly prioritised quality over speed — "though we are delayed na sa schedule, still quality" — alongside the bugs-are-good testing philosophy ("the more bugs/errors/inconsistencies, the better … so we can avoid it before the survey proper"). (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - ASPSI Team Meeting 2026-05-18]])

## How it is applied

- The [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CAPI Seven-Language Translation Build]] treats the 2026-06-12 PSA date as a constraint to sequence around, not a reason to rush: the seven-language build was held to quality rather than rushed to the date. As of 2026-06-12 the gate date has been reached; outcome pending.
- **Root-cause fixes over papering over.** When a blocker or data-integrity bug surfaces, the fix is root-caused rather than shortcut (working preference `feedback_quality_over_shortcut_blockers`).

## Related

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CAPI Seven-Language Translation Build]] — the hardest external date this stance has been tested against
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Forward-Only Sign-Off]] — sibling working convention: drive to a testable artifact; test bugs loop back to source docs
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Team Communication Protocol]] — sibling working convention: formal DOH-facing comms routing
