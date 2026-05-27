# Technical Solution V5 Direction A - ai-superpower Core Bootstrap

## Design
Extend installer planning with a first-class core bootstrap phase. The default install flow becomes:

1. Bootstrap local ai-superpower scaffold under `~/.superpower-clockless/ai-superpower`.
2. Generate starter `config.toml` and writable `db/` directory.
3. Install/copy agent-specific proposal-management skills/rules.
4. Merge MCP config pointing at the local ai-superpower API URL.
5. Optionally start the server from the core path.

## New API Surface
- `install_agent(..., install_core=True, install_root=..., force_core=False)`
- CLI `install <agent> [--skip-core] [--install-root PATH] [--force-core]`
- CLI `explain <agent|all> [--skip-core] [--install-root PATH] [--force-core]`

## Implementation Details
- Add `core.py` with `CoreInstallPlan`, `install_core_project`, and `default_install_root`.
- Use existing `templates/ai-superpower` as the bundled seed, expanding it with a starter package skeleton.
- Never overwrite existing core files unless `--force-core` is set.
- In dry-run mode, return action strings only.
- `maybe_start_server` accepts optional `core_path`; dry-run reports `would run: <python> -m ai_superpower.server from <core_path>`.
- `ExplainPlan` adds `install_core`, `install_root`, and `core_actions`.

## Safety
- Existing agent config merge behavior remains idempotent.
- Core bootstrap does not touch `~/.ai-superpower` directly; it writes inside the chosen install root.
- Starter config uses `${AI_SUPERPOWER_API_KEY}` placeholder instead of embedding secrets.
- Force refresh is opt-in.

## Test Strategy
- Unit test dry-run action order.
- Unit test real temp HOME core scaffold creation.
- Unit test skip-core preserves old action shape.
- Unit test explain JSON includes core metadata.
- Unit test start-server dry-run includes install root command.
- Full pytest + coverage gate.
