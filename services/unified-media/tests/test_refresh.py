import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import refresh


class RefreshLoopTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.snapshot = Path(self.tempdir.name) / "recommendations.json"
        self.trigger = Path(self.tempdir.name) / "refresh-now"

    def tearDown(self):
        self.tempdir.cleanup()

    def test_due_state_uses_durable_snapshot_age(self):
        self.snapshot.write_text("[]", encoding="utf-8")
        os.utime(self.snapshot, (1000, 1000))
        with patch.object(refresh, "SNAPSHOT_PATH", self.snapshot), \
             patch.object(refresh, "REFRESH_TRIGGER_PATH", self.trigger):
            self.assertFalse(refresh.refresh_due(600, now=1500))
            self.assertTrue(refresh.refresh_due(600, now=1600))

    def test_trigger_or_missing_snapshot_is_due(self):
        with patch.object(refresh, "SNAPSHOT_PATH", self.snapshot), \
             patch.object(refresh, "REFRESH_TRIGGER_PATH", self.trigger):
            self.assertTrue(refresh.refresh_due(600, now=1000))
            self.snapshot.write_text("[]", encoding="utf-8")
            os.utime(self.snapshot, (1000, 1000))
            self.trigger.touch()
            self.assertTrue(refresh.refresh_due(600, now=1001))

    def test_rotation_is_stable_and_changes_start(self):
        values = ["A", "B", "A", "C"]
        self.assertEqual(refresh._rotated_unique(values, 0), ["A", "B", "C"])
        self.assertEqual(refresh._rotated_unique(values, 1), ["B", "C", "A"])

    def test_library_source_failure_retains_that_sources_last_good_records(self):
        library = Path(self.tempdir.name) / "library.json"
        library.write_text(json.dumps([
            {"authority": "audiobookshelf", "authority_id": "a1",
             "media_type": "audiobook", "title": "Retained"}
        ]), encoding="utf-8")
        with patch.object(refresh, "LIBRARY_SNAPSHOT_PATH", str(library)), \
             patch.dict(os.environ, {
                 "AUDIOBOOKSHELF_TOKEN_PATH": "/unused/token",
                 "AUDIOBOOKSHELF_LIBRARY_IDS": "library-1",
             }, clear=True), \
             patch.object(refresh, "collect_audiobookshelf", side_effect=OSError("offline")):
            refresh._refresh_library_snapshot()
        self.assertEqual(json.loads(library.read_text(encoding="utf-8"))[0]["title"], "Retained")

    def test_history_source_failure_retains_last_good_and_allows_other_sources(self):
        history = Path(self.tempdir.name) / "history.json"
        history.write_text(json.dumps([
            {"authority": "audiobookshelf", "authority_id": "a1", "title": "Retained"}
        ]), encoding="utf-8")
        with patch.object(refresh, "HISTORY_SNAPSHOT_PATH", str(history)), \
             patch.dict(os.environ, {
                 "AUDIOBOOKSHELF_TOKEN_PATH": "/unused/token",
                 "AUDIOBOOKSHELF_USER_ID": "user-1",
             }, clear=True), \
             patch.object(refresh, "collect_audiobookshelf_history", side_effect=OSError("offline")):
            refresh._refresh_history_snapshot()
        self.assertEqual(json.loads(history.read_text(encoding="utf-8"))[0]["title"], "Retained")


if __name__ == "__main__":
    unittest.main()
