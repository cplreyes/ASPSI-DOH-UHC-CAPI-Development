# CAPI Scrum — daily standup .md generator (launch-independent).
#
# WHY THIS EXISTS (root cause, Sprint 008 retro / E0-AUTO-STANDUP):
# Standup generation used to ride ONLY on the project's SessionStart hook, which
# fires only when Claude Code is launched inside the ASPSI project dir. On days
# Carl opened Claude elsewhere (or not at all), nothing ran and the daily file
# silently dropped — exactly what happened 2026-05-27 onward. A "daily" artifact
# needs a time-based trigger, so this script runs from Windows Task Scheduler
# every morning regardless of whether Claude is opened. The SessionStart hook is
# kept as an intraday top-up; this is the guaranteed floor.
#
# It calls the same idempotent generators the hook uses (safe to run repeatedly),
# then runs a self-check probe that turns a silent drop into a logged canary line.
#
# TO (RE)REGISTER THE WINDOWS SCHEDULED TASK (machine-local; not version-controlled —
# recreate per machine). Run once in PowerShell:
#   $repo      = "C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development"
#   $wrapper   = Join-Path $repo ".claude\scripts\daily-standup-md.ps1"
#   $action    = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$wrapper`""
#   $trigger   = New-ScheduledTaskTrigger -Daily -At 8:30AM
#   $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
#   $settings  = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 5)
#   Register-ScheduledTask -TaskName "CAPI Scrum Daily Standup MD" -Action $action -Trigger $trigger -Principal $principal -Settings $settings

$ErrorActionPreference = "Continue"
$repo = "C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development"
$log  = Join-Path $repo ".claude\scripts\generate-standup.log"
$env:PYTHONIOENCODING = "utf-8"

function Write-Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz"
    "[$ts] $msg" | Out-File -FilePath $log -Append -Encoding utf8
}

# Resolve a python interpreter: py > python > python3 (mirrors the hook).
$py = $null
foreach ($cand in @("py", "python", "python3")) {
    $cmd = Get-Command $cand -ErrorAction SilentlyContinue
    if ($cmd) { $py = $cmd.Source; break }
}
if (-not $py) { Write-Log "scheduled: no python interpreter on PATH"; exit 0 }

# Generate today's standup + seed retro. Both are idempotent and never crash
# (they self-log "wrote"/"skip"/"error"), so failures here are non-fatal.
& $py (Join-Path $repo ".claude\scripts\generate_standup.py") --repo $repo 2>&1 | Out-Null
& $py (Join-Path $repo ".claude\scripts\generate_retro.py")    --repo $repo 2>&1 | Out-Null

# --- Self-check probe -------------------------------------------------------
# The retro asked for a canary: a silent drop must become a visible log line.
$today      = (Get-Date).ToString("yyyy-MM-dd")
$standupDir = Join-Path $repo "scrum\standups"
$todayFile  = Join-Path $standupDir "$today.md"

if (Test-Path $todayFile) {
    Write-Log "scheduled: ok - $today.md present"
} else {
    Write-Log "scheduled: PROBE-MISSING - $today.md was not generated; investigate generate_standup.py"
}

# Staleness guard: if even the newest file is 2+ days old, shout in the log.
$latest = Get-ChildItem $standupDir -Filter "*.md" -ErrorAction SilentlyContinue |
          Sort-Object Name -Descending | Select-Object -First 1
if ($latest) {
    try {
        $latestDate = [datetime]::ParseExact($latest.BaseName, "yyyy-MM-dd", $null)
        $ageDays = (New-TimeSpan -Start $latestDate -End (Get-Date)).Days
        if ($ageDays -ge 2) {
            Write-Log "scheduled: PROBE-STALE - newest standup is $($latest.Name) ($ageDays days old)"
        }
    } catch { }
}

# --- E0-SCRUM-SYNC drift canary --------------------------------------------
# Runs daily regardless of whether today's standup file already exists (the
# generator is idempotent and skips when it does, so the in-standup callout
# alone would miss skip days). Fires when log.md has outpaced the sprint board
# by 2+ days — the stale-board condition behind the S009->S011 late-retro
# three-peat. Surfaces here in the scheduled log; the generator surfaces the
# same drift as a callout inside the standup when it (re)writes one.
$logMd    = Join-Path $repo "log.md"
$sprintMd = Join-Path $repo "scrum\sprint-current.md"
if ((Test-Path $logMd) -and (Test-Path $sprintMd)) {
    try {
        $logWrite    = (Get-Item $logMd).LastWriteTime
        $sprintWrite = (Get-Item $sprintMd).LastWriteTime
        $driftDays   = [math]::Round((New-TimeSpan -Start $sprintWrite -End $logWrite).TotalDays, 1)
        if ($driftDays -gt 2) {
            Write-Log "scheduled: PROBE-SPRINT-DRIFT - log.md is $driftDays days newer than sprint-current.md; sync the sprint board (E0-SCRUM-SYNC canary)"
        }
    } catch { }
}

exit 0
