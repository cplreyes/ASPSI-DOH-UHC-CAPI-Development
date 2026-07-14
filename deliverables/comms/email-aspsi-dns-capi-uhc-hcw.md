---
title: "Email — ASPSI DNS records: capi + uhc-hcw + uhc-csweb (full CAPI domain restructure)"
category: deliverable
tags: [capi, f2-pwa, portal, dns, domain, elestio, comms]
to: "Ma'am Juvy (cjrocamora@gmail.com) + Sir EJ / Edward Ramilo (ejramilo@gmail.com — manages the asiansocial.org domain, added the June csweb record); CC aspsi.doh.uhc.survey2@gmail.com, merlynepaunlagui@gmail.com, nrquilloy@asiansocial.org"
from: clreyes6@up.edu.ph
status: "SCHEDULED by Carl 2026-07-08 to send 2026-07-09 08:00 MNL (draft r3141131097279167806: HTML table + explicit csweb→uhc-csweb RENAME framing — step 1 add-alongside now / step 2 delete old csweb after post-pretest switchover) — in-thread reply to the June 'CSWeb Server — One DNS Record' trail (thread 19e87c95588279f1). Superseded drafts r3760215775992077282 / r-8260985728138492844 to be discarded. NEXT: watch the thread for EJ's confirmation → then gate curl https://uhc-hcw.asiansocial.org/api/health"
last_updated: 2026-07-08
---

> [!note] As staged
> The Gmail draft is a **shorter in-thread reply** (EJ already knows the drill from June)
> using EJ's own record format — the full standalone version below is kept for reference.

# Email — ASPSI: two DNS records to activate `capi.asiansocial.org` + `uhc-hcw.asiansocial.org`

Companion to [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/F2/F2-Prod-Migration-Plan|F2-Prod-Migration-Plan]] (P2 gate) and the CAPI portal decision
([[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CAPI-Portal/capi-domain-restructure-options|capi-domain-restructure-options]], Option C, 2026-07-08).
Follows the exact format of [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/comms/email-aspsi-dns-csweb|email-aspsi-dns-csweb]] (the June request that activated csweb) — provider-agnostic, since we don't manage or assume ASPSI's domain provider.

> [!note] Security
> ASPSI-facing — contains only the server's **public IP / hostname** (no SSH keys, no
> passwords, no mention of how the server is operated).

---

**Subject:** ASPSI CAPI Portal + Survey Apps — Three DNS Records to Activate

**To:** Ma'am Juvy (`cjrocamora@gmail.com`) — *forward from the review draft at clreyes6@up.edu.ph*

---

Dear Ma'am Juvy,

Good day po! We are organizing all the CAPI survey services under one clean set of addresses on the same ASPSI survey server that already runs csweb.asiansocial.org: the **ASPSI CAPI portal** (project pages and documentation), the **F2 Health Care Worker survey app**, and a **new address for the field data hub** that we will switch to after the pretest. To set these up, **three DNS records** need to be added to the **asiansocial.org** domain — the same simple step we did for csweb in June.

Could you (or whoever manages the asiansocial.org domain) please add these three records:

| Field | Record 1 | Record 2 | Record 3 |
|---|---|---|---|
| **Type** | A | A | A |
| **Name / Host** | `capi` | `uhc-hcw` | `uhc-csweb` |
| **Points to / IP** | `207.148.65.115` | `207.148.65.115` | `207.148.65.115` |
| **TTL** | Automatic (or 3600) | Automatic (or 3600) | Automatic (or 3600) |

Those are the only changes needed. Once saved, the addresses activate automatically within a few minutes to a few hours, and the secure "https" padlock is configured automatically — there is **no certificate to buy or install**. All existing asiansocial.org records — **including csweb, which keeps working exactly as it does today** — stay as they are; this only adds the three new subdomains. (The `uhc-csweb` address will simply sit unused until we do the switchover after the pretest, at a time we'll coordinate with the team.)

### Quick step-by-step (for the domain provider)

1. Log in to the account where **asiansocial.org** is managed (the domain registrar / DNS provider).
2. Open **"DNS"**, **"DNS Management"**, or **"Zone Editor"** for asiansocial.org.
3. Click **"Add Record"** and enter the first record:
   - **Type:** A
   - **Name / Host:** `capi`  *(if it asks for the full name, use `capi.asiansocial.org`)*
   - **Value / Points to:** `207.148.65.115`
   - **TTL:** leave default (or 1 hour)
4. **Save**, then repeat for the other two records with **Name / Host:** `uhc-hcw` and `uhc-csweb`.

*Alternative — if the provider prefers CNAME records instead of A records, use: Type **CNAME**, Name **`capi`** (and **`uhc-hcw`**, **`uhc-csweb`**), Value **`aspsi-csweb-prod-u73907.vm.elestio.app`**. Either kind works — please add one record per name, not both kinds.*

Please let me know once they're added — or if it's easier, I'm happy to coordinate directly with your domain provider. I'll confirm everything is live on our end as soon as it propagates.

Thank you very much!

Best regards,
Carl Patrick Reyes

---

## Carl-side checklist (NOT part of the email)

1. **With/before sending (recommended):** Elestio dashboard → `aspsi-csweb-prod` →
   **Domains / Custom domain** → add `uhc-hcw.asiansocial.org` with **target port 8787**
   (f2-api) and, once the portal container exists, `capi.asiansocial.org` with its port.
   This is how csweb was activated in June — Elestio then generates/owns the nginx conf
   and the cert flow. **Caveat:** the P2/P3 walk hand-wrote
   `/opt/elestio/nginx/conf.d/uhc-hcw.asiansocial.org.conf` + appended `ALLOWED_DOMAINS`
   manually (works standalone via auto-SSL). If the Elestio panel generates its own conf
   for the same name, remove the hand-written file to avoid duplicate `server_name` —
   and check the panel's conf preserves the `/exec|/verify-token|/api/|/admin/api/`
   → `127.0.0.1:8787` routing (if the panel conf is a plain single-proxy like csweb's,
   it forwards everything to 8787, which is fine — f2-api serves the SPA itself).
2. **After the records resolve:** gate check `curl https://uhc-hcw.asiansocial.org/api/health`
   → `{"ok":true,...}` (first hit mints the cert; give it a few seconds). Then the P5
   UAT re-enrollment smoke per the migration plan.
3. **Portal:** `capi.asiansocial.org` returns Elestio's default/404 until the portal
   container + vhost ship (CAPI-Portal v1 build) — harmless to have DNS ready first.

VPS reference (for the record target): IP `207.148.65.115` · Elestio hostname `aspsi-csweb-prod-u73907.vm.elestio.app`.
