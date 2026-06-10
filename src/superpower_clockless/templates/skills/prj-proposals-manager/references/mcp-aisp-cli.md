# mcp_aisp.py — Unified MCP CLI Reference (v5.0.0)

**Status**: NEW in v5.0.0 (2026-06-10)
**Replaces**: `ai-superpower ...` CLI calls and direct `urllib`/REST patterns in earlier versions

## What it is

`mcp_aisp.py` is a **single Python script** that wraps all 18 ai-superpower MCP tools as CLI subcommands. Each invocation:

1. Spawns `aisp mcp --transport=stdio` as a subprocess
2. Sends JSON-RPC `initialize` then `tools/call` over stdio
3. Prints the result and exits

**Every command goes through MCP** — there is no direct CLI or REST bypass. The script is the unified entry point for any agent or shell that needs to read/write proposal data.

## Quick start

```bash
# List all 18 tools
mcp_aisp.py --list

# Show one tool's args
mcp_aisp.py --describe create-proposal

# Common operations
mcp_aisp.py list-projects --page-size 5
mcp_aisp.py create-project --name "MyProj" --git-repo "https://..."
mcp_aisp.py create-proposal --title "..." --owner "..." --project-id "PRJ-..."
mcp_aisp.py update-proposal-status --proposal-id P-... --status in_dev
```

## API key resolution

The script tries 3 sources in order:

1. `$AI_SUPERPOWER_API_KEY` env var (preferred — matches MCP convention)
2. `~/.ai-superpower/config.toml` `[api].key` (fallback, parsed via regex)
3. Error: "No API key found" (exit code 3)

The resolved key is injected as `api_key` argument to the MCP tool AND exported into the subprocess env (some tools check env var at startup).

## Bundle behavior

Some MCP tools take a single `dict` parameter instead of flat args. The script handles two patterns:

**Pattern A: id + dict of fields** (e.g. `update_project(project_id, updates: dict)`)
```
mcp_aisp.py update-project --project-id PRJ-... --name "New" --description "..."
# Becomes: {"project_id": "PRJ-...", "updates": {"name": "New", "description": "..."}}
```

**Pattern B: dict contains all fields including id** (e.g. `create_proposal(data: dict)`)
```
mcp_aisp.py create-proposal --title "X" --owner "O" --project-id "PRJ-..." --stage approved_for_dev
# Becomes: {"data": {"title": "X", "owner": "O", "project_id": "PRJ-...", "stage": "approved_for_dev"}}
```

The `DICT_BUNDLE_TOOLS` dict at the top of the script controls this. Add a new tool with `(bundle_key, includes_id)` tuple.

## Return format

The script prints `result.content[].text` for each TextContent item, one per line. Exit codes:

| Exit | Meaning |
|------|---------|
| 0 | Tool returned success |
| 1 | Tool returned an error result (printed to stdout) |
| 2 | Invalid CLI args (missing required, bad JSON) |
| 3 | No API key found |
| 130 | Ctrl-C |
| other | Python exception (printed to stderr) |

Use `--raw` to get the full JSON envelope (`{"isError": ..., "content": [...]}`) instead of just text.

## Why MCP and not direct CLI?

`aisp project create`, `aisp proposal status` etc. are the **direct CLI path** — they call the storage layer without going through MCP. They work but:

1. They bypass MCP's auth/lifespan/lock management
2. They can't be monitored/audited the same way (no JSON-RPC frames)
3. They diverge from the SPA's MCP path (different code paths, different bugs)

`mcp_aisp.py` forces every operation through the **MCP protocol**, ensuring:
- Single canonical path for all clients (SPA + agent + cron)
- MCP auth + state machine validation apply uniformly
- Easier to add cross-cutting concerns (audit logging, rate limits) in one place

## When to use the legacy REST API

For one-off smoke tests or emergency debugging, `curl http://127.0.0.1:8000/api/...` still works (HTTP REST, X-API-Key header). Document this in SKILL.md "Legacy REST API" section. Don't use it for new code.

## Portability

The script auto-detects `aisp` binary in this order:

1. `$MCP_AISP_BIN` env var (override)
2. `/home/hermes/ai-superpower-dev/.venv/bin/aisp` (dev)
3. `/usr/local/bin/aisp` (system)
4. `/home/hermes/.local/bin/aisp` (user pip install)
5. `aisp` (PATH fallback)

Override with `--server /path/to/aisp` or set `MCP_AISP_BIN=/path/to/aisp`.

## See also

- `SKILL.md` — main skill, 11 Steps all use `mcp_aisp.py`
- `references/mcp-vs-rest-migration.md` — v4→v5 tool mapping (older version)
- `references/mcp-connection-troubleshooting.md` — 7 MCP failure modes
- ai-superpower SKILL.md § "MCP 端点" — server-side MCP setup