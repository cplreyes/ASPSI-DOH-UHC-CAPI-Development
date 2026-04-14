---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Documentations/CSPro Android Data Transfer Guide]]"
date_ingested: 2026-04-09
tags: [cspro, csentry, sync, csweb, dropbox, bluetooth, deployment]
---

# Source - CSPro Android Data Transfer Guide

A short, practical guide from the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/US Census Bureau|US Census Bureau]] covering how to move data and applications between development PCs, enumerator devices, and a server. This document is the operational complement to the synchronization sections in [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro 8.0 Complete Users Guide]] — where the complete guide explains *what* the sync system is, this guide tells you *which buttons to press*.

## Key takeaways

### Choosing a server

| Option | When to use |
|---|---|
| **CSWeb** | Organizations with web-server experience and cyber-security capacity. Best for small-to-very-large surveys and censuses. |
| **Dropbox** | Smaller organizations without server expertise. No setup or maintenance, but data lives on Dropbox's servers. |
| **FTP** | Smaller surveys where Dropbox is unacceptable but a CSWeb stand-up is impractical. |

For [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/UHC Survey Year 2|UHC Survey Year 2]] the project commitment is to **CSWeb** (per the inception report). Dropbox is the practical fallback if the CSWeb stand-up slips.

### CSPro Deploy Application tool (one-shot deployment)

`Tools → CSPro Deploy Application` packages a single-application project so field staff can install it on their device by tapping `Add Application → <server>` in CSEntry. Workflow:

1. Set Package name (e.g., `my-questionnaire`).
2. Drag the application directory onto the Files box (only `.ent` and `.pff` are auto-included; the `.ent` is deployed as a `.pen`).
3. Leave the main dictionary checked — this prepares the server to accept uploaded data.
4. Pick the server (Dropbox / CSWeb / FTP) and click Deploy.
5. On the device, `CSEntry → Add Application → <server> → INSTALL` pulls the package down.

### Simple Synchronization (single-application project)

Set under `Options → Synchronization Options` in the application:

1. Enable/disable sync.
2. Pick the server (URL required for CSWeb/FTP; Dropbox URL is fixed).
3. Direction:
    - **Upload changes to server** — most common for interviewers; only modified data goes up, nothing comes down.
    - **Download changes from server** — for supervisors who watch but don't edit.
    - **Sync local and remote changes** — bidirectional; if two interviewers modify the same case at the same time, one will overwrite the other.

### Synchronization from Logic (multi-application or non-data files)

For projects with multiple apps (e.g., a listing app + questionnaire app + menu app), Simple Synchronization isn't enough. The pattern uses CSPro logic functions:

```
if syncconnect(Dropbox) then
    syncdata(PUT, MY_LISTING_DICT);
    syncdata(PUT, MY_QUESTIONNAIRE_DICT);
    syncfile(GET, "/my-project/my-menu/my-menu.pen", "./menu.pen");
    syncfile(GET, "/my-project/my-menu/my-menu.pff", "./menu.pff");
    // ... sync each .pen and .pff for the listing and questionnaire apps
    syncdisconnect();
endif;
```

`syncconnect` opens the session, `syncdata` moves cases (only deltas, by case), `syncfile` moves arbitrary files (always full copies — prefer `syncdata` for CSPro data), `syncdisconnect` ends the session. Wrap in `if syncconnect(...) then ... endif` so the rest of the logic only runs if the connection succeeded. CSPro 7.0+ ships an example application called **Synchronization in Logic** that demonstrates this exact pattern.

### Bluetooth synchronization

Same logic functions, but `syncconnect(Bluetooth)` instead of `syncconnect(Dropbox)`. Used when the interviewer device cannot reach the Internet — a supervisor's device acts as the local server (`syncserver(Bluetooth)`), the interviewer's device is the client. The supervisor later uploads to the central server when they get connectivity. CSPro 7.0+ ships a Bluetooth example as part of "Synchronization in Logic".

### Downloading collected data from the server

CSPro's Dropbox sync does **not** store a single combined data file in Dropbox. Each sync writes a per-case file to `/CSPro/DataSync/`. To get a usable single `.csdb` file:

1. Open `Tools → Data Viewer`.
2. `File → Download...` → select the server, click Connect.
3. Pick the application, browse to a save location, click Download.
4. The combined `.csdb` opens in Data Viewer.

### Switching Dropbox accounts

- **Windows**: `File → CSPro Settings → Clear Credentials`.
- **Android**: CSEntry → Entry Applications screen → vertical-ellipses menu → `Settings → Clear Credentials`.

## Why this matters for the project

- **Tranche 2 bench test** — even before CSWeb is stood up, the Deploy Application tool plus a Dropbox account is enough to demo end-to-end "developer PC → enumerator tablet → upload → Data Viewer" for the DOH client. This is the lowest-friction proof that the CAPI app is ready.
- **CSWeb deployment plan** — once the server is up, the same Simple Synchronization options will be flipped from Dropbox to CSWeb without changing the application. The PFF can pre-bake the URL.
- **Multi-app sync** — if [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/UHC Survey Year 2|UHC Survey Year 2]] ends up with separate F1, F3, and F4 apps plus a launcher, the Sync-from-Logic pattern is the template — directly copy the example structure and substitute dictionary names.
- **Bluetooth fallback** — relevant for facility-head interviews in connectivity-poor regions; supervisors can collect from interviewers in person and upload later.

## Notes and caveats

- The doc references CSPro 7.0+ examples; in 8.0 the example application is still bundled but the menu paths may differ slightly.
- Bluetooth sync requires both devices to be in close physical proximity and the operators to start their respective routines at roughly the same time — not appropriate for unattended field workflows.
- `sync.log` (in `<external storage>/Android/data/gov.census.cspro.csentry/files/csentry/` on Android, `%AppData%\CSPro` on Windows) is the first place to look for sync errors. Always attach it when asking the support list for help.
