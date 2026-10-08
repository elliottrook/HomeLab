import tempfile
import unittest
from pathlib import Path

from trakt_sources import collect_trakt_recommendations


class TraktSourceTests(unittest.TestCase):
    def test_collects_bounded_personal_movie_and_show_recommendations(self):
        calls = []

        def request(url, **kwargs):
            calls.append((url, kwargs))
            if url.endswith("/movies"):
                return ([{"title": "Arrival", "year": 2016,
                          "ids": {"trakt": 1, "tmdb": 329865}}], {})
            return ([{"show": {"title": "The Expanse", "ids": {"trakt": 2, "tmdb": 63639}},
                      "year": 2015}], {})

        with tempfile.TemporaryDirectory() as directory:
            token = Path(directory) / "token"
            client = Path(directory) / "client"
            token.write_text("access", encoding="utf-8")
            client.write_text("client", encoding="utf-8")
            result = collect_trakt_recommendations(
                request=request, access_token_path=str(token),
                client_id_path=str(client), limit=3)

        self.assertEqual([item["title"] for item in result], ["Arrival", "The Expanse"])
        self.assertEqual([item["media_type"] for item in result], ["movie", "tv"])
        self.assertEqual(result[0]["source_label"], "Trakt personal recommendations")
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][1]["params"], {"limit": 3, "extended": "full"})

    def test_skips_malformed_items(self):
        def request(_url, **_kwargs):
            return ([{"title": "Usable", "ids": {"trakt": 9}},
                     {}, {"title": "No IDs", "ids": {}}], {})

        with tempfile.TemporaryDirectory() as directory:
            token = Path(directory) / "token"
            client = Path(directory) / "client"
            token.write_text("access", encoding="utf-8")
            client.write_text("client", encoding="utf-8")
            result = collect_trakt_recommendations(
                request=request, access_token_path=str(token),
                client_id_path=str(client), limit=2)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["title"], "Usable")


if __name__ == "__main__":
    unittest.main()
