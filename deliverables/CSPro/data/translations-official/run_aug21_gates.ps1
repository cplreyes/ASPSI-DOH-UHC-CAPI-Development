# deliverables/CSPro/data/translations-official/run_aug21_gates.ps1
# Aug-21 post-merge gates. Run AFTER `apply_aug21.py --apply`, BEFORE generate_dcf.py.
#
# Usage (from deliverables/CSPro):
#     .\data\translations-official\run_aug21_gates.ps1 -Inst F1 -PreBridge $preBC
#
#   -Inst      focuses the bridge_check per-file lines; BOTH tools always scan all three
#              instruments (neither has an instrument filter).
#   -PreBridge REQUIRED. The Rule-B + Rule-C defect count measured BEFORE --apply. Take it
#              from the same JSON this script reads, so pre and post are the same number:
#
#     $preJson = "data\translations-official\out-aug21\aug21_pre_bridge.json"
#     python aug17-tools\bridge_check.py --check --json $preJson
#     $preBC = (Get-Content $preJson -Raw | ConvertFrom-Json).bc
#
#              There is deliberately no default: 0 would silently pass a fleet that already
#              carries B/C rows, and any non-zero guess would silently mask a new one.
#
# Gate 1 = scan_poisoned_keys.py per-reason delta vs aug21_pre_findings.json (post <= pre per
#          reason; the scan's reference corpus is June-5, so an Aug-21 rewording is allowed to
#          land as a suspect only if it does not GROW a reason).
# Gate 2 = bridge_check.py Rule B/C delta. Rule A (June-5 legacy mismatch) is EXPECTED to grow
#          once Aug-21 replaces values and is triage-only by that tool's own docstring, so the
#          total is reported but never gated on.
#          The gated `bc` number is MARKER-based, not tag-based: bridge_check's rule dispatch is
#          first-fired-wins and Rule A fires on any legacy mismatch, so a B/C corruption newly
#          introduced by an Aug-21 value on a row that also has a legacy entry would carry the
#          tag `A-mismatch`. bridge_check therefore stamps `bc_marker` on every defect row from
#          the VALUE itself (bc_markers_match()) and `bc` sums that - which is why `bc` can be
#          larger than by_rule["B-admin-leak"] + by_rule["C-glued-fragments"], and why the
#          detail lines below filter on `bc_marker` rather than on `rule`.
#
# PowerShell 5.1: no `2>&1` on native exes, every Select-String result guarded before use.
param(
    [Parameter(Mandatory=$true)][ValidateSet("F1","F3","F4")][string]$Inst,
    [Parameter(Mandatory=$true)][int]$PreBridge
)
$env:PYTHONIOENCODING = "utf-8"
$here  = Split-Path -Parent $MyInvocation.MyCommand.Path
$cspro = (Resolve-Path (Join-Path $here "..\..")).Path
$pre        = Join-Path $here "aug21_pre_findings.json"
$post       = Join-Path $here "aug21_post_findings.json"
$bridgeJson = Join-Path (Join-Path $here "out-aug21") "aug21_post_bridge.json"  # out-aug21/ is gitignored
if (-not (Test-Path $pre)) {
    Write-Host "missing $pre - run scan_poisoned_keys.py --apply-report BEFORE --apply (Task 6 step 5.1)"
    exit 1
}
Push-Location $cspro
try {
    Write-Host "== gate 1: scan_poisoned_keys.py (regenerates the .dcf files as a side effect)"
    $scan = & python (Join-Path $here "scan_poisoned_keys.py") --apply-report $post
    $m = $scan | Select-String -Pattern "^TOTAL suspect entries: (\d+)"
    if (-not $m) { Write-Host "scan did not complete (no TOTAL line):"; $scan | Select-Object -Last 15; exit 1 }
    $scanTotal = $m.Matches[0].Groups[1].Value
    # Echo the scan's waiver lines (scan_waivers.json, Task 50 fix round 1). A waived row is a
    # row this gate would otherwise have failed on, so every gate transcript must show which
    # ones were waived and any waiver that has gone STALE - otherwise the exemption is a
    # silent one, which is the whole thing the waiver file is not allowed to be.
    $wv = $scan | Select-String -Pattern "^--- waived|^\[.* waived\]|^STALE WAIVER"
    if ($wv) { $wv | ForEach-Object { Write-Host ("  " + $_.Line) } }
    & python (Join-Path $here "apply_aug21.py") --compare-findings $pre $post
    $scanOk = ($LASTEXITCODE -eq 0)

    Write-Host "== gate 2: bridge_check.py --check (Rule A = June-5 legacy mismatch, EXPECTED after Aug-21 replaces; only B/C count)"
    $bridge = & python (Join-Path $cspro "aug17-tools\bridge_check.py") --check --json $bridgeJson
    $t = $bridge | Select-String -Pattern "^Total defects found: (\d+)"
    if (-not $t) { Write-Host "bridge_check did not complete:"; $bridge | Select-Object -Last 15; exit 1 }
    $bridgeTotal = [int]$t.Matches[0].Groups[1].Value
    if (-not (Test-Path $bridgeJson)) { Write-Host "bridge_check wrote no JSON at $bridgeJson"; exit 1 }
    $bj = Get-Content $bridgeJson -Raw | ConvertFrom-Json
    $bridgeBC = [int]$bj.bc
    $bridge | Select-String -Pattern "^Scanned|^Total defects found|^By rule|^  \(B/C is|^  $Inst/"
    # Filter on bc_marker, not on rule: a B/C corruption on a row that also has a legacy
    # entry is tagged A-mismatch by the first-fired-wins dispatch, and printing only
    # rule-tagged rows would hide exactly the rows this gate exists to surface.
    foreach ($d in $bj.defects) {
        if ($d.bc_marker) {
            Write-Host ("  B/C: {0}/{1} {2} [tagged {3}] {4}" -f $d.instrument, $d.locale, $d.item, $d.rule, $d.current)
        }
    }
    $bridgeOk = ($bridgeBC -le $PreBridge)

    Write-Host ("== {0} gates: scan total={1} ({2})  bridge total={3} (A-mismatch ignored), B/C={4} vs pre {5} ({6})" -f
        $Inst, $scanTotal, $(if ($scanOk) {"no reason grew"} else {"a reason GREW"}),
        $bridgeTotal, $bridgeBC, $PreBridge, $(if ($bridgeOk) {"ok"} else {"GREW"}))
    if (-not ($scanOk -and $bridgeOk)) { Write-Host "GATES FAILED - do not regenerate"; exit 1 }
    Write-Host "GATES CLEAN - proceed to generate_dcf.py"; exit 0
} finally { Pop-Location }
