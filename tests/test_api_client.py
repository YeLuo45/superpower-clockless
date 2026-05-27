from __future__ import annotations

import json
import urllib.error
from io import BytesIO

import pytest

from superpower_clockless.api_client import SuperpowerAPIError, SuperpowerClient


class FakeResponse:
    def __init__(self, payload: dict, status: int = 200) -> None:
        self.payload = payload
        self.status = status

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class FakeOpener:
    def __init__(self) -> None:
        self.requests = []
        self.responses = []

    def queue(self, payload: dict) -> None:
        self.responses.append(FakeResponse(payload))

    def __call__(self, request, timeout: int = 10):
        self.requests.append((request, timeout))
        response = self.responses.pop(0)
        return response


def test_client_from_env_loads_url_and_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_SUPERPOWER_URL", "http://example.test/")
    monkeypatch.setenv("AI_SUPERPOWER_API_KEY", "secret")

    client = SuperpowerClient.from_env()

    assert client.base_url == "http://example.test"
    assert client.api_key == "secret"


def test_list_projects_encodes_query_and_auth_header() -> None:
    opener = FakeOpener()
    opener.queue({"items": []})
    client = SuperpowerClient("http://api.test", "k", opener=opener)

    assert client.list_projects(search="clock less", page_size=20) == {"items": []}

    request, timeout = opener.requests[0]
    assert request.full_url == "http://api.test/api/projects?search=clock+less&page_size=20"
    assert request.get_method() == "GET"
    assert request.headers["X-api-key"] == "k"
    assert timeout == 10


def test_create_proposal_posts_json_body() -> None:
    opener = FakeOpener()
    opener.queue({"id": "P-1"})
    client = SuperpowerClient("http://api.test", "k", opener=opener)

    result = client.create_proposal(title="T", owner="小墨", project_id="PRJ-1", stage="approved_for_dev")

    request, _ = opener.requests[0]
    assert result == {"id": "P-1"}
    assert request.full_url == "http://api.test/api/proposals"
    assert request.get_method() == "POST"
    assert json.loads(request.data.decode("utf-8"))["title"] == "T"
    assert request.headers["Content-type"] == "application/json"


def test_update_proposal_status_and_fields_use_dedicated_endpoints() -> None:
    opener = FakeOpener()
    opener.queue({"status": "in_dev"})
    opener.queue({"acceptance": "accepted"})
    client = SuperpowerClient("http://api.test", "k", opener=opener)

    client.update_proposal_status("P-1", "in_dev")
    client.update_proposal_fields("P-1", acceptance="accepted")

    assert opener.requests[0][0].full_url == "http://api.test/api/proposals/P-1/status"
    assert json.loads(opener.requests[0][0].data.decode()) == {"status": "in_dev"}
    assert opener.requests[1][0].full_url == "http://api.test/api/proposals/P-1/fields"
    assert json.loads(opener.requests[1][0].data.decode()) == {"acceptance": "accepted"}


def test_missing_api_key_fails_before_network() -> None:
    opener = FakeOpener()
    client = SuperpowerClient("http://api.test", "", opener=opener)

    with pytest.raises(SuperpowerAPIError, match="AI_SUPERPOWER_API_KEY"):
        client.health()

    assert opener.requests == []


def test_http_error_includes_status_and_body() -> None:
    def failing_opener(request, timeout: int = 10):
        raise urllib.error.HTTPError(request.full_url, 400, "Bad Request", {}, BytesIO(b'{"detail":"bad"}'))

    client = SuperpowerClient("http://api.test", "k", opener=failing_opener)

    with pytest.raises(SuperpowerAPIError) as exc:
        client.get_project("missing")

    assert exc.value.status == 400
    assert "bad" in str(exc.value)
