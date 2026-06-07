---
title: "CSWeb on a Linux VPS — Provisioning & Install Runbook"
category: deliverable
tags: [capi, cspro, csweb, deployment, vps, linux, ubuntu, tls, sprint-006, e4-csweb-001, e4-csweb-002]
last_updated: 2026-06-01
status: draft
---

# CSWeb on a Linux VPS — Provisioning & Install Runbook

This runbook stands up the CSWeb server backplane for the ASPSI-DOH UHC Year 2 CAPI track (F1 Facility Head / F3 Patient / F4 Household) on a fresh Ubuntu VPS. It covers Sprint 006 Goal D tasks **E4-CSWeb-001** (VPS provisioning — host, OS, network, TLS) and **E4-CSWeb-002** (CSWeb install + admin account).

It is the **Linux/Ubuntu equivalent** of the Windows + Wampserver path in [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/UHC-Survey-CAPI-Guide/06-Phase-8-CSWeb-and-Tablets|06 — Phase 8: CSWeb and Tablets]] §§8.2–8.4. Every command here is Linux-native. The operational wisdom from the Phase-8 guide is preserved (dedicated non-root MySQL user, never expose 3306, DNS not raw IP, Let's Encrypt, the "sync URL must be the live URL not localhost" rule, setup-wizard gotchas, folder-permission notes) — only the commands changed platform. For CSWeb's feature surface, roles model and the Symfony break-out command, see [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSWeb|CSWeb concept page]].

> [!important] Execution model
> Carl provisions the VPS **after** this runbook is signed off. Once the box exists and Carl has SSHed in, a **Claude Code session running natively on the VPS (Linux)** executes Parts 2–6 step by step. The runbook is therefore written self-contained: a fresh on-VPS Claude can follow it with zero prior project context. Steps are tagged **[CARL — DECISION/INPUT]** (something Carl must supply or do off-box) or **[ON-VPS]** (a command the on-VPS Claude runs).

> [!note] Scope
> F2 (Healthcare Worker) is a separate Cloudflare Pages PWA and **does not sync through CSWeb** — out of scope here. This runbook ends at a verified CSWeb admin login over HTTPS. Uploading the F1/F3/F4 apps, creating enumerator users, and configuring tablet sync are S007 tasks E4-CSWeb-003/004/005 — see [What's next](#whats-next-s007-carry).

---

## Verified facts (sourced — do not substitute)

| Fact | Value | Source |
|---|---|---|
| Current CSWeb version | **8.0.1** (release tag `v8.0.1-2024-03-19`) | [CSPro Downloads](https://csprousers.org/downloads/), [csprousers/csweb releases](https://github.com/csprousers/csweb/releases) |
| Download artifacts | `csweb-8.0.1.zip` and `csweb-8.0.1.tar.gz` at `csprousers.org/downloads/releases/8.0/` | [CSPro Downloads](https://csprousers.org/downloads/) |
| Matched CSPro Designer | **8.0.1** (released 2024-03-19) | [CSPro Downloads](https://csprousers.org/downloads/) |
| PHP requirement | **PHP 8** required for CSWeb 8.x | [Introduction to CSWeb](https://www.csprousers.org/help/CSWeb/) |
| PHP modules (official README) | `fileinfo`, `pdo`, `pdo_mysql`, `curl`, `openssl` | [csprousers/csweb README](https://github.com/csprousers/csweb) |
| Database | MySQL 5.5.3+ (MySQL 8 / MariaDB 10.x both satisfy) | [csprousers/csweb README](https://github.com/csprousers/csweb) |
| Web server | Apache (or IIS) with URL-rewrite (`mod_rewrite`) | [Apache CSWeb Setup](https://www.csprousers.org/help/CSWeb/apache_csweb_setup.html) |
| Official install steps | (1) copy source to `www/csweb`; (2) make `var`, `var/logs`, `app` writable by web user; (3) create MySQL DB + user; (4) browse `/csweb/setup` wizard | [csprousers/csweb README](https://github.com/csprousers/csweb) |

> [!warning] Two ambiguities — verify on the box, do not guess
> 1. **The official docs explicitly state "the setup of an Apache server is beyond the scope of this document."** There is no Census-published Ubuntu command list. This runbook gives the **most-documented, standard LAMP approach** and assembles the PHP extension list from the CSWeb README plus the Ubuntu PHP packaging conventions — but the **CSWeb `/csweb/setup` wizard's own prerequisite-check page is the authority**. If it flags a red item, install that extension and re-run. Section 4.7 covers this loop.
> 2. **A CSWeb 8.1.0 alpha exists** (commit dated `alpha-2026-03-18`) but is **not a stable release**. Use **8.0.1** unless csprousers.org publishes a stable 8.1.x by execution day. Re-check [CSPro Downloads](https://csprousers.org/downloads/) at execution time — Part 0 makes this a checklist item.

---

## Part 0 — Prerequisites & inputs Carl must supply

Do not start Part 2 until every item below is settled. The first three are **hard blockers**.

### 0.1 HARD PREREQUISITE — a domain or subdomain

> [!warning] E4-CSWeb-001 cannot pass without a domain name
> E4-CSWeb-001's pass criterion is **"CSWeb reachable over HTTPS."** Let's Encrypt (and every other ACME CA) issues certificates **only to domain names, never to bare IP addresses.** A VPS with only a raw IP **cannot get a trusted TLS cert** and therefore **cannot satisfy E4-CSWeb-001.**
>
> **Carl must own or control a domain and be able to add a DNS `A` record before execution day.** A subdomain of any domain ASPSI already controls is fine — **for this deployment ASPSI confirmed `csweb.asiansocial.org` under its existing `asiansocial.org`.** If no domain exists, registering one is the first action — it is not optional, and it is not something the on-VPS Claude can do.
>
> This also matches the Phase-8 guide's "DNS not raw IP" rule (§8.4.2): IPs change; a hostname survives a VPS re-provision with one DNS edit instead of re-flashing every tablet's sync URL.

### 0.2 HARD PREREQUISITE — CSWeb version must match the CSPro Designer version used to build F1/F3/F4

CSWeb and the CSPro Designer that builds the `.pen`/`.dcf` artifacts should be the **same major.minor line**. The F1/F3/F4 generators in this project target CSPro 8.0.x; CSWeb 8.0.1 is the matched server.

**[CARL — DECISION/INPUT]** Before execution day, confirm the CSPro Designer version actually used to build the current F1/F3/F4 artifacts (check the Designer "About" dialog, or the `Version=` line in a generated `.pff`). Record it here:

- CSPro Designer version building F1/F3/F4: `__________` (expected: 8.0.x)
- CSWeb version to install: **8.0.1** (unless a stable 8.1.x has shipped — see warning above)

This is a **check, not a guess.** If the Designer version is not 8.0.x, stop and reconcile before installing.

### 0.3 HARD PREREQUISITE — the VPS exists and Carl can SSH in

Parts 2–6 run **on the VPS**. Carl provisions the box per the Part 1 spec sheet, then SSHes in as `root` (or the provider's initial user) and launches the on-VPS Claude Code session.

### 0.4 Inputs Carl supplies (placeholder table)

Every placeholder used in this runbook, in one place. Fill the right column before/at execution. Treat passwords as secrets — store them in a password manager, not in this file, not in git.

| Placeholder | What it is | Who decides | Example |
|---|---|---|---|
| `<your-domain>` | The FQDN CSWeb will live at | Carl (Part 0.1) | `csweb.asiansocial.org` |
| `<server-ip>` | The VPS public IPv4 | Provider, after provisioning | `203.0.113.45` |
| `<admin-user>` | Non-root Linux sudo user to create | Carl | `aspsi` |
| `<your-ssh-public-key>` | Carl's SSH public key (`.pub` contents) | Carl's workstation | `ssh-ed25519 AAAA...` |
| `<csweb-db-name>` | MySQL database name for CSWeb | Fixed by this runbook | `csweb_uhc_y2` |
| `<csweb-db-user>` | Dedicated non-root MySQL user | Fixed by this runbook | `csweb_user` |
| `<csweb-db-password>` | Password for `<csweb-db-user>` | Carl — generate strong | (32-char random) |
| `<mysql-root-password>` | MySQL root password | Carl — generate strong | (32-char random) |
| `<csweb-admin-password>` | CSWeb dashboard `admin` password — **distinct from every DB password** | Carl — generate strong | (16+ char random) |
| `<letsencrypt-email>` | Email for Let's Encrypt expiry notices | Carl | `aspsi.doh.uhc.survey2.data@gmail.com` |
| `<csweb-version>` | CSWeb release to install | Part 0.2 | `8.0.1` |

> [!warning] Three different passwords — do not conflate them
> `<mysql-root-password>`, `<csweb-db-password>`, and `<csweb-admin-password>` are **three separate secrets**. The Phase-8 guide flags this explicitly (§8.3.4): the MySQL root password administers the database engine; the CSWeb DB-user password is what the CSWeb PHP app authenticates to MySQL with; the CSWeb admin password is the human login to the `/csweb` dashboard. Reusing one for another collapses two trust boundaries into one. Generate all three independently.

### 0.5 Generating strong passwords

On the VPS (once it exists), the on-VPS Claude can generate secrets with:

```bash
openssl rand -base64 24
```

Run it three times, hand the three values to Carl to store in his password manager, and use them where the placeholders appear.

---

## Part 1 — VPS spec sheet (E4-CSWeb-001 inputs)

**[CARL — DECISION/INPUT]** This is the spec Carl hands to whatever VPS provider he picks. The runbook is **provider-agnostic** — it does not assume DigitalOcean, Linode, Vultr, AWS, or any other host. Any provider that offers an Ubuntu LTS image and a public IPv4 works.

### 1.1 Minimum spec

| Resource | Starting minimum | Comfortable for fieldwork | Notes |
|---|---|---|---|
| RAM | **2 GB** | 4 GB | CSWeb is a light PHP/MySQL app. 2 GB is fine for install + initial use. 50 tablets syncing nightly **plus** the `csweb:process-cases` relational break-out cron warrant 4 GB — see 1.3. |
| vCPU | **2** | 2–4 | Apache + MySQL + PHP-CLI cron share these. |
| SSD storage | **~50 GB** | 80–100 GB | Case-blob tables, sync logs, uploaded photos and backups all grow over an 8-region fieldwork. SSD (not spinning disk) matters when the Data tab queries live. |
| OS image | **Ubuntu Server 24.04 LTS** | same | 24.04 LTS ("Noble Numbat") is the current Ubuntu LTS. Ships PHP 8.3, which satisfies CSWeb's PHP 8 requirement. Use Server (no desktop). |
| Region / PoP | **Singapore** | same | Closest major cloud PoP to the Philippines — lowest sync latency for field tablets. Pick the provider's Singapore datacenter. |
| Public IPv4 | **1, static** | same | Required for the DNS `A` record. Most VPS plans include one. |
| Bandwidth | Provider default (≥1 TB/mo typical) | same | Tablets push small case blobs; bandwidth is not the constraint. |

### 1.2 Why these numbers

CSWeb is intentionally lightweight — PHP + MySQL, no heavy runtime. The Phase-8 guide's Windows spec (§8.2.1) recommends 4 GB / 8 GB because Wampserver on Windows carries the OS overhead of a desktop Windows install. A headless Ubuntu Server VPS has far less baseline overhead, so **2 GB / 2 vCPU / 50 GB is a genuinely comfortable starting minimum** for install and early use.

### 1.3 Resize-later guidance

**A VPS resizes in minutes** (a reboot on most providers) — RAM and vCPU can be bumped without rebuilding the box. So **starting at the 2 GB minimum is fine.** Plan to **bump to 4 GB before main fieldwork** when (a) ~50 tablets sync nightly around the 10 PM mandate and (b) the relational break-out cron runs concurrently. Storage usually also resizes, but is harder to shrink — if unsure, start at 50 GB and grow.

> [!important] Approved spec (2026-06-01)
> ASPSI approved provisioning on **Elestio (fully managed), 4 GB base, 2 vCPU, 80 GB, Singapore**, resizable to 8 GB on demand, with the domain **`csweb.asiansocial.org`** under ASPSI's existing `asiansocial.org` (no purchase — ASPSI controls the DNS). The 4 GB base carries a **swap file (Part 2.8)** as its OOM safety net; resize to 8 GB for heavier on-VPS setup sessions or peak fieldwork, then resize back down.

### 1.4 What Carl does with this section

1. Pick a provider.
2. Provision **1 Ubuntu Server 24.04 LTS instance**, **Singapore region**, **2 GB RAM / 2 vCPU / 50 GB SSD** (or 4 GB if budget allows starting there).
3. Add **Carl's SSH public key** during creation (most providers offer this at provision time — strongly preferred over a root password).
4. Record the assigned **public IPv4** into the Part 0.4 table as `<server-ip>`.
5. **[CARL — DECISION/INPUT]** At the DNS provider, add an `A` record: `<your-domain>` → `<server-ip>`. Do this **now** — DNS propagation (15 min–24 h) runs in the background while Parts 2–3 execute, so the cert step in Part 5 isn't blocked waiting.
6. SSH in and start the on-VPS Claude Code session.

**Verification gate:** From Carl's workstation, `ssh root@<server-ip>` (or the provider's initial user) succeeds and lands at a shell prompt. If not — check the provider console for the correct initial username, confirm the SSH key was attached, confirm the instance is "running." Do not proceed until SSH works.

---

## Part 2 — Initial server hardening

**[ON-VPS]** Everything in Part 2 runs on the VPS. Start as `root` (or the provider's sudo-capable initial user).

### 2.1 System update

```bash
apt update && apt upgrade -y
```

**Verification gate:** Command finishes without errors. If a kernel was upgraded, the runbook will reboot at the end of Part 2 — note it now.

### 2.2 Create a non-root sudo user

Replace `<admin-user>` with the value from Part 0.4.

```bash
adduser <admin-user>
usermod -aG sudo <admin-user>
```

`adduser` prompts for a password — set a strong one and have Carl store it. Then install Carl's SSH key for that user so key-auth works after password login is disabled:

```bash
mkdir -p /home/<admin-user>/.ssh
echo "<your-ssh-public-key>" > /home/<admin-user>/.ssh/authorized_keys
chmod 700 /home/<admin-user>/.ssh
chmod 600 /home/<admin-user>/.ssh/authorized_keys
chown -R <admin-user>:<admin-user> /home/<admin-user>/.ssh
```

**Verification gate:** From a **second terminal on Carl's workstation** (keep the current root session open as a safety net), run `ssh <admin-user>@<server-ip>`. It must log in **without asking for a password** (key auth) and `sudo whoami` must return `root`. If either fails, fix it **before** Section 2.3 — disabling root/password login while locked out bricks the box.

### 2.3 Harden SSH — key-only, no root login

Edit `/etc/ssh/sshd_config`:

```bash
sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sshd -t && systemctl restart ssh
```

`sshd -t` validates the config before the restart — if it prints errors, the restart is skipped; fix the file and re-run.

**Verification gate:** From Carl's workstation, `ssh <admin-user>@<server-ip>` still works via key. `ssh root@<server-ip>` is now **rejected**. If the admin user can no longer get in, use the still-open root session (or the provider's web console) to revert.

### 2.4 Firewall — ufw, allow only 22/80/443

```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
ufw status verbose
```

**Verification gate:** `ufw status verbose` shows `Status: active` and exactly three allowed inbound services — 22 (OpenSSH), 80, 443. **Port 3306 (MySQL) must not appear** — MySQL stays localhost-only (Part 3). This is the Linux equivalent of the Phase-8 firewall table (§8.4.3).

### 2.5 fail2ban — block SSH brute-force

```bash
apt install -y fail2ban
systemctl enable --now fail2ban
fail2ban-client status sshd
```

**Verification gate:** `fail2ban-client status sshd` prints a jail status block (currently-banned count of 0 is expected on a fresh box).

### 2.6 Unattended security upgrades

```bash
apt install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades
```

**Verification gate:** `systemctl status unattended-upgrades` shows the service `enabled`. `/etc/apt/apt.conf.d/20auto-upgrades` exists with `Unattended-Upgrade "1";`.

### 2.7 Timezone and hostname

The project runs in the Philippines; the Phase-8 sync mandate is 10 PM **local** time. Set the box to Manila time so logs and the break-out cron align with field operations.

```bash
timedatectl set-timezone Asia/Manila
hostnamectl set-hostname aspsi-csweb-prod
```

**Verification gate:** `timedatectl` shows `Time zone: Asia/Manila`. `hostnamectl` shows `Static hostname: aspsi-csweb-prod`.

### 2.8 Swap file — OOM safety net

The box runs on the **4 GB base spec** (Part 1), and during Parts 2–6 it carries the on-VPS Claude Code session alongside the LAMP stack. A small swap file gives the kernel an out-of-memory safety net: a transient memory spike degrades to a brief slowdown instead of an OOM-killed process (MySQL or the Claude session). This is standard hardening on a small VPS and is **not optional at 4 GB**.

Create a 4 GB swap file (the `||` falls back to `dd` if the filesystem doesn't support `fallocate`):

```bash
sudo fallocate -l 4G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=4096
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

Persist it across reboots (the `grep` guard avoids a duplicate fstab line on a re-run):

```bash
grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

Tune the box to prefer RAM and treat swap as a fallback, and persist the setting:

```bash
sudo sysctl vm.swappiness=10
echo 'vm.swappiness=10' | sudo tee /etc/sysctl.d/99-swappiness.conf
```

**Verification gate:**

```bash
swapon --show                  # lists /swapfile, TYPE file, SIZE 4G
free -h                        # the Swap row shows ~4.0Gi total
cat /proc/sys/vm/swappiness    # 10
```

`swapon --show` must list `/swapfile` and `free -h` must show ~4 Gi of swap. If `free -h` shows `0B` swap, `swapon /swapfile` did not take — re-check the `mkswap` / `swapon` steps.

> [!note] For heavier on-VPS Claude sessions
> Swap protects against spikes but is slow if leaned on hard. If a setup/config session does memory-intensive work, **resize the instance to 8 GB for that window** (Elestio and most providers resize in minutes), then resize back to the 4 GB base afterward — paying the higher rate only while needed.

### 2.9 Reboot if the kernel was updated

```bash
[ -f /var/run/reboot-required ] && echo "REBOOT NEEDED" || echo "no reboot needed"
```

If it prints `REBOOT NEEDED`, run `reboot`, wait ~60 s, and `ssh <admin-user>@<server-ip>` back in before continuing.

---

## Part 3 — LAMP stack

**[ON-VPS]** Run as `<admin-user>` with `sudo`.

### 3.1 Apache

```bash
sudo apt install -y apache2
sudo a2enmod rewrite
sudo systemctl enable --now apache2
```

`a2enmod rewrite` enables `mod_rewrite` — **CSWeb requires URL rewrite** ([Apache CSWeb Setup](https://www.csprousers.org/help/CSWeb/apache_csweb_setup.html)). On Ubuntu this is one command; it is the Linux equivalent of uncommenting `LoadModule rewrite_module` in `httpd.conf`.

**Verification gate:** From Carl's workstation browser, visit `http://<server-ip>` — the Apache2 Ubuntu default page renders. If not, check `sudo systemctl status apache2` and that ufw allows port 80.

### 3.2 Database — MySQL 8

**Decision: MySQL 8** (not MariaDB). Justification: CSWeb's documentation, the official README, and the Phase-8 Windows guide all reference **MySQL** by name; MySQL 8 is the Ubuntu 24.04 default `mysql-server` package and the path with the least divergence from CSWeb's tested matrix. MariaDB would almost certainly work (CSWeb only needs MySQL-protocol 5.5.3+ semantics), but choosing the explicitly-named engine removes one variable from any future support question.

```bash
sudo apt install -y mysql-server
sudo systemctl enable --now mysql
```

Secure the installation:

```bash
sudo mysql_secure_installation
```

Answer the prompts: set the root password to `<mysql-root-password>`, remove anonymous users **yes**, disallow remote root login **yes**, remove test database **yes**, reload privileges **yes**.

**Bind MySQL to localhost only** — it must never accept external connections (Phase-8 §8.4.3, "3306 — Localhost only — never expose externally"):

```bash
sudo sed -i 's/^bind-address.*/bind-address = 127.0.0.1/' /etc/mysql/mysql.conf.d/mysqld.cnf
sudo grep -q '^mysqlx-bind-address' /etc/mysql/mysql.conf.d/mysqld.cnf && \
  sudo sed -i 's/^mysqlx-bind-address.*/mysqlx-bind-address = 127.0.0.1/' /etc/mysql/mysql.conf.d/mysqld.cnf
sudo systemctl restart mysql
```

**Verification gate:** `sudo ss -tlnp | grep 3306` shows MySQL listening on `127.0.0.1:3306` **only** — not `0.0.0.0:3306`. The dedicated CSWeb DB user and database are created in Part 4 (Section 4.4), after the CSWeb files are in place.

### 3.3 PHP 8 and the extensions CSWeb needs

Ubuntu 24.04 ships PHP 8.3, which satisfies CSWeb 8.x's PHP 8 requirement. Install PHP, the Apache module, and every extension CSWeb needs. The list combines the official `csprousers/csweb` README modules (`fileinfo`, `pdo`, `pdo_mysql`, `curl`, `openssl`) with the standard CSWeb/Symfony web-app extensions (`mbstring`, `xml`, `zip`):

```bash
sudo apt install -y \
  php php-cli libapache2-mod-php \
  php-mysql php-curl php-mbstring php-xml php-zip
```

Notes on the list:
- `php-mysql` provides **`pdo_mysql`** — CSWeb's database driver.
- `fileinfo`, `pdo`, `openssl`, `curl` are compiled into mainline Ubuntu PHP 8.3 or covered by `php-curl`; `mbstring`, `xml`, `zip` are explicit packages.
- The **authority on completeness is the CSWeb setup wizard's prerequisite-check page** (Section 4.7). If it flags a missing extension, `sudo apt install php-<name>` and `sudo systemctl reload apache2`, then re-run the wizard.

Reload Apache so it picks up PHP:

```bash
sudo systemctl reload apache2
```

**Verification gate — PHP version:**

```bash
php -v
```
Must report **PHP 8.x** (8.3 on 24.04).

**Verification gate — extensions loaded:**

```bash
php -m | grep -E '^(pdo_mysql|curl|mbstring|xml|fileinfo|openssl|zip)$' | sort
```
Should list all seven. Any missing one → install its `php-*` package and re-check.

**Verification gate — Apache executes PHP:**

```bash
echo "<?php phpinfo();" | sudo tee /var/www/html/info.php >/dev/null
```
Visit `http://<server-ip>/info.php` — the PHP info page renders (not raw source, not a download prompt). Then **delete it immediately** — `phpinfo()` leaks server detail:

```bash
sudo rm /var/www/html/info.php
```

---

## Part 4 — CSWeb install (E4-CSWeb-002)

**[ON-VPS]** Run as `<admin-user>` with `sudo`. This installs **CSWeb `<csweb-version>`** (8.0.1 per Part 0.2).

### 4.1 Confirm the version before downloading

> [!warning] Re-verify at execution time
> The verified current release is **CSWeb 8.0.1** (`csweb-8.0.1.zip`). Before downloading, the on-VPS Claude should re-check [csprousers.org/downloads](https://csprousers.org/downloads/) for whether a **stable 8.1.x** has shipped. Install the current **stable** release that matches the F1/F3/F4 Designer line (Part 0.2). If 8.0.1 is still current, proceed with the URL below.

### 4.2 Download and extract into the Apache web root

CSWeb's official install step 1 is "copy the source code to your www directory so you have `www/csweb`" ([csprousers/csweb README](https://github.com/csprousers/csweb)). On Ubuntu the Apache web root is `/var/www/html`, so the target is `/var/www/html/csweb`.

```bash
cd /tmp
curl -fL -o csweb.zip "https://csprousers.org/downloads/releases/8.0/csweb-8.0.1.zip"
sudo apt install -y unzip
unzip -q csweb.zip -d /tmp/csweb-extract
```

Inspect what the archive expanded to (the top-level folder name can vary by release), then move it to the web root as `csweb`:

```bash
ls /tmp/csweb-extract
# Move the CSWeb application root to /var/www/html/csweb.
# If the archive expanded directly to files, adjust the source path accordingly.
sudo mv /tmp/csweb-extract/csweb-8.0.1 /var/www/html/csweb
```

> [!note] Folder name discipline
> The folder **must be `csweb`**, all lowercase. The official Apache CSWeb Setup page warns: *"CSWeb and csweb will require different URLs to access the server. For simplicity, we recommend using all lowercase e.g. csweb."* Every URL in this runbook, every tablet's recorded sync URL, and the URL in the Designer Deploy wizard all encode this folder name. Pick `csweb` and never change it.

**Verification gate:** `ls /var/www/html/csweb` shows the CSWeb application tree (expect directories such as `app`, `var`, `public`/`web`, `setup`). If instead you see a single nested `csweb-8.0.1` folder, you moved one level too high — move the inner directory.

### 4.3 File ownership and permissions for the Apache user

On Ubuntu the Apache process runs as the **`www-data`** user. CSWeb's official install step 2: the **`var`, `var/logs`, and `app` directories must be writable by the web-server user** ([csprousers/csweb README](https://github.com/csprousers/csweb)). This is the Linux equivalent of the Phase-8 note that `config\` and `files\` must be writable by the Apache `LocalSystem` user (§8.3.6).

Give the whole tree to `www-data` and set sane permissions:

```bash
sudo chown -R www-data:www-data /var/www/html/csweb
sudo find /var/www/html/csweb -type d -exec chmod 755 {} \;
sudo find /var/www/html/csweb -type f -exec chmod 644 {} \;
```

Ensure the runtime-writable directories exist and are writable (the `app` directory may not be present until setup runs — create it so the wizard can write config):

```bash
sudo mkdir -p /var/www/html/csweb/var/logs /var/www/html/csweb/app
sudo chown -R www-data:www-data /var/www/html/csweb/var /var/www/html/csweb/app
sudo chmod -R 775 /var/www/html/csweb/var /var/www/html/csweb/app
```

**Verification gate:**
```bash
sudo -u www-data test -w /var/www/html/csweb/var && echo "var writable OK"
sudo -u www-data test -w /var/www/html/csweb/app && echo "app writable OK"
```
Both must print `OK`. If not, the setup wizard will fail to save its config — fix ownership before continuing.

### 4.4 Create the CSWeb database and a dedicated non-root MySQL user

> [!warning] Never let the web app authenticate as MySQL root
> The Phase-8 guide is explicit (§8.3.3): the demo videos use `root` for simplicity, but **for production CSWeb must connect with a dedicated, least-privilege MySQL user** scoped to only its own database. The on-VPS Claude creates `<csweb-db-user>` here.

```bash
sudo mysql
```

At the `mysql>` prompt, run (substituting the Part 0.4 values):

```sql
CREATE DATABASE csweb_uhc_y2 CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
CREATE USER 'csweb_user'@'localhost' IDENTIFIED BY '<csweb-db-password>';
GRANT ALL PRIVILEGES ON csweb_uhc_y2.* TO 'csweb_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

`GRANT ALL ... ON csweb_uhc_y2.*` scopes the user to **only** that database — it cannot touch other schemas. The database name `csweb_uhc_y2` carries the project-and-year prefix so a future second project on the same box cannot collide (Phase-8 §8.3.3).

**Verification gate:** Confirm the dedicated user can log in and see its database:
```bash
mysql -u csweb_user -p'<csweb-db-password>' -e "SHOW DATABASES;" | grep csweb_uhc_y2
```
Must print `csweb_uhc_y2`. (For a real run, prefer `mysql -u csweb_user -p` and type the password at the prompt so it stays out of shell history.)

### 4.5 Apache virtualhost for the domain

Create a virtualhost so Apache serves CSWeb under `<your-domain>`. This also positions the site for the certbot step in Part 5.

```bash
sudo tee /etc/apache2/sites-available/csweb.conf >/dev/null <<'EOF'
<VirtualHost *:80>
    ServerName <your-domain>
    DocumentRoot /var/www/html

    <Directory /var/www/html/csweb>
        Options FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/csweb_error.log
    CustomLog ${APACHE_LOG_DIR}/csweb_access.log combined
</VirtualHost>
EOF
```

Edit the file to replace `<your-domain>` with the real FQDN (the heredoc is single-quoted so it wrote the literal placeholder):

```bash
sudo sed -i 's/<your-domain>/csweb.asiansocial.org/' /etc/apache2/sites-available/csweb.conf
```

`AllowOverride All` lets CSWeb's `.htaccess` rewrite rules take effect — required because CSWeb depends on `mod_rewrite`. Enable the site and disable the Apache default:

```bash
sudo a2ensite csweb.conf
sudo a2dissite 000-default.conf
sudo apache2ctl configtest && sudo systemctl reload apache2
```

**Verification gate:** `apache2ctl configtest` prints `Syntax OK`. From Carl's workstation, `http://<your-domain>/csweb/` (once DNS has propagated) reaches the CSWeb app — likely a redirect to `/csweb/setup` or a not-yet-configured page. If DNS hasn't propagated yet, test with the host header instead:
```bash
curl -s -H "Host: <your-domain>" http://localhost/csweb/setup -o /dev/null -w "%{http_code}\n"
```
A `200` or `3xx` (not `404`/`500`) means Apache is serving CSWeb.

### 4.6 Run the CSWeb web setup wizard

CSWeb's official install step 4: browse to `/csweb/setup` and follow the wizard ([csprousers/csweb README](https://github.com/csprousers/csweb)).

**[CARL — DECISION/INPUT]** The wizard is a browser flow — Carl drives it from his workstation browser; the on-VPS Claude cannot click through a GUI. Once DNS has propagated, Carl visits:

```
http://<your-domain>/csweb/setup
```

(HTTP for now — HTTPS comes in Part 5. If DNS hasn't propagated, the on-VPS Claude can confirm wizard reachability via the `curl` host-header test in 4.5; Carl still needs DNS live to complete the wizard from a browser.)

Wizard fields (from the official setup flow and Phase-8 §8.3.4) — Carl enters:

| Wizard field | Value |
|---|---|
| Database name | `csweb_uhc_y2` |
| Hostname | `localhost` |
| Database username | `csweb_user` — **not `root`** |
| Database password | `<csweb-db-password>` |
| CSWeb admin password | `<csweb-admin-password>` — **a distinct secret**, not any DB password |
| Path to files directory | `/var/www/html/csweb/files` (see note below) |
| CSWeb API URL | `https://<your-domain>/csweb/api` — see the warning below |

> [!warning] The API URL must be the live HTTPS URL, never localhost
> Phase-8 §8.4.5 calls this *"the single most-cited Phase 8 mistake."* The API URL entered here is what tablets call to sync. Enter the **final production URL** — `https://<your-domain>/csweb/api` — even though Part 5 (TLS) hasn't run yet. If you enter `localhost`, syncs work on the server and **fail in the field**, and the symptom only surfaces mid-fieldwork. The path suffix is literally `/api`. If the wizard rejects an `https://` URL because the cert doesn't exist yet, enter `http://<your-domain>/csweb/api`, complete Part 5, then return to the wizard or CSWeb's settings and switch it to `https://`.

> [!note] Files directory
> If `/var/www/html/csweb/files` does not exist, create it and hand it to the Apache user before running the wizard:
> ```bash
> sudo mkdir -p /var/www/html/csweb/files
> sudo chown www-data:www-data /var/www/html/csweb/files
> sudo chmod 775 /var/www/html/csweb/files
> ```

**Verification gate:** The wizard ends on a **"Setup Complete!"** page. If it does not — see Section 4.7.

### 4.7 Setup-wizard prerequisite loop (the authority on PHP extensions)

The wizard's **first page is a prerequisite check** — PHP version and required extensions. **This page, not this runbook, is the authoritative list.** If any item is red:

1. Note the missing extension name (e.g. `intl`, `gd`).
2. On the VPS: `sudo apt install php-<name>`
3. `sudo systemctl reload apache2`
4. Reload the wizard page — the item should now be green.
5. Repeat until all green, then proceed.

Other gotchas (Linux equivalents of Phase-8 §8.3.6):
- **Database wiring fails** → re-check the Section 4.4 verification (can `csweb_user` log in?), confirm `pdo_mysql` is in `php -m`.
- **"cannot write config"** → re-run the Section 4.3 writability gate; the `app` and `var` directories must be `www-data`-writable.
- **Blank page / 500 error** → `sudo tail -n 50 /var/log/apache2/csweb_error.log` for the PHP error.

### 4.8 Verify the CSWeb login (pre-TLS)

```
http://<your-domain>/csweb/
```

Log in as username **`admin`** with `<csweb-admin-password>`. The CSWeb dashboard should render. This confirms **E4-CSWeb-002's core** — full sign-off comes after TLS in Part 6.

**Verification gate:** `admin` login succeeds and the dashboard loads. If login fails, the admin password was set differently in the wizard — re-run the wizard or reset via CSWeb's documented procedure.

---

## Part 5 — TLS / HTTPS

**[ON-VPS]** This is what makes **E4-CSWeb-001** pass. Let's Encrypt issues only to domain names — Part 0.1's domain prerequisite is consumed here.

### 5.1 Confirm DNS resolves before requesting a cert

certbot's HTTP-01 challenge needs `<your-domain>` to resolve to this VPS.

```bash
dig +short <your-domain>
```

**Verification gate:** The output is `<server-ip>` — this VPS's public IP. If empty or a different IP, **stop** — DNS has not propagated, or the `A` record (Part 1.4 step 5) is wrong/missing. certbot will fail until this resolves. Wait and re-check; propagation can take up to 24 h but is usually under an hour.

### 5.2 Install certbot and issue the certificate

```bash
sudo apt install -y certbot python3-certbot-apache
sudo certbot --apache -d <your-domain> --non-interactive --agree-tos -m <letsencrypt-email> --redirect
```

What the flags do:
- `--apache` — certbot edits the Apache config directly and installs the cert.
- `-d <your-domain>` — the single domain to certify.
- `--redirect` — certbot adds the **HTTP→HTTPS redirect** so all port-80 traffic upgrades to 443 (Phase-8 §8.4.4 requires this).
- `-m <letsencrypt-email>` — expiry-notice address.

**Verification gate:** certbot prints `Congratulations!` / `Successfully received certificate`. It creates `/etc/apache2/sites-available/csweb-le-ssl.conf` (the :443 vhost) and reloads Apache. If it fails, the error is almost always the 5.1 DNS gate or ufw blocking port 80 — re-check both.

### 5.3 Confirm auto-renewal

certbot installs a systemd timer that renews certs before expiry. Confirm it and dry-run a renewal:

```bash
sudo systemctl status certbot.timer --no-pager
sudo certbot renew --dry-run
```

**Verification gate:** `certbot.timer` is `active`; the dry-run ends with `Congratulations, all simulations of the renewal succeeded`. No cron edit is needed — the timer handles it.

### 5.4 Switch the CSWeb API URL to HTTPS (if not already)

If Part 4.6 entered an `http://` API URL because the cert didn't exist yet, **[CARL — DECISION/INPUT]** Carl now updates it to `https://<your-domain>/csweb/api` via the CSWeb dashboard's settings (or by re-running `/csweb/setup`). The tablet sync URL must be HTTPS for fieldwork.

**Verification gate:** The configured API URL inside CSWeb begins with `https://`.

---

## Part 6 — Admin account & verification

**[CARL — DECISION/INPUT]** These checks run from a **non-server machine** (Carl's workstation or a phone) — the point is to prove the public surface works, not just localhost. This is the Linux equivalent of Phase-8 §8.4.6.

### 6.1 Dashboard renders over HTTPS

In a browser on a non-server machine, visit:
```
https://<your-domain>/csweb/
```
**Verification gate:** The CSWeb login page renders with a **valid padlock** — no certificate warning. Log in as `admin` / `<csweb-admin-password>`; the dashboard loads. If a cert warning appears, Part 5.2 did not install the cert correctly — re-check.

### 6.2 HTTP redirects to HTTPS

Visit:
```
http://<your-domain>/csweb/
```
**Verification gate:** The browser is **automatically redirected to `https://`**. Confirm from the command line:
```bash
curl -sI http://<your-domain>/csweb/ | grep -i location
```
The `Location:` header points at the `https://` URL. If not, re-run `sudo certbot --apache -d <your-domain> --redirect`.

### 6.3 The API endpoint returns a non-404 response

The path tablets sync against is `/csweb/api`. It must respond — a non-404 status, typically a small JSON-ish payload, not the Apache 404 page (Phase-8 §8.3.6, §8.4.6).

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://<your-domain>/csweb/api/
```
**Verification gate:** Status is **not 404** (commonly 200, or a 4xx auth challenge — anything CSWeb-generated rather than Apache's 404 confirms the API is reachable). A 404 means the folder name, the rewrite module, or `AllowOverride All` is wrong — re-check Sections 3.1, 4.2, 4.5.

### 6.4 Certificate is valid

```bash
echo | openssl s_client -connect <your-domain>:443 -servername <your-domain> 2>/dev/null \
  | openssl x509 -noout -issuer -dates
```
**Verification gate:** Issuer is **Let's Encrypt** and `notAfter` is ~90 days out. Browser padlock shows a valid cert.

### 6.5 CSWeb admin account confirmed

**Verification gate:** The `admin` account logs into `https://<your-domain>/csweb/` and the dashboard's tabs are visible. This is the **E4-CSWeb-002 admin-account criterion**.

> [!note] Record-keeping
> Once verified, confirm with Carl that `<csweb-admin-password>`, `<mysql-root-password>`, and `<csweb-db-password>` are all stored in his password manager. None of them belong in this file or in git.

---

## Part 7 — Exit criteria

### E4-CSWeb-001 — VPS provisioning (host / OS / network / TLS) — DONE when:

- [ ] VPS provisioned: Ubuntu Server 24.04 LTS, Singapore region, ≥2 GB RAM / 2 vCPU / ~50 GB SSD (Part 1)
- [ ] DNS `A` record `<your-domain>` → `<server-ip>` resolves correctly (Part 5.1 gate)
- [ ] Non-root sudo user created; SSH key-only auth; root login and password auth disabled (Part 2.2–2.3)
- [ ] `ufw` active, allowing only 22 / 80 / 443; port 3306 not exposed (Part 2.4)
- [ ] `fail2ban` and `unattended-upgrades` enabled (Part 2.5–2.6)
- [ ] Timezone `Asia/Manila`, hostname set (Part 2.7)
- [ ] Swap file (4 GB) active and persisted in `/etc/fstab`; `vm.swappiness` tuned to 10 (Part 2.8)
- [ ] Apache + MySQL 8 + PHP 8.x installed; MySQL bound to `127.0.0.1` only (Part 3)
- [ ] **CSWeb reachable over HTTPS with a valid Let's Encrypt cert; HTTP redirects to HTTPS; auto-renewal confirmed (Part 5, Part 6.1–6.2, 6.4)** ← the headline pass criterion

### E4-CSWeb-002 — CSWeb install + admin account — DONE when:

- [ ] CSWeb `<csweb-version>` (8.0.1) extracted to `/var/www/html/csweb`, owned by `www-data`, `var`/`app` writable (Part 4.2–4.3)
- [ ] Dedicated non-root MySQL user `csweb_user` scoped to database `csweb_uhc_y2` (Part 4.4)
- [ ] Apache virtualhost for `<your-domain>` serving CSWeb; `mod_rewrite` + `AllowOverride All` active (Part 3.1, 4.5)
- [ ] CSWeb setup wizard completed — "Setup Complete!"; API URL set to `https://<your-domain>/csweb/api` (Part 4.6, 5.4)
- [ ] CSWeb admin password set as a **secret distinct from both DB passwords** (Part 4.6)
- [ ] `admin` account logs into the CSWeb dashboard over HTTPS (Part 6.5)
- [ ] `/csweb/api/` returns a non-404 response (Part 6.3)
- [ ] All three passwords stored in Carl's password manager; none committed to git (Part 6.5 note)

---

## What's next (S007 carry)

This runbook stops at a verified, hardened, HTTPS-served CSWeb with a working admin login. The next CSWeb tasks are **out of scope here** — pointers only, do not execute:

- **E4-CSWeb-003** — Per-survey app upload: deploy the F1/F3/F4 `.pen` packages via CSPro Designer's **Deploy Application** wizard (the CSWeb dashboard's Apps tab is read-only — see [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSWeb|CSWeb concept page]] and Phase-8 §8.8). Registers each dictionary's backing tables.
- **E4-CSWeb-004** — Users and roles: build the UHC role matrix (`ASPSI_ADMIN`, `ASPSI_OPS`, `STL_REGION`, `ENUMERATOR`, `DOH_VIEWER`) and bulk-import the enumerator roster via CSV (Phase-8 §8.6–8.7).
- **E4-CSWeb-005** — Tablet sync configuration: wire each tablet's sync URL to `https://<your-domain>/csweb/api`, provision credentials, and prove the round-trip — case captured on a tablet appears in the CSWeb Data tab (Phase-8 §8.9–8.10).

The relational break-out (`php bin/console csweb:process-cases`, scheduled via cron) is also a later task — configure it only if DOH wants SQL/BI access to the data (Phase-8 §8.8.4).

---

## Open questions / execution blockers

1. **Domain name (HARD BLOCKER).** E4-CSWeb-001 cannot pass without a domain — Let's Encrypt does not issue to bare IPs. Carl must own/control a domain (or ASPSI subdomain) and be able to add an `A` record **before** execution day. This is the single dependency most likely to stall the runbook.
2. **CSPro Designer version of the F1/F3/F4 build (Part 0.2).** CSWeb must match the Designer line. Confirmed assumption is 8.0.x → CSWeb 8.0.1; Carl must verify against the actual Designer/`.pff` version, not assume.
3. **CSWeb 8.1.x stable?** Only 8.0.1 is a verified stable release; 8.1.0 exists as a 2026-03-18 alpha. Re-check [csprousers.org/downloads](https://csprousers.org/downloads/) on execution day and install the current **stable** release matching the Designer line.
4. **No Census-published Ubuntu command list.** The official docs say Apache server setup is "beyond the scope of this document." Parts 3–4 are the standard LAMP approach; the CSWeb setup wizard's prerequisite-check page (Section 4.7) is the runtime authority on PHP extensions — the runbook routes any gap through that loop rather than guessing.
5. **Archive top-level folder name.** `csweb-8.0.1.zip` may expand to a `csweb-8.0.1/` folder or directly to files — Section 4.2 has the on-VPS Claude inspect with `ls` before moving, so this resolves itself at execution time.
