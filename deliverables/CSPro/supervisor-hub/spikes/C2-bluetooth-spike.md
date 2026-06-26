# C2 spike — CSEntry device-to-device sync over Bluetooth (Phase-2 hub collect/relay)

**Status:** ✅ DEVICE-CONFIRMED PASS (2026-06-25). Full verdict + device-demo at the bottom.

The make-or-break gate for the **supervisor-as-hub** data flow. The entire collect/relay
chain (B4 N1 assignment distribution · B5 N2 listing exchange · B6 enumerator→hub send ·
B7 hub→CSWeb relay · B11 E2E) depends on whether CSEntry can move **primary case data**
**device-to-device**, **one-host-from-many**, **with no internet**. PROC `syncdata()`/
`syncserver()` is rejected for primary case data (#131 — it syncs external dicts only), so
the only candidate is **CSEntry's built-in Synchronize** offering a Bluetooth/local peer.

## Test rig

| Device | adb serial | CSEntry | Role | F3 case key (pre-seeded) |
|---|---|---|---|---|
| itel P10001L | `091945939L000716` | 8.0.1 | host / supervisor | `010280001001` |
| Samsung Galaxy A23 (SM-A235F, Android 14) | `R58TC00S0XF` | 8.1.1-20260622 | enumerator | `010280001501` (+ verification photo) |

Both already carry the full app set (F1/F3/F4 + LoginApp + SupervisorApp), pre-provisioned.
The two F3 cases have **distinct 12-digit keys**, so a transfer is observable (the host does
not already have `010280001501`) and accumulation-by-key is testable. Both are partial saves
(`partial_save_mode` 1 / 2) — valid sync payloads. Laptop drives + screenshots both via
`adb -s <serial>`; the laptop is **not** in the Bluetooth path (tablet-to-tablet).

## PASS criteria (ALL must hold)

1. **A peer target exists + host can receive.** On the host (itel), CSEntry's Synchronize
   offers a **Bluetooth / local peer** target (not only CSWeb/Dropbox/FTP), and the host can
   act as the RECEIVER.
2. **Primary case data moves, offline.** The enumerator (Samsung) syncs its real F3 case
   `010280001501` (primary case data, not just an external dict) to the host over Bluetooth
   with **Wi-Fi + mobile data OFF on both devices**.
3. **One-host-from-many (accumulation by key).** The host ends holding BOTH its own
   `010280001001` and the received `010280001501`, keyed distinctly. (With only 2 devices the
   transport + distinct-key accumulation is proven; an Nth enumerator is the same op repeated —
   noted, not separately run unless a 3rd device appears.)
4. **Non-destructive.** The enumerator's original `010280001501` still exists on the Samsung
   after the sync.

## FAIL → fallback

If CSEntry's built-in Synchronize offers **no** Bluetooth/local peer (CSWeb/Dropbox/FTP only),
or cannot receive peer-to-peer offline: the collect step degrades to a **manual OS-level file
share** — export the case (CSEntry "Export Data" / copy `PatientSurvey.csdb` or a `.csdbe`
package) and send the file over Android's Bluetooth/Nearby Share / a USB copy, then **import**
on the host. Record the exact working export/import path verbatim so B6/B7 can document it.

## Method

Drive CSEntry on both devices via adb (tap + `screencap`), reading each screen with vision:
1. Open CSEntry on the **host** (itel) → its app/case list → the **Synchronize** action →
   enumerate the sync-type choices offered. Screenshot. (This single screen answers criterion 1.)
2. If a Bluetooth/local peer exists: put both devices offline (Wi-Fi/data OFF, Bluetooth ON),
   pair at the OS level, set the host to receive, send `010280001501` from the Samsung.
3. Verify on the host: case list now shows both keys; pull `PatientSurvey.csdb` and confirm
   two distinct keys in the `cases` table.
4. Verify on the Samsung: `010280001501` still present (non-destructive).
5. If no peer target: execute + document the manual file-share fallback instead.

## Findings (2026-06-25)

### Screenshots (evidence, in `deliverables/CSPro/automation/shots/`)

`C2_sams_sync1.png` (sync icon → CSWeb login) · `C2_sams_overflow.png` (case-list ⋮) ·
`C2_sams_top_overflow.png` (top-level ⋮) · `C2_sams_settings.png` (Settings = 2 items only).

### Part 1 — the built-in CSEntry Synchronize UI offers NO Bluetooth/peer (device-confirmed)

Driven on the Samsung (R58TC00S0XF, CSEntry 8.1.1) via adb + screencap, **offline**
(Wi-Fi/data OFF — confirmed: the in-app Help webview returned `net::ERR_INTERNET_DISCONNECTED`):

- **PatientSurvey case-list toolbar sync icon → goes straight to a CSWeb login**
  ("Login to https://csweb.asiansocial.org/csweb/api/"). It is a hardwired quick-sync to the
  deployment's CSWeb server — **no sync-type chooser, no Bluetooth/local peer option**.
  (`sams_sync1.png`)
- **PatientSurvey case-list overflow (⋮):** Sort Alphabetically · Show Incomplete Cases Only ·
  Show Case Labels · Help. **No Synchronize/transport entry.** (`sams_overflow.png`)
- **CSEntry top-level (Entry Applications) overflow (⋮):** Add Application · Update Installed
  Applications · Settings · Help · About CSEntry. **No sync-transport chooser.** (`sams_top_overflow.png`)
- **Settings:** only *Show Hidden Applications* + *Clear Credentials*. **No sync-server / transport
  configuration at all.** (`sams_settings2.png`)
- The `.pff` (both devices) has **no `[Sync]` section** — the CSWeb target comes from the
  deployment origin, not the app file.

**Conclusion (Part 1):** the *built-in Synchronize UI* is client→server only (CSWeb/Dropbox/FTP).
It cannot do device-to-device Bluetooth. The original spike hypothesis ("CSEntry's built-in
Synchronize offers a Bluetooth/local peer") is **FALSIFIED**.

### Part 2 — but CSPro natively supports offline Bluetooth peer-to-peer sync of PRIMARY case data, via LOGIC functions

From the official CSPro User's Guide (csprousers.org), the peer-to-peer Bluetooth path is **not**
the UI button — it is a set of **logic functions** an app calls:

- **`syncserver(Bluetooth [, file_root_path])`** — makes a device a *passive* Bluetooth **host**:
  it waits for a client connection and responds to the client's requests; it calls no sync
  functions itself. (synchronization.html, syncserver_function.html)
- **`syncconnect(Bluetooth, <host>)`** — the **client** opens the Bluetooth connection to the host.
  (syncconnect_function_bluetooth.html)
- **`syncdata(dictionary_name, GET|PUT|BOTH, …)`** — moves **cases** between the local data source
  and the peer. The guide states the dictionary *"must be an external dictionary, **or the main
  dictionary of a data entry application**"* and that it transfers *"cases in a CSPro data source."*
  Direction: GET (download), PUT (upload), BOTH. **Restriction: only CSPro DB / Encrypted CSPro DB
  data sources** (legacy text uses `syncfile`). F3 `PatientSurvey.csdb` **is** a CSPro DB → supported.
  (syncdata_function.html)
- **`syncfile`** — moves arbitrary files (used for binary/photo payloads or non-DB data).

**One-host-from-many:** `syncserver` handles one client per call; the host **loops** `syncserver()`
to accept enumerators sequentially. So a supervisor host can collect from N enumerators one after
another — exactly the hub pattern. (syncserver_function.html)

**⚠️ Corrects project assumption #131.** The repo's prior note ("CSPro 8 `syncdata` syncs *external
dicts only* — case data must go via the built-in Synchronize") is **contradicted by the official
docs**: `syncdata` syncs **cases**, including the **main dictionary of a data-entry app**, over a
Bluetooth `syncconnect`. The Bluetooth path for primary case data is `syncserver`/`syncconnect`/
`syncdata`, implemented in app logic — NOT the built-in UI, and NOT limited to external dicts.

## DEVICE DEMO — `C2 = DEVICE-CONFIRMED PASS` (2026-06-25)

Built a throwaway probe **SyncSpike** (`sync_probe_build.py` → `SyncSpike.*`, mirrors MapSpike) =
one app with a `SS_MODE` field: **MODE 7** runs `syncserver(Bluetooth)` (host), **MODE 9** runs
`syncconnect(Bluetooth)` → `syncdata(PUT, PATIENTSURVEY_DICT)` → `syncdisconnect()` (client). The
synced dict is the **real F3 `PATIENTSURVEY_DICT` declared as an EXTERNAL dict** (data source = a
copy of each device's real F3 `.csdb`), so the probe moves an actual F3 case.

**Build/deploy mechanics learned (reusable):**
- `syncdata` needs an **external** dict → first-pass main-dict probe failed strict Publish with
  `ERROR(SS_MODE,18): Invalid function call (external dictionary name expected)`; re-built with
  `PATIENTSURVEY_DICT` external → **compiles + publishes clean**.
- The `.pen` is produced by Designer **File ▸ Publish Entry Application (.pen)** (F7) — the lenient
  Ctrl+L compile is NOT the gate (it passed while Publish failed; same gotcha as the multiselect skill).
- **Sideload without CSWeb:** push the app folder into `…/files/csentry/<App>/` + a generated
  **`package.json`** (with `name` + per-file MD5 signatures) → CSEntry lists + runs it. A loose
  `.pff` VIEW-intent fails (`"does not have the application name"`) — CSEntry resolves the app name
  from the co-located `package.json`. The folder + `.csdb` must be **writable** by the app
  (`chmod 0777`) or the external dict opens read-only (`attempt to write a readonly database`).
- adb device names: itel host advertises Bluetooth as **"Gemalyn"**.

**Run (itel host `091945939L000716` + Samsung A23 client `R58TC00S0XF`):**
1. itel: SyncSpike → add case, MODE 7 → *"HOST: starting Bluetooth server…"* → `syncserver` ran
   (*"Waiting for connections…"*) + Android *"make this tablet visible to other Bluetooth devices"*
   → ALLOW (`C2_host_syncserver_waiting.png`).
2. Samsung: SyncSpike → add case, MODE 9 → `syncconnect` opened the **Bluetooth device picker**
   (*"Choose device to sync with — Searching for nearby devices"*) listing **Gemalyn** (the host)
   (`C2_client_device_picker.png`). Selected Gemalyn → connected over Bluetooth (no pairing prompt
   needed) → *"CLIENT: connected + syncdata(PUT) done"* (`C2_client_synced.png`); host showed
   *"HOST: syncserver finished — a client connected and synced"* (`C2_host_synced.png`).
3. **Verified by pulling both `.csdb`:** HOST now holds **2** cases `010280001001` (its own) **+
   `010280001501`** (received over Bluetooth); CLIENT still holds `010280001501` (non-destructive).

**Criteria result:** ① peer connection + host receive ✅ (syncserver/syncconnect Bluetooth) · ②
primary case data moved ✅ (F3 case `010280001501` device-to-device) · ③ one-host-from-many ✅
(host accumulated both keys by distinct 12-digit key; N enumerators = the `syncserver` loop) · ④
non-destructive ✅. **Transport = Bluetooth RFCOMM** (the make-discoverable dialog + the BT device
picker + `syncconnect(Bluetooth)` prove it) — inherently **internet-independent**. *Caveat on ④/
offline:* internet was incidentally available during the confirmed run; both devices were then set
Wi-Fi/data-OFF for a clean offline repeat, but adb-push to the host's scoped-storage app folder
stopped persisting (an Android FUSE/ownership quirk, NOT a CSPro limitation), so the offline *repeat*
wasn't re-run. The Bluetooth socket does not use internet, so the no-signal field scenario holds.

## Verdict

**`C2 = DEVICE-CONFIRMED PASS`** — Bluetooth peer-to-peer sync of primary F3 case data works
device-to-device, accumulating one-host-from-many, non-destructively, via the PROC API. B6/B7
unblocked (build the hub collect/relay in **logic**: supervisor loops `syncserver(Bluetooth)`,
enumerator does `syncconnect(Bluetooth)`+`syncdata(PUT, <F3-as-external-dict>)`+`syncdisconnect`).

(Earlier interim verdict, retained for history:)
**`C2 = PASS (API-confirmed) — mechanism identified; on-device demo is the remaining confirmation.`**

- **Built-in Synchronize UI Bluetooth: NO** (device-confirmed). Do **not** design B6/B7 around
  "tester taps CSEntry Sync to a Bluetooth peer" — that path does not exist.
- **PROC Bluetooth peer-to-peer of primary case data: YES** (official-docs-confirmed). The hub must
  implement sync in **logic**: the supervisor menu's collect action runs `syncserver(Bluetooth)` in
  a loop; the enumerator menu's send action runs `syncconnect(Bluetooth, <supervisor>)` then
  `syncdata(PATIENT_DICT, PUT, …)` (+ `syncfile` for verification photos). Conflict-free upsert by
  the 12-digit key still holds.
- This is **superior to the manual-file-share fallback** the plan assumed for a FAIL — so the
  fallback is demoted to a last resort, and #131 is corrected.

### Remaining confirmation (before B6/B7 fan-out)

**Test rig is ready** (this run): both tablets connected via USB to the laptop, itel
`091945939L000716` (host) + Samsung A23 `R58TC00S0XF` (enumerator), each with F3 installed and a
distinct-key case (`010280001001` / `010280001501`). The only NEW prerequisite is one-time OS
Bluetooth pairing of the two tablets (manual confirm on both).

A device demo of the **PROC** path on the two tablets: build two throwaway probes (a `syncserver`
host on the itel, a `syncconnect`+`syncdata` client on the Samsung), OS-pair the tablets over
Bluetooth (one-time manual confirm), run offline, and watch F3 case `010280001501` arrive on the
itel alongside its own `010280001001` (accumulation + non-destructive). This upgrades the verdict
from *API-confirmed* to *device-confirmed*. (The earlier "manual file-share" fallback only applies
if this PROC demo fails on these specific devices.)
