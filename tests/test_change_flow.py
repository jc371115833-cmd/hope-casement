import sys
import tempfile
import threading
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

from PIL import Image

from hopecasement import main
from hopecasement.config import Config, load_config, save_config
from hopecasement.ui.app import App


class ChangeFlowTests(unittest.TestCase):
    def setUp(self):
        self.data = Path(self.enterContext(tempfile.TemporaryDirectory()))
        for module in ("config", "quotes", "image", "renderer"):
            self.enterContext(patch(f"hopecasement.{module}.get_appdata_dir", return_value=self.data))
        self.enterContext(patch("hopecasement.renderer._screen_size", return_value=(320, 180)))
        self.set_desktop = self.enterContext(patch("hopecasement.changer.set_wallpaper"))
        self.enterContext(patch.object(sys, "argv", ["HopeCasement.exe", "--change"]))
        self.cfg = Config(background_colors=["#123456"], show_text=False, save_history=True)
        save_config(self.cfg)
        (self.data / "quotes.txt").write_text("* Example quote", encoding="utf-8")

    def test_scheduled_entry_uses_saved_settings_and_archives_applied_image(self):
        main()
        output = self.data / "current_wallpaper.png"
        self.set_desktop.assert_called_once_with(output)
        with Image.open(output) as image:
            self.assertEqual(image.size, (320, 180))
            self.assertEqual(image.getpixel((0, 0)), (18, 52, 86))
        archives = list((self.data / "history").glob("*.png"))
        self.assertEqual(len(archives), 1)
        self.assertEqual(archives[0].read_bytes(), output.read_bytes())

    def test_scheduled_failure_logs_error_without_archiving(self):
        self.set_desktop.side_effect = OSError("desktop update failed")
        main()
        self.assertIn("desktop update failed", (self.data / "error.log").read_text(encoding="utf-8"))
        self.assertFalse((self.data / "history").exists())

    def test_change_now_uses_window_style_without_overwriting_saved_plan(self):
        app = object.__new__(App)
        app._tab_quotes = Mock()
        app._collect_config = Mock(return_value=replace(
            self.cfg, background_colors=["#FF0000"], save_history=False, daily_time="23:59",
        ))
        app._change_btn = Mock()
        app.after = Mock()
        with patch.object(threading.Thread, "start", threading.Thread.run):
            app._change_now()
        self.assertEqual(app._change_result[0], "ok")
        app._tab_quotes.save.assert_called_once()
        output = self.data / "current_wallpaper.png"
        self.set_desktop.assert_called_once_with(output)
        with Image.open(output) as image:
            self.assertEqual(image.getpixel((0, 0)), (255, 0, 0))
        self.assertEqual(load_config(), self.cfg)
        self.assertFalse((self.data / "history").exists())
