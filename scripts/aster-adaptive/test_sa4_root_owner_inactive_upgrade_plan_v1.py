import hashlib
import unittest

import sa4_root_owner_inactive_upgrade_plan_v1 as upgrade
import sa4_single_file_repair_contract_v1 as contract


class SA4RootOwnerInactiveUpgradePlanTests(unittest.TestCase):
    def test_executed_plan_digest_remains_frozen(self):
        self.assertEqual(
            "f7ab264cd40f6639b23c59ab68e36e1c92cea2032bd72f9645f6831e800c9943",
            hashlib.sha256(contract.canonical(upgrade.plan())).hexdigest())

    def test_two_exact_replacements_and_two_exclusive_creations(self):
        value = upgrade.plan()
        replacements = [item for item in value["changes"]
                        if item["before_sha256"] is not None]
        creations = [item for item in value["changes"]
                     if item["before_sha256"] is None]
        self.assertEqual(2, len(replacements))
        self.assertEqual(2, len(creations))
        self.assertEqual(list(reversed([item["destination"]
                                       for item in creations])),
                         value["rollback"]["remove_creations"])

    def test_plan_is_inactive_and_excludes_invocation(self):
        value = upgrade.plan()
        self.assertFalse(value["effect_authorized"])
        self.assertEqual("off", value["automatic_routing"])
        self.assertIn("no-target-write-repair-rollback-or-root-owner-invocation",
                      value["exclusions"])
        self.assertEqual("retain-and-stop", value["rollback"]["uncertainty"])


if __name__ == "__main__":
    unittest.main()
