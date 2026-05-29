#!/usr/bin/env bash
# superpower-clockless bootstrap installer
# Full setup: Python + ai-superpower + Agent skills + MCP bridge
#
# What it does:
#   1. Detect / install Python 3.10+
#   2. Clone superpower-clockless and ai-superpower repos
#   3. Let user choose an AI agent (Hermes / Cursor / Codex / Claude Code / OpenClaw)
#   4. Install superpower-clockless (provides MCP bridge)
#   5. Install skills and MCP configuration for the chosen agent
#   6. Set AI_SUPERPOWER_API_KEY (user-provided or auto-generated)
#   7. Install ai-superpower dependencies

set -e

echo "=== superpower-clockless Bootstrap ==="
echo ""

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SC_DIR="$HOME/superpower-clockless"
AI_DIR="$HOME/ai-superpower"
VENV_DIR="$HOME/.superpower-clockless/venv"
ENV_FILE="$HOME/.superpower-clockless/env"

# ---------------------------------------------------------------------------
# OS detection
# ---------------------------------------------------------------------------
detect_os() {
    case "$(uname)" in
        Darwin)      echo "macos" ;;
        Linux)
            if [ -f /etc/os-release ]; then
                . /etc/os-release
                case "$ID" in
                    ubuntu|debian|linuxmint)    echo "debian" ;;
                    fedora|rhel|centos|rocky|almalinux) echo "rhel" ;;
                    arch|manjaro)                echo "arch" ;;
                    alpine)                      echo "alpine" ;;
                    *)                           echo "unknown" ;;
                esac
            else
                echo "unknown"
            fi
            ;;
        *)           echo "unknown" ;;
    esac
}

# ---------------------------------------------------------------------------
# Python check / install
# ---------------------------------------------------------------------------
check_python() {
    if command -v python3 &>/dev/null; then
        MAJOR=$(python3 -c 'import sys; print(sys.version_info[0])')
        MINOR=$(python3 -c 'import sys; print(sys.version_info[1])')
        if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 10 ]; then
            echo "ok"
            return 0
        fi
    fi
    echo "missing"
    return 1
}

install_python() {
    OS=$(detect_os)
    echo "[bootstrap] OS: $OS, installing Python 3.10+..."

    case "$OS" in
        macos)
            if ! command -v brew &>/dev/null; then
                echo "ERROR: Homebrew not found. Install from https://brew.sh"
                exit 1
            fi
            brew install python@3.11 2>/dev/null || brew install python@3.11
            ;;
        debian)
            export DEBIAN_FRONTEND=noninteractive
            apt-get update -qq
            apt-get install -y -qq python3.11 python3.11-venv python3-pip curl git
            ;;
        rhel)
            dnf install -y -q python311 python311-venv python3-pip curl git 2>/dev/null || \
            yum install -y -q python3.11 python3-venv python3-pip curl git
            ;;
        arch)
            pacman -Sy --noconfirm python python-pip curl git
            ;;
        alpine)
            apk add --no-cache python3 py3-pip curl git
            ;;
        *)
            echo "ERROR: Cannot auto-install Python on this OS. Please install Python 3.10+ manually."
            exit 1
            ;;
    esac
}

# ---------------------------------------------------------------------------
# Git clone / pull
# ---------------------------------------------------------------------------
git_clone_or_pull() {
    local url="$1"
    local dir="$2"
    local branch="${3:-main}"

    if [ -d "$dir/.git" ]; then
        echo "[git] $dir exists, pulling latest..."
        git -C "$dir" pull origin "$branch" 2>/dev/null || \
            echo "[git] pull failed, using existing files"
    else
        echo "[git] Cloning $url ..."
        git clone -b "$branch" "$url" "$dir"
    fi
}

# ---------------------------------------------------------------------------
# API key
# ---------------------------------------------------------------------------
prompt_api_key() {
    local key=""
    echo "  Press Enter to auto-generate a key, or type your own:"
    echo "  (Get your key from https://github.com/YeLuo45/ai-superpower)"
    read -r -p "  API Key: " key
    if [ -z "$key" ]; then
        if command -v openssl &>/dev/null; then
            key=$(openssl rand -hex 16)
        else
            key=$(od -An -tx1 -N16 /dev/urandom | tr -d ' \n')
        fi
        echo "  Auto-generated: $key"
    fi
    echo "$key"
}

# ---------------------------------------------------------------------------
# Agent selection
# ---------------------------------------------------------------------------
select_agent() {
    local agents=("hermes" "cursor" "claude-code" "codex" "openclaw" "windsurf")
    local names=("Hermes Agent" "Cursor" "Claude Code" "Codex CLI" "OpenClaw" "Windsurf")
    local descs=(
        "CLI agent with MCP bridge, proposal management"
        "IDE with Ctrl+Shift+P MCP setup"
        "Anthropic CLI agent with Claude Code MCP"
        "OpenAI Codex CLI with MCP plugin"
        "OpenClaw IDE with MCP extension"
        "Windsurf IDE with MCP bridge"
    )

    echo ""
    echo "[3/6] Select your AI agent:"
    for i in "${!agents[@]}"; do
        echo "  $((i+1)). ${names[$i]} - ${descs[$i]}"
    done
    echo ""

    local choice=""
    read -r -p "Enter choice [1]: " choice
    if [ -z "$choice" ]; then choice="1"; fi
    local idx=$((choice - 1))
    if [ "$idx" -lt 0 ] || [ "$idx" -ge ${#agents[@]} ]; then
        idx=0
    fi

    SELECTED_AGENT="${agents[$idx]}"
    SELECTED_NAME="${names[$idx]}"
    echo "  Selected: $SELECTED_NAME"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
echo "[1/6] Checking Python..." >&2
if ! check_python; then
    echo "[bootstrap] Python 3.10+ not found. Installing..." >&2
    install_python
else
    echo "  Python $(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")') found." >&2
fi

echo ""
echo "[2/6] Fetching superpower-clockless and ai-superpower..." >&2
git_clone_or_pull "https://github.com/YeLuo45/superpower-clockless.git" "$SC_DIR" "main"
git_clone_or_pull "https://github.com/YeLuo45/ai-superpower.git" "$AI_DIR" "main"
echo "  Repos ready." >&2

select_agent

echo ""
echo "[4/6] Setting up superpower-clockless..." >&2
if [ -d "$VENV_DIR" ]; then
    echo "  Removing old venv..." >&2
    rm -rf "$VENV_DIR"
fi
echo "  Creating virtual environment..." >&2
python3 -m venv "$VENV_DIR"
echo "  Upgrading pip..." >&2
"$VENV_DIR/bin/pip" install --upgrade pip --timeout 60 -q
echo "  Installing superpower-clockless..." >&2
"$VENV_DIR/bin/pip" install -e "$SC_DIR" --timeout 60 -q
echo "  superpower-clockless installed." >&2

echo ""
echo "[5/6] Configuring AI_SUPERPOWER_API_KEY..." >&2
API_KEY=$(prompt_api_key)

echo ""
echo "[6/6] Finalizing setup..." >&2

# Build agent-specific env block
AGENT_ENV=""
case "$SELECTED_AGENT" in
    hermes)
        AGENT_ENV="
export HERMES_MCP_ENABLED=1
export HERMES_MCP_TOOLS='proposal_list,proposal_get,proposal_create,proposal_update_fields,proposal_update_status,project_list,project_get,health'
"
        ;;
    cursor)
        AGENT_ENV="
# === Cursor MCP config ===
# Add to Cursor settings (Ctrl+Shift+P > Open User Settings > JSON):
#   \"mcpServers\": {
#     \"ai-superpower\": {
#       \"command\": \"$VENV_DIR/bin/python\",
#       \"args\": [\"-m\", \"superpower_clockless.mcp\"]
#     }
#   }
"
        ;;
    claude-code)
        AGENT_ENV="
# === Claude Code MCP config ===
# Add to ~/.claude/settings.json:
#   \"mcpServers\": {
#     \"ai-superpower\": {
#       \"command\": \"$VENV_DIR/bin/python\",
#       \"args\": [\"-m\", \"superpower_clockless.mcp\"]
#     }
#   }
"
        ;;
esac

mkdir -p "$(dirname "$ENV_FILE")"

cat > "$ENV_FILE" << ENVFILE
# superpower-clockless environment
# Auto-generated by bootstrap.sh

# === Core ===
export AI_SUPERPOWER_API_KEY="$API_KEY"
export AI_SUPERPOWER_URL="http://127.0.0.1:8000"
export SUPERPOWER_ROOT="$SC_DIR"
$AGENT_ENV
# === Activate venv ===
if [ -f "\$HOME/.superpower-clockless/venv/bin/activate" ]; then
    source "\$HOME/.superpower-clockless/venv/bin/activate"
fi
ENVFILE

chmod 600 "$ENV_FILE"
echo "  Environment written to: $ENV_FILE" >&2
echo "  Agent: $SELECTED_NAME" >&2

# Install ai-superpower dependencies
if [ -f "$AI_DIR/requirements.txt" ]; then
    echo ""
    echo "  Installing ai-superpower dependencies..." >&2
    AI_VENV="$AI_DIR/.venv"
    if [ ! -d "$AI_VENV" ]; then
        python3 -m venv "$AI_VENV"
    fi
    "$AI_VENV/bin/pip" install -r "$AI_DIR/requirements.txt" --timeout 60 -q 2>/dev/null || \
        echo "  Some ai-superpower dependencies failed (non-critical)" >&2
    echo "  ai-superpower dependencies installed." >&2
fi

echo ""
echo "=== Bootstrap Complete ===" >&2
echo ""
echo "Your API key: $API_KEY"
echo ""
echo "1. Copy your API key to ai-superpower config:"
echo "   Edit $AI_DIR/config.toml and set api_key = \"$API_KEY\""
echo ""
echo "2. Start ai-superpower server:"
echo "   cd $AI_DIR"
echo "   source .venv/bin/activate"
echo "   python -m ai_superpower.server --config config.toml"
echo ""
echo "3. In a new terminal, activate superpower-clockless:"
echo "   source ~/.superpower-clockless/env"
echo ""
echo "4. Verify: superpower-clockless agents"