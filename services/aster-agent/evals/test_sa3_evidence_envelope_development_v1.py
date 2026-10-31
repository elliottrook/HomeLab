import json
import unittest
from pathlib import Path

from sa3_deterministic_evidence_envelope_v1 import project


FIXTURE = Path(__file__).with_name("sa3-evidence-envelope-development-v1.json")


class EvidenceEnvelopeDevelopmentTests(unittest.TestCase):
    def test_fresh_synthetic_development_set(self):
        value = json.loads(FIXTURE.read_text())
        self.assertEqual("synthetic-public-development", value["data_class"])
        self.assertEqual("none", value["authority"])
        self.assertEqual(12, len(value["cases"]))
        for case in value["cases"]:
            with self.subTest(case=case["id"]):
                result = project(case["input"], case["prose_draft"])
                expected = case["expected"]
                self.assertEqual(expected["outcome"], result["outcome"])
                self.assertEqual(expected["checks"], result["checks"])
                self.assertEqual(expected["prose_source"], result["prose_source"])
                self.assertEqual([], result["effects"])
                self.assertEqual("none", result["authority"])

    def test_development_set_is_not_the_spent_packet(self):
        value = json.loads(FIXTURE.read_text())
        self.assertFalse(any(case["id"].startswith("expanded-") for case in value["cases"]))
        self.assertNotIn("sa3-expanded-source-quality-v1", FIXTURE.read_text())


if __name__ == "__main__":
    unittest.main()
