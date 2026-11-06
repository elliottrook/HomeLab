import hashlib
from pathlib import Path
import unittest

import sa4_signer_preflight_install_plan_v1 as install


ROOT = Path(__file__).parents[2]


class SA4SignerPreflightInstallPlanTests(unittest.TestCase):
    def test_all_source_hashes_match(self):
        for path, expected in install.SOURCE_HASHES.items():
            with self.subTest(path=path):
                self.assertEqual(expected, hashlib.sha256(
                    (ROOT / path).read_bytes()).hexdigest())

    def test_plan_is_exact_reversible_and_zero_effect(self):
        value = install.plan()
        self.assertEqual(3, len(value["changes"]))
        self.assertEqual(1, sum(
            item["operation"] == "checkpoint-and-atomic-replace"
            for item in value["changes"]))
        self.assertEqual(2, sum(
            item["operation"] == "create-exclusive"
            for item in value["changes"]))
        self.assertFalse(value["effect_authorized"])
        self.assertEqual("off", value["automatic_routing"])
        self.assertIn("no-private-key-read-print-copy-or-export",
                      value["exclusions"])
        self.assertIn("uncertainty", value["rollback"])

    def test_compiled_owner_binary_is_new_versioned_path(self):
        owner = install.CHANGES[0]
        self.assertEqual(install.MAC_NEW_BINARY, owner.destination)
        self.assertNotEqual(install.MAC_OLD_BINARY, owner.destination)
        self.assertIsNone(owner.old_sha256)


if __name__ == "__main__":
    unittest.main()
