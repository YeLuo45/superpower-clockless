#!/usr/bin/env python3
"""
mcp_aisp.py — Unified CLI for all ai-superpower MCP tools.

Spawns `aisp mcp --transport=stdio` as a subprocess and forwards CLI
arguments as JSON-RPC tool calls. Every command goes through the
MCP protocol (stdio JSON-RPC), NOT through the `aisp` CLI's direct
storage path.

Usage:
    mcp_aisp.py <tool-name> [tool-args]
    mcp_aisp.py --list                  # show all 18 available tools
    mcp_aisp.py --describe <tool>       # show a tool's arg schema

Examples:
    mcp_aisp.py list-projects --search "ai-"
    mcp_aisp.py get-proposal --proposal-id P-20260608-005
    mcp_aisp.py create-project --name "X" --git-repo "https://..."
    mcp_aisp.py update-proposal-status --proposal-id P-... --status accepted
    mcp_aisp.py update-proposal-fields --proposal-id P-... \\
        --fields '{"tech_expectations":"timeout-approved","notes":"..."}'

API key: read from $AI_SUPERPOWER_API_KEY env var, or fallback to
~/.ai-superpower/config.toml [api].key.

Author: 小墨 (hermes-agent coordinator) — 2026-06-10
License: MIT
"""
from __future__ import annotations
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# ─── Tool schemas ────────────────────────────────────────────────────────
# Each tool maps to argparse args. Use _json suffix to indicate a JSON-typed arg.
# Order matters for help message; required args are listed first.

TOOLS: Dict[str, Dict[str, Any]] = {
    "set_api_key": {
        "args": ["api_key"],
        "required": ["api_key"],
        "help": "Set API key (stdio mode only — writes env var for the session)",
    },
    "list_projects": {
        "args": ["page", "page_size", "search", "sort_by", "sort_order"],
        "help": "List projects (paginated, optional search). sort_by=last_update|name|create_at",
    },
    "get_project": {
        "args": ["project_id"],
        "required": ["project_id"],
        "help": "Get a specific project by ID",
    },
    "create_project": {
        # Flat args (the tool accepts name + git_repo + optionals, NOT a data dict)
        "args": ["name", "git_repo", "prj_url", "local_path", "description", "force"],
        "required": ["name"],
        "help": "Create a new project. force=True bypasses ALL duplicate checks. Exact-name match returns existing project (no error).",
    },
    "update_project": {
        # Takes (project_id, updates: dict). CLI: --project-id + individual fields
        # bundled into updates dict.
        "args": ["project_id", "name", "git_repo", "prj_url", "local_path", "description"],
        "required": ["project_id"],
        "help": "Update project. Pass any of --name --git-repo --prj-url --local-path --description.",
    },
    "check_project_duplicate": {
        "args": ["name", "git_repo"],
        "required": ["name"],
        "help": "Check if a project with same name+git_repo exists",
    },
    "list_proposals": {
        # Tool signature: page, page_size, search, status, project_id, sort_by
        "args": ["page", "page_size", "search", "status", "project_id", "sort_by"],
        "help": "List proposals. --status filter, --project-id filter, --search keyword",
    },
    "get_proposal": {
        "args": ["proposal_id"],
        "required": ["proposal_id"],
        "help": "Get a specific proposal by ID",
    },
    "create_proposal": {
        # Takes (data: dict). CLI: --title + --project-id + --owner + optionals
        # bundled into data dict.
        "args": ["title", "owner", "project_id", "stage", "prd_path", "tech_solution_path",
                 "project_path", "git_repo", "deployment_url", "prd_confirmation",
                 "tech_expectations", "engine", "target", "game_type", "notes"],
        "required": ["title", "owner", "project_id"],
        "help": "Create a new proposal. stage MUST be 'approved_for_dev' at creation.",
    },
    "update_proposal_fields": {
        # Takes (proposal_id, fields: dict). CLI bundles into fields dict.
        "args": ["proposal_id", "prd_path", "tech_solution_path", "project_path",
                 "deployment_url", "prd_confirmation", "tech_expectations", "engine",
                 "target", "game_type", "notes"],
        "required": ["proposal_id"],
        "help": "Update non-status fields (prd_path, notes, etc.). status uses update-proposal-status.",
    },
    "update_proposal_status": {
        "args": ["proposal_id", "status"],
        "required": ["proposal_id", "status"],
        "help": "Strict linear state machine: intake → clarifying → ... → delivered",
    },
    "merge_proposals_by_project": {
        # Tool signature: target_project_id, source_project_name
        "args": ["target_project_id", "source_project_name"],
        "required": ["target_project_id", "source_project_name"],
        "help": "Merge all proposals from source project to target project",
    },
    "scan_duplicate_projects": {
        # scan_duplicate_projects(case_insensitive=True, api_key)
        # Flat optional flag — no required positional args
        "args": ["case_insensitive"],
        "required": [],
        "help": "Scan existing projects for duplicate names (legacy data dedup). Returns groups [{name, count, projects:[...]}]. --case-insensitive (default true) groups 'MyProj', 'myproj', 'MYPROJ' together.",
    },
    "merge_projects": {
        # merge_projects(target_id, source_id, delete_source=True, api_key)
        "args": ["target_id", "source_id", "delete_source"],
        "required": ["target_id", "source_id"],
        "help": "Merge source INTO target: move all proposals, optionally delete source. Use with scan_duplicate_projects output to dedupe legacy data.",
    },
    "get_audit": {
        # Tool signature: page, page_size, entity, op, since
        "args": ["page", "page_size", "entity", "op", "since"],
        "help": "Query audit log. --entity=proposal|project --op=create|update|delete --since=ISO date",
    },
    "get_stats": {
        # Tool signature: days (default 30)
        "args": ["days"],
        "help": "Get aggregate statistics for last N days (default 30)",
    },
    "get_sync_config": {
        "args": [],
        "help": "Read the GitHub Pages sync configuration",
    },
    "update_sync_config": {
        # Tool signature: many optional fields
        "args": ["sync_target_repo", "sync_prj_repo", "sync_enabled", "sync_token",
                 "sync_branch", "sync_template", "sync_schedule"],
        "help": "Update sync config fields",
    },
    "export_sync": {
        "args": [],
        "help": "Trigger a GitHub Pages sync export now",
    },
    "get_sync_status": {
        "args": [],
        "help": "Get current sync status (last run, pending changes, etc.)",
    },
}

# ─── Helpers ─────────────────────────────────────────────────────────────

def find_aisp_binary() -> str:
    """Locate the `aisp` binary. Prefer dev venv, fall back to PATH."""
    candidates = [
        "/home/hermes/ai-superpower-dev/.venv/bin/aisp",
        "/usr/local/bin/aisp",
        "/home/hermes/.local/bin/aisp",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    # Fall back to PATH (resolved by subprocess)
    return "aisp"


def get_api_key() -> str:
    """Read API key from env var, fallback to config.toml."""
    key = os.environ.get("AI_SUPERPOWER_API_KEY", "").strip()
    if key:
        return key
    # Fallback: ~/.ai-superpower/config.toml
    cfg_paths = [
        Path.home() / ".ai-superpower" / "config.toml",
        Path("/home/hermes/.ai-superpower/config.toml"),
    ]
    for cfg in cfg_paths:
        if cfg.exists():
            import re
            m = re.search(r'^key\s*=\s*"([^"]+)"', cfg.read_text(), re.M)
            if m:
                return m.group(1)
    return ""


def build_parser() -> argparse.ArgumentParser:
    """Build argparse with subcommands for each tool."""
    parser = argparse.ArgumentParser(
        prog="mcp_aisp.py",
        description="Unified CLI for ai-superpower MCP tools (stdio JSON-RPC)",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List all 18 available tools and exit",
    )
    parser.add_argument(
        "--describe", metavar="TOOL",
        help="Show a tool's arguments and exit",
    )
    parser.add_argument(
        "--raw", action="store_true",
        help="Print raw JSON-RPC response (no pretty-printing)",
    )
    parser.add_argument(
        "--server", metavar="PATH",
        help="Override aisp binary path (default: auto-detect)",
    )

    sub = parser.add_subparsers(dest="tool", metavar="TOOL")

    for tool_name, schema in TOOLS.items():
        sp = sub.add_parser(
            tool_name.replace("_", "-"),
            help=schema.get("help", ""),
            description=schema.get("help", ""),
        )
        for arg in schema.get("args", []):
            flag = "--" + arg.replace("_", "-")
            required = arg in schema.get("required", [])
            # Boolean flags (action="store_true") for fields named force/...
            if arg in ("force",):
                sp.add_argument(flag, action="store_true",
                                help=f"set {arg}=True")
            else:
                sp.add_argument(flag, required=required, help=f"{arg} value")

    return parser


def print_result(result, raw: bool = False) -> int:
    """Print MCP tool result. Return exit code (0=ok, 1=error)."""
    if raw:
        # Print full object as JSON
        d = {
            "isError": getattr(result, "isError", False),
            "content": [
                {"type": "text", "text": getattr(c, "text", str(c))}
                for c in (result.content or [])
            ],
        }
        print(json.dumps(d, indent=2, ensure_ascii=False))
    else:
        for c in (result.content or []):
            text = getattr(c, "text", str(c))
            print(text)
    return 1 if getattr(result, "isError", False) else 0


async def call_tool_via_mcp(tool: str, arguments: Dict[str, Any]) -> Any:
    """Spawn aisp mcp --transport=stdio and call a tool via JSON-RPC."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    aisp = os.environ.get("MCP_AISP_BIN") or find_aisp_binary()
    params = StdioServerParameters(
        command=aisp,
        args=["mcp", "--transport=stdio"],
        env={**os.environ},  # inherit env (incl. AI_SUPERPOWER_API_KEY)
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.call_tool(tool, arguments)


# Tools that take a single dict arg (besides api_key).
# bundle_includes_id=True means the id (project_id/proposal_id) goes INTO
# the dict (e.g. create_proposal(data={title, project_id, owner})).
# bundle_includes_id=False means the id stays top-level and only OTHER
# fields go into the dict (e.g. update_project(project_id, updates={name})).
DICT_BUNDLE_TOOLS = {
    "update_project":        ("updates", False),
    "create_proposal":       ("data", True),
    "update_proposal_fields": ("fields", False),
}


def collect_args(tool: str, parsed: argparse.Namespace) -> Dict[str, Any]:
    """Collect argparse Namespace → tool arguments dict."""
    schema = TOOLS[tool]
    flat: Dict[str, Any] = {}
    for arg in schema.get("args", []):
        cli_name = arg.replace("-", "_")
        value = getattr(parsed, cli_name, None)
        if value is not None:
            flat[arg] = value

    bundle_cfg = DICT_BUNDLE_TOOLS.get(tool)
    if bundle_cfg:
        bundle_key, includes_id = bundle_cfg
        if includes_id:
            # ALL non-empty args go into the bundle
            bundled = {k: v for k, v in flat.items() if v != "" and v is not None}
            return {bundle_key: bundled}
        else:
            # Extract id arg; bundle the rest
            id_keys = ("project_id", "proposal_id")
            id_arg = next((k for k in id_keys if k in flat), None)
            if not id_arg:
                print(f"ERROR: tool {tool} requires an id arg but none provided", file=sys.stderr)
                sys.exit(2)
            bundled = {k: v for k, v in flat.items()
                       if k != id_arg and v != "" and v is not None}
            return {id_arg: flat[id_arg], bundle_key: bundled}
    return flat


def main() -> int:
    parser = build_parser()
    # Handle --list before parsing subcommands
    if "--list" in sys.argv:
        print("Available MCP tools (18):")
        for name, schema in TOOLS.items():
            print(f"  {name:30s}  {schema.get('help', '')}")
        return 0
    if "--describe" in sys.argv:
        idx = sys.argv.index("--describe")
        try:
            target = sys.argv[idx + 1].replace("-", "_")
        except IndexError:
            print("ERROR: --describe requires a tool name", file=sys.stderr)
            return 2
        if target not in TOOLS:
            print(f"ERROR: unknown tool '{target}'. Use --list to see all.", file=sys.stderr)
            return 2
        s = TOOLS[target]
        print(f"Tool: {target}")
        print(f"Help: {s.get('help', '')}")
        print(f"Args:")
        for a in s.get("args", []):
            req = " (required)" if a in s.get("required", []) else ""
            print(f"  --{a.removesuffix('_json').replace('_','-')}{req}")
        return 0

    args = parser.parse_args()
    if not args.tool:
        parser.print_help()
        return 1

    tool = args.tool.replace("-", "_")
    if args.server:
        os.environ["MCP_AISP_BIN"] = args.server

    # Inject API key — needed by the aisp mcp subprocess
    # (the server checks $AI_SUPERPOWER_API_KEY at startup, not per-call)
    key = get_api_key()
    if not key:
        print("ERROR: No API key found. Set $AI_SUPERPOWER_API_KEY or check ~/.ai-superpower/config.toml",
              file=sys.stderr)
        return 3
    os.environ["AI_SUPERPOWER_API_KEY"] = key

    tool_args = collect_args(tool, args)
    # Pass api_key as call argument too (belt + suspenders for stdio auth)
    tool_args["api_key"] = key

    # Call MCP
    try:
        result = asyncio.run(call_tool_via_mcp(tool, tool_args))
        return print_result(result, raw=args.raw)
    except KeyboardInterrupt:
        return 130
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
