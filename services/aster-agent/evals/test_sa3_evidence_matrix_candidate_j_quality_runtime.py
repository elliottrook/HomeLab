import copy
import unittest

from sa3_evidence_matrix_candidate_j_quality_freeze import build
from sa3_evidence_matrix_candidate_j_quality_runtime import validate_packet


class CandidateJQualityRuntimeTests(unittest.TestCase):
    def test_exact_packet_validates_without_keys(self):
        packet, _keys = build()
        result = validate_packet(packet)
        self.assertEqual(14, result["model_requests"])
        self.assertEqual(6, result["abstentions"])

    def test_packet_content_drift_fails_closed(self):
        packet, _keys = build(); changed = copy.deepcopy(packet)
        changed["cases"][0]["prompt"] += " changed"
        with self.assertRaises(ValueError):
            validate_packet(changed)

    def test_runtime_module_has_no_answer_key_dependency(self):
        import sa3_evidence_matrix_candidate_j_quality_runtime as runtime
        self.assertFalse(hasattr(runtime, "build"))
        self.assertFalse(hasattr(runtime, "validate"))


if __name__ == "__main__": unittest.main()
