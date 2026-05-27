from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PACKAGE_ROOT = Path(__file__).resolve().parent
AGENT_CATALOG = PACKAGE_ROOT / "catalog" / "agents.json"
SKILL_TEMPLATE = PACKAGE_ROOT / "templates" / "skills" / "prj-proposals-manager"
SUPERPOWER_NOTE = PACKAGE_ROOT / "templates" / "agents" / "SUPERPOWER.md"
CURSOR_RULE = PACKAGE_ROOT / "templates" / "agents" / "cursor-rule.mdc"
DEFAULT_API_URL = "http://127.0.0.1:8000"
SUPPORTED_AGENTS = ("hermes", "openclaw", "cursor", "claude-code", "codex")


@dataclass(frozen=True)
class InstallPlan:
    agent: str
    api_url: str
    start_server: bool
    dry_run: bool
    actions: list[str]


class InstallError(RuntimeError):
    pass


def expand(path: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(path)))


def load_catalog() -> dict[str, dict[str, Any]]:
    return json.loads(AGENT_CATALOG.read_text(encoding="utf-8"))


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def copytree(src: Path, dst: Path, *, dry_run: bool) -> str:
    if dry_run:
        return f"copy {src} -> {dst}"
    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)
    return f"copied {src} -> {dst}"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any], *, dry_run: bool) -> str:
    content = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if not dry_run:
        atomic_write(path, content)
    return f"write json {path}"


def append_unique(path: Path, marker: str, block: str, *, dry_run: bool) -> str:
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in current:
        return f"skip existing block in {path}"
    new_content = (current.rstrip() + "\n\n" + block.strip() + "\n") if current else block.strip() + "\n"
    if not dry_run:
        atomic_write(path, new_content)
    return f"append block to {path}"


def mcp_json_block(api_url: str) -> dict[str, Any]:
    return {
        "command": "superpower-clockless",
        "args": ["mcp"],
        "env": {"AI_SUPERPOWER_URL": api_url, "AI_SUPERPOWER_API_KEY": "${AI_SUPERPOWER_API_KEY}"},
    }


def configure_json_mcp(path: Path, server_key: str, api_url: str, *, dry_run: bool) -> str:
    data = read_json(path)
    servers = data.setdefault("mcpServers", {})
    servers[server_key] = mcp_json_block(api_url)
    return write_json(path, data, dry_run=dry_run)


def configure_opencode_style_json(path: Path, server_key: str, api_url: str, *, dry_run: bool) -> str:
    data = read_json(path)
    mcp = data.setdefault("mcpServers", {})
    mcp[server_key] = mcp_json_block(api_url)
    return write_json(path, data, dry_run=dry_run)


def configure_yaml_append(path: Path, api_url: str, *, dry_run: bool) -> str:
    block = f"""
# superpower-clockless BEGIN
mcp_servers:
  superpower:
    command: superpower-clockless
    args: ["mcp"]
    env:
      AI_SUPERPOWER_URL: "{api_url}"
      AI_SUPERPOWER_API_KEY: "${{AI_SUPERPOWER_API_KEY}}"

memory:
  proposal_provider: ai-superpower
# superpower-clockless END
"""
    return append_unique(path, "# superpower-clockless BEGIN", block, dry_run=dry_run)


def configure_toml_append(path: Path, api_url: str, *, dry_run: bool) -> str:
    block = f"""
# superpower-clockless BEGIN
[mcp_servers.superpower]
command = "superpower-clockless"
args = ["mcp"]

[mcp_servers.superpower.env]
AI_SUPERPOWER_URL = "{api_url}"
AI_SUPERPOWER_API_KEY = "${{AI_SUPERPOWER_API_KEY}}"
# superpower-clockless END
"""
    return append_unique(path, "# superpower-clockless BEGIN", block, dry_run=dry_run)


def maybe_start_server(dry_run: bool) -> str:
    if dry_run:
        return "would run: ai-superpower run"
    if shutil.which("ai-superpower") is None and shutil.which("aisp") is None:
        return "ai-superpower command not found; install ai-superpower first or use --no-start-server"
    cmd = [shutil.which("ai-superpower") or shutil.which("aisp"), "run"]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    return "started ai-superpower server in background"


def install_agent(agent: str, *, api_url: str = DEFAULT_API_URL, start_server: bool = False, dry_run: bool = False) -> InstallPlan:
    catalog = load_catalog()
    if agent not in catalog:
        raise InstallError(f"unsupported agent: {agent}. supported: {', '.join(SUPPORTED_AGENTS)}")

    meta = catalog[agent]
    actions: list[str] = []
    skill_path = expand(meta["skillPath"])
    config_path = expand(meta["configPath"])

    actions.append(copytree(SKILL_TEMPLATE, skill_path, dry_run=dry_run))

    if agent == "hermes":
        actions.append(configure_yaml_append(config_path, api_url, dry_run=dry_run))
        actions.append(append_unique(expand("~/.hermes/SUPERPOWER.md"), "# Superpower Clockless", SUPERPOWER_NOTE.read_text(), dry_run=dry_run))
    elif agent == "codex":
        actions.append(configure_toml_append(config_path, api_url, dry_run=dry_run))
        actions.append(append_unique(expand("~/.codex/AGENTS.md"), "# Superpower Clockless", SUPERPOWER_NOTE.read_text(), dry_run=dry_run))
    elif agent == "cursor":
        actions.append(configure_json_mcp(config_path, meta["mcpServerKey"], api_url, dry_run=dry_run))
        rule_path = skill_path
        if dry_run:
            actions.append(f"copy cursor rule -> {rule_path}")
        else:
            rule_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(CURSOR_RULE, rule_path)
            actions.append(f"copied cursor rule -> {rule_path}")
    elif agent == "claude-code":
        actions.append(configure_json_mcp(config_path, meta["mcpServerKey"], api_url, dry_run=dry_run))
        actions.append(append_unique(expand("~/.claude/CLAUDE.md"), "# Superpower Clockless", SUPERPOWER_NOTE.read_text(), dry_run=dry_run))
    elif agent == "openclaw":
        actions.append(configure_opencode_style_json(config_path, meta["mcpServerKey"], api_url, dry_run=dry_run))
        actions.append(append_unique(expand("~/.openclaw/SUPERPOWER.md"), "# Superpower Clockless", SUPERPOWER_NOTE.read_text(), dry_run=dry_run))

    if start_server:
        actions.append(maybe_start_server(dry_run=dry_run))

    return InstallPlan(agent=agent, api_url=api_url, start_server=start_server, dry_run=dry_run, actions=actions)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="superpower-clockless", description="Install ai-superpower + proposal workflow into coding agents")
    sub = parser.add_subparsers(dest="command", required=True)

    install = sub.add_parser("install", help="install integration for an agent")
    install.add_argument("agent", choices=SUPPORTED_AGENTS)
    install.add_argument("--api-url", default=os.environ.get("AI_SUPERPOWER_URL", DEFAULT_API_URL))
    install.add_argument("--start-server", action="store_true")
    install.add_argument("--dry-run", action="store_true")

    sub.add_parser("agents", help="list supported agents")
    sub.add_parser("mcp", help="run MCP stdio bridge")
    sub.add_parser("mcp-info", help="print MCP bridge metadata")
    return parser


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "agents":
        for key, meta in load_catalog().items():
            print(f"{key}\t{meta['displayName']}\t{meta['kind']}")
        return 0
    if args.command == "mcp":
        from .mcp_server import serve

        return serve()
    if args.command == "mcp-info":
        from .mcp_server import tool_names

        print(json.dumps({"name": "superpower", "api_url": os.environ.get("AI_SUPERPOWER_URL", DEFAULT_API_URL), "tools": tool_names()}, indent=2))
        return 0
    plan = install_agent(args.agent, api_url=args.api_url, start_server=args.start_server, dry_run=args.dry_run)
    print(f"superpower-clockless install plan: {plan.agent}")
    for action in plan.actions:
        print(f"- {action}")
    return 0
