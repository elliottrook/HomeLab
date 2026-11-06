import hashlib
from pathlib import Path
import unittest

import sa4_terminal_reconciliation_v2_inactive_install_plan as install


class Tests(unittest.TestCase):
    def test_sources_are_exact(self):
        root = Path(__file__).parents[2]
        for item in install.CHANGES:
            self.assertEqual(
                item.after_sha256,
                hashlib.sha256((root / item.source).read_bytes()).hexdigest())

    def test_create_only_and_exact_rollback(self):
        value = install.plan()
        self.assertTrue(all(
            item["operation"] == "create-exclusive"
            for item in value["changes"]))
        self.assertEqual(
            [item.destination for item in reversed(install.CHANGES)],
            value["rollback"]["remove-only-exact-after-hashes"])

    def test_plan_is_inactive_and_forbids_reconciliation_rewrite(self):
        value = install.plan()
        self.assertFalse(value["effect_authorized"])
        self.assertIn("no-ledger-rewrite", value["exclusions"])
        self.assertIn("no-repair", value["exclusions"])
        self.assertEqual("off", value["automatic_routing"])


if __name__ == "__main__":
    unittest.main()
