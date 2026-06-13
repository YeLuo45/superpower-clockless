# ai-superpower Quick Reference — **MCP via mcp_aisp.py (v5.0.0+)**

> 🚫 **DEPRECATED**: This file used to document the v4 REST API (curl). v5.0.0+ uses **MCP** exclusively. The MCP unified CLI `mcp_aisp.py` is the only supported access path for normal operations.
>
> For legacy v4 curl examples, see git history. For MCP troubleshooting, see `references/mcp-connection-troubleshooting.md` and `references/mcp-aisp-cli.md`.

---

## Server Info

- **Actual port: 8000** (HTTP mode, default `ai-superpower run`); config.toml `socket_path` is a Unix-socket placeholder, NOT the HTTP port
- MCP endpoint: `http://127.0.0.1:8000/mcp/` (with trailing slash — 307 redirect if missing)
- `aisp mcp --transport=stdio` (for agents) talks directly to the same server
- Verify with: `ss -tlnp | grep 8000`

## API Key

From `~/.ai-superpower/config.toml`:
```toml
[api]
key = "<40-hex-char key>"
```

Or set env var: `AI_SUPERPOWER_API_KEY=<key>` (preferred — `mcp_aisp.py` reads this first).

## Health Check

```bash
ss -tlnp | grep 8000   # confirm server is listening
mcp_aisp.py --list      # confirm 18 tools are available
```

## Project Operations

```bash
# List projects
mcp_aisp.py list-projects --page-size 5

# Search by name
mcp_aisp.py list-projects --search "ProjectName" --page-size 5

# Create project
mcp_aisp.py create-project --name "ProjectName" --git-repo "https://github.com/owner/repo"

# Get one project
mcp_aisp.py get-project --project-id PRJ-20260608-001

# Update project
mcp_aisp.py update-project --project-id PRJ-... --name "NewName" --description "..."

# Check duplicate
mcp_aisp.py check-project-duplicate --name "X" --git-repo "https://..."

# Merge duplicates
mcp_aisp.py merge-projects --target-id PRJ-... --source-id PRJ-... --delete-source true
```

## Proposal Operations

```bash
# List proposals (filter by project/status)
mcp_aisp.py list-proposals --project-id PRJ-... --page-size 10
mcp_aisp.py list-proposals --status in_dev

# Get one proposal
mcp_aisp.py get-proposal --proposal-id P-20260608-005

# Create proposal
mcp_aisp.py create-proposal \
  --title "ProposalTitle" \
  --owner "coordinator" \
  --project-id "PRJ-YYYYMMDD-XXX" \
  --stage "approved_for_dev" \
  --prd-confirmation "timeout-approved" \
  --tech-expectations "timeout-approved" \
  --notes "mode: unattended | Direction A"

# Update proposal fields (acceptance, notes, prd_path, etc.)
mcp_aisp.py update-proposal-fields \
  --proposal-id P-... \
  --prd-path "/path/to/prd.md" \
  --tech-solution-path "/path/to/tech.md" \
  --acceptance "accepted" \
  --notes "delivered V1426"

# Walk status state machine (one transition at a time)
mcp_aisp.py update-proposal-status --proposal-id P-... --status clarifying
mcp_aisp.py update-proposal-status --proposal-id P-... --status prd_pending_confirmation
mcp_aisp.py update-proposal-status --proposal-id P-... --status approved_for_dev
mcp_aisp.py update-proposal-status --proposal-id P-... --status in_dev
mcp_aisp.py update-proposal-status --proposal-id P-... --status in_test_acceptance
mcp_aisp.py update-proposal-status --proposal-id P-... --status accepted

# Audit / Stats
mcp_aisp.py get-audit --entity proposal --op create --page-size 10
mcp_aisp.py get-stats --days 7
mcp_aisp.py get-sync-config
mcp_aisp.py export-sync
mcp_aisp.py get-sync-status
```

## Unattended Mode Defaults

For unattended iterations, set these flags on `create-proposal` to **skip both PRD and Tech confirmation gates immediately** (no cron, no boss wait):

```bash
--prd-confirmation "timeout-approved"   # Skip Step 4 PRD gate
--tech-expectations "timeout-approved"  # Skip Step 5 Tech gate
--notes "mode: unattended | Direction A"
```

Boss can override in the next session by re-setting either field to `"pending"`.

## Why MCP and not curl/urllib

- **Auth & lifespan**: MCP server enforces API key validation, request/response schema, and state machine validation
- **Audit log**: every MCP `tools/call` is logged with JSON-RPC frame (entity, op, payload)
- **Lock management**: MCP uses file locks around CSV writes — direct curl can race
- **State machine**: `update-proposal-status` is the ONLY way to transition status; REST/PUT fields silently ignore `status` field

## See also

- `references/mcp-aisp-cli.md` — full unified CLI reference (18 tools, JSON-RPC, exit codes)
- `references/mcp-connection-troubleshooting.md` — 7 MCP failure modes
- `references/api-python-urllib-quick-ref.md` — **DEPRECATED**, cron diagnostics only
- `SKILL.md` — main skill, 11 Steps all use `mcp_aisp.py`
