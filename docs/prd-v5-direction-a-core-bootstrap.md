# PRD V5 Direction A - ai-superpower Core Bootstrap

## Proposal
- Proposal ID: P-20260527-028
- Project ID: PRJ-20260527-001
- Mode: unattended
- Direction: A from boss feedback

## Problem
Current `superpower-clockless install <agent>` only wires an agent to an expected ai-superpower service. On a machine with no ai-superpower project installed, the generated MCP config points to a missing backend and `--start-server` cannot start anything useful.

## Goal
Make the install flow bootstrap a local ai-superpower core project first, then wire agent integrations to that local service.

## User Stories
1. As a new user, I can run one command and get a local ai-superpower scaffold plus agent integration.
2. As a cautious user, I can preview all core bootstrap filesystem changes before writing anything.
3. As an existing ai-superpower user, I can keep the old adapter-only behavior with a flag.
4. As an automation agent, I can parse JSON explain output and see whether core bootstrap is included.

## Scope
- Add bundled ai-superpower core template installation into `~/.superpower-clockless/ai-superpower` by default.
- Add `--skip-core` for adapter-only installs.
- Add `--install-root` to override core install location.
- Add `--force-core` to refresh/replace existing scaffold content safely.
- Generate starter config at `<install-root>/config.toml` using `AI_SUPERPOWER_API_KEY` env reference by default.
- Adjust `--start-server` to run from the bootstrapped core path when available.
- Update explain, doctor, README, and static site copy.

## Acceptance Criteria
- Dry-run install includes core scaffold/config actions before agent actions.
- Real install creates a minimal ai-superpower project scaffold and starter config in temp HOME tests.
- `--skip-core` preserves previous adapter-only behavior.
- `explain --json` exposes core bootstrap fields and actions.
- `--start-server --dry-run` previews the exact command rooted at the install path.
- Tests pass 100%; package coverage remains at least 90%.
