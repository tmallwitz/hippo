#Requires -Version 5.1
<#
.SYNOPSIS
    Start all Hippo bots listed in bots.yaml as separate background processes.

.DESCRIPTION
    Reads bots.yaml from the project root, starts each bot as an independent
    process via `uv run hippo <BotName>`, and redirects output to
    logs\<BotName>.log and logs\<BotName>-error.log.

    The Python process handles daily log rotation via TimedRotatingFileHandler.
    This script only captures process-level startup errors in the -error.log.

.EXAMPLE
    .\scripts\start-bots.ps1
#>

$ErrorActionPreference = "Stop"

# Resolve project root (one level up from scripts/)
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BotsYaml   = Join-Path $ProjectRoot "bots.yaml"
$LogsDir    = Join-Path $ProjectRoot "logs"

if (-not (Test-Path $BotsYaml)) {
    Write-Error "bots.yaml not found at $BotsYaml"
    exit 1
}

# Parse bot names from bots.yaml (lines matching "  <name>:" under "bots:")
$yamlContent = Get-Content $BotsYaml -Raw
$botNames = @()
$inBots = $false
foreach ($line in ($yamlContent -split "`n")) {
    if ($line -match '^bots\s*:') {
        $inBots = $true
        continue
    }
    if ($inBots -and $line -match '^\s{2}([A-Za-z][A-Za-z0-9_]*)\s*:') {
        $botNames += $Matches[1]
    }
    # Stop at a top-level key that isn't indented
    if ($inBots -and $line -match '^[A-Za-z]' -and $line -notmatch '^bots\s*:') {
        $inBots = $false
    }
}

if ($botNames.Count -eq 0) {
    Write-Error "No bot names found in $BotsYaml"
    exit 1
}

# Ensure logs directory exists
if (-not (Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir | Out-Null
}

Write-Host "Starting $($botNames.Count) bot(s)..." -ForegroundColor Cyan

$pids = @()
foreach ($botName in $botNames) {
    $stdoutLog = Join-Path $LogsDir "$botName.log"
    $stderrLog = Join-Path $LogsDir "$botName-error.log"

    $proc = Start-Process `
        -FilePath "uv" `
        -ArgumentList "run", "hippo", $botName `
        -WorkingDirectory $ProjectRoot `
        -RedirectStandardOutput $stdoutLog `
        -RedirectStandardError $stderrLog `
        -PassThru `
        -NoNewWindow

    $pids += $proc.Id
    Write-Host "  Started $botName (PID: $($proc.Id)) -> $stdoutLog" -ForegroundColor Green
}

Write-Host ""
Write-Host "All bots started. PIDs: $($pids -join ', ')" -ForegroundColor Cyan
Write-Host "Logs:  $LogsDir"
Write-Host "Stop:  Stop-Process -Id <PID>"
