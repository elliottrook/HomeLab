import ast
import unittest
from pathlib import Path


SOURCE = (Path(__file__).resolve().parent / "install_aster_remote_brand_assets.py").read_text()


class RemoteBrandInstallerTests(unittest.TestCase):
    def test_target_and_exact_predecessor_are_pinned(self):
        ast.parse(SOURCE)
        for value in (
            'HOST = "hermesagent"',
            'GATEWAY = Path("/opt/aster-agent/aster_remote.py")',
            'TARGET = Path("/opt/aster-agent/static/remote")',
            '"aster_remote.py": "f2780775df560903ecf6a0b4efe224343f327914bd680fe8fdd4abb24484e983"',
            'remote-brand-checkpoint-drift',
        ):
            self.assertIn(value, SOURCE)

    def test_assets_are_exact_svg_placement_exports(self):
        for value in (
            '"astertv-remote-180.png": "36eb73e019be374fbf4cb2fdf2e16de14b30e0dc470cbc5b19fae63bc4ba8379"',
            '"astertv-remote-512.png": "07880f3fb4e791b6383cabfe3c77a5218c184e84073c8cb89037e9b9c5a16074"',
            '"source_svg_sha256": "7effb1ffe3ba828de63059235c976f26e0d7fb869e0856d0fb52cea86a775ada"',
        ):
            self.assertIn(value, SOURCE)

    def test_install_is_checkpointed_atomic_and_restores_on_failure(self):
        self.assertIn("os.replace(temporary, path)", SOURCE)
        self.assertIn('route = "" if name == "index.html" else name', SOURCE)
        self.assertIn("except Exception:\n        restore(); raise", SOURCE)
        self.assertIn('["systemctl", "restart", "aster-agent.service"]', SOURCE)
        self.assertIn("remote-brand-auth-regression", SOURCE)


if __name__ == "__main__":
    unittest.main()
