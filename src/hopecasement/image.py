import random
from pathlib import Path

from hopecasement.config import get_appdata_dir

SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".gif")


def get_user_images_dir() -> Path:
    return get_appdata_dir() / "backgrounds"


def scan_user_images() -> list[Path]:
    d = get_user_images_dir()
    if not d.exists():
        return []
    return [f for f in d.iterdir() if f.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS]


def get_background(bg_colors: list[str]) -> "Path | str":
    """Return a random background: a hex color string or a user image Path."""
    pool: list = list(bg_colors) + scan_user_images()
    if not pool:
        raise FileNotFoundError("未配置背景。请在【背景】页面添加颜色或图片。")
    return random.choice(pool)
