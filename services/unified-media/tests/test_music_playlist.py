import unittest

from music_playlist import PlaylistTrack, match_tracks, playlist_plan, retry


class MusicPlaylistTests(unittest.TestCase):
    def test_matching_is_exact_and_preserves_missing_tracks(self):
        matched, missing = match_tracks(
            [PlaylistTrack("Song", "Artist", "Album"), PlaylistTrack("Lost", "Artist", "Album")],
            [{"Id": "1", "Name": "Song", "Artists": ["Artist"], "AlbumArtist": "Artist", "Album": "Album"}],
        )
        self.assertEqual([item[1]["Id"] for item in matched], ["1"])
        self.assertEqual([item.title for item in missing], ["Lost"])

    def test_playlist_plan_is_not_complete_with_any_missing_track(self):
        result = playlist_plan("Mix", [PlaylistTrack("Lost", "Artist")], [])
        self.assertFalse(result["complete"])
        self.assertEqual(result["matched_ids"], [])

    def test_retry_repeats_bounded_operation(self):
        calls = []
        def operation():
            calls.append(1)
            if len(calls) < 3:
                raise RuntimeError("temporary")
            return "ok"
        self.assertEqual(retry(operation, attempts=3), "ok")
        self.assertEqual(len(calls), 3)


if __name__ == "__main__":
    unittest.main()
