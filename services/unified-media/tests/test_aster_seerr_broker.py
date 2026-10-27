import json
import tempfile
import threading
import unittest
from unittest import mock
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aster_acquisition_broker import BrokerError as AcquisitionBrokerError
from aster_seerr_broker import (BrokerError, Handler, SeerrClient, authorize,
                                provider_transport, request_json)


class Transport:
    def __init__(self, *, existing=False, season_status=1,
                 season_request=None):
        self.calls = []
        self.existing = existing
        self.season_status = season_status
        self.season_request = season_request

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
        if url.endswith("/tv/1413"):
            return 200, {"id": 1413, "name": "Exact series",
                "externalIds": {"tvdbId": 250487},
                "seasons": [{"seasonNumber": 1, "episodeCount": 2}],
                "mediaInfo": {"status": 1, "seasons": [],
                              "requests": []}}, {}
        if url.endswith("/movie/123"):
            requests = [{"id": 77, "status": 1}] if self.existing else []
            return 200, {"id": 123, "title": "Example", "mediaInfo": {
                "status": 2 if self.existing else 1, "requests": requests}}, {}
        if url.endswith("/tv/456"):
            return 200, {"id": 456, "name": "Series", "seasons": [
                {"seasonNumber": 0}, {"seasonNumber": 1}, {"seasonNumber": 2}],
                "mediaInfo": {"status": 1,
                    "seasons": [{"seasonNumber": 2,
                                 "status": self.season_status}],
                    "requests": [self.season_request]
                    if self.season_request else []}}, {}
        if url.endswith("/tv/456/season/2"):
            return 200, {"seasonNumber": 2, "episodes": [{
                "id": 99, "name": "Episode", "airDate": "2026-01-01",
                "episodeNumber": 1, "seasonNumber": 2,
                "stillPath": "https://image.tmdb.org/t/p/original/still.jpg",
                "overview": "Synopsis"}]}, {}
        if url.endswith("/request"):
            return 201, {"id": 88, "status": 1, "requestedBy": {"email": "private"}}, {}
        raise AssertionError(url)


def proposal(kind="movie", media_id=123, seasons=None):
    return {"schema": 1, "action": "request", "authority": "seerr",
            "candidate_id": f"seerr:{kind}:{media_id}", "media_type": kind,
            "media_id": media_id, "seasons": seasons or [], "confirmed": True}


def season_proposal():
    return {"schema": 1, "action": "request-season", "authority": "seerr",
            "candidate_id": "seerr:tv:456", "media_id": 456,
            "season": 2, "confirmed": True}


class AsterSeerrBrokerTests(unittest.TestCase):
    def test_only_explicit_lazy_queue_accepts_plain_ok(self):
        class Reply(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'OK')
            def log_message(self, *_):
                pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Reply)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as temporary:
                key = Path(temporary)/'key'
                key.write_text('synthetic-key')
                base = 'http://127.0.0.1:%d' % server.server_port
                lazy = provider_transport(base, key, 'lazylibrarian')
                self.assertEqual(lazy('GET', '/api', {'cmd': 'queueBook', 'id': 'OL1W'}, None),
                                 (200, 'OK'))
                with self.assertRaises(BrokerError):
                    lazy('GET', '/api', {'cmd': 'getAllBooks'}, None)
                with self.assertRaises(BrokerError):
                    request_json(base)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

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

    def test_provider_transport_keeps_keys_out_of_lidarr_query_and_lazy_headers(self):
        with tempfile.TemporaryDirectory() as temporary:
            key = Path(temporary) / "key"
            key.write_text("private-key")
            calls = []
            def transport(url, **kwargs):
                calls.append((url, kwargs))
                return 200, {}, {}
            lidarr = provider_transport("http://lidarr:8686", key, "lidarr",
                                        transport)
            lidarr("GET", "/api/v1/album", {"term": "Blue"}, None)
            self.assertNotIn("private-key", calls[0][0])
            self.assertEqual(calls[0][1]["headers"]["X-Api-Key"],
                             "private-key")
            lazy = provider_transport("http://lazylibrarian:5299", key,
                                      "lazylibrarian", transport)
            lazy("GET", "/api", {"cmd": "getAllBooks"}, None)
            self.assertIn("apikey=private-key", calls[1][0])
            self.assertNotIn("X-Api-Key", calls[1][1]["headers"])

    def test_provider_transport_rejects_https_userinfo_and_paths(self):
        for value in ("https://lidarr:8686", "http://user@lidarr:8686",
                      "http://lidarr:8686/api"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(BrokerError,
                                            "provider-url-invalid"):
                    provider_transport(value, Path("/unused"), "lidarr")

    def test_acquisition_coordinator_error_is_a_bounded_conflict(self):
        with tempfile.TemporaryDirectory() as temporary:
            token = Path(temporary) / "token"
            token.write_text("a" * 48)
            class Reject:
                def submit(self, _value):
                    raise AcquisitionBrokerError("candidate-unavailable")
            with mock.patch.dict("os.environ", {
                    "ASTER_ACQUISITION_TOKEN_PATH": str(token)}), \
                    mock.patch.object(Handler, "_acquisition",
                                      return_value=Reject()):
                server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
                thread = threading.Thread(target=server.serve_forever,
                                          daemon=True)
                thread.start()
                try:
                    request = urllib.request.Request(
                        "http://127.0.0.1:%d/v1/acquisition" % server.server_port,
                        data=b'{"schema":1}', method="POST",
                        headers={"Authorization": "Bearer " + "a" * 48,
                                 "Content-Type": "application/json"})
                    with self.assertRaises(urllib.error.HTTPError) as raised:
                        urllib.request.urlopen(request, timeout=2)
                    self.assertEqual(raised.exception.code, 409)
                    self.assertIn(b"candidate-unavailable",
                                  raised.exception.read())
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join(timeout=2)

    def test_search_returns_only_sanitized_exact_schema(self):
        transport = Transport()
        value = self.client(transport).search("Example title", "all")
        self.assertEqual([row["identity"] for row in value["candidates"]],
                         ["seerr:movie:123", "seerr:tv:456"])
        self.assertEqual(value["candidates"][1]["seasons"], [1, 2])
        self.assertNotIn("requestedBy", json.dumps(value))
        search_url = next(url for url, _ in transport.calls if "/search?" in url)
        self.assertIn("query=Example%20title", search_url)
        self.assertNotIn("Example+title", search_url)

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

    def test_episode_catalogue_and_season_are_sanitized(self):
        client = self.client(Transport())
        summary = client.catalogue(456)
        self.assertEqual(summary["candidate_id"], "seerr:tv:456")
        self.assertTrue(summary["seasons"][2]["requestable"])
        value = client.season(456, 2)
        self.assertEqual(value["episodes"][0]["title"], "Episode")
        self.assertNotIn("id", value["episodes"][0])

    def test_tvdb_resolution_uses_exact_external_identity(self):
        class ResolveTransport(Transport):
            def __call__(self, url, **kwargs):
                if "/search?" in url:
                    self.calls.append((url, kwargs))
                    return 200, {"results": [
                        {"id": 1413, "mediaType": "tv", "name": "Exact series"},
                        {"id": 1414, "mediaType": "tv", "name": "Similar series"},
                    ]}, {}
                if url.endswith("/tv/1414"):
                    self.calls.append((url, kwargs))
                    return 200, {"id": 1414, "name": "Similar series",
                                 "externalIds": {"tvdbId": 999}}, {}
                return super().__call__(url, **kwargs)
        transport = ResolveTransport()
        value = self.client(transport).resolve_tv(250487, "Exact series")
        self.assertEqual(value["candidate_id"], "seerr:tv:1413")
        search = next(url for url, _ in transport.calls if "/search?" in url)
        self.assertIn("query=Exact%20series", search)

    def test_tvdb_resolution_fails_closed_on_no_or_duplicate_match(self):
        class Duplicate(Transport):
            def __call__(self, url, **kwargs):
                if "/search?" in url:
                    self.calls.append((url, kwargs))
                    return 200, {"results": [
                        {"id": 1413, "mediaType": "tv"},
                        {"id": 1414, "mediaType": "tv"}]}, {}
                if url.endswith("/tv/1414"):
                    self.calls.append((url, kwargs))
                    return 200, {"id": 1414, "name": "Duplicate",
                                 "externalIds": {"tvdbId": 250487}}, {}
                return super().__call__(url, **kwargs)
        with self.assertRaisesRegex(BrokerError, "tvdb-match-unavailable"):
            self.client(Duplicate()).resolve_tv(250487, "Exact series")
        with self.assertRaisesRegex(BrokerError, "tvdb-identity"):
            self.client(Transport()).resolve_tv(True, "Exact series")

    def test_season_request_is_revalidated_and_duplicate_safe(self):
        transport = Transport()
        value = self.client(transport).submit_season(season_proposal())
        self.assertEqual((value["season"], value["state"], value["duplicate"]),
                         (2, "pending", False))
        call = [row for row in transport.calls if row[0].endswith("/request")][-1]
        self.assertEqual(call[1]["body"], {"mediaType": "tv", "mediaId": 456,
                                           "seasons": [2]})
        request = {"id": 91, "status": 1,
                   "seasons": [{"seasonNumber": 2}]}
        duplicate = Transport(season_status=2, season_request=request)
        value = self.client(duplicate).submit_season(season_proposal())
        self.assertEqual((value["request_id"], value["duplicate"]), (91, True))
        self.assertFalse(any(url.endswith("/request") for url, _ in duplicate.calls))


if __name__ == "__main__":
    unittest.main()
