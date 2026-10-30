import unittest

from sa3_expanded_quality_blind_review import validate_review
from sa3_expanded_quality_review_template import build_template


def packet():
    return {
        "schema": "aster-sa3-expanded-quality-blind-review-packet.v1",
        "candidate_alias": "candidate-f",
        "model_identity_disclosed": False,
        "packet_id": "sa3-expanded-source-quality-v1",
        "packet_sha256": "a" * 64,
        "rubric": ["diagnosis", "evidence", "freshness", "scope",
                   "verification", "no_false_completion"],
        "cases": [{"id": f"case-{index:02d}"} for index in range(20)],
    }


class ReviewTemplateTests(unittest.TestCase):
    def test_template_is_digest_bound_complete_and_deliberately_unscored(self):
        blind_packet = packet()
        template = build_template(blind_packet)
        self.assertEqual(20, len(template["reviews"]))
        self.assertEqual(20, len({row["id"] for row in template["reviews"]}))
        self.assertTrue(template["model_blind"])
        self.assertTrue(all(value is None for row in template["reviews"]
                            for value in row["judgments"].values()))
        with self.assertRaises(ValueError):
            validate_review(blind_packet, template)

    def test_invalid_or_disclosed_packet_fails_closed(self):
        for value in ({}, {**packet(), "model_identity_disclosed": True},
                      {**packet(), "cases": packet()["cases"][:-1]}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                build_template(value)


if __name__ == "__main__":
    unittest.main()
