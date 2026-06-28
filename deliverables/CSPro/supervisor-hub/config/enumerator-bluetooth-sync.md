# Enumerator → Supervisor: send interviews over Bluetooth (B6)

**What this is:** the field SOP for an enumerator pushing their captured F1/F3/F4 cases to the
supervisor's hub device over **Bluetooth**, with no internet — the no-signal / daily-regroup
safety-net path. Direct enumerator→CSWeb sync stays the default where there is signal (D1).

**Mechanism (logic, not the Sync button):** CSEntry's built-in *Synchronize* button is CSWeb/
Dropbox/FTP only — it has **no** Bluetooth peer option (device-confirmed, spike `spikes/C2-bluetooth-spike.md`).
The Bluetooth case exchange is implemented in MenuApp **logic** via the CSPro sync PROC API:
`syncconnect(Bluetooth)` → `syncdata(PUT, <instrument dict>)` → `syncdisconnect()`. The enumerator
never touches the Sync button for this; they pick a menu item.

## One-time setup

1. **OS Bluetooth pairing.** On both tablets: Settings → Bluetooth ON. The first connect shows a
   device picker on the enumerator's tablet; the supervisor's tablet advertises a Bluetooth name
   (the test itel advertises **"Gemalyn"**). Pair/allow once (Android may skip the PIN prompt for
   RFCOMM). Range ≈ 10 m; keep the tablets close.
2. **LoginApp installed + up to date** on the enumerator tablet (Add Application → from CSWeb, or
   remove + re-add to force the latest — ⋮ *Update Installed Applications* is unreliable for CSWeb
   redeploys, see `[[reference_csentry_update_propagation]]`).
3. The enumerator has **received their assignment** first (menu → *Receive Assigned Data*), so the
   "send" step knows which instrument to push. If no assignment was received, send defaults to F3.

## Field steps (each regroup)

1. **Supervisor starts the host first.** On the supervisor tablet: log in as the supervisor →
   menu → **Collect Interviews from Enumerators**. The screen shows *"COLLECT: starting the
   Bluetooth server…"* and Android asks to *make this tablet visible to other Bluetooth devices* →
   **Allow**. Leave this screen open. (This serves **one** enumerator per connection.)
2. **Enumerator sends.** On the enumerator tablet: log in as the enumerator → menu → **Send My
   Interviews to Supervisor**. A Bluetooth device picker appears → select the supervisor's device
   (e.g. *Gemalyn*). On connect, the app pushes the assigned instrument's cases (`syncdata PUT`) and
   shows *"Sent your F3 interviews to the supervisor over Bluetooth. Your own copies are unchanged."*
3. **Non-destructive.** The enumerator's own cases remain on their tablet after sending (proven in
   C2). Sending again is safe — CSWeb/host upsert by the 12-digit key, so duplicates collapse.
4. **Next enumerator.** The supervisor re-selects **Collect Interviews from Enumerators** (the host
   serves one connection per call) and the next enumerator sends. Repeat for the whole cluster
   (one-host-from-many).

## What moves, and where it lands

- Only the enumerator's **assigned instrument** is sent (F1 → `FACILITYHEADSURVEY_DICT`, F3 →
  `PATIENTSURVEY_DICT`, F4 → `HOUSEHOLDSURVEY_DICT`). The instrument's cases live in that app's own
  `…/csentry/<App>/<App>.csdb`; MenuApp reaches it as an **external** dict (`..\<App>\<App>.csdb`).
- On the supervisor tablet the received cases merge into the hub's **own** `<App>.csdb` for that
  instrument, keyed by the 12-digit `RR-PP-MMM-FF-CCC` key. The supervisor then relays to CSWeb —
  see `hub-collect-and-relay.md`.

## Fallback (if a Bluetooth connect won't hold)

Manual OS file share: on the enumerator tablet, CSEntry → *Export Data* (or copy
`…/csentry/<App>/<App>.csdb`) → send the file via Android **Bluetooth / Nearby Share** → on the
supervisor tablet, **Import** it into the matching instrument. Slower and not conflict-merged
case-by-case, so use only if the logic path fails on the day.

## Status

- Transport (`syncconnect`/`syncdata` over Bluetooth, one-host-from-many, non-destructive):
  **DEVICE-CONFIRMED** (C2, 2026-06-25, F3 case itel↔Samsung).
- THIS MenuApp wiring (menu items routing to the sync logic; syncdata against an external mapped to
  a **sibling app's live `.csdb`**; the no-assignment default): **device-verify pending** a dedicated
  2-tablet session. Until then, treat the steps above as the intended SOP, to be confirmed on-device.
