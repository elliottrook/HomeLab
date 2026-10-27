import unittest

import nlu_e5_public_gate_v1 as gate


class E5PublicGateTests(unittest.TestCase):
    def test_fixture_is_bounded_and_public(self):
        self.assertEqual(20, len(gate.SUPPORT))
        self.assertEqual(24, len(gate.EVALUATION))
        for text, expected in gate.SUPPORT + gate.EVALUATION:
            self.assertTrue(text.startswith(("query: ", "passage: ")))
            gate.candidate._label_key(expected)

    def test_exact_vectors_pass_without_authority(self):
        support = [[1.0 if i == j else 0.0 for i in range(20)] for j in range(20)]
        vectors = []
        for index in range(24):
            expected = gate.EVALUATION[index][1]
            match = next(i for i, (_, label) in enumerate(gate.SUPPORT) if label == expected)
            vectors.append(support[match])
        result = gate.evaluate(support, vectors)
        self.assertTrue(result["pass"])
        self.assertEqual("not-granted", result["authority"])
        self.assertEqual("off", result["automatic_routing"])

    def test_dimension_mismatch_fails_closed(self):
        support = [[1.0, 0.0] for _ in gate.SUPPORT]
        vectors = [[1.0] for _ in gate.EVALUATION]
        with self.assertRaises(ValueError):
            gate.evaluate(support, vectors)


if __name__ == "__main__":
    unittest.main()
