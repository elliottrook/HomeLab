import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / "install_aster_remote_redirect.py").read_text()
BLUEPRINT = (ROOT / "aster-companion-provider-app.yaml").read_text()


class RemoteRedirectTests(unittest.TestCase):
    def test_source_parses_and_is_exact_provider_bound(self):
        ast.parse(SOURCE)
        for value in ('PROVIDER_PK = 26', 'CLIENT_ID = "aster-companion"',
                      'PROVIDER_NAME = "Aster Companion"'):
            self.assertIn(value, SOURCE)

    def test_redirect_is_strict_and_checkpointed(self):
        self.assertIn('REMOTE = "https://aster.elliottrook.com/remote/"', SOURCE)
        self.assertIn("RedirectURIMatchingMode.STRICT", SOURCE)
        self.assertIn("checkpoint(item)", SOURCE)
        self.assertIn("transaction.atomic()", SOURCE)
        self.assertNotIn("update_fields", SOURCE)
        self.assertIn('elif action == "verify"', SOURCE)
        self.assertNotIn("client_secret", SOURCE)

    def test_blueprint_preserves_all_three_strict_redirects(self):
        for value in ("aster-companion://callback",
                      "https://aster.elliottrook.com/companion",
                      "https://aster.elliottrook.com/remote/"):
            self.assertIn("url: " + value, BLUEPRINT)
        self.assertEqual(BLUEPRINT.count("matching_mode: strict"), 3)


if __name__ == "__main__":
    unittest.main()
