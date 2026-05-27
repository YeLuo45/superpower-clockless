# PRD V2 Direction A: ai-superpower API Client + MCP Bridge

## Background

superpower-clockless V1 installs ai-superpower and prj-proposals-manager instructions into Hermes, OpenClaw, Cursor, Claude Code, and Codex. Direction A turns the MCP placeholder into a practical bridge so these agents can query and mutate projects/proposals through ai-superpower instead of direct CSV edits.

## Goals

- Provide a reusable Python API client for ai-superpower REST endpoints.
- Provide a minimal MCP stdio server that exposes project/proposal operations to supported agents.
- Keep installation zero-extra-runtime-dependency and compatible with Python 3.10+.
- Preserve unattended-mode requirements: use ai-superpower for project/proposal CRUD and keep auditable records.

## Scope

- Add `SuperpowerClient` with health, list/get/create/update-status/update-fields methods for projects/proposals.
- Add MCP JSON-RPC stdio implementation with `tools/list` and `tools/call`.
- Expose MCP tools: `health`, `project_list`, `project_get`, `proposal_list`, `proposal_get`, `proposal_create`, `proposal_update_fields`, `proposal_update_status`.
- Add CLI compatibility: `superpower-clockless mcp` now starts the bridge, while `mcp-info` prints metadata.
- Update README and design documentation.

## Acceptance Criteria

- Tests run with 100% pass rate.
- Coverage is at least 90% for the package.
- CLI install behavior remains backward compatible for existing agents.
- MCP server returns valid JSON-RPC responses for initialize, tools/list, and tools/call.
- API client sends `X-API-Key` and JSON bodies correctly without curl.

## Out of Scope

- Full MCP resource/prompt support.
- Background ai-superpower server lifecycle management beyond existing `--start-server` hook.
- Auth token generation or secret storage.
