# Supervisor-hub role menus -> styled UI (htmldialog("menu.html") from logic — prompt-free AND secure)

**Date:** 2026-07-01  **Status:** DONE — option (c) built, DEPLOYED to CSWeb 2026-07-02, and BOTH role menus DEVICE-VERIFIED on the itel (CSEntry 8.0.1): styled render + NO "Allow Access?" prompt + routing round-trip, for Enumerator (se-001) and Supervisor (fs-01). **ROUND 2 (same day): CSEntry 8.1 blank-menu regression found + FIXED** (dual bridge + registered access token + pff `[DataEntryInit]`), redeployed, and DEVICE-VERIFIED on the Samsung A23 (8.1.1) off the clean server package — see the 8.1 section below.
**Component:** deliverables/CSPro/supervisor-hub (menu.html + build_hub_apps.py + deploy_hub_bundle.py)

## Problem
The Enumerator/Supervisor role menus rendered as CSEntry's default `accept()` list. The coverage
report already has a styled HTML UI (report.html, green theme). Bring the menus to the same look —
without the security downgrade the first approach required.

## Final approach (device-verified) — call htmldialog() from the menu logic
Drop the native `accept()`. `MENU_PICK`'s preproc builds a per-role JSON menu and calls
`htmldialog("menu.html", inputData := menuJson, displayOptions := dopt)`, then routes on the returned
string. `menu.html` returns the chosen action wrapped as `<<action>>`; the logic routes with
`pos("<<action>>", res) > 0` branches. Because `htmldialog()` goes through the **deprecated `CSPro.*`
interface** (not the modern Action Invoker / `CS.UI`), it does **NOT** trip CSEntry's external-caller
consent gate — so the menu is **prompt-free AND keeps the secure default**
(`accessFromExternalCaller = promptIfNoValidAccessToken`). This is the same channel report.html uses
(`show_coverage_report` → `htmldialog("report.html")`), so no new security surface.

## What was built
1. `menu.html` (NEW, app folder) — self-contained styled menu (inline CSS/JS, green `#00532f` theme).
   Input `{title, groups:[{header, items:[{label,action}]}]}`. `csGetInput()` tries `CS.UI` then
   `CSPro.getInputData()` (object OR string). Renders group headers (`.gh`) + tappable rows (`.item`,
   chevron). On tap, `csReturn(action)` returns `payload = "<<"+action+">>"` (tries `CS.UI.closeDialog`
   then `CSPro.returnData`). Self-sizes via `csSetDisplay`.
2. `build_hub_apps.py` — `MENU_PICK` preproc rewritten from `accept()` to `htmldialog("menu.html")`:
   - `_menu_json_expr(role_label, grouped)` builds the inputData JSON as a **chunked `concat()`**
     expression (each string literal <=180 chars) injecting the live `strip(m_op)` operator id — guards
     against any CSPro string-literal length limit.
   - `_routing_block()` emits `pos("<<key>>", res) > 0` branches for every `MENU_ACTIONS` key, plus a
     defensive `else move to MENU_SESSION;` fallback (cancel/back or an unexpected return silently
     re-shows the menu). The bring-up `errmsg("(debug) menu returned: …")` diagnostic was REMOVED
     2026-07-02 after routing was device-proven on both 8.0.1 and 8.1; rebuilt + redeployed +
     Samsung-verified (back-key now silently loops the menu, no popup).
   - `build_ent` keeps `accessFromExternalCaller = "promptIfNoValidAccessToken"` (secure).
   - `MenuApp.pff` carries NO `HtmlDialogs` override (reverted — not needed for htmldialog()).
   - `*_MENU_GROUPED` + `MENU_ACTIONS` (menu content + routing targets) unchanged — single source.
3. `deploy_hub_bundle.py` — `menu.html` in BUNDLE (swapped in for `choice.html`).

## The debugging that got here (so we don't repeat it)
- CSEntry runs the compiled `.pen`, not `.apc`/`.ent` — logic/settings changes need a recompile
  (add/re-add), NOT a hot-push. Only runtime assets (menu.html, report.html, .pff, mbtiles) hot-swap.
  Deleting the `.pen` breaks the app; a REINSTALL-over-existing poisons extraction ("Error extracting
  application") → fix = wipe the on-device app folder (`rm -rf`) then a fresh INSTALL (shows as INSTALL,
  not REINSTALL, in Add Application → the clean-extract path).
- FIRST approach (superseded): restyle the native `accept()` via the pff `HtmlDialogs=.` + a custom
  `choice.html` using the **Action Invoker** (`CS.UI.closeDialog({result:{index}})` via
  `/action-invoker.js`; the deprecated `CSPro.returnData` path FAILS "not an object: 'index'"). It
  rendered + routed, but popped "Allow Access?" on EVERY show. Removing that needs
  `grantAccessWithoutPrompting`, which the automated security review flagged HIGH (disables consent for
  ALL external callers; the token in the readable choice.html stops being a secret → any app/webpage/QR
  could reach CSPro + survey PII). Reverted. That tradeoff is why we moved to the htmldialog() path.
- `choice.html` remains in the repo + deploy package as an inert leftover (nothing references it now:
  `MenuApp.pff` has no `HtmlDialogs`, and the logic calls `htmldialog("menu.html")`). Harmless dead weight.

## Verified on device (itel CSEntry 8.0.1, 2026-07-02, fresh CSWeb install)
- Enumerator (se-001): green grouped menu (ASSIGNMENT / INTERVIEWS / REPORTS / SESSION) renders, NO
  consent prompt; "View my report" routed to `show_coverage_report` → "MY INTERVIEW COVERAGE" (F3=2);
  menu re-shows after OK (MENU_SESSION loop, still no prompt); "Log out" routed back to LoginApp.
- Supervisor (fs-01): green grouped menu (ASSIGNMENTS / COLLECT & RELAY / REVIEW & REPORTS / SESSION)
  renders, NO consent prompt; "Survey Interview - view report" routed to the supervisor coverage
  variant ("SURVEY COVERAGE - interviews collected at this hub").
- KEY PROOF: the `htmldialog()` return round-trips — `<<action>>` wrapping + `pos()` survives whatever
  encoding CSEntry applies to the returned string. This was the one unproven risk; it works.

## CSEntry 8.1 regression + fix (round 2, 2026-07-02) — the blank menu Carl hit on the Samsung
- The Samsung A23 runs CSEntry **8.1.1-20260622** (the itel runs 8.0.1). On 8.1 the deprecated
  `CSPro.*` bridge still EXISTS inside htmldialog web views but is **SEVERED**:
  `CSPro.getInputData()` returns `""` (empty string, not null) and `CSPro.returnData()` is a silent
  no-op. menu.html's round-1 code only fell through to `CS.UI` when the input was `null`, so it
  parsed `""` → `{}` → zero groups → **blank menu**. The CSWeb package IS the tester-facing build,
  so every tester on CSEntry 8.1.x had a blank menu until this fix (8.0.1 devices were fine).
- **Fix 1 — dual bridge with BRIDGE tracking** (menu.html + report.html): treat `""` as no-input and
  fall through to the Action Invoker (`<script src="/action-invoker.js">` +
  `new CSProActionInvoker(<hub token>)` + `CS.UI.getInputData()`); record which side delivered the
  input (`BRIDGE = "cspro" | "ai"`) and RETURN through the SAME side
  (`A.UI.closeDialog({result: payload})` on 8.1) — returning via the dead `CSPro.returnData` first
  would leave the dialog stuck open. `csSetDisplay` routes by BRIDGE the same way.
- **Fix 2 — registered access token** (`build_hub_apps.py` `HUB_ACCESS_TOKEN`, emitted into both
  .ents' `logicSettings.actionInvoker.accessTokens`): a caller presenting a REGISTERED token gets NO
  "Allow Access?" prompt while `accessFromExternalCaller` STAYS the secure
  `promptIfNoValidAccessToken` (confirmed in csprousers/cspro source, zAppO/LogicSettings.cpp). This
  is the secure alternative to the rejected `grantAccessWithoutPrompting`: the token only helps a
  caller already running inside the app's own web view.
- **Fix 3 — pff `[DataEntryInit]`** with `StartMode=Add` + `Lock=CaseListing` (both .pffs, emitted by
  `_pff()` whenever `input_data` starts with `|`): 8.1 showed an empty "0 Cases" case listing for the
  `|type=None` input where 8.0.1 auto-started; now both apps open straight at the first field.
- **Verified on the Samsung A23 (8.1.1) off the CLEAN server package** (hashes device == repo:
  menu.html `5ee3641b…`, report.html `fefb8f87…`, MenuApp.pff `adf6b5d7…`): login opens straight at
  Username (no case list), styled se-001 Enumerator menu renders, "View my report" → "MY INTERVIEW
  COVERAGE" (F3=2), OK → menu loops. The itel path is untouched by design (`CSPro.*` is still tried
  first; on 8.0.1 it answers, BRIDGE="cspro", and the return uses `CSPro.returnData` exactly as
  verified in round 1) — a physical itel re-check is a low-risk pending item.
- **Rollout nuance:** THIS redeploy WAS picked up on the A23 by Add Application → CSWeb → **UPDATE**
  ("New version available"), hash-verified. Treat remove/wipe + re-add as the reliable fallback, but
  try UPDATE first and verify by hash or behavior.

## Deploy / fleet rollout
Recompile+redeploy pipeline: regenerate (`build_hub_apps.py`) → CSPro Designer File>Publish&Deploy of
LoginApp (the strict-publish compile passing = the dialog opening) → `deploy_hub_bundle.py` (stage) then
`--deploy-only` (push to CSWeb) → device **remove/wipe + re-add** LoginApp (that install regenerates the
`.pen`). "Update Installed Applications" does NOT pull a redeploy — every tablet needs the remove+re-add.
Only the itel is adb-reachable here; other tester tablets must each do CSEntry → Add Application → CSWeb →
LoginApp → INSTALL (wipe/remove first if it still shows REINSTALL).
