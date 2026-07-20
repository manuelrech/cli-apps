import webbrowser
from datetime import date

import typer
from rich.prompt import Prompt

from clockify.client import ClockifyClient
from clockify.models import LogRequest
from clockify.ui import UI
from clockify.utils import parse_date
from shared.ui import error

app = typer.Typer()
ui = UI()
client = ClockifyClient()


@app.command()
def log(date_arg: str = typer.Option(None, "--date", "-d", help="today by default, -1, +1, or 01/03/25")) -> None:
    try:
        target_date = parse_date(date_arg)
    except ValueError as e:
        error(str(e))
        raise typer.Exit(1)

    ui.show_target_date(target_date)

    user_id = client.get_user_id()
    entries = client.get_month_entries(user_id, target_date.year, target_date.month)

    if entries:
        ui.show_entries(entries)
        description, project_id = ui.prompt_entry(entries)
    else:
        description = Prompt.ask("No entries this month yet. Description").strip()
        project_id = None

    if project_id is None:
        projects = client.get_projects()
        ui.show_projects(projects)
        project = ui.prompt_project(projects)
        project_id = project.id

    client.log_entry(LogRequest(
        target_date=target_date,
        description=description,
        project_id=project_id,
    ))
    ui.success(target_date, description)


@app.command()
def show(
    month: int = typer.Option(None, "--month", "-m", help="Month number (default: current)"),
    year: int = typer.Option(None, "--year", "-y", help="Year (default: current)"),
) -> None:
    today = date.today()
    month = month or today.month
    year = year or today.year

    user_id = client.get_user_id()
    entries = client.get_month_entries_full(user_id, year, month)
    ui.show_report(entries, year, month)


@app.command()
def open() -> None:
    """Open the Clockify app in the browser."""
    webbrowser.open("https://app.clockify.me/calendar")


if __name__ == "__main__":
    app()
