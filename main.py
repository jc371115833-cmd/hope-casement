import ctypes
import os
import random
import sys


def set_wallpaper(image_path: str) -> bool:
    """将指定图片设为 Windows 桌面壁纸"""
    if not os.path.isfile(image_path):
        print(f"[错误] 文件不存在: {image_path}")
        return False

    abs_path = os.path.abspath(image_path)
    result = ctypes.windll.user32.SystemParametersInfoW(20, 0, abs_path, 3)
    if result:
        print(f"[成功] 壁纸已设置为: {abs_path}")
        return True
    else:
        print("[失败] 设置壁纸失败")
        return False


def main():
    image_dir = os.path.join(os.path.dirname(__file__), "assets", "images")
    if not os.path.isdir(image_dir):
        print(f"[错误] 图片目录不存在: {image_dir}")
        sys.exit(1)

    images = [
        f for f in os.listdir(image_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif"))
    ]
    if not images:
        print(f"[错误] 目录中没有图片: {image_dir}")
        sys.exit(1)

    chosen = random.choice(images)
    wallpaper_path = os.path.join(image_dir, chosen)
    set_wallpaper(wallpaper_path)


if __name__ == "__main__":
    main()
