from __future__ import annotations

import json
from pathlib import Path

import pytest

from superpower_clockless.installer import InstallError, install_agent, load_catalog, run


def test_catalog_contains_required_agents() -> None:
    catalog = load_catalog()

    assert set(catalog) >= {"hermes", "openclaw", "cursor", "claude-code", "codex"}


def test_rejects_unsupported_agent() -> None:
    with pytest.raises(InstallError):
        install_agent("unknown-agent", dry_run=True)


def test_dry_run_hermes_includes_core_and_does_not_write_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))

    plan = install_agent("hermes", api_url="http://127.0.0.1:8000", dry_run=True)

    assert plan.dry_run is True
    assert plan.install_core is True
    assert plan.install_root == str(tmp_path / ".superpower-clockless" / "ai-superpower")
    assert any("core file" in action for action in plan.actions)
    assert any("copy" in action for action in plan.actions)
    assert any("config.yaml" in action for action in plan.actions)
    assert not (tmp_path / ".superpower-clockless" / "ai-superpower").exists()
    assert not (tmp_path / ".hermes" / "config.yaml").exists()


def test_cursor_install_merges_existing_mcp_servers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    config_path = tmp_path / ".cursor" / "mcp.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(json.dumps({"mcpServers": {"existing": {"command": "node"}}}), encoding="utf-8")

    plan = install_agent("cursor", api_url="http://127.0.0.1:9000", dry_run=False)

    data = json.loads(config_path.read_text(encoding="utf-8"))
    assert "existing" in data["mcpServers"]
    assert data["mcpServers"]["superpower"]["command"] == "superpower-clockless"
    assert data["mcpServers"]["superpower"]["env"]["AI_SUPERPOWER_URL"] == "http://127.0.0.1:9000"
    assert (tmp_path / ".cursor" / "rules" / "prj-proposals-manager.mdc").exists()
    assert plan.agent == "cursor"


def test_codex_install_appends_toml_block_idempotently(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    config_path = tmp_path / ".codex" / "config.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text("model = \"gpt-5\"\n", encoding="utf-8")

    install_agent("codex", api_url="http://127.0.0.1:8000", dry_run=False)
    install_agent("codex", api_url="http://127.0.0.1:8000", dry_run=False)

    content = config_path.read_text(encoding="utf-8")
    assert content.count("# superpower-clockless BEGIN") == 1
    assert "[mcp_servers.superpower]" in content
    assert (tmp_path / ".codex" / "skills" / "prj-proposals-manager" / "SKILL.md").exists()


def test_claude_install_merges_json_and_instruction(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))

    install_agent("claude-code", dry_run=False)

    data = json.loads((tmp_path / ".claude.json").read_text(encoding="utf-8"))
    assert data["mcpServers"]["superpower"]["args"] == ["mcp"]
    assert "Superpower Clockless" in (tmp_path / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")


def test_mcp_info_cli_lists_real_tools(capsys: pytest.CaptureFixture[str]) -> None:
    assert run(["mcp-info"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["name"] == "superpower"
    assert "proposal_create" in payload["tools"]
