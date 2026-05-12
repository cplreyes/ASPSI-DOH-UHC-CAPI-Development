# F4 Household Listing — Skip Logic and Validations

Source-of-truth for the validation rules and skip patterns that
`F4Listing.ent.apc` implements. Parallel to `F1-Skip-Logic-and-
Validations.md`, `F3-Listing-Skip-Logic-and-Validations.md`,
`F3-Skip-Logic-and-Validations.md`, `F4-Skip-Logic-and-Validations.md`.

> Pattern: patch this spec first when a rule changes, then regenerate
> the APC via `python generate_apc.py`. Do NOT hand-edit
> `F4Listing.ent.apc` directly.

## 1. Required-and-protected fields

These are populated by APC preproc — operator never touches them:

| Field | Source | When set |
|---|---|---|
| `SURVEY_CODE` | literal `"F4L"` | `REC_LISTING_CONTROL.preproc` |
| `ENUMERATOR_ID` | `loadsetting("login_id")` | Phase 2 menu-driven (currently operator-entered) |
| `SUPERVISOR_ID` | `loadsetting("supervisor_id")` | Phase 2 menu-driven (currently operator-entered) |
| `BARANGAY_CODE` | `loadsetting("login_brgy_code")` | Phase 2 menu-driven (currently operator-entered) |
| `FRAME_TARGET` | `loadsetting("frame_target")` | Phase 2 menu-driven (currently operator-entered) |
| `REPLACEMENT_RESERVES` default | `DEFAULT_REPLACEMENT_RESERVES = 10` | `REC_LISTING_CONTROL.preproc` |
| `LISTED_COUNT` / `REFUSED_COUNT` / `EXCLUDED_COUNT` | bumped by APC | `HH_ELIGIBLE.postproc` |
| `LISTING_NO` | `totocc(REC_LISTING_BRGY_FRAME)` | `REC_LISTING_BRGY_FRAME.preproc` |
| `F4_STATUS` default | `0` (Pending) | `REC_LISTING_BRGY_FRAME.preproc` |
| `FROM_RESERVE_POOL` default | `2` (No) | `REC_LISTING_BRGY_FRAME.preproc` |
| `TIME_SESSION_END` | `SYSTIME("HHMMSS")` | `SESSION_STATUS.postproc` (on close) |

## 2. LISTING_SOURCE hybrid model (Q1)

Carl's 2026-05-12 sign-off — `LISTING_SOURCE` field on
`REC_LISTING_CONTROL` distinguishes the two field paths:

- `LISTING_SOURCE = 1` — Captain-supplied list (primary). Crew receives
  a pre-existing household list from the barangay captain. Faster;
  expected default.
- `LISTING_SOURCE = 2` — Fresh door-to-door (fallback). Crew walks the
  barangay and enumerates households on the spot.

Same `REC_LISTING_BRGY_FRAME` schema either way — only the data source
differs. The downstream F4 consumer cannot tell which path was used (and
should not need to).

### Soft warnmsg cross-check (`LISTING_SOURCE.postproc`)

If `LISTING_SOURCE = 1` AND `FRAME_NOTES` contains text matching:

- `captain refused`
- `refused to share`
- `list missing`
- `no captain list`
- `captain unavail` (matches `unavailable`, `unavailability`, etc.)

then a `warnmsg` fires:

> "LISTING_SOURCE is set to 1 (captain-supplied) but FRAME_NOTES
> mentions captain refused / list missing. Confirm: should this be
> LISTING_SOURCE = 2 (fresh door-to-door)? Press Enter to keep current
> value, or go back and change."

Soft — operator may continue with the original value if there is
context the heuristic missed. Implemented via
`ContainsRefusalMarker(string notes)` helper at PROC GLOBAL.

## 3. Replacement reserves (Q2)

`REPLACEMENT_RESERVES` defaults to `10` (per `DEFAULT_REPLACEMENT_RESERVES`
in `PROC GLOBAL`). Rows beyond `FRAME_TARGET` are drawn from the reserve
pool and flagged via `REC_LISTING_BRGY_FRAME.FROM_RESERVE_POOL = 1`.

**Supervisor dashboard enforces** the Annex D 5–10% replacement-rate
cap — NOT CSPro. CSPro just tags the rows so the dashboard can compute
the rate.

## 4. Validations

| Item | Rule | Failure message |
|---|---|---|
| `FRAME_TARGET` | `>= 1 and <= 999` | "Frame target must be between 1 and 999." |
| `REPLACEMENT_RESERVES` | `>= 0 and <= 99` | "Replacement reserves must be 0-99 (project default 10)." |
| `BARANGAY_CODE` | `>= 1000000000 and <= 9999999999` (10-digit PSGC) | "Barangay code must be a 10-digit PSGC value." |
| `MOBILE` | regex `^09\d{9}$` OR empty | "Mobile must be a Philippine number (09xxxxxxxxx) or blank." |
| `LISTING_SOURCE` | `in {1, 2}` | "Listing source must be 1 (captain-supplied) or 2 (fresh door-to-door)." |

Validations not yet wired in the .apc — they land as `onfocus` /
`postproc` checks in a follow-up commit (the smoke-test commit, this
one, is intentionally tight). Tracking under E2-F4LIST-005.

## 5. Sync behavior

- `SESSION_STATUS.postproc` calls `synchronize_file(remotePath)` when
  the operator transitions `SESSION_STATUS` out of 1 (In progress).
- `remotePath = f4_listing/<env>/<RR><PP><MMM><FF>/<YYYYMMDD>/<BARANGAY10>/<SSS>.csdb`.
- BARANGAY10 path segment derived from `REC_LISTING_CONTROL.BARANGAY_CODE`
  (a regular data item — NOT part of the session ID block per Q3).
- Failure surfaces an `errmsg` and leaves the case saved locally. The
  retry path is `Synchronize → Send data` from the CSPro Android menu
  (native sync UI).

## 6. Cross-instrument linkage

The listing app issues no F4 CASE_SEQ. F4 entry app (`115_F4`) consumes
`F4LISTING_DICT` via the EXTERNAL dictionary declared at commit
`d8a511a` and stamps `ASSIGNED_F4_CASE_SEQ` back into the chosen
roster occurrence (commit 12 of THIS build activates the handshake).

- F4 consumes rows with `F4_STATUS = 0` (pending — not yet attempted).
- F4 preproc calls `PickHousehold()` (formerly stubbed); the function
  walks `forcase F4LISTING_DICT` filtered by the F4 crew's login
  facility-tier prefix.
- After consumption, F4 stamps `F4_STATUS = 2` (In progress) and
  `ASSIGNED_F4_CASE_SEQ`. On completion, F4 stamps `F4_STATUS = 1`. On
  refusal, F4 stamps `F4_STATUS = 3` and the case takes a slot in the
  `CASE_SEQ_REFUSED_RANGE = 900..999` partition.

## 7. Auto-tag — NOT applicable

Unlike 110_F3_listing, the F4 listing app does NOT compute a
`LISTING_TAG`. Every listed household in the barangay frame is F4-
eligible by definition; the F4 entry app filters by `F4_STATUS = 0`
(pending), not by any tag value.

This is the structural reason `REC_LISTING_BRGY_FRAME` has no
`LISTING_TAG` item and `PROC GLOBAL` has no `ComputeListingTag` /
`TAG*_THRESHOLD_KM` constants — there is no decision to make at listing
time.

## 8. Seed-PRNG inputs (Q8)

`SeedSessionPRNG()` derives the per-session seed from four inputs:

```
seed_source = (ENUMERATOR_ID * 1e8) + DATE_SESSION + TIME_SESSION_START
              + (BARANGAY_CODE * 1e4)
session_seed = seed_source mod (2^32 - 1)
seed(session_seed)
```

Seed inputs vs F3 listing: F3 omits BARANGAY (one facility-day per
session); F4 includes it so two crews at the same facility-tier on the
same date in different barangays get distinct seed streams.

`g_session_seed` is captured in PROC GLOBAL state. Snapshot for audit
trail is NOT written to any DCF item (no `RI_SEED_USED` analog in F4
listing — no per-event log record exists).

## 9. Smoke-test pass

Defined in `tests/unit/test_f4_listing_smoke.py` (commit 8). Asserts:

1. `python build_all.py --env=dev --only=F4LIST` runs to completion.
2. `F4Listing.dcf` parses as JSON and has 4 records (root + control +
   roster + GPS), 35 record items (excluding the 6-item listing-session
   ID block).
3. `F4Listing.fmf` is BOM-prefixed and contains 5 `[Form]` blocks (1
   IDS + 4 record forms).
4. `F4Listing.ent.apc` contains:
   - `function SeedSessionPRNG`
   - `function ContainsRefusalMarker`
   - `function IncrementSessionCounter`
   - `synchronize_file(remotePath)`
   - `DEFAULT_REPLACEMENT_RESERVES = 10`
5. `F4Listing.ent` has `userSettings.csweb_url = "PLACEHOLDER"` in the
   committed copy (not the per-build env-spliced variant).
6. APC has NO `ComputeListingTag` / `TAG1_THRESHOLD_KM` / cadence-engine
   references (those belong to F3 listing only).

## 10. Open spec items (deferred — Myra edit-pass pending)

Per `feedback_defer_clarifications_during_upstream_review.md`, no
parallel clarification emails are sent for these. Documented here for
the desk reviewer:

- **Protocol V2 line 1199-1201 `{.mark}`** — fresh vs existing listing
  question. The hybrid `LISTING_SOURCE` model in this build is the
  build-time resolution. Myra's pass may collapse to one mode (which
  becomes a value-set restriction on `LISTING_SOURCE`, not a schema
  change).
- **No Annex F4b** — this build is the de facto F4 listing spec until
  Myra reviews. The F3 listing has an Annex F3b precedent; the F4
  analog is forward-referenced but not yet authored.
- **Annex D 5-10% replacement-rate cap** — supervisor dashboard
  enforces, not CSPro. CSPro tags rows via `FROM_RESERVE_POOL` so the
  dashboard can compute the rate.
- **Eligibility verification at listing time** — handled at F4 visit
  consent, not listing. The `HH_ELIGIBLE` item on
  `REC_LISTING_BRGY_FRAME` is a "did the listing crew see anything
  obvious to disqualify" cheap-check, not a substitute for the F4
  consent gate.
