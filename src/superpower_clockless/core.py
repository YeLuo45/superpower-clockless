from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from .installer import PACKAGE_ROOT, atomic_write, expand

CORE_TEMPLATE = PACKAGE_ROOT / "templates" / "ai-superpower"
DEFAULT_CORE_DIR = "~/.superpower-clockless/ai-superpower"


@dataclass(frozen=True)
class CoreInstallPlan:
    install_root: str
    dry_run: bool
    force: bool
    actions: list[str]


def default_install_root() -> Path:
    return expand(os.environ.get("SUPERPOWER_CLOCKLESS_CORE", DEFAULT_CORE_DIR))


def _copy_template(src: Path, dst: Path, *, dry_run: bool, force: bool) -> str:
    if dst.exists() and not force:
        return f"skip existing core file {dst}"
    if dry_run:
        verb = "refresh" if dst.exists() and force else "copy"
        return f"{verb} core file {src} -> {dst}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return f"copied core file {src} -> {dst}"


def _starter_config(root: Path) -> str:
    return f'''[api]
key = "${{AI_SUPERPOWER_API_KEY}}"
data_dir = "{root / 'db'}"

[server]
host = "127.0.0.1"
port = 8000

[backup]
enabled = false
frequency = "1h"
max_copies = 48
'''


def install_core_project(*, install_root: str | Path | None = None, dry_run: bool = False, force: bool = False) -> CoreInstallPlan:
    root = expand(str(install_root)) if install_root is not None else default_install_root()
    actions: list[str] = []

    for src in sorted(CORE_TEMPLATE.iterdir()):
        if src.is_file():
            actions.append(_copy_template(src, root / src.name, dry_run=dry_run, force=force))

    db_dir = root / "db"
    if dry_run:
        actions.append(f"ensure directory {db_dir}")
    else:
        db_dir.mkdir(parents=True, exist_ok=True)
        actions.append(f"ensured directory {db_dir}")

    config_path = root / "config.toml"
    if config_path.exists() and not force:
        actions.append(f"skip existing core config {config_path}")
    elif dry_run:
        action = "refresh" if config_path.exists() and force else "write"
        actions.append(f"{action} core config {config_path}")
    else:
        atomic_write(config_path, _starter_config(root))
        actions.append(f"wrote core config {config_path}")

    return CoreInstallPlan(install_root=str(root), dry_run=dry_run, force=force, actions=actions)


def server_start_command(core_path: str | Path | None = None) -> list[str]:
    root = expand(str(core_path)) if core_path is not None else default_install_root()
    python = shutil.which("python3") or shutil.which("python") or sys.executable
    return [python, "-m", "ai_superpower.server", "--config", str(root / "config.toml")]
