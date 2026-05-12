---
title: UHC Phase 2 tablet test — F3LIST + F3 + F4LIST + F4 end-to-end
type: runbook
date: 2026-05-12
status: active
applies_to: UHC Survey System Phase 2 (2026-05-12 from-scratch rebuild)
---

# UHC Phase 2 tablet test — F3LIST + F3 + F4LIST + F4 end-to-end

End-to-end verification of the Phase 2 rebuild (2026-05-12): F3 patient survey + 110_F3_listing + F4 household survey + 113_F4_listing. The highest-risk surface is the EXTERNAL DICTIONARY `loadcase`/`savecase` handoff (F3↔listing and F4↔listing) on real CSPro 8.0 Android — verify here before any further build.

## Prereqs

- ✅ Phase 1 tablet bring-up complete per `2026-05-08-tablet-sideload-runbook.md` (CSWeb + Android APK + sync server config + F1 verified).
- ✅ Phase 2 source generation: `python build_all.py --env=uat` clean across all 5 instruments (F1 + F3LIST + F3 + F4LIST + F4). 97/97 unit tests pass.
- ✅ Tablet on same Wi-Fi as laptop; `urls.yaml` LAN IP unchanged.

## Step 1 — Publish the Phase 2 .pen chain

Per `2026-05-08-cspro-publish-entry-runbook.md`. **Order matters** because of EXTERNAL DICTIONARY references — break the order and Designer rejects the publish.

| # | Open in Designer | Produces | Dependency |
|---|---|---|---|
| 1 | `107_F1\FacilityHeadSurvey.ent` | `FacilityHeadSurvey.pen` | none |
| 2 | `110_F3_listing\PatientListing.ent` | `PatientListing.pen` | none (producer) |
| 3 | `111_F3\PatientSurvey.ent` | `PatientSurvey.pen` | reads PATIENTLISTING_DICT (step 2 must exist) |
| 4 | `113_F4_listing\F4Listing.ent` | `F4Listing.pen` | none (producer) |
| 5 | `115_F4\HouseholdSurvey.ent` | `HouseholdSurvey.pen` | reads F4LISTING_DICT (step 4 must exist) |

Sync helpers (custom-sync, separate small apps — F7-publish their `.ent` if it exists; the `.pff` parameter file lives in the listing dir):

- `110_F3_listing\sync_F3_listing_app.pff` → `109_sync\sync_F3_listing_app.pen`
- `113_F4_listing\sync_F4_listing_app.pff` → `109_sync\sync_F4_listing_app.pen`

**If F7 fails on step 3 or 5**: most likely the EXTERNAL DICTIONARY's source `.dcf` was modified after the consumer's `.ent` was generated. Re-run `python build_all.py --env=uat` in dependency order.

## Step 2 — Deploy to CSWeb

Per `reference_csweb_deploy_flow.md` memory: use CSPro Designer's **Deploy Application** wizard (Tools → Deploy Application), not the CSWeb UI Apps tab (read-only).

For each `.pen`: Deploy Application → select `.pen` → upload to CSWeb endpoint. Verify all 5 instruments + 2 sync helpers appear in CSWeb Apps list.

## Step 3 — Pull apps to tablet

On the tablet, CSPro Android → Synchronize → Get applications. Expect 5 entry apps + 2 sync helpers to download.

## Step 4 — Seed the listings (required before F3/F4 testing)

F3 and F4 can't be tested in isolation — they read from listing apps via EXTERNAL DICTIONARY. The listings must run first.

### Step 4a — 110_F3_listing (patient listing)

1. Tap **F3 Patient Listing** on tablet.
2. Set facility (loaded from menu's loadsetting() — auto if you logged in as Test RA Alpha).
3. Run a listing session. Capture 3 test patients to exercise the auto-tag rule (Candidate A — distance-gated):

| Test patient | Inputs | Expected `LISTING_TAG` |
|---|---|---|
| Patient A | `DISTANCE_TO_HOME_KM=1.5`, `CONTACT_VERIFIED=Yes` | **1 = exit-survey** (≤2.0 km + contact verified) |
| Patient B | `DISTANCE_TO_HOME_KM=8.0`, `CONTACT_VERIFIED=Yes` | **2 = household-survey** (>2.0 km, ≤15.0 km) |
| Patient C | `DISTANCE_TO_HOME_KM=3.0`, `CONTACT_VERIFIED=No` | **3 = ineligible** (contact_verified gate fails) |

4. Close session (SESSION_STATUS leaves "In progress") → custom sync push fires automatically.
5. **Verify on CSWeb**: file appears at `patient_listing/<env>/<RR><PP><MMM><FF>/<YYYYMMDD>/<SSS>.csdb`.

### Step 4b — 113_F4_listing (barangay HH listing)

1. Tap **F4 Household Listing** on tablet.
2. Set barangay (PSGC 10-digit) on session control.
3. Choose `LISTING_SOURCE` = **1 (Barangay-captain-supplied)** for the primary test.
4. Transcribe 30 test households into REC_LISTING_BRGY_FRAME. Use realistic-looking placeholder PII.
5. Set `FRAME_FINALIZED=1` → APC's `DrawSystematicSample()` runs.
6. **Expected**: roster of 30 rows in REC_LISTING_SAMPLE — 20 with `SAMPLE_ROLE=1` (main) + 10 with `SAMPLE_ROLE=2` (replacement), all with `F4_STATUS=0`.
7. **Deterministic-seed test**: note the random sample drawn. Repeat the same session with identical inputs (same enumerator, same date, same start time, same barangay) — same 30 rows should be drawn. If not, the seed inputs are wrong.
8. Close session → custom sync push.
9. **Verify on CSWeb**: file at `f4_listing/<env>/<facility9>/<YYYYMMDD>/<barangay10>/<SSS>.csdb`.

Also test hybrid fallback: run a second session with `LISTING_SOURCE=2 (Fresh door-to-door)`. Same REC_LISTING_BRGY_FRAME schema; just enumerator-filled rather than transcribed.

## Step 5 — F3 patient interview (EXTERNAL dict handoff)

This is the **highest-risk surface** — F3's `forcase PATIENTLISTING_DICT` + write-back triple on the roster occurrence.

1. Tap **F3 Patient Survey** on tablet.
2. **Verify case-open**: patient-pick screen displays. It should show **Patient A** (the LISTING_TAG=1 row from Step 4a) and NOT Patients B or C.
3. Pick Patient A. **Verify pre-fill**:
   - `CASE_SEQ` auto-populates (from `f3_seq_lo + LISTING_NO - 1`)
   - `PATIENT_LISTING_NO` copies from listing roster
   - PII (name, age, sex, address) pre-fills the informed-consent block as read-only
4. **Verify write-back #1 (start)**: re-open the listing app's case → REC_PATIENT_ROSTER row for Patient A should now have `F3_STATUS=1` (in-progress).
5. Walk through F3 interview, hit save at end. **Verify write-back #2 (complete)**: listing roster row's F3_STATUS now = **2 (done)**.
6. **Test refusal path**: open F3, pick Patient B (LISTING_TAG=2 — wait, B is for F4. Re-list a fresh LISTING_TAG=1 patient for this test). At consent screen, set `CONSENT_GIVEN=2 (refused)`. **Verify write-back #3 (refusal)**: roster row's F3_STATUS = **3 (refused-at-F3)**.
7. **CASE_SEQ replacement protocol**: after refusal, list another LISTING_TAG=1 patient — their `ASSIGNED_F3_CASE_SEQ` should land in the **700-899 replacement range**.

## Step 6 — F4 household interview (EXTERNAL dict handoff)

Parallel to Step 5 but for F4 → 113_F4_listing.

1. Tap **F4 Household Survey** on tablet.
2. **Verify case-open**: PickHousehold() screen displays. It filters by:
   - 9-digit facility prefix matching current enumerator
   - `F4_STATUS=0` (pending)
   - `SAMPLE_ROLE=1` (main) rows shown first; if exhausted, fall back to `SAMPLE_ROLE=2` (replacement)
3. Pick a main row. **Verify pre-fill**:
   - F4 case-ID block
   - `HH_LISTING_NO` from listing roster
   - `BARANGAY_CODE` auto-stamps into `HOUSEHOLD_GEO_ID.BARANGAY` from the listing dict
   - `F4_PARENT_F3_CASE_SEQ` defaults to **999** (NA per F-series convention, since this HH was sampled via barangay listing, not F3 interval-walk)
4. **Verify write-back #1**: listing roster `F4_STATUS=1` (in-progress) on the selected row.
5. **Test soft-warnmsg-on-cancel**: at PickHousehold prompt, hit cancel. Expect a soft warnmsg (NOT hard error) permitting manual HH_LISTING_NO entry. F3's PickPatient errmsgs on cancel; F4's PickHousehold deliberately allows the manual fallback for households missed by listing crew.
6. Complete interview, save. **Verify write-back #2**: `F4_STATUS=2 (done)`.
7. **Test refusal path** (Q1 = No, not HH head): observe the routing fallback (per F4 logic-pass spec §5, currently SOFT prompt).

## Step 7 — Sync verification

| Instrument | Sync mechanism | Path |
|---|---|---|
| F1 | Native (CSPro Android UI → Send data) | `<app_id>/cases/...` standard CSWeb cases endpoint |
| 110_F3_listing | Custom (`synchronize_file PUT`) | `patient_listing/<env>/<facility9>/<YYYYMMDD>/<SSS>.csdb` |
| F3 | Native | standard cases endpoint |
| 113_F4_listing | Custom (`synchronize_file PUT`) | `f4_listing/<env>/<facility9>/<YYYYMMDD>/<barangay10>/<SSS>.csdb` |
| F4 | Native | standard cases endpoint |

For native sync: Synchronize → Send data → expect green checkmark per dictionary.
For custom sync: fires on SESSION_STATUS transition; check CSWeb file browser at the path above.

## Step 8 — Success matrix

- [ ] All 5 `.pen` + 2 sync helper `.pen` published without error
- [ ] All 7 deployed to CSWeb via Designer wizard
- [ ] Tablet pulls all 7 apps
- [ ] F1 case still works end-to-end (regression check)
- [ ] 110_F3_listing random-interval cadence fires (1-10 min countdown)
- [ ] Auto-tag PROC sets `LISTING_TAG` per Candidate A on all 3 test patients
- [ ] 113_F4_listing systematic random sample drawn (20 main + 10 replacement)
- [ ] 113_F4_listing deterministic seed reproducibility verified
- [ ] F3 patient-pick screen filters correctly (LISTING_TAG=1 + F3_STATUS=0)
- [ ] F3 write-back triple all 3 transitions verified (1=in-progress, 2=done, 3=refused-at-F3)
- [ ] F4 PickHousehold filters (main first, replacement fallback)
- [ ] F4 BARANGAY_CODE auto-stamps from listing dict
- [ ] F4 soft-warnmsg-on-cancel allows manual HH_LISTING_NO entry
- [ ] F4 write-back triple verified
- [ ] CASE_SEQ replacement range (700-899) activates after F3 refusal
- [ ] All custom-sync .csdb files land at documented paths
- [ ] All native-sync cases visible in CSWeb Data tab

## Known gotchas

- **CSWeb UI Apps tab is read-only** — deploy only via Designer's Deploy Application wizard
- **F7 publish order matters** — break the EXTERNAL DICTIONARY dependency chain and Designer rejects
- **Line endings pinned by `.gitattributes`** — don't manually edit Designer artifacts; regenerate from generators
- **PowerShell, not cmd.exe** — for `set VAR=value && cmd` patterns, use `$env:VAR='...'; cmd` (cmd.exe injects a trailing space)
- **`urls.yaml` LAN IP** — if your laptop's IP changed since Phase 1 sideload, regenerate with `--env=uat` and re-publish, or sync will fail with "Could not reach server"
- **CSPro 8.0 PFF launch method hook false-positive** — workaround in place at `106_menu/generate_apc.py`; doesn't affect runtime, just file as a hook bug at some point

## PENDING_DESIGN markers to verify at runtime

These are encoded in APC with PENDING_DESIGN comments; they reflect open design questions awaiting Myra's edit pass:

| Marker | Where | What to verify |
|---|---|---|
| `PENDING_DESIGN_AUTO_TAG_RULE` | `110_F3_listing/PatientListing.ent.apc` PROC `LISTING_TAG` | Candidate A behavior (distance-gated, 2.0/15.0 km thresholds, contact_verified gate). Constants `TAG1_THRESHOLD_KM=2.0` and `TAG2_THRESHOLD_KM=15.0` are tunable |
| Q136 → Q113 MAIFIP cross-reference | `115_F4/HouseholdSurvey.ent.apc` Section L | Skip rule encoded literally; unreachable because Q113 has no MAIFIP option. Inline comment documents this is a transcription artifact awaiting Myra's edit pass |
| Section M Q132 routing | `115_F4/HouseholdSurvey.ent.apc` | Agent retargeted from spec's Q137_MAIFIP_SOURCE to Q136_HEARD_MAIFIP for natural awareness-source ordering. Verify routing matches your read |

## When this is done

- Update Phase 2 status in `scrum/product-backlog.md` to reflect tablet-verified
- File any issues found as new GH Issues with `phase-2-tablet-test` tag
- Mark task #9 (Kidd-facing case-ID brief export) as the next remaining open item

## Related

- F7 publish runbook: `2026-05-08-cspro-publish-entry-runbook.md`
- Tablet sideload runbook: `2026-05-08-tablet-sideload-runbook.md`
- 110_F3_listing sync model: `deliverables/CSPro/UHC-Survey-System/110_F3_listing/SYNC.md`
- 113_F4_listing sync model: `deliverables/CSPro/UHC-Survey-System/113_F4_listing/SYNC.md`
- F4 listing hybrid model concept: `wiki/concepts/F4 Listing - Hybrid Frame Model.md`
- Case-ID concept page: `wiki/concepts/Questionnaire Numbering Convention.md`
- CSWeb deploy flow memory: `reference_csweb_deploy_flow.md`
