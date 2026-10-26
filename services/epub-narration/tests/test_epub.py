from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).parents[1]))

from epub_narration.epub import extract_chapters


CONTAINER = """<?xml version='1.0'?>
<container xmlns='urn:oasis:names:tc:opendocument:xmlns:container'>
  <rootfiles><rootfile full-path='OEBPS/content.opf'/></rootfiles>
</container>"""

PACKAGE = """<?xml version='1.0'?>
<package xmlns='http://www.idpf.org/2007/opf'>
  <manifest>
    <item id='two' href='two.xhtml' media-type='application/xhtml+xml'/>
    <item id='one' href='one.xhtml' media-type='application/xhtml+xml'/>
  </manifest>
  <spine><itemref idref='one'/><itemref idref='two'/></spine>
</package>"""


def write_epub(
    path: Path,
    extra: tuple[tuple[str, str], ...] = (),
    package: str = PACKAGE,
) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("mimetype", "application/epub+zip")
        archive.writestr("META-INF/container.xml", CONTAINER)
        archive.writestr("OEBPS/content.opf", package)
        archive.writestr(
            "OEBPS/one.xhtml",
            "<html><body><h1>Synthetic One</h1><p>Only fixture words.</p><script>hidden()</script></body></html>",
        )
        archive.writestr(
            "OEBPS/two.xhtml",
            "<html><body><h1>Synthetic Two</h1><p>More fixture words.</p></body></html>",
        )
        for name, contents in extra:
            archive.writestr(name, contents)


class EpubTests(unittest.TestCase):
    def test_extracts_synthetic_spine_order_and_ignores_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.epub"
            write_epub(path)
            chapters = extract_chapters(path)
            self.assertEqual(["OEBPS/one.xhtml", "OEBPS/two.xhtml"], [c.member for c in chapters])
            self.assertIn("Synthetic One", chapters[0].text)
            self.assertNotIn("hidden", chapters[0].text)
            self.assertEqual(64, len(chapters[0].text_sha256))

    def test_rejects_any_unsafe_archive_member(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.epub"
            write_epub(path, (("../escape", "synthetic"),))
            with self.assertRaisesRegex(ValueError, "epub-unsafe-member"):
                extract_chapters(path)

    def test_rejects_missing_spine_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.epub"
            write_epub(path, package=PACKAGE.replace("idref='two'", "idref='missing'"))
            with self.assertRaisesRegex(ValueError, "epub-spine-reference"):
                extract_chapters(path)


if __name__ == "__main__":
    unittest.main()

