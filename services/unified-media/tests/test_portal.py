import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from portal.server import load_recommendations, render_html


class PortalTests(unittest.TestCase):
    def test_render_escapes_snapshot_text(self):
        html = render_html([{"title": "<Dune>", "media_type": "movie", "explanation": "safe"}])
        self.assertIn("&lt;Dune&gt;", html)
        self.assertNotIn("<Dune>", html)

    def test_missing_snapshot_is_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("portal.server.SNAPSHOT_PATH", Path(directory) / "missing.json"):
                self.assertEqual(load_recommendations(), [])

    def test_snapshot_requires_a_list(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as handle:
            json.dump({"bad": True}, handle)
            handle.flush()
            with patch("portal.server.SNAPSHOT_PATH", Path(handle.name)):
                with self.assertRaises(ValueError):
                    load_recommendations()


if __name__ == "__main__":
    unittest.main()
