import unittest

import nlu_e5_augmented_public_gate_v1 as gate


class AugmentedE5PublicGateTests(unittest.TestCase):
    def test_public_fixture_has_reviewed_complete_labels(self):
        self.assertEqual(40, len(gate.SUPPORT))
        self.assertEqual(24, len(gate.EVALUATION))
        for text, expected in gate.SUPPORT + gate.EVALUATION:
            self.assertTrue(text.startswith(("query: ", "passage: ")))
            gate.boundary._label_key(expected)

    def test_separable_vectors_pass_without_authority(self):
        labels = sorted({gate.boundary._label_key(expected)
                         for _, expected in gate.SUPPORT}, key=repr)
        basis = {label: [1.0 if i == index else 0.0 for i in range(len(labels))]
                 for index, label in enumerate(labels)}
        support = [basis[gate.boundary._label_key(expected)]
                   for _, expected in gate.SUPPORT]
        evaluation = [basis[gate.boundary._label_key(expected)]
                      for _, expected in gate.EVALUATION]
        result = gate.evaluate(support, evaluation)
        self.assertTrue(result["pass"])
        self.assertEqual(24, result["exact"])
        self.assertEqual([], result["failed_indices"])
        self.assertEqual("not-granted", result["authority"])
        self.assertEqual("off", result["automatic_routing"])

    def test_count_and_dimension_drift_fail_closed(self):
        with self.assertRaises(ValueError):
            gate.evaluate([], [])
        support = [[1.0, 0.0] for _ in gate.SUPPORT]
        evaluation = [[1.0] for _ in gate.EVALUATION]
        with self.assertRaises(ValueError):
            gate.evaluate(support, evaluation)


if __name__ == "__main__":
    unittest.main()
