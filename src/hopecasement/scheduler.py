import subprocess
import sys
from pathlib import Path

from hopecasement.config import Config

_TASK_STARTUP = r"\HopeCasement\ChangeOnStartup"
_TASK_INTERVAL = r"\HopeCasement\ChangeOnInterval"
_TASK_DAILY = r"\HopeCasement\ChangeAtTime"
_ALL_TASKS = [_TASK_STARTUP, _TASK_INTERVAL, _TASK_DAILY]


def _exe_path() -> str:
    if not getattr(sys, "frozen", False):
        raise RuntimeError("调度功能仅在打包后的 exe 中可用，开发模式下请手动运行。")
    return str(Path(sys.executable).resolve())


def _schtasks(*args: str) -> None:
    subprocess.run(
        ["schtasks", *args],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def _delete_task(name: str) -> None:
    _schtasks("/delete", "/tn", name, "/f")


def clear_all_tasks() -> None:
    for task in _ALL_TASKS:
        _delete_task(task)


def apply_schedule(cfg: Config) -> None:
    exe = _exe_path()
    action = f'"{exe}" --change'
    clear_all_tasks()

    if cfg.schedule_mode == "startup":
        _schtasks(
            "/create", "/f",
            "/tn", _TASK_STARTUP,
            "/tr", action,
            "/sc", "ONLOGON",
            "/delay", "0000:30",
        )
    elif cfg.schedule_mode == "interval":
        _schtasks(
            "/create", "/f",
            "/tn", _TASK_INTERVAL,
            "/tr", action,
            "/sc", "HOURLY",
            "/mo", str(cfg.interval_hours),
        )
    elif cfg.schedule_mode == "daily":
        _schtasks(
            "/create", "/f",
            "/tn", _TASK_DAILY,
            "/tr", action,
            "/sc", "DAILY",
            "/st", cfg.daily_time,
        )
    # manual: tasks already cleared, nothing to register
