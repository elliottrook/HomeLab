import tempfile
import unittest
from pathlib import Path

from service_collectors import (collect_arr, collect_audiobookshelf,
                                collect_audiobookshelf_history, collect_jellyfin,
                                collect_lazylibrarian, collect_lidarr)


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.key = Path(self.tempdir.name) / "key"
        self.key.write_text("test-secret\n", encoding="utf-8")
        self.calls = []

    def tearDown(self):
        self.tempdir.cleanup()

    def request(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if url.endswith("/api/v3/movie"):
            return [{"tmdbId": 8, "title": "Arrival", "hasFile": True}], {}
        if url.endswith("/api/v1/album"):
            return [{"foreignAlbumId": "mb-1", "title": "Kind of Blue",
                     "statistics": {"trackFileCount": 1}}], {}
        if url.endswith("/Items"):
            return {"Items": [{"Id": "j1", "Name": "Dune", "Type": "Movie"}]}, {}
        if "/listening-sessions" in url:
            return {"sessions": [{"libraryItemId": "a1", "title": "Dune",
                                   "startedAt": 1, "updatedAt": 2,
                                   "timeListening": 30}]}, {}
        if url.endswith("/api"):
            return {"books": [{"bookid": "b1", "bookname": "Dune", "status": "Wanted"}]}, {}
        return {"results": [{"id": "a1", "media": {"title": "Dune"}}]}, {}

    def test_arr_collector_is_read_only_and_sanitized(self):
        result = collect_arr("http://radarr", str(self.key), "radarr", request=self.request)
        self.assertEqual(result[0].title, "Arrival")
        self.assertEqual(result[0].authority_id, "8")
        self.assertEqual(self.calls[0][0], "http://radarr/api/v3/movie")
        self.assertEqual(self.calls[0][1]["headers"]["X-Api-Key"], "test-secret")

    def test_jellyfin_collector_uses_token_header_and_omits_history(self):
        result = collect_jellyfin("http://jellyfin", str(self.key), request=self.request)
        self.assertEqual(result[0].authority_id, "j1")
        self.assertNotIn("UserData", self.calls[0][1].get("params", {}))
        self.assertIn('Token="test-secret"', self.calls[0][1]["headers"]["Authorization"])

    def test_audiobookshelf_collector_scopes_library_requests(self):
        result = collect_audiobookshelf("http://abs", str(self.key), request=self.request,
                                       library_ids=("lib1",))
        self.assertEqual(result[0].media_type, "audiobook")
        self.assertIn("/api/libraries/lib1/items", self.calls[0][0])

    def test_audiobookshelf_history_is_sanitized(self):
        result = collect_audiobookshelf_history(
            "http://abs", str(self.key), "user1", request=self.request)
        self.assertEqual(result[0]["authority_id"], "a1")
        self.assertEqual(result[0]["time_listening"], 30)
        self.assertIn("/api/users/user1/listening-sessions", self.calls[0][0])

    def test_lazylibrarian_collector_uses_read_only_list_route(self):
        result = collect_lazylibrarian("http://lazy", str(self.key), request=self.request)
        self.assertEqual(result[0].authority_id, "b1")
        self.assertEqual(self.calls[0][1]["params"]["cmd"], "getAllBooks")

    def test_lidarr_collector_uses_v1_read_route(self):
        result = collect_lidarr("http://lidarr", str(self.key), request=self.request)
        self.assertTrue(result[0].owned)
        self.assertEqual(self.calls[0][0], "http://lidarr/api/v1/album")


if __name__ == "__main__":
    unittest.main()
