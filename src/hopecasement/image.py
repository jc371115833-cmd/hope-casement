from ast import Dict, List
import logging
import os
import random
import sys
from pathlib import Path

SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".gif")

def _get_images_dir() -> Path:
    """获取图片存放目录。
        开发模式：src\assets\images
        exe模式：exe同目录的assets\images
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "assets" / "images"
    return Path(__file__).resolve().parent.parent / "assets" / "images"

def _get_images(images_dir:Path) -> List:
    """根据文件夹路径获取图片路径列表"""
    images =  [
        f for f in os.listdir(images_dir)
        if f.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS)
    ]
    return images


def get_an_image() -> str:
    """从 images 目录随机选取一张图片，返回完整路径"""
    images_dir = _get_images_dir()
    images = _get_images(images_dir)

    chosen_image_path = os.path.join(images_dir, random.choice(images))
    return chosen_image_path
