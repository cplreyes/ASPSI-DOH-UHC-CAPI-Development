---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Documentations/CSWeb-help/]]"
date_ingested: 2026-05-01
tags: [csweb, csprousers, documentation, roles, permissions, dashboards, sync-report, map-report, official]
---

# Source - CSWeb User's Guide

The official CSWeb User's Guide hosted at `csprousers.org/help/CSWeb/` — the documentation that the CSPro 8.0 Complete User's Guide repeatedly punts to ("see the CSWeb help documentation"). Authored by the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/US Census Bureau|US Census Bureau]] / IPC. Ingested via clipping the seven canonical HTML pages on 2026-05-01 to fill the gap our existing [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSWeb|CSWeb]] concept page had on permissions and dashboard semantics.

## Why we ingested this

While brainstorming the F2 PWA admin portal, the project asked to mirror CSWeb's role/permission model 1:1. The CSPro 8.0 Complete User's Guide does not document CSWeb's permission schema — only one sentence ("custom roles that specify dashboard and dictionary permissions") and a pointer to the CSWeb help. Without ingesting the actual help, the role matrix was being built on guessed primitives. This source replaces those guesses with documented facts.

## Pages clipped

| Page | URL | What it covers |
|---|---|---|
| Introduction to CSWeb | https://www.csprousers.org/help/CSWeb/introduction_to_csweb.html | What CSWeb is, infrastructure (PHP + MySQL), smart sync, large-survey use case |
| Adding Roles | https://www.csprousers.org/help/CSWeb/adding_roles.html | The complete permissions schema |
| Adding Users | https://www.csprousers.org/help/CSWeb/adding_users.html | User fields, single-add UI, bulk CSV format |
| Accessing Data | https://www.csprousers.org/help/CSWeb/accessing_data.html | Data tab → download via PFF launching Data Manager → CSPro DB file |
| Sync Report | https://www.csprousers.org/help/CSWeb/sync_report.html | Cases-uploaded-by-geography report; column filters; label CSV import |
| Map Report | https://www.csprousers.org/help/CSWeb/map_report.html | GPS-required case-marker map; click-through to View Case |
| Data Settings | https://www.csprousers.org/help/CSWeb/data_settings.html | Relational break-out config + `php bin/console csweb:process-cases` |

Raw HTML clippings live in `raw/Documentations/CSWeb-help/`.

## Permission Model — Verified Facts

### Two permission axes, no others

CSWeb has exactly two permission axes:

1. **Dashboard permissions** — five dashboards, each gated by a single binary checkbox.
2. **Dictionary permissions** — per-dictionary upload/download flag (binary, applies across CSEntry, Batch, and Data Manager).

> **There is no row-level filtering, no regional/geographic permission, no time-window permission, no alert-config permission, and no "limited dataset" permission.** Either you have the dashboard checkbox or you don't; either you can up/download a dictionary or you can't.

### The five dashboards

| Dashboard | What a holder of the permission can do |
|---|---|
| **data** | Browse collected data; download a dictionary's data as a single CSPro DB (`.csdb`) via PFF that launches the Data Manager tool |
| **report** | View Sync Report (cases uploaded by geography, columnar by dictionary IDs, code-label CSV import supported) and Map Report (GPS markers per case, click-through to View Case, two ID-level filters) |
| **apps** | Application/dictionary management on the server (Deploy Application targets) |
| **users** | Add/edit/delete users; single-add UI and bulk CSV import |
| **roles** | Add/edit/delete custom roles; check dashboard and dictionary permission boxes |

### Built-in roles (only two ship with CSWeb)

| Role | Dashboards | Dictionaries | CSWeb login |
|---|---|---|---|
| **Administrator** | All 5 | All up/down | Yes |
| **Standard User** | None | All up/down (via CSEntry, Batch, Data Manager) | **No** — but can deploy applications via the Deploy Application tool. **Default fallback** assigned when a custom role is deleted. |

All roles can download applications using CSEntry.

### Custom roles

Admin-defined. Combine any subset of the 5 dashboard checkboxes plus per-dictionary checkboxes. Constraints:

- At least one permission (dashboard or dictionary) must be assigned.
- The role's name **cannot** be edited — to rename, delete and re-add.

## User Model — Verified Facts

### Required user fields
- `username`
- `first name` (letters only)
- `last name` (letters only)
- `role` (must match an existing role name exactly)
- `password` (≥8 characters)

### Optional user fields
- `email`
- `phone`

### Bulk CSV format

```
username, first name, last name, user role, password, email, phone
```

- Header row supported via a checkbox during import.
- Role must be exactly `Administrator`, `Standard User`, or a custom role name.

Documented examples:

```csv
user007, James, Bond, Administrator, PasSwOrD7
user008, Bill, Timothy, Standard User, PasSwOrD8, b8@gmail.com, 123-4567
```

## Data Settings — Relational Break-Out

CSWeb can break out collected case data into a separate relational MySQL/MariaDB database for downstream BI/SQL reporting. Configuration fields per dictionary:

- **Source Data** — dictionary in CSWeb to be broken out
- **Database name** (must differ from the CSWeb database)
- **Hostname**
- **Database username**
- **Database password**
- **Additional Options** — JSON file with extra configuration (e.g., the Process Cases Options that pick which dictionary variables get broken out)

### Execution

`php bin/console csweb:process-cases` from the CSWeb directory.

- Each invocation runs for **5 minutes**, then exits.
- Schedule via cron (UNIX) or Task Scheduler (Windows) for continuous processing.
- Manual runs may need multiple iterations to drain the queue.
- Processes only new cases since the last run.

Deleting a data configuration removes only the configuration; the target relational database is **not** dropped.

## Map Report — GPS Requirement

Cases are plotted only when the dictionary and data both contain `latitude` and `longitude`. Cases without GPS are silently omitted from the map. Click a marker to open a popup with case key + lat/long + a **View Case** link + up to five custom configurable fields. Two ID-level filters (first two ID items in the dictionary) gate which markers are visible.

## Sync Report — Geography Pivot

Pivot of cases-uploaded against the dictionary IDs (typically province / district / EA / totals). One column per ID level. Code-label CSV upload is supported but ordering is strict: the first pair must define the lowest-level ID; later pairs must follow consecutive ID order; skipping breaks all subsequent labels. By default only codes display.

## Critical Implications for Project

### CSWeb's permission primitives are coarser than the IR-Fig-4 organizational chart implies

The IR project structure has **10 distinct titles** (Project Director / Survey Manager / Data Manager / Field Manager / Project Coordinator / 3 ADMs / 6 RAs / 4 PAs / 20 Field Supervisors / 100 Survey Enumerators). CSWeb cannot express functional differences like "Monitor sees alerts but no full export" or "Field Supervisor sees only their region" because **alerts are not a documented CSWeb feature** and **regional row-level filtering is not a documented permission**.

Practically, the IR's 10 titles collapse onto **three distinct CSWeb permission shapes**:

1. **Full admin** — `data + report + apps + users + roles` + all dictionaries up/down. (Project Director, Survey Manager.)
2. **Data observer** — `data + report` + per-dictionary download (no upload). (Data Manager, Field Manager, Project Coordinator, Assistant Data Managers, Field Supervisors. Functionally identical in CSWeb terms.)
3. **Sync identity** — built-in `Standard User`; no dashboards, dictionary up/down via CSEntry only. (Survey Enumerators.)

A possible fourth shape — **Operator** — would be `data` only (no `report`) plus per-dictionary download. (RAs, Project Assistants for case-level QC.)

### What's NOT in the documented CSWeb feature surface

The wiki concept page (and CSPro 8.0 release notes summary) listed "automated alerts — missing data, upload delays, duplicate entries, non-response patterns, unusual interview duration." **The CSWeb User's Guide does not document an alerts feature.** Possibilities:

- The feature exists in a newer CSWeb release not yet on csprousers.org;
- "Automated alerts" was aspirational language in the project's IR rather than a CSWeb capability;
- Alerts are achievable downstream by querying the broken-out relational tables (Data Settings) but not by CSWeb itself.

This needs verification before any project communication treats alerts as a built-in CSWeb capability.

### Implication for F2 PWA admin portal

The user has committed to a 1:1 mirror (Question 1, option a). The honest interpretation of "1:1 mirror" against CSWeb's verified primitives is:

- F2 admin portal exposes the **same five dashboards** (data, report, apps, users, roles).
- F2 has **per-instrument** binary up/download permissions (where "instrument" means F2 self-admin, paper-encoded path, optional CAPI build).
- The project-wide **5-role taxonomy** still works as labels, but in CSWeb's permission model they collapse to 3 effective permission shapes (or 4 if Operator is split out). F2 can either (i) match this exactly or (ii) extend with primitives CSWeb lacks (regional filtering, alert config) — which would break 1:1 alignment.

## Sources

- (Source: this clipping set — `raw/Documentations/CSWeb-help/`)

## Cross-references

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSWeb|CSWeb]] — concept page (to be updated with the verified permission model)
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Synchronization|CSPro Synchronization]] — how CSEntry talks to CSWeb
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro Documentation|Source - CSPro Documentation]] — index page that omits the CSWeb help URL
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro 8.0 Complete Users Guide|Source - CSPro 8.0 Complete Users Guide]] — punts to "CSWeb help documentation" without including it
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/US Census Bureau|US Census Bureau]] — author/maintainer

> [!note] Source format
> The clipped HTML files are the verbatim authoritative source. The summary above is faithful but condensed; for any constraint that needs a literal quote, refer back to the corresponding `.html` file under `raw/Documentations/CSWeb-help/`.
