# Supervisor App — Design Spec (Phase 2: Bluetooth Sync Hub)

**Date:** 2026-06-21
**Status:** Approved design (brainstorm complete) — ready for implementation planning
**Author:** Carl Patrick Reyes (with Claude)
**Builds on:** Phase 1 (`docs/superpowers/specs/2026-06-20-supervisor-app-design.md`) — the deferred Phase 2 from that spec's phasing table. Phase 1 (Review Layer) is **built + committed**; the Cluster-5 `CASE_DISPOSITION` sentinel (#515/#561) is **shipped + device-confirmed**.

---

## Goal

When field sites have **no/poor internet**, give a cluster a way to get cases off enumerator
tablets the same day and into CSWeb: enumerators **Bluetooth-sync to the supervisor's tablet**
(the "hub") at a daily regroup; the hub **relays to CSWeb** when it reaches signal. It also acts
as a **same-day data-safety net**, consolidates the cluster's **cellular uplink** to one device,
and lets the supervisor run **advisory QA on the collected cases before relay**.

## Architecture (one line)

A **3-tier, supervisor-as-intermediary** topology running as a **dual-path fallback**:
enumerators still sync **direct to CSWeb where signal exists** (unchanged); Bluetooth-to-hub is
the **no-signal/safety-net path**, and the hub relays to CSWeb. CSWeb upserts by the 12-digit
key, so the two paths are additive and conflict-free.

## Tech Stack

CSEntry 8.0 built-in **Bluetooth (local/peer) sync** for enumerator→hub case movement · CSEntry
**CSWeb sync** for hub→CSWeb relay (HTTPS, `csweb.asiansocial.org`) · a CSPro 8 **login + menu
app** (Khurshid pattern) wrapping the existing generator-built F1/F3/F4 instruments via PFF
chain-launch · the Phase-1 Supervisor-QA report (Python, reused unchanged) for on-hub QA · an
external roster/assignment dictionary. **No new server.** **The F1/F3/F4 instruments are not
modified** — they are chain-launched, not edited.

---

## Why Phase 2 now (the four drivers — all in scope)

| Driver | How Phase 2 serves it |
|---|---|
| **No internet at field sites** | Hub collects over Bluetooth on-site (no signal needed), relays later from signal. |
| **Daily data-safety net** | Cases land on a second device (the hub) the same day, even off-grid; reduces loss if a tablet is lost/broken before its own sync. |
| **QA before CSWeb** | Supervisor runs the Phase-1 QA report on collected cases before relay — **advisory** (see D3). |
| **Reduce cellular cost/load** | One hub uplink per cluster instead of many enumerator uplinks. |

---

## Decisions locked (during brainstorm, 2026-06-21)

| # | Decision |
|---|---|
| **D1** | **Dual-path / fallback** (not single mandatory hub). Direct enumerator→CSWeb stays the default where signal exists; Bluetooth→hub is the no-signal + safety-net path. Preserves Phase 1's conflict-free 12-digit-key design. |
| **D2** | **QA stays advisory** (Phase-1 style). The hub reviews collected cases before relay but does **not** hard-gate them; **no reject/reassign write-back channel** (that would require single-path and tear up the conflict-free model). |
| **D3** | **Primary collection mechanism = CSEntry built-in Bluetooth sync** (device-to-device). **Fallback = manual export/import over Bluetooth file share.** The PROC `syncserver()`/`syncconnect()`/`syncdata()` path is **rejected** for case data — see the #131 constraint below. |
| **D4** | **Login & role routing via the Khurshid login+menu app** (enumerator vs supervisor), **spike-gated** on CSPro 8. It is a local UX/identity gate, **not** a security boundary; real sync auth remains the CSWeb account. |
| **D5** | **Hub relays under the existing `supervisor-qa` CSWeb role** (it already carries F1/F3/F4 dictionary sync from the Phase-1 C1 decision). No new CSWeb role. |
| **D6** | **Instruments are not modified.** The login/menu app wraps the generator-built F1/F3/F4 via PFF chain-launch; no hand-edits to `.dcf`/`.apc`/`.fmf`/`.qsf`. |
| **D7** | **Phase 2 stays deferred** until F1/F3/F4 are near-zero UAT bugs (the Phase-1 phasing trigger). This spec is written now; the build waits. |

---

## Hard constraint from production reality (#131)

The Phase-1 spec's forward note assumed *"enumerators `syncconnect` to the supervisor's
`syncserver` (Bluetooth)."* **That mechanism does not move primary case data in CSPro 8.**
`deliverables/CSWeb/Field-Tablet-Sync-Configuration.md` records (per resolved issue #131):

> "In CSPro 8 `syncdata()` syncs *external* (lookup) dictionaries, not primary case data.
> Primary case-data sync is handled by CSEntry's built-in Synchronize, configured at the
> tablet/deployment level — not from `.apc` PROC code."

So Phase-2 case movement **must** ride **CSEntry's built-in sync** (the same path case data
uses today), with **Bluetooth** as the configured server type — **not** PROC-code `syncdata()`.
This is the reason for D3.

---

## Reference correction (vs the Phase-1 spec)

The Phase-1 spec cited Arshan Khurshid as demonstrating "supervisor-held sync (`syncconnect` +
`syncdata PUT`)" over Bluetooth. **Verified against his actual tutorials (this session): there is
no Bluetooth tutorial in his set** — his sync content is **CSWeb-only** (deploy+sync to CSWeb,
sync report + add users + define roles on CSWeb, batch download, `synctime`). What Khurshid
*does* provide and we adopt here is the **login + role-based menu app** (below). The Bluetooth
mechanism is grounded in the **CSPro Synchronization docs**, not Khurshid.

---

## Architecture

```
 Enumerator tablets (login app → Enumerator mode → F1/F3/F4, CSEntry)
   │  ① Bluetooth — CSEntry built-in sync, at a DAILY REGROUP (~10m, no internet)
   │     (also: ②a direct → CSWeb where signal exists — unchanged, dual path)
   ▼
 Supervisor HUB tablet (login app → Supervisor mode; accumulates the cluster's .csdb)
   │  ③ CSWeb sync (HTTPS) when signal is reached — under the supervisor-qa account
   │  (④ on-hub QA: run the Phase-1 report on the collected .csdb before relay)
   ▼
 CSWeb (csweb.asiansocial.org) — UPSERT by the conflict-free 12-digit key
```

**Key safety property:** every case is keyed by the 12-digit `RR-PP-MMM-FF-CCC` key, and CSWeb
upserts by key. A case arriving via the hub **and** later via the enumerator's own direct sync
is the same/newer revision — no conflict, no dedup machinery. Phase 1's conflict-free design is
fully preserved.

**Two operating realities:**
- **Bluetooth is ~10m**, so collection is not continuous — it happens at a **daily physical
  regroup** (the SOP heartbeat). Clusters that never regroup can't be collected (stated limit;
  those enumerators fall back to their own direct sync whenever they reach signal).
- **Phase-1 synergy:** the hub holds the collected `.csdb`, so the **Phase-1 Supervisor-QA report
  runs directly on the hub** — coverage/partials/flags *before* relay, no CSWeb round-trip in a
  no-signal cluster.

---

## Components

### C1 — Login & role routing app (NEW; Khurshid login+menu pattern; spike-gated, D4)

A thin CSPro 8 wrapper that fronts the existing instruments without modifying them.

- **Login app:** a login form + an external **`USERNAME_PASSWORD_DICT`** (one row per person:
  `USERNAME, PASSWORD, ROLE` (enumerator | supervisor), `OPERATOR_ID`, `CLUSTER`). `loadcase()`
  matches the entered username/password against the dictionary.
- **Role handoff:** on success, `savesetting("role", …)`, `savesetting("operator_id", …)`,
  `savesetting("cluster", …)`.
- **Menu app:** reads the role via `loadsetting` and routes:
  - **Enumerator mode** → PFF chain-launch F1/F3/F4 (generator-built, unchanged).
  - **Supervisor mode** → the collect → relay → QA flow (C2/C3/C4).
- **Nature:** a **local UX/identity gate**, not a security boundary — the password sits in an
  on-device dictionary and only routes the UX. Real auth is the CSWeb account (C3/D5).
- **Grounding:** Khurshid `videos/2022-03-27_tutorial1-create-login-application-in-cspro/` +
  `videos/2022-04-05_tutorial-3-writing-cspro-code-and-add-external-dictionary/` (roles
  "Supervisor and Enumerator" @02:21; `loadcase` auth @12:44) +
  `videos/2022-04-15_tutorial-1-create-pff-and-menu-application/` (PFF chain-launch +
  `savesetting`/`loadsetting` role handoff). Khurshid's example is **CSPro 7.7-era** → confirm on
  CSPro 8 + itel in the C1 spike.

### C2 — Bluetooth collection (the core mechanism; #1 spike, D3)

- **Enumerator side:** a "Sync to Supervisor" action invoking CSEntry's **built-in** sync with a
  **CSPro local/Bluetooth peer** server type, targeting the hub device.
- **Hub side:** the supervisor device acts as the collection host, accumulating each enumerator's
  cases into the hub's local app data per instrument (F1/F3/F4).
- **Spike (gating, see Testing):** confirm CSEntry built-in Bluetooth sync supports (a)
  **one host collecting from many peers** (vs strict 1:1 pairing) and (b) **primary case data**
  (not only external dicts), on the itel/Android targets, and that it is **non-destructive** to
  the enumerator's originals.
- **Fallback (if the spike fails):** **manual export/import over OS Bluetooth file share** —
  enumerator exports the case file → Bluetooth file transfer → supervisor imports into the hub's
  local data → relay. Crude and per-device but mechanism-independent and certain.

### C3 — Hub→CSWeb relay (D5)

Supervisor-mode action: standard CSEntry **CSWeb sync** of all collected cases under the
**`supervisor-qa`** account (already has F1/F3/F4 dictionary sync). CSWeb upserts by the 12-digit
key → additive, conflict-free, dual-path safe. Smart-sync moves only new/changed cases.

### C4 — On-hub QA review (reuses Phase 1; advisory, D2)

The hub holds the collected `.csdb`, so the **Phase-1 Supervisor-QA report** (the Python tool at
`deliverables/CSWeb/supervisor-app/`) runs on it directly — coverage vs plan, partials (#561),
data-quality flags — **before relay**, no CSWeb round-trip needed in a no-signal cluster.
Advisory only: the supervisor chases gaps verbally; the enumerator fixes on their own device. No
write-back / reject channel.

### C5 — Roster / assignment dictionary

`USERNAME_PASSWORD_DICT` (C1) plus the Phase-1 assignment/target lookup (`ENUMERATOR_ID,
FACILITY_CODE, INSTRUMENT, TARGET_COUNT`) — **likely merged** into one supervisor-maintained
source (confirm in planning). Because the Bluetooth hop is unauthenticated, case provenance
rests on the **in-data `ENUMERATOR_S_NAME` + the 12-digit key**, not on an authenticated
enumerator login at the Bluetooth step.

### C6 — Security & identity controls (the governance the login questions surfaced)

- The **Bluetooth hop has no authentication** (CSPro Bluetooth sync requires only physical
  proximity) → procedural controls: **encrypted + password-locked tablets**, supervisor
  **visually confirms each pairing**, and **wipe collected copies after confirmed relay**.
- The whole cluster's PII lands on **one hub device** → encryption is mandatory.
- The C1 app login is **UX/identity routing, not security**; the only credentialed login in the
  flow is the CSWeb account at relay (C3).

---

## Data flow — the daily cycle

```
MORNING    Operator logs in (Enumerator mode) → instrument; capture offline        [unchanged]
DAY        Capture offline; direct-sync to CSWeb where signal exists               [dual path]
REGROUP    (no signal) enumerators "Sync to Supervisor" → Bluetooth → hub collects
HUB        Supervisor mode → run the on-hub QA report on collected cases; chase gaps verbally
SIGNAL     Hub relays all collected cases → CSWeb (supervisor-qa); CSWeb upserts by key
```

**Integrity property:** the hub copy and the enumerator's own copy are both keyed by the 12-digit
key; relay is additive (upsert), never a merge conflict. The enumerator's device keeps its own
cases (the hub is a copy), so collection adds redundancy without removing the original.

## Edge cases

- **Same case via hub *and* direct** → CSWeb upsert by key; latest revision wins; no conflict, no
  dedup needed.
- **Enumerator never regroups** (out of ~10m range for days) → not collected; falls back to their
  own direct sync whenever they reach signal. **Stated limit.**
- **Hub lost/stolen** → whole cluster's PII exposed → encryption + wipe-after-relay; but
  enumerators' own devices still hold their cases (hub is a copy), so **no data loss**.
- **Partial cases collected** → carry the Cluster-5 `CASE_DISPOSITION` sentinel; on-hub QA
  surfaces them exactly as in Phase 1.
- **Operator not in roster / forgotten password** → can't obtain a role; SOP fallback
  (roster pre-loaded with the deployment + a supervisor override path).
- **Bluetooth pairing fails / version mismatch** → fall back to manual file share (C2 fallback).

## Error handling (fail-soft, non-destructive)

- **Bluetooth transfer interrupted** → smart-sync retries; the enumerator's originals stay intact
  (confirm non-destructive in the C2 spike).
- **Relay fails (no signal)** → collected cases stay on the hub; retry when signal returns.
- **Missing `USERNAME_PASSWORD_DICT`** → ship the roster with the deployment; the login app
  cannot authenticate without it (state this in the deployment SOP).

## Testing

- **Spike gates (must pass before any build):**
  1. **C2:** CSEntry built-in Bluetooth sync — one host collects from ≥2 peers + primary case
     data + non-destructive, on the itel/Android targets.
  2. **C1:** PFF chain-launch + `savesetting`/`loadsetting` + `loadcase` auth on CSPro 8 + itel.
- **Login/role unit:** roster with enumerator + supervisor rows → each routes to the correct
  menu; bad credentials are rejected.
- **Bluetooth integration:** 2–3 enumerator devices → hub collects all → relay → CSWeb shows all
  keys; the same case via direct + hub produces no duplicate/conflict.
- **On-hub QA:** reuse the Phase-1 Supervisor-QA `pytest` suite against the collected `.csdb`.
- **Security:** verify tablet encryption + the wipe-after-relay procedure.

---

## Dependencies & open items (resolve in planning)

1. **C2 Bluetooth mechanism spike** — the gating technical risk; everything downstream assumes it
   passes (else the C2 manual-file fallback governs).
2. **C1 login/menu CSPro-8 spike** — confirm the Khurshid 7.7-era pattern on CSPro 8 + itel.
3. **Roster merge** — whether `USERNAME_PASSWORD_DICT` and the Phase-1 assignment lookup become
   one file; who maintains it.
4. **Trigger condition** — Phase 2 build waits until F1/F3/F4 are near-zero UAT bugs (D7).
5. **Device fleet** — cluster size (enumerators per supervisor) and the itel tablets' encryption
   capability.

## References

- CSPro Synchronization Overview — Internet (CSWeb/Dropbox/FTP) + **Bluetooth peer-to-peer**;
  "the client and server devices must be in close physical proximity in order to connect"
  (no credential/login model documented for the Bluetooth hop).
  <https://www.csprousers.org/help/CSPro/synchronization.html>
- CSPro `SyncServer` (Bluetooth local server) — context for why PROC-level sync is rejected for
  case data (#131). <https://www.csprousers.org/help/CSPro/syncserver_function.html>
- **#131 constraint** + current sync model: `deliverables/CSWeb/Field-Tablet-Sync-Configuration.md`
  (CSPro 8 `syncdata()` = external dicts only; case data via CSEntry built-in Synchronize).
- CSWeb RBAC (the `supervisor-qa` relay role):
  `deliverables/CSWeb/CSWeb-User-Management-and-RBAC-Provisioning-Pack.md` (§2, post-2026-06-21).
- Phase-1 spec + build: `docs/superpowers/specs/2026-06-20-supervisor-app-design.md`;
  `deliverables/CSWeb/supervisor-app/` (the QA report tool reused on-hub).
- Cluster-5 disposition backbone (#515/#561):
  `deliverables/CSPro/F3,F4/generate_*.py` (BREAKOFF + `CASE_DISPOSITION`).
- **Khurshid login + role-based menu pattern** (the adopted C1 mechanism):
  `3_Resources/Learning-Materials/mentors/khurshid-arshad/videos/2022-03-27_tutorial1-create-login-application-in-cspro/`,
  `…/2022-04-05_tutorial-3-writing-cspro-code-and-add-external-dictionary/` (roles
  "Supervisor and Enumerator"; `loadcase` auth),
  `…/2022-04-15_tutorial-1-create-pff-and-menu-application/` (PFF chain-launch + role handoff).
  Note: Khurshid has **no** Bluetooth tutorial — his sync content is CSWeb-only.
- Survey Solutions (World Bank) HQ/Supervisor/Interviewer model — supervisor app as offline
  temporary storage + assignment distribution. <https://docs.mysurvey.solutions/supervisor/supervisor-app/>
