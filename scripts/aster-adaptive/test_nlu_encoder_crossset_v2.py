import unittest

import nlu_encoder_crossset_v2 as crossset


def label(name, disposition="route"):
    return {
        "request_family": "general-answer",
        "sensitivity": "public",
        "capability_needs": [],
        "ambiguity": "clear",
        "disposition": disposition,
        "reason": name,
    }


def row(vector, expected):
    return {"vector": vector, "expected": expected}


class EncoderCrosssetV2Tests(unittest.TestCase):
    def test_nested_selection_passes_separable_sets_without_authority(self):
        sets = {}
        for set_index in range(3):
            rows = []
            for index in range(10):
                if index < 5:
                    rows.append(row([1.0, 0.0], label("left")))
                else:
                    rows.append(row([0.0, 1.0], label("right", "abstain")))
            sets[f"v{set_index + 1}"] = rows
        result = crossset.evaluate_nested(sets)
        self.assertTrue(result["nested_pass"])
        self.assertEqual("not-granted", result["authority"])
        self.assertEqual("off", result["automatic_routing"])
        self.assertTrue(all(fold["status"] == "pass" for fold in result["folds"]))

    def test_no_safe_threshold_fails_closed(self):
        safe = label("safe", "abstain")
        unsafe = label("unsafe", "route")
        sets = {
            "v1": [row([1.0, 0.0], safe)] * 10,
            "v2": [row([1.0, 0.0], unsafe)] * 10,
            "v3": [row([1.0, 0.0], safe)] * 10,
        }
        result = crossset.evaluate_nested(sets)
        self.assertFalse(result["nested_pass"])
        self.assertTrue(any(fold["status"] != "pass" for fold in result["folds"]))

    def test_threshold_selection_counts_nonroute_decisions(self):
        rows = []
        for index in range(10):
            rows.append({
                "decision_score": 0.9,
                "route_score": 0.0,
                "proposes_route": False,
                "accepted_decision_correct": index < 9,
                "privacy_underclassified_if_routed": False,
                "unsafe_false_route_if_routed": False,
            })
        selected = crossset.select_thresholds(rows)
        self.assertEqual(1.0, selected["metrics"]["decision_coverage"])
        self.assertEqual(0, selected["metrics"]["routed"])

    def test_empty_set_is_rejected(self):
        with self.assertRaises(ValueError):
            crossset.evaluate_nested({"v1": [], "v2": [], "v3": []})


if __name__ == "__main__":
    unittest.main()
