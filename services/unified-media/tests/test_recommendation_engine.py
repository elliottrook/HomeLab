import unittest

from recommendation_engine import (identity_key, rank_candidates,
                                   select_with_exposure_cooldown)


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

    def test_result_cap_balances_available_media_types(self):
        candidates = []
        for media_type in ("movie", "album", "ebook", "audiobook"):
            for index in range(6):
                candidates.append({
                    "media_type": media_type, "authority": media_type,
                    "authority_id": f"{media_type}-{index}",
                    "title": f"{media_type} {index}", "score": 10 - index,
                })
        result = rank_candidates(candidates, limit=8)
        self.assertEqual([item["media_type"] for item in result],
                         ["album", "audiobook", "ebook", "movie"] * 2)

    def test_exposure_cooldown_rotates_candidates_before_repeating(self):
        candidates = [{"media_type": "ebook", "authority": "openlibrary",
                       "authority_id": str(index), "title": f"Book {index}"}
                      for index in range(10)]
        first, ledger = select_with_exposure_cooldown(
            candidates, exposures={}, now=1000000, per_media_limit=4, limit=4)
        second, _ = select_with_exposure_cooldown(
            candidates, exposures=ledger, now=1000000 + 86400,
            per_media_limit=4, limit=4)
        self.assertEqual([item["authority_id"] for item in first], ["0", "1", "2", "3"])
        self.assertEqual([item["authority_id"] for item in second], ["4", "5", "6", "7"])

    def test_exposure_cooldown_falls_back_to_oldest_recent_item(self):
        candidates = [{"media_type": "album", "authority": "musicbrainz",
                       "authority_id": str(index), "title": f"Album {index}"}
                      for index in range(2)]
        result, _ = select_with_exposure_cooldown(
            candidates, exposures={"musicbrainz|0": 90, "musicbrainz|1": 80},
            now=100, cooldown_seconds=1000, per_media_limit=1, limit=1)
        self.assertEqual(result[0]["authority_id"], "1")


if __name__ == "__main__":
    unittest.main()
