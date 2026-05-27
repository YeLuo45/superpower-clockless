from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

DEFAULT_API_URL = "http://127.0.0.1:8000"


class SuperpowerAPIError(RuntimeError):
    def __init__(self, message: str, *, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class SuperpowerClient:
    def __init__(
        self,
        base_url: str = DEFAULT_API_URL,
        api_key: str | None = None,
        *,
        opener: Callable[..., Any] | None = None,
        timeout: int = 10,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or ""
        self.opener = opener or urllib.request.urlopen
        self.timeout = timeout

    @classmethod
    def from_env(cls) -> "SuperpowerClient":
        return cls(
            os.environ.get("AI_SUPERPOWER_URL", DEFAULT_API_URL),
            os.environ.get("AI_SUPERPOWER_API_KEY", ""),
        )

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None, query: dict[str, Any] | None = None) -> Any:
        if not self.api_key:
            raise SuperpowerAPIError("AI_SUPERPOWER_API_KEY is required")
        clean_query = {k: v for k, v in (query or {}).items() if v not in (None, "")}
        url = f"{self.base_url}{path}"
        if clean_query:
            url = f"{url}?{urllib.parse.urlencode(clean_query)}"
        data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        request = urllib.request.Request(url, data=data, method=method)
        request.add_header("X-API-Key", self.api_key)
        if body is not None:
            request.add_header("Content-Type", "application/json")
        try:
            with self.opener(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise SuperpowerAPIError(f"ai-superpower HTTP {exc.code}: {detail}", status=exc.code) from exc
        except urllib.error.URLError as exc:
            raise SuperpowerAPIError(f"ai-superpower connection failed: {exc.reason}") from exc

    def health(self) -> Any:
        return self._request("GET", "/health")

    def list_projects(self, **query: Any) -> Any:
        return self._request("GET", "/api/projects", query=query)

    def get_project(self, project_id: str) -> Any:
        return self._request("GET", f"/api/projects/{urllib.parse.quote(project_id)}")

    def create_project(self, **payload: Any) -> Any:
        return self._request("POST", "/api/projects", body=payload)

    def update_project(self, project_id: str, **fields: Any) -> Any:
        return self._request("PUT", f"/api/projects/{urllib.parse.quote(project_id)}", body=fields)

    def list_proposals(self, **query: Any) -> Any:
        return self._request("GET", "/api/proposals", query=query)

    def get_proposal(self, proposal_id: str) -> Any:
        return self._request("GET", f"/api/proposals/{urllib.parse.quote(proposal_id)}")

    def create_proposal(self, **payload: Any) -> Any:
        return self._request("POST", "/api/proposals", body=payload)

    def update_proposal_fields(self, proposal_id: str, **fields: Any) -> Any:
        return self._request("PUT", f"/api/proposals/{urllib.parse.quote(proposal_id)}/fields", body=fields)

    def update_proposal_status(self, proposal_id: str, status: str) -> Any:
        return self._request("PUT", f"/api/proposals/{urllib.parse.quote(proposal_id)}/status", body={"status": status})
