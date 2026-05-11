# UHC Phase 1 — F1 + CSPro Android Native Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close `E3-F1-088` by deploying a clean F1 entry app to CSWeb, pulling it to an Android tablet, entering a test case, syncing it via CSPro Android's native Synchronize → Send data UI, and verifying the case lands in CSWeb's MySQL backend.

**Architecture:** F1 standalone deployable (no login/menu chain). F1 carries zero custom sync code. Sync transport is entirely CSPro Android's responsibility. Build pipeline (`build_all.py` + per-instrument generators) stays source of truth. Phase 1 INSTRUMENTS collapses to just F1; login + menu directories park on disk for Phase 2.

**Tech Stack:** Python 3.13 (generators), CSPro 8.0 (Designer F7 publish + Deploy Application wizard), Wampserver64 + CSWeb 8.0.1 on Apache 2.4 + MySQL, CSPro Android on the test tablet, PowerShell + Bash (smoke commands), gh CLI (issue close).

**Spec:** [`docs/superpowers/specs/2026-05-11-uhc-phase-1-f1-native-sync-design.md`](../specs/2026-05-11-uhc-phase-1-f1-native-sync-design.md)

**Working environment:** All work happens in the existing git worktree at `.claude/worktrees/uhc-survey-system-build/` on branch `feature/uhc-survey-system-build`. No new worktree needed.

---

## Phase 0 — Cleanup (single commit)

**Goal:** Bring the worktree to a clean Phase 1 starting state by removing failed B1 experiment artifacts, reverting drift in the menu generator, and reducing the build pipeline to F1 only.

### Task 0.1: Delete the failed 109_sync experiment

**Files:**
- Delete: `deliverables/CSPro/UHC-Survey-System/109_sync/` (entire directory, 10 files: 4 generators + 6 generated outputs)

- [ ] **Step 1: Verify current state of 109_sync directory**

Run from worktree root:
```bash
ls -la deliverables/CSPro/UHC-Survey-System/109_sync/
```

Expected output: 4 `generate_*.py` files + `sync_F1_app.dcf` + `sync_F1_app.ent` + `sync_F1_app.ent.apc` + `sync_F1_app.ent.mgf` + `sync_F1_app.ent.qsf` + `sync_F1_app.fmf` (10 files).

- [ ] **Step 2: Delete the entire 109_sync directory via git**

```bash
git rm -rf deliverables/CSPro/UHC-Survey-System/109_sync/
```

Expected output: `rm 'deliverables/CSPro/UHC-Survey-System/109_sync/generate_apc.py'` and 9 more rm lines.

- [ ] **Step 3: Verify deletion**

```bash
ls -la deliverables/CSPro/UHC-Survey-System/109_sync/ 2>&1
git status --short deliverables/CSPro/UHC-Survey-System/109_sync/
```

Expected: `ls: cannot access ...: No such file or directory` and 10 staged deletions (lines starting with `D`).

### Task 0.2: Delete the orphan Sync-Helpers.apc

**Files:**
- Delete: `deliverables/CSPro/UHC-Survey-System/shared/Sync-Helpers.apc`

- [ ] **Step 1: Re-confirm zero callers**

```bash
grep -rn "Sync-Helpers\|send_data_on_server\|receive_from_server" \
  deliverables/CSPro/UHC-Survey-System/ \
  --include="*.py" --include="*.apc"
```

Expected: only matches inside `Sync-Helpers.apc` itself (the file's own header comment and function definitions). No external callers.

- [ ] **Step 2: Delete the file via git**

```bash
git rm deliverables/CSPro/UHC-Survey-System/shared/Sync-Helpers.apc
```

Expected output: `rm 'deliverables/CSPro/UHC-Survey-System/shared/Sync-Helpers.apc'`.

### Task 0.3: Revert 106_menu/generate_apc.py to single-F1-choice version

**Files:**
- Modify: `deliverables/CSPro/UHC-Survey-System/106_menu/generate_apc.py`

The current version has `launch_sync_F1` plus a 2nd menu choice for "Sync data to server". Revert to the pre-B1 version (single `launch_F1` function only, single menu choice).

- [ ] **Step 1: Find the pre-B1 commit that had the single-choice version**

```bash
git log --oneline --follow deliverables/CSPro/UHC-Survey-System/106_menu/generate_apc.py
```

The commit *before* `8ac7594` (the "feat(UHC-build): add 109_sync entry app" commit that added launch_sync_F1) is the version we want. Typically `b9eed0b` (move sync into F1, drop menu sync) or `79abfcb` (add Send-data menu choice — actually this is also drift; go further back).

To be safe, find the last commit that touched menu_app/generate_apc.py BEFORE Day 5's sync experiments started — likely `33f724f` (Phase 6 — menu app enumerator-only). Use:

```bash
git log --oneline -5 deliverables/CSPro/UHC-Survey-System/106_menu/generate_apc.py
```

Pick the commit that pre-dates any sync work. Let `<PREB1_SHA>` be that commit's SHA.

- [ ] **Step 2: Restore the file from that commit**

```bash
git show <PREB1_SHA>:deliverables/CSPro/UHC-Survey-System/106_menu/generate_apc.py > deliverables/CSPro/UHC-Survey-System/106_menu/generate_apc.py
```

This overwrites the current file with the pre-B1 content.

- [ ] **Step 3: Update the file's docstring to mark Phase 1 parking**

Use the Edit tool to change the top docstring. Replace the existing docstring with:

```
"""generate_apc.py — emit menu_app.ent.apc with role-conditional accept() menu.

Phase 1 (2026-05-11): parked. Menu app reactivates in Phase 2 when 2nd
questionnaire arrives. Single-F1-choice form retained for forward continuity.
"""
```

Also update the APC's top comment block (inside the `APC = r'''...'''` raw string) to mention Phase 1 parking and that sync is handled natively:

```
{ Application 'UHC Menu' logic file generated by CSPro }
{ Phase 1: parked — menu app activates in Phase 2 when 2nd questionnaire
  is deployed. Single-choice form retained for forward continuity. Sync is
  handled natively by CSPro Android (Synchronize -> Send data UI), not via
  a menu choice. }
```

- [ ] **Step 4: Run the reverted generator to regenerate menu_app.ent.apc on disk**

```bash
cd deliverables/CSPro/UHC-Survey-System/106_menu
python generate_apc.py
cd ../../../..
```

Expected output: `wrote menu_app.ent.apc`.

- [ ] **Step 5: Verify the regenerated menu_app.ent.apc no longer references sync**

```bash
grep -n "launch_sync_F1\|sync_pff\|Sync data to server" \
  deliverables/CSPro/UHC-Survey-System/106_menu/menu_app.ent.apc
```

Expected output: empty (no matches). The reverted menu has only one menu choice (F1) and no sync references.

### Task 0.4: Reduce build_all.py INSTRUMENTS to F1 only

**Files:**
- Modify: `deliverables/CSPro/UHC-Survey-System/build_all.py` (lines 29-36)

- [ ] **Step 1: Confirm current INSTRUMENTS list**

```bash
sed -n '29,36p' deliverables/CSPro/UHC-Survey-System/build_all.py
```

Expected output (4 instruments): comment + `INSTRUMENTS = [` + 4 tuple lines for login/menu/F1/sync_F1 + closing `]`.

- [ ] **Step 2: Replace INSTRUMENTS with the F1-only version**

Use the Edit tool. Replace the block:

```python
# (numeric_prefix, short_name, dir_name, ent_filename)
# Phase 1 builds 4 instruments. Phase 2 will append PLF, F3, F4_listing, F4.
INSTRUMENTS = [
    ("101", "login",   "101_login", "login_app"),
    ("106", "menu",    "106_menu",  "menu_app"),
    ("107", "F1",      "107_F1",    "FacilityHeadSurvey"),
    ("109", "sync_F1", "109_sync",  "sync_F1_app"),
]
```

With:

```python
# (numeric_prefix, short_name, dir_name, ent_filename)
# Phase 1 builds F1 only. Login + menu parked at 101_login/ and 106_menu/
# (on-disk but not built); reactivated in Phase 2 alongside chain rebuild.
INSTRUMENTS = [
    ("107", "F1", "107_F1", "FacilityHeadSurvey"),
]
```

- [ ] **Step 3: Verify the edit**

```bash
sed -n '29,36p' deliverables/CSPro/UHC-Survey-System/build_all.py
```

Expected output: F1-only INSTRUMENTS list with updated comment referencing Phase 1 parking of login/menu.

### Task 0.5: Smoke build_all.py --env=uat with F1-only configuration

**Files:**
- Generated: `deliverables/CSPro/UHC-Survey-System/107_F1/FacilityHeadSurvey.{dcf,ent,fmf,ent.apc,ent.qsf,ent.mgf}`

- [ ] **Step 1: Run build_all.py --env=uat**

```bash
cd deliverables/CSPro/UHC-Survey-System
python build_all.py --env=uat
cd ../../..
```

Expected output (key lines):
```
[107_F1] generating sources ...
  -> generate_apc.py
  -> generate_dcf.py
  -> generate_ent.py
  -> generate_fmf.py
[107_F1] splicing env config into FacilityHeadSurvey.ent
[107_F1] OK (sources at 107_F1)

Generated sources for 1 instrument(s), env=uat.
```

The build should NOT process login, menu, or sync_F1 instruments (they're not in INSTRUMENTS).

- [ ] **Step 2: Verify F1's emitted .ent has the correct UAT URL spliced in**

```bash
python -c "import json; d = json.load(open(r'deliverables/CSPro/UHC-Survey-System/107_F1/FacilityHeadSurvey.ent')); print('csweb_url:', next((s['value'] for s in d.get('userSettings', []) if s['name']=='csweb_url'), 'NOT FOUND'))"
```

Expected output: `csweb_url: http://192.168.1.168/csweb8.0.1/api`

If the IP differs from your laptop's current LAN IP, run `Get-NetIPAddress -AddressFamily IPv4` (PowerShell) and update `urls.yaml[uat].csweb_url` accordingly before re-running build_all.py.

- [ ] **Step 3: Verify F1's emitted .ent.apc has zero sync code**

```bash
grep -n "syncconnect\|syncdata\|synchronize_data\|setfile" \
  deliverables/CSPro/UHC-Survey-System/107_F1/FacilityHeadSurvey.ent.apc
```

Expected output: empty (no matches). F1 is pure data entry; native sync owns transport.

### Task 0.6: Commit Phase 0 cleanup

- [ ] **Step 1: Review what's staged**

```bash
git status --short
```

Expected: deletions for 109_sync/ files + Sync-Helpers.apc; modifications to build_all.py + 106_menu/generate_apc.py + 106_menu/menu_app.ent.apc; any 107_F1 .ent / .fmf / .ent.apc / .dcf updates from regeneration.

- [ ] **Step 2: Stage all cleanup changes**

```bash
git add deliverables/CSPro/UHC-Survey-System/
```

- [ ] **Step 3: Commit**

```bash
git commit -m "chore(UHC-build): Phase 1 cleanup — remove 109_sync + Sync-Helpers + park menu/login

E3-F1-088 architecture reset (per spec 2026-05-11-uhc-phase-1-f1-native-sync-design.md):
sync moves to CSPro Android's native Synchronize -> Send data UI; F1 carries
zero custom sync code. Phase 1 collapses to F1 standalone; login/menu parked
on disk for Phase 2.

- Delete 109_sync/ (failed B1 experiment)
- Delete shared/Sync-Helpers.apc (7.x orphan, zero callers)
- Revert 106_menu/generate_apc.py (drop launch_sync_F1 + 2nd menu choice)
- Reduce build_all.py INSTRUMENTS to F1 only
- Regenerate 106_menu/menu_app.ent.apc to match reverted generator

Verified: build_all.py --env=uat emits F1 cleanly; F1 .ent.apc has zero
sync code; UAT LAN IP (192.168.1.168) correctly spliced into userSettings."
```

Expected: commit succeeds with a SHA. Note the SHA for later evidence.

- [ ] **Step 4: Verify clean working tree**

```bash
git status
```

Expected: `nothing to commit, working tree clean` (or only `dist/` ignored).

---

## Phase 1 — F7 publish (manual, in CSPro Designer)

**Goal:** Compile `FacilityHeadSurvey.ent` to `FacilityHeadSurvey.pen` via CSPro Designer's manual F7 step. CSPro 8.0 has no headless CLI for this.

### Task 1.1: Open F1.ent in CSPro Designer

- [ ] **Step 1: Launch CSPro Designer**

Open from Start Menu, or run:
```powershell
& 'C:\Program Files (x86)\CSPro 8.0\CSPro.exe'
```

- [ ] **Step 2: Open the F1 .ent file**

In CSPro Designer: **File → Open Application** (Ctrl+O) → navigate to:
```
C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development\.claude\worktrees\uhc-survey-system-build\deliverables\CSPro\UHC-Survey-System\107_F1\FacilityHeadSurvey.ent
```

Wait a few seconds for Designer to load (F1 has 671 items so the form may take a moment).

- [ ] **Step 3: Confirm the .ent is loaded as the focused tab**

The CSPro Designer window title bar should show `CSPro 8.0 - [FacilityHeadSurvey]`. The Files panel (bottom left) should list the .ent and its referenced files.

### Task 1.2: F7-publish the .ent to .pen

- [ ] **Step 1: Trigger publish**

Press **F7** (or **File → Publish Entry Application**).

- [ ] **Step 2: Confirm save dialog**

A dialog appears asking where to save the .pen. The default should be the same folder as the .ent (`107_F1/`) with the same basename (`FacilityHeadSurvey.pen`). Click **Save** to accept.

- [ ] **Step 3: Wait for compile**

Designer's bottom pane shows compile progress. Wait until it reports completion (~5-10 seconds for F1).

- [ ] **Step 4: Inspect the compile output**

Look at Designer's bottom **Compiler Output** pane. Expected: no `ERROR` lines. A `WARNING(GLOBAL, ...): The setting csweb_url was not found in the Common Store settings file` warning is acceptable — it's load-time only, doesn't block compile, and CSPro Android resolves the user setting at runtime from the .ent's spliced value.

If any `ERROR` lines appear, capture the exact text. Common cases:
- `ERROR(GLOBAL, ...): <something> is not a declared variable` → generator drift; report and pause for diagnosis
- `ERROR(... LEVEL, ...): Invalid syntax` → likely a stale `.apc` or `.dcf`; re-run build_all.py and retry

- [ ] **Step 5: Verify .pen on disk**

In a Bash terminal (or PowerShell `Get-ChildItem`):
```bash
ls -la deliverables/CSPro/UHC-Survey-System/107_F1/FacilityHeadSurvey.pen
```

Expected: file exists, size > 0 (typically 40-100KB for F1's 671 items). Modification time matches when you pressed F7.

### Task 1.3: Close the .ent in Designer (release file lock)

- [ ] **Step 1: Close the application**

In Designer: **File → Close** (Ctrl+W).

This releases the .ent file lock so subsequent steps (Deploy Application wizard) can re-open it.

---

## Phase 2 — CSWeb deploy (manual, via Designer's Deploy Application wizard)

**Goal:** Upload `FacilityHeadSurvey.pen` to the local CSWeb instance so the tablet can pull it.

### Task 2.1: Pre-check Wampserver64 + CSWeb are running

- [ ] **Step 1: Verify Wampserver64 is running**

Look at the system tray (bottom-right of Windows taskbar). The Wampserver64 icon should be **green** (not orange or red).

If orange/red: right-click the icon → **Start All Services** → wait for green.

- [ ] **Step 2: Verify CSWeb responds**

In a browser, open:
```
http://localhost/csweb8.0.1/
```

Expected: CSWeb login page renders. Log in with your admin credentials to confirm the admin UI loads.

- [ ] **Step 3: Verify CSWeb API responds (for the tablet's sync path)**

In a browser or via curl:
```
http://localhost/csweb8.0.1/api/
```

Expected: API responds (may return JSON, an error page, or 404 for the root — what matters is the server responds, not 503 / connection refused).

### Task 2.2: Open the .ent in Designer and launch Deploy Application

- [ ] **Step 1: Open F1.ent in Designer**

Same as Task 1.1 (you may already have it open).

- [ ] **Step 2: Open Deploy Application wizard**

**Tools → CSPro Deploy Application**

The wizard opens.

### Task 2.3: Configure the deployment

The wizard walks through several screens. Settings per screen:

- [ ] **Step 1: Choose deployment target**

Select the option that says **CSWeb** (or **Web server**, depending on CSPro 8.0 build's exact label).

- [ ] **Step 2: Enter server connection**

- **URL:** `http://192.168.1.168/csweb8.0.1/api`
  - This must match what's spliced into the .ent's `userSettings.csweb_url` (verified in Task 0.5 Step 2). The tablet will use this URL when it pulls the .pen, so it must be the laptop's LAN IP (not `localhost`) so the tablet can route to it.
- **Username:** your CSWeb admin user
- **Password:** your CSWeb admin password

- [ ] **Step 3: Set package + application identity**

- **Package Name:** `UHC_Survey_Phase1` (reuses your previous package name for continuity; the wizard will update the existing package's app entry rather than create a new package)
- **Application Name (within package):** `FACILITYHEADSURVEY` (matches the .ent's internal `name` field)

- [ ] **Step 4: Confirm files to include**

The wizard auto-selects the .pen + referenced files (.dcf, .fmf, .qsf, .mgf). For Phase 1, no external dictionaries are involved (F1 has only its own primary dict, no externals).

- [ ] **Step 5: Finish/Deploy**

Click the final **Finish** or **Deploy** button. The wizard uploads the bundle.

Expected: wizard reports success (e.g., "Application deployed successfully").

If the wizard errors:
- "Cannot connect to server" → re-check Task 2.1 (Wampserver running + CSWeb reachable)
- "Authentication failed" → re-check CSWeb admin credentials
- "Package already exists" + no overwrite option → either accept overwrite if prompted, or use a fresh package name like `UHC_Survey_Phase1_v2`

### Task 2.4: Verify the .pen is registered in CSWeb

- [ ] **Step 1: Open CSWeb admin UI**

In a browser:
```
http://localhost/csweb8.0.1/
```

Log in.

- [ ] **Step 2: Navigate to Apps tab**

Click **Apps** in the left navigation.

- [ ] **Step 3: Confirm F1 is listed**

Expected: a row with the package name `UHC_Survey_Phase1` (expandable or with sub-listing) containing `FACILITYHEADSURVEY` as an application. Timestamp should match the deploy you just completed.

---

## Phase 3 — Tablet sideload + CSPro Android setup

**Goal:** Pull the F1 .pen to the test Android tablet so the enumerator workflow can begin.

### Task 3.1: Verify tablet on same Wi-Fi as laptop

- [ ] **Step 1: Check laptop's LAN IP**

In PowerShell:
```powershell
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.PrefixOrigin -eq 'Dhcp'} | Select-Object IPAddress, InterfaceAlias
```

Expected: an IPv4 address starting with `192.168.x.x` or similar private LAN range. Confirm it matches what's in `urls.yaml[uat].csweb_url` and the `.ent` userSettings.

If the laptop's IP differs from the deployed .ent's URL: rebuild + re-deploy (Tasks 0.5 → 2.4) with the corrected IP. Tablet won't be able to reach CSWeb otherwise.

- [ ] **Step 2: Tablet — connect to the same Wi-Fi network as the laptop**

On the tablet: Settings → Wi-Fi → select the same SSID the laptop is on.

- [ ] **Step 3: Sanity ping (optional but worth a few seconds)**

If the tablet has a browser, navigate to `http://192.168.1.168/csweb8.0.1/` (substitute your laptop's actual LAN IP). Expected: CSWeb login page renders. Confirms tablet→laptop network reachable.

### Task 3.2: Configure CSPro Android sync server

- [ ] **Step 1: Open CSPro Android on tablet**

Tap the CSPro app icon. Wait for the main screen to load.

- [ ] **Step 2: Open settings**

Tap the gear/settings icon (typically top-right).

- [ ] **Step 3: Sync Server section**

Find the **Sync server** entry and tap to edit.

- **Server URL:** `http://192.168.1.168/csweb8.0.1/api/` (trailing slash matters in some CSPro Android builds)
- **Username:** the CSWeb user the tablet syncs as (matches a CSWeb user account configured in Task 2.1's CSWeb setup, e.g., your admin or a dedicated tablet user)
- **Password:** matching password

- [ ] **Step 4: Test connection**

Tap **Test connection** button.

Expected: green checkmark or "OK" message. If error:
- "Could not reach server" → re-check Wi-Fi (Task 3.1) and Wampserver running (Task 2.1)
- "Authentication failed" → re-check CSWeb credentials
- "Network timeout" → check Windows Firewall on the laptop allows port 80 inbound from LAN: `New-NetFirewallRule -DisplayName "Apache 80 LAN" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow` (PowerShell as admin)

### Task 3.3: Pull F1 to the tablet

- [ ] **Step 1: Initiate Get applications**

In CSPro Android: tap **Synchronize → Get applications** (or equivalent menu path).

- [ ] **Step 2: Confirm sync**

Tablet shows progress. Wait for completion (typically 10-30 seconds for a single F1 .pen at ~50KB).

Expected: success message + the `UHC_Survey_Phase1` package (containing F1) appears in the tablet's installed app list. F1's app icon should be tappable.

If error:
- "Application not found" → re-verify CSWeb's Apps tab (Task 2.4 Step 3) shows the package
- "Permission denied" → CSPro Android user lacks app-download permission in CSWeb; check the user's role in CSWeb admin

---

## Phase 4 — Smoke test the round-trip

**Goal:** Enter a test case in F1 on the tablet, end-case it, push to CSWeb via native sync, and verify the case lands in CSWeb's Cases tab. This is the actual E3-F1-088 close.

### Task 4.1: Launch F1 on tablet

- [ ] **Step 1: Tap F1 app icon**

In CSPro Android's installed apps list (or wherever F1 appears), tap the F1 app.

Expected: F1 entry form opens. The first field (QUESTIONNAIRE_NO) should be focused, or a case-tree screen appears (empty if this is the first launch).

### Task 4.2: Enter a dummy test case

- [ ] **Step 1: Start a new case**

If a case-tree appears: tap "Add new case" (or equivalent UI element). If F1 opens directly to the form: you're already on the first field.

- [ ] **Step 2: Enter QUESTIONNAIRE_NO**

Type: `000001`

Press Enter (or tap the next-field arrow / "Next" button) to advance.

- [ ] **Step 3: Enter SURVEY_CODE**

Type: `F1`

Advance.

- [ ] **Step 4: Enter INTERVIEWER_ID**

Type: `0001`

Advance.

- [ ] **Step 5: Enter DATE_STARTED**

Type: `20260511` (or today's date in YYYYMMDD format; use `Get-Date -Format yyyyMMdd` on the laptop to confirm format).

Advance.

- [ ] **Step 6: Enter TIME_STARTED**

Type: `103000` (or any HHMMSS).

Advance.

- [ ] **Step 7: Enter AAPOR_DISPOSITION**

Type: `120` (Partial — appropriate since we're committing an incomplete case).

Advance.

### Task 4.3: End Case (force commit to F1.csdb)

**Critical:** Use **End Case (X icon at top right)**, NOT the back arrow / partial save. End Case forcibly commits the case to F1.csdb regardless of validation completeness. The back arrow / Suspend approach failed in Sprint 005 Day 1 attempts because partial saves don't reliably persist for CSPro Android's sync to pick up.

- [ ] **Step 1: Tap End Case (X icon)**

Located at the top-right of the F1 form view.

- [ ] **Step 2: Confirm end-case prompt**

CSPro Android may warn about incomplete fields and ask whether to end the case anyway. Tap **Yes** / **End anyway**.

- [ ] **Step 3: Returns to case tree or F1 main screen**

Expected: the case (now committed to F1.csdb) should appear in the case tree with `QUESTIONNAIRE_NO=000001` visible.

### Task 4.4: Verify F1.csdb persistence by re-launching F1

This step catches the "case tree empty on re-launch" failure observed earlier. If End Case worked, the case persists; if it failed, we know before sync.

- [ ] **Step 1: Exit F1**

From the F1 main screen or case tree, tap the device back button or close button to exit F1 back to CSPro Android's app list.

- [ ] **Step 2: Re-launch F1**

Tap F1's app icon again.

- [ ] **Step 3: Verify case tree shows the case**

Expected: the case with `QUESTIONNAIRE_NO=000001` is visible in the case tree.

If the case tree is empty: End Case did not persist. Capture the issue and pause for diagnosis — this is a fundamental tablet-side issue that needs separate investigation before proceeding to sync.

### Task 4.5: Push F1 data to CSWeb via native sync

- [ ] **Step 1: Exit F1 back to CSPro Android main screen**

- [ ] **Step 2: Initiate Send data**

In CSPro Android: **Synchronize → Send data** (or equivalent menu path).

- [ ] **Step 3: Select F1 as the dictionary to sync**

CSPro Android may prompt for which app's data to sync. Select `FACILITYHEADSURVEY` (or the F1 app entry).

- [ ] **Step 4: Confirm sync completion**

CSPro Android shows progress. Wait for completion.

Expected: success message indicating cases pushed (e.g., "1 case sent" or "Sync complete").

If error:
- "Could not reach server" → re-check Wi-Fi + Wampserver + Test connection (Task 3.2 Step 4)
- "Authentication failed" → re-check CSPro Android sync credentials
- "Server error 500" → check Wampserver Apache + PHP logs; check CSWeb MySQL is running

### Task 4.6: Verify case landed in CSWeb

- [ ] **Step 1: Open CSWeb admin UI**

In browser: `http://localhost/csweb8.0.1/`. Log in.

- [ ] **Step 2: Navigate to Cases / Data tab**

The path varies by CSWeb version — look for "Cases", "Data", or "Reports" in the left nav.

- [ ] **Step 3: Find F1's case list**

Select the `FACILITYHEADSURVEY` dictionary / application from any dropdown or list.

- [ ] **Step 4: Confirm the test case is present**

Expected: a row with `QUESTIONNAIRE_NO=000001`, with the fields you entered visible (SURVEY_CODE=F1, INTERVIEWER_ID=0001, etc.).

If the case is missing:
- Check CSWeb MySQL directly via phpMyAdmin (`http://localhost/phpmyadmin`): find the F1 data table and look for the row
- Check Apache + CSWeb logs for upload errors

If the case is present → **E3-F1-088 closes**. Proceed to Phase 5 for evidence recording.

---

## Phase 5 — Evidence recording + E3-F1-088 close

**Goal:** Document the successful smoke test in version-controlled artifacts, close the GitHub issue, and update sprint state.

### Task 5.1: Record smoke evidence in worktree log.md

**Files:**
- Modify: `log.md` (append a dated section)

- [ ] **Step 1: Identify the Phase 0 cleanup commit SHA from Task 0.6**

```bash
git log --oneline -5
```

Note the Phase 0 cleanup commit SHA (the one with the `chore(UHC-build): Phase 1 cleanup` message).

- [ ] **Step 2: Append the smoke entry to log.md**

Open `log.md` (in the worktree root) and append at the end. The entry should be structured as:

- Header: `## 2026-05-11 (Sprint 005 Day 1 — E3-F1-088 closed via CSPro Android native sync)`
- Bullet 1: E3-F1-088 closed; F1 round-tripped successfully via CSPro Android's Synchronize → Send data UI; no custom syncdata code
- Bullet 2: Architecture summary (F1 standalone, zero sync code, CSPro Android handles transport); reference spec doc path
- Bullet 3: Cleanup commit SHA (paste from Step 1) — what got removed/reverted
- Bullet 4: Build pipeline verification — F1 .ent.apc has zero sync code; UAT LAN IP correctly spliced
- Bullet 5: F7 publish — compiled clean (only csweb_url Common Store warning)
- Bullet 6: CSWeb deploy — uploaded via Deploy Application wizard; appears in Apps tab under package `UHC_Survey_Phase1`
- Bullet 7: Tablet round-trip — pulled cleanly, test case entered + End Cased + native sync sent + visible in CSWeb Cases tab
- Bullet 8: Lessons from the 4 failed custom-syncdata attempts (v1 polymorphic dictname → v2 inline syncdata → v3 setfile path binding → v4 partial-save persistence)
- Bullet 9: Phase 2 parking — 101_login/ and 106_menu/ stay on disk, reactivate alongside 2nd questionnaire

- [ ] **Step 3: Commit the log entry**

```bash
git add log.md
git commit -m "docs(log): record E3-F1-088 close via native sync smoke 2026-05-11"
```

Expected: commit succeeds. Note the SHA for the GitHub issue close comment.

### Task 5.2: Close GitHub issue #131 (E3-F1-088)

- [ ] **Step 1: Get the smoke commit SHA from Task 5.1 Step 3**

```bash
git log --oneline -1
```

Copy the SHA.

- [ ] **Step 2: Close the issue with comment + evidence link**

```bash
gh issue close 131 -R cplreyes/ASPSI-DOH-UHC-CAPI-Development -c "Closed 2026-05-11. E3-F1-088 Phase 1 sync mechanic resolved via CSPro Android native sync (no custom syncdata code).

Architecture: F1 standalone deployable; F1.apc carries zero sync code. CSPro Android's Synchronize -> Send data UI handles transport, auth, and case selection.

Smoke evidence: test case QUESTIONNAIRE_NO=000001 round-tripped end-to-end from tablet entry -> End Case -> native sync -> CSWeb Cases tab. Verified in log.md entry for 2026-05-11.

Spec: docs/superpowers/specs/2026-05-11-uhc-phase-1-f1-native-sync-design.md
Plan: docs/superpowers/plans/2026-05-11-uhc-phase-1-f1-native-sync-plan.md

Custom sync (Phase 2 follow-up): 4 attempts at custom in-app syncdata logic ran into CSPro 8.0 constraints (external dict expected -> dictname param removed -> datasource flat .dat default -> F1.csdb path mismatch). Native sync sidesteps all of these. Phase 2 can revisit custom sync once we have a verified CSPro 8.0 working reference."
```

Expected: GitHub returns a URL to the closed issue. The issue should now show `CLOSED` status.

### Task 5.3: Update sprint-current.md DoD checkbox

**Files:**
- Modify: `scrum/sprint-current.md` (the E3-F1-088 entries in the "Goal A" committed items and "Definition of Done — Sprint 005" sections)

- [ ] **Step 1: Open scrum/sprint-current.md and find the DoD checkbox**

Find the line in the "Definition of Done" section that begins:
```
- [ ] **E3-F1-088** closed: Phase 1 sync mechanic working end-to-end on tablet...
```

- [ ] **Step 2: Replace the unchecked checkbox with a checked one**

Update to:

```
- [x] **E3-F1-088** closed 2026-05-11: Phase 1 sync via CSPro Android native Synchronize -> Send data UI; F1 standalone deployable; zero custom sync code; test case QUESTIONNAIRE_NO=000001 round-tripped tablet -> CSWeb. Spec `2026-05-11-uhc-phase-1-f1-native-sync-design.md`; plan `2026-05-11-uhc-phase-1-f1-native-sync-plan.md`; smoke evidence in `log.md` 2026-05-11.
```

- [ ] **Step 3: Update the committed item checkbox too**

Find this line earlier in the file (under "Goal A — UHC Phase 1 sync close-out"):
```
- [ ] **E3-F1-088** Phase 1 sync mechanic resolution — `syncdata` external-dict + CSDB binding...
```

Replace `[ ]` with `[x]` and update the status tag:
```
- [x] **E3-F1-088** Phase 1 sync mechanic resolution — CLOSED via CSPro Android native sync (architecture pivot 2026-05-11 PM; see spec/plan/log). `status::done` `priority::critical` `actual::~6h (4 failed custom syncdata attempts + architecture reset to native + smoke close)`
```

- [ ] **Step 4: Commit sprint state update**

```bash
git add scrum/sprint-current.md
git commit -m "chore(scrum): mark E3-F1-088 done in Sprint 005 (native sync close)"
```

Expected: commit succeeds.

### Task 5.4: Push the worktree branch to origin

- [ ] **Step 1: Push feature branch**

```bash
git push origin feature/uhc-survey-system-build
```

Expected: push succeeds. Slack post-commit hook may fire if configured for the worktree (per memory `project_slack_task_changes_notifier`).

### Task 5.5: Final verification

- [ ] **Step 1: Confirm GitHub issue #131 is closed**

```bash
gh issue view 131 -R cplreyes/ASPSI-DOH-UHC-CAPI-Development --json state,title,closedAt
```

Expected: `state: CLOSED`, recent `closedAt` timestamp.

- [ ] **Step 2: Confirm Project #8 status updated for #131**

```bash
gh project item-list 8 --owner cplreyes --format json --limit 300 | python -c "import json, sys; items=json.load(sys.stdin)['items']; [print(f\"#{it.get('content',{}).get('number')}: status={it.get('status')} slot={it.get('sprint Slot')}\") for it in items if it.get('content',{}).get('number') == 131]"
```

Expected: `#131: status=Done slot=sprint-005` (or whatever Project #8 maps closed issues to). If status hasn't auto-updated to Done, set it manually via `gh project item-edit` (out of scope for Phase 1 plan — worth noting as a Project #8 automation gap).

- [ ] **Step 3: Sanity check on sprint-current.md**

```bash
grep -n "E3-F1-088" scrum/sprint-current.md
```

Expected: both occurrences (Committed Items line + DoD line) show `[x]` and reference the 2026-05-11 close.

---

## Plan complete

After Phase 5, Phase 1 of UHC Survey System is done. Sprint 005 Goal A's anchor item (E3-F1-088) closes. Remaining Goal A item is `E3-F1-PHASE2-PLAN` (Phase 2 scope confirmation), which can now build on the proven Phase 1 foundation.
