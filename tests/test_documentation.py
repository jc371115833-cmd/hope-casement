import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
FENCED_BLOCK = re.compile(r"^```[^\n]*\n.*?^```[^\n]*$", re.MULTILINE | re.DOTALL)
LINK = re.compile(r'\]\(([^()\s]+)\)|<(?:img|a)\s+[^>]*?(?:src|href)="([^"]+)"')


class DocumentationTests(unittest.TestCase):
    def test_internal_links_images_and_section_references(self):
        for page in sorted([*ROOT.glob("*.md"), *(ROOT / "docs").rglob("*.md")]):
            body = FENCED_BLOCK.sub("", page.read_text(encoding="utf-8"))
            for markdown, html in LINK.findall(body):
                link = markdown or html
                with self.subTest(page=page.relative_to(ROOT), link=link):
                    url = urlsplit(link)
                    if url.scheme or url.netloc:
                        continue
                    target = (page.parent / unquote(url.path)).resolve() if url.path else page
                    self.assertTrue(target.exists(), "Missing local link target")
                    if url.fragment and target.suffix == ".md":
                        headings = re.findall(
                            r"^#{1,6}\s+(.+)$", target.read_text(encoding="utf-8"), re.MULTILINE
                        )
                        anchors = {re.sub(r"[^\w -]", "", h.lower()).replace(" ", "-") for h in headings}
                        self.assertIn(unquote(url.fragment), anchors)
