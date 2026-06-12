<#
  F2 PWA - Pretest Pilot Dry-Run (R4) staging setup helper (token mint + admin accounts)
  -----------------------------------------------------------------------
  Automates Phases 3 + 4 of the R4 coordinator pre-flight against the
  staging Admin Portal API:
    * reissues a fresh 30-day enrollment token per test HCW and prints a
      paste-ready markdown table for the HCW tester guide (Section 3);
    * (with -CreateAccounts) sets up ALL four test accounts: creates
      marriz_admin (Administrator) + data_reader_uat (DataReader), and
      resets shan_admin + kidd_admin - printing every temp password.
      All four force a password change on first login.

  PREREQUISITE - run this AFTER:
    1. Staging Apps Script backend redeployed with current dist/Code.gs
       (republish the EXISTING deployment so the /exec URL stays stable).
    2. purgeDemoData() + seedDemoData() run on the staging sheet
       (so your admin account + the DEMO-HCW-* rows + built-in roles exist).
  The Pages frontend (git push to staging) is NOT required for this script -
  it talks to the worker directly. But testers DO need it before the round opens.

  USAGE (PowerShell, from anywhere):
    # tokens only (the 3 primaries):
    ./F2-PWA-Pretest-Dry-Run-R4-mint-tokens.ps1 -User carl_admin

    # tokens for primaries + spares:
    ./F2-PWA-Pretest-Dry-Run-R4-mint-tokens.ps1 -User carl_admin -Hcws DEMO-HCW-004,DEMO-HCW-007,DEMO-HCW-002,DEMO-HCW-001,DEMO-HCW-003

    # tokens AND create the two test accounts (auto-generated temp passwords):
    ./F2-PWA-Pretest-Dry-Run-R4-mint-tokens.ps1 -User carl_admin -CreateAccounts

    # ...with passwords you choose:
    ./F2-PWA-Pretest-Dry-Run-R4-mint-tokens.ps1 -User carl_admin -CreateAccounts -MarrizPw 'Temp-Marriz-1' -ReaderPw 'Temp-Reader-1'

  It prompts for the admin password (hidden). Nothing is stored.
#>
param(
  [string]   $Worker         = "https://f2-pwa-worker-staging.hcw.workers.dev",
  [string]   $Origin         = "https://staging.f2-pwa.pages.dev",
  [string]   $User,
  [string[]] $Hcws           = @("DEMO-HCW-004", "DEMO-HCW-007", "DEMO-HCW-002"),
  [switch]   $CreateAccounts,
  [string]   $MarrizPw,
  [string]   $ReaderPw,
  [string]   $ShanPw,
  [string]   $KiddPw
)

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

function New-TempPw {
  -join (((48..57) + (65..90) + (97..122)) | Get-Random -Count 12 | ForEach-Object { [char]$_ })
}

if (-not $User) { $User = Read-Host "Staging admin username (e.g. carl_admin)" }
$secure = Read-Host "Password for $User" -AsSecureString
$pw = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure))

Write-Host "`nLogging in to $Worker as $User ..." -ForegroundColor Cyan
try {
  $loginBody = @{ username = $User; password = $pw } | ConvertTo-Json
  $login = Invoke-RestMethod -Uri "$Worker/admin/api/login" -Method Post `
             -ContentType "application/json" -Body $loginBody -ErrorAction Stop
} catch {
  Write-Error "Login request failed: $($_.Exception.Message)"
  Write-Host  "If this is an Apps Script / 5xx error, the staging worker's APPS_SCRIPT_URL secret may not point at the current staging /exec deployment." -ForegroundColor Yellow
  exit 1
}
$token = $login.token
if (-not $token) { Write-Error "No token in login response - check credentials."; exit 1 }
if ($login.password_must_change) {
  Write-Host "NOTE: this account has password_must_change=true. Rotate it in the portal first, then re-run." -ForegroundColor Yellow
}
Write-Host "Logged in (role: $($login.role))." -ForegroundColor Green

$headers = @{ Authorization = "Bearer $token"; Origin = $Origin }

# ---------------------------------------------------------------------------
# Phase 4 (optional) - set up all four test accounts
#   create: marriz_admin (Administrator), data_reader_uat (DataReader)
#   reset:  shan_admin, kidd_admin (existing Administrators)
# ---------------------------------------------------------------------------
if ($CreateAccounts) {
  Write-Host "`nSetting up test accounts..." -ForegroundColor Cyan
  if (-not $MarrizPw) { $MarrizPw = New-TempPw }
  if (-not $ReaderPw) { $ReaderPw = New-TempPw }
  if (-not $ShanPw)   { $ShanPw   = New-TempPw }
  if (-not $KiddPw)   { $KiddPw   = New-TempPw }

  $results = @()

  # --- create new accounts ---
  $toCreate = @(
    @{ username = 'marriz_admin';    role_name = 'Administrator'; first_name = 'Marriz'; last_name = 'Data Manager'; pw = $MarrizPw },
    @{ username = 'data_reader_uat'; role_name = 'DataReader';    first_name = 'UAT';    last_name = 'Reader';       pw = $ReaderPw }
  )
  foreach ($a in $toCreate) {
    $cbody = @{
      username   = $a.username
      password   = $a.pw
      role_name  = $a.role_name
      first_name = $a.first_name
      last_name  = $a.last_name
    } | ConvertTo-Json
    try {
      Invoke-RestMethod -Uri "$Worker/admin/api/dashboards/users" -Method Post `
        -Headers $headers -ContentType "application/json" -Body $cbody -ErrorAction Stop | Out-Null
      $results += [pscustomobject]@{ Username = $a.username; Action = 'created'; Role = $a.role_name; TempPassword = $a.pw; Status = 'OK (force-rotates on first login)' }
    } catch {
      $results += [pscustomobject]@{ Username = $a.username; Action = 'created'; Role = $a.role_name; TempPassword = '-'; Status = "SKIP: $($_.Exception.Message) (may already exist - reset it instead)" }
    }
  }

  # --- reset existing tester accounts ---
  $toReset = @(
    @{ username = 'shan_admin'; pw = $ShanPw },
    @{ username = 'kidd_admin'; pw = $KiddPw }
  )
  foreach ($a in $toReset) {
    $ubody = @{ password = $a.pw } | ConvertTo-Json
    try {
      Invoke-RestMethod -Uri "$Worker/admin/api/dashboards/users/$($a.username)" -Method Patch `
        -Headers $headers -ContentType "application/json" -Body $ubody -ErrorAction Stop | Out-Null
      $results += [pscustomobject]@{ Username = $a.username; Action = 'reset'; Role = 'Administrator'; TempPassword = $a.pw; Status = 'OK (force-rotates on first login)' }
    } catch {
      $results += [pscustomobject]@{ Username = $a.username; Action = 'reset'; Role = 'Administrator'; TempPassword = '-'; Status = "FAIL: $($_.Exception.Message) (does the account exist on staging?)" }
    }
  }

  Write-Host "`n--- test accounts (share temp passwords out-of-band) ---" -ForegroundColor Cyan
  $results | Format-Table -AutoSize
  Write-Host "DM shan/kidd/marriz their temp password; data_reader_uat -> post in #f2-pwa-uat. All force a password change on first login." -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
# Phase 3 - reissue enrollment tokens
# ---------------------------------------------------------------------------
Write-Host "`nReissuing enrollment tokens..." -ForegroundColor Cyan
$rows = foreach ($h in $Hcws) {
  try {
    $r = Invoke-RestMethod -Uri "$Worker/admin/api/hcws/$h/reissue-token" -Method Post `
           -Headers $headers -ContentType "application/json" -Body "{}" -ErrorAction Stop
    [pscustomobject]@{ HCW = $h; URL = $r.enroll_url }
  } catch {
    [pscustomobject]@{ HCW = $h; URL = "ERROR: $($_.Exception.Message)" }
  }
}

Write-Host "`n--- paste into the HCW guide, Section 3 ---`n" -ForegroundColor Cyan
"| HCW ID | Enrollment URL |"
"|---|---|"
foreach ($row in $rows) { "| ``$($row.HCW)`` | $($row.URL) |" }
Write-Host ""
