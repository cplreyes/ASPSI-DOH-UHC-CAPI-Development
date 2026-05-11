# 110_F3_listing — Sync model

Listing-app data flows differ from the F-series questionnaire sync model
because the listing app's output (`PATIENTLISTING_DICT`) is **read** by
sibling instruments (F3, F4) at interview time. The roster needs to be
on every enumerator's tablet — not just the listing enumerator who
captured it.

## Data flow

```
[Listing enumerator's tablet]
       |
       |   PATIENTLISTING_DICT (one .csdb per facility-day)
       |   contains LISTING_SESSION_DATE + LISTING_SESSION_SEQ as ID,
       |   roster occurrences inside.
       v
[CSWeb server]
       |   case path:
       |     patient_listing/<env>/<facility-id-prefix>/<YYYYMMDD>/<seq>.csdb
       v
[F3 enumerator's tablet]     [F4 enumerator's tablet]
   reads via                     reads via
   EXTERNAL DICTIONARY           EXTERNAL DICTIONARY
   PATIENTLISTING_DICT           PATIENTLISTING_DICT
   loadcase()                    loadcase()
```

## Path convention (CSWeb)

For each environment (dev / uat / prod), the listing-data path is:

```
patient_listing/<env>/<RR><PP><MMM><FF>/<YYYYMMDD>/<SSS>.csdb
```

Where `<RR><PP><MMM><FF>` is the 9-character facility prefix derived from
the listing session ID block (concatenation of REGION_CODE,
PROVINCE_HUC_CODE, CITY_MUNICIPALITY_CODE, FACILITY_NO).

The path is constructed in the listing app's APC via the
`synchronize_file` directive once the session is closed — see
`sync_F3_listing_app.pff` for the .pff parameters.

## .pen artifact

The compiled application bundle for the listing-side sync helper lives at:

```
../109_sync/sync_F3_listing_app.pen   (parallel to sync_F1_app.pen)
```

Compilation is via CSPro Designer's `File -> Publish Entry Application`
(F7) on `sync_F3_listing_app.ent` — same manual SOP as the F-series
publish step documented in `docs/superpowers/runbooks/cspro-publish-
entry-runbook.md`. The `.pen` is committed to the repo; the `.ent` is
not (only the `.pff` parameter file lives here so the Designer-laid
configuration is reproducible).

## Pull side (F3 / F4 reading the listing dictionary)

When the F3 entry app is built (commit 12 + its sibling work),
`111_F3/PatientSurvey.ent` will declare `PATIENTLISTING_DICT` as an
EXTERNAL dictionary so PROC code can call:

```
key(PATIENTLISTING_DICT) = LISTING_SESSION_DATE_F3 + ...;
if loadcase(PATIENTLISTING_DICT, key) then
    { iterate REC_PATIENT_ROSTER occurrences, pick LISTING_TAG=1 +
      F3_STATUS=0 rows for today's same-day exit interview queue. }
endif;
```

Schema for that pull-side wiring is held until commit 12 lands the F3
entry-app skeleton.

## Sync auth + ownership

Per the project-wide CSWeb sync auth model:
  - listing enumerator's tablet authenticates to CSWeb with their
    enumerator user (provisioned at training);
  - the case-ID prefix gates write access — an enumerator can only
    push cases whose case-ID's facility prefix matches their
    assignment (enforced server-side via the case-ownership filter
    on the CSWeb endpoint).
  - F3 / F4 enumerators get read access to all `patient_listing/*`
    cases by virtue of the "all_facilities_read" CSWeb group.

Details of the group membership are in the `csweb` deployment runbook,
not duplicated here.
