import random
import re
from pathlib import Path

from hopecasement.config import get_appdata_dir

DEFAULT_QUOTES = [
    "不积跬步，无以至千里。",
    "日日新，又日新。",
    "来日方长，以待岁月。",
    "Stay hungry, stay foolish.",
    "种一棵树最好的时间是十年前，其次是现在。",
]

_FALLBACK = "来日方长，以待岁月。"
_BULLET_RE = re.compile(r"^[*\-+]\s+")


def _quotes_path() -> Path:
    return get_appdata_dir() / "quotes.txt"


def load_quotes() -> list[str]:
    path = _quotes_path()
    if not path.exists():
        save_quotes(DEFAULT_QUOTES)
        return list(DEFAULT_QUOTES)
    result = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        ln = _BULLET_RE.sub("", ln, count=1)
        if ln:
            result.append(ln)
    return result


def save_quotes(quotes: list[str]) -> None:
    _quotes_path().write_text(
        "\n".join(f"* {q}" for q in quotes), encoding="utf-8"
    )


def get_random_quote() -> str:
    quotes = load_quotes()
    return random.choice(quotes) if quotes else _FALLBACK
