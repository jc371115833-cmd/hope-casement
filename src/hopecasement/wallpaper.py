import ctypes
import os
from contextlib import contextmanager
from ctypes import wintypes
from pathlib import Path


@contextmanager
def wallpaper_change_lock():
    """Serialize publication, desktop update and archiving in this Windows session."""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateMutexW.restype = wintypes.HANDLE
    handle = wintypes.HANDLE(kernel.CreateMutexW(None, False, r"Local\HopeCasement_WallpaperChange"))
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        # An abandoned mutex also grants ownership when an earlier process crashed.
        result = kernel.WaitForSingleObject(handle, wintypes.DWORD(0xFFFFFFFF))
        if result not in (0, 0x80):  # WAIT_OBJECT_0, WAIT_ABANDONED
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            yield
        finally:
            kernel.ReleaseMutex(handle)
    finally:
        kernel.CloseHandle(handle)


def set_wallpaper(image_path: Path | str) -> None:
    abs_path = os.path.abspath(image_path)
    if not ctypes.windll.user32.SystemParametersInfoW(20, 0, abs_path, 3):
        raise OSError(f"设置壁纸失败，路径：{abs_path}")
