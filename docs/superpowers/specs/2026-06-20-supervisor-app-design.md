# Supervisor App — Design Spec (Phase 1: Review Layer)

**Date:** 2026-06-20
**Status:** Approved design (brainstorm complete) — ready for implementation planning
**Author:** Carl Patrick Reyes (with Claude)
**Origin:** UAT R4 issue **#561** (partial cases sync to CSWeb but the web dashboard can't show which are partial) + the Cluster-5 disposition work (**#515/#561**).

---

## Goal

Give field supervisors a tool to **monitor and quality-check** F1/F3/F4 CAPI cases in the
field — partial-case visibility, coverage vs plan, read-only case spot-check, and automated
data-quality flags — **without** changing the conflict-free direct-to-CSWeb sync the
enumerators use today.

## Architecture (one line)

A **read-only review layer**: enumerators keep syncing directly to CSWeb; the supervisor
**pulls** review copies and reviews them on two surfaces — a thin on-site tablet (CSEntry
built-in review) and a laptop-at-base engine (a CSPro batch report + Data Viewer).

## Tech Stack

CSPro 8.0 batch application (HTML report output) · CSEntry 8.0 review mode · CSWeb 8.0.1
(`csweb.asiansocial.org`) GET sync · a small assignment/target lookup (CSV / external dict).
No new server, no web app, no change to the enumerator instruments' sync.

---

## Phasing (important — this spec is Phase 1 only)

| Phase | What | Status |
|---|---|---|
| **Phase 1 — Review Layer** | Supervisor *monitors/QA* pulled cases. Enumerators still sync direct to CSWeb. | **This spec.** Build now. |
| **Phase 2 — Bluetooth Sync Hub** | Enumerators Bluetooth-sync to the supervisor's tablet on-site (no internet); supervisor uploads to CSWeb. | **Deferred** until the F1/F3/F4 instruments are stable (near-zero UAT bugs). Separate spec. |

The Phase-1 report engine is written against **pulled `.csdb` files regardless of how they
arrived** (CSWeb GET now, Bluetooth later), so it serves both phases without a rewrite.
The thin Phase-1 tablet surface thickens into the Phase-2 hub; nothing in Phase 1 is torn up.

---

## Background — current architecture (what exists today)

- **No supervisor tablet app today.** Enumerators sync **directly** to `csweb.asiansocial.org`
  via CSEntry's built-in Synchronize (send-only, manual, the Protocol-V2 22:00 daily upload
  mandate). Source: `deliverables/CSWeb/Field-Tablet-Sync-Configuration.md`.
- **Conflict-free by design:** the 12-digit case key (`RR-PP-MMM-FF-CCC`) + one-facility-per-
  enumerator assignment means no two devices mint the same key — no merge conflicts.
- **"Supervisor" today = a CSWeb web role** (`supervisor-monitor`, report-only: Sync Report
  counts + Map geo, *not* full-PII case rows). Source:
  `deliverables/CSWeb/CSWeb-User-Management-and-RBAC-Provisioning-Pack.md`.
- **The #561 gap:** CSWeb's web dashboard shows case **counts** (Total / Processed) but has
  **no partial-vs-complete indicator or filter**. Partial status is only visible in the
  desktop **Data Viewer** ("Partial Cases Only" filter) or as data inside the case. So a
  supervisor watching the web dashboard cannot see which synced cases are incomplete.

## Goals

1. **Partial-case visibility (#561)** — surface which synced cases are incomplete and why
   (disposition: Withdrew / Postponed / In-progress / force-quit-no-disposition), per enumerator.
2. **Coverage vs plan** — completed cases against planned interviews, per facility and per
   enumerator (replaces the manual 22:00 STL roll-call off the Sync Report).
3. **Read-only case spot-check** — open an individual synced case to verify data quality.
4. **Automated data-quality flags** — a rule-based exception worklist.

## Non-goals (Phase 1)

- **No write-back.** The supervisor never edits or re-syncs case data; no reject/reassign
  channel (that is Survey Solutions' approve/reject flow → **Phase 2**). Acting on findings
  is out-of-band: the supervisor tells the enumerator to fix/finish on *their* device.
- **No change to enumerator sync** (stays direct-to-CSWeb).
- **No interview-duration flag** in Phase 1 (no start/end timestamps exist — see Decisions).
- **No new server / web app.** Reuses CSWeb + desktop CSPro tooling.

## Decisions locked (during brainstorm)

| # | Decision |
|---|---|
| D1 | **Phase 1 = Review Layer** (sync stays direct); **Phase 2 = Bluetooth hub** later. |
| D2 | **Both surfaces:** thin tablet on-site + laptop-at-base engine. |
| D3 | All four capabilities in scope (partials, coverage, spot-check, QA flags). |
| D4 | **PII split:** the QA **report is PII-light** (case keys + enumerator + status + flag reasons, no names/answers); **full PII only in spot-check** (Data Viewer / CSEntry review), by exception. |
| D5 | **Duration flag dropped** for Phase 1 — instruments capture no interview timestamps (`cspro_helpers.py:317` deliberately omits `TIME_STARTED`). Revisit later via CSPro **paradata** (no instrument change needed). |
| D6 | **Read-only, no write-back** in Phase 1 (preserves the conflict-free 12-digit-key design). |
| D7 | The Supervisor App **reports on the #515/#561 disposition field** — that completeness data is the backbone the report reads to classify partial vs complete. |

---

## Architecture

```
                          ┌─────────────────────────┐
   Enumerator tablets ───►│   CSWeb                  │   Phase 1: enumerators
   (F1/F3/F4, send-only)  │   csweb.asiansocial.org  │   sync direct — unchanged
                          └───────────┬─────────────┘   conflict-free (12-digit key)
                                      │  GET (pull read-only review copy)
                  ┌───────────────────┴───────────────────┐
                  ▼                                         ▼
   ┌──────────────────────────┐            ┌──────────────────────────────────┐
   │ TABLET (CSEntry, on-site)│            │ LAPTOP (CSPro desktop, at base)  │
   │  • quick partials list   │            │  • Supervisor-QA batch report    │
   │  • read-only spot-check  │            │     → coverage vs plan           │
   │  (built-in review mode)  │            │     → partials + disposition     │
   │  thin — config + SOP     │            │     → data-quality flag worklist │
   └──────────────────────────┘            │  • Data Viewer 'Partial Only'    │
                                           │  • read-only case review         │
                                           │  the engine (the build)          │
                                           └──────────────────────────────────┘
```

- **Laptop at base = the engine.** A CSPro batch application reads pulled F1/F3/F4 cases +
  the assignment/target lookup and emits one HTML report (coverage / partials / flags). Plus
  Data Viewer for the partial filter + read-only spot-check. Delivers all four capabilities
  with mostly existing tools.
- **Tablet on-site = thin.** Supervisor CSEntry with GET permission; review via the built-in
  case listing (partial icon) + read-only open. No custom tablet build in Phase 1.

**Connectivity caveat (Phase 1):** the tablet pulls its review copy *from CSWeb*, so on-site
review only works where there's signal on-site. Where there isn't, the supervisor's real
review is the evening laptop pass at base. Phase-2 Bluetooth removes this limit.

---

## Components

### C1 — CSWeb supervisor sync role (+ PII governance)
**RESOLVED 2026-06-21 (supersedes the original "extend `supervisor-monitor`" wording below):**
the down-sync runs on CSWeb **dictionary-sync permission, not the web `data` dashboard**, so
provision a **dedicated `supervisor-qa` role** (`report` dashboard + dictionary sync on
`FACILITYHEADSURVEY_DICT` / `PATIENTSURVEY_DICT` / `HOUSEHOLDSURVEY_DICT`) held only by the
designated QA supervisor(s), and keep `supervisor-monitor` `report`-only with **no** sync.
This scopes the bulk-PII pull to a named few rather than all ~26 supervisors. See the RBAC
pack §2 (`CSWeb-User-Management-and-RBAC-Provisioning-Pack.md`) and the app README §C1.

~~Extend the existing `supervisor-monitor` role with dictionary GET / down-sync on the three
dicts.~~ **Governance (D4):** routine report touches no PII; the only PII action is opening an
individual case in spot-check, on a controlled device. **Remaining ASPSI input:** the names of
the designated QA supervisor(s), authorized for case-level PII spot-check (pack §6 item 4).

### C2 — Supervisor-QA batch application (the laptop engine, the build)
A CSPro 8 batch/driver app, run by double-clicking a `.pff`, that reads the pulled F1/F3/F4
case files (via `Case` objects so one app covers all three) + the assignment lookup, and
writes **one HTML report** it opens in the browser, with three panels:

```
SUPERVISOR-QA REPORT — Cluster 01028 — 2026-06-20 22:10
───────────────────────────────────────────────────────
① COVERAGE vs PLAN
   se-004  F3   8/10    2 left
   se-011  F3   5/10    5 left   ⚠ behind
   Team    F3  23/30   (77%)
② PARTIALS / INCOMPLETE  (#561)
   se-004  010280001001  Withdrew (Sec F)
   se-011  010280002003  In progress (Sec C)
   se-019  010280004005  Force-quit, no disposition
③ DATA-QUALITY FLAGS
   010280001007  no GPS fix
   010280002003  no verification photo (Completed)
```

Read-only by design (never writes case data). PII-light (keys/status/flags only).

### C3 — Assignment / target lookup (the coverage "plan")
A small external lookup the supervisor maintains, one row per assignment:
`ENUMERATOR_ID, FACILITY_CODE (RR-PP-MMM-FF), INSTRUMENT, TARGET_COUNT`
e.g. `se-004, 01-028-001-01, F3, 10`. Source: the existing fieldwork assignment / sample.
Without it, panel ① degrades to raw counts (no "vs plan"). **To confirm in planning:** exact
source/format (supervisor-maintained CSV vs generated from the sample).

### C4 — QA flag rule set (starter, extensible)
Panel ③ runs these rules per case (duration rule deferred — D5):
1. **No GPS fix** — facility/home GPS lat/lon empty.
2. **No verification photo** on a case marked Completed (ties to the #713 binary-image fix).
3. **Stuck partial** — partial case older than N days, still In-Progress.
4. **Disposition mismatch** — Completed but a required section is blank (forced-through).
5. **Consent contradiction** — consent = No / Withdrew but substantive answers present.

### C5 — Tablet review setup (on-site, thin)
Supervisor CSEntry with the 3 deployed apps + GET-enabled supervisor account. Review = pull
(Sync → GET) → built-in review mode: case listing shows partial cases with a distinct icon;
a case opens read-only for spot-check. **No custom tablet build in Phase 1** — account +
config step + SOP. Thickens into the Bluetooth hub in Phase 2.

---

## Data flow — the review cycle

```
DURING DAY   Enumerators capture offline; sync (PUSH) to CSWeb when signal allows  [unchanged]
EVENING @ base (laptop)
 1. PULL    Data Manager GET → F1/F3/F4 review copies (.csdb) onto laptop
 2. REPORT  double-click Supervisor-QA.pff → HTML (coverage / partials / flags)
 3. REVIEW  read the 3 panels; for any flagged/partial case →
 4. SPOT    open it read-only (Data Viewer / 'Partial Cases Only') — the only PII step
 5. ACT     chase enumerators on gaps/partials/flags (verbal/radio); log in the 22:30 roll-call
ON-SITE (tablet, when signal exists)
 quick: CSEntry Sync GET → case listing (partial icon) → open read-only spot-check
```

**Integrity property:** every pulled copy is read-only; the Supervisor App never edits or
re-syncs case data → it cannot clobber enumerator data or create a conflict; the conflict-free
12-digit-key design stays intact. Acting on findings is out-of-band (enumerator fixes on their
own device, which re-syncs normally).

## Edge cases

- **Stale snapshot** — review copy ages as enumerators work. Report header stamps pull-time;
  SOP = pull immediately before running.
- **Force-quit partial, no disposition** — still surfaces in panel ② via the case-start
  In-Progress sentinel (#561 work) set at case open.
- **No-sync vs no-work ambiguity** — 0/target may mean nothing done *or* done-but-not-synced;
  report flags 0-sync enumerators for the STL to disambiguate by radio.
- **Assignment drift** — reassigned facilities require updating the lookup, else coverage is
  wrong. SOP: supervisor edits the lookup on reassignment.
- **PII on device** — review copies hold PII → laptop/tablet must be encrypted + passworded;
  wipe review copies at cluster end.
- **No on-site signal** — tablet review unavailable; falls back to evening laptop review.
  Phase-2 Bluetooth removes this.

## Error handling (batch app, fail-soft)

- Instrument not pulled → report prints "F1 not pulled" for that panel, no crash.
- Missing/empty assignment lookup → coverage degrades to raw counts with a notice.
- Empty data set → report shows zeros, not an error.

## Testing

- **Unit (deterministic, no device):** synthetic `.csdb` of known cases (mix of complete /
  partial / each flag) + known target lookup → assert HTML counts, partials, flags match.
- **Rule tests:** one crafted case per QA rule → each flag fires; clean cases stay clean.
- **Coverage math:** target 10, 8 complete + 1 partial → "8/10, 2 left, 1 partial."
- **PII guard:** grep the generated HTML → case keys/status/flags only, no names/answers.
- **Device integration:** itel tablet → GET pull → confirm partial icon + read-only review;
  laptop → full pull → report → spot-check round-trip.

---

## Dependencies & open items (resolve in planning)

1. **Disposition backbone** — the Supervisor-QA report depends on the **#515/#561 disposition
   field** (Result-of-Visit + case-start In-Progress sentinel). Build/confirm that first (or
   in parallel); the report's partial classification reads it.
2. **CSWeb role extension** (C1) — add dictionary GET to `supervisor-monitor`; confirm PII
   spot-check authorization.
3. **Assignment/target lookup source** (C3) — confirm format + who maintains it.
4. **`Case`-object multi-dictionary read** — confirm the CSPro 8 batch pattern for reading
   three dictionaries in one driver app (fallback: 3 runs, concatenated report fragments).

## Phase 2 forward note (out of scope here)

Bluetooth sync hub: enumerators `syncconnect` to the supervisor's `syncserver` (Bluetooth);
supervisor collects on-site with no internet, then uploads to CSWeb. Adds a write-back /
reassign channel and on-tablet dashboards. Separate spec when instruments are stable.

## References

- CSPro Synchronization Overview — Internet (CSWeb/Dropbox/FTP) + Bluetooth peer-to-peer; the
  supervisor-as-intermediary 3-tier topology. <https://www.csprousers.org/help/CSPro/synchronization.html>
- CSPro `SyncServer` (Bluetooth local server). <https://www.csprousers.org/help/CSPro/syncserver_function.html>
- CSPro `IsPartial` — a case is "currently marked as a partial save" (persisted attribute).
  <https://www.csprousers.org/help/CSPro/ispartial_function.html>
- Data Viewer — "Partial Cases Only" filter. <https://www.csprousers.org/help/DataViewer/filtering_cases_and_display_options.html>
- CSWeb Accessing Data / Data Settings — web UI shows dictionary list + Total/Processed counts
  only (no partial indicator). <https://www.csprousers.org/help/CSWeb/accessing_data.html>
- Survey Solutions (World Bank) HQ / Supervisor / Interviewer model; supervisor app as offline
  temporary storage + assignment distribution. <https://docs.mysurvey.solutions/supervisor/supervisor-app/>
- Arshan Khurshid CSPro tutorials (vault: `3_Resources/Learning-Materials/mentors/khurshid-arshad/videos/`)
  — role-based menu app; supervisor-held sync (`syncconnect` + `syncdata PUT`); supervisor-side
  sampling + file sync.
- Current ASPSI sync model: `deliverables/CSWeb/Field-Tablet-Sync-Configuration.md`;
  RBAC: `deliverables/CSWeb/CSWeb-User-Management-and-RBAC-Provisioning-Pack.md`.
