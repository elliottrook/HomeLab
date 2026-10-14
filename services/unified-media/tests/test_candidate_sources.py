import unittest

from candidate_sources import (collect_listenbrainz_albums, collect_musicbrainz,
                               collect_openlibrary, collect_openlibrary_author,
                               collect_openlibrary_subject)


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

    def test_openlibrary_author_discovery_uses_offset_and_exact_author(self):
        result = collect_openlibrary_author(
            "Frank Herbert", media_type="ebook", request=self.request, offset=6)
        self.assertEqual([item["title"] for item in result], ["Dune"])
        self.assertIn("author=Frank+Herbert", self.calls[0][0])
        self.assertIn("offset=6", self.calls[0][0])
        self.assertIn("recently enjoyed author", result[0]["signals"][0])

    def test_openlibrary_subject_discovery_normalizes_works(self):
        def subject_request(url, **kwargs):
            self.calls.append((url, kwargs))
            return {"works": [{"key": "/works/OL9W", "title": "A New World",
                                "cover_id": 99, "first_publish_year": 2024,
                                "authors": [{"name": "Writer"}]}]}, {}
        result = collect_openlibrary_subject(
            "Science Fiction", media_type="audiobook", request=subject_request, offset=12)
        self.assertEqual(result[0]["authority_id"], "/works/OL9W")
        self.assertIn("subjects/science_fiction.json", self.calls[0][0])
        self.assertIn("offset=12", self.calls[0][0])

    def test_musicbrainz_requires_exact_artist_album_identity(self):
        result = collect_musicbrainz("Miles Davis|Kind of Blue", request=self.request)
        self.assertEqual(result[0]["authority_id"], "mbid-1")
        self.assertEqual(result[0]["artist"], "Miles Davis")
        self.assertEqual(result[0]["poster_path"], "https://cover.test/front.jpg")
        self.assertIn("User-Agent", self.calls[0][1]["headers"])

    def test_musicbrainz_rejects_title_only_seed(self):
        self.assertEqual(collect_musicbrainz("Kind of Blue", request=self.request), [])
        self.assertEqual(self.calls, [])

    def test_listenbrainz_discovers_album_from_similar_artist(self):
        def discovery_request(url, **kwargs):
            self.calls.append((url, kwargs))
            if "/artist/?" in url:
                return {"artists": [{"id": "seed-mbid", "name": "Miles Davis", "score": 100}]}, {}
            if "api.listenbrainz.org" in url:
                return {"similar-mbid": [{"similar_artist_mbid": "similar-mbid",
                                           "similar_artist_name": "Nina Simone",
                                           "total_listen_count": 3000}]}, {}
            if "/release-group/?" in url:
                return {"release-groups": [{"id": "rg-1", "title": "Little Girl Blue",
                                             "first-release-date": "1959-02"}]}, {}
            return {"images": [{"front": True, "thumbnails": {"large": "https://cover.test/nina.jpg"}}]}, {}
        result = collect_listenbrainz_albums(
            "Miles Davis", request=discovery_request, pause=lambda _: None)
        self.assertEqual(result[0]["artist"], "Nina Simone")
        self.assertEqual(result[0]["authority_id"], "rg-1")
        self.assertEqual(result[0]["source_label"], "ListenBrainz similar-artist discovery")
        self.assertTrue(any("pop_begin=20" in url for url, _ in self.calls))


if __name__ == "__main__":
    unittest.main()
