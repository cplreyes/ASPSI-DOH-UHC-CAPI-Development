# 113_F4_listing — Sync model

Listing-app data flows differ from the F-series questionnaire sync model
because the listing app's output (`F4LISTING_DICT`) is **read** by the
sibling F4 entry instrument at interview time. The barangay frame
roster needs to be on every F4 enumerator's tablet — not just the
listing crew's tablet that captured it.

Sibling to `110_F3_listing/SYNC.md` — same model, different path
structure (extra `<BARANGAY10>` segment).

## Data flow

```
[Listing crew's tablet]
       |
       |   F4LISTING_DICT (one .csdb per barangay-day session)
       |   contains LISTING_SESSION_DATE + LISTING_SESSION_SEQ as ID,
       |   household roster occurrences inside (REC_LISTING_BRGY_FRAME).
       v
[CSWeb server]
       |   case path:
       |     f4_listing/<env>/<facility-id-prefix>/<YYYYMMDD>/<barangay10>/<seq>.csdb
       v
[F4 enumerator's tablet]
   reads via EXTERNAL DICTIONARY F4LISTING_DICT, loadcase() / forcase()
```

## Path convention (CSWeb)

For each environment (dev / uat / prod), the F4 listing-data path is:

```
f4_listing/<env>/<RR><PP><MMM><FF>/<YYYYMMDD>/<BARANGAY10>/<SSS>.csdb
```

Where:

- `<RR><PP><MMM><FF>` is the 9-character facility-tier prefix derived
  from the listing session ID block (concatenation of REGION_CODE,
  PROVINCE_HUC_CODE, CITY_MUNICIPALITY_CODE, FACILITY_NO).
- `<BARANGAY10>` is the 10-digit PSGC barangay code from
  `REC_LISTING_CONTROL.BARANGAY_CODE` (a regular data item, not part
  of the session ID block — per Carl's Q3 sync-path encoding plan).
- `<SSS>` is the per-(facility+day) session sequence — increments when
  a crew starts a second session even at the same facility-day, so two
  barangays per day become `SSS=001` and `SSS=002` without collision.

The path is constructed in `F4Listing.ent.apc` PROC `SESSION_STATUS`
postproc via the `synchronize_file()` directive — see commit 4.

The `sync_F4_listing_app.pff` parameter file (this directory) documents
the parameterization for the standalone sync helper used when the
listing case .csdb is pushed by an out-of-band tool (e.g., supervisor
laptop after a tablet sync failure).

## .pen artifact

The compiled application bundle for the listing-side sync helper lives at:

```
../109_sync/sync_F4_listing_app.pen   (parallel to sync_F3_listing_app.pen)
```

Compilation is via CSPro Designer's `File -> Publish Entry Application`
(F7) on `sync_F4_listing_app.ent` — same manual SOP as the F-series
publish step documented in `docs/superpowers/runbooks/cspro-publish-
entry-runbook.md`. The `.pen` is committed to the repo; the `.ent` is
not (only the `.pff` parameter file lives here so the Designer-laid
configuration is reproducible).

## Pull side (F4 reading the listing dictionary)

`115_F4/HouseholdSurvey.ent` declares `F4LISTING_DICT` as an EXTERNAL
dictionary (already wired in commit `d8a511a` from the F4 quartet
build):

```json
{"type": "external", "path": "../113_F4_listing/F4Listing.dcf"}
```

The household-pick PROC (`PickHousehold()`) — stubbed in the F4 quartet
build, activated in commit 12 of THIS build — uses `forcase
F4LISTING_DICT` to walk the eligible-household pool and `loadcase()` to
re-open a chosen listing case for the F4_STATUS write-back at case-save
time.

## Sync auth + ownership

Per the project-wide CSWeb sync auth model (same as F3 listing):

- Listing crew's tablet authenticates to CSWeb with their enumerator
  user (provisioned at training).
- The case-ID prefix (9-digit facility tier) gates write access — an
  enumerator can only push cases whose case-ID's facility-tier prefix
  matches their assignment.
- F4 enumerators get read access to all `f4_listing/*` cases by virtue
  of the "all_facilities_read" CSWeb group.

Details of the group membership are in the `csweb` deployment runbook,
not duplicated here.

## Multi-barangay-per-day scenarios

Carl's Q3 reasoning (sync-path-collision concern): two barangays at the
same facility-tier on the same day get distinct `SSS` values via per-
session SSS increment (the 101_login menu app rotates the sequence when
the operator starts a new session). Combined with the explicit
`<BARANGAY10>` path segment, the resulting file paths are:

```
f4_listing/uat/0150123401/20260520/0150123402001/001.csdb   (Brgy 1)
f4_listing/uat/0150123401/20260520/0150123402002/002.csdb   (Brgy 2)
```

This keeps the CSWeb server's filesystem cleanly organized even though
the case key (the 20-digit ID block) doesn't include BARANGAY_CODE.
F4's `forcase F4LISTING_DICT` does NOT filter by barangay in the case-
key sense — it filters at the row level by reading
`REC_LISTING_CONTROL.BARANGAY_CODE` from the loaded case, which is what
the household-pick PROC needs anyway (filter eligible-households by the
F4 crew's current login_brgy_code).
