"""Allow only one UI window at a time via a named Windows mutex."""
import ctypes

_MUTEX_NAME = "HopeCasement_SingleInstance_Mutex"
_ERROR_ALREADY_EXISTS = 183
_SW_RESTORE = 9

_mutex_handle = None  # kept alive for the process lifetime so the mutex persists


def already_running() -> bool:
    """Create the mutex; return True if another instance already holds it."""
    global _mutex_handle
    kernel32 = ctypes.windll.kernel32
    _mutex_handle = kernel32.CreateMutexW(None, False, _MUTEX_NAME)
    return kernel32.GetLastError() == _ERROR_ALREADY_EXISTS


def focus_existing(window_title: str) -> None:
    """Bring the already-running window to the foreground (best effort)."""
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, window_title)
        if hwnd:
            user32.ShowWindow(hwnd, _SW_RESTORE)
            user32.SetForegroundWindow(hwnd)
    except Exception:
        pass
