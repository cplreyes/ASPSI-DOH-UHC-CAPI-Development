# 101_login — Login Application Spec

Front door for everyone (RA, supervisor, ops). Validates credentials against
`user_roster.dcf`, savesetting()s session identity, PFF-launches `106_menu`.

## Dictionary (LOGIN_DICT)

Single-level. One ID item, one input record.

### ID items
- `LOGIN_APP_ID` (numeric, length 4, zero-fill) — fixed at 1, single-case session

### Record: LOGIN_REC
- `LOGIN_RA_ID`   (numeric, length 4, zero-fill)  — what the user types
- `LOGIN_PW`      (alpha,   length 40)            — what the user types
- `LOGIN_ROLE`    (numeric, length 1)             — populated from lookup, protected
- `LOGIN_NAME`    (alpha,   length 40)            — populated from lookup, protected
- `APP_VERSION`   (alpha,   length 16)            — populated by PROC, protected

## External dictionary (loaded for lookup)
- `USER_ROSTER_DICT` from `..\102_EXT_DIC\user_roster.dcf`

## Form (FORM000 — Login)
- LOGIN_RA_ID    (numpad, max 9999)
- LOGIN_PW       (text, masked)
- LOGIN_NAME     (protected, populated post-lookup)
- LOGIN_ROLE     (protected; displayed via VS_ROLE_LABEL value set: 1=Supervisor, 2=Enumerator, 3=Ops)
- APP_VERSION    (protected; populated by PROC from publishdate())

## Logic

### LOGIN_PW.postproc
1. `loadcase(USER_ROSTER_DICT, LOGIN_RA_ID)` — fetch user record
2. If lookup fails → errmsg("Unknown RA ID") + reenter LOGIN_RA_ID
3. If `sha256(LOGIN_PW) <> USER_ROSTER_DICT.PASSWORD_HASH` → errmsg("Incorrect password") + reenter
4. Else:
   - `LOGIN_NAME = USER_ROSTER_DICT.RA_NAME`
   - `LOGIN_ROLE = USER_ROSTER_DICT.ROLE`
   - `savesetting("login_id", LOGIN_RA_ID)`
   - `savesetting("login_roll", LOGIN_ROLE)`
   - `savesetting("supervisor_id", USER_ROSTER_DICT.SUPERVISOR_ID)`
   - call `start_menu()` — PFF-launches `..\106_menu\menu_app.pen`

### LEVEL.preproc
- `#include "..\shared\Expiration-Guard.apc"` then `check_expiration()`
- Set `APP_VERSION` from `publishdate()`

## Mentor source
- Authenticate-then-launch postproc pattern: Tutorial 1: Create Login Application in CSPro @ 03:43
- savesetting handoff: Tutorial 1: Create PFF and Menu Application @ 04:18
- PFF launch: Tutorial 1: Create PFF and Menu Application @ 04:34

## Phase 1 password gap (resolve in Phase 2)

CSPro 8.0 doesn't natively SHA-256. The `.apc` Phase 1 fallback compares
plaintext (with `build_username_dict.py` reverted to store plaintext rather
than SHA-256 in the .dat) so the login flow can be smoke-tested end-to-end.
Phase 2 either: (a) pre-hash on the device via `httpaction()` calling a
local helper, or (b) use the new CSPro Action Invoker `Hash.createHash`
(per CSPro 8.0 release notes — line 138 of readme.txt).
