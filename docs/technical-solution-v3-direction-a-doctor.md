# Technical Solution V3 Direction A - Doctor Command

## Design
Introduce a dedicated `doctor.py` module with pure validation functions and a small CLI wrapper in `installer.run()`.

## Components
- `DoctorCheck`: immutable check result with `name`, `ok`, and `message`.
- `DoctorReport`: immutable report with `agent`, `api_url`, `checks`, and derived `ok`.
- `run_doctor(agent, api_url, timeout)`: validates one agent or all agents.
- `format_text_report(reports)`: terminal-friendly output.
- `format_json_report(reports)`: stable JSON payload for automation.

## Checks
1. `catalog`: supported agent metadata exists.
2. `config`: expected host config file exists.
3. `mcp`: config contains a `superpower` MCP server entry.
4. `skill`: expected skill/rule file exists.
5. `api`: `GET /health` succeeds through urllib with timeout.

## Agent-Specific Paths
Reuse `catalog/agents.json` so doctor stays aligned with installer paths. Cursor uses the rule path from catalog; other agents use the bundled skill path.

## Safety
- Doctor never calls mutating ai-superpower endpoints.
- Doctor never writes local files.
- API health failures are reported as failed checks instead of raising.

## Test Strategy
Use pytest with temporary HOME directories. Create minimal installed config files via existing installer, then validate doctor behavior. Monkeypatch urllib for deterministic API success/failure.
