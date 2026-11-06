import importlib.util
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "astertv_restore_rehearsal", HERE / "rehearse_isolated_restore.py"
)
RESTORE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RESTORE)


class IsolatedRestoreTests(unittest.TestCase):
    def test_runner_is_pinned_and_proof_is_content_free(self):
        source = (HERE / "rehearse_isolated_restore.py").read_text()
        self.assertIn("apply_composition_bundle.py", source)
        self.assertIn("corrupt-package", source)
        self.assertIn("accepted.previous", source)
        self.assertIn("isolated-restore-drift", source)
        self.assertNotIn("TOKEN=", source)
        self.assertNotIn("password", source.lower())

    def test_missing_bundle_fails_closed(self):
        with self.assertRaises(FileNotFoundError):
            RESTORE.rehearse(Path("/definitely/missing.tar.gz"), "0" * 64)


if __name__ == "__main__":
    unittest.main()
