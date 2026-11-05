import copy
import unittest

from sa3_evidence_matrix_candidate_j_quality_freeze import build, validate


class CandidateJQualityFreezeTests(unittest.TestCase):
    def test_distinct_untouched_boundary(self):
        packet, keys = build(); result = validate(packet, keys)
        self.assertEqual(20, result["cases"])
        self.assertEqual(14, result["model_requests"])
        self.assertEqual(6, result["mandatory_abstentions"])
        self.assertFalse(result["model_calls_authorized"])

    def test_control_drift_fails_closed(self):
        packet, keys = build(); changed = copy.deepcopy(packet)
        changed["constraints"]["authority"] = "granted"
        with self.assertRaises(ValueError): validate(changed, keys)

    def test_key_drift_fails_closed(self):
        packet, keys = build(); changed = copy.deepcopy(keys)
        changed["case_answer_keys"][0]["expected_hypothesis_ids"] = ["foreign"]
        with self.assertRaises(ValueError): validate(packet, changed)

    def test_builder_does_not_evaluate_candidate(self):
        packet, keys = build(); result = validate(packet, keys)
        self.assertNotIn("quality_decision", result)
        self.assertNotIn("predictions", result)
        self.assertNotIn("reviews", result)

if __name__ == "__main__": unittest.main()
