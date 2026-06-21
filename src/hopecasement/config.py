import json
import os
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
    schedule_mode: str = "manual"
    interval_hours: int = 3
    daily_time: str = "08:00"


def get_appdata_dir() -> Path:
    base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    d = base / "HopeCasement"
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
    defaults = asdict(Config())
    defaults.update({k: v for k, v in data.items() if k in defaults})
    return Config(**defaults)


def save_config(cfg: Config) -> None:
    _config_path().write_text(
        json.dumps(asdict(cfg), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
