import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

import customtkinter as ctk

from hopecasement.config import Config, load_config
from hopecasement.ui.app import App
from hopecasement.ui.tab_schedule import ScheduleTab


class ScheduleFormTests(unittest.TestCase):
    def test_disabled_styles_survive_reopening_and_reset(self):
        window = ctk.CTk()
        window.withdraw()
        self.addCleanup(window.destroy)
        tab = ScheduleTab(window)
        cfg = Config(show_text=False, text_x=17, text_y=62, text_width_ratio=0.29,
                     font_color="#FEDCBA", font_file="custom.ttf")
        tab.load_config(cfg)
        self.assertEqual(replace(cfg, **tab.get_config_values()), cfg)
        tab._reset_defaults()
        self.assertEqual(replace(cfg, **tab.get_config_values()), Config())
        self.assertEqual(tab._font_box.cget("state"), "readonly")
        tab._interval_hours_entry.delete(0, "end")
        self.assertEqual(tab.get_config_values()["interval_minutes"], 1)
        tab._daily_entry.delete(0, "end")
        tab._daily_entry.insert(0, "9:30")
        self.assertEqual(tab.get_config_values()["daily_time"], "09:30")


class SaveTests(unittest.TestCase):
    def setUp(self):
        directory = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(patch("hopecasement.config.get_appdata_dir", return_value=directory))
        self.enterContext(patch.object(sys, "frozen", True, create=True))
        self.schedule = self.enterContext(patch("hopecasement.scheduler.apply_schedule"))
        self.dialogs = self.enterContext(patch("hopecasement.ui.app.mb"))
        self.dialogs.askyesnocancel.return_value = True
        self.edited = Config(daily_time="19:45", schedule_modes=["daily"])

        # Exercise the real callbacks without creating a Tk window.
        self.app = object.__new__(App)
        self.app._cfg = Config()
        self.app._schedule_pending = False
        self.app._collect_config = Mock(return_value=self.edited)
        self.app._tab_quotes = Mock()
        self.app._tab_schedule = Mock()
        self.app._tab_quotes.has_changes.return_value = False
        self.app._flash_status = Mock()
        self.app.destroy = Mock()

    def test_save_applies_new_plan(self):
        self.assertTrue(self.app._save())
        self.app._tab_quotes.save.assert_called_once()
        self.assertEqual(load_config(), self.edited)
        self.schedule.assert_called_once_with(self.edited)

    def test_invalid_active_time_leaves_existing_settings_and_task_untouched(self):
        self.edited.daily_time = "25:10"
        self.app._on_close()
        self.dialogs.showerror.assert_called_once()
        self.app._tab_quotes.save.assert_not_called()
        self.app.destroy.assert_not_called()
        self.schedule.assert_not_called()
        self.assertEqual(load_config(), Config())

    def test_confirm_save_on_close_applies_new_plan(self):
        self.app._on_close()
        self.assertEqual(load_config(), self.edited)
        self.schedule.assert_called_once_with(self.edited)
        self.app.destroy.assert_called_once()

    def test_cancel_or_discard_never_registers_a_plan(self):
        self.dialogs.askyesnocancel.return_value = None
        self.app._on_close()
        self.app.destroy.assert_not_called()

        self.dialogs.askyesnocancel.return_value = False
        self.app._on_close()
        self.app.destroy.assert_called_once()
        self.app._tab_quotes.save.assert_not_called()
        self.assertEqual(load_config(), Config())
        self.schedule.assert_not_called()

    def test_registration_failure_preserves_disk_edits_and_allows_retry(self):
        self.schedule.side_effect = [OSError("registration failed"), None]
        self.app._on_close()
        self.assertEqual(load_config(), self.edited)
        self.dialogs.showwarning.assert_called_once()
        self.app.destroy.assert_not_called()
        self.app._flash_status.assert_not_called()
        self.assertTrue(self.app._save())
        self.assertEqual(self.schedule.call_count, 2)

    def test_close_after_failed_schedule_offers_retry_or_explicit_exit(self):
        self.schedule.side_effect = [RuntimeError("denied"), None]
        self.assertFalse(self.app._save())
        self.assertFalse(self.app._has_unsaved_changes())
        self.dialogs.askyesnocancel.return_value = None
        self.app._on_close()
        self.app.destroy.assert_not_called()
        self.dialogs.askyesnocancel.return_value = True
        self.app._on_close()
        self.assertEqual(self.schedule.call_count, 2)
        self.app.destroy.assert_called_once()

    def test_write_failure_leaves_window_open_without_registering(self):
        with patch("hopecasement.ui.app.save_config", side_effect=OSError("disk full")):
            self.app._on_close()
        self.dialogs.showerror.assert_called_once()
        self.assertEqual(self.app._cfg, Config())
        self.schedule.assert_not_called()
        self.app.destroy.assert_not_called()

    def test_source_mode_can_save_and_exit_after_schedule_warning(self):
        with patch.object(sys, "frozen", False):
            self.schedule.side_effect = RuntimeError("requires the packaged executable")
            self.app._on_close()
        self.dialogs.showwarning.assert_called_once()
        self.assertEqual(load_config(), self.edited)
        self.app.destroy.assert_called_once()
