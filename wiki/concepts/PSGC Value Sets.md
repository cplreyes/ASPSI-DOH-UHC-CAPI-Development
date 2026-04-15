---
type: concept
tags: [cspro, dcf, value-sets, psgc, geography, blocker, conventions]
source_count: 0
---

# PSGC Value Sets

**PSGC** = Philippine Standard Geographic Code, the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/PSA|PSA]]'s authoritative geographic code list covering Region → Province → City/Municipality → Barangay. Every F-series CAPI instrument needs PSGC value sets for the geographic identification fields on the cover/FIELD_CONTROL block.

## Items affected

In F1's `FacilityHeadSurvey.dcf` (the template for F2/F3/F4):

- `REGION` — 1-level code
- `PROVINCE_HUC` — province or HUC (Highly Urbanized City) code
- `CITY_MUNICIPALITY` — city/municipality code
- `BARANGAY` — barangay code

F2/F3/F4 inherit the same four items and the same blocker.

## Blocker

As of 2026-04-15, ASPSI has not delivered the PSGC code lists. `generate_dcf.py` marks the four items as **plain numerics without value sets** so the DCF still loads in CSPro Designer — the items are live but don't have drop-downs or validation yet. When ASPSI delivers the lists:

1. Drop them into the generator as new value-set constants.
2. Wire them into the four items.
3. Regenerate — no other schema changes required.

Until then, these items are **ASPSI-blocked**, not design-blocked (distinct from the six `PENDING_DESIGN_*` F1 questions that await a Leadership decision on schema shape).

## F2 parallel

[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F2 Google Forms Track|F2 Google Forms Track]] takes a different approach: rather than shipping PSGC as drop-downs, the F2 design **absorbs geographic fields into a `FacilityMasterList` Sheet** that prefills facility-linked metadata (region, province, city_mun, barangay) via per-facility prefilled URLs (`Links.generateLinks()`). This sidesteps the PSGC dropdown problem for F2 — but the underlying blocker (ASPSI must produce the facility master list) is the same shape of dependency.

## Memory

- `memory/project_aspsi_psgc_value_sets.md` — ASPSI ask + F2–F4 inheritance note.

## Related

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F-Series Value Set Conventions|F-Series Value Set Conventions]] — project-internal coding rules for NA codes + value-set shape.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Data Dictionary|CSPro Data Dictionary]] — how value sets attach to items in `.dcf`.
