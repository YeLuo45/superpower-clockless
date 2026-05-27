from __future__ import annotations

import json

from superpower_clockless.mcp_server import SuperpowerMCPServer, tool_names


class FakeClient:
    def __init__(self) -> None:
        self.calls = []

    def health(self):
        self.calls.append(("health", {}))
        return {"status": "healthy"}

    def list_projects(self, **kwargs):
        self.calls.append(("list_projects", kwargs))
        return {"items": [{"id": "PRJ-1"}]}

    def get_project(self, project_id):
        self.calls.append(("get_project", {"project_id": project_id}))
        return {"id": project_id}

    def list_proposals(self, **kwargs):
        self.calls.append(("list_proposals", kwargs))
        return {"items": [{"id": "P-1"}]}

    def get_proposal(self, proposal_id):
        self.calls.append(("get_proposal", {"proposal_id": proposal_id}))
        return {"id": proposal_id}

    def create_proposal(self, **kwargs):
        self.calls.append(("create_proposal", kwargs))
        return {"id": "P-new", **kwargs}

    def update_proposal_fields(self, proposal_id, **fields):
        self.calls.append(("update_proposal_fields", {"proposal_id": proposal_id, **fields}))
        return {"id": proposal_id, **fields}

    def update_proposal_status(self, proposal_id, status):
        self.calls.append(("update_proposal_status", {"proposal_id": proposal_id, "status": status}))
        return {"id": proposal_id, "status": status}


def parse_text_payload(result: dict) -> dict:
    return json.loads(result["result"]["content"][0]["text"])


def test_tool_names_include_project_and_proposal_operations() -> None:
    assert set(tool_names()) >= {
        "health",
        "project_list",
        "project_get",
        "proposal_list",
        "proposal_get",
        "proposal_create",
        "proposal_update_fields",
        "proposal_update_status",
    }


def test_initialize_returns_capabilities() -> None:
    server = SuperpowerMCPServer(client_factory=FakeClient)

    response = server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})

    assert response["id"] == 1
    assert response["result"]["protocolVersion"] == "2024-11-05"
    assert response["result"]["capabilities"] == {"tools": {}}


def test_tools_list_returns_schemas() -> None:
    server = SuperpowerMCPServer(client_factory=FakeClient)

    response = server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})

    tools = response["result"]["tools"]
    names = {tool["name"] for tool in tools}
    assert "proposal_create" in names
    proposal_tool = next(tool for tool in tools if tool["name"] == "proposal_create")
    assert "title" in proposal_tool["inputSchema"]["properties"]


def test_tool_call_invokes_client_and_returns_json_text() -> None:
    fake = FakeClient()
    server = SuperpowerMCPServer(client_factory=lambda: fake)

    response = server.handle({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "proposal_create", "arguments": {"title": "T", "owner": "小墨", "project_id": "PRJ-1"}},
    })

    assert parse_text_payload(response)["id"] == "P-new"
    assert fake.calls == [("create_proposal", {"title": "T", "owner": "小墨", "project_id": "PRJ-1"})]


def test_tool_error_is_returned_without_crashing() -> None:
    class BrokenClient(FakeClient):
        def health(self):
            raise RuntimeError("boom")

    server = SuperpowerMCPServer(client_factory=BrokenClient)

    response = server.handle({"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "health", "arguments": {}}})

    assert response["result"]["isError"] is True
    assert "boom" in response["result"]["content"][0]["text"]


def test_unknown_method_returns_json_rpc_error() -> None:
    server = SuperpowerMCPServer(client_factory=FakeClient)

    response = server.handle({"jsonrpc": "2.0", "id": 5, "method": "missing"})

    assert response["error"]["code"] == -32601


def test_notification_returns_none() -> None:
    server = SuperpowerMCPServer(client_factory=FakeClient)

    assert server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
