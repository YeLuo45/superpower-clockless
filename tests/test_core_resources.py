from __future__ import annotations

from pathlib import Path

from superpower_clockless.core import install_core_project


REQUIRED_RESOURCE_PATHS = [
    ".github/workflows/deploy.yml",
    "README-dev-zh.md",
    "README-zh.md",
    "config.toml",
    "db/audit.log",
    "db/projects.csv",
    "db/proposals.csv",
    "deploy/ai-superpower.service",
    "deploy/install.sh",
    "site/404.html",
    "site/app.js",
    "site/audit.html",
    "site/data/projects.csv",
    "site/data/proposals.csv",
    "site/index.html",
    "site/projects/list.html",
    "site/proposals/list.html",
    "site/settings.html",
    "site/style.css",
    "src/ai_superpower/static/app.js",
    "src/ai_superpower/static/style.css",
    "src/ai_superpower/templates/audit.html",
    "src/ai_superpower/templates/index.html",
    "src/ai_superpower/templates/projects/list.html",
    "src/ai_superpower/templates/proposals/list.html",
    "src/ai_superpower/templates/settings.html",
]


def test_core_install_copies_nested_ai_superpower_resources(tmp_path: Path) -> None:
    install_core_project(install_root=tmp_path, dry_run=False, force=False)

    missing = [path for path in REQUIRED_RESOURCE_PATHS if not (tmp_path / path).exists()]
    assert missing == []


def test_core_install_keeps_seed_data_private_and_usable(tmp_path: Path) -> None:
    install_core_project(install_root=tmp_path, dry_run=False, force=False)

    projects_csv = (tmp_path / "db/projects.csv").read_text(encoding="utf-8")
    proposals_csv = (tmp_path / "db/proposals.csv").read_text(encoding="utf-8")

    assert projects_csv == "id,name,description,status,created_at,updated_at\n"
    assert proposals_csv == "id,project_id,title,status,stage,priority,owner,created_at,updated_at,summary\n"
    assert (tmp_path / "site/data/projects.csv").read_text(encoding="utf-8") == projects_csv
    assert (tmp_path / "site/data/proposals.csv").read_text(encoding="utf-8") == proposals_csv
