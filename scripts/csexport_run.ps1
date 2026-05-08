# scripts/csexport_run.ps1
# Run F1 CSExport for STATA + SPSS + CSV.
# Prereq: Phase 9 complete; F1.csdb populated from synced cases.

$ErrorActionPreference = 'Stop'

$cspro  = 'C:\Program Files (x86)\CSPro 8.0'
$root   = Resolve-Path "$PSScriptRoot\..\deliverables\CSPro\UHC-Survey-System"
$f1     = Join-Path $root '107_F1'
$data   = Join-Path $root '108_F1_data\F1.csdb'

if (-not (Test-Path $data))  { Write-Error "No synced F1 data at $data (Phase 9 not complete)" }

foreach ($fmt in @('csv', 'stata', 'spss')) {
    $pff = Join-Path $f1 "export_F1_$fmt.pff"
    if (-not (Test-Path $pff)) {
        Write-Warning "PFF missing: $pff"
        continue
    }
    Write-Host "Running CSExport for $fmt..."
    & "$cspro\runpff.exe" $pff
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "runpff returned $LASTEXITCODE for $fmt"
    }
}

Write-Host ""
Write-Host "Outputs in $($data | Split-Path):"
Get-ChildItem (Split-Path $data) -Filter 'F1.*' | Select-Object Name, Length, LastWriteTime | Format-Table -AutoSize

# Compare CSV row count to whatever the .csdb has (rough proxy)
$csv = Join-Path (Split-Path $data) 'F1.csv'
if (Test-Path $csv) {
    $rows = (Get-Content $csv | Measure-Object -Line).Lines - 1   # subtract header
    Write-Host "F1.csv: $rows data rows (header excluded)"
}
