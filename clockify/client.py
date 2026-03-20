from datetime import date, datetime, timezone

import httpx

from clockify.config import BASE_URL, HEADERS, WORKSPACE_ID
from clockify.models import LogRequest, Project, TimeEntry


class ClockifyClient:
    def __init__(self) -> None:
        self.base = BASE_URL
        self.headers = HEADERS
        self.workspace = WORKSPACE_ID

    def get_user_id(self) -> str:
        r = httpx.get(f"{self.base}/user", headers=self.headers)
        r.raise_for_status()
        return r.json()["id"]

    def get_projects(self) -> list[Project]:
        r = httpx.get(
            f"{self.base}/workspaces/{self.workspace}/projects",
            headers=self.headers,
            params={"page-size": 50},
        )
        r.raise_for_status()
        return [Project(id=p["id"], name=p["name"]) for p in r.json()]

    def _fetch_month_entries_raw(self, user_id: str, year: int, month: int) -> list[dict]:
        next_month = date(year + (month // 12), (month % 12) + 1, 1)
        r = httpx.get(
            f"{self.base}/workspaces/{self.workspace}/user/{user_id}/time-entries",
            headers=self.headers,
            params={
                "start": f"{year}-{month:02d}-01T00:00:00Z",
                "end": f"{next_month.isoformat()}T00:00:00Z",
                "page-size": 200,
            },
        )
        r.raise_for_status()
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

        r = httpx.post(
            f"{self.base}/workspaces/{self.workspace}/time-entries",
            headers=self.headers,
            json={
                "start": start.isoformat(),
                "end": end.isoformat(),
                "description": request.description,
                "projectId": request.project_id,
            },
        )
        r.raise_for_status()
