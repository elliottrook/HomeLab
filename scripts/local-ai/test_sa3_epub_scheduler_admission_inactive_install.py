import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import sa3_epub_scheduler_admission_inactive_install as install


class SA3EpubSchedulerAdmissionInstallTests(unittest.TestCase):
    def test_exact_two_file_scope_and_source_pins(self):
        self.assertEqual({"full_inference_lab_sources.py",
                          "lab_hours_release_manifest.json"}, set(install.FILES))
        root = Path(__file__).parent
        for name, (_, expected) in install.FILES.items():
            self.assertEqual(expected,
                             hashlib.sha256((root / name).read_bytes()).hexdigest())

    def test_cli_is_inert_without_apply(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run((sys.executable, "-B", install.__file__,
                                     "--stage", temporary), capture_output=True,
                                    text=True, check=False)
        self.assertEqual(2, result.returncode)
        self.assertEqual("source-only", json.loads(result.stdout)["state"])

    def test_quiet_rejects_state_or_nonready_lease(self):
        with patch.object(install.Path, "exists", return_value=True):
            with self.assertRaisesRegex(install.InstallError, "SHARED"):
                install._quiet()
        result = type("Result", (), {"returncode": 0,
                                      "stdout": '{"state":"active"}'})()
        with patch.object(install.Path, "exists", return_value=False), \
             patch.object(install.subprocess, "run", return_value=result):
            with self.assertRaisesRegex(install.InstallError, "LEASE"):
                install._quiet()


if __name__ == "__main__":
    unittest.main()
