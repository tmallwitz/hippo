#Requires -Version 5.1
<#
.SYNOPSIS
    Interactive deployment wizard for Hippo on Windows 11 Pro.

.DESCRIPTION
    9-step idempotent wizard that guides you through a full Hippo setup
    on a fresh Windows 11 Pro machine. Safe to re-run when adding bots
    or updating tokens — existing .env values are never overwritten without
    your explicit confirmation.

.EXAMPLE
    .\scripts\deploy.ps1
#>

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# Allow script execution for this process only (does not change system policy)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EnvFile     = Join-Path $ProjectRoot ".env"
$BotsYaml   = Join-Path $ProjectRoot "bots.yaml"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

function Write-Step([int]$n, [string]$title) {
    Write-Host ""
    Write-Host "━━━ Step $n/9: $title ━━━" -ForegroundColor Cyan
}

function Write-Ok([string]$msg)   { Write-Host "  [OK]  $msg" -ForegroundColor Green }
function Write-Warn([string]$msg) { Write-Host "  [!!]  $msg" -ForegroundColor Yellow }
function Write-Fail([string]$msg) { Write-Host "  [XX]  $msg" -ForegroundColor Red }

function Prompt-Confirm([string]$question) {
    $ans = Read-Host "$question [y/N]"
    return ($ans -match '^[yY]')
}

function Read-EnvFile([string]$path) {
    $result = @{}
    if (Test-Path $path) {
        foreach ($line in (Get-Content $path)) {
            if ($line -match '^\s*([^#][^=]*)\s*=\s*(.*)$') {
                $result[$Matches[1].Trim()] = $Matches[2].Trim()
            }
        }
    }
    return $result
}

function Write-EnvValue([string]$path, [string]$key, [string]$value, [hashtable]$existing) {
    if ($existing.ContainsKey($key) -and $existing[$key] -ne "") {
        if (-not (Prompt-Confirm "  $key already set. Overwrite?")) {
            Write-Warn "Kept existing value for $key"
            return
        }
    }
    # Append or update
    $lines = @()
    $found = $false
    if (Test-Path $path) {
        foreach ($line in (Get-Content $path)) {
            if ($line -match "^\s*$([regex]::Escape($key))\s*=") {
                $lines += "$key=$value"
                $found = $true
            } else {
                $lines += $line
            }
        }
    }
    if (-not $found) { $lines += "$key=$value" }
    $lines | Set-Content $path -Encoding UTF8
}

function Parse-BotNames([string]$yamlPath) {
    $names = @()
    if (-not (Test-Path $yamlPath)) { return $names }
    $inBots = $false
    foreach ($line in (Get-Content $yamlPath)) {
        if ($line -match '^bots\s*:') { $inBots = $true; continue }
        if ($inBots -and $line -match '^\s{2}([A-Za-z][A-Za-z0-9_]*)\s*:') {
            $names += $Matches[1]
        }
        if ($inBots -and $line -match '^[A-Za-z]' -and $line -notmatch '^bots\s*:') {
            $inBots = $false
        }
    }
    return $names
}

function Scaffold-Vault([string]$vaultPath) {
    $dirs = @(
        "semantic", "episodic",
        "short_term", "short_term/processed",
        "scheduled", "inbox",
        "raw", "raw/processed",
        "personality", "dream_reports",
        ".claude", ".claude/skills"
    )
    foreach ($d in $dirs) {
        $full = Join-Path $vaultPath $d
        if (-not (Test-Path $full)) {
            New-Item -ItemType Directory -Path $full -Force | Out-Null
        }
    }
}

# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------

Write-Host ""
Write-Host "╔══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Hippo Deployment Wizard             ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════╝" -ForegroundColor Cyan

# --- Step 1: Prerequisites ---------------------------------------------------
Write-Step 1 "Prerequisites check"

$prereqOk = $true

$gitVer = git --version 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Ok "git: $gitVer"
} else {
    Write-Fail "git not found. Install: https://git-scm.com/download/win"
    $prereqOk = $false
}

$uvVer = uv --version 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Ok "uv: $uvVer"
} else {
    Write-Fail "uv not found. Install: https://docs.astral.sh/uv/getting-started/installation/"
    $prereqOk = $false
}

$pyVer = python --version 2>$null
if ($LASTEXITCODE -eq 0) {
    if ($pyVer -match 'Python 3\.(\d+)') {
        $minor = [int]$Matches[1]
        if ($minor -ge 12) {
            Write-Ok "Python: $pyVer"
        } else {
            Write-Fail "Python 3.12+ required, found: $pyVer"
            $prereqOk = $false
        }
    }
} else {
    Write-Warn "python not found on PATH (uv will manage Python — continuing)"
}

if (-not $prereqOk) {
    Write-Host ""
    Write-Fail "Some prerequisites are missing. Install them and re-run this wizard."
    exit 1
}

# --- Step 2: Clone / update --------------------------------------------------
Write-Step 2 "Clone / update repository"

$gitDir = Join-Path $ProjectRoot ".git"
if (Test-Path $gitDir) {
    Write-Ok "Repository already cloned at $ProjectRoot"
    if (Prompt-Confirm "  Run git pull to update?") {
        Push-Location $ProjectRoot
        git pull
        Pop-Location
    }
} else {
    $repoUrl = Read-Host "  Enter repository URL (e.g. https://github.com/tmallwitz/hippo)"
    git clone $repoUrl $ProjectRoot
    Write-Ok "Cloned to $ProjectRoot"
}

# --- Step 3: Dependencies ----------------------------------------------------
Write-Step 3 "Install dependencies"

Push-Location $ProjectRoot
uv sync
Pop-Location
Write-Ok "Dependencies installed"

# --- Step 4: Claude auth -----------------------------------------------------
Write-Step 4 "Claude authentication"

$claudeCmd = Get-Command claude -ErrorAction SilentlyContinue
if ($claudeCmd) {
    Write-Ok "claude CLI found at $($claudeCmd.Source)"
} else {
    Write-Warn "claude CLI not found. Install Claude Code: https://claude.ai/download"
}
Write-Host "  Run 'claude login' in a terminal to authenticate, then press Enter to continue."
Read-Host "  Press Enter when authenticated"
Write-Ok "Claude auth step complete"

# --- Step 5: Bot configuration -----------------------------------------------
Write-Step 5 "Bot configuration"

$existing = Read-EnvFile $EnvFile

# Ensure shared defaults are present
$sharedDefaults = @{
    "HIPPO_MODEL"      = "claude-sonnet-4-5"
    "HIPPO_DREAM_MODEL" = "claude-sonnet-4-5"
    "HIPPO_TIMEZONE"   = "Europe/Berlin"
}
foreach ($k in $sharedDefaults.Keys) {
    if (-not $existing.ContainsKey($k) -or $existing[$k] -eq "") {
        "$k=$($sharedDefaults[$k])" | Add-Content $EnvFile -Encoding UTF8
        Write-Ok "Set default: $k=$($sharedDefaults[$k])"
    }
}

# Configure bots
$numBots = [int](Read-Host "  How many bots do you want to configure?")
$configuredBots = @()

for ($i = 1; $i -le $numBots; $i++) {
    Write-Host ""
    Write-Host "  --- Bot $i of $numBots ---" -ForegroundColor White
    $botName = Read-Host "  Bot name (e.g. Alice)"
    if ($botName -notmatch '^[A-Za-z][A-Za-z0-9_]*$') {
        Write-Fail "Invalid name '$botName'. Must start with a letter, letters/digits/underscores only."
        $i--; continue
    }
    $prefix = $botName.ToUpper() + "_"

    $existing = Read-EnvFile $EnvFile  # re-read in case we wrote above

    $token = Read-Host "  Telegram bot token (from @BotFather)"
    Write-EnvValue $EnvFile "${prefix}TELEGRAM_BOT_TOKEN" $token $existing

    $ids = Read-Host "  Allowed Telegram user IDs (comma-separated)"
    $existing = Read-EnvFile $EnvFile
    Write-EnvValue $EnvFile "${prefix}ALLOWED_TELEGRAM_IDS" $ids $existing

    $vault = Read-Host "  Vault path (e.g. C:\Users\you\hippo-vaults\$botName)"
    $existing = Read-EnvFile $EnvFile
    Write-EnvValue $EnvFile "${prefix}HIPPO_VAULT_PATH" $vault $existing

    $configuredBots += @{ Name = $botName; Vault = $vault }
    Write-Ok "Configured $botName"
}

# Update bots.yaml
Write-Host ""
if (Prompt-Confirm "  Update bots.yaml with configured bots?") {
    $yaml = "# Bot registry for inter-bot mailbox (Hippo Phase 3)`n#`nbots:`n"
    foreach ($b in $configuredBots) {
        $vaultYaml = $b.Vault -replace '\\', '/'
        $yaml += "  $($b.Name.ToLower()):`n"
        $yaml += "    vault: $vaultYaml`n"
        $yaml += "    role: `"`"`n"
    }
    # Merge with existing bots not in configuredBots
    $existingBots = Parse-BotNames $BotsYaml
    foreach ($eb in $existingBots) {
        if (-not ($configuredBots | Where-Object { $_.Name -eq $eb })) {
            Write-Warn "Keeping existing bot '$eb' from bots.yaml (not reconfigured)"
        }
    }
    $yaml | Set-Content $BotsYaml -Encoding UTF8
    Write-Ok "Updated bots.yaml"
}

# --- Step 6: Vault scaffold --------------------------------------------------
Write-Step 6 "Vault scaffold"

foreach ($b in $configuredBots) {
    $vault = $b.Vault
    if (-not (Test-Path $vault)) {
        New-Item -ItemType Directory -Path $vault -Force | Out-Null
        Write-Ok "Created vault: $vault"
    }
    Scaffold-Vault $vault
    Write-Ok "Scaffolded: $($b.Name) -> $vault"
}

# --- Step 7: Smoke test ------------------------------------------------------
Write-Step 7 "Smoke test"

Write-Warn "Smoke test starts each bot for 5 seconds. Ensure your Telegram tokens are correct."
if (-not (Prompt-Confirm "  Run smoke test?")) {
    Write-Warn "Skipped smoke test"
} else {
    $procs = @()
    foreach ($b in $configuredBots) {
        $proc = Start-Process `
            -FilePath "uv" `
            -ArgumentList "run", "hippo", $b.Name `
            -WorkingDirectory $ProjectRoot `
            -PassThru `
            -NoNewWindow
        $procs += @{ Name = $b.Name; Proc = $proc }
        Write-Host "  Started $($b.Name) (PID: $($proc.Id))..."
    }

    Start-Sleep -Seconds 5

    $allOk = $true
    foreach ($p in $procs) {
        if ($p.Proc.HasExited) {
            Write-Fail "$($p.Name) exited early (exit code $($p.Proc.ExitCode))"
            $allOk = $false
        } else {
            Write-Ok "$($p.Name) is running"
            $p.Proc.Kill()
        }
    }

    if ($allOk) {
        Write-Ok "Smoke test passed"
    } else {
        Write-Warn "Some bots failed — check logs/ for details"
    }
}

# --- Step 8: Task Scheduler --------------------------------------------------
Write-Step 8 "Task Scheduler (auto-start on login)"

if (Prompt-Confirm "  Install Task Scheduler tasks for auto-start?") {
    & (Join-Path $PSScriptRoot "install-tasks.ps1")
} else {
    Write-Warn "Skipped — run scripts\install-tasks.ps1 later to enable auto-start"
}

# --- Step 9: Summary ---------------------------------------------------------
Write-Step 9 "Summary"

Write-Host ""
Write-Host "  Configured bots:" -ForegroundColor White
foreach ($b in $configuredBots) {
    Write-Host "    • $($b.Name) -> $($b.Vault)" -ForegroundColor Green
}
Write-Host ""
Write-Host "  Start all bots:   .\scripts\start-bots.ps1" -ForegroundColor White
Write-Host "  Start one bot:    uv run hippo <BotName>" -ForegroundColor White
Write-Host "  View logs:        logs\<BotName>.log" -ForegroundColor White
Write-Host ""
Write-Host "  Manual follow-up items:" -ForegroundColor Yellow
Write-Host "    • Verify Telegram bot tokens with @BotFather"
Write-Host "    • Fill in vault paths in bots.yaml if roles are needed for inter-bot mailbox"
Write-Host "    • Run 'claude login' if not already authenticated"
Write-Host ""
Write-Ok "Deployment complete!"
