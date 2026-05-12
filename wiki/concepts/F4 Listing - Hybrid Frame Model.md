---
type: concept
tags: [capi, cspro, f4, listing, survey-design, protocol-resolution]
source_count: 2
---

# F4 Listing - Hybrid Frame Model

Build-time resolution of the F4 household-listing protocol question raised by [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/2026-05-06-survey-manual-bundle/2026-05-06_Survey-Manual-Working-File-Kidd.docx]] **Protocol V2 line 1199–1201** (a `{.mark}` annotation flagging that the Survey Manual hasn't yet committed to a frame-construction method for the F4 household sample).

The CAPI build cannot wait for Myra's pending edit pass on the Survey Manual to resolve the `{.mark}` — F4 listing fieldwork starts before that pass concludes. Carl's 2026-05-12 design sign-off adopts a **hybrid frame model** that supports both candidate methods within the same CSPro app and the same DCF schema. When Myra's pass resolves the question, the implementation can collapse to a single mode via a value-set restriction on `LISTING_SOURCE` — no schema migration required.

> [!note] Status
> Adopted 2026-05-12 as the working build-time decision for the 113_F4_listing CAPI app. CAPI carries this until Myra's pass resolves the Protocol V2 line 1199–1201 question, after which the implementation may be narrowed.

## The two candidate methods

| Method | Description | Speed | Coverage risk |
|---|---|---|---|
| **Captain-supplied list** | The crew receives a pre-existing barangay household list from the barangay captain and enumerates from it. | Fast — list already exists | Coverage gaps if captain's list is stale or excludes informal settlements. |
| **Fresh door-to-door** | The crew walks the barangay and enumerates households on the spot. | Slow — full canvass | Lower coverage risk; matches the gold-standard sampling-frame methodology. |

## The hybrid resolution

`REC_LISTING_CONTROL.LISTING_SOURCE` is a length-1 numeric with value set:

| Code | Label | Path |
|---|---|---|
| 1 | Captain-supplied list (primary path) | Captain provides list; crew works through it. |
| 2 | Fresh door-to-door enumeration (captain list missing) | Captain list refused / missing / stale; crew falls back to door-to-door. |
| 9 | Not applicable | (reserved; project-wide NA-at-highest-value convention) |

**Operational rule** — the crew defaults to LISTING_SOURCE = 1 (captain's list is faster). They fall back to LISTING_SOURCE = 2 if any of the following occur on arrival at the barangay:

- Barangay captain is unavailable.
- Barangay captain refuses to share the list.
- The list is stale (e.g., LGU has not updated it in >12 months).
- The list materially under-counts households (visible informal-settlement gap).

Both paths populate the same `REC_LISTING_BRGY_FRAME` roster record — identical item set, identical downstream handshake. The F4 entry app (115_F4) cannot tell which path was used (and should not need to).

## Why this resolution works

1. **Both methods produce the same artifact.** The roster is the same shape regardless of how it was filled. Downstream F4 case-key allocation, `forcase`/`loadcase` semantics, and supervisor dashboards are all source-agnostic.

2. **Schema is forward-compatible.** When Myra's edit pass resolves to one method, we restrict the `LISTING_SOURCE` value set to `{1, 9}` or `{2, 9}` — purely a generator change, no DCF migration, no data-loss risk.

3. **Field reality demands both.** Even if the Survey Manual mandates door-to-door, captains will still try to hand crews their existing list (it's hospitable and they want the survey to "go fast"). The hybrid model encodes the operational truth: the crew has to know what to do when the captain insists on supplying a list.

4. **Audit signal is preserved.** Desk reviewers can compute the captain-supplied vs door-to-door ratio per region/province from `LISTING_SOURCE`, surfacing patterns that inform Year 3 protocol refinement.

## Implementation

Encoded in `[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/UHC-Survey-System/113_F4_listing/]]` — see `generate_dcf.py` (`build_listing_control()` includes `LISTING_SOURCE`) and `generate_apc.py` (`PROC LISTING_SOURCE` adds a soft warnmsg cross-check).

### Soft warnmsg cross-check

`F4Listing.ent.apc` `PROC LISTING_SOURCE` postproc fires a soft `warnmsg` if the operator marks `LISTING_SOURCE = 1` (captain-supplied) but `FRAME_NOTES` contains text suggesting the captain refused or the list was missing:

```
"LISTING_SOURCE is set to 1 (captain-supplied) but FRAME_NOTES
 mentions captain refused / list missing. Confirm: should this be
 LISTING_SOURCE = 2 (fresh door-to-door)?"
```

The match is a case-insensitive substring check against five phrases:
- `captain refused`
- `refused to share`
- `list missing`
- `no captain list`
- `captain unavail` (catches `unavailable`, `unavailability`)

`warnmsg` is non-blocking — the operator may continue with the original value if they have context the heuristic missed. Implementation: `ContainsRefusalMarker(string notes)` helper at `PROC GLOBAL`.

## Carl's Q1–Q8 design decisions encoded by this build

The hybrid frame model is decision **Q1** of an 8-decision design sign-off (2026-05-12) that shaped 113_F4_listing in its entirety:

| # | Decision | Pick | Encoding |
|---|---|---|---|
| Q1 | Frame source | **Hybrid** | This concept page. `LISTING_SOURCE` field + soft warnmsg. |
| Q2 | Replacement reserves | 10 | `DEFAULT_REPLACEMENT_RESERVES = 10` in `PROC GLOBAL`; `REC_LISTING_CONTROL.REPLACEMENT_RESERVES` defaults to 10 if 0 at preproc. |
| Q3 | Session ID block | Reuse F3 listing's 20-digit shape | `build_listing_id_block()` from `shared/cspro_helpers.py` reused unchanged; `BARANGAY_CODE` lives on `REC_LISTING_CONTROL` as a regular data item; sync path encodes `<barangay10>` as a separate path segment. |
| Q4 | Frame cap | 999 occurrences | `REC_LISTING_BRGY_FRAME.max_occurs = 999`. |
| Q5 | Phone capture | Optional, alpha-11 | `MOBILE` alpha-11 on `REC_LISTING_BRGY_FRAME`, blank-permitted. |
| Q6 | Verification capture | GPS only — no photo | `REC_LISTING_BARANGAY_GPS` record present; no photo record. |
| Q7 | Menu label | "F4 Household Listing" | Will land in Phase 2 menu rebuild. |
| Q8 | Seed inputs | ENUMERATOR_ID + DATE_SESSION + TIME_SESSION_START + BARANGAY_CODE | `SeedSessionPRNG()` signature widened vs F3-listing (which has no barangay dimension). |

## Open items deferred to Myra's edit pass

Documented in `[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/UHC-Survey-System/113_F4_listing/F4-Listing-Skip-Logic-and-Validations.md]]` §10. No parallel clarification emails sent per [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Forward-Only Sign-Off]] / feedback memory `feedback_defer_clarifications_during_upstream_review.md`:

- Protocol V2 line 1199–1201 `{.mark}` is the question this concept page resolves at build time.
- There is no Annex F4b — Year 1 had no F4 listing protocol annex; this build is the de facto F4 listing spec until Myra reviews.
- The Annex D 5–10% replacement-rate cap is enforced by the supervisor dashboard, NOT CSPro (CSPro tags rows via `FROM_RESERVE_POOL` so the dashboard can compute the rate).
- Eligibility verification at listing time is intentionally cheap (`HH_ELIGIBLE` is a "anything obviously disqualifying" check) — the canonical eligibility gate runs at F4 visit consent, not at listing.

## Cross-references

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Questionnaire Numbering Convention]] — the 20-digit listing-session ID block is the listing-app analog of the 12-digit F-series case ID; both anchor to PSA 1Q 2026 PSGC.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/GPS and Photo Capture]] — explains why F4 listing has only GPS audit (Q6) while F1/F3/F4 questionnaire instruments have both GPS and photo.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Forward-Only Sign-Off]] — the governance pattern that allows this hybrid resolution to land without a parallel clarification email to Kidd / Myra.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - DOH UHC Year 2 Survey Manual]] — Apr 28 ASPSI manual that the May 6 Working File supersedes; line numbers in §3.4 differ between the two versions.

(Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/2026-05-06-survey-manual-bundle/2026-05-06_Survey-Manual-Working-File-Kidd.docx]])
