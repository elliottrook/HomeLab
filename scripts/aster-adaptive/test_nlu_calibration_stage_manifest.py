import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import nlu_calibration_stage_manifest as stage


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


class NluCalibrationStageManifestTests(unittest.TestCase):
    def test_frozen_packet_is_exact_and_has_no_authority(self):
        value = stage.load_and_validate(encoded(stage.expected_manifest()))
        self.assertEqual(10, len(value["inputs"]))
        self.assertEqual("not-granted", value["authority"])
        self.assertIn("labels.json", value["excluded"])

    def test_path_hash_mode_or_output_drift_fails_closed(self):
        variants = []
        for key, changed in (
            ("guest_id", 104),
            ("base_directory", "/tmp/aster"),
            ("directory_mode", "0755"),
            ("outputs", ["run.json"]),
            ("authority", "granted"),
        ):
            value = copy.deepcopy(stage.expected_manifest())
            value[key] = changed
            variants.append(value)
        value = copy.deepcopy(stage.expected_manifest())
        value["inputs"][0]["sha256"] = "0" * 64
        variants.append(value)
        for value in variants:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "frozen"):
                stage.load_and_validate(encoded(value))

    def test_duplicate_json_keys_are_rejected(self):
        raw = encoded(stage.expected_manifest()).replace(
            b'"schema":"aster-nlu-calibration-stage-manifest.v1"',
            b'"schema":"aster-nlu-calibration-stage-manifest.v1","schema":"duplicate"',
            1,
        )
        with self.assertRaisesRegex(ValueError, "unique-key"):
            stage.load_and_validate(raw)

    def test_exact_regular_packet_bytes_are_verified(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "one.py"
            path.write_bytes(b"one\n")
            inputs = [("one.py", hashlib.sha256(b"one\n").hexdigest(), "source")]
            with patch.object(stage, "INPUTS", inputs):
                manifest = stage.expected_manifest()
                result = stage.validate_packet_files(manifest, {"one.py": path})
            self.assertEqual({"input_count": 1, "byte_total": 4}, result)

    def test_missing_changed_or_symlink_packet_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "one.py"
            path.write_bytes(b"one\n")
            inputs = [("one.py", hashlib.sha256(b"one\n").hexdigest(), "source")]
            with patch.object(stage, "INPUTS", inputs):
                manifest = stage.expected_manifest()
                with self.assertRaisesRegex(ValueError, "exact"):
                    stage.validate_packet_files(manifest, {})
                path.write_bytes(b"changed\n")
                with self.assertRaisesRegex(ValueError, "digest"):
                    stage.validate_packet_files(manifest, {"one.py": path})
                target = Path(root) / "target"
                target.write_bytes(b"one\n")
                link = Path(root) / "link"
                link.symlink_to(target)
                with self.assertRaisesRegex(ValueError, "non-symlink"):
                    stage.validate_packet_files(manifest, {"one.py": link})

    def test_exact_staged_directory_custody_is_verified(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root) / "run"
            directory.mkdir(mode=0o700)
            path = directory / "one.py"
            path.write_bytes(b"one\n")
            path.chmod(0o600)
            inputs = [("one.py", hashlib.sha256(b"one\n").hexdigest(), "source")]
            with patch.object(stage, "INPUTS", inputs):
                result = stage.validate_staged_directory(
                    stage.expected_manifest(), directory,
                    expected_uid=directory.stat().st_uid,
                    expected_gid=directory.stat().st_gid,
                )
            self.assertEqual(True, result["custody_verified"])
            self.assertEqual(4, result["byte_total"])

    def test_staged_directory_rejects_mode_and_extra_output(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root) / "run"
            directory.mkdir(mode=0o700)
            path = directory / "one.py"
            path.write_bytes(b"one\n")
            path.chmod(0o600)
            inputs = [("one.py", hashlib.sha256(b"one\n").hexdigest(), "source")]
            with patch.object(stage, "INPUTS", inputs):
                manifest = stage.expected_manifest()
                path.chmod(0o644)
                with self.assertRaisesRegex(ValueError, "custody"):
                    stage.validate_staged_directory(
                        manifest, directory,
                        expected_uid=directory.stat().st_uid,
                        expected_gid=directory.stat().st_gid,
                    )
                path.chmod(0o600)
                (directory / "run.json").write_text("unused")
                with self.assertRaisesRegex(ValueError, "exactly"):
                    stage.validate_staged_directory(
                        manifest, directory,
                        expected_uid=directory.stat().st_uid,
                        expected_gid=directory.stat().st_gid,
                    )


if __name__ == "__main__":
    unittest.main()
