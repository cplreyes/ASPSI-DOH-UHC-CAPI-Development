# scripts/csbatch_run.ps1
# Run F1 consistency batch against the live (synced) CSWeb data.
# Prereq: Phase 9 complete; F1 cases have been synced to CSWeb and downloaded
# to 108_F1_data/F1.csdb.

$ErrorActionPreference = 'Stop'

$root   = Resolve-Path "$PSScriptRoot\..\deliverables\CSPro\UHC-Survey-System"
$batch  = Join-Path $root '118_csbatch\F1_CONSISTENCY.bat'
$data   = Join-Path $root '108_F1_data\F1.csdb'
$report = Join-Path $root '118_csbatch\edit_report_F1.txt'

if (-not (Test-Path $batch)) { Write-Error "Batch app not found: $batch (Phase 10 not complete)" }
if (-not (Test-Path $data))  { Write-Error "No synced F1 data at $data (Phase 9 not complete)" }

# CSBatch.exe needs the batch app compiled to .pen first; F7 it in Designer
# (same as instrument apps), then run runpff.exe with a PFF that wires .pen + data.
$pen = $batch -replace '\.bat$', '.pen'
if (-not (Test-Path $pen)) {
    Write-Error "F1_CONSISTENCY.pen not found at $pen. Open F1_CONSISTENCY.bat in CSPro Designer and press F7 to publish."
}

$pff = Join-Path $root '118_csbatch\F1_CONSISTENCY.pff'
@"
[Run Information]
Version=CSPro 8.0
AppType=Batch

[Files]
Application=$pen
InputData=$data
OutputData=$data

[Parameters]
ListingFile=$report
"@ | Out-File -FilePath $pff -Encoding ASCII

& 'C:\Program Files (x86)\CSPro 8.0\runpff.exe' $pff
if ($LASTEXITCODE -ne 0) {
    Write-Error "runpff failed (exit $LASTEXITCODE)"
}

if (Test-Path $report) {
    $count = (Get-Content $report | Measure-Object -Line).Lines
    Write-Host "Edit report generated: $report ($count lines)"
    Write-Host "First 10 lines:"
    Get-Content $report -TotalCount 10
} else {
    Write-Warning "Expected report at $report but file not found"
}
