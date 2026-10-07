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
                "first_sentence": "A desert planet becomes the centre of an empire.",
                "subject": ["Science fiction", "Political fiction"],
            }, {
                "key": "/works/OL2W", "title": "An Unrelated Book", "author_name": ["Someone"],
                "first_publish_year": 2020,
            }]}, {}
        if "coverartarchive.org" in url:
            return {"images": [{"front": True, "thumbnails": {"large": "https://cover.test/front.jpg"}}]}, {}
        return {"release-groups": [{
            "id": "mbid-1", "title": "Kind of Blue", "first-release-date": "1959-08-17",
            "artist-credit": [{"name": "Miles Davis"}], "score": 100,
        }]}, {}

    def test_openlibrary_normalizes_ebook_and_never_writes(self):
        result = collect_openlibrary("Dune", media_type="ebook", request=self.request)
        self.assertEqual(result[0]["authority_id"], "/works/OL1W")
        self.assertEqual(result[0]["author"], "Frank Herbert")
        self.assertEqual(result[0]["year"], "1965")
        self.assertEqual(result[0]["overview"], "A desert planet becomes the centre of an empire.")
        self.assertEqual(result[0]["genres"], ["Science fiction", "Political fiction"])
        self.assertEqual(len(result), 1)
        self.assertIn("fields=key%2Ctitle", self.calls[0][0])
        self.assertEqual(self.calls[0][1]["headers"]["Accept"], "application/json")

    def test_openlibrary_rejects_unsupported_media_type(self):
        self.assertEqual(collect_openlibrary("Dune", media_type="movie", request=self.request), [])
        self.assertEqual(self.calls, [])

    def test_openlibrary_skips_records_without_art(self):
        def no_art_request(url, **kwargs):
            return {"docs": [{"key": "/works/OL3W", "title": "Dune", "author_name": ["Frank Herbert"]}]}, {}
        self.assertEqual(collect_openlibrary("Dune", media_type="ebook", request=no_art_request), [])

    def test_musicbrainz_requires_exact_artist_album_identity(self):
        result = collect_musicbrainz("Miles Davis|Kind of Blue", request=self.request)
        self.assertEqual(result[0]["authority_id"], "mbid-1")
        self.assertEqual(result[0]["artist"], "Miles Davis")
        self.assertEqual(result[0]["poster_path"], "https://cover.test/front.jpg")
        self.assertIn("User-Agent", self.calls[0][1]["headers"])

    def test_musicbrainz_rejects_title_only_seed(self):
        self.assertEqual(collect_musicbrainz("Kind of Blue", request=self.request), [])
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
