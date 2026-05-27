from __future__ import annotations

import json
from pathlib import Path

from superpower_clockless.explain import build_explain_plans, format_explain_json, format_explain_text
from superpower_clockless.installer import SUPPORTED_AGENTS, run


def test_explain_single_agent_text_includes_paths_and_actions(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))

    code = run(["explain", "hermes", "--api-url", "http://127.0.0.1:9000"])

    output = capsys.readouterr().out
    assert code == 0
    assert "hermes: install preview" in output
    assert "api_url: http://127.0.0.1:9000" in output
    assert str(tmp_path / ".hermes" / "config.yaml") in output
    assert "mcp_server_key: superpower" in output
    assert "copy" in output


def test_explain_all_agents_json_has_stable_schema(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))

    code = run(["explain", "all", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["ok"] is True
    assert [plan["agent"] for plan in payload["plans"]] == list(SUPPORTED_AGENTS)
    assert {"agent", "api_url", "config_path", "skill_path", "mcp_server_key", "actions"} <= set(payload["plans"][0])


def test_explain_is_non_mutating(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    config = tmp_path / ".codex" / "config.toml"
    config.parent.mkdir(parents=True)
    config.write_text("model = \"gpt-5\"\n", encoding="utf-8")

    before = config.read_text(encoding="utf-8")
    plans = build_explain_plans("codex", api_url="http://127.0.0.1:8000")
    plans_again = build_explain_plans("codex", api_url="http://127.0.0.1:8000")

    assert plans[0].agent == "codex"
    assert plans_again[0].actions == plans[0].actions
    assert config.read_text(encoding="utf-8") == before
    assert not (tmp_path / ".codex" / "skills" / "prj-proposals-manager").exists()


def test_explain_start_server_is_preview_only(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))

    plan = build_explain_plans("cursor", start_server=True)[0]

    assert "would run: ai-superpower run" in plan.actions
    assert not (tmp_path / ".cursor" / "mcp.json").exists()


def test_explain_formatters_are_deterministic(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    plans = build_explain_plans("openclaw")

    assert format_explain_text(plans) == format_explain_text(plans)
    assert json.loads(format_explain_json(plans))["plans"][0]["agent"] == "openclaw"
