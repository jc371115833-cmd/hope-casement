from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from PIL import Image

from hopecasement import changer, renderer
from hopecasement.config import Config


class HistoryTests(TestCase):
    def setUp(self):
        self.data = Path(self.enterContext(TemporaryDirectory()))
        self.history = self.data / "history"
        self.enterContext(patch.object(changer, "get_history_dir", return_value=self.history))
        clock = self.enterContext(patch.object(changer, "datetime"))
        clock.now.return_value = datetime(2026, 1, 1, 12)

    def test_overlapping_changes_archive_each_generated_image(self):
        self.enterContext(patch.object(renderer, "_screen_size", return_value=(40, 30)))
        self.enterContext(patch.object(renderer, "get_appdata_dir", return_value=self.data))
        self.enterContext(patch.object(changer, "get_background", side_effect=lambda colors, _: colors[0]))
        self.enterContext(patch.object(changer, "get_random_quote", side_effect=AssertionError("text hidden")))
        desktop = self.enterContext(patch.object(changer, "set_wallpaper"))
        configs = [Config(background_colors=[color], show_text=False, save_history=True)
                   for color in ["#FF0000", "#00FF00", "#0000FF"]]
        with ThreadPoolExecutor(max_workers=3) as executor:
            list(executor.map(changer.change_wallpaper, configs))
        self.assertEqual(desktop.call_count, 3)
        colors = []
        for path in self.history.glob("*.png"):
            with Image.open(path) as image:
                colors.append(image.getpixel((0, 0)))
        self.assertCountEqual(colors, [(255, 0, 0), (0, 255, 0), (0, 0, 255)])

    def test_limit_counts_legacy_and_new_files_but_preserves_personal_png(self):
        self.history.mkdir()
        personal = self.history / "000-personal.png"
        legacy = self.history / "20251231_010203.png"
        wall = self.data / "current_wallpaper.png"
        personal.write_bytes(b"personal")
        legacy.write_bytes(b"old archive")
        with patch.object(changer, "_HISTORY_KEEP", 2):
            for content in (b"first", b"second", b"third", b"fourth"):
                wall.write_bytes(content)
                changer._save_to_history(wall)
        self.assertEqual(personal.read_bytes(), b"personal")
        self.assertFalse(legacy.exists())
        self.assertCountEqual([p.read_bytes() for p in self.history.glob("2026*.png")],
                              [b"third", b"fourth"])

    def test_new_save_survives_a_clock_change(self):
        self.history.mkdir()
        (self.history / "20260101_125959.png").write_bytes(b"previous hour")
        wall = self.data / "current_wallpaper.png"
        wall.write_bytes(b"new save")
        with patch.object(changer, "_HISTORY_KEEP", 1):
            changer._save_to_history(wall)
        self.assertEqual([p.read_bytes() for p in self.history.iterdir()], [b"new save"])
