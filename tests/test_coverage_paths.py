from __future__ import annotations

import io
import json
import subprocess

import pytest

from superpower_clockless.api_client import SuperpowerAPIError, SuperpowerClient
from superpower_clockless.installer import (
    append_unique,
    configure_opencode_style_json,
    copytree,
    install_agent,
    maybe_start_server,
    run,
)
from superpower_clockless.mcp_server import SuperpowerMCPServer, serve


class DummyClient:
    def list_projects(self, **kwargs):
        return {"kwargs": kwargs}

    def get_project(self, project_id):
        return {"project_id": project_id}

    def list_proposals(self, **kwargs):
        return {"kwargs": kwargs}

    def get_proposal(self, proposal_id):
        return {"proposal_id": proposal_id}

    def update_proposal_fields(self, proposal_id, **fields):
        return {"proposal_id": proposal_id, **fields}

    def update_proposal_status(self, proposal_id, status):
        return {"proposal_id": proposal_id, "status": status}

    def health(self):
        return {"ok": True}

    def create_proposal(self, **kwargs):
        return kwargs


def text_from_response(response: dict) -> dict:
    return json.loads(response["result"]["content"][0]["text"])


def call(server: SuperpowerMCPServer, name: str, arguments: dict) -> dict:
    return server.handle({"jsonrpc": "2.0", "id": name, "method": "tools/call", "params": {"name": name, "arguments": arguments}})


def test_mcp_dispatches_remaining_tools() -> None:
    server = SuperpowerMCPServer(client_factory=DummyClient)

    assert text_from_response(call(server, "project_list", {"search": "x"}))["kwargs"] == {"search": "x"}
    assert text_from_response(call(server, "project_get", {"project_id": "PRJ"}))["project_id"] == "PRJ"
    assert text_from_response(call(server, "proposal_list", {"project_id": "PRJ"}))["kwargs"] == {"project_id": "PRJ"}
    assert text_from_response(call(server, "proposal_get", {"proposal_id": "P"}))["proposal_id"] == "P"
    assert text_from_response(call(server, "proposal_update_fields", {"proposal_id": "P", "fields": {"acceptance": "accepted"}}))["acceptance"] == "accepted"
    assert text_from_response(call(server, "proposal_update_status", {"proposal_id": "P", "status": "in_dev"}))["status"] == "in_dev"
    assert call(server, "missing_tool", {})["result"]["isError"] is True


def test_mcp_serve_reads_json_lines_and_writes_responses() -> None:
    input_stream = io.StringIO('{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n')
    output_stream = io.StringIO()

    assert serve(input_stream, output_stream) == 0
    assert json.loads(output_stream.getvalue())["result"]["tools"]


def test_client_connection_error_is_wrapped() -> None:
    def opener(request, timeout=10):
        raise OSError("low level")

    client = SuperpowerClient("http://api.test", "k", opener=opener)

    with pytest.raises(OSError):
        client.health()


def test_client_project_methods_use_expected_endpoints() -> None:
    requests = []

    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): return None
        def read(self): return b'{"ok": true}'

    def opener(request, timeout=10):
        requests.append(request)
        return Response()

    client = SuperpowerClient("http://api.test", "k", opener=opener)
    client.create_project(name="n")
    client.update_project("PRJ/1", name="n2")
    client.list_proposals(search="s")
    client.get_proposal("P/1")

    assert requests[0].full_url == "http://api.test/api/projects"
    assert requests[1].full_url == "http://api.test/api/projects/PRJ/1"
    assert requests[2].full_url == "http://api.test/api/proposals?search=s"
    assert requests[3].full_url == "http://api.test/api/proposals/P/1"


def test_openclaw_install_and_start_server_dry_run(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))

    plan = install_agent("openclaw", start_server=True, dry_run=True)

    assert any("would run from" in action and ".superpower-clockless/ai-superpower" in action for action in plan.actions)
    assert any("openclaw.json" in action for action in plan.actions)


def test_append_unique_skips_existing_marker(tmp_path) -> None:
    path = tmp_path / "file.txt"
    path.write_text("# marker\n", encoding="utf-8")

    assert append_unique(path, "# marker", "new", dry_run=False).startswith("skip existing")
    assert path.read_text(encoding="utf-8") == "# marker\n"


def test_copytree_replaces_existing_destination(tmp_path) -> None:
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    dst.mkdir()
    (src / "a.txt").write_text("a", encoding="utf-8")
    (dst / "old.txt").write_text("old", encoding="utf-8")

    copytree(src, dst, dry_run=False)

    assert (dst / "a.txt").read_text(encoding="utf-8") == "a"
    assert not (dst / "old.txt").exists()


def test_maybe_start_server_handles_missing_command(monkeypatch) -> None:
    monkeypatch.setattr("shutil.which", lambda name: None)

    assert "command not found" in maybe_start_server(dry_run=False)


def test_maybe_start_server_invokes_available_command(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr("shutil.which", lambda name: "/bin/aisp" if name == "aisp" else None)
    monkeypatch.setattr(subprocess, "Popen", lambda cmd, **kwargs: calls.append((cmd, kwargs)))

    assert maybe_start_server(dry_run=False) == "started ai-superpower server in background"
    assert calls[0][0] == ["/bin/aisp", "run"]


def test_run_agents_and_install_dry_run(capsys, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))

    assert run(["agents"]) == 0
    assert "hermes" in capsys.readouterr().out
    assert run(["install", "hermes", "--dry-run"]) == 0
    assert "install plan" in capsys.readouterr().out


def test_configure_opencode_style_json_creates_server(tmp_path) -> None:
    path = tmp_path / "openclaw.json"

    configure_opencode_style_json(path, "superpower", "http://api", dry_run=False)

    assert json.loads(path.read_text(encoding="utf-8"))["mcpServers"]["superpower"]["env"]["AI_SUPERPOWER_URL"] == "http://api"
