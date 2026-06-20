# Supervisor App — Phase 1 (Review Layer)

Read-only field QA over pulled F1/F3/F4 cases. No write-back; enumerators keep
syncing directly to CSWeb (Phase 1). See the spec:
`docs/superpowers/specs/2026-06-20-supervisor-app-design.md`.

## C1 — CSWeb supervisor role (one-time, server admin)

The Supervisor App needs **case data** (dictionary GET / down-sync) to run the report
and to open a case read-only for spot-check. The existing `supervisor-monitor` role
(see `deliverables/CSWeb/CSWeb-User-Management-and-RBAC-Provisioning-Pack.md`) is
**deliberately `report`-only with NO `data` download** — counts + geo, no full-PII rows —
so widening it would change the PII posture for every field supervisor / cluster RA on it.

**Therefore: provision a SEPARATE QA role** (e.g. `supervisor-qa`) granted **dictionary
GET / down-sync** on `FACILITYHEADSURVEY_DICT`, `PATIENTSURVEY_DICT`, `HOUSEHOLDSURVEY_DICT`,
and assign it ONLY to the supervisor(s) doing QA. Leave `supervisor-monitor` PII-free as
designed.

> **PII NOTE (decision for ASPSI):** pulling cases exposes respondent data. The HTML report
> is PII-light, but the case-level spot-check shows PII. Confirm the QA supervisor(s) are
> authorized for PII spot-check before enabling the GET role.

## C5 — Tablet review (on-site, thin)

On the supervisor tablet, CSEntry with the GET-enabled QA account:
1. Sync → CSWeb → GET (pull latest).
2. Open the app in review mode; the case list shows **partial cases with a red bar /
   distinct icon**. Open a case read-only to spot-check.

(On-site review needs signal; otherwise do the laptop pass at base. Phase 2's
Bluetooth hub removes the signal dependency.)

## Evening laptop run (the report engine)

1. **Pull**: Data Manager → GET F1/F3/F4 onto the laptop.
2. **Export to CSV**: in the desktop **Data Viewer**, open each instrument's data and
   `File → Export → CSV`, saving as `exports/F1.csv`, `exports/F3.csv`, `exports/F4.csv`
   (the CSV headers are the dictionary item names — the report reads them directly).
3. **Maintain** `assignments.csv` from `assignments.example.csv` (one row per
   enumerator/facility/instrument with the target count).
4. **Run**:
   ```
   python supervisor_qa_report.py --exports ./exports --assignments ./assignments.csv \
       --out ./supervisor-qa.html --cluster <cluster> --today <YYYYMMDD>
   ```
5. **Review** `supervisor-qa.html`: coverage vs plan, partials (#561), QA flags. For any
   flagged/partial case, open it read-only in Data Viewer (the only PII step) and chase
   the enumerator by radio. Partial-case visibility note: CSWeb's web dashboard does NOT
   show partial vs complete — this report and the Data Viewer "Partial Cases Only" filter
   do.

## The 5 data-quality flags (`qa_rules.py`)

| Flag | Fires when |
|---|---|
| `no_gps` | case has no GPS latitude captured |
| `no_photo_completed` | Completed case with no verification photo |
| `stuck_partial` | partial / in-progress and last visit > 2 days ago (`STUCK_DAYS`) |
| `disposition_mismatch` | Completed but the opening question is blank |
| `consent_contradiction` | Withdraw/Refused result code but answers are present |

## Field-name notes (verified against the live dictionaries, 2026-06-21)

- **F4** GPS latitude item is `LATITUDE` (label "GPS Latitude") — there is no `HH_GPS_LATITUDE`.
- **F1** final-visit date item is `DATE_OF_FINAL_VISIT_TO_THE_FACILITY` (F3/F4 use `DATE_FINAL_VISIT`).
- **F1** has no `CASE_DISPOSITION` (Cluster 5 covered F3/F4 only); F1 completeness is derived
  from `ENUM_RESULT_FINAL_VISIT` (Completed = `1`). If ASPSI later wants F1 break-off, fan out
  the Cluster-5 pattern to F1 first.

## Notes

- Read-only: the tool never writes case data.
- Phase-2 compatible: it reads CSV exports regardless of how cases arrived (CSWeb GET now,
  Bluetooth hub later).
- Stuck-partial threshold is 2 days; edit `STUCK_DAYS` in `qa_rules.py` to change.
- stdlib only; tests need pytest. Run them with: `python -m pytest -q` from this directory.
