import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import build_sa3_candidate_j_quality_inactive_bundle as bundle
import sa3_candidate_j_quality_inactive_install as install


class CandidateJQualityInactiveInstallTests(unittest.TestCase):
    def test_exact_host_and_guest_change_boundary(self):
        self.assertEqual(4, len(install.HOST_REPLACE))
        self.assertEqual(3, len(install.HOST_ADD))
        self.assertEqual(0, len(install.GUEST_EXISTING))
        self.assertEqual(5, len(install.GUEST_ADD))
        self.assertEqual(0o755,
                         install.HOST_REPLACE["lab_hours_reserved_runner.py"][2])
        self.assertEqual(0o755,
                         install.HOST_REPLACE["full_inference_lab_runtime.py"][2])
        self.assertFalse(any("review" in name or "keys" in name or "scorer" in name
                             for name in install.GUEST_ADD))
        self.assertFalse(any("candidate-i" in name or "envelope-quality" in name
                             for name in install.GUEST_ADD))

    def test_source_hashes_are_exact(self):
        root = Path(__file__).parent
        for name, (_, expected, _) in install.HOST_REPLACE.items():
            self.assertEqual(
                expected, hashlib.sha256((root / name).read_bytes()).hexdigest())
        for name, (expected, _) in install.HOST_ADD.items():
            self.assertEqual(
                expected, hashlib.sha256((root / name).read_bytes()).hexdigest())

    def test_cli_is_noop_without_apply(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(
                (sys.executable, "-B", install.__file__, "--stage", temporary),
                capture_output=True, text=True, check=False)
        self.assertEqual(2, result.returncode)
        self.assertEqual("source-only", json.loads(result.stdout)["state"])

    def test_bundle_is_deterministic_and_binds_both_commits(self):
        with tempfile.TemporaryDirectory() as temporary:
            first = bundle.build(Path(temporary) / "a")
            second = bundle.build(Path(temporary) / "b")
        self.assertEqual(first["sha256"], second["sha256"])
        self.assertEqual(14, first["files"])
        self.assertEqual(
            "4929237ab1b34a43ec50bdcaae08c6217758bfde", bundle.MAIN_COMMIT)


if __name__ == "__main__":
    unittest.main()
