import unittest

from snapshot_readers import (
    audiobookshelf_items, calibre_books, jellyfin_items, lazylibrarian_items,
    lidarr_albums, radarr_movies, seerr_requests, sonarr_series,
)


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

    def test_arr_readers_preserve_ids_and_file_state(self):
        sonarr = sonarr_series([{"tvdbId": 7, "title": "Dune", "monitored": True, "hasFile": False}])
        radarr = radarr_movies([{"tmdbId": 8, "title": "Arrival", "hasFile": True}])
        self.assertEqual(sonarr[0].authority_id, "7")
        self.assertFalse(sonarr[0].owned)
        self.assertTrue(radarr[0].owned)

    def test_book_and_audio_readers_sanitize_to_owned_records(self):
        audio = audiobookshelf_items({"results": [{"id": "a1", "media": {"title": "Dune"}}]})
        nested_audio = audiobookshelf_items({"results": [{"id": "a2", "media": {"metadata": {"title": "The Hobbit"}}}]})
        books = calibre_books({"books": [{"id": 2, "title": "Dune"}]})
        lazy = lazylibrarian_items({"books": [{"bookid": "b3", "bookname": "Dune", "status": "Have"}]})
        self.assertEqual(audio[0].media_type, "audiobook")
        self.assertEqual(nested_audio[0].title, "The Hobbit")
        self.assertEqual(books[0].authority, "calibre")
        self.assertTrue(lazy[0].owned)


if __name__ == "__main__":
    unittest.main()
