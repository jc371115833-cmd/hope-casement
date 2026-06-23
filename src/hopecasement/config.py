import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class Config:
    font_size: float = 4.0  # % of image height
    font_file: str = "msyh.ttc"  # font filename under the Windows Fonts dir
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
    schedule_modes: list[str] = field(default_factory=list)  # empty = manual; values: "startup","interval","daily"
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


_POS_MAP = {
    "top_left": (15, 15), "top_center": (50, 15), "center": (50, 50),
    "bottom_center": (50, 88), "bottom_right": (85, 88),
}


def _migrate(data: dict) -> dict:
    if "font_size" in data and data["font_size"] > 15:
        data["font_size"] = max(1, round(data["font_size"] / 10.8))
    if "text_position" in data and "text_x" not in data:
        data["text_x"], data["text_y"] = _POS_MAP.get(data.pop("text_position"), (50, 88))
    else:
        data.pop("text_position", None)
    data.pop("text_padding", None)
    if "schedule_mode" in data and "schedule_modes" not in data:
        old_mode = data.pop("schedule_mode")
        data["schedule_modes"] = [] if old_mode == "manual" else [old_mode]
    else:
        data.pop("schedule_mode", None)
    return data


def load_config() -> Config:
    path = _config_path()
    if not path.exists():
        return Config()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return Config()
    data = _migrate(data)
    defaults = asdict(Config())
    defaults.update({k: v for k, v in data.items() if k in defaults})
    return Config(**defaults)


def save_config(cfg: Config) -> None:
    _config_path().write_text(
        json.dumps(asdict(cfg), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
