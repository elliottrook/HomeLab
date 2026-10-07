import unittest

from candidate_sources import collect_musicbrainz, collect_openlibrary


class CandidateSourceTests(unittest.TestCase):
    def setUp(self):
        self.calls = []

    def request(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if "openlibrary.org" in url:
            return {"docs": [{
                "key": "/works/OL1W", "title": "Dune", "author_name": ["Frank Herbert"],
                "first_publish_year": 1965, "cover_i": 123, "ratings_average": 4.2,
            }]}, {}
        return {"release-groups": [{
            "id": "mbid-1", "title": "Kind of Blue", "first-release-date": "1959-08-17",
            "artist-credit": [{"name": "Miles Davis"}], "score": 100,
        }]}, {}

    def test_openlibrary_normalizes_ebook_and_never_writes(self):
        result = collect_openlibrary("science fiction", media_type="ebook", request=self.request)
        self.assertEqual(result[0]["authority_id"], "/works/OL1W")
        self.assertEqual(result[0]["author"], "Frank Herbert")
        self.assertEqual(result[0]["year"], "1965")
        self.assertIn("fields=key%2Ctitle", self.calls[0][0])
        self.assertEqual(self.calls[0][1]["headers"]["Accept"], "application/json")

    def test_openlibrary_rejects_unsupported_media_type(self):
        self.assertEqual(collect_openlibrary("Dune", media_type="movie", request=self.request), [])
        self.assertEqual(self.calls, [])

    def test_musicbrainz_requires_exact_artist_album_identity(self):
        result = collect_musicbrainz("Miles Davis|Kind of Blue", request=self.request)
        self.assertEqual(result[0]["authority_id"], "mbid-1")
        self.assertEqual(result[0]["artist"], "Miles Davis")
        self.assertIn("User-Agent", self.calls[0][1]["headers"])

    def test_musicbrainz_rejects_title_only_seed(self):
        self.assertEqual(collect_musicbrainz("Kind of Blue", request=self.request), [])
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
