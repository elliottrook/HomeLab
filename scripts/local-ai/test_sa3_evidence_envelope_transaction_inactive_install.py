import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import sa3_evidence_envelope_transaction_inactive_install as install


class CandidateGTransactionInstallTests(unittest.TestCase):
    def test_fixed_change_is_three_host_one_guest_and_no_unit(self):
        self.assertEqual(3, len(install.HOST_FILES))
        self.assertEqual(1, len(install.GUEST_FILES))
        self.assertIn("lab_hours_release_manifest.json", install.HOST_FILES)
        self.assertIn("aster_llama_sa3_evidence_envelope_wrapper.py", install.GUEST_FILES)

    def test_historical_pins_are_exact_or_explicitly_superseded(self):
        root = Path(__file__).parent
        superseded = {"sa3_evidence_envelope_listener_adapter.py",
                      "lab_hours_release_manifest.json"}
        for name, (_, expected, _) in install.HOST_FILES.items():
            current = hashlib.sha256((root / name).read_bytes()).hexdigest()
            (self.assertNotEqual if name in superseded else self.assertEqual)(expected, current)
        for name, expected in install.GUEST_FILES.items():
            self.assertNotEqual(expected,
                                hashlib.sha256((root / name).read_bytes()).hexdigest())

    def test_cli_is_noop_without_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run((sys.executable, "-B", install.__file__, "--stage", tmp),
                                    capture_output=True, text=True, check=False)
        self.assertEqual(2, result.returncode)
        self.assertEqual("source-only", json.loads(result.stdout)["state"])

    def test_installer_dependency_is_present_in_bundle_selection(self):
        import build_sa3_evidence_envelope_transaction_bundle as bundle
        self.assertIn("scripts/local-ai/sa3_evidence_envelope_inactive_install.py",
                      bundle.FILES)


if __name__ == "__main__":
    unittest.main()
