import unittest

from authority_adapters import LazyLibrarianAdapter, LidarrAdapter, SeerrAdapter
from request_contract import Candidate


class FakeTransport:
    def __init__(self, response):
        self.calls = []
        self.response = response

    def __call__(self, method, path, body):
        self.calls.append((method, path, body))
        return self.response


class AuthorityAdapterTests(unittest.TestCase):
    def test_seerr_requires_approval_and_posts_seasons(self):
        transport = FakeTransport({"id": 42, "status": "pending"})
        adapter = SeerrAdapter(transport)
        candidate = Candidate("tv", "seerr", "tmdb-123", "Dune", evidence=("tmdb",))
        blocked = adapter.request(candidate, media_id=123)
        self.assertEqual(blocked.state, "blocked")
        self.assertEqual(transport.calls, [])
        result = adapter.request(candidate, media_id=123, seasons=[1], approve=True)
        self.assertEqual(result.request_id, "42")
        self.assertEqual(transport.calls[0][1], "/api/v1/request")
        self.assertEqual(transport.calls[0][2]["seasons"], [1])

    def test_lidarr_is_album_only(self):
        transport = FakeTransport({"id": 77})
        adapter = LidarrAdapter(transport)
        candidate = Candidate("album", "lidarr", "mb-1", "Kind of Blue", evidence=("mbid",))
        result = adapter.add_album(
            candidate,
            lookup={"foreignAlbumId": "mb-1", "title": "Kind of Blue",
                    "artist": {"foreignArtistId": "9"}},
            root_folder_path="/media/media/music",
            quality_profile_id=1,
            metadata_profile_id=1,
            approve=True,
        )
        self.assertEqual(result.request_id, "77")
        self.assertTrue(transport.calls[0][2]["monitored"])
        self.assertEqual(transport.calls[0][2]["addOptions"]["monitor"], "all")

    def test_lazy_wanted_route_blocks_ambiguous_match(self):
        transport = FakeTransport({"bookId": 5})
        adapter = LazyLibrarianAdapter(transport)
        candidate = Candidate("ebook", "lazylibrarian", "book-1", "Dune",
                              evidence=("author",), match_count=2)
        result = adapter.add_wanted(candidate, approve=True)
        self.assertEqual(result.state, "blocked")
        self.assertEqual(transport.calls, [])

    def test_lazy_wanted_adds_then_queues_ebook(self):
        transport = FakeTransport(True)
        adapter = LazyLibrarianAdapter(transport)
        candidate = Candidate("ebook", "lazylibrarian", "book-1", "Dune",
                              evidence=("author",), match_count=1)
        result = adapter.add_wanted(candidate, approve=True)
        self.assertEqual(result.state, "submitted")
        self.assertEqual(transport.calls, [
            ("GET", "/api", {"cmd": "addBook", "id": "book-1"}),
            ("GET", "/api", {"cmd": "queueBook", "id": "book-1", "type": "eBook"}),
        ])


if __name__ == "__main__":
    unittest.main()
