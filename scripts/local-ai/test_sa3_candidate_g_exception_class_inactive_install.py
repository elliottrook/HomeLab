import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import sa3_candidate_g_exception_class_inactive_install as install


class CandidateGExceptionClassInstallTests(unittest.TestCase):
    def test_exact_one_file_scope_and_source_pin(self):
        self.assertEqual("aster_llama_sa3_evidence_envelope_wrapper.py",
                         install.NAME)
        current = hashlib.sha256(
            Path(__file__).with_name(install.NAME).read_bytes()).hexdigest()
        self.assertEqual(install.NEW, current)
        self.assertNotEqual(install.OLD, install.NEW)

    def test_cli_is_inert_without_apply(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run((sys.executable, "-B", install.__file__,
                                     "--stage", temporary), capture_output=True,
                                    text=True, check=False)
        self.assertEqual(2, result.returncode)
        self.assertEqual("source-only", json.loads(result.stdout)["state"])

    def test_checkpoint_and_rollback_are_fail_closed(self):
        self.assertIn("CHECKPOINT_EXISTS", install.REMOTE)
        self.assertIn("ROLLBACK_UNCERTAIN", install.REMOTE)
        self.assertIn("CHECKPOINT_DRIFT", install.REMOTE)


if __name__ == "__main__":
    unittest.main()
