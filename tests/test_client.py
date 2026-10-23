import httpx
import pytest
from typer.testing import CliRunner

from clockify import main
from clockify.client import MAX_ATTEMPTS, ClockifyClient
from clockify.models import LogRequest


def make_client(handler) -> tuple[ClockifyClient, list[float]]:
    sleeps: list[float] = []
    return ClockifyClient(transport=httpx.MockTransport(handler), sleep=sleeps.append), sleeps


def test_retries_429_then_succeeds():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(429 if len(calls) == 1 else 200, json={"id": "u1"})

    client, sleeps = make_client(handler)
    assert client.get_user_id() == "u1"
    assert len(calls) == 2
    assert sleeps == [1.0]


def test_retry_after_honoured():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(429, headers={"Retry-After": "7"})
        return httpx.Response(200, json={"id": "u1"})

    client, sleeps = make_client(handler)
    client.get_user_id()
    assert sleeps == [7.0]


def test_persistent_429_raises_after_max_attempts():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(429)

    client, sleeps = make_client(handler)
    with pytest.raises(httpx.HTTPStatusError):
        client.get_user_id()
    assert len(calls) == MAX_ATTEMPTS
    assert sleeps == [1.0, 2.0, 4.0]


def test_cli_prints_clean_error_on_persistent_429(monkeypatch):
    client, _ = make_client(lambda request: httpx.Response(429))
    monkeypatch.setattr(main, "client", client)
    result = CliRunner().invoke(main.app, ["show"])
    assert result.exit_code == 1
    assert "rate limit" in result.output
    assert "Traceback" not in result.output
    assert isinstance(result.exception, SystemExit)


def test_log_flow_fetches_user_and_projects_once(monkeypatch):
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path.endswith("/user"):
            return httpx.Response(200, json={"id": "u1"})
        if request.url.path.endswith("/projects"):
            return httpx.Response(200, json=[{"id": "p1", "name": "Proj"}])
        if request.method == "POST":
            return httpx.Response(201, json={})
        return httpx.Response(200, json=[])

    client, _ = make_client(handler)
    monkeypatch.setattr(main, "client", client)
    monkeypatch.setattr(main.Prompt, "ask", lambda *a, **k: "work")
    monkeypatch.setattr(main.ui, "prompt_project", lambda projects: projects[0])
    monkeypatch.setattr(main.ui, "show_projects", lambda projects: None)
    result = CliRunner().invoke(main.app, ["log"])
    assert result.exit_code == 0, result.output
    assert sum(p.endswith("/user") for p in paths) == 1
    assert sum(p.endswith("/projects") for p in paths) == 1
    assert LogRequest  # imported for type parity
