"""Regression coverage for the September 28 compaction and Jellyfin failures."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent / "video-archiver"))
from video_archiver.compact import audio_bitrate, probe_full, make_plan
from video_archiver.jellyfin_client import JellyfinClient, JellyfinApiError


class CompactBudgetTests(unittest.TestCase):
    def probe(self, audio):
        data = {"format": {"duration": "7361.28"}, "streams": [
            {"codec_type": "video", "width": 1920, "height": 816, "codec_name": "hevc"},
            dict(audio, codec_type="audio", channels=6, codec_name="aac")]}
        with patch("video_archiver.compact._run", return_value=SimpleNamespace(
                returncode=0, stdout=json.dumps(data))):
            return probe_full(Path("test.mkv"), SimpleNamespace(ffprobe_bin="probe"))

    def plan(self, info):
        return make_plan(Path("test.mkv"), info,
                         SimpleNamespace(target_size_bytes=1610612736), {"cap_bytes": 1900000000})

    def test_real_xfiles_audio_is_budgeted(self):
        info = self.probe({"tags": {"BPS": "351446"}})
        plan = self.plan(info)
        self.assertEqual(info.audio[0].bit_rate, 351446)
        self.assertEqual(plan.audio_args, ["-c:a:0", "copy"])
        self.assertEqual(plan.audio_kbps, 351)
        self.assertLess(plan.video_kbps, 1800)
        self.assertEqual((plan.out_w, plan.out_h), (1920, 816))
        self.assertLess(plan.predicted_bytes, 1900000000)

    def test_bitrate_variants_and_invalid_values(self):
        self.assertEqual(audio_bitrate({"bit_rate": "192000", "tags": {"BPS": "351446"}}), 192000)
        self.assertEqual(audio_bitrate({"bit_rate": "N/A", "tags": {"BPS-eng": "387827"}}), 387827)
        self.assertIsNone(audio_bitrate({"bit_rate": "0", "tags": {"BPS": "-1"}}))
        self.assertIsNone(audio_bitrate({"tags": {"BPS": "N/A"}}))

    def test_unknown_audio_gets_bounded_surround_encode(self):
        plan = self.plan(self.probe({}))
        self.assertEqual(plan.audio_kbps, 384)
        self.assertEqual(plan.audio_args, ["-c:a:0", "eac3", "-b:a:0", "384k"])


class JellyfinTests(unittest.TestCase):
    @patch("video_archiver.jellyfin_client.requests.post")
    def test_current_authorization_and_scan_endpoint(self, post):
        post.return_value = SimpleNamespace(status_code=204)
        JellyfinClient("http://jellyfin:8096", "synthetic-key", "scan-id").refresh_all_libraries()
        args, kwargs = post.call_args
        self.assertEqual(args[0], "http://jellyfin:8096/ScheduledTasks/Running/scan-id")
        self.assertNotIn("X-Emby-Token", kwargs["headers"])
        self.assertIn('Token="synthetic-key"', kwargs["headers"]["Authorization"])
        self.assertTrue(kwargs["headers"]["Authorization"].startswith("MediaBrowser "))

    @patch("video_archiver.jellyfin_client.requests.post")
    def test_rejected_scan_remains_an_error(self, post):
        post.return_value = SimpleNamespace(status_code=401, text="")
        with self.assertRaises(JellyfinApiError):
            JellyfinClient("http://jellyfin:8096", "synthetic-key", "scan-id").refresh_all_libraries()


if __name__ == "__main__":
    unittest.main()
