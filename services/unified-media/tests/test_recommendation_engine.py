import unittest

from recommendation_engine import identity_key, rank_candidates


class RecommendationEngineTests(unittest.TestCase):
    def test_normalizes_cross_provider_identity(self):
        self.assertEqual(identity_key({"media_type": "Movie", "title": "Beyoncé: Homecoming"}),
                         ("movie", "beyonce homecoming"))

    def test_suppresses_owned_archived_and_ambiguous_items(self):
        candidates = [
            {"media_type": "movie", "authority": "seerr", "authority_id": "1", "title": "Owned", "score": 9},
            {"media_type": "movie", "authority": "seerr", "authority_id": "2", "title": "Archived", "score": 9},
            {"media_type": "album", "authority": "lidarr", "authority_id": "3", "title": "Same", "score": 9},
            {"media_type": "album", "authority": "musicbrainz", "authority_id": "4", "title": "Same", "score": 9},
            {"media_type": "movie", "authority": "seerr", "authority_id": "5", "title": "Keep", "score": 8.5},
        ]
        library = [
            {"media_type": "movie", "title": "Owned", "archived": False},
            {"media_type": "movie", "title": "Archived", "archived": True},
        ]
        result = rank_candidates(candidates, library=library)
        self.assertEqual([item["title"] for item in result], ["Keep"])
        self.assertIn("active or archive", result[0]["explanation"])

    def test_history_genre_signal_is_explicit_and_deterministic(self):
        result = rank_candidates([
            {"media_type": "audiobook", "authority": "openlibrary", "authority_id": "1",
             "title": "A New Mystery", "score": 0.8, "genres": ["Mystery"]},
        ], history=[{"title": "Previous", "genres": ["Mystery"]}])
        self.assertEqual(len(result), 1)
        self.assertIn("matches genres", result[0]["explanation"])


if __name__ == "__main__":
    unittest.main()
