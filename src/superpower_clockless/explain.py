from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .installer import DEFAULT_API_URL, SUPPORTED_AGENTS, expand, install_agent, load_catalog


@dataclass(frozen=True)
class ExplainPlan:
    agent: str
    api_url: str
    config_path: str
    skill_path: str
    mcp_server_key: str
    actions: list[str]


def _explain_one(agent: str, api_url: str, start_server: bool) -> ExplainPlan:
    catalog = load_catalog()
    meta = catalog[agent]
    plan = install_agent(agent, api_url=api_url, start_server=start_server, dry_run=True)
    return ExplainPlan(
        agent=agent,
        api_url=api_url,
        config_path=str(expand(meta["configPath"])),
        skill_path=str(expand(meta["skillPath"])),
        mcp_server_key=meta["mcpServerKey"],
        actions=plan.actions,
    )


def build_explain_plans(agent: str = "all", *, api_url: str = DEFAULT_API_URL, start_server: bool = False) -> list[ExplainPlan]:
    agents = list(SUPPORTED_AGENTS) if agent == "all" else [agent]
    unsupported = [name for name in agents if name not in SUPPORTED_AGENTS]
    if unsupported:
        raise ValueError(f"unsupported agent: {unsupported[0]}")
    return [_explain_one(name, api_url, start_server) for name in agents]


def format_explain_json(plans: list[ExplainPlan]) -> str:
    payload = {"ok": True, "plans": [asdict(plan) for plan in plans]}
    return json.dumps(payload, ensure_ascii=False, indent=2)


def format_explain_text(plans: list[ExplainPlan]) -> str:
    lines: list[str] = []
    for plan in plans:
        lines.append(f"{plan.agent}: install preview")
        lines.append(f"  api_url: {plan.api_url}")
        lines.append(f"  config_path: {Path(plan.config_path)}")
        lines.append(f"  skill_path: {Path(plan.skill_path)}")
        lines.append(f"  mcp_server_key: {plan.mcp_server_key}")
        lines.append("  actions:")
        lines.extend(f"    - {action}" for action in plan.actions)
    return "\n".join(lines)
