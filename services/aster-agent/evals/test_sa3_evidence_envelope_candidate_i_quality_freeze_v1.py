import copy
import json
import unittest
from pathlib import Path

from sa3_evidence_envelope_candidate_i_quality_freeze_v1 import (
    FORBIDDEN_PACKET_SHA256, build, validate,
)


class CandidateIQualityFreezeTests(unittest.TestCase):
    def test_new_packet_and_keys_pass_frozen_boundary(self):
        packet, keys = build(); value = validate(packet, keys)
        self.assertEqual(20, value["cases"])
        self.assertEqual(6, value["abstentions"])
        self.assertNotIn(value["packet_sha256"], FORBIDDEN_PACKET_SHA256)
        self.assertFalse(value["model_calls_authorized"])

    def test_identifiers_and_control_fields_are_exact(self):
        packet, keys = build()
        for change in (
            ("data_class", "development"),
            ("constraints", {"authority": "granted"}),
        ):
            changed = copy.deepcopy(packet); changed[change[0]] = change[1]
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate(changed, keys)
        changed = copy.deepcopy(packet); changed["cases"][0]["id"] = "old-case"
        with self.assertRaises(ValueError): validate(changed, keys)

    def test_answer_key_and_coverage_drift_fail(self):
        packet, keys = build()
        changed = copy.deepcopy(keys)
        changed["case_answer_keys"][0]["expected_checks"] = []
        with self.assertRaises(ValueError): validate(packet, changed)
        changed = copy.deepcopy(packet)
        changed["cases"][0]["observations"] = []
        with self.assertRaises(ValueError): validate(changed, keys)

    def test_packet_is_not_evaluated_by_builder(self):
        packet, keys = build(); value = validate(packet, keys)
        self.assertNotIn("quality_gate_met", value)
        self.assertNotIn("predictions", value)
        self.assertNotIn("reviews", value)

    def test_repository_freeze_matches_deterministic_build(self):
        root = Path(__file__).parent
        packet, keys = build()
        self.assertEqual(packet, json.loads((root /
            "sa3-evidence-envelope-candidate-i-quality-v1.json").read_text()))
        self.assertEqual(keys, json.loads((root /
            "sa3-evidence-envelope-candidate-i-quality-keys-v1.json").read_text()))


if __name__ == "__main__": unittest.main()
