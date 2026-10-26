import tempfile
import unittest
from pathlib import Path
from unittest import mock

import run_fixed_doctor_usefulness_v3 as runner


class RunFixedDoctorUsefulnessV3Tests(unittest.TestCase):
    def test_requires_inherited_descriptor(self):
        with self.assertRaisesRegex(ValueError, "inherited"):
            runner.read_key_fd(2)

    def test_selects_limitation_calibrated_adapter(self):
        self.assertIn("cannot establish a cause or a repair", runner.adapter.LIMITATION)

    def test_run_wipes_key_and_uses_v2_adapter(self):
        root = Path(__file__).with_name("fixtures")
        fixture = root / "fixed-doctor-usefulness-v1.json"
        profile = root / "fixed-doctor-usefulness-profile-v1.json"
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            runner, "read_key_fd", return_value=bytearray(b"test-only-key")
        ), mock.patch.object(runner.adapter, "invoke", return_value="bounded answer") as invoke, mock.patch.object(
            runner.journaled, "capture_journaled", return_value={"completed": 8}
        ) as capture:
            result = runner.run(fixture, profile, Path(directory), 3)
        self.assertEqual({"completed": 8}, result)
        self.assertTrue(callable(capture.call_args.args[2]))
        self.assertFalse(invoke.called)


if __name__ == "__main__":
    unittest.main()
