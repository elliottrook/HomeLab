from dataclasses import replace
from unittest import TestCase

from video_archiver.optimizer_contract import (
    Audio, Manifest, Sidecar, Subtitle, Video, check_candidate,
)


class CandidateContractTests(TestCase):
    source = Manifest(
        size_bytes=20_000_000_000,
        duration_seconds=7200,
        video=Video(3840, 2160, "smpte2084", "bt2020"),
        audio=(Audio("eng", 8), Audio("fra", 2)),
        subtitles=(
            Subtitle("eng", "hdmv_pgs_subtitle", forced=True),
            Subtitle("eng", "hdmv_pgs_subtitle", hearing_impaired=True),
            Subtitle("und", "subrip"),
        ),
        sidecars=(Sidecar(".en.srt", "abc123"),),
    )
    output = Manifest(
        size_bytes=4_900_000_000,
        duration_seconds=7200,
        video=Video(1920, 1080, "smpte2084", "bt2020"),
        audio=(Audio("eng", 6),),
        subtitles=source.subtitles,
        sidecars=source.sidecars,
    )

    def test_good_1080_hdr_fallback_passes_machine_contract(self):
        self.assertEqual(check_candidate(self.source, self.output), ())

    def test_exact_ceiling_is_allowed(self):
        self.assertEqual(check_candidate(self.source, replace(self.output, size_bytes=5_000_000_000)), ())

    def test_one_byte_over_ceiling_is_rejected(self):
        self.assertIn("ceiling", " ".join(check_candidate(self.source, replace(self.output, size_bytes=5_000_000_001))))

    def test_dropped_forced_or_sdh_track_is_rejected(self):
        bad = replace(self.output, subtitles=self.output.subtitles[1:])
        self.assertIn("subtitle", " ".join(check_candidate(self.source, bad)))
        bad = replace(self.output, subtitles=(replace(self.output.subtitles[1], hearing_impaired=False),) + self.output.subtitles[:1] + self.output.subtitles[2:])
        self.assertIn("subtitle", " ".join(check_candidate(self.source, bad)))

    def test_hdr_loss_is_rejected(self):
        bad = replace(self.output, video=replace(self.output.video, transfer=None))
        self.assertIn("HDR", " ".join(check_candidate(self.source, bad)))

    def test_surround_downmix_is_rejected(self):
        bad = replace(self.output, audio=(Audio("eng", 2),))
        self.assertIn("5.1", " ".join(check_candidate(self.source, bad)))

    def test_english_audio_loss_is_rejected(self):
        bad = replace(self.output, audio=(Audio("fra", 6),))
        self.assertIn("English", " ".join(check_candidate(self.source, bad)))

    def test_720p_and_distorted_aspect_are_rejected(self):
        bad = replace(self.output, video=replace(self.output.video, width=1280, height=720))
        self.assertIn("1080p", " ".join(check_candidate(self.source, bad)))
        bad = replace(self.output, video=replace(self.output.video, width=1920, height=900))
        self.assertIn("aspect", " ".join(check_candidate(self.source, bad)))

    def test_changed_sidecar_is_rejected(self):
        bad = replace(self.output, sidecars=(Sidecar(".en.srt", "different"),))
        self.assertIn("sidecar", " ".join(check_candidate(self.source, bad)))

    def test_compliant_source_is_not_recompressed(self):
        source = replace(self.source, size_bytes=4_000_000_000)
        self.assertIn("do not recompress", " ".join(check_candidate(source, self.output)))
