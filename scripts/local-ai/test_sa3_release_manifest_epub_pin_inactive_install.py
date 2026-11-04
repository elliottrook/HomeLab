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
    def test_historical_installer_is_superseded_by_v3_manifest(self):
        root = Path(__file__).parent
        raw = (root / "lab_hours_release_manifest.json").read_bytes()
        self.assertNotEqual(install.NEW_SHA256, hashlib.sha256(raw).hexdigest())
        value = json.loads(raw)
        self.assertEqual("c07c2966a13144b8ca2b68639917381bad7381f9d8fa61adc265f1b30f59c5d9",
                         value["pins"]["full_inference_lab_sources.py"])
        self.assertEqual("094d588b5ff1a6cea1f102375930424ed389cc7af6750a941ce44363043bbf31",
                         value["pins"]["full_inference_lab_validator.py"])
        self.assertEqual("sa3-evidence-envelope-guest-diagnostic-v6",
                         value["release"])
        self.assertEqual("b3c38f030cbe1c0d45f59947cb2bc68cb7f80ed6410ef1669c88c18027296e9a",
                         value["pins"]["full_inference_lab_session.py"])
        self.assertEqual("32fbe1d9e63fdab78a00496c36ca4b3da7a81809e14cf930a209a32ec9649d76",
                         value["pins"]["lab_hours_doctor.py"])

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
