import httpx
from typer.testing import CliRunner

from clockify import main
from clockify.client import ClockifyClient
from clockify.utils import summarize_by_task


def entry(description: str, project: str, start: str, end: str | None) -> dict:
    return {
        "description": description,
        "projectName": project,
        "timeInterval": {"start": start, "end": end},
    }


def test_groups_by_description_and_project_and_sums_hours():
    tasks = summarize_by_task([
        entry("dev", "A", "2025-03-03T09:00:00Z", "2025-03-03T17:00:00Z"),
        entry("dev", "A", "2025-03-04T09:00:00Z", "2025-03-04T13:30:00Z"),
        entry("dev", "B", "2025-03-05T09:00:00Z", "2025-03-05T10:00:00Z"),
        entry("call", "A", "2025-03-05T14:00:00Z", "2025-03-05T23:00:00Z"),
    ])
    assert [(t.description, t.project_name, t.hours, t.entries) for t in tasks] == [
        ("dev", "A", 12.5, 2),
        ("call", "A", 9.0, 1),
        ("dev", "B", 1.0, 1),
    ]


def test_running_entries_are_skipped():
    tasks = summarize_by_task([
        entry("dev", "A", "2025-03-03T09:00:00Z", "2025-03-03T10:00:00Z"),
        entry("dev", "A", "2025-03-04T09:00:00Z", None),
    ])
    assert len(tasks) == 1 and tasks[0].hours == 1.0 and tasks[0].entries == 1


def test_empty_description_grouped_as_dash():
    tasks = summarize_by_task([entry("", "A", "2025-03-03T09:00:00Z", "2025-03-03T10:00:00Z")])
    assert tasks[0].description == "—"


def test_cli_report_shows_tasks_and_total(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/user"):
            return httpx.Response(200, json={"id": "u1"})
        if request.url.path.endswith("/projects"):
            return httpx.Response(200, json=[{"id": "p1", "name": "Proj"}])
        assert request.url.params["start"] == "2025-03-01T00:00:00Z"
        return httpx.Response(200, json=[
            {"description": "dev", "projectId": "p1",
             "timeInterval": {"start": "2025-03-03T09:00:00Z", "end": "2025-03-03T17:00:00Z"}},
            {"description": "dev", "projectId": "p1",
             "timeInterval": {"start": "2025-03-04T09:00:00Z", "end": "2025-03-04T11:00:00Z"}},
            {"description": "review", "projectId": "p1",
             "timeInterval": {"start": "2025-03-05T09:00:00Z", "end": "2025-03-05T14:00:00Z"}},
        ])

    monkeypatch.setattr(main, "client", ClockifyClient(transport=httpx.MockTransport(handler)))
    result = CliRunner().invoke(main.app, ["report", "-m", "3", "-y", "2025"], env={"COLUMNS": "120"})
    assert result.exit_code == 0, result.output
    assert "dev" in result.output and "review" in result.output
    assert "10.0h" in result.output and "5.0h" in result.output
    assert "Total: 15.0h" in result.output
    assert "67%" in result.output
    assert result.output.index("dev") < result.output.index("review")
