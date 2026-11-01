import copy
import json
import unittest
from pathlib import Path

import sa3_evidence_envelope_quality_freeze_v1 as freeze


ROOT = Path(__file__).parent
PACKET = ROOT / "sa3-evidence-envelope-quality-v1.json"
KEYS = ROOT / "sa3-evidence-envelope-quality-keys-v1.json"


class EvidenceEnvelopeQualityFreezeTests(unittest.TestCase):
    def test_generator_reproduces_frozen_packet_and_keys(self):
        packet, keys = freeze.build()
        self.assertEqual(PACKET.read_bytes(), freeze.canonical(packet))
        self.assertEqual(KEYS.read_bytes(), freeze.canonical(keys))
        summary = freeze.validate(packet, keys)
        self.assertEqual(20, summary["cases"])
        self.assertGreaterEqual(summary["abstentions"], 6)
        self.assertFalse(summary["model_calls_authorized"])

    def test_key_cannot_change_deterministic_outcome_or_checks(self):
        packet, keys = freeze.build()
        for field, changed in (("expected_outcome", "clarify"), ("expected_checks", [])):
            variant = copy.deepcopy(keys)
            variant["case_answer_keys"][0][field] = changed
            with self.subTest(field=field), self.assertRaises(ValueError):
                freeze.validate(packet, variant)

    def test_packet_authority_coverage_and_identity_fail_closed(self):
        packet, keys = freeze.build()
        variants = []
        authority = copy.deepcopy(packet)
        authority["constraints"]["authority"] = "granted"
        variants.append(authority)
        duplicate = copy.deepcopy(packet)
        duplicate["cases"][1]["id"] = duplicate["cases"][0]["id"]
        variants.append(duplicate)
        short = copy.deepcopy(packet)
        short["cases"].pop()
        variants.append(short)
        for variant in variants:
            with self.subTest(), self.assertRaises(ValueError):
                freeze.validate(variant, keys)

    def test_frozen_json_is_unique_key_valid_json(self):
        self.assertEqual(freeze.build()[0], json.loads(PACKET.read_text()))
        self.assertEqual(freeze.build()[1], json.loads(KEYS.read_text()))


if __name__ == "__main__":
    unittest.main()
