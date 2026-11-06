import hashlib
from pathlib import Path
import unittest

import sa4_distinct_canary_seed_inactive_install_plan_v1 as install


class Tests(unittest.TestCase):
    def test_sources_are_exact(self):
        root = Path(__file__).parents[2]
        for item in install.CHANGES:
            self.assertEqual(
                item.after_sha256,
                hashlib.sha256((root / item.source).read_bytes()).hexdigest())

    def test_create_only_and_reverse_exact_rollback(self):
        value = install.plan()
        self.assertTrue(all(
            row["operation"] == "create-exclusive" for row in value["changes"]))
        self.assertEqual(
            [item.destination for item in reversed(install.CHANGES)],
            value["rollback"]["remove-only-exact-after-hashes"])

    def test_install_is_inert_and_not_a_repair(self):
        value = install.plan()
        self.assertFalse(value["effect_authorized"])
        self.assertFalse(value["repair_authorized"])
        self.assertIn("no-existing-canary-touch", value["exclusions"])


if __name__ == "__main__":
    unittest.main()
