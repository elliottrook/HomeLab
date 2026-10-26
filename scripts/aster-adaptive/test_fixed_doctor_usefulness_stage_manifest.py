import json
import os
import tempfile
import unittest
from pathlib import Path

import fixed_doctor_usefulness_stage_manifest as staging


ROOT = Path(__file__).parent
MANIFEST = ROOT / "fixtures" / "fixed-doctor-usefulness-stage-manifest-v1.json"
SOURCES = {
    "fixed-doctor-usefulness-v1.json": ROOT / "fixtures" / "fixed-doctor-usefulness-v1.json",
    "fixed-doctor-usefulness-profile-v1.json": ROOT / "fixtures" / "fixed-doctor-usefulness-profile-v1.json",
    "fixed_doctor_usefulness.py": ROOT / "fixed_doctor_usefulness.py",
    "fixed_doctor_usefulness_capture.py": ROOT / "fixed_doctor_usefulness_capture.py",
    "journaled_fixed_doctor_usefulness_capture.py": ROOT / "journaled_fixed_doctor_usefulness_capture.py",
    "fixed_doctor_usefulness_9b_adapter.py": ROOT / "fixed_doctor_usefulness_9b_adapter.py",
    "fixed_doctor_usefulness_profile.py": ROOT / "fixed_doctor_usefulness_profile.py",
    "run_fixed_doctor_usefulness.py": ROOT / "run_fixed_doctor_usefulness.py",
}


def stage(root: Path):
    root.mkdir(mode=0o700)
    for name, source in SOURCES.items():
        target = root / name
        target.write_bytes(source.read_bytes())
        target.chmod(0o600)


class FixedDoctorUsefulnessStageManifestTests(unittest.TestCase):
    def test_exact_root_owned_packet_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "stage"
            stage(target)
            result = staging.validate(
                MANIFEST.read_bytes(), target,
                expected_uid=os.geteuid(), expected_gid=os.getegid(),
            )
            self.assertEqual(8, result["verified_input_count"])
            self.assertEqual(29892, result["verified_byte_total"])
            self.assertEqual("not-granted", result["authority"])

    def test_manifest_and_file_drift_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "stage"
            stage(target)
            (target / "fixed_doctor_usefulness.py").write_text("changed")
            os.chmod(target / "fixed_doctor_usefulness.py", 0o600)
            with self.assertRaises(ValueError):
                staging.validate(
                    MANIFEST.read_bytes(), target,
                    expected_uid=os.geteuid(), expected_gid=os.getegid(),
                )
        value = json.loads(MANIFEST.read_bytes())
        value["authority"] = "granted"
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "stage"
            stage(target)
            with self.assertRaises(ValueError):
                staging.validate(
                    json.dumps(value).encode(), target,
                    expected_uid=os.geteuid(), expected_gid=os.getegid(),
                )

    def test_extra_file_and_symlink_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "stage"
            stage(target)
            (target / "extra").write_text("x")
            os.chmod(target / "extra", 0o600)
            with self.assertRaises(ValueError):
                staging.validate(
                    MANIFEST.read_bytes(), target,
                    expected_uid=os.geteuid(), expected_gid=os.getegid(),
                )


if __name__ == "__main__":
    unittest.main()
