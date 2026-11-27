import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

from PIL import ImageColor

from hopecasement.storage import atomic_output


@dataclass
class Config:
    font_size: float = 4.0  # % of image height
    font_file: str = "simkai.ttf"  # font filename under the Windows Fonts dir (楷体)
    font_color: str = "#FFFFFF"
    shadow_color: str = "#000000"
    shadow_offset: int = 3
    text_bg_color: str = "#000000"
    text_bg_opacity: int = 30  # 0–100, 0 = no background behind text
    show_text: bool = True
    text_x: int = 50  # horizontal center of text block, % of image width (0=left, 100=right)
    text_y: int = 88  # vertical center of text block, % of image height (0=top, 100=bottom)
    line_spacing: float = 1.4
    text_width_ratio: float = 0.75
    text_align: str = "center"  # left | center | right
    background_colors: list[str] = field(default_factory=lambda: ["#2D3033"])
    images_dir: str = ""  # custom background folder; empty = appdata/backgrounds
    save_history: bool = False  # keep a timestamped copy of every generated wallpaper
    language: str = ""  # "zh" | "en"; empty = resolve from installer / system at startup
    schedule_modes: list[str] = field(  # empty = manual; values: "startup","interval","daily"
        default_factory=lambda: ["startup", "interval", "daily"])
    interval_hours: int = 3
    interval_minutes: int = 0
    daily_time: str = "08:00"


def get_appdata_dir() -> Path:
    if getattr(sys, "frozen", False):
        d = Path(sys.executable).parent
    else:
        d = Path(__file__).parent.parent.parent / "userdata"
    d.mkdir(parents=True, exist_ok=True)
    (d / "backgrounds").mkdir(exist_ok=True)
    return d


def _config_path() -> Path:
    return get_appdata_dir() / "config.json"


def get_history_dir() -> Path:
    return get_appdata_dir() / "history"


_POS_MAP = {
    "top_left": (15, 15), "top_center": (50, 15), "center": (50, 50),
    "bottom_center": (50, 88), "bottom_right": (85, 88),
}


def _migrate(data: dict) -> None:
    size = data.get("font_size")
    legacy_position = "text_position" in data or "text_padding" in data
    if type(size) in (int, float) and 15 < size <= sys.maxsize:
        if size > 20 or (legacy_position and "text_x" not in data):
            data["font_size"] = max(1, round(size / 10.8))
    if isinstance(data.get("text_position"), str) and "text_x" not in data:
        data["text_x"], data["text_y"] = _POS_MAP.get(data["text_position"], (50, 88))
    if "schedule_mode" in data and "schedule_modes" not in data:
        old_mode = data["schedule_mode"]
        data["schedule_modes"] = [] if old_mode == "manual" else [old_mode]


def _rgb(value: str) -> str | None:
    try:
        r, g, b = ImageColor.getrgb(value)
    except (ValueError, OverflowError):
        return None
    if not all(0 <= channel <= 255 for channel in (r, g, b)):
        return None
    return f"#{r:02X}{g:02X}{b:02X}"


_RANGES = {
    "font_size": (1, 20), "line_spacing": (1, 3), "text_width_ratio": (0.2, 1),
    "text_x": (0, 100), "text_y": (0, 100), "text_bg_opacity": (0, 100),
    "interval_minutes": (0, 59), "interval_hours": (0, float("inf")),
}

_CHOICES = {"text_align": ("left", "center", "right"), "language": ("", "zh", "en")}


def normalize_daily_time(value: str) -> str | None:
    match = re.fullmatch(r"([01]?[0-9]|2[0-3]):([0-5][0-9])", value.strip())
    return f"{int(match[1]):02}:{match[2]}" if match else None


def load_config() -> Config:
    path = _config_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (ValueError, RecursionError, FileNotFoundError):
        return Config()
    if not isinstance(data, dict):
        return Config()
    _migrate(data)
    cfg = Config()
    for key, default in asdict(cfg).items():
        value = data.get(key)
        if isinstance(default, float):
            if type(value) not in (float, int):
                continue
        elif type(value) is not type(default):
            continue
        if key in _RANGES:
            low, high = _RANGES[key]
            if not low <= value <= high:
                continue
        if key in _CHOICES and value not in _CHOICES[key]:
            continue
        if key in ("font_color", "shadow_color", "text_bg_color"):
            value = _rgb(value) or default
        elif key == "background_colors":
            colors = [rgb for item in value if isinstance(item, str) and (rgb := _rgb(item))]
            value = colors if colors or not value else default
        elif key == "schedule_modes":
            value = [mode for mode in value if mode in ("startup", "interval", "daily")]
        elif key == "daily_time":
            value = normalize_daily_time(value) or default
        elif key in ("images_dir", "font_file") and "\0" in value:
            continue
        setattr(cfg, key, value)
    return cfg


def save_config(cfg: Config) -> None:
    with atomic_output(_config_path()) as path:
        path.write_text(json.dumps(asdict(cfg), ensure_ascii=False, indent=2), encoding="utf-8")
