# Supervisor App — Phase 2 (Bluetooth Sync Hub + Field-Ops Role Menus) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **This plan is SPIKE-FIRST: Phase A spikes are gating; do not start a Phase-B task until its gating spike(s) PASS. If a spike fails, switch that track to its documented fallback before proceeding.**
>
> **REVISED 2026-06-25** — integrated the full field-ops **role-menu scope** (spec ADDENDUM-2: the Supervisor/Enumerator menus + N1–N4), added the **C7 on-device-map spike**, and **corrected the plan to what was actually built** (the `build_hub_apps.py` generator + flat `supervisor-hub/` layout — NOT the original `login/`+`menu/`+`roster/` subdir sketch). The original Jun-21 plan only built a flat collect/relay launcher; this revision aligns it with Carl's menu design.

**Goal:** Stand up the **supervisor-as-hub field-ops workflow** for a no/poor-internet cluster: a CSPro 8 login + **role-filtered menu** wraps the unmodified F1/F3/F4 + listing instruments, the supervisor **distributes EA/listing assignments** to enumerators and **collects cases back over Bluetooth** at a daily regroup, runs **advisory QA**, **relays to CSWeb** on signal, and both roles get **on-device reports + an on-device EA map** — all as a **dual-path fallback** that never disables the conflict-free direct-to-CSWeb sync.

**Architecture:** 3-tier supervisor-as-intermediary, benchmarked on **Survey Solutions HQ/Supervisor/Interviewer** + the **classic CSPro census enumeration menu** (spec ADDENDUM-2). Mapping: **CSWeb = HQ · supervisor hub = Supervisor app · enumerator = Interviewer app.** A login + menu app (`build_hub_apps.py`) routes by role and PFF-chain-launches the **unmodified** generator-built instruments. Case + assignment movement rides **CSEntry's built-in sync** (Bluetooth peer for hub↔enumerator; CSWeb for hub→server relay under `supervisor-qa`). On-device reports + map use logic-generated **HTML + `view()`** (the Phase-3 SupervisorApp mechanism). The Phase-1 Supervisor-QA Python report runs unchanged on the hub-collected `.csdb`.

**Tech Stack:** CSEntry 8.0 built-in Bluetooth/local sync · CSEntry CSWeb sync (`csweb.asiansocial.org`) · CSPro 8 Designer + `build_hub_apps.py` generator (login/menu apps: `.dcf`/`.fmf`/`.apc`/`.qsf`/`.ent`/`.pff`, `loadcase`/`savesetting`/`loadsetting`, `Pff` object, `execpff`, `setvalueset`) · the existing **PatientListing** app (chain-launched for N2) · an **assignment dictionary** (N1) · on-device `view()`+HTML reports/map (N3/N4) · itel tablets (AVD `capi_tablet`; `itel.py` driver) · the Phase-1 report at `deliverables/CSWeb/supervisor-app/` (reused, not modified).

## Global Constraints

- **Instruments + listing apps are NOT modified.** F1/F3/F4 + PatientListing generated `.dcf`/`.apc`/`.fmf`/`.qsf` are untouched; the menu app only **chain-launches** them (PFF/`execpff`). (Spec D6.)
- **Iron rule on the hub apps too:** never hand-edit the generated `supervisor-hub/*.dcf/.fmf/.qsf/.ent/.apc/.pff/.dat` — edit **`build_hub_apps.py`** and rerun.
- **No git commits / pushes.** Carl handles all git. End each task by leaving changes in the working tree.
- **Menus match spec ADDENDUM-2** (the exact Supervisor/Enumerator items + codes). The build target is that structure, not the v1 flat-6 launcher.
- **Dual-path / fallback (D1).** Direct enumerator→CSWeb stays default where signal exists; Bluetooth→hub is the no-signal + safety-net path. Never disable direct sync.
- **QA stays advisory (D2).** No write-back, no reject/reassign channel (the conscious divergence from Survey Solutions). The hub reviews; the enumerator fixes on their own device.
- **Case/assignment movement = CSEntry built-in sync (D3).** PROC `syncdata()`/`syncserver()`/`syncconnect()` is **rejected for primary case data** (#131). Fallback = manual export/import over OS Bluetooth file share.
- **Login is a local UX/identity gate, not security (D4).** Real auth is the CSWeb account; the roster password only routes the UX.
- **Hub relays under the existing `supervisor-qa` CSWeb role (D5).** No new CSWeb role.
- **Reuse the Phase-1 report tool unchanged** (`deliverables/CSWeb/supervisor-app/`).
- **On-device reports/map reuse the proven Phase-3 mechanism** — logic-generated HTML + `view()` (`Capture-Helpers.apc` / `SV/`), NOT a new rendering stack.
- **Conflict-free key:** every case is keyed by the 12-digit `RR-PP-MMM-FF-CCC` key; CSWeb upserts by key, so hub-relayed and direct-synced copies of the same case never conflict.
- **Security:** tablets encrypted + password-locked; supervisor visually confirms each Bluetooth pairing; **wipe collected copies after confirmed relay**.
- **DOH-Manual alignment caveat:** the supervisor-as-hub path diverges from the DOH-approved Manual (SEs sync direct). Dual-path keeps direct sync as default; **adopting the hub as the primary path needs ASPSI/DOH sign-off** (build the capability; the adoption call is theirs).
- **Device test harness:** itel `SER=091945939L000716` via `deliverables/CSPro/automation/itel.py`; emulator AVD `capi_tablet`; adb at `C:\Users\analy\AppData\Local\Android\Sdk\platform-tools\adb.exe`. **C2 + the integration tests need TWO CSEntry devices.**

## File Structure (ALIGNED TO REALITY — flat generator layout)

All hub artifacts live in `deliverables/CSPro/supervisor-hub/`, **generated by one script** `build_hub_apps.py` (flat layout so `execpff`/sibling-`.pff` paths resolve). The original plan's `login/`+`menu/`+`roster/` subdirs were a sketch and are SUPERSEDED.

- `build_hub_apps.py` — **single generator** for LoginApp + MenuApp + UserRoster (BUILT). To extend: edit here, rerun, recompile, redeploy via `deploy_hub_bundle.py`.
- `LoginApp.{dcf,fmf,ent.apc,ent.qsf,ent.mgf,ent,pff}` — login app (BUILT, deployed).
- `MenuApp.{dcf,fmf,ent.apc,ent.qsf,ent.mgf,ent,pff}` — role-routing menu (BUILT v1; **restructure target** = ADDENDUM-2 menus).
- `UserRoster.{dcf,dat}` — login roster, external dict (BUILT; placeholder `changeme*` creds).
- `deploy_hub_bundle.py` — deploys the Login+Menu+roster bundle to CSWeb as one package (BUILT).
- `spikes/C1-login-menu-spike.md` — C1 spike record (PASS, device-confirmed).
- `spikes/C2-bluetooth-spike.md` — **NEW** (Task A2): Bluetooth spike procedure + verdict.
- `spikes/C7-map-spike.md` — **NEW** (Task A3): on-device map feasibility spike + verdict.
- `Assignment.{dcf,dat}` — **NEW** (Task B3): EA/cluster→enumerator + patient pre-list assignment dict.
- `config/enumerator-bluetooth-sync.md` — **NEW** (Task B6): enumerator "send to supervisor" SOP.
- `config/hub-collect-and-relay.md` — **NEW** (Task B7): hub collect + CSWeb relay SOP.
- `qa/run-on-hub.md` — **NEW** (Task B8): on-hub QA (reuse Phase-1).
- `reports/` — **NEW** (Task B2/N4): on-device listing/interview report templates (HTML + `view()` logic in the generator).
- `map/` — **NEW** (Task B9/N3): EA KML/base-map assets + `view()` wiring (gated on C7).
- `README.md` — **NEW** (Task B10): deployment + field SOP runbook.
- `spikes/E2E-integration-result.md` — **NEW** (Task B11): acceptance result.

**Reused unchanged:** `deliverables/CSWeb/supervisor-app/` (Phase-1 report + `pytest` suite); the **PatientListing** + F1/F3/F4 deployed apps.

---

## SPIKE STATUS (2026-06-25)

- **C1 (login/menu) = PASS — device-confirmed** on the itel. `loadcase` auth, `savesetting`/`loadsetting` cross-app role handoff, `execpff` chain-launch, role-filtered menu (`setvalueset`), and OnExit return-to-menu (`Pff` object) all work on CSPro 8 + CSEntry. Built by `build_hub_apps.py`; full chain Login→Menu→real instrument→back device-confirmed. **v1 re-deployed to production CSWeb 2026-06-25.** Record: `spikes/C1-login-menu-spike.md`.
  - **API LOCKED by C1:** chain-launch = `execpff("<app>.pff", stop)`; return-to-menu = `Pff p; p.load("../<App>/<App>.pff"); p.setProperty("OnExit","../LoginApp/MenuApp.pff"); p.exec();`. CSEntry installs each app at a STABLE sibling folder `…/files/csentry/<App>/`; the running MenuApp sits in `…/csentry/LoginApp/`, so instruments resolve via `../<App>/<App>.pff` (no co-bundle, no drift). The original plan's `PFF.setProperty/.execute` sketch is WRONG — use the above.
- **C2 (Bluetooth one-host-from-many) = PENDING** — needs **2 physical CSEntry devices** (Carl has a 2nd tablet). Make-or-break for collect/relay (C2/C3) AND assignment distribution (N1) AND listing exchange (N2). Until it runs, those tasks are blocked or on the manual-file-share fallback.
- **C7 (on-device map, N3) = NOT RUN** — new feasibility spike; gates N3 only.

---

## Menu design (the build target — from spec ADDENDUM-2)

Role-filtered via `setvalueset` on `MENU_CHOICE` (enumerators see only their items; the v1 mechanism). Exact items + codes:

**Supervisor (`ROLE = supervisor`):** 1 Assign Enumeration Area · 2 Listing Data (receive→relay→report) · 3 Survey Interview (receive→relay→report) · 4 View EA on Map · 5 Close.
**Enumerator (`ROLE = enumerator`):** 1 Listing Exercise (receive EA→list→send→report) · 2 Receive Assigned Data (Patient) · 3 Survey Interview (conduct→send→report) · 4 View EA on Map · 5 Close.

Open point (confirm at Task B1): keep a supervisor "launch F1/F3/F4 for spot-check" entry (v1 had it) — default = retain as a 6th supervisor item.

---

# PHASE A — Gating spikes (Phase-B tasks are blocked until their gate PASSes)

### Task A1: C1 — login/menu app on CSPro 8 — ✅ DONE (PASS)

Built via `build_hub_apps.py`; device-confirmed; re-deployed 2026-06-25. No action — recorded for completeness. Findings: `spikes/C1-login-menu-spike.md`.

### Task A2: C2 spike — CSEntry built-in Bluetooth sync (one-host-from-many + primary case data)

**Files:** Create `deliverables/CSPro/supervisor-hub/spikes/C2-bluetooth-spike.md`.
**Gates:** B4 (N1), B5 (N2), B6, B7, B11. On FAIL → those tasks adopt the **manual file-share fallback**.
**Why first:** the entire hub data-exchange depends on whether CSEntry's *built-in* sync moves *primary case data* device-to-device over Bluetooth in a *one-host-from-many* pattern. PROC sync can't (#131) — this is the make-or-break.

- [ ] **Step 1 — Write PASS/FAIL criteria** into `spikes/C2-bluetooth-spike.md`:
  1. On the host (supervisor) device, CSEntry's Synchronize offers a Bluetooth/local peer target (not only CSWeb/Dropbox/FTP), and the host can RECEIVE.
  2. An enumerator device syncs PRIMARY case data (a real F3 case, not just an external dict) to the host over Bluetooth, with NO internet on either device.
  3. A SECOND enumerator device syncs to the SAME host; the host accumulates BOTH, keyed distinctly by their 12-digit keys (one-host-from-many).
  4. NON-DESTRUCTIVE: the enumerator's original case remains after sync.
- [ ] **Step 2 — Stand up two CSEntry devices** (itel + emulator, or two tablets); install F3; capture a case on each with distinct keys (`010280001001` / `010280002001`).
- [ ] **Step 3 — Attempt host receive over Bluetooth** (Wi-Fi/data OFF). Record the exact CSEntry sync menu path + which server types appear + whether the host can act as receiver.
- [ ] **Step 4 — Verify accumulation + non-destructiveness** (host shows both keys; enumerator keeps its own). Screenshot.
- [ ] **Step 5 — Record `C2 = PASS|FAIL`** + findings. On FAIL, document the manual-file-share fallback verbatim. **Do not start C2-gated Phase-B tasks until PASS or the fallback is adopted.**

### Task A3: C7 spike — on-device EA map (`view()` of an offline KML/HTML map) — NEW (gates N3)

**Files:** Create `deliverables/CSPro/supervisor-hub/spikes/C7-map-spike.md`.
**Gates:** B9 (N3 map). On FAIL → N3 degrades to "open the CSWeb Map Report when on signal" (no on-device map) and/or a static coordinates list.
**Why:** N3 ("View EA on Google Earth / on map") needs CSEntry to render an EA boundary + captured GPS **offline on the device**. Confirm the mechanism before building menu wiring around it.

- [ ] **Step 1 — Write PASS/FAIL criteria** into `spikes/C7-map-spike.md`:
  1. CSEntry can `view()` a generated **offline** map artifact (KML opened by a map viewer, or a self-contained HTML/Leaflet map with embedded tiles/coords) from logic, with no internet.
  2. The map can plot the **EA boundary** (from a "set map file" KML) AND **captured case GPS points** (from the `.csdb` LATITUDE/LONGITUDE).
  3. It renders acceptably on the itel screen (800×1280) and returns to the menu on close.
- [ ] **Step 2 — Build a minimal map artifact** (a tiny KML or self-contained HTML with 2–3 hard-coded points) + a one-field test app that `view()`s it.
- [ ] **Step 3 — Run on the itel offline**; screenshot what renders.
- [ ] **Step 4 — Record `C7 = PASS|FAIL`** + the exact working mechanism (KML-viewer intent vs embedded-HTML) or the fallback. **N3 (B9) is blocked until PASS or the fallback is adopted.**

---

# PHASE B — Build (each task gated as noted; build top-down)

> **Buildable NOW (no spike):** B1 menu restructure, B2 N4 reports, B3 assignment-dict design, B8 on-hub QA wiring, B10 README scaffold.
> **Gated on C2:** B4 (N1 distribution), B5 (N2 listing exchange), B6, B7, B11.
> **Gated on C7:** B9 (N3 map).

### Task B1: Menu restructure — flat-6 → the ADDENDUM-2 role menus  *(no spike)*

**Files:** Edit `build_hub_apps.py` (`MENU_OPTIONS`, `MENU_APC`); regenerate `MenuApp.*`.
**What:** Replace the v1 flat 6-item launcher with the two role menus (spec ADDENDUM-2). Supervisor: Assign EA / Listing Data / Survey Interview / View Map / Close (+ optional spot-check launch). Enumerator: Listing Exercise / Receive Assigned Data / Survey Interview / View Map / Close. Keep the proven plumbing: role read via `loadsetting("hub_role")`, role-filter via `setvalueset`+`ValueSet.remove`, instrument launch via the `Pff`-object OnExit pattern, return-to-menu.
**Acceptance:** recompile clean (`cspro_compile_driver.py MENU`); LoginApp publishes; on device, `fs-01` sees the 5 supervisor items, `se-004` sees the 5 enumerator items; each item routes to the right action (launch/stub-pending-its-task). Items whose backend isn't built yet show a clear "pending" `errmsg` (not a dead tap).
- [ ] Confirm the open design point (supervisor spot-check launch: keep/where) with Carl before finalizing codes.

### Task B2: N4 — per-role on-device reports (listing report + interview report)

**Status (2026-06-25):** report ENTRY POINTS built — the menu's "view report" items (supervisor
02/03, enumerator 17) display a per-role on-device report via `errmsg` (proven mechanism). **CORRECTION
to the earlier "reuse Phase-3 view()+HTML" assumption:** the Phase-3 `view()` displays a binary photo
**IMAGE**, NOT generated HTML (`SV/SupervisorApp.ent.apc` `VERIFICATION_PHOTO_IMAGE.view()`). There is
**no proven on-device HTML-report mechanism in the repo**, so the rich HTML/live-coverage version is
NOT no-spike — it needs:
- **a small feasibility spike** (call it **C8**): can CSEntry write a generated HTML file in logic and
  `view()` it (or render it via a CSPro 8 HTML dialog) offline on the itel? Fallback = the `errmsg`
  text report (already built) or the at-base laptop report (B8).
- **the C2-collected data** for the live assigned-vs-collected / captured-vs-target counts.

**Files:** `build_hub_apps.py` (`MENU_APC` report items — DONE); `supervisor-hub/reports/` (HTML
templates — deferred to C8).
**What's left (gated on C8 + C2):** upgrade the entry-point `errmsg` to a rendered HTML report over the
device's own (enumerator) / hub-collected (supervisor) `.csdb`, with the Phase-1 metric definitions.
**Acceptance (built part):** the menu "view report" items show a role-correct on-device message
confirming the report surface, offline, returning to the menu (device-confirm at deploy). **Acceptance
(C8 part):** a generated HTML report renders on-device, PII-light.

### Task B3: Roster + assignment dictionary  *(dict design no-spike; distribution = B4)*

**Files:** `build_hub_apps.py` (roster already built); add `Assignment.{dcf,dat}`.
**What:** Keep `UserRoster` (login). Add an **Assignment dict** keyed by EA/cluster → `ENUMERATOR_ID`, `FACILITY_CODE`, `INSTRUMENT`, `TARGET_COUNT`, + the **patient pre-list** rows (the listing output that becomes the enumerator's assigned interview targets). Confirm in build whether to merge with the Phase-1 assignment lookup (spec C5 "likely merged").
**Acceptance:** `loadcase(Assignment, <ea>)` returns the EA's enumerator + targets; structure validated in Designer; seed `.dat` loads.

### Task B4: N1 — EA/assignment distribution (supervisor → enumerator)  *(gated: C2)*
**Files:** `build_hub_apps.py` (supervisor "Assign EA" + enumerator "Receive Assigned Data" actions); `config/` SOP.
**What:** Supervisor picks an EA → pushes the Assignment dict (+ patient pre-list) to the enumerator over the **same C2 transport, reverse direction** (Survey Solutions "assignment distribution"). Enumerator's "Receive Assigned Data (Patient)" pulls it in. On C2 FAIL → manual file-share of the assignment `.dat`.
**Acceptance:** supervisor assigns EA X to `se-004`; on `se-004`'s device, "Receive Assigned Data" loads EA X's targets; verified on 2 devices.

### Task B5: N2 — listing as a structured step  *(gated: C2)*
**Files:** `build_hub_apps.py` (enumerator "Listing Exercise" wiring); `config/`.
**What:** Enumerator "Listing Exercise" → receive assigned EA (B4) → **chain-launch the existing PatientListing app** (unmodified) → send the listing `.csdb` to the supervisor over Bluetooth → the supervisor compiles the cumulative listing and (B4) sends back the assigned patients. Listing→assignment handoff ties to B3/B4.
**Acceptance:** end-to-end on 2 devices: assign EA → enumerator lists → listing reaches supervisor → supervisor relays cumulative listing → assigned patients return to the enumerator. PatientListing's own files unchanged.

### Task B6: Enumerator "Send to Supervisor" Bluetooth config + SOP  *(gated: C2)*
**Files:** `config/enumerator-bluetooth-sync.md`.
**What:** Document the exact CSEntry steps the C2 spike proved (OS Bluetooth pairing → CSEntry Sync → the Bluetooth peer target → send F1/F3/F4 + listing to the hub; non-destructive). On C2 FAIL → the manual file-share fallback verbatim.
**Acceptance:** one device follows ONLY the written steps and reaches the hub; no undocumented tap.

### Task B7: Hub collection + CSWeb relay (under `supervisor-qa`) + SOP  *(gated: C2)*
**Files:** `config/hub-collect-and-relay.md`.
**What:** Hub receive (accumulate each enumerator's F1/F3/F4 + listing); then CSEntry → CSWeb sync under the **`supervisor-qa`** account when on signal. State the conflict-free upsert-by-key property verbatim. Smart-sync moves only new/changed.
**Acceptance:** after a collection, relay; cases appear in CSWeb (Data tab/Sync Report) under the expected keys; record counts.

### Task B8: On-hub QA — reuse the Phase-1 report on collected data  *(reuse; no spike)*
**Files:** `qa/run-on-hub.md`. **Reuses** `deliverables/CSWeb/supervisor-app/` UNCHANGED.
**What:** Confirm the Phase-1 `pytest` is green (`14 passed`); document export of the hub-collected `.csdb` → CSV → `supervisor_qa_report.py … --out supervisor-qa.html` (same command as Phase-1; only the export source differs). PII-light; advisory (D2).
**Acceptance:** run on collected cases → HTML shows coverage/partials/flags, no respondent names (`grep` the HTML).

### Task B9: N3 — on-device EA map wiring  *(gated: C7)*
**Files:** `build_hub_apps.py` (the "View EA on Map" menu action), `map/` assets.
**What:** Wire both roles' "View EA on Map" to the C7-proven mechanism: load the EA map file (KML), plot captured GPS, view offline. On C7 FAIL → degrade to the CSWeb Map Report link (on signal) + a static coordinate list.
**Acceptance:** from the menu, the map renders the EA + case points offline and returns to the menu.

### Task B10: Security & deployment SOP runbook  *(no spike; finalize after others)*
**Files:** `supervisor-hub/README.md`.
**What:** Sections — What this is (Phase-2 hub + role menus, dual-path); Spike gates (C1 PASS / C2 / C7 + which fallback if failed); Deployment (`build_hub_apps.py` → compile → `deploy_hub_bundle.py`; ship `UserRoster.dat` + `Assignment.dat`; the `supervisor-qa` account on the hub); Daily field SOP (login → assign/receive → list → interview → regroup collect → on-hub QA → relay); Security (C6: encryption, visual pairing confirm, wipe-after-relay; login = UX not security); Limits (~10m Bluetooth range; never-regroup → direct sync).
**Acceptance:** every referenced file/command/account/role matches the built artifacts.

### Task B11: End-to-end integration acceptance  *(gated: B1–B10 + C2)*
**Files:** `spikes/E2E-integration-result.md`.
**What:** 2 enumerators (`se-004`,`se-011`) + 1 hub (`fs-01`), offline. Supervisor assigns EAs → enumerators list + interview → Bluetooth send to hub → on-hub QA → relay to CSWeb. Then prove dual-path: `se-004` ALSO direct-syncs one case → CSWeb shows each key exactly once (upsert).
**Acceptance:** recorded counts + the dual-path no-conflict observation + a report/map screenshot + any SOP gaps fixed.

---

## Dependency / gating summary

```
A1 C1  ✅ DONE ───────────────────────────────► B1 menu restructure ─► B2 N4 reports ─► B10 README ─► B11 E2E
A2 C2  ⏳ (2 devices) ──► B4 N1 ─► B5 N2 ─► B6 ─► B7 ─────────────────────────────────────────────────► B11
A3 C7  🆕 ────────────────────────────────────► B9 N3 map ───────────────────────────────────────────► B11
                                                B3 assignment dict (now) ─► B4
                                                B8 on-hub QA (reuse, now)
```

**Start order when building begins:** B1 + B2 + B3 + B8 (no spikes) in parallel-ish; run A2 (C2) + A3 (C7) as devices/time allow; then the C2-gated chain (B4→B7) and C7-gated B9; finish with B10 + B11.

---

## Self-Review

**Spec coverage (incl. ADDENDUM-2):** D1 dual-path → B6/B7/B11. D2 advisory QA → B8 + README. D3 CSEntry built-in + manual fallback → A2 + B6/B7. D4 login/role gate → A1 + B1. D5 relay under supervisor-qa → B7. D6 instruments+listing unmodified (chain-launch) → B1/B5. D7 deferred trigger → header. N1 → B4. N2 → B5. N3 → A3 + B9. N4 → B2. Menu structure → B1. Benchmark → spec ADDENDUM-2. Conflict-free upsert-by-key → B7 + B11.

**Reality alignment:** file structure + statuses corrected to the `build_hub_apps.py` flat generator and the C1-PASS API (`execpff`/`Pff`-object, sibling `.pff`); the superseded `login/menu/roster` subdir sketch + the `PFF.setProperty/.execute` code are removed.

**Placeholder scan:** no "TBD"; `<ea>`/`<YYYYMMDD>` are runtime args; spike fallbacks are concrete.

**TDD adaptation:** device/Designer/ops work — "tests" are device-verification steps with explicit PASS criteria + screenshots; the three spikes (C1✅/C2/C7) are the risk gates; the one unit-tested component (Phase-1 report) is reused unchanged and re-run, not rewritten.

**Git:** per Global Constraints, no task commits — leave the working tree changed (Carl commits).
