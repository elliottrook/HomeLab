from __future__ import annotations

import json
import unittest
from unittest import mock

import app


class AudioCacheVersionTests(unittest.TestCase):
    def test_metadata_generation_timestamp_is_media_version(self):
        generated = "2026-11-06T13:24:53.863683+00:00"
        fake_path = mock.Mock()
        fake_path.read_text.return_value = json.dumps(
            {"generated_at": generated, "story_count": 12}
        )
        with mock.patch.object(app, "AUDIO_META_PATH", fake_path):
            metadata = app.get_audio_meta()
        self.assertEqual(metadata["media_version"], generated)

    def test_audio_and_chapters_urls_are_versioned(self):
        self.assertIn("latest.mp3?v={{ audio.media_version|urlencode }}", app.TEMPLATE_DIGEST)
        self.assertIn("latest.vtt?v={{ audio.media_version|urlencode }}", app.TEMPLATE_DIGEST)

    def test_digest_updated_timestamp_uses_24_hour_clock(self):
        connection = mock.Mock()
        connection.execute.return_value.fetchone.return_value = (
            "2026-11-06T23:17:00+00:00",
        )
        with mock.patch.object(app.sqlite3, "connect", return_value=connection):
            updated = app.get_digest_updated_at()
        self.assertEqual(updated, "Updated Nov 6, 2026 at 16:17")
        connection.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
