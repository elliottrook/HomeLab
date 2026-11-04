import os
import tempfile
import unittest
from pathlib import Path

from lab_hours_workloads import (REGISTERED_WORKLOADS, validate_inactive_target,
                                 workload)


class WorkloadRegistryTests(unittest.TestCase):
    def test_third_registration_is_distinct_and_fixed(self):
        self.assertIn("sa3-expanded-source-quality-v1", REGISTERED_WORKLOADS)
        spec = workload("sa3-expanded-source-quality-v1")
        self.assertEqual(spec.request_count, 20)
        self.assertEqual(spec.per_request_timeout_seconds, 120)
        self.assertEqual(spec.deadline_seconds, 2700)
        self.assertEqual(spec.minimum_booking_seconds, 3600)
        self.assertEqual(spec.recovery_reserve_seconds, 900)
        self.assertEqual(spec.rescue_after_seconds, 2700)
        self.assertEqual(len(spec.runtime_pins), 4)

    def test_unknown_workload_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "not registered"):
            workload("operator-command")

    def test_m3_registration_is_distinct_fixed_and_booked_for_recovery(self):
        self.assertIn("m3-joint-semantic-35b-public-v1", REGISTERED_WORKLOADS)
        spec = workload("m3-joint-semantic-35b-public-v1")
        self.assertEqual("aster-stream-a", spec.owner)
        self.assertEqual(24, spec.request_count)
        self.assertEqual(2700, spec.deadline_seconds)
        self.assertEqual(3600, spec.minimum_booking_seconds)
        self.assertEqual(900, spec.recovery_reserve_seconds)
        self.assertEqual("m3-joint-semantic-35b", spec.runner_kind)
        self.assertEqual(14, len(spec.runtime_pins))

    def test_evidence_envelope_registration_is_fixed_and_excludes_keys(self):
        workload_id = "sa3-evidence-envelope-quality-v1"
        self.assertIn(workload_id, REGISTERED_WORKLOADS)
        spec = workload(workload_id)
        self.assertEqual("aster-stream-a", spec.owner)
        self.assertEqual(20, spec.request_count)
        self.assertEqual(14, 20 - 6)
        self.assertEqual(120, spec.per_request_timeout_seconds)
        self.assertEqual(2700, spec.deadline_seconds)
        self.assertEqual(3600, spec.minimum_booking_seconds)
        self.assertEqual(900, spec.recovery_reserve_seconds)
        self.assertEqual("sa3-evidence-envelope-quality", spec.runner_kind)
        self.assertEqual(5, len(spec.runtime_pins))
        self.assertFalse(any("keys" in name or "review" in name
                             for name, _ in spec.runtime_pins))

    def test_candidate_i_registration_is_exact_and_excludes_keys(self):
        spec = workload("sa3-evidence-envelope-candidate-i-quality-v1")
        self.assertEqual("aster-stream-a", spec.owner)
        self.assertEqual(20, spec.request_count)
        self.assertEqual(5, len(spec.runtime_pins))
        self.assertEqual(
            "0b9bfb86ef0e3381aca520e294b90b01f9616c51caea21e71d559467837625d0",
            spec.packet_sha256)
        self.assertFalse(any("keys" in name or "review" in name
                             for name, _ in spec.runtime_pins))

    def test_evidence_envelope_inactive_validation_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "target file missing"):
                validate_inactive_target(
                    Path(tmp), unit_root=Path(tmp), expected_uid=os.geteuid(),
                    workload_id="sa3-evidence-envelope-quality-v1")

    def test_inactive_validation_fails_closed_when_target_is_not_installed(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "target file missing"):
                validate_inactive_target(Path(tmp), unit_root=Path(tmp),
                                         expected_uid=os.geteuid())

    def test_inactive_validation_does_not_allow_target_unit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unit_root = root / "units"
            unit_root.mkdir()
            (unit_root / "aster-lab-hours-booking-sa3-expanded-source-quality-v1.service").touch()
            with self.assertRaisesRegex(ValueError, "target file missing"):
                validate_inactive_target(root, unit_root=unit_root,
                                         expected_uid=os.geteuid())


if __name__ == "__main__":
    unittest.main()
