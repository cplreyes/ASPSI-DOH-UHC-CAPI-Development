# scripts/csweb_smoke_test.ps1
# Verify CSWeb 8.0.1 is reachable and the csweb DB is populated.

$ErrorActionPreference = 'Stop'

$base = 'http://localhost/csweb8.0.1'

Write-Host "Checking CSWeb at $base..."
try {
    $resp = Invoke-WebRequest -Uri $base -UseBasicParsing -TimeoutSec 5
    if ($resp.StatusCode -ne 200) {
        Write-Error "Expected 200; got $($resp.StatusCode)"
    }
    Write-Host "  CSWeb root responds (status $($resp.StatusCode), $($resp.Content.Length) bytes)"
} catch {
    Write-Error "CSWeb root unreachable: $_"
}

# Login UI
$ui = "$base/ui/login"
try {
    $resp = Invoke-WebRequest -Uri $ui -UseBasicParsing -TimeoutSec 5
    Write-Host "  CSWeb login UI responds (status $($resp.StatusCode))"
} catch {
    Write-Host ("  CSWeb login UI unexpected: " + $_.Exception.Message.Split([Environment]::NewLine)[0])
}

# DB sanity
$mysql = (Get-ChildItem -Path 'C:\wamp64\bin\mysql\' -Directory | Sort-Object Name -Descending | Select-Object -First 1).FullName + '\bin\mysql.exe'
$tables = & $mysql -u root -e "USE csweb; SHOW TABLES;" 2>$null | Measure-Object | Select-Object -ExpandProperty Count
Write-Host "  csweb DB has $tables tables"
if ($tables -lt 10) {
    Write-Error "Expected >=10 tables in csweb; got $tables. Re-run setup wizard at $base/setup/configure.php"
}

# Apps already deployed
$apps = & $mysql -u root -N -e "USE csweb; SELECT name FROM cspro_apps;" 2>$null
Write-Host ""
Write-Host "Apps currently deployed in CSWeb:"
if ($apps) {
    $apps | ForEach-Object { Write-Host "  - $_" }
} else {
    Write-Host "  (none -- Apps tab is empty)"
}

Write-Host ""
Write-Host "CSWeb is ready. Login at $base/ui/login as your existing admin user."
Write-Host "Upload .pen files via the Apps tab once produced (after F7-publish)."
