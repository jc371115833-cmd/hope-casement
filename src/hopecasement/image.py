import random
import sys
from pathlib import Path

SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".gif")


def _get_images_dir() -> Path:
    """获取图片存放目录。
    开发模式：src/assets/images
    exe 模式：exe 同目录的 assets/images
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "assets" / "images"
    return Path(__file__).resolve().parent.parent / "assets" / "images"


def _get_images(images_dir: Path) -> list[Path]:
    return [f for f in images_dir.iterdir() if f.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS]


def get_an_image() -> str:
    images_dir = _get_images_dir()
    images = _get_images(images_dir)
    return str(random.choice(images))
