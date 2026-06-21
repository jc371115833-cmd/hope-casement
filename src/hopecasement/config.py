import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class Config:
    font_size: int = 48
    font_color: str = "#FFFFFF"
    shadow_color: str = "#000000"
    shadow_offset: int = 2
    text_position: str = "bottom_center"
    text_padding: int = 80
    line_spacing: float = 1.4
    text_width_ratio: float = 0.75
    background_colors: list = field(default_factory=lambda: [
        "#2C3E50", "#251E3F", "#2D3033", "#1A3A2A", "#3B2012",
    ])
    schedule_modes: list = field(default_factory=list)  # empty = manual; values: "startup","interval","daily"
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


def load_config() -> Config:
    path = _config_path()
    if not path.exists():
        return Config()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return Config()
    # Migrate legacy schedule_mode field
    if "schedule_mode" in data and "schedule_modes" not in data:
        old_mode = data.pop("schedule_mode")
        data["schedule_modes"] = [] if old_mode == "manual" else [old_mode]
    else:
        data.pop("schedule_mode", None)
    defaults = asdict(Config())
    defaults.update({k: v for k, v in data.items() if k in defaults})
    return Config(**defaults)


def save_config(cfg: Config) -> None:
    _config_path().write_text(
        json.dumps(asdict(cfg), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
