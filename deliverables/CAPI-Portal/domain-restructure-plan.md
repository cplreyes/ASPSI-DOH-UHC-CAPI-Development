---
title: "CAPI Domain Restructure — Plan of Record"
category: deliverable
tags: [capi, portal, dns, csweb, f2-pwa, elestio, restructure]
status: committed 2026-07-08
last_updated: 2026-07-08
---

# CAPI Domain Restructure — Plan of Record

Decided 2026-07-08 (Carl, via [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CAPI-Portal/capi-domain-restructure-options|options diagram]], Option C —
with the csweb rename **committed**, not optional). One box (`207.148.65.115`,
Elestio `aspsi-csweb-prod`), one flat naming scheme:

| Name | Role | Status |
|---|---|---|
| `capi.asiansocial.org` | Portal + docs — ASPSI CAPI services home; UHC = first project page | to build (v1 next) |
| `uhc-csweb.asiansocial.org` | F1/F3/F4 field data hub (CSWeb, renamed) | **committed — Phase R below** |
| `uhc-hcw.asiansocial.org` | F2 HCW survey app (f2-api + PWA) | built dark; DNS pending |
| `csweb.asiansocial.org` | legacy alias during transition | retires at end of Phase R |

DNS: all three A records requested in ONE email to Ma'am Juvy
([[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/comms/email-aspsi-dns-capi-uhc-hcw|email-aspsi-dns-capi-uhc-hcw]]) — `uhc-csweb` sits dark/unused until Phase R flips it.

## Sequencing principle

The portal is presentation; hostnames are plumbing. Plumbing renames happen only at
**redeploy boundaries** — never inside a live testing window. The one hard freeze:
**no csweb changes between now and pretest completion** (a sync failure at pretest,
in front of DOH, outcosts the whole restructure).

## Phases

### Phase P — Portal (now, parallel with the DNS wait)
Static portal at `deliverables/CAPI-Portal/site/` (vendored assets, no CDN) served by a
loopback container + vhost (same pattern as f2-api). Content: ASPSI CAPI services
framing + UHC Survey 2026 project page (cards → Field data hub / F2 HCW app / Docs) +
docs section. **Carl/ASPSI approve public copy before it goes live.** The UHC card
links to `csweb.asiansocial.org` until Phase R completes, then flips to `uhc-csweb`.

### Phase F2 — uhc-hcw activation (in flight)
Migration plan P3 staged (one Carl-gated command) → DNS → gate curl → P4 authority
flip → P5 re-enrollment → P6 retire CF/Google. See
[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/F2/F2-Prod-Migration-Plan|F2-Prod-Migration-Plan]].

### Phase R — CSWeb rename csweb → uhc-csweb (post-pretest, pre-training; target Jul–Aug window)
Rides the training republish that happens anyway. The REAL field fleet (provisioned at
Aug training for Sep rollout) enrolls on the new name from day one — same greenfield
logic as F2. Steps, all additive until the final one:

1. **Alias live:** Elestio custom domain / vhost for `uhc-csweb.asiansocial.org`
   (DNS already exists from the Juvy email). Both names now serve CSWeb identically.
   Gate: `https://uhc-csweb.asiansocial.org/csweb/` loads with valid padlock.
2. **Server config:** `config.php` → `API_URL = 'https://uhc-csweb.asiansocial.org/csweb/api/'`.
3. **Instruments:** republish F1/F3/F4 `.pen` with the new sync URL (generator-level,
   rides the training build; auto_deploy target-URL check updated).
4. **Consumers sweep:** supervisor hub relay · poller cron env · dashboard/map-report
   gen · tester/training guides · versions.json stamps.
5. **Devices:** UAT testers + training fleet remove + re-add (standard update path;
   scheduled at training day, not ad hoc).
6. **Retire:** after every consumer verified on `uhc-csweb` (sync report shows all
   devices current), the `csweb` record/vhost retires — or stays as a permanent
   harmless alias if ASPSI prefers.

Rollback at any step ≤5: the old name still serves; nothing has hard-cut.

**Effort estimate:** ~1 focused day of build/sweep + the republish cycle already
scheduled for training.

## Out of scope
- Path-hosting CSWeb under `capi.asiansocial.org/...` — rejected (PHP app path-prefix
  surgery, no benefit once the flat scheme exists).
- Any csweb change before pretest completes — hard freeze.
