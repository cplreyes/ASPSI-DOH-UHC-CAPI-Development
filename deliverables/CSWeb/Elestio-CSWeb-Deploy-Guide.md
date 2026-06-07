---
title: "CSWeb on Elestio (Managed LAMP) — Deploy Guide"
category: deliverable
tags: [capi, cspro, csweb, deployment, elestio, lamp, managed, vps, tls, e4-csweb-001, e4-csweb-002]
last_updated: 2026-06-02
status: deployed
---

# CSWeb on Elestio (Managed LAMP) — Deploy Guide

Companion to [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSWeb/CSWeb-on-VPS-Setup-Runbook|CSWeb on a Linux VPS — Provisioning & Install Runbook]]. That runbook stands CSWeb up on a **bare Ubuntu VPS** (manual LAMP, manual certbot). **This guide is the Elestio managed-LAMP path** that ASPSI approved on 2026-06-01 — most of the bare-VPS hardening/LAMP/TLS steps become the platform's job, and the CSWeb install adapts to Elestio's Docker-packaged LAMP layout.

> [!important] Decision of record (2026-06-01)
> ASPSI approved hosting on **Elestio (fully managed)**, **4 GB base / 2 vCPU / ~100 GB, Singapore (Vultr)**, ~₱2,800/mo, resizable to 8 GB on demand. Account is under ASPSI's own email **`aspsi.doh.uhc.survey2.data@gmail.com`**. Domain is **`csweb.asiansocial.org`** as a subdomain of ASPSI's existing **`asiansocial.org`** (ASPSI controls the DNS; no purchase). Approval thread: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/comms/email-juvy-vps-specs|email-juvy-vps-specs]].

> [!success] Deployment record — 2026-06-02 (LIVE)
> CSWeb **8.0.1** installed and verified on `aspsi-csweb-prod` (Vultr Singapore, `207.148.65.115`). Live at **`https://aspsi-csweb-prod-u73907.vm.elestio.app/csweb/`** — admin login + OAuth `/token` endpoint both confirmed working. Custom domain **`csweb.asiansocial.org` LIVE 2026-06-03** (ASPSI A record → 207.148.65.115; domain added in Elestio dashboard; Let's Encrypt cert auto-issued; `API_URL` repointed — see below). Secrets in `/root/csweb-db-credentials.txt` (root-only, not in git). Operated over SSH (key-based); the Elestio MCP was not used.
>
> **Four deviations from the steps below — apply these next time:**
> 1. **Dead base image.** Elestio's LAMP template pins `php:8.1-apache-buster` (Debian 10, EOL → apt repos 404, build fails). Fix: set `SOFTWARE_VERSION_TAG=8.1-apache-bookworm` in `/opt/app/.env`, then `docker compose up -d --build`. PHP 8.1 on bookworm already bundles every required extension (`pdo_mysql, curl, mbstring, dom, zip, fileinfo, openssl, gd`) — **no extension rebuild needed**.
> 2. **App stack ships down.** On creation, only `elestio-nginx`/`elestio-postfix` run; the LAMP services (`webserver`/`database`/`phpmyadmin`) are defined but not started. Bring them up: `cd /opt/app && docker compose up -d`.
> 3. **Real layout.** Web root = `/opt/app/lamp/www` (→ container `/var/www/html`). DB host = **`database`** (compose service name; container `lamp-mysql8`, MySQL **8.4**), DB user `csweb_user`@`'%'`. Apache vhost already has `AllowOverride all` + `mod_rewrite`.
> 4. **Trigger-creation blocked.** MySQL 8.4 + GTID rejects `CREATE TRIGGER` by a non-SUPER user (error **1419**), so the wizard dies after the first table. Fix once as root **before** running the wizard: `SET PERSIST log_bin_trust_function_creators = 1;` (durable, keeps `csweb_user` least-privilege).
> 5. **Mixed-content / reverse-proxy HTTPS (post-install — silently breaks user mgmt + all AJAX).** Elestio terminates SSL and forwards plain HTTP to the container (`$_SERVER['HTTPS']` unset, `SERVER_PORT=80`) while sending `X-Forwarded-Proto: https`. CSWeb then builds `http://` AJAX URLs that the HTTPS page blocks as **mixed content** — symptom: *"Add User does nothing"* and an empty user table (the `users/json` and `users/` POST are both blocked; console shows `Mixed Content … has been blocked`). Fix: in the Apache vhost `/opt/app/lamp/config/vhosts/default.conf` add `SetEnvIf X-Forwarded-Proto "https" HTTPS=on`, then `docker restart lamp-php8`. Host-agnostic — also covers `csweb.asiansocial.org` after the domain cutover. **(Applied 2026-06-02; verified create/list/delete user via browser.)**
>
> **Download URL (corrected):** `https://www.csprousers.org/releases/8.0/csweb-8.0.1.zip` — the `/downloads/releases/...` path 404s, and the CDN throttles datacenter IPs (the VPS got 503), so fetch it on a local/residential machine and `scp` to the box. Writable dirs the wizard requires: `var`, `app/config`, **`src/AppBundle`** (chown to uid `33`).
>
> **Wizard.** `setup/configure.php` is a single tokenless POST (completable via curl). Its final step live-tests `<apiurl>/token`, so `apiurl` must resolve with a **valid cert at setup time** → configured on the elestio.app hostname first.
>
> **Domain repoint (when `csweb.asiansocial.org` resolves + has its cert):** edit `src/AppBundle/config.php` → `define('API_URL', 'https://csweb.asiansocial.org/csweb/api/');`. That file is the *only* place the URL is persisted — no reconfigure, no table drop, no wizard re-run.

> [!note] What Elestio replaces vs the bare-VPS runbook
> - **Replaced by the platform:** Part 2 hardening (firewall, fail2ban, unattended-upgrades, swap), Part 3 manual LAMP install, **Part 5 certbot/TLS** (Elestio auto-issues + renews Let's Encrypt), and backups/monitoring.
> - **Still needed (this guide):** placing the CSWeb app into the LAMP web root, creating its database + dedicated user, running the `/csweb/setup` wizard, pointing the domain.
> - **Key inversion:** on the bare VPS, MySQL is `localhost` and bound to `127.0.0.1`. On Elestio the app and DB are **separate containers**, so the DB host is the **MySQL service name** and the CSWeb DB user is scoped `'@'%'`, not `'@localhost'`.

---

## Prerequisites (Carl-side, before Step 4)

1. **CSPro Designer version check** — confirm F1/F3/F4 were built on **CSPro 8.0.x** so they match **CSWeb 8.0.1** (bare-VPS runbook Part 0.2). This is independent of hosting.
2. **Re-check the current stable CSWeb release** at [csprousers.org/downloads](https://csprousers.org/downloads/) on execution day — install the current stable that matches the Designer line (8.0.1 unless a stable 8.1.x has shipped).
3. **DNS access to `asiansocial.org`** — ability to add one record (Step 5). ASPSI controls this.

---

## Step 1 — Create the ASPSI Elestio account

1. Go to **elest.io** → **Sign up**.
2. Use **`aspsi.doh.uhc.survey2.data@gmail.com`** — "Sign up with Google" (cleanest for a Gmail) or email + password.
3. Verify the email if prompted.

> The Elestio MCP connected to Carl's tooling is authenticated as the **personal** `carlpatricklreyes@gmail.com` account and **cannot drive this ASPSI account** via API. This account is operated by browser + SSH unless its own API token is later added to the MCP config (optional — see end).

## Step 2 — Project + billing

4. Create a **project** (e.g. `ASPSI-UHC`).
5. **Add a payment method** under Billing — this account is charged ~₱2,800/mo. Whoever covers it (ASPSI directly per Juvy's offer, or Carl billing through) adds the card here. The first **Elestio invoice** generated here is the "billing/supporting document" Juvy requested.

## Step 3 — Deployment approach (locked)

**Managed LAMP service** (Apache + PHP 8.1 + MySQL/MariaDB, managed). Chosen over a bare Ubuntu VM because (a) it honors the fully-managed plan ASPSI approved, and (b) a bare VM on Elestio means paying the managed premium without using it — raw Vultr/DO would be cheaper for a self-managed box.

## Step 4 — Create the LAMP service

Dashboard → **Create Service**:

| Field | Choose |
|---|---|
| Software / template | **LAMP** (Apache + PHP 8.1 + MySQL/MariaDB) |
| Cloud provider | **Vultr** (matches pricing + confirmed Singapore DC) |
| Region | **Singapore** |
| Service plan | **MEDIUM-2C-4G** — 4 GB / 2 vCPU / ~100 GB (~$48/mo); resizes to 8 GB in one click |
| Support level | default/included tier |
| Service name | `aspsi-csweb-prod` |

**Create** → wait ~5–10 min for **Running**.

## Step 5 — Point the domain (replaces runbook Part 5)

Service → **Domains / Custom domain** → add **`csweb.asiansocial.org`**. Elestio shows a DNS target (CNAME to its `…vm.elestio.app` hostname, or an A record to the IP).

→ In **`asiansocial.org`'s DNS** (ASPSI), add exactly that record. Elestio then **auto-issues Let's Encrypt SSL** once DNS resolves — no certbot, no manual cert, auto-renewal handled.

## Step 6 — Read connection details off the live service

Once **Running**, from the dashboard note: the **App URL**, **MySQL credentials** (env/credentials panel), and the **Terminal / SSH** access. These feed Step 7.

## Step 7 — Install CSWeb on the LAMP service

> Values in `<brackets>` are confirmed on the box at 7.2.

**7.1 — Open a shell.** Service → **Terminal** (web SSH), or SSH as `root` with the dashboard key.

**7.2 — Read the actual layout** (replaces the runbook's placeholders):
```bash
cd /opt/app && ls -la
cat docker-compose.yml      # → the web-root volume mount + the MySQL service name
cat .env 2>/dev/null        # → DB root/app passwords, if stored here
```
Gives: **(a)** `<webroot>` (host dir mounted as Apache's web root), **(b)** `<mysql-service>` (e.g. `mysql`/`db`) + root password.

**7.3 — Drop CSWeb into the web root:**
```bash
cd <webroot>
curl -fL -o csweb.zip "https://csprousers.org/downloads/releases/8.0/csweb-8.0.1.zip"
unzip -q csweb.zip && mv csweb-8.0.1 csweb     # adjust to the extracted folder name
chown -R 33:33 csweb/var csweb/app             # PHP container's www-data is usually uid 33
chmod -R 775 csweb/var csweb/app
```

**7.4 — PHP extensions (Docker divergence).** You **cannot** `apt install php-*` on the host — PHP runs in a container. CSWeb needs `pdo_mysql, curl, mbstring, xml, zip, fileinfo, openssl`. If the wizard (7.6) flags any missing, add them by editing the LAMP **Dockerfile/compose** (`docker-php-ext-install pdo_mysql mbstring zip …`) and redeploying via Elestio — **not** host apt. Many are pre-baked; confirm at 7.6.

**7.5 — Create the database + dedicated user:**
```bash
docker compose exec <mysql-service> mysql -u root -p
```
```sql
CREATE DATABASE csweb_uhc_y2 CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
CREATE USER 'csweb_user'@'%' IDENTIFIED BY '<strong-password>';
GRANT ALL PRIVILEGES ON csweb_uhc_y2.* TO 'csweb_user'@'%';
FLUSH PRIVILEGES;
```
> `'@'%'` (not `localhost`) because the app and DB are separate containers. The DB user is still scoped to **only** `csweb_uhc_y2` (least privilege) — that rule from the bare-VPS runbook holds.

**7.6 — Run the setup wizard:** browse `https://csweb.asiansocial.org/csweb/setup`

| Wizard field | Value |
|---|---|
| Database host | **`<mysql-service>`** (the container name — **not** `localhost`) |
| Database name | `csweb_uhc_y2` |
| Database user | `csweb_user` — **not root** |
| Database password | `<strong-password>` |
| CSWeb admin password | a **distinct** secret (not any DB password) |
| API URL | **`https://csweb.asiansocial.org/csweb/api`** (live HTTPS, never localhost) |

Clear any red prerequisite via 7.4, then re-run until "Setup Complete!".

## Step 8 — Verify (from a non-server device)

- `https://csweb.asiansocial.org/csweb/` → admin login renders with a **valid padlock** (Elestio auto-SSL).
- `http://csweb.asiansocial.org/csweb/` → **auto-redirects to HTTPS**.
- `https://csweb.asiansocial.org/csweb/api/` → **not 404** (a CSWeb-generated response).
- `admin` logs in; dashboard loads.

This closes **E4-CSWeb-001** (server reachable over HTTPS with valid cert) and **E4-CSWeb-002** (CSWeb installed + admin account).

## Secrets to record (Carl's password manager — never in git)

- `<mysql-root-password>` (from 7.2 / dashboard)
- `<strong-password>` for `csweb_user`
- CSWeb `admin` dashboard password (distinct from both)

---

## Out of scope here (S007 carry — do not execute now)

- **E4-CSWeb-003** — per-survey app upload (F1/F3/F4 `.pen` via CSPro Designer **Deploy Application**).
- **E4-CSWeb-004** — enumerator users + UHC role matrix.
- **E4-CSWeb-005** — field-tablet sync config against `https://csweb.asiansocial.org/csweb/api` (gates `E3-F1-088`).

See the bare-VPS runbook's "What's next (S007 carry)" for detail — those steps are host-agnostic.

## Open items / verify-on-box

1. **Exact LAMP layout** — `<webroot>` path, `<mysql-service>` name, and whether the bundled DB is MySQL or MariaDB are read at 7.2; the rest of Step 7 adapts to them.
2. **PHP extension completeness** — the wizard prereq page (7.6) is the authority; gaps are fixed via the container image (7.4), not host apt.
3. **Resize lever** — the 4 GB base resizes to 8 GB in-dashboard for heavier setup sessions or peak fieldwork; swap is host-managed on Elestio (the bare-VPS swap step does not apply here).
4. **Optional MCP automation** — to let Carl's tooling deploy/log/back up this ASPSI server directly, add the ASPSI account's Elestio API token to the MCP config (separate setup).
