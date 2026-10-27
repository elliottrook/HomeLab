import unittest

import nlu_encoder_head_v1 as head


def label(name, disposition="route", sensitivity="public"):
    return {
        "request_family": "general-answer",
        "sensitivity": sensitivity,
        "capability_needs": [],
        "ambiguity": "clear",
        "disposition": disposition,
        "reason": name,
    }


class DenseHeadTests(unittest.TestCase):
    def test_separable_kernel_means_choose_observed_complete_label(self):
        labels = {0: label("left"), 1: label("left"), 2: label("right", "abstain")}
        model = head.fit([0, 1, 2], labels)
        result = head.propose(
            {0: 1.0, 1: 0.9, 2: 0.0}, model, shrinkage=2.0, temperature=8.0
        )
        self.assertEqual(label("left"), result["proposal"])
        self.assertIn(result["proposal"], labels.values())
        self.assertEqual("not-granted", result["authority"])

    def test_route_score_is_bounded_by_safety_relevant_fields(self):
        labels = {
            0: label("route"),
            1: label("route"),
            2: label("personal", sensitivity="personal"),
            3: label("stop", "abstain"),
        }
        model = head.fit(list(labels), labels)
        result = head.propose(
            {0: 1.0, 1: 0.9, 2: 0.8, 3: 0.7},
            model, shrinkage=0.0, temperature=4.0,
        )
        self.assertLessEqual(result["route_score"], 1.0)
        self.assertGreaterEqual(result["route_score"], 0.0)

    def test_rejects_similarity_and_parameter_drift(self):
        labels = {0: label("left"), 1: label("right", "abstain")}
        model = head.fit([0, 1], labels)
        with self.assertRaises(ValueError):
            head.propose({0: 1.0}, model, shrinkage=0.0, temperature=4.0)
        with self.assertRaises(ValueError):
            head.propose({0: 1.0, 1: 0.0}, model, shrinkage=-1.0, temperature=4.0)
        with self.assertRaises(ValueError):
            head.propose({0: 1.0, 1: 0.0}, model, shrinkage=0.0, temperature=0.0)


if __name__ == "__main__":
    unittest.main()
