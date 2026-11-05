import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import sa3_candidate_j_exclusion_correction_install as install


class CandidateJExclusionCorrectionInstallTests(unittest.TestCase):
    def test_exact_change_boundary_and_hashes(self):
        root = Path(__file__).parent
        self.assertEqual(install.NEW_WRAPPER,
                         hashlib.sha256((root / install.WRAPPER).read_bytes()).hexdigest())
        self.assertEqual(install.NEW_MANIFEST,
                         hashlib.sha256((root / install.MANIFEST).read_bytes()).hexdigest())
        self.assertEqual(2, len({install.WRAPPER, install.MANIFEST}))

    def test_cli_is_noop_without_apply(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(
                (sys.executable, "-B", install.__file__, "--stage", temporary),
                capture_output=True, text=True, check=False)
        self.assertEqual(2, result.returncode)
        self.assertEqual("source-only", json.loads(result.stdout)["state"])


if __name__ == "__main__":
    unittest.main()
