import hashlib
from pathlib import Path
import unittest

import sa4_runtime_control_inactive_upgrade_plan_v1 as upgrade


class SA4RuntimeControlInactiveUpgradePlanTests(unittest.TestCase):
    def test_sources_match_exact_pins(self):
        root = Path(__file__).parents[2]
        for item in upgrade.CHANGES:
            self.assertEqual(item.after_sha256, hashlib.sha256(
                (root / item.source).read_bytes()).hexdigest())

    def test_one_replace_one_create_and_exact_rollback(self):
        value = upgrade.plan()
        self.assertEqual("checkpoint-and-atomic-replace",
                         value["changes"][0]["operation"])
        self.assertEqual("create-exclusive", value["changes"][1]["operation"])
        self.assertEqual(upgrade.CHANGES[0].destination,
                         value["rollback"]["restore"])
        self.assertEqual(upgrade.CHANGES[1].destination,
                         value["rollback"]["remove"])

    def test_upgrade_is_inactive(self):
        value = upgrade.plan()
        self.assertFalse(value["effect_authorized"])
        self.assertEqual("off", value["automatic_routing"])
        self.assertIn("no-root-owner-invocation", value["exclusions"])
        self.assertIn("operation-lock-absent", value["precondition"])


if __name__ == "__main__":
    unittest.main()
