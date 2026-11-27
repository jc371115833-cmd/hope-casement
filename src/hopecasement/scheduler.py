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
_TASK_NS = "http://schemas.microsoft.com/windows/2004/02/mit/task"

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_RUN_VALUE = "HopeCasement"


def _exe_path() -> str:
    if not getattr(sys, "frozen", False):
        raise RuntimeError("调度功能仅在打包后的 exe 中可用，开发模式下请手动运行。")
    return str(Path(sys.executable).resolve())


def _schtasks(*args: str, missing_ok: bool = False) -> None:
    result = subprocess.run(
        ["schtasks", *args, "/HRESULT"],
        capture_output=True,
        text=True,
        errors="replace",
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    # Missing task or missing task folder are both valid when disabling a trigger.
    code = result.returncode & 0xFFFFFFFF
    if code and not (missing_ok and code in (0x80070002, 0x80070003)):
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"schtasks (0x{code:08X}): {detail}")


def _task_xml(exe: str, trigger_xml: str) -> str:
    """Build a Task Scheduler XML that runs even on battery and never expires."""
    return (
        '<?xml version="1.0" encoding="UTF-16"?>\n'
        f'<Task version="1.2" xmlns="{_TASK_NS}">\n'
        "  <RegistrationInfo><Author>HopeCasement</Author></RegistrationInfo>\n"
        f"  <Triggers>\n{trigger_xml}\n  </Triggers>\n"
        "  <Principals><Principal id=\"Author\">"
        "<LogonType>InteractiveToken</LogonType>"
        "<RunLevel>LeastPrivilege</RunLevel></Principal></Principals>\n"
        "  <Settings>\n"
        "    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>\n"
        "    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>\n"
        "    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>\n"
        "    <StartWhenAvailable>true</StartWhenAvailable>\n"
        "    <ExecutionTimeLimit>PT10M</ExecutionTimeLimit>\n"
        "    <Enabled>true</Enabled>\n"
        "  </Settings>\n"
        "  <Actions Context=\"Author\">\n"
        f"    <Exec><Command>{escape(exe)}</Command><Arguments>--change</Arguments></Exec>\n"
        "  </Actions>\n"
        "</Task>\n"
    )


def _interval_trigger(total_minutes: int) -> str:
    return (
        "    <TimeTrigger>\n"
        "      <StartBoundary>2020-01-01T00:00:00</StartBoundary>\n"
        "      <Enabled>true</Enabled>\n"
        f"      <Repetition><Interval>PT{total_minutes}M</Interval>"
        "<StopAtDurationEnd>false</StopAtDurationEnd></Repetition>\n"
        "    </TimeTrigger>"
    )


def _daily_trigger(hhmm: str) -> str:
    return (
        "    <CalendarTrigger>\n"
        f"      <StartBoundary>2020-01-01T{hhmm}:00</StartBoundary>\n"
        "      <Enabled>true</Enabled>\n"
        "      <ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>\n"
        "    </CalendarTrigger>"
    )


def _create_task_xml(name: str, xml: str) -> None:
    """schtasks /create /xml needs a UTF-16 file on disk."""
    with tempfile.NamedTemporaryFile(
        "w", suffix=".xml", delete=False, encoding="utf-16"
    ) as f:
        f.write(xml)
        path = f.name
    try:
        _schtasks("/create", "/f", "/tn", name, "/xml", path)
    finally:
        os.unlink(path)


def _set_startup_registry(exe: str) -> None:
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, _RUN_VALUE, 0, winreg.REG_SZ, f'"{exe}" --change')


def _delete_startup_registry() -> None:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.DeleteValue(key, _RUN_VALUE)
    except FileNotFoundError:
        pass


def apply_schedule(cfg: Config) -> None:
    exe = _exe_path()
    errors: list[str] = []

    try:
        if "startup" in cfg.schedule_modes:
            _set_startup_registry(exe)
        else:
            _delete_startup_registry()
    except OSError as e:
        errors.append(f"HKCU\\{_RUN_KEY}\\{_RUN_VALUE}: {e}")

    total_minutes = max(1, cfg.interval_hours * 60 + cfg.interval_minutes)
    for mode, name, trigger in (
        ("interval", _TASK_INTERVAL, _interval_trigger(total_minutes)),
        ("daily", _TASK_DAILY, _daily_trigger(cfg.daily_time)),
    ):
        try:
            if mode in cfg.schedule_modes:
                _create_task_xml(name, _task_xml(exe, trigger))
            else:
                _schtasks("/delete", "/tn", name, "/f", missing_ok=True)
        except (OSError, RuntimeError) as e:
            errors.append(f"{name}: {e}")

    if errors:
        raise RuntimeError("\n".join(errors))
