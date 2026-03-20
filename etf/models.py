from datetime import date

from pydantic import BaseModel


class ETFInfo(BaseModel):
    ticker: str
    name: str
    currency: str
    current_price: float
    change_pct: float
    high_52w: float
    low_52w: float


class ETFHistory(BaseModel):
    ticker: str
    currency: str
    dates: list[date]
    closes: list[float]
