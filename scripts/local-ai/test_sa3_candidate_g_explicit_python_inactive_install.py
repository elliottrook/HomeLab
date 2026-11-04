import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import sa3_candidate_g_explicit_python_inactive_install as install


class CandidateGExplicitPythonInstallTests(unittest.TestCase):
    def test_exact_two_file_scope_and_source_pins(self):
        self.assertEqual({"sa3_evidence_envelope_listener_adapter.py",
                          "lab_hours_release_manifest.json"}, set(install.FILES))
        root = Path(__file__).parent
        for name, (_, expected, _) in install.FILES.items():
            self.assertEqual(expected,
                             hashlib.sha256((root / name).read_bytes()).hexdigest())

    def test_cli_is_inert_without_apply(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run((sys.executable, "-B", install.__file__,
                                     "--stage", temporary), capture_output=True,
                                    text=True, check=False)
        self.assertEqual(2, result.returncode)
        self.assertEqual("source-only", json.loads(result.stdout)["state"])

    def test_checkpoint_is_unique_and_root_scoped(self):
        self.assertIn("sa3-candidate-g-explicit-python-r1-20261104",
                      str(install.CHECKPOINT))


if __name__ == "__main__":
    unittest.main()
