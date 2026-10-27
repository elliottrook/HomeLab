import unittest

import nlu_e5_crossset_v1 as candidate


def label(name):
    return {"request_family": name, "sensitivity": "public", "capability_needs": ["facts.answer"],
            "ambiguity": "clear", "disposition": "route", "reason": "understood"}


class E5CrosssetTests(unittest.TestCase):
    def test_query_passage_vectors_are_directional(self):
        sets = {}
        for index in range(3):
            sets[f"v{index}"] = [
                {"query_vector": [1.0, 0.0], "passage_vector": [1.0, 0.0], "expected": label("general-answer")},
                {"query_vector": [0.0, 1.0], "passage_vector": [0.0, 1.0], "expected": label("external-research")},
            ]
        rows, similarities = candidate._prepare(sets)
        self.assertEqual(1.0, similarities[("v0", 0)][("v1", 0)])
        self.assertEqual(0.0, similarities[("v0", 0)][("v1", 1)])
        self.assertEqual(6, len(rows))

    def test_empty_set_fails_closed(self):
        with self.assertRaises(ValueError):
            candidate.evaluate_nested({"v1": [], "v2": [], "v3": []})


if __name__ == "__main__": unittest.main()
