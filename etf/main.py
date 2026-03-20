from typing import Optional

import typer

from etf.client import ETFClient
from etf.config import load_aliases, load_tickers
from etf.ui import show_info, show_period_stats, show_sparkline, show_tickers
from shared.ui import error

app = typer.Typer()
client = ETFClient()

_VALID_PERIODS = {"7d", "1m", "1y"}


@app.command()
def get(
    ticker: str = typer.Argument(..., help="ETF ticker symbol, e.g. acwi, spy"),
    period: Optional[str] = typer.Argument(None, help="Optional period: 7d, 1m or 1y"),
) -> None:
    ticker = ticker.upper()
    ticker = load_aliases().get(ticker, ticker)

    try:
        info = client.get_info(ticker)
    except Exception as e:
        error(str(e))
        raise typer.Exit(1)

    show_info(info)

    if period is not None:
        if period not in _VALID_PERIODS:
            error(f"Invalid period '{period}'. Use one of: {', '.join(sorted(_VALID_PERIODS))}")
            raise typer.Exit(1)

        try:
            history = client.get_history(ticker, period)
        except Exception as e:
            error(str(e))
            raise typer.Exit(1)

        show_period_stats(history, period)
        show_sparkline(history)


@app.command()
def show() -> None:
    """Show available tickers and aliases."""
    tickers = load_tickers()
    aliases = load_aliases()
    show_tickers(tickers, aliases)


if __name__ == "__main__":
    app()
