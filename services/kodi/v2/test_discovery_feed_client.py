from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from discovery_feed_client import DiscoveryFeedClient, DiscoveryUnavailable


NOW = datetime(2026, 10, 26, 18, 0, tzinfo=timezone.utc)


def raw(stamp="2026-10-26T17:59:00Z"):
    return json.dumps({"schema": 1, "generated_at": stamp, "items": []}).encode()


class Response:
    status = 200

    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, _):
        return self.value


class DiscoveryFeedClientTests(unittest.TestCase):
    def client(self, root, opener):
        token = Path(root) / "token"
        token.write_text("a" * 48)
        return DiscoveryFeedClient("http://192.168.20.40:8788", token,
                                   Path(root) / "cache", opener)

    def test_live_feed_is_authenticated_validated_and_cached(self):
        calls = []

        def opener(request, timeout):
            calls.append((request, timeout))
            return Response(raw())

        with tempfile.TemporaryDirectory() as temporary:
            feed, source = self.client(temporary, opener).load("media", NOW)
            self.assertEqual((source, feed.items), ("live", ()))
            request, timeout = calls[0]
            self.assertEqual((request.full_url, timeout),
                             ("http://192.168.20.40:8788/v1/discovery/media", 10))
            self.assertEqual(request.get_header("Authorization"), "Bearer " + "a" * 48)
            cache = Path(temporary) / "cache/media.json"
            self.assertEqual(cache.read_bytes(), raw())
            self.assertEqual(cache.stat().st_mode & 0o777, 0o600)

    def test_transport_failure_uses_only_fresh_valid_cache(self):
        def unavailable(*_args, **_kwargs):
            raise OSError("offline")

        with tempfile.TemporaryDirectory() as temporary:
            client = self.client(temporary, unavailable)
            cache = Path(temporary) / "cache/media.json"
            cache.parent.mkdir()
            cache.write_bytes(raw())
            feed, source = client.load("media", NOW)
            self.assertEqual((source, feed.items), ("cache", ()))
            cache.write_bytes(raw("2026-10-25T01:00:00Z"))
            with self.assertRaisesRegex(DiscoveryUnavailable,
                                        "discovery-client-feed-unavailable"):
                client.load("media", NOW)

    def test_invalid_live_response_never_replaces_good_cache(self):
        with tempfile.TemporaryDirectory() as temporary:
            client = self.client(temporary, lambda *_args, **_kwargs: Response(b"{}"))
            cache = Path(temporary) / "cache/media.json"
            cache.parent.mkdir()
            cache.write_bytes(raw())
            feed, source = client.load("media", NOW)
            self.assertEqual(source, "cache")
            self.assertEqual(cache.read_bytes(), raw())
            self.assertEqual(feed.domain, "media")

    def test_domain_broker_and_token_boundaries_are_exact(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(DiscoveryUnavailable):
                DiscoveryFeedClient("https://recommendations.example", "token",
                                    temporary)
            client = self.client(temporary, lambda *_args, **_kwargs: Response(raw()))
            with self.assertRaises(DiscoveryUnavailable):
                client.load("video", NOW)
            Path(temporary, "token").write_text("short")
            with self.assertRaises(DiscoveryUnavailable):
                client.load("media", NOW)


if __name__ == "__main__":
    unittest.main()
