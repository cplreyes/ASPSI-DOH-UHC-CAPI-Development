---
type: deliverable
kind: sop
audience: Carl (data programmer) · ASPSI data manager · supervising RAs
prepared_by: Carl Patrick L. Reyes
date_drafted: 2026-06-03
status: draft-for-review
related_tasks: [E4-CSWeb-006, E4-CSWeb-007]
companion_to:
  - CSWeb/Elestio-CSWeb-Deploy-Guide.md
  - CSWeb/CSWeb-on-VPS-Setup-Runbook.md
  - security/Data-Privacy-and-Security-Plan.md
tags: [csweb, elestio, backup, monitoring, ops, sop, e4]
---

# CSWeb Operations SOP — Backup & Monitoring

Operational procedures for the **live CSWeb 8.0.1 server on Elestio** (managed LAMP, Singapore) that receives F1/F3/F4 tablet syncs and runs the relational break-out. Covers data **backup + restore** (#238) and **sync/submission/field-device monitoring** (#239).

> **Two-layer model.** Elestio is a **managed** platform, so backups + monitoring exist at two layers:
> 1. **Platform layer (Elestio-managed):** host snapshots, TLS renewal, CPU/RAM/disk/uptime metrics + alerts.
> 2. **Application layer (our responsibility):** the CSWeb **case database** (MySQL), the **uploaded-photo / file store**, and the **sync-health + submission-count + field-device** view that the field team actually monitors.
>
> This SOP specifies both. Backup strategy aligns with the **Data Privacy & Security Plan §7** (this is its CSWeb-specific implementation). `⟨CONFIRM⟩` = a value Carl reads off / sets in the live Elestio dashboard; `⟨DECISION⟩` = needs DOH/ASPSI.

---

## Part A — Backup & restore  ·  *(E4-CSWeb-006 / #238)*

### A.1 What must be backed up
| Asset | Where | Why |
|---|---|---|
| **CSWeb case database** (MySQL/MariaDB) | server DB | the synced F1/F3/F4 cases + sync logs + audit — the irreplaceable field data |
| **Uploaded file store** (verification photos, attachments) | server filesystem (CSWeb data dir) | per-case evidence; not in the DB dump |
| **Relational break-out exports** (`csweb:process-cases` output) | server / export path | regenerable from cases, but cheap to retain |
| **CSWeb app config** (`/csweb/setup`, sync endpoint, accounts) | server | fast rebuild after a host loss |

### A.2 Platform-layer backup (Elestio-managed)
- Elestio takes **automated host backups/snapshots** of the service. **⟨CONFIRM⟩** in the Elestio dashboard: backup **frequency** (target: **daily**) and **retention** (target: **≥ 7 daily + 4 weekly**). Enable if not already on.
- Restore path: the Elestio dashboard's **restore-from-backup** (rebuilds the service to a snapshot). This is the fast "host died" recovery.

### A.3 Application-layer backup (our cron — portability + off-site + de-identified)
Platform snapshots are host-locked; add an **independent logical backup** so data survives even a provider/account problem and can be moved off-site:
```
# nightly, AFTER the 10 PM Manila sync window + the break-out cron
mysqldump --single-transaction --routines <csweb_db> | gzip > csweb-db_$(date +%F).sql.gz
tar czf csweb-files_$(date +%F).tar.gz <csweb_data_dir>
# encrypt before it leaves the box (key held OFF the server — see A.6)
```
- Schedule via cron at **~11 PM Manila** (after sync + break-out, before the next day).
- Rotate locally (keep ~7 days on-box), push the encrypted copy off-site per A.4.

### A.4 Frequency, retention, off-site
- **Frequency:** **daily** logical dump (A.3) + Elestio daily snapshot (A.2). A weekly full retained longer.
- **Retention:** ride the Data Privacy & Security Plan §8 retention — identifiable data only through collection + QA + analysis sign-off; **⟨DECISION⟩** authoritative period from DOH (Plan §8.1 / #225).
- **Off-site:** **⟨DECISION⟩ (#224)** — recommend an **encrypted, geo-separate** copy (e.g. an object store in a different region/provider) in addition to Elestio's snapshots; a single-platform backup is lost with the account. If DOH forbids off-site, document the accepted single-platform risk.

### A.5 Restore drill  *(Plan §7.3 — a backup never test-restored is not a backup)*
- **Before fieldwork** and **at least once mid-engagement:** restore the latest backup to a **clean staging service** (Elestio clone or a scratch box), then verify: **record counts match**, the **CSWeb app loads + logs in**, a **sample case opens**, and the **break-out tables regenerate**.
- **Log each drill** (date, who, source backup, result). A failed/never-run drill is a release blocker for fieldwork.

### A.6 Encryption & key custody
- Backups (A.3) **encrypted at rest**; the encryption key is held **separately from the server** (Carl's password manager / a separate secret store), so a server compromise doesn't expose the backups. Ties to Plan §6.1.

---

## Part B — Monitoring  ·  *(E4-CSWeb-007 / #239)*

"Sync health, submission counts, field-device status" — assembled from three existing surfaces (Elestio metrics + the CSWeb dashboard + a thin SQL view over the break-out tables); **no new system to build.**

### B.1 Platform monitoring (Elestio)
- Elestio dashboard exposes **CPU / RAM / disk / uptime**. **⟨CONFIRM⟩** set alerts: **disk > 80%** (case blobs + photos + backups grow over 8-region fieldwork), **sustained CPU** (the nightly sync + break-out cron are the load spikes — see the runbook 4 GB note), and **service-down/uptime**.
- These catch the "box is unhealthy" class before it drops syncs.

### B.2 CSWeb application monitoring (the field-facing view)
| Signal | Source | What it tells you |
|---|---|---|
| **Sync health** | CSWeb sync logs (who synced, when, success/fail) | are tablets reaching the server before the 10 PM mandate? |
| **Submission counts** | CSWeb Data tab + a SQL query over the break-out tables, grouped by **instrument × region × day** | coverage vs target; the live progress number |
| **Field-device status** | last-sync timestamp **per device/enumerator** | which tablets are silent (lost/broken/connectivity) — feeds the STL field-replacement SOP |
| **Break-out cron health** | `csweb:process-cases` exit + last-run time | is the relational/BI layer current? |

> A small **saved SQL view** (`v_daily_coverage`: instrument, region, count, last_sync) over the break-out tables is the cleanest single "monitoring dashboard" artifact — point Looker Studio (see `data-harmonization/bi-dashboard-blueprint.md` §5.1) or the CSWeb Data tab at it.

### B.3 Daily monitoring routine (data manager / supervising RA)
Each morning, against yesterday's syncs:
1. **Coverage:** completed counts by region/instrument vs the day's target (B.2).
2. **Field-device status:** any device with no sync in 24–48 h → flag to the STL (field-replacement / connectivity check).
3. **Break-out cron ran** + **disk headroom** OK (B.1).
4. Reconcile against the STL daily diary (the STL Training Deck end-of-day routine).

### B.4 Alerting & escalation
- **Sync-failure spike / a cluster silent** → STL → ASPSI CAPI team.
- **Disk > 80% / service down / break-out cron failing** → Carl / CAPI team (Elestio alert → action).
- Tie lost/silent-device follow-up to the **field-replacement** and **incident** chains (Plan §10/§11).

---

## Issue coverage map
| Section | Issue |
|---|---|
| A Backup & restore | #238 (E4-CSWeb-006) |
| B Monitoring | #239 (E4-CSWeb-007) |

**Pending ⟨CONFIRM⟩ on the live box:** Elestio backup frequency/retention + alert thresholds (read/set in the dashboard); the `v_daily_coverage` SQL view wired to the break-out tables. **⟨DECISION⟩:** retention period (#225/Plan §8) + off-site copy (#224/Plan §7.4). Restore-drill execution + the live alert setup are operational follow-ups; this SOP is the strategy + procedure of record.
