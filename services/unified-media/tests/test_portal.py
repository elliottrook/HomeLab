import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from portal.server import (_lazylibrarian_request, action_key,
                           load_recommendations, render_html)
from portal.refresh import _prepare_candidates, _unique_exact_album


class PortalTests(unittest.TestCase):
    def test_render_escapes_snapshot_text(self):
        html = render_html([{"title": "<Dune>", "media_type": "movie", "explanation": "safe"}])
        self.assertIn("&lt;Dune&gt;", html)
        self.assertNotIn("<Dune>", html)
        self.assertIn("class='request-button'", html)

    def test_render_disables_owned_candidate(self):
        html = render_html([{"title": "Dune", "media_type": "movie", "owned": True}])
        self.assertIn("disabled>Unavailable", html)
        self.assertNotIn("data-authority=", html)

    def test_candidate_preparation_filters_title_collisions(self):
        items = _prepare_candidates([
            {"authority": "seerr", "media_type": "movie", "authority_id": "1",
             "title": "Arrival", "score": 0.8},
            {"authority": "seerr", "media_type": "movie", "authority_id": "2",
             "title": "arrival", "score": 0.9},
            {"authority": "seerr", "media_type": "movie", "authority_id": "3",
             "title": "Dune", "score": 0.7},
        ])
        self.assertEqual([item["title"] for item in items], ["Dune"])

    def test_lidarr_album_identity_requires_artist_and_title(self):
        self.assertIsNone(_unique_exact_album([
            {"title": "Kind of Blue", "foreignAlbumId": "1",
             "artist": {"artistName": "Miles Davis"}},
            {"title": "KIND OF BLUE", "foreignAlbumId": "2",
             "artist": {"artistName": "Miles Davis"}},
        ], "Miles Davis", "Kind of Blue"))

    def test_missing_snapshot_is_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("portal.server.SNAPSHOT_PATH", Path(directory) / "missing.json"):
                self.assertEqual(load_recommendations(), [])

    def test_snapshot_requires_a_list(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as handle:
            json.dump({"bad": True}, handle)
            handle.flush()
            with patch("portal.server.SNAPSHOT_PATH", Path(handle.name)):
                with self.assertRaises(ValueError):
                    load_recommendations()

    def test_action_key_is_stable_and_scoped_to_authority_identity(self):
        item = {"authority": "seerr", "authority_id": "1"}
        self.assertEqual(action_key(item), action_key(dict(item)))
        self.assertNotEqual(action_key(item), action_key({"authority": "lidarr", "authority_id": "1"}))

    def test_lazylibrarian_revalidates_then_adds_and_queues(self):
        with tempfile.NamedTemporaryFile(mode="w") as token:
            token.write("shadow-key")
            token.flush()
            responses = [(200, [], {}), (200, True, {}), (200, "OK", {})]
            with patch.dict("os.environ", {
                    "LAZYLIBRARIAN_API_KEY_PATH": token.name,
                    "LAZYLIBRARIAN_URL": "http://lazy"}), \
                    patch("portal.server._request_json", side_effect=responses) as request:
                result = _lazylibrarian_request({
                    "authority_id": "OL1", "title": "Dune", "media_type": "ebook"})
            self.assertEqual(result["authority"], "lazylibrarian")
            self.assertEqual(request.call_count, 3)
            self.assertIn("cmd=getAllBooks", request.call_args_list[0].args[0])
            self.assertIn("cmd=queueBook", request.call_args_list[2].args[0])

    def test_seerr_tv_request_requires_validated_seasons(self):
        with tempfile.NamedTemporaryFile(mode="w") as password:
            password.write("shadow-password")
            password.flush()
            responses = [(200, {}, {"Set-Cookie": "connect.sid=test; Path=/"}),
                         (200, {"id": 123}, {})]
            with patch.dict("os.environ", {
                    "SEERR_PASSWORD_PATH": password.name,
                    "SEERR_EMAIL": "requester@example.invalid",
                    "SEERR_URL": "http://seerr"}), \
                    patch("portal.server._request_json", side_effect=responses) as request:
                from portal.server import _seerr_request
                result = _seerr_request({"media_type": "tv", "authority_id": "93740",
                                         "title": "Foundation", "seasons": [1, 2, 3]})
            self.assertEqual(result["request_id"], 123)
            self.assertEqual(request.call_args_list[1].kwargs["body"]["seasons"], [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
