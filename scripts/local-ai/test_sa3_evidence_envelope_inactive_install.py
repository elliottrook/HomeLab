import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import sa3_evidence_envelope_inactive_install as install


class EvidenceEnvelopeInactiveInstallTests(unittest.TestCase):
    def test_exact_registration_and_runtime_boundary(self):
        self.assertEqual(3, len(install.HOST_FILES))
        self.assertEqual(5, len(install.GUEST_FILES))
        self.assertIn("sa3-evidence-envelope-quality-v1.json", install.GUEST_FILES)
        self.assertFalse(any("keys" in name or "review" in name
                             for name in install.GUEST_FILES))

    def test_default_cli_is_source_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                (sys.executable, "-B", install.__file__, "--stage", tmp),
                capture_output=True, text=True, check=False)
        self.assertEqual(2, result.returncode)
        self.assertEqual("source-only", json.loads(result.stdout)["state"])

    def test_historical_pins_are_exact_or_explicitly_superseded(self):
        root = Path(__file__).parent
        for name, (_, expected, _) in install.HOST_FILES.items():
            import hashlib
            current = hashlib.sha256((root / name).read_bytes()).hexdigest()
            if name == "lab_hours_release_manifest.json":
                self.assertNotEqual(expected, current)
            else:
                self.assertEqual(expected, current)


if __name__ == "__main__":
    unittest.main()
