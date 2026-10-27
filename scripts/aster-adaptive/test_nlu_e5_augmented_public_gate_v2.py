import unittest

import nlu_e5_augmented_public_gate_v2 as gate


class CorrectedAugmentedE5PublicGateTests(unittest.TestCase):
    def test_correction_is_public_bounded_and_complete(self):
        self.assertEqual(52, len(gate.SUPPORT))
        self.assertEqual(12, len(gate.CORRECTION))
        for text, expected in gate.CORRECTION:
            self.assertTrue(text.startswith("passage: "))
            gate.boundary._label_key(expected)

    def test_separable_vectors_pass_fixed_gate(self):
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

    def test_count_drift_fails_closed(self):
        with self.assertRaises(ValueError):
            gate.evaluate([], [])


if __name__ == "__main__":
    unittest.main()
