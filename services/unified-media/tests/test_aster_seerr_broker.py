import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aster_seerr_broker import BrokerError, SeerrClient, authorize


class Transport:
    def __init__(self, *, existing=False):
        self.calls = []
        self.existing = existing

    def __call__(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if url.endswith("/auth/local"):
            return 200, {}, {"Set-Cookie": "connect.sid=test; Path=/"}
        if "/search?" in url:
            return 200, {"results": [
                {"id": 123, "mediaType": "movie", "title": "Example",
                 "releaseDate": "2026-04-01", "overview": "Movie", "posterPath": "/p.jpg"},
                {"id": 456, "mediaType": "tv", "name": "Series",
                 "firstAirDate": "2024-01-01", "overview": "TV", "posterPath": "/t.jpg"},
            ]}, {}
        if url.endswith("/movie/123"):
            requests = [{"id": 77, "status": 1}] if self.existing else []
            return 200, {"id": 123, "title": "Example", "mediaInfo": {
                "status": 2 if self.existing else 1, "requests": requests}}, {}
        if url.endswith("/tv/456"):
            return 200, {"id": 456, "name": "Series", "seasons": [
                {"seasonNumber": 0}, {"seasonNumber": 1}, {"seasonNumber": 2}],
                "mediaInfo": {"status": 1, "requests": []}}, {}
        if url.endswith("/request"):
            return 201, {"id": 88, "status": 1, "requestedBy": {"email": "private"}}, {}
        raise AssertionError(url)


def proposal(kind="movie", media_id=123, seasons=None):
    return {"schema": 1, "action": "request", "authority": "seerr",
            "candidate_id": f"seerr:{kind}:{media_id}", "media_type": kind,
            "media_id": media_id, "seasons": seasons or [], "confirmed": True}


class AsterSeerrBrokerTests(unittest.TestCase):
    def client(self, transport):
        temporary = tempfile.NamedTemporaryFile(mode="w", delete=False)
        temporary.write("password"); temporary.close()
        self.addCleanup(Path(temporary.name).unlink)
        return SeerrClient("http://seerr:5055", "requester@example.invalid",
                           Path(temporary.name), transport)

    def test_bearer_auth_is_exact_and_constant_time_boundary(self):
        token = "a" * 48
        authorize("Bearer " + token, token)
        for value in ("", token, "Bearer short", "bearer " + token):
            with self.assertRaises(BrokerError):
                authorize(value, token)

    def test_search_returns_only_sanitized_exact_schema(self):
        transport = Transport()
        value = self.client(transport).search("Example", "all")
        self.assertEqual([row["identity"] for row in value["candidates"]],
                         ["seerr:movie:123", "seerr:tv:456"])
        self.assertEqual(value["candidates"][1]["seasons"], [1, 2])
        self.assertNotIn("requestedBy", json.dumps(value))

    def test_movie_request_is_revalidated_and_sanitized(self):
        transport = Transport()
        value = self.client(transport).submit(proposal())
        self.assertEqual(value, {"schema": 1, "candidate_id": "seerr:movie:123",
                                 "request_id": 88, "state": "pending",
                                 "duplicate": False})
        call = next(call for call in transport.calls if call[0].endswith("/request"))
        self.assertEqual(call[1]["body"], {"mediaType": "movie", "mediaId": 123})

    def test_existing_request_returns_duplicate_without_write(self):
        transport = Transport(existing=True)
        value = self.client(transport).submit(proposal())
        self.assertEqual((value["request_id"], value["duplicate"]), (77, True))
        self.assertFalse(any(url.endswith("/request") for url, _ in transport.calls))

    def test_tv_request_requires_still_available_seasons(self):
        transport = Transport()
        client = self.client(transport)
        with self.assertRaisesRegex(BrokerError, "seasons-changed"):
            client.submit(proposal("tv", 456, [3]))
        value = client.submit(proposal("tv", 456, [1, 2]))
        self.assertEqual(value["request_id"], 88)
        call = [call for call in transport.calls if call[0].endswith("/request")][-1]
        self.assertEqual(call[1]["body"]["seasons"], [1, 2])


if __name__ == "__main__":
    unittest.main()
