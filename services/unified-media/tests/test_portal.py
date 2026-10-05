import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from portal.server import action_key, load_recommendations, render_html


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

    def test_action_key_is_stable_and_scoped_to_authority_identity(self):
        item = {"authority": "seerr", "authority_id": "1"}
        self.assertEqual(action_key(item), action_key(dict(item)))
        self.assertNotEqual(action_key(item), action_key({"authority": "lidarr", "authority_id": "1"}))


if __name__ == "__main__":
    unittest.main()
