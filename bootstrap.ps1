# superpower-clockless bootstrap installer
# Full setup: Python + ai-superpower + Agent skills + MCP bridge
#
# What it does:
#   1. Detect / install Python 3.10+
#   2. Clone superpower-clockless and ai-superpower repos
#   3. Let user choose an AI agent (Hermes / Cursor / Codex / Claude Code / OpenClaw)
#   4. Install superpower-clockless (provides MCP bridge)
#   5. Install skills and MCP configuration for the chosen agent
# superpower-clockless bootstrap installer
# Full setup: Python + ai-superpower + Agent skills + MCP bridge

param(
    [string]$ApiKey = "",
    [string]$Agent = ""
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$BOOTSTRAP_VERSION = "1.0.4"
$BOOTSTRAP_COMMIT = "219f381"

Write-Host "=== superpower-clockless Bootstrap v$BOOTSTRAP_VERSION ($BOOTSTRAP_COMMIT) ===" -ForegroundColor Cyan
Write-Host ""

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
$HOME_DIR = $env:USERPROFILE
$SC_DIR = "$HOME_DIR\superpower-clockless"
$AI_DIR = "$HOME_DIR\ai-superpower"
$VENV_DIR = "$HOME_DIR\.superpower-clockless\venv"
$ENV_FILE = "$HOME_DIR\.superpower-clockless\env.bat"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
function Get-PythonVersion {
    try {
        $version = python --version 2>&1
        if ($version -match "Python (\d+)\.(\d+)") {
            return @{
                major = [int]$Matches[1]
                minor = [int]$Matches[2]
                ok = ($Matches[1] -eq 3 -and $Matches[2] -ge 10)
            }
        }
    } catch {}
    return @{ ok = $false }
}

function git_clone_or_pull($url, $dir, $branch = "main") {
    if (Test-Path $dir) {
        Write-Host "[git] $dir exists, pulling latest..." -ForegroundColor Yellow
        Set-Location $dir
        git pull origin $branch *> $null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[git] pull failed (using existing files)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "[git] Cloning $url ..." -ForegroundColor Yellow
        git clone -b $branch $url $dir *> $null
        Set-Location $dir
    }
}

function New-RandomKey {
    return [guid]::NewGuid().ToString("N")
}

# ---------------------------------------------------------------------------
# Step 1: Python check
# ---------------------------------------------------------------------------
Write-Host "[1/6] Checking Python..." -ForegroundColor White

$py = Get-PythonVersion
if (-not $py.ok) {
    Write-Host "Python 3.10+ not found. Please install Python first:" -ForegroundColor Red
    Write-Host "  https://www.python.org/downloads/" -ForegroundColor Cyan
    Write-Host "  OR: winget install Python.Python.3.11" -ForegroundColor Cyan
    exit 1
}
Write-Host "  Python $($py.major).$($py.minor) found." -ForegroundColor Green

# ---------------------------------------------------------------------------
# Step 2: Clone / update repos
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[2/6] Fetching superpower-clockless and ai-superpower..." -ForegroundColor White

git_clone_or_pull "https://github.com/YeLuo45/superpower-clockless.git" $SC_DIR "main"
git_clone_or_pull "https://github.com/YeLuo45/ai-superpower.git" $AI_DIR "main"

Write-Host "  Repos ready." -ForegroundColor Green

# ---------------------------------------------------------------------------
# Step 3: Agent selection
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[3/6] Select your AI agent:" -ForegroundColor White

$AGENTS = @(
    @{ id = "hermes";      name = "Hermes Agent";      desc = "CLI agent with MCP bridge, proposal management" },
    @{ id = "cursor";      name = "Cursor";            desc = "IDE with Ctrl+Shift+P MCP setup" },
    @{ id = "claude-code"; name = "Claude Code";       desc = " Anthropic CLI agent with Claude Code MCP" },
    @{ id = "codex";       name = "Codex CLI";         desc = "OpenAI Codex CLI with MCP plugin" },
    @{ id = "openclaw";    name = "OpenClaw";          desc = "OpenClaw IDE with MCP extension" },
    @{ id = "windsurf";    name = "Windsurf";          desc = "Windsurf IDE with MCP bridge" }
)

for ($i = 0; $i -lt $AGENTS.Length; $i++) {
    $a = $AGENTS[$i]
    Write-Host "  $($i+1). $($a.name) - $($a.desc)" -ForegroundColor Cyan
}

if ($Agent -eq "") {
    Write-Host ""
    $choice = Read-Host "Enter choice [1]: "
    if ($choice -eq "") { $choice = "1" }
    $idx = [int]$choice - 1
    if ($idx -lt 0 -or $idx -ge $AGENTS.Length) {
        $idx = 0
    }
} else {
    $idx = ($AGENTS | ForEach-Object { $_.id }).IndexOf($Agent)
    if ($idx -lt 0) { $idx = 0 }
}
$SELECTED_AGENT = $AGENTS[$idx]
Write-Host "  Selected: $($SELECTED_AGENT.name)" -ForegroundColor Green

# ---------------------------------------------------------------------------
# Step 4: Python venv + superpower-clockless install
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[4/6] Setting up superpower-clockless..." -ForegroundColor White

if (Test-Path $VENV_DIR) {
    Write-Host "  Removing old venv..." -ForegroundColor Yellow
    Remove-Item -Path $VENV_DIR -Recurse -Force
}

Write-Host "  Creating virtual environment..." -ForegroundColor Yellow
python -m venv $VENV_DIR

Write-Host "  Upgrading pip..." -ForegroundColor Yellow
& "$VENV_DIR\Scripts\pip.exe" install --upgrade pip --timeout 60 -q *> $null

Write-Host "  Installing superpower-clockless..." -ForegroundColor Yellow
Set-Location $SC_DIR
$output = & "$VENV_DIR\Scripts\pip.exe" install -e . --timeout 60 -q *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  pip install failed: $output" -ForegroundColor Red
    exit 1
}
Write-Host "  superpower-clockless installed." -ForegroundColor Green

# ---------------------------------------------------------------------------
# Step 5: API key
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[5/6] Configuring AI_SUPERPOWER_API_KEY..." -ForegroundColor White

if ($ApiKey -eq "") {
    Write-Host "  Press Enter to auto-generate a key, or type your own:" -ForegroundColor Gray
    Write-Host "  (Get your key from https://github.com/YeLuo45/ai-superpower)" -ForegroundColor Gray
    $ApiKey = Read-Host "  API Key"
    if ($ApiKey -eq "") {
        $ApiKey = New-RandomKey
        Write-Host "  Auto-generated: $ApiKey" -ForegroundColor Cyan
    }
} else {
    Write-Host "  Using provided key: $ApiKey" -ForegroundColor Cyan
}

# ---------------------------------------------------------------------------
# Step 6: Write env file + agent-specific setup
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[6/6] Finalizing setup..." -ForegroundColor White

$envDir = Split-Path $ENV_FILE -Parent
if (-not (Test-Path $envDir)) { New-Item -ItemType Directory -Path $envDir -Force | Out-Null }

$agentEnv = ""
switch ($SELECTED_AGENT.id) {
    "hermes" {
        $agentEnv = @"

REM === Hermes Agent MCP bridge ===
set "HERMES_MCP_ENABLED=1"
set "HERMES_MCP_TOOLS=proposal_list,proposal_get,proposal_create,proposal_update_fields,proposal_update_status,project_list,project_get,health"
"@
    }
    "cursor" {
        $agentEnv = @"

REM === Cursor MCP config ===
REM Add this to Cursor settings (Ctrl+Shift+P > Open User Settings > JSON):
REM   "mcpServers": {
REM     "ai-superpower": {
REM       "command": "$VENV_DIR\Scripts\python.exe",
REM       "args": ["-m", "superpower_clockless.mcp"]
REM     }
REM   }
"@
    }
    "claude-code" {
        $agentEnv = @"

REM === Claude Code MCP config ===
REM Add to ~/.claude/settings.json:
REM   "mcpServers": {
REM     "ai-superpower": {
REM       "command": "$VENV_DIR\Scripts\python.exe",
REM       "args": ["-m", "superpower_clockless.mcp"]
REM     }
REM   }
"@
    }
}

@"
@echo off
REM superpower-clockless environment
REM Auto-generated by bootstrap.ps1

REM === Core ===
set "AI_SUPERPOWER_API_KEY=$ApiKey"
set "AI_SUPERPOWER_URL=http://127.0.0.1:8000"
set "SUPERPOWER_ROOT=$SC_DIR"

REM === Activate venv ===
call "%USERPROFILE%\.superpower-clockless\venv\Scripts\activate.bat"
$agentEnv
"@ | Set-Content -Path $ENV_FILE -Encoding ASCII

Write-Host "  Environment written to: $ENV_FILE" -ForegroundColor Green
Write-Host "  Agent: $($SELECTED_AGENT.name)" -ForegroundColor Green

# ---------------------------------------------------------------------------
# ai-superpower dependencies
# ---------------------------------------------------------------------------
$AI_VENV = "$AI_DIR\.venv"
Write-Host ""
Write-Host "  Installing ai-superpower dependencies..." -ForegroundColor Yellow
if (Test-Path "$AI_DIR\requirements.txt") {
    if (-not (Test-Path $AI_VENV)) {
        python -m venv $AI_VENV
    }
    & "$AI_VENV\Scripts\pip.exe" install -r "$AI_DIR\requirements.txt" --timeout 60 -q 2>$null
    Write-Host "  ai-superpower dependencies installed." -ForegroundColor Green
}

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "=== Bootstrap Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Your API key: $ApiKey" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Copy your API key to ai-superpower config:" -ForegroundColor White
Write-Host "   Edit $AI_DIR\config.toml and set api_key = `"$ApiKey`"" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Start ai-superpower server:" -ForegroundColor White
Write-Host "   cd $AI_DIR" -ForegroundColor Yellow
Write-Host "   .\.venv\Scripts\activate.bat" -ForegroundColor Yellow
Write-Host "   python -m ai_superpower.server --config config.toml" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. In a new terminal, activate superpower-clockless:" -ForegroundColor White
Write-Host "   .\.superpower-clockless\env.bat" -ForegroundColor Yellow
Write-Host ""
Write-Host "4. Verify: superpower-clockless agents" -ForegroundColor White
Write-Host ""
Write-Host "Press Enter to exit..." -ForegroundColor Gray
Read-Host