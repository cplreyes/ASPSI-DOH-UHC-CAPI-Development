# Supervisor App — Design Spec (Phase 3: Facility Visit Log)

**Date:** 2026-06-23
**Status:** Approved design (brainstorm complete) — ready for implementation planning
**Author:** Carl Patrick Reyes (with Claude)
**Origin:** Review of the **DOH-submitted Survey Manual v1.0** (2026-05-12 Clean Final) + its companion **CAPI-Input doc**. Both name a **"Supervisor App"** whose primary, explicitly-described function is a **Facility Visit Log** — and that function was never built. Everything previously built and labelled "Supervisor App" (Phases 1–2) is the *QA review* layer, which the Manual frames as the FS's "Supervisor Inspections" **activity**, not the named app.

---

## The naming correction (read first)

"Supervisor App" has been pointing at two different things. This spec fixes the names:

| Term (going forward) | What it is | Status |
|---|---|---|
| **Supervisor App** | The **Facility Visit Log** the Manual names (CAPI-Input §3.3.2, l.277; Manual l.755). A CSEntry **data-capture** app for facility touchpoints. | **This spec. Unbuilt — build now.** |
| **Supervisor QA Review tool** | The coverage / partials / flags report (formerly "Supervisor App Phase 1"). Maps to the Manual's "Supervisor Inspections / Daily Questionnaire Review" activity. | Built (laptop engine, `deliverables/CSWeb/supervisor-app/`, 15/15 tests). Unchanged by this spec. |
| **Bluetooth Sync Hub** | Offline enumerator→supervisor→CSWeb relay (formerly "Phase 2"). | Spec'd, deferred (D7 of that spec). Unchanged. |

The CSWeb dashboards (Sync/Map reports + monitoring hub) cover the Manual's **CSWeb real-time monitoring** layer and are also separate from this app.

---

## Goal

Give each Field Supervisor (FS) a CSEntry app to **document every facility touchpoint in real time** — arrival, courtesy-call engagement and outcomes, endorsement-letter delivery, workstation arrangement, focal-person assignment, master-HCW-list capture, and departure — **auto-stamped with GPS coordinates and timestamps**, producing an auditable record that syncs to CSWeb and can be reconciled against scheduled visits and reserve-list draws.

> Source (verbatim), CAPI-Input §3.3.2, l.277: *"All courtesy call activities — arrival, head or representative engagement, endorsement letter delivery, workstation arrangement, focal person assignment, master Healthcare Worker list capture, and departure — are documented in real time by the Field Supervisor using the **Facility Visit Log** section of the **Supervisor App**. The Supervisor App auto-stamps GPS coordinates and timestamps for every entry, creating an auditable record of every facility touchpoint that can be reconciled against scheduled visits and reserve-list draws."*
>
> Source, Manual l.755: *"Supervisor App and Visit Logs: FSs use a dedicated app to document every facility touchpoint—including arrival, courtesy call outcomes, and departure—which is automatically stamped with GPS coordinates and timestamps."*

## Architecture (one line)

A **standalone CSPro 8 / CSEntry data-capture app** (`SupervisorApp`), generator-built like F1/F3/F4, installed by the FS under their own CSWeb account, capturing one **Facility Visit Log** case per facility (a repeating geo/time-stamped touchpoint roster + a once-per-facility courtesy-call block), syncing to CSWeb like any instrument.

## Tech Stack

CSPro 8.0 data-entry application (`.dcf`/`.apc`/`.fmf`/`.qsf`) · CSEntry 8.0 on Android · CSWeb 8.0.1 (`csweb.asiansocial.org`) sync under the FS account · the shared `deliverables/CSPro/shared/Capture-Helpers.apc` GPS helper (`ReadGPSReading` + `gps(...)`). **No rendering crux** (this is data capture, not a computed report) — and no new server.

---

## Background — what exists vs. what the Manual promised

- **What DOH was told the FS uses (the Supervisor App):** a dedicated app for the Facility Visit Log (above). The FS "install[s] the same set [of instruments] in monitoring mode **plus the Supervisor App**" (CAPI-Input §3.3.4, Step 5, l.297), signing in with a **unique account** (l.296).
- **What exists:** the QA Review tool (laptop engine) + CSWeb dashboards. **The Facility Visit Log app does not exist.** This spec closes that gap.
- **Why CSEntry is the right host:** the instruments already auto-capture GPS via `ReadGPSReading(120,20)` + `gps(latitude/longitude/altitude/accuracy/satellites/readtime)` in a field preproc, captured-once and `protect()`ed (e.g. F1 `generate_apc.py` `PROC FACILITY_GPS_LATITUDE`). Timestamps via `sysdate("YYYYMMDD")` / `systime`. The visit log reuses this proven, tamper-evident pattern verbatim.

## Goals

1. **Touchpoint log** — capture each facility touchpoint (typed) with **auto GPS + auto timestamp**, across the multi-day engagement (courtesy-call day, patient-listing day, interview days).
2. **Courtesy-call outcomes** — the structured one-time-per-facility results of the initial visit (approval/endorsement, focal person, scheduling, HCW master-list capture, QR poster, workstation).
3. **Auditable + syncable** — every entry geo/time-stamped and protected; cases sync to CSWeb alongside survey data.
4. **Reconcilable** — the record supports later reconciliation against the visit schedule / reserve-list (the report is a fast-follow, not v1 — see Non-goals).

## Non-goals (v1)

- **No household Visit Sheet / replacement approval** (Manual l.707 — ≥3 contact attempts, reason codes, FS replacement approval). That is a distinct *household-side* record; the CAPI-Input doc frames the Facility Visit Log as facility-focused. Scoped separately later (belongs with F4 or its own SE tool). **(Decided: facility log only for v1.)**
- **No QA review inside this app** — coverage/partials/flags stays the separate QA Review tool (laptop engine).
- **No reconciliation report in v1** — capture first; the schedule/reserve-list reconciliation is a thin follow-on (reuses the QA tool's assignment-lookup pattern or a CSWeb view).
- **No Bluetooth** (that's the deferred Sync Hub).
- **No role-routing menu in v1** — the FS launches the app directly under their CSWeb account; the Khurshid login+menu wrapper (shared with the Sync-Hub C1 spike) is an optional later add, not required for a standalone capture app.

## Decisions locked (during brainstorm, 2026-06-23)

| # | Decision |
|---|---|
| D1 | **Phase 3 = the Facility Visit Log app the Manual names.** The QA review layer stays the separate laptop engine; rename to end the two-things-one-name confusion. |
| D2 | **Standalone CSEntry data-capture app**, generator-built (iron rule: never hand-edit `.dcf`/`.apc`/`.fmf`/`.qsf`). |
| D3 | **One case per facility**, keyed by the facility code (`RR-PP-MMM-FF`); a repeating **touchpoint roster** + a once-per-facility **courtesy-call block**. |
| D4 | **Auto GPS + timestamp per touchpoint**, captured-once and `protect()`ed, reusing the shared `Capture-Helpers.apc` `ReadGPSReading`/`gps()` pattern. |
| D5 | **Syncs to CSWeb under the FS's existing account** — no new server role for capture. |
| D6 | **Facility log only for v1** — household Visit Sheet / replacement approval out of scope. |
| D7 | **Reconciliation report is a fast-follow**, not v1. |
| D8 | **Login = FS CSWeb account** (real auth); role-routing menu optional/later. |

---

## Architecture

```
   FS tablet (CSEntry, FS's unique CSWeb account)
   ┌───────────────────────────────────────────────┐
   │  Survey instruments (F1/F3/F4) — monitoring     │
   │  SupervisorApp  ← THIS APP                  │
   │   • Header: facility code, FS id, facility name  │
   │   • Courtesy-call block (once per facility)      │
   │   • Touchpoint roster (repeating):               │
   │       type + AUTO gps() + AUTO sysdate/systime   │
   │       + outcome note + optional photo            │
   └───────────────────────┬───────────────────────-─┘
                            │  CSEntry Synchronize (HTTPS)
                            ▼
                   CSWeb (csweb.asiansocial.org)
                   SUPERVISORAPP_DICT cases
                            │
                            ▼  (fast-follow)
              Reconciliation report: logged visits vs
              schedule / reserve-list draws
```

## Data model — `SUPERVISORAPP_DICT`

**Case key:** `FACILITY_CODE` (the `RR-PP-MMM-FF` facility identifier derived from / consistent with the 12-digit survey case key). One case per facility, accumulating touchpoints across the engagement.

**Header (id + once):**
- `FACILITY_CODE` (PSGC cascade or typed; reuse the shared PSGC cascade where practical)
- `FACILITY_NAME` (alpha)
- `FS_OPERATOR_ID` (the FS's operator/login id)

**Courtesy-call block (once per facility, the initial-visit outcomes — CAPI-Input §3.3.2):**
- `CC_ENDORSEMENT_OBTAINED` (yes/no)
- `CC_HEAD_INTERVIEW_DATE` (date scheduled)
- `CC_FOCAL_PERSON_NAME` (alpha)
- `CC_DISCHARGE_CUTOFF` (alpha/short — usual discharge/billing cutoff time)
- `CC_HCW_LIST_CAPTURED` (yes/no) + `CC_HCW_LIST_COUNT` (numeric) + optional `CC_HCW_LIST_PHOTO` (Image)
- `CC_QR_POSTER_POSTED` (yes/no)
- `CC_PATIENT_LISTING_DATE` (date scheduled)
- `CC_WORKSTATION_ARRANGED` (yes/no)

**Touchpoint roster (repeating record, `max_occurs` generous, `required=False`):**
- `TP_LINE` (numeric, occurrence index, noinput)
- `TP_TYPE` (select_one: 1 Arrival / 2 Courtesy call / 3 Endorsement delivery / 4 Workstation / 5 Focal person / 6 HCW-list / 7 Departure / 8 Other)
- `TP_TIMESTAMP` (auto, protected — `sysdate`+`systime`)
- `TP_GPS_LATITUDE` / `TP_GPS_LONGITUDE` / `TP_GPS_ACCURACY` / `TP_GPS_SATELLITES` / `TP_GPS_READTIME` (auto, protected — `gps(...)`)
- `TP_OUTCOME_NOTE` (alpha, optional)
- `TP_PHOTO` (Image, optional — reuse the verification-photo helper pattern; binary-Image dict item so it syncs to CSWeb per #713)

## Components

1. **`generate_dcf.py`** — builds `SUPERVISORAPP_DICT` (header + courtesy-call block + touchpoint roster record). New record-type letters chosen from unused set.
2. **`generate_apc.py`** — the touchpoint row's **preproc auto-stamp** (GPS + timestamp, captured-once guarded on `TP_GPS_READTIME` empty, then `protect()`); `TP_TYPE`-driven prompts; minimal validation (note required for "Other").
3. **`generate_fmf.py`** (or hand-fmf if simpler for a one-off small app — decide in plan) — forms: header form → courtesy-call form → touchpoint roster form. Photo + GPS field placement.
4. **`generate_qsf.py`** — question text / enumerator instructions per field.
5. **Shared reuse** — `Capture-Helpers.apc` (`ReadGPSReading`, photo `view()`/`save()`), PSGC cascade for facility selection.
6. **CSWeb deploy** — publish + `auto_deploy` like an instrument; the dictionary registered on CSWeb so FS accounts can sync it.

## Auto-capture mechanics (grounded, reused verbatim)

Each touchpoint row preproc (pattern proven in F1 `PROC FACILITY_GPS_LATITUDE`):
```cspro
PROC TP_GPS_LATITUDE   { fires on the touchpoint row; capture once }
preproc
  if length(strip(TP_GPS_READTIME)) = 0 then
    if ReadGPSReading(120, 20) then
      TP_GPS_LATITUDE   = maketext("%f", gps(latitude));
      TP_GPS_LONGITUDE  = maketext("%f", gps(longitude));
      TP_GPS_ACCURACY   = gps(accuracy);
      TP_GPS_SATELLITES = gps(satellites);
      TP_GPS_READTIME   = maketext("%d", gps(readtime));
      TP_TIMESTAMP      = maketext("%s %s", sysdate("YYYYMMDD"), systime("HHMM"));
    endif;
  endif;
postproc
  if length(strip(TP_GPS_READTIME)) > 0 then
    protect(TP_GPS_LATITUDE, true); protect(TP_GPS_LONGITUDE, true);
    protect(TP_GPS_ACCURACY, true); protect(TP_GPS_SATELLITES, true);
    protect(TP_GPS_READTIME, true); protect(TP_TIMESTAMP, true);
  endif;
```
Desktop has no GPS — guard with the `getos()` 10–19 check the instruments already use, so desktop compile/desk-test doesn't loop on a missing reading.

## Sync & reconciliation

- **Sync:** `SUPERVISORAPP_DICT` cases sync to CSWeb via CSEntry Synchronize under the FS account — same mechanism as the instruments. The auditable record lands server-side.
- **Reconciliation (fast-follow):** a report comparing logged facility visits to the planned visit schedule / reserve-list draws. Reuse the QA Review tool's assignment-lookup pattern (it already reads an `assignments.csv` of facility/enumerator/target) or add a CSWeb view. Not v1.

## Login / role

The FS signs into CSEntry with their **unique CSWeb account** (the real auth) and opens `SupervisorApp` directly — same as opening any instrument. The Khurshid login + role-routing **menu app** (shared with the Sync-Hub C1 spike) is an optional later wrapper for one-tap role separation; **not required** for v1.

## Testing & rollout

- **Build gates (same as instruments):** Designer compile (lenient) → strict **Publish** packager (the real gate) → `auto_deploy`. A `verify_questions`-style reachability pass if applicable.
- **Device verification (itel):** add a facility, log Arrival → confirm GPS + timestamp auto-stamp and are protected; add several touchpoints; capture the HCW-list photo; **sync to CSWeb** and confirm the case + binary photo land server-side.
- **Pilot one facility** before fleet rollout; short **FS SOP** (install under your account, log each touchpoint live, sync nightly).

## Open items for ASPSI / Carl

1. **Facility identifier** — confirm the FS keys the log by the same `RR-PP-MMM-FF` facility code used in the survey case key (so reconciliation joins cleanly), and whether facility selection is a PSGC cascade or a typed code + lookup.
2. **HCW master-list capture** — photo of the printed list (simplest), a typed count only, or both? (v1 assumes count + optional photo.)
3. **Touchpoint type list** — confirm the 8-type enumeration matches the FS's real workflow vocabulary.
4. **Reconciliation report timing** — fast-follow after capture is device-confirmed, or bundle into v1?
