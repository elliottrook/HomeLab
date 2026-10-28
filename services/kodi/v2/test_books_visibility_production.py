import json
from pathlib import Path
import tempfile
import unittest

import build_books_visibility_production as builder
import books_visibility_followup as subject


class ProductionBooksVisibilityTests(unittest.TestCase):
    def test_build_is_production_scoped_and_pinned(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            output = root / "output"
            source.mkdir()
            raw = (b'<window><control type="button" id="300"><visible>A</visible>'
                   b'<visible>B</visible></control><control type="button" id="304">'
                   b'<visible>A</visible><visible>B</visible></control></window>')
            (source / "IncludesBooks.xml").write_bytes(raw)
            original = subject.DEPLOYED_SOURCE
            subject.DEPLOYED_SOURCE = subject.sha(raw)
            try:
                pin = builder.build(source, output)
            finally:
                subject.DEPLOYED_SOURCE = original
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertEqual(manifest["kind"], "production-books-visibility.v2")
            self.assertIs(manifest["production_changed"], True)
            self.assertEqual(subject.sha((output / "manifest.json").read_bytes()), pin)
            self.assertEqual(manifest["files"][0]["before_sha256"], subject.sha(raw))

    def test_installer_is_fail_closed_to_production(self):
        source = (Path(__file__).parent / "tools/deploy_books_visibility_production.py").read_text()
        self.assertIn('nodename == "AsterTVProd"', source)
        self.assertIn('CHECKPOINT = Path("/storage/.aster-checkpoints/aster-books-visibility-prod2")', source)
        self.assertNotIn('production_changed") is False', source)


if __name__ == "__main__":
    unittest.main()
