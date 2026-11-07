"""A candidate manifest must account for embedded tracks and every sidecar."""

import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from video_archiver.retention_subtitles_live import inspect_subtitles, jellyfin_container_probe


class SubtitleEvidenceTests(TestCase):
    def test_container_probe_maps_only_verified_media(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            video = root / "archive-movies" / "film.mkv"
            video.parent.mkdir()
            video.write_bytes(b"fixture")
            completed = type("Result", (), {"returncode": 0, "stdout": '{"streams": []}'})()
            with patch("video_archiver.retention_subtitles_live.subprocess.run",
                       return_value=completed) as run:
                self.assertEqual(jellyfin_container_probe(video, data_root=root), {"streams": []})
                command = run.call_args.args[0]
                self.assertEqual(command[:3], ["docker", "exec", "jellyfin"])
                self.assertEqual(command[-1], "/media/archive-movies/film.mkv")
            outside = root.parent / "other.mkv"
            with self.assertRaisesRegex(RuntimeError, "cannot be verified"):
                jellyfin_container_probe(outside, data_root=root)

    def test_embedded_variants_and_associated_sidecar_are_recorded(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            video = root / "episode.mkv"
            video.write_bytes(b"fixture")
            (root / "episode.en.forced.srt").write_bytes(b"English forced")
            (root / "other.mkv").write_bytes(b"other")
            (root / "other.fr.srt").write_bytes(b"French")
            probe = lambda _: {"streams": [
                {"codec_type": "subtitle", "codec_name": "hdmv_pgs_subtitle",
                 "tags": {"language": "eng"}, "disposition": {"forced": 1}},
                {"codec_type": "subtitle", "codec_name": "subrip",
                 "tags": {"language": "und"}, "disposition": {}},
            ]}
            result = inspect_subtitles(video, data_root=root, probe=probe)
            self.assertEqual(len(result.embedded), 2)
            self.assertTrue(result.embedded[0].forced)
            self.assertEqual([row.name for row in result.sidecars], ["episode.en.forced.srt"])
            (root / "mystery.srt").write_bytes(b"unknown owner")
            with self.assertRaisesRegex(RuntimeError, "ownership ambiguous"):
                inspect_subtitles(video, data_root=root, probe=probe)
            (root / "mystery.srt").unlink()
            (root / "Subs").mkdir()
            (root / "Subs" / "episode.en.srt").write_bytes(b"nested")
            with self.assertRaisesRegex(RuntimeError, "nested subtitle"):
                inspect_subtitles(video, data_root=root, probe=probe)
