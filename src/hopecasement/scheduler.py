import subprocess
import sys
import winreg
from pathlib import Path

from hopecasement.config import Config

_TASK_INTERVAL = r"\HopeCasement\ChangeOnInterval"
_TASK_DAILY = r"\HopeCasement\ChangeAtTime"
_ALL_TASKS = [_TASK_INTERVAL, _TASK_DAILY]

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_RUN_VALUE = "HopeCasement"


def _exe_path() -> str:
    if not getattr(sys, "frozen", False):
        raise RuntimeError("调度功能仅在打包后的 exe 中可用，开发模式下请手动运行。")
    return str(Path(sys.executable).resolve())


def _schtasks(*args: str) -> None:
    result = subprocess.run(
        ["schtasks", *args],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    if result.returncode != 0:
        raise RuntimeError(f"schtasks 失败：{result.stderr.strip() or result.stdout.strip()}")


def _delete_task(name: str) -> None:
    subprocess.run(
        ["schtasks", "/delete", "/tn", name, "/f"],
        capture_output=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def _set_startup_registry(exe: str) -> None:
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
    ) as key:
        winreg.SetValueEx(key, _RUN_VALUE, 0, winreg.REG_SZ, f'"{exe}" --change')


def _delete_startup_registry() -> None:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.DeleteValue(key, _RUN_VALUE)
    except OSError:
        pass


def clear_all_tasks() -> None:
    _delete_startup_registry()
    for task in _ALL_TASKS:
        _delete_task(task)


def apply_schedule(cfg: Config) -> None:
    exe = _exe_path()
    action = f'"{exe}" --change'
    errors: list[str] = []

    # startup: registry Run key
    if "startup" in cfg.schedule_modes:
        _set_startup_registry(exe)
    else:
        _delete_startup_registry()

    # interval: schtasks MINUTE
    if "interval" in cfg.schedule_modes:
        total_minutes = cfg.interval_hours * 60 + cfg.interval_minutes
        if total_minutes < 1:
            total_minutes = 60
        try:
            _schtasks(
                "/create", "/f",
                "/tn", _TASK_INTERVAL,
                "/tr", action,
                "/sc", "MINUTE",
                "/mo", str(total_minutes),
            )
        except RuntimeError as e:
            errors.append(str(e))
    else:
        _delete_task(_TASK_INTERVAL)

    # daily: schtasks DAILY
    if "daily" in cfg.schedule_modes:
        try:
            _schtasks(
                "/create", "/f",
                "/tn", _TASK_DAILY,
                "/tr", action,
                "/sc", "DAILY",
                "/st", cfg.daily_time,
            )
        except RuntimeError as e:
            errors.append(str(e))
    else:
        _delete_task(_TASK_DAILY)

    if errors:
        raise RuntimeError("\n".join(errors))
