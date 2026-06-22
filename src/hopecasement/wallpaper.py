import ctypes
import os
from pathlib import Path


def set_wallpaper(image_path: Path | str) -> None:
    abs_path = os.path.abspath(image_path)
    if not ctypes.windll.user32.SystemParametersInfoW(20, 0, abs_path, 3):
        raise OSError(f"设置壁纸失败，路径：{abs_path}")
