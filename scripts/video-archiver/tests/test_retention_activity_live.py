"""Playback in progress must block retention even when paused."""

from unittest import TestCase

from video_archiver.retention_activity_live import (
    collect_active_item_ids, scope_has_active_playback,
)


class ActivePlaybackTests(TestCase):
    def test_active_and_paused_items_are_protected(self):
        def fetch(url, headers):
            self.assertTrue(url.endswith("/Sessions"))
            self.assertIn("Token=", headers["Authorization"])
            return 200, [
                {"NowPlayingItem": {"Id": "movie-a"}, "PlayState": {"IsPaused": False}},
                {"NowPlayingItem": {"Id": "episode-b"}, "PlayState": {"IsPaused": True}},
                {"NowPlayingItem": None},
            ]
        active = collect_active_item_ids("http://jellyfin", "fixture-key", fetch=fetch)
        self.assertTrue(scope_has_active_playback(("movie-a",), active))
        self.assertTrue(scope_has_active_playback(("episode-a", "episode-b"), active))
        self.assertFalse(scope_has_active_playback(("movie-c",), active))

    def test_failed_or_incomplete_session_scan_holds(self):
        for result in ((503, None), (200, {}), (200, [{"NowPlayingItem": {}}])):
            with self.subTest(result=result), self.assertRaises(RuntimeError):
                collect_active_item_ids("http://jellyfin", "fixture-key",
                                        fetch=lambda *_: result)
