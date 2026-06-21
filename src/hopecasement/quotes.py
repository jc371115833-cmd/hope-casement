import random
from pathlib import Path

from hopecasement.config import get_appdata_dir

_DEFAULT_QUOTES = [
    "不积跬步，无以至千里。",
    "日日新，又日新。",
    "来日方长，以待岁月。",
    "Stay hungry, stay foolish.",
    "种一棵树最好的时间是十年前，其次是现在。",
]

_FALLBACK = "来日方长，以待岁月。"


def _quotes_path() -> Path:
    return get_appdata_dir() / "quotes.txt"


def load_quotes() -> list[str]:
    path = _quotes_path()
    if not path.exists():
        save_quotes(_DEFAULT_QUOTES)
        return list(_DEFAULT_QUOTES)
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines()]
    return [ln for ln in lines if ln]


def save_quotes(quotes: list[str]) -> None:
    _quotes_path().write_text("\n".join(quotes), encoding="utf-8")


def get_random_quote() -> str:
    quotes = load_quotes()
    return random.choice(quotes) if quotes else _FALLBACK
