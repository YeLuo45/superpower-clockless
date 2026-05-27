from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from .installer import DEFAULT_API_URL, SUPPORTED_AGENTS, expand, load_catalog

HealthProbe = Callable[[str, float], tuple[bool, str]]


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    ok: bool
    message: str


@dataclass(frozen=True)
class DoctorReport:
    agent: str
    api_url: str
    checks: list[DoctorCheck]

    @property
    def ok(self) -> bool:
        return all(check.ok for check in self.checks)


def probe_api_health(api_url: str, timeout: float = 2.0) -> tuple[bool, str]:
    url = api_url.rstrip("/") + "/health"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            if response.status == 200:
                return True, "healthy"
            return False, f"HTTP {response.status}"
    except (OSError, urllib.error.URLError) as exc:
        return False, str(exc)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _config_contains_mcp(path: Path, agent: str, server_key: str) -> bool:
    if not path.exists():
        return False
    text = _read_text(path)
    if agent in {"cursor", "claude-code", "openclaw"}:
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return False
        return server_key in data.get("mcpServers", {})
    if agent == "codex":
        return f"[mcp_servers.{server_key}]" in text and "superpower-clockless" in text
    if agent == "hermes":
        return "mcp_servers:" in text and f"{server_key}:" in text and "superpower-clockless" in text
    return False


def _skill_message(path: Path, agent: str) -> DoctorCheck:
    if agent == "cursor":
        ok = path.exists()
        return DoctorCheck("skill", ok, f"cursor rule {'found' if ok else 'missing'}: {path}")
    ok = (path / "SKILL.md").exists()
    return DoctorCheck("skill", ok, f"skill {'found' if ok else 'missing'}: {path}")


def _doctor_one(agent: str, api_url: str, timeout: float, health_probe: HealthProbe) -> DoctorReport:
    catalog = load_catalog()
    meta = catalog.get(agent)
    checks: list[DoctorCheck] = []
    checks.append(DoctorCheck("catalog", meta is not None, f"catalog entry {'found' if meta else 'missing'} for {agent}"))
    if meta is None:
        checks.append(DoctorCheck("config", False, "missing catalog metadata"))
        checks.append(DoctorCheck("mcp", False, "missing catalog metadata"))
        checks.append(DoctorCheck("skill", False, "missing catalog metadata"))
    else:
        config_path = expand(meta["configPath"])
        skill_path = expand(meta["skillPath"])
        config_ok = config_path.exists()
        checks.append(DoctorCheck("config", config_ok, f"config {'found' if config_ok else 'missing'}: {config_path}"))
        mcp_ok = _config_contains_mcp(config_path, agent, meta["mcpServerKey"])
        checks.append(DoctorCheck("mcp", mcp_ok, f"MCP server {meta['mcpServerKey']} {'configured' if mcp_ok else 'not configured'} in {config_path}"))
        checks.append(_skill_message(skill_path, agent))
    api_ok, api_message = health_probe(api_url, timeout)
    checks.append(DoctorCheck("api", api_ok, api_message))
    return DoctorReport(agent=agent, api_url=api_url, checks=checks)


def run_doctor(
    agent: str = "all",
    *,
    api_url: str = DEFAULT_API_URL,
    timeout: float = 2.0,
    health_probe: HealthProbe | None = None,
) -> list[DoctorReport]:
    agents = list(SUPPORTED_AGENTS) if agent == "all" else [agent]
    unsupported = [name for name in agents if name not in SUPPORTED_AGENTS]
    if unsupported:
        raise ValueError(f"unsupported agent: {unsupported[0]}")
    health_probe = health_probe or probe_api_health
    return [_doctor_one(name, api_url, timeout, health_probe) for name in agents]


def format_json_report(reports: list[DoctorReport]) -> str:
    payload = {
        "ok": all(report.ok for report in reports),
        "reports": [
            {"agent": report.agent, "api_url": report.api_url, "ok": report.ok, "checks": [asdict(check) for check in report.checks]}
            for report in reports
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def format_text_report(reports: list[DoctorReport]) -> str:
    lines: list[str] = []
    for report in reports:
        lines.append(f"{report.agent}: {'OK' if report.ok else 'FAIL'}")
        for check in report.checks:
            lines.append(f"  [{'OK' if check.ok else 'FAIL'}] {check.name}: {check.message}")
    return "\n".join(lines)
