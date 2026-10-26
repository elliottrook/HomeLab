import unittest

from spotify_oauth import authorization_url, playlist_items


class SpotifyOAuthTests(unittest.TestCase):
    def test_authorization_url_uses_read_only_playlist_scopes(self):
        url, state, verifier = authorization_url(
            "client", "https://example.test/callback", "state")
        self.assertEqual(state, "state")
        self.assertTrue(verifier)
        self.assertIn("playlist-read-private", url)
        self.assertIn("playlist-read-collaborative", url)
        self.assertIn("code_challenge_method=S256", url)
        self.assertNotIn("playlist-modify", url)

    def test_playlist_items_paginates_and_ignores_local_tracks(self):
        responses = iter([
            {"items": [{"track": {"id": "one", "name": "One"}},
                       {"track": {"id": None, "is_local": True}}], "next": "next"},
            {"items": [{"track": {"id": "two", "name": "Two"}}], "next": None},
        ])
        import spotify_oauth
        original = spotify_oauth.api_get
        spotify_oauth.api_get = lambda token, path, query=None: next(responses)
        try:
            self.assertEqual([item["id"] for item in playlist_items("token", "mix")],
                             ["one", "two"])
        finally:
            spotify_oauth.api_get = original


if __name__ == "__main__":
    unittest.main()
