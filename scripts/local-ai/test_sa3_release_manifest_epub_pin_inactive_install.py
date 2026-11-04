import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import sa3_release_manifest_epub_pin_inactive_install as install


class SA3ReleaseManifestEpubPinInstallTests(unittest.TestCase):
    def test_exact_manifest_candidate_and_pins(self):
        root = Path(__file__).parent
        raw = (root / "lab_hours_release_manifest.json").read_bytes()
        self.assertEqual(install.NEW_SHA256, hashlib.sha256(raw).hexdigest())
        value = json.loads(raw)
        self.assertEqual("6103da31e85e957ae9491c2d64bd3f2bfb497c31db5c8bac0616786fff4c13ad",
                         value["pins"]["full_inference_lab_sources.py"])
        self.assertEqual("094d588b5ff1a6cea1f102375930424ed389cc7af6750a941ce44363043bbf31",
                         value["pins"]["full_inference_lab_validator.py"])

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
        result = type("Result", (), {"returncode": 0, "stdout": '{"state":"active"}'})()
        with patch.object(install.Path, "exists", return_value=False), \
             patch.object(install.subprocess, "run", return_value=result):
            with self.assertRaisesRegex(install.InstallError, "LEASE"):
                install._quiet()


if __name__ == "__main__":
    unittest.main()
