import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import lab_hours_inactive_target as target


class InactiveGuestTargetTests(unittest.TestCase):
    def test_fixed_guest_validation_passes(self):
        def run(command, **kwargs):
            self.assertEqual(command[:4], ("pct", "exec", "110", "--"))
            payload = json.loads(kwargs["input"])
            self.assertEqual(payload["root"], target.GUEST_ROOT)
            self.assertEqual(len(payload["pins"]), 4)
            out = {"effects": "not-attempted", "guest": "110",
                   "runtime_files": 4, "state": "valid"}
            return subprocess.CompletedProcess(command, 0, json.dumps(out), "")
        with tempfile.TemporaryDirectory() as tmp:
            value = target.validate_guest_target(unit_root=Path(tmp), runner=run)
        self.assertEqual(value["target_units"], "absent")

    def test_guest_failure_is_closed(self):
        def run(command, **kwargs):
            return subprocess.CompletedProcess(command, 1, "", "TARGET_FILE_MISSING:packet")
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "TARGET_FILE_MISSING"):
                target.validate_guest_target(unit_root=Path(tmp), runner=run)

    def test_existing_unit_is_closed_before_guest_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "aster-lab-hours-booking-sa3-expanded-source-quality-v1.service").touch()
            with self.assertRaisesRegex(ValueError, "must remain inactive"):
                target.validate_guest_target(unit_root=root, runner=lambda *a, **k: None)


if __name__ == "__main__":
    unittest.main()
