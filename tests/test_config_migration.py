import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from hopecasement import config


class ConfigMigrationTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.data_dir = Path(temp.name)
        self.enterContext(patch.object(config, "get_appdata_dir", return_value=self.data_dir))
        self.path = self.data_dir / "config.json"

    def test_legacy_manual_config_survives_save_and_reload(self):
        legacy = {
            "schedule_mode": "manual",
            "text_position": "top_left",
            "font_size": 54,
            "text_padding": 10,
            "images_dir": "背景",
        }
        self.path.write_text(json.dumps(legacy), encoding="utf-8")
        cfg = config.load_config()
        self.assertEqual(cfg.schedule_modes, [])
        self.assertEqual((cfg.text_x, cfg.text_y), (15, 15))
        self.assertEqual(cfg.font_size, 5)
        self.assertEqual(cfg.images_dir, "背景")
        self.assertEqual(cfg.daily_time, config.Config().daily_time)

        config.save_config(cfg)
        saved = json.loads(self.path.read_text(encoding="utf-8"))
        for obsolete in ("schedule_mode", "text_position", "text_padding"):
            self.assertNotIn(obsolete, saved)
        self.assertEqual(config.load_config(), cfg)

    def test_legacy_daily_value_becomes_single_enabled_mode(self):
        self.path.write_text('{"schedule_mode":"daily"}', encoding="utf-8")
        self.assertEqual(config.load_config().schedule_modes, ["daily"])

    def test_modern_settings_take_precedence_when_both_formats_are_present(self):
        settings = {
            "schedule_modes": ["interval", "daily"],
            "schedule_mode": "startup",
            "text_position": "top_left",
            "text_x": 60,
            "text_y": 70,
        }
        self.path.write_text(json.dumps(settings), encoding="utf-8")
        cfg = config.load_config()
        self.assertEqual(cfg.schedule_modes, ["interval", "daily"])
        self.assertEqual((cfg.text_x, cfg.text_y), (60, 70))
