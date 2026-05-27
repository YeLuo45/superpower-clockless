from __future__ import annotations

import json
from pathlib import Path

from superpower_clockless.core import install_core_project
from superpower_clockless.explain import build_explain_plans
from superpower_clockless.installer import install_agent, run


def test_real_install_creates_core_scaffold_and_agent_files(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))

    plan = install_agent("codex", dry_run=False)

    core = tmp_path / ".superpower-clockless" / "ai-superpower"
    assert plan.install_root == str(core)
    assert (core / "README.md").exists()
    assert (core / "pyproject.toml").exists()
    assert (core / "config.toml").exists()
    assert (core / "db").is_dir()
    assert (tmp_path / ".codex" / "skills" / "prj-proposals-manager" / "SKILL.md").exists()


def test_skip_core_preserves_adapter_only_mode(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))

    plan = install_agent("cursor", install_core=False, dry_run=True)

    assert plan.install_core is False
    assert plan.install_root is None
    assert plan.core_actions == []
    assert not any("core file" in action or "core config" in action for action in plan.actions)
    assert any("cursor rule" in action for action in plan.actions)


def test_explain_json_exposes_core_plan(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))

    code = run(["explain", "all", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert all(plan["install_core"] is True for plan in payload["plans"])
    assert all(plan["install_root"].endswith(".superpower-clockless/ai-superpower") for plan in payload["plans"])
    assert all(plan["core_actions"] for plan in payload["plans"])


def test_start_server_preview_uses_core_root(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))

    plan = install_agent("hermes", start_server=True, dry_run=True)

    assert any("would run from" in action and ".superpower-clockless/ai-superpower" in action for action in plan.actions)


def test_force_core_refresh_changes_existing_file(tmp_path: Path) -> None:
    root = tmp_path / "core"
    root.mkdir()
    readme = root / "README.md"
    readme.write_text("custom", encoding="utf-8")

    install_core_project(install_root=root, dry_run=False, force=False)
    assert readme.read_text(encoding="utf-8") == "custom"

    install_core_project(install_root=root, dry_run=False, force=True)
    assert "ai-superpower" in readme.read_text(encoding="utf-8")


def test_explain_can_skip_core(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))

    plan = build_explain_plans("hermes", install_core=False)[0]

    assert plan.install_core is False
    assert plan.install_root is None
    assert plan.core_actions == []
