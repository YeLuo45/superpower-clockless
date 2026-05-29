# superpower-clockless

Cross-agent installer for the Superpower proposal system.

It packages two capabilities into one portable project:

- `ai-superpower`: API-first project/proposal storage with audit logs, CSV locking, validation, and lifecycle transitions.
- `prj-proposals-manager`: platform-agnostic proposal lifecycle skill for intake, PRD, TDD, development handoff, acceptance, deployment, and delivery.

The design follows the `agentmemory` pattern: one shared local service, plus thin per-agent adapters for MCP/config/skills.

## Supported Agents

| Agent | Integration |
| --- | --- |
| Hermes | `~/.hermes/config.yaml` MCP block + skill copy |
| OpenClaw | `~/.openclaw/openclaw.json` MCP block + extension skill copy |
| Cursor | `~/.cursor/mcp.json` MCP block + always-on rule |
| Claude Code | `~/.claude.json` MCP block + `CLAUDE.md` workflow note |
| Codex CLI | `~/.codex/config.toml` MCP block + `AGENTS.md` workflow note |

## Installation Without Python

`superpower-clockless` is a Python application. If you don't have Python installed, use one of the methods below.

### Option 1: Bootstrap Script (Linux/macOS)

Run the bootstrap script — it detects your OS, installs Python 3 if missing, then sets up `superpower-clockless`:

```bash
curl -fsSL https://raw.githubusercontent.com/YeLuo45/superpower-clockless/main/bootstrap.sh | bash
```

The bootstrap script:
1. Detects OS (Linux/macOS)
2. Installs Python 3.10+ via system package manager (`apt`/`brew`/`yum`)
3. Creates a Python virtual environment at `~/.superpower-clockless/venv`
4. Installs `superpower-clockless` into the venv
5. Writes `~/.superpower-clockless/env` with API key export prompt

After bootstrap, add to shell profile:
```bash
# Unix
echo 'source ~/.superpower-clockless/env' >> ~/.bashrc
source ~/.bashrc
```

### Option 2: Docker

```bash
# Pull latest image
docker pull yeluo45/superpower-clockless:latest

# Run with API key and port
docker run -d \
  --name superpower-clockless \
  -p 8000:8000 \
  -e AI_SUPERPOWER_API_KEY="<your-key>" \
  yeluo45/superpower-clockless:latest
```

Access ai-superpower API at `http://localhost:8000`. The container runs the ai-superpower server + superpower-clockless MCP bridge.

### Option 3: Standalone Binary (Windows)

Download the standalone Windows executable from GitHub Releases:

```powershell
# Download and run installer (no Python required)
irm https://raw.githubusercontent.com/YeLuo45/superpower-clockless/main/bootstrap.ps1 | iex
```

The bootstrap.ps1 script downloads and runs directly — no GitHub Releases attachment needed.

---

## Quick Start

```bash
pip install -e .
export AI_SUPERPOWER_API_KEY="<your-key>"
superpower-clockless agents
superpower-clockless mcp-info
superpower-clockless explain hermes
superpower-clockless install hermes --dry-run
superpower-clockless install hermes --api-url http://127.0.0.1:8000 --start-server
```

During install, `superpower-clockless` reads `AI_SUPERPOWER_API_KEY` or `--api-key` and writes an env file with the export. Unix/macOS uses `~/.superpower-clockless/env` and Windows uses `~/.superpower-clockless/env.bat`.

```bash
# Unix / macOS
export AI_SUPERPOWER_API_KEY="<your-key>"
```

```bat
:: Windows
@echo off
set "AI_SUPERPOWER_API_KEY=<your-key>"
```

Source this file from shell startup scripts when you want the key available in new terminal sessions.

By default, install first bootstraps a local ai-superpower scaffold at `~/.superpower-clockless/ai-superpower`, then wires the selected agent to it. Use `--skip-core` only when ai-superpower is already installed elsewhere.

Install other hosts by changing the agent name:

```bash
superpower-clockless install cursor
superpower-clockless install claude-code
superpower-clockless install codex
superpower-clockless install openclaw
```

## Runtime Model

`superpower-clockless` now bootstraps a starter ai-superpower core when needed, then wires agents to that local service.

```text
Hermes / OpenClaw / Cursor / Claude Code / Codex
        | config + MCP + skill/rules
        v
superpower-clockless MCP bridge + adapter
        |
        v
ai-superpower REST API (default http://127.0.0.1:8000)
        |
        v
projects.csv / proposals.csv / audit.log
```

## Repository Layout

```text
src/superpower_clockless/
  api_client.py                # ai-superpower REST client
  core.py                      # bundled ai-superpower core bootstrap
  doctor.py                    # post-install validation checks
  explain.py                   # non-mutating install preview plans
  mcp_server.py                # minimal MCP stdio bridge
  installer.py                 # CLI installer and config merge logic
  catalog/agents.json          # supported agent matrix
  templates/skills/            # bundled prj-proposals-manager skill
  templates/ai-superpower/     # ai-superpower package metadata snapshot
  templates/agents/            # host instruction blocks

tests/
  test_api_client.py              # REST client behavior tests
  test_mcp_server.py              # MCP bridge behavior tests
  test_installer.py               # installer behavior tests
```

## MCP Tools

`superpower-clockless mcp` starts a stdio JSON-RPC bridge. The bridge exposes these tools:

- `health`
- `project_list`, `project_get`
- `proposal_list`, `proposal_get`, `proposal_create`
- `proposal_update_fields`, `proposal_update_status`

Use `superpower-clockless mcp-info` to inspect tool names without starting the stdio loop.

## Doctor

Run the post-install doctor to verify local host wiring and ai-superpower connectivity without mutating files or data:

```bash
superpower-clockless doctor --agent hermes
superpower-clockless doctor --agent all
superpower-clockless doctor --json
```

The doctor checks catalog metadata, host config file presence, MCP server entries, skill/rule files, and `GET /health` on the configured ai-superpower API URL.

## Explain

Preview installer changes before writing any files:

```bash
superpower-clockless explain hermes
superpower-clockless explain all --json
superpower-clockless explain codex --start-server
```

The explain command reuses the install planner in dry-run mode and reports expanded config paths, skill paths, MCP server keys, API URL, and planned actions.

## Safety Rules

- All project/proposal data writes must go through ai-superpower API/CLI.
- CSV files are data storage, not a user-editing interface.
- Existing agent config files are merged, not replaced.
- Default install bootstraps ai-superpower core before agent wiring; use `--skip-core` for adapter-only mode.
- `--dry-run` shows planned filesystem changes without writing.

## Windows Support

On Windows systems:
- `~/.superpower-clockless/env.bat` is written for API key exports
- `set "AI_SUPERPOWER_API_KEY=<your-key>"` is the equivalent of `export`
- Paths like `~/.hermes/config.yaml` resolve to `%USERPROFILE%\.hermes\config.yaml`
- PowerShell users: run `.\.superpower-clockless\env.bat` or add it to `$PROFILE`

## Multi-Language Documentation

| File | Language |
| --- | --- |
| `README.md` | English |
| `README-zh.md` | Chinese (中文) |
| `README-de.md` | German (Deutsch) |
| `README-fr.md` | French (Français) |
| `README-ja.md` | Japanese (日本語) |

## Development

```bash
python -m pip install -e .[dev]
python -m pytest -q
python -m superpower_clockless.cli agents
python -m superpower_clockless.cli mcp-info
python -m superpower_clockless.cli install hermes --dry-run
```
