from etf.models import ETFHistory, ETFInfo
from shared.ui import ColumnDef, console, make_table

_CURRENCY_SYMBOLS: dict[str, str] = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "CHF": "Fr",
}


def _fmt(amount: float, currency: str) -> str:
    symbol = _CURRENCY_SYMBOLS.get(currency, currency + " ")
    return f"{symbol}{amount:,.2f}"


def show_info(info: ETFInfo) -> None:
    table = make_table(
        f"[bold]{info.ticker}[/bold] — {info.name}",
        [
            ColumnDef(header="Label", style="dim", width=18),
            ColumnDef(header="Value"),
        ],
        show_header=False,
    )
    change_color = "green" if info.change_pct >= 0 else "red"
    change_sign = "+" if info.change_pct >= 0 else ""

    table.add_row("Price", _fmt(info.current_price, info.currency))
    table.add_row("Daily change", f"[{change_color}]{change_sign}{info.change_pct:.2f}%[/{change_color}]")
    table.add_row("52w High", _fmt(info.high_52w, info.currency))
    table.add_row("52w Low", _fmt(info.low_52w, info.currency))
    console.print(table)


def show_period_stats(history: ETFHistory, period: str) -> None:
    closes = history.closes
    period_change = closes[-1] - closes[0]
    period_change_pct = period_change / closes[0] * 100
    period_high = max(closes)
    period_low = min(closes)
    color = "green" if period_change >= 0 else "red"
    sign = "+" if period_change >= 0 else "-"

    table = make_table(
        None,
        [
            ColumnDef(header="Label", style="dim", width=18),
            ColumnDef(header="Value"),
        ],
        show_header=False,
    )
    table.add_row("Period", period)
    table.add_row(
        "Period change",
        f"[{color}]{sign}{_fmt(abs(period_change), history.currency)}  ({sign}{abs(period_change_pct):.2f}%)[/{color}]",
    )
    table.add_row("Period high", _fmt(period_high, history.currency))
    table.add_row("Period low", _fmt(period_low, history.currency))
    console.print(table)


def show_sparkline(history: ETFHistory) -> None:
    closes = history.closes
    first = _fmt(closes[0], history.currency)
    last = _fmt(closes[-1], history.currency)

    max_blocks = console.width - len(first) - len(last) - 4
    closes = _downsample(closes, max_blocks)

    min_v, max_v = min(closes), max(closes)
    blocks = "▁▂▃▄▅▆▇█"
    if max_v == min_v:
        line = blocks[0] * len(closes)
    else:
        line = "".join(blocks[round((v - min_v) / (max_v - min_v) * 7)] for v in closes)

    console.print(f"  [dim]{first}[/dim] {line} [dim]{last}[/dim]")


def _downsample(values: list[float], max_points: int) -> list[float]:
    if len(values) <= max_points:
        return values
    step = len(values) / max_points
    return [values[round(i * step)] for i in range(max_points)]


def show_tickers(tickers: list[str], aliases: dict[str, str]) -> None:
    table = make_table(
        "Available ETFs",
        [
            ColumnDef(header="Ticker", style="bold cyan"),
            ColumnDef(header="Real Symbol", style="dim"),
        ],
    )
    for ticker in tickers:
        table.add_row(ticker, "")
    for alias, real in aliases.items():
        table.add_row(alias, real)
    console.print(table)
