import copy
import json
import unittest

from sa3_evidence_matrix_candidate_j_public import FIXTURE, load_and_validate, validate


class CandidateJPublicTests(unittest.TestCase):
    def setUp(self):
        self.value = json.loads(FIXTURE.read_text())

    def test_exact_public_fixture_passes(self):
        result = load_and_validate()
        self.assertEqual(6, result["case_count"])
        self.assertEqual(2, result["plans"])
        self.assertEqual(4, result["abstentions"])
        self.assertEqual("none", result["authority"])

    def test_identity_expectation_and_composition_drift_fail(self):
        variants = []
        identity = copy.deepcopy(self.value); identity["candidate_alias"] = "candidate-i"
        variants.append(identity)
        expected = copy.deepcopy(self.value)
        expected["cases"][0]["expected"]["outcome"] = "clarify"
        variants.append(expected)
        short = copy.deepcopy(self.value); short["cases"].pop(); variants.append(short)
        duplicate = copy.deepcopy(self.value)
        duplicate["cases"][1]["id"] = duplicate["cases"][0]["id"]
        variants.append(duplicate)
        for value in variants:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate(value)


if __name__ == "__main__":
    unittest.main()
