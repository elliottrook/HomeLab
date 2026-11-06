import unittest
from unittest.mock import patch

import sa4_distinct_canary_transaction_release_v1 as release
import sa4_fixed_transaction_runner_v3 as runner
import sa4_root_transaction_owner_v3 as owner
import sa4_target_registry_v1 as registry_v1
import sa4_target_registry_v2 as registry_v2


class Tests(unittest.TestCase):
    def test_release_binds_distinct_inert_seed_and_sources(self):
        release.validate_static_evidence()
        value = release.packet()
        self.assertEqual(owner.BOUND_TARGET_ID, value["target_id"])
        self.assertEqual(3, len(value["source_sha256"]))
        self.assertFalse(value["effect_authorized"])
        self.assertFalse(value["transaction_limits"]["automatic_retry"])

    def test_registry_boundary_is_one_way(self):
        with self.assertRaises(ValueError):
            registry_v1.resolve_production(owner.BOUND_TARGET_ID)
        target = registry_v2.resolve_production(owner.BOUND_TARGET_ID)
        self.assertEqual("lxc104", target.host_id)
        self.assertEqual(release.TARGET_BEFORE_SHA256,
                         release.packet()["target_before_sha256"])

    def test_owner_rejects_spent_v1_target_before_effect(self):
        with patch.object(owner.previous.contract, "validate_plan",
                          return_value={
                              "target_id": "sa4-lxc104-canary-adapter-v1"}), \
             self.assertRaisesRegex(ValueError, "target changed"):
            with owner._accepted_registry(b"spent-v1-plan\n"):
                self.fail("spent target unexpectedly entered v3 chain")

    def test_runner_uses_separate_create_only_state(self):
        self.assertEqual("transaction-input-v2", runner.INPUT_DIR.name)
        self.assertEqual("transaction-evidence-v2", runner.EVIDENCE_DIR.name)
        self.assertEqual("one-use-ledger-v2", runner.LEDGER_ROOT.name)
        self.assertNotEqual("sa4-canary-first-operation-v1",
                            runner.OPERATION_ID)
        with self.assertRaisesRegex(ValueError, "accepts no arguments"):
            runner.main(["unexpected"])


if __name__ == "__main__":
    unittest.main()
