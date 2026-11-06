import hashlib
from pathlib import Path
import unittest

import sa4_transaction_inactive_install_plan_v1 as install


ROOT = Path(__file__).parents[2]


class SA4TransactionInactiveInstallPlanTests(unittest.TestCase):
    def test_all_source_hashes_are_exact(self):
        for item in install.CHANGES:
            self.assertEqual(item.new_sha256, hashlib.sha256(
                (ROOT / item.source).read_bytes()).hexdigest())

    def test_live_predecessors_are_exact_and_new_files_are_exclusive(self):
        replacements = [item for item in install.CHANGES
                        if item.operation == "checkpoint-and-atomic-replace"]
        creations = [item for item in install.CHANGES
                     if item.operation != "checkpoint-and-atomic-replace"]
        self.assertEqual(2, len(replacements))
        self.assertTrue(all(item.old_sha256 for item in replacements))
        self.assertEqual(5, len(creations))
        self.assertTrue(all(item.old_sha256 is None for item in creations))

    def test_install_is_inactive_reversible_and_cannot_sign_or_repair(self):
        value = install.plan()
        self.assertFalse(value["effect_authorized"])
        self.assertEqual("off", value["automatic_routing"])
        self.assertIn("three-transaction-host-bindings-remain-unconfigured",
                      value["postchecks"])
        self.assertIn("no-private-key-read-print-copy-export-or-signing",
                      value["exclusions"])
        self.assertIn("no-target-write-repair-rollback-or-receipt",
                      value["exclusions"])


if __name__ == "__main__":
    unittest.main()
