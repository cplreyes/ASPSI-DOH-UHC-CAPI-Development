---
title: "06 — Phase 8: CSWeb and Tablets"
category: deliverable
tags: [capi, cspro, csweb, csentry, deployment, sync, tablets, uhc-y2]
last_updated: 2026-05-08
status: draft
---

# Phase 8 — Sync, Packaging, Deployment (CSWeb + Tablets)

This is the longest, most operational phase in the CAPI workflow. Phase 6 produces a `.pen`; Phase 7 proves it correct on a desk; Phase 8 turns that artifact into something a real enumerator can pick up, run, and sync from a tablet over a real network. Three independent tracks must converge before main fieldwork: a working **server**, a working **client**, and a working **connectivity layer** that ties them together.

For UHC Year 2 the deadline is hard: **completion before Aug 1st-week supervisor training**. Anything not validated end-to-end before that date becomes training-day risk.

---

## 8.1 Phase 8 mental model

Phase 8 is "get the application to enumerators with a working data path back to the server". The phrase has three operational halves and they must each succeed independently before they can be combined:

| Track | Owns | Pass criterion |
|---|---|---|
| **Server** | Wampserver host, MySQL, CSWeb 7.7, dictionaries registered, users + roles, DNS / static IP, HTTPS | Dashboard reachable from a non-server machine over the configured URL; sample case visible in Data tab |
| **Client** | CSEntry build, packaged `.pen`, packaged `.pff`, tablet provisioning SOP, backup/restore configured | Tablet completes a smoke-test case on the actual device hardware that will be issued |
| **Connectivity** | Sync URL configured in user settings, credentials provisioned, `syncconnect`/`synchronize_data` exercised over tablet's data plan | Round-trip: case captured on tablet → arrives in CSWeb dashboard within the SLA window |

The **dependency order** is server → connectivity → client. You can build the client first chronologically (Phase 6/7), but you cannot **validate** it without the server, and you cannot **deploy** it without connectivity. Everything below assumes you start with a green Phase 7 build and work outward toward the field.

For UHC: **F1 is already packaged** (`FacilityHeadSurvey.pff` exists from the April pilot). **F3 and F4 need PFFs** after their June 12 build cutoff. **F2 PWA is out of scope for this phase** — that track has its own deployment story (staging/production CDN projects) covered elsewhere.

### Why three tracks, not one big checklist

When sync fails, it always fails on exactly one track. Treating Phase 8 as a flat checklist trains you to retry random things. Treating it as three independent tracks trains you to **isolate the failure**:

- "Sync fails" → which track is broken?
- Server → can I reach the dashboard from a browser on a different machine?
- Connectivity → can the tablet ping the server? does HTTPS resolve? are creds correct?
- Client → is `syncconnect` returning success but `synchronize_data` failing? is the dictionary registered?

Triage discipline saves hours. The triage matrix is in [[#8.21 Phase 8 exit criteria]].

### Deadline-anchored mental model

Work backward from Aug 1st-week:

| Date | Milestone |
|---|---|
| Aug 1st-week | Supervisor training — server + 1 demo tablet must be live |
| Jul 4th-week | Tablet bring-up sprint — provision N tablets end-to-end |
| Jul 3rd-week | UAT round 2 of CAPI on real hardware over real network |
| Jul 2nd-week | UAT round 1 — internal smoke test through the full sync stack |
| Jun 4th-week | F3/F4 packaged as PFFs; all three apps registered on CSWeb |
| Jun 3rd-week | CSWeb users + roles configured against final enumerator roster |
| Jun 2nd-week | CSWeb server provisioned on production hosting target (office static IP or VPS — see [[#8.22 Open decisions]]) |
| Jun 1st-week | F3/F4 entry app build complete (Phase 6 exit) |

Anything that slips before mid-July compresses the bring-up sprint. Anything that slips after mid-July compresses training prep.

---

## 8.2 Server provisioning — Wampserver 3.2.6

**Goal**: stand up the local web/MySQL/PHP stack that hosts CSWeb on the production server box.

The reference walkthrough is **(Khurshid 2022-03-14)** *CSPro: How to Install Wampserver, CSPro and CSWeb server*. We follow it exactly for the production install, with one substitution: the **CSWeb folder is renamed `cswebtest` in his demo, but for ASPSI we name it `csweb` (no test suffix)** to make the URLs production-grade. Every URL in the rest of this guide assumes the production folder name `csweb`.

### 8.2.1 Hardware / VM specs

For ASPSI's CSWeb host (whether on-prem static-IP machine or cloud VPS):

| Resource | Minimum | Recommended | Notes |
|---|---|---|---|
| RAM | 4 GB | 8 GB | MySQL + Apache + PHP + dashboard concurrency. 4 GB is tight when the relational break-out cron runs at the same time as field syncs |
| Disk | 100 GB | 250 GB SSD | Dictionary tables grow; sync logs grow; backups grow. SSD matters when the Data tab is querying live |
| OS | Windows 10 Pro x64 | Windows 11 Pro x64 or Windows Server 2022 | Wampserver 3.2.6 64-bit needs a 64-bit Windows |
| CPU | 2 vCPU | 4 vCPU | Apache and MySQL share these; PHP CLI cron also competes |
| Network | 10 Mbps up | 50 Mbps up | Upload bandwidth matters more than download — tablets push data |
| Power | UPS recommended | UPS mandatory if on-prem | Mid-fieldwork power flap = mid-sync failures and partial commits |

### 8.2.2 Visual C++ redistributable prerequisites

Wampserver will not start without these. **(Khurshid 2022-03-14)**: *"In order to successfully install and run the WAMP server, please make sure that you have installed the following Microsoft Visual C++ Re-distributable packages: 2008, 10, 12, 13, 15 and 17."*

Install all six (both x86 and x64 where Microsoft ships separate installers — Wampserver 3.2.6 64-bit nominally only needs x64, but installing both avoids one class of "DLL not found" errors when third-party PHP extensions get added later):

- Visual C++ 2008 redistributable
- Visual C++ 2010 redistributable
- Visual C++ 2012 redistributable
- Visual C++ 2013 redistributable
- Visual C++ 2015–2019 redistributable (single combined installer covers both — also satisfies the 2017 requirement)

Reboot the server after installing all VC++ packages. Yes, Windows asks you to. Don't skip.

### 8.2.3 Wampserver 3.2.6 64-bit install

1. Download Wampserver 3.2.6 64-bit from `wampserver.com`. Pin the version — newer Wampserver releases ship with PHP versions that may not match CSWeb 7.7's tested matrix.
2. Run installer as Administrator.
3. Accept defaults except:
   - **Default browser**: say **Yes** (Windows defaults to Edge/IE; Wampserver wants something with a working dev console; Chrome or Firefox is fine).
   - **Default text editor**: say **No** (keep Notepad++ or whatever the host already has).
4. Let installer finish. Tray icon appears.
5. Wait. Tray icon transitions: **red → amber → green**. Green = all services running.

**Canonical health signal**: tray icon color. Don't proceed to step 8.3 until it's green.

### 8.2.4 Verify install

Open three things in sequence:

1. **Apache** — browse to `http://localhost`. Default Wampserver landing page should render. If it shows a 404 or browser error, Apache isn't bound to port 80 (likely conflict — Skype, IIS, or another web server is grabbing port 80; resolve before continuing).
2. **PHP** — left-click Wamp tray icon → **PHP** → **Version** → confirm 7.4.x or 8.0.x is shown. CSWeb 7.7 has been tested with both.
3. **MySQL** — left-click Wamp tray icon → **MySQL** → **MySQL console**. It prompts for the root password (none yet — press Enter). Should land at a `mysql>` prompt. Type `exit` to leave.

### 8.2.5 Document root

Wampserver's document root is `C:\wamp64\www\`. **Anything under this path is served by Apache.** This is where CSWeb 7.7 unzips into in [[#8.3 CSWeb 7.7 deployment to Wampserver]].

### 8.2.6 Production-grade install checklist

For UHC's production server box (not a dev laptop):

- [ ] Server hardware procured per [[#8.2.1 Hardware / VM specs]]
- [ ] Hostname set (e.g., `aspsi-csweb-prod`) — easier to identify in network logs
- [ ] Windows Update fully applied; pending reboots cleared before Wamp install
- [ ] All six VC++ redistributables installed; reboot completed
- [ ] Wampserver 3.2.6 64-bit installed; tray icon green
- [ ] `http://localhost` returns Wampserver landing page
- [ ] PHP version verified
- [ ] MySQL console reachable
- [ ] Wampserver added to startup (Windows Services tab — set Apache and MySQL to **Automatic**) so a server reboot doesn't take CSWeb down silently
- [ ] Windows Defender / antivirus has `C:\wamp64` in its exclusion list (otherwise scan-on-write thrashes MySQL writes during heavy sync)
- [ ] System time synced via NTP (drift breaks HMAC-style auth and confuses sync timestamps)
- [ ] Firewall configured — see [[#8.4 Network exposure]]

---

## 8.3 CSWeb 7.7 deployment to Wampserver

**Goal**: get CSWeb running under Apache, backed by MySQL, with an admin login.

### 8.3.1 Download and unzip

1. Browse to `csprousers.org` → Downloads → CSWeb 7.7. Match the version to your CSPro Designer (we run CSPro 7.7.1 on dev workstations — CSWeb 7.7 is the matched server).
2. Download the zip.
3. Verify the zip's checksum if csprousers publishes one — never deploy a zip from an unverified source onto a production box.

### 8.3.2 Deploy to document root

**(Khurshid 2022-03-14)**: *"copy the root directory of your CSWeb 7.7 project to drive colon slash wamp64 slash www slash csweb 7.7 — in my case the result will look like `c:\wamp64\www\csweb7.7`."* He renames to `cswebtest`; we rename to `csweb`.

```bash
# Conceptual — actual is unzip + manual rename in Explorer
unzip csweb-7.7.zip -d C:\wamp64\www\
mv C:\wamp64\www\csweb-7.7 C:\wamp64\www\csweb
```

After unzip:

```
C:\wamp64\www\csweb\
├── api\                  ← what tablets call
├── bin\                  ← php bin\console csweb:* commands live here
├── config\               ← will be populated by setup script
├── files\                ← non-data file uploads land here (pictures, supplementary)
├── public\               ← static dashboard assets
├── setup.php (or /setup) ← one-time config wizard
└── ui\                   ← /csweb/ui/login etc.
```

**Critical: if you skipped the rename to `csweb`, every URL in this guide that says `/csweb/` must be adjusted to match your folder name.** Pick one and stick with it. The CSWeb API URL recorded on every tablet, the bookmark every ops user uses, the entry in user-config-settings on the entry app — all of them encode this folder name.

### 8.3.3 Create the CSWeb backing database in phpMyAdmin

**(Khurshid 2022-03-14)** walks the GUI; this is the production version of the same steps:

1. Left-click Wamp tray icon → **phpMyAdmin** (typically version 5.1.x bundled with Wamp 3.2.6).
2. Default first-login: user `root`, empty password.
3. Click **New** in the left pane.
4. Database name: `csweb_uhc_y2` (project-and-year prefix; if ASPSI hosts multiple projects on the same box, the prefix prevents collision). Encoding: `utf8mb4_general_ci`.
5. Click **Create**.

Now create a dedicated user for CSWeb to use (Khurshid uses `root` directly in his demo for simplicity; **for production, never let a web app authenticate as MySQL root**):

```sql
-- Run in phpMyAdmin → SQL tab on the csweb_uhc_y2 database

CREATE USER 'csweb_user'@'localhost' IDENTIFIED BY '<long-random-password>';
GRANT ALL PRIVILEGES ON csweb_uhc_y2.* TO 'csweb_user'@'localhost';
FLUSH PRIVILEGES;
```

Save `<long-random-password>` to a password manager. You will need it again in the setup script.

Then lock down `root`:

1. **Privileges → root → Edit privileges → Change password** → set twice → **Go**.
2. Log out.
3. Log back in as `root` with the new password to confirm it took.

**(Khurshid 2022-03-14)** explicitly walks this rotation. Don't skip — phpMyAdmin with empty-password root is exposed the moment port 80 is open externally.

### 8.3.4 Configure CSWeb via the web setup script

**(Khurshid 2022-03-14)**: browse to `http://localhost/csweb/setup` (or `/csweb/setup.php` depending on the build). Khurshid's example uses `/cswebtest/setup`; ours is `/csweb/setup`.

The setup wizard:

1. **Prerequisite check page** — confirms PHP version, required PHP extensions (mbstring, pdo_mysql, etc.). Any red items must be fixed before proceeding. Common: `pdo_mysql` extension not enabled — left-click Wamp tray → PHP → PHP extensions → check `pdo_mysql` → restart Apache.
2. **Database wiring**:
   - Database name: `csweb_uhc_y2`
   - Host: `localhost`
   - DB user: `csweb_user` (NOT `root` for production)
   - DB password: the long random one from 8.3.3
3. **CSWeb admin password** — this is **separate** from the MySQL password. **(Khurshid 2022-03-14)** is explicit: *"Don't conflate the `root` MySQL password with the `admin` CSWeb password — they're different credentials."*
4. **Path to file directory**: `C:\wamp64\www\csweb\files`. This is where non-data file uploads (pictures, supplementary docs) land — see [[#8.5 CSWeb dashboard tour]] Files tab.
5. **CSWeb API URL**: this is the URL tablets will hit. **In setup, fill in the eventual production URL, not localhost** — see [[#8.4 Network exposure]] for the URL pattern. The exact suffix is `/api/` — that's literally what `syncconnect` will call.
6. **Next** → **Setup complete**.

### 8.3.5 Verify

Browse to `http://localhost/csweb/ui/login`. Login with username `admin` and the CSWeb admin password from step 3. You should land on the dashboard with [[#8.5 CSWeb dashboard tour|seven tabs]] visible.

### 8.3.6 Setup gotchas

- **PHP not on system PATH**: the relational-export command (`php bin\console csweb:process-cases`) requires PHP on PATH. **(Khurshid 2022-04-30)** hits this exact error in his demo and fixes it by adding the PHP install path (`C:\wamp64\bin\php\php7.4.x\`) to the **System Environment Variables** dialog, then closing and reopening the command prompt for the new PATH to take effect. Add this to your post-install checklist now so you don't trip on it during fieldwork.
- **Folder permissions**: `C:\wamp64\www\csweb\config\` and `C:\wamp64\www\csweb\files\` must be writable by the Apache user (typically `LocalSystem`). On a fresh install, this works out of the box. On a hardened server with file-system ACLs applied later, this can break — note the requirement.
- **Trailing slashes**: the API URL the tablet calls ends with `/api/`. Some setup scripts strip trailing slashes; some don't. Once setup completes, browse to `<your-API-URL>/api/` directly and confirm you get a JSON-ish response (often a small status payload), not a 404.

---

## 8.4 Network exposure

Localhost works for desk demos. Field tablets need to reach the server over the public internet.

### 8.4.1 Hosting decision matrix

| Option | Pros | Cons | UHC fit |
|---|---|---|---|
| **ASPSI office static IP** | No monthly cloud bill; ASPSI controls hardware; faster local backup | Office power/network outages take CSWeb down; static IP must be procured from ISP; HTTPS cert renewal is on ASPSI | Default unless ops capacity is constrained |
| **Cloud VPS (DigitalOcean / Vultr / Linode / AWS Lightsail)** | High availability; static IP included; managed firewall; trivial to scale | Monthly cost; ASPSI ops must learn cloud admin; data residency considerations (PH data on PH servers vs SG/HK) | Recommended fallback if office static IP isn't available; PH-region VPS preferred for residency |
| **Cloud (managed Windows VM on Azure/AWS)** | Pro-grade infra; Windows-native; easy snapshots | Higher cost; over-provisioned for the workload | Only if ASPSI already has Azure/AWS contract |

This is an **open decision** — see [[#8.22 Open decisions]].

### 8.4.2 DNS vs raw IP

**Strongly recommend a stable hostname** like `csweb.aspsi.example.com` over the raw IP `142.190.01.947`. Reasons:

- IPs change. Office gets a new ISP plan; cloud VPS gets re-provisioned; the IP shifts. Every shift breaks every tablet's hardcoded URL.
- Hostnames are also recoverable: if ASPSI has to migrate the box, point DNS to the new IP and the tablets keep working.
- HTTPS certs require a hostname (Let's Encrypt issues to domains, not IPs).

**(Khurshid 2022-04-30)** stays on raw IP because his demos are local. For production fieldwork over public internet, **DNS is the production-grade choice**.

DNS setup (assuming ASPSI owns `aspsi.example.com`):

1. In ASPSI's DNS provider control panel: add an `A` record `csweb.aspsi.example.com` → `<server-IP>`.
2. Wait for propagation (15 min – 24 hours; often ~1 hour).
3. From a non-server machine: `nslookup csweb.aspsi.example.com` → should resolve to your IP.
4. Browse to `http://csweb.aspsi.example.com/csweb/ui/login` from a **non-server machine** — don't trust localhost. If the dashboard renders, the network exposure is working over HTTP. HTTPS is next.

### 8.4.3 Firewall and ports

Two ports matter:

| Port | Use | Open to |
|---|---|---|
| 80 | HTTP — initial setup, redirect-to-HTTPS | Internet |
| 443 | HTTPS — production sync traffic | Internet |
| 3306 | MySQL | **Localhost only** — never expose externally |

Configure **Windows Defender Firewall** (or whatever the cloud provider's equivalent is):

```powershell
# Inbound rules — run as Administrator
New-NetFirewallRule -DisplayName "CSWeb HTTP" -Direction Inbound -LocalPort 80 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "CSWeb HTTPS" -Direction Inbound -LocalPort 443 -Protocol TCP -Action Allow
# MySQL — explicitly DENY external
New-NetFirewallRule -DisplayName "MySQL block external" -Direction Inbound -LocalPort 3306 -Protocol TCP -Action Block -RemoteAddress Any
```

If the host is behind ASPSI office NAT, port-forward 80 and 443 from the router to the server's LAN IP.

### 8.4.4 HTTPS

**(Khurshid 2022-04-30)** demos use HTTP because they're local. For UHC fieldwork over public internet, **HTTPS is mandatory**. Reasons:

- Sync credentials are sent in the request body — over HTTP they're cleartext on every public WiFi network the enumerator's tablet touches.
- Survey data — even when not strictly PII — includes facility identifiers, GPS, dates, sometimes consent capture. Treat as confidential by default.
- HTTPS prevents MITM injection of fake responses ("sync OK" when it isn't).

**Option A — Let's Encrypt (recommended)**: free, automated renewal.

1. Install **win-acme** (Windows ACME client) on the CSWeb server.
2. Run `wacs.exe`, choose option 1 (single binding), pick the Apache binding for `csweb.aspsi.example.com`.
3. Win-acme handles HTTP-01 validation, generates the cert, configures Apache (`httpd-vhosts.conf` or equivalent) to use the cert with HTTP→HTTPS redirect.
4. Schedule auto-renewal (win-acme installs a Windows Scheduled Task by default).

**Option B — Commercial cert**: if ASPSI has a security policy mandating commercial CA. Procure cert; install in Apache; configure auto-renewal reminders manually (or get a cert with multi-year validity).

**Option C — Self-signed (testing only)**: acceptable for the internal smoke test before real fieldwork, **never** for production. Self-signed certs make every tablet show a "this site is unsafe" warning that enumerators learn to click through, training them to ignore the exact warning we want them to heed.

### 8.4.5 The "tablet sync URL must be the live IP, not localhost" rule

This is **the single most-cited Phase 8 mistake**. **(Khurshid 2022-04-30)** is explicit:

> *"if we are using live IP then URL will be `http://142.190.01.947/cswebtest/api`"*

For UHC, post-DNS-and-HTTPS:

```
https://csweb.aspsi.example.com/csweb/api
```

Translation of the rule: **anywhere a sync URL is configured (entry app User Settings, PFF, Designer's Deploy Application wizard, the User Settings on tablets), substitute the production URL — never `localhost`.** The reason `localhost` is so easy to leave behind is that during desk testing with CSEntry Windows on the same machine as Wampserver, `localhost` works perfectly. The first sign that someone forgot to swap is "syncs work in the office and fail in the field" — at which point the team is already mid-fieldwork.

**Enforce it via [[#8.10 Sync session implementation in the entry app|user-config-driven URL]]** so this swap is one edit, not a code change.

### 8.4.6 Smoke-test the public surface

From a phone on cellular (not on office WiFi — that bypasses NAT):

1. Browse to `https://csweb.aspsi.example.com/csweb/ui/login` — login screen renders.
2. Browse to `https://csweb.aspsi.example.com/csweb/api/` — get a JSON-ish response (not 404).
3. Verify HTTPS lock icon — no cert warning.
4. From the same phone, try `http://csweb.aspsi.example.com/csweb/ui/login` — should redirect to HTTPS automatically.

If all four pass, network exposure is production-ready.

---

## 8.5 CSWeb dashboard tour

**(Khurshid 2022-04-30)** + (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSWeb Users Guide|Source - CSWeb Users Guide]]) — the dashboard has seven tabs. Each one matters; ops teams that don't know all seven blind-spot the parts of CSWeb they don't use, then rediscover them mid-fieldwork.

### 8.5.1 Data tab

Incoming case data per dictionary. Tree view: **dictionary → record level → ID values → individual cases**. Click through to **View Case** for a single case.

Use cases:
- Confirm a tablet's sync actually landed (search by case key or by date).
- Spot-check a single case during pretest (does Q12 = "yes" lead to Q13 being filled?).
- Download a single dictionary's data via the per-dictionary download icon — this generates a sync PFF that pulls all data for that dictionary down to your workstation as a single CSPro DB file (`.csdb`). The download icon is also how you build [[#8.13 PFF generation|pre-built PFFs]] without hand-writing them.

### 8.5.2 Apps tab

Uploaded entry-application packages (`.pen` files). Each upload registers the app + its dictionary on the server.

Use cases:
- Initial deployment — push F1, F3, F4 `.pen`s up here once Phase 6 builds are done.
- Hot-fix re-deploy — re-upload a fixed `.pen`; tablets pick it up on next sync. See [[#8.20 Hot-fix / re-publish flow]].
- Deprecate old apps — delete after fieldwork closes.

### 8.5.3 Users tab

User account CRUD. **Each user has** username, first name (letters only), last name (letters only), role (must match an existing role), password (≥8 chars), optional email, optional phone. Role assignment is one-per-user. (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSWeb Users Guide|Source - CSWeb Users Guide]].)

Use cases:
- Manual single-user add (small teams, ad-hoc additions during fieldwork).
- **Bulk CSV import** for the whole enumerator + supervisor roster — see [[#8.7 Adding users via CSV import]].

### 8.5.4 Files tab

Non-data files synced from tablets — pictures, supplementary docs, signed consent images, log files. Separate from case data; uses `synchronize_file()` not `synchronize_data()`.

Use cases:
- Photo capture (e.g., facility frontage photos for F1).
- Signed consent capture (where IRB requires image of physical signature).
- Log-file upload from tablets when troubleshooting (enumerator sends device-side log on request).

You can create folders here ahead of time to keep the file tree organized — **(Khurshid 2022-05-05)**: *"If `to_path` is not specified, then the files will be saved in the server root directory."* Always specify a destination subfolder.

### 8.5.5 Settings tab

Server-side configuration. Three subsections that matter:

- **Dictionary configuration** — for the relational break-out (per [[#8.8 Defining the dictionary on the server]]). Source DB, target relational DB, host, credentials. One configuration per dictionary that you want broken out.
- **Process Cases Options** — JSON-format additional config for which dictionary variables the relational break-out should pick up.
- **Map Report config** — per-dictionary lat/long field mapping if the dictionary has GPS items.

### 8.5.6 Reports tab

Two reports out of the box:

- **Sync Report** — pivot of cases-uploaded against the dictionary's ID items. Default columns: each ID level + total count. Filter by ID-item value. Code-label CSV import lets the report show "Region IV-A" instead of "01". (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSWeb Users Guide|Source - CSWeb Users Guide]].)
- **Map Report** — GPS markers per case (only if the dictionary has `latitude` and `longitude` fields populated). Click a marker → popup with case key + lat/long + **View Case** link + up to 5 custom fields.

**For UHC**: F1 likely has facility lat/long for Map Report; F3/F4 may not (depends on whether enumerators capture GPS at the household). Decide per-dictionary in [[#8.8 Defining the dictionary on the server]].

### 8.5.7 Roles tab

Role definitions. Two built-ins (Administrator, Standard User) ship; custom roles are admin-defined. See [[#8.6 CSWeb roles model]].

### 8.5.8 Operational visibility — what's NOT here

Per the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSWeb Users Guide|verified CSWeb User's Guide]], **CSWeb does not document an automated-alerts feature**. The IR's brainstorming language ("automated alerts: missing data, upload delays, duplicate entries, non-response patterns") is not a CSWeb capability. If alerting is a deliverable, it must be built **downstream** of the relational break-out (querying the broken-out tables on a schedule and pushing notifications) — not via CSWeb itself.

---

## 8.6 CSWeb roles model

CSWeb has **exactly two permission axes** (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSWeb Users Guide|Source - CSWeb Users Guide]]):

1. **Dashboard permissions** — five dashboards (data, report, apps, users, roles), each gated by a single binary checkbox.
2. **Dictionary permissions** — per-dictionary upload/download flag (binary), applies across CSEntry, Batch, and Data Manager.

**No row-level filtering. No regional permission. No time-window permission. No alert-config permission.** Either you have the dashboard checkbox or you don't; either you can up/down a dictionary or you can't. This is coarser than most projects' org charts imply.

### 8.6.1 Built-in roles

| Role | Dashboards | Dictionaries | CSWeb login |
|---|---|---|---|
| **Administrator** | All 5 | All up/down | Yes |
| **Standard User** | None | All up/down (via CSEntry, Batch, Data Manager) | **No** — but can deploy applications via Deploy Application tool. **Default fallback** when a custom role is deleted. |

All roles can download applications using CSEntry. **(Khurshid 2022-05-05)**: *"All roles are able to download applications using CSEntry."*

### 8.6.2 Custom roles

Admin-defined. Combine any subset of dashboard checkboxes + per-dictionary checkboxes. Constraints:

- At least one permission (dashboard or dictionary) must be assigned.
- The role's name **cannot** be edited after creation — to rename, delete and re-add (and reassign all users currently bound to it; this is why the role taxonomy below is named once and held).

### 8.6.3 UHC role matrix

Working from the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSWeb Users Guide|three permission shapes]] CSWeb actually supports, here's the proposed UHC matrix:

| Role | Dashboards | Dictionary perms | Who | Count |
|---|---|---|---|---|
| `ASPSI_ADMIN` | data, report, apps, users, roles | F1/F3/F4 up+down | Carl + Project Coordinator | 2 |
| `ASPSI_OPS` | data, report | F1/F3/F4 down only | Field Manager, Data Manager, Survey Manager | 3 |
| `STL_REGION` | data, report | F1/F3/F4 down only | Supervisory Team Leaders (one role, used by all STLs across regions) | ~6 |
| `ENUMERATOR` | (Standard User built-in) | F1/F3/F4 up only via CSEntry | Enumerators in the field | ~50 |
| `DOH_VIEWER` | report | none (no dictionary access) | DOH client interim review | 1–3 |

**Notes**:

- **One STL role for all regions** rather than `STL_REGION_IV-A`, `STL_REGION_V`, etc. — because CSWeb cannot enforce regional row-level filtering. Naming each STL by region creates the false impression of region-bound access. Operationally, STLs see **all** data; we rely on operational discipline + DOH norms, not permission enforcement, to keep them focused on their region. Document this gap explicitly in the Field Manual.
- **DOH_VIEWER** has report-only access (no Data tab). They see the Sync Report and Map Report — enough for "are we hitting target counts?" — but not individual case content. If DOH wants case-level review, escalate to `data` permission (and document the data-handling protocol in the DPA).
- **ENUMERATOR** uses the built-in `Standard User` role: no dashboard, sync up only via CSEntry. The username + password is the field credential; the user record optionally encodes allowed device IDs (see [[#8.11 Enumerator login bound to tablet device ID]]).

### 8.6.4 Creating the custom roles

**(Khurshid 2022-05-05)** walks the UI: **Roles tab → Add Role → name → check the appropriate dashboard + dictionary boxes → Add**. To later expand a role's permissions (he adds **Application and Data**, then **Download/Sense Data** in his demo), use the pencil icon to edit.

**Test before issuing creds**: create one user under the new role, log in as that user, confirm they see exactly the tabs they should and can sync exactly the dictionaries they should. *"When 'access denied' error appears during a deploy or data-pull, that's a role-permission gap, not a network issue."* — **(Khurshid 2022-05-05)**.

---

## 8.7 Adding users via CSV import

**(Khurshid 2022-05-05)** + (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSWeb Users Guide|Source - CSWeb Users Guide]]) — the Users tab supports bulk CSV import. For 50+ enumerators across 6 clusters, manual single-user entry is wrong; do the CSV.

### 8.7.1 CSV format

Columns in this exact order:

```
username, first name, last name, user role, password, email, phone
```

- Header row supported via a checkbox in the import UI.
- `user role` must match an existing role name **exactly** (case-sensitive: `Administrator` not `administrator`; `STL_REGION` not `stl_region`).
- Password must be ≥8 characters.
- First name and last name accept letters only — names with hyphens, apostrophes, or accented characters need normalization (Filipino names with `ñ` may need transliteration to `n` for the import to accept).
- Email and phone are optional; leave blank columns rather than omit them.

### 8.7.2 Sample CSV — 50 enumerators across 6 clusters

```csv
username,first name,last name,user role,password,email,phone
ENUM01-01,Maria,Santos,ENUMERATOR,Cluster1Pass01!,maria.santos@aspsi.example,
ENUM01-02,Juan,Cruz,ENUMERATOR,Cluster1Pass02!,juan.cruz@aspsi.example,
ENUM01-03,Anna,Reyes,ENUMERATOR,Cluster1Pass03!,,
ENUM01-04,Pedro,Garcia,ENUMERATOR,Cluster1Pass04!,,
ENUM01-05,Liza,Aquino,ENUMERATOR,Cluster1Pass05!,,
ENUM01-06,Mark,Tan,ENUMERATOR,Cluster1Pass06!,,
ENUM01-07,Grace,Lim,ENUMERATOR,Cluster1Pass07!,,
ENUM01-08,Rico,Mendoza,ENUMERATOR,Cluster1Pass08!,,
ENUM02-01,Bea,Domingo,ENUMERATOR,Cluster2Pass01!,,
ENUM02-02,Karl,Bautista,ENUMERATOR,Cluster2Pass02!,,
ENUM02-03,Joy,Villanueva,ENUMERATOR,Cluster2Pass03!,,
ENUM02-04,Miguel,Reyes,ENUMERATOR,Cluster2Pass04!,,
ENUM02-05,Cris,Pascual,ENUMERATOR,Cluster2Pass05!,,
ENUM02-06,Tina,Soriano,ENUMERATOR,Cluster2Pass06!,,
ENUM02-07,Vince,Hernandez,ENUMERATOR,Cluster2Pass07!,,
ENUM02-08,Leah,Ramos,ENUMERATOR,Cluster2Pass08!,,
ENUM03-01,Paolo,Gomez,ENUMERATOR,Cluster3Pass01!,,
ENUM03-02,Riza,Mercado,ENUMERATOR,Cluster3Pass02!,,
ENUM03-03,Jay,Castro,ENUMERATOR,Cluster3Pass03!,,
ENUM03-04,Mia,Diaz,ENUMERATOR,Cluster3Pass04!,,
ENUM03-05,Niko,Salvador,ENUMERATOR,Cluster3Pass05!,,
ENUM03-06,Cara,Yap,ENUMERATOR,Cluster3Pass06!,,
ENUM03-07,Ben,Roxas,ENUMERATOR,Cluster3Pass07!,,
ENUM03-08,Eli,Morales,ENUMERATOR,Cluster3Pass08!,,
ENUM04-01,Sam,Aguilar,ENUMERATOR,Cluster4Pass01!,,
ENUM04-02,Iris,Cortez,ENUMERATOR,Cluster4Pass02!,,
ENUM04-03,Tom,Navarro,ENUMERATOR,Cluster4Pass03!,,
ENUM04-04,Rina,Buenaventura,ENUMERATOR,Cluster4Pass04!,,
ENUM04-05,Nina,De Leon,ENUMERATOR,Cluster4Pass05!,,
ENUM04-06,Lex,Rivera,ENUMERATOR,Cluster4Pass06!,,
ENUM04-07,Ines,Manalo,ENUMERATOR,Cluster4Pass07!,,
ENUM04-08,Ari,Velasquez,ENUMERATOR,Cluster4Pass08!,,
ENUM05-01,Owen,Tolentino,ENUMERATOR,Cluster5Pass01!,,
ENUM05-02,Faye,Macapagal,ENUMERATOR,Cluster5Pass02!,,
ENUM05-03,Rafa,Ocampo,ENUMERATOR,Cluster5Pass03!,,
ENUM05-04,Zara,Ibarra,ENUMERATOR,Cluster5Pass04!,,
ENUM05-05,Drew,Marasigan,ENUMERATOR,Cluster5Pass05!,,
ENUM05-06,Dom,Pineda,ENUMERATOR,Cluster5Pass06!,,
ENUM05-07,Vera,Lacuesta,ENUMERATOR,Cluster5Pass07!,,
ENUM05-08,Jules,Sevilla,ENUMERATOR,Cluster5Pass08!,,
ENUM06-01,Gio,Espinosa,ENUMERATOR,Cluster6Pass01!,,
ENUM06-02,Trina,Almonte,ENUMERATOR,Cluster6Pass02!,,
ENUM06-03,Bryan,Cabrera,ENUMERATOR,Cluster6Pass03!,,
ENUM06-04,Stella,Guerrero,ENUMERATOR,Cluster6Pass04!,,
ENUM06-05,Migs,Lazaro,ENUMERATOR,Cluster6Pass05!,,
ENUM06-06,Pat,Robles,ENUMERATOR,Cluster6Pass06!,,
ENUM06-07,Nadia,Suarez,ENUMERATOR,Cluster6Pass07!,,
ENUM06-08,Leo,Trinidad,ENUMERATOR,Cluster6Pass08!,,
STL01-01,Rena,Magbanua,STL_REGION,Stl1Pass01!,rena.magbanua@aspsi.example,
STL02-01,Pio,Sandoval,STL_REGION,Stl2Pass01!,pio.sandoval@aspsi.example,
STL03-01,Cleo,Maquiling,STL_REGION,Stl3Pass01!,cleo.maquiling@aspsi.example,
STL04-01,Ino,Fajardo,STL_REGION,Stl4Pass01!,ino.fajardo@aspsi.example,
STL05-01,Bea,Apolinario,STL_REGION,Stl5Pass01!,bea.apolinario@aspsi.example,
STL06-01,Raf,Quirino,STL_REGION,Stl6Pass01!,raf.quirino@aspsi.example,
```

Replace the placeholder names + passwords with the **real Field Manager-finalized roster** before import. Generate strong unique passwords per user (a password manager's bulk-generate feature, or `openssl rand -base64 12` per user).

### 8.7.3 Import workflow

1. **Users tab → Import Users** (or "Add via CSV" — the exact label varies by CSWeb build).
2. Browse to the CSV, check **CSV file has a header row**, click **Import**.
3. CSWeb shows a per-row result: success / error. Errors usually mean: role name mismatch, password too short, name with non-letter characters.
4. Fix the CSV, re-import only the failed rows.

### 8.7.4 Username convention

The username pattern `<role><cluster>-<seq>` (e.g., `STL01-01`, `ENUM01-01`, `ENUM01-02`) encodes role + cluster + sequence in the username itself. Operational benefits:

- Filtering Sync Report by `ENUM01-*` shows all enumerators in cluster 1.
- Lost tablet recovery: "tablet was logged in as ENUM03-04" tells you the cluster, the sequence, and the role at a glance.
- Audit: every case in Data tab has an `interviewer_id` field; pattern-matching the value is human-parseable.

This convention also surfaces in [[#8.12 Supervisor / enumerator team-ID convention]].

### 8.7.5 Password lifecycle

- **Initial passwords** generated per the CSV bulk-generate workflow above.
- **Mandatory rotation at first login** — CSWeb enforces this if the role has the `force-password-change` flag (Standard User does not by default; consider enabling project-wide).
- **Mid-fieldwork rotation** if a tablet is lost or an enumerator's credential is suspected compromised: rotate that one user's password via the Users tab, communicate the new password via a side channel (not over the same Slack channel where the tablet was reported lost).
- **End-of-fieldwork**: disable enumerator users (don't delete — disable preserves the audit trail; deletion would force their `Standard User` role to fall back, breaking referential integrity).

---

## 8.8 Defining the dictionary on the server

For each F-series instrument, CSWeb needs to know about the dictionary so it can store incoming cases and (optionally) break out into a relational target.

### 8.8.1 Upload the .pen via Apps tab

1. **Apps tab → Add Application** (or **Upload**).
2. Browse to the local `.pen` (e.g., `F1.pen`).
3. Upload.
4. CSWeb extracts the embedded `.dcf` and creates the backing tables — one table per dictionary record level, plus the case-blob table.
5. Confirm via **Data tab → dictionary appears in the tree → empty (zero cases) initially**.

Repeat for F3 and F4 once their `.pen`s are built (after June 12).

### 8.8.2 What the dictionary registration actually creates

Behind the scenes, CSWeb's MySQL backing DB gets:

- **case-blob table** — one row per case, with the entire CSPro case serialized in a blob column. This is the canonical store; everything else is derivative.
- **operator log table** — sync events per case (who synced when, from which device).
- **dictionary metadata** — copy of the `.dcf` so CSWeb can reconstruct field names if the entry app is later updated.

If you want a queryable relational view of the data — for BI, custom dashboards, ad-hoc SQL — that's the **relational break-out** in [[#8.8.4 Optional: relational break-out]] below.

### 8.8.3 Verify round-trip with one mock case

Don't wait for tablet provisioning to verify the dictionary registration works. From CSEntry Windows on Carl's dev machine:

1. Open F1 in CSEntry Windows.
2. Capture one mock case.
3. **File → Synchronize → CSWeb** → enter the production sync URL + an admin's CSWeb credentials.
4. Expect "Sync OK" with 1 case sent.
5. In CSWeb → Data tab → F1 dictionary → expand → see the mock case.
6. View Case → confirm the field values match what was entered.
7. Delete the mock case from CSWeb (Data tab → case row → delete) so it doesn't pollute real-fieldwork data.

If this round-trip works, the server is sound. If it doesn't, server-side troubleshooting before you put anything on a tablet — see [[#8.21 Phase 8 exit criteria]] triage.

### 8.8.4 Optional: relational break-out

If the project wants SQL access to the data (DOH BI dashboards, mid-fieldwork progress reports, joined cross-instrument analysis), configure the relational break-out (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSWeb Users Guide|Source - CSWeb Users Guide]]):

1. **phpMyAdmin → New** → create target DB `csweb_uhc_y2_relational` (must differ from `csweb_uhc_y2`).
2. **CSWeb → Settings → Add Configuration**:
   - Source Data: F1 (or F3/F4)
   - Database name: `csweb_uhc_y2_relational`
   - Hostname: `localhost`
   - Database username: `csweb_user` (same user; needs GRANT on the new DB)
   - Database password: (same)
   - Map Report: enable per-dictionary if the dictionary has lat/long
3. Grant the user on the new DB:

```sql
GRANT ALL PRIVILEGES ON csweb_uhc_y2_relational.* TO 'csweb_user'@'localhost';
FLUSH PRIVILEGES;
```

4. Run the break-out:

```bash
cd C:\wamp64\www\csweb
php bin\console csweb:process-cases
```

**(Khurshid 2022-04-30)**: *"please make sure that you are running the command from the cswebtest folder"* — adapted, the production version: from the `csweb` folder. PHP must be on PATH (see [[#8.3.6 Setup gotchas]]).

5. **Each invocation runs for 5 minutes then exits** (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSWeb Users Guide|Source - CSWeb Users Guide]]). To process continuously, schedule via Windows Task Scheduler (every 5 min, run-when-not-already-running). Manual runs may need multiple iterations to drain the queue.

6. Verify: refresh CSWeb's Data tab — processed case count = dictionary case count. Browse the relational DB in phpMyAdmin — see one table per record level, plus joins by case key.

### 8.8.5 F2 PWA scope — explicitly out

F2 (Healthcare Worker) is the self-administered PWA track. **It does not sync through this CSWeb.** F2's data lands in the Apps Script Web App backend → Google Sheet target. Mention it explicitly in the Field Manual so ops doesn't go looking for F2 data in the CSWeb Data tab. F2 is monitored via its own staging/production CDN dashboards and the GitHub Actions `#f2-pwa-uat` digest.

---

## 8.9 Sync architecture

The workflow template offers three sync options for the CAPI track. UHC chooses **CSWeb** as the primary; we document the fallbacks because they will matter when CSWeb has a bad day.

### 8.9.1 Three options compared

| Option | How it works | Pros | Cons | UHC role |
|---|---|---|---|---|
| **CSWeb (RECOMMENDED)** | Tablet calls server API; server stores in MySQL; dashboard for monitoring | Real-time monitoring; central server; granular role-based access; relational break-out for BI | Single point of failure; requires server uptime; bandwidth-dependent | **Primary** |
| **Dropbox** | Tablet uploads `.csdb` to Dropbox folder; ops downloads | Trivially simple; cloud SLA; no server to maintain | No dashboard; no per-case visibility; manual ingest into CSPro | **Fallback** when CSWeb >24h unreachable |
| **FTP / Bluetooth** | Tablet pushes to FTP server / Bluetooth-pairs to ops laptop | Works on local network without internet | Field-impractical at 50-tablet scale; FTP is plaintext unless FTPS configured | **Local-only fallback** for emergency same-room data pulls |

For UHC, the policy is clear: **CSWeb is the only sync path during normal operations**. Fallbacks exist for documented contingencies, not as parallel options enumerators choose between.

### 8.9.2 Decision matrix — when to fall back

Treat this as **operational SOP**, not as something each enumerator decides:

| Trigger | Action | Owner | Recovery |
|---|---|---|---|
| CSWeb 5xx errors for >2 hours | STL pings ops; ops investigates | STL → Project Coordinator | Resume normal sync after fix |
| CSWeb unreachable for >24 hours | Activate Dropbox fallback: each tablet exports `.csdb` from CSEntry Settings → Data Export → upload to per-cluster Dropbox folder | Project Coordinator announces; STLs walk enumerators through | Resume CSWeb when available; ops merges the Dropbox `.csdb`s into CSWeb via Data Manager |
| Server box hard-fails (disk, hardware) | Failover to backup server (snapshot if VPS; cold spare if on-prem) | Carl + ASPSI ops | Rebuild from latest backup; tablets re-sync since their last successful sync |
| Network outage local to one enumerator (cellular tower down) | No action — sync resumes when connectivity returns; data persists locally on tablet's `.csdb` | Enumerator continues working offline | Auto on next successful `syncconnect` |

The fallbacks are documented because **any of them not pre-decided becomes a 4-hour scramble during fieldwork**.

### 8.9.3 Sync frequency policy

Per Protocol V2: **"CSWeb daily 10 PM upload mandate"**. Translation:

- Every enumerator must complete a sync **at least once per fieldwork day**, by 10 PM local time.
- Cases captured offline during the day persist in the tablet's `.csdb` until sync completes.
- The 10 PM deadline is **end-of-day reconciliation** — STLs check the Sync Report at 10:30 PM to confirm their team's case counts match the day's planned interviews.

Enforced two ways:

1. **In-app reminder** via `synctime()` — see [[#8.17 synctime() for upload tracking]].
2. **Operational discipline** via STL — STLs WhatsApp/Slack their cluster nightly: "All synced? Reply with case count."

### 8.9.4 What "sync" actually moves

CSWeb's smart-sync semantics: only changed cases are uploaded. Specifically:

- **New cases since last sync** — added.
- **Modified cases since last sync** — updated.
- **Cases unchanged since last sync** — not re-uploaded (saves bandwidth).

This is `synchronize_data(F1_DATA, sync_direction_send)` — direction `send` (a.k.a. `put` in older syntax). For two-way sync (downloads from server, e.g., supervisor pulls cluster's data for review), use `sync_direction_both`. For UHC, enumerators use `send` (push only); supervisors use `both` for review workflows.

---

## 8.10 Sync session implementation in the entry app

The entry app needs PROC code to actually invoke sync. This is the production-grade pattern, drawn from **(Khurshid 2022-04-30)** *Deploy an Application and Synchronize the Data on the CSWeb Server* and adapted for ASPSI's user-config-driven URL design.

### 8.10.1 Three primitives

**(Khurshid 2022-04-30)**:

```cspro
syncconnect(<type>, <url>)        { open sync session; returns 0 on success }
synchronize_data(<dict>, <dir>)   { upload/download case data; returns 0 on success }
syncdisconnect()                  { close sync session }
```

Wrap every sync action in `syncconnect` / `syncdisconnect`. *"The first argument must be the keyword `csweb`. The second argument is the CSWeb URL."* — **(Khurshid 2022-04-30)**.

### 8.10.2 Bind the sync URL via config attribute

**(Khurshid 2022-04-30)** — declare the URL via the `config` statement, driven by a User-and-Configuration-Settings attribute. This makes the URL **changeable without rebuilding the .pen**.

In Designer:

1. **View menu → User and Configuration Settings**.
2. **Add attribute** → name `sync_url` → value `https://csweb.aspsi.example.com/csweb/api`.
3. Save.

In `PROC GLOBAL`:

```cspro
PROC GLOBAL

config sync_url csweb_url;
{ The 'config' statement declares a string variable populated from the
  named attribute when the application begins. The variable name and
  attribute name MUST match. }
```

Now `csweb_url` is usable everywhere. Changing the deploy URL is a one-line edit in User Settings — no Designer rebuild, no re-publish, no re-deploy.

**Critical Khurshid rule**: *"Once embedded in the PFF/PEN, the attribute name is fixed — pick something that makes sense to whoever will edit settings later."* For UHC, `sync_url` is the attribute name we standardize on.

### 8.10.3 Bind data file to dictionary with setfile()

**(Khurshid 2022-04-30)**: *"In the synchronize data function we are using two arguments — `put` and the dictionary name. With `put`, upload to the server any cases that were added or modified in the local data file since the last synchronized."* The dictionary doesn't know where its data lives on disk — `setfile()` tells it.

```cspro
setfile(F1_DATA, pathconcat(pathname(path_type_csentry_application), "F1.csdb"));
```

For ASPSI we use `pathname(path_type_csentry_application)` instead of relative `..\` paths — relative paths are fragile across the dev machine ↔ tablet path-structure mismatch.

### 8.10.4 Production-grade sync function

Putting it all together — paste-ready `syncToServer()` for F1's `.apc`. Adapt the dictionary name + filename for F3/F4.

```cspro
PROC GLOBAL

config sync_url csweb_url;
config user_id  USER_ID;
config user_pwd USER_PWD;

function syncToServer()
   numeric rc;

   { Verify URL configured }
   if length(strip(csweb_url)) = 0 then
      errmsg("Sync URL is not configured. Contact your supervisor.");
      exit;
   endif;

   { Bind data file to dictionary }
   setfile(F1_DATA, pathconcat(pathname(path_type_csentry_application),
                                "F1.csdb"));

   { Open session }
   rc = syncconnect("csweb", csweb_url, USER_ID, USER_PWD);
   if rc <> 0 then
      errmsg("Sync failed: cannot connect to %s. Check internet and try again.",
             csweb_url);
      exit;
   endif;

   { Push data — direction send (upload only) }
   rc = synchronize_data(F1_DATA, sync_direction_send);
   if rc <> 0 then
      errmsg("Data sync failed (rc=%d). Tablet retains data; retry later.", rc);
      syncdisconnect();
      exit;
   endif;

   { Push photos / supplementary files (per facility) }
   { This is in addition to the data sync above. }
   { synchronize_file(put, ...); — see Khurshid 2022-05-05 }

   { Close session }
   syncdisconnect();

   warning("Sync complete. %d cases uploaded since last sync.",
           sync_uploaded_count);
end;
```

### 8.10.5 Wire into the menu app

The `syncToServer()` function lives in `PROC GLOBAL` of the menu app (or whatever shell app ties the F1/F3/F4 entry apps together). Bind it to a menu item: "Sync to server", invoked manually by the enumerator end-of-day.

**Why manual, not auto-on-exit**: enumerators may have unstable connections; an auto-on-exit attempt that fails silently leaves them thinking they synced. Manual-with-feedback (`warning("Sync complete")` or `errmsg("Sync failed")`) trains them to verify.

### 8.10.6 What success looks like

End-to-end flow on a single tablet, end-of-day:

1. Enumerator finishes last interview of the day.
2. Returns to menu app.
3. Taps **Sync to server**.
4. App calls `syncconnect` → `synchronize_data` → `syncdisconnect`.
5. App displays `warning("Sync complete. 12 cases uploaded.")`.
6. STL checks Sync Report on CSWeb dashboard at 10:30 PM → sees the 12 cases under that enumerator's username.
7. STL DMs the enumerator: "Confirmed 12, thanks."

If step 5 shows an error or step 6 doesn't match, that's a P1 to triage immediately.

---

## 8.11 Enumerator login bound to tablet device ID

Per **(Khurshid 2022-03-31)** patterns (referenced from the Khurshid Login app technique cards): tablets expose a unique device ID via `getdeviceid()`. Bind enumerator credentials to specific device IDs to prevent credential reuse on rogue tablets.

### 8.11.1 Why bind credentials to devices

Threat model:

- An enumerator's credentials are written on the tablet sticker (or memorized).
- Tablet is lost / stolen / shared.
- Without device binding: anyone with the credentials can sync from any device with internet — possibly impersonating the enumerator with fabricated cases.
- With device binding: even with the credentials, the rogue device's `getdeviceid()` doesn't match — login fails.

This is **belt-and-suspenders** alongside the CSWeb username/password — it adds a hardware-bound factor without complicating the enumerator's UX.

### 8.11.2 Pattern

In the entry app's login PROC (or a shared `validateLogin()` function called from menu preproc):

```cspro
PROC GLOBAL

alpha (50) ALLOWED_DEVICE_IDS;   { semicolon-separated; loaded from external dict
                                    or User Settings — one per cluster }
alpha (50) THIS_DEVICE_ID;

function validateLoginDevice()
   THIS_DEVICE_ID = getdeviceid();

   { Lookup ALLOWED_DEVICE_IDS for the current USER_ID — could be a
     small external dictionary keyed by username. Below is the simplest
     form: a hardcoded check (replace with dict lookup in production). }
   if pos(THIS_DEVICE_ID, ALLOWED_DEVICE_IDS) = 0 then
      errmsg("This device (%s) is not authorized for user %s. "
             "Contact your supervisor.", THIS_DEVICE_ID, USER_ID);
      stop(1);
   endif;
end;
```

### 8.11.3 Provisioning workflow

Each enumerator's CSWeb user record has an `allowed_device_ids` field — typically a comma-or-semicolon-separated list of 1–2 device IDs (one primary + one backup). When provisioning:

1. Tablet bring-up → record `getdeviceid()` value (visible in CSEntry's Settings → About, or via a one-shot diagnostic PFF).
2. Update the enumerator's user record (or the parallel external dict the entry app reads) with the device ID.
3. Re-deploy the external dict + force tablets to re-sync.

For UHC, the **simplest viable version** is to skip per-user device binding for the pilot and add it for main fieldwork only if the threat model warrants. Note in [[#8.22 Open decisions]].

### 8.11.4 Backup device IDs

Enumerator's primary tablet breaks; STL issues a spare. The spare's device ID isn't in the user record yet. Workflow:

1. STL records the spare's device ID.
2. STL has either CSWeb access (if STL_REGION role permits user editing — it does not by default) or pings ops.
3. Ops updates the user record.
4. Spare is now usable.

Define this workflow in advance to avoid 10 PM panic when a tablet swap is needed.

---

## 8.12 Supervisor / enumerator team-ID convention

**(Khurshid 2022-03-31)**: username pattern `<role><cluster>-<seq>` encodes role and cluster in the credential. For UHC:

| Role | Pattern | Example | Notes |
|---|---|---|---|
| Enumerator | `ENUM<cluster>-<seq>` | `ENUM01-01` | Cluster 01–06; seq 01–08 (8 enums per cluster) |
| Supervisor (STL) | `STL<cluster>-<seq>` | `STL01-01` | One STL per cluster typical; seq for backups |
| ASPSI ops | `OPS-<initials>` | `OPS-CR` | Carl Reyes |
| ASPSI admin | `ADMIN-<initials>` | `ADMIN-CR` | Higher privilege than ops |
| DOH viewer | `DOH-<initials>` | `DOH-JS` | Read-only client account |

**Operational benefits**:

- **Filter Sync Report by `ENUM01-*`** → see all of cluster 1's case counts in one row.
- **Pattern-match logs**: `grep -E "ENUM(01|02|03)" sync.log` extracts clusters 1–3.
- **Audit trail**: `interviewer_id` field in every case is human-parseable; "ENUM03-04" is decodable without a lookup table.
- **Onboarding new field staff**: "you're cluster 4, your seq is 09 because we already have 8 enumerators — your username is `ENUM04-09`" — no need to consult a master spreadsheet.

**Match the convention against the Field Manager's roster spreadsheet** when it's finalized. Misalignment between CSWeb usernames and the roster is a top-3 source of "missing case" confusion.

---

## 8.13 PFF generation

A **PFF (Program Information File)** is the configuration that tells CSEntry which app to run and how. For sync apps specifically, the PFF carries the dictionary, data-file path, sync URL, and sync direction.

**(Khurshid 2022-05-12)** *Use the Batch File to Download the Data from the CSWeb Server* lays out three options for generating sync PFFs.

### 8.13.1 Option 1 — Hand-write in Notepad

Useful when you need a sync that isn't tied to any data-entry app — e.g., an **unattended download** from a back-office workstation that pulls data nightly for analysis.

**(Khurshid 2022-05-12)**: *"PFF file is not case sensitive so you can use any combination of upper and lower case text."* Three required blocks:

```ini
[Run Information]
Version=CSPro 7.7.1
ApplicationType=synchronize

[ExternalFiles]
F1=C:\path\to\F1.csdb

[Parameters]
SyncType=csweb
SyncDirection=get
SyncURL=https://csweb.aspsi.example.com/csweb/api
Silent=yes
```

Save as `<name>.pff`. Double-click to run, or invoke via batch file.

**Critical gotcha** (Khurshid): the External Files block name must equal the **dictionary** name (`F1`), not the data file name. *"A copy of dictionary must exist on the server"* — i.e., the dictionary must already be registered (per [[#8.8 Defining the dictionary on the server]]) before scheduled downloads work.

### 8.13.2 Option 2 — Generate via PFF Editor (GUI)

Same outcome as hand-writing, but no risk of typo'd block names. Use for quick one-offs.

**(Khurshid 2022-05-12)**:

1. Save an empty file with `.pff` extension → right-click → **Edit** → opens in PFF Editor.
2. Set:
   - **Version** → 7.7
   - **ApplicationType** → Synchronize
   - **SyncType** → csweb
   - **SyncDirection** → get (or `put` for upload, `both` for two-way)
   - **SyncURL** → production URL
   - **Silent** → yes
3. **Add → External File for Data Dictionary** → double-click the dictionary file (`.dcf`) → PFF Editor reads the dictionary name (`F1`), enters as parameter.
4. **Data file** → set type **CSPro DB** + folder icon → name the output file (e.g., `F1_export`).
5. Save.

**Critical gotcha**: data type **must** be CSPro DB (not text); leaving it default produces an unusable file.

### 8.13.3 Option 3 — Pull pre-built PFF from CSWeb dashboard (RECOMMENDED for UHC)

Fastest path; the server already knows its URL, dictionary, and sync params. Use this for the standard sync PFFs that ship with each tablet.

**(Khurshid 2022-05-12)**:

1. Login to CSWeb → **Data tab**.
2. Click the **download icon** next to the dictionary (e.g., F1).
3. Save the PFF locally (e.g., `F1_sync.pff`).
4. Right-click → **Edit** → opens in PFF Editor.
5. Set **Data file** path to wherever the tablet expects the data (e.g., `F1.csdb` in the application folder).
6. Save.

**For UHC, standardize on Option 3 for all three F-series instruments.** Each tablet ships with `F1_sync.pff`, `F3_sync.pff`, `F4_sync.pff` — pre-built by CSWeb, with the production sync URL already correct.

### 8.13.4 Sample sync PFF for F1 (paste-ready)

After Option 3 + setting the data-file path, the PFF looks like this:

```ini
[Run Information]
Version=CSPro 7.7.1
ApplicationType=synchronize
Description=F1 sync — Facility Head Survey

[ExternalFiles]
F1=.\F1.csdb

[Parameters]
SyncType=csweb
SyncDirection=both
SyncURL=https://csweb.aspsi.example.com/csweb/api
Silent=no
SyncUserID=
SyncUserPwd=

[Other Settings]
Logging=yes
LogFile=.\sync.log
```

Notes:
- **`SyncDirection=both`** for the field-tablet PFF — uploads new cases AND downloads any pre-assigned sample updates pushed from the server.
- **`Silent=no`** for tablets — show progress to the enumerator. (Use `yes` for unattended back-office PFFs.)
- **`SyncUserID=` empty** — CSEntry prompts the enumerator on first sync; their credentials aren't baked into the PFF (avoids credential leakage if a tablet is shared/lost).
- **`Logging=yes`** + log path — local sync log on the tablet. STLs can pull the log file via Files-tab `synchronize_file(put, ...)` if troubleshooting.

For F3 and F4, replace the dictionary name and filename. Three PFFs total ship per tablet.

### 8.13.5 Wrap PFF execution in a Windows batch file (for unattended download)

For ops/analysts who want nightly auto-pulls of data to their workstation, **(Khurshid 2022-05-12)** provides the batch-file pattern:

```bat
cd ..\..
c:
cd c:\wamp64\www\csweb
F1_download.pff
```

**Critical gotcha** (Khurshid): drive letter (`c:`) **must be on its own line before** `cd` to absolute path; otherwise Windows just changes directory on whichever drive is current.

Schedule via **Windows Task Scheduler**:

1. Task Scheduler → Create Task.
2. Name: `download_F1_data`.
3. Trigger → Daily → 1:30 AM.
4. Action → New → Browse → `F1_download.bat`.

Repeat for F3 and F4 if the analyst pipeline wants them too. Stagger by ~1 minute to avoid concurrent run conflicts.

### 8.13.6 PFF + entry app packaging

**(Khurshid 2022-04-24)** — once the entry app is built, packaging it for tablets is a two-step:

1. **File → Publish Entry Application** (or **F7**) → choose name → Save → produces `.pen`.
2. **Tools → Deploy Application** → enter package name + description → drag-drop or **Add Folder** for application folders (logic, login, menu, listing) → **Add File** for individual files (data files, images, HTML templates).

**Critical packaging gotcha** (Khurshid): **Add Folder** bundles only `.ent`, `.pff`, and similar app-recognized files. **External dictionaries' data files (e.g., `103_EXT_DATA/*.dat`), HTML dialog folders, and reference data must be added with Add File**, or they're missing on the tablet.

For UHC, the per-tablet bundle includes:

- `F1.pen` (published F1 entry app)
- `F3.pen` (after June 12)
- `F4.pen` (after June 12)
- `F1_sync.pff`, `F3_sync.pff`, `F4_sync.pff` (per [[#8.13.3 Option 3]])
- `MENU.pen` (the menu shell that ties everything together — invokes `syncToServer()`)
- `LOGIN.pen` (login app — validates user credentials + device ID)
- `<sample-file>.dat` (F4's pre-assigned household sample, per Phase 6.15)
- `109_html_dialog/` (custom HTML dialog directory — see **(Khurshid 2022-04-24)**)
- Reference data (locality codes, facility codes — read by entry apps as external dicts)

### 8.13.7 Per-application HTML dialog directory

If the entry apps use customized HTML dialogs (wider message boxes, branded UX), each app's PFF needs its own **HTML Dialog Directory** entry — **(Khurshid 2022-04-24)**: *"This HTML dialog directory is associated with menu application only. If you want to associate with the login application, then you need to add HTML dialog directory in the login PFF file."*

In PFF Editor:

1. **Add → HTML Dialog Directory** → folder icon → select the `109_html_dialog` folder → Select Folder.
2. Save and close.
3. Re-publish the `.pen` and re-deploy.

**Easy-to-forget gotcha**: each chained app's PFF needs its own HTML dialog directory entry. The entry in the menu PFF doesn't propagate to the login PFF.

---

## 8.14 PFF + entry application packaging summary

Phase 8 packaging summary, for the team's reference:

| Artifact | Built by | Lives on tablet at | Purpose |
|---|---|---|---|
| `F1.pen` / `F3.pen` / `F4.pen` | Designer → File → Publish Entry Application | `/Internal Storage/CSPro/<F-series>/<F>.pen` | Entry app binary |
| `F1_sync.pff` / etc. | CSWeb dashboard download icon → PFF Editor | `/Internal Storage/CSPro/<F-series>/<F>_sync.pff` | Manual-trigger sync (called from menu) |
| `MENU.pen` | Designer → Publish | `/Internal Storage/CSPro/Menu/MENU.pen` | Menu shell that dispatches to F1/F3/F4 entry, sync, backup, restore |
| `LOGIN.pen` | Designer → Publish | `/Internal Storage/CSPro/Login/LOGIN.pen` | Validate user + device |
| `109_html_dialog/` | Project resource — copy from `/wiki/concepts/HTML Dialogs` | per-app folder, referenced by each PFF | Custom dialog styling |
| External dicts (`*.dat`) | Reference data ingestion | per-app `103_EXT_DATA/` | Locality, facility, sample data |

**One PFF per role** if needed (interviewer / supervisor) — the supervisor PFF launches a different menu app with extra options (review cases, edit cases, mark complete). For UHC, a single PFF per F-series suffices in the pilot; supervisor-vs-enumerator dispatch is via the [[#8.6.3 UHC role matrix|role matrix]] + login-time index dispatch (per **(Khurshid 2022-10-12)** `cell_option_dummy` pattern).

---

## 8.15 Tablet provisioning SOP

The bring-up checklist for each tablet — **the script the bring-up team follows on every device**.

### 8.15.1 SOP — step by step

```
Tablet Provisioning Checklist — UHC Y2 CAPI
============================================
Tablet ID:  __________
Enumerator: __________
Cluster:    __________
Supervisor: __________
Date:       __________
Provisioned by: __________

[ ]  1. RECEIVE & INVENTORY
       Note tablet serial number and model. Register in
       tablet inventory spreadsheet (link: ASPSI Drive > UHC Y2
       > Tablet Inventory). Mark status: "received, awaiting
       provision".

[ ]  2. INSTALL CSEntry FROM GOOGLE PLAY
       Open Play Store → search "CSEntry" → install version 7.7+
       (version must match CSWeb). If Play Store unavailable,
       sideload the latest APK from csprousers.org via USB.
       Confirm CSEntry opens.

[ ]  3. CONFIGURE CSEntry STORAGE PATHS
       Open CSEntry → Settings → set path_type_csentry_external
       to the SD card if available. Confirms SD card was
       inserted BEFORE first launch (Khurshid 2022-10-12 SD-card-
       before-launch rule). If SD card was inserted after first
       launch, force-stop CSEntry, then re-open — folder will be
       created.

[ ]  4. DEPLOY ENTRY APPS
       Copy via USB to /Internal Storage/CSPro/:
         - F1/  (contains F1.pen, F1_sync.pff)
         - F3/  (contains F3.pen, F3_sync.pff)
         - F4/  (contains F4.pen, F4_sync.pff)
         - Menu/ (contains MENU.pen)
         - Login/ (contains LOGIN.pen, 109_html_dialog/)
         - Reference/ (locality, facility external dicts)
       Verify file sizes match the deployment manifest.

[ ]  5. CONFIGURE SYNC CREDENTIALS & URL
       Launch MENU.pen → first-run prompts for username (e.g.,
       ENUM01-03), password, sync URL.
       URL: https://csweb.aspsi.example.com/csweb/api
       Sync URL is also stored in User Settings (attribute
       'sync_url') — confirm by viewing Settings.

[ ]  6. SMOKE-TEST CASE (REAL DEVICE)
       From Menu, launch F1. Capture one mock case with
       facility name "TEST-PROVISION-<tablet-ID>". Save.
       Return to Menu → Sync to server.
       Expected: warning("Sync complete. 1 case uploaded.")
       Verify on CSWeb dashboard: Data tab → F1 → search by
       facility name "TEST-PROVISION-<tablet-ID>" → case visible.
       After verification, DELETE the test case from CSWeb.

[ ]  7. PRE-LOAD ASSIGNED SAMPLE (F4 ONLY)
       For F4, run F4_sync.pff with SyncDirection=get to
       download the pre-assigned household sample for this
       enumerator's cluster. Verify the sample lands in
       F4 external dict.

[ ]  8. STICKER LABEL
       Apply sticker showing:
         - Tablet ID: T-UHC-Y2-<NNN>
         - Enumerator name + username: <name> (ENUM<cluster>-<seq>)
         - Cluster: <cluster>
         - Supervisor (STL): <name> + WhatsApp/Slack contact
       Sticker placement: back of tablet, lower-right (does not
       interfere with case grip).

[ ]  9. TEST SD-CARD BACKUP
       Menu → Backup → confirm backup folder created on SD
       card (verify path: /Android/data/gov.sensis.cspro.csentry
       /files/<timestamp>_<username>/).
       Confirm backup zip exists.

[ ] 10. HAND OFF TO STL
       Sign bring-up checklist (provisioner + STL).
       File checklist in tablet inventory folder.
       Mark tablet status: "provisioned, with STL".
       STL signs off after their own end-user smoke test
       during training week.

Provisioner signature: __________  Date: __________
STL receipt signature: __________  Date: __________
```

### 8.15.2 Bring-up sprint plan

For 50 tablets, plan 2 days × 25 tablets/day with 2 provisioners working in parallel. Per-tablet time: ~30 min if everything works first-try; ~45 min average accounting for the inevitable SD-card or sync-credential snags.

Schedule the bring-up sprint **two weeks before training** so the inventory has buffer for failures (DOA tablets, broken chargers, app-install glitches that need re-flashing).

### 8.15.3 SD-card-before-launch rule

**(Khurshid 2022-10-12)** is explicit on this rule and we hit it during step 3 of the SOP:

> *"Ensure that an SD card is installed and that there is enough space to create a backup. If you insert an SD card while your application is running and attempt to backup your data, an error message will be displayed and the data will not be backed up. Why is this happening? Essentially, the application requires a subfolder named `gov.sensis.cspro.csentry/files` in the `Android/data` folder. When you insert the SD card while the application is running, this folder is not created."*
>
> *"The most effective method is to close the application before inserting the SD card and then run your application."*

If a tablet's SD card is added or swapped post-provisioning, the enumerator must **force-stop CSEntry, then relaunch**. Add this to the field troubleshooting card in the Field Manual.

### 8.15.4 Inventory hygiene

Every tablet has:
- A **physical sticker** (per step 8) — for ops to identify in the field.
- A **digital row** in the inventory spreadsheet — tablet ID, serial, model, enumerator, cluster, supervisor, provision date, last-known-condition (active/lost/damaged/returned).
- A **device ID** (`getdeviceid()` value) recorded in the row — enables [[#8.11 Enumerator login bound to tablet device ID|device-binding]].

Update the inventory whenever a tablet swaps hands. End-of-fieldwork reconciliation depends on the inventory being accurate.

---

## 8.16 publishdate() forced-update pattern

**(Khurshid 2022-10-08)** *Tutorial on PublishDate() Function* — force enumerators onto the latest build when the dev team pushes a fix.

### 8.16.1 The problem

Without forced update: enumerators run whatever `.pen` is installed on their tablet. A bug fix pushed to CSWeb's Apps tab is only picked up when the enumerator actively re-syncs the app. Some never do. Result: cases captured against stale logic, dirty data, post-hoc cleanup costs.

With forced update: each `.pen` carries its publish date (`publishdate()`). The entry app checks at every launch — if the publish date is older than N days, refuse to launch and prompt for re-sync. Stale apps don't even open.

### 8.16.2 publishdate() basics

`publishdate()` returns the date+time the `.pen` was built, encoded as `YYYYMMDDhhmmss`. Divide by 1000 to keep just `YYYYMMDD`.

**(Khurshid 2022-10-08)**: *"Whenever you create the .pen file the value written by the function will be the date and time that the .pen file was created. Simply divide the published date by 1000 to obtain the date only."*

Two ways to set: manual constant (`publish_day = 20260612`) or `publishdate()` auto-injected at build time. **Khurshid recommends the latter** — manual is error-prone, forgets to update on re-publish.

### 8.16.3 Production pattern

```cspro
PROC GLOBAL

numeric publish_day, days_left;
array app_months(12) string;

PROC LEVEL
preproc

  { initialize month names — once per app run }
  app_months(1)  = "January";
  app_months(2)  = "February";
  app_months(3)  = "March";
  app_months(4)  = "April";
  app_months(5)  = "May";
  app_months(6)  = "June";
  app_months(7)  = "July";
  app_months(8)  = "August";
  app_months(9)  = "September";
  app_months(10) = "October";
  app_months(11) = "November";
  app_months(12) = "December";

  { extract date-only from publishdate() }
  publish_day = publishdate() / 1000;

  { allow up to 90 days from publish; warn at last 5 }
  if datediff(systemdate(), publish_day, days) > 90 then
    errmsg("App build is %d days old. Please re-sync to update.",
           datediff(systemdate(), publish_day, days));
    stop(1);
  else
    days_left = 90 - datediff(systemdate(), publish_day, days);
    if days_left <= 5 then
      if days_left = 0 then
        warning("After today midnight you will be unable to access "
                "the application. Sync now to update.");
      else
        warning(maketext(
          "%d days left. Please update by %d %s %d.",
          days_left,
          day(systemdate() + days_left),
          app_months(month(systemdate() + days_left)),
          year(systemdate() + days_left)
        ));
      endif;
    endif;
  endif;
```

Pattern: every entry app calls a `checkAppVersion()` style check in `PROC LEVEL preproc`. Out-of-date apps refuse to launch and prompt resync.

### 8.16.4 Tuning the window

**90 days** is conservative for a 3-month UHC fieldwork period. Tune per-project:

- Short fieldwork (2 weeks): 21 days expiry — forces resync every 3 weeks.
- Medium fieldwork (3 months): 90 days — covers full fieldwork without forcing resync mid-stream unless bug fix needed.
- Long fieldwork (6+ months): 30 days — forces monthly re-sync to stay close to the latest build.

Fieldwork-end **buffer**: the expiry should land **at least 30 days after the planned end-of-fieldwork date** so a delayed wrap-up doesn't lock everyone out.

### 8.16.5 Hot-fix and the publishdate() check together

When Carl pushes a fixed `.pen` to CSWeb (per [[#8.20 Hot-fix / re-publish flow]]):

1. New `.pen` has a fresh `publishdate()`.
2. Tablet syncs (or is forced to via the staleness check).
3. CSWeb compares hash; downloads the new `.pen`.
4. Enumerator launches → `publishdate()` is fresh → no warning, app runs normally.
5. Enumerator on a tablet that hasn't synced in 90+ days: app refuses to launch → enumerator runs sync from menu → new `.pen` arrives → next launch is fresh.

The two patterns reinforce: hot-fix delivers the new `.pen`; `publishdate()` enforces nobody runs the old one.

---

## 8.17 synctime() for upload tracking

**(Khurshid 2025-02-20)** *Tutorial on synctime Function* — the in-app pattern for "did all of yesterday's interviews actually upload?"

Per Protocol V2: **"CSWeb daily 10 PM upload mandate"**. We need a tablet-side check that prompts enumerators if their last sync was too long ago.

### 8.17.1 synctime() basics

Returns the timestamp of the last successful synchronization. Two scopes:

- **Whole-dictionary** call — last sync time for the entire data file: `synctime(<url>, <dict>)`.
- **Per-case** call — last sync time for a specific case: `synctime(<url>, <dict>, "", <case-uuid>)`.

Returns Unix time. Convert with `timestring()` for display.

**Critical insight** (Khurshid): *"If a case was synchronized earlier but later modified or if a new case is added, the function will return notappl."* — `notappl` is the **signal for "needs sync"**.

### 8.17.2 Daily-reminder pattern

In MENU.pen's `PROC LEVEL preproc`:

```cspro
PROC GLOBAL

numeric last_sync, hours_since;
config sync_url csweb_url;

function checkSyncFreshness()
   last_sync = synctime(csweb_url, F1_DATA);

   if last_sync = 0 then
      { never synced — likely first launch }
      warning("This tablet has never synced. Please sync after "
              "your first interview today.");
      exit;
   endif;

   { Unix-time math: 1 hour = 3600 seconds }
   hours_since = (systemdate() - last_sync) / 3600;

   if hours_since > 24 then
      warning("Last sync was %d hours ago. Please sync now to "
              "stay current.", hours_since);
   else if hours_since > 12 then
      warning("Last sync was %d hours ago. Plan to sync by 10 PM.",
              hours_since);
   endif;
end;
```

Wire into MENU.pen's preproc. Enumerator opens the menu app → check fires → reminder shown if sync is stale.

### 8.17.3 Per-case "pending sync" report

For supervisors who want to see exactly which cases on this tablet aren't yet on the server:

```cspro
function pendingSyncReport()
   numeric per_case_time;
   numeric pending_count;
   pending_count = 0;

   forcase F1_DATA do
      per_case_time = synctime(csweb_url, F1_DATA, "", uuid(F1_DATA));
      if per_case_time = notappl then
         { case has been modified since last sync OR is new }
         pending_count = pending_count + 1;
         { write to a per-case report — case key, last modified }
      endif;
   enddo;

   if pending_count = 0 then
      warning("All cases are synced.");
   else
      warning("%d case(s) pending sync.", pending_count);
   endif;
end;
```

Bind to a menu item: "Show pending sync report". STL can ask enumerators to run it as a verification step.

### 8.17.4 Wire-up summary

For UHC, every menu app gets:

- `checkAppVersion()` — `publishdate()` staleness check (per [[#8.16 publishdate() forced-update pattern]]).
- `checkSyncFreshness()` — `synctime()` daily reminder (per this section).
- `pendingSyncReport()` — on-demand per-case status (per this section).

All three live in MENU.pen's PROC GLOBAL + LEVEL preproc.

---

## 8.18 Backup and recovery

**(Khurshid 2022-10-12)** + **(Khurshid 2022-10-18)** — the SD-card-based backup-and-restore pattern. Tablets fail; enumerators delete things; apps crash mid-save. Local backup means a 30-min re-entry instead of a day of lost work.

### 8.18.1 Backup pattern — overview

Every backup run:

1. **Resolve external storage path** via `pathname(path_type_csentry_external)`.
2. **Build timestamp + login-ID-named subfolder** within `<external>/test_project/backup/listing/` (using `dircreate` if needed).
3. **Copy `.csdb` files** from the application data folder into the subfolder via `filecopy`.
4. **Compress** all `.csdb` files in the subfolder into a single zip via `compress`.
5. **Delete the loose `.csdb` files** (only after verifying zip is valid) via `filedelete`.
6. Result: one zipped backup per session, named by time + user.

### 8.18.2 Backup PROC pattern

Adapted from **(Khurshid 2022-10-12)** for UHC's three-instrument structure:

```cspro
PROC GLOBAL

alpha (200) backupRoot, backupFolder;

function performBackup()
   { Skip on Windows desk test }
   if getos() = 10 then
      warning("Backup runs on Android only.");
      exit;
   endif;

   { Build path — external storage > test_project > backup > listing }
   backupRoot = pathname(path_type_csentry_external)
              + "uhc_y2\backup\";
   dircreate(backupRoot);

   { Time + login-ID subfolder; sanitize : / characters out of timestamp }
   alpha (50) safe_ts;
   safe_ts = edit("9999-99-99_99-99", systemdate());
   { remove illegal filesystem chars }
   backupFolder = backupRoot + safe_ts + "_" + USER_ID + "\";
   dircreate(backupFolder);

   { Copy data — F1, F3, F4 csdb's that exist on this tablet }
   filecopy(pathconcat(pathname(path_type_csentry_application),
                       "F1.csdb"),
            backupFolder + "F1.csdb");
   filecopy(pathconcat(pathname(path_type_csentry_application),
                       "F3.csdb"),
            backupFolder + "F3.csdb");
   filecopy(pathconcat(pathname(path_type_csentry_application),
                       "F4.csdb"),
            backupFolder + "F4.csdb");

   { Compress all into one archive }
   compress(backupFolder + "data.zip", backupFolder, "*.csdb");

   { Verify zip exists before deleting source }
   if fileexist(backupFolder + "data.zip") then
      filedelete(backupFolder + "*.csdb");
      warning("Backup complete: %s", backupFolder + "data.zip");
   else
      errmsg("Backup compression failed; source files retained.");
   endif;
end;
```

Bind to menu item "Backup data". Recommend running once per day, end-of-day (after sync to server). The two protect different failures: sync protects against tablet loss; SD-card backup protects against app/data corruption between syncs.

### 8.18.3 Restore-from-backup pattern

**(Khurshid 2022-10-18)** — the restore flow uses `pathdotselectfile()` for a sandboxed file picker, `decompress()` to extract, and a three-option dialog for move-all / move-one / cancel.

```cspro
PROC GLOBAL

function restoreFromBackup()
   alpha (200) backup_root, selected_path;
   numeric selection;

   { Resolve backup root }
   backup_root = pathname(path_type_csentry_external)
               + "uhc_y2\backup\";

   { Pick a backup zip — sandboxed to backup_root }
   selected_path = pathdotselectfile(
      "Select a backup zip to restore",
      "data.zip",       { wildcard filter }
      backup_root,      { starting directory }
      backup_root       { root — user can't navigate above }
   );

   if length(selected_path) = 0 then exit; endif;

   { Confirm }
   select(continue,
      maketext("Restore from %s?", selected_path),
      "Restore",
      "Cancel"
   );

   { decompress in-place — original zip stays for re-restore safety }
   decompress(selected_path);

   { Move into app data folder; three-option dialog for granularity }
   moveBackupFiles(backup_root, pathname(path_type_csentry_application));
end;

function moveBackupFiles(alpha src_dir, alpha dest_dir)
   numeric selection;
   numeric file_count;
   file_count = 3;   { F1, F3, F4 }

   selection = 2;
   do while selection = 2 and file_count > 0
      select(continue,
         "Move all files",       { 1 → bulk }
         "Move only F1",         { 2 → selective }
         "Move only F3",
         "Move only F4",
         "Return to menu"
      );

      if selection = 1 then
         filecopy(src_dir + "*.csdb", dest_dir);
         filedelete(src_dir + "*.csdb");
         exit;
      else if selection = 2 then
         filecopy(src_dir + "F1.csdb", dest_dir + "F1.csdb");
         filedelete(src_dir + "F1.csdb");
         file_count = file_count - 1;
      else if selection = 3 then
         filecopy(src_dir + "F3.csdb", dest_dir + "F3.csdb");
         filedelete(src_dir + "F3.csdb");
         file_count = file_count - 1;
      else if selection = 4 then
         filecopy(src_dir + "F4.csdb", dest_dir + "F4.csdb");
         filedelete(src_dir + "F4.csdb");
         file_count = file_count - 1;
      else if selection = 5 then
         exit;
      endif;
   enddo;
end;
```

Bind to menu item "Restore from backup". Permissions: this should be **STL-only** (per [[#8.6 CSWeb roles model]]) — not enumerator — to prevent accidental data loss. Use `cell_option_dummy` (per **(Khurshid 2022-10-12)**) to gate visibility based on login role.

### 8.18.4 SD-card-before-launch rule (revisited)

Repeated from [[#8.15.3 SD-card-before-launch rule]] because it bites here too:

> SD card must already be inserted when CSEntry launches. Otherwise `path_type_csentry_external` resolution fails, and backup/restore can't find the folder.

If the SD card was inserted post-launch, force-stop CSEntry and relaunch. Add a guard at the top of `performBackup()` and `restoreFromBackup()`:

```cspro
if length(pathname(path_type_csentry_external)) = 0 then
   errmsg("SD card not detected. Close the app, insert SD card, "
          "and relaunch.");
   exit;
endif;
```

### 8.18.5 Backup retention policy

SD cards have finite space. Define retention:

- **Keep last 14 daily backups** on the SD card.
- **Old backups move to "archive" folder** on the same SD card after 14 days.
- **Manual cleanup at end-of-fieldwork**: archive moves to ASPSI's secure backup; SD cards wiped before re-issue.

Implement retention as a periodic task in MENU.pen's preproc — every 7th launch, scan backup folder, move >14-day-old folders to archive.

### 8.18.6 Backup vs sync — separate failure modes

| Failure | Sync protects | SD backup protects |
|---|---|---|
| Tablet lost / stolen | Yes — server has all synced cases | No — backup is on the tablet |
| Tablet damaged (still readable) | Partial — server has up-to-last-sync | Yes — backup retrievable from SD |
| App crash mid-save | Sometimes — depends on autosave | Yes — yesterday's backup intact |
| User deletes a case | No — sync deletion propagates | Yes — backup pre-dates the deletion |
| MySQL corruption on server | No — server is the corruption source | Yes — restore from backups + re-sync |

Both are mandatory. Don't argue with the redundancy.

---

## 8.19 Connectivity policy

The tablet's network path to the server. Three modes; cellular is primary; WiFi is opportunistic; HTTPS is always.

### 8.19.1 Cellular data

Each tablet ships with a SIM card and data plan. Provisioning:

- **STL provides SIM** with a 5 GB monthly plan (subject to confirmation per [[#8.22 Open decisions]]).
- **5 GB** sized for: ~300 cases × ~5 KB per case = 1.5 MB; plus app updates (~10 MB per update); plus photos (~200 KB × 50 = 10 MB) — well under 100 MB/month for the data, with the rest as buffer for incidental usage.
- **APN configured** at provisioning (carrier-specific; document the APN values per carrier).
- **Hotspot disabled by default** — prevent enumerators from hotspotting personal devices, which would burn the data plan.

### 8.19.2 WiFi

Where available — facility WiFi, hotel WiFi during travel days, ASPSI office WiFi at end-of-week debriefs.

- **Auto-connect to known networks** — provision the ASPSI office WiFi password at bring-up.
- **Sync prefers WiFi** when on a known network — set in CSEntry Settings → Sync → "WiFi only when available" off (the default — sync uses whatever is available).
- **Travel WiFi** is opt-in. Hotel WiFi is often unencrypted; HTTPS protects credentials but enumerators should still avoid syncing on unknown public networks unless ops explicitly OKs it.

### 8.19.3 HTTPS enforcement

**Mandate**: sync URL is `https://csweb.aspsi.example.com/csweb/api`. The `https` schema is hardcoded in the User Settings attribute. Without HTTPS:

- Public WiFi networks can MITM the credentials.
- Even cellular data can be intercepted on rogue base stations (unlikely in PH but documented threat globally).
- Server returns plaintext data — facility names, GPS coords visible to anyone listening.

There's no fallback to HTTP. If HTTPS fails, the sync fails — and the failure is visible to the enumerator (errmsg). The solution is to fix HTTPS, not to bypass it.

### 8.19.4 Connectivity troubleshooting card

For STLs and enumerators — laminated card in the tablet kit:

```
SYNC FAILED — TROUBLESHOOTING
=============================

1. Check internet:
   - Open Chrome, browse to google.com.
   - If page loads → internet OK; sync issue is server-side or
     credentials.
   - If page doesn't load → internet issue; resolve first.

2. Check cellular signal:
   - Pull down notification shade — see signal bars.
   - If no signal → move to a different location.
   - If signal but no data → toggle airplane mode on, then off.

3. Verify URL:
   - Menu → Settings → sync_url
   - Should be: https://csweb.aspsi.example.com/csweb/api
   - If wrong → contact STL.

4. Verify credentials:
   - Menu → Logout → Login again with username + password.
   - If login fails → contact STL.

5. Try again in 5 minutes:
   - Server may be temporarily down.

6. If still failing after 30 minutes:
   - Cases are SAFE on the tablet — no data lost.
   - WhatsApp/Slack STL with: tablet ID, time, error message.
   - STL escalates to ops.
```

---

## 8.20 Hot-fix / re-publish flow

Mid-fieldwork bug discovered. What does the dev team do?

### 8.20.1 What counts as hotfix-worthy

- **Critical**: data integrity bug — wrong skip path, miscalculated derived value, save-fails-silently. Hotfix.
- **High**: blocking UX bug — keyboard input stuck, screen not advancing, validation always-fails. Hotfix.
- **Medium**: cosmetic bug — typo in question text, mistranslated label. Batch into next planned update.
- **Low**: nice-to-have — UI polish, additional logging. Defer to post-fieldwork.

Rule of thumb: if it would corrupt data or stop fieldwork, hotfix. Otherwise batch.

### 8.20.2 Hotfix flow

```
1. Bug identified by STL / enumerator / data review.
   Reported via WhatsApp/Slack channel + ticketed in
   ASPSI issue tracker (severity: critical/high).

2. Carl + Project Coordinator confirm severity.

3. Carl reproduces in Designer (CSEntry Windows desk test).
   Mock case that triggers the bug — replay → confirm.

4. Fix:
   - Edit generator (.py) → regenerate .dcf if dictionary
     change.
   - Edit .apc → fix PROC logic.
   - Edit .fmf → fix form layout.
   - Add or update test case to cover the bug.

5. Regression test:
   - Replay all archived test cases.
   - Confirm new bug fixed AND no regressions in other paths.

6. Re-publish:
   - File → Publish Entry Application → new .pen.
   - publishdate() is auto-injected — fresh.

7. Re-deploy to CSWeb:
   - Apps tab → upload new .pen → existing entry replaced.
   - CSWeb stores both old and new (versioned by upload time);
     latest is what tablets pull.

8. Push out:
   - Slack #uhc-y2-field channel: "Build vX uploaded; please
     run sync now to pick up the fix."
   - Tablets that sync within 24h pick up automatically.
   - Tablets that don't: publishdate() check kicks in at next
     launch (per Section 8.16); refuses to launch; forces sync.

9. Verify:
   - Sample 3-5 random tablets via STLs: confirm new
     publishdate() shown in Menu → About.
   - Watch incoming case data for a day — confirm bug-pattern
     no longer appears.

10. Post-mortem:
    - Document in issue tracker: root cause, fix, prevention.
    - If preventable by a Phase 4 logic-pass, update the
      logic-pass checklist for next instrument.
```

### 8.20.3 Hash-based update detection

CSWeb compares the SHA hash of each tablet's installed `.pen` against the latest `.pen` on the server. Different hash → tablet downloads new `.pen` on its next sync. Same hash → no download. This is how the "tablets pick it up on next sync" magic actually works.

The `publishdate()` enforcement is the **second line of defense** — even if the hash check somehow misses (edge cases, sync interruptions), the publishdate refusal forces resync at next launch.

### 8.20.4 Versioning

For the dev team's own tracking (since the workflow template doesn't dictate a versioning scheme — and per project conventions, git/version commentary is out of scope for this guide):

- Publish dates serve as de-facto version IDs. `F1.pen` published 2026-06-12 is "version dated June 12, 2026".
- For human-readable versions, optionally maintain a Description string in PFF — e.g., `Description=F1 sync v1.2 (2026-06-15 hotfix)`.
- The deployment manifest tracks: instrument, publish date, change summary, deployer.

---

## 8.21 Phase 8 exit criteria

Phase 8 is **done** when all of these are green. Anything red blocks supervisor training.

### 8.21.1 Server track

- [ ] CSWeb server provisioned per [[#8.2 Server provisioning — Wampserver 3.2.6]].
- [ ] Production URL `https://csweb.aspsi.example.com/csweb` reachable from external IP (test from a phone on cellular, not from the office).
- [ ] HTTPS cert valid (no browser warnings).
- [ ] CSWeb dashboard login works for `admin`.
- [ ] F1, F3, F4 dictionaries registered on the server (Apps tab + Data tab visible).
- [ ] Six cluster-roles + ASPSI_ADMIN + ASPSI_OPS + STL_REGION + ENUMERATOR + DOH_VIEWER created and tested.
- [ ] CSV bulk-import of 50+ users completed once Field Manager finalizes the roster.
- [ ] Relational break-out configured (optional — only if BI dashboards are in scope).

### 8.21.2 Client track

- [ ] One tablet provisioned end-to-end per [[#8.15 Tablet provisioning SOP]].
- [ ] Smoke-test case captured on the tablet, synced, visible on dashboard.
- [ ] Backup-to-SD-card tested; backup zip exists.
- [ ] Restore-from-backup tested; data round-trips.
- [ ] `publishdate()` check wired in F1 + F3 + F4 entry apps (verifies refusal-to-launch on stale builds via test).
- [ ] `synctime()` reminder wired in MENU.pen (verifies reminder fires after 24 hours via test).
- [ ] `synchronize_data()` round-trip works on tablet (independent verification of the sync pipeline).
- [ ] HTML dialog directory configured per app PFF.
- [ ] External dictionaries (locality, facility, sample) deployed and read by entry apps.
- [ ] At least 3 tablets bring-up'd in parallel (validates the SOP works at scale, not just on the dev box).

### 8.21.3 Connectivity track

- [ ] Sync URL configured via User Settings attribute `sync_url`.
- [ ] Sync URL is the production URL, not localhost (verified per [[#8.4.5 The "tablet sync URL must be the live IP, not localhost" rule]]).
- [ ] HTTPS resolves on both the dev workstation AND on a tablet over cellular.
- [ ] Cellular data plan active on at least the smoke-test tablet.
- [ ] WiFi auto-connect to ASPSI office configured.
- [ ] Connectivity troubleshooting card included in tablet kit.

### 8.21.4 Operational track

- [ ] Field Manual updated with sync SOP, backup schedule, restore-from-backup steps, hot-fix communication channel.
- [ ] Incident-response SOP documented (server down, tablet lost, credential compromised) per [[#8.9.2 Decision matrix — when to fall back]].
- [ ] Tablet inventory spreadsheet exists with all bring-up'd tablets logged.
- [ ] STL training material includes Sync Report walkthrough.

### 8.21.5 Triage matrix

When a Phase 8 verification step fails, isolate to the right track:

| Symptom | First-look track | Likely root cause |
|---|---|---|
| Dashboard not loading from external | Server | Apache not exposing port 80/443; firewall blocks |
| Dashboard loads but login fails | Server | Wrong admin password; user not created; role mismatch |
| Tablet's sync says "cannot connect" | Connectivity | Wrong URL; HTTPS cert invalid; cellular signal lost |
| Tablet's sync connects but no data lands | Client | `setfile()` path wrong; dictionary not registered |
| Sync OK but case not in Data tab | Server | Dictionary version mismatch; relational break-out behind |
| Backup succeeds but folder empty | Client | SD-card-before-launch rule violated; relaunch needed |
| Old `.pen` running despite new upload | Client | Hash check missed; force via `publishdate()` refusal |
| `publishdate()` refusal is wrong-fired | Client | System date wrong on tablet; NTP sync not configured |

Run through the matrix for any failed exit criterion before escalating.

---

## 8.22 Open decisions (TODOs)

These decisions block exit-criteria green. Each has an owner and a deadline.

| # | Decision | Owner | Deadline | Notes |
|---|---|---|---|---|
| 1 | **Server hosting**: ASPSI office static IP vs cloud VPS | Project Director + Carl | 2026-05-22 | Per [[#8.4.1 Hosting decision matrix]]; cloud VPS recommended if office static IP procurement is uncertain |
| 2 | **HTTPS cert source**: Let's Encrypt vs commercial CA | Carl + ASPSI ops | 2026-05-22 | Let's Encrypt is free + automated; commercial only if security policy mandates |
| 3 | **Tablet model + spec** (flagged to Juvy in May 4 meeting) | Juvy → Project Coordinator | 2026-05-29 | Need: 8" screen min, Android 11+, 32 GB storage, SD card slot, 4G LTE — confirm shortlist |
| 4 | **Cellular plan provider + per-tablet cost** | Project Coordinator | 2026-06-05 | Globe vs Smart vs DITO; 5 GB monthly plan typical; verify coverage in target regions |
| 5 | **Device-binding policy** (per [[#8.11 Enumerator login bound to tablet device ID]]) | Carl + Project Director | 2026-06-12 | Decision: enable for main fieldwork, skip for pretest? |
| 6 | **Field Manager roster finalization** | Field Manager | 2026-06-19 | Blocks CSV import; needs full enumerator + STL list with names, contacts, cluster assignments |
| 7 | **Translation locale strategy** (Filipino + others) | Carl + ASPSI translations | 2026-06-26 | Per [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/docs/translations-pipeline|translations pipeline]]; affects what locales the entry apps ship with |
| 8 | **DOH_VIEWER credential issue date** | Project Director + DOH liaison | 2026-07-10 | DOH client interim review window — when do they want first read access? |
| 9 | **Backup retention period on SD card** | Carl + Field Manager | 2026-06-12 | Default 14 days proposed; confirm vs SD-card capacity |
| 10 | **Hotfix communication channel** | Carl + Project Coordinator | 2026-06-19 | WhatsApp #uhc-y2-field vs Slack #uhc-y2-capi — pick one and standardize |

Re-review the open decisions weekly until all are closed.

---

## Appendix A — Quick-reference command + file paths

For ops use during Phase 8 work:

```text
SERVER PATHS
  Document root:     C:\wamp64\www
  CSWeb root:        C:\wamp64\www\csweb
  CSWeb files dir:   C:\wamp64\www\csweb\files
  CSWeb config:      C:\wamp64\www\csweb\config
  PHP CLI:           C:\wamp64\bin\php\php7.4.x\php.exe

URLS
  Wamp landing:      http://localhost
  phpMyAdmin:        http://localhost/phpmyadmin
  CSWeb dashboard:   https://csweb.aspsi.example.com/csweb/ui/login
  CSWeb API:         https://csweb.aspsi.example.com/csweb/api/
  CSWeb setup:       https://csweb.aspsi.example.com/csweb/setup

DATABASES
  CSWeb backing:     csweb_uhc_y2
  Relational:        csweb_uhc_y2_relational
  Web user:          csweb_user (password: see ASPSI password vault)

COMMANDS
  Process cases:     cd C:\wamp64\www\csweb && php bin\console csweb:process-cases
  PHP version:       php -v
  Apache restart:    Wamp tray icon → Apache → Service administrator → Restart Service
  MySQL restart:     Wamp tray icon → MySQL → Service administrator → Restart Service

TABLET PATHS
  CSEntry app dir:   /Internal Storage/CSPro/<F-series>/
  External (SD):     /Android/data/gov.sensis.cspro.csentry/files/
  Backup root:       /Android/data/gov.sensis.cspro.csentry/files/uhc_y2/backup/

PFF FILES (per tablet)
  F1 sync:           /CSPro/F1/F1_sync.pff
  F3 sync:           /CSPro/F3/F3_sync.pff
  F4 sync:           /CSPro/F4/F4_sync.pff

ENVIRONMENT VARIABLES (server box)
  PATH addition:     C:\wamp64\bin\php\php7.4.x  (for php bin\console)
```

---

## Appendix B — CSPro PROC reference for Phase 8

| Function | Purpose | Example |
|---|---|---|
| `syncconnect("csweb", url, user, pwd)` | Open sync session | `rc = syncconnect("csweb", csweb_url, USER_ID, USER_PWD);` |
| `syncdisconnect()` | Close sync session | `syncdisconnect();` |
| `synchronize_data(<dict>, <dir>)` | Upload/download cases | `synchronize_data(F1_DATA, sync_direction_send);` |
| `synchronize_file(put, src, dst)` | Upload arbitrary file | `synchronize_file(put, photo_path, "pictures/photo1.jpg");` |
| `setfile(<dict>, path)` | Bind data file to dict | `setfile(F1_DATA, pathconcat(pathname(path_type_csentry_application), "F1.csdb"));` |
| `getdeviceid()` | Tablet device ID | `THIS_DEVICE_ID = getdeviceid();` |
| `publishdate()` | `.pen` build date | `publish_day = publishdate() / 1000;` |
| `synctime(url, dict)` | Last-sync timestamp | `last_sync = synctime(csweb_url, F1_DATA);` |
| `synctime(url, dict, "", uuid)` | Per-case last sync | `t = synctime(csweb_url, F1_DATA, "", uuid(F1_DATA));` |
| `pathname(path_type_csentry_external)` | SD-card root | `ext = pathname(path_type_csentry_external);` |
| `pathname(path_type_csentry_application)` | App folder | `app = pathname(path_type_csentry_application);` |
| `pathconcat(...)` | Path join | `p = pathconcat(app, "F1.csdb");` |
| `pathdotselectfile(title, wildcard, start, root)` | Sandboxed file picker | `f = pathdotselectfile("Pick", "*.zip", root, root);` |
| `dircreate(path)` | Create directory | `dircreate(backupFolder);` |
| `filecopy(src, dst)` | Copy file | `filecopy("F1.csdb", backupFolder + "F1.csdb");` |
| `filedelete(pattern)` | Delete files | `filedelete(backupFolder + "*.csdb");` |
| `compress(zip, folder, pattern)` | Zip files | `compress(folder + "data.zip", folder, "*.csdb");` |
| `decompress(zip)` | Unzip | `decompress(selected_zip_path);` |
| `fileexist(path)` | Existence check | `if fileexist(backupFolder + "data.zip") then ...` |
| `getos()` | OS code (10 = Windows) | `if getos() = 10 then ...` |
| `errmsg(msg, args...)` | HARD error | `errmsg("Sync failed: %s", csweb_url);` |
| `warning(msg, args...)` | Non-blocking warning | `warning("Sync complete.");` |
| `maketext(fmt, args...)` | Format string | `m = maketext("After %d days...", days_left);` |
| `datediff(a, b, days)` | Date math | `datediff(systemdate(), publish_day, days)` |
| `systemdate()` | Current date | `today = systemdate();` |
| `timestring(unix)` | Unix → readable | `display = timestring(last_sync);` |
| `loadsetting(key)` / `savesetting(key, val)` | User Settings I/O | `s = loadsetting("sync_url");` |
| `config <attr> <var>;` | Bind variable to attribute | `config sync_url csweb_url;` |

---

## Appendix C — Phase 8 deliverables checklist

For UHC Year 2, Phase 8 produces:

| Deliverable | Location | Owner | Status |
|---|---|---|---|
| Wampserver + CSWeb production install | ASPSI server box | Carl + ops | TBD |
| `csweb_uhc_y2` MySQL DB + `csweb_user` | Server box | Carl | TBD |
| HTTPS cert + DNS for `csweb.aspsi.example.com` | Server box + ASPSI DNS | ASPSI ops | TBD |
| CSWeb roles (5 custom + 2 built-in) | CSWeb dashboard | Carl | TBD |
| CSWeb users (~50–60 imported) | CSWeb dashboard | Carl + Field Manager | Blocks on roster |
| F1.pen + F1_sync.pff | Designer + CSWeb dashboard | Carl | F1 done; F3/F4 after Jun 12 |
| F3.pen + F3_sync.pff | Designer + CSWeb dashboard | Carl | After Jun 12 |
| F4.pen + F4_sync.pff | Designer + CSWeb dashboard | Carl | After Jun 12 |
| MENU.pen with sync + backup + restore + checks | Designer | Carl | TBD |
| LOGIN.pen with device-ID validation | Designer | Carl | TBD (open decision per device-binding) |
| Tablet inventory spreadsheet | ASPSI Drive | Project Coordinator | Started |
| Field Manual section: sync SOP + backup SOP + restore SOP + troubleshooting card | `deliverables/Field-Manual/` | Carl + Field Manager | TBD |
| Hot-fix runbook | `deliverables/Runbooks/` | Carl | TBD |
| Bring-up checklist (per [[#8.15.1 SOP — step by step]]) | `deliverables/Tablet-Bring-Up/` | Carl | This document |

Mark "done" as each deliverable lands; track in the project's standup log.

---

## Cross-references

- [[00-Architecture]] — System architecture; where Phase 8 sits in the lifecycle
- [[01-Roles-and-Handoffs]] — Who hands off what at Phase 8 entry/exit
- [[02-Phase-0-2-Foundation]] — Toolchain knowledge that Phase 8 builds on
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSWeb|CSWeb concept page]] — verified permission model
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSWeb Users Guide|Source - CSWeb Users Guide]] — official documentation summary
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Synchronization|CSPro Synchronization concept]] — sync protocol details
- [[2_Areas/IT-Standards/templates/CAPI-Development-Workflow|CAPI Development Workflow]] — living-document template
- Khurshid technique cards (Phase 8 cluster):
  - 2022-03-14 Wampserver + CSWeb install
  - 2022-04-30 Deploy + sync data
  - 2022-05-05 Sync report, sync files, users, roles
  - 2022-05-12 Batch file download from CSWeb
  - 2022-04-24 HTML dialogs + Deploy Application
  - 2022-10-08 publishdate()
  - 2025-02-20 synctime()
  - 2022-10-12 Backup
  - 2022-10-18 Restore

---

## Appendix A — Linux VPS hosting alternative *(folded from CAPI-Development-Playbook 2026-04-21)*

The main body of this guide assumes Wampserver on Windows (Khurshid 2022-03-14 baseline). For a national-scale UHC deployment where the server must be reachable from cellular tablets across PH regions, a **Linux VPS hosting CSWeb on Tomcat + Nginx** is a stronger production choice. Wampserver is fine for development and pilots; Tomcat-on-VPS is the recommendation for production.

### A.1 Hosting decision matrix

| Option | Pros | Cons | When to pick |
|---|---|---|---|
| **Generic VPS** — Hostinger / DigitalOcean / Hetzner / Linode / Vultr | Full root, any stack version, cheapest ($10–40/mo), easy migration, your backups your rules. | You install/patch/secure Tomcat, MySQL, Nginx, certbot yourself. On-call is you. | **Default for UHC Year 2** — DOH data, ~50–100 tablets, 6+ months of fieldwork, data-sovereignty matters. |
| **Elestio** (managed app hosting) | One-click Tomcat + MySQL, managed TLS, automated backups, monitoring dashboard. | ~1.5–2× VPS price. Less root control. Migration = re-export + re-import. No CSWeb-native image (you still deploy the WAR yourself to their Tomcat). | Pilot, demo, or if you don't want to touch Linux. |
| **DOH-provided server** | Inside the DOH security perimeter; matches data-sovereignty posture. | Access/change-control ceremonies; slower iteration. | If DOH mandates it. **Confirm with DOH-PMSMD before deploying elsewhere.** |
| **AWS / Azure / GCP** | Enterprise-grade everything. | Over-engineered for this scale; surprise pricing. | Not worth it here. |
| **Wampserver (Windows)** — main body of §8.2 | Khurshid baseline; familiar tooling for ASPSI ops. | Windows-server licensing; harder to harden than Linux; not a typical national-scale production posture. | **Development + pilot only.** |

### A.2 Recommended minimum VPS spec

For ~50–100 tablets with daily 22:00 MNL sync and weekly export pulls:

- **Hetzner CPX21** (3 vCPU, 4 GB RAM, 80 GB SSD, ~€8/mo) **or** **DigitalOcean Premium 4 GB** (~$24/mo) **or** **Hostinger KVM 2** (~$7/mo promo, ~$13/mo renewal).
- **Ubuntu 22.04 LTS** (or 24.04 — pick whichever has the longer LTS tail at decision time).
- One DNS name pointing at it (e.g. `csweb.aspsi.example.ph`).
- HTTPS via **Let's Encrypt + certbot** (auto-renewing).
- UFW firewall: 22 (SSH), 80 (HTTP→HTTPS redirect), 443 (HTTPS).
- fail2ban for SSH brute-force protection.
- Disable password SSH; key-only login.

### A.3 Bare-VPS deployment outline

Paste-ready 10-step bring-up:

```bash
# 1. Provision VPS, SSH in
ssh root@csweb.aspsi.example.ph

# 2. System packages
apt update && apt upgrade -y
apt install -y openjdk-17-jre tomcat9 mysql-server nginx certbot python3-certbot-nginx ufw fail2ban

# 3. Firewall
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw enable

# 4. MySQL: create DB + dedicated user
mysql -u root -p
> CREATE DATABASE csweb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
> CREATE USER 'csweb_user'@'localhost' IDENTIFIED BY '<strong-pwd>';
> GRANT ALL PRIVILEGES ON csweb.* TO 'csweb_user'@'localhost';
> FLUSH PRIVILEGES;

# 5. Download CSWeb WAR matching CSPro Designer version (7.7+)
cd /tmp
wget https://csprousers.org/path/to/csweb-7.7.war   # check current URL on csprousers.org

# 6. Drop into Tomcat webapps; auto-deploys
cp csweb-7.7.war /var/lib/tomcat9/webapps/csweb.war
systemctl restart tomcat9

# 7. Configure CSWeb via web UI (browse to http://localhost:8080/csweb/setup.php)
#    - DB host=localhost  user=csweb_user  password=<strong-pwd>  db=csweb
#    - Admin user / pwd

# 8. Nginx HTTPS reverse proxy → Tomcat 8080
cat > /etc/nginx/sites-available/csweb <<'NGX'
server {
    listen 80;
    server_name csweb.aspsi.example.ph;
    location / { proxy_pass http://127.0.0.1:8080; proxy_set_header Host $host; }
}
NGX
ln -s /etc/nginx/sites-available/csweb /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# 9. TLS via Let's Encrypt
certbot --nginx -d csweb.aspsi.example.ph

# 10. Daily MySQL backup (cron → S3 / Backblaze B2 / DOH-approved off-site)
crontab -e
# 0 2 * * * /usr/bin/mysqldump -u root -p<pwd> csweb | gzip > /backups/csweb-$(date +\%F).sql.gz && rclone copy /backups/ b2:aspsi-csweb-backups
```

### A.4 Trade-offs vs Wampserver baseline

- **Pro Linux:** smaller attack surface, no Windows-server licence, easier scripting, better long-term backup/restore tooling (`mysqldump` + `rclone` to S3-compatible).
- **Pro Wampserver:** matches Khurshid corpus screenshots step-for-step; ASPSI ops may prefer Windows for staff familiarity.
- **Recommendation:** Wampserver for the dev/pilot CSWeb on Carl's machine + ASPSI office; **Linux VPS for production** — cutover before tablet provisioning (Jul 1st-week).

### A.5 Sync URL hand-off

Once the VPS is live, the public sync URL (e.g. `https://csweb.aspsi.example.ph/csweb/api`) is the single value that needs to land in:

- Each tablet's CSEntry sync settings (configured during tablet bring-up per §8.15).
- The `sync_url` config attribute in each F-series `.apc` (per §8.10 paste-ready PROC).
- The Field Manager + STL ops cheat sheet ([[99-Quick-Reference]] §3 CSWeb Admin).

The Khurshid 2022-04-30 rule applies regardless of OS choice: **"Tablet sync URL must be the live IP, not localhost."** On the VPS, that means the public DNS name, not `127.0.0.1` or `localhost`.

---

## Next

Once Phase 8 exit criteria are green, fieldwork prep begins.

Continue: [[07-Phase-9-10-Pretest-Fieldwork]]
