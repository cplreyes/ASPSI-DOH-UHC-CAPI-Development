<#
.SYNOPSIS
  CSEntry screenshot helper for the enumerator field guide. Boots the Android tablet
  emulator, ensures CSEntry is installed, and captures named screenshots via adb — so
  producing the guide's images is one command each.

.WHY
  The survey-app screenshots for `2026-06-07-CSEntry-Enumerator-App-Guide.md` must come from
  the real Android UI (CSEntry on Windows renders a *desktop* window, not the tablet). Capture
  is fully automatable (adb); the in-app navigation + CSWeb sync are done by hand in the emulator
  window because CSEntry's UI isn't reliably scriptable via the accessibility tree.

.PREREQS
  - Android SDK at %LOCALAPPDATA%\Android\Sdk (platform-tools + emulator) with an AVD named 'capi_tablet'.
    (Create once:  avdmanager create avd -n capi_tablet -k "system-images;android-34;google_apis;x86_64" -d pixel_tablet)
  - CSEntry APK (gov.census.cspro.csentry) — official: https://www.csprousers.org/apk/

.WORKFLOW
  1) .\capture-csentry-screenshots.ps1 -Setup -Apk C:\path\to\csentry-8.0.1.apk
     (boots a *windowed* emulator, installs CSEntry, grants perms, launches it)
  2) In the emulator window: CSEntry > menu > Sync > add server https://csweb.asiansocial.org/csweb
     > sign in > download the F1/F3/F4 survey > open a case and navigate.
  3) At each screen you want, capture it (name to match the guide's [SCREENSHOT: ...] markers):
       .\capture-csentry-screenshots.ps1 -Shot 05-id-block
       .\capture-csentry-screenshots.ps1 -Shot 06-single-choice
  4) .\capture-csentry-screenshots.ps1 -Kill
#>
param(
  [switch]$Setup,
  [string]$Shot,
  [string]$Apk,
  [switch]$Kill,
  [string]$Avd = "capi_tablet",
  [string]$OutDir = "$PSScriptRoot\csentry-screenshots"
)
$ErrorActionPreference = "Stop"

$sdk    = if ($env:ANDROID_SDK_ROOT) { $env:ANDROID_SDK_ROOT } else { "$env:LOCALAPPDATA\Android\Sdk" }
$adb    = Join-Path $sdk "platform-tools\adb.exe"
$emu    = Join-Path $sdk "emulator\emulator.exe"
$pkg    = "gov.census.cspro.csentry"
$serial = "emulator-5554"
if (-not (Test-Path $adb)) { throw "adb not found at $adb — set `$env:ANDROID_SDK_ROOT or install the SDK." }
function Running { (& $adb devices) -match $serial }

if ($Kill) {
  if (Running) { & $adb -s $serial emu kill 2>$null; "Emulator $serial killed." } else { "No emulator running." }
  return
}

if ($Setup) {
  if (-not (Test-Path $emu)) { throw "emulator not found at $emu" }
  if (-not (Running)) {
    Write-Host "Booting '$Avd' (windowed)..."
    Start-Process -FilePath $emu -ArgumentList @("-avd",$Avd,"-no-audio","-no-snapshot","-gpu","swiftshader_indirect")
  } else { Write-Host "Emulator already running." }
  Write-Host "Waiting for boot (up to 5 min)..."
  & $adb -s $serial wait-for-device
  $booted = $false
  for ($i=0; $i -lt 60; $i++) {
    if ((& $adb -s $serial shell getprop sys.boot_completed 2>$null).Trim() -eq "1") { $booted=$true; break }
    Start-Sleep 5
  }
  if (-not $booted) { throw "Emulator did not finish booting." }
  Write-Host "Boot complete."

  if (-not ((& $adb -s $serial shell pm list packages 2>$null) -match $pkg)) {
    if (-not $Apk) { throw "CSEntry not installed and no -Apk given. Get it from https://www.csprousers.org/apk/" }
    Write-Host "Installing CSEntry from $Apk ..."
    & $adb -s $serial install -r $Apk
  } else { Write-Host "CSEntry already installed." }

  # Pre-grant runtime perms so first-run dialogs don't block screenshots.
  foreach ($p in @("ACCESS_FINE_LOCATION","ACCESS_COARSE_LOCATION","CAMERA","RECORD_AUDIO",
                   "READ_EXTERNAL_STORAGE","WRITE_EXTERNAL_STORAGE","POST_NOTIFICATIONS")) {
    & $adb -s $serial shell pm grant $pkg "android.permission.$p" 2>$null
  }
  & $adb -s $serial shell monkey -p $pkg -c android.intent.category.LAUNCHER 1 2>$null | Out-Null
  Write-Host ""
  Write-Host "CSEntry launched. Next: in the emulator, Sync to https://csweb.asiansocial.org/csweb,"
  Write-Host "download the survey, navigate, then run:  .\capture-csentry-screenshots.ps1 -Shot <name>"
  return
}

if ($Shot) {
  if (-not (Running)) { throw "No emulator running. Run -Setup first." }
  New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
  $out = Join-Path $OutDir "$Shot.png"
  # Capture to the device then pull — binary-safe (PowerShell '>' would corrupt the PNG).
  & $adb -s $serial shell screencap -p /sdcard/_shot.png
  & $adb -s $serial pull /sdcard/_shot.png "$out" 2>$null | Out-Null
  & $adb -s $serial shell rm -f /sdcard/_shot.png 2>$null
  $sz = (Get-Item $out).Length
  if ($sz -lt 1000) { Write-Warning "Captured file is only $sz bytes — screen may not be ready." }
  Write-Host ("Saved {0} ({1:N0} KB)" -f $out, ($sz/1KB))
  return
}

Write-Host "Usage: -Setup [-Apk <path>] | -Shot <name> | -Kill    (see the header for the full workflow)"
