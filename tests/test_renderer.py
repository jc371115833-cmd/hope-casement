import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PIL import Image, ImageChops

from hopecasement import renderer
from hopecasement.config import Config


class RendererTests(unittest.TestCase):
    def test_solid_background_has_exact_rgb_value_across_canvas(self):
        image = renderer.compose_wallpaper(
            "#123456", "Example", Config(show_text=False), (127, 83)
        )
        self.assertEqual(image.mode, "RGB")
        self.assertEqual(image.size, (127, 83))
        self.assertEqual(image.getextrema(), ((18, 18), (52, 52), (86, 86)))

    def test_wide_background_is_center_cropped(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "wide.png"
            source = Image.new("RGB", (90, 30), "red")
            source.paste("green", (30, 0, 60, 30))
            source.save(path)
            image = renderer.compose_wallpaper(
                path, "Example", Config(show_text=False), (30, 30)
            )
        self.assertEqual(image.size, (30, 30))
        self.assertEqual(image.getextrema(), ((0, 0), (128, 128), (0, 0)))

    def test_text_position_moves_visible_content(self):
        size = (400, 300)
        background = Image.new("RGB", size, "black")
        for position in (25, 75):
            with self.subTest(position=position):
                cfg = Config(text_x=position, text_y=position, text_bg_opacity=0)
                image = renderer.compose_wallpaper("#000000", "ABC", cfg, size)
                bounds = ImageChops.difference(image, background).getbbox()
                self.assertIsNotNone(bounds)
                left, top, right, bottom = bounds
                if position == 25:
                    self.assertLess(right, size[0] // 2)
                    self.assertLess(bottom, size[1] // 2)
                else:
                    self.assertGreater(left, size[0] // 2)
                    self.assertGreater(top, size[1] // 2)

    def test_render_wallpaper_writes_the_current_png_at_screen_size(self):
        with TemporaryDirectory() as directory:
            with (
                patch.object(renderer, "_screen_size", return_value=(123, 92)),
                patch.object(renderer, "get_appdata_dir", return_value=Path(directory)),
            ):
                path = renderer.render_wallpaper("#123456", "Example", Config(show_text=False))
            self.assertEqual(path, Path(directory) / "current_wallpaper.png")
            with Image.open(path) as saved:
                self.assertEqual(saved.format, "PNG")
                self.assertEqual(saved.size, (123, 92))
                self.assertEqual(saved.getpixel((0, 0)), (18, 52, 86))
