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
