import random
import re
from pathlib import Path

from hopecasement import i18n
from hopecasement.config import get_appdata_dir

# Seed quotes shipped on first run. All public-domain (ancient Chinese classics /
# traditional English proverbs) to avoid any copyright concerns.
_DEFAULT_QUOTES = {
    "zh": [
        "不积跬步，无以至千里。",
        "千里之行，始于足下。",
        "天行健，君子以自强不息。",
        "学而不思则罔，思而不学则殆。",
        "苟日新，日日新，又日新。",
    ],
    "en": [
        "A journey of a thousand miles begins with a single step.",
        "Well begun is half done.",
        "Rome was not built in a day.",
        "Little strokes fell great oaks.",
        "Lost time is never found again.",
    ],
}

_BULLET_RE = re.compile(r"^[*\-+]\s+")


def default_quotes() -> list[str]:
    """Seed quotes for the current language (falls back to Chinese)."""
    return list(_DEFAULT_QUOTES.get(i18n.get_language(), _DEFAULT_QUOTES["zh"]))


def quotes_path() -> Path:
    return get_appdata_dir() / "quotes.txt"


def load_quotes() -> list[str]:
    path = quotes_path()
    if not path.exists():
        defaults = default_quotes()
        save_quotes(defaults)
        return defaults
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
    quotes_path().write_text(
        "\n".join(f"* {q}" for q in quotes), encoding="utf-8"
    )


def get_random_quote() -> str:
    quotes = load_quotes()
    return random.choice(quotes) if quotes else default_quotes()[0]
