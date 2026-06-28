# Supervisor hub — Khurshid 101-apps adoptions (post-device-confirmation refinements)

> **Status:** planning. Follows the 2026-06-27 ingest of Arshad Khurshid's "101 - Applications" reference
> (analysis: `deliverables/CSPro/supervisor-hub/reference/khurshid-101-applications.md`; vendored source:
> `…/reference/khurshid-101-applications/`). Extends the Phase-2 plan
> (`2026-06-21-supervisor-app-phase2-bluetooth.md`) whose B6/B7 Bluetooth case exchange is now
> **device-confirmed (2026-06-27)** and whose B7 relay is **wired to real logic (C1 below, done)**.

**Goal:** fold the proven Khurshid patterns the hub lacks into the live hub, in a sequence that re-verifies
the device-confirmed build **once**, not repeatedly. Three of these are Carl-requested this round: the menu
**interface** (C3), and the **folder-structure** benchmark/refactor (C6).

**Iron rules (unchanged):** generator-only edits (`build_hub_apps.py`), never hand-edit generated artifacts;
do NOT modify F1/F3/F4 instruments; no git commits (Carl handles git); each functional change re-runs the
gates (compile → strict `.pen` Publish → deploy → 2-tablet device-verify).

**On-device invariant (governs everything below, esp. C6):** CSEntry installs each app by **name** into a
sibling folder `…/files/csentry/<AppName>/`, and the device-confirmed chain-launch resolves instruments via
`../<App>/<App>.pff` and externals via `../<App>/<App>.csdb`. That on-device layout is **fixed** and is
**decoupled from the source folder layout** — which is exactly why C6 (source refactor) is safe.

---

## Task ledger

> **2026-06-28 session (autonomous /goal):** Built **C4** (real coverage report — `forcase`
> counts over the F1/F3/F4 externals + received target; `countcases`/`chr` rejected by the strict
> GLOBAL compile, rewrote with proven idioms) and **C5** (roster `UR_SUPERVISOR_ID`). Gates passed
> (build → MENU+LOGIN compile → MENU strict-publish). Redeployed the LoginApp bundle to prod CSWeb,
> updated the itel via Add Application → CSWeb → **Update**. **Device-verified BOTH menus end-to-end
> on the itel:** enumerator (renders/role-filtered, View-my-report shows live counts `F3:1`, map,
> Conduct-F3 launch + OnExit return, loop, logout) and supervisor (renders, **C1 Relay to CSWeb
> SUCCEEDED on our server** — the success branch fired, cached creds, no prompt; C4 report; Open-F3
> review; loop; logout). **C1 is now DEVICE-CONFIRMED.** Enumerator menu verified on the itel first (role is
> login-driven) while the **Samsung was briefly PIN-locked**, THEN — after it unlocked — the Samsung
> was updated to the latest build (Add Application→CSWeb→Update) and the **enumerator menu was
> verified LITERALLY ON THE SAMSUNG** (renders role-filtered, View-my-report → C4 live counts +
> captured-vs-target, loop, logout). Both tablets on the current build. Training **hub-guide.html
> PUBLISHED LIVE** at csweb.asiansocial.org/docs/hub-guide.html (Carl approved the prod-SSH; backed
> up first). **C6 deferred** (Carl's call; source-only, zero user impact).

| # | Adoption | Value | Risk | State |
|---|---|---|---|---|
| C1 | CSWeb relay **in logic** (B7) | high — one-tap relay | low | ✅ **DONE + DEVICE-CONFIRMED 2026-06-28** (relay-to-CSWeb succeeded on the itel against our server, cached creds) |
| C4b | Live coverage **report** (forcase counts) | med — real per-instrument coverage | low | ✅ **DONE + DEVICE-CONFIRMED 2026-06-28** (both roles; itel showed F3:1 live) |
| C5b | Roster `UR_SUPERVISOR_ID` | low — hierarchy field | low | ✅ **DONE 2026-06-28** (added; loadcase auth re-verified on device) |
| C2 | `InputData=\|type=None` for Login+Menu | med — drops the "tap +" step | low | ⚠ **applied 2026-06-27 but INEFFECTIVE on device** — `\|type=None` does NOT remove the "tap +"/"0 Cases" list (CSEntry shows its own case-list UI for CSWeb-installed apps). The real lever is Khurshid's `StartMode=Add` (set via the Pff object), not `\|type=None` — deferred (marginal UX win) |
| C3 | **Khurshid menu interface** (grouped/sectioned) | med — Carl-requested UX | **med** (replaces a device-confirmed component) | ✅ **C3a DONE — supervisor DEVICE-CONFIRMED 2026-06-27** (grouped menu renders + routes + loops + leave-actions). Enumerator = identical generated code, not separately verified (Samsung dropped off USB). 3 device-caught fixes baked in: menu in **preproc** (reenter is postproc-only; strict-publish catches, lenient misses); loop via **`move to`** not reenter; `move to` target id must be **protected** (noinput is still entered on move-to). C3b (HTML-styled) still optional |
| C4 | **HTMLDialogs** → C8 on-device HTML report (+ optional menu styling) | med — unblocks rich reports | med | planned (spike-first) |
| C5 | Roster hardening: `SUPERVISOR_ID` + encryption (+ optional device-bound login) | med — hierarchy + prod security | low–med | planned (encryption + device-binding are ASPSI-gated) |
| C6 | **Folder-structure refactor** (benchmark Khurshid's per-app subdirs) | med — maintainability | med (touches the device-confirmed build) | planned — **answer to "is this a refactoring?": yes, source-only; see C6** |

---

## C1 — CSWeb relay in logic ✅ DONE (2026-06-27)

Supervisor menu code 09 now runs `relay_to_csweb()` = `syncconnect(CSWeb, url) + syncdata(PUT, F1/F3/F4
dicts) + syncdisconnect()` (creds omitted → CSEntry prompts supervisor-qa once + caches; grounded in
csprousers.org + Khurshid `senddataontheserver`). **Build-valid** (compile + strict `.pen` Publish PASS).
**Remaining:** device-verify the CSWeb-from-logic + supervisor-qa prompt on our server (rides the next deploy).

## C2 — `InputData=|type=None` for Login + Menu

**What:** Khurshid's `Login_App.pff` / `MenuApplication.pff` set `InputData=|type=None`, so those apps store
**no case data** — they open straight to the form/menu. Our LoginApp/MenuApp use real `.csdb` files, so on
device they show a **"0 Cases" list and require a `+` tap** before the form (we noted "straight-to-form is a
future nicety"). This is that nicety.
**Files:** `build_hub_apps.py` `_pff(...)` — emit `InputData=|type=None` for LoginApp.pff + MenuApp.pff.
**Watch:** the `Pff`-object OnExit chain + the menu's single-case model assume a data file today; confirm the
login→menu→instrument→back chain still works with no stored case.
**Gate:** compile + strict Publish + device-verify (login opens straight to username; menu straight to the
choice; chain + OnExit intact).

## C3 — Khurshid menu interface (the grouped/sectioned menu) — *Carl-requested*

**What Carl wants:** Khurshid's menu is a single **`accept(title, …options)`** dialog with **section headers**
(ALL-CAPS, non-actionable) + **indented sub-actions** (`   +   …`), role-built (two option lists), routed by
the returned index, with an invalid-option guard for the header/blank rows. (He optionally styles it via
`choice.html` — see C4.) The value over our current **flat value-set radio field** is the **grouping** —
which scales far better for a long field-ops menu.

**Current vs proposed (adapted to OUR actions):**

```
CURRENT (value-set radio field, device-confirmed)   PROPOSED (Khurshid grouped accept())
  Assign Enumeration Area            ( )              Carla — Supervisor
  Collect Interviews from Enumerators( )              ASSIGNMENTS
  Relay Collected Interviews to CSWeb( )                +  Assign Enumeration Area
  Survey Interview — view report     ( )              COLLECT & RELAY
  View EA on Map                     ( )                +  Collect Interviews from Enumerators
  Open F1 — Facility Head (review)   ( )                +  Relay Collected Interviews to CSWeb
  Open F3 — Patient (review)         ( )              REVIEW & REPORTS
  Open F4 — Household (review)       ( )                +  Survey Interview — view report
  Log out                            ( )                +  View EA on Map
                                                         +  Open F1 / F3 / F4 (review)
  (flat; no grouping; one screen)                     SESSION
                                                         +  Log out
```

**Approach (two sub-options — pick in build):**
- **C3a — plain `accept()` menu** (recommended first): replace the `MENU_CHOICE` value-set field with an
  `accept()`-driven loop in logic (Khurshid's `ViewMenu()` shape). Two grouped option lists by `m_role`;
  route by index; guard the header/blank indices (`elseif Sel_Option in <header rows> then errmsg(...)`).
  Reuses all the existing action functions (`collect_interviews`, `send_to_supervisor`, `receive_assignment`,
  `relay_to_csweb`, `launch_instrument`, `show_ea_map`). No HTML needed.
- **C3b — HTML-styled `accept()`** (optional, bundle with C4): same `accept()` + `choice.html` in an
  `HtmlDialogs` folder + the pff `HtmlDialogs=` property → the full Bootstrap-styled Khurshid look.

**Trade-off to accept:** this **replaces the device-confirmed radio menu** with a new selection mechanism, so
it re-opens menu device-verification (role-filter + every route). Worth it for the grouped UX Carl wants.
**Structural note:** `accept()` is a modal dialog shown from a proc (not a form field), so MenuApp shifts from
"a form with a radio field" to "a proc that shows the menu dialog in a loop" — exactly Khurshid's structure.
**Gate:** compile + strict Publish + device-verify both roles render the grouped menu and every item routes.

## C4 — HTMLDialogs → C8 on-device HTML report (+ optional menu styling)

**What:** `109_HTMLDialogs/choice.html` proves the HTML-in-CSEntry mechanism: an `HtmlDialogs=<folder>` pff
property + the JS bridge `CSPro.getInputData()` / `returnData()` / `setDisplayOptions()`. This is the proven
path we lacked for **C8** (rich offline report) — our report items are currently `errmsg` stubs.
**Spike first (C8):** drop a `report.html` (crib `choice.html`'s Bootstrap+Mustache shell) in an
`HtmlDialogs/` folder, feed it the Phase-1 metrics JSON (coverage / partials #561 / QA flags), render
**offline** on the itel, return to the menu. Then wire the supervisor "Survey Interview — view report" /
enumerator "View my report" items to it (over the hub-collected `.csdb`).
**Reuse for C3b** if the styled menu is wanted (same folder + mechanism).
**Gate:** device-verify the HTML renders offline + returns cleanly; report is PII-light (grep the HTML).

## C5 — Roster hardening

Khurshid's `UsernamePassword.dcf` carries `SUPERVISOR_ID` (enumerator→supervisor hierarchy), `DEVICE_ID`
(tablet binding), and is **encrypted** (`SecurityOptions`). Ours (`UserRoster`) is `username/password/role/
operator_id/cluster` in a **plaintext `.dat` with placeholder `changeme*` creds**.
- **Add `SUPERVISOR_ID`** to `UserRoster` (models "which enumerators report to me" — we only have `cluster`).
- **Encrypt the roster + real creds for prod** (replace placeholders) — *ASPSI-gated (real names/creds).*
- **Optional device-bound login** (`getos()=20 and getdeviceid()=DEVICE_ID` → login only on the assigned
  tablet) — the real-security upgrade past our UX-only login (spec D4). *ASPSI go/no-go; don't build unprompted.*
**Gate:** compile + device-verify login still authenticates with the new roster shape.

## C6 — Folder-structure refactor (benchmark Khurshid's per-app subdirs) — *Carl's question*

**"Is this a refactoring?" — Yes**, and a worthwhile one for maintainability. Our `supervisor-hub/` is a
**flat pile of ~30 mixed files** (both apps' generated files + roster + assignment files + 3 ~2 MB instrument
dcf snapshots + the 26 MB mbtiles + the generator/deploy scripts, all in one dir). Khurshid separates every
app + its data + the HTML dialogs into their own folders.

**The one critical nuance (why this is safe):** Khurshid's per-app subdirs (`101_Login`, `106_Menu`, …) are a
**desktop/source** convention. **On device the layout is fixed** — CSEntry installs each app by name into
`…/csentry/<App>/`, and our device-confirmed chain-launch uses `../<App>/<App>.pff` paths that resolve against
that, **not** against the source folders. So the refactor is **SOURCE-ONLY**: the generator emits into tidy
subdirs and the deploy bundle gathers from them, while the **on-device paths stay byte-identical**.

```
CURRENT (flat)                        PROPOSED (Khurshid-benchmarked, SOURCE-ONLY)
supervisor-hub/                       supervisor-hub/
  build_hub_apps.py                     build_hub_apps.py
  deploy_hub_bundle.py                  deploy_hub_bundle.py
  LoginApp.*                            login/        LoginApp.*            (≙ 101_Login)
  MenuApp.*                             menu/         MenuApp.*             (≙ 106_Menu)
  UserRoster.dcf/.dat                   roster/       UserRoster.dcf/.dat   (≙ 102+103)
  Assignment.dcf/.dat, AS_*.dat,        assignment/   Assignment.*, AS_*.dat, MyAssignment.dat
    MyAssignment.dat                    externals/    FacilityHeadSurvey/Patient/Household .dcf snapshots
  FacilityHeadSurvey.dcf …(3 snaps)     htmldialogs/  report.html, choice.html   (≙ 109_HTMLDialogs)
  survey-basemap.mbtiles                map/          survey-basemap.mbtiles, make_mbtiles.py
  config/ map/ qa/ spikes/ reference/   config/ qa/ spikes/ reference/
```

**What changes:** only `build_hub_apps.py` (emit paths) + `deploy_hub_bundle.py` (gather paths). The
generated `.pff`/`.ent` **on-device** external + chain paths (`../<App>/…`) are untouched.
**Risk:** it does touch the device-confirmed build → a wrong emit path = a broken deploy. So it needs a full
**re-deploy + 2-tablet re-device-verify** of the whole chain (login → menu → assign/collect/send/receive →
relay → map).
**Sequencing:** do C6 **LAST**, after the functional adoptions (C2–C5), so the build is re-device-verified
**once** with everything in place — not re-verified after each change.

---

## Recommended sequence (re-verify the device build once)

1. **C2** `|type=None` (cheap, isolated) →
2. **C3a** grouped `accept()` menu (the interface Carl wants) →
3. **C4** HTMLDialogs C8 report spike → wire reports (+ optionally C3b styled menu) →
4. **C5** roster `SUPERVISOR_ID` (+ encryption/device-binding when ASPSI says) →
5. **C6** source folder refactor →
6. **one** deploy + 2-tablet device-verify of the whole chain (also clears C1's pending relay verify).

Each task is generator-only + gated; C1 is done. Spec note: the Phase-2 design spec's flat-radio menu is
**superseded** by C3 (grouped menu) — fold into a spec ADDENDUM when C3 is built.

## Open decisions for Carl
- **C3**: plain `accept()` menu (C3a) first, or go straight to HTML-styled (C3b)? *(Recommend C3a first.)*
- **C5**: encrypt the roster / device-bind login now, or hold for ASPSI? *(Recommend: add SUPERVISOR_ID now;
  hold encryption+device-binding for ASPSI.)*
- **C6**: green-light the source refactor (sequenced last)? *(Recommend yes — our flat dir is unwieldy.)*
- **Execution order**: build C2→C6 in one pass with a single end device-verify, or stop-and-verify per task?
