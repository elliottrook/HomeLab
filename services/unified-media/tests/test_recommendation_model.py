import unittest

from recommendation_model import Recommendation, explain, rank_recommendations


class RecommendationModelTests(unittest.TestCase):
    def test_rank_is_deterministic_and_filters_unsafe_candidates(self):
        items = [
            Recommendation("movie", "seerr", "2", "B", 0.8),
            Recommendation("movie", "seerr", "1", "A", 0.8),
            Recommendation("movie", "seerr", "3", "Owned", 0.99, owned=True),
            Recommendation("movie", "seerr", "4", "Archive", 0.99, archived=True),
            Recommendation("movie", "seerr", "5", "Ambiguous", 0.99, match_count=2),
        ]
        self.assertEqual([x.title for x in rank_recommendations(items)], ["A", "B"])

    def test_limit_and_explanation(self):
        item = Recommendation("album", "lidarr", "1", "Dune", 1.0,
                              signals=("you played electronic music", "it is not in the library"))
        self.assertEqual(rank_recommendations([item], limit=0), [])
        self.assertEqual(explain(item), "Recommended because you played electronic music; it is not in the library.")


if __name__ == "__main__":
    unittest.main()
