import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from playlist_bridge import Api, Track, match, normalized, read_playlist, read_spotify_url, replace_playlist, request_album, wait_decision


class FakeApi:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def request(self, method, path, query=None, body=None):
        self.calls.append((method, path, query, body))
        return next(self.responses)


class ErrorApi:
    def request(self, method, path, query=None, body=None):
        raise RuntimeError("GET /api/v1/album/lookup: HTTP 503: unavailable")


class FakeResponse:
    def __init__(self, body):
        self.body = body.encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self):
        return self.body


class PlaylistBridgeTests(unittest.TestCase):
    def test_csv_common_headers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "Road Trip.csv"
            path.write_text("Track Name,Artist Name,Album Name,ISRC\nSong,The Band,Record,ABC1\n")
            name, tracks = read_playlist(path)
        self.assertEqual(name, "Road Trip")
        self.assertEqual(tracks, [Track("Song", "The Band", "Record", "ABC1")])

    def test_spotify_export(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "Playlist1.json"
            path.write_text(json.dumps({"playlists": [{"name": "Mix", "items": [
                {"track": {"trackName": "Song", "artistName": "Artist", "albumName": "Album"}}
            ]}]}))
            name, tracks = read_playlist(path)
        self.assertEqual((name, tracks[0].title), ("Mix", "Song"))

    def test_match_ignores_remaster_suffix(self):
        item = {"Id": "1", "Name": "Song - 2011 Remastered", "Artists": ["Beyoncé"], "Album": "Hits"}
        self.assertEqual(match(Track("Song", "Beyonce", "Hits"), [item])["Id"], "1")

    def test_normalized(self):
        self.assertEqual(normalized("Beyoncé!"), "beyonce")

    def test_normalized_removes_feature_credit(self):
        self.assertEqual(normalized("Godzilla (feat. Juice WRLD)"), "godzilla")

    def test_spotify_url_reads_next_data(self):
        state = {"props": {"pageProps": {"state": {"data": {"entity": {
            "name": "Public Mix", "trackList": [
                {"title": "Song", "subtitle": "Artist,\u00a0Guest"}]}}}}}}
        html = '<script id="__NEXT_DATA__" type="application/json">' + json.dumps(state) + '</script>'
        opener = lambda request, timeout: FakeResponse(html)
        name, tracks = read_spotify_url("https://open.spotify.com/playlist/abc123?si=x", opener)
        self.assertEqual(name, "Public Mix")
        self.assertEqual(tracks, [Track("Song", "Artist, Guest")])

    def test_collaborating_artist_can_match(self):
        item = {"Id": "1", "Name": "Song", "Artists": ["Guest"], "Album": ""}
        self.assertEqual(match(Track("Song", "Artist, Guest"), [item])["Id"], "1")

    def test_missing_album_metadata_never_executes_lidarr_request(self):
        api = FakeApi([])
        result = request_album(api, Track("Song", "Artist"), {}, True)
        self.assertEqual(result["status"], "needs-album-metadata")
        self.assertEqual(api.calls, [])

    def test_lidarr_lookup_error_is_reported_without_stopping_run(self):
        result = request_album(ErrorApi(), Track("Song", "Artist", "Album"), {}, False)
        self.assertEqual(result["status"], "lookup-error")
        self.assertIn("HTTP 503", result["error"])

    def test_lidarr_lookup_uses_primary_artist_only(self):
        api = FakeApi([[]])
        request_album(api, Track("Song", "Artist, Guest", "Album"), {}, False)
        self.assertEqual(api.calls[0][2], {"term": "Artist Album"})

    def test_existing_album_is_searched_without_readding(self):
        lookup = {"id": 42, "title": "Album", "artist": {"artistName": "Artist"}}
        api = FakeApi([[lookup], {"id": 100}])
        result = request_album(api, Track("Song", "Artist", "Album"), {}, True)
        self.assertEqual(result["status"], "existing-search-queued")
        self.assertEqual(api.calls[1][1], "/api/v1/command")

    def test_partial_playlist_wait_expires_after_24_hours(self):
        now = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
        tracks = [Track("Song", "Artist")]
        state = {"playlists": {}}
        expired, _ = wait_decision(state, "Mix", tracks, 1, 24, now, True)
        self.assertFalse(expired)
        expired, report = wait_decision(state, "Mix", tracks, 1, 24,
                                        now + timedelta(hours=24, seconds=1), True)
        self.assertTrue(expired)
        self.assertEqual(report["status"], "deadline-expired")

    def test_jellyfin_uses_query_auth(self):
        api = Api("http://jellyfin", "secret", auth="query")
        self.assertEqual(api.auth, "query")

    def test_existing_playlist_is_replaced_create_first(self):
        api = FakeApi([{"Items": [{"Id": "playlist-1", "Name": "Mix"}]},
                       {"Id": "playlist-2"}, None])
        result = replace_playlist(api, "user-1", "Mix", ["song-1", "song-2"], True)
        self.assertEqual(result["status"], "replaced")
        self.assertEqual(api.calls[1][1], "/Playlists")
        self.assertEqual(api.calls[2][0:2], ("DELETE", "/Items/playlist-1"))

    def test_new_playlist_is_created_directly(self):
        api = FakeApi([{"Items": []}, {"Id": "playlist-2"}])
        result = replace_playlist(api, "user-1", "Mix", ["song-1"], True)
        self.assertEqual(result["status"], "created")
        self.assertEqual(api.calls[1][1], "/Playlists")

    def test_lidarr_album_payload_configures_nested_artist(self):
        lookup = {"title": "Album", "foreignAlbumId": "release-group", "artist": {
            "artistName": "Artist", "foreignArtistId": "artist-id"}}
        api = FakeApi([[lookup], {"id": 42, "title": "Album"}, {"id": 99}])
        result = request_album(api, Track("Song", "Artist", "Album"), {
            "root_folder": "/music", "quality_profile_id": 2, "metadata_profile_id": 3}, True)
        self.assertEqual(result["status"], "added-search-queued")
        payload = api.calls[1][3]
        self.assertEqual(payload["artist"]["rootFolderPath"], "/music")
        self.assertEqual(payload["artist"]["qualityProfileId"], 2)
        self.assertEqual(api.calls[2], ("POST", "/api/v1/command", None,
                                        {"name": "AlbumSearch", "albumIds": [42]}))


if __name__ == "__main__":
    unittest.main()
