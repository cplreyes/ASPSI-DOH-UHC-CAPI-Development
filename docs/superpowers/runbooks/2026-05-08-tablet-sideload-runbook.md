---
title: Android tablet sideload + first sync
type: runbook
date: 2026-05-08
status: active
applies_to: UHC Survey System Plan 1, Phase 9
---

# Android tablet sideload + first sync

One-time bring-up of an Android tablet for UHC Survey CAPI. After this, the tablet just connects to your laptop's Wi-Fi and syncs.

## Prereqs (already complete)

- ✅ Wampserver64 running with CSWeb 8.0.1 at `http://localhost/csweb8.0.1/`
- ✅ MySQL `csweb` DB populated with full schema (27 tables)
- ✅ Carl has admin credentials for CSWeb UI
- ✅ All 3 instrument `.ent` files generated for UAT env with LAN IP spliced in

## What you (Carl) still need to do

### Step 1: F7-publish each instrument in Designer

Per the F7 runbook (`2026-05-08-cspro-publish-entry-runbook.md`), open CSPro Designer and publish:

```
deliverables/CSPro/UHC-Survey-System/101_login/login_app.ent       → login_app.pen
deliverables/CSPro/UHC-Survey-System/106_menu/menu_app.ent         → menu_app.pen
deliverables/CSPro/UHC-Survey-System/107_F1/FacilityHeadSurvey.ent → FacilityHeadSurvey.pen
```

If Designer rejects the login or menu `.ent` due to schema-shape differences (login + menu use a simplified shape vs F1's real CSPro 8.0 shape), the fix is in `101_login/generate_dcf.py` and `106_menu/generate_dcf.py` — bring the schema into line with F1's (use `labels: [{text: ...}]` arrays, `contentType` not `type`, `ids: {items: [...]}`).

### Step 2: Upload `.pen` files to CSWeb

1. Open `http://localhost/csweb8.0.1/ui/login` in a browser
2. Log in with your admin credentials
3. Click **Apps** in the left nav
4. For each `.pen`: **Add Application** → upload → save
5. Verify all 3 appear in the apps list

### Step 3: Install CSPro Android APK on the tablet

Download CSPro Android from <https://www.csprousers.org/products/cspro-android>. APK is named `CSPro-8.0.1.apk` or similar.

Enable Developer Options on the tablet (Settings → About tablet → tap Build number 7 times) and enable USB debugging.

Plug tablet to laptop via USB. Run from PowerShell (with [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools) installed):

```powershell
adb install path\to\CSPro-8.0.1.apk
```

If you don't have ADB, install Platform Tools first (~10MB):
```powershell
# Quick install: download zip from the Android site, extract anywhere, add to PATH
# Or via chocolatey: choco install adb
```

### Step 4: Configure sync server in CSPro Android

Open CSPro app on tablet:
- Settings (gear icon) → **Sync server**
- Server URL: `http://192.168.1.168/csweb8.0.1/api/`
- Username: `Application_Name` admin user (whatever Carl created during prior CSWeb setup)
- Password: as set in CSWeb Users tab

Tap **Test connection** — expect green "OK".

> **If "Could not reach server":** ensure tablet and laptop are on same Wi-Fi. Open Windows Firewall on port 80 if blocked: `New-NetFirewallRule -DisplayName "Apache 80" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow`. Verify your laptop's LAN IP hasn't changed since the .ent was built (`Get-NetIPAddress`).

### Step 5: Pull the 3 apps to the tablet

In CSPro Android:
- **Synchronize → Get applications**
- Should pull `login_app.pen`, `menu_app.pen`, `FacilityHeadSurvey.pen`

### Step 6: Test login → menu → F1 flow

On tablet:
1. Tap `login_app` from the app list
2. Enter RA ID `2001` (Test RA Alpha) and password `ra-pass-01`
3. Should PFF-launch into menu app, "Welcome Test RA Alpha — Enumerator Menu"
4. Tap "Conduct facility interview (F1)"
5. F1 form should open. Walk through the first form (Field Control items), enter a few fields, save
6. Return to menu, exit

> **Phase 1 password gap (per spec §7):** the .apc currently does plaintext compare. The user_roster.dat stores SHA-256 hashes. Before this works end-to-end, either: (a) re-run `shared/build_username_dict.py` after temporarily changing `_hash_password()` to `_pad_alpha(plaintext, 64)`, or (b) hand-update user_roster.dat to plaintext-padded passwords. Phase 2 will fix this properly via CSPro 8.0's Action Invoker `Hash.createHash`.

### Step 7: Sync cases back to CSWeb

In CSPro Android:
- **Synchronize → Send data**
- Expect green checkmark per dictionary
- Open `http://localhost/csweb8.0.1/ui/login` in browser → **Data** tab → F1 dictionary → confirm new case appears

### Step 8: Verify case in MySQL

```powershell
$mysql = (Get-ChildItem 'C:\wamp64\bin\mysql\' -Directory | Sort -Desc Name | Select -First 1).FullName + '\bin\mysql.exe'
& $mysql -u root -e "USE csweb; SELECT COUNT(*) AS f1_cases FROM cspro_cases WHERE name LIKE '%FACILITY%';"
```

Or open phpMyAdmin at `http://localhost/phpmyadmin/`, click `csweb` database, browse the `cspro_cases` table.

## Success criteria for Phase 9

- [ ] All 3 `.pen` files exist alongside their `.ent`
- [ ] All 3 `.pen` files uploaded to CSWeb Apps tab
- [ ] CSPro Android on tablet connects to local CSWeb (Test connection green)
- [ ] Login app authenticates RA 2001
- [ ] PFF chain launches menu, then F1
- [ ] Synthetic F1 case completes and saves to local CSDB
- [ ] Sync push uploads case to CSWeb
- [ ] Case visible in CSWeb Data tab AND in MySQL `cspro_cases` table

## When this is done

- Update Task 17 status to `completed`
- Continue to Phase 10 (CSBatch consistency) and Phase 11 (CSExport STATA/SPSS/CSV)

## Related

- F7 runbook: `2026-05-08-cspro-publish-entry-runbook.md`
- Plan 1: `docs/superpowers/plans/2026-05-08-uhc-survey-system-build-phase-1.md`
- Mentor: Khurshid Arshad, [Tutorial 4: Deploy Application @ 11:17](https://www.youtube.com/watch?v=hil_SpX_fsA&t=677s) (live IP vs localhost)
