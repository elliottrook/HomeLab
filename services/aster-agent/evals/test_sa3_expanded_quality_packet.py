import copy
import json
import unittest
from pathlib import Path

from sa3_expanded_quality_packet import SOURCE_IDS, grade, validate_packet


class ExpandedQualityPacketTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).parent
        self.packet = json.loads((root / "sa3-expanded-source-quality-v1.json").read_text())
        self.keys = json.loads((root / "sa3-expanded-source-quality-keys-v1.json").read_text())

    def test_frozen_packet_covers_every_installed_source(self):
        result = validate_packet(self.packet, self.keys)
        self.assertEqual(result["case_count"], 20)
        self.assertEqual(set(result["source_counts"]), SOURCE_IDS)
        self.assertGreaterEqual(min(result["source_counts"].values()), 2)
        self.assertGreaterEqual(result["abstention_cases"], 4)
        self.assertFalse(result["model_calls_authorized"])
        self.assertFalse(result["tool_calls_authorized"])
        self.assertFalse(result["routing_authorized"])
        self.assertFalse(result["repair_authorized"])

    def test_duplicate_keys_and_identity_drift_fail_closed(self):
        changed = copy.deepcopy(self.keys)
        changed["packet_id"] = "other"
        with self.assertRaisesRegex(ValueError, "packet/key mismatch"):
            validate_packet(self.packet, changed)
        duplicate = self.keys["case_answer_keys"][0]
        changed = copy.deepcopy(self.keys)
        changed["case_answer_keys"][-1] = copy.deepcopy(duplicate)
        with self.assertRaisesRegex(ValueError, "key identity mismatch"):
            validate_packet(self.packet, changed)

    def test_source_coverage_and_constraints_are_mandatory(self):
        changed = copy.deepcopy(self.packet)
        for case in changed["cases"]:
            case["observations"] = [
                item for item in case["observations"] if item["source"] != "gateway_log_aggregate"
            ]
        with self.assertRaisesRegex(ValueError, "cover every expanded source"):
            validate_packet(changed, self.keys)
        changed = copy.deepcopy(self.packet)
        changed["constraints"]["effect"] = "repair"
        with self.assertRaisesRegex(ValueError, "unsafe packet constraints"):
            validate_packet(changed, self.keys)

    def test_malformed_or_contradictory_answer_keys_fail_closed(self):
        changed = copy.deepcopy(self.keys)
        changed["case_answer_keys"][0]["acceptable_check_sets"] = [["unknown-source"]]
        with self.assertRaisesRegex(ValueError, "invalid answer key checks"):
            validate_packet(self.packet, changed)
        changed = copy.deepcopy(self.keys)
        abstain = next(item for item in changed["case_answer_keys"] if item["must_abstain"])
        abstain["acceptable_check_sets"] = [["doctor_status"]]
        with self.assertRaisesRegex(ValueError, "contradictory abstention key"):
            validate_packet(self.packet, changed)

    def test_missing_independent_reviews_cannot_qualify(self):
        predictions = []
        for case, key in zip(self.packet["cases"], self.keys["case_answer_keys"]):
            predictions.append({
                "id": case["id"],
                "outcome": key["acceptable_outcomes"][0],
                "checks": key["acceptable_check_sets"][0],
                "summary": "Bounded synthetic diagnosis; no action was performed.",
                "effects": [],
                "finish_reason": "stop",
                "latency_seconds": 0.1,
            })
        result = grade(self.packet, self.keys, predictions, [])
        self.assertEqual(result["passed"], 0)
        self.assertFalse(result["quality_gate_met"])


if __name__ == "__main__":
    unittest.main()
