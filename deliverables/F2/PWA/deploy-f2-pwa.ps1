# F2 PWA — guarded production deploy.
#
# WHY THIS EXISTS
# The Facilities admin tab vanished from production TWICE (2026-08-12, and again
# discovered 2026-08-13) without a single line of code regressing. Both times the
# cause was identical: someone built the PWA from a LOCAL checkout that was behind
# origin/main and scp'd the result over the docroot. A pre-merge build simply does
# not contain the tab, so a good deploy got silently reverted.
#
# Being careful is not a fix. This script makes a stale deploy IMPOSSIBLE TO
# COMPLETE, by asserting the invariant at three points:
#
#   1. BEFORE build  — the checkout must equal origin/main, and the source module
#                      must exist on disk.
#   2. AFTER build   — the built admin bundle must actually contain the Facilities
#                      nav entry. This gate is NOT bypassable, not even with
#                      -Force, because it is the invariant we actually care about:
#                      it catches a stale build regardless of HOW it got stale.
#   3. AFTER deploy  — the LIVE bundle is re-downloaded and re-checked, plus the
#                      API is probed. A deploy that "succeeded" but serves the
#                      wrong bundle fails loudly instead of looking fine.
#
# It also always backs up the docroot first (the 08-12 overwrite did not) and
# writes build-info.json so "is prod actually main?" is one curl away.
#
# USAGE
#   .\deploy-f2-pwa.ps1                # full guarded deploy
#   .\deploy-f2-pwa.ps1 -VerifyOnly    # check live prod, change nothing
#   .\deploy-f2-pwa.ps1 -DryRun        # build + assert, stop before touching prod
#   .\deploy-f2-pwa.ps1 -Force         # allow HEAD != origin/main (post-build gate STILL applies)

[CmdletBinding()]
param(
    [switch]$VerifyOnly,
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$RepoRoot  = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$AppDir    = Join-Path $PSScriptRoot "app"
$SshKey    = Join-Path $env:USERPROFILE ".ssh\aspsi-csweb"
$Server    = "root@207.148.65.115"
$DocRoot   = "/opt/app/f2-www"
$SiteUrl   = "https://uhc-hcw.asiansocial.org"
$ProxyUrl  = "https://uhc-hcw.asiansocial.org"   # same origin; the worker serves both

# The invariant. Add a line here whenever a feature must never silently vanish.
#
# The mid-section notes (#1041/#1042/#1043) belong here for the SAME reason the
# Facilities tab does, and it is not hypothetical: as of 2026-08-13 the matrix
# preamble RENDER exists only on integration/capi-ops. origin/main's
# MatrixQuestion.tsx contains no preamble block at all, while main's items.ts
# DOES carry the note data -- so a build from main looks complete, ships the
# notes as dead data, and silently reverts all three tickets. Testers have
# re-filed this trio twice (#1179/#1180/#1181, then again 08-13) precisely
# because each main-built deploy undoes it.
#
# `italic text-muted-foreground` is the class on MatrixQuestion's preamble <p>
# and appears nowhere else in the app, so it is a true render-path probe rather
# than a data probe -- the note text alone would pass even on a build that
# never displays it.
$RequiredMarkers = @(
    @{ Name = "Facilities nav entry";      Pattern = 'label:"Facilities"';           Bundle = "admin" },
    @{ Name = "Facilities API call";       Pattern = '/admin/api/facilities';        Bundle = "admin" },
    @{ Name = "Matrix preamble render";    Pattern = 'italic text-muted-foreground'; Bundle = "admin" },
    @{ Name = "Q63 fee note (#1041)";      Pattern = 'negotiable';                   Bundle = "admin" },
    @{ Name = "Q98/Q114 instr (#1042/3)";  Pattern = 'past 6 months';                Bundle = "admin" }
)

function Say($msg, $color = "White") { Write-Host $msg -ForegroundColor $color }
function Fail($msg) { Say "`n  FAIL  $msg`n" "Red"; exit 1 }
function Pass($msg) { Say "  ok    $msg" "Green" }

# ---------------------------------------------------------------- verify live
function Test-Live {
    Say "`n== Verifying LIVE production ==" "Cyan"
    $stamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    try {
        $html = (Invoke-WebRequest "$SiteUrl/?cb=$stamp" -UseBasicParsing).Content
    } catch { Fail "site unreachable: $($_.Exception.Message)" }
    Pass "site responds"

    if ($html -notmatch 'assets/(index-[A-Za-z0-9]+\.js)') { Fail "no index bundle referenced by index.html" }
    $indexName = $Matches[1]
    Say "        serving $indexName"

    # Show the deployed identity when present (informational only).
    try {
        $info = (Invoke-WebRequest "$SiteUrl/build-info.json?cb=$stamp" -UseBasicParsing).Content | ConvertFrom-Json
        Say "        build-info: sha=$($info.sha.Substring(0,8)) branch=$($info.branch) built=$($info.built_at)"
    } catch { Say "        (no build-info.json on prod - deployed before this script)" "DarkGray" }

    # Resolve the admin chunk from PROD'S OWN reference chain: index.html -> index
    # bundle -> lazy admin chunk. Never guess from a local dist -- an early version
    # of this script did, matched a stale local filename that prod still had lying
    # around from an overlay deploy, and reported a false MISSING. The whole point
    # is to check what production actually serves, so only production may name it.
    $adminUrl = $null
    try {
        $indexJs = (Invoke-WebRequest "$SiteUrl/assets/$indexName" -UseBasicParsing).Content
        if ($indexJs -match 'admin-[A-Za-z0-9_-]+\.js') { $adminUrl = "$SiteUrl/assets/$($Matches[0])" }
    } catch { Fail "could not fetch the index bundle prod references ($indexName)" }
    if (-not $adminUrl) { Fail "prod's index bundle references no admin chunk - the admin portal is not in this build" }
    Say "        admin chunk $($adminUrl.Split('/')[-1])"

    try { $adminJs = (Invoke-WebRequest $adminUrl -UseBasicParsing).Content }
    catch { Fail "admin bundle not served at $adminUrl - prod is NOT running this build" }

    $bad = $false
    foreach ($m in $RequiredMarkers) {
        if ($adminJs -like "*$($m.Pattern)*") { Pass "live: $($m.Name)" }
        else { Say "  FAIL  live bundle is MISSING $($m.Name)" "Red"; $bad = $true }
    }

    try {
        Invoke-WebRequest "$SiteUrl/admin/api/facilities?limit=1" -UseBasicParsing | Out-Null
        Pass "facilities API reachable"
    } catch {
        $code = [int]$_.Exception.Response.StatusCode
        if ($code -eq 401) { Pass "facilities API 401 (exists, auth-gated)" }
        else { Say "  FAIL  facilities API returned $code (404 = endpoint missing)" "Red"; $bad = $true }
    }
    if ($bad) { return $false }
    Say "`n  PROD IS HEALTHY`n" "Green"
    return $true
}

if ($VerifyOnly) { if (Test-Live) { exit 0 } else { exit 1 } }

# ------------------------------------------------------- guard 1: pre-build
Say "`n== Guard 1/3: checkout state ==" "Cyan"
if (-not (Test-Path (Join-Path $AppDir "package.json"))) {
    Fail "cannot find the app at $AppDir - run this script from its home in the repo (deliverables/F2/PWA/)"
}
Push-Location $RepoRoot
# Same PS 5.1 native-stderr trap as the build block: git writing ANY progress or
# warning to stderr would become a terminating error and abort the deploy before
# the guards ever ran. Gate on $LASTEXITCODE instead.
$prevEAP = $ErrorActionPreference
$ErrorActionPreference = "Continue"
try {
    git rev-parse --is-inside-work-tree | Out-Null
    if ($LASTEXITCODE -ne 0) { $ErrorActionPreference = $prevEAP; Pop-Location; Fail "$RepoRoot is not a git repository - cannot verify the checkout matches origin/main" }
    git fetch origin main --quiet | Out-Null
    if ($LASTEXITCODE -ne 0) { Say "  warn  could not fetch origin/main; comparing against the last-known ref" "Yellow" }
    $head   = (git rev-parse HEAD).Trim()
    $origin = (git rev-parse origin/main).Trim()
    $branch = (git rev-parse --abbrev-ref HEAD).Trim()
} finally { $ErrorActionPreference = $prevEAP; Pop-Location }
if (-not $head -or -not $origin) { Fail "could not resolve HEAD / origin/main - refusing to build blind" }

Say "        HEAD       $($head.Substring(0,8))  ($branch)"
Say "        origin/main $($origin.Substring(0,8))"

if ($head -ne $origin) {
    if (-not $Force) {
        Fail @"
Checkout is NOT at origin/main - refusing to build.

This is exactly what broke production on 2026-08-12: a build from a behind
checkout was deployed and silently reverted the Facilities tab.

Fix it:   git -C "$RepoRoot" pull origin main
Override: re-run with -Force (the post-build content gate still applies)
"@
    }
    Say "  warn  -Force: proceeding despite drift" "Yellow"
} else { Pass "checkout matches origin/main" }

$facSrc = Join-Path $AppDir "src\admin\facilities\FacilitiesPage.tsx"
if (-not (Test-Path $facSrc)) { Fail "source module missing: $facSrc`nThis checkout cannot produce a build containing the Facilities tab." }
Pass "facilities source module present"

# ------------------------------------------------------------------- build
Say "`n== Building ==" "Cyan"
Push-Location $AppDir
try {
    # Windows PowerShell 5.1 turns a native exe's STDERR into NativeCommandError
    # ErrorRecords, and with $ErrorActionPreference='Stop' that makes npm's
    # ordinary deprecation warnings fatal. This bit the script on its first run
    # from a FRESH worktree -- the exact case it exists for, since an existing
    # node_modules makes `npm ci` quiet enough to hide the bug. Drop the stderr
    # redirect and gate on $LASTEXITCODE, which is the real success signal.
    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        npm ci | Out-Null
        if ($LASTEXITCODE -ne 0) { $ErrorActionPreference = $prevEAP; Fail "npm ci failed (exit $LASTEXITCODE)" }
        $env:VITE_F2_PROXY_URL = $ProxyUrl
        npm run build | Select-Object -Last 3
        if ($LASTEXITCODE -ne 0) { $ErrorActionPreference = $prevEAP; Fail "npm run build failed (exit $LASTEXITCODE)" }
    } finally { $ErrorActionPreference = $prevEAP }
} finally { Pop-Location }
Pass "build completed"

# ------------------------------------------------ guard 2: post-build (HARD)
Say "`n== Guard 2/3: built artifact (not bypassable) ==" "Cyan"
$distAssets = Join-Path $AppDir "dist\assets"
$adminFile  = Get-ChildItem $distAssets -Filter "admin-*.js" | Select-Object -First 1
if (-not $adminFile) { Fail "no admin bundle in dist/assets" }
$adminText  = Get-Content $adminFile.FullName -Raw

foreach ($m in $RequiredMarkers) {
    if ($adminText -like "*$($m.Pattern)*") { Pass "built: $($m.Name)" }
    else { Fail "built bundle is MISSING $($m.Name).`nThis build would revert production. Deploy aborted - nothing was touched." }
}

# Stamp identity so "is prod main?" is one curl.
@{
    sha          = $head
    branch       = $branch
    built_at     = (Get-Date).ToUniversalTime().ToString("o")
    admin_bundle = $adminFile.Name
    matches_main = ($head -eq $origin)
} | ConvertTo-Json | Set-Content (Join-Path $AppDir "dist\build-info.json") -Encoding utf8
Pass "stamped build-info.json ($($head.Substring(0,8)))"

if ($DryRun) { Say "`n  -DryRun: build verified, production untouched.`n" "Yellow"; exit 0 }

# ------------------------------------------------------------------ deploy
Say "`n== Deploying ==" "Cyan"
$tgz    = Join-Path $env:TEMP "f2-dist-deploy.tgz"
$backup = "$DocRoot.bak-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

Push-Location (Join-Path $AppDir "dist")
try { tar czf $tgz . } finally { Pop-Location }
if (-not (Test-Path $tgz)) { Fail "failed to package dist" }
Pass "packaged $([math]::Round((Get-Item $tgz).Length/1MB,2)) MB"

scp -i $SshKey -o StrictHostKeyChecking=no $tgz "${Server}:/tmp/f2-dist-deploy.tgz" | Out-Null
if ($LASTEXITCODE -ne 0) { Fail "scp failed - production untouched" }
Pass "uploaded"

# Back up BEFORE extracting (the 08-12 overwrite skipped this). Overlay, don't
# wipe: old hashed chunks stay so in-flight sessions do not 404 mid-page.
$remote = "cp -a $DocRoot $backup && tar xzf /tmp/f2-dist-deploy.tgz -C $DocRoot && rm -f /tmp/f2-dist-deploy.tgz && echo OK"
$res = ssh -i $SshKey -o StrictHostKeyChecking=no $Server $remote
if ($res -notmatch "OK") { Fail "remote extract failed - check $backup" }
Pass "backed up to $backup"
Pass "extracted into $DocRoot"
Remove-Item $tgz -Force -ErrorAction SilentlyContinue

# ------------------------------------------------ guard 3: post-deploy live
Start-Sleep -Seconds 3
if (-not (Test-Live)) {
    Say "`n  DEPLOY VERIFICATION FAILED - roll back with:" "Red"
    Say "  ssh -i `"$SshKey`" $Server `"cp -a $backup/. $DocRoot/`"`n" "Yellow"
    exit 1
}

Say "  Deployed $($head.Substring(0,8)) and verified live." "Green"
Say "  Rollback if needed: ssh -i `"$SshKey`" $Server `"cp -a $backup/. $DocRoot/`"`n" "DarkGray"
