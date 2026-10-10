from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from build_sample import BANNER, build


class SampleBuildTests(unittest.TestCase):
    def make_source(self, root: Path) -> Path:
        source = root / "source"
        source.mkdir(parents=True)
        for name in ("index.html", "landscapes.html", "flora.html", "contrasts.html", "people.html"):
            (source / name).write_text("<html><head></head><body>fixture</body></html>")
        (source / "styles.css").write_text("body{}")
        (source / "script.js").write_text("")
        return source

    def test_every_page_is_conspicuously_marked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            destination = root / "release"
            build(self.make_source(root), destination)
            for page in destination.glob("*.html"):
                self.assertIn(BANNER, page.read_text())
            self.assertTrue((destination / "SAMPLE-NOT-FOR-PUBLICATION.txt").is_file())
            manifest = (destination / "MANIFEST.sha256").read_text()
            self.assertIn("./index.html", manifest)
            self.assertNotIn("MANIFEST.sha256", manifest)

    def test_appledouble_metadata_is_excluded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.make_source(root)
            (source / "._index.html").write_bytes(b"metadata")
            destination = root / "release"
            build(source, destination)
            self.assertFalse((destination / "._index.html").exists())

    def test_refuses_incomplete_or_existing_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.make_source(root)
            (source / "people.html").unlink()
            with self.assertRaises(ValueError):
                build(source, root / "release")
            source = self.make_source(root / "other")
            destination = root / "existing"
            destination.mkdir()
            with self.assertRaises(ValueError):
                build(source, destination)


if __name__ == "__main__":
    unittest.main()
