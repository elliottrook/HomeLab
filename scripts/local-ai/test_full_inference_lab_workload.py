import json
import unittest

from full_inference_lab_workload import (LAB_COMMAND, LAB_PROFILE, LabWorkloadError,
                                         run_fixed_smoke, validate_receipt)


class FullInferenceLabWorkloadTests(unittest.TestCase):
    def receipt(self, **updates):
        value = {
            "schema": "aster-9b-direct-control-smoke.v1",
            "profile": LAB_PROFILE,
            "lease_id": "lease-1",
            "generation": 2,
            "port": 11436,
            "production_service": "masked-inactive",
            "credential_exported": False,
            "tool_mode": "disabled",
            "request_count": 3,
            "observation_ids": ["a", "b", "c"],
            "exit_status": 0,
        }
        value.update(updates)
        return value

    def test_fixed_command_is_distinct_from_production_service(self):
        self.assertIn("aster-llama-lab-smoke", " ".join(LAB_COMMAND))
        self.assertIn("11436", LAB_COMMAND)
        self.assertNotIn("aster-llama.service", LAB_COMMAND)

    def test_accepts_only_content_free_three_request_receipt(self):
        value = validate_receipt(self.receipt(), lease_id="lease-1", generation=2)
        self.assertEqual(value["request_count"], 3)

    def test_runner_never_returns_raw_answers(self):
        seen = []
        def runner(command, timeout):
            seen.append((tuple(command), timeout))
            return 0, json.dumps(self.receipt())
        value = run_fixed_smoke(runner, lease_id="lease-1", generation=2)
        self.assertNotIn("answer", value)
        self.assertEqual(seen, [(LAB_COMMAND, 300.0)])

    def test_rejects_production_or_credential_drift(self):
        for updates in ({"production_service": "active"}, {"credential_exported": True},
                        {"port": 11435}, {"request_count": 20}):
            with self.subTest(updates=updates):
                with self.assertRaises(LabWorkloadError):
                    validate_receipt(self.receipt(**updates), lease_id="lease-1", generation=2)


if __name__ == "__main__":
    unittest.main()
