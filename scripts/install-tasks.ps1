#Requires -Version 5.1
<#
.SYNOPSIS
    Install Windows Task Scheduler tasks that auto-start Hippo bots on login.

.DESCRIPTION
    Reads bots.yaml from the project root and creates one Task Scheduler task
    per bot named "Hippo-<BotName>". Each task starts `uv run hippo <BotName>`
    at user login. Tasks are created in the current user's scope (no admin needed).

    Safe to re-run: existing tasks are skipped unless -Force is specified.

.PARAMETER Force
    Overwrite existing Task Scheduler tasks instead of skipping them.

.EXAMPLE
    .\scripts\install-tasks.ps1
    .\scripts\install-tasks.ps1 -Force
#>

param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# Resolve project root and uv executable
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BotsYaml   = Join-Path $ProjectRoot "bots.yaml"
$UvExe      = (Get-Command uv -ErrorAction SilentlyContinue)?.Source

if (-not $UvExe) {
    Write-Error "uv not found on PATH. Install from https://docs.astral.sh/uv/"
    exit 1
}

if (-not (Test-Path $BotsYaml)) {
    Write-Error "bots.yaml not found at $BotsYaml"
    exit 1
}

# Parse bot names from bots.yaml
$yamlContent = Get-Content $BotsYaml -Raw
$botNames = @()
$inBots = $false
foreach ($line in ($yamlContent -split "`n")) {
    if ($line -match '^bots\s*:') { $inBots = $true; continue }
    if ($inBots -and $line -match '^\s{2}([A-Za-z][A-Za-z0-9_]*)\s*:') {
        $botNames += $Matches[1]
    }
    if ($inBots -and $line -match '^[A-Za-z]' -and $line -notmatch '^bots\s*:') {
        $inBots = $false
    }
}

if ($botNames.Count -eq 0) {
    Write-Error "No bot names found in $BotsYaml"
    exit 1
}

Write-Host "Installing Task Scheduler tasks for $($botNames.Count) bot(s)..." -ForegroundColor Cyan

foreach ($botName in $botNames) {
    $taskName = "Hippo-$botName"

    $existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existing -and -not $Force) {
        Write-Host "  Skipping $taskName (already exists — use -Force to overwrite)" -ForegroundColor Yellow
        continue
    }

    $trigger  = New-ScheduledTaskTrigger -AtLogOn
    $action   = New-ScheduledTaskAction `
        -Execute $UvExe `
        -Argument "run hippo $botName" `
        -WorkingDirectory $ProjectRoot
    $settings = New-ScheduledTaskSettingsSet `
        -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 1)
    $principal = New-ScheduledTaskPrincipal `
        -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) `
        -LogonType Interactive `
        -RunLevel Limited

    Register-ScheduledTask `
        -TaskName $taskName `
        -Trigger $trigger `
        -Action $action `
        -Settings $settings `
        -Principal $principal `
        -Force:$Force `
        | Out-Null

    Write-Host "  Registered: $taskName" -ForegroundColor Green
}

Write-Host ""
Write-Host "Done. Bots will start automatically at next login." -ForegroundColor Cyan
Write-Host "Manage tasks: taskschd.msc"
