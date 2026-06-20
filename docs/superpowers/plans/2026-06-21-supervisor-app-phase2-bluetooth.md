# Supervisor App — Phase 2 (Bluetooth Sync Hub) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **This plan is SPIKE-FIRST: Phase A (Tasks 1–2) are gating feasibility spikes; do not start Phase B (Tasks 3–10) until both spikes PASS. If a spike fails, switch that track to its documented fallback before proceeding.**

**Goal:** Let a field cluster get cases off enumerator tablets the same day with no internet — enumerators Bluetooth-sync to the supervisor's "hub" tablet at a daily regroup; the hub relays to CSWeb when it reaches signal — as a dual-path fallback that preserves the conflict-free direct-to-CSWeb sync.

**Architecture:** 3-tier supervisor-as-intermediary. A CSPro 8 **login + menu app** (Khurshid pattern) wraps the unmodified generator-built F1/F3/F4 instruments via PFF chain-launch and routes by role (enumerator vs supervisor). Case movement uses **CSEntry's built-in sync** with a Bluetooth peer server type (enumerator→hub) and CSWeb (hub→CSWeb relay under `supervisor-qa`). The Phase-1 Supervisor-QA Python report runs unchanged on the hub-collected `.csdb`.

**Tech Stack:** CSEntry 8.0 built-in Bluetooth/local sync · CSEntry CSWeb sync (`csweb.asiansocial.org`) · CSPro 8 Designer (login/menu app: `.dcf`/`.fmf`/`.apc`, PFF objects, `loadcase`/`savesetting`/`loadsetting`) · itel tablets (AVD `capi_tablet` for emulation; `itel.py` driver) · the Phase-1 Python report at `deliverables/CSWeb/supervisor-app/` (reused, not modified).

## Global Constraints

- **Instruments are NOT modified.** F1/F3/F4 generated `.dcf`/`.apc`/`.fmf`/`.qsf` are untouched; the login/menu app only **chain-launches** them via PFF. (Spec D6.)
- **No git commits / pushes.** Carl handles all git. End each task by leaving changes in the working tree — no `git add`/`commit`.
- **Dual-path / fallback (D1).** Direct enumerator→CSWeb stays the default where signal exists; Bluetooth→hub is the no-signal + safety-net path. Never disable direct sync.
- **QA stays advisory (D2).** No write-back, no reject/reassign channel. The hub reviews; the enumerator fixes on their own device.
- **Mechanism = CSEntry built-in Bluetooth sync (D3).** PROC `syncdata()`/`syncserver()`/`syncconnect()` is **rejected for primary case data** (per #131 — in CSPro 8 `syncdata()` syncs external dicts only). Fallback = manual export/import over OS Bluetooth file share.
- **Login is a local UX/identity gate, not security (D4).** The real credentialed login is the CSWeb account. The roster password lives in an on-device dictionary and only routes the UX.
- **Hub relays under the existing `supervisor-qa` CSWeb role (D5).** No new CSWeb role.
- **Reuse the Phase-1 report tool unchanged** (`deliverables/CSWeb/supervisor-app/`). Do not fork or edit it.
- **Conflict-free key:** every case is keyed by the 12-digit `RR-PP-MMM-FF-CCC` key; CSWeb upserts by key, so hub-relayed and direct-synced copies of the same case never conflict.
- **Security:** tablets encrypted + password-locked; supervisor visually confirms each Bluetooth pairing; **wipe collected copies after confirmed relay**.
- **Build deferred (D7):** this plan is written now; execution waits until F1/F3/F4 are near-zero UAT bugs.
- **Device test harness:** itel `SER=091945939L000716` via `deliverables/CSPro/automation/itel.py`; emulator AVD `capi_tablet`. ADB at `C:\Users\analy\AppData\Local\Android\Sdk\platform-tools\adb.exe`. A spike needs **two** CSEntry devices (two emulators, or itel + emulator, or two physical tablets).

## File Structure

All new artifacts under `deliverables/CSPro/supervisor-hub/` (a NEW app dir; not a generator and not part of the instrument build):

- `spikes/C2-bluetooth-spike.md` — C2 spike procedure + recorded PASS/FAIL result + findings.
- `spikes/C1-login-menu-spike.md` — C1 spike procedure + recorded PASS/FAIL result + findings.
- `roster/UserRoster.dcf` — the `USERNAME_PASSWORD_DICT` external dictionary (login roster).
- `roster/UserRoster.csv` — sample/seed roster (converted to `.dat` for the device).
- `login/LoginApp.dcf`, `login/LoginApp.fmf`, `login/LoginApp.apc` — the login application.
- `menu/MenuApp.dcf`, `menu/MenuApp.fmf`, `menu/MenuApp.apc` — the role-routing menu application.
- `config/enumerator-bluetooth-sync.md` — CSEntry "Sync to Supervisor" (Bluetooth peer) config + SOP.
- `config/hub-collect-and-relay.md` — hub-side collection + CSWeb relay (`supervisor-qa`) config + SOP.
- `qa/run-on-hub.md` — how the hub exports its collected `.csdb` and runs the Phase-1 report (reuse).
- `README.md` — the deployment + field SOP runbook (security, pairing, wipe-after-relay).

**Reused unchanged:** `deliverables/CSWeb/supervisor-app/` (Phase-1 report + its `pytest` suite).

---

# PHASE A — Gating spikes (do these first; Phase B is blocked until both PASS)

### Task 1: C2 spike — CSEntry built-in Bluetooth sync (one-host-collects-from-many + primary case data)

**Files:**
- Create: `deliverables/CSPro/supervisor-hub/spikes/C2-bluetooth-spike.md`

**Interfaces:**
- Produces: a recorded verdict `C2 = PASS | FAIL` plus findings, consumed by every Phase-B collection task (6, 7, 10). On FAIL, Phase B switches to the manual-file-share fallback (documented in this task).

**Why first:** the entire hub depends on whether CSEntry's *built-in* sync can move *primary case data* between devices over Bluetooth in a *one-host-from-many* pattern. PROC-code sync can't (Global Constraint / #131), so this is the make-or-break test.

- [ ] **Step 1: Write the spike's PASS/FAIL criteria into the spike doc** (define the acceptance before testing)

Create `spikes/C2-bluetooth-spike.md` with this exact criteria block:

```markdown
# C2 spike — CSEntry built-in Bluetooth sync

## PASS criteria (ALL must hold)
1. On the supervisor (host) device, CSEntry's Synchronize offers a Bluetooth / local
   peer target (not only CSWeb/Dropbox/FTP), and the host can RECEIVE.
2. An enumerator device can sync its PRIMARY case data (a real F3 PatientSurvey case,
   not just an external dict) to the host over Bluetooth, with NO internet on either device.
3. A SECOND enumerator device can sync to the SAME host, and the host accumulates BOTH
   devices' cases (one-host-from-many), keyed distinctly by their 12-digit keys.
4. The transfer is NON-DESTRUCTIVE: the enumerator's original case remains on the
   enumerator device after the sync.

## FAIL → fallback
If any of 1–4 fails, C2 = FAIL. Phase B uses the MANUAL FILE-SHARE fallback:
enumerator exports the instrument's data file (CSEntry → app → Export, or share the
.csdb) → OS Bluetooth file transfer → supervisor imports into the hub's local data for
that instrument → relay. Record exactly which of 1–4 failed and why.
```

- [ ] **Step 2: Stand up two CSEntry devices with F3 deployed**

Run (emulator route): start two AVD instances, or `capi_tablet` + the physical itel.
```
"C:\Users\analy\AppData\Local\Android\Sdk\platform-tools\adb.exe" devices
```
Expected: at least two devices/emulators listed. Install CSEntry + deploy F3 (PatientSurvey) to both via CSWeb Add Application (per `project_aspsi_csentry_update_propagation` — remove+re-add, not ⋮ Update). Capture one F3 case on each device (use demo QN `010280001001` on device A, `010280002001` on device B so keys differ).

- [ ] **Step 3: Attempt host (supervisor) receive over Bluetooth**

On device A (host): CSEntry → Sync → inspect available server types. Pair A↔B over Android Bluetooth first (OS-level). Attempt a local/Bluetooth sync of F3 from device B → device A with Wi-Fi/data OFF on both.
Record in the spike doc: which sync server types CSEntry offers, the exact menu path, and whether the host can act as receiver.

- [ ] **Step 4: Verify accumulation + non-destructiveness**

After B→A sync, on device A open the F3 case list. Then sync a second device (or re-image B with key `010280002001`) → A.
Expected (PASS): device A's F3 list shows BOTH `010280001001` and `010280002001`; device B still shows its own case. Screenshot both. If the host cannot receive, or only 1:1 works, or it moves only external dicts → mark the failing criterion.

- [ ] **Step 5: Record the verdict**

Write `C2 = PASS` or `C2 = FAIL` at the top of `spikes/C2-bluetooth-spike.md` with the screenshots referenced and a one-paragraph finding. Leave the working tree changed (Carl commits). **Do not start Phase-B collection tasks until this reads PASS — or until the fallback is explicitly adopted.**

---

### Task 2: C1 spike — login/menu app on CSPro 8 (PFF chain-launch + savesetting/loadsetting + loadcase)

**Files:**
- Create: `deliverables/CSPro/supervisor-hub/spikes/C1-login-menu-spike.md`

**Interfaces:**
- Produces: a recorded verdict `C1 = PASS | FAIL` consumed by Tasks 3–5. On FAIL, Phase B drops the app-login (skip Tasks 3–5) and differentiates roles by **CSWeb account only** (the enumerator runs the instrument directly as today; the supervisor uses the `supervisor-qa` account + the hub relay/QA — Tasks 7–8 still apply).

**Why:** Khurshid's login+menu pattern is CSPro 7.7-era; this confirms `loadcase` auth, `savesetting`/`loadsetting` handoff, and `Pff.execute()` chain-launch all work on CSPro 8 + itel.

- [ ] **Step 1: Write the PASS/FAIL criteria into the spike doc**

Create `spikes/C1-login-menu-spike.md`:

```markdown
# C1 spike — login/menu app on CSPro 8

## PASS criteria (ALL must hold)
1. A minimal LoginApp authenticates a username/password against an external roster
   dictionary via loadcase() (correct creds accept; wrong creds re-enter).
2. On success, savesetting("role", ...) persists, and a separate MenuApp reads it via
   loadsetting("role") after launch.
3. The MenuApp's PFF object chain-launches a target .pen (use the deployed F3
   PatientSurvey.pen) via Pff.setProperty(...) + Pff.execute(), and OnExit returns to the menu.
4. All three compile in CSPro 8 Designer AND run on the itel/emulator (not just compile).

## FAIL → fallback
If chain-launch or savesetting/loadsetting does not work on CSPro 8/itel, C1 = FAIL.
Phase B skips the app-login (Tasks 3–5); roles are distinguished by CSWeb account only.
Record which CSPro 8 API differs from Khurshid's 7.7 example.
```

- [ ] **Step 2: Build a minimal LoginApp in Designer**

In CSPro 8 Designer, create `supervisor-hub/login/LoginApp` with a dictionary holding `LOGIN_USERNAME` (alpha 20) and `LOGIN_PASSWORD` (alpha 20) on one form, and add the roster external dict (Task 3's `UserRoster`, or a 2-row stub for the spike: one enumerator, one supervisor). Paste this auth logic into the password field postproc:

```
PROC LOGIN_PASSWORD
postproc
  if loadcase(UserRoster, LOGIN_USERNAME) then
    if UserRoster.PASSWORD = LOGIN_PASSWORD then
      savesetting("role", UserRoster.ROLE);
      savesetting("operator_id", UserRoster.OPERATOR_ID);
      savesetting("cluster", UserRoster.CLUSTER);
    else
      errmsg("Incorrect password."); reenter;
    endif;
  else
    errmsg("Unknown username."); reenter;
  endif;
```

- [ ] **Step 3: Build a minimal MenuApp that reads the role and chain-launches**

Create `supervisor-hub/menu/MenuApp` with this logic (level preproc + a launch action):

```
PROC GLOBAL
  PFF target_pff;
  alpha(20) m_role;

PROC MENUAPP_LEVEL
preproc
  m_role = loadsetting("role");

PROC MENU_GO          { a single numeric field: 1=launch F3 }
postproc
  target_pff.setProperty("Version", "CSPro 8.0");
  target_pff.setProperty("ApplicationType", "entry");
  target_pff.setProperty("StartMode", "add");
  target_pff.setProperty("Application", "..\\..\\F3\\PatientSurvey.pen");
  target_pff.setProperty("OnExit", "..\\menu\\MenuApp.pff");
  target_pff.execute();
```

- [ ] **Step 4: Compile + run both on device**

Compile all three apps (Designer Ctrl+L, then Publish packager — the strict gate; see [[reference_capi_multiselect_skill]] lenient-vs-strict lesson). Deploy/sideload to the emulator. Run LoginApp → enter the supervisor stub creds → confirm it accepts and the MenuApp opens showing `m_role = "supervisor"` (display it via a protected field or errmsg) → trigger MENU_GO → confirm F3 launches and OnExit returns to the menu.

- [ ] **Step 5: Record the verdict**

Write `C1 = PASS` or `C1 = FAIL` with findings into `spikes/C1-login-menu-spike.md`. Leave the working tree changed. **Do not start Tasks 3–5 until this reads PASS** (else use the CSWeb-account-only fallback).

---

# PHASE B — Build (gated: start only after Task 1 AND Task 2 PASS)

### Task 3: USERNAME_PASSWORD_DICT roster dictionary + seed data

**Gated on:** Task 2 PASS (else skip — fallback uses CSWeb accounts only).

**Files:**
- Create: `deliverables/CSPro/supervisor-hub/roster/UserRoster.dcf`
- Create: `deliverables/CSPro/supervisor-hub/roster/UserRoster.csv`

**Interfaces:**
- Produces: external dict `UserRoster` keyed by `LOGIN_USERNAME` (alpha 20), with items `PASSWORD` (alpha 20), `ROLE` (alpha 20: `enumerator`|`supervisor`), `OPERATOR_ID` (alpha 20 — the field ID, e.g. `se-004`/`fs-01`), `CLUSTER` (alpha 10). Consumed by Task 4 (`loadcase(UserRoster, LOGIN_USERNAME)`) and Task 5 (`UserRoster.ROLE`).

- [ ] **Step 1: Define the verification (a load check)**

The dictionary is correct when CSPro can `loadcase` a known username and read its role. Acceptance: a roster row `fs-01,pw,supervisor,fs-01,01028` loads and `UserRoster.ROLE = "supervisor"`. (Verified at runtime in Task 4 — here, confirm the dict structure + sample parse.)

- [ ] **Step 2: Author the roster dictionary**

Create `roster/UserRoster.dcf` as a single-level external dictionary (external dicts are single-level — Khurshid Tutorial 1). Record `USER_REC` with key item `LOGIN_USERNAME` (alpha, len 20, ID) and items `PASSWORD` (alpha 20), `ROLE` (alpha 20), `OPERATOR_ID` (alpha 20), `CLUSTER` (alpha 10). Use the existing dcf JSON shape of any external dict in the repo (e.g. `deliverables/CSPro/F1/facility_lookup.dcf`) as the structural template — same `levels`/`records`/`items` layout, alpha items, `LOGIN_USERNAME` as the sole ID.

- [ ] **Step 3: Seed sample roster data**

Create `roster/UserRoster.csv`:

```csv
LOGIN_USERNAME,PASSWORD,ROLE,OPERATOR_ID,CLUSTER
se-004,changeme04,enumerator,se-004,01028
se-011,changeme11,enumerator,se-011,01028
fs-01,changeme-fs,supervisor,fs-01,01028
```

- [ ] **Step 4: Convert CSV → CSPro `.dat` for the device**

In Designer, use the dictionary's data tooling (or Tools → Excel/CSV import per Khurshid Tutorial 2) to produce `UserRoster.dat` keyed by `LOGIN_USERNAME`. Confirm 3 cases load. Leave the working tree changed.

- [ ] **Step 5: Confirm a load**

In a Designer test (or the Task-4 app), `loadcase(UserRoster, "fs-01")` then check `UserRoster.ROLE`.
Expected: returns true; `ROLE = "supervisor"`. Record in `qa/run-on-hub.md` notes if needed.

---

### Task 4: Login app (loadcase auth + role savesetting)

**Gated on:** Task 2 PASS. **Consumes:** `UserRoster` (Task 3).

**Files:**
- Create: `deliverables/CSPro/supervisor-hub/login/LoginApp.dcf`
- Create: `deliverables/CSPro/supervisor-hub/login/LoginApp.fmf`
- Create: `deliverables/CSPro/supervisor-hub/login/LoginApp.apc`

**Interfaces:**
- Consumes: `loadcase(UserRoster, LOGIN_USERNAME)` and `UserRoster.PASSWORD/ROLE/OPERATOR_ID/CLUSTER` (Task 3).
- Produces: on success, `savesetting("role"|"operator_id"|"cluster", …)` for Task 5; chain-launches `MenuApp` (Task 5) via a PFF.

- [ ] **Step 1: Define the acceptance**

LoginApp is correct when: a valid `fs-01`/`changeme-fs` accepts and launches the menu with role `supervisor`; a wrong password re-enters with "Incorrect password."; an unknown username re-enters with "Unknown username." (Verified on device in Step 4.)

- [ ] **Step 2: Build the login form + dictionary**

In Designer create `login/LoginApp` with main dict items `LOGIN_USERNAME` (alpha 20) and `LOGIN_PASSWORD` (alpha 20) on one form `F_login_form`; add `UserRoster` as an external dictionary (File → add external dictionary). (Mirrors Khurshid Tutorial 1/3.)

- [ ] **Step 3: Write the auth + handoff + launch logic**

Put this in `LoginApp.apc`:

```
PROC GLOBAL
  PFF menu_pff;

PROC LOGIN_PASSWORD
postproc
  if loadcase(UserRoster, LOGIN_USERNAME) then
    if UserRoster.PASSWORD = LOGIN_PASSWORD then
      savesetting("role", UserRoster.ROLE);
      savesetting("operator_id", UserRoster.OPERATOR_ID);
      savesetting("cluster", UserRoster.CLUSTER);
      menu_pff.setProperty("Version", "CSPro 8.0");
      menu_pff.setProperty("ApplicationType", "entry");
      menu_pff.setProperty("StartMode", "add");
      menu_pff.setProperty("Application", "..\\menu\\MenuApp.pen");
      menu_pff.setProperty("OnExit", "..\\login\\LoginApp.pff");
      menu_pff.execute();
    else
      errmsg("Incorrect password."); reenter;
    endif;
  else
    errmsg("Unknown username."); reenter;
  endif;
```

- [ ] **Step 4: Compile, publish, run on device**

Compile (Ctrl+L) → strict Publish packager → sideload/deploy to the emulator. Run: enter `fs-01`/`changeme-fs` → MenuApp opens. Enter `fs-01`/`wrong` → "Incorrect password." + re-enter. Enter `zzz`/`x` → "Unknown username." + re-enter. Screenshot each. Leave the working tree changed.

---

### Task 5: Menu app (role routing via PFF: enumerator→F1/F3/F4 unmodified, supervisor→hub flow)

**Gated on:** Task 2 PASS. **Consumes:** the savesettings from Task 4.

**Files:**
- Create: `deliverables/CSPro/supervisor-hub/menu/MenuApp.dcf`
- Create: `deliverables/CSPro/supervisor-hub/menu/MenuApp.fmf`
- Create: `deliverables/CSPro/supervisor-hub/menu/MenuApp.apc`

**Interfaces:**
- Consumes: `loadsetting("role")` (Task 4).
- Produces: chain-launches the unmodified instruments (`..\\F1\\FacilityHeadSurvey.pen`, `..\\F3\\PatientSurvey.pen`, `..\\F4\\HouseholdSurvey.pen`) for enumerators; for supervisors, surfaces the collect/relay/QA actions (collect + relay are CSEntry built-in Sync per Tasks 6–7; this menu just points the supervisor at them via SOP).

- [ ] **Step 1: Define the acceptance**

Menu is correct when: launched after an `enumerator` login it offers F1/F3/F4 and launches the chosen instrument (unmodified) with OnExit back to the menu; after a `supervisor` login it shows the supervisor actions (Collect from enumerators / Relay to CSWeb / Run QA) per the SOP. (Verified on device, Step 4.)

- [ ] **Step 2: Build the menu form**

Create `menu/MenuApp` with a numeric `MENU_CHOICE` field and a protected `ROLE_SHOWN` (alpha 20) field for visibility. Value set for `MENU_CHOICE`: `1=F1, 2=F3, 3=F4` (enumerator) and `4=Collect, 5=Relay, 6=Run QA` (supervisor).

- [ ] **Step 3: Write role-aware routing logic**

`MenuApp.apc`:

```
PROC GLOBAL
  PFF instr_pff;
  alpha(20) m_role;

PROC MENUAPP_LEVEL
preproc
  m_role = loadsetting("role");
  ROLE_SHOWN = m_role;        { protected, for on-screen confirmation }

PROC MENU_CHOICE
postproc
  if m_role = "enumerator" then
    if MENU_CHOICE = 1 then launch_instrument("..\\F1\\FacilityHeadSurvey.pen"); endif;
    if MENU_CHOICE = 2 then launch_instrument("..\\F3\\PatientSurvey.pen"); endif;
    if MENU_CHOICE = 3 then launch_instrument("..\\F4\\HouseholdSurvey.pen"); endif;
  elseif m_role = "supervisor" then
    { 4/5/6 are operator actions done via CSEntry built-in Sync + the QA tool;
      this menu shows them as guidance. The hub Collect (Task 6) and Relay (Task 7)
      are CSEntry Synchronize operations, and Run QA (Task 8) is the laptop report. }
    errmsg("Supervisor: 4=Collect via CSEntry Sync (Bluetooth), 5=Relay via CSEntry Sync (CSWeb), 6=export + run the QA report. See README.");
  endif;

PROC GLOBAL
function launch_instrument(string pen)
  instr_pff.setProperty("Version", "CSPro 8.0");
  instr_pff.setProperty("ApplicationType", "entry");
  instr_pff.setProperty("StartMode", "add");
  instr_pff.setProperty("Application", pen);
  instr_pff.setProperty("OnExit", "..\\menu\\MenuApp.pff");
  instr_pff.execute();
end;
```

- [ ] **Step 4: Compile, publish, run both role paths on device**

Compile → strict Publish → deploy. Log in as `se-004` → choose F3 → confirm PatientSurvey launches (unmodified) → exit returns to menu. Log in as `fs-01` → confirm the supervisor guidance shows and `ROLE_SHOWN = supervisor`. Screenshot both paths. **Confirm the instruments' own `.dcf`/`.apc`/`.fmf`/`.qsf` are unchanged** (`git status` shows no edits under `deliverables/CSPro/F1|F3|F4/` except newly-referenced `.pen` paths if any). Leave the working tree changed.

---

### Task 6: Enumerator "Sync to Supervisor" Bluetooth config + SOP

**Gated on:** Task 1 PASS (else this task documents the manual file-share fallback instead).

**Files:**
- Create: `deliverables/CSPro/supervisor-hub/config/enumerator-bluetooth-sync.md`

**Interfaces:**
- Consumes: the C2 verdict (Task 1).
- Produces: the documented enumerator-side procedure consumed by the Task 10 integration test and the README.

- [ ] **Step 1: Write the config + SOP from the C2 findings**

Document the EXACT steps the spike proved: OS-level Bluetooth pairing of the enumerator device to the named hub device; CSEntry → Sync → (the Bluetooth/local server type the spike found) → select the hub → send F1/F3/F4. Include: data/Wi-Fi OFF is fine; the hub must be in "receive" mode (Task 7); transfer is non-destructive (originals stay). If C2 = FAIL, instead document the manual fallback verbatim from `spikes/C2-bluetooth-spike.md` (export → OS Bluetooth file send → hub import).

- [ ] **Step 2: Verify the doc against a real run**

Have one device sync to the hub following only the written steps; confirm they're sufficient (no undocumented tap). Fix any gap. Leave the working tree changed.

---

### Task 7: Hub collection + CSWeb relay (under supervisor-qa) config + SOP

**Gated on:** Task 1 PASS.

**Files:**
- Create: `deliverables/CSPro/supervisor-hub/config/hub-collect-and-relay.md`

**Interfaces:**
- Consumes: the enumerator sync (Task 6); the `supervisor-qa` CSWeb account (spec D5 / RBAC pack).
- Produces: the hub-side procedure consumed by Task 8 (QA on collected data), Task 10 (integration), and the README.

- [ ] **Step 1: Document hub RECEIVE (collection)**

Steps to put the hub device in receive mode (the host side the C2 spike proved), accept F1/F3/F4 from each enumerator at the regroup, and confirm accumulation (case list shows all enumerators' keys). Note: the hub holds the cluster's collected `.csdb` per instrument.

- [ ] **Step 2: Document hub→CSWeb RELAY**

Steps: when signal is available, CSEntry → Sync → CSWeb (`https://csweb.asiansocial.org/csweb`) signed in with the **`supervisor-qa`** account → send F1/F3/F4. State the conflict-free property verbatim: *"CSWeb upserts by the 12-digit key, so a case also synced direct by the enumerator is the same/newer revision — no conflict."* Smart-sync moves only new/changed.

- [ ] **Step 3: Verify against a real relay**

After a collection, relay from the hub and confirm the cases appear in CSWeb (Data tab counts / Sync Report) under the expected keys. Record the observed counts. Leave the working tree changed.

---

### Task 8: On-hub QA — reuse the Phase-1 report on collected data

**Gated on:** Task 1 PASS. **Reuses:** `deliverables/CSWeb/supervisor-app/` UNCHANGED.

**Files:**
- Create: `deliverables/CSPro/supervisor-hub/qa/run-on-hub.md`

**Interfaces:**
- Consumes: the hub-collected `.csdb` (Task 7); the Phase-1 `supervisor_qa_report.py` CLI (`--exports <dir> --assignments <csv> --out <html> --cluster <c> --today <YYYYMMDD>`).
- Produces: the on-hub QA procedure.

- [ ] **Step 1: Confirm the Phase-1 tool still passes (no changes)**

Run the Phase-1 suite to prove the reused tool is green before relying on it:
```
cd deliverables/CSWeb/supervisor-app && python -m pytest -q
```
Expected: `14 passed` (the Phase-1 suite). Do NOT modify the tool.

- [ ] **Step 2: Document the hub→report path**

Write `qa/run-on-hub.md`: from the hub-collected data, export each instrument to CSV (`F1.csv`/`F3.csv`/`F4.csv`) via Data Viewer / Data Manager (same export the Phase-1 README §"Evening laptop run" describes — the hub IS the laptop's data source now, no CSWeb round-trip), maintain `assignments.csv`, then:
```
python supervisor_qa_report.py --exports ./exports --assignments ./assignments.csv \
    --out ./supervisor-qa.html --cluster <cluster> --today <YYYYMMDD>
```
Note this is the SAME tool/command as Phase 1 — the only difference is the export source (hub-collected `.csdb` vs CSWeb-pulled). PII-light report; spot-check is the only PII step (advisory, D2).

- [ ] **Step 3: Verify end-to-end on collected data**

Export the Task-7 collected cases → run the command → confirm the HTML shows the collected cases in coverage/partials/flags and contains no respondent names (`grep` the HTML). Leave the working tree changed.

---

### Task 9: Security & deployment SOP runbook

**Files:**
- Create: `deliverables/CSPro/supervisor-hub/README.md`

**Interfaces:** none (documentation). Captures the security controls (C6) + the full field SOP, referencing Tasks 1–8 and both spike fallbacks.

- [ ] **Step 1: Write the runbook**

`README.md` with these exact sections:
- **What this is** — Phase-2 Bluetooth hub, dual-path fallback; link the spec.
- **Spike gates** — C1/C2 must be PASS; if a spike FAILED, which fallback is active (CSWeb-accounts-only for C1; manual file-share for C2).
- **Deployment** — install the login+menu app (or, on C1 FAIL, just the instruments); ship `UserRoster.dat` with the deployment (login can't authenticate without it); the `supervisor-qa` account on the hub device.
- **Daily field SOP** — morning login → capture → daily regroup Bluetooth collect → on-hub QA → relay on signal (the spec's data-flow cycle).
- **Security (C6, verbatim intent):** tablets encrypted + password-locked; supervisor **visually confirms each Bluetooth pairing**; **wipe collected copies after confirmed relay**; the app login is UX/identity routing, not security — real auth is the CSWeb account.
- **Limits:** ~10m Bluetooth range needs a physical regroup; enumerators who never regroup fall back to their own direct sync.

- [ ] **Step 2: Cross-check the runbook against Tasks 1–8**

Confirm every referenced file/command/account matches (the `supervisor_qa_report.py` command, the `supervisor-qa` account, the roster filename, the spike verdicts). Fix drift. Leave the working tree changed.

---

### Task 10: End-to-end integration test (acceptance)

**Gated on:** Tasks 3–9 complete (or their fallbacks).

**Files:**
- Create: `deliverables/CSPro/supervisor-hub/spikes/E2E-integration-result.md`

**Interfaces:**
- Consumes: everything above.
- Produces: the recorded acceptance result.

- [ ] **Step 1: Define the acceptance scenario**

Two enumerator devices (`se-004`, `se-011`) + one hub (`fs-01`), all offline. Each enumerator captures an F3 case (distinct 12-digit keys). At "regroup", both sync to the hub over Bluetooth. The hub runs the QA report on the collected data, then (with signal) relays to CSWeb.

- [ ] **Step 2: Run it**

Execute the scenario end to end following ONLY the written SOPs (Tasks 6/7/8/9). Then, to prove dual-path safety: have `se-004` ALSO sync its case direct to CSWeb. Confirm CSWeb shows each key exactly once (upsert by key — no duplicate, no conflict).

- [ ] **Step 3: Record the acceptance result**

Write `E2E-integration-result.md`: collected counts, relay counts, the dual-path no-conflict observation, QA report screenshot, and any SOP gaps found+fixed. Leave the working tree changed.

---

## Self-Review

**1. Spec coverage:**
- D1 dual-path → Tasks 6/7 (direct stays; hub is fallback) + Task 10 dual-path check. ✓
- D2 advisory QA, no write-back → Task 8 (report only) + README. ✓
- D3 CSEntry built-in Bluetooth + manual fallback; PROC sync rejected → Task 1 spike + Tasks 6/7. ✓
- D4 login/role gate, spike-gated, not security → Task 2 spike + Tasks 3/4/5 + README. ✓
- D5 relay under supervisor-qa → Task 7. ✓
- D6 instruments unmodified (PFF chain-launch) → Task 5 (Step 4 asserts no instrument edits). ✓
- D7 build deferred → plan header + this is plan-now. ✓
- C1 login → Tasks 2/4/5; C2 Bluetooth → Tasks 1/6/7; C3 relay → Task 7; C4 on-hub QA → Task 8; C5 roster → Task 3; C6 security → Task 9. ✓
- Conflict-free upsert-by-key → Task 7 Step 2 + Task 10 Step 2. ✓

**2. Placeholder scan:** No "TBD"/"implement later". `<cluster>`/`<YYYYMMDD>` are CLI argument placeholders (runtime values), not unspecified design. Spike fallbacks are concrete, not "figure it out later".

**3. Type consistency:** `UserRoster` items (`LOGIN_USERNAME`/`PASSWORD`/`ROLE`/`OPERATOR_ID`/`CLUSTER`) defined in Task 3 are used identically in Tasks 4/5. `savesetting("role")` (Task 4) ↔ `loadsetting("role")` (Task 5) match. `m_role` values `"enumerator"`/`"supervisor"` match the roster `ROLE` seed (Task 3). The reused `supervisor_qa_report.py` signature matches the Phase-1 plan/tool exactly (Task 8). PFF property pattern is identical across Tasks 2/4/5.

**Note (TDD adaptation):** This plan is device/Designer/ops work, not unit-testable Python (except the reused Phase-1 tool, which keeps its `pytest` suite — Task 8 Step 1). "Tests" are therefore device-verification steps with explicit PASS criteria + screenshots, and the two spikes are the primary risk gates. The one place real unit tests exist (the Phase-1 report) is reused unchanged and re-run, not rewritten.

**Note (git):** Per the Global Constraints, no task commits. Every task ends "leave the working tree changed (Carl commits)" instead of the skill's default commit step.
