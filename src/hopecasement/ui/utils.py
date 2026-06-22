import re


def normalize_hex_color(s: str) -> str:
    """Return normalized #RRGGBB, or '' if invalid."""
    s = s.strip().upper()
    if not s.startswith("#"):
        s = "#" + s
    if re.fullmatch(r"#[0-9A-F]{3}", s):
        s = "#" + s[1] * 2 + s[2] * 2 + s[3] * 2
    if re.fullmatch(r"#[0-9A-F]{6}", s):
        return s
    return ""
