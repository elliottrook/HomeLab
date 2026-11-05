import ast
import unittest
from pathlib import Path


SOURCE = (Path(__file__).resolve().parent / "repair_jen_search_authority.py").read_text()


class SearchAuthorityRepairTests(unittest.TestCase):
    def test_exact_host_hashes_and_checkpoint(self):
        ast.parse(SOURCE)
        for value in ('HOST = "AsterTV-Jen"', "OLD_INSTALLER", "NEW_INSTALLER",
                      "CURRENT_FAMILY", "DISPATCH_SHA", "CHECKPOINT"):
            self.assertIn(value, SOURCE)
        self.assertIn("search-authority-boundary", SOURCE)
        self.assertIn("search-authority-checkpoint-drift", SOURCE)

    def test_only_authority_pin_and_stable_installer_change(self):
        self.assertIn('data["skin"]["tools/select_dispatch.py"] = DISPATCH_SHA', SOURCE)
        self.assertIn('"dispatcher_changed": False', SOURCE)
        self.assertNotIn("DISPATCH.write", SOURCE)
        self.assertNotIn("systemctl", SOURCE)


if __name__ == "__main__":
    unittest.main()
