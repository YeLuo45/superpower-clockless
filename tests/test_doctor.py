from __future__ import annotations

import json
from pathlib import Path

from superpower_clockless.doctor import format_json_report, run_doctor
from superpower_clockless.installer import SUPPORTED_AGENTS, install_agent, run


def healthy_api(*_args, **_kwargs) -> tuple[bool, str]:
    return True, "healthy"


def failing_api(*_args, **_kwargs) -> tuple[bool, str]:
    return False, "connection refused"


def test_doctor_reports_success_for_installed_hermes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    install_agent("hermes", dry_run=False)

    reports = run_doctor("hermes", api_url="http://127.0.0.1:8000", health_probe=healthy_api)

    assert len(reports) == 1
    assert reports[0].ok is True
    assert {check.name for check in reports[0].checks} == {"catalog", "config", "mcp", "skill", "core", "api"}
    assert all(check.ok for check in reports[0].checks)


def test_doctor_detects_missing_codex_config_and_skill(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))

    report = run_doctor("codex", api_url="http://127.0.0.1:8000", health_probe=healthy_api)[0]

    checks = {check.name: check for check in report.checks}
    assert report.ok is False
    assert checks["catalog"].ok is True
    assert checks["config"].ok is False
    assert checks["mcp"].ok is False
    assert checks["skill"].ok is False
    assert checks["core"].ok is False
    assert checks["api"].ok is True


def test_doctor_api_failure_does_not_crash_and_preserves_local_checks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    install_agent("cursor", dry_run=False)

    report = run_doctor("cursor", api_url="http://127.0.0.1:65530", health_probe=failing_api)[0]

    checks = {check.name: check for check in report.checks}
    assert report.ok is False
    assert checks["config"].ok is True
    assert checks["mcp"].ok is True
    assert checks["skill"].ok is True
    assert checks["core"].ok is True
    assert checks["api"].ok is False
    assert "connection refused" in checks["api"].message


def test_doctor_all_agents_aggregates_reports(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    for agent in SUPPORTED_AGENTS:
        install_agent(agent, dry_run=False)

    reports = run_doctor("all", api_url="http://127.0.0.1:8000", health_probe=healthy_api)

    assert [report.agent for report in reports] == list(SUPPORTED_AGENTS)
    assert all(report.ok for report in reports)


def test_doctor_json_cli_output(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    install_agent("cursor", dry_run=False)
    monkeypatch.setattr("superpower_clockless.doctor.probe_api_health", healthy_api)

    code = run(["doctor", "--agent", "cursor", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["ok"] is True
    assert payload["reports"][0]["agent"] == "cursor"
    assert [check["name"] for check in payload["reports"][0]["checks"]] == ["catalog", "config", "mcp", "skill", "core", "api"]


def test_doctor_is_non_mutating(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    install_agent("codex", dry_run=False)
    config = tmp_path / ".codex" / "config.toml"
    before = config.read_text(encoding="utf-8")

    run_doctor("codex", api_url="http://127.0.0.1:8000", health_probe=healthy_api)
    run_doctor("codex", api_url="http://127.0.0.1:8000", health_probe=healthy_api)

    assert config.read_text(encoding="utf-8") == before
    assert json.loads(format_json_report(run_doctor("codex", api_url="http://127.0.0.1:8000", health_probe=healthy_api)))["ok"] is True
