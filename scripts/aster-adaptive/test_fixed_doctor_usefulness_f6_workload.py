import json
import unittest
from pathlib import Path

import fixed_doctor_usefulness_f6_workload as workload


PROPOSAL = Path(__file__).with_name("fixtures") / "fixed-doctor-usefulness-f6-workload-v1.json"


class FixedDoctorUsefulnessF6WorkloadTests(unittest.TestCase):
    def test_exact_proposal_is_non_admitted_and_non_authoritative(self):
        value = workload.validate(PROPOSAL.read_bytes())
        self.assertEqual("not-admitted", value["status"])
        self.assertEqual("separate-reviewed-plan-required", value["sequence_binding"])
        self.assertEqual("disabled", value["tools"])
        self.assertEqual("not-granted", value["authority"])
        self.assertEqual("not-enabled", value["routing"])

    def test_effect_and_recovery_drift_fail_closed(self):
        value = json.loads(PROPOSAL.read_bytes())
        for key, replacement in (
            ("status", "admitted"),
            ("maximum_model_requests", 9),
            ("attempt_policy", "retry"),
            ("tools", "enabled"),
            ("sequence_binding", "reuse-candidate-h-m3"),
            ("recovery_reserve_seconds", 0),
        ):
            with self.subTest(key=key):
                changed = dict(value)
                changed[key] = replacement
                with self.assertRaises(ValueError):
                    workload.validate(json.dumps(changed).encode())


if __name__ == "__main__":
    unittest.main()
