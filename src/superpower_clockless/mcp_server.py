from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any, Callable

from .api_client import SuperpowerClient

Json = dict[str, Any]


def _schema(properties: Json, required: list[str] | None = None) -> Json:
    return {"type": "object", "properties": properties, "required": required or []}


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    input_schema: Json


TOOLS: tuple[Tool, ...] = (
    Tool("health", "Check ai-superpower server health", _schema({})),
    Tool("project_list", "List ai-superpower projects", _schema({"search": {"type": "string"}, "page_size": {"type": "integer"}})),
    Tool("project_get", "Get a project by ID", _schema({"project_id": {"type": "string"}}, ["project_id"])),
    Tool("proposal_list", "List proposals", _schema({"project_id": {"type": "string"}, "search": {"type": "string"}, "page_size": {"type": "integer"}})),
    Tool("proposal_get", "Get a proposal by ID", _schema({"proposal_id": {"type": "string"}}, ["proposal_id"])),
    Tool("proposal_create", "Create a proposal", _schema({"title": {"type": "string"}, "owner": {"type": "string"}, "project_id": {"type": "string"}, "stage": {"type": "string"}}, ["title", "owner", "project_id"])),
    Tool("proposal_update_fields", "Update proposal fields", _schema({"proposal_id": {"type": "string"}, "fields": {"type": "object"}}, ["proposal_id", "fields"])),
    Tool("proposal_update_status", "Update proposal status through the state machine", _schema({"proposal_id": {"type": "string"}, "status": {"type": "string"}}, ["proposal_id", "status"])),
)


def tool_names() -> list[str]:
    return [tool.name for tool in TOOLS]


class SuperpowerMCPServer:
    def __init__(self, client_factory: Callable[[], SuperpowerClient] | None = None) -> None:
        self.client_factory = client_factory or SuperpowerClient.from_env

    def handle(self, message: Json) -> Json | None:
        if "id" not in message:
            return None
        method = message.get("method")
        if method == "initialize":
            return self._result(message["id"], {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "superpower-clockless", "version": "0.2.0"}})
        if method == "tools/list":
            return self._result(message["id"], {"tools": [self._tool_payload(tool) for tool in TOOLS]})
        if method == "tools/call":
            return self._call_tool(message["id"], message.get("params", {}))
        return {"jsonrpc": "2.0", "id": message["id"], "error": {"code": -32601, "message": f"Method not found: {method}"}}

    def _call_tool(self, request_id: Any, params: Json) -> Json:
        name = params.get("name")
        arguments = params.get("arguments") or {}
        try:
            payload = self._dispatch(name, arguments)
            return self._tool_result(request_id, payload)
        except Exception as exc:  # MCP tool errors should be data, not process crashes.
            return self._tool_result(request_id, {"error": str(exc)}, is_error=True)

    def _dispatch(self, name: str, arguments: Json) -> Any:
        client = self.client_factory()
        if name == "health":
            return client.health()
        if name == "project_list":
            return client.list_projects(**arguments)
        if name == "project_get":
            return client.get_project(arguments["project_id"])
        if name == "proposal_list":
            return client.list_proposals(**arguments)
        if name == "proposal_get":
            return client.get_proposal(arguments["proposal_id"])
        if name == "proposal_create":
            return client.create_proposal(**arguments)
        if name == "proposal_update_fields":
            fields = dict(arguments.get("fields") or {})
            return client.update_proposal_fields(arguments["proposal_id"], **fields)
        if name == "proposal_update_status":
            return client.update_proposal_status(arguments["proposal_id"], arguments["status"])
        raise ValueError(f"Unknown tool: {name}")

    @staticmethod
    def _tool_payload(tool: Tool) -> Json:
        return {"name": tool.name, "description": tool.description, "inputSchema": tool.input_schema}

    @staticmethod
    def _result(request_id: Any, result: Json) -> Json:
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    def _tool_result(self, request_id: Any, payload: Any, *, is_error: bool = False) -> Json:
        text = json.dumps(payload, ensure_ascii=False, indent=2)
        result: Json = {"content": [{"type": "text", "text": text}]}
        if is_error:
            result["isError"] = True
        return self._result(request_id, result)


def serve(input_stream=sys.stdin, output_stream=sys.stdout) -> int:
    server = SuperpowerMCPServer()
    for line in input_stream:
        if not line.strip():
            continue
        response = server.handle(json.loads(line))
        if response is not None:
            output_stream.write(json.dumps(response, ensure_ascii=False) + "\n")
            output_stream.flush()
    return 0
