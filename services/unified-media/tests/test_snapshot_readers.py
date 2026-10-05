import unittest

from snapshot_readers import jellyfin_items, lidarr_albums, seerr_requests


class SnapshotReaderTests(unittest.TestCase):
    def test_jellyfin_normalizes_library_and_archive_state(self):
        result = jellyfin_items({"Items": [
            {"Id": "m1", "Name": "Dune", "Type": "Movie"},
            {"Id": "x", "Name": "Ignore", "Type": "Folder"},
        ]}, archive_ids=("m1",))
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0].owned and result[0].archived)

    def test_seerr_uses_external_media_identity(self):
        result = seerr_requests({"results": [{
            "mediaType": "movie", "title": "Dune",
            "media": {"tmdbId": 438631},
        }]})
        self.assertEqual(result[0].authority_id, "438631")

    def test_lidarr_owned_state_comes_from_track_files(self):
        result = lidarr_albums([{
            "foreignAlbumId": "mb-1", "title": "Dune", "monitored": True,
            "statistics": {"trackFileCount": 0},
        }])
        self.assertFalse(result[0].owned)
        self.assertIn("monitored", result[0].signals[0])


if __name__ == "__main__":
    unittest.main()
