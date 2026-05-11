# 106_menu — Menu Application Spec

Role-conditional menu. Reads loadsetting("login_roll") to decide which menu to render.
PFF-launches the chosen instrument.

**Phase 1 scope:** Enumerator menu with 2 choices — F1 + F3 listing (F3LIST).
**Phase 2 will add:** PLF, F3 entry, F4_listing, F4 + full Supervisor menu;
   will also enforce "must-run-listing-before-F3" ordering (currently the
   operator picks freely between F1 and F3LIST).

## Dictionary (MENU_DICT)

Single-level. One ID, one record carrying the loaded session identity.

### ID items
- `MENU_APP_ID` (numeric, length 4, zero-fill)

### Record: MENU_REC
- `MENU_LOGIN_ID`     (numeric, 4)  — from loadsetting, protected
- `MENU_LOGIN_NAME`   (alpha, 40)   — looked up, protected
- `MENU_ROLE`         (numeric, 1)  — from loadsetting, protected
- `MENU_SUP_ID`       (numeric, 4)  — from loadsetting, protected
- `APP_VERSION`       (alpha, 16)

## External dictionary
- `USER_ROSTER_DICT` from `..\102_EXT_DIC\user_roster.dcf`

## Form (FORM000)
All fields protected. Welcome banner only.

## Logic

### LEVEL.preproc
- `#include "..\shared\Expiration-Guard.apc"` -> `check_expiration()`
- `MENU_LOGIN_ID = tonumber(loadsetting("login_id"))`
- `MENU_ROLE     = tonumber(loadsetting("login_roll"))`
- `MENU_SUP_ID   = tonumber(loadsetting("supervisor_id"))`
- `loadcase(USER_ROSTER_DICT, MENU_LOGIN_ID)` -> set `MENU_LOGIN_NAME`
- `setattributes(<all fields>, protect, on)`
- Call `view_menu()`

### view_menu()
- If `MENU_ROLE = 2` (enumerator): accept() with 2 choices:
    1. "Conduct facility interview (F1)"
    2. "Patient listing session (F3 listing)"
- Else (supervisor / ops): errmsg "Supervisor menu not yet enabled (Phase 2)" + stop(0)

### launch_F1()
- PFF-launch `..\107_F1\FacilityHeadSurvey.pen` with OnExit returning to menu.

### launch_F3LIST()
- PFF-launch `..\110_F3_listing\PatientListing.pen` with OnExit returning to menu.

## Mentor source
- Role-conditional accept(): Tutorial 2: Create PFF and Menu @ 04:15
- setattributes for protect: Tutorial 2 @ 02:45
- tonumber on loadsetting: Tutorial 2 @ 02:00
