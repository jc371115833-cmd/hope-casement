import random
import sys
from pathlib import Path

from hopecasement.config import get_appdata_dir

SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".gif")


def _get_builtin_images_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "assets" / "images"
    return Path(__file__).resolve().parents[2] / "src" / "assets" / "images"


def _get_user_images_dir() -> Path:
    return get_appdata_dir() / "backgrounds"


def _scan(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return [f for f in directory.iterdir() if f.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS]


def get_all_images() -> list[Path]:
    return _scan(_get_builtin_images_dir()) + _scan(_get_user_images_dir())


def get_an_image() -> Path:
    images = get_all_images()
    if not images:
        raise FileNotFoundError("No background images found. Please add images in the app.")
    return random.choice(images)
