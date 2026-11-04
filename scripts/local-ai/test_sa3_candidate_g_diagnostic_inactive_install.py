import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import sa3_candidate_g_diagnostic_inactive_install as install


class CandidateGDiagnosticInstallTests(unittest.TestCase):
    def test_exact_scope_and_source_pins(self):
        self.assertEqual({"sa3_evidence_envelope_listener_adapter.py",
                          "lab_hours_release_manifest.json"},
                         set(install.HOST_FILES))
        self.assertEqual({"aster_llama_sa3_evidence_envelope_wrapper.py"},
                         set(install.GUEST_FILES))
        root = Path(__file__).parent
        for name, (_, expected, _) in install.HOST_FILES.items():
            self.assertEqual(expected, hashlib.sha256((root / name).read_bytes()).hexdigest())
        for name, (_, expected, _) in install.GUEST_FILES.items():
            self.assertEqual(expected, hashlib.sha256((root / name).read_bytes()).hexdigest())

    def test_cli_is_inert_without_apply(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run((sys.executable, "-B", install.__file__,
                                     "--stage", temporary), capture_output=True,
                                    text=True, check=False)
        self.assertEqual(2, result.returncode)
        self.assertEqual("source-only", json.loads(result.stdout)["state"])

    def test_quiet_fails_closed(self):
        with patch.object(install.Path, "exists", return_value=True):
            with self.assertRaisesRegex(install.InstallError, "SHARED"):
                install._quiet()
        result = type("Result", (), {"returncode": 0,
                                      "stdout": '{"state":"active"}'})()
        with patch.object(install.Path, "exists", return_value=False), \
             patch.object(install.subprocess, "run", return_value=result):
            with self.assertRaisesRegex(install.InstallError, "LEASE"):
                install._quiet()

    def test_remote_requires_baseline_and_checkpoint(self):
        self.assertIn("BASELINE_DRIFT", install.REMOTE)
        self.assertIn("CHECKPOINT_EXISTS", install.REMOTE)
        self.assertIn("ROLLBACK_UNCERTAIN", install.REMOTE)


if __name__ == "__main__":
    unittest.main()
