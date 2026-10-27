import functools
import webbrowser
from collections.abc import Callable
from datetime import date, datetime

import httpx
import typer
import yfinance as yf
from rich.prompt import Prompt

from clockify.client import ClockifyClient
from clockify.models import LogRequest
from clockify.ui import UI
from clockify.utils import parse_date, summarize_by_task
from shared.ui import console, error

app = typer.Typer()
ui = UI()
client = ClockifyClient()


def handle_http_errors(fn: Callable[..., None]) -> Callable[..., None]:
    @functools.wraps(fn)
    def wrapper(*args, **kwargs) -> None:
        try:
            fn(*args, **kwargs)
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            error("Clockify rate limit hit, try again in a minute" if status == 429 else f"Clockify API error: {status}")
            raise typer.Exit(1)
        except httpx.RequestError as e:
            error(f"Could not reach Clockify: {e}")
            raise typer.Exit(1)
    return wrapper


@app.command()
@handle_http_errors
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

    full_entries = client.get_month_entries_full(user_id, target_date.year, target_date.month)
    ui.show_report(full_entries, target_date.year, target_date.month)


@app.command()
@handle_http_errors
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
@handle_http_errors
def report(
    month: int = typer.Option(None, "--month", "-m", help="Month number (default: current)"),
    year: int = typer.Option(None, "--year", "-y", help="Year (default: current)"),
) -> None:
    """Show hours worked per task for a month."""
    today = date.today()
    month = month or today.month
    year = year or today.year

    entries = client.get_month_entries_full(client.get_user_id(), year, month)
    ui.show_task_report(summarize_by_task(entries), year, month)


@app.command()
@handle_http_errors
def prospect(
    rate: float = typer.Option(..., "--rate", "-r", envvar="CLOCKIFY_CHF_RATE", help="Hourly rate in CHF"),
    fx: float = typer.Option(None, "--fx", help="CHF→EUR rate (default: live from Yahoo)"),
    net: float = typer.Option(0.8, "--net", help="Share kept after taxes"),
    days: int = typer.Option(0, "--days", "-d", help="Extra future days to add (8h each)"),
) -> None:
    """Estimate this month's earnings in EUR."""
    today = date.today()
    entries = client.get_month_entries_full(client.get_user_id(), today.year, today.month)
    hours = sum(
        (datetime.fromisoformat(e["timeInterval"]["end"]) - datetime.fromisoformat(e["timeInterval"]["start"]))
        .total_seconds()
        for e in entries
        if e["timeInterval"].get("end")
    ) / 3600 + days * 8
    fx = fx or yf.Ticker("CHFEUR=X").fast_info.last_price

    console.print(f"\n[bold]{hours:.1f}h[/bold] × {rate:g} CHF × {fx:.4f} EUR/CHF")
    for label, chf, style in [
        ("Gross:      ", hours * rate, "green"),
        (f"Net (×{net:g}): ", hours * rate * net, "green"),
        ("Net × 11/12:", hours * rate * net * 11 / 12, "bold green"),
    ]:
        console.print(f"{label}  [{style}]€{chf * fx:>10,.2f}[/{style}]   [dim]CHF {chf:>10,.2f}[/dim]")


@app.command()
def open() -> None:
    """Open the Clockify app in the browser."""
    webbrowser.open("https://app.clockify.me/calendar")


if __name__ == "__main__":
    app()
