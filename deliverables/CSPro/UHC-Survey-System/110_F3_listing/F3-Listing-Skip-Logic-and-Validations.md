# F3 Patient Listing — Skip Logic and Validations

Source-of-truth for the validation rules and skip patterns that
PatientListing.ent.apc implements. Parallel to F1-Skip-Logic-and-
Validations.md / F3-Skip-Logic-and-Validations.md in 107_F1 / 111_F3.

> Pattern: patch this spec first when a rule changes, then regenerate
> the APC via `python generate_apc.py`. Do NOT hand-edit
> PatientListing.ent.apc directly. (For now the .apc is hand-written
> inside the generator template; once we exceed ~500 lines we'll lift
> it into a logic-builder pattern like F1 has.)

## 1. Required-and-protected fields

These are populated by APC preproc — operator never touches them:

| Field | Source | When set |
|---|---|---|
| `SURVEY_CODE` | literal "F3L" | `REC_LISTING_CONTROL.preproc` |
| `ENUMERATOR_ID` | `loadsetting("login_id")` | Phase 2 menu-driven (currently operator-entered) |
| `SUPERVISOR_ID` | `loadsetting("supervisor_id")` | Phase 2 menu-driven (currently operator-entered) |
| `FACILITY_TARGET` | `loadsetting("facility_target")` | Phase 2 menu-driven (currently operator-entered) |
| `CADENCE_MIN_MIN` | `loadsetting("cadence_min_min")` | Phase 2 menu-driven |
| `CADENCE_MAX_MIN` | `loadsetting("cadence_max_min")` | Phase 2 menu-driven |
| `BACKUP_TARGET` | `ComputeBackupTarget(FACILITY_TARGET)` | `FACILITY_TARGET.onfocus` |
| `LISTED_COUNT` / `REFUSED_COUNT` / `EXCLUDED_COUNT` | bumped by APC | `RI_OUTCOME.postproc` |
| `RI_CYCLE_NO` | `NextCycle()` | `REC_RANDOM_INTERVAL_LOG.preproc` |
| `RI_SEED_USED` | `g_session_seed` | `REC_RANDOM_INTERVAL_LOG.preproc` |
| `RI_INTERVAL_SEC` | `DrawRandomInterval(...)` | `RI_INTERVAL_SEC.onfocus` |
| `ROSTER_SEQ` | `totocc(REC_PATIENT_ROSTER)` | `REC_PATIENT_ROSTER.preproc` |
| `LISTING_TAG` | `ComputeListingTag(CONTACT_VERIFIED, DISTANCE_TO_HOME_KM)` | `CONTACT_VERIFIED.postproc` |
| `F3_STATUS` / `F4_STATUS` defaults | 0 (Pending) | `REC_PATIENT_ROSTER.preproc` |

## 2. Auto-tag rule (PENDING_DESIGN — Candidate A)

The auto-tag PROC `ComputeListingTag()` returns 1, 2, or 3 per
Candidate A — Distance-gated:

```
if CONTACT_VERIFIED <> 1                          -> 3 (ineligible)
elseif DISTANCE_TO_HOME_KM <= TAG1_THRESHOLD_KM   -> 1 (F3 exit, same-day at facility)
elseif DISTANCE_TO_HOME_KM <= TAG2_THRESHOLD_KM   -> 2 (F4 home visit)
else                                              -> 3 (ineligible — outside catchment)
```

Thresholds (named constants in `PROC GLOBAL`):
- `TAG1_THRESHOLD_KM = 2.0`
- `TAG2_THRESHOLD_KM = 15.0`

Marked `PENDING_DESIGN_AUTO_TAG_RULE` — Myra's §3a edit pass can tune
these constants without changing DCF / FMF / downstream F3 / F4.
Reference: `wiki/sources/Source - Survey Manual 2026-05-06 - Section 3a.md`.

Side effects on tag assignment:
- Tag 1 → `F4_STATUS = 9` (F4 won't run for this patient).
- Tag 3 → `F3_STATUS = 9` AND `F4_STATUS = 9` (neither will run).

## 3. Random-interval cadence engine

Per cycle the engine:

1. `preproc REC_RANDOM_INTERVAL_LOG` — increment `g_cycle_no`, snapshot seed.
2. `onfocus RI_INTERVAL_SEC` — draw a random interval in
   `[max(CADENCE_MIN_MIN*60, CADENCE_HARD_MIN_SEC),
     min(CADENCE_MAX_MIN*60, CADENCE_HARD_MAX_SEC)]`.
3. Operator waits, lists a patient (or doesn't), confirms `RI_OUTCOME`.
4. `postproc RI_OUTCOME` — bump session counter that matches the outcome.
   Outcome 4 (timeout) bumps nothing.

Hard clamps (refuses to leave even if config says otherwise):
- `CADENCE_HARD_MIN_SEC = 60`
- `CADENCE_HARD_MAX_SEC = 14400`

Determinism: same `(ENUMERATOR_ID, DATE_SESSION, TIME_SESSION_START)` →
same interval sequence. Intentional for desk-audit replay.

## 4. Validations

| Item | Rule | Failure message |
|---|---|---|
| `FACILITY_TARGET` | `>= 1 and <= 999` | "Facility target must be between 1 and 999." |
| `CADENCE_MIN_MIN` | `>= 1 and < CADENCE_MAX_MIN` | "Cadence minimum must be ≥1 minute and less than the maximum." |
| `CADENCE_MAX_MIN` | `> CADENCE_MIN_MIN and <= 240` | "Cadence maximum must exceed the minimum and not exceed 240 minutes." |
| `P_AGE` | `>= 0 and <= 130` | "Patient age must be 0–130 years." |
| `DISTANCE_TO_HOME_KM` | `>= 0.0 and <= 99.9` | "Distance must be 0.0–99.9 km. Beyond 99.9 km the patient is ineligible — set CONTACT_VERIFIED=2." |
| `P_MOBILE` | regex `^09\d{9}$` OR empty | "Mobile must be a Philippine number (09xxxxxxxxx) or blank." |
| `RI_INTERVAL_SEC` | within hard clamps | (validated in `DrawRandomInterval`; never user-entered) |

Validations not yet wired in the .apc — they land as `onfocus` /
`postproc` checks in a follow-up commit (the smoke-test commit, this
one, is intentionally tight). Tracking under E2-F3LIST-005.

## 5. Sync behavior

- `SESSION_STATUS.postproc` calls `synchronize_file(remotePath)` when
  the operator transitions `SESSION_STATUS` out of 1 (In progress).
- `remotePath = patient_listing/<env>/<RR><PP><MMM><FF>/<YYYYMMDD>/<SSS>.csdb`.
- Failure surfaces an `errmsg` and leaves the case saved locally.
  The retry path is `Synchronize → Send data` from the CSPro Android
  menu (native sync UI).

## 6. Cross-instrument linkage

The listing app issues no F-series CASE_SEQ values. F3 / F4 entry apps
consume `PATIENTLISTING_DICT` via EXTERNAL dictionary at interview
time and stamp `ASSIGNED_F3_CASE_SEQ` / `ASSIGNED_F4_CASE_SEQ` back
into the roster occurrence.

- F3 consumes rows with `LISTING_TAG = 1 AND F3_STATUS = 0` (today's
  same-day exit interview queue). After consumption, F3.preproc sets
  `F3_STATUS = 2` (In progress) and stamps `ASSIGNED_F3_CASE_SEQ`.
  On exit-survey completion, F3.postproc sets `F3_STATUS = 1`.
- F4 consumes rows with `LISTING_TAG = 2 AND F4_STATUS = 0` (home-visit
  queue). Same status-transition model.

Refused-at-F3 rows (`F3_STATUS = 3`) consume F-series CASE_SEQ from
the 900-999 refused range (per `shared/cspro_helpers.py::CASE_SEQ_REFUSED_RANGE`).
Refused-at-listing rows (`RI_OUTCOME = 2` at the cadence-engine layer)
produce NO roster occurrence — they cost 0 CASE_SEQ slots.

## 7. Smoke-test pass

Defined in `tests/smoke_f3_listing.py` (commit 11). Asserts:

1. `python build_all.py --env=dev --only=F3LIST` runs to completion.
2. `PatientListing.dcf` parses as JSON and has 6 records, 69 items
   (excluding the 6-item listing-session ID block).
3. `PatientListing.fmf` is BOM-prefixed and contains 7 `[Form]` blocks
   (1 IDS + 6 record forms).
4. `PatientListing.ent.apc` contains:
   - `function DrawRandomInterval`
   - `function ComputeListingTag`
   - `synchronize_file(remotePath)`
   - `PENDING_DESIGN_AUTO_TAG_RULE` reference.
5. `PatientListing.ent` has `userSettings.csweb_url = "PLACEHOLDER"`
   in the committed copy (not the per-build env-spliced variant).
