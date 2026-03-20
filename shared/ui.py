from typing import Literal

from pydantic import BaseModel
from rich.console import Console
from rich.table import Table

console = Console()


class ColumnDef(BaseModel):
    header: str
    style: str = ""
    width: int | None = None
    justify: Literal["left", "center", "right", "full"] = "left"
    footer_style: str = ""


def error(message: str) -> None:
    console.print(f"[bold red]✗ {message}[/bold red]")


def success(message: str) -> None:
    console.print(f"[bold green]✓ {message}[/bold green]")


def make_table(title: str | None, columns: list[ColumnDef], **table_kwargs) -> Table:
    table = Table(title=title, highlight=True, **table_kwargs)
    for col in columns:
        table.add_column(
            col.header,
            style=col.style or None,
            width=col.width,
            justify=col.justify,
            footer_style=col.footer_style or None,
        )
    return table
