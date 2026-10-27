import unittest

import nlu_linear_head_v1 as head


def label(reason, disposition="route"):
    return {"request_family": "general-answer", "sensitivity": "public",
            "capability_needs": ["facts.answer"] if disposition == "route" else [],
            "ambiguity": "clear", "disposition": disposition, "reason": reason}


class LinearHeadTests(unittest.TestCase):
    def test_learns_complete_reviewed_labels_without_authority(self):
        model = head.fit([([1.0, 0.0], label("left")),
                          ([0.9, 0.1], label("left")),
                          ([0.0, 1.0], label("right", "abstain")),
                          ([0.1, 0.9], label("right", "abstain"))])
        left = head.propose([1.0, 0.0], model)
        right = head.propose([0.0, 1.0], model)
        self.assertEqual("left", left["proposal"]["reason"])
        self.assertEqual("right", right["proposal"]["reason"])
        self.assertGreater(left["route_score"], 0)
        self.assertEqual(0.0, right["route_score"])
        self.assertEqual("not-granted", left["authority"])
        self.assertEqual("off", left["automatic_routing"])

    def test_training_is_deterministic(self):
        rows = [([1.0, 0.0], label("left")),
                ([0.0, 1.0], label("right", "abstain"))]
        self.assertEqual(head.fit(rows), head.fit(rows))

    def test_rejects_invalid_vectors_and_single_label(self):
        with self.assertRaises(ValueError):
            head.fit([([1.0, 0.0], label("only"))])
        model = head.fit([([1.0, 0.0], label("left")),
                          ([0.0, 1.0], label("right", "abstain"))])
        for vector in ([1.0], [0.0, 0.0], [float("nan"), 0.0]):
            with self.subTest(vector=vector), self.assertRaises(ValueError):
                head.propose(vector, model)


if __name__ == "__main__":
    unittest.main()
