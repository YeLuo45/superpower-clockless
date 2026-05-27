# Test Cases V5 Direction A - ai-superpower Core Bootstrap

## TC-CORE-001 Default Install Dry Run Includes Core
- Steps: call `install_agent('hermes', dry_run=True)`.
- Expected: actions include ai-superpower core scaffold/config before skill/config actions.

## TC-CORE-002 Real Install Creates Core Scaffold
- Steps: set HOME to temp dir; call `install_agent('codex', dry_run=False)`.
- Expected: `~/.superpower-clockless/ai-superpower/pyproject.toml`, `README.md`, `config.toml`, and `db/` exist; Codex skill/config also exists.

## TC-CORE-003 Skip Core Keeps Adapter-Only Mode
- Steps: call `install_agent('cursor', install_core=False, dry_run=True)`.
- Expected: no core action strings; agent integration actions remain present.

## TC-CORE-004 Explain JSON Exposes Core Plan
- Steps: run `superpower-clockless explain all --json`.
- Expected: each plan includes `install_core=true`, `install_root`, and non-empty `core_actions`.

## TC-CORE-005 Start Server Preview Uses Core Root
- Steps: call `install_agent('hermes', start_server=True, dry_run=True)`.
- Expected: final action previews server launch from the core install root; no process starts.

## TC-CORE-006 Force Core Refresh
- Steps: create existing core README; run install with `force_core=False`, then `force_core=True`.
- Expected: first run skips existing scaffold; second run refreshes template files.
