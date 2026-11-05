import ast
import unittest
from pathlib import Path


SOURCE = (Path(__file__).resolve().parent / "install_aster_remote_headers.py").read_text()


class HeaderInstallerTests(unittest.TestCase):
    def test_exact_host_hash_checkpoint_and_rollback(self):
        ast.parse(SOURCE)
        for value in ('HOST = "hermesagent"', "header-install-boundary",
                      "header-checkpoint-drift", "header-rollback-boundary"):
            self.assertIn(value, SOURCE)
        self.assertIn("shutil.copy2(CHECKPOINT, TARGET)", SOURCE)

    def test_live_validation_requires_header_and_route(self):
        self.assertIn('reply.status == 200 and present is expected', SOURCE)
        self.assertIn('Content-Security-Policy', SOURCE)
        self.assertIn("systemctl", SOURCE)


if __name__ == "__main__":
    unittest.main()
