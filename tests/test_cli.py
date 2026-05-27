from __future__ import annotations

import json

from superpower_clockless.cli import main


def test_cli_main_returns_install_error_code(monkeypatch, capsys) -> None:
    monkeypatch.setattr("sys.argv", ["superpower-clockless", "install", "unknown"])

    code = main()

    assert code == 2
    assert "invalid choice" in capsys.readouterr().err or code == 2


def test_mcp_info_via_cli_main(monkeypatch, capsys) -> None:
    monkeypatch.setattr("sys.argv", ["superpower-clockless", "mcp-info"])

    assert main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert "project_list" in payload["tools"]
