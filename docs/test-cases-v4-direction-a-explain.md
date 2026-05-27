# Test Cases V4 Direction A - Install Explain Command

## TC-EXP-001 Single Agent Text Explain
- Precondition: clean temp HOME.
- Steps: call `run(['explain', 'hermes', '--api-url', 'http://127.0.0.1:9000'])`.
- Expected: exit 0; stdout includes agent, config path, skill path, MCP server key, API URL, and dry-run actions.

## TC-EXP-002 All Agent JSON Explain
- Precondition: clean temp HOME.
- Steps: call `run(['explain', 'all', '--json'])`.
- Expected: JSON has `ok=true`, one plan per supported agent, and stable path/action fields.

## TC-EXP-003 Non-Mutating Behavior
- Precondition: temp HOME contains an existing Codex config file.
- Steps: run `build_explain_plans('codex')` twice.
- Expected: config file content remains unchanged and no skill directory is created.

## TC-EXP-004 Start Server Preview
- Precondition: clean temp HOME.
- Steps: call `build_explain_plans('cursor', start_server=True)`.
- Expected: actions include `would run: ai-superpower run`; no process is started.

## TC-EXP-005 CLI Rejects Unsupported Agent
- Precondition: none.
- Steps: call CLI with `explain unknown`.
- Expected: argparse returns code 2 through the CLI wrapper.
