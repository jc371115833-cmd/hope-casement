import ctypes
import os

from hopecasement.image import get_an_image

def set_wallpaper(image_path: str) -> bool:
    """将指定图片设为 Windows 桌面壁纸"""
    abs_path = os.path.abspath(image_path)
    result = ctypes.windll.user32.SystemParametersInfoW(20, 0, abs_path, 3)
    return result

def main() -> None:
    
    image_path = get_an_image()
    set_wallpaper(image_path)

