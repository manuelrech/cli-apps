import time
from collections.abc import Callable
from datetime import date, datetime, timezone

import httpx

from clockify.config import BASE_URL, HEADERS, WORKSPACE_ID
from clockify.models import LogRequest, Project, TimeEntry


RETRY_STATUSES = {429, 503}
MAX_ATTEMPTS = 4
MAX_BACKOFF = 8.0


class ClockifyClient:
    def __init__(
        self,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.workspace = WORKSPACE_ID
        self.http = httpx.Client(base_url=BASE_URL, headers=HEADERS, transport=transport)
        self.sleep = sleep
        self._user_id: str | None = None
        self._projects: list[Project] | None = None

    def _request(self, method: str, path: str, **kw) -> httpx.Response:
        for attempt in range(MAX_ATTEMPTS):
            r = self.http.request(method, path, **kw)
            if r.status_code not in RETRY_STATUSES or attempt == MAX_ATTEMPTS - 1:
                break
            retry_after = r.headers.get("Retry-After", "")
            self.sleep(float(retry_after) if retry_after.isdigit() else min(2.0**attempt, MAX_BACKOFF))
        r.raise_for_status()
        return r

    def get_user_id(self) -> str:
        if self._user_id is None:
            self._user_id = self._request("GET", "/user").json()["id"]
        return self._user_id

    def get_projects(self) -> list[Project]:
        if self._projects is None:
            r = self._request("GET", f"/workspaces/{self.workspace}/projects", params={"page-size": 50})
            self._projects = [Project(id=p["id"], name=p["name"]) for p in r.json()]
        return self._projects

    def _fetch_month_entries_raw(self, user_id: str, year: int, month: int) -> list[dict]:
        next_month = date(year + (month // 12), (month % 12) + 1, 1)
        r = self._request(
            "GET",
            f"/workspaces/{self.workspace}/user/{user_id}/time-entries",
            params={
                "start": f"{year}-{month:02d}-01T00:00:00Z",
                "end": f"{next_month.isoformat()}T00:00:00Z",
                "page-size": 200,
            },
        )
        return r.json()

    def _build_project_map(self) -> dict[str, str]:
        return {p.id: p.name for p in self.get_projects()}

    def get_month_entries(self, user_id: str, year: int, month: int) -> list[TimeEntry]:
        project_map = self._build_project_map()
        seen: dict[tuple[str, str], TimeEntry] = {}
        for e in self._fetch_month_entries_raw(user_id, year, month):
            key = (e.get("description", ""), e.get("projectId", ""))
            if key not in seen:
                project_id = e.get("projectId", "")
                seen[key] = TimeEntry(
                    description=e.get("description", ""),
                    project_id=project_id,
                    project_name=project_map.get(project_id, "—"),
                )
        return list(seen.values())

    def get_month_entries_full(self, user_id: str, year: int, month: int) -> list[dict]:
        project_map = self._build_project_map()
        entries = self._fetch_month_entries_raw(user_id, year, month)
        for e in entries:
            e["projectName"] = project_map.get(e.get("projectId", ""), "—")
        return entries

    def log_entry(self, request: LogRequest) -> None:
        d = request.target_date
        start = datetime(d.year, d.month, d.day, 9, 0, 0, tzinfo=timezone.utc)
        end = datetime(d.year, d.month, d.day, 17, 0, 0, tzinfo=timezone.utc)

        self._request(
            "POST",
            f"/workspaces/{self.workspace}/time-entries",
            json={
                "start": start.isoformat(),
                "end": end.isoformat(),
                "description": request.description,
                "projectId": request.project_id,
            },
        )
