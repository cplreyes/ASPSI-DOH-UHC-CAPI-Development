---
type: concept
tags: [csweb, monitoring, server, data-sync, dashboards, user-management, app-deployment, roles, permissions]
source_count: 4
---

# CSWeb — CSPro Web Server

Web-based companion to [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro|CSPro]] used for real-time survey monitoring, data synchronization, application deployment, and user management in the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/UHC Survey Year 2|UHC Survey Year 2]]. Built on PHP 8 + MySQL/MariaDB; runs on any web server with that stack.

## Feature Surface

### A. Identity & access
- **User accounts** with username/password authentication. Required user fields: `username`, `first name` (letters only), `last name` (letters only), `role`, `password` (≥8 chars). Optional: `email`, `phone`.
- **Bulk user provisioning** via CSV upload through the Users dashboard. Format: `username, first name, last name, user role, password, email, phone`. Header row supported via checkbox.
- **Built-in roles ship as exactly two**: `Administrator` (all 5 dashboards + all dictionary up/down + can log into CSWeb) and `Standard User` (no dashboard access — cannot log into CSWeb — but can up/download dictionaries via CSEntry/Batch/Data Manager and deploy apps; default fallback when a custom role is deleted).
- **Custom roles** combine any subset of the two permission axes; ≥1 permission must be assigned. Role names cannot be edited (delete + re-add to rename).
- Credentials are hashed and stored in secure storage on the device after first sync; can be cleared from CSEntry settings.

### B. Application lifecycle
- **Application upload** — the Designer's `Tools → CSPro Deploy Application` packages `.pen` + `.pff` + dictionary and uploads to the server.
- **Device-side install** — `CSEntry → Add Application → <server> → INSTALL` pulls the package.
- **Programmatic app updates** — `syncapp()` from logic, or `Update Installed Applications` from the device, refreshes a running app to a newer server version.
- **File uploads via the CSWeb web UI** — admins can post arbitrary files to the server outside the Designer flow.

#### Project deploy procedure (as-built 2026-06-12)

The F1/F3/F4 deploy is built around one hard-won fact: **Designer's Publish auto-bundles external-dictionary `.dcf` files but NEVER their `.dat` data files** — so all 8 `psgc_*.{dcf,dat}` lookup files must be Add-Files'd on EVERY deploy or the PSGC cascades arrive empty on device.

1. **Publish** from Designer (`Tools → CSPro Deploy Application`) — agent-drivable.
2. **`automation/auto_deploy.py <F1|F3|F4>`** adds the 8 PSGC files and verifies the deploy dialog: package name, files tree, main-dcf-only sync, CSWeb URL.
3. **`--deploy`** clicks Deploy and confirms the `Application Deployed Successfully` popup.

Lessons encoded in the script:

- **`.dat` is never bundled** — Designer packages the external-dict `.dcf`s automatically but silently omits the `.dat` files; the 8 `psgc_*` pairs are re-added by `auto_deploy.py` every time.
- **The publish packager is a STRICTER FMF parser than Designer open+compile** — an application that opens and compiles clean in Designer can still be rejected at packaging time (legacy standalone `CaptureDateFormat` lines were rejected 2026-06-12; capture types are now owned by `automation/optimize_capture_types.py`, which strips the legacy lines in favor of combined `Date,YYYYMMDD`).
- **CSDeploy.exe is its own process** — the deploy dialog does not belong to the Designer window; automation has to attach to it separately.

### C. Data movement
- **Case-level differential sync** — `syncdata(PUT/GET, dict)` moves only new or modified cases. Direction can be one-way (upload-only or download-only) or two-way.
- **Paradata sync** — `syncparadata(PUT/GET)` moves operator-event logs (timing, navigation, edits).
- **Arbitrary file sync** — `syncfile(direction, fromPath, toPath)` for non-data files (images, `.pen`, `.pff`).
- **Transport** — HTTPS supported and recommended; encryption support for data-at-rest on the tablet so encrypted data isn't undone in transit.

### D. Server-side data store
- Case data is stored in a **MySQL/MariaDB** database on the server.
- **Relational break-out** — `php bin/console csweb:process-cases` converts case data into a separate relational database. Each invocation runs for 5 minutes; schedule via cron / Task Scheduler. Configuration is per-dictionary (Source Data, Database name, Hostname, DB credentials, optional JSON of Process Cases Options).
- **Process Cases Options** lets you specify which dictionary variables get broken out, keeping the relational tables narrow.

### E. Reporting & dashboards
The five dashboards exposed by CSWeb are: `data`, `report`, `apps`, `users`, `roles`. The `report` dashboard contains:

- **Sync Report** — pivot of cases-uploaded against the dictionary IDs (typically province / district / EA / totals). Column filters refine displayed values; global ID search; CSV upload of code↔label pairs (consecutive, lowest-level first).
- **Map Report** — case-level geo-visualization. Cases are plotted only when the dictionary AND data both contain `latitude` and `longitude`; cases without GPS are silently omitted. Click a marker to open a popup with case key + lat/long + a **View Case** link + up to five custom configurable fields. Two ID-level filters (first two ID items in the dictionary) gate which markers are visible.

> [!note] What's NOT in the documented CSWeb feature surface
> The CSWeb User's Guide does **not** document an automated-alerts feature for missing data, upload delays, duplicates, non-response patterns, or unusual interview duration. Earlier iterations of this concept page (and the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Revised Inception Report|Revised Inception Report]] section on the CSWeb platform) listed those as built-in capabilities. Either (a) the feature exists in a newer CSWeb release not on csprousers.org, (b) the IR's "automated alerts" language was aspirational, or (c) alerts are derivable downstream from the broken-out relational DB but not native to CSWeb. Verify before any DOH-facing communication treats alerts as a built-in capability.

### F. Operations & exports
- **Data tab download** — for each dictionary listed, click the download icon to fetch a PFF that auto-launches the Data Manager tool, then authenticate with CSWeb credentials to download a single CSPro DB (`.csdb`).
- **`sync.log`** on the device captures every sync operation; useful for diagnosing upload failures end-to-end.

## Permission Model — verified

CSWeb has exactly two permission axes, no others:

| Axis | Granularity | What it gates |
|---|---|---|
| **Dashboard permissions** | 5 binary checkboxes — one per dashboard | Login + access to that dashboard's functionality (`data`, `report`, `apps`, `users`, `roles`) |
| **Dictionary permissions** | Binary up/download per dictionary | Whether CSEntry / Batch / Data Manager can sync that dictionary on this user's behalf |

> [!warning] What CSWeb does NOT support natively
> - **No row-level filtering** — dashboards show all rows the user has dictionary access to; no "regional", "cluster-of-assignment", or "own queue" predicate.
> - **No time-window permission** — no "last 7 days only" gating.
> - **No alert-config permission** — alerts aren't a documented CSWeb feature.
> - **No "limited dataset" permission** — either you can up/download a dictionary or you can't.
>
> Permissions richer than this require either (a) modifying CSWeb's PHP source, (b) splitting the survey into multiple dictionaries (e.g., per region), or (c) achieving the discrimination downstream of the relational break-out (Data Settings → BI tool).

## Operational Role

- Assistant data managers are responsible for daily CSWeb monitoring.
- Interim data extracted within the first full week of collection for initial quality review.
- Weekly data extraction for quality control and interview count verification.
- After fieldwork, full dataset extracted for final validation and cleaning.
- Enumerators sync completed interviews daily, before 10 PM.

## Project-Wide Role Mapping (IR Fig. 4 → CSWeb permission shapes)

The Inception Report has 10 organizational titles. CSWeb's permission model collapses them into **three to four distinct permission shapes**:

| CSWeb permission shape | Dashboards | Dictionaries | IR titles that fit |
|---|---|---|---|
| **Full admin** | all 5 | all up/down | Project Director, Survey Manager |
| **Data observer** | `data`, `report` | per-dictionary download (no upload) | Data Manager, Field Manager, Project Coordinator, Assistant Data Managers, Field Supervisors |
| **Operator** *(optional split)* | `data` only | per-dictionary download | Research Associate, Project Assistant — case-level QC without report-dashboard access |
| **Sync identity** (built-in `Standard User`) | none | all up/download via CSEntry | Survey Enumerators |

Functional differences inside "Data observer" (Monitor sees alerts but no full export; Field Supervisor sees only their region) **cannot be expressed in CSWeb's permission model**. They become project-level conventions, not enforced permissions.

The [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F2 Admin Portal|F2 Admin Portal]] seeds **five named roles** (Administrator, Data Manager, Monitor, Operator, Field Supervisor) plus a vestigial built-in Standard User. The five names collapse onto exactly these shapes: Data Manager, Monitor, and Field Supervisor all carry identical default permissions (the **Data observer** shape); Administrator = Full admin; Operator = the operator split; Standard User = the sync identity. So "10 IR titles → 4 permission shapes → 5 F2 role names" is consistent — the F2 mirror is 1:1 at the permission-shape level, not the role-name count.

## Project Relevance

> [!info] Current state (as-built 2026-06-12)
> CSWeb 8.0.1 is **LIVE at `csweb.asiansocial.org`** — no longer a future target, and Dropbox fallback framing is retired. Three application packages (F1, F3, F4) are deployed; tablet↔server sync is proven for all three instruments. The relational break-out databases and the Sync Report are running in production (breakout DBs refreshed on a 5-minute cron). Role-permission lesson from go-live: **field-sync permission is granted per dictionary** — F3/F4 syncs returned 403 until their dictionaries were explicitly enabled on the syncing role; enabling F1 alone is not enough. (Source: log.md entry 2026-06-12)

- **F2 has no CSWeb** — F2 is a Cloudflare Pages PWA with a Worker JWT proxy; its operational backplane is designed separately. See [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Synchronization]] for the F1/F3/F4 sync architecture. The [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F2 Admin Portal|F2 admin portal]] mirrors this concept page's permission model (1:1 at the permission-shape level — see the role-mapping note above) so a single role taxonomy governs both systems.
- **`sync.log` discipline** — every sync issue starts with "send us your sync.log"; bake this into the enumerator manual.

## Sources

- (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSWeb Users Guide]]) — authoritative for the permission/dashboard model
- (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Revised Inception Report]])
- (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro 8.0 Complete Users Guide]])
- (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro Android Data Transfer Guide]])
