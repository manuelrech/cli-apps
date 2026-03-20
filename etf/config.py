import json
from pathlib import Path

TICKERS_FILE = Path(__file__).parent / "tickers.json"
ALIASES_FILE = Path(__file__).parent / "aliases.json"


def load_tickers() -> list[str]:
    return json.loads(TICKERS_FILE.read_text())


def load_aliases() -> dict[str, str]:
    return json.loads(ALIASES_FILE.read_text())
