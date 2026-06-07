---
title: "Field-Tablet Sync Configuration (E4-CSWeb-005)"
category: deliverable
tags: [csweb, csentry, sync, tablets, fieldwork, uhc-y2, ops]
status: ready
last_updated: 2026-06-04
gh_issue: 237
supersedes_notes: "Production-specific config. The methodology walkthrough in UHC-Survey-CAPI-Guide/06-Phase-8 was written against CSWeb 7.7 / Wampserver / in-app syncconnect — reconciled to current reality below."
---

# Field-Tablet Sync Configuration — UHC Year 2 CAPI

**Issue:** #237 (E4-CSWeb-005). **Scope:** how the F1/F3/F4 field tablets push captured cases to the production CSWeb server — the **endpoint**, the **schedule**, and the **conflict policy**, plus the per-tablet setup, auth, and fallback SOP.

This is the production config of record. Two things changed from the generic Phase-8 methodology guide and govern everything below:

1. **No in-app sync logic.** Per **#131** (resolved): in CSPro 8 `syncdata()` syncs *external* (lookup) dictionaries, not primary case data. Primary case-data sync is handled by **CSEntry's built-in Synchronize**, configured at the tablet/deployment level — *not* from `.apc` PROC code. The current generator-based F1/F3/F4 build has **no `syncconnect`/`synchronize_data` calls** (verified). So Phase-8 §8.10 (in-app `syncToServer()`) does **not** apply.
2. **Production server is CSWeb 8.0.1 on Elestio** (Docker LAMP), not CSWeb 7.7 on Wampserver. Live at **`https://csweb.asiansocial.org`**.

---

## 1. Endpoint

| Item | Value |
|---|---|
| **CSWeb server** | `https://csweb.asiansocial.org` (CSWeb 8.0.1, Elestio, Singapore) |
| **Sync API base** | `https://csweb.asiansocial.org/csweb/api` (`API_URL` configured in `src/AppBundle/config.php`; live — verified reachable) |
| **CSEntry sync server URL** | In CSEntry → **Sync → CSWeb → add server**, enter `https://csweb.asiansocial.org/csweb` (CSEntry appends the `/api` path itself). **Verify the exact accepted form at the first round-trip (#196)** — if CSEntry rejects the base, use the full `https://csweb.asiansocial.org/csweb/api`. |
| **Transport** | HTTPS only (Let's Encrypt cert, auto-renew). Cleartext HTTP is redirected. Encryption-in-transit spec: #216 (closed). |
| **Auth** | Per-user CSWeb credentials (username + password) entered on the tablet at sync time. OAuth handshake under the hood (`/csweb/api/token`, `client_id=cspro_android`). Credentials provisioned per **#236** (user management — pending the enumerator roster). |

The **one rule** that breaks fieldwork if missed: the sync URL on every tablet must be the **production domain**, never `localhost` / an Elestio preview URL. "Works in the office, fails in the field" is always a leftover `localhost`.

---

## 2. Sync model & direction

CSEntry **built-in Synchronize**, manual (enumerator-triggered), one dictionary per instrument:

| Instrument | Dictionary (registered in CSWeb) | Enumerator direction | Supervisor direction |
|---|---|---|---|
| F1 Facility Head | `FACILITYHEADSURVEY_DICT` | **send** (push only) | both (pull for review) |
| F3 Patient | `PATIENTSURVEY_DICT` | **send** | both |
| F4 Household | `HOUSEHOLDSURVEY_DICT` | **send** | both |

- **Smart-sync**: only **new or changed** cases since the last successful sync move — unchanged cases are not re-sent (bandwidth-frugal over cellular).
- **Manual, not auto-on-exit**: enumerators tap Sync at end-of-day and read the success/failure message. Silent auto-sync that fails leaves them falsely believing data is safe.
- **F2 (HCW PWA) does NOT sync here** — it is a Cloudflare PWA → Apps Script → Google Sheets path. Ops must not look for F2 data in the CSWeb Data tab. (See [[../data-harmonization/codebook|codebook]] §11 — F2's case-ID is derived at ETL.)

---

## 3. Schedule

Per Protocol V2 — **daily 22:00 (10 PM) local upload mandate**:

| Time | Action | Owner |
|---|---|---|
| During the day | Cases captured offline; persist on the tablet's local `.csdb`. No connectivity required to keep working. | Enumerator |
| By **22:00** each fieldwork day | Complete at least one successful sync. | Enumerator |
| **22:30** | Check the CSWeb **Sync Report**; confirm each enumerator's case count matches the day's planned interviews; chase any gap. | STL |

Enforcement is **operational** (STL nightly roll-call), not technical — CSWeb has no server-side scheduler or automated-alert feature (verified against the CSWeb User's Guide). Any alerting must be built downstream of the data store, not in CSWeb.

---

## 4. Conflict policy

**Conflicts are designed out by the 12-digit case key, not resolved after the fact.**

- The case key is `RR-PP-MMM-FF-CCC` (`REGION_CODE`·`PROVINCE_HUC_CODE`·`CITY_MUNICIPALITY_CODE`·`FACILITY_NO`·`CASE_SEQ`) — see [[../../wiki/concepts/Questionnaire Numbering Convention]]. The first 9 digits pin the **facility**; `CASE_SEQ` (001–699 active / 700–899 replacement / 900–999 refused) is unique **within facility, within instrument**.
- Enumerators are assigned **distinct facilities**, so two devices never mint the **same** case key. There is no concurrent-write race on a single case → **no merge conflict to resolve.**
- **Re-sync of an edited case** (e.g., a callback correction the next day): smart-sync sends the changed case; CSWeb stores the **latest version** (case-level last-write-wins — CSPro does not field-merge). Because one case = one device, "latest" is unambiguous.
- **Partial / break-off cases** sync as partial (AAPOR `120`); they update in place when completed and re-synced.

**F3 two-stream integrity** (the "errors" concern raised by Dr. Myra — see [[../../wiki/...|csweb deployment notes]]): a single F3 instrument with a **required, no-default patient-type field** means there is no "wrong form," and **CSWeb auto-computes per-type running counts** — so the admitted/outpatient tallies can't be mis-reconciled by hand. Count mismatch / duplicate / missing-required conditions surface same-day in the Sync Report for callback while the team is still in-area.

---

## 5. Per-tablet setup (at enrollment / bring-up)

Done once per device during provisioning (the tablet bring-up SOP, #182):

1. Install CSEntry + the deployed `.pen` (F1/F3/F4) — pulled from CSWeb **Apps** once the apps are deployed (Designer → Deploy Application; the `.pen` upload is the residual on #235).
2. CSEntry → **Sync → CSWeb** → **Add server** → URL = `https://csweb.asiansocial.org/csweb` (see §1).
3. Enter the enumerator's **CSWeb credentials** (from #236). Optionally bind to device ID (Phase-8 §8.11 — deferred for pilot).
4. Run **one mock-case round-trip** before issuing the device (capture → Sync → confirm it appears in CSWeb Data tab → delete the mock).

---

## 6. Fallback SOP (CSWeb unavailable)

CSWeb is the **only** sync path in normal operations. Fallbacks are pre-decided contingencies, not enumerator choices:

| Trigger | Action | Owner |
|---|---|---|
| CSWeb 5xx > 2 h | STL pings ops; investigate (Elestio status, container health). | STL → Coordinator |
| CSWeb unreachable > 24 h | Each tablet exports `.csdb` (CSEntry → Data Export) → upload to per-cluster cloud folder; ops merges into CSWeb via Data Manager on recovery. | Coordinator |
| Local cellular outage (one device) | None — keep working offline; sync resumes automatically when connectivity returns. | Enumerator |
| Server host failure | Restore from Elestio snapshot/backup; tablets re-sync from last successful point (local `.csdb` retains everything). | Carl + ASPSI ops |

---

## 7. Readiness & gaps

| Component | Status |
|---|---|
| CSWeb server live (8.0.1, HTTPS) | ✅ |
| F1/F3/F4 dictionaries registered (12-digit) | ✅ re-registered + DB-verified 2026-06-04 |
| Sync API endpoint reachable | ✅ (`/csweb/api/token` responds) |
| Per-user credentials / roles | ⛔ **#236** — needs the finalized enumerator roster (CSV import) |
| `.pen` apps deployed to CSWeb Apps | ⛔ residual on **#235** — Designer → Deploy Application after CSPro Designer compile |
| End-to-end round-trip verified | ⛔ **#196** — tablet → CSWeb → ETL, during desk-testing |

**Server-side, sync is ready now.** The remaining gates (credentials, `.pen` deploy, live round-trip) are tracked under #236 / #235 / #196 and ride the CSPro-Designer + desk-test pass.

---

## 8. References

- Methodology walkthrough (private guide): `UHC-Survey-CAPI-Guide/06-Phase-8-CSWeb-and-Tablets.md` §8.9–8.10 (reconcile to this doc where they differ: 8.0.1/Elestio + no in-app sync).
- Sync mechanic decision: #131 (CSEntry built-in, no in-app `syncdata`).
- Encryption in transit: #216. Deploy guide: `CSWeb/Elestio-CSWeb-Deploy-Guide.md`. Case key: [[../../wiki/concepts/Questionnaire Numbering Convention]].
