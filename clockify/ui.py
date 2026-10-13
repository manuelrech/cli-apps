from calendar import month_name, monthrange
from datetime import date, datetime

from rich.prompt import Prompt

from clockify.models import Project, TimeEntry
from shared.ui import ColumnDef, console, make_table


class UI:
    def show_target_date(self, target_date: date) -> None:
        console.print(
            f"\n[bold]Logging for[/bold] "
            f"[cyan]{target_date:%A, %d %B %Y}[/cyan]"
        )

    def show_entries(self, entries: list[TimeEntry]) -> list[TimeEntry]:
        table = make_table("This month's entries", [
            ColumnDef(header="#", style="cyan", width=4),
            ColumnDef(header="Description"),
            ColumnDef(header="Project", style="dim"),
        ])
        for i, e in enumerate(entries, 1):
            table.add_row(str(i), e.description, e.project_name)
        console.print(table)
        return entries

    def show_projects(self, projects: list[Project]) -> list[Project]:
        table = make_table("Available projects", [
            ColumnDef(header="#", style="cyan", width=4),
            ColumnDef(header="Name"),
        ])
        for i, p in enumerate(projects, 1):
            table.add_row(str(i), p.name)
        console.print(table)
        return projects

    def prompt_entry(self, entries: list[TimeEntry]) -> tuple[str, str | None]:
        """Returns (description, project_id | None).
        project_id is None when reusing an existing entry."""
        choice = Prompt.ask(
            "\nPick [cyan]#[/cyan] to reuse an entry, or press [cyan]Enter[/cyan] to type new"
        ).strip()

        if choice.isdigit():
            entry = entries[int(choice) - 1]
            console.print(f"[green]Reusing:[/green] {entry.description} → {entry.project_name}")
            return entry.description, entry.project_id

        description = Prompt.ask("Description").strip()
        return description, None

    def prompt_project(self, projects: list[Project]) -> Project:
        choice = Prompt.ask("Pick project [cyan]#[/cyan]").strip()
        return projects[int(choice) - 1]

    def success(self, target_date: object, description: str) -> None:
        console.print(f"\n[bold green]✓ Logged[/bold green] 09:00–17:00 on [cyan]{target_date}[/cyan] → {description}")

    def show_report(self, entries: list[dict], year: int, month: int) -> None:
        table = make_table(
            f"[bold]{month_name[month]} {year}[/bold]",
            [
                ColumnDef(header="Date", style="cyan"),
                ColumnDef(header="Description"),
                ColumnDef(header="Project", style="dim"),
                ColumnDef(header="Hours", style="green", justify="right", footer_style="bold green"),
            ],
            show_footer=True,
        )

        by_day: dict[int, list[tuple[datetime, dict]]] = {}
        for e in entries:
            interval = e["timeInterval"]
            start = datetime.fromisoformat(interval["start"].replace("Z", "+00:00"))
            by_day.setdefault(start.day, []).append((start, e))

        total = 0.0
        for day in range(1, monthrange(year, month)[1] + 1):
            d = date(year, month, day)
            if day not in by_day:
                table.add_row(f"[dim]{d:%a %d}[/dim]", "[dim]—[/dim]", "", "")
                continue
            for start, e in sorted(by_day[day], key=lambda x: x[0]):
                interval = e["timeInterval"]
                end = datetime.fromisoformat(interval["end"].replace("Z", "+00:00")) if interval.get("end") else None
                hours = round((end - start).total_seconds() / 3600, 1) if end else 0
                total += hours
                table.add_row(
                    start.strftime("%a %d"),
                    e.get("description", "—"),
                    e.get("projectName", "—"),
                    f"{hours}h",
                )

        table.columns[3].footer = f"{round(total, 1)}h"
        console.print(table)
        console.print(f"\n[bold]Total: {round(total, 1)}h[/bold] across {len(entries)} entries")
