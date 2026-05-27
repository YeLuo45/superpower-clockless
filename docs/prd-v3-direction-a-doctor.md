# PRD V3 Direction A - Post-install Doctor

## Proposal
- Proposal ID: P-20260527-025
- Project ID: PRJ-20260527-001
- Mode: unattended
- Direction: A (auto-selected)

## Goal
Add a non-mutating `doctor` command that validates whether superpower-clockless was installed correctly for Hermes, OpenClaw, Cursor, Claude Code, and Codex.

## User Stories
1. As a user, I can run `superpower-clockless doctor --agent hermes` after installation and see a concise pass/fail report.
2. As a user, I can run `superpower-clockless doctor --agent all` to validate all supported host integrations.
3. As a user, I can run `superpower-clockless doctor --json` to get machine-readable results for CI or agent automation.
4. As a user, I can run doctor without an ai-superpower server and still see local config/skill checks; API health should be reported as failed, not crash.

## Scope
- Add validation checks for bundled catalog metadata, host config file presence, MCP server block, skill/rule files, and ai-superpower API health.
- The command must not modify files or project/proposal data.
- The command must support `--api-url`, `--agent`, and `--json`.

## Acceptance Criteria
- `doctor` exits 0 only when all selected checks pass.
- `doctor` exits 1 when any selected check fails.
- JSON output includes `ok`, `agent`, and `checks` with stable check names.
- Text output is readable in terminals and includes each check status.
- Tests cover success, missing config, API failure, all-agent aggregation, CLI JSON output, and non-mutating behavior.
- Test pass rate is 100%; coverage is at least 90%.
