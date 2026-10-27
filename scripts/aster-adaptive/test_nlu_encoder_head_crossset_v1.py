import unittest

import nlu_encoder_head_crossset_v1 as crossset


def label(name, disposition="route"):
    return {
        "request_family": "general-answer",
        "sensitivity": "public",
        "capability_needs": [],
        "ambiguity": "clear",
        "disposition": disposition,
        "reason": name,
    }


class DenseHeadCrosssetTests(unittest.TestCase):
    def test_nested_dense_head_passes_separable_sets(self):
        sets = {}
        for set_index in range(3):
            rows = []
            for index in range(10):
                expected = label("left") if index < 5 else label("right", "abstain")
                vector = [1.0, 0.0] if index < 5 else [0.0, 1.0]
                rows.append({"vector": vector, "expected": expected})
            sets[f"v{set_index + 1}"] = rows
        result = crossset.evaluate_nested(sets)
        self.assertTrue(result["nested_pass"])
        self.assertTrue(all(fold["status"] == "pass" for fold in result["folds"]))
        self.assertEqual("not-granted", result["authority"])

    def test_contradictory_sets_fail_closed(self):
        sets = {
            "v1": [{"vector": [1.0, 0.0], "expected": label("safe", "abstain")}] * 10,
            "v2": [{"vector": [1.0, 0.0], "expected": label("unsafe", "route")}] * 10,
            "v3": [{"vector": [1.0, 0.0], "expected": label("safe", "abstain")}] * 10,
        }
        result = crossset.evaluate_nested(sets)
        self.assertFalse(result["nested_pass"])


if __name__ == "__main__":
    unittest.main()
