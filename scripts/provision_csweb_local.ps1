# scripts/provision_csweb_local.ps1
# Verify Wampserver running before attempting CSWeb install.
# Run as Administrator (needed for service control / firewall later).

$ErrorActionPreference = 'Stop'

Write-Host "Checking Wampserver64 status..."

# Apache
$apache = Get-Process -Name 'httpd' -ErrorAction SilentlyContinue
if (-not $apache) {
    Write-Error "Apache (httpd.exe) not running. Start Wampserver via tray icon -> Start All Services."
}
Write-Host ("  Apache running (PIDs: " + ($apache.Id -join ', ') + ")")

# MySQL
$mysql = Get-Process -Name 'mysqld' -ErrorAction SilentlyContinue
if (-not $mysql) {
    Write-Error "MySQL (mysqld.exe) not running. Start Wampserver."
}
Write-Host ("  MySQL running (PID: " + $mysql.Id + ")")

# Wampserver root
$wamp = 'C:\wamp64'
if (-not (Test-Path $wamp)) {
    Write-Error "Wampserver root not at $wamp. Update this script."
}
Write-Host "  Wampserver root at $wamp"

# www dir
$www = "$wamp\www"
if (-not (Test-Path $www)) {
    Write-Error "Wampserver www dir not at $www."
}
Write-Host "  www dir at $www"

# Find MySQL CLI (version varies between Wampserver releases)
$mysqlBin = Get-ChildItem -Path "$wamp\bin\mysql\" -Directory -ErrorAction SilentlyContinue |
    Sort-Object Name -Descending | Select-Object -First 1
if (-not $mysqlBin) {
    Write-Error "No MySQL bin dir under $wamp\bin\mysql\"
}
$mysqlExe = Join-Path $mysqlBin.FullName 'bin\mysql.exe'
if (-not (Test-Path $mysqlExe)) {
    Write-Error "mysql.exe not at $mysqlExe"
}
Write-Host "  MySQL CLI at $mysqlExe"

# PHP detection (CSWeb is PHP)
$phpBin = Get-ChildItem -Path "$wamp\bin\php\" -Directory -ErrorAction SilentlyContinue |
    Sort-Object Name -Descending | Select-Object -First 1
if (-not $phpBin) {
    Write-Error "No PHP bin dir under $wamp\bin\php\"
}
$phpExe = Join-Path $phpBin.FullName 'php.exe'
Write-Host "  PHP CLI at $phpExe"

Write-Host ""
Write-Host "All checks passed. Wampserver is ready for CSWeb."
Write-Host ""
Write-Host "Detected paths (use these in subsequent scripts):"
Write-Host "  WAMP_ROOT  = $wamp"
Write-Host "  WAMP_WWW   = $www"
Write-Host "  MYSQL_EXE  = $mysqlExe"
Write-Host "  PHP_EXE    = $phpExe"
