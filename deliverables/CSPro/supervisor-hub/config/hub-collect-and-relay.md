# Supervisor hub: collect from enumerators + relay to CSWeb (B7)

**What this is:** the field SOP for the supervisor's hub device — **collecting** F1/F3/F4 cases from
each enumerator over Bluetooth at a daily regroup, then **relaying** them to CSWeb under the
`supervisor-qa` account when signal is available. The hub is a *dual-path safety net*: direct
enumerator→CSWeb sync stays the default (D1); the hub path covers no-signal days and same-day backup.

## A. Collect (Bluetooth host)

**Mechanism:** the supervisor menu's **Collect Interviews from Enumerators** runs
`syncserver(Bluetooth)` — a *passive* host that waits for a connection and responds to whatever the
client requests. It serves **one** enumerator per call; the supervisor re-selects the item for each
enumerator (one-host-from-many = the C2-proven loop). `syncserver` is the same call as *Assign EA*;
it both serves assignment files and receives case data, depending on what the connected enumerator
does.

Steps (mirror of `enumerator-bluetooth-sync.md`):
1. Supervisor: log in (supervisor) → **Collect Interviews from Enumerators** → *Allow* the
   "make this tablet visible" prompt → keep the screen open.
2. Each enumerator runs **Send My Interviews to Supervisor** and picks this device.
3. After each connection the hub shows *"COLLECT: an enumerator connected and synced…"*. Re-select
   **Collect Interviews** for the next enumerator. Repeat for the whole cluster.

**Where collected cases land:** each instrument's incoming cases merge into the hub's **own**
`…/csentry/<App>/<App>.csdb` (MenuApp reaches it as the external `..\<App>\<App>.csdb`), keyed by
the 12-digit `RR-PP-MMM-FF-CCC` key. Two copies of the same case (hub-collected + direct-synced)
**upsert to one** on CSWeb — conflict-free by key.

## B. Relay to CSWeb (under `supervisor-qa`)

**Now a one-tap logic relay** (wired 2026-06-27, Khurshid 101-apps pattern, grounded in csprousers.org).
The hub menu's **Relay Collected Interviews to CSWeb** (supervisor code 09) runs `relay_to_csweb()`:

```cspro
if syncconnect(CSWeb, "https://csweb.asiansocial.org/csweb/api") then
   syncdata(PUT, FACILITYHEADSURVEY_DICT);
   syncdata(PUT, PATIENTSURVEY_DICT);
   syncdata(PUT, HOUSEHOLDSURVEY_DICT);
   syncdisconnect();
endif;
```

1. Credentials are **omitted**, so CSEntry prompts the supervisor **once** for the **`supervisor-qa`**
   login (the scoped QA role — `report` + F1/F3/F4 dictionary sync; must be authorized to sync those
   dicts) and caches it; later relays are one-tap. *(In the device test the `cplreyes` admin account was
   used; confirm the `supervisor-qa` account is what production uses.)*
2. `syncdata(PUT)` requires each dict to be **uploaded to CSWeb already** — F1/F3/F4 are (deployed
   there), so the PUT is valid. Cases **upsert by the 12-digit key**, so hub-relayed + direct-synced
   copies never conflict.
3. Confirm on CSWeb: the collected cases appear in the **Data** tab (and, after the reporting cron, the
   Sync Report — which lags real-time, see `[[reference_csweb_sync_report_lag]]`). Record counts.

**Status:** the relay is **build-valid** (compile + strict `.pen` Publish both PASS 2026-06-27); the
`syncconnect(CSWeb)`-from-logic + the supervisor-qa credential prompt on **our** server are
**device-verify pending** (the one thing even Khurshid's reference doesn't prove on our deployment).
Fallback if it ever fails on device: open each instrument (F1/F3/F4) and tap its built-in **Sync** under
`supervisor-qa` — the existing, proven CSWeb sync.

## C. Then run on-hub QA (advisory)

After collecting, the Phase-1 Supervisor-QA report runs **unchanged** on the hub-collected data —
see `qa/run-on-hub.md`. QA stays **advisory** (D2): no write-back, no reject/reassign; the hub reviews,
the enumerator fixes on their own device.

## Daily field SOP (one line)

login → **Assign EA** (push assignments) → enumerators interview → **Collect Interviews** at regroup
(loop per enumerator) → on-hub **QA** → **Relay to CSWeb** on signal.

## Security (C6)

Tablets encrypted + password-locked; the supervisor **visually confirms** each Bluetooth pairing;
**wipe collected copies after confirmed relay**. Login is a local UX/identity gate, not security —
the real auth is the CSWeb account (D4).

## Status

- `syncserver(Bluetooth)` collect, one-host-from-many, primary case data, non-destructive:
  **DEVICE-CONFIRMED** (C2, 2026-06-25).
- THIS MenuApp wiring (the Collect menu item; receiving `syncdata` into the hub's **sibling-app
  `.csdb`**): **device-verify pending** a dedicated 2-tablet session.
- CSWeb relay via the instrument Sync under `supervisor-qa`: the existing, proven deployment sync —
  only the **role's dictionary-sync grants** need confirming for the QA supervisor.
