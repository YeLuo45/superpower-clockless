# Technical Solution V4 Direction A - Install Explain Command

## Design
Introduce an `explain` command that uses the existing `install_agent(..., dry_run=True)` planner and enriches it with catalog metadata. This avoids a second source of truth and guarantees the explain output matches install behavior.

## Components
- `ExplainPlan`: immutable data object with agent, api_url, config_path, skill_path, mcp_server_key, and actions.
- `build_explain_plans(agent, api_url, start_server)`: returns one or all dry-run plans.
- `format_explain_text(plans)`: terminal output for humans.
- `format_explain_json(plans)`: stable JSON output for automation.
- CLI integration in `installer.build_parser()` and `installer.run()`.

## Behavior
1. Validate `agent` via argparse choices: supported agent or `all`.
2. Load catalog metadata for each target agent.
3. Call `install_agent(agent, api_url=..., start_server=..., dry_run=True)`.
4. Return expanded paths and dry-run action strings.
5. Never write files and never start a process.

## Safety
- `dry_run=True` is enforced inside the explain implementation.
- `--start-server` only surfaces the planned server action (`would run: ai-superpower run`).
- No ai-superpower API calls are made.
- Existing installer behavior remains unchanged.

## Test Strategy
Use pytest with temporary HOME directories and pre-existing config files to prove explain does not mutate filesystem contents. Validate text output, JSON schema, all-agent aggregation, and start-server preview action.
