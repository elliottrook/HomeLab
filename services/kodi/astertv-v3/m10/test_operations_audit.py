import importlib.util
import json
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SPEC = importlib.util.spec_from_file_location("astertv_m10_operations", HERE / "audit_operations.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)
OBSERVATION = ROOT / "docs/projects/evidence/AsterTV-v3-M10-operations-observation-2026-11-05.json"


class OperationsAuditTests(unittest.TestCase):
    def test_current_observation_fails_closed_with_named_gaps(self):
        result = AUDIT.audit(json.loads(OBSERVATION.read_text()))
        self.assertEqual(result["outcome"], "attention")
        self.assertIn("doctor:astertv-bedroom:unobserved", result["gaps"])
        self.assertIn("doctor:astertv-family:unobserved", result["gaps"])
        self.assertNotIn("doctor:astertv-jen:drift", result["gaps"])
        self.assertEqual(result["gap_count"], 12)
        self.assertIn("wiki:live-astertv-department-absent", result["gaps"])
        self.assertIn("mirror:astertv-derived-source-absent", result["gaps"])

    def test_complete_synthetic_observation_passes(self):
        devices = list(AUDIT.DEVICES)
        observation = {
            "schema_version": 1,
            "doctor": {device: "clean" for device in devices},
            "monitoring": {device: "up" for device in devices},
            "netbox": {device: {"primary_ip": "registered", "mac": "registered"}
                       for device in devices},
            "wiki": {"candidate_page_count": 25, "published": True, "live_page_count": 25},
            "reference": {"astertv_page_count": 1},
            "mirror": {"source_registered": True, "derived_with_provenance": True},
            "backup": {"forgejo_restore_proven": True, "wiki_restore_proven": True,
                       "appliance_restore_proven": devices},
            "ai_administration": {"fleet_skill_manifested": True,
                                  "design_skill_manifested": True,
                                  "forward_tests_passed": True},
        }
        self.assertEqual(AUDIT.audit(observation)["outcome"], "pass")

    def test_unknown_schema_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "operations-observation-schema"):
            AUDIT.audit({"schema_version": 2})


if __name__ == "__main__":
    unittest.main()
