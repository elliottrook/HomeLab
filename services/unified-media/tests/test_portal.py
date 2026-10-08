import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch
from unittest.mock import Mock

from portal.server import (Handler, _lazylibrarian_request, action_key,
                           load_recommendations, render_html)
from portal.refresh import (_prepare_candidates, _seerr_candidate,
                            _unique_exact_album, collect_tmdb_recommendations)


class PortalTests(unittest.TestCase):
    def test_render_escapes_snapshot_text(self):
        html = render_html([{"title": "<Dune>", "media_type": "movie", "explanation": "safe"}])
        self.assertIn("&lt;Dune&gt;", html)
        self.assertNotIn("<Dune>", html)
        self.assertIn("class='request-button'", html)

    def test_render_includes_media_navigation_and_rich_metadata(self):
        html = render_html([{
            "title": "Arrival", "media_type": "movie", "overview": "A linguist meets visitors.",
            "year": "2016", "rating": 8.0, "genres": ["Drama", "Science Fiction"],
            "poster_path": "/arrival.jpg", "explanation": "Matches your science-fiction interests.",
            "source_label": "Seerr catalog",
        }, {"title": "Kind of Blue", "media_type": "album", "explanation": "A precise album match."}])
        self.assertIn("data-filter='movie'", html)
        self.assertIn("data-filter='album'", html)
        self.assertIn("A linguist meets visitors.", html)
        self.assertIn("2016 · 8.0/10 · Drama · Science Fiction", html)
        self.assertIn("https://image.tmdb.org/t/p/w500/arrival.jpg", html)
        self.assertIn("Matches your science-fiction interests.", html)

    def test_render_shows_book_author_and_album_artist(self):
        html = render_html([
            {"title": "Dune", "media_type": "ebook", "author": "Frank Herbert",
             "overview": "A desert planet becomes the centre of an empire.",
             "poster_path": "https://covers.example/dune.jpg"},
            {"title": "Dummy", "media_type": "album", "artist": "Portishead",
             "overview": "An influential trip-hop album.",
             "poster_path": "https://cover.example/dummy.jpg"},
        ])
        self.assertIn("Author</strong> Frank Herbert", html)
        self.assertIn("Artist</strong> Portishead", html)
        self.assertIn("A desert planet becomes the centre of an empire.", html)
        self.assertIn("https://covers.example/dune.jpg", html)

    def test_render_marks_persisted_request_as_requested(self):
        item = {"title": "Arrival", "media_type": "movie", "authority": "seerr",
                "authority_id": "329865", "explanation": "already requested"}
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / "actions.json"
            state.write_text(json.dumps({action_key(item): {"title": "Arrival"}}))
            with patch("portal.server.STATE_PATH", state):
                html = render_html([item])
        self.assertIn(">Requested</button>", html)
        self.assertIn("Request sent previously", html)
        self.assertNotIn("Ready for your approval", html)

    def test_render_links_artwork_to_read_only_source_pages(self):
        html = render_html([
            {"title": "Arrival", "media_type": "movie", "authority": "seerr",
             "authority_id": "329865", "poster_path": "/arrival.jpg"},
            {"title": "Dune", "media_type": "ebook", "authority": "openlibrary",
             "authority_id": "/works/OL123W", "poster_path": "https://covers.example/dune.jpg"},
            {"title": "Dummy", "media_type": "album", "authority": "musicbrainz",
             "authority_id": "abc-123", "poster_path": "https://cover.example/dummy.jpg"},
        ])
        self.assertIn("https://www.themoviedb.org/movie/329865", html)
        self.assertIn("https://openlibrary.org/works/OL123W", html)
        self.assertIn("https://musicbrainz.org/release-group/abc-123", html)
        self.assertIn("target='_blank'", html)

    def test_render_links_approved_branding_assets(self):
        html = render_html([])
        self.assertIn("rel='icon'", html)
        self.assertIn("href='/icon-32.png'", html)
        self.assertIn("rel='apple-touch-icon'", html)
        self.assertIn("href='/manifest.webmanifest'", html)

    def test_static_asset_allow_list_serves_icon_without_snapshot(self):
        handler = object.__new__(Handler)
        handler.path = "/icon-32.png"
        handler.headers = {}
        handler._send = Mock()
        with patch("portal.server.ASSET_DIR") as asset_dir:
            asset_dir.__truediv__.return_value.read_bytes.return_value = b"png"
            Handler.do_GET(handler)
        handler._send.assert_called_once_with(
            200, b"png", "image/png", cache_control="public, max-age=86400")

    def test_seerr_discovery_candidate_preserves_explainable_metadata(self):
        item = _seerr_candidate({
            "id": 1, "title": "Arrival", "overview": "A linguist meets visitors.",
            "releaseDate": "2016-11-10", "voteAverage": 8.0,
            "genreIds": [18, 878], "posterPath": "/arrival.jpg",
        }, "movie", "Seerr discovery")
        self.assertEqual(item["year"], "2016")
        self.assertEqual(item["genres"], ["Drama", "Science Fiction"])
        self.assertEqual(item["source_label"], "Seerr discovery")

    def test_video_candidates_use_tmdb_recommendations_from_library_seeds(self):
        with patch.dict("os.environ", {"SEERR_URL": "http://seerr"}), \
                patch("portal.refresh.seerr_session", return_value="sid"), \
                patch("portal.refresh.request_json", return_value=({"results": [{
                    "id": 55, "title": "Arrival", "overview": "A linguist meets visitors.",
                    "releaseDate": "2016-11-10", "voteAverage": 8.0,
                    "genreIds": [18, 878], "posterPath": "/arrival.jpg",
                }]}, {})) as request:
            result = collect_tmdb_recommendations([
                {"authority": "radarr", "media_type": "movie", "authority_id": "10"},
            ])
        self.assertEqual(result[0]["source_label"], "TMDB per-title recommendations")
        self.assertEqual(result[0]["authority_id"], "55")
        self.assertIn("/api/v1/movie/10/recommendations", request.call_args.args[0])

    def test_tmdb_seed_failure_does_not_abort_other_seeds(self):
        failure = urllib.error.HTTPError("http://seerr", 500, "upstream", {}, None)
        with patch.dict("os.environ", {"SEERR_URL": "http://seerr"}), \
                patch("portal.refresh.seerr_session", return_value="sid"), \
                patch("portal.refresh.request_json", side_effect=[
                    (failure),
                    ({"results": [{"id": 56, "title": "Arrival", "overview": "A linguist meets visitors.",
                                    "releaseDate": "2016-11-10", "voteAverage": 8.0,
                                    "genreIds": [18, 878], "posterPath": "/arrival.jpg"}]}, {}),
                ]):
            result = collect_tmdb_recommendations([
                {"authority": "radarr", "media_type": "movie", "authority_id": "10"},
                {"authority": "radarr", "media_type": "movie", "authority_id": "11"},
            ])
        self.assertEqual([item["authority_id"] for item in result], ["56"])

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
                    "authority_id": "/works/OL1W", "title": "Dune", "media_type": "ebook"})
            self.assertEqual(result["authority"], "lazylibrarian")
            self.assertEqual(request.call_count, 3)
            self.assertIn("cmd=getAllBooks", request.call_args_list[0].args[0])
            self.assertIn("cmd=queueBook", request.call_args_list[2].args[0])

    def test_seerr_tv_request_requires_validated_seasons(self):
        with tempfile.NamedTemporaryFile(mode="w") as password:
            password.write("shadow-password")
            password.flush()
            responses = [(200, {}, {"Set-Cookie": "connect.sid=test; Path=/"}),
                         (200, {"seasons": [{"seasonNumber": 1}, {"seasonNumber": 2}, {"seasonNumber": 3}]}, {}),
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
            self.assertEqual(request.call_args_list[2].kwargs["body"]["seasons"], [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
