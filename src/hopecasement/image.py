import random
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from hopecasement.config import get_appdata_dir

SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".gif")


def get_user_images_dir(images_dir: str = "") -> Path:
    if images_dir:
        return Path(images_dir)
    return get_appdata_dir() / "backgrounds"


def scan_user_images(images_dir: str = "") -> list[Path]:
    d = get_user_images_dir(images_dir)
    try:
        return [f for f in d.iterdir() if f.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS and f.is_file()]
    except (FileNotFoundError, NotADirectoryError, PermissionError):
        return []


def import_image(source: Path, directory: Path) -> None:
    """Copy a new image without replacing a user's existing file."""
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / source.name
    if target.exists() and target.samefile(source):
        return
    number = 1
    # Stage on the same volume so a concurrent wallpaper change sees only complete images.
    with TemporaryDirectory(dir=directory) as staging:
        staged = Path(staging) / source.name
        shutil.copy2(source, staged)
        while True:
            try:
                staged.rename(target)  # On Windows, rename refuses to replace an existing path.
                return
            except FileExistsError:
                target = directory / f"{source.stem} ({number}){source.suffix}"
                number += 1


def get_background(bg_colors: list[str], images_dir: str = "") -> Path | str:
    """Return a random background: a hex color string or a user image Path."""
    pool: list = list(bg_colors) + scan_user_images(images_dir)
    if not pool:
        raise FileNotFoundError("未配置背景。请在【背景】页面添加颜色或图片。")
    return random.choice(pool)
