import unittest

from jellyfin_trailer_route import (
    extract_youtube_video_id,
    first_supported_remote_trailer,
    kodi_youtube_plugin_url,
    validated_kodi_youtube_plugin_url,
)


class JellyfinTrailerRouteTests(unittest.TestCase):
    def test_supported_jellyfin_youtube_forms_become_one_plugin_route(self) -> None:
        video_id = "UrIbxk7idYA"
        for url in (
            f"https://www.youtube.com/watch?v={video_id}",
            f"https://youtu.be/{video_id}",
            f"https://youtube.com/embed/{video_id}",
            f"https://m.youtube.com/shorts/{video_id}",
            f"https://www.youtube.com/live/{video_id}",
        ):
            with self.subTest(url=url):
                self.assertEqual(extract_youtube_video_id(url), video_id)
        self.assertEqual(
            kodi_youtube_plugin_url(video_id),
            "plugin://plugin.video.youtube/play/?video_id=UrIbxk7idYA",
        )

    def test_rejects_untrusted_or_ambiguous_values(self) -> None:
        for value in (
            "http://youtube.com/watch?v=UrIbxk7idYA",
            "https://youtube.example/watch?v=UrIbxk7idYA",
            "https://www.youtube.com/watch?v=too-short",
            "https://youtu.be/UrIbxk7idYA/extra",
            "plugin://plugin.video.youtube/play/?video_id=UrIbxk7idYA",
            "javascript:alert(1)",
            "",
        ):
            with self.subTest(value=value):
                self.assertIsNone(extract_youtube_video_id(value))

    def test_uses_only_first_supported_curated_trailer(self) -> None:
        self.assertEqual(
            first_supported_remote_trailer(
                [
                    "https://invalid.example/trailer",
                    "https://youtu.be/Pc9MbCNYn3k",
                    "https://youtu.be/2sBRb7Mbg0A",
                ]
            ),
            "plugin://plugin.video.youtube/play/?video_id=Pc9MbCNYn3k",
        )
        self.assertIsNone(first_supported_remote_trailer([]))

    def test_plugin_route_refuses_unvalidated_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid-youtube-video-id"):
            kodi_youtube_plugin_url("../../unsafe")

    def test_accepts_only_the_exact_jellyfin_kodi_route(self) -> None:
        expected = "plugin://plugin.video.youtube/play/?video_id=Pc9MbCNYn3k"
        self.assertEqual(validated_kodi_youtube_plugin_url(expected), expected)
        for value in (
            "plugin://plugin.video.youtube/play/?video_id=too-short",
            "plugin://plugin.video.youtube/play/?video_id=Pc9MbCNYn3k&next=1",
            "plugin://plugin.video.other/play/?video_id=Pc9MbCNYn3k",
            "plugin://plugin.video.youtube/search/?video_id=Pc9MbCNYn3k",
            "https://www.youtube.com/watch?v=Pc9MbCNYn3k",
        ):
            with self.subTest(value=value):
                self.assertIsNone(validated_kodi_youtube_plugin_url(value))


if __name__ == "__main__":
    unittest.main()
