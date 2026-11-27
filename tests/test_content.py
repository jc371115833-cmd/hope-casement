import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from hopecasement import image, quotes
from hopecasement.storage import atomic_output
from hopecasement.ui import tab_quotes


class ContentTests(unittest.TestCase):
    def setUp(self):
        self.data = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(patch.object(quotes, "get_appdata_dir", return_value=self.data))

    def test_interrupted_replace_preserves_old_content_and_cleans_up(self):
        path = self.data / "config.json"
        path.write_bytes(b"original")
        with self.assertRaises(OSError), atomic_output(path) as temporary:
            temporary.write_bytes(b"partial")
            raise OSError("disk full")
        self.assertEqual(path.read_bytes(), b"original")
        self.assertEqual(list(self.data.iterdir()), [path])

    def test_quote_library_reads_utf8_bom_and_does_not_reseed_existing_file(self):
        path = quotes.quotes_path()
        path.write_text("* first\nsecond", encoding="utf-8-sig")
        self.assertEqual(quotes.load_quotes(), ["first", "second"])
        with self.assertRaises(FileExistsError):
            quotes.save_quotes(["new default"], overwrite=False)
        self.assertEqual(quotes.load_quotes(), ["first", "second"])

    def test_import_deduplicates_and_reports_decoding_errors_before_editing(self):
        path = self.data / "new.md"
        tab = Mock()
        tab._get_quotes.return_value = ["already"]
        self.enterContext(patch.object(tab_quotes.fd, "askopenfilename", return_value=str(path)))
        dialogs = self.enterContext(patch.object(tab_quotes, "mb"))
        path.write_text("# Heading\n* already\n* first\n* first\nsecond", encoding="utf-8-sig")
        tab_quotes.QuotesTab._import(tab)
        tab._replace_all_undoable.assert_called_once_with(["already", "first", "second"])
        path.write_bytes(b"\xff")
        tab_quotes.QuotesTab._import(tab)
        self.assertEqual(tab._replace_all_undoable.call_count, 1)
        dialogs.showerror.assert_called_once()

    def test_external_edits_survive_save_before_refresh_and_conflicting_edits(self):
        quotes.save_quotes(["external"])
        tab = Mock()
        tab._baseline = ["original"]
        tab._get_quotes.return_value = ["original"]
        tab_quotes.QuotesTab.save(tab)
        tab.poll_reload.assert_called_once()
        self.assertEqual(quotes.load_quotes(), ["external"])
        tab._get_quotes.return_value = ["local"]
        with self.assertRaises(OSError):
            tab_quotes.QuotesTab.save(tab)
        self.assertEqual(quotes.load_quotes(), ["external"])
        self.assertEqual(tab._get_quotes(), ["local"])

    def test_scanner_ignores_directories_and_a_missing_or_replaced_folder(self):
        (self.data / "trip.png").mkdir()
        (self.data / "wall.JPG").touch()
        self.assertEqual(image.scan_user_images(str(self.data)), [self.data / "wall.JPG"])
        for folder in ("missing", "wall.JPG"):
            self.assertEqual(image.scan_user_images(str(self.data / folder)), [])

    def test_importing_a_same_name_or_same_file_keeps_existing_photos(self):
        folder = self.data / "backgrounds"
        folder.mkdir()
        original = folder / "wall.jpg"
        original.write_bytes(b"first photo")
        (folder / "wall (1).jpg").write_bytes(b"second photo")
        new = self.data / "wall.jpg"
        new.write_bytes(b"third photo")
        image.import_image(original, folder)
        image.import_image(new, folder)
        self.assertEqual(original.read_bytes(), b"first photo")
        self.assertEqual((folder / "wall (1).jpg").read_bytes(), b"second photo")
        self.assertEqual((folder / "wall (2).jpg").read_bytes(), b"third photo")
        self.assertEqual(len(list(folder.iterdir())), 3)
