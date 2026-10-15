import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]


class ApplicationKeyHelperTests(unittest.TestCase):
    def test_add_remove_status_wrappers_use_fixed_paths_and_no_secret_output(self):
        add = (ROOT / "services/local-ai-lease/aster-llama-test-key-add").read_text()
        status = (ROOT / "services/local-ai-lease/aster-llama-test-key-status").read_text()
        remove = (ROOT / "services/local-ai-lease/aster-llama-test-key-remove").read_text()
        for text in (add, status, remove):
            self.assertIn("/etc/aster-llama-api-keys", text)
            self.assertIn("/var/lib/local-ai-lab/application-b60", text)
            self.assertNotIn("print(key", text)
        self.assertIn("append_key", add)
        self.assertIn("remove_key_hash", remove)
        self.assertIn('"removed"', status)
        self.assertIn('"uncertain"', status)


if __name__ == "__main__":
    unittest.main()
