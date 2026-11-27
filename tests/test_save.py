import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from hopecasement.config import Config, load_config
from hopecasement.ui.app import App


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
        self.app._collect_config = Mock(return_value=self.edited)
        self.app._tab_quotes = Mock()
        self.app._tab_quotes.has_changes.return_value = False
        self.app._flash_status = Mock()
        self.app.destroy = Mock()

    def test_save_applies_new_plan(self):
        self.assertTrue(self.app._save())
        self.app._tab_quotes.save.assert_called_once()
        self.assertEqual(load_config(), self.edited)
        self.schedule.assert_called_once_with(self.edited)

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
