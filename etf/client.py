import yfinance as yf

from etf.models import ETFHistory, ETFInfo

_PERIOD_MAP: dict[str, str] = {
    "7d": "7d",
    "1m": "1mo",
    "1y": "1y",
}


class ETFClient:
    def get_info(self, ticker: str) -> ETFInfo:
        t = yf.Ticker(ticker)
        fast = t.fast_info

        try:
            last_price = fast.last_price
            previous_close = fast.previous_close
        except KeyError:
            raise ValueError(f"No data found for ticker '{ticker}'. Is it valid?")

        if last_price is None or previous_close is None:
            raise ValueError(f"No data found for ticker '{ticker}'. Is it valid?")

        change_pct = round((last_price - previous_close) / previous_close * 100, 2)

        try:
            name = t.info.get("longName") or t.info.get("shortName") or ticker.upper()
        except Exception:
            name = ticker.upper()

        return ETFInfo(
            ticker=ticker.upper(),
            name=name,
            currency=fast.currency or "USD",
            current_price=round(last_price, 2),
            change_pct=change_pct,
            high_52w=round(fast.year_high, 2),
            low_52w=round(fast.year_low, 2),
        )

    def get_history(self, ticker: str, period: str) -> ETFHistory:
        yf_period = _PERIOD_MAP.get(period, period)
        t = yf.Ticker(ticker)
        fast = t.fast_info
        hist = t.history(period=yf_period)

        if hist.empty:
            raise ValueError(f"No history found for ticker '{ticker}' with period '{period}'.")

        return ETFHistory(
            ticker=ticker.upper(),
            currency=fast.currency or "USD",
            dates=[ts.date() for ts in hist.index],
            closes=[round(float(c), 2) for c in hist["Close"]],
        )
