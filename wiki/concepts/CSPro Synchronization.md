---
type: concept
tags: [cspro, csweb, sync, dropbox, ftp, bluetooth, deployment, paradata]
source_count: 2
---

# CSPro Synchronization

CSPro's mechanism for moving data between interviewer devices in the field and a central server (or between two devices directly via Bluetooth). The architecture supports both fully online and fully offline collection scenarios, and is the linchpin of the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/UHC Survey Year 2|UHC Survey Year 2]] data flow from enumerator tablets to the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSWeb|CSWeb]] server.

## Architecture

CSPro supports two transport modes:

1. **Internet sync** between interviewer devices and a central server (CSWeb / Dropbox / FTP). Wi-Fi or mobile data (2G/3G/4G).
2. **Bluetooth sync** between two devices in close proximity, no Internet required. The supervisor's device acts as a local server collecting from interviewer devices, then later uploads to the central server when connectivity is available.

Sync can be **one-way** (upload only or download only) or **two-way** (both). Both data files (CSPro `.csdb`) and arbitrary non-data files (`.pen`, `.pff`, images, text) can be synchronized.

Sync is **case-level** for CSPro data: only cases that are new or modified since the last sync are transferred. This minimizes bandwidth and reduces the chance of two interviewers overwriting each other's work — as long as they don't modify the *same* case at the same time.

## Server options

| Server | When to use | Trade-offs |
|---|---|---|
| **CSWeb** | Best for large surveys/censuses; org has web-server and security expertise | PHP + MySQL; needs hosting + maintenance + security capacity |
| **Dropbox** | Small/medium surveys; no server expertise needed | Data lives on Dropbox's servers; free; zero setup |
| **FTP** | Small/medium when Dropbox is unacceptable but CSWeb is impractical | Need to run/maintain an FTP server |

> **For UHC Survey Year 2 the chosen server is CSWeb.** Dropbox is the practical fallback during early bench-testing — the same Simple Synchronization options can be flipped over without code changes.

## Two ways to set up sync

### Simple Synchronization
Configured through the GUI under `Options → Synchronization Options` in the application. Suitable when:
1. You have a single questionnaire app.
2. You only need to sync the main dictionary.
3. The server is CSWeb, Dropbox, or FTP.
4. You only need to download `.pen` / `.pff` files alongside the data.

### Synchronization from Logic
Required when:
1. You have multiple applications (listing app + questionnaire app + menu launcher).
2. You need to sync external dictionaries.
3. You need to sync arbitrary additional files.
4. You need Bluetooth (peer-to-peer).
5. You want fine-grained control over sync direction per file.

## The `sync*` logic functions

| Function | Purpose |
|---|---|
| `syncconnect(server)` | Open a session. Server is one of `CSWeb`, `Dropbox`, `FTP`, `Bluetooth`. Returns true on success — wrap subsequent sync calls in `if syncconnect(...) then ... endif`. |
| `syncdisconnect()` | Close the session. |
| `syncdata(direction, dictionary)` | Move CSPro cases. Direction is `PUT` (upload) or `GET` (download). Only modified cases are transferred. **Always prefer this to `syncfile` for CSPro data files.** |
| `syncfile(direction, fromPath, toPath)` | Move arbitrary non-data files. Always full copies. |
| `syncparadata(direction)` | Move paradata logs. |
| `syncapp()` | Update the running application from a newer version on the server. |
| `syncmessage()` | Send/receive string messages to/from a Bluetooth peer. |
| `synctime()` | Returns time of last sync for a data file or specific case. |
| `syncserver(Bluetooth)` | Run a passive local server on this device that waits for incoming Bluetooth connections (used by supervisor's device). |

### Canonical multi-app sync example

```
string ServerUrl = "https://www.myserver.org/api";

if syncconnect(CSWeb, ServerUrl) then
    syncdata(PUT, MY_LISTING_DICT);
    syncdata(PUT, MY_QUESTIONNAIRE_DICT);
    syncfile(GET, "/my-project/my-menu/my-menu.pen", "./menu.pen");
    syncfile(GET, "/my-project/my-menu/my-menu.pff", "./menu.pff");
    // ... pull updated app files for each sub-application
    syncdisconnect();
endif;
```

CSPro 7.0+ ships an example application called **Synchronization in Logic** that demonstrates exactly this pattern (and also a Bluetooth variant).

### Bluetooth pattern

```
// Client (interviewer device)
if syncconnect(Bluetooth) then
    syncdata(PUT, SURVEY_DICT);
    syncdisconnect();
endif;

// Server (supervisor device)
syncserver(Bluetooth);
```

The client and server must be in physical proximity, and the operators must coordinate to start their respective routines at roughly the same time.

## Application deployment

The sync functions assume the application is **already on the device**. To get an application onto a fresh device the first time, two paths:

1. **USB copy** — `.pen` + `.pff` into `<external storage>/Android/data/gov.census.cspro.csentry/files/csentry/` (CSPro 7.5+) or `<external storage>/csentry/` (older).
2. **CSPro Deploy Application tool** (`Tools → CSPro Deploy Application`) — packages the app and uploads to a server. Field staff install via `CSEntry → Add Application → <server> → INSTALL`. Updates can later be re-deployed and pulled with `Update Installed Applications` or programmatically via `syncapp()`.

## Downloading collected data from the server

CSPro's Dropbox sync does **not** store a single combined data file. Each sync writes a per-case file under `/CSPro/DataSync/` on the server. To assemble a usable `.csdb`:

1. `Tools → Data Viewer`
2. `File → Download...` → pick the server, click Connect.
3. Select the application, set save path/name, click Download.
4. Combined `.csdb` opens in Data Viewer.

Same workflow works for CSWeb (data stored in MySQL on the server) and FTP (per-case files).

## Troubleshooting

The first thing to check is **network connectivity itself**. If you can't reach `https://dropbox.com` from the device's browser, the sync will never connect.

For deeper diagnosis, look at `sync.log`:

- **Android (CSPro 7.5+)** — `<external storage>/Android/data/gov.census.cspro.csentry/files/csentry/sync.log`
- **Android (older)** — `<external storage>/csentry/sync.log`
- **Windows** — `%AppData%\CSPro\sync.log` (also reachable via `Help → Troubleshooting → sync.log` in the Designer)

The log captures all sync operations including Deploy Application uploads/downloads and Data Viewer downloads. Always attach it when emailing the support list.

## Project relevance

- **CSWeb is the production target** — the project's entire data flow assumes it. Until it's stood up, Dropbox is the bench-test fallback that needs zero infrastructure.
- **Bench test path for Tranche 2** — `Deploy Application → Dropbox` is the lowest-friction way to demonstrate end-to-end "PC → tablet → upload → Data Viewer" without waiting on the SJREB chain.
- **Multi-app sync pattern** — if F1 / F3 / F4 end up as separate `.pen` files plus a launcher, lift the canonical example above directly. Each annex dictionary becomes one `syncdata(PUT, ...)` call.
- **Bluetooth fallback** — relevant for facility-head visits in connectivity-poor regions; supervisor pulls from interviewers in person. Set up the supervisor app early enough to test it before fieldwork.
- **`sync.log` discipline** — bake it into the enumerator manual. Any sync issue starts with "send us your sync.log".

## Sources

- (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro 8.0 Complete Users Guide]])
- (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro Android Data Transfer Guide]])
