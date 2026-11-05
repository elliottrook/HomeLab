from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from auth import AuthenticationError, TokenRegistry
from audiobookshelf import AudiobookshelfCatalogue


class Response:
    def __init__(self, value):
        self.data = json.dumps(value).encode()
        self.status = 200
        self.headers = {"Content-Length": str(len(self.data))}
    def __enter__(self): return self
    def __exit__(self, *_args): return False
    def read(self, size): return self.data[:size]


class AuthCatalogueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def private(self, name, value):
        path = self.root / name
        path.write_text(value)
        path.chmod(0o600)
        return path

    def test_hash_only_registry_authenticates_exact_token(self):
        token = "s" * 48
        registry = self.private("clients.json", json.dumps({
            "schema": "aster-podcast-client-tokens.v1", "clients": [{
                "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
                "client_id": "AsterTV-Jen", "profile_id": "jason", "enabled": True,
            }]}
        ))
        auth = TokenRegistry(registry)
        self.assertEqual(auth.authenticate("Bearer " + token).profile_id, "jason")
        with self.assertRaises(AuthenticationError):
            auth.authenticate("Bearer " + "x" * 48)

    def test_catalogue_uses_singular_live_search_route_and_hashes_duplicates(self):
        key = self.private("abs.key", "k" * 48)
        seen = []
        def opener(request, timeout):
            seen.append((request.full_url, request.headers.get("Authorization"), timeout))
            if "/api/search/podcast?" in request.full_url:
                return Response([{"id": 123, "feedUrl": "https://feeds.example/show.xml",
                    "title": "Show", "artistName": "Artist",
                    "cover": "https://images.example/show.jpg"}])
            if request.full_url.endswith("/api/libraries"):
                return Response({"libraries": [{"id": "lib_p", "mediaType": "podcast"}]})
            return Response({"results": [{"media": {"metadata": {
                "feedUrl": "https://feeds.example/show.xml", "itunesId": 123}}}]})
        catalogue = AudiobookshelfCatalogue("https://abs.example", key, opener=opener)
        result = catalogue.search("science", "ca")
        feeds, providers = catalogue.identities()
        self.assertEqual(result[0]["provider_id"], "123")
        self.assertEqual(providers, {"123"})
        self.assertEqual(len(feeds), 1)
        self.assertIn("/api/search/podcast?term=science&country=ca", seen[0][0])
        self.assertTrue(all(value[1] == "Bearer " + "k" * 48 for value in seen))


if __name__ == "__main__":
    unittest.main()
