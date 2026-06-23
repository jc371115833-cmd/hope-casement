import os
import subprocess
import sys
import tempfile
import winreg
from pathlib import Path
from xml.sax.saxutils import escape

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


def _task_xml(exe: str, trigger: str) -> str:
    """Build a Task Scheduler XML.

    Power conditions are disabled so the change still runs on battery, and the
    trigger repeats indefinitely. Runs in the interactive session (needed to
    affect the visible desktop).
    """
    return (
        '<?xml version="1.0" encoding="UTF-16"?>'
        '<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">'
        "<RegistrationInfo><Description>HopeCasement 换壁纸</Description></RegistrationInfo>"
        f"<Triggers>{trigger}</Triggers>"
        '<Principals><Principal id="Author">'
        "<LogonType>InteractiveToken</LogonType><RunLevel>LeastPrivilege</RunLevel>"
        "</Principal></Principals>"
        "<Settings>"
        "<DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>"
        "<StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>"
        "<MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>"
        "<StartWhenAvailable>true</StartWhenAvailable>"
        "<ExecutionTimeLimit>PT0S</ExecutionTimeLimit>"
        "<Enabled>true</Enabled>"
        "</Settings>"
        '<Actions Context="Author"><Exec>'
        f"<Command>{escape(exe)}</Command><Arguments>--change</Arguments>"
        "</Exec></Actions>"
        "</Task>"
    )


def _register_task(name: str, xml: str) -> None:
    fd, path = tempfile.mkstemp(suffix=".xml")
    try:
        with os.fdopen(fd, "w", encoding="utf-16") as f:
            f.write(xml)
        _schtasks("/create", "/f", "/tn", name, "/xml", path)
    finally:
        os.unlink(path)


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
    errors: list[str] = []

    # startup: registry Run key
    if "startup" in cfg.schedule_modes:
        _set_startup_registry(exe)
    else:
        _delete_startup_registry()

    # interval: repeat every N minutes, indefinitely
    if "interval" in cfg.schedule_modes:
        total_minutes = cfg.interval_hours * 60 + cfg.interval_minutes
        if total_minutes < 1:
            total_minutes = 60
        trigger = (
            "<TimeTrigger>"
            "<StartBoundary>2020-01-01T00:00:00</StartBoundary><Enabled>true</Enabled>"
            f"<Repetition><Interval>PT{total_minutes}M</Interval>"
            "<StopAtDurationEnd>false</StopAtDurationEnd></Repetition>"
            "</TimeTrigger>"
        )
        try:
            _register_task(_TASK_INTERVAL, _task_xml(exe, trigger))
        except RuntimeError as e:
            errors.append(str(e))
    else:
        _delete_task(_TASK_INTERVAL)

    # daily: once a day at the chosen time
    if "daily" in cfg.schedule_modes:
        trigger = (
            "<CalendarTrigger>"
            f"<StartBoundary>2020-01-01T{cfg.daily_time}:00</StartBoundary><Enabled>true</Enabled>"
            "<ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>"
            "</CalendarTrigger>"
        )
        try:
            _register_task(_TASK_DAILY, _task_xml(exe, trigger))
        except RuntimeError as e:
            errors.append(str(e))
    else:
        _delete_task(_TASK_DAILY)

    if errors:
        raise RuntimeError("\n".join(errors))
