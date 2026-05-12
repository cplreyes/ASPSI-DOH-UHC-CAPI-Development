# 113_F4_listing — F4 Household Listing CAPI app

CAPI listing instrument used **before** F4 fieldwork to enumerate the
household sampling frame in each assigned barangay. Sibling to
`110_F3_listing` (patient listing for F3); shares the 20-digit session-
scoped case-ID shape and the EXTERNAL-dictionary handshake into the
downstream F4 entry app.

The de facto F4 listing protocol spec until Myra's pending edit pass on
`raw/2026-05-06-survey-manual-bundle/2026-05-06_Survey-Manual-Working-
File-Kidd.docx` resolves the Protocol V2 line 1199-1201 `{.mark}`
(fresh-vs-existing listing question). Build-time resolution per Carl's
2026-05-12 design sign-off:

| # | Decision | Resolved as |
|---|---|---|
| Q1 | Listing source | Hybrid — captain's list primary, door-to-door fallback (LISTING_SOURCE field) |
| Q2 | Replacement reserves | 10 |
| Q3 | ID block shape | Reuse F3 listing's 20-digit shape (per-session SSS preserves uniqueness; BARANGAY_CODE is a data item, encoded as a sync-path segment) |
| Q4 | Frame cap | 999 occurrences |
| Q5 | Phone | Optional, alpha-11 |
| Q6 | Verification capture | GPS only — no photo |
| Q7 | Menu label | "F4 Household Listing" |
| Q8 | Seed inputs | ENUMERATOR_ID + DATE_SESSION + TIME_SESSION_START + BARANGAY_CODE |

## Position in the F-series pipeline

```
  STL allocates barangay assignments per crew (user_roster.xlsx)
        |
        v
  113_F4_listing  ---->  F4LISTING_DICT.csdb  (per barangay-day session)
        |                       |
        |                       +--- F4_STATUS=0 -> F4 home-visit queue
        |                       +--- F4_STATUS=3 -> refused at F4 visit
        |                       |
        v                       v
  Sync to CSWeb          F4 entry app loadcase() on the dictionary
```

The listing app issues no F4 CASE_SEQ itself — it produces the
**barangay-frame roster** that F4 reads at interview time via the
EXTERNAL-dictionary mechanism wired in commit 12 of this build.

## Generator chain

```
generate_dcf.py   ->  F4Listing.dcf
generate_ent.py   ->  F4Listing.ent
generate_fmf.py   ->  F4Listing.fmf  (Designer-owned post-publish)
generate_apc.py   ->  F4Listing.ent.apc  (logic)
```

Run via `python ../build_all.py --env=dev --only=F4LIST` once the entry
is added to the `INSTRUMENTS` list in `build_all.py` (commit 11).

## Listing-session case-ID block

Same shape as 110_F3_listing per Carl's Q3 decision:

```
  RR  PP  MMM  FF  YYYYMMDD  SSS    (20 digits total)
  ^^  ^^  ^^^  ^^  ^^^^^^^^  ^^^
   2   2   3    2      8      3
```

Where SSS is the per-(facility-tier+day) session sequence — increments
when a crew starts a new session even at the same facility-day. Two
barangays/day get SSS=001 and SSS=002 without collision; BARANGAY_CODE
lives on `REC_LISTING_CONTROL` as a regular data item.

Use `shared/cspro_helpers.py::build_listing_id_block()` (same helper
F3 listing uses — explicitly reused per Q3).

## Hybrid frame model (LISTING_SOURCE)

- **LISTING_SOURCE = 1** (captain-supplied, primary path) — the crew
  uses the barangay captain's pre-supplied household list. Fastest;
  expected default.
- **LISTING_SOURCE = 2** (fresh door-to-door, fallback) — the captain
  list is missing or refused; the crew walks the barangay and enumerates
  households on the spot.

`REC_LISTING_BRGY_FRAME` occurrences are identical regardless of source
— same items, same downstream handshake. Difference is only who fills
the roster (captain vs crew).

A soft `warnmsg` triggers if LISTING_SOURCE=1 but FRAME_NOTES contains
text like "captain refused" or "list missing" — operator likely meant
LISTING_SOURCE=2.

## Replacement reserves

Frame-builder pads the FRAME_TARGET by `REPLACEMENT_RESERVES` (default
10 per Q2). Rows drawn from the reserve pool are flagged via
`REC_LISTING_BRGY_FRAME.FROM_RESERVE_POOL = 1`. The supervisor dashboard
enforces the Annex D 5-10% replacement-rate cap — NOT CSPro (CSPro just
tags the rows).

## GPS-only capture

Per Q6 — barangay GPS at session start, no verification photo. Reduces
field-time friction; the captain-list scenario is short enough that
GPS alone is sufficient audit signal.

## Line endings

See `.gitattributes` — Designer-owned binaries (.dcf, .fmf, .ent.apc,
.ent.mgf, .ent.qsf) are pinned CRLF; generator-emitted sources (.py,
.ent, .pff, .md) are pinned LF. Pattern parity with 107_F1, 110_F3_listing,
111_F3, 115_F4.

## Status

Scaffolded 2026-05-12 per commit 1 of 12. Subsequent commits land DCF
records, FMF, ENT, APC, sync plumbing, build_all wiring, F4 stub
activation, and the smoke-test pass.
