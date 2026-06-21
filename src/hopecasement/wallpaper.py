import ctypes
import os
from pathlib import Path


def set_wallpaper(image_path: Path | str) -> bool:
    abs_path = os.path.abspath(image_path)
    return bool(ctypes.windll.user32.SystemParametersInfoW(20, 0, abs_path, 3))
