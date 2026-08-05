# GPS Capture Placement — move GPS after the verification photo (F1/F3/F4)

**Date:** 2026-07-16
**Status:** Approved (Option A — move only; ship during the live pretest)
**Issue:** #157 (Facility GPS) · raised from the live pretest (`from-pretest-2026-07`, Los Baños & Bay, opened 2026-07-15)
**Diagram:** `docs/diagrams/2026-07-16-gps-placement.excalidraw` (+ `.png`)

## Problem

Field teams report they "cannot proceed" with Facility Head (F1) and Patient (F3) interviews because there is no GPS signal inside hospitals. They asked for GPS to be moved to the end of the survey.

The actual mechanism is narrower than "blocked":

- `shared/Capture-Helpers.apc:42` → `ReadGPSReading(120, 20)` calls `gps(read, maxTimeSec=120, desiredAccuracyM=20)`, which is **synchronous**. Indoors with no fix it stalls for a full **120 seconds**, then raises `errmsg` and leaves the GPS fields blank.
- It is **not a hard block** — no retry loop, no required-field trap, no bounding-box check. The enumerator can dismiss the error and continue. But the tablet appears frozen, so the field reads it as blocked.
- It fires **early, on a pre-consent form**, from an `onfocus` on the first GPS field:

| Instrument | GPS form(s) | Sits before |
|---|---|---|
| F1 FacilityHeadSurvey | `FORM002` "Facility GPS" (3rd of 13) | consent, Section A |
| F3 PatientSurvey | `FORM003` Facility GPS + `FORM004` Patient Home GPS | `FORM005` Informed Consent |
| F4 HouseholdSurvey | `FORM002` (GPS fused with Geographic ID) | `FORM003` Informed Consent |

For F3 this is up to **2 × 120s per patient, before consent is even asked**. That is the operational bottleneck.

## Decision

Move GPS capture to **after the verification photo** in all three instruments. Because the photo is *already the last form* in every instrument (`FORM012` / `FORM038` / `FORM054`), "after the photo" means **GPS becomes the final form**. This satisfies the field's request exactly.

**Scope: Option A — move only.** No dictionary change. A `GPS_UNAVAILABLE_REASON` code (Option B) is deferred to a follow-up after the pretest window closes.

### Resulting flow (all three converge on one shape)

```
Case Key → Geo ID → [interview sections] → Field Control / Closing → Photo → GPS
```

- **F1**: `FORM002` Facility GPS → after `FORM012` Photo.
- **F3**: `FORM003` Facility GPS **and** `FORM004` Patient Home GPS → both after `FORM038` Photo, in that order.
- **F4**: GPS items split out of the fused `FORM002` "Geographic ID + HH GPS" → new final form after `FORM054` Photo. Geo items 1–6 stay on `FORM002`.

## Why this is safe

**Form order is already decoupled from `.dcf` item order in this codebase.** Precedent: in F4, `FIELD_CONTROL` items 1–9 render on `FORM053` while items 18–20 render on `FORM002` — the form order is the *inverse* of dict order. F1's `REC_FACILITY_CAPTURE` already splits across two forms 10 apart (GPS items 1–6 on `FORM002`, photo items 7–9 on `FORM012`).

Therefore:

- **No `.dcf` item is moved.** No start-position shift, no layout change.
- **No data migration.** Case data binds to dictionary items, not form positions. Synced pretest cases and in-progress partial cases on tablets are unaffected.
- The live data path is `.csdb` (SQLite) per the `.pff` `InputData=` setting; fixed-width `.dat` layout only matters for the external lookup dictionaries, which are untouched.
- The capture-once guard (`if length(strip(*_GPS_READTIME)) = 0`) means cases that already hold a fix will not re-capture.

## Components to change

| Instrument | File | Change |
|---|---|---|
| **F3** | `deliverables/CSPro/F3/generate_fmf.py` | Move the `("Case Verification Photo", …)` / GPS tuples within `FORM_PLAN` (lines 81–173) so both GPS forms follow the photo. |
| **F4** | `deliverables/CSPro/F4/generate_fmf.py` | In `_FORM_PLAN_STATIC` (lines 74–160): filter `HOUSEHOLD_GEO_ID` on `FORM002` to exclude GPS items 7–12; add a new final form entry carrying only those GPS items. |
| **F1** | `deliverables/CSPro/F1/inject_gps_end.py` (**new**) | F1 has **no** `generate_fmf.py` — its `.fmf` is hand-maintained and mutated by an ordered injector pipeline (`fmf_checkbox_convert → inject_blocks → inject_case_key → inject_field_control_end`). Add a post-processor modeled on `inject_field_control_end.py`: move the Facility GPS `[Form]` + `[Group]` blocks after the photo, then re-derive every form ordinal from position (`FORM Name=` and every `Group/Field Form=`). Generator-first, not a hand-edit. |

**Unchanged:** all `.dcf` files; `shared/Capture-Helpers.apc` (`ReadGPSReading` keeps its `120, 20` arguments); the photo gate; the `.apc` GPS capture logic itself.

## Constraints to honor

1. **The photo must stay after Field Control / Closing.** Its `preproc` gates on `ENUM_RESULT_FINAL_VISIT`, so the result must be entered before the camera fires. GPS moving *after* the photo is safe — GPS has no such gate. Per `inject_field_control_end.py:18-21`, the photo was previously required to be the very last form; that invariant is now relaxed to "last *before GPS*", and the comment must be updated to say so.
2. **Do not touch the photo gate value sets** — they differ per instrument (F1 `1,4` · F3 `1,2,4,5` · F4 `1,3`).
3. **`.apc` PROC order must follow the new form order** where the CSPro compiler requires it; the generators emit the `.apc`, so regenerate rather than hand-edit.
4. **Keep the desktop guard** (`getos() in 10:19` → silent skip) intact for desk-test.

## What this does and does not fix

**Fixes:** the interview no longer waits on a satellite fix. The respondent is never held up, and capture moves *after* consent. The enumerator finishes, records the result, takes the photo, walks out, and the GPS acquires outdoors — the natural workflow.

**Does not fix:** the 120-second stall still exists; it is **relocated to case-close**, not removed. If the enumerator stays indoors at the end, it still freezes — but by then the respondent is done. A missing fix still leaves silent blanks with no recorded reason (deferred: Option B).

**Reverses a prior decision, deliberately:** `F4/generate_fmf.py:152-154` documents the 2026-06-12 intent — *"HH GPS stays early so it auto-locks while the form is worked."* Indoors that assumption never held. Update the comment to record the reversal and why.

## Verification

1. **Static gates** — regenerate F1/F3/F4; confirm form ordinals are contiguous and re-derived; confirm no `.dcf` diff.
2. **Compile gate** — fresh disposable CSPro Designer open + compile per `cspro-compile-validate`, all three instruments.
3. **Device check** — confirm on-device that GPS is the final form and that the interview runs start-to-finish with no pre-consent stall.
4. **Data check** — open a previously synced case and confirm it still renders (no layout regression).

## Rollout risk (the real hazard)

The code change is low-risk; **propagation is not**. Per `reference_csentry_update_propagation`, CSEntry's "Update Installed Applications" is known to miss CSWeb redeploys. Enumerators can silently keep running the old form order and we would wrongly believe it shipped.

Mitigation: after deploy, require an explicit re-install/verification step, confirm the running version on at least one field tablet before declaring it live, and send a clear instruction to the field team via the per-instrument Slack channel.

## Follow-ups (not in this change)

- **`GPS_UNAVAILABLE_REASON`** (Option B) — adds a dict item; land after the pretest window closes. Distinguishes "no signal indoors" / "enumerator skipped" / "hardware or permission off". Today the Map Report counts these all as `nofix` with no reason.
- **Stale validation docs** — `F1/F1-Skip-Logic-and-Validations.md:171-179` (and F3/F4 equivalents) document a `FACILITY_CAPTURE_GPS` trigger button removed on 2026-06-12 and HARD bounding-box checks (`[4.5, 21.5]` / `[116.5, 127.0]`) that **do not exist in the generated code**. Correct or delete.
- **F3 `P_HOME_GPS`** — if captured while standing in the facility it records the facility's coordinates, not the patient's home, which would make the map-gen `displacement` QA flag meaningless. Worth its own review.
- **`facility_lookup` has no coordinates** — so there is no reference point to validate a captured fix against, and no fallback pre-fill. The map-gen cluster-outlier check compensates self-referentially (needs `CLUSTER_MIN = 3` cases). Consider sourcing facility coordinates.
