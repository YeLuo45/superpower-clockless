# PRD V4 Direction A - Install Explain Command

## Proposal
- Proposal ID: P-20260527-027
- Project ID: PRJ-20260527-001
- Mode: unattended
- Direction: A (auto-selected)

## Goal
Add a non-mutating `explain` command that shows exactly what `superpower-clockless install <agent>` would touch before a user runs the installer.

## User Stories
1. As a user, I can run `superpower-clockless explain hermes` and see the config path, skill path, MCP server key, API URL, and planned actions.
2. As a user, I can run `superpower-clockless explain all` to audit every supported host integration at once.
3. As an automation agent, I can run `superpower-clockless explain codex --json` and parse a stable machine-readable install plan.
4. As a cautious user, I can trust that `explain` never writes files, starts servers, or mutates project/proposal data.

## Scope
- Add `explain` subcommand with `agent`, `--api-url`, `--start-server`, and `--json` options.
- Reuse the existing install planner in dry-run mode.
- Include expanded local paths and planned action strings.
- Support one agent or all supported agents.
- Document the command in README and the static site.

## Acceptance Criteria
- `explain` exits 0 for supported agents and all-agent aggregation.
- `explain` rejects unsupported agents through argparse choices.
- Text output is terminal-readable and includes agent, API URL, config path, skill path, MCP server key, and actions.
- JSON output contains `plans[]` with stable keys: `agent`, `api_url`, `config_path`, `skill_path`, `mcp_server_key`, `actions`.
- Tests cover single-agent text, all-agent JSON, non-mutating behavior, start-server dry-run action, and CLI integration.
- Test pass rate is 100%; package coverage is at least 90%.
