# Design

## Goal

Create a reusable installer that brings proposal-management superpowers into multiple coding agents without re-implementing the data layer for each host.

## Agentmemory Pattern Applied

`agentmemory` uses a shared service plus host-specific adapters. `superpower-clockless` follows the same shape:

1. Shared service: ai-superpower API engine.
2. Shared workflow package: prj-proposals-manager skill.
3. Thin host adapters: config snippets, MCP server entries, and instruction files.

## Integration Contract

Every host gets three things:

- Access to ai-superpower through an MCP entry or equivalent command hook.
- The prj-proposals-manager lifecycle skill or a host-native rule file.
- A short instruction block that preserves the API-first, no-direct-CSV rule.

## Agent Targets

| Agent | Config Strategy | Workflow Strategy |
| --- | --- | --- |
| Hermes | YAML append in `~/.hermes/config.yaml` | copy full skill directory |
| OpenClaw | JSON `mcpServers` merge | copy extension skill directory |
| Cursor | JSON `mcpServers` merge | write `.mdc` rule |
| Claude Code | JSON MCP merge | append `CLAUDE.md` block + copy skill |
| Codex CLI | TOML append | append `AGENTS.md` block + copy skill |

## Non-Goals for V1

- Replace ai-superpower internals.
- Implement a full MCP protocol server in-process.
- Mutate existing proposal data.
- Install global dependencies without an explicit user action.

## Acceptance Criteria

- Installer lists all required agents.
- Dry-run install works for every agent.
- Config merge preserves existing keys.
- Skill template is bundled in the repository.
- Tests cover JSON/TOML/YAML config generation and unsupported-agent handling.
