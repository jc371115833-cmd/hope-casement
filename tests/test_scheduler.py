import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree

from hopecasement import scheduler
from hopecasement.config import Config


class SchedulerTests(unittest.TestCase):
    def setUp(self):
        self.exe = r"C:\Test & Tools\HopeCasement.exe"
        self.enterContext(patch.object(sys, "frozen", True, create=True))
        self.enterContext(patch.object(sys, "executable", self.exe))
        self.registry = self.enterContext(patch.object(scheduler, "winreg"))
        self.commands = self.enterContext(patch.object(scheduler.subprocess, "run"))
        self.tasks = {}
        self.deleted = []
        self.commands.side_effect = self.record_task_command

    def record_task_command(self, args, **kwargs):
        self.assertEqual(args[0], "schtasks")
        name = args[args.index("/tn") + 1]
        if args[1] == "/create":
            xml_path = Path(args[args.index("/xml") + 1])
            self.tasks[name] = ElementTree.fromstring(xml_path.read_bytes())
        else:
            self.assertEqual(args[1], "/delete")
            self.deleted.append(name)
        return subprocess.CompletedProcess(args, returncode=0, stdout="", stderr="")

    def test_packaged_schedule_registers_login_interval_and_daily(self):
        scheduler.apply_schedule(Config(interval_hours=1, interval_minutes=15, daily_time="19:45"))

        self.registry.SetValueEx.assert_called_once_with(
            self.registry.CreateKeyEx.return_value.__enter__.return_value,
            "HopeCasement", 0, self.registry.REG_SZ, f'"{self.exe}" --change',
        )
        self.assertEqual(set(self.tasks), {
            r"\HopeCasement\ChangeOnInterval", r"\HopeCasement\ChangeAtTime",
        })
        for root in self.tasks.values():
            self.assertEqual(root.findtext(".//{*}Command"), self.exe)
            self.assertEqual(root.findtext(".//{*}Arguments"), "--change")
        interval = self.tasks[r"\HopeCasement\ChangeOnInterval"]
        daily = self.tasks[r"\HopeCasement\ChangeAtTime"]
        self.assertEqual(interval.findtext(".//{*}Interval"), "PT75M")
        self.assertEqual(daily.findtext(".//{*}StartBoundary"), "2020-01-01T19:45:00")

    def test_manual_mode_removes_all_three_triggers(self):
        scheduler.apply_schedule(Config(schedule_modes=[]))
        self.assertEqual(self.tasks, {})
        self.assertCountEqual(self.deleted, [
            r"\HopeCasement\ChangeOnInterval", r"\HopeCasement\ChangeAtTime",
        ])
        self.registry.DeleteValue.assert_called_once_with(
            self.registry.OpenKey.return_value.__enter__.return_value, "HopeCasement",
        )

    def test_source_checkout_stops_before_changing_windows(self):
        with patch.object(sys, "frozen", False), self.assertRaises(RuntimeError):
            scheduler.apply_schedule(Config())
        self.commands.assert_not_called()
        self.registry.OpenKey.assert_not_called()
        self.registry.CreateKeyEx.assert_not_called()

    def test_disable_ignores_absent_tasks_and_reports_permission_failures(self):
        self.commands.side_effect = [
            subprocess.CompletedProcess([], 0x80070002, "", ""),
            subprocess.CompletedProcess([], 0x80070005, "", "Access denied"),
        ]
        with self.assertRaisesRegex(RuntimeError, r"ChangeAtTime.*0x80070005"):
            scheduler.apply_schedule(Config(schedule_modes=[]))

    def test_disable_startup_reports_registry_permission_failure(self):
        self.registry.DeleteValue.side_effect = PermissionError("Access denied")
        with self.assertRaisesRegex(RuntimeError, "Access denied"):
            scheduler.apply_schedule(Config(schedule_modes=[]))
        self.assertEqual(len(self.deleted), 2)
