# Khurshid "101 - Applications" — reference ingest for the Supervisor hub

**Source:** Arshad Khurshid CSPro tutorial set (`C:\Users\analy\Downloads\101 - Applications`), CSPro 7.7.
**Ingested:** 2026-06-27, to mine the *logic* for the Supervisor hub (`deliverables/CSPro/supervisor-hub/`).
**Why it matters:** this is the exact login→menu→listing→HH→sync pattern our hub is built on. The hub
already matches its **structure**; this ingest pulls out the **3 working mechanisms we don't yet have**
(CSWeb relay in logic, HTMLDialogs, `|type=None`) plus several smaller upgrades.

## The module map (and what each gave us)

| Module | What it is | Hub equivalent |
|---|---|---|
| `101_Login` | Login app (auth + role handoff + chain-launch) | **LoginApp** |
| `102_Ext_Dic` + `103_Ext_Data` | `UsernamePassword.dcf` + `.csdb` (the roster, **encrypted**) | **UserRoster** |
| `104_Excel` / `105_ExcelToCSPro` | Excel→CSPro roster import (`.xl2cs`) | — (roster-build tooling) |
| `106_Menu` | Role-routing menu + chain-launch + **CSWeb relay** | **MenuApp** |
| `107_Listing` | Listing data-entry app (chain-launched) | the descoped **B5** leg |
| `108_Data` | Per-login data files `L_<id>.csdb` / `HH_<id>.csdb` | (we use one shared instrument `.csdb`) |
| `109_HTMLDialogs` | `choice.html` — custom HTML dialog (Bootstrap+jQuery+Mustache) | the deferred **C8** report spike |
| `110_HH` | "Census Data Entry" — the real instrument w/ skip logic | F1/F3/F4 |

---

## What the hub ALREADY matches (confirmation, no action)

- **`loadcase(USERNAMEPASSWORD_DICT, id)` auth against an external roster dict** → our `LOGIN_PASSWORD`
  postproc does exactly this against `UserRoster`.
- **`savesetting`/`loadsetting` role handoff** between apps → ours (`hub_role`, `hub_operator_id`, …).
- **`pff` object + `setproperty(…) + setproperty("OnExit", …) + exec()` chain-launch with return** →
  ours (`launch_instrument`). Khurshid points `"Application"` at the `.ent` and sets `InputData`/`OnExit`
  explicitly; we load the instrument's own `.pff`. Both are valid; his is more explicit per-launch.
- **Role-routed menu** (supervisor vs enumerator) → ours via `setvalueset` value-set swap. **Khurshid uses
  `accept()`** (a numbered text dialog) instead — ours (radio value-set) is the nicer UX and is already
  device-confirmed, so keep ours.

---

## The 3 mechanisms worth ADOPTING (the high-value finds)

### 1. ⭐ Working CSWeb relay **in logic** — fills our B7 gap

We shipped "Relay Collected to CSWeb" as an **SOP-reminder errmsg** because we didn't want to ship an
unverified `syncconnect(CSWeb)`-from-logic. **Khurshid proves the exact pattern** (`106_Menu`,
`senddataontheserver()`):

```cspro
PROC GLOBAL
config sendhhdata;            { a named sync config (holds the CSWeb server + creds) }

Function senddataontheserver()
  if syncconnect(CSWeb, sendhhdata) = 1 then
     setfile(CEN2000, "..\108_Data\HH_Data\HH_1511.csdb");
     syncdata(PUT, CEN2000);
     syncdisconnect();
  endif;
end;
```

So the real relay = **`config <name>;`** (declare a CSWeb sync config) → **`syncconnect(CSWeb, <config>)`**
→ **`syncdata(PUT, <dict>)`** → **`syncdisconnect()`**. The `config` object is configured once (server URL +
credentials), referenced by name. This is the one-tap relay we wanted.
- **For the hub:** add a `config supervisor_qa_relay;` and turn the supervisor menu code 09 from the SOP
  errmsg into `syncconnect(CSWeb, supervisor_qa_relay)` + `syncdata(PUT, …)` for each collected instrument
  dict, under the `supervisor-qa` account. **Device-verify** the CSWeb-from-logic + creds (the one thing
  Khurshid's reference doesn't prove on *our* server).

### 2. ⭐ `InputData = |type=None` for Login + Menu — removes the "tap +" step

Khurshid's `Login_App.pff` / `MenuApplication.pff`:

```
[Files]
Application=.\Login_App.ent
InputData=|type=None          { <-- the login/menu apps store NO case data }
HtmlDialogs=..\109_HTMLDialogs
```

Our LoginApp/MenuApp use real `.csdb` files, so on device they show a **"0 Cases" list and you must tap +**
(we noted "straight-to-form is a future nicety"). `|type=None` is that nicety: the app runs transiently with
no case list — login opens straight to the username field, the menu straight to the choice. Clean UX win,
low risk.
- **For the hub:** set `InputData=|type=None` in `LoginApp.pff` and `MenuApp.pff` (generator: `_pff(...)`).
  Watch the interaction with the `Pff`-object OnExit chain (we keep cases out anyway), and re-device-verify.

### 3. HTMLDialogs mechanism — unblocks the deferred C8 (rich on-device report)

`109_HTMLDialogs/choice.html` is a full custom dialog (Bootstrap + jQuery + Mustache) wired to CSEntry via:
- the **`HtmlDialogs=..\109_HTMLDialogs` pff property** (Khurshid also sets it dynamically:
  `menuapp_pff.setproperty("HTMLDialogs", "..\109_HTMLDialogs")`),
- and the JS bridge: **`CSPro.getInputData()`** (read the JSON CSPro passes in), **`CSPro.returnData(json)`**
  (return the user's choice), **`CSPro.setDisplayOptions({width,height,…})`** (size the dialog).

We deferred C8 ("can CSEntry render a generated HTML report offline?") for lack of a proven mechanism — and
**this is the proven mechanism.** It confirms HTML-in-CSEntry works offline; a report becomes an HTML doc fed
`CSPro.getInputData()` (the coverage/partials/flags JSON) and rendered with a Mustache template like
`choice.html`. (Note: `choice.html` overrides the *accept/select* dialog specifically; a standalone report
would be invoked as its own HTML dialog/userbar, but the bridge API is identical.)
- **For the hub:** a small C8 spike — drop a `report.html` in an `HTMLDialogs/` folder, feed it the Phase-1
  metrics JSON, render offline. Upgrades the current `errmsg` report entry points to the rich version.

---

## Smaller upgrades (roster + data model)

### Roster fields — Khurshid's `UsernamePassword.dcf` carries more than ours

| Khurshid field | Ours (`UserRoster`) | Worth adding? |
|---|---|---|
| `USERNAMEPASSWORD_ID` (4-num key) | `UR_USERNAME` (20-alpha key) | ours is fine |
| `USER_PASSWORD`, `USER_NAME`, `ROLE` | `UR_PASSWORD`, (name n/a), `UR_ROLE` | parity |
| **`SUPERVISOR_ID`** (enumerator→supervisor link) | — | **yes** — models the hierarchy ("who reports to me"); we only have `cluster` |
| **`DEVICE_ID`** (20-alpha, the tablet binding) | — | **optional security** — see below |
| `GENDER` | — | not needed |
| `SecurityOptions=…` (the **dcf/csdb is encrypted**) | plaintext `.dat` | **yes for prod** — encrypt the roster (we ship placeholder `changeme*` creds in a plaintext `.dat`) |

### Device-ID-bound login — the real-security upgrade path (D4)

Our login is a UX/identity gate only (spec D4). Khurshid shows how to make it *real* security
(`101_Login`, `LOGIN_APP_ID` postproc):

```cspro
if getos() = 20 and getdeviceid() = USERNAMEPASSWORD_DICT.DEVICE_ID then   { Android: bind to THIS tablet }
   …login ok…
elseif getos() = 10 then                                                   { Windows: skip device check }
   …login ok…
else
   errmsg("Entered Login ID is Not for this Tablet"); reenter;
endif;
```

i.e. on Android the login only succeeds if the tablet's `getdeviceid()` matches the `DEVICE_ID` stored in the
roster for that user. **This is the upgrade if ASPSI ever wants login tied to assigned tablets** — surface as
an ASPSI go/no-go, don't build unprompted (D4 says UX-only for now).

### Per-login data files — `L_<id>.csdb` / `HH_<id>.csdb`

Khurshid keys each enumerator's data file by login id (`InputData=concat("..\…\HH_", loadsetting("Save_LoginID"), ".csdb")`).
We use the instrument's single shared `.csdb` and rely on the 12-digit key for conflict-free merge (proven).
The per-login approach is an alternative for keeping each enumerator's cases isolated on the hub before merge —
**lower priority**, our syncdata-by-key merge already works.

---

## Notes / non-adoptions

- **`accept()` menu + `choice.html`** — Khurshid styles his `accept()` menu via the HTML dialog override. Our
  value-set radio menu is already nicer and device-confirmed; keep ours. (But `choice.html` is the template to
  crib for C8.)
- **App versioning** (`Version.txt` + `APP_VERSION` proc reading the latest version line) — minor; our deploy
  story is CSWeb redeploy + Add→CSWeb UPDATE (which *does* detect new versions; see the supervisor-app memo).
- **Multi-language** (`setvaluesets("_" + getlanguage())`, EN/UR) — ties to our separate translations pipeline,
  not the hub.
- **Listing app (`107_Listing`)** — present here as a chain-launched skeleton (the listing *form* lives in the
  dcf). Confirms the B5 mechanics, but our B5 block was the **unauthored Survey-Manual §3a auto-tag rule**
  (a spec gap, ASPSI's call) — not the app mechanics — so this doesn't unblock B5 by itself.

---

## Recommended next actions (Carl's pick)

1. ~~Wire the logic CSWeb relay (B7)~~ **✅ DONE 2026-06-27** — supervisor code-09 now runs `relay_to_csweb()`
   = `syncconnect(CSWeb, url) + syncdata(PUT, F1/F3/F4 dicts) + syncdisconnect()` (used the grounded
   `syncconnect(CSWeb,url[,user,pass])` form, not the bare `config` — creds prompted-once-then-cached).
   Build-valid (compile + strict `.pen` Publish PASS). **Device-verify pending** the next hub deploy
   (CSWeb-from-logic + supervisor-qa prompt on our server is the one unproven bit).
2. **Switch Login/Menu to `InputData=|type=None`** — drop the "tap +" step. *(cheap UX win)*
3. **C8 spike via HTMLDialogs** — render a real offline HTML report from the Phase-1 metrics JSON. *(unblocks
   rich reports)*
4. **Harden the roster** — add `SUPERVISOR_ID`, encrypt the roster for prod (replace placeholder creds).
5. *(ASPSI-gated)* **Device-ID-bound login** — only if real per-tablet security is wanted.
