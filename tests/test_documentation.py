import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
FENCED_BLOCK = re.compile(r"^```[^\n]*\n.*?^```[^\n]*$", re.MULTILINE | re.DOTALL)
LINK = re.compile(r'\]\(([^()\s]+)\)|<(?:img|a)\s+[^>]*?(?:src|href)="([^"]+)"')


def local_links(page):
    body = FENCED_BLOCK.sub("", page.read_text(encoding="utf-8"))
    for markdown, html in LINK.findall(body):
        url = urlsplit(markdown or html)
        if not (url.scheme or url.netloc):
            target = (page.parent / unquote(url.path)).resolve() if url.path else page
            yield target, unquote(url.fragment)


class DocumentationTests(unittest.TestCase):
    def test_internal_links_images_and_section_references(self):
        for page in sorted([*ROOT.glob("*.md"), *(ROOT / "docs").rglob("*.md")]):
            for target, fragment in local_links(page):
                with self.subTest(page=page.relative_to(ROOT), target=target, fragment=fragment):
                    self.assertTrue(target.exists(), "Missing local link target")
                    if fragment and target.suffix == ".md":
                        headings = re.findall(
                            r"^#{1,6}\s+(.+)$", target.read_text(encoding="utf-8"), re.MULTILINE
                        )
                        anchors = {re.sub(r"[^\w -]", "", h.lower()).replace(" ", "-") for h in headings}
                        self.assertIn(fragment, anchors)

    def test_all_guides_are_reachable_from_the_index(self):
        docs = ROOT / "docs"
        guides = set(docs.rglob("*.md"))
        pending = [docs / "index.md"]
        reached = set()
        while pending:
            page = pending.pop()
            if page not in reached:
                reached.add(page)
                pending.extend(target for target, _ in local_links(page) if target in guides)
        self.assertEqual(guides - reached, set(), "Guide missing from documentation navigation")
